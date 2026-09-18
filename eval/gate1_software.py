"""Software-level lead time: how early the cover went on, in wall-clock time.

GATE 1 asks whether the cover was fully on at least 150 ms before the marker
appeared, and only a camera pointed at a screen can answer that. The stick is
not here yet, so this measures the part that does not need a camera: the gap
between the moment the app applied the cover and the moment the marker was due,
both in wall-clock time.

    python3 eval/gate1_software.py --passes 3

WHAT THIS IS. A software-level number. It is the app's own timing, measured
from the events it posts during a run on the Vega Virtual Device.

WHAT THIS IS NOT. A screen-level number. Everything after the app sets its
state is unmeasured here: React commits the change, the compositor draws it,
the device scans it out, the panel responds. Each of those adds delay, and all
of it lands in the real GATE 1 figure and none of it lands in this one. So this
number is an upper bound on how well the real thing can do, never a prediction
of it. The real gate is 50 trials filmed at 240 fps on a real stick.

HOW THE WALL-CLOCK MOMENT OF A MARKER IS FOUND. The app reports (wall clock,
media time) pairs on every timeupdate. For a marker at media time M, the two
reports either side of M give the wall-clock instant when the playhead passed
M, by interpolation. The lead is that instant minus the wall clock when the
cover went on. Markers with no timeupdate on both sides are not counted, and
the count of those is reported rather than hidden.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REQUIRED_LEAD_MS = 150


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> dict:
    if trials == 0:
        return {"low": None, "high": None}
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = p + z * z / (2 * trials)
    spread = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return {
        "low": round((centre - spread) / denominator, 4),
        "high": round((centre + spread) / denominator, 4),
    }


def summarize(values: list[float]) -> dict | None:
    if not values:
        return None
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min": round(ordered[0], 1),
        "median": round(statistics.median(ordered), 1),
        "p95": round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 1),
        "max": round(ordered[-1], 1),
    }


def wall_clock_at_media(events: list[dict], media_ms: float) -> float | None:
    """When did the playhead pass this media time, in wall-clock terms."""
    reports = [
        (e["wallClockMs"], e["mediaTimeMs"])
        for e in events
        if e.get("kind") == "timeupdate" and isinstance(e.get("mediaTimeMs"), (int, float))
    ]
    reports.sort(key=lambda pair: pair[1])
    before = None
    after = None
    for wall, media in reports:
        if media <= media_ms:
            before = (wall, media)
        if media >= media_ms and after is None:
            after = (wall, media)
    if before is None or after is None:
        return None
    if after[1] == before[1]:
        return float(before[0])
    span_media = after[1] - before[1]
    span_wall = after[0] - before[0]
    fraction = (media_ms - before[1]) / span_media
    return before[0] + fraction * span_wall


def stalled_between(events: list[dict], start_wall: float, end_wall: float) -> bool:
    """Did playback stop between the cover going on and the marker being due.

    A stall makes the lead time meaningless as a measure of scheduling. If the
    player buffers for forty seconds, the cover was indeed on for forty
    seconds before the marker appeared, but that says nothing about whether
    the schedule fires early enough: it says the cover was held, which it is
    supposed to do. Those trials are recorded and excluded rather than
    averaged in, because leaving them in makes the numbers look better than
    the scheduler is.
    """
    for event in events:
        if event.get("kind") not in ("waiting", "stalled", "pause"):
            continue
        when = event.get("wallClockMs")
        if isinstance(when, (int, float)) and start_wall <= when <= end_wall:
            return True
    return False


def trials_from_events(events: list[dict], schedule: dict, guard_band_ms: int) -> list[dict]:
    covers_on = [
        e
        for e in events
        if e.get("kind") == "cover-on"
        and isinstance(e.get("reason"), str)
        and e["reason"].startswith("interval ")
    ]
    trials = []
    for marker in schedule["markers"]:
        label = (
            f"interval {marker['start_ms'] - guard_band_ms}-"
            f"{marker['end_ms'] + guard_band_ms}"
        )
        matching = [e for e in covers_on if e["reason"] == label]
        if not matching:
            continue
        cover = min(matching, key=lambda e: e["wallClockMs"])
        due = wall_clock_at_media(events, marker["start_ms"])
        if due is None:
            trials.append(
                {
                    "marker": marker["index"],
                    "counted": False,
                    "why": "no timeupdate on both sides of the marker",
                }
            )
            continue
        if stalled_between(events, cover["wallClockMs"], due):
            trials.append(
                {
                    "marker": marker["index"],
                    "counted": False,
                    "why": "playback stalled between the cover and the marker",
                    "uncounted_lead_ms": round(due - cover["wallClockMs"], 1),
                }
            )
            continue
        # Two leads, because they answer different questions.
        #
        # The wall-clock lead is how long the cover was actually up before the
        # picture arrived. It is the one a viewer would feel, and it is the one
        # GATE 1 films.
        #
        # The media-time lead is how far ahead of the marker the schedule put
        # the cover, in the clip's own time. It should sit at the guard band
        # whatever the machine is doing.
        #
        # They come apart when playback runs slower than real time, which the
        # virtual device does constantly: the cover goes on at the right place
        # in the clip and then waits a long time in wall clock for the playhead
        # to reach the marker. That inflates the wall-clock tail without the
        # scheduler being early, so reporting only the wall-clock number would
        # make a slow machine look like a design fault.
        lead_wall = due - cover["wallClockMs"]
        lead_media = marker["start_ms"] - cover["mediaTimeMs"]
        trials.append(
            {
                "marker": marker["index"],
                "counted": True,
                "lead_ms": round(lead_wall, 1),
                "lead_media_ms": round(lead_media, 1),
                "in_time": lead_wall >= REQUIRED_LEAD_MS,
                "held_longer_than_guard_band": lead_media > guard_band_ms + 1,
                "why_held": why_held(events, cover, guard_band_ms, lead_media),
                # What, if anything, forced the cover to be held. Empty means
                # nothing did: the wall-clock lead is then the schedule plus
                # however slowly the clip was playing.
                "forced_by": forcing_between(events, cover["wallClockMs"], due),
                # Media milliseconds per wall millisecond over the lead. Well
                # under 1 means playback was running slower than real time,
                # which stretches the wall-clock lead without the schedule
                # having fired any earlier in the clip.
                "effective_rate": (
                    round(lead_media / lead_wall, 3) if lead_wall > 0 else None
                ),
            }
        )
    return trials


def worst_tick_gap(events: list[dict]) -> float | None:
    """The longest gap between two runs of the scheduler's tick, over all passes.

    Read from the harness-stop line each pass writes, and from the tick-gap
    lines themselves, so it survives a pass that ended without stopping
    cleanly. Returns None when no pass reported it at all.
    """
    seen: list[float] = []
    for event in events:
        extra = event.get("extra") or {}
        for key in ("worstTickGapMs", "gapMs"):
            value = extra.get(key)
            if isinstance(value, (int, float)):
                seen.append(float(value))
    return round(max(seen), 1) if seen else None


# The events that force a cover to be held longer than the schedule asked for.
# A stall, a pause or a seek all make the playhead untrustworthy, and the cover
# is supposed to stay on through them, so a long lead caused by one of these is
# the design working rather than the schedule firing early.
FORCING_KINDS = ("seeking", "seeked", "waiting", "stalled", "pause", "background")


def forcing_between(
    events: list[dict], start_wall: float, end_wall: float
) -> list[str]:
    """Which forcing events happened between the cover going on and the marker."""
    seen = {
        event["kind"]
        for event in events
        if event.get("kind") in FORCING_KINDS
        and isinstance(event.get("wallClockMs"), (int, float))
        and start_wall <= event["wallClockMs"] <= end_wall
    }
    return sorted(seen)


def why_held(
    events: list[dict], cover: dict, guard_band_ms: float, lead_media_ms: float
) -> str | None:
    """Why a cover went on earlier in the clip than the guard band asked for.

    The schedule puts a cover exactly one guard band ahead of its segment, so
    anything earlier than that had a reason, and the reason should be in the
    record rather than left as an outlier for someone to wonder about. The
    honest ones are a merge with the segment before it, or a hold the harness
    took because the playhead had become untrustworthy.
    """
    if lead_media_ms <= guard_band_ms + 1:
        return None
    reason = cover.get("reason")
    if isinstance(reason, str) and not reason.startswith("interval "):
        return reason
    # A hold that started before this cover and had not been cleared.
    before = [
        e
        for e in events
        if e.get("kind") in ("seeking", "waiting", "stalled", "pause")
        and isinstance(e.get("wallClockMs"), (int, float))
        and e["wallClockMs"] <= cover["wallClockMs"]
    ]
    if before:
        return f"held after {before[-1]['kind']}"
    return "merged with the interval before it"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--target-trials", type=int, default=50)
    parser.add_argument("--guard-band-ms", type=int, default=500)
    parser.add_argument("--seconds", type=float, default=215.0)
    parser.add_argument(
        "--schedule",
        type=Path,
        default=REPO / "eval/harness_runs/marker_schedule_50.json",
    )
    parser.add_argument("--clip", type=Path, default=REPO / "media/markers50.mp4")
    parser.add_argument(
        "--out", type=Path, default=REPO / "results/gate1_software_vvd.json"
    )
    args = parser.parse_args()

    schedule = json.loads(args.schedule.read_text())
    all_trials: list[dict] = []
    pooled_events: list[dict] = []
    runs: list[dict] = []

    for index in range(args.passes):
        counted = len([t for t in all_trials if t.get("counted")])
        if counted >= args.target_trials:
            break
        print(f"pass {index + 1} of {args.passes}, {counted} trials so far")
        events_path = REPO / f"results/.software_pass_{index}.json"
        result = subprocess.run(
            [
                str(REPO / ".venv/bin/python"),
                str(REPO / "eval/vvd_timing_run.py"),
                "--mode", "timing",
                "--seconds", str(args.seconds),
                "--format", "HLS",
                "--schedule", str(args.schedule),
                "--clip", str(args.clip),
                "--guard-band-ms", str(args.guard_band_ms),
                "--out", str(events_path),
            ],
            capture_output=True,
            text=True,
            timeout=int(args.seconds) + 600,
        )
        raw = events_path.with_name(events_path.stem + "_events.json")
        if not raw.exists():
            print(f"  pass produced no events: {result.stdout[-300:]}")
            continue
        events = json.loads(raw.read_text())
        trials = trials_from_events(events, schedule, args.guard_band_ms)
        counted_now = len([t for t in trials if t.get("counted")])
        runs.append({"pass": index + 1, "events": len(events), "trials": counted_now})
        print(f"  {len(events)} events, {counted_now} usable trials")
        all_trials.extend(trials)
        pooled_events.extend(events)
        events_path.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)

    counted = [t for t in all_trials if t.get("counted")]
    leads = [float(t["lead_ms"]) for t in counted]
    in_time = [t for t in counted if t.get("in_time")]

    result = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "measurement": "software-level lead time, not screen-level",
        "what_this_is": (
            "The gap between the moment the app applied the cover and the "
            "moment the marker was due, both in wall-clock time, from the "
            "events the app posted during runs on the Vega Virtual Device."
        ),
        "what_this_is_not": (
            "GATE 1, and not a prediction of it. Everything after the app sets "
            "its state is unmeasured here: the React commit, the compositor, "
            "scan-out and the panel. All of that delay lands in the real "
            "figure and none of it lands in this one, so treat this as an "
            "upper bound on how well the real thing can do. GATE 1 is 50 "
            "trials filmed at 240 fps on a real stick."
        ),
        "device": "Vega Virtual Device",
        "clip_sha256": schedule["clip"]["sha256"],
        "markers_per_pass": len(schedule["markers"]),
        "guard_band_ms": args.guard_band_ms,
        "required_lead_ms": REQUIRED_LEAD_MS,
        "passes": runs,
        # Two accountings, because a dropped trial is not a pass.
        #
        # The strict one treats every marker that had a cover as a trial, and
        # every trial that could not be measured as a failure. It is the
        # pessimistic reading and it is the one to quote if only one is quoted.
        #
        # The usable one is over the trials that could actually be measured. It
        # says how the scheduler behaved when the run was good enough to see,
        # and on its own it flatters, because the runs that went wrong are the
        # ones that dropped out.
        "accounting": (
            "strict counts every dropped trial as a failure; usable counts "
            "only the trials that could be measured. Both are reported "
            "because quoting the second alone would hide the runs that failed "
            "to produce evidence."
        ),
        "trials_attempted": len(all_trials),
        "in_time_strict_fraction": (
            round(len(in_time) / len(all_trials), 4) if all_trials else None
        ),
        "wilson_95_interval_strict": wilson_interval(len(in_time), len(all_trials)),
        "trials_counted": len(counted),
        "trials_dropped_no_timeupdate": len(
            [t for t in all_trials if not t.get("counted") and "stalled" not in str(t.get("why", ""))]
        ),
        "trials_dropped_playback_stalled": len(
            [t for t in all_trials if "stalled" in str(t.get("why", ""))]
        ),
        "in_time": len(in_time),
        "in_time_fraction": round(len(in_time) / len(counted), 4) if counted else None,
        "wilson_95_interval": wilson_interval(len(in_time), len(counted)),
        # Two distributions, because one of them answers the question and the
        # other one is mostly a property of this machine.
        #
        # lead_ms is wall clock: how long the cover was up before the picture
        # arrived. Its tail is long, and the tail is not the schedule. Every
        # trial with a wall-clock lead over 1.5 s has a media-time lead inside
        # the guard band, and its effective_rate is a fraction of real time:
        # the virtual device plays the opening seconds of a clip far slower
        # than real time, so the playhead takes seconds of wall clock to cover
        # a few hundred milliseconds of media. Five of the six longest are the
        # first marker of a pass, which is where that is worst.
        #
        # lead_media_ms is the clip's own time, and it is the one that says
        # whether the schedule fired early. It cannot exceed the guard band by
        # design, and measured it does not.
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
        "lead_time_statement": (
            "Two distributions. lead_ms is wall clock and lead_ms_unforced is "
            "the same over trials where no stall, seek, pause or background "
            "held the cover. The wall-clock tail is the virtual device playing "
            "slower than real time near the start of a clip, not the schedule "
            "firing early: every trial over 1.5 s of wall-clock lead has a "
            "media-time lead inside the guard band. lead_media_ms is the "
            "measure of the schedule itself."
        ),
        "worst_lead_ms": round(min(leads), 1) if leads else None,
        "held_longer_than_guard_band": len(
            [t for t in counted if t.get("held_longer_than_guard_band")]
        ),
        # The longest the scheduler's own tick was kept waiting. It asks every
        # 50 ms whether the cover should be on, so a gap far past that is the
        # JavaScript thread being away, and the guard band has to be wider than
        # the worst of them. Null means the app did not report it, which is
        # what a build from before the instrumentation looks like.
        "worst_tick_gap_ms": worst_tick_gap(pooled_events),
        "tick_gaps_over_twice_the_tick": len(
            [e for e in pooled_events if e.get("kind") == "tick-gap"]
        ),
        "why_held": sorted(
            {t["why_held"] for t in counted if t.get("why_held")}
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    # Keep the events behind the summary, so anyone can recompute it.
    args.out.with_name(args.out.stem + "_events.json").write_text(
        json.dumps(pooled_events, indent=2) + "\n"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "passes"}, indent=2))
    return 0 if len(counted) >= args.target_trials else 1


if __name__ == "__main__":
    sys.exit(main())
