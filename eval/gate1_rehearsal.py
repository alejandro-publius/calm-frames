"""Rehearse the GATE 1 analysis against a run on the virtual device.

GATE 1 asks one question: was the cover fully on at least 150 ms before the
marker appeared, in at least 48 of 50 trials. The real answer comes from a
240 fps phone recording of a real stick, because only a camera can say what a
screen actually showed.

This is the rehearsal. It runs the same analysis against the events the app
posted during a run, so the matching, the lead time statistics and the
interval are all exercised and reviewed before the stick arrives.

    python3 eval/gate1_rehearsal.py \
        --events results/vvd_timeupdate_stats_events.json \
        --schedule eval/harness_runs/marker_schedule.json

WHAT THIS IS NOT. It measures what the app believed, not what the screen
showed. A cover that the app scheduled correctly but that the compositor drew
late would pass here and fail on camera. Two separate things stop us
recording the virtual device's screen on this machine:

  - macOS screen recording exposes no capture device to ffmpeg without the
    Screen Recording permission, which a person has to grant;
  - the virtual device's window is not captured anyway. A full screen grab
    while it was frontmost returned the desktop behind it, and QEMU's own
    screendump returns black, because the app draws through a GPU layer that
    neither capture path sees.

Neither of those affects GATE 1 itself, which films a TV with a phone.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The gate: the cover must be fully on this long before the marker.
REQUIRED_LEAD_MS = 150


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> dict:
    """Wilson score interval, which behaves at the edges where this lives.

    A run of 20 for 20 has no spread under the normal approximation, which
    would claim certainty we do not have.
    """
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--events",
        type=Path,
        default=REPO / "results/vvd_timeupdate_stats_events.json",
    )
    parser.add_argument(
        "--schedule", type=Path, default=REPO / "eval/harness_runs/marker_schedule.json"
    )
    parser.add_argument("--guard-band-ms", type=int, default=500)
    parser.add_argument(
        "--out", type=Path, default=REPO / "results/gate1_rehearsal_vvd.json"
    )
    args = parser.parse_args()

    events = json.loads(args.events.read_text())
    schedule = json.loads(args.schedule.read_text())
    markers = schedule["markers"]

    covers_on = [
        e
        for e in events
        if e["kind"] == "cover-on"
        and isinstance(e.get("reason"), str)
        and e["reason"].startswith("interval ")
    ]

    # Each cover-on names the interval it belongs to, so a cover can be matched
    # to its marker without guessing from timestamps.
    trials = []
    for marker in markers:
        interval_start = marker["start_ms"] - args.guard_band_ms
        interval_end = marker["end_ms"] + args.guard_band_ms
        label = f"interval {interval_start}-{interval_end}"
        matching = [e for e in covers_on if e["reason"] == label]
        if not matching:
            trials.append(
                {
                    "marker": marker["index"],
                    "marker_start_ms": marker["start_ms"],
                    "covered": False,
                    "lead_ms": None,
                    "note": "no cover-on for this interval in the run",
                }
            )
            continue
        first = min(matching, key=lambda e: e["wallClockMs"])
        lead = marker["start_ms"] - first["mediaTimeMs"]
        trials.append(
            {
                "marker": marker["index"],
                "marker_start_ms": marker["start_ms"],
                "covered": True,
                "cover_on_media_ms": round(first["mediaTimeMs"], 1),
                "lead_ms": round(lead, 1),
                "in_time": lead >= REQUIRED_LEAD_MS,
            }
        )

    reached = [t for t in trials if t["covered"]]
    in_time = [t for t in reached if t.get("in_time")]
    leads = [t["lead_ms"] for t in reached if t["lead_ms"] is not None]

    result = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "what_this_is": (
            "A rehearsal of the GATE 1 analysis against the events the app "
            "posted during a run on the Vega Virtual Device. It measures what "
            "the app believed about media time, not what the screen showed."
        ),
        "what_this_is_not": (
            "GATE 1. That is 50 trials filmed at 240 fps on a real Fire TV "
            "stick, which is the only way to see what the screen did. The "
            "virtual device's screen cannot be recorded on this machine: "
            "macOS exposes no capture device without the Screen Recording "
            "permission, and the window is not captured anyway because the "
            "app draws on a GPU layer that both screen grabs and QEMU's "
            "screendump miss."
        ),
        "source_events": str(args.events.relative_to(REPO)),
        "clip_sha256": schedule["clip"]["sha256"],
        "guard_band_ms": args.guard_band_ms,
        "required_lead_ms": REQUIRED_LEAD_MS,
        "markers_in_schedule": len(markers),
        "markers_reached_during_run": len(reached),
        "markers_covered_in_time": len(in_time),
        "covered_in_time_fraction": (
            round(len(in_time) / len(reached), 4) if reached else None
        ),
        "wilson_95_interval": wilson_interval(len(in_time), len(reached)),
        "lead_ms": summarize([float(v) for v in leads]),
        "worst_lead_ms": round(min(leads), 1) if leads else None,
        "trials": trials,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "trials"},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
