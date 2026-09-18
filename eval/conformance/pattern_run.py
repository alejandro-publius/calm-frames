#!/usr/bin/env python3
"""The regular pattern conformance suite: design, generate, measure, delete, score. One job.

SAFETY, NOT NEGOTIABLE. Read this before changing anything in this file.
-----------------------------------------------------------------------
These clips are hazardous by design. They are high contrast gratings built to sit on and around
the limits in ITU-R BT.1702-3 Attachment 1 to Annex 1, and some of them reverse contrast every
frame. So, exactly as eval/conformance/generate_analyze.py does:

- each clip is written under a scratch directory outside the repository, owner only, with a
  `HAZARD_` name, and is deleted in a `finally` block in the same job that made it, before the
  next clip starts. At no point does the set of them exist;
- nothing here opens, plays, thumbnails or previews a clip, and neither does a person. The only
  thing that ever sees these pixels is a decoder;
- the run asserts at exit that no `HAZARD_` file survived. If one did, it is removed and the run
  fails, because a hazard file that outlives its job is the one failure mode that can hurt
  somebody;
- SIGTERM is turned into an exception so the `finally` that deletes the clip actually runs.

What this measures
------------------
flashmap's pattern rule, on its own, against a ground truth computed from the quoted spec text
and from what the generator drew, by modules that cannot import flashmap. The guard for that is
`check_ground_truth_is_independent` below, which reads their syntax trees and then imports them
in a fresh interpreter, and which runs before a single clip is made.

Nothing here scores the flash rules. They have their own suite. A pattern finding is not a WCAG
finding, so no number this file produces may be described as WCAG conformance.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
import signal
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.pattern_geometry import (  # noqa: E402
    MOTIONS,
    ORIENTATIONS,
    block_for,
    draw_frame,
    frame_times,
    phase_for,
)
from conformance.pattern_spec import load_pattern_spec  # noqa: E402
from conformance.pattern_truth import clip_truth  # noqa: E402
from conformance.render import HAZARD_PREFIX, scratch_dir  # noqa: E402
from metrics import (  # noqa: E402
    bootstrap_groups,
    confusion,
    f1,
    rate_with_interval,
    windows_from_intervals,
)

REPO = _EVAL_DIR.parent
OUT = REPO / "results" / "conformance_pattern.json"
RAW = REPO / "results" / "conformance_pattern_raw.jsonl"

SEED = 20260917
DURATION_MS = 3000.0
PATTERN_START_MS = 1000.0
PROFILE = "broadcast"

RESOLUTIONS = {"480p": (854, 480), "720p": (1280, 720)}
PAIRS = [2, 3, 4, 5, 6, 7, 8, 10, 12, 16]
AREAS = [0.10, 0.20, 0.24, 0.26, 0.30, 0.38, 0.42, 0.50, 0.70, 0.95]
CONTRAST_MULTIPLES = [0.5, 0.9, 1.0, 1.1, 2.0, 4.0]
DARK_MULTIPLES = [0.1, 0.5, 0.9, 1.05]
CRF_LEVELS = [18, 23, None]
SPEED_BARS = 0.25

# How far the bar to bar difference that came back out of the encoder may sit from the one that
# was drawn before the clip is excluded and counted. A fifth of the Guideline 1 difference. An
# encoding tolerance, not a threshold about patterns.
FIDELITY_TOLERANCE_NITS = 4.0

GROUND_TRUTH_MODULES = ("pattern_truth", "pattern_spec", "pattern_geometry")


# ---- the guard that makes the numbers mean anything -------------------------------------


def check_ground_truth_is_independent() -> dict[str, object]:
    """The ground truth must not import flashmap, however it is spelled or reached.

    Two checks, because either alone can be fooled: the syntax tree of each module, so a
    comment about flashmap is fine and an import is not; and a real import in a fresh
    interpreter, which catches a module that reaches flashmap through something else.

    To confirm this guard is live, add `import flashmap` to pattern_truth.py and watch the run
    refuse to start. Verified on 2026-09-17: it does, with
    "pattern_truth.py imports flashmap: ['line 47: import flashmap']".
    """
    here = Path(__file__).resolve().parent
    offenders: dict[str, list[str]] = {}
    for name in GROUND_TRUTH_MODULES:
        path = here / f"{name}.py"
        found: list[str] = []
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                found += [
                    f"line {node.lineno}: import {alias.name}"
                    for alias in node.names
                    if alias.name.split(".")[0] == "flashmap"
                ]
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] == "flashmap":
                    found.append(f"line {node.lineno}: from {node.module} import ...")
        if found:
            offenders[path.name] = found
    if offenders:
        raise SystemExit(
            "the pattern ground truth imports flashmap, so it would be grading its own "
            f"homework: {offenders}"
        )

    program = (
        "import sys; sys.path.insert(0, %r);"
        "import conformance.pattern_truth, conformance.pattern_spec, "
        "conformance.pattern_geometry;"
        "print(any(n == 'flashmap' or n.startswith('flashmap.') for n in sys.modules))"
        % str(_EVAL_DIR)
    )
    out = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, timeout=180)
    if out.returncode != 0 or out.stdout.strip() != "False":
        raise SystemExit(f"importing the pattern ground truth reached flashmap: {out.stderr}")
    return {
        "modules": list(GROUND_TRUTH_MODULES),
        "imports_flashmap": False,
        "checked": "syntax tree and a fresh interpreter import, before any clip was made",
    }


# ---- the design -------------------------------------------------------------------------


def make_clip(
    spec,
    *,
    axis: str,
    resolution: str = "480p",
    orientation: str = "vertical",
    pairs: int = 8,
    area_fraction: float = 0.60,
    motion: str = "stationary",
    contrast_multiple: float = 2.0,
    dark_multiple: float = 0.5,
    fps: int = 25,
    crf: int | None = 23,
) -> dict:
    width, height = RESOLUTIONS[resolution]
    dark_nits = dark_multiple * spec.dark_image_below_nits
    delta_nits = contrast_multiple * spec.min_nits_delta
    dark_code = spec.grey_code_for_nits(dark_nits)
    bright_code = spec.grey_code_for_nits(dark_nits + delta_nits)
    # A pattern that flashes as a whole lifts both bars by the flash difference, so the pattern
    # is still a pattern and the picture still flashes.
    lift_code = max(1, spec.grey_code_for_nits(dark_nits + 2.0 * spec.min_nits_delta) - dark_code)

    clip = {
        "axis": axis,
        "resolution": resolution,
        "width": width,
        "height": height,
        "orientation": orientation,
        "pairs": pairs,
        "area_fraction": area_fraction,
        "motion": motion,
        "contrast_multiple": contrast_multiple,
        "dark_multiple": dark_multiple,
        "fps": fps,
        "crf": crf,
        "duration_ms": DURATION_MS,
        "pattern_start_ms": PATTERN_START_MS,
        "speed_bars": SPEED_BARS,
        "dark_code": dark_code,
        "bright_code": bright_code,
        "background_code": dark_code,
        "lift_code": lift_code,
    }
    clip["clip_id"] = hashlib.sha256(
        json.dumps({k: v for k, v in clip.items() if k != "axis"}, sort_keys=True).encode()
    ).hexdigest()[:16]
    truth = clip_truth(clip, spec)
    clip["truth"] = truth.as_dict()
    clip["near_limit"] = near_limit(clip, truth, spec)
    return clip


def near_limit(clip: dict, truth, spec) -> bool:
    """Does some governing quantity sit within 15% of the limit that governs it?

    Same rule as the flash suite (docs/EVAL_PLAN.md section 4). The pair count counts when it
    is on the grid point either side of the gate, because pairs are whole numbers.
    """
    margin = 0.15
    if truth.area_limit is not None:
        if abs(truth.drawn_area_fraction - truth.area_limit) <= margin * truth.area_limit:
            return True
    if abs(truth.bar_delta_nits - spec.min_nits_delta) <= margin * spec.min_nits_delta:
        return True
    if abs(truth.darker_bar_nits - spec.dark_image_below_nits) <= (
        margin * spec.dark_image_below_nits
    ):
        return True
    return spec.more_than_pairs <= truth.pairs_drawn <= spec.more_than_pairs + 1


def spine(spec) -> list[dict]:
    rows: list[dict] = []
    for pairs in PAIRS:
        for motion in ("stationary", "reversing"):
            rows.append(make_clip(spec, axis="pairs", pairs=pairs, motion=motion))
    for area in AREAS:
        for motion in ("stationary", "reversing", "drift"):
            rows.append(make_clip(spec, axis="area", area_fraction=area, motion=motion))
    for multiple in CONTRAST_MULTIPLES:
        rows.append(make_clip(spec, axis="contrast", contrast_multiple=multiple))
    for multiple in DARK_MULTIPLES:
        rows.append(make_clip(spec, axis="darker_bar", dark_multiple=multiple))
    for orientation in ORIENTATIONS:
        for motion in ("stationary", "drift"):
            rows.append(make_clip(spec, axis="orientation", orientation=orientation, motion=motion))
    for motion in MOTIONS:
        rows.append(make_clip(spec, axis="motion", motion=motion, area_fraction=0.30))
        rows.append(make_clip(spec, axis="motion", motion=motion, area_fraction=0.60))
    for resolution in RESOLUTIONS:
        rows.append(make_clip(spec, axis="resolution", resolution=resolution))
    for crf in CRF_LEVELS:
        rows.append(make_clip(spec, axis="compression", crf=crf))
    return rows


def cross_product(spec, count: int, rng: random.Random) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    attempts = 0
    while len(rows) < count and attempts < count * 20:
        attempts += 1
        row = make_clip(
            spec,
            axis="cross",
            resolution=rng.choice(list(RESOLUTIONS)),
            orientation=rng.choice(ORIENTATIONS),
            pairs=rng.choice(PAIRS),
            area_fraction=rng.choice(AREAS),
            motion=rng.choice(MOTIONS),
            contrast_multiple=rng.choice(CONTRAST_MULTIPLES),
            dark_multiple=rng.choice(DARK_MULTIPLES),
            crf=rng.choice(CRF_LEVELS),
        )
        if row["clip_id"] in seen:
            continue
        seen.add(row["clip_id"])
        rows.append(row)
    return rows


def build_design(total: int) -> dict:
    spec = load_pattern_spec()
    rng = random.Random(SEED)
    unique: dict[str, dict] = {}
    for row in spine(spec):
        unique.setdefault(row["clip_id"], row)
    rows = list(unique.values())
    spine_count = len(rows)
    for row in cross_product(spec, max(0, total - spine_count), rng):
        if row["clip_id"] not in unique:
            unique[row["clip_id"]] = row
            rows.append(row)
    ordered = rows[:spine_count] + rows[spine_count:]
    for index, row in enumerate(ordered):
        row["order_index"] = index
    return {
        "seed": SEED,
        "spec": spec.as_dict(),
        "spine": spine_count,
        "clips": ordered,
    }


# ---- drawing and measuring --------------------------------------------------------------


def clip_frames(clip: dict) -> tuple[list[float], list[np.ndarray]]:
    """Every frame of the clip. The calm lead-in is flat background, then the pattern."""
    width, height = int(clip["width"]), int(clip["height"])
    block = block_for(
        width, height, str(clip["orientation"]), float(clip["area_fraction"]), int(clip["pairs"])
    )
    times = frame_times(float(clip["duration_ms"]), float(clip["fps"]))
    background = np.full((height, width, 3), int(clip["background_code"]), dtype=np.uint8)
    motion = str(clip["motion"])
    frames: list[np.ndarray] = []
    pattern_index = 0
    for time_ms in times:
        if time_ms < float(clip["pattern_start_ms"]):
            frames.append(background)
            continue
        frames.append(
            draw_frame(
                width,
                height,
                orientation=str(clip["orientation"]),
                block=block,
                pairs=int(clip["pairs"]),
                dark_code=int(clip["dark_code"]),
                bright_code=int(clip["bright_code"]),
                background_code=int(clip["background_code"]),
                phase_px=phase_for(motion, pattern_index, block.bar_px, float(clip["speed_bars"])),
                invert=motion == "reversing" and pattern_index % 2 == 1,
                lift_code=int(clip["lift_code"]) if motion == "flashing" and pattern_index % 2 else 0,
            )
        )
        pattern_index += 1
    return times, frames


def render_clip(clip: dict, destination: Path) -> dict:
    """Write one hazard clip. The caller owns the file and must delete it."""
    import os

    import av

    width, height = int(clip["width"]), int(clip["height"])
    times, frames = clip_frames(clip)
    container = av.open(str(destination), "w")
    try:
        stream = container.add_stream("libx264", rate=Fraction(int(clip["fps"]), 1))
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"
        stream.time_base = Fraction(1, 1000)
        stream.codec_context.time_base = Fraction(1, 1000)
        stream.codec_context.color_primaries = 1
        stream.codec_context.color_trc = 1
        stream.codec_context.colorspace = 1
        options = {"preset": "veryfast", "x264-params": "scenecut=0:keyint=25"}
        if clip["crf"] is None:
            options["qp"] = "0"
        else:
            options["crf"] = str(int(clip["crf"]))
        stream.options = options
        for time_ms, frame in zip(times, frames):
            video = av.VideoFrame.from_ndarray(np.ascontiguousarray(frame), format="rgb24")
            video.pts = int(round(time_ms))
            video.time_base = Fraction(1, 1000)
            container.mux(stream.encode(video))
        container.mux(stream.encode(None))
    finally:
        container.close()
    os.chmod(destination, 0o600)
    return {"frames_written": len(times), "bytes": destination.stat().st_size}


def fidelity(path: Path, clip: dict, spec) -> dict:
    """Did the bar to bar difference that came back out of the encoder match the drawn one.

    Decoded with av, measured on the block, converted to cd/m2 with the same BT.1886 mapping
    the ground truth uses. It does not import flashmap and it decides nothing about patterns.
    """
    import av

    block = block_for(
        int(clip["width"]),
        int(clip["height"]),
        str(clip["orientation"]),
        float(clip["area_fraction"]),
        int(clip["pairs"]),
    )
    def drawn_delta(pattern_index: int) -> float:
        """The bar to bar difference drawn on this pattern frame.

        A flashing clip lifts both bars every other frame, and BT.1886 is a curve, so the same
        pair of grey codes is a bigger difference in cd/m2 once it is lifted. Comparing every
        frame against the unlifted difference threw out three quarters of the flashing clips,
        which is how this came to be measured per frame.
        """
        lift = int(clip["lift_code"]) if clip["motion"] == "flashing" and pattern_index % 2 else 0
        low = spec.nits_of_grey_code(min(255, int(clip["dark_code"]) + lift))
        high = spec.nits_of_grey_code(min(255, int(clip["bright_code"]) + lift))
        return abs(high - low)

    height = int(clip["height"])
    gaps: list[float] = []
    pattern_index = 0
    measured: list[float] = []
    with av.open(str(path)) as container:
        video = container.streams.video[0]
        video.thread_type = "AUTO"
        for frame in container.decode(video):
            if frame.pts is None:
                continue
            # The muxer rewrites the time base, so a raw pts is not milliseconds.
            time_ms = float(frame.pts * frame.time_base * 1000)
            if time_ms < float(clip["pattern_start_ms"]):
                continue
            # The Y plane as coded, which is limited range, so undo that before BT.1886. This
            # is the same normalisation flashmap's decoder does, written out here rather than
            # imported, because this module may not reach into the thing it is checking.
            luma = frame.to_ndarray(format="yuv420p")[:height]
            grey = luma[block.y0 : block.y1, block.x0 : block.x1]
            if grey.size == 0:
                continue
            lo_level = max(0.0, (float(np.percentile(grey, 5)) - 16.0) / 219.0)
            hi_level = max(0.0, (float(np.percentile(grey, 95)) - 16.0) / 219.0)
            delta = (
                spec.peak_nits * hi_level**spec.bt1886_gamma
                - spec.peak_nits * lo_level**spec.bt1886_gamma
            )
            measured.append(delta)
            gaps.append(abs(delta - drawn_delta(pattern_index)))
            pattern_index += 1
    if not measured:
        return {"frames": 0, "measured_delta_nits": None, "typical_gap_nits": None, "ok": False}
    gap = float(np.median(gaps))
    return {
        "frames": len(measured),
        "drawn_delta_nits": round(drawn_delta(0), 3),
        "measured_delta_nits": round(float(np.median(measured)), 3),
        "typical_gap_nits": round(gap, 3),
        "ok": gap <= FIDELITY_TOLERANCE_NITS,
    }


def measure(clip: dict) -> dict:
    """One clip, start to finish, with the file gone before this function returns."""
    from flashmap import analyze_file, get_profile

    spec = load_pattern_spec()
    path = scratch_dir() / f"{HAZARD_PREFIX}pattern_{clip['clip_id']}.mp4"
    row: dict[str, object] = {"clip_id": clip["clip_id"], "axis": clip.get("axis")}
    try:
        row["encode"] = render_clip(clip, path)
        row["fidelity"] = fidelity(path, clip, spec)
        started = time.time()
        result = analyze_file(path, get_profile(PROFILE))
        row["seconds"] = round(time.time() - started, 3)
        row["first_pts_ms"] = result.first_pts_ms
        row["pattern_segments"] = [
            {
                "start_ms": segment.start_ms,
                "end_ms": segment.end_ms,
                "stripe_pairs": segment.stripe_pairs,
                "area_fraction": segment.area_fraction,
                "area_limit": segment.area_limit,
                "motion": segment.motion,
            }
            for segment in result.pattern_segments
        ]
        row["pattern_exemptions"] = [
            {
                "start_ms": exemption.start_ms,
                "end_ms": exemption.end_ms,
                "area_fraction": exemption.area_fraction,
            }
            for exemption in result.pattern_exemptions
        ]
        row["flash_segment_count"] = len(result.segments)
        row["flash_pass"] = result.flash_passes
    except Exception as error:  # noqa: BLE001 - one bad clip must not stop the suite
        row["error"] = f"{type(error).__name__}: {error}"
    finally:
        # The clip goes away here whatever happened above. Nothing keeps a strobe.
        try:
            if path.exists():
                path.unlink()
        except OSError as error:  # pragma: no cover
            row["delete_error"] = str(error)
    return row


def _terminate(signum, frame):  # noqa: ARG001
    raise SystemExit(f"stopped by signal {signum}")


def _init_worker() -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, _terminate)


def sweep_leftovers(fail: bool = True) -> int:
    """No hazard file outlives the job. Anything still here is removed and the run fails."""
    leftovers = sorted(scratch_dir().glob(f"{HAZARD_PREFIX}pattern_*"))
    for path in leftovers:
        try:
            path.unlink()
        except OSError:
            pass
    if leftovers and fail:
        print(
            f"SAFETY: {len(leftovers)} hazard file(s) outlived their job and were removed. "
            "That must not happen, so this run is a failure.",
            file=sys.stderr,
        )
    return len(leftovers)


# ---- scoring ----------------------------------------------------------------------------


class Tally:
    def __init__(self) -> None:
        self.tp = self.fp = self.fn = self.tn = 0
        self.recall_groups: list[tuple[int, int]] = []
        self.precision_groups: list[tuple[int, int]] = []

    def add(self, predicted: set[int], truth: set[int], universe: list[int]) -> None:
        counts = confusion(predicted, truth, universe=universe)
        self.tp += counts["tp"]
        self.fp += counts["fp"]
        self.fn += counts["fn"]
        self.tn += counts["tn"]
        if counts["tp"] + counts["fn"]:
            self.recall_groups.append((counts["tp"], counts["tp"] + counts["fn"]))
        if counts["tp"] + counts["fp"]:
            self.precision_groups.append((counts["tp"], counts["tp"] + counts["fp"]))

    def as_dict(self) -> dict[str, object]:
        precision = rate_with_interval(self.tp, self.tp + self.fp)
        recall = rate_with_interval(self.tp, self.tp + self.fn)
        return {
            "counts": {"tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn},
            "precision": precision,
            "recall": recall,
            "f1": f1(precision["value"], recall["value"]),
            "precision_bootstrap_over_clips": bootstrap_groups(self.precision_groups),
            "recall_bootstrap_over_clips": bootstrap_groups(self.recall_groups),
        }


def predicted_windows(row: dict, n_windows: int, min_overlap: float = 0.0) -> set[int]:
    intervals = [(s["start_ms"], s["end_ms"]) for s in row.get("pattern_segments", [])]
    origin = row.get("first_pts_ms") or 0.0
    return windows_from_intervals(
        intervals, n_windows=n_windows, origin_ms=origin, min_overlap=min_overlap
    )


def score(design: dict, rows: list[dict], independence: dict) -> dict:
    clips = {clip["clip_id"]: clip for clip in design["clips"]}
    spec = design["spec"]

    exclusions: dict[str, int] = defaultdict(int)
    kept: list[tuple[dict, dict]] = []
    for row in rows:
        clip = clips[row["clip_id"]]
        if "error" in row:
            exclusions["analysis error"] += 1
            continue
        fid = row.get("fidelity") or {}
        if not fid.get("ok"):
            exclusions["the encoded bar difference did not match the drawn one"] += 1
            continue
        kept.append((row, clip))

    # Three window universes, all published, none of them the only one anybody may quote.
    #
    # `all_windows` is the headline and the least flattering. Under the any overlap rule a hide
    # that starts one frame before the pattern does marks the whole calm second before it, so
    # most of its false positives are 40 ms of lead-in costing a whole window.
    # `pattern_windows_only` drops that calm second, so it says how the rule does on the windows
    # the pattern is actually in. `pattern_windows_after_the_first` drops the window the pattern
    # arrives in as well, which is the window a causal detector spends working out how the
    # pattern moves. The half window rule below is the other half of the story: it asks for half
    # a window of cover before a window counts, which is what removes the lead-in artefact
    # without removing any real window.
    universes = {
        "all_windows": lambda truth, n: list(range(n)),
        "pattern_windows_only": lambda truth, n: list(truth["pattern_windows"]),
        "pattern_windows_after_the_first": lambda truth, n: [
            k for k in truth["pattern_windows"] if k != truth["establishing_window"]
        ],
    }

    tallies: dict[str, Tally] = {name: Tally() for name in universes}
    half_window = Tally()
    clip_level = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    curves: dict[str, dict[str, Tally]] = defaultdict(lambda: defaultdict(Tally))
    curve_clips: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    exemption_rows = {"drift_clips": 0, "drift_clips_with_an_exemption": 0, "exempt_ms": 0.0}
    false_positive_reasons: dict[str, int] = defaultdict(int)
    windows_total = positives_total = 0

    for row, clip in kept:
        truth_row = clip["truth"]
        n_windows = truth_row["n_windows"]
        truth = set(truth_row["positive_windows"])
        predicted = predicted_windows(row, n_windows)
        windows_total += n_windows
        positives_total += len(truth)

        for name, universe_of in universes.items():
            universe = universe_of(truth_row, n_windows)
            tallies[name].add(predicted & set(universe), truth & set(universe), universe)
        half_window.add(
            predicted_windows(row, n_windows, 0.5), truth, list(range(n_windows))
        )

        if bool(predicted) and bool(truth):
            clip_level["tp"] += 1
        elif bool(predicted):
            clip_level["fp"] += 1
        elif bool(truth):
            clip_level["fn"] += 1
        else:
            clip_level["tn"] += 1

        if truth_row["drawn_motion"] == "drift":
            exemption_rows["drift_clips"] += 1
            if row.get("pattern_exemptions"):
                exemption_rows["drift_clips_with_an_exemption"] += 1
        exemption_rows["exempt_ms"] += sum(
            e["end_ms"] - e["start_ms"] for e in row.get("pattern_exemptions", [])
        )

        for window in predicted - truth:
            if window not in truth_row["pattern_windows"]:
                false_positive_reasons["the calm second before the pattern arrives"] += 1
            elif window == truth_row["establishing_window"]:
                false_positive_reasons["the window the pattern arrives in"] += 1
            elif truth_row["exempt"]:
                false_positive_reasons["a smooth flow the detector would not call smooth"] += 1
            elif not truth_row["area_qualifies"]:
                false_positive_reasons["under the area limit"] += 1
            elif not truth_row["pairs_qualify"]:
                false_positive_reasons["under the stripe count"] += 1
            elif not truth_row["contrast_qualifies"]:
                false_positive_reasons["under the bar to bar difference"] += 1
            else:
                false_positive_reasons["something else"] += 1

        for axis, key in (
            ("pairs", truth_row["pairs_drawn"]),
            ("drawn_motion", truth_row["drawn_motion"]),
            ("orientation", clip["orientation"]),
            ("area_over_limit", _band(truth_row, spec)),
            ("contrast_over_limit", round(truth_row["bar_delta_nits"] / spec["min_nits_delta"], 1)),
            ("resolution", clip["resolution"]),
            ("compression_crf", "lossless" if clip["crf"] is None else clip["crf"]),
            ("near_limit", bool(clip["near_limit"])),
        ):
            bucket = str(key)
            curve_clips[axis][bucket] += 1
            curves[axis][bucket].add(predicted, truth, list(range(n_windows)))

    curve_out: dict[str, list] = {}
    for axis, buckets in curves.items():
        points = []
        for bucket, tally in buckets.items():
            summary = tally.as_dict()
            points.append(
                {
                    "bucket": bucket,
                    "clips": curve_clips[axis][bucket],
                    "precision": summary["precision"]["value"],
                    "precision_wilson": [
                        summary["precision"]["wilson_lo"],
                        summary["precision"]["wilson_hi"],
                    ],
                    "recall": summary["recall"]["value"],
                    "recall_wilson": [
                        summary["recall"]["wilson_lo"],
                        summary["recall"]["wilson_hi"],
                    ],
                    "counts": summary["counts"],
                }
            )
        points.sort(key=lambda point: _bucket_order(point["bucket"]))
        curve_out[axis] = points

    def flat(tally: Tally, prefix: str) -> dict[str, object]:
        summary = tally.as_dict()
        out: dict[str, object] = {}
        for metric in ("precision", "recall"):
            value = summary[metric]["value"]
            out[f"{prefix}_{metric}"] = None if value is None else round(value, 3)
            out[f"{prefix}_{metric}_lo"] = round(summary[metric]["wilson_lo"], 3)
            out[f"{prefix}_{metric}_hi"] = round(summary[metric]["wilson_hi"], 3)
            out[f"{prefix}_{metric}_denominator"] = summary[metric]["denominator"]
        out[f"{prefix}_f1"] = None if summary["f1"] is None else round(summary["f1"], 3)
        return out

    return {
        "generated_on": time.strftime("%Y-%m-%d"),
        "rule": "ITU-R BT.1702-3 Attachment 1 to Annex 1 (informative), regular patterns",
        "profile": PROFILE,
        "not_a_wcag_measurement": (
            "WCAG 2.2 SC 2.3.1 does not cover regular patterns, so no number in this file is a "
            "WCAG number and none of it may be described as WCAG conformance."
        ),
        "ground_truth": {
            "source": "computed from the spec text by eval/conformance/pattern_truth.py",
            **independence,
            "spec_file": spec["source"],
            "spec_sha256": spec["source_sha256"],
            "design_seed": design["seed"],
        },
        "sample": {
            "clips_designed": len(clips),
            "clips_measured": len(rows),
            "clips_kept": len(kept),
            "windows_kept": windows_total,
            "ground_truth_positive_windows": positives_total,
        },
        "exclusions": dict(exclusions),
        "published": {
            **flat(tallies["all_windows"], "pattern"),
            **flat(tallies["pattern_windows_only"], "pattern_on_screen"),
            **flat(tallies["pattern_windows_after_the_first"], "pattern_settled"),
            **flat(half_window, "pattern_half_window"),
            "clip_level_precision": round(
                clip_level["tp"] / max(1, clip_level["tp"] + clip_level["fp"]), 3
            ),
            "clip_level_recall": round(
                clip_level["tp"] / max(1, clip_level["tp"] + clip_level["fn"]), 3
            ),
        },
        "headline_all_windows": tallies["all_windows"].as_dict(),
        "pattern_windows_only": tallies["pattern_windows_only"].as_dict(),
        "pattern_windows_after_the_first": tallies["pattern_windows_after_the_first"].as_dict(),
        "half_window_rule": half_window.as_dict(),
        "clip_level": {
            "counts": clip_level,
            "precision": rate_with_interval(clip_level["tp"], clip_level["tp"] + clip_level["fp"]),
            "recall": rate_with_interval(clip_level["tp"], clip_level["tp"] + clip_level["fn"]),
        },
        "where_the_false_positives_are": dict(false_positive_reasons),
        "smooth_flow_exemption": {
            **exemption_rows,
            "meaning": (
                "a drift clip is drawn flowing smoothly one way, which Attachment 1 exempts, so "
                "its true answer is no hidden window at all. Every drift clip the detector "
                "hides instead is a false positive here, on purpose: the exemption is the one "
                "place where a wrong call hides a hazard from a child rather than covering a "
                "few safe seconds, so it is applied only when the flow is unambiguous and the "
                "cost of that is this number."
            ),
        },
        "error_curves": curve_out,
        "window_rules": {
            "primary": "any overlap at all between a pattern segment and the window",
            "sensitivity": "at least half the window covered, reported as the half window rule",
        },
        "known_gaps": [
            "radial, curved and dotted patterns are in BT.1702-3's wording and are not drawn "
            "by this suite. Only straight stripes, in three orientations, are measured.",
            "letterboxed pictures are not in this suite. The flash suite covers that path.",
            "no real footage. Every clip here is generated.",
        ],
    }


def _band(truth_row: dict, spec: dict) -> str:
    limit = truth_row["area_limit"]
    if limit is None:
        return "exempt"
    ratio = truth_row["drawn_area_fraction"] / limit
    edges = [0.5, 0.85, 0.95, 1.0, 1.05, 1.15, 1.5, 2.0]
    if ratio < edges[0]:
        return f"under {edges[0]:g}"
    for low, high in zip(edges, edges[1:]):
        if low <= ratio < high:
            return f"{low:g} to {high:g}"
    return f"{edges[-1]:g} and over"


def _bucket_order(bucket: str) -> tuple[int, float, str]:
    try:
        return (0, float(bucket), "")
    except ValueError:
        pass
    found = re.findall(r"-?\d*\.?\d+", bucket)
    if found:
        return (0, float(found[0]) - (0.001 if bucket.startswith("under") else 0.0), "")
    return (1, 0.0, bucket)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--total", type=int, default=200)
    parser.add_argument("--limit", type=int, default=None, help="measure only this many clips")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("-o", "--out", type=Path, default=OUT)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="re-score the rows already in the raw file and make no clip at all",
    )
    arguments = parser.parse_args()

    independence = check_ground_truth_is_independent()
    print("ground truth checked: it cannot import flashmap", flush=True)

    if arguments.score_only:
        design = build_design(arguments.total)
        rows = [
            json.loads(line)
            for line in arguments.raw.read_text().splitlines()
            if line.strip()
        ]
        report = score(design, rows, independence)
        report["sample"]["hazard_files_that_leaked"] = 0
        report["sample"]["scored_from"] = str(arguments.raw.relative_to(REPO))
        arguments.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
        _print_summary(report, arguments.out)
        return 0

    swept = sweep_leftovers(fail=False)
    if swept:
        print(f"swept {swept} hazard file(s) left by an earlier run", file=sys.stderr)
    signal.signal(signal.SIGTERM, _terminate)

    design = build_design(arguments.total)
    todo = design["clips"][: arguments.limit] if arguments.limit else design["clips"]
    print(f"{len(todo)} clips, {arguments.workers} workers", flush=True)

    rows: list[dict] = []
    started = time.time()
    with ProcessPoolExecutor(max_workers=arguments.workers, initializer=_init_worker) as pool:
        futures = {pool.submit(measure, clip): clip for clip in todo}
        try:
            for done, future in enumerate(as_completed(futures), start=1):
                rows.append(future.result())
                if done % 25 == 0:
                    rate = done / max(1e-9, time.time() - started)
                    print(
                        f"{done}/{len(todo)} clips, {rate:.2f} clips/s, "
                        f"about {(len(todo) - done) / max(1e-9, rate) / 60:.1f} min left",
                        flush=True,
                    )
        except BaseException as stop:  # noqa: BLE001 - Ctrl-C, SIGTERM, anything
            print(f"stopping ({type(stop).__name__}), cancelling the queue", file=sys.stderr)
            pool.shutdown(cancel_futures=True, wait=True)
            sweep_leftovers(fail=False)
            raise

    leftovers = sweep_leftovers()
    report = score(design, rows, independence)
    report["sample"]["hazard_files_that_leaked"] = leftovers
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
    # The rows, so the scoring can be re-run offline without making a single clip again. They
    # hold intervals and counts. No pixels, no clip, nothing hazardous.
    arguments.raw.write_text("".join(json.dumps(row) + "\n" for row in rows))

    _print_summary(report, arguments.out)
    return 1 if leftovers else 0


def _print_summary(report: dict, out: Path) -> None:
    def line(label: str, table: dict) -> str:
        parts = [f"  {label}:"]
        for metric in ("precision", "recall"):
            row = table[metric]
            value = "n/a" if row["value"] is None else f"{row['value']:.4f}"
            parts.append(
                f"{metric} {value} [{row['wilson_lo']:.4f}, {row['wilson_hi']:.4f}] "
                f"n={row['denominator']}"
            )
        return "  ".join(parts)

    print(
        f"{report['sample']['clips_kept']} clips kept of {report['sample']['clips_measured']} "
        f"measured, {report['sample']['windows_kept']} windows.\n"
        + line("all windows      ", report["headline_all_windows"])
        + "\n"
        + line("pattern on screen", report["pattern_windows_only"])
        + "\n"
        + line("half window rule ", report["half_window_rule"])
        + f"\n  -> {out}",
        flush=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
