#!/usr/bin/env python3
"""The camera meter: WCAG flash counting on a filmed TV screen.

What it is for
--------------
Two jobs, one instrument:

1. the meter that sits beside the TV in the demo video, reading the screen through a phone
   camera and showing flashes per second and a running leak count;
2. the tool that turns the 200-event screen-level recordings into numbers, through
   `eval/meter_ingest.py`.

It takes a recording of a TV (or a live camera feed), finds the screen region, corrects the
camera's exposure against a step-chart calibration filmed on the same screen, and counts
WCAG 2.2 SC 2.3.1 general flashes and red flashes inside that region, in a trailing one second
window.

What it measures, and what it does not
--------------------------------------
It measures the light that came off the panel and reached the camera, as the camera recorded it.
That is the point: it is the only view of the system that includes the TV, the compositor and
the panel. It is not a second opinion on a file. Pointed at a file, flashmap is the better tool,
because it reads the pixels the decoder produced instead of a photograph of them.

Two limits that a reader has to know:

- **Luminance is calibrated end to end, colour is not.** The step chart is neutral gray, so the
  fit corrects each channel's gain and black level but cannot undo the camera's colour matrix.
  Red flash counts from camera footage are therefore an indication, not a calibrated
  measurement, and every report says so in `quality.warnings`.
- **The camera is a sampler.** A camera at 60 fps cannot see a fast strobe faithfully, and
  neither can this meter through it. `results/meter_validation.json` records where 60 fps starts
  to under-count on simulated footage.

Independence
------------
This module must not import flashmap, directly or through anything it imports. The meter is how
we check whether the thing flashmap protects actually stayed covered on a real screen, and a
check that shares code with the thing it checks is not a check. Thresholds are read at run time
out of the quoted spec text through `eval/conformance/spec.py`, which has the same rule, so no
number is restated here. `eval/tests/test_meter_guards.py` enforces both.

Safety
------
Nothing here opens a player, a preview or a thumbnail. It decodes, it counts, and it can draw a
plot. Hazard footage is inspected as plots only, which is what `plot` writes.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

_EVAL_DIR = Path(__file__).resolve().parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.spec import SpecNumbers, load_spec  # noqa: E402

__all__ = [
    "METER_VERSION",
    "InstrumentSettings",
    "Roi",
    "Calibration",
    "Meter",
    "MeterReport",
    "find_roi",
    "calibrate",
    "step_chart_image",
    "step_chart_luminances",
    "decode_frames",
    "run_file",
    "CalibrationError",
    "RoiError",
]

METER_VERSION = "1.0.0"


class CalibrationError(RuntimeError):
    """The step chart take cannot support a calibration. No numbers come out of this take."""


class RoiError(RuntimeError):
    """No plausible screen was found in the recording."""


# ----------------------------------------------------------------- instrument settings


@dataclass(frozen=True)
class InstrumentSettings:
    """Tuning of this instrument. **None of these is a threshold from a spec.**

    Every flash threshold comes from the quoted spec text through `conformance.spec`. The numbers
    below are choices about how the camera is read: how big the working grid is, how much of a
    patch is measured, when a calibration is too poor to trust. They are written into every
    report so a reader can see what the instrument was set to.
    """

    working_width: int = 480
    """Decode width for finding the screen. Camera frames are scaled to this before anything."""

    analysis_width: int = 96
    """Width of the grid the flash counters run on, inside the screen region."""

    roi_sample_frames: int = 40
    """How many frames are sampled to find the screen."""

    roi_trim_percentile: float = 1.0
    """The screen rectangle spans this percentile to its complement of the lit pixels."""

    roi_inset_fraction: float = 0.02
    """Trimmed from each side of the found rectangle, to stay off the bezel and its glow."""

    roi_min_area_fraction: float = 0.02
    """Below this share of the camera frame, the found rectangle is not a TV."""

    roi_max_area_fraction: float = 0.90
    """Above this share, there is no room left around the TV to tell a screen from a wall."""

    chart_margin_fraction: float = 0.10
    """The step chart's border, as a share of the screen. Patches fill what is left."""

    patch_measure_fraction: float = 0.5
    """The central share of each patch that is measured, so edges and ringing are left out."""

    clip_high_code: int = 250
    """A channel at or above this 8 bit value is treated as clipped and left out of the fit."""

    clip_low_code: int = 3
    """A channel at or below this 8 bit value is treated as crushed and left out of the fit."""

    min_usable_patches: int = 4
    """Fewer usable patches than this and the calibration is refused."""

    max_calibration_residual: float = 0.05
    """Worst patch error the fit may leave, in relative luminance. Above it, refused."""

    max_clipped_frame_fraction: float = 0.02
    """Above this share of clipped pixels in the screen region, the run is flagged."""

    leak_hold_ms: float = 1000.0
    """A leak event stays open until the count has been at or below the limit for this long."""

    def as_dict(self) -> dict[str, object]:
        out = dataclasses.asdict(self)
        out["note"] = (
            "Instrument tuning, not thresholds. Every flash threshold comes from "
            "flashmap/docs/SPEC_SOURCES.md through eval/conformance/spec.py."
        )
        return out


# ----------------------------------------------------------------- colour arithmetic


def _linear_from_srgb8(spec: SpecNumbers, rgb8: NDArray[np.floating]) -> NDArray[np.float64]:
    """8 bit encoded values to linear light, with the transfer function read from the spec."""
    return spec.srgb_to_linear(np.asarray(rgb8, dtype=np.float64) / 255.0)


def _luminance(spec: SpecNumbers, linear_rgb: NDArray[np.floating]) -> NDArray[np.float64]:
    weights = np.asarray(spec.luma_weights, dtype=np.float64)
    return np.asarray(linear_rgb, dtype=np.float64) @ weights


def _ucs_and_red_ratio(
    spec: SpecNumbers, linear_rgb: NDArray[np.floating]
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """u', v' and R/(R + G + B) for a whole frame at once.

    `SpecNumbers.ucs` takes one colour. This is the same arithmetic over an image, using the
    matrix and the two UCS formulas parsed out of the spec file rather than any number typed
    here.
    """
    linear = np.asarray(linear_rgb, dtype=np.float64)
    matrix = np.asarray(spec.xyz_matrix, dtype=np.float64)
    xyz = linear @ matrix.T
    a, b, c = spec.ucs_denominator
    denominator = a * xyz[..., 0] + b * xyz[..., 1] + c * xyz[..., 2]
    safe = np.where(denominator == 0, 1.0, denominator)
    u_prime = np.where(denominator == 0, 0.0, spec.ucs_u_numerator * xyz[..., 0] / safe)
    v_prime = np.where(denominator == 0, 0.0, spec.ucs_v_numerator * xyz[..., 1] / safe)
    total = linear.sum(axis=-1)
    red_ratio = np.where(total <= 0, 0.0, linear[..., 0] / np.where(total <= 0, 1.0, total))
    return u_prime, v_prime, red_ratio


# ----------------------------------------------------------------- the step chart


def step_chart_codes(steps: int = 10) -> list[int]:
    """The 8 bit gray levels on the chart, evenly spaced from black to white."""
    if steps < 2:
        raise ValueError("a step chart needs at least two steps")
    return [int(round(v)) for v in np.linspace(0.0, 255.0, steps)]


def step_chart_luminances(spec: SpecNumbers, steps: int = 10) -> list[float]:
    """What each patch is worth in relative luminance, by the spec's own definition."""
    return [
        float(_luminance(spec, _linear_from_srgb8(spec, np.array([c, c, c], dtype=np.float64))))
        for c in step_chart_codes(steps)
    ]


def step_chart_image(
    width: int = 1920,
    height: int = 1080,
    steps: int = 10,
    settings: InstrumentSettings | None = None,
) -> NDArray[np.uint8]:
    """The chart to put on the TV: a row of gray patches inside a mid gray border.

    The border is mid gray rather than black so that a camera set for the chart is not set for a
    black field, and so the chart's own edges are visible in the recording.
    """
    settings = settings or InstrumentSettings()
    codes = step_chart_codes(steps)
    image = np.full((height, width, 3), 128, dtype=np.uint8)
    margin_x = int(round(width * settings.chart_margin_fraction))
    margin_y = int(round(height * settings.chart_margin_fraction))
    inner_w = width - 2 * margin_x
    inner_h = height - 2 * margin_y
    for index, code in enumerate(codes):
        x0 = margin_x + int(round(inner_w * index / len(codes)))
        x1 = margin_x + int(round(inner_w * (index + 1) / len(codes)))
        image[margin_y : margin_y + inner_h, x0:x1] = code
    return image


def gray_field_image(
    width: int = 1920, height: int = 1080, code: int = 128
) -> NDArray[np.uint8]:
    """A flat field, for the region and the flicker check. Mid gray by default."""
    return np.full((height, width, 3), int(code), dtype=np.uint8)


def write_still_video(
    image: NDArray[np.uint8], path: Path, seconds: float = 10.0, fps: int = 30
) -> Path:
    """Hold one picture as a short clip, for a TV that would rather play than browse.

    The chart and the gray field are both still pictures, so this is never hazardous. It exists
    because the surest way to fill a TV screen with an exact picture is to play it: a photo
    viewer may scale, letterbox or sharpen, and the calibration would be measuring that instead
    of the panel.
    """
    import av

    from fractions import Fraction

    count = max(1, int(round(seconds * fps)))
    array = np.ascontiguousarray(image)
    container = av.open(str(path), "w")
    try:
        stream = container.add_stream("libx264", rate=Fraction(fps, 1))
        stream.width = array.shape[1]
        stream.height = array.shape[0]
        stream.pix_fmt = "yuv420p"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = Fraction(1, 1000)
        stream.codec_context.color_primaries = 1
        stream.codec_context.color_trc = 1
        stream.codec_context.colorspace = 1
        stream.options = {
            "preset": "veryfast",
            "crf": "14",
            "x264-params": "scenecut=0:keyint=30",
        }
        for index in range(count):
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            frame.pts = int(round(index * 1000.0 / fps))
            frame.time_base = Fraction(1, 1000)
            container.mux(stream.encode(frame))
        container.mux(stream.encode(None))
    finally:
        container.close()
    return path


def _patch_boxes(
    roi_height: int, roi_width: int, steps: int, settings: InstrumentSettings
) -> list[tuple[int, int, int, int]]:
    """The measured box of every patch, in screen region pixels, as (y0, y1, x0, x1)."""
    margin_x = roi_width * settings.chart_margin_fraction
    margin_y = roi_height * settings.chart_margin_fraction
    inner_w = roi_width - 2 * margin_x
    inner_h = roi_height - 2 * margin_y
    keep = settings.patch_measure_fraction
    boxes = []
    for index in range(steps):
        x0 = margin_x + inner_w * index / steps
        x1 = margin_x + inner_w * (index + 1) / steps
        cx, half_w = (x0 + x1) / 2.0, (x1 - x0) * keep / 2.0
        cy, half_h = margin_y + inner_h / 2.0, inner_h * keep / 2.0
        boxes.append(
            (
                max(0, int(round(cy - half_h))),
                min(roi_height, max(1, int(round(cy + half_h)))),
                max(0, int(round(cx - half_w))),
                min(roi_width, max(1, int(round(cx + half_w)))),
            )
        )
    return boxes


# ----------------------------------------------------------------- the screen region


@dataclass(frozen=True)
class Roi:
    """The screen region, stored as fractions of the frame so it survives a rescale."""

    x0: float
    y0: float
    x1: float
    y1: float
    method: str
    detail: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= self.x0 < self.x1 <= 1.0 and 0.0 <= self.y0 < self.y1 <= 1.0):
            raise RoiError(f"nonsense region {self.as_dict()}")

    def pixels(self, height: int, width: int) -> tuple[int, int, int, int]:
        """(y0, y1, x0, x1) in whole pixels, always at least one pixel across."""
        y0 = int(math.floor(self.y0 * height))
        y1 = max(y0 + 1, int(math.ceil(self.y1 * height)))
        x0 = int(math.floor(self.x0 * width))
        x1 = max(x0 + 1, int(math.ceil(self.x1 * width)))
        return y0, min(height, y1), x0, min(width, x1)

    def crop(self, frame: NDArray[np.uint8]) -> NDArray[np.uint8]:
        y0, y1, x0, x1 = self.pixels(frame.shape[0], frame.shape[1])
        return frame[y0:y1, x0:x1]

    def as_dict(self) -> dict[str, object]:
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "method": self.method,
            **self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Roi":
        detail = {
            k: v for k, v in data.items() if k not in {"x0", "y0", "x1", "y1", "method"}
        }
        return cls(
            x0=float(data["x0"]),
            y0=float(data["y0"]),
            x1=float(data["x1"]),
            y1=float(data["y1"]),
            method=str(data.get("method", "from-file")),
            detail=detail,
        )

    @classmethod
    def from_spec_string(cls, text: str) -> "Roi":
        """`x0,y0,x1,y1` as fractions, the way a person types it on the command line."""
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 4:
            raise RoiError(f"expected x0,y0,x1,y1 as fractions, got {text!r}")
        values = [float(p) for p in parts]
        return cls(*values, method="explicit")  # type: ignore[arg-type]


def _otsu_threshold(values: NDArray[np.floating], bins: int = 256) -> float:
    """Otsu's split of a one dimensional histogram. A standard method, not a tuned number."""
    flat = np.asarray(values, dtype=np.float64).ravel()
    low, high = float(flat.min()), float(flat.max())
    if high <= low:
        return high
    counts, edges = np.histogram(flat, bins=bins, range=(low, high))
    centres = (edges[:-1] + edges[1:]) / 2.0
    weights = counts.astype(np.float64)
    total = weights.sum()
    if total <= 0:
        return high
    w0 = np.cumsum(weights)
    w1 = total - w0
    sum0 = np.cumsum(weights * centres)
    sum_total = sum0[-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        mean0 = np.where(w0 > 0, sum0 / np.where(w0 > 0, w0, 1.0), 0.0)
        mean1 = np.where(w1 > 0, (sum_total - sum0) / np.where(w1 > 0, w1, 1.0), 0.0)
        between = w0 * w1 * (mean0 - mean1) ** 2
    return float(centres[int(np.argmax(between))])


def find_roi(
    frames: Sequence[NDArray[np.uint8]], settings: InstrumentSettings | None = None
) -> Roi:
    """Find the TV screen in a handful of camera frames.

    The screen is the bright, and usually busy, rectangle in a darker room. The score is half
    mean brightness and half how much each pixel moves over the sampled frames, so that a take
    where the screen holds still (a cover, a gray field) is still found by brightness alone.
    Otsu's method splits the score into lit and unlit, and the rectangle is the bounding box of
    the lit pixels with `roi_trim_percentile` trimmed off each edge, so a lamp or a standby LED
    cannot drag a corner out.

    The bounding box is used rather than a run of bright rows and columns because a screen is
    often only partly lit. A step chart is black at one end, and a rule that wanted every column
    bright would hand back the white half of the chart and call it the TV. That is not a
    hypothetical: it is what the first version of this function did.

    Best practice is not to rely on this at all on the night. Film the gray field first, as
    docs/SCREEN_TEST_PROTOCOL.md says, take the region from that take, and pass it to the rest
    with --roi. A uniform gray screen is the easiest thing in the world to find.

    Raises RoiError rather than returning a guess.
    """
    settings = settings or InstrumentSettings()
    if not len(frames):
        raise RoiError("no frames to look at")
    stack = np.stack(
        [np.asarray(f, dtype=np.float32).mean(axis=2) / 255.0 for f in frames], axis=0
    )
    brightness = stack.mean(axis=0)
    movement = stack.std(axis=0)

    def normalise(image: NDArray[np.floating]) -> NDArray[np.float64]:
        lo, hi = float(image.min()), float(image.max())
        if hi <= lo:
            return np.zeros_like(image, dtype=np.float64)
        return (np.asarray(image, dtype=np.float64) - lo) / (hi - lo)

    if float(brightness.max() - brightness.min()) <= 0 and float(movement.max()) <= 0:
        raise RoiError(
            "every pixel in the frame is the same and none of them moves, so there is no screen "
            "to find. Point the camera at the TV, or pass --roi."
        )

    score = 0.5 * normalise(brightness) + 0.5 * normalise(movement)
    threshold = _otsu_threshold(score)
    mask = score >= threshold
    if not mask.any():
        raise RoiError("nothing in the frame separated from the background")

    lit_rows, lit_cols = np.nonzero(mask)
    trim = settings.roi_trim_percentile
    row_lo, row_hi = np.percentile(lit_rows, [trim, 100.0 - trim])
    col_lo, col_hi = np.percentile(lit_cols, [trim, 100.0 - trim])
    row_run = (int(math.floor(row_lo)), int(math.ceil(row_hi)) + 1)
    col_run = (int(math.floor(col_lo)), int(math.ceil(col_hi)) + 1)
    if row_run[1] <= row_run[0] + 1 or col_run[1] <= col_run[0] + 1:
        raise RoiError("the lit pixels do not make a rectangle big enough to be a screen")

    height, width = score.shape
    row_run = (row_run[0], min(height, row_run[1]))
    col_run = (col_run[0], min(width, col_run[1]))
    y0, y1 = row_run[0] / height, row_run[1] / height
    x0, x1 = col_run[0] / width, col_run[1] / width

    # Both area checks are asked of the lit rectangle, before the bezel inset comes off it. The
    # question is whether this thing can be a TV, and the inset is a measuring margin, not part
    # of the screen. Asking after the inset put the ceiling out of reach: a rectangle covering
    # the entire frame came out at 0.895 once trimmed, under a ceiling of 0.90, so the guard
    # could never fire. The mutation run found that, and this is the fix.
    area_fraction = (y1 - y0) * (x1 - x0)
    if area_fraction < settings.roi_min_area_fraction:
        raise RoiError(
            f"the brightest rectangle covers {area_fraction:.4f} of the frame, under the "
            f"{settings.roi_min_area_fraction} a TV has to fill. Film closer, or pass --roi."
        )
    if area_fraction > settings.roi_max_area_fraction:
        raise RoiError(
            f"the lit rectangle covers {area_fraction:.4f} of the frame, over the "
            f"{settings.roi_max_area_fraction} this can check. With no room visible around the "
            "TV there is nothing to tell a screen from a wall. Step back, or pass --roi."
        )

    inset = settings.roi_inset_fraction
    dy, dx = (y1 - y0) * inset, (x1 - x0) * inset
    y0, y1, x0, x1 = y0 + dy, y1 - dy, x0 + dx, x1 - dx
    if y1 <= y0 or x1 <= x0:
        raise RoiError("the found rectangle vanished once the bezel inset was taken off")

    inside = mask[row_run[0] : row_run[1], col_run[0] : col_run[1]].mean()
    outside_count = mask.sum() - mask[row_run[0] : row_run[1], col_run[0] : col_run[1]].sum()
    outside_pixels = mask.size - (row_run[1] - row_run[0]) * (col_run[1] - col_run[0])
    outside = float(outside_count) / outside_pixels if outside_pixels else 0.0
    if inside <= outside:
        raise RoiError(
            "the rectangle is no brighter or busier than the rest of the frame, so it is not a "
            "screen"
        )
    return Roi(
        x0=float(x0),
        y0=float(y0),
        x1=float(x1),
        y1=float(y1),
        method="otsu-profile",
        detail={
            "frames_sampled": int(stack.shape[0]),
            "fill_inside": float(inside),
            "fill_outside": float(outside),
            "area_fraction_of_frame": float(area_fraction),
            "inset_fraction": float(inset),
            "trim_percentile": float(settings.roi_trim_percentile),
        },
    )


# ----------------------------------------------------------------- calibration


@dataclass(frozen=True)
class Calibration:
    """Camera readings to display relative luminance, fitted on a filmed step chart.

    The fit is affine per channel in linear light: `display = gain * camera_linear + offset`.
    Gain absorbs the exposure and the channel's white balance, offset absorbs lens flare and the
    black level. Anything the TV or the camera does that is not affine is left in the residual,
    which is reported and which is where the tolerance for a covered screen comes from.
    """

    gain: tuple[float, float, float]
    offset: tuple[float, float, float]
    max_residual: float
    rms_residual: float
    r_squared: float
    usable_patches: int
    patches: list[dict[str, object]]
    steps: int
    saturation_luminance: float | None
    spec_sha256: str

    def apply(self, rgb8: NDArray[np.floating]) -> NDArray[np.float64]:
        """Camera 8 bit RGB to estimated display linear RGB, clamped at zero."""
        spec = load_spec()
        camera_linear = _linear_from_srgb8(spec, rgb8)
        gain = np.asarray(self.gain, dtype=np.float64)
        offset = np.asarray(self.offset, dtype=np.float64)
        return np.maximum(camera_linear * gain + offset, 0.0)

    def as_dict(self) -> dict[str, object]:
        return {
            "gain": list(self.gain),
            "offset": list(self.offset),
            "max_residual_relative_luminance": self.max_residual,
            "rms_residual_relative_luminance": self.rms_residual,
            "r_squared": self.r_squared,
            "usable_patches": self.usable_patches,
            "steps": self.steps,
            "saturation_luminance": self.saturation_luminance,
            "spec_sha256": self.spec_sha256,
            "patches": self.patches,
            "model": "per channel affine in linear light: display = gain * camera + offset",
            "colour_note": (
                "The chart is neutral gray, so this fit corrects luminance and per channel "
                "gain. It cannot correct the camera's colour matrix, so red flash counts from "
                "camera footage are an indication and not a calibrated measurement."
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Calibration":
        return cls(
            gain=tuple(float(v) for v in data["gain"]),  # type: ignore[arg-type]
            offset=tuple(float(v) for v in data["offset"]),  # type: ignore[arg-type]
            max_residual=float(data["max_residual_relative_luminance"]),
            rms_residual=float(data["rms_residual_relative_luminance"]),
            r_squared=float(data["r_squared"]),
            usable_patches=int(data["usable_patches"]),
            patches=list(data.get("patches", [])),
            steps=int(data.get("steps", 10)),
            saturation_luminance=(
                None
                if data.get("saturation_luminance") is None
                else float(data["saturation_luminance"])
            ),
            spec_sha256=str(data.get("spec_sha256", "")),
        )


def calibrate(
    frames: Sequence[NDArray[np.uint8]],
    roi: Roi,
    *,
    steps: int = 10,
    settings: InstrumentSettings | None = None,
    spec: SpecNumbers | None = None,
) -> Calibration:
    """Fit the camera to the step chart it is looking at.

    `frames` are camera frames of the TV showing `step_chart_image`. They are averaged first,
    because a still chart only has to be read once and averaging takes the noise out.

    Refuses, loudly, when the take cannot support a calibration: too few patches left after
    clipping, a non monotone chart (the chart is not framed the way it was drawn), or a residual
    over the tolerance (the TV or the camera is doing something an affine fit cannot follow).
    """
    settings = settings or InstrumentSettings()
    spec = spec or load_spec()
    if not len(frames):
        raise CalibrationError("no frames of the chart")

    mean_frame = np.mean(
        np.stack([np.asarray(f, dtype=np.float64) for f in frames], axis=0), axis=0
    )
    crop = roi.crop(mean_frame.astype(np.float64))
    if crop.shape[0] < 4 or crop.shape[1] < steps:
        raise CalibrationError(
            f"the screen region is {crop.shape[1]} by {crop.shape[0]} pixels, too small to read "
            f"{steps} patches"
        )

    codes = step_chart_codes(steps)
    targets = step_chart_luminances(spec, steps)
    boxes = _patch_boxes(crop.shape[0], crop.shape[1], steps, settings)

    rows: list[dict[str, object]] = []
    for index, (box, code, target) in enumerate(zip(boxes, codes, targets)):
        y0, y1, x0, x1 = box
        patch = crop[y0:y1, x0:x1]
        mean_rgb = patch.reshape(-1, 3).mean(axis=0)
        clipped = bool(
            (mean_rgb >= settings.clip_high_code).any()
            or (mean_rgb <= settings.clip_low_code).any()
        )
        rows.append(
            {
                "index": index,
                "code": code,
                "target_relative_luminance": target,
                "camera_rgb8": [float(v) for v in mean_rgb],
                "usable": not clipped,
                "clipped": clipped,
            }
        )

    measured = np.array([r["camera_rgb8"] for r in rows], dtype=np.float64)
    measured_grey = measured.mean(axis=1)
    usable = np.array([bool(r["usable"]) for r in rows])

    # Clipping is judged first. A chart filmed a stop too bright has several patches pinned at
    # white, which is not the same complaint as a chart read in the wrong place, and the operator
    # needs to be told the right one.
    if usable.sum() < settings.min_usable_patches:
        raise CalibrationError(
            f"{int(usable.sum())} patches survived clipping, and the fit needs "
            f"{settings.min_usable_patches}. Re-film with a different exposure."
        )
    if np.any(np.diff(measured_grey[usable]) <= 0):
        raise CalibrationError(
            "the patches do not get brighter from left to right: "
            f"{[round(v, 1) for v in measured_grey[usable]]}. The chart is not framed the way it "
            "was drawn, or the screen region is wrong."
        )

    camera_linear = _linear_from_srgb8(spec, measured)
    target_array = np.array(targets, dtype=np.float64)
    gains: list[float] = []
    offsets: list[float] = []
    for channel in range(3):
        x = camera_linear[usable, channel]
        y = target_array[usable]
        design = np.stack([x, np.ones_like(x)], axis=1)
        solution, *_ = np.linalg.lstsq(design, y, rcond=None)
        gains.append(float(solution[0]))
        offsets.append(float(solution[1]))

    fitted_linear = camera_linear * np.asarray(gains) + np.asarray(offsets)
    fitted_luminance = _luminance(spec, np.maximum(fitted_linear, 0.0))
    residuals = fitted_luminance - target_array
    used_residuals = residuals[usable]
    max_residual = float(np.abs(used_residuals).max())
    rms_residual = float(np.sqrt((used_residuals**2).mean()))
    spread = target_array[usable] - target_array[usable].mean()
    denominator = float((spread**2).sum())
    r_squared = (
        1.0 - float((used_residuals**2).sum()) / denominator if denominator > 0 else 0.0
    )

    for row, fitted, residual in zip(rows, fitted_luminance, residuals):
        row["fitted_relative_luminance"] = float(fitted)
        row["residual"] = float(residual)

    if max_residual > settings.max_calibration_residual:
        raise CalibrationError(
            f"the worst patch is out by {max_residual:.4f} in relative luminance, over the "
            f"{settings.max_calibration_residual} this instrument allows. Check the TV's picture "
            "mode: contrast enhancement and dynamic backlight both bend this curve."
        )

    clipped_targets = [float(r["target_relative_luminance"]) for r in rows if r["clipped"]]
    saturation = min(clipped_targets) if clipped_targets else None

    return Calibration(
        gain=(gains[0], gains[1], gains[2]),
        offset=(offsets[0], offsets[1], offsets[2]),
        max_residual=max_residual,
        rms_residual=rms_residual,
        r_squared=r_squared,
        usable_patches=int(usable.sum()),
        patches=rows,
        steps=steps,
        saturation_luminance=saturation,
        spec_sha256=spec.source_sha256,
    )


def flicker_check(
    frames: Sequence[NDArray[np.uint8]],
    times_ms: Sequence[float],
    roi: Roi,
    calibration: Calibration | None = None,
    *,
    settings: InstrumentSettings | None = None,
    spec: SpecNumbers | None = None,
) -> dict[str, object]:
    """Film a still gray screen and see whether it is still.

    The protocol asks for this before every run. A backlight that pulses, a TV that is still
    doing motion processing, or a light in the room on a mains cycle all put a ripple on a screen
    that is showing nothing, and every one of them would land on the meter as luminance change it
    has to explain. This reports the ripple and compares it against the tolerance the calibration
    earned, so a take that cannot be trusted is thrown out before it is filmed over.

    It decides nothing on its own. `passes` is the reading; the operator decides.
    """
    settings = settings or InstrumentSettings()
    spec = spec or load_spec()
    if len(frames) < 4:
        raise ValueError("a flicker check needs at least four frames of the gray field")

    series = []
    for frame in frames:
        grid = _downsample(roi.crop(np.asarray(frame)), settings.analysis_width)
        linear = (
            calibration.apply(grid.astype(np.float64))
            if calibration is not None
            else _linear_from_srgb8(spec, grid.astype(np.float64))
        )
        series.append(float(_luminance(spec, linear).mean()))
    values = np.asarray(series, dtype=np.float64)
    swing = float(values.max() - values.min())

    times = np.asarray(times_ms, dtype=np.float64)
    dominant_hz: float | None = None
    dominant_amplitude: float | None = None
    if len(values) >= 8 and times.size == values.size and times[-1] > times[0]:
        step_s = (times[-1] - times[0]) / (len(times) - 1) / 1000.0
        spectrum = np.abs(np.fft.rfft(values - values.mean())) * 2.0 / len(values)
        freqs = np.fft.rfftfreq(len(values), d=step_s)
        peak = int(np.argmax(spectrum[1:]) + 1) if spectrum.size > 1 else 0
        if peak:
            dominant_hz = float(freqs[peak])
            dominant_amplitude = float(spectrum[peak])

    tolerance = (
        calibration.max_residual
        if calibration is not None
        else settings.max_calibration_residual
    )
    return {
        "frames": len(values),
        "mean_relative_luminance": float(values.mean()),
        "peak_to_peak": swing,
        "standard_deviation": float(values.std()),
        "dominant_hz": dominant_hz,
        "dominant_amplitude": dominant_amplitude,
        "tolerance": float(tolerance),
        "tolerance_source": (
            "the worst patch residual of this take's calibration"
            if calibration is not None
            else "the instrument's calibration tolerance, because this check had no calibration"
        ),
        "passes": bool(swing <= tolerance),
        "statement": (
            "Ripple on a still gray screen, measured in relative luminance on the screen region. "
            "A take that fails this is excluded, per docs/EVAL_PLAN.md section 9."
        ),
    }


# ----------------------------------------------------------------- flash counters


class GeneralFlashCounter:
    """WCAG general flashes, one state machine per pixel.

    From the quoted definition: a general flash is a pair of opposing changes in relative
    luminance of at least `min_delta` of the maximum, where the darker image is below
    `dark_image_below`. Two readings the spec leaves open are taken the way
    flashmap/docs/SPEC_SOURCES.md writes them up:

    - a transition is declared on the first frame where the swing away from the last confirmed
      level is big enough, because a causal meter cannot wait to find out that a peak was a peak;
    - transitions pair without overlapping, so a square wave at 5 Hz is 5 flashes a second.

    **One reading is this meter's own, and it is there because of the camera.** A run of
    transitions in the same direction counts once for pairing, because WCAG measures between
    *adjacent peaks and valleys* and a run in one direction is one journey from a valley to a
    peak. On a file that changes on a frame boundary the rule never fires. On camera footage it
    fires constantly: an exposure window that straddles an edge records a middle value, so one
    edge on the TV arrives as two steps at the camera, and pairing them as written would report a
    6 Hz strobe as 12 flashes a second. It did, before this rule was added: see
    results/meter_validation.json, `known_issues`. Collapsing a run can only ever remove a
    duplicate, never an opposing pair, so it cannot hide a flash.

    The code is this module's own. Sharing an implementation with the analyser under test is
    exactly what the meter exists to avoid.
    """

    def __init__(self, min_delta: float, dark_image_below: float) -> None:
        self.min_delta = float(min_delta)
        self.dark_image_below = float(dark_image_below)
        self._anchor: NDArray[np.float64] | None = None
        self._peak: NDArray[np.float64] | None = None
        self._trend: NDArray[np.int8] | None = None
        self._pending: NDArray[np.bool_] | None = None
        self._last_direction: NDArray[np.int8] | None = None

    def step(self, luminance: NDArray[np.floating]) -> NDArray[np.bool_]:
        values = np.asarray(luminance, dtype=np.float64)
        if self._anchor is None:
            self._anchor = values.copy()
            self._peak = values.copy()
            self._trend = np.zeros(values.shape, dtype=np.int8)
            self._pending = np.zeros(values.shape, dtype=bool)
            self._last_direction = np.zeros(values.shape, dtype=np.int8)
            return np.zeros(values.shape, dtype=bool)

        anchor, peak = self._anchor, self._peak
        trend, pending, last_direction = self._trend, self._pending, self._last_direction
        assert peak is not None and trend is not None and pending is not None
        assert last_direction is not None

        # A swing that turned back before it was big enough still marks a peak or a valley.
        # Start measuring the next swing from there, or the meter keeps facing the wrong way.
        turned = ((trend > 0) & (values < peak)) | ((trend < 0) & (values > peak))
        anchor = np.where(turned, peak, anchor)
        trend = np.where(turned, np.int8(0), trend).astype(np.int8)

        fresh = trend == 0
        trend = np.where(
            fresh & (values > anchor),
            np.int8(1),
            np.where(fresh & (values < anchor), np.int8(-1), trend),
        ).astype(np.int8)
        peak = np.where(fresh, values, peak)
        peak = np.where(trend > 0, np.maximum(peak, values), peak)
        peak = np.where(trend < 0, np.minimum(peak, values), peak)

        swing = peak - anchor
        darker = np.minimum(anchor, peak)
        confirmed = (np.abs(swing) >= self.min_delta) & (darker < self.dark_image_below)
        direction = np.where(swing > 0, np.int8(1), np.int8(-1)).astype(np.int8)

        # A confirmed step that carries on in the same direction as the last one is the same
        # journey between a valley and a peak, seen a second time because the camera caught the
        # middle of it. It moves the anchor but it is not a new transition.
        turning = confirmed & (direction != last_direction)
        flashed = turning & pending
        pending = np.where(flashed, False, np.where(turning, True, pending))
        last_direction = np.where(turning, direction, last_direction).astype(np.int8)
        anchor = np.where(confirmed, peak, anchor)
        trend = np.where(confirmed, np.int8(0), trend).astype(np.int8)

        self._anchor, self._peak, self._trend, self._pending = anchor, peak, trend, pending
        self._last_direction = last_direction
        return flashed


class RedFlashCounter:
    """WCAG red flashes, one state machine per pixel.

    A pixel is in the saturated red state when R/(R + G + B) is at or above the ratio. A
    transition is a move into or out of that state that also moves further than the minimum
    distance in the CIE 1976 UCS diagram. Entering and leaving are the opposing pair, which is
    the reading written up in flashmap/docs/SPEC_SOURCES.md.
    """

    def __init__(self, saturated_ratio: float, min_distance: float) -> None:
        self.saturated_ratio = float(saturated_ratio)
        self.min_distance = float(min_distance)
        self._u: NDArray[np.float64] | None = None
        self._v: NDArray[np.float64] | None = None
        self._red: NDArray[np.bool_] | None = None
        self._pending: NDArray[np.int8] | None = None

    def step(
        self,
        u_prime: NDArray[np.floating],
        v_prime: NDArray[np.floating],
        red_ratio: NDArray[np.floating],
    ) -> NDArray[np.bool_]:
        u = np.asarray(u_prime, dtype=np.float64)
        v = np.asarray(v_prime, dtype=np.float64)
        red = np.asarray(red_ratio, dtype=np.float64) >= self.saturated_ratio
        if self._u is None:
            self._u, self._v, self._red = u.copy(), v.copy(), red.copy()
            self._pending = np.zeros(u.shape, dtype=np.int8)
            return np.zeros(u.shape, dtype=bool)

        anchor_u, anchor_v, anchor_red = self._u, self._v, self._red
        pending = self._pending
        assert anchor_v is not None and anchor_red is not None and pending is not None

        distance = np.hypot(u - anchor_u, v - anchor_v)
        confirmed = (red != anchor_red) & (distance > self.min_distance)
        direction = np.where(red, np.int8(1), np.int8(-1)).astype(np.int8)

        flashed = confirmed & (pending != 0) & (pending != direction)
        pending = np.where(
            flashed, np.int8(0), np.where(confirmed, direction, pending)
        ).astype(np.int8)
        self._u = np.where(confirmed, u, anchor_u)
        self._v = np.where(confirmed, v, anchor_v)
        self._red = np.where(confirmed, red, anchor_red)
        self._pending = pending
        return flashed


def max_window_coverage(
    mask: NDArray[np.bool_], window_height: int, window_width: int
) -> float:
    """The largest share of any window of this size that the mask fills.

    WCAG asks about *any* 10 degree visual field, so the window is slid over every position and
    the busiest one wins. A window larger than the region is clipped to it: a small screen cannot
    show more than a screenful.
    """
    array = np.asarray(mask, dtype=np.float64)
    height, width = array.shape
    win_h = max(1, min(int(window_height), height))
    win_w = max(1, min(int(window_width), width))
    integral = np.zeros((height + 1, width + 1), dtype=np.float64)
    integral[1:, 1:] = array.cumsum(axis=0).cumsum(axis=1)
    sums = (
        integral[win_h:, win_w:]
        - integral[:-win_h, win_w:]
        - integral[win_h:, :-win_w]
        + integral[:-win_h, :-win_w]
    )
    if sums.size == 0:
        return 0.0
    return float(sums.max()) / float(win_h * win_w)


# ----------------------------------------------------------------- the meter


@dataclass
class FrameReading:
    """What the meter knew at one frame. This is what the display beside the TV shows."""

    time_ms: float
    general_per_second: int
    red_per_second: int
    flashes_per_second: int
    above_limit: bool
    excess_per_second: int
    leaks: int
    mean_luminance: float
    general_area_fraction: float
    red_area_fraction: float
    clipped_fraction: float

    def as_line(self) -> str:
        flag = "ABOVE LIMIT" if self.above_limit else "within limit"
        return (
            f"t={self.time_ms / 1000.0:8.3f}s  flashes/s general {self.general_per_second} "
            f"red {self.red_per_second}  {flag}  leaks {self.leaks}"
        )


@dataclass
class MeterReport:
    """Everything one run of the meter is prepared to say."""

    source: dict[str, object]
    thresholds: dict[str, object]
    roi: dict[str, object]
    calibration: dict[str, object] | None
    instrument: dict[str, object]
    general: dict[str, object]
    red: dict[str, object]
    headline: dict[str, object]
    quality: dict[str, object]
    leak_events: list[dict[str, object]]
    per_second: list[dict[str, object]]
    publishable: bool
    statement: str
    trace: list[dict[str, object]] | None = None

    def as_dict(self) -> dict[str, object]:
        out = dataclasses.asdict(self)
        out["tool"] = "eval/meter.py"
        out["meter_version"] = METER_VERSION
        out["generated_on"] = date.today().isoformat()
        if self.trace is None:
            out.pop("trace")
        return out


class Meter:
    """Feed it camera frames, ask it what it has seen.

    The same object serves the live display and the file run, so the demo meter and the
    screen-level numbers cannot drift apart.
    """

    def __init__(
        self,
        *,
        roi: Roi,
        calibration: Calibration | None = None,
        settings: InstrumentSettings | None = None,
        spec: SpecNumbers | None = None,
    ) -> None:
        self.roi = roi
        self.calibration = calibration
        self.settings = settings or InstrumentSettings()
        self.spec = spec or load_spec()
        self.general_counter = GeneralFlashCounter(
            self.spec.general_min_delta, self.spec.general_dark_image_below
        )
        self.red_counter = RedFlashCounter(
            self.spec.red_saturated_ratio, self.spec.red_min_ucs_distance
        )
        self._general_times: list[float] = []
        self._red_times: list[float] = []
        self.readings: list[FrameReading] = []
        self._leaks = 0
        self._leak_open: dict[str, float] | None = None
        self.leak_events: list[dict[str, object]] = []
        self._clipped_frames = 0
        self._frames = 0
        self._first_time: float | None = None
        self._last_time: float | None = None

    # -- one frame ---------------------------------------------------------------------

    def feed(self, frame_rgb8: NDArray[np.uint8], time_ms: float) -> FrameReading:
        crop = self.roi.crop(np.asarray(frame_rgb8))
        grid = _downsample(crop, self.settings.analysis_width)

        # Clipping is judged on the crop as the decoder handed it over, not on the averaged
        # grid. Averaging a pinned pixel with its neighbours hides it, and a camera that clipped
        # is the one fault that can only make this meter read low.
        clipped = float(
            np.mean(
                (crop >= self.settings.clip_high_code).any(axis=2)
                | (crop <= self.settings.clip_low_code).all(axis=2)
            )
        )
        if clipped > self.settings.max_clipped_frame_fraction:
            self._clipped_frames += 1

        if self.calibration is not None:
            linear = self.calibration.apply(grid.astype(np.float64))
        else:
            linear = _linear_from_srgb8(self.spec, grid.astype(np.float64))
        luminance = _luminance(self.spec, linear)
        u_prime, v_prime, red_ratio = _ucs_and_red_ratio(self.spec, linear)

        general_mask = self.general_counter.step(luminance)
        red_mask = self.red_counter.step(u_prime, v_prime, red_ratio)

        win_h = max(1, int(round(grid.shape[0] * self.spec.field_height_fraction)))
        win_w = max(1, int(round(grid.shape[1] * self.spec.field_width_fraction)))
        general_area = (
            max_window_coverage(general_mask, win_h, win_w) if general_mask.any() else 0.0
        )
        red_area = max_window_coverage(red_mask, win_h, win_w) if red_mask.any() else 0.0

        # Condition 2 of the threshold definition: content passes while the concurrent flashing
        # area is no more than the area limit of a 10 degree field, so a flash counts only once
        # it is over that.
        if general_area > self.spec.area_fraction_limit:
            self._general_times.append(time_ms)
        if red_area > self.spec.area_fraction_limit:
            self._red_times.append(time_ms)

        window = float(self.spec.window_ms)
        general_count = _count_in_window(self._general_times, time_ms, window)
        red_count = _count_in_window(self._red_times, time_ms, window)
        limit = self.spec.flash_limit_per_second
        above = general_count > limit or red_count > limit
        excess = max(0, general_count - limit, red_count - limit)

        self._update_leaks(time_ms, above, general_count, red_count)

        self._frames += 1
        if self._first_time is None:
            self._first_time = time_ms
        self._last_time = time_ms

        reading = FrameReading(
            time_ms=time_ms,
            general_per_second=general_count,
            red_per_second=red_count,
            flashes_per_second=max(general_count, red_count),
            above_limit=above,
            excess_per_second=excess,
            leaks=self._leaks,
            mean_luminance=float(luminance.mean()),
            general_area_fraction=general_area,
            red_area_fraction=red_area,
            clipped_fraction=clipped,
        )
        self.readings.append(reading)
        return reading

    def _update_leaks(
        self, time_ms: float, above: bool, general_count: int, red_count: int
    ) -> None:
        """One strobe is one leak, not one leak per frame of it.

        A leak event opens on the first frame over the limit and stays open until the count has
        been at or below the limit for a whole `leak_hold_ms`, so a strobe that dips for two
        frames does not become two leaks.
        """
        if above:
            if self._leak_open is None:
                self._leaks += 1
                self._leak_open = {
                    "start_ms": time_ms,
                    "peak_general": general_count,
                    "peak_red": red_count,
                }
                self.leak_events.append(self._leak_open)
            else:
                self._leak_open["peak_general"] = max(
                    int(self._leak_open["peak_general"]), general_count
                )
                self._leak_open["peak_red"] = max(
                    int(self._leak_open["peak_red"]), red_count
                )
            self._leak_open["last_above_ms"] = time_ms
        elif self._leak_open is not None:
            last = float(self._leak_open.get("last_above_ms", self._leak_open["start_ms"]))
            if time_ms - last >= self.settings.leak_hold_ms:
                self._leak_open["end_ms"] = last
                self._leak_open = None

    # -- the summary -------------------------------------------------------------------

    @property
    def leaks(self) -> int:
        return self._leaks

    def report(self, source: dict[str, object] | None = None) -> MeterReport:
        if self._leak_open is not None:
            self._leak_open["end_ms"] = self._leak_open.get(
                "last_above_ms", self._leak_open["start_ms"]
            )
            self._leak_open = None

        limit = self.spec.flash_limit_per_second
        general_peak = _peak_in_window(self._general_times, float(self.spec.window_ms))
        red_peak = _peak_in_window(self._red_times, float(self.spec.window_ms))
        frames_above = sum(1 for r in self.readings if r.above_limit)
        duration_ms = (
            (self._last_time - self._first_time)
            if self._first_time is not None and self._last_time is not None
            else 0.0
        )
        fps = (self._frames - 1) / (duration_ms / 1000.0) if duration_ms > 0 else None

        warnings: list[str] = []
        if self.calibration is None:
            warnings.append(
                "no step-chart calibration: luminance is read with the sRGB curve straight off "
                "the camera, so nothing from this run may be published"
            )
        clipped_fraction = self._clipped_frames / self._frames if self._frames else 0.0
        if clipped_fraction > 0:
            warnings.append(
                f"{clipped_fraction:.3f} of frames had more clipped pixels in the screen region "
                f"than the {self.settings.max_clipped_frame_fraction} allowed. A clipped camera "
                "reads bright states low, so this run can only under-count flashes."
            )
        if self._frames and fps is not None and fps < 100:
            warnings.append(
                f"the recording runs at about {fps:.0f} fps. Below roughly 100 fps a camera "
                "under-counts fast strobes; see results/meter_validation.json for where."
            )
        if red_peak > 0 and self.calibration is not None:
            warnings.append(
                "red flashes were counted through a gray-chart calibration, which does not "
                "correct the camera's colour matrix. Treat the red count as an indication."
            )

        publishable = self.calibration is not None and clipped_fraction == 0.0

        return MeterReport(
            source=source or {},
            thresholds=self.spec.as_dict(),
            roi=self.roi.as_dict(),
            calibration=self.calibration.as_dict() if self.calibration else None,
            instrument=self.settings.as_dict(),
            general={
                "flashes": len(self._general_times),
                "peak_per_second": general_peak,
                "over_limit": general_peak > limit,
            },
            red={
                "flashes": len(self._red_times),
                "peak_per_second": red_peak,
                "over_limit": red_peak > limit,
            },
            headline={
                "peak_flashes_per_second": max(general_peak, red_peak),
                "limit_per_second": limit,
                "peak_excess_per_second": max(0, max(general_peak, red_peak) - limit),
                "above_limit": max(general_peak, red_peak) > limit,
                "leaks": self._leaks,
                "frames_above_limit": frames_above,
                "seconds_above_limit": (
                    frames_above / fps if fps else None
                ),
            },
            quality={
                "frames": self._frames,
                "duration_ms": duration_ms,
                "fps_measured": fps,
                "clipped_frame_fraction": clipped_fraction,
                "mean_luminance": (
                    float(np.mean([r.mean_luminance for r in self.readings]))
                    if self.readings
                    else None
                ),
                "warnings": warnings,
            },
            leak_events=[dict(event) for event in self.leak_events],
            per_second=self._per_second(),
            publishable=publishable,
            statement=(
                "Measured through a camera, on the screen region only. Counts are WCAG 2.2 "
                "SC 2.3.1 general and red flashes in a trailing one second window, with "
                "thresholds read from flashmap/docs/SPEC_SOURCES.md at run time."
            ),
        )

    def _per_second(self) -> list[dict[str, object]]:
        """A row per second of recording: the worst the meter saw inside it."""
        if not self.readings:
            return []
        origin = self.readings[0].time_ms
        buckets: dict[int, dict[str, object]] = {}
        for reading in self.readings:
            key = int((reading.time_ms - origin) // 1000.0)
            row = buckets.setdefault(
                key,
                {
                    "second": key,
                    "general_per_second": 0,
                    "red_per_second": 0,
                    "above_limit": False,
                    "frames": 0,
                },
            )
            row["general_per_second"] = max(
                int(row["general_per_second"]), reading.general_per_second
            )
            row["red_per_second"] = max(int(row["red_per_second"]), reading.red_per_second)
            row["above_limit"] = bool(row["above_limit"]) or reading.above_limit
            row["frames"] = int(row["frames"]) + 1
        return [buckets[key] for key in sorted(buckets)]


# Float noise, not a threshold. Frame times are computed as pts * time_base * 1000, so a run of
# exactly six flashes a second comes out 1000.0000000000001 ms apart and the flash on the window
# edge would be counted twice over. A nanosecond is far below any frame interval a camera has.
_WINDOW_EPS_MS = 1e-6


def _count_in_window(times: list[float], now: float, window_ms: float) -> int:
    """How many of those instants fall in the trailing window that ends now.

    The window is (now - window_ms, now], the placement flashmap uses and the one that makes the
    family of trailing windows complete: if four flashes share any one second, they share the
    trailing window ending at the fourth of them. Anything later than `now` is in the future and
    is not counted, which only matters when this is called on a finished run.
    """
    start = now - window_ms + _WINDOW_EPS_MS
    count = 0
    for value in reversed(times):
        if value > now + _WINDOW_EPS_MS:
            continue
        if value <= start:
            break
        count += 1
    return count


def _peak_in_window(times: list[float], window_ms: float) -> int:
    """The worst trailing window over the whole run, in one pass."""
    best = 0
    first = 0
    for index, value in enumerate(times):
        start = value - window_ms + _WINDOW_EPS_MS
        while times[first] <= start:
            first += 1
        best = max(best, index - first + 1)
    return best


def _downsample(frame: NDArray[np.uint8], target_width: int) -> NDArray[np.float64]:
    """Box average down to about `target_width`, keeping the aspect ratio.

    Averaging rather than picking pixels, because the area rule asks what share of a region is
    flashing and dropping pixels would answer a different question. Already small enough, and it
    is returned untouched.
    """
    array = np.asarray(frame, dtype=np.float64)
    height, width = array.shape[:2]
    if width <= target_width:
        return array
    factor = int(max(1, math.floor(width / target_width)))
    new_h = max(1, height // factor)
    new_w = max(1, width // factor)
    trimmed = array[: new_h * factor, : new_w * factor]
    return trimmed.reshape(new_h, factor, new_w, factor, array.shape[2]).mean(axis=(1, 3))


# ----------------------------------------------------------------- decoding


def decode_frames(
    source: str,
    *,
    width: int,
    input_format: str | None = None,
    options: dict[str, str] | None = None,
    limit: int | None = None,
    assume_fps: float | None = None,
) -> Iterator[tuple[NDArray[np.uint8], float]]:
    """Frames and their times, from a file or from a live device.

    Live capture is the same code path with `input_format` set (`avfoundation` on this Mac,
    `v4l2` on Linux), because a meter that behaves differently on the night is not a meter.
    """
    import av

    container = av.open(source, format=input_format, options=options or {})
    try:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        height_hint = None
        width_used = width
        index = 0
        for frame in container.decode(stream):
            if height_hint is None:
                # Never scale up. A recording narrower than the working width carries no more
                # detail for being stretched, and stretching it costs time on every frame.
                width_used = min(width, frame.width)
                height_hint = max(2, int(round(width_used * frame.height / frame.width)))
                height_hint -= height_hint % 2
            array = frame.to_ndarray(format="rgb24", width=width_used, height=height_hint)
            if frame.pts is not None and frame.time_base is not None:
                time_ms = float(frame.pts * frame.time_base * 1000)
            elif assume_fps:
                time_ms = index * 1000.0 / assume_fps
            else:
                raise RuntimeError(
                    "the stream has no timestamps. Pass --assume-fps to say what rate it ran at."
                )
            yield array, time_ms
            index += 1
            if limit is not None and index >= limit:
                return
    finally:
        container.close()


def sample_frames_and_times(
    source: str, *, width: int, count: int, input_format: str | None = None
) -> tuple[list[NDArray[np.uint8]], list[float]]:
    """A spread of frames, with their times, for finding the screen or reading a chart.

    It takes the first `count` frames after a short warmup rather than seeking, because a camera
    file and a live device do not seek the same way and the screen does not move. The times come
    back because the flicker check needs to know how fast the frames arrived before it can say
    what frequency a ripple is.
    """
    frames: list[NDArray[np.uint8]] = []
    times: list[float] = []
    warmup = 2
    for index, (array, time_ms) in enumerate(
        decode_frames(source, width=width, input_format=input_format, limit=count + warmup)
    ):
        if index < warmup:
            continue
        frames.append(array)
        times.append(time_ms)
    if not frames:
        raise RoiError(f"no frames decoded from {source}")
    return frames, times


def sample_frames(
    source: str, *, width: int, count: int, input_format: str | None = None
) -> list[NDArray[np.uint8]]:
    """The frames alone, for callers that do not care when they arrived."""
    return sample_frames_and_times(
        source, width=width, count=count, input_format=input_format
    )[0]


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run_frames(
    frames: Iterable[tuple[NDArray[np.uint8], float]],
    *,
    roi: Roi,
    calibration: Calibration | None = None,
    settings: InstrumentSettings | None = None,
    spec: SpecNumbers | None = None,
    on_reading=None,
) -> Meter:
    """Run the meter over an iterable of (frame, time_ms). The core both paths share."""
    meter = Meter(roi=roi, calibration=calibration, settings=settings, spec=spec)
    for array, time_ms in frames:
        reading = meter.feed(array, time_ms)
        if on_reading is not None:
            on_reading(reading)
    return meter


def run_file(
    path: str | Path,
    *,
    roi: Roi | None = None,
    calibration: Calibration | None = None,
    settings: InstrumentSettings | None = None,
    spec: SpecNumbers | None = None,
    input_format: str | None = None,
    assume_fps: float | None = None,
    on_reading=None,
    with_trace: bool = False,
) -> MeterReport:
    """The whole measurement for one recording: find the screen, count, report."""
    settings = settings or InstrumentSettings()
    source = str(path)
    if roi is None:
        roi = find_roi(
            sample_frames(
                source,
                width=settings.working_width,
                count=settings.roi_sample_frames,
                input_format=input_format,
            ),
            settings,
        )
    meter = run_frames(
        decode_frames(
            source,
            width=settings.working_width,
            input_format=input_format,
            assume_fps=assume_fps,
        ),
        roi=roi,
        calibration=calibration,
        settings=settings,
        spec=spec,
        on_reading=on_reading,
    )
    source_record: dict[str, object] = {"source": source}
    file_path = Path(source)
    if file_path.is_file():
        source_record["sha256"] = file_digest(file_path)
        source_record["bytes"] = file_path.stat().st_size
    report = meter.report(source_record)
    if with_trace:
        report.trace = [dataclasses.asdict(r) for r in meter.readings]
    return report


# ----------------------------------------------------------------- plots


def plot_report(report: MeterReport, readings: Sequence[FrameReading], path: Path) -> Path:
    """Draw the run. A plot, never a frame: hazard footage is inspected this way or not at all."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    times = [r.time_ms / 1000.0 for r in readings]
    figure, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(times, [r.mean_luminance for r in readings], linewidth=0.8)
    axes[0].set_ylabel("mean relative luminance\nof the screen region")
    axes[0].grid(alpha=0.3)
    limit = int(report.headline["limit_per_second"])
    axes[1].plot(times, [r.general_per_second for r in readings], label="general", linewidth=0.9)
    axes[1].plot(times, [r.red_per_second for r in readings], label="red", linewidth=0.9)
    axes[1].axhline(limit, color="crimson", linestyle="--", linewidth=1.0, label="WCAG limit")
    axes[1].set_ylabel("flashes in the\ntrailing second")
    axes[1].set_xlabel("time in the recording (s)")
    axes[1].legend(loc="upper right", fontsize=8)
    axes[1].grid(alpha=0.3)
    title = "camera meter: %s" % Path(str(report.source.get("source", "recording"))).name
    if not report.publishable:
        title += "   [not publishable: see quality.warnings]"
    figure.suptitle(title, fontsize=10)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=130)
    plt.close(figure)
    return path


# ----------------------------------------------------------------- command line


def _load_roi(args) -> Roi | None:
    if getattr(args, "roi", None):
        text = args.roi
        candidate = Path(text)
        if candidate.is_file():
            return Roi.from_dict(json.loads(candidate.read_text()))
        return Roi.from_spec_string(text)
    return None


def _load_calibration(args) -> Calibration | None:
    if getattr(args, "calibration", None):
        return Calibration.from_dict(json.loads(Path(args.calibration).read_text()))
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="meter",
        description="WCAG flash meter for a filmed TV screen. Never opens a player.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    chart = sub.add_parser("chart", help="write the step chart, or the gray field, for the TV")
    chart.add_argument("--out", type=Path, required=True, help=".mp4 to play, .png to show")
    chart.add_argument("--width", type=int, default=1920)
    chart.add_argument("--height", type=int, default=1080)
    chart.add_argument("--steps", type=int, default=10)
    chart.add_argument("--gray", action="store_true", help="a flat field instead of the chart")
    chart.add_argument("--code", type=int, default=128, help="the level for --gray")
    chart.add_argument("--seconds", type=float, default=10.0, help="length, for a video --out")
    chart.add_argument("--fps", type=int, default=30)

    roi_cmd = sub.add_parser("roi", help="find the screen region in a recording")
    roi_cmd.add_argument("recording")
    roi_cmd.add_argument("--out", type=Path)
    roi_cmd.add_argument("--input-format")

    cal = sub.add_parser("calibrate", help="fit the camera against a filmed step chart")
    cal.add_argument("recording")
    cal.add_argument("--roi", help="roi.json, or x0,y0,x1,y1 as fractions")
    cal.add_argument("--steps", type=int, default=10)
    cal.add_argument("--out", type=Path)
    cal.add_argument("--input-format")

    run = sub.add_parser("run", help="count flashes in a recording or a live feed")
    run.add_argument("recording")
    run.add_argument("--roi", help="roi.json, or x0,y0,x1,y1 as fractions")
    run.add_argument("--calibration", help="calibration.json from `meter calibrate`")
    run.add_argument("--out", type=Path)
    run.add_argument("--plot", type=Path)
    run.add_argument("--trace", action="store_true", help="keep every frame in the report")
    run.add_argument("--input-format", help="avfoundation on macOS, v4l2 on Linux, for a camera")
    run.add_argument("--assume-fps", type=float)
    run.add_argument("--print-every", type=int, default=0, help="print a line every N frames")
    args = parser.parse_args(argv)

    settings = InstrumentSettings()

    if args.command == "chart":
        if args.gray:
            image = gray_field_image(args.width, args.height, args.code)
        else:
            image = step_chart_image(args.width, args.height, args.steps, settings)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if args.out.suffix.lower() in {".mp4", ".mov", ".m4v", ".mkv"}:
            write_still_video(image, args.out, seconds=args.seconds, fps=args.fps)
        else:
            try:
                import matplotlib

                matplotlib.use("Agg")
                import matplotlib.image as mpimg

                mpimg.imsave(str(args.out), image)
            except ImportError:
                print(
                    "matplotlib is needed for a still image. Ask for a .mp4 instead, which "
                    "needs only PyAV.",
                    file=sys.stderr,
                )
                return 2
        spec = load_spec()
        if args.gray:
            level = float(
                _luminance(spec, _linear_from_srgb8(spec, np.array([args.code] * 3)))
            )
            print(f"gray field, code {args.code} -> {args.out}")
            print(f"  relative luminance {level:.4f}")
            return 0
        print(f"step chart -> {args.out}")
        for code, luminance in zip(
            step_chart_codes(args.steps), step_chart_luminances(spec, args.steps)
        ):
            print(f"  code {code:3d}  relative luminance {luminance:.4f}")
        return 0

    if args.command == "roi":
        frames = sample_frames(
            args.recording,
            width=settings.working_width,
            count=settings.roi_sample_frames,
            input_format=args.input_format,
        )
        roi = find_roi(frames, settings)
        text = json.dumps(roi.as_dict(), indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text + "\n")
        print(text)
        return 0

    if args.command == "calibrate":
        roi = _load_roi(args)
        frames = sample_frames(
            args.recording,
            width=settings.working_width,
            count=settings.roi_sample_frames,
            input_format=args.input_format,
        )
        if roi is None:
            roi = find_roi(frames, settings)
        calibration = calibrate(frames, roi, steps=args.steps, settings=settings)
        payload = {"roi": roi.as_dict(), **calibration.as_dict()}
        text = json.dumps(payload, indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text + "\n")
        print(text)
        return 0

    # run
    roi = _load_roi(args)
    calibration = _load_calibration(args)
    printed = {"n": 0}

    def on_reading(reading: FrameReading) -> None:
        printed["n"] += 1
        if args.print_every and printed["n"] % args.print_every == 0:
            print(reading.as_line(), flush=True)

    report = run_file(
        args.recording,
        roi=roi,
        calibration=calibration,
        settings=settings,
        input_format=args.input_format,
        assume_fps=args.assume_fps,
        on_reading=on_reading if args.print_every else None,
        with_trace=args.trace,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report.as_dict(), indent=2) + "\n")
    print(json.dumps({k: report.as_dict()[k] for k in ("headline", "quality", "publishable")},
                     indent=2))
    if args.plot:
        # The readings are not on the report, so re-run only if a plot was asked for. Cheap
        # enough on a take, and it keeps the report file small.
        meter = Meter(roi=report_roi(report), calibration=calibration, settings=settings)
        for array, time_ms in decode_frames(
            args.recording,
            width=settings.working_width,
            input_format=args.input_format,
            assume_fps=args.assume_fps,
        ):
            meter.feed(array, time_ms)
        plot_report(report, meter.readings, args.plot)
        print(f"plot -> {args.plot}")
    return 0


def report_roi(report: MeterReport) -> Roi:
    return Roi.from_dict(dict(report.roi))


if __name__ == "__main__":
    raise SystemExit(main())
