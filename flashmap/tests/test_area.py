"""Sliding area windows.

WCAG's second condition rescues content whose flashing is small: "the combined area of flashes
occurring concurrently occupies no more than a total of .006 steradians within any 10 degree
visual field on the screen (25% of any 10 degree visual field on the screen)".

The window is slid over every position, so "any" is taken at its word.
"""

from __future__ import annotations

import numpy as np
import pytest

import clipgen
from flashmap import WCAG, analyze_file
from flashmap.area import (
    WCAG_FIELD_HEIGHT_FRACTION,
    WCAG_FIELD_WIDTH_FRACTION,
    AreaWindow,
    best_window,
    max_coverage,
    wcag_reference_window,
)

W, H = 64, 48
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)


def test_the_reference_window_is_the_published_fraction_of_the_picture():
    window = wcag_reference_window(1024, 768)
    assert (window.width_px, window.height_px) == (341, 256)
    assert WCAG_FIELD_WIDTH_FRACTION == pytest.approx(341 / 1024)
    assert WCAG_FIELD_HEIGHT_FRACTION == pytest.approx(256 / 768)


def test_an_empty_mask_covers_nothing_and_a_full_mask_covers_everything():
    assert max_coverage(np.zeros((20, 20), dtype=bool), 6, 6) == 0.0
    assert max_coverage(np.ones((20, 20), dtype=bool), 6, 6) == 1.0


def test_the_window_slides_to_the_busiest_place_not_the_average():
    mask = np.zeros((20, 20), dtype=bool)
    mask[0:4, 0:4] = True  # a sixteenth of the picture, all in one corner
    assert max_coverage(mask, 20, 20) == pytest.approx(16 / 400)
    assert max_coverage(mask, 4, 4) == pytest.approx(1.0)


def test_a_window_bigger_than_the_picture_is_clipped_to_the_picture():
    mask = np.ones((10, 10), dtype=bool)
    assert max_coverage(mask, 1000, 1000) == 1.0


def test_adding_a_window_can_only_raise_the_answer():
    """This is the structural reason a room setting can never weaken the result."""
    rng = np.random.default_rng(7)
    mask = rng.random((32, 32)) < 0.2
    base = [AreaWindow("base", 10, 10, "test")]
    more = base + [AreaWindow("small", 4, 4, "test")]
    _, base_value = best_window(mask, base)
    _, more_value = best_window(mask, more)
    assert more_value >= base_value


@pytest.mark.parametrize("window_height", [4, 8, 16, 24, 48])
def test_several_window_sizes_all_report_a_fraction_between_zero_and_one(window_height):
    rng = np.random.default_rng(3)
    mask = rng.random((48, 64)) < 0.3
    value = max_coverage(mask, window_height, 21)
    assert 0.0 <= value <= 1.0


def test_flashing_over_the_whole_picture_fails_the_area_rule(hazard_clip):
    frames = clipgen.alternating(40, clipgen.solid(W, H, GRAY), clipgen.solid(W, H, WHITE))
    path = hazard_clip("full.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    assert result.segments[0].area_fraction > WCAG.area_fraction_limit


def test_a_band_that_fills_a_fifth_of_the_field_passes(calm_clip):
    """The reference window on a 64 by 48 picture is 21 by 16 pixels. A band three rows tall
    fills 3/16 of it, which is under a quarter."""
    window = wcag_reference_window(W, H)
    assert (window.width_px, window.height_px) == (21, 16)
    band_rows = 3
    assert band_rows / window.height_px < WCAG.area_fraction_limit

    background = clipgen.solid(W, H, GRAY)
    flashing = clipgen.patch(
        background, WHITE, top=0.4, left=0.0, height=band_rows / H, width=1.0
    )
    path = calm_clip("band.mkv", clipgen.alternating(40, background, flashing), fps=20)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]


def test_a_band_that_fills_more_than_a_quarter_of_the_field_fails(hazard_clip):
    window = wcag_reference_window(W, H)
    band_rows = 6
    assert band_rows / window.height_px > WCAG.area_fraction_limit

    background = clipgen.solid(W, H, GRAY)
    flashing = clipgen.patch(
        background, WHITE, top=0.4, left=0.0, height=band_rows / H, width=1.0
    )
    path = hazard_clip("wideband.mkv", clipgen.alternating(40, background, flashing), fps=20)
    result = analyze_file(path, WCAG)
    assert not result.passes
    assert result.segments[0].area_window == "wcag-10deg"


def test_the_map_names_the_window_every_area_fraction_was_measured_in(hazard_clip):
    frames = clipgen.alternating(40, clipgen.solid(W, H, GRAY), clipgen.solid(W, H, WHITE))
    path = hazard_clip("named.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    names = {window.name for window in result.area_windows}
    assert names == {"wcag-10deg"}
    for segment in result.segments:
        assert segment.area_window in names
