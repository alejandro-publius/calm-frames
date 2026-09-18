"""Tests for the conformance ground truth: known answers worked out by hand from the spec text.

None of these run a detector. They pin what the true answer is, so that a change to truth.py
that would quietly move every precision and recall number in the repository has to go past
them first.

To see them fail on purpose: flip `>` to `>=` in the area comparison in truth.py, or drop the
darker-image part of the general condition, and watch. Verified Sep 17, 2026.
"""

from __future__ import annotations

import pytest

from conformance.design import make_clip
from conformance.geometry import Rect, frame_plan, picture_rect, region_rects
from conformance.spec import load_spec
from conformance.truth import clip_truth, flash_completions, max_field_coverage

SPEC = load_spec()


def test_the_spec_numbers_came_out_of_the_spec_file():
    assert SPEC.source_path.endswith("SPEC_SOURCES.md")
    assert SPEC.flash_limit_per_second == 3
    assert 0 < SPEC.general_min_delta < 1
    assert 0 < SPEC.area_fraction_limit < 1


def test_a_full_picture_region_fills_every_field():
    picture = Rect(0, 0, 854, 480)
    coverage = max_field_coverage(picture, [picture], SPEC)
    assert coverage == pytest.approx(1.0)


def test_a_compact_region_inside_one_field_counts_nine_times_its_share_of_the_picture():
    # The 10 degree field is about a third of the width by a third of the height, so a
    # rectangle that fits inside one fills about nine times the share of the picture it takes.
    picture = picture_rect(854, 480)
    rects = region_rects(picture, "center_rect", 0.05)
    drawn = sum(r.area for r in rects) / (picture.width * picture.height)
    coverage = max_field_coverage(picture, rects, SPEC)
    ratio = 1.0 / (SPEC.field_width_fraction * SPEC.field_height_fraction)
    assert coverage == pytest.approx(drawn * ratio, rel=0.02)


def test_scattered_blocks_of_the_same_area_fill_far_less_of_any_one_field():
    picture = picture_rect(854, 480)
    compact = max_field_coverage(picture, region_rects(picture, "center_rect", 0.2), SPEC)
    scattered = max_field_coverage(picture, region_rects(picture, "scatter", 0.2), SPEC)
    assert compact > scattered * 3


def test_a_square_wave_gives_one_flash_per_cycle():
    times, states = frame_plan(
        duration_ms=3000, fps=60, timing="cfr", flash_start_ms=1000, flash_hz=10
    )
    completions = flash_completions(times, states)
    # Two seconds at ten flashes a second, less the one that has not finished at the end.
    assert 19 <= len(completions) <= 20


def test_a_square_wave_sampled_at_its_own_rate_is_not_seen_to_flash_at_all():
    times, states = frame_plan(
        duration_ms=3000, fps=30, timing="cfr", flash_start_ms=1000, flash_hz=30
    )
    assert flash_completions(times, states) == []


def _truth(**kwargs):
    return clip_truth(make_clip(SPEC, axis="test", **kwargs), SPEC)


def test_a_clear_ten_hertz_full_field_flash_is_positive_in_both_test_windows():
    truth = _truth(flash_hz=10, area_fraction=0.25, step_multiple=2.0)
    assert truth.positive_windows == [1, 2]
    assert truth.general_qualifies and not truth.red_qualifies


def test_the_calm_lead_in_window_is_never_a_positive():
    truth = _truth(flash_hz=20, area_fraction=0.6, step_multiple=3.0)
    assert 0 not in truth.positive_windows


def test_three_flashes_a_second_is_below_the_limit_and_four_is_over_it():
    assert _truth(flash_hz=3, fps=30).positive_windows == []
    assert _truth(flash_hz=4, fps=30).positive_windows == [1, 2]


def test_a_luminance_step_under_the_limit_is_not_a_flash_however_fast_it_goes():
    truth = _truth(flash_hz=20, step_multiple=0.8)
    assert not truth.general_qualifies
    assert truth.positive_windows == []


def test_a_bright_pair_is_not_a_general_flash_however_big_the_step():
    # The darker image has to be below the darker-image limit. Above it, nothing counts.
    truth = _truth(flash_hz=10, step_multiple=1.5, dark_multiple=1.05)
    assert truth.darker_luminance > SPEC.general_dark_image_below
    assert not truth.general_qualifies
    assert truth.positive_windows == []


def test_a_small_area_is_not_a_failure_however_hard_it_flashes():
    truth = _truth(flash_hz=20, area_fraction=0.01, step_multiple=3.0)
    assert truth.general_qualifies
    assert not truth.area_qualifies
    assert truth.positive_windows == []


def test_the_area_rule_turns_over_where_the_spec_puts_it_and_not_lower():
    """A coverage just under the limit passes and just over it fails.

    Without this, an area rule set to half the limit would still pass every other test here,
    because the other area cases are nowhere near the line.
    """
    from conformance.design import area_crossing

    crossing = area_crossing(SPEC, "center_rect")
    under = _truth(flash_hz=10, area_fraction=round(crossing * 0.85, 4))
    over = _truth(flash_hz=10, area_fraction=round(crossing * 1.15, 4))
    assert 0.5 * SPEC.area_fraction_limit < under.field_coverage < SPEC.area_fraction_limit
    assert over.field_coverage > SPEC.area_fraction_limit
    assert not under.area_qualifies and under.positive_windows == []
    assert over.area_qualifies and over.positive_windows == [1, 2]


def test_red_to_gray_at_matched_luminance_fires_the_red_rule_and_not_the_general_one():
    truth = _truth(red_mode="red_gray_matched", flash_hz=10)
    assert truth.red_qualifies
    assert not truth.general_qualifies
    assert truth.positive_windows == [1, 2]


def test_two_reds_on_one_chromaticity_are_not_a_red_flash():
    truth = _truth(red_mode="red_same_chroma", flash_hz=10)
    assert truth.ucs_distance == pytest.approx(0.0, abs=1e-9)
    assert not truth.red_qualifies
    assert truth.positive_windows == []


def test_a_non_red_colour_at_the_same_luminance_fires_nothing():
    truth = _truth(red_mode="nonred_control", flash_hz=10)
    assert not truth.red_qualifies and not truth.general_qualifies
    assert truth.positive_windows == []


def test_the_distance_rule_binds_before_the_ratio_rule_against_a_neutral_background():
    # SPEC_SOURCES says these two red numbers overlap heavily. This holds it to that: a colour
    # whose red ratio is still over the limit can fail the red test on distance alone.
    truth = _truth(red_mode="near_red_distance_0.9", flash_hz=10)
    assert truth.red_ratio_max >= SPEC.red_saturated_ratio
    assert truth.ucs_distance < SPEC.red_min_ucs_distance
    assert not truth.red_qualifies


def test_exactly_a_quarter_of_the_field_passes_because_the_spec_says_no_more_than():
    """A band one twelfth of the picture tall fills exactly a quarter of a 10 degree field.

    The spec's wording is "no more than", so exactly at the limit the content passes. This is
    the one place that can be checked without floating point slop: 40 pixels of 160 is a
    quarter to the last bit.
    """
    truth = _truth(shape="band", area_fraction=1.0 / 12.0, flash_hz=10, step_multiple=2.0)
    assert truth.field_coverage == SPEC.area_fraction_limit
    assert not truth.area_qualifies
    assert truth.positive_windows == []


def test_letterbox_bars_are_not_part_of_the_picture():
    plain = _truth(area_fraction=0.05, letterbox_fraction=0.0)
    barred = _truth(area_fraction=0.05, letterbox_fraction=0.25)
    # The same share of a shorter picture covers about the same share of a 10 degree field,
    # because the field is a fraction of the picture too.
    assert barred.field_coverage == pytest.approx(plain.field_coverage, rel=0.1)
