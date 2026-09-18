"""Two hours of playback with a clock that runs half a percent fast.

The cover schedule runs on a wall clock, not on the player's position reports, because the
player can go quiet for seconds at a time: results/vvd_timeupdate_stats.json records a gap of
over five seconds in a run where the clip kept playing. A wall clock keeps covering through
that gap. What it costs is drift, and drift is what this file measures.

The timeline is synthetic and the scheduler is real. eval/property_scheduler_runner.mjs plays
the whole two hours against app/src/calmframes, ticking every 50 ms as useCoverHarness does,
re-anchoring on every position report, and it is told where the playhead really is so an
uncovered flagged frame can be spotted.

Three arms, and the third is the argument for the second:

  measured_cadence   position reports at the median interval the virtual device produced
  worst_measured_gap reports at the longest gap that run recorded, over five seconds
  no_resync          one report at the start and never again

The cadences are read from results/vvd_timeupdate_stats.json rather than typed in here, so
they move when the measurement moves.

    python3 eval/property_drift_test.py       run it and write results/drift.json
    python3 -m pytest eval/property_drift_test.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import pytest

from property_runner import RunnerUnavailable, SchedulerRunner, scheduler  # noqa: F401

REPO = Path(__file__).resolve().parent.parent
TIMEUPDATE_STATS = REPO / "results" / "vvd_timeupdate_stats.json"
RESULT = REPO / "results" / "drift.json"

TWO_HOURS_MS = 2 * 60 * 60 * 1000
TICK_MS = 50
GUARD_BAND_MS = 500
# Half a percent. A player whose media clock runs this much faster than the app assumes.
DRIFT_FACTOR = 1.005

# A flagged span every five minutes, three seconds long. Twenty four of them across the two
# hours, which is more than any title in the pool and enough that an estimate drifting away
# from the player has somewhere to be caught out.
SEGMENTS = [
    {"startMs": start, "endMs": start + 3_000, "reason": "general"}
    for start in range(300_000, TWO_HOURS_MS, 300_000)
]


def measured_cadences() -> dict[str, float]:
    """The position report cadence the virtual device actually produced."""
    stats = json.loads(TIMEUPDATE_STATS.read_text())["timeupdate"]["interval_ms"]
    return {"median": float(stats["median"]), "max": float(stats["max"])}


def arm(runner, name: str, report_every_ms: float) -> dict:
    answer = runner.call(
        {
            "job": "scheduleRun",
            "segments": SEGMENTS,
            "options": {"guardBandMs": GUARD_BAND_MS, "minCoverMs": 400},
            "phases": [{"untilWallMs": TWO_HOURS_MS, "kind": "play", "rate": 1.0}],
            "endWallMs": TWO_HOURS_MS,
            "tickMs": TICK_MS,
            "reportEveryMs": report_every_ms,
            "driftFactor": DRIFT_FACTOR,
        }
    )
    assert answer["ok"], answer.get("error")
    corrections = answer["corrections"]
    # The first report is at wall zero, where there is nothing to correct yet.
    after_the_first = corrections[1:] or [0.0]
    return {
        "name": name,
        "report_every_ms": report_every_ms,
        "ticks": answer["ticks"],
        "ticks_inside_a_flagged_span": answer["ticksInsideFlagged"],
        "position_reports": answer["reports"],
        "uncovered_moments": len(answer["uncoveredAt"]),
        "first_uncovered": answer["uncoveredAt"][:3],
        "worst_estimate_error_ms": round(answer["worstEstimateErrorMs"], 3),
        "worst_estimate_error_inside_a_flagged_span_ms": round(
            answer["worstErrorInsideFlaggedMs"], 3
        ),
        "correction_ms": {
            "count": len(corrections),
            "min": round(min(after_the_first), 3),
            "median": round(statistics.median(after_the_first), 3),
            "mean": round(statistics.fmean(after_the_first), 3),
            "max": round(max(after_the_first), 3),
            "total": round(sum(after_the_first), 3),
        },
        "first_six_resyncs": answer["resyncSample"],
    }


def run_all(runner) -> dict:
    cadences = measured_cadences()
    arms = {
        "measured_cadence": arm(runner, "measured_cadence", cadences["median"]),
        "worst_measured_gap": arm(runner, "worst_measured_gap", cadences["max"]),
        # A report at wall zero and then never again, for the whole two hours.
        "no_resync": arm(runner, "no_resync", TWO_HOURS_MS * 10),
    }
    return {
        "statement": (
            "Two hours of synthetic playback against the app's real cover scheduler, with a "
            "player whose media clock runs 0.5 percent faster than the app assumes. The "
            "position report cadences are the ones results/vvd_timeupdate_stats.json "
            "measured on the virtual device. Nothing here was measured on hardware, and it "
            "is not a GATE 1 number."
        ),
        "tool": "eval/property_drift_test.py",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "timeline": {
            "length_ms": TWO_HOURS_MS,
            "tick_ms": TICK_MS,
            "guard_band_ms": GUARD_BAND_MS,
            "drift_factor": DRIFT_FACTOR,
            "flagged_spans": len(SEGMENTS),
            "flagged_span_ms": 3_000,
        },
        "cadences_from": "results/vvd_timeupdate_stats.json",
        "arms": arms,
        "reading": (
            "With re-sync the correction each report applies is small and the estimate never "
            "falls behind the player by as much as the guard band, so no flagged frame is "
            "ever showing. Without it the estimate ends the film about half a percent of two "
            "hours behind, which is why the schedule re-anchors on every report instead of "
            "trusting its own clock."
        ),
    }


@pytest.fixture(scope="module")
def drift(scheduler) -> dict:
    return run_all(scheduler)


def test_the_timeline_really_does_pass_through_the_flagged_spans(drift):
    """The negative control. A run that never reaches a flagged span proves nothing."""
    for name, result in drift["arms"].items():
        assert result["ticks_inside_a_flagged_span"] > 0, name
        assert result["ticks"] > 100_000, name


def test_half_a_percent_of_drift_stays_covered_at_the_measured_cadence(drift):
    result = drift["arms"]["measured_cadence"]
    assert result["uncovered_moments"] == 0, result["first_uncovered"]
    assert abs(result["worst_estimate_error_ms"]) < GUARD_BAND_MS


def test_it_stays_covered_even_at_the_longest_gap_the_device_produced(drift):
    """Over five seconds between position reports, which is what that run really did."""
    result = drift["arms"]["worst_measured_gap"]
    assert result["uncovered_moments"] == 0, result["first_uncovered"]
    assert abs(result["worst_estimate_error_ms"]) < GUARD_BAND_MS


def test_the_correction_each_resync_applies_is_the_drift_since_the_last_one(drift):
    """0.5 percent of the gap, which is what half a percent of drift means.

    This is the number the task asks to be logged: how far the re-sync moves the estimate
    every time the player says where it is.
    """
    for name in ("measured_cadence", "worst_measured_gap"):
        result = drift["arms"][name]
        expected = result["report_every_ms"] * (DRIFT_FACTOR - 1.0)
        assert result["correction_ms"]["median"] == pytest.approx(expected, rel=0.05), name
        # Always the same sign: the player is ahead, so every correction moves the estimate
        # forward. A correction that changed sign would mean the clock was overshooting.
        assert result["correction_ms"]["min"] > 0, name


def test_without_re_sync_the_same_drift_would_leave_the_picture_showing(drift):
    """The third arm, which is the argument for the other two.

    The same player, the same schedule, the same half a percent, and one position report at
    the start. Two hours later the estimate is about thirty six seconds behind, and the cover
    is being drawn in the wrong places.
    """
    result = drift["arms"]["no_resync"]
    assert result["position_reports"] == 1
    expected_lag = TWO_HOURS_MS * (DRIFT_FACTOR - 1.0)
    assert result["worst_estimate_error_ms"] == pytest.approx(-expected_lag, rel=0.01)
    assert result["uncovered_moments"] > 0


def main() -> int:
    try:
        runner = SchedulerRunner()
        runner.__enter__()
    except RunnerUnavailable as error:
        print(f"the drift run needs node and the app's tsc: {error}", file=sys.stderr)
        return 1
    try:
        report = run_all(runner)
    finally:
        runner.__exit__(None, None, None)

    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(report, indent=2) + "\n")
    for name, result in report["arms"].items():
        print(
            f"{name:20s} reports {result['position_reports']:6d}  "
            f"median correction {result['correction_ms']['median']:8.3f} ms  "
            f"worst error {result['worst_estimate_error_ms']:10.3f} ms  "
            f"uncovered {result['uncovered_moments']}"
        )
    print(f"written to {RESULT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
