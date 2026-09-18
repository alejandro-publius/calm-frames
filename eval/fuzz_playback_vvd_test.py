"""The analysis behind the playback fuzzing run, checked without a device.

eval/fuzz_playback_vvd.py needs a Vega Virtual Device, so CI cannot run it. What CI can run,
and must, is the arithmetic that turns the events into the claim. A run that counted wrongly
would be worse than no run: docs/GATES.md records a perfect score that came from comparing a
scheduler against its own clock.

Each test here feeds the analysis events it could plausibly be given and checks the answer,
including the two ways a number could be flattered: counting a marker the player never
reached, and letting a previous app instance's late batch into this pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fuzz_playback_vvd as chaos  # noqa: E402

MARKERS = [{"index": 1, "start_ms": 2_000, "end_ms": 2_500}]


def crossings(events):
    cleaned, _ = chaos.clean_pass(events)
    return chaos.marker_crossings(cleaned, MARKERS)


def test_a_marker_the_player_walked_through_with_the_cover_on_is_counted_and_covered():
    found = crossings(
        [
            {"kind": "harness-start", "wallClockMs": 1_000},
            {"kind": "cover-on", "wallClockMs": 1_400, "mediaTimeMs": 1_500},
            {"kind": "timeupdate", "wallClockMs": 1_800, "mediaTimeMs": 1_800},
            {"kind": "timeupdate", "wallClockMs": 2_700, "mediaTimeMs": 2_700},
            {"kind": "cover-off", "wallClockMs": 3_100, "mediaTimeMs": 3_100},
        ]
    )
    assert len(found) == 1
    assert found[0]["covered"] is True
    assert found[0]["showing_for_ms"] == 0
    assert found[0]["media_from_ms"] == 2_000
    assert found[0]["media_to_ms"] == 2_500


def test_a_cover_that_came_off_inside_the_marker_is_caught():
    found = crossings(
        [
            {"kind": "harness-start", "wallClockMs": 1_000},
            {"kind": "cover-on", "wallClockMs": 1_400, "mediaTimeMs": 1_500},
            {"kind": "cover-off", "wallClockMs": 2_100, "mediaTimeMs": 2_100},
            {"kind": "timeupdate", "wallClockMs": 1_800, "mediaTimeMs": 1_800},
            {"kind": "timeupdate", "wallClockMs": 2_700, "mediaTimeMs": 2_700},
        ]
    )
    assert len(found) == 1
    assert found[0]["covered"] is False
    assert found[0]["showing_for_ms"] > 0


def test_a_marker_the_player_never_reached_is_not_counted():
    """The failure docs/GATES.md is about. No report near the marker means no measurement."""
    found = crossings(
        [
            {"kind": "harness-start", "wallClockMs": 1_000},
            {"kind": "cover-on", "wallClockMs": 1_400, "mediaTimeMs": 1_500},
            {"kind": "timeupdate", "wallClockMs": 1_500, "mediaTimeMs": 170},
            {"kind": "timeupdate", "wallClockMs": 1_800, "mediaTimeMs": 259},
        ]
    )
    assert found == []


def test_a_batch_from_the_previous_app_instance_is_thrown_out():
    events = [
        {"kind": "timeupdate", "wallClockMs": 500, "mediaTimeMs": 9_000},
        {"kind": "harness-start", "wallClockMs": 20_000},
        {"kind": "timeupdate", "wallClockMs": 20_800, "mediaTimeMs": 1_800},
        # The previous instance, twenty seconds late and twenty seconds behind.
        {"kind": "timeupdate", "wallClockMs": 900, "mediaTimeMs": 11_000},
        {"kind": "timeupdate", "wallClockMs": 21_700, "mediaTimeMs": 2_700},
    ]
    cleaned, split = chaos.clean_pass(events)
    assert split["dropped_before_the_last_harness_start"] == 1
    assert split["dropped_for_going_backwards"] == 1
    assert len(cleaned) == 3
    found = chaos.marker_crossings(cleaned, MARKERS)
    assert len(found) == 1 and found[0]["covered"] is False


def test_a_seek_is_not_a_journey_through_the_clip():
    """Two reports with the position going backwards say a seek happened, not that the
    playhead visited everything in between."""
    assert (
        crossings(
            [
                {"kind": "harness-start", "wallClockMs": 1_000},
                {"kind": "timeupdate", "wallClockMs": 1_800, "mediaTimeMs": 3_000},
                {"kind": "timeupdate", "wallClockMs": 2_700, "mediaTimeMs": 500},
            ]
        )
        == []
    )


def test_the_picture_is_showing_before_the_first_cover_on():
    """The harness starts with the picture visible, so a marker reached before the first
    cover-on is an uncovered marker and has to be counted as one."""
    found = crossings(
        [
            {"kind": "harness-start", "wallClockMs": 1_000},
            {"kind": "timeupdate", "wallClockMs": 1_800, "mediaTimeMs": 1_800},
            {"kind": "timeupdate", "wallClockMs": 2_700, "mediaTimeMs": 2_700},
            {"kind": "cover-on", "wallClockMs": 5_000, "mediaTimeMs": 5_000},
        ]
    )
    assert len(found) == 1
    assert found[0]["covered"] is False


def test_a_cover_that_never_came_off_covers_to_the_end_of_the_pass():
    found = crossings(
        [
            {"kind": "harness-start", "wallClockMs": 1_000},
            {"kind": "cover-on", "wallClockMs": 1_100, "mediaTimeMs": 1_100},
            {"kind": "timeupdate", "wallClockMs": 1_800, "mediaTimeMs": 1_800},
            {"kind": "timeupdate", "wallClockMs": 2_700, "mediaTimeMs": 2_700},
            {"kind": "harness-stop", "wallClockMs": 9_000},
        ]
    )
    assert len(found) == 1 and found[0]["covered"] is True


def test_the_chaos_plan_is_reproducible_and_does_something():
    first = chaos.chaos_plan(seed=7, seconds=18.0)
    again = chaos.chaos_plan(seed=7, seconds=18.0)
    assert first == again, "the same seed gave a different plan"
    assert len(first) >= 3
    assert {action["kind"] for action in first} <= {
        "throttle",
        "stall",
        "fast-forward",
        "rewind",
        "pause",
        "background",
    }
    assert all(0 < action["at_s"] < 18.0 for action in first)
    different = chaos.chaos_plan(seed=8, seconds=18.0)
    assert different != first, "every seed gave the same plan, so the seed does nothing"
