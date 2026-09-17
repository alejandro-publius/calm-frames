"""The WCAG red flash rule.

"A red flash is defined as any pair of opposing transitions involving a saturated red", and the
working definition is a transition to or from a state whose R/(R + G + B) is at or above 0.8,
where the two states are more than 0.2 apart in the CIE 1976 UCS chromaticity diagram.

The clips here alternate red with a gray of almost the same relative luminance, so the general
flash rule stays quiet and only the red rule can speak.
"""

from __future__ import annotations

import numpy as np
import pytest

import clipgen
from flashmap import WCAG, analyze_file, color

W, H = 64, 48
RED = (255, 0, 0)
MATCHING_GRAY = (128, 128, 128)
DULL_RED = (200, 120, 120)
DARK_RED = (128, 0, 0)


def _state(rgb):
    linear = color.srgb_to_linear(np.array(rgb, dtype=np.float64)[None, None, :] / 255.0)
    xyz = color.linear_rgb_to_xyz(linear)
    u, v = color.ucs_1976(xyz)
    return (
        float(color.relative_luminance(linear)[0, 0]),
        float(color.red_ratio(linear)[0, 0]),
        float(u[0, 0]),
        float(v[0, 0]),
    )


def test_the_test_setup_matches_the_spec_wording():
    red_lum, red_ratio, red_u, red_v = _state(RED)
    gray_lum, gray_ratio, gray_u, gray_v = _state(MATCHING_GRAY)
    # Pure red is a saturated red state, the gray is not.
    assert red_ratio >= WCAG.red.saturated_red_ratio
    assert gray_ratio < WCAG.red.saturated_red_ratio
    # They are far enough apart in the 1976 UCS diagram.
    assert np.hypot(red_u - gray_u, red_v - gray_v) > WCAG.red.min_ucs_distance
    # And their relative luminance is close enough that no general flash can be claimed.
    assert abs(red_lum - gray_lum) < WCAG.general.min_delta

    dull_lum, dull_ratio, _, _ = _state(DULL_RED)
    assert dull_ratio < WCAG.red.saturated_red_ratio
    assert abs(dull_lum - gray_lum) < WCAG.general.min_delta


def test_red_to_gray_at_ten_hertz_is_a_red_flash(hazard_clip):
    frames = clipgen.alternating(40, clipgen.solid(W, H, RED), clipgen.solid(W, H, MATCHING_GRAY))
    path = hazard_clip("red.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    assert {segment.reason for segment in result.segments} == {"red"}
    assert result.segments[0].area_fraction == pytest.approx(1.0)


def test_a_colour_that_is_not_saturated_red_does_not_trigger_the_red_rule(calm_clip):
    frames = clipgen.alternating(
        40, clipgen.solid(W, H, DULL_RED), clipgen.solid(W, H, MATCHING_GRAY)
    )
    path = calm_clip("dull.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]


def test_two_reds_never_leave_the_saturated_state_so_it_is_not_a_red_flash(hazard_clip):
    """Bright red to dark red is a general flash, because the luminance swing is big. It is
    not a red flash, because no transition goes into or out of the saturated red state."""
    frames = clipgen.alternating(40, clipgen.solid(W, H, RED), clipgen.solid(W, H, DARK_RED))
    path = hazard_clip("twored.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    reasons = {segment.reason for segment in result.segments}
    assert "red" not in reasons, [segment.as_dict() for segment in result.segments]
    assert reasons == {"general"}


def test_two_colours_far_apart_in_chromaticity_are_not_a_red_flash(hazard_clip):
    """Blue to yellow moves a long way in the 1976 UCS diagram, but neither state is a
    saturated red, so no transition is to or from one."""
    blue, yellow = (0, 0, 255), (255, 255, 0)
    assert _state(blue)[1] < WCAG.red.saturated_red_ratio
    assert _state(yellow)[1] < WCAG.red.saturated_red_ratio
    blue_u, blue_v = _state(blue)[2:]
    yellow_u, yellow_v = _state(yellow)[2:]
    assert np.hypot(blue_u - yellow_u, blue_v - yellow_v) > WCAG.red.min_ucs_distance

    frames = clipgen.alternating(40, clipgen.solid(W, H, blue), clipgen.solid(W, H, yellow))
    path = hazard_clip("bluesun.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    reasons = {segment.reason for segment in result.segments}
    assert "red" not in reasons, [segment.as_dict() for segment in result.segments]


def test_three_red_flashes_a_second_passes(calm_clip):
    frames = clipgen.every_nth(
        60, clipgen.solid(W, H, MATCHING_GRAY), clipgen.solid(W, H, RED), 7
    )
    path = calm_clip("threered.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]


def test_a_small_red_patch_passes_the_area_rule(calm_clip):
    """Red flashing over a tenth of the height of the picture cannot fill a quarter of a
    10 degree field, so it is below the thresholds."""
    background = clipgen.solid(W, H, MATCHING_GRAY)
    flashing = clipgen.patch(background, RED, top=0.4, left=0.0, height=0.06, width=1.0)
    path = calm_clip("redstrip.mkv", clipgen.alternating(40, background, flashing), fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]
