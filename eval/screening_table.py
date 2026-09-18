#!/usr/bin/env python3
"""The per source positives table, and the self-filmed clips that are still missing.

`eval/screen.py` runs flashmap over the media pool and records one row per clip. This module
turns those rows into the two things the pool has to be able to answer:

1. **Positives per source.** How many titles a source gave us, how many of them flashed, how
   many segments came out, and, for each rule separately, how many of those segments fired the
   general flash rule and how many fired the red flash rule. A count of "flagged segments" with
   no rule beside it hides the thing that matters most about this pool.
2. **What is still missing.** Every flagged segment so far fired the general rule and none fired
   the red rule, so the pool has no saturated red strobe in it and no sustained regular strobe.
   No free third-party footage was found that covers either, so the gap closes by filming. The
   shooting list is here, beside the counts that say why each clip is needed, and each entry
   carries `still_needed`, computed from the screening rather than asserted.

Nothing here is a threshold. The filming targets are written as multiples of the analyser's own
per second flash limit, and the concrete rate is worked out from the profile at run time, so the
only place a threshold number lives is still flashmap/docs/SPEC_SOURCES.md.

Run it two ways:

    python eval/screening_table.py            add or refresh the table in results/screening.json
    python eval/screening_table.py --check     fail if the file has no table, or it has drifted

`eval/screen.py` calls `enrich()` before it writes, so a fresh screening run already carries the
table. The CLI is for a file written by an older run, and `--check` is what CI uses to catch a
screening.json that was written without it.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCREENING = REPO / "results" / "screening.json"
LICENSES = REPO / "media" / "LICENSES.csv"

# The rules flashmap can name on a segment. Anything else is reported under "other" rather than
# folded into one of these, because a silent bucket is how a rule stops being counted.
KNOWN_RULES = ("general", "red")


def title_key(name: str) -> str:
    """One name for one title, with or without the hazard prefix screening adds."""
    stem = Path(name).stem
    return stem[len("HAZARD_") :] if stem.startswith("HAZARD_") else stem


def durations_from_ledger(path: Path = LICENSES) -> dict[str, float]:
    """Title to duration in seconds, from the licence ledger. Missing is missing."""
    out: dict[str, float] = {}
    if not path.is_file():
        return out
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("file") or "").strip()
            if not name or name.startswith("("):
                continue
            try:
                out[title_key(name)] = float(row.get("duration_s") or 0.0)
            except ValueError:
                continue
    return out


def merged_seconds(segments: list[dict]) -> float:
    """Total flagged time, with overlapping segments counted once.

    flashmap emits one segment per flagging window, and consecutive windows overlap, so adding
    the lengths up double counts badly: on the 1930 prints it roughly triples the answer.
    """
    spans = sorted(
        (float(s["start_s"]), float(s["end_s"]))
        for s in segments
        if s.get("start_s") is not None and s.get("end_s") is not None
    )
    total = 0.0
    current_start = current_end = None
    for start, end in spans:
        if current_end is None or start > current_end:
            if current_end is not None:
                total += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_end is not None:
        total += current_end - current_start
    return round(total, 3)


def positives_table(per_file: list[dict], durations: dict[str, float] | None = None) -> dict:
    """Per source: how many titles, how many flashed, and how many segments of each rule."""
    durations = durations_from_ledger() if durations is None else durations
    table: dict[str, dict] = {}

    for entry in per_file:
        source = entry.get("source", "unknown")
        row = table.setdefault(
            source,
            {
                "files": 0,
                "flagged_files": 0,
                "flagged_segments": 0,
                "files_failed_to_decode": 0,
                "segments_by_rule": {name: 0 for name in KNOWN_RULES},
                "flagged_seconds": 0.0,
                "analysed_seconds": 0.0,
                "max_flashes_in_window": 0,
                "max_area_fraction": 0.0,
                "titles": [],
                "titles_with_a_red_segment": [],
            },
        )
        row["titles"].append(entry["file"])
        if entry.get("error"):
            row["files_failed_to_decode"] += 1
            continue

        segments = entry.get("segments") or []
        row["files"] += 1
        row["flagged_segments"] += len(segments)
        row["flagged_files"] += 1 if segments else 0
        row["flagged_seconds"] = round(row["flagged_seconds"] + merged_seconds(segments), 3)
        row["analysed_seconds"] = round(
            row["analysed_seconds"] + durations.get(title_key(entry["file"]), 0.0), 3
        )
        for segment in segments:
            rule = segment.get("reason") or "unnamed"
            if rule not in row["segments_by_rule"]:
                row["segments_by_rule"][rule] = 0
            row["segments_by_rule"][rule] += 1
            if rule == "red" and entry["file"] not in row["titles_with_a_red_segment"]:
                row["titles_with_a_red_segment"].append(entry["file"])
            flashes = segment.get("max_flashes_in_window") or 0
            row["max_flashes_in_window"] = max(row["max_flashes_in_window"], int(flashes))
            area = segment.get("area_fraction") or 0.0
            row["max_area_fraction"] = max(row["max_area_fraction"], round(float(area), 6))

    for row in table.values():
        row["titles"].sort()
        row["flagged_share_of_analysed_time"] = (
            round(row["flagged_seconds"] / row["analysed_seconds"], 4)
            if row["analysed_seconds"]
            else None
        )
    return dict(sorted(table.items()))


def flash_limit_per_second() -> int | None:
    """The analyser's own per second flash limit, read from the profile, never from memory."""
    try:
        source = REPO / "flashmap" / "src"
        if source.is_dir() and str(source) not in sys.path:
            sys.path.insert(0, str(source))
        import flashmap  # noqa: PLC0415

        return int(flashmap.get_profile("wcag").flash_limit_per_second)
    except Exception:  # noqa: BLE001
        return None


# The shooting list. Each entry says what has to be in frame, how fast it has to flash as a
# multiple of the analyser's per second flash limit, and how long to roll. `still_needed` is
# filled in from the screening, so a clip drops off this list when the pool stops needing it.
#
# Safety, from docs/SAFETY.md and CLAUDE.md, applies to every one of them: whoever films is not
# photosensitive and does not look at the lights, anyone in frame consents, and the file lands
# in media/ with the HAZARD_ prefix and a row in media/LICENSES.csv before anything else runs.
SELF_FILMED: list[dict] = [
    {
        "id": "red_emergency_lightbar",
        "gap": "red",
        "must_show": (
            "a red emergency vehicle light bar filling most of the frame, shot head on after "
            "dark or against a dark wall, with nothing bright behind it. The red has to be the "
            "lamp itself, not a red wash on a pale surface, because the rule is about how "
            "saturated the red state is (profiles.WCAG.red.saturated_red_ratio)."
        ),
        "flash_rate_multiple_of_limit": 2.0,
        "duration_s": 30,
        "framing": "the flashing part covering well over half the picture height and width",
        "why": "the pool has no saturated red strobe at all, so the red rule has never fired on real footage",
    },
    {
        "id": "red_stage_wash",
        "gap": "red",
        "must_show": (
            "a red stage or party light washing the whole frame, chased on and off, with the "
            "camera close enough that the red fills the picture rather than sitting in a corner"
        ),
        "flash_rate_multiple_of_limit": 1.4,
        "duration_s": 30,
        "framing": "whole frame red at the peak of each flash",
        "why": "a red positive close to the flash limit, where a detector that rounds the rate the wrong way shows it",
    },
    {
        "id": "red_below_the_limit",
        "gap": "red-negative",
        "must_show": "the same red rig as red_stage_wash, flashing slowly, one take, nothing else changed",
        "flash_rate_multiple_of_limit": 0.6,
        "duration_s": 20,
        "framing": "identical to red_stage_wash, so the only difference between the two is the rate",
        "why": (
            "a red negative control. Without it, a red flag says only that the picture was red, "
            "and there is no way to show the rate mattered"
        ),
    },
    {
        "id": "white_strobe_steady",
        "gap": "sustained-regular-strobe",
        "must_show": (
            "a white strobe lamp pointed at a plain wall, running at a steady rate for the whole "
            "take, with the camera locked off and the exposure locked"
        ),
        "flash_rate_multiple_of_limit": 3.3,
        "duration_s": 30,
        "framing": "the lit wall filling the frame",
        "why": (
            "every flagged segment in the pool so far comes from fireworks, lightning, a cut "
            "heavy 1930 print or an explosion, all of them irregular. Nothing in the pool holds "
            "one rate for more than a second or two"
        ),
    },
    {
        "id": "strobe_small_area",
        "gap": "area-negative",
        "must_show": (
            "the same strobe as white_strobe_steady, at the same rate, but as a small lamp in a "
            "wide shot of a lit room, so the flashing part is roughly a tenth of the picture"
        ),
        "flash_rate_multiple_of_limit": 3.3,
        "duration_s": 20,
        "framing": "flashing area well under the profile's area fraction limit (profiles.WCAG.area_fraction_limit)",
        "why": (
            "an area rule negative: real flashing, fast enough to fail on rate alone, that the "
            "area condition should rescue. The pool has no such clip, so the area rule is only "
            "exercised by generated clips"
        ),
    },
]

FILMING_NOTES = [
    "Film at 60 fps if the camera offers it, with the shutter and exposure locked. A rolling "
    "shutter at 24 or 30 fps can beat against a strobe and record a rate that is not the one in "
    "the room, and the analyser would then be measuring the camera.",
    "Do not use the phone's own torch or any auto exposure. Auto exposure chases the flashes and "
    "turns a square wave into a ramp.",
    "One take per entry, no cuts inside the take, and no colour grading afterwards. The file that "
    "lands in media/ is the file that came off the camera.",
    "Write the rate you actually set into media/LICENSES.csv in the notes column. What was "
    "intended and what the lamp did are two different numbers.",
    "Safety first, every take: whoever films is not photosensitive and does not look at the "
    "lights, anyone in frame consents, and the clip goes into media/ with the HAZARD_ prefix "
    "before anything opens it.",
]


def self_filmed_needed(table: dict) -> dict:
    """The shooting list, with each entry marked still needed or not from the screening."""
    limit = flash_limit_per_second()
    red_segments = sum(row["segments_by_rule"].get("red", 0) for row in table.values())
    clips = []
    for entry in SELF_FILMED:
        multiple = entry["flash_rate_multiple_of_limit"]
        clip = dict(entry)
        clip["flash_rate_per_second"] = round(limit * multiple, 1) if limit else None
        clip["still_needed"] = red_segments == 0 if entry["gap"].startswith("red") else True
        clips.append(clip)
    return {
        "what_this_is": (
            "a shooting list, not a measurement. It says what has to be filmed because no "
            "licensed footage we could find covers it."
        ),
        "flash_limit_per_second_from_profile": limit,
        "flash_rate_note": (
            "every rate here is a multiple of the analyser's own per second flash limit, read "
            "from the wcag profile at run time. No threshold is written out in this file."
        ),
        "red_segments_in_the_pool": red_segments,
        "clips": clips,
        "filming_notes": FILMING_NOTES,
    }


def enrich(report: dict) -> dict:
    """Add the positives table and the shooting list to a screening report, in place."""
    table = positives_table(report.get("per_file", []))
    report["per_source"] = table
    by_rule: dict[str, int] = {}
    for row in table.values():
        for rule, count in row["segments_by_rule"].items():
            by_rule[rule] = by_rule.get(rule, 0) + count
    totals = report.setdefault("totals", {})
    totals["segments_by_rule"] = dict(sorted(by_rule.items()))
    totals["red_rule_segments"] = by_rule.get("red", 0)
    totals["sources_with_a_red_segment"] = sum(
        1 for row in table.values() if row["segments_by_rule"].get("red", 0)
    )
    totals["red_rule_statement"] = (
        "no segment in this pool fired the red flash rule"
        if by_rule.get("red", 0) == 0
        else f"{by_rule['red']} segments fired the red flash rule"
    )
    report["self_filmed_needed"] = self_filmed_needed(table)
    return report


def check(report: dict) -> list[str]:
    """Everything wrong with the table in a screening report. Empty means it is current."""
    problems = []
    if "self_filmed_needed" not in report:
        problems.append("no self_filmed_needed block: this file was written without the table")
    fresh = enrich(json.loads(json.dumps(report)))
    if report.get("per_source") != fresh["per_source"]:
        problems.append("per_source has drifted from per_file")
    for field in ("segments_by_rule", "red_rule_segments", "red_rule_statement"):
        if report.get("totals", {}).get(field) != fresh["totals"][field]:
            problems.append(f"totals.{field} has drifted from per_file")
    if report.get("self_filmed_needed", {}).get("clips") != fresh["self_filmed_needed"]["clips"]:
        problems.append("self_filmed_needed.clips has drifted from the screening counts")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("-f", "--file", type=Path, default=SCREENING)
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write. Exit non-zero if the table is missing or has drifted",
    )
    arguments = parser.parse_args()

    if not arguments.file.is_file():
        print(f"{arguments.file} does not exist. Run eval/screen.py first.", file=sys.stderr)
        return 2
    report = json.loads(arguments.file.read_text())

    if arguments.check:
        problems = check(report)
        for problem in problems:
            print(f"{arguments.file}: {problem}", file=sys.stderr)
        if problems:
            print(
                "Re-run `python eval/screening_table.py` to rebuild the table from per_file.",
                file=sys.stderr,
            )
            return 2
        print(f"{arguments.file}: the per source table matches per_file")
        return 0

    enrich(report)
    arguments.file.write_text(json.dumps(report, indent=2) + "\n")
    rule_counts = report["totals"]["segments_by_rule"]
    print(f"wrote {arguments.file}")
    print(f"  segments by rule: {rule_counts}")
    print(f"  {report['totals']['red_rule_statement']}")
    still = [c["id"] for c in report["self_filmed_needed"]["clips"] if c["still_needed"]]
    print(f"  self-filmed clips still needed: {len(still)} ({', '.join(still)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
