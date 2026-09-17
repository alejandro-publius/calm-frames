"""The hide plan: guard band, merging, red handling, calm moments.

This is the Python twin of app/src/calmframes/coverSchedule.ts, so these tests
mirror the ones on that file. If one side changes, the other has to change
with it or the pipeline and the player stop agreeing about what is covered.
"""

from __future__ import annotations

import json

import pytest

from pipeline.flashmap_adapter import FlashMapDoc, MapSegment
from pipeline.hideplan import (
    DEFAULT_GUARD_BAND_MS,
    DIM,
    OPAQUE,
    CoverInterval,
    HidePlan,
    build_cover_intervals,
    build_hide_plan,
    calm_ranges,
    cover_mode,
    is_calm,
    is_covered,
    nearest_calm_time_ms,
    total_covered_ms,
    union_intervals,
)


def seg(start, end, reason="general"):
    return MapSegment(start_ms=start, end_ms=end, reason=reason)


def pairs(intervals):
    return [(i.start_ms, i.end_ms) for i in intervals]


class TestGuardBand:
    def test_widens_both_sides(self):
        intervals = build_cover_intervals([seg(5000, 6000)], guard_band_ms=500)
        assert pairs(intervals) == [(4500, 6500)]

    def test_zero_guard_band_leaves_the_segment_alone(self):
        intervals = build_cover_intervals(
            [seg(5000, 6000)], guard_band_ms=0, min_cover_ms=0
        )
        assert pairs(intervals) == [(5000, 6000)]

    def test_clamped_at_the_start_of_the_title(self):
        intervals = build_cover_intervals([seg(100, 900)], guard_band_ms=500)
        assert pairs(intervals) == [(0, 1400)]

    def test_clamped_at_the_end_of_the_title(self):
        intervals = build_cover_intervals(
            [seg(9000, 9800)], guard_band_ms=500, duration_ms=10_000
        )
        assert pairs(intervals) == [(8500, 10_000)]

    def test_default_is_five_hundred_milliseconds(self):
        assert DEFAULT_GUARD_BAND_MS == 500

    def test_a_negative_guard_band_is_refused(self):
        with pytest.raises(ValueError):
            build_cover_intervals([seg(1000, 2000)], guard_band_ms=-1)

    def test_a_bigger_guard_band_only_ever_adds_cover(self):
        narrow = build_cover_intervals([seg(5000, 6000)], guard_band_ms=200)
        wide = build_cover_intervals([seg(5000, 6000)], guard_band_ms=2000)
        assert wide[0].start_ms <= narrow[0].start_ms
        assert wide[0].end_ms >= narrow[0].end_ms


class TestMinimumCover:
    def test_short_segment_is_grown_at_the_end(self):
        intervals = build_cover_intervals(
            [seg(5000, 5010)], guard_band_ms=0, min_cover_ms=400
        )
        # The start never moves later than the guard band promised.
        assert pairs(intervals) == [(5000, 5400)]

    def test_long_segment_is_left_alone(self):
        intervals = build_cover_intervals(
            [seg(5000, 9000)], guard_band_ms=0, min_cover_ms=400
        )
        assert pairs(intervals) == [(5000, 9000)]


class TestMerging:
    def test_overlapping_intervals_merge(self):
        intervals = build_cover_intervals(
            [seg(1000, 2000), seg(1900, 3000)], guard_band_ms=0, min_cover_ms=0
        )
        assert pairs(intervals) == [(1000, 3000)]

    def test_intervals_that_only_touch_merge(self):
        intervals = build_cover_intervals(
            [seg(1000, 2000), seg(2000, 3000)], guard_band_ms=0, min_cover_ms=0
        )
        assert pairs(intervals) == [(1000, 3000)]

    def test_guard_bands_that_meet_merge(self):
        # 400 ms apart, so two 500 ms guard bands overlap.
        intervals = build_cover_intervals(
            [seg(1000, 2000), seg(2400, 3000)], guard_band_ms=500
        )
        assert pairs(intervals) == [(500, 3500)]

    def test_far_apart_intervals_stay_separate(self):
        intervals = build_cover_intervals(
            [seg(1000, 2000), seg(9000, 9500)], guard_band_ms=500
        )
        assert pairs(intervals) == [(500, 2500), (8500, 10_000)]

    def test_input_order_does_not_matter(self):
        forward = build_cover_intervals([seg(1000, 2000), seg(5000, 6000)])
        backward = build_cover_intervals([seg(5000, 6000), seg(1000, 2000)])
        assert pairs(forward) == pairs(backward)

    def test_a_merged_interval_keeps_every_source_segment(self):
        intervals = build_cover_intervals(
            [seg(1000, 2000), seg(2100, 3000)], guard_band_ms=500
        )
        assert len(intervals) == 1
        assert len(intervals[0].sources) == 2

    def test_empty_and_backwards_segments_are_dropped(self):
        intervals = build_cover_intervals(
            [seg(1000, 1000), seg(3000, 2000), seg(5000, 6000)]
        )
        assert pairs(intervals) == [(4500, 6500)]


class TestRedIsNeverDimmed:
    def test_a_red_interval_is_opaque(self):
        intervals = build_cover_intervals([seg(1000, 2000, "red")])
        assert cover_mode(intervals[0], allow_dim=True) == OPAQUE

    def test_a_general_interval_may_be_dimmed(self):
        intervals = build_cover_intervals([seg(1000, 2000, "general")])
        assert cover_mode(intervals[0], allow_dim=True) == DIM

    def test_a_general_interval_is_opaque_when_the_house_forbids_dim(self):
        intervals = build_cover_intervals([seg(1000, 2000, "general")])
        assert cover_mode(intervals[0], allow_dim=False) == OPAQUE

    def test_red_makes_a_whole_merged_interval_red(self):
        intervals = build_cover_intervals(
            [seg(1000, 2000, "general"), seg(2100, 3000, "red")], guard_band_ms=500
        )
        assert len(intervals) == 1
        assert intervals[0].reason == "red"
        assert cover_mode(intervals[0], allow_dim=True) == OPAQUE

    def test_red_wins_whichever_order_the_segments_arrive_in(self):
        intervals = build_cover_intervals(
            [seg(2100, 3000, "red"), seg(1000, 2000, "general")], guard_band_ms=500
        )
        assert intervals[0].reason == "red"

    def test_a_plan_never_lists_a_red_interval_as_dim(self):
        plan = HidePlan(
            profile="wcag",
            source_sha256="a" * 64,
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=20_000,
            allow_dim=True,
            intervals=build_cover_intervals(
                [seg(1000, 2000, "red"), seg(9000, 9500, "general")]
            ),
        )
        assert all(i.reason != "red" for i in plan.dim_intervals())
        assert [i.reason for i in plan.opaque_intervals()] == ["red"]


class TestCalmMoments:
    intervals = build_cover_intervals([seg(5000, 6000)], guard_band_ms=500)

    def test_a_time_inside_an_interval_is_not_calm(self):
        assert not is_calm(self.intervals, 5500, margin_ms=1000)

    def test_a_time_inside_the_margin_is_not_calm(self):
        assert not is_calm(self.intervals, 4000, margin_ms=1000)
        assert not is_calm(self.intervals, 7000, margin_ms=1000)

    def test_a_time_outside_the_margin_is_calm(self):
        assert is_calm(self.intervals, 2000, margin_ms=1000)
        assert is_calm(self.intervals, 9000, margin_ms=1000)

    def test_calm_ranges_skip_the_covered_span_and_its_margin(self):
        ranges = calm_ranges(self.intervals, 20_000, margin_ms=1000)
        assert ranges == [(0.0, 3500.0), (7500.0, 20_000.0)]

    def test_nearest_calm_time_moves_out_of_a_covered_span(self):
        found = nearest_calm_time_ms(self.intervals, 5500, 20_000, margin_ms=1000)
        assert found is not None
        assert is_calm(self.intervals, found, margin_ms=1000)

    def test_a_title_that_is_flagged_end_to_end_has_no_calm_time(self):
        everywhere = build_cover_intervals([seg(0, 20_000)], guard_band_ms=0)
        assert nearest_calm_time_ms(everywhere, 5000, 20_000, margin_ms=1000) is None

    def test_is_covered_matches_interval_bounds(self):
        assert is_covered(self.intervals, 4500)
        assert not is_covered(self.intervals, 4499)
        assert not is_covered(self.intervals, 6500)


class TestUnionAcrossPresets:
    def test_the_union_covers_every_preset(self):
        wcag = HidePlan(
            profile="wcag",
            source_sha256="a" * 64,
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=30_000,
            allow_dim=True,
            intervals=build_cover_intervals([seg(5000, 6000)]),
        )
        cautious = HidePlan(
            profile="extra-cautious",
            source_sha256="a" * 64,
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=30_000,
            allow_dim=True,
            intervals=build_cover_intervals([seg(5000, 6000), seg(20_000, 21_000)]),
        )
        union = union_intervals([wcag, cautious])
        assert pairs(union) == [(4500, 6500), (19_500, 21_500)]

    def test_a_still_calm_in_the_union_is_calm_in_every_preset(self):
        wcag = build_cover_intervals([seg(5000, 6000)])
        cautious = build_cover_intervals([seg(5000, 6000), seg(20_000, 21_000)])
        plans = [
            HidePlan("wcag", "a" * 64, 500, 400, 30_000, True, wcag),
            HidePlan("extra-cautious", "a" * 64, 500, 400, 30_000, True, cautious),
        ]
        union = union_intervals(plans)
        for time_ms in range(0, 30_000, 250):
            if is_calm(union, time_ms, margin_ms=1000):
                assert is_calm(wcag, time_ms, margin_ms=1000)
                assert is_calm(cautious, time_ms, margin_ms=1000)


class TestPlanRoundTrip:
    def test_a_plan_survives_json(self):
        doc = FlashMapDoc(
            version=1,
            source_sha256="b" * 64,
            profile="wcag",
            segments=[seg(1000, 2000, "red"), seg(8000, 8500)],
        )
        plan = build_hide_plan(doc, source_sha256="b" * 64, duration_ms=20_000)
        restored = HidePlan.from_dict(json.loads(json.dumps(plan.to_dict())))
        assert [(i.start_ms, i.end_ms, i.reason) for i in restored.intervals] == [
            (i.start_ms, i.end_ms, i.reason) for i in plan.intervals
        ]
        assert restored.guard_band_ms == plan.guard_band_ms

    def test_total_covered_ms_adds_the_intervals_up(self):
        intervals = [
            CoverInterval(0, 1000, "general"),
            CoverInterval(5000, 5500, "red"),
        ]
        assert total_covered_ms(intervals) == 1500
