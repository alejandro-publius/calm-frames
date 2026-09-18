#!/usr/bin/env python3
"""Ablations: turn one thing off at a time and measure what it cost.

docs/EVAL_PLAN.md section 7. Three groups, each written into results/ablations.json under its
own key so a partial run still leaves a valid file:

1. **detection**, one rule off at a time, against the same committed ground truth as the main
   conformance run. Each arm is the shipped `analyze_file` on the shipped code path: the rules
   are turned off by handing the analyser a profile with that rule out of reach, and sRGB
   linearisation is turned off by replacing the one function that does it. The `default` arm is
   asserted to reproduce the main run's segments exactly, clip for clip, which is what proves
   the harness did not quietly become a different analyser.

2. **guard band** at 0, 100, 250 and 500 ms. Simulated, and the file says so in as many words.
   It runs the app's own scheduler (app/src/calmframes/coverSchedule.ts) through Node, so the
   ablation cannot drift from the code the player runs, and asks how often the cover is fully
   in place before the flashing starts. There is no measured render latency yet, because
   results/gate1_timing.json does not exist, so the answer is reported across a grid of assumed
   latencies rather than at one number that would look measured and would not be.

3. **cover**, dim against opaque, through the verify step: render the cover over the clip in
   linear light, re-run flashmap on the covered rendition, and count what still fails. Reported
   for red and non-red separately, because a dim cover cannot fix a red flash: dimming scales
   all three channels together and leaves the chromaticity, which is what the red rule reads,
   exactly where it was.

SAFETY: this script generates the same hazardous clips the conformance suite does, under the
same rules. Generate, analyse, delete, in the same job, never opened, never kept. The covered
renditions are safer than the originals but are treated identically, because a bug in the cover
is exactly the case where that assumption would be wrong.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.generate_analyze import _init_worker, sweep_leftovers  # noqa: E402
from conformance.render import HAZARD_PREFIX, render_clip, scratch_dir  # noqa: E402
from conformance.spec import load_spec  # noqa: E402
from metrics import confusion, rate_with_interval, windows_from_intervals  # noqa: E402

REPO = _EVAL_DIR.parent
DESIGN = REPO / "results" / "conformance_design.json"
RAW = REPO / "results" / "conformance_raw.jsonl"
OUT = REPO / "results" / "ablations.json"

ARMS = [
    "default",
    "red_rule_off",
    "area_rule_off",
    "darker_image_rule_off",
    "srgb_linearization_off",
]
GUARD_BANDS = [0, 100, 250, 500]
# No GATE 1 recording exists yet, so the cover's real render latency is unknown. These are the
# assumptions the guard band answer is reported across, not measurements.
ASSUMED_LATENCIES_MS = [0, 33, 66, 100, 200]


def arm_profile(arm: str):
    """The shipped WCAG profile with one rule put out of reach. Nothing else changes."""
    from flashmap import WCAG

    if arm in ("default", "srgb_linearization_off"):
        return WCAG
    if arm == "red_rule_off":
        # A red ratio can never exceed 1, so a threshold above 1 can never be met.
        return replace(WCAG, red=replace(WCAG.red, saturated_red_ratio=2.0))
    if arm == "area_rule_off":
        # Coverage only has to beat zero, so any flashing area at all qualifies.
        return replace(WCAG, area_fraction_limit=0.0)
    if arm == "darker_image_rule_off":
        # Relative luminance never exceeds 1, so the darker image is always "below" this.
        return replace(WCAG, general=replace(WCAG.general, dark_image_below=2.0))
    raise ValueError(arm)


def analyze_arm(path: Path, arm: str) -> list[dict]:
    from flashmap import analyze_file

    if arm == "srgb_linearization_off":
        # Measure on the gamma encoded values: replace the one function that linearises, on
        # the same code path, for the length of this call.
        from unittest.mock import patch

        import flashmap.analyze as analyze_module

        with patch.object(
            analyze_module.color_math, "srgb_to_linear", lambda values: np.asarray(values)
        ):
            result = analyze_file(path, arm_profile(arm))
    else:
        result = analyze_file(path, arm_profile(arm))
    return [
        {
            "start_ms": s.start_ms,
            "end_ms": s.end_ms,
            "reason": s.reason,
            "area_fraction": s.area_fraction,
        }
        for s in result.segments
    ]


def dim(rgb, factor: float, spec) -> list[int]:
    """The colour after a cover that passes `factor` of the light through, in linear light."""
    linear = spec.srgb_to_linear(np.asarray(rgb, dtype=np.float64) / 255.0) * factor
    encoded = np.where(
        linear <= spec.srgb_break / spec.srgb_divisor,
        linear * spec.srgb_divisor,
        spec.srgb_scale * np.power(np.clip(linear, 0, 1), 1.0 / spec.srgb_exponent)
        - spec.srgb_offset,
    )
    return [int(min(255, max(0, round(float(v) * 255.0)))) for v in encoded]


def detection_worker(job: tuple[dict, list[str]]) -> dict:
    clip, arms = job
    path = scratch_dir() / f"{HAZARD_PREFIX}abl_{clip['clip_id']}.mp4"
    out: dict[str, object] = {"clip_id": clip["clip_id"]}
    try:
        render_clip(clip, path)
        for arm in arms:
            out[arm] = analyze_arm(path, arm)
    except Exception as error:  # noqa: BLE001
        out["error"] = f"{type(error).__name__}: {error}"
    finally:
        if path.exists():
            path.unlink()
    return out


def cover_worker(clip: dict) -> dict:
    """Render the clip, then the same clip under a dim cover and under an opaque one."""
    spec = load_spec()
    out: dict[str, object] = {"clip_id": clip["clip_id"]}
    arms = {
        "uncovered": clip,
        # 90% or darker is what CLAUDE.md allows a dim cover to be, so the cover passes a tenth
        # of the light. Applied in linear light to every pixel of the picture, which is what the
        # player's dim cover does.
        "dim_10_percent": {
            **clip,
            "state_a_rgb": dim(clip["state_a_rgb"], 0.10, spec),
            "state_b_rgb": dim(clip["state_b_rgb"], 0.10, spec),
            "background_rgb": dim(clip["background_rgb"], 0.10, spec),
        },
        "opaque": {
            **clip,
            "state_a_rgb": [0, 0, 0],
            "state_b_rgb": [0, 0, 0],
            "background_rgb": [0, 0, 0],
        },
    }
    for name, variant in arms.items():
        path = scratch_dir() / f"{HAZARD_PREFIX}cover_{name}_{clip['clip_id']}.mp4"
        try:
            render_clip(variant, path)
            out[name] = analyze_arm(path, "default")
        except Exception as error:  # noqa: BLE001
            out[f"{name}_error"] = f"{type(error).__name__}: {error}"
        finally:
            if path.exists():
                path.unlink()
    return out


def score(rows: list[dict], clips: dict, arm: str) -> dict:
    """Window level precision and recall for one arm, against the committed ground truth."""
    tp = fp = fn = tn = 0
    for row in rows:
        if arm not in row:
            continue
        clip = clips[row["clip_id"]]
        n_windows = clip["truth"]["n_windows"]
        truth = set(clip["truth"]["positive_windows"])
        predicted = windows_from_intervals(
            [(s["start_ms"], s["end_ms"]) for s in row[arm]], n_windows=n_windows
        )
        counts = confusion(predicted, truth, universe=list(range(n_windows)))
        tp += counts["tp"]
        fp += counts["fp"]
        fn += counts["fn"]
        tn += counts["tn"]
    return {
        "counts": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": rate_with_interval(tp, tp + fp),
        "recall": rate_with_interval(tp, tp + fn),
    }


def sample_clips(design: dict, count: int, measured: set[str] | None = None) -> list[dict]:
    """An even spread across the committed run order, so the sample is not the spine alone.

    Clips the main run has already measured come first. The default arm has to be compared
    against that run clip for clip, and a sample of clips nobody has measured yet would leave
    that check with nothing to compare.
    """
    clips = sorted(design["clips"], key=lambda clip: clip["order_index"])
    if measured:
        preferred = [clip for clip in clips if clip["clip_id"] in measured]
        if len(preferred) >= count:
            clips = preferred
    if count >= len(clips):
        return clips
    step = len(clips) / count
    return [clips[int(index * step)] for index in range(count)]


def run_detection(design: dict, count: int, workers: int, raw_rows: dict) -> dict:
    clips = sample_clips(design, count, measured=set(raw_rows))
    started = time.time()
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
        for row in pool.map(detection_worker, [(clip, ARMS) for clip in clips]):
            rows.append(row)
    by_id = {clip["clip_id"]: clip for clip in design["clips"]}

    # The default arm has to reproduce the main run exactly, or this harness is measuring
    # something other than the analyser the rest of the numbers came from.
    checked = mismatched = 0
    examples = []
    for row in rows:
        main = raw_rows.get(row["clip_id"])
        if not main or "default" not in row or "flashmap" not in main:
            continue
        checked += 1
        ours = [(round(s["start_ms"], 3), round(s["end_ms"], 3), s["reason"]) for s in row["default"]]
        theirs = [
            (round(s["start_ms"], 3), round(s["end_ms"], 3), s["reason"])
            for s in main["flashmap"]["segments"]
        ]
        if ours != theirs:
            mismatched += 1
            if len(examples) < 5:
                examples.append({"clip_id": row["clip_id"], "ablation": ours, "main_run": theirs})

    out = {
        "clips": len(rows),
        "errors": sum(1 for row in rows if "error" in row),
        "seconds": round(time.time() - started, 1),
        "default_arm_matches_main_run": {
            "clips_compared": checked,
            "mismatched": mismatched,
            "examples": examples,
            "meaning": (
                "with every flag at its default this harness must produce the segments the "
                "main conformance run produced, clip for clip. A mismatch here invalidates "
                "every ablation number in this file."
            ),
        },
        "arms": {},
    }
    baseline = score(rows, by_id, "default")
    for arm in ARMS:
        result = score(rows, by_id, arm)
        for metric in ("precision", "recall"):
            base = baseline[metric]["value"]
            value = result[metric]["value"]
            result[f"{metric}_change_vs_default"] = (
                None if (base is None or value is None) else round(value - base, 6)
            )
        out["arms"][arm] = result
    out["what_each_arm_does"] = {
        "default": "the shipped WCAG profile, nothing changed",
        "red_rule_off": "the saturated red ratio put above 1, so no red flash can ever be found",
        "area_rule_off": "the area limit put at zero, so any flashing area at all qualifies",
        "darker_image_rule_off": (
            "the darker-image limit put above 1, so a flash counts however bright both states are"
        ),
        "srgb_linearization_off": (
            "the sRGB to linear light step replaced by the identity, so every threshold is "
            "applied to gamma encoded values instead"
        ),
    }
    return out


def run_guard_band(design: dict, raw_rows: dict) -> dict:
    """The app's scheduler over the measured flash maps, at four guard bands."""
    by_id = {clip["clip_id"]: clip for clip in design["clips"]}
    request = {"guardBands": GUARD_BANDS, "clips": []}
    onsets: dict[str, float] = {}
    for clip_id, row in raw_rows.items():
        clip = by_id.get(clip_id)
        if not clip or "flashmap" not in row:
            continue
        segments = row["flashmap"]["segments"]
        if not segments or not clip["truth"]["positive_windows"]:
            continue
        request["clips"].append(
            {
                "id": clip_id,
                "durationMs": clip["duration_ms"],
                "segments": [
                    {"startMs": s["start_ms"], "endMs": s["end_ms"], "reason": s["reason"]}
                    for s in segments
                ],
            }
        )
        onsets[clip_id] = float(clip["flash_start_ms"])

    if not request["clips"]:
        return {"error": "no measured flash maps to simulate over yet"}

    proc = subprocess.run(
        ["node", "--experimental-strip-types", str(_EVAL_DIR / "ablations" / "cover_sim.mjs")],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=600,
        cwd=REPO,
    )
    if proc.returncode != 0:
        return {"error": f"the cover scheduler harness failed: {proc.stderr[-400:]}"}
    simulated = json.loads(proc.stdout)

    results = {}
    for guard in GUARD_BANDS:
        per_latency = {}
        for latency in ASSUMED_LATENCIES_MS:
            in_place = 0
            total = 0
            for clip_id, onset in onsets.items():
                intervals = simulated["clips"][clip_id][str(guard)]
                covering = [
                    interval
                    for interval in intervals
                    if interval["endMs"] > onset and interval["startMs"] <= onset + 1e-9
                ]
                total += 1
                if covering and min(i["startMs"] for i in covering) + latency <= onset:
                    in_place += 1
            per_latency[str(latency)] = rate_with_interval(in_place, total)
        results[str(guard)] = per_latency

    return {
        "simulated": True,
        "how": (
            "the app's own scheduler, app/src/calmframes/coverSchedule.ts, run through Node over "
            "the flash maps the conformance run measured. No video is played and no device is "
            "involved."
        ),
        "question": (
            "is the cover fully in place before the flashing starts, for a clip flashmap flagged"
        ),
        "onset_definition": "the first frame of the clip's flashing section, known from the design",
        "assumed_render_latency_ms": ASSUMED_LATENCIES_MS,
        "latency_is_assumed_not_measured": (
            "results/gate1_timing.json does not exist yet, so there is no measured cover latency "
            "to put here. Read the rows as: at this guard band, the cover is in place in time as "
            "long as the player takes no longer than this to put it up."
        ),
        "min_cover_ms": simulated.get("minCoverMs"),
        "clips": len(onsets),
        "covered_before_onset": results,
    }


def run_cover(design: dict, raw_rows: dict, count: int, workers: int) -> dict:
    """Dim against opaque, through the verify step: cover it, analyse it again, count."""
    by_id = {clip["clip_id"]: clip for clip in design["clips"]}
    red, general = [], []
    for clip_id, row in raw_rows.items():
        clip = by_id.get(clip_id)
        if not clip or "flashmap" not in row or not row["flashmap"]["segments"]:
            continue
        reasons = {s["reason"] for s in row["flashmap"]["segments"]}
        (red if "red" in reasons else general).append(clip)
    half = max(1, count // 2)
    chosen = red[:half] + general[:half]
    if not chosen:
        return {"error": "no flagged clips to cover yet"}

    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
        for row in pool.map(cover_worker, chosen):
            rows.append(row)

    def summarise(subset: list[dict]) -> dict:
        out = {}
        for arm in ("uncovered", "dim_10_percent", "opaque"):
            flagged = sum(1 for row in subset if row.get(arm))
            out[arm] = {
                "clips_still_flagged": flagged,
                "clips": len(subset),
                "share_still_flagged": flagged / len(subset) if subset else None,
            }
        return out

    red_ids = {clip["clip_id"] for clip in red}
    return {
        "clips": len(rows),
        "how": (
            "each clip is rendered again with the cover applied over the picture in linear "
            "light, then analysed by flashmap exactly as the verify step does. Nothing is "
            "played and nobody watches."
        ),
        "all": summarise(rows),
        "red_segments": summarise([row for row in rows if row["clip_id"] in red_ids]),
        "non_red_segments": summarise([row for row in rows if row["clip_id"] not in red_ids]),
        "dim_definition": "a cover passing a tenth of the light, which is 90% dark",
        "why_red_is_always_opaque": (
            "dimming multiplies all three channels by the same factor, which leaves the "
            "chromaticity where it was, and the red rule reads chromaticity. So a dim cover "
            "cannot clear a red flash, whatever the luminance does. The red rows here are the "
            "measurement of that, not an argument for it."
        ),
    }


def publishable(report: dict) -> dict:
    """Flat, marker friendly copies of the numbers a document may quote.

    eval/readme_sync.py reads a dotted path with no spaces in it, so the numbers a write-up
    quotes get short keys here rather than being dug out of the tables by hand.
    """
    out: dict[str, object] = {}
    detection = report.get("detection") or {}
    arms = detection.get("arms") or {}
    if arms:
        out["clips"] = detection.get("clips")
        out["default_arm_mismatches"] = detection["default_arm_matches_main_run"]["mismatched"]
        out["default_arm_clips_compared"] = detection["default_arm_matches_main_run"][
            "clips_compared"
        ]
        for arm, row in arms.items():
            for metric in ("precision", "recall"):
                value = row[metric]["value"]
                out[f"{arm}_{metric}"] = None if value is None else round(value, 3)
                change = row.get(f"{metric}_change_vs_default")
                if change is not None:
                    out[f"{arm}_{metric}_change"] = round(change, 3)
    cover = report.get("cover") or {}
    for label, key in (("red", "red_segments"), ("non_red", "non_red_segments"), ("all", "all")):
        row = cover.get(key)
        if isinstance(row, dict) and "uncovered" in row:
            out[f"cover_{label}_clips"] = row["uncovered"]["clips"]
            out[f"cover_{label}_uncovered_flagged"] = row["uncovered"]["clips_still_flagged"]
            out[f"cover_{label}_dim_flagged"] = row["dim_10_percent"]["clips_still_flagged"]
            out[f"cover_{label}_opaque_flagged"] = row["opaque"]["clips_still_flagged"]
    guard = report.get("guard_band") or {}
    covered = guard.get("covered_before_onset") or {}
    for band, per_latency in covered.items():
        for latency, row in per_latency.items():
            value = row["value"]
            out[f"guard_{band}ms_latency_{latency}ms"] = None if value is None else round(value, 3)
    if guard.get("clips"):
        out["guard_clips"] = guard["clips"]
    return out


def load_raw(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if not path.exists():
        return rows
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                row = json.loads(line)
                rows.setdefault(row["clip_id"], row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("-o", "--out", type=Path, default=OUT)
    parser.add_argument("--detection-clips", type=int, default=250)
    parser.add_argument("--cover-clips", type=int, default=80)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--skip", action="append", default=[], choices=["detection", "guard", "cover"])
    arguments = parser.parse_args()

    sweep_leftovers(fail=False)  # nothing from an earlier job survives into this one
    design = json.loads(arguments.design.read_text())
    raw_rows = load_raw(arguments.raw)

    report: dict[str, object] = {}
    if arguments.out.exists():
        report = json.loads(arguments.out.read_text())
    report["generated_on"] = "2026-09-17"
    report["design_seed"] = design["seed"]
    report["ground_truth"] = "the same committed truth the conformance report uses"

    def save(stage: str) -> None:
        """Write the file after every stage.

        The three groups take a long time under load, and a run that only writes at the very
        end throws away an hour of finished arms if it is stopped in the last one. Each stage
        lands on disk as soon as it is done, and a later run merges into the same file.
        """
        report["published"] = publishable(report)
        arguments.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
        print(f"{stage} done, written to {arguments.out}", flush=True)

    if "detection" not in arguments.skip:
        report["detection"] = run_detection(
            design, arguments.detection_clips, arguments.workers, raw_rows
        )
        save("detection arms")
    if "guard" not in arguments.skip:
        report["guard_band"] = run_guard_band(design, raw_rows)
        save("guard band simulation")
    if "cover" not in arguments.skip:
        report["cover"] = run_cover(design, raw_rows, arguments.cover_clips, arguments.workers)
        save("cover arms")
    leftovers = sweep_leftovers()
    print(f"wrote {arguments.out}, {leftovers} hazard files leaked")
    return 1 if leftovers else 0


if __name__ == "__main__":
    raise SystemExit(main())
