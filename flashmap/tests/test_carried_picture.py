"""Carrying the picture rectangle across a re-encode.

Area fractions are measured on the picture rectangle. Re-encoding nudges the outermost rows
and columns, so a detector run on a re-encode can find a rectangle a row or two smaller than
the one it found in the original. A smaller rectangle lifts every area fraction, and a lifted
fraction pushes spans over the 25 percent line that the original never broke. That blocked a
real title: the source's picture was 192 by 108 analysis pixels and the rendition's came out
192 by 106.

The rule: the source file is what gets analyzed, and a re-encode of it is measured on the
rectangle out of the source's map rather than on one found in the re-encode.
"""

from __future__ import annotations

import json

import pytest

import clipgen
from flashmap import WCAG, analyze_file
from flashmap.decode import UnsupportedInput
from flashmap.picture import CARRIED, DETECTED, CarriedPicture, rect_in_frame
from flashmap.sidecar import build_map

W, H = 64, 48
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (110, 110, 110)

FULL_FRAME = CarriedPicture(left=0, top=0, width=W, height=H, coded_width=W, coded_height=H)
TWO_ROWS_SHORT = CarriedPicture(
    left=0, top=0, width=W, height=H - 2, coded_width=W, coded_height=H
)


def _flashing_band_frames(count: int = 24):
    """A band that flashes over a still grey background, on a clip with no bars.

    Eight rows deep, which is half the height of the ten degree window on a 48 row picture.
    Half rather than all of it, because a window the band fills completely reads 1.0 whatever
    the rectangle is, and this clip has to be able to show the difference.
    """
    quiet = clipgen.solid(W, H, GRAY)
    lit = clipgen.patch(quiet, WHITE, top=0.25, left=0.0, height=8 / H, width=1.0)
    return clipgen.alternating(count, quiet, lit)


def test_rect_in_frame_scales_a_coded_rectangle_into_an_analysis_frame():
    carried = CarriedPicture(
        left=40, top=60, width=1200, height=600, coded_width=1280, coded_height=720
    )
    rect = rect_in_frame(carried, 192, 108)
    assert (rect.left, rect.top, rect.width, rect.height) == (6, 9, 180, 90)
    assert (rect.frame_width, rect.frame_height) == (192, 108)


def test_rect_in_frame_never_runs_off_the_frame():
    carried = CarriedPicture(
        left=0, top=0, width=9999, height=9999, coded_width=64, coded_height=48
    )
    rect = rect_in_frame(carried, 64, 48)
    assert rect.left + rect.width <= 64
    assert rect.top + rect.height <= 48


def test_a_shorter_rectangle_lifts_the_area_fraction(hazard_clip):
    """This is the bug in one assertion. Same file, same pixels, two rectangles.

    Two rows fewer is the whole difference, and every area fraction goes up because the
    denominator went down.
    """
    path = hazard_clip("carried_band.mkv", _flashing_band_frames(), fps=20)
    on_source = analyze_file(path, WCAG, carried_picture=FULL_FRAME)
    on_shrunken = analyze_file(path, WCAG, carried_picture=TWO_ROWS_SHORT)
    assert on_source.segments and on_shrunken.segments
    assert on_shrunken.segments[0].area_fraction > on_source.segments[0].area_fraction


def test_the_carried_rectangle_is_the_one_measured_on(hazard_clip):
    path = hazard_clip("carried_used.mkv", _flashing_band_frames(), fps=20)
    result = analyze_file(path, WCAG, carried_picture=TWO_ROWS_SHORT)
    assert (result.picture.width, result.picture.height) == (W, H - 2)
    assert result.picture_source == CARRIED


def test_the_detector_still_says_what_it_found(hazard_clip):
    """Carrying a rectangle in does not switch the detector off. What it found is reported,
    so the two can be compared without analysing the file again."""
    path = hazard_clip("carried_detected.mkv", _flashing_band_frames(), fps=20)
    result = analyze_file(path, WCAG, carried_picture=TWO_ROWS_SHORT)
    assert result.detected_picture is not None
    assert (result.detected_picture.width, result.detected_picture.height) == (W, H)
    assert result.detected_picture.height != result.picture.height


def test_detecting_is_still_what_happens_when_nothing_is_carried(hazard_clip):
    path = hazard_clip("carried_none.mkv", _flashing_band_frames(), fps=20)
    result = analyze_file(path, WCAG)
    assert result.picture_source == DETECTED
    assert (result.picture.width, result.picture.height) == (W, H)


def test_a_rectangle_from_a_different_frame_size_is_refused(hazard_clip):
    """A rectangle from a 1280 by 720 file says nothing about a 64 by 48 one."""
    path = hazard_clip("carried_wrong_size.mkv", _flashing_band_frames(), fps=20)
    wrong = CarriedPicture(
        left=0, top=0, width=1280, height=720, coded_width=1280, coded_height=720
    )
    with pytest.raises(UnsupportedInput) as caught:
        analyze_file(path, WCAG, carried_picture=wrong)
    assert "1280x720" in str(caught.value)


def test_the_map_carries_the_rectangle_in_coded_pixels(hazard_clip):
    """Analysis pixels depend on the analysis width, which is a setting. Coded pixels are the
    file, so they are what a re-encode is measured against later."""
    path = hazard_clip("carried_map.mkv", _flashing_band_frames(), fps=20)
    document = build_map(analyze_file(path, WCAG))
    picture = document["picture"]
    assert picture["source"] == DETECTED
    assert picture["coded"] == {"left": 0, "top": 0, "width": W, "height": H}
    assert "detected" not in picture


def test_a_carried_map_says_so_and_keeps_what_the_detector_found(hazard_clip):
    path = hazard_clip("carried_map2.mkv", _flashing_band_frames(), fps=20)
    document = build_map(analyze_file(path, WCAG, carried_picture=TWO_ROWS_SHORT))
    picture = document["picture"]
    assert picture["source"] == CARRIED
    assert picture["coded"] == {"left": 0, "top": 0, "width": W, "height": H - 2}
    assert picture["detected"]["coded"] == {"left": 0, "top": 0, "width": W, "height": H}
    assert "carried in from another file's map" in picture["note"]
    # The map still has to serialise, because it is signed as canonical JSON.
    json.dumps(document, sort_keys=True, allow_nan=False)
