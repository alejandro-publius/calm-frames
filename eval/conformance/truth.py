#!/usr/bin/env python3
"""The true answer for a generated clip, computed from the spec text and from what was drawn.

**This module must not import flashmap.** eval/tests/test_conformance_standalone.py reads its
syntax tree and fails on any flashmap import, directly or through spec.py and geometry.py. If
truth and flashmap disagree, that is a finding to report, not a bug to be fixed by making truth
agree (docs/EVAL_PLAN.md section 4).

Every threshold used here is parsed out of flashmap/docs/SPEC_SOURCES.md by spec.py at run
time. No number in this file is a threshold.

How a window is judged
----------------------
WCAG's condition is about "any one-second period", and our unit of analysis is a fixed one
second window, so the two have to be joined up. This module does it in the way that follows the
wording most closely:

1. Walk the frames the generator planned. A transition is a change between the two drawn
   states; a flash is a pair of opposing transitions, paired without overlap, so a square wave
   at f Hz is f flashes a second. That pairing is the reading recorded in SPEC_SOURCES under
   implementation decision 1.
2. A flash qualifies if the two states meet the general flash condition (a change in relative
   luminance of at least the minimum, with the darker state below the darker-image limit) or
   the red flash condition (a state at or above the saturated red ratio, and a move of more
   than the minimum distance in the CIE 1976 UCS diagram).
3. Find every one-second period that holds more than the permitted number of qualifying
   flashes. A period is half open, `[s, s + 1000)`. Every flash inside such a period is a
   failing flash.
4. The area rule: the flashing region has to fill more than the area limit of some 10 degree
   field on the picture. The field is a box of the picture's own width and height fractions,
   slid to every position, and the best position wins. Computed exactly on the drawn geometry,
   not on a downscaled grid.
5. A window is a ground truth positive when a failing flash completes inside it and the area
   rule fails. A window with no flashing in it at all is a negative, whatever a detector chose
   to hide around it.

The half open period in step 3 is a choice the spec does not make for us. The other choice, a
closed period `[s, s + 1000]`, counts a flash at both ends and so calls a clean 3 Hz square
wave four flashes in a second. flashmap's trailing window is closed. That difference shows up
at exactly the flash limit and nowhere else, and the conformance report says so rather than
smoothing it over.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.geometry import Rect, frame_plan, picture_rect, region_rects  # noqa: E402
from conformance.spec import SpecNumbers, load_spec  # noqa: E402

__all__ = ["ClipTruth", "clip_truth", "max_field_coverage", "flash_completions"]


@dataclass(frozen=True)
class ClipTruth:
    n_windows: int
    window_ms: int
    positive_windows: list[int]
    flashes_per_window: list[int]
    failing_flashes_per_window: list[int]
    general_qualifies: bool
    red_qualifies: bool
    general_delta: float
    darker_luminance: float
    red_ratio_max: float
    ucs_distance: float
    field_coverage: float
    area_qualifies: bool
    drawn_area_fraction: float
    observed_flash_rate_hz: float
    mean_luminance_by_state: list[float]
    frames: int

    def as_dict(self) -> dict[str, object]:
        return {
            "n_windows": self.n_windows,
            "window_ms": self.window_ms,
            "positive_windows": self.positive_windows,
            "flashes_per_window": self.flashes_per_window,
            "failing_flashes_per_window": self.failing_flashes_per_window,
            "general_qualifies": self.general_qualifies,
            "red_qualifies": self.red_qualifies,
            "general_delta": round(self.general_delta, 6),
            "darker_luminance": round(self.darker_luminance, 6),
            "red_ratio_max": round(self.red_ratio_max, 6),
            "ucs_distance": round(self.ucs_distance, 6),
            "field_coverage": round(self.field_coverage, 6),
            "area_qualifies": self.area_qualifies,
            "drawn_area_fraction": round(self.drawn_area_fraction, 6),
            "observed_flash_rate_hz": round(self.observed_flash_rate_hz, 4),
            "mean_luminance_by_state": [round(v, 6) for v in self.mean_luminance_by_state],
            "frames": self.frames,
        }


def max_field_coverage(picture: Rect, rects: list[Rect], spec: SpecNumbers) -> float:
    """The largest share of any 10 degree field on the picture that these rectangles fill.

    Exact, on real valued geometry. For axis aligned rectangles the best field position can
    always be slid until one of its edges meets a rectangle edge or the edge of the picture, so
    only those positions are tried. The rectangles must not overlap, which every shape in
    geometry.py guarantees, because the areas are added rather than unioned.
    """
    if not rects:
        return 0.0
    pw, ph = float(picture.width), float(picture.height)
    fw = min(pw, pw * spec.field_width_fraction)
    fh = min(ph, ph * spec.field_height_fraction)
    if fw <= 0 or fh <= 0:
        return 0.0

    x0 = np.array([r.x0 - picture.x0 for r in rects], dtype=np.float64)
    x1 = np.array([r.x1 - picture.x0 for r in rects], dtype=np.float64)
    y0 = np.array([r.y0 - picture.y0 for r in rects], dtype=np.float64)
    y1 = np.array([r.y1 - picture.y0 for r in rects], dtype=np.float64)

    def candidates(starts: np.ndarray, ends: np.ndarray, size: float, extent: float):
        raw = np.concatenate([starts, ends - size, np.array([0.0, extent - size])])
        clipped = np.clip(raw, 0.0, max(0.0, extent - size))
        return np.unique(clipped)

    xs = candidates(x0, x1, fw, pw)
    ys = candidates(y0, y1, fh, ph)

    # overlap of each candidate position with each rectangle, on each axis
    ox = np.clip(
        np.minimum(x1[None, :], xs[:, None] + fw) - np.maximum(x0[None, :], xs[:, None]),
        0.0,
        None,
    )
    oy = np.clip(
        np.minimum(y1[None, :], ys[:, None] + fh) - np.maximum(y0[None, :], ys[:, None]),
        0.0,
        None,
    )
    areas = ox @ oy.T  # [x candidate, y candidate], rectangles summed
    return float(areas.max()) / (fw * fh)


def flash_completions(times: list[float], states: list[int]) -> list[float]:
    """When each flash completes, from the frames as they were planned.

    A transition is a frame whose state differs from the one before. Transitions alternate
    between the two states, so every second transition completes a pair of opposing
    transitions, which is one flash. The time recorded is the time of the frame that completed
    it, because that is the first moment the flash can be counted.
    """
    completions: list[float] = []
    pending = False
    for index in range(1, len(states)):
        if states[index] == states[index - 1]:
            continue
        if pending:
            completions.append(times[index])
            pending = False
        else:
            pending = True
    return completions


# Frame times are thirds and sixths of a millisecond, so a flash that lands exactly one second
# after another can come out a fraction of a picosecond early in binary. This tolerance keeps
# that from deciding whether a clean 3 Hz square wave passes. It is a floating point guard, not
# a threshold: a microsecond is far below one frame at any frame rate here.
_TIE_MS = 1e-6


def _failing_flashes(completions: list[float], limit: int, window_ms: float) -> list[float]:
    """Every flash that sits inside some one-second period holding more than `limit` flashes."""
    failing: set[int] = set()
    n = len(completions)
    for start in range(n):
        end = start
        while (
            end + 1 < n
            and completions[end + 1] < completions[start] + window_ms - _TIE_MS
        ):
            end += 1
        if end - start + 1 > limit:
            failing.update(range(start, end + 1))
    return [completions[i] for i in sorted(failing)]


def _mean_luminance(
    picture: Rect,
    rects: list[Rect],
    background: tuple[int, int, int],
    state_rgb: tuple[int, int, int],
    spec: SpecNumbers,
) -> float:
    """Mean relative luminance over the picture when the region shows this state.

    Used only by the encoding fidelity check, which compares the decoded clip against the
    waveform that was asked for. Bars are outside the picture and are not part of it.
    """
    region_area = float(sum(r.area for r in rects))
    total = float(picture.width * picture.height)
    if total <= 0:
        return 0.0
    l_background = spec.luminance_of_srgb8(background)
    l_state = spec.luminance_of_srgb8(state_rgb)
    share = min(1.0, region_area / total)
    return l_background * (1.0 - share) + l_state * share


def clip_truth(clip: dict, spec: SpecNumbers | None = None) -> ClipTruth:
    """The per window truth for one clip of the design manifest."""
    spec = spec or load_spec()
    picture = picture_rect(
        int(clip["width"]), int(clip["height"]), float(clip.get("letterbox_fraction", 0.0))
    )
    rects = region_rects(picture, str(clip["shape"]), float(clip["area_fraction"]))
    times, states = frame_plan(
        duration_ms=float(clip["duration_ms"]),
        fps=float(clip["fps"]),
        timing=str(clip["timing"]),
        flash_start_ms=float(clip["flash_start_ms"]),
        flash_hz=float(clip["flash_hz"]),
        seed=int(clip.get("seed", 0)),
    )

    state_a = tuple(int(v) for v in clip["state_a_rgb"])
    state_b = tuple(int(v) for v in clip["state_b_rgb"])
    background = tuple(int(v) for v in clip["background_rgb"])

    linear_a = spec.srgb_to_linear(np.asarray(state_a, dtype=np.float64) / 255.0)
    linear_b = spec.srgb_to_linear(np.asarray(state_b, dtype=np.float64) / 255.0)
    lum_a = float(spec.relative_luminance(linear_a))
    lum_b = float(spec.relative_luminance(linear_b))

    general_delta = abs(lum_a - lum_b)
    darker = min(lum_a, lum_b)
    general_qualifies = (
        general_delta >= spec.general_min_delta and darker < spec.general_dark_image_below
    )

    ratio_a = spec.red_ratio(linear_a)
    ratio_b = spec.red_ratio(linear_b)
    u_a, v_a = spec.ucs(linear_a)
    u_b, v_b = spec.ucs(linear_b)
    ucs_distance = float(np.hypot(u_a - u_b, v_a - v_b))
    red_qualifies = (
        max(ratio_a, ratio_b) >= spec.red_saturated_ratio
        and ucs_distance > spec.red_min_ucs_distance
    )

    coverage = max_field_coverage(picture, rects, spec)
    area_qualifies = coverage > spec.area_fraction_limit

    window_ms = float(spec.window_ms)
    duration_ms = float(clip["duration_ms"])
    n_windows = int(duration_ms // window_ms)

    completions = flash_completions(times, states)
    qualifying = completions if (general_qualifies or red_qualifies) else []
    failing = _failing_flashes(qualifying, spec.flash_limit_per_second, window_ms)

    per_window = [0] * n_windows
    failing_per_window = [0] * n_windows
    for t in qualifying:
        index = int(t // window_ms)
        if 0 <= index < n_windows:
            per_window[index] += 1
    for t in failing:
        index = int(t // window_ms)
        if 0 <= index < n_windows:
            failing_per_window[index] += 1

    positive = (
        [k for k in range(n_windows) if failing_per_window[k] > 0] if area_qualifies else []
    )

    flashing_span_ms = max(1.0, duration_ms - float(clip["flash_start_ms"]))
    drawn_area = sum(r.area for r in rects) / float(picture.width * picture.height)

    return ClipTruth(
        n_windows=n_windows,
        window_ms=int(window_ms),
        positive_windows=positive,
        flashes_per_window=per_window,
        failing_flashes_per_window=failing_per_window,
        general_qualifies=general_qualifies,
        red_qualifies=red_qualifies,
        general_delta=general_delta,
        darker_luminance=darker,
        red_ratio_max=max(ratio_a, ratio_b),
        ucs_distance=ucs_distance,
        field_coverage=coverage,
        area_qualifies=area_qualifies,
        drawn_area_fraction=drawn_area,
        observed_flash_rate_hz=len(completions) * 1000.0 / flashing_span_ms,
        mean_luminance_by_state=[
            _mean_luminance(picture, rects, background, state_a, spec),
            _mean_luminance(picture, rects, background, state_b, spec),
        ],
        frames=len(times),
    )
