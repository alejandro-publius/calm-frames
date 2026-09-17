"""The ITU-R BT.1702-3 profile, standard dynamic range only.

The rule is a pair of opposing luminance changes of 20 cd/m2 or more where the darker image is
below 160 cd/m2, more than three times in a second, over more than 25% of the displayed screen
area. See flashmap/docs/SPEC_SOURCES.md section 5.
"""

from __future__ import annotations

import numpy as np
import pytest

import clipgen
from flashmap import BROADCAST_SDR, get_profile
from flashmap.analyze import analyze_file
from flashmap.color import bt1886_nits

W, H = 64, 48


def nits_of(code: int, peak: float = 200.0) -> float:
    """Screen luminance for an 8-bit limited range luma code."""
    level = (code - 16.0) / 219.0
    return float(bt1886_nits(np.array([level]), peak).item())


def gray(code: int):
    return clipgen.solid(W, H, (code, code, code))


def test_the_profile_carries_the_numbers_the_recommendation_prints():
    assert BROADCAST_SDR.general.min_delta == 20.0
    assert BROADCAST_SDR.general.dark_image_below == 160.0
    assert BROADCAST_SDR.peak_nits == 200.0
    assert BROADCAST_SDR.flash_limit_per_second == 3
    assert BROADCAST_SDR.area_fraction_limit == 0.25
    assert BROADCAST_SDR.area_window_mode == "whole-picture"


def test_the_area_rule_is_the_whole_screen_not_a_ten_degree_field(hazard_clip):
    """BT.1702-3 says 25% of the displayed screen area. WCAG says 25% of any 10 degree field.
    A band that fills a fifth of the screen breaks WCAG but not the broadcast rule."""
    from flashmap import WCAG

    background = gray(128)
    band = clipgen.patch(background, (255, 255, 255), top=0.3, left=0.0, height=0.20, width=1.0)
    path = hazard_clip("band1702.mkv", clipgen.alternating(40, background, band), fps=20)

    assert not analyze_file(path, WCAG).passes
    assert analyze_file(path, BROADCAST_SDR).passes


def test_a_full_screen_strobe_fails_both_profiles(hazard_clip):
    from flashmap import WCAG

    path = hazard_clip("full1702.mkv", clipgen.alternating(40, gray(16), gray(235)), fps=20)
    assert not analyze_file(path, WCAG).passes
    assert not analyze_file(path, BROADCAST_SDR).passes


def test_a_swing_smaller_than_twenty_nits_is_not_a_flash(calm_clip):
    dark, bright = 40, 90
    assert nits_of(dark) < 160.0
    assert nits_of(bright) - nits_of(dark) < 20.0
    path = calm_clip("small1702.mkv", clipgen.alternating(40, gray(dark), gray(bright)), fps=20)
    assert analyze_file(path, BROADCAST_SDR).passes


def test_a_swing_larger_than_twenty_nits_is_a_flash(hazard_clip):
    dark, bright = 40, 160
    assert nits_of(dark) < 160.0
    assert nits_of(bright) - nits_of(dark) > 20.0
    path = hazard_clip("big1702.mkv", clipgen.alternating(40, gray(dark), gray(bright)), fps=20)
    assert not analyze_file(path, BROADCAST_SDR).passes


def test_the_peak_luminance_can_be_set_and_changes_the_verdict(hazard_clip, calm_clip):
    """The same signal on a dimmer assumed display swings through fewer cd/m2."""
    dark, bright = 40, 130
    frames = clipgen.alternating(40, gray(dark), gray(bright))

    bright_display = get_profile("broadcast", peak_nits=200.0)
    dim_display = get_profile("broadcast", peak_nits=60.0)
    assert nits_of(bright, 200.0) - nits_of(dark, 200.0) > 20.0
    assert nits_of(bright, 60.0) - nits_of(dark, 60.0) < 20.0

    path = hazard_clip("peak.mkv", frames, fps=20)
    assert not analyze_file(path, bright_display).passes
    assert analyze_file(path, dim_display).passes


def test_the_wcag_profile_refuses_a_peak_luminance():
    with pytest.raises(ValueError, match="does not use a peak luminance"):
        get_profile("wcag", peak_nits=200.0)


def test_the_profile_says_what_it_does_not_implement():
    described = BROADCAST_SDR.as_dict()
    joined = " ".join(described["rules_not_implemented"])
    assert "HDR" in joined
    assert "334 ms" in joined
    assert "patterns" in joined
