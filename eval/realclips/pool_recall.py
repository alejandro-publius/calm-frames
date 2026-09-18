#!/usr/bin/env python3
"""Recall against the pooled candidates, which is the only recall the real clips can give yet.

Nobody has labelled a segment, and nobody on this lane will. So there is no ground truth here
and there is no precision here. What there is, is the thing the labelling pool is built on: the
union of what every candidate list proposed. Measuring each detector against that union says how
much of everything anybody proposed each one found, and that is the number the README's caveat
was about.

Read it for what it is. A window is "positive" here because some detector proposed it, not
because a person looked at a plot and said a flash was there. So:

- this is an upper bound on recall, not recall. A hazard every one of the four lists missed is
  in nobody's union and costs nobody anything here;
- it cannot be compared with the conformance recall in results/conformance.json, which is
  measured against ground truth computed from the spec text;
- a detector's own flags are always inside the union, so its coverage can only fall when a new
  list joins. That is the whole point: before EA IRIS was a candidate list, every detector's
  coverage of the union was measured against a smaller union, and the number flattered them by
  an amount nobody could name.

Both unions are reported, side by side, for exactly that reason: the four list union that stands
now, and the three list union that stood before IRIS was built. Publishing only the friendlier
of a pair is the mistake CLAUDE.md names four times over, so the pair travels together.

Two scopes, because they answer different questions:

- `all_titles`, every one second window of every title all four lists have analysed. The stable
  measurement, and the one to quote;
- `pool_segments`, the windows of the blinded segments in eval/labeling/pool_key.json. The
  sample two people will actually label, and a much smaller denominator.

The headline interval is the bootstrap over titles, because windows inside one title are not
independent. Wilson is reported beside it and marked optimistic, the same way every other set in
this repository does it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from labeling.make_pool import (  # noqa: E402
    CANDIDATE_LISTS,
    detector_intervals,
    eligible_titles,
    iris_build,
    title_key,
)
from metrics import (  # noqa: E402
    bootstrap_groups,
    rate_with_interval,
    window_count,
    windows_from_intervals,
)

REPO = _EVAL_DIR.parent
LABELING = _EVAL_DIR / "labeling"
BASELINES = REPO / "results" / "baselines"
OUT = REPO / "results" / "pool_recall.json"

# The lists as they stood before EA IRIS was built, kept so the two unions can be compared.
LISTS_BEFORE_IRIS = tuple(name for name in CANDIDATE_LISTS if name != "iris")


def windows_per_title(
    flags: dict[str, dict[str, list[tuple[float, float]]]],
    titles: list[tuple[str, dict, float]],
    min_overlap: float,
) -> dict[str, dict[str, set[int]]]:
    """Each detector's positive windows, per title, over the whole clip."""
    out: dict[str, dict[str, set[int]]] = {}
    for name, _row, duration in titles:
        key = title_key(name)
        # Through the shared counter, so a trailing remainder is dropped here the same way it
        # is everywhere else in this repository.
        n_windows = window_count(duration * 1000.0)
        per_detector: dict[str, set[int]] = {}
        for detector, intervals in flags.get(key, {}).items():
            per_detector[detector] = windows_from_intervals(
                [(start * 1000.0, end * 1000.0) for start, end in intervals],
                n_windows=n_windows,
                min_overlap=min_overlap,
            )
        out[name] = per_detector
    return out


def windows_per_segment(
    flags: dict[str, dict[str, list[tuple[float, float]]]],
    key: dict,
    min_overlap: float,
) -> dict[str, dict[str, set[int]]]:
    """The same, restricted to the blinded segments, keyed by segment id.

    The grouping for the bootstrap is still the title, so each segment carries the file it came
    from. Two segments of one film are not two independent draws.
    """
    out: dict[str, dict[str, set[int]]] = {}
    for segment in key["segments"]:
        name = title_key(segment["file"])
        start_ms = float(segment["start_s"]) * 1000.0
        end_ms = float(segment["end_s"]) * 1000.0
        n_windows = int(round((end_ms - start_ms) / 1000.0))
        per_detector: dict[str, set[int]] = {}
        for detector, intervals in flags.get(name, {}).items():
            clipped = [
                (max(start * 1000.0, start_ms), min(end * 1000.0, end_ms))
                for start, end in intervals
                if end * 1000.0 > start_ms and start * 1000.0 < end_ms
            ]
            per_detector[detector] = windows_from_intervals(
                clipped, n_windows=n_windows, origin_ms=start_ms, min_overlap=min_overlap
            )
        out[segment["segment_id"]] = {"file": segment["file"], "detectors": per_detector}
    return out


def score(
    groups: dict[str, dict[str, set[int]]],
    group_file: dict[str, str],
    lists: tuple[str, ...],
) -> dict:
    """Per detector coverage of the union of `lists`, pooled over windows and over titles."""
    totals: dict[str, int] = defaultdict(int)
    per_title: dict[str, dict[str, int]] = {name: defaultdict(int) for name in lists}
    union_per_title: dict[str, int] = defaultdict(int)
    union_total = 0
    sole_source: dict[str, int] = defaultdict(int)

    for group, per_detector in groups.items():
        file = group_file[group]
        union: set[int] = set()
        for detector in lists:
            union |= per_detector.get(detector, set())
        union_total += len(union)
        union_per_title[file] += len(union)
        for detector in lists:
            found = per_detector.get(detector, set()) & union
            totals[detector] += len(found)
            per_title[detector][file] += len(found)
        for index in union:
            proposers = [
                detector for detector in lists if index in per_detector.get(detector, set())
            ]
            if len(proposers) == 1:
                sole_source[proposers[0]] += 1

    table = {}
    for detector in lists:
        rate = rate_with_interval(totals[detector], union_total)
        table[detector] = {
            "recall_against_the_union": rate,
            "bootstrap_over_titles": bootstrap_groups(
                [
                    (per_title[detector][file], union_per_title[file])
                    for file in sorted(union_per_title)
                ]
            ),
            "windows_only_this_list_proposed": sole_source[detector],
        }
    return {
        "candidate_lists": list(lists),
        "union_windows": union_total,
        "titles": len(union_per_title),
        "table": table,
    }


def iris_over_the_whole_pool() -> dict:
    """What IRIS did over every clip it was pointed at, not only the titles in scope here.

    The titles in scope are the ones every candidate list has analysed. IRIS was run over the
    whole of media/, which is more, and the count of what it flagged there is a fact about
    IRIS rather than about this pool. It belongs in the same file as the recall it changed.
    """
    reports = sorted((BASELINES / "iris").glob("*.json"))
    failures_path = BASELINES / "iris_failures.json"
    failures = json.loads(failures_path.read_text()) if failures_path.is_file() else {}
    flagged = 0
    warned = 0
    clips_with_a_flag = 0
    for path in reports:
        data = json.loads(path.read_text())
        flagged += data.get("segment_count", 0)
        warned += data.get("warning_segment_count", 0)
        if data.get("segment_count", 0):
            clips_with_a_flag += 1
    return {
        "clips_analyzed": len(reports),
        "clips_it_could_not_decode": failures.get("failed", 0),
        "why_it_could_not": failures.get("failures", {}),
        "flagged_segments": flagged,
        "clips_with_at_least_one_flag": clips_with_a_flag,
        "warning_segments": warned,
        "warning_segments_are_not_flags": (
            "IRIS passes flashing between 2 and 3 Hz. Those frames are counted here so that "
            "'IRIS flagged nothing' can be told apart from 'IRIS saw nothing'."
        ),
    }


def build(min_overlap: float) -> dict:
    flags = detector_intervals()
    titles, skipped = eligible_titles(flags)

    by_title = windows_per_title(flags, titles, min_overlap)
    title_file = {name: name for name in by_title}

    key_path = LABELING / "pool_key.json"
    pool_scope = None
    if key_path.is_file():
        key = json.loads(key_path.read_text())
        by_segment = windows_per_segment(flags, key, min_overlap)
        segment_detectors = {
            segment_id: row["detectors"] for segment_id, row in by_segment.items()
        }
        segment_file = {segment_id: row["file"] for segment_id, row in by_segment.items()}
        pool_scope = {
            "segments": len(by_segment),
            "now": score(segment_detectors, segment_file, CANDIDATE_LISTS),
            "before_iris_was_built": score(segment_detectors, segment_file, LISTS_BEFORE_IRIS),
        }

    now = score(by_title, title_file, CANDIDATE_LISTS)
    before = score(by_title, title_file, LISTS_BEFORE_IRIS)
    flashmap_now = now["table"]["flashmap"]["recall_against_the_union"]["value"]
    flashmap_before = before["table"]["flashmap"]["recall_against_the_union"]["value"]

    report = {
        "generated_on": "2026-09-18",
        "set": "real clips, every window of every title all candidate lists have analysed",
        "what_this_measures": (
            "each detector against the union of what the candidate lists proposed, not against "
            "ground truth. Nobody has labelled anything. A window is positive here because some "
            "detector proposed it, so this is an upper bound on recall and it is not comparable "
            "with the conformance recall."
        ),
        "no_labels_yet": True,
        "window_rule": "any overlap" if min_overlap == 0 else f"at least {min_overlap:.0%}",
        "headline_interval": "bootstrap over titles, 10000 resamples",
        "wilson_note": (
            "reported as the optimistic bound, because windows in one title are not independent"
        ),
        "iris_build": iris_build(),
        "iris_over_the_whole_pool": iris_over_the_whole_pool(),
        "titles_in_scope": sorted(name for name, _row, _duration in titles),
        "titles_skipped": skipped,
        "all_titles": {"now": now, "before_iris_was_built": before},
        "pool_segments": pool_scope,
        "what_iris_cost_the_estimate": {
            "flashmap_recall_before_iris_was_a_candidate_list": flashmap_before,
            "flashmap_recall_now": flashmap_now,
            "difference": (
                None
                if flashmap_before is None or flashmap_now is None
                else flashmap_before - flashmap_now
            ),
            "iris_only_windows": now["table"]["iris"]["windows_only_this_list_proposed"],
            "read_it_like_this": (
                "the first number is what this repository could have published while IRIS was "
                "missing. The second is the same measurement against a union that now includes "
                "IRIS. The drop is the part of the old estimate that was optimism, and it is no "
                "longer unknown."
            ),
        },
    }
    report["published"] = {
        "flashmap_pool_recall": flashmap_now,
        "flashmap_pool_recall_lo": now["table"]["flashmap"]["bootstrap_over_titles"]["lo"],
        "flashmap_pool_recall_hi": now["table"]["flashmap"]["bootstrap_over_titles"]["hi"],
        "flashmap_pool_recall_before_iris": flashmap_before,
        "union_windows": now["union_windows"],
        "titles": now["titles"],
        "iris_only_windows": now["table"]["iris"]["windows_only_this_list_proposed"],
        "candidate_lists": len(CANDIDATE_LISTS),
        "iris_clips_analyzed": report["iris_over_the_whole_pool"]["clips_analyzed"],
        "iris_clips_it_could_not_decode": report["iris_over_the_whole_pool"][
            "clips_it_could_not_decode"
        ],
        "iris_flagged_segments": report["iris_over_the_whole_pool"]["flagged_segments"],
        "iris_warning_segments": report["iris_over_the_whole_pool"]["warning_segments"],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("-o", "--out", type=Path, default=OUT)
    parser.add_argument("--min-overlap", type=float, default=0.0)
    arguments = parser.parse_args()

    report = build(arguments.min_overlap)
    arguments.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(f"wrote {arguments.out}")
    now = report["all_titles"]["now"]
    print(
        f"  {now['titles']} titles, {now['union_windows']} windows in the union of "
        f"{len(CANDIDATE_LISTS)} candidate lists"
    )
    for name, row in now["table"].items():
        rate = row["recall_against_the_union"]
        boot = row["bootstrap_over_titles"]
        value = "n/a" if rate["value"] is None else f"{rate['value']:.3f}"
        interval = (
            "n/a"
            if boot["lo"] is None
            else f"{boot['lo']:.3f} to {boot['hi']:.3f}"
        )
        print(
            f"  {name:24s} {value} ({interval}), "
            f"{rate['numerator']}/{rate['denominator']}, "
            f"{row['windows_only_this_list_proposed']} only it proposed"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
