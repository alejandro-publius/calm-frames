"""Rebuild the software-level lead time summary from its own event archive.

`eval/gate1_software.py` writes two files: a summary, and the raw events that
produced it. This rebuilds the summary from the events and fails if the two
disagree, so a published number is never the only copy of itself.

    python3 eval/verify_gate1_archive.py

WHY THIS EXISTS. The archive is the pooled events from every pass, one pass
after another, and the pass boundaries are not marked in the events. They live
in the summary instead, as the event count of each pass. Split it any other way
and the answer is wrong in a way that looks fine: on Sep 17, 2026 a split at
each `harness-start` event gave 54 trials rather than 49, with one lead time of
13.3 seconds that came from interpolating a media position across two separate
app launches. Nothing about that reads as broken. It is only wrong.

So the recipe is written down here and run in CI, rather than being something a
reader has to work out. If this fails, either the archive was edited or the
summary was, and neither of them can be published until it passes.

WHAT IT CATCHES. Checked by breaking each one on purpose on Sep 17, 2026: a
published number edited, an event missing from the archive, a pass boundary
moved far enough to put two app launches in one pass, a lead time nudged, and
the wrong marker schedule passed in. All five go red.

WHAT IT DOES NOT CATCH. Moving a boundary by a single event, when that event is
not a harness-start and no interpolation needs it. That was tried too and it
stays green, because it changes nothing: every rebuilt number comes back
identical. A difference that cannot reach a published number is not one this
has to find.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO / "eval"))

from gate1_software import (  # noqa: E402
    summarize,
    trials_from_events,
    wilson_interval,
)

# The fields that have to come back identical. Everything else in the summary
# is a timestamp or a description of the run.
REBUILT_FIELDS = (
    "trials_attempted",
    "in_time_strict_fraction",
    "wilson_95_interval_strict",
    "trials_counted",
    "trials_dropped_no_timeupdate",
    "trials_dropped_playback_stalled",
    "in_time",
    "in_time_fraction",
    "wilson_95_interval",
    "lead_ms",
    "lead_ms_unforced",
    "lead_media_ms",
    "lead_media_ms_unforced",
    "forced_covers",
    "worst_lead_ms",
)


def split_passes(events: list[dict], summary: dict) -> list[list[dict]]:
    """The events of each pass, in order, from the counts in the summary."""
    counts = [entry["events"] for entry in summary["passes"]]
    if sum(counts) != len(events):
        raise ValueError(
            f"the summary accounts for {sum(counts)} events and the archive "
            f"holds {len(events)}, so the two are not from the same run"
        )
    blocks = []
    at = 0
    for count in counts:
        blocks.append(events[at : at + count])
        at += count

    # Each block is one app launch, so each block holds exactly one
    # harness-start. This is what catches a boundary that has moved: the counts
    # can still add up to the right total while the splits sit in the wrong
    # places, and the lead times that come out of that look ordinary. It is not
    # enough to check the total.
    #
    # Note that the harness-start is not always the first event in its block.
    # In the Sep 17, 2026 run two passes opened with a batch the previous app
    # instance had posted late, putting the start 74 and 23 events in. That is
    # the same fact that makes splitting on harness-start the wrong recipe.
    wrong = [
        (index, sum(1 for e in block if e.get("kind") == "harness-start"))
        for index, block in enumerate(blocks)
    ]
    wrong = [(index, found) for index, found in wrong if found != 1]
    if wrong:
        detail = ", ".join(f"pass {i + 1} has {n}" for i, n in wrong)
        raise ValueError(
            "the pass boundaries do not line up with the app launches: every "
            f"pass should hold exactly one harness-start, but {detail}"
        )
    return blocks


def rebuild(events: list[dict], summary: dict, schedule: dict) -> dict:
    trials: list[dict] = []
    per_pass: list[int] = []
    for block in split_passes(events, summary):
        found = trials_from_events(block, schedule, summary["guard_band_ms"])
        trials += found
        per_pass.append(len([t for t in found if t.get("counted")]))

    counted = [t for t in trials if t.get("counted")]
    leads = [float(t["lead_ms"]) for t in counted]
    in_time = [t for t in counted if t.get("in_time")]

    return {
        # Strict first, because it is the worse of the two and the one a reader
        # should meet first. It counts every trial that was started, including
        # the ones that produced no usable evidence, as a failure.
        "trials_attempted": len(trials),
        "in_time_strict_fraction": (
            round(len(in_time) / len(trials), 4) if trials else None
        ),
        "wilson_95_interval_strict": wilson_interval(len(in_time), len(trials)),
        "trials_counted": len(counted),
        "trials_dropped_no_timeupdate": len(
            [
                t
                for t in trials
                if not t.get("counted") and "stalled" not in str(t.get("why", ""))
            ]
        ),
        "trials_dropped_playback_stalled": len(
            [t for t in trials if "stalled" in str(t.get("why", ""))]
        ),
        "in_time": len(in_time),
        "in_time_fraction": round(len(in_time) / len(counted), 4) if counted else None,
        "wilson_95_interval": wilson_interval(len(in_time), len(counted)),
        "lead_ms": summarize(leads),
        "lead_ms_unforced": summarize(
            [float(t["lead_ms"]) for t in counted if not t.get("forced_by")]
        ),
        "lead_media_ms": summarize(
            [float(t["lead_media_ms"]) for t in counted if "lead_media_ms" in t]
        ),
        "lead_media_ms_unforced": summarize(
            [
                float(t["lead_media_ms"])
                for t in counted
                if "lead_media_ms" in t and not t.get("forced_by")
            ]
        ),
        "forced_covers": len([t for t in counted if t.get("forced_by")]),
        "worst_lead_ms": round(min(leads), 1) if leads else None,
        "_trials_per_pass": per_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary", type=Path, default=REPO / "results/gate1_software_vvd.json"
    )
    parser.add_argument(
        "--events",
        type=Path,
        default=REPO / "results/gate1_software_vvd_events.json",
    )
    parser.add_argument(
        "--schedule",
        type=Path,
        default=REPO / "eval/harness_runs/marker_schedule_packed.json",
    )
    args = parser.parse_args()

    if not args.summary.exists() or not args.events.exists():
        print(
            f"nothing to check: {args.summary.name} or {args.events.name} is missing",
            file=sys.stderr,
        )
        return 1

    summary = json.loads(args.summary.read_text())
    events = json.loads(args.events.read_text())
    schedule = json.loads(args.schedule.read_text())

    if schedule["clip"]["sha256"] != summary["clip_sha256"]:
        print(
            "the schedule is not the one the run used: "
            f"{args.schedule.name} is for clip {schedule['clip']['sha256'][:12]} "
            f"and the summary records {summary['clip_sha256'][:12]}",
            file=sys.stderr,
        )
        return 1

    try:
        rebuilt = rebuild(events, summary, schedule)
    except ValueError as error:
        print(f"{args.summary.name} does not match its own events:", file=sys.stderr)
        print(f"  {error}", file=sys.stderr)
        return 1
    per_pass = rebuilt.pop("_trials_per_pass")

    problems = []
    for field in REBUILT_FIELDS:
        if rebuilt[field] != summary.get(field):
            problems.append(
                f"  {field}: the archive rebuilds {rebuilt[field]!r}, "
                f"the summary says {summary.get(field)!r}"
            )
    recorded_per_pass = [entry["trials"] for entry in summary["passes"]]
    if per_pass != recorded_per_pass:
        problems.append(
            f"  trials per pass: the archive rebuilds {per_pass}, "
            f"the summary says {recorded_per_pass}"
        )

    if problems:
        print(
            f"{args.summary.name} does not match its own events:", file=sys.stderr
        )
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    print(
        f"{args.summary.name} rebuilds from {args.events.name}: "
        f"{summary['trials_counted']} trials over {len(summary['passes'])} passes, "
        f"{summary['in_time']} in time"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
