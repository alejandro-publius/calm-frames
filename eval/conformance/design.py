#!/usr/bin/env python3
"""The conformance design: every clip that will be generated, decided before anything is drawn.

docs/EVAL_PLAN.md section 4: the design is committed before generation, generation reads the
manifest, and nothing is sampled at generation time. This script writes
`results/conformance_design.json`, one row per clip with every parameter and the ground truth
that truth.py computes for it. The RNG seed is in the file.

Shape of a clip (a deviation from the plan's 2 s + 2 s + 2 s, logged in eval/DEVIATIONS.md):
three seconds, a one second calm lead-in and a two second test section. Two seconds of test is
the least that lets a four-flash-per-second clip prove itself, and three seconds a clip keeps
about three thousand clips inside one session. The calm lead-in is what makes the leading edge
of a detector's hide measurable: a detector that hides the second before the flashing pays for
it in precision, which is the right way round for a thing whose job is to hide.

Rows come in two parts:

1. the spine, about a hundred and fifty rows that walk one axis at a time from a single centre
   point, so every error curve has a complete sweep even from a short run;
2. a seeded random cross product over every axis, which is where interactions show up.

The run order is the spine first and then the shuffled cross product, so a run that stops early
is still a random sample of the design with complete sweeps, and the report says how many rows
it actually has.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.spec import SpecNumbers, load_spec  # noqa: E402
from conformance.truth import clip_truth  # noqa: E402

REPO = _EVAL_DIR.parent
OUT = REPO / "results" / "conformance_design.json"

SEED = 20260917
DURATION_MS = 3000.0
FLASH_START_MS = 1000.0

RESOLUTIONS = {
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "2160p": (3840, 2160),
}
# 4K clips cost about nine times what a 480p clip costs to make and measure, so the random
# draw leans on the small ones. The spine covers every resolution whatever the draw does.
RESOLUTION_WEIGHTS = {"480p": 0.50, "720p": 0.30, "1080p": 0.15, "2160p": 0.05}

FLASH_RATES = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 20, 24, 30]
STEP_MULTIPLES = [0.5, 0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.25, 2.0]
DARK_MULTIPLES = [0.8, 0.95, 1.05, 1.2]
AREA_FRACTIONS = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.33, 0.40, 0.50, 0.60]
SHAPES = ["center_rect", "offset_rect", "scatter", "band"]
FPS_LEVELS = [24, 25, 30, 50, 60]
TIMINGS = ["cfr", "vfr_alternating", "vfr_dropped"]
CRF_LEVELS = [18, 23, 28, None]  # None is the lossless reference encode
TAGGINGS = ["bt709", "untagged_hd", "untagged_sd", "full_range"]
RED_MODES = [
    "gray_only",
    "red_gray_matched",
    "near_red_distance_0.9",
    "near_red_distance_0.95",
    "near_red_distance_1.05",
    "near_red_distance_1.1",
    "near_red_ratio_0.9",
    "near_red_ratio_0.95",
    "nonred_control",
    "red_same_chroma",
]

BACKGROUND = (64, 64, 64)
DEFAULT_DARK_LUMINANCE = 0.20


# ---- colour helpers, all built on the parsed spec arithmetic ---------------------------


def _gray_code(target_luminance: float, spec: SpecNumbers) -> int:
    """The 8 bit gray whose relative luminance is closest to the target."""
    value = min(1.0, max(0.0, target_luminance))
    if value <= spec.srgb_break / spec.srgb_divisor:
        encoded = value * spec.srgb_divisor
    else:
        encoded = spec.srgb_scale * value ** (1.0 / spec.srgb_exponent) - spec.srgb_offset
    return int(min(255, max(0, round(encoded * 255.0))))


def _luminance(rgb: tuple[int, int, int], spec: SpecNumbers) -> float:
    return spec.luminance_of_srgb8(rgb)


def _linear(rgb: tuple[int, int, int], spec: SpecNumbers) -> np.ndarray:
    return spec.srgb_to_linear(np.asarray(rgb, dtype=np.float64) / 255.0)


def _ucs_distance(a: tuple[int, int, int], b: tuple[int, int, int], spec: SpecNumbers) -> float:
    ua, va = spec.ucs(_linear(a, spec))
    ub, vb = spec.ucs(_linear(b, spec))
    return float(math.hypot(ua - ub, va - vb))


def _gray_matching(color: tuple[int, int, int], spec: SpecNumbers) -> tuple[int, int, int]:
    code = _gray_code(_luminance(color, spec), spec)
    return (code, code, code)


def _red_with_ucs_distance(target: float, spec: SpecNumbers) -> tuple[int, int, int]:
    """(255, k, k) whose distance from its luminance-matched gray is closest to the target.

    Desaturating a pure red towards white moves it towards the neutral point, so the distance
    falls as k rises. Searched over every k rather than bisected, because there are only 256 of
    them and an exhaustive search cannot land on the wrong side of a rounding.
    """
    best_k, best_error = 0, float("inf")
    for k in range(0, 256):
        color = (255, k, k)
        distance = _ucs_distance(color, _gray_matching(color, spec), spec)
        error = abs(distance - target)
        if error < best_error:
            best_k, best_error = k, error
    return (255, best_k, best_k)


def _red_with_ratio(target: float, spec: SpecNumbers) -> tuple[int, int, int]:
    """(255, k, k) whose linear R/(R+G+B) is closest to the target ratio."""
    best_k, best_error = 0, float("inf")
    for k in range(0, 256):
        ratio = spec.red_ratio(_linear((255, k, k), spec))
        error = abs(ratio - target)
        if error < best_error:
            best_k, best_error = k, error
    return (255, best_k, best_k)


def _cyan_matching(luminance: float, spec: SpecNumbers) -> tuple[int, int, int]:
    """A non-red colour at the requested luminance, for the luminance-matched control."""
    best, best_error = (0, 0, 0), float("inf")
    for k in range(0, 256):
        color = (0, k, k)
        error = abs(_luminance(color, spec) - luminance)
        if error < best_error:
            best, best_error = color, error
    return best


def state_pair(
    spec: SpecNumbers,
    *,
    red_mode: str,
    step_multiple: float,
    dark_multiple: float | None,
) -> tuple[tuple[int, int, int], tuple[int, int, int], dict[str, object]]:
    """The two colours a clip alternates between, and a note on how they were chosen.

    Gray pairs are built for a requested luminance step, so the general flash rule is the one
    under test. Red pairs are built luminance matched, so that only the red rule can fire and a
    detector cannot pass the red test by noticing a luminance change.
    """
    if red_mode == "gray_only":
        if dark_multiple is not None:
            dark_luminance = dark_multiple * spec.general_dark_image_below
        else:
            dark_luminance = DEFAULT_DARK_LUMINANCE
        wanted = step_multiple * spec.general_min_delta
        bright_luminance = dark_luminance + wanted
        if bright_luminance > 1.0:
            bright_luminance = 1.0
        dark_code = _gray_code(dark_luminance, spec)
        bright_code = _gray_code(bright_luminance, spec)
        note = {
            "requested_dark_luminance": dark_luminance,
            "requested_step": wanted,
            "step_reachable": bright_luminance - dark_luminance >= wanted - 1e-9,
        }
        return (dark_code,) * 3, (bright_code,) * 3, note

    if red_mode == "red_gray_matched":
        red = (255, 0, 0)
        return _gray_matching(red, spec), red, {"red_source": "saturated red 255,0,0"}

    if red_mode.startswith("near_red_distance_"):
        multiple = float(red_mode.rsplit("_", 1)[1])
        target = multiple * spec.red_min_ucs_distance
        color = _red_with_ucs_distance(target, spec)
        return (
            _gray_matching(color, spec),
            color,
            {"target_ucs_distance": target, "multiple": multiple},
        )

    if red_mode.startswith("near_red_ratio_"):
        multiple = float(red_mode.rsplit("_", 1)[1])
        target = multiple * spec.red_saturated_ratio
        color = _red_with_ratio(target, spec)
        return (
            _gray_matching(color, spec),
            color,
            {"target_red_ratio": target, "multiple": multiple},
        )

    if red_mode == "nonred_control":
        red = (255, 0, 0)
        control = _cyan_matching(_luminance(red, spec), spec)
        return (
            _gray_matching(control, spec),
            control,
            {"control": "non-red at the luminance of saturated red"},
        )

    if red_mode == "red_same_chroma":
        # Two reds on the same chromaticity, a luminance step under the general limit: the
        # chromaticity never moves, so the red rule must not fire and neither must the general
        # rule. This is the clip that separates "saturated red is present" from "a red flash".
        bright = (255, 0, 0)
        target = _luminance(bright, spec) - 0.5 * spec.general_min_delta
        best, best_error = (0, 0, 0), float("inf")
        for k in range(0, 256):
            color = (k, 0, 0)
            error = abs(_luminance(color, spec) - target)
            if error < best_error:
                best, best_error = color, error
        return best, bright, {"pair": "red to red, same chromaticity"}

    raise ValueError(f"unknown red mode {red_mode!r}")


# ---- rows ------------------------------------------------------------------------------


def make_clip(
    spec: SpecNumbers,
    *,
    axis: str,
    resolution: str = "480p",
    letterbox_fraction: float = 0.0,
    shape: str = "center_rect",
    area_fraction: float = 0.25,
    flash_hz: float = 10.0,
    fps: int = 30,
    timing: str = "cfr",
    crf: int | None = 23,
    tagging: str = "bt709",
    red_mode: str = "gray_only",
    step_multiple: float = 2.0,
    dark_multiple: float | None = None,
    seed: int = 0,
) -> dict:
    width, height = RESOLUTIONS[resolution]
    state_a, state_b, note = state_pair(
        spec, red_mode=red_mode, step_multiple=step_multiple, dark_multiple=dark_multiple
    )
    clip = {
        "axis": axis,
        "resolution": resolution,
        "width": width,
        "height": height,
        "letterbox_fraction": letterbox_fraction,
        "shape": shape,
        "area_fraction": area_fraction,
        "flash_hz": flash_hz,
        "fps": fps,
        "timing": timing,
        "crf": crf,
        "color_tagging": tagging,
        "red_mode": red_mode,
        "step_multiple": step_multiple,
        "dark_multiple": dark_multiple,
        "duration_ms": DURATION_MS,
        "flash_start_ms": FLASH_START_MS,
        "background_rgb": list(BACKGROUND),
        "state_a_rgb": list(state_a),
        "state_b_rgb": list(state_b),
        "state_note": note,
        "seed": seed,
    }
    digest = hashlib.sha256(
        json.dumps({k: v for k, v in clip.items() if k != "axis"}, sort_keys=True).encode()
    ).hexdigest()[:16]
    clip["clip_id"] = digest
    truth = clip_truth(clip, spec)
    clip["truth"] = truth.as_dict()
    clip["near_threshold"] = near_threshold(clip, truth, spec)
    return clip


def near_threshold(clip: dict, truth, spec: SpecNumbers) -> bool:
    """Does some governing quantity sit within 15% of the limit that governs it?

    EVAL_PLAN section 4. Flash rate counts when it is on the grid point either side of the
    limit, because the rate grid is integers and 15% of three flashes is not a grid point.
    """
    margin = 0.15
    if truth.general_qualifies or clip["red_mode"] == "gray_only":
        if truth.general_delta > 0 and abs(
            truth.general_delta - spec.general_min_delta
        ) <= margin * spec.general_min_delta:
            return True
        if abs(
            truth.darker_luminance - spec.general_dark_image_below
        ) <= margin * spec.general_dark_image_below:
            return True
    if abs(truth.field_coverage - spec.area_fraction_limit) <= margin * spec.area_fraction_limit:
        return True
    if clip["red_mode"] != "gray_only":
        if abs(
            truth.ucs_distance - spec.red_min_ucs_distance
        ) <= margin * spec.red_min_ucs_distance:
            return True
        if abs(
            truth.red_ratio_max - spec.red_saturated_ratio
        ) <= margin * spec.red_saturated_ratio:
            return True
    limit = spec.flash_limit_per_second
    if limit <= truth.observed_flash_rate_hz <= limit + 1.5:
        return True
    return False


def drawable_area(spec: SpecNumbers, shape: str, fraction: float, resolution: str = "480p") -> bool:
    """Can this shape actually be drawn at this area fraction on this picture?

    A scatter of nine blocks cannot fill more than its grid cells, and a band cannot be half a
    pixel tall. Asking for an area the shape cannot draw would produce two clips with different
    labels and identical pixels, so those rows are dropped from the design instead.
    """
    from conformance.geometry import picture_rect, region_rects

    width, height = RESOLUTIONS[resolution]
    picture = picture_rect(width, height, 0.0)
    rects = region_rects(picture, shape, fraction)
    drawn = sum(r.area for r in rects) / float(picture.width * picture.height)
    return abs(drawn - fraction) <= 0.12 * fraction


def area_crossing(spec: SpecNumbers, shape: str, resolution: str = "480p") -> float:
    """The area fraction at which this shape's 10 degree field coverage crosses the limit.

    Found by bisection on the geometry, so the near-threshold area points are placed where the
    rule actually turns over for that shape rather than at a number picked by eye. A compact
    rectangle crosses at a much smaller area than a scatter of blocks does, which is the whole
    reason the shape axis exists.
    """
    from conformance.geometry import picture_rect, region_rects
    from conformance.truth import max_field_coverage

    width, height = RESOLUTIONS[resolution]
    picture = picture_rect(width, height, 0.0)

    def coverage(fraction: float) -> float:
        return max_field_coverage(picture, region_rects(picture, shape, fraction), spec)

    low, high = 0.001, 1.0
    if coverage(high) <= spec.area_fraction_limit:
        return float("nan")
    for _ in range(40):
        mid = (low + high) / 2
        if coverage(mid) > spec.area_fraction_limit:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def spine(spec: SpecNumbers) -> list[dict]:
    """One axis at a time from a single centre point."""
    rows: list[dict] = []

    # flash rate, at two frame rates so aliasing is visible
    for rate in FLASH_RATES:
        for fps in (30, 60):
            rows.append(make_clip(spec, axis="flash_rate", flash_hz=rate, fps=fps))

    # luminance step, at two darker-image levels
    for multiple in STEP_MULTIPLES:
        for dark in (None, 0.5):
            rows.append(
                make_clip(
                    spec,
                    axis="luminance_step",
                    step_multiple=multiple,
                    dark_multiple=dark,
                    crf=None,
                )
            )

    # darker image condition
    for dark in DARK_MULTIPLES:
        for multiple in (1.5, 3.0):
            rows.append(
                make_clip(
                    spec,
                    axis="darker_image",
                    step_multiple=multiple,
                    dark_multiple=dark,
                    crf=None,
                )
            )

    # area and shape, with the crossing point of each shape bracketed
    for shape in SHAPES:
        crossing = area_crossing(spec, shape)
        fractions = list(AREA_FRACTIONS)
        if not math.isnan(crossing):
            fractions += [
                round(min(0.95, max(0.005, crossing * m)), 4)
                for m in (0.85, 0.95, 1.05, 1.15)
            ]
        for fraction in sorted(set(fractions)):
            if not drawable_area(spec, shape, fraction):
                continue
            rows.append(make_clip(spec, axis="area", shape=shape, area_fraction=fraction))

    # red versus near red
    for mode in RED_MODES:
        if mode == "gray_only":
            continue
        rows.append(make_clip(spec, axis="red", red_mode=mode))
        rows.append(make_clip(spec, axis="red", red_mode=mode, crf=None))

    # frame rate and timing
    for fps in FPS_LEVELS:
        rows.append(make_clip(spec, axis="frame_rate", fps=fps))
    for timing in ("vfr_alternating", "vfr_dropped"):
        for fps in (30, 60):
            rows.append(make_clip(spec, axis="frame_rate", fps=fps, timing=timing))

    # resolution, including letterboxed pictures
    for resolution in RESOLUTIONS:
        rows.append(make_clip(spec, axis="resolution", resolution=resolution))
    for resolution in ("480p", "1080p"):
        rows.append(
            make_clip(spec, axis="resolution", resolution=resolution, letterbox_fraction=0.25)
        )

    # compression
    for crf in CRF_LEVELS:
        rows.append(make_clip(spec, axis="compression", crf=crf))
        rows.append(
            make_clip(spec, axis="compression", crf=crf, area_fraction=0.03, shape="center_rect")
        )

    # colour tagging, each on a picture size that makes the guess meaningful
    for tagging in TAGGINGS:
        resolution = "720p" if tagging == "untagged_hd" else "480p"
        rows.append(make_clip(spec, axis="color_tagging", tagging=tagging, resolution=resolution))
        rows.append(
            make_clip(
                spec,
                axis="color_tagging",
                tagging=tagging,
                resolution=resolution,
                step_multiple=1.05,
            )
        )
    return rows


# Values that are deliberately clear of every limit, for the rows that are meant to be easy.
# Without these the draw is accidentally near threshold most of the time, because five of the
# nine luminance steps and three of the fourteen flash rates sit inside the near band, and a
# suite that is four fifths boundary cases reports a pessimistic headline for ordinary content.
FAR_RATES = [1, 2, 6, 8, 10, 12, 15, 18, 20, 24, 30]
FAR_STEPS = [0.5, 0.8, 1.25, 2.0]
FAR_RED_MODES = ["gray_only", "red_gray_matched", "nonred_control", "red_same_chroma"]
FAR_DARK = [None, None, 0.8]
NEAR_RED_MODES = [
    "gray_only",
    "near_red_distance_0.9",
    "near_red_distance_0.95",
    "near_red_distance_1.05",
    "near_red_distance_1.1",
    "near_red_ratio_0.9",
]


def cross_product(spec: SpecNumbers, count: int, rng: random.Random) -> list[dict]:
    """A seeded random draw over every axis at once, where interactions live.

    Four rows in ten are aimed at a threshold and six are aimed clear of every one of them.
    Aiming is not the same as hitting, because quantising a colour to eight bits moves the
    luminance step and sampling a square wave moves the rate, so each row is redrawn a few
    times until `near_threshold` agrees with what was aimed for, and the manifest records what
    the row turned out to be rather than what it was meant to be.
    """
    resolutions = list(RESOLUTION_WEIGHTS)
    weights = [RESOLUTION_WEIGHTS[name] for name in resolutions]
    near_area = {shape: area_crossing(spec, shape) for shape in SHAPES}

    def draw(want_near: bool) -> dict:
        shape = rng.choice(SHAPES)
        crossing = near_area[shape]
        if want_near and not math.isnan(crossing):
            area = round(crossing * rng.choice([0.88, 0.94, 1.0, 1.06, 1.12]), 4)
            area = min(0.9, max(0.004, area))
        else:
            choices = [f for f in AREA_FRACTIONS if drawable_area(spec, shape, f)]
            area = rng.choice(choices)
        return make_clip(
            spec,
            axis="cross",
            resolution=rng.choices(resolutions, weights=weights, k=1)[0],
            letterbox_fraction=rng.choice([0.0, 0.0, 0.0, 0.125, 0.25]),
            shape=shape,
            area_fraction=area,
            flash_hz=rng.choice([3, 4, 5] if want_near else FAR_RATES),
            fps=rng.choice(FPS_LEVELS),
            timing=rng.choices(TIMINGS, weights=[0.8, 0.1, 0.1], k=1)[0],
            crf=rng.choice(CRF_LEVELS),
            tagging=rng.choices(TAGGINGS, weights=[0.7, 0.1, 0.1, 0.1], k=1)[0],
            red_mode=rng.choice(NEAR_RED_MODES if want_near else FAR_RED_MODES),
            step_multiple=rng.choice(
                [0.9, 0.95, 1.0, 1.05, 1.1] if want_near else FAR_STEPS
            ),
            dark_multiple=rng.choice([None, None, 0.95, 1.05] if want_near else FAR_DARK),
            seed=rng.randrange(1 << 30),
        )

    rows: list[dict] = []
    seen: set[str] = set()
    attempts = 0
    while len(rows) < count and attempts < count * 40:
        want_near = len(rows) % 10 < 4
        row = draw(want_near)
        attempts += 1
        if row["near_threshold"] != want_near and attempts % 8 != 0:
            continue
        if row["clip_id"] in seen:
            continue
        seen.add(row["clip_id"])
        rows.append(row)
    return rows


def build(total: int = 3000) -> dict:
    spec = load_spec()
    rng = random.Random(SEED)
    rows = spine(spec)
    # The centre point of one axis is a point on another, so the spine holds a few rows that
    # are the same clip twice. Identical pixels measured twice would be one clip and two rows,
    # and the runner would skip the second, so they are dropped here and the cross product is
    # topped up to keep the count the design asked for.
    unique: dict[str, dict] = {}
    for row in rows:
        unique.setdefault(row["clip_id"], row)
    rows = list(unique.values())
    spine_count = len(rows)
    for row in cross_product(spec, max(0, total - spine_count), rng):
        if row["clip_id"] not in unique:
            unique[row["clip_id"]] = row
            rows.append(row)

    # run order: the whole spine first, then the cross product shuffled, so that a run which
    # stops early still holds every sweep and a random sample of everything else.
    shuffled = rows[spine_count:]
    rng.shuffle(shuffled)
    ordered = rows[:spine_count] + shuffled
    for index, row in enumerate(ordered):
        row["order_index"] = index

    near = sum(1 for row in ordered if row["near_threshold"])
    positives = sum(1 for row in ordered if row["truth"]["positive_windows"])
    share = near / len(ordered)
    if share < 0.40:
        raise SystemExit(
            f"near threshold share is {share:.3f}, under the 0.40 the plan requires. "
            "Fix the design, do not lower the bar."
        )

    return {
        "generated_on": "2026-09-17",
        "seed": SEED,
        "clip_shape": {
            "duration_ms": DURATION_MS,
            "calm_lead_in_ms": FLASH_START_MS,
            "test_section_ms": DURATION_MS - FLASH_START_MS,
            "windows_per_clip": int(DURATION_MS // 1000),
            "deviation": (
                "EVAL_PLAN section 4 designs 6 s clips as 2 s calm, 2 s test, 2 s calm. These "
                "are 3 s as 1 s calm and 2 s test, so that about three thousand clips fit in "
                "one session. Logged in eval/DEVIATIONS.md. The trailing calm section is gone, "
                "so this suite does not measure how long a hide runs on past the flashing."
            ),
        },
        "spec": spec.as_dict(),
        "counts": {
            "clips": len(ordered),
            "spine": spine_count,
            "cross": len(ordered) - spine_count,
            "near_threshold": near,
            "near_threshold_share": round(share, 4),
            "clips_with_a_positive_window": positives,
            "windows": sum(row["truth"]["n_windows"] for row in ordered),
            "positive_windows": sum(len(row["truth"]["positive_windows"]) for row in ordered),
        },
        "axes": sorted({row["axis"] for row in ordered}),
        "area_crossing_by_shape": {
            shape: round(area_crossing(load_spec(), shape), 5) for shape in SHAPES
        },
        "clips": ordered,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--total", type=int, default=3000)
    parser.add_argument("-o", "--out", type=Path, default=OUT)
    arguments = parser.parse_args()

    design = build(arguments.total)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(design, indent=1) + "\n")
    counts = design["counts"]
    print(
        f"{counts['clips']} clips ({counts['spine']} spine, {counts['cross']} cross), "
        f"{counts['near_threshold']} near threshold ({counts['near_threshold_share']:.0%}), "
        f"{counts['positive_windows']} positive windows of {counts['windows']} "
        f"-> {arguments.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
