"""Decoding, with the colour tags worked out before any pixel is read.

Two rules matter here and both are written up in docs/SPEC_SOURCES.md section 6 and 7:

* an untagged stream is decoded as BT.709 when the picture is HD and BT.601 when it is SD,
  and the guess is recorded in the sidecar so nobody has to wonder;
* a `yuvj*` pixel format is full range whatever the range tag says.

flashmap never multiplies a YCbCr matrix itself. It tells libswscale which matrix and range to
use and reads back RGB.

Timestamps come from the container. There is no assumed frame rate anywhere in this file.
"""

from __future__ import annotations

import fractions
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import av
import numpy as np
from av.video.reformatter import Interpolation, VideoReformatter
from numpy.typing import NDArray

__all__ = [
    "ColorPolicy",
    "ColorDecision",
    "AnalysisFrame",
    "SourceInfo",
    "UnsupportedInput",
    "decide_color",
    "probe",
    "iter_frames",
]

# libavutil AVColorSpace values. See docs/SPEC_SOURCES.md section 7 for the source file.
_AVCOL_SPC_RGB = 0
_AVCOL_SPC_BT709 = 1
_AVCOL_SPC_UNSPECIFIED = 2
_AVCOL_SPC_FCC = 4
_AVCOL_SPC_BT470BG = 5
_AVCOL_SPC_SMPTE170M = 6
_AVCOL_SPC_SMPTE240M = 7
_AVCOL_SPC_BT2020_NCL = 9
_AVCOL_SPC_BT2020_CL = 10

# libavutil AVColorRange values.
_AVCOL_RANGE_UNSPECIFIED = 0
_AVCOL_RANGE_MPEG = 1
_AVCOL_RANGE_JPEG = 2

# libavutil AVColorTransferCharacteristic values for the two HDR curves we refuse.
_AVCOL_TRC_SMPTE2084 = 16
_AVCOL_TRC_ARIB_STD_B67 = 18

_MATRIX_NAMES = {
    _AVCOL_SPC_BT709: ("bt709", "ITU709"),
    _AVCOL_SPC_FCC: ("fcc", "FCC"),
    _AVCOL_SPC_BT470BG: ("bt601", "ITU601"),
    _AVCOL_SPC_SMPTE170M: ("bt601", "ITU601"),
    _AVCOL_SPC_SMPTE240M: ("smpte240m", "SMPTE240M"),
    _AVCOL_SPC_BT2020_NCL: ("bt2020ncl", "BT2020"),
    _AVCOL_SPC_BT2020_CL: ("bt2020ncl", "BT2020"),
}


class UnsupportedInput(Exception):
    """The file is something flashmap version 1 refuses to measure."""


def _open(path: str | Path) -> "av.container.InputContainer":
    """Open a file, turning any decoder complaint into one exception callers can handle."""
    try:
        return av.open(str(path))
    except (av.FFmpegError, OSError, ValueError) as exc:
        raise UnsupportedInput(f"{path} could not be opened: {exc}") from exc


@dataclass(frozen=True)
class ColorPolicy:
    """How to fill in tags the file did not carry.

    `hd_min_height` is a project convention, not a number from any spec. See
    docs/SPEC_SOURCES.md section 6.
    """

    hd_min_height: int = 720
    allow_hdr: bool = False


@dataclass(frozen=True)
class ColorDecision:
    matrix: str
    matrix_source: str
    color_range: str
    range_source: str
    swscale_colorspace: str
    swscale_range: str
    pixel_format: str
    transfer: str

    def as_dict(self) -> dict[str, str]:
        return {
            "matrix": self.matrix,
            "matrix_source": self.matrix_source,
            "range": self.color_range,
            "range_source": self.range_source,
            "pixel_format": self.pixel_format,
            "transfer_tag": self.transfer,
            "luminance_model": "wcag-relative-luminance-srgb",
        }


@dataclass
class AnalysisFrame:
    """One decoded frame, already scaled to the analysis size."""

    index: int
    pts_ms: float
    rgb: NDArray[np.float32]
    """Height by width by 3, sRGB encoded, 0 to 1."""
    video_level: NDArray[np.float32]
    """Height by width, the luma signal normalised so black is 0 and white is 1."""


@dataclass
class SourceInfo:
    path: str
    sha256: str
    size_bytes: int
    coded_width: int
    coded_height: int
    analysis_width: int
    analysis_height: int
    container_frame_rate: str | None
    duration_ms: float | None
    color: ColorDecision
    timestamp_source: str = "container-pts"


def _tag(frame_value: int | None, stream_value: int | None) -> int:
    for value in (frame_value, stream_value):
        if value is not None and value != _AVCOL_SPC_UNSPECIFIED:
            return int(value)
    return _AVCOL_SPC_UNSPECIFIED


def decide_color(
    pixel_format: str,
    height: int,
    colorspace_tag: int,
    range_tag: int,
    transfer_tag: int,
    policy: ColorPolicy = ColorPolicy(),
) -> ColorDecision:
    """Work out the matrix and the range to decode with, and say where each came from."""
    transfer_name = str(transfer_tag)
    if not policy.allow_hdr and transfer_tag in (_AVCOL_TRC_SMPTE2084, _AVCOL_TRC_ARIB_STD_B67):
        curve = "PQ (SMPTE ST 2084)" if transfer_tag == _AVCOL_TRC_SMPTE2084 else "HLG"
        raise UnsupportedInput(
            f"this file is tagged {curve}, and flashmap version 1 measures SDR only. "
            "See docs/SPEC_SOURCES.md section 5 for what is missing."
        )

    if pixel_format.startswith("yuvj"):
        color_range, range_source = "full", "pixel-format-yuvj"
    elif range_tag == _AVCOL_RANGE_JPEG:
        color_range, range_source = "full", "stream-tag"
    elif range_tag == _AVCOL_RANGE_MPEG:
        color_range, range_source = "limited", "stream-tag"
    else:
        color_range, range_source = "limited", "default-limited"

    if colorspace_tag == _AVCOL_SPC_RGB:
        # An RGB stream carries no YCbCr matrix at all. libswscale passes the samples
        # through, and we say so rather than pretending a matrix was chosen.
        matrix, swscale_colorspace, matrix_source = "rgb", "ITU709", "rgb-stream-no-matrix"
    elif colorspace_tag in _MATRIX_NAMES:
        matrix, swscale_colorspace = _MATRIX_NAMES[colorspace_tag]
        matrix_source = "stream-tag"
    elif height >= policy.hd_min_height:
        matrix, swscale_colorspace, matrix_source = "bt709", "ITU709", "inferred-hd-bt709"
    else:
        matrix, swscale_colorspace, matrix_source = "bt601", "ITU601", "inferred-sd-bt601"

    return ColorDecision(
        matrix=matrix,
        matrix_source=matrix_source,
        color_range=color_range,
        range_source=range_source,
        swscale_colorspace=swscale_colorspace,
        swscale_range="JPEG" if color_range == "full" else "MPEG",
        pixel_format=pixel_format,
        transfer=transfer_name,
    )


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _analysis_size(width: int, height: int, target_width: int) -> tuple[int, int]:
    if width <= target_width:
        return width, height
    scaled_height = max(2, int(round(height * target_width / width)))
    # libswscale is happier with even sizes for the formats we touch.
    return target_width - (target_width % 2), scaled_height - (scaled_height % 2)


def probe(path: str | Path, policy: ColorPolicy = ColorPolicy(), analysis_width: int = 192) -> SourceInfo:
    """Read the header and the first frame, and decide how the file will be decoded."""
    path = Path(path)
    with _open(path) as container:
        if not container.streams.video:
            raise UnsupportedInput(f"{path} has no video stream")
        stream = container.streams.video[0]
        codec = stream.codec_context
        first = None
        try:
            for frame in container.decode(stream):
                first = frame
                break
        except (av.FFmpegError, OSError, ValueError) as exc:
            raise UnsupportedInput(f"{path} could not be decoded: {exc}") from exc
        if first is None:
            raise UnsupportedInput(f"{path} decoded no frames")

        colorspace_tag = _tag(getattr(first, "colorspace", None), getattr(codec, "colorspace", None))
        range_tag = int(
            getattr(first, "color_range", None)
            or getattr(codec, "color_range", None)
            or _AVCOL_RANGE_UNSPECIFIED
        )
        transfer_tag = int(
            getattr(first, "color_trc", None) or getattr(codec, "color_trc", None) or 2
        )
        decision = decide_color(
            pixel_format=first.format.name,
            height=first.height,
            colorspace_tag=colorspace_tag,
            range_tag=range_tag,
            transfer_tag=transfer_tag,
            policy=policy,
        )
        rate: fractions.Fraction | None = stream.average_rate
        duration_ms = None
        if stream.duration is not None and stream.time_base is not None:
            duration_ms = float(stream.duration * stream.time_base) * 1000.0
        aw, ah = _analysis_size(first.width, first.height, analysis_width)

    return SourceInfo(
        path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        coded_width=first.width,
        coded_height=first.height,
        analysis_width=aw,
        analysis_height=ah,
        container_frame_rate=None if rate is None else f"{rate.numerator}/{rate.denominator}",
        duration_ms=duration_ms,
        color=decision,
    )


def iter_frames(
    path: str | Path,
    info: SourceInfo,
    interpolation: int = Interpolation.AREA,
) -> Iterator[AnalysisFrame]:
    """Decode every frame, scaled to the analysis size, with real container timestamps.

    The timestamp is the frame's presentation timestamp multiplied by the stream time base.
    No frame rate is assumed, so variable frame rate files come out right.
    """
    reformatter = VideoReformatter()
    index = 0
    last_pts_ms: float | None = None
    with _open(path) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        time_base = stream.time_base
        for frame in container.decode(stream):
            stamp = frame.pts if frame.pts is not None else frame.dts
            if stamp is None or time_base is None:
                raise UnsupportedInput(
                    f"{path} frame {index} has no presentation timestamp, so flashmap cannot "
                    "place it in time. flashmap never assumes a frame rate."
                )
            pts_ms = float(stamp * time_base) * 1000.0
            if last_pts_ms is not None and pts_ms < last_pts_ms:
                # Out of order presentation timestamps mean the decoder handed us frames in
                # coded order. Skip rather than mis-time the flash windows.
                continue
            last_pts_ms = pts_ms

            rgb_frame = reformatter.reformat(
                frame,
                width=info.analysis_width,
                height=info.analysis_height,
                format="rgb24",
                src_colorspace=info.color.swscale_colorspace,
                src_color_range=info.color.swscale_range,
                dst_color_range="JPEG",
                interpolation=interpolation,
            )
            rgb = rgb_frame.to_ndarray().astype(np.float32) / np.float32(255.0)

            luma_plane = frame.reformat(format="yuv444p").to_ndarray()[0]
            gray = av.VideoFrame.from_ndarray(luma_plane, format="gray")
            gray = gray.reformat(
                width=info.analysis_width,
                height=info.analysis_height,
                interpolation=interpolation,
            )
            level = gray.to_ndarray().astype(np.float32)
            if info.color.color_range == "limited":
                level = (level - np.float32(16.0)) / np.float32(219.0)
            else:
                level = level / np.float32(255.0)
            np.clip(level, 0.0, 1.0, out=level)

            yield AnalysisFrame(index=index, pts_ms=pts_ms, rgb=rgb, video_level=level)
            index += 1
