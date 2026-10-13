"""Burned-in subtitles and small user interface overlays.

A subtitle that pops in and out, or a small blinking icon, changes a few pixels very often. The
area rule is what keeps that from being reported as a hazard: a small region cannot fill a
quarter of a 10 degree field. These tests hold the analyser to that, and the last one shows the
analyser still sees flashing that a subtitle happens to sit on top of.
"""

from __future__ import annotations

import clipgen
from flashmap import WCAG, analyze_file
from flashmap.area import wcag_reference_window

W, H = 64, 48
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

SUBTITLE = dict(top=0.80, left=0.20, height=3 / H, width=0.60)
ICON = dict(top=0.04, left=0.88, height=6 / H, width=6 / W)


def test_the_overlays_are_small_enough_that_the_area_rule_should_save_them():
    window = wcag_reference_window(W, H)
    subtitle_rows = 3
    icon_rows, icon_cols = 6, 6
    assert subtitle_rows / window.height_px < WCAG.area_fraction_limit
    assert (icon_rows * icon_cols) / (window.height_px * window.width_px) < (
        WCAG.area_fraction_limit
    )


def test_a_static_burned_in_subtitle_is_not_flashing(calm_clip):
    background = clipgen.solid(W, H, GRAY)
    with_subtitle = clipgen.patch(background, WHITE, **SUBTITLE)
    path = calm_clip("static_sub.mkv", [with_subtitle] * 40, fps=20)
    assert analyze_file(path, WCAG).passes


def test_a_subtitle_popping_in_and_out_every_frame_does_not_trigger(calm_clip):
    """The worst case for a subtitle: 10 changes a second, on and off."""
    background = clipgen.solid(W, H, GRAY)
    with_subtitle = clipgen.patch(background, WHITE, **SUBTITLE)
    path = calm_clip("blink_sub.mkv", clipgen.alternating(40, background, with_subtitle), fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]


def test_a_small_blinking_icon_does_not_trigger(calm_clip):
    background = clipgen.solid(W, H, GRAY)
    with_icon = clipgen.patch(background, WHITE, **ICON)
    path = calm_clip("icon.mkv", clipgen.alternating(40, background, with_icon), fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]


def test_a_subtitle_and_an_icon_together_still_do_not_trigger(calm_clip):
    background = clipgen.solid(W, H, GRAY)
    busy = clipgen.patch(clipgen.patch(background, WHITE, **SUBTITLE), WHITE, **ICON)
    path = calm_clip("both.mkv", clipgen.alternating(40, background, busy), fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]


def test_a_subtitle_over_real_flashing_does_not_hide_the_flashing(hazard_clip):
    """The static subtitle must not make the analyser miss the strobe behind it."""
    dark = clipgen.patch(clipgen.solid(W, H, BLACK), WHITE, **SUBTITLE)
    bright = clipgen.patch(clipgen.solid(W, H, WHITE), WHITE, **SUBTITLE)
    path = hazard_clip("sub_over_strobe.mkv", clipgen.alternating(40, dark, bright), fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    assert result.segments[0].area_fraction > WCAG.area_fraction_limit


def test_a_subtitle_the_size_of_a_third_of_the_screen_is_not_a_small_overlay(hazard_clip):
    """The rule is about area, not about being called a subtitle. A caption block this big
    really would break the thresholds, and the analyser says so."""
    background = clipgen.solid(W, H, GRAY)
    huge = clipgen.patch(background, WHITE, top=0.6, left=0.0, height=0.34, width=1.0)
    path = hazard_clip("huge_sub.mkv", clipgen.alternating(40, background, huge), fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
