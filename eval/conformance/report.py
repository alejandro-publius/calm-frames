#!/usr/bin/env python3
"""Turn the conformance rows into numbers: precision, recall, intervals, error curves.

Reads the committed design (which carries the ground truth) and results/conformance_raw.jsonl
(which carries what each detector said), and writes results/conformance.json. It is offline,
deterministic and re-runnable: no clip is generated here and nothing is measured again.

What it will not do:

- publish a rate without the counts it came from;
- quietly drop a clip. Every exclusion is counted and named next to the metric it affects;
- treat a window a baseline never saw as a window the baseline got wrong. ffmpeg's filter has
  its first second dropped, so window 0 of every clip is missing from its denominator, and the
  baseline table therefore reports every detector twice: once over all windows and once over
  the windows that every detector saw.

The headline interval is Wilson, as the plan says for this set, because each clip was generated
independently. The bootstrap over clips is reported beside it, and it is not automatically the
wider of the two: recall clusters by clip so its bootstrap comes out wider, while precision is
nearly the same on every positive clip, so its bootstrap comes out narrower. Both are in the
file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from metrics import bootstrap_groups, confusion, f1, rate_with_interval, windows_from_intervals  # noqa: E402

REPO = _EVAL_DIR.parent
DESIGN = REPO / "results" / "conformance_design.json"
RAW = REPO / "results" / "conformance_raw.jsonl"
OUT = REPO / "results" / "conformance.json"

# How far the decoded mean relative luminance may sit from the waveform the design asked for
# before the clip is excluded and counted. EVAL_PLAN section 4 sets 2% of full scale, with a
# per axis tolerance where deviation is part of the design. Lossy coding at the highest
# quantiser is the one case that needs the wider band.
FIDELITY_TOLERANCE = 0.02
FIDELITY_TOLERANCE_HIGH_CRF = 0.04

# The naive baseline's own rule, from eval/baselines/naive_luma_diff/run.py: a segment of a
# single frame is a cut, not a flash. Not a spec number.
NAIVE_MIN_FRAMES = 2


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, timeout=20
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---- detectors, each reduced to the windows it called positive -------------------------


def flashmap_windows(row: dict, n_windows: int, min_overlap: float, tight: bool) -> set[int]:
    segments = row.get("flashmap", {}).get("segments", [])
    if tight:
        intervals = [(s["flash_first_ms"], s["flash_last_ms"]) for s in segments]
    else:
        intervals = [(s["start_ms"], s["end_ms"]) for s in segments]
    origin = row.get("flashmap", {}).get("first_pts_ms") or 0.0
    return windows_from_intervals(
        intervals, n_windows=n_windows, origin_ms=origin, min_overlap=min_overlap
    )


def naive_windows(row: dict, rung: int) -> set[int]:
    data = row.get("baselines", {}).get("naive_luma_diff")
    if not data:
        return set()
    counts = data["frames_over_per_window"].get(str(rung), [])
    return {index for index, count in enumerate(counts) if count >= NAIVE_MIN_FRAMES}


def ffmpeg_windows(row: dict, rung: float) -> set[int]:
    data = row.get("baselines", {}).get("ffmpeg_photosensitivity")
    if not data:
        return set()
    return {
        index
        for index, value in enumerate(data["max_ymax_per_window"])
        if value > rung and data["frames_seen_per_window"][index] > 0
    }


def ffmpeg_universe(row: dict, n_windows: int) -> list[int]:
    """The windows ffmpeg's filter actually saw: its first second is dropped."""
    data = row.get("baselines", {}).get("ffmpeg_photosensitivity")
    if not data:
        return []
    return [
        index
        for index in range(n_windows)
        if index < len(data["frames_seen_per_window"]) and data["frames_seen_per_window"][index] > 0
    ]


# ---- scoring ---------------------------------------------------------------------------


class Tally:
    """Counts for one detector under one window rule, plus the per clip groups it came from."""

    def __init__(self) -> None:
        self.tp = self.fp = self.fn = self.tn = 0
        self.recall_groups: list[tuple[int, int]] = []
        self.precision_groups: list[tuple[int, int]] = []
        self.segment_found = 0
        self.segment_total = 0
        self.onset_leads: list[int] = []

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
        if truth:
            self.segment_total += 1
            if predicted & truth:
                self.segment_found += 1
                self.onset_leads.append(min(predicted) - min(truth))

    def as_dict(self) -> dict[str, object]:
        precision = rate_with_interval(self.tp, self.tp + self.fp)
        recall = rate_with_interval(self.tp, self.tp + self.fn)
        out: dict[str, object] = {
            "counts": {"tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn},
            "precision": precision,
            "recall": recall,
            "f1": f1(precision["value"], recall["value"]),
            "precision_bootstrap_over_clips": bootstrap_groups(self.precision_groups),
            "recall_bootstrap_over_clips": bootstrap_groups(self.recall_groups),
            "segment_recall": rate_with_interval(self.segment_found, self.segment_total),
        }
        if self.onset_leads:
            out["onset_lead_windows"] = {
                "median": statistics.median(self.onset_leads),
                "min": min(self.onset_leads),
                "max": max(self.onset_leads),
                "share_early_or_on_time": sum(1 for v in self.onset_leads if v <= 0)
                / len(self.onset_leads),
                "n": len(self.onset_leads),
                "meaning": (
                    "first predicted positive window minus first true positive window, so a "
                    "negative number means the detector was already hiding before the flashing "
                    "started"
                ),
            }
        negatives = self.fp + self.tn
        if negatives:
            out["false_positive_seconds_per_minute_of_calm"] = 60.0 * self.fp / negatives
            out["calm_windows"] = negatives
        return out


def excluded_reason(row: dict, clip: dict) -> str | None:
    if "error" in row:
        return "analysis error"
    fidelity = row.get("fidelity") or {}
    deviation = fidelity.get("max_abs_deviation")
    if deviation is None:
        return "no decodable frames"
    tolerance = (
        FIDELITY_TOLERANCE_HIGH_CRF
        if (clip.get("crf") is not None and int(clip["crf"]) >= 28)
        else FIDELITY_TOLERANCE
    )
    if deviation > tolerance:
        return "decoded luminance off the intended waveform"
    if clip["timing"] == "cfr" and not fidelity.get("timestamps_match", False):
        return "frame timestamps did not match the requested constant rate"
    return None


def band(value: float, edges: list[float]) -> str:
    """A readable band label for a continuous axis.

    Exact values make a curve with one or two clips per point, which is unreadable and whose
    intervals say nothing. The edges are placed tightly around each limit, because that is
    where the answer changes, and loosely away from it, where it does not.
    """
    if value < edges[0]:
        return f"under {edges[0]:g}"
    for low, high in zip(edges, edges[1:]):
        if low <= value < high:
            return f"{low:g} to {high:g}"
    return f"{edges[-1]:g} and over"


def _near_split(points: list[dict]) -> dict[str, object]:
    """Recall and its counts, split by whether the clip sits near a limit or clear of one."""
    out: dict[str, object] = {}
    for point in points:
        key = "recall_near_limits" if str(point["bucket"]) == "True" else "recall_away_from_limits"
        row = point.get("flashmap")
        if not isinstance(row, dict):
            continue
        value = row.get("recall")
        out[key] = None if value is None else round(value, 3)
        out[f"{key}_clips"] = point["clips"]
        out[f"{key}_positive_windows"] = row["counts"]["tp"] + row["counts"]["fn"]
    return out


def _bucket_order(bucket: object) -> tuple[int, float, str]:
    """Sort a curve's buckets: numbers in order, bands by their lower edge, names last."""
    text = str(bucket)
    try:
        return (0, float(text), "")
    except ValueError:
        pass
    found = re.findall(r"-?\d*\.?\d+", text)
    if found:
        low = float(found[0])
        return (0, low - (0.001 if text.startswith("under") else 0.0), "")
    return (1, 0.0, text)


def bucket_key(clip: dict, truth: dict, axis: str, spec: dict):
    if axis == "flash_rate_hz":
        # float, always: the spine writes 10 and the cross product writes 10.0, and two buckets
        # for one rate would split the very points this axis exists to compare.
        return float(clip["flash_hz"])
    if axis == "observed_flash_rate_hz":
        return round(truth["observed_flash_rate_hz"])
    if axis == "luminance_step_over_limit":
        return band(
            truth["general_delta"] / spec["general_min_delta"],
            [0.5, 0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.25, 2.0],
        )
    if axis == "field_coverage_over_limit":
        return band(
            truth["field_coverage"] / spec["area_fraction_limit"],
            [0.5, 0.85, 0.95, 1.0, 1.05, 1.15, 1.5, 2.0, 4.0],
        )
    if axis == "area_fraction_of_picture":
        return band(truth["drawn_area_fraction"], [0.02, 0.05, 0.1, 0.2, 0.35, 0.5])
    if axis == "ucs_distance_over_limit":
        return band(
            truth["ucs_distance"] / spec["red_min_ucs_distance"],
            [0.5, 0.9, 0.95, 1.0, 1.05, 1.1, 1.3],
        )
    if axis == "frame_rate":
        return clip["fps"]
    if axis == "timing":
        return clip["timing"]
    if axis == "resolution":
        return clip["resolution"]
    if axis == "compression_crf":
        return "lossless" if clip["crf"] is None else clip["crf"]
    if axis == "color_tagging":
        return clip["color_tagging"]
    if axis == "shape":
        return clip["shape"]
    if axis == "red_mode":
        return clip["red_mode"]
    if axis == "near_threshold":
        return bool(clip["near_threshold"])
    if axis == "letterbox":
        return clip["letterbox_fraction"]
    raise ValueError(axis)


CURVE_AXES = [
    "flash_rate_hz",
    "observed_flash_rate_hz",
    "luminance_step_over_limit",
    "field_coverage_over_limit",
    "area_fraction_of_picture",
    "ucs_distance_over_limit",
    "frame_rate",
    "timing",
    "resolution",
    "compression_crf",
    "color_tagging",
    "shape",
    "red_mode",
    "letterbox",
    "near_threshold",
]


def build(design_path: Path, raw_path: Path) -> dict:
    design = json.loads(design_path.read_text())
    spec = design["spec"]
    clips = {clip["clip_id"]: clip for clip in design["clips"]}

    rows = []
    seen: set[str] = set()
    with raw_path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row["clip_id"] in seen or row["clip_id"] not in clips:
                continue
            seen.add(row["clip_id"])
            rows.append(row)

    exclusions: dict[str, int] = defaultdict(int)
    kept: list[tuple[dict, dict]] = []
    for row in rows:
        clip = clips[row["clip_id"]]
        reason = excluded_reason(row, clip)
        if reason:
            exclusions[reason] += 1
            continue
        kept.append((row, clip))

    detectors = {
        "flashmap": lambda row, n, overlap: flashmap_windows(row, n, overlap, tight=False),
        "flashmap_tight_bounds": lambda row, n, overlap: flashmap_windows(
            row, n, overlap, tight=True
        ),
    }
    naive_ladder = sorted(
        {
            int(rung)
            for row, _ in kept
            for rung in row.get("baselines", {})
            .get("naive_luma_diff", {})
            .get("frames_over_per_window", {})
        }
    )
    ffmpeg_ladder = [1, 2, 4, 8, 16, 32]

    tallies: dict[str, dict[str, Tally]] = defaultdict(lambda: defaultdict(Tally))
    clip_level = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    windows_total = 0
    positives_total = 0
    hidden_windows = 0
    baseline_rows = 0
    per_row: list[tuple[dict, dict, dict[str, set[int]], list[int], list[int], set[int]]] = []

    for row, clip in kept:
        truth_row = clip["truth"]
        n_windows = truth_row["n_windows"]
        truth = set(truth_row["positive_windows"])
        every_window = list(range(n_windows))
        shared = ffmpeg_universe(row, n_windows) if row.get("baselines") else every_window
        if row.get("baselines"):
            baseline_rows += 1
        windows_total += n_windows
        positives_total += len(truth)

        predictions: dict[str, set[int]] = {}
        for name, call in detectors.items():
            predictions[name] = call(row, n_windows, 0.0)
            predictions[f"{name}@half_window"] = call(row, n_windows, 0.5)
        if row.get("baselines"):
            for rung in naive_ladder:
                predictions[f"naive_luma_diff@{rung}"] = naive_windows(row, rung)
            for rung in ffmpeg_ladder:
                predictions[f"ffmpeg_photosensitivity@{rung}"] = ffmpeg_windows(row, rung)

        hidden_windows += len(predictions["flashmap"])
        for name, predicted in predictions.items():
            is_baseline = "@" in name and not name.startswith("flashmap")
            if not is_baseline:
                tallies["all_windows"][name].add(predicted, truth, every_window)
            tallies["windows_every_detector_saw"][name].add(
                predicted & set(shared), truth & set(shared), shared
            )
        per_row.append((row, clip, predictions, every_window, shared, truth))

        predicted_fail = bool(predictions["flashmap"])
        truth_fail = bool(truth)
        if predicted_fail and truth_fail:
            clip_level["tp"] += 1
        elif predicted_fail:
            clip_level["fp"] += 1
        elif truth_fail:
            clip_level["fn"] += 1
        else:
            clip_level["tn"] += 1

    def operating_point(prefix: str, ladder: list, universe: str) -> dict:
        sweep = []
        for rung in ladder:
            name = f"{prefix}@{rung}"
            tally = tallies[universe].get(name)
            if tally is None:
                continue
            summary = tally.as_dict()
            sweep.append(
                {
                    "threshold": rung,
                    "precision": summary["precision"]["value"],
                    "recall": summary["recall"]["value"],
                    "f1": summary["f1"],
                    "counts": summary["counts"],
                }
            )
        best = max(
            (point for point in sweep if point["f1"] is not None),
            key=lambda point: point["f1"],
            default=None,
        )
        return {"sweep": sweep, "best_f1_operating_point": best}

    naive_best = operating_point("naive_luma_diff", naive_ladder, "windows_every_detector_saw")
    ffmpeg_best = operating_point(
        "ffmpeg_photosensitivity", ffmpeg_ladder, "windows_every_detector_saw"
    )

    naive_pick = (naive_best["best_f1_operating_point"] or {}).get("threshold")
    ffmpeg_pick = (ffmpeg_best["best_f1_operating_point"] or {}).get("threshold")

    def labelled(universe: str) -> dict[str, str]:
        """Detector key to the name it is published under, for one window universe."""
        names = {
            "flashmap": "flashmap (this project)",
            "flashmap@half_window": "flashmap, half window rule",
            "flashmap_tight_bounds": "flashmap, flash bounds only (diagnostic, not the hide)",
        }
        if universe == "windows_every_detector_saw":
            if naive_pick is not None:
                names[f"naive_luma_diff@{naive_pick}"] = (
                    f"naive mean luminance differencing (best threshold on this suite, "
                    f"{naive_pick} luma codes)"
                )
            if ffmpeg_pick is not None:
                names[f"ffmpeg_photosensitivity@{ffmpeg_pick}"] = (
                    f"ffmpeg photosensitivity filter (best difference threshold on this suite, "
                    f"{ffmpeg_pick} codes, first second dropped)"
                )
        return names

    def table(universe: str) -> dict:
        return {
            title: tallies[universe][key].as_dict()
            for key, title in labelled(universe).items()
            if key in tallies[universe]
        }

    # Error curves. flashmap is curved over every window; the baselines are curved over the
    # windows every detector saw, because ffmpeg's filter never saw the first second.
    curve_detectors = ["flashmap"]
    if naive_pick is not None:
        curve_detectors.append(f"naive_luma_diff@{naive_pick}")
    if ffmpeg_pick is not None:
        curve_detectors.append(f"ffmpeg_photosensitivity@{ffmpeg_pick}")

    curves: dict[str, dict[str, dict[str, Tally]]] = {
        axis: defaultdict(lambda: defaultdict(Tally)) for axis in CURVE_AXES
    }
    curve_clips: dict[str, dict[str, int]] = {axis: defaultdict(int) for axis in CURVE_AXES}
    curve_near: dict[str, dict[str, int]] = {axis: defaultdict(int) for axis in CURVE_AXES}
    for row, clip, predictions, every_window, shared, truth in per_row:
        for axis in CURVE_AXES:
            key = str(bucket_key(clip, clip["truth"], axis, spec))
            curve_clips[axis][key] += 1
            if clip["near_threshold"]:
                curve_near[axis][key] += 1
            for name in curve_detectors:
                if name not in predictions:
                    continue
                if name == "flashmap":
                    curves[axis][key][name].add(predictions[name], truth, every_window)
                else:
                    curves[axis][key][name].add(
                        predictions[name] & set(shared), truth & set(shared), shared
                    )

    curve_out: dict[str, list] = {}
    for axis, buckets in curves.items():
        points = []
        for key, per_detector in buckets.items():
            clips_here = curve_clips[axis][key]
            point: dict[str, object] = {
                "bucket": key,
                "clips": clips_here,
                # How much of this bucket is boundary cases. The design puts its near threshold
                # rows at the flash rates either side of the limit, so a dip on the rate axis
                # can be other limits being near rather than the rate being hard. Without this
                # share next to the point, that confound is invisible.
                "near_threshold_share": round(curve_near[axis][key] / clips_here, 3)
                if clips_here
                else None,
            }
            for name, tally in per_detector.items():
                summary = tally.as_dict()
                point[name] = {
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
            points.append(point)
        points.sort(key=lambda point: _bucket_order(point["bucket"]))
        curve_out[axis] = points

    def flat(tally_name: str, universe: str, prefix: str) -> dict[str, object]:
        """Flat, marker friendly copies of the numbers a document is allowed to quote.

        eval/readme_sync.py reads a dotted path with no spaces in it, and the table keys here
        are sentences. So the publishable numbers get short keys of their own, rounded to what
        a document should show, and a document quotes these and nothing else.
        """
        tally = tallies[universe].get(tally_name)
        if tally is None:
            return {}
        row = tally.as_dict()
        out: dict[str, object] = {}
        for metric in ("precision", "recall"):
            value = row[metric]["value"]
            out[f"{prefix}_{metric}"] = None if value is None else round(value, 3)
            out[f"{prefix}_{metric}_lo"] = round(row[metric]["wilson_lo"], 3)
            out[f"{prefix}_{metric}_hi"] = round(row[metric]["wilson_hi"], 3)
            out[f"{prefix}_{metric}_denominator"] = row[metric]["denominator"]
        out[f"{prefix}_f1"] = None if row["f1"] is None else round(row["f1"], 3)
        return out

    measured = len(rows)
    designed = len(clips)
    sample_note = (
        f"{len(kept)} clips measured and kept, of {designed} clips in the committed design. "
        f"{measured - len(kept)} were measured and excluded. The run order is the whole spine "
        f"({design['counts']['spine']} rows that walk one axis at a time) followed by the "
        "cross product shuffled with the committed seed, so a partial run is a random sample "
        "of the cross product with every sweep complete. Every number in this file is from "
        "that sample and from nothing else."
    )

    return {
        "generated_on": "2026-09-17",
        "git_commit": git_commit(),
        "flashmap_version": next(
            (row.get("flashmap", {}).get("version") for row, _ in kept), "unknown"
        ),
        "profile": "wcag",
        "sample": {
            "clips_designed": designed,
            "clips_measured": measured,
            "clips_kept": len(kept),
            "clips_with_baselines": baseline_rows,
            "windows_kept": windows_total,
            "ground_truth_positive_windows": positives_total,
            "is_complete_run": len(kept) + sum(exclusions.values()) >= designed,
            "statement": sample_note,
        },
        "ground_truth": {
            "source": "computed from the spec text by eval/conformance/truth.py",
            "imports_flashmap": False,
            "spec_file": spec["source"],
            "spec_sha256": spec["source_sha256"],
            "design_sha256": sha256_of(design_path),
            "design_seed": design["seed"],
        },
        "exclusions": dict(exclusions),
        "published": {
            "clips_designed": designed,
            "clips_measured": measured,
            "clips_kept": len(kept),
            "windows": windows_total,
            "positive_windows": positives_total,
            "excluded_clips": sum(exclusions.values()),
            **flat("flashmap", "all_windows", "flashmap"),
            **flat("flashmap", "windows_every_detector_saw", "flashmap_shared"),
            **flat("flashmap@half_window", "all_windows", "flashmap_half"),
            **(
                flat(f"naive_luma_diff@{naive_pick}", "windows_every_detector_saw", "naive")
                if naive_pick is not None
                else {}
            ),
            **(
                flat(
                    f"ffmpeg_photosensitivity@{ffmpeg_pick}",
                    "windows_every_detector_saw",
                    "ffmpeg",
                )
                if ffmpeg_pick is not None
                else {}
            ),
            "naive_best_threshold": naive_pick,
            "ffmpeg_best_threshold": ffmpeg_pick,
            # The split that explains the recall number: away from every limit flashmap finds
            # everything, and the misses are all boundary cases. Both halves get published so
            # neither can be quoted on its own.
            **_near_split(curve_out.get("near_threshold", [])),
            # Where the false positives actually are. The shared universe drops the first
            # second of every clip, so the difference between the two false positive counts is
            # exactly the hide that lands in the calm second before the flashing.
            "false_positives_total": tallies["all_windows"]["flashmap"].fp,
            "false_positives_in_the_calm_lead_in": (
                tallies["all_windows"]["flashmap"].fp
                - tallies["windows_every_detector_saw"]["flashmap"].fp
            ),
            "false_positives_elsewhere": tallies["windows_every_detector_saw"]["flashmap"].fp,
            "clip_level_precision": round(
                clip_level["tp"] / max(1, clip_level["tp"] + clip_level["fp"]), 3
            ),
            "clip_level_recall": round(
                clip_level["tp"] / max(1, clip_level["tp"] + clip_level["fn"]), 3
            ),
            "what_these_are": (
                "the same numbers as the tables below, rounded and with short keys, because "
                "eval/readme_sync.py quotes a dotted path with no spaces in it. A document "
                "quotes these."
            ),
        },
        "headline_all_windows": table("all_windows"),
        "baseline_table_windows_every_detector_saw": table("windows_every_detector_saw"),
        "baselines_not_run": {
            "EA IRIS": (
                "not run. The pinned image at eval/baselines/iris/ has never built, and the "
                "shared colima VM was running another project's stack on 4 CPUs and 8 GB when "
                "this suite ran, so building it would have taken the machine away from work "
                "that was already going. No IRIS number appears anywhere in this file."
            ),
            "Apple VideoFlashingReduction": (
                "not run. It needs Xcode and this machine has Command Line Tools only "
                "(xcode-select -p reports /Library/Developer/CommandLineTools). It is also cut "
                "list item 4 in EVAL_PLAN section 6, so it was never part of the committed "
                "comparison."
            ),
        },
        "baseline_operating_points": {
            "chosen_on": "this conformance suite, by best F1, before any real clip is touched",
            "naive_luma_diff": naive_best,
            "ffmpeg_photosensitivity": ffmpeg_best,
            "note": (
                "flashmap's own thresholds are not tuned on either set. They come from the "
                "spec text and are the same numbers the analyser ships with."
            ),
        },
        "clip_level": {
            "counts": clip_level,
            "precision": rate_with_interval(clip_level["tp"], clip_level["tp"] + clip_level["fp"]),
            "recall": rate_with_interval(clip_level["tp"], clip_level["tp"] + clip_level["fn"]),
            "meaning": "does the clip fail at all, which is what `flashmap check` answers",
        },
        "hidden_window_share": {
            "windows_flashmap_would_hide": hidden_windows,
            "windows_measured": windows_total,
            "share": hidden_windows / windows_total if windows_total else None,
        },
        "error_curves": curve_out,
        "window_rules": {
            "primary": "any overlap at all between a detector interval and the window",
            "sensitivity": "at least half the window covered, reported as @half_window",
            "baselines": (
                "the two frame based baselines have no intervals, so a flagged frame marks the "
                "window that contains it, which is the mapping EVAL_PLAN section 6 gives them. "
                "The half window rule does not apply to them and is not reported for them."
            ),
        },
        "known_disagreements": {
            "one_second_period_boundary": (
                "The ground truth counts flashes in a half open one second period and flashmap "
                "counts them in a closed trailing one. On a clean square wave at exactly the "
                "flash limit the closed reading finds one more flash than the half open one. "
                "Look at the flash_rate_hz error curve at 3 Hz to see what it costs. Neither "
                "reading is written in the spec."
            ),
            "leading_hide": (
                "flashmap hides the whole failing one second period, which starts before the "
                "flashing does. Under the any overlap rule that shows up as false positive "
                "windows in the calm lead-in. It is the direction a safety layer should err "
                "in, and it is counted here rather than excused: see onset_lead_windows."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("-o", "--out", type=Path, default=OUT)
    arguments = parser.parse_args()

    report = build(arguments.design, arguments.raw)
    arguments.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
    headline = report["headline_all_windows"]["flashmap (this project)"]
    print(
        f"{report['sample']['clips_kept']} clips kept, "
        f"{report['sample']['windows_kept']} windows. "
        f"precision {headline['precision']['value']:.4f} "
        f"[{headline['precision']['wilson_lo']:.4f}, {headline['precision']['wilson_hi']:.4f}] "
        f"recall {headline['recall']['value']:.4f} "
        f"[{headline['recall']['wilson_lo']:.4f}, {headline['recall']['wilson_hi']:.4f}] "
        f"-> {arguments.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
