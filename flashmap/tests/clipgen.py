"""Tiny clip generator for the test suite.

SAFETY. Anything this module makes that flashes is hazardous. Tests generate such a clip,
analyse it and delete it inside the same test, through the `hazard_clip` fixture in conftest.py.
Nobody opens one in a player. Files carry a HAZARD_ prefix so a stray one is obvious.

Clips are deliberately tiny: a few dozen small frames is enough to prove a rule, and the whole
suite has to run on a CI runner.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from av.video.reformatter import VideoReformatter
from numpy.typing import NDArray

# libavutil AVColorSpace and AVColorRange values, see flashmap/docs/SPEC_SOURCES.md section 7.
AVCOL_SPC_UNSPECIFIED = 2
AVCOL_SPC_BT709 = 1
AVCOL_SPC_SMPTE170M = 6
AVCOL_RANGE_UNSPECIFIED = 0
AVCOL_RANGE_MPEG = 1
AVCOL_RANGE_JPEG = 2

_SWS_NAMES = {AVCOL_SPC_BT709: "ITU709", AVCOL_SPC_SMPTE170M: "ITU601"}


def solid(width: int, height: int, rgb: tuple[int, int, int]) -> NDArray[np.uint8]:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = rgb
    return frame


def patch(
    base: NDArray[np.uint8],
    rgb: tuple[int, int, int],
    top: float,
    left: float,
    height: float,
    width: float,
) -> NDArray[np.uint8]:
    """Paint a rectangle given as fractions of the frame. Returns a new array."""
    out = base.copy()
    h, w = out.shape[:2]
    y0 = int(round(top * h))
    x0 = int(round(left * w))
    y1 = min(h, y0 + max(1, int(round(height * h))))
    x1 = min(w, x0 + max(1, int(round(width * w))))
    out[y0:y1, x0:x1] = rgb
    return out


def grating(
    width: int,
    height: int,
    pairs: int,
    dark: tuple[int, int, int],
    bright: tuple[int, int, int],
    *,
    vertical: bool = True,
    area: float = 1.0,
    shift: int = 0,
    invert: bool = False,
) -> NDArray[np.uint8]:
    """A block of `pairs` light and dark stripe pairs, so exactly `2 * pairs` bars.

    The block covers `area` of the frame along the striped axis and the whole of the other
    axis. `shift` slides the whole block, for drift clips, and `invert` swaps light for dark,
    for contrast reversal clips. Bar widths are whole pixels and equal, so the bar count a
    detector should find is not a matter of opinion.
    """
    if pairs < 1:
        raise ValueError("a grating needs at least one pair")
    frame = solid(width, height, dark)
    extent = width if vertical else height
    span = int(round(extent * area))
    span -= span % (2 * pairs)
    if span < 2 * pairs:
        raise ValueError("the frame is too small for that many bars")
    bar = span // (2 * pairs)
    start = (extent - span) // 2 + shift
    for index in range(2 * pairs):
        if (index % 2 == 0) == invert:
            continue
        low = max(0, min(extent, start + index * bar))
        high = max(0, min(extent, low + bar))
        if high <= low:
            continue
        if vertical:
            frame[:, low:high] = bright
        else:
            frame[low:high, :] = bright
    return frame


def alternating(
    count: int,
    frame_a: NDArray[np.uint8],
    frame_b: NDArray[np.uint8],
) -> list[NDArray[np.uint8]]:
    """count frames that swap between the two given frames, starting with a."""
    return [frame_a if index % 2 == 0 else frame_b for index in range(count)]


def every_nth(
    count: int,
    quiet: NDArray[np.uint8],
    loud: NDArray[np.uint8],
    period: int,
) -> list[NDArray[np.uint8]]:
    """count frames that are `quiet`, except every `period`-th frame which is `loud`."""
    return [loud if index % period == 0 else quiet for index in range(count)]


def write_clip(
    path: str | Path,
    frames: Sequence[NDArray[np.uint8]],
    *,
    fps: float = 20.0,
    timestamps_ms: Sequence[float] | None = None,
    codec: str = "ffv1",
    pix_fmt: str = "yuv444p",
    colorspace: int = AVCOL_SPC_BT709,
    color_range: int = AVCOL_RANGE_MPEG,
    tag_colorspace: bool = True,
    tag_range: bool = True,
) -> Path:
    """Encode RGB frames to a file, in full control of the colour tags and the timestamps.

    `colorspace` and `color_range` say how the RGB is converted to YCbCr. `tag_colorspace` and
    `tag_range` say whether the file admits it. Turning both off makes an untagged file, which
    is what the colour inference tests need.
    """
    path = Path(path)
    height, width = frames[0].shape[:2]
    container = av.open(str(path), mode="w")
    stream = container.add_stream(codec, rate=Fraction(1000, 1))
    stream.width = width
    stream.height = height
    stream.pix_fmt = pix_fmt
    stream.time_base = Fraction(1, 1000)
    codec_context = stream.codec_context
    codec_context.time_base = Fraction(1, 1000)
    if tag_colorspace:
        codec_context.colorspace = colorspace
    else:
        codec_context.colorspace = AVCOL_SPC_UNSPECIFIED
    if tag_range:
        codec_context.color_range = color_range
    else:
        codec_context.color_range = AVCOL_RANGE_UNSPECIFIED

    reformatter = VideoReformatter()
    stamps = (
        list(timestamps_ms)
        if timestamps_ms is not None
        else [index * 1000.0 / fps for index in range(len(frames))]
    )
    if len(stamps) != len(frames):
        raise ValueError("timestamps_ms must have one entry per frame")

    for array, stamp in zip(frames, stamps, strict=True):
        source = av.VideoFrame.from_ndarray(np.ascontiguousarray(array), format="rgb24")
        converted = reformatter.reformat(
            source,
            format=pix_fmt,
            src_color_range="JPEG",
            dst_colorspace=_SWS_NAMES.get(colorspace, "ITU709"),
            dst_color_range="JPEG" if color_range == AVCOL_RANGE_JPEG else "MPEG",
        )
        converted.pts = int(round(stamp))
        converted.time_base = Fraction(1, 1000)
        for packet in stream.encode(converted):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    return path
