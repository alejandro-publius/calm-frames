"""Frames bigger than the working size, and the slow end of the suite.

Area fractions are ratios, so scaling a frame down before analysis does not change them. What
scaling does change is how long the run takes, which is why it exists.
"""

from __future__ import annotations

import pytest

import clipgen
from flashmap import WCAG, analyze_file
from flashmap.decode import _analysis_size, probe

GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def test_the_working_size_keeps_the_aspect_ratio_and_stays_even():
    assert _analysis_size(640, 360, 192) == (192, 108)
    assert _analysis_size(1920, 1080, 192) == (192, 108)
    assert _analysis_size(64, 48, 192) == (64, 48), "small frames are left alone"


def test_a_large_frame_is_scaled_down_for_analysis(calm_clip):
    path = calm_clip("big.mkv", [clipgen.solid(640, 360, GRAY)] * 4, fps=20)
    info = probe(path)
    assert (info.coded_width, info.coded_height) == (640, 360)
    assert (info.analysis_width, info.analysis_height) == (192, 108)


def test_a_large_strobe_is_still_caught_after_scaling(hazard_clip):
    frames = clipgen.alternating(
        30, clipgen.solid(640, 360, BLACK), clipgen.solid(640, 360, WHITE)
    )
    path = hazard_clip("bigstrobe.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    assert result.segments[0].area_fraction == pytest.approx(1.0, abs=0.01)


def test_the_area_fraction_barely_moves_when_the_working_size_changes(hazard_clip):
    """Same clip, two working sizes, the same answer to within a pixel of rounding."""
    background = clipgen.solid(640, 360, GRAY)
    band = clipgen.patch(background, WHITE, top=0.3, left=0.0, height=0.10, width=1.0)
    path = hazard_clip("scaleband.mkv", clipgen.alternating(30, background, band), fps=20)
    coarse = analyze_file(path, WCAG, analysis_width=96)
    fine = analyze_file(path, WCAG, analysis_width=320)
    assert coarse.passes == fine.passes
    assert coarse.segments[0].area_fraction == pytest.approx(
        fine.segments[0].area_fraction, abs=0.08
    )


@pytest.mark.slow
def test_a_longer_clip_at_a_realistic_size(hazard_clip):
    """Three hundred frames of 480 by 270, a calm stretch with a strobe in the middle. Slow
    enough to be worth skipping on a busy runner, small enough to still finish."""
    calm = [clipgen.solid(480, 270, GRAY)] * 120
    strobe = clipgen.alternating(
        60, clipgen.solid(480, 270, BLACK), clipgen.solid(480, 270, WHITE)
    )
    path = hazard_clip("long.mkv", calm + strobe + calm, fps=30)
    result = analyze_file(path, WCAG)
    assert result.frame_count == 300
    assert not result.passes
    strobe_starts_at = 120 * 1000.0 / 30.0
    strobe_ends_at = 180 * 1000.0 / 30.0
    assert any(
        segment.start_ms <= strobe_starts_at and segment.end_ms >= strobe_ends_at - 100
        for segment in result.segments
    )
