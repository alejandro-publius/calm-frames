#!/usr/bin/env python3
"""Draw a conformance clip and encode it. Nothing here imports flashmap.

SAFETY, NOT NEGOTIABLE
----------------------
Every clip this module writes is a strobe built on purpose to sit near the flash thresholds.
Some of them are worse than anything we would ever let a player show. They are hazardous by
design, and that is why:

- they are written only under a scratch directory outside the repository, created with owner
  only permissions, with a `HAZARD_` name;
- the job that writes one analyses it and deletes it before moving to the next clip, in a
  `finally` block, so a crash cannot leave one lying around;
- the run asserts at exit that no `HAZARD_` file survived;
- nothing in the pipeline opens, plays, thumbnails or previews one, and neither does a person.
  The only thing that ever looks at these pixels is a decoder.

If you are reading this because you want to eyeball one: do not. Use eval/plots.py on a real
clip instead, which draws a graph and never shows a frame.

Encoding notes
--------------
The frames are drawn in 8 bit sRGB, which is the space the thresholds are written in, and
handed to libx264. The generator records the exact drawn values, so the ground truth is about
what was drawn and not about what was asked for. What comes back out of the decoder is a
slightly different signal, because 4:2:0, limited range and lossy coding all move it, and that
difference is part of what the suite measures rather than something to hide.
"""

from __future__ import annotations

import os
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.geometry import frame_plan, picture_rect, region_rects  # noqa: E402
from conformance.spec import SpecNumbers  # noqa: E402

__all__ = ["render_clip", "decode_mean_luminance", "HAZARD_PREFIX", "scratch_dir"]

HAZARD_PREFIX = "HAZARD_conformance_"

# Color tagging variants. The numbers are the AVColorSpace / AVColorPrimaries /
# AVColorTransferCharacteristic enum values from FFmpeg, not thresholds.
_BT709 = 1
_BT601_SD = 6  # smpte170m, what an untagged SD stream is treated as
_RANGE_JPEG = 2


def scratch_dir() -> Path:
    """Where hazard clips live for the seconds they exist. Never inside the repository."""
    base = os.environ.get("CALM_CONFORMANCE_SCRATCH")
    if not base:
        tmp = os.environ.get("TMPDIR", "/tmp")
        base = str(Path(tmp) / "calm-frames-conformance")
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def state_frames(clip: dict) -> list[np.ndarray]:
    """The two pictures the clip alternates between, as 8 bit RGB."""
    width, height = int(clip["width"]), int(clip["height"])
    picture = picture_rect(width, height, float(clip.get("letterbox_fraction", 0.0)))
    rects = region_rects(picture, str(clip["shape"]), float(clip["area_fraction"]))
    background = tuple(int(v) for v in clip["background_rgb"])

    frames = []
    for key in ("state_a_rgb", "state_b_rgb"):
        color = tuple(int(v) for v in clip[key])
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[picture.y0 : picture.y1, picture.x0 : picture.x1] = background
        for rect in rects:
            frame[rect.y0 : rect.y1, rect.x0 : rect.x1] = color
        frames.append(frame)
    return frames


def render_clip(clip: dict, destination: Path) -> dict:
    """Write one hazard clip. Returns what was encoded, for the record.

    The caller owns the file and must delete it. See the safety note at the top of this file.
    """
    import av

    width, height = int(clip["width"]), int(clip["height"])
    times, states = frame_plan(
        duration_ms=float(clip["duration_ms"]),
        fps=float(clip["fps"]),
        timing=str(clip["timing"]),
        flash_start_ms=float(clip["flash_start_ms"]),
        flash_hz=float(clip["flash_hz"]),
        seed=int(clip.get("seed", 0)),
    )
    frames = state_frames(clip)
    tagging = str(clip.get("color_tagging", "bt709"))
    crf = clip.get("crf", 23)

    container = av.open(str(destination), "w")
    try:
        stream = container.add_stream("libx264", rate=Fraction(int(round(clip["fps"])), 1))
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = Fraction(1, 1000)
        options = {"preset": "veryfast", "x264-params": "scenecut=0:keyint=30"}
        if crf is None:  # lossless reference encode
            options["qp"] = "0"
        else:
            options["crf"] = str(int(crf))
        stream.options = options

        if tagging == "bt709":
            stream.codec_context.color_primaries = _BT709
            stream.codec_context.color_trc = _BT709
            stream.codec_context.colorspace = _BT709
        elif tagging == "untagged_hd":
            pass  # no tags at all, HD sized: flashmap has to guess BT.709
        elif tagging == "untagged_sd":
            pass  # no tags at all, SD sized: flashmap has to guess BT.601
        elif tagging == "full_range":
            stream.codec_context.color_primaries = _BT709
            stream.codec_context.color_trc = _BT709
            stream.codec_context.colorspace = _BT709
            stream.codec_context.color_range = _RANGE_JPEG
        elif tagging == "bt601":
            stream.codec_context.color_primaries = _BT601_SD
            stream.codec_context.color_trc = _BT601_SD
            stream.codec_context.colorspace = _BT601_SD
        else:
            raise ValueError(f"unknown color_tagging {tagging!r}")

        for time_ms, state in zip(times, states):
            frame = av.VideoFrame.from_ndarray(frames[state], format="rgb24")
            frame.pts = int(round(time_ms))
            frame.time_base = Fraction(1, 1000)
            container.mux(stream.encode(frame))
        container.mux(stream.encode(None))
    finally:
        container.close()
    os.chmod(destination, 0o600)

    return {
        "frames_written": len(times),
        "first_pts_ms": times[0] if times else None,
        "last_pts_ms": times[-1] if times else None,
        "bytes": destination.stat().st_size,
    }


def decode_mean_luminance(
    path: Path, spec: SpecNumbers, work_width: int = 96
) -> tuple[list[float], list[float]]:
    """Per frame mean relative luminance of the encoded clip, and the frame times.

    This is the encoding fidelity check of docs/EVAL_PLAN.md section 4: it is how the job finds
    out whether what came back out of the encoder is the waveform it asked for. It decodes to a
    small RGB image, which is an average of the picture and is all a mean needs.

    It does not import flashmap and it is not a detector. It decides nothing about flashing.
    """
    import av

    times: list[float] = []
    means: list[float] = []
    with av.open(str(path)) as container:
        video = container.streams.video[0]
        video.thread_type = "AUTO"
        for frame in container.decode(video):
            if frame.pts is None:
                continue
            array = frame.to_ndarray(format="rgb24", width=work_width, height=max(2, work_width * frame.height // frame.width))
            linear = spec.srgb_to_linear(array.astype(np.float64) / 255.0)
            luminance = spec.relative_luminance(linear)
            times.append(float(frame.pts * frame.time_base * 1000))
            means.append(float(luminance.mean()))
    return times, means
