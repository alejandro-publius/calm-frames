#!/usr/bin/env python3
"""What the regular pattern rule does to text, and what the periodicity test cost.

    python eval/pattern_text_precision.py                 # measure and write the report
    python eval/pattern_text_precision.py --check         # re-score the committed report
    python eval/pattern_text_precision.py --only grating  # one kind, while working

Why this exists. `scan_bars` counts alternating steps that reach the Guideline 1 flash
difference, and a page of readable text is full of them: cream on teal is 160.77 against
8.47 cd/m2, so every glyph edge is one. Before the periodicity test the whole report page
read as a pattern over 44 to 74 per cent of every display frame, which is
eval/report_page_check.py's finding and is written up in docs/DECISIONS.md. Nothing in the
grating conformance suite could see that, because every clip in it is a grating: a suite made
only of stripes cannot measure what a detector does to something that is not stripes.

So this is the other half of that suite. It draws pages a person reads and gratings a person
should not watch, at the same display size, and scores the rule against what was drawn.

Ground truth. `eval/pattern_text_frames.py` draws every picture and records what went into
it, and it does not import flashmap. A picture is positive when the drawing put more than
the spec's pair count of light and dark pairs into a block covering more than the spec's
area. A page of text had no pair drawn into it at all, so it is negative whatever a scan
line makes of it, and that is the claim this file rests on rather than any opinion about
whether a paragraph looks like a grating.

Which area limit. These are stills, and a still is stationary, so the stationary limit is
the one the drawing is scored against. The shipped analyzer is stricter on a held still: its
motion class starts uncertain and an uncertain class takes the changing limit, so a segment
that spans the opening frames is judged at the tighter number. That is a deliberate fail
safe and it is not modelled here; this file is about the spatial test, not the motion class.

Every number comes out of flashmap/docs/SPEC_SOURCES.md through eval/conformance/pattern_spec.py.
Nothing is restated here.

SAFETY. The gratings are hazardous by design. They are stills drawn in memory, encoded into
a temporary directory under a HAZARD_ name, decoded by the analyzer and deleted in the same
run. Nothing is played and nothing is written where a person can open it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
for extra in (REPO / "eval", REPO / "flashmap" / "src"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from conformance.pattern_spec import load_pattern_spec  # noqa: E402
from metrics import Z_95, f1, wilson  # noqa: E402
from pattern_text_frames import HEIGHT, WIDTH, Frame, frames  # noqa: E402

from flashmap import color as color_math  # noqa: E402
from flashmap.decode import iter_frames, probe  # noqa: E402
from flashmap.pattern import stripe_mask  # noqa: E402
from flashmap.picture import detect_picture  # noqa: E402
from flashmap.profiles import get_profile  # noqa: E402

OUT = REPO / "results" / "pattern_text_precision.json"
PROFILE = "broadcast"
ANALYSIS_WIDTH = 192

# The sweep. The shipped value is one of these and the report says which, so the choice is a
# row in a table rather than a number somebody liked.
PEAKS = (0.0, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.98)


@dataclass
class Measured:
    """One picture, reduced to the metric frame the analyzer would have seen."""

    clip_id: str
    kind: str
    note: str
    drawn_area: float
    drawn_pairs: int
    metric: np.ndarray


def metric_frame(frame: Frame, work: Path) -> np.ndarray:
    """Draw it, encode it losslessly, and decode it the way the analyzer does.

    Through a real encode and a real decode rather than scaling the array here, because the
    YCbCr round trip and libswscale's area scaling are both part of what the rule sees, and
    a pattern that survives one does not always survive the other.
    """
    picture = frame.draw()
    if picture.shape != (HEIGHT, WIDTH, 3):
        raise ValueError(f"{frame.clip_id} drew {picture.shape}, wanted {(HEIGHT, WIDTH, 3)}")
    raw = work / f"HAZARD_{frame.clip_id}.rgb"
    video = work / f"HAZARD_{frame.clip_id}.mkv"
    raw.write_bytes(picture.tobytes())
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
            "-framerate", "24", "-i", str(raw),
            "-vf", "format=yuv420p", "-c:v", "ffv1", "-frames:v", "1",
            str(video),
        ],
        check=True, capture_output=True,
    )
    raw.unlink(missing_ok=True)
    profile = get_profile(PROFILE)
    info = probe(video, analysis_width=ANALYSIS_WIDTH)
    peak = profile.peak_nits or 200.0
    out = None
    relative = None
    for decoded in iter_frames(video, info):
        out = np.asarray(color_math.bt1886_nits(decoded.video_level, peak), dtype=np.float32)
        relative = color_math.relative_luminance(color_math.srgb_to_linear(decoded.rgb))
        break
    video.unlink(missing_ok=True)
    if out is None or relative is None:
        raise RuntimeError(f"{frame.clip_id} decoded to no frames")
    # The same crop the analyzer would make, found the same way: on relative luminance, not
    # on nits. A pattern measured on an uncropped frame is measured against the wrong area.
    rect = detect_picture([np.asarray(relative, dtype=np.float32)])
    return np.ascontiguousarray(rect.crop(out))


def truth_of(measured: Measured, spec) -> bool:
    """Positive when the drawing put a pattern over the rule's own numbers into the picture."""
    return (
        measured.drawn_pairs > spec.more_than_pairs
        and measured.drawn_area > spec.stationary_area_limit
    )


def predict(measured: Measured, profile, *, require_periodicity: bool, min_peak: float,
            area_limit: float) -> dict:
    pattern = profile.pattern
    scan = stripe_mask(
        measured.metric,
        min_delta=profile.general.min_delta,
        dark_below=profile.general.dark_image_below,
        min_bars=2 * (pattern.more_than_pairs + 1),
        orientations=pattern.settings.orientations,
        min_profile_samples=pattern.settings.min_profile_samples,
        require_periodicity=require_periodicity,
        min_autocorrelation_peak=min_peak,
    )
    return {
        "over": bool(scan.area_fraction > area_limit),
        "area": round(float(scan.area_fraction), 6),
        "counted_area": round(float(scan.counted_area_fraction), 6),
        "pairs": int(scan.stripe_pairs),
    }


def rate(successes: int, trials: int) -> dict:
    low, high = wilson(successes, trials)
    return {
        "value": round(successes / trials, 4) if trials else None,
        "wilson_lo": round(low, 4),
        "wilson_hi": round(high, 4),
        "numerator": successes,
        "denominator": trials,
    }


def score(rows: list[dict]) -> dict:
    tp = sum(1 for r in rows if r["predicted"] and r["truth"])
    fp = sum(1 for r in rows if r["predicted"] and not r["truth"])
    fn = sum(1 for r in rows if not r["predicted"] and r["truth"])
    tn = sum(1 for r in rows if not r["predicted"] and not r["truth"])
    precision = rate(tp, tp + fp)
    recall = rate(tp, tp + fn)
    out = {
        "counts": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": precision,
        "recall": recall,
        "f1": round(f1(precision["value"] or 0.0, recall["value"] or 0.0), 4),
    }
    for kind in ("text", "ui", "grating", "mixed"):
        subset = [r for r in rows if r["kind"] == kind]
        if not subset:
            continue
        wrong = [r for r in subset if r["predicted"] != r["truth"]]
        out.setdefault("by_kind", {})[kind] = {
            "pictures": len(subset),
            "wrong": len(wrong),
            "which": sorted(r["clip_id"] for r in wrong)[:12],
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="one kind: text, ui, grating or mixed")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true",
                        help="re-score the committed report from its own rows and fail on drift")
    arguments = parser.parse_args()

    if arguments.check:
        return recheck(arguments.out)

    if shutil.which("ffmpeg") is None:
        print("ffmpeg is not on PATH", file=sys.stderr)
        return 2

    spec = load_pattern_spec()
    profile = get_profile(PROFILE)
    wanted = [f for f in frames() if not arguments.only or f.kind == arguments.only]

    work = Path(tempfile.mkdtemp(prefix="pattern-text-"))
    measured: list[Measured] = []
    try:
        for index, frame in enumerate(wanted, start=1):
            measured.append(
                Measured(frame.clip_id, frame.kind, frame.note, frame.drawn_area,
                         frame.drawn_pairs, metric_frame(frame, work))
            )
            if index % 20 == 0:
                print(f"  measured {index} of {len(wanted)}", file=sys.stderr)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    area_limit = spec.stationary_area_limit
    settings = profile.pattern.settings
    sweep = {}
    for min_peak in PEAKS:
        rows = []
        for item in measured:
            prediction = predict(item, profile, require_periodicity=True, min_peak=min_peak,
                                 area_limit=area_limit)
            rows.append({
                "clip_id": item.clip_id, "kind": item.kind, "note": item.note,
                "drawn_pairs": item.drawn_pairs, "drawn_area": item.drawn_area,
                "truth": truth_of(item, spec), "predicted": prediction["over"],
                **{k: v for k, v in prediction.items() if k != "over"},
            })
        sweep[f"{min_peak:.2f}"] = {"rows": rows, **score(rows)}

    off_rows = []
    for item in measured:
        prediction = predict(item, profile, require_periodicity=False, min_peak=0.0,
                             area_limit=area_limit)
        off_rows.append({
            "clip_id": item.clip_id, "kind": item.kind, "note": item.note,
            "drawn_pairs": item.drawn_pairs, "drawn_area": item.drawn_area,
            "truth": truth_of(item, spec), "predicted": prediction["over"],
            **{k: v for k, v in prediction.items() if k != "over"},
        })

    shipped = f"{settings.min_autocorrelation_peak:.2f}"
    report = {
        "generated_on": "2026-09-19",
        "what_this_is": (
            "the regular pattern rule measured on pictures that are not gratings, which is "
            "what the grating conformance suite cannot cover. Ground truth is what "
            "eval/pattern_text_frames.py drew."
        ),
        "not_a_wcag_measurement": (
            "WCAG 2.2 SC 2.3.1 does not cover regular patterns, so no number here is a WCAG "
            "number and none of it may be described as WCAG conformance."
        ),
        "profile": PROFILE,
        "analysis_width": ANALYSIS_WIDTH,
        "display": f"{WIDTH}x{HEIGHT}",
        "area_limit_used": area_limit,
        "area_limit_note": (
            "the stationary limit, because every picture here is a still. The shipped "
            "analyzer is stricter on a held still: an uncertain motion class takes the "
            "changing limit."
        ),
        "spec_file": "flashmap/docs/SPEC_SOURCES.md",
        "spec_numbers": spec.as_dict(),
        "pictures": len(measured),
        "ground_truth_positive": sum(1 for m in measured if truth_of(m, spec)),
        "shipped_min_autocorrelation_peak": settings.min_autocorrelation_peak,
        "how_the_shipped_peak_was_chosen": (
            "the largest peak at which recall does not fall. The rule was fixed before the "
            "sweep was read, because a threshold picked to make one page pass is not a "
            "measurement. Recall is flat from 0 up to the chosen value and drops above it."
        ),
        "periodicity_off": {"rows": off_rows, **score(off_rows)},
        "sweep": sweep,
        "published": {},
    }
    chosen = sweep.get(shipped)
    if chosen is not None:
        report["published"] = {
            "pattern_text_precision": chosen["precision"]["value"],
            "pattern_text_precision_lo": chosen["precision"]["wilson_lo"],
            "pattern_text_precision_hi": chosen["precision"]["wilson_hi"],
            "pattern_text_precision_denominator": chosen["precision"]["denominator"],
            "pattern_text_recall": chosen["recall"]["value"],
            "pattern_text_recall_lo": chosen["recall"]["wilson_lo"],
            "pattern_text_recall_hi": chosen["recall"]["wilson_hi"],
            "pattern_text_recall_denominator": chosen["recall"]["denominator"],
            "pattern_text_f1": chosen["f1"],
            "pattern_text_precision_without_periodicity": report["periodicity_off"]["precision"]["value"],
            "pattern_text_recall_without_periodicity": report["periodicity_off"]["recall"]["value"],
        }

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(report, indent=2) + "\n")
    _print(report)
    return 0


def recheck(path: Path) -> int:
    """Re-score the committed report from its own rows, so a hand edited summary fails."""
    if not path.exists():
        print(f"{path} does not exist", file=sys.stderr)
        return 1
    report = json.loads(path.read_text())
    problems = []
    for name, block in [("periodicity_off", report["periodicity_off"])] + [
        (f"sweep {k}", v) for k, v in report["sweep"].items()
    ]:
        again = score(block["rows"])
        for key in ("counts", "precision", "recall", "f1"):
            if again[key] != block[key]:
                problems.append(f"{name}: {key} is {block[key]} but its own rows give {again[key]}")
    shipped = f"{report['shipped_min_autocorrelation_peak']:.2f}"
    if shipped not in report["sweep"]:
        problems.append(f"the shipped peak {shipped} is not one of the sweep's rows")
    else:
        chosen = report["sweep"][shipped]
        if report["published"].get("pattern_text_precision") != chosen["precision"]["value"]:
            problems.append("the published precision is not the shipped row's precision")
        if report["published"].get("pattern_text_recall") != chosen["recall"]["value"]:
            problems.append("the published recall is not the shipped row's recall")
    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"{path}: every summary matches its own rows")
    return 0


def _print(report: dict) -> None:
    print(f"\n{report['pictures']} pictures, {report['ground_truth_positive']} of them "
          f"positive by what was drawn. Area limit {report['area_limit_used']}.")
    off = report["periodicity_off"]
    print(f"\nperiodicity off: precision {off['precision']['value']} "
          f"recall {off['recall']['value']} {off['counts']}")
    print("\n  peak   precision              recall                 f1    text wrong  ui wrong")
    for peak, block in report["sweep"].items():
        by = block.get("by_kind", {})
        print(
            f"  {peak}  "
            f"{block['precision']['value']!s:6} ({block['precision']['wilson_lo']:.3f}-{block['precision']['wilson_hi']:.3f})  "
            f"{block['recall']['value']!s:6} ({block['recall']['wilson_lo']:.3f}-{block['recall']['wilson_hi']:.3f})  "
            f"{block['f1']:.3f}  {by.get('text', {}).get('wrong', 0):5d}      {by.get('ui', {}).get('wrong', 0):5d}"
        )
    print(f"\nshipped peak: {report['shipped_min_autocorrelation_peak']}")


if __name__ == "__main__":
    sys.exit(main())
