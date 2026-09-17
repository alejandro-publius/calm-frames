"""The WCAG general flash rule.

A general flash is "a pair of opposing changes in relative luminance of 10% or more of the
maximum relative luminance (1.0) where the relative luminance of the darker image is below
0.80", and more than three of them in any one-second period is what fails.

Each test states the arithmetic it relies on, so a reader can check the setup without trusting
the detector.
"""

from __future__ import annotations

import numpy as np
import pytest

import clipgen
from flashmap import WCAG, analyze_file

W, H = 64, 48


def luminance_of(code: int) -> float:
    from flashmap import color

    linear = color.srgb_to_linear(np.array([code / 255.0]))
    return float(np.dot([0.2126, 0.7152, 0.0722], [linear[0]] * 3))


def gray(code: int):
    return clipgen.solid(W, H, (code, code, code))


def test_the_test_setup_matches_the_spec_wording():
    """Guard the numbers the rest of this file leans on."""
    assert luminance_of(0) == pytest.approx(0.0, abs=1e-6)
    assert luminance_of(255) == pytest.approx(1.0, abs=1e-6)
    # The pair used for "big enough swing".
    assert luminance_of(140) - luminance_of(100) >= 0.10
    # The pair used for "too small a swing".
    assert luminance_of(128) - luminance_of(100) < 0.10
    # The pair used for "both images too bright".
    assert luminance_of(235) >= 0.80
    assert luminance_of(255) - luminance_of(235) >= 0.10


def test_ten_flashes_a_second_over_the_whole_frame_fails(hazard_clip):
    path = hazard_clip("tenhz.mkv", clipgen.alternating(40, gray(0), gray(255)), fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    assert [segment.reason for segment in result.segments] == ["general"]
    assert result.segments[0].area_fraction == pytest.approx(1.0)


def test_three_flashes_a_second_passes(calm_clip):
    """20 fps, a bright frame every 7th frame, so under three flashes a second."""
    frames = clipgen.every_nth(60, gray(0), gray(255), 7)
    path = calm_clip("three.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [s.as_dict() for s in result.segments]


def test_four_flashes_a_second_fails(hazard_clip):
    """20 fps, a bright frame every 5th frame, so four flashes a second, one over the limit."""
    frames = clipgen.every_nth(60, gray(0), gray(255), 5)
    path = hazard_clip("four.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    assert result.segments[0].max_flashes_in_window > WCAG.flash_limit_per_second


def test_a_swing_under_ten_percent_is_not_a_flash(calm_clip):
    path = calm_clip("small.mkv", clipgen.alternating(40, gray(100), gray(128)), fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes


def test_the_same_rhythm_with_a_big_enough_swing_is_a_flash(hazard_clip):
    path = hazard_clip("big.mkv", clipgen.alternating(40, gray(100), gray(140)), fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes


def test_flashing_between_two_bright_images_is_not_a_general_flash(calm_clip):
    """"where the relative luminance of the darker image is below 0.80". Here it is not."""
    path = calm_clip("bright.mkv", clipgen.alternating(40, gray(235), gray(255)), fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [s.as_dict() for s in result.segments]


def test_a_slow_ramp_is_not_flashing(calm_clip):
    """A transition is one thing. A flash needs two opposing ones."""
    up = [gray(int(round(255 * index / 29))) for index in range(30)]
    down = list(reversed(up))
    path = calm_clip("ramp.mkv", up + down, fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [s.as_dict() for s in result.segments]


def test_a_static_picture_is_not_flashing(calm_clip):
    path = calm_clip("static.mkv", [gray(128)] * 40, fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes


def test_the_segment_covers_the_flashing_and_starts_before_it(hazard_clip):
    """Calm, then a burst, then calm. The segment has to cover the burst."""
    calm = [gray(40)] * 20
    burst = clipgen.alternating(30, gray(0), gray(255))
    frames = calm + burst + calm
    path = hazard_clip("burst.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    burst_start_ms = 20 * 50.0
    burst_end_ms = (20 + 30) * 50.0
    covered = [(s.start_ms, s.end_ms) for s in result.segments]
    assert any(start <= burst_start_ms and end >= burst_end_ms - 100 for start, end in covered), (
        covered
    )
