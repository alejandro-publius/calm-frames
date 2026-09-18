"""Letterbox and pillarbox: the area has to be measured on the picture.

Bars are not picture. Counting them makes every area fraction look smaller than it is, which
lets flashing through. These tests show a clip that passes when the bars are counted and fails
when they are not, which is the whole point.
"""

from __future__ import annotations

import numpy as np
import pytest

import clipgen
from flashmap import WCAG, analyze_file
from flashmap.area import max_coverage, wcag_reference_window
from flashmap.picture import LetterboxSettings, detect_picture

W, H = 64, 48
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BAR_ROWS = 12
BAND_ROWS = 3


def _letterboxed(inner_rgb, band: bool = False):
    frame = clipgen.solid(W, H, BLACK)
    frame[BAR_ROWS : H - BAR_ROWS, :] = inner_rgb
    if band:
        top = BAR_ROWS + 8
        frame[top : top + BAND_ROWS, :] = WHITE
    return frame


def test_detect_picture_finds_nothing_when_there_are_no_bars():
    sample = np.full((48, 64), 0.5, dtype=np.float32)
    rect = detect_picture([sample])
    assert (rect.left, rect.top, rect.width, rect.height) == (0, 0, 64, 48)
    assert not rect.letterbox and not rect.pillarbox


def test_detect_picture_finds_top_and_bottom_bars():
    sample = np.zeros((48, 64), dtype=np.float32)
    sample[12:36, :] = 0.5
    rect = detect_picture([sample], LetterboxSettings(erode_px=0))
    assert rect.letterbox and not rect.pillarbox
    assert (rect.top, rect.height) == (12, 24)


def test_detect_picture_finds_left_and_right_bars():
    sample = np.zeros((48, 64), dtype=np.float32)
    sample[:, 16:48] = 0.5
    rect = detect_picture([sample], LetterboxSettings(erode_px=0))
    assert rect.pillarbox and not rect.letterbox
    assert (rect.left, rect.width) == (16, 32)


def test_a_dark_stripe_at_one_edge_is_not_a_pillarbox():
    """A bar is a frame around the picture. One dark edge and one bright edge is content.

    This is the shape of a black to white grating whose outermost bar happens to be dark, and
    cropping it cost the pattern rule a whole pair of stripes.
    """
    sample = np.full((48, 64), 0.5, dtype=np.float32)
    sample[:, :8] = 0.0
    rect = detect_picture([sample], LetterboxSettings(erode_px=0))
    assert not rect.pillarbox
    assert (rect.left, rect.width) == (0, 64)


def test_dark_bars_at_both_edges_of_a_grating_are_not_a_pillarbox():
    """Both edges dark, so symmetry alone would crop. The picture is full of dark columns, and
    a pillarbox bar has nothing like itself inside the picture, so this is content."""
    sample = np.full((48, 64), 0.5, dtype=np.float32)
    for start in range(0, 64, 16):
        sample[:, start : start + 8] = 0.0
    rect = detect_picture([sample], LetterboxSettings(erode_px=0))
    assert not rect.pillarbox
    assert (rect.left, rect.width) == (0, 64)


def test_a_dark_frame_is_not_a_letterboxed_frame():
    sample = np.zeros((48, 64), dtype=np.float32)
    rect = detect_picture([sample])
    assert (rect.width, rect.height) == (64, 48)
    assert not rect.letterbox


def test_bars_are_judged_over_every_sampled_frame_not_just_one():
    """A row is a bar only when it is dark in every sampled frame. One frame with bars and one
    frame that fills the screen means there are no bars."""
    letterboxed = np.zeros((48, 64), dtype=np.float32)
    letterboxed[12:36, :] = 0.5
    full_screen = np.full((48, 64), 0.5, dtype=np.float32)

    assert detect_picture([letterboxed], LetterboxSettings(erode_px=0)).height == 24
    rect = detect_picture([letterboxed, full_screen], LetterboxSettings(erode_px=0))
    assert (rect.width, rect.height) == (64, 48)
    assert not rect.letterbox


def test_a_frame_that_is_black_all_over_does_not_make_the_file_letterboxed():
    dark = np.zeros((48, 64), dtype=np.float32)
    bright = np.full((48, 64), 0.5, dtype=np.float32)
    rect = detect_picture([dark, bright, dark])
    assert (rect.width, rect.height) == (64, 48)


def test_the_same_band_passes_on_the_coded_frame_and_fails_on_the_picture():
    """The arithmetic behind the clip test below, with no decoding in the way."""
    mask = np.zeros((H, W), dtype=bool)
    mask[BAR_ROWS + 8 : BAR_ROWS + 8 + BAND_ROWS, :] = True

    whole = wcag_reference_window(W, H)
    assert max_coverage(mask, whole.height_px, whole.width_px) <= WCAG.area_fraction_limit

    picture_height = H - 2 * (BAR_ROWS + 1)  # the detector erodes one row per bar
    picture = wcag_reference_window(W, picture_height)
    cropped = mask[BAR_ROWS + 1 : H - BAR_ROWS - 1, :]
    assert max_coverage(cropped, picture.height_px, picture.width_px) > WCAG.area_fraction_limit


def test_a_letterboxed_clip_is_measured_on_the_picture(hazard_clip):
    frames = clipgen.alternating(40, _letterboxed(GRAY), _letterboxed(GRAY, band=True))
    path = hazard_clip("letterbox.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)

    assert result.picture.letterbox
    assert result.picture.height < H
    assert not result.passes, "the band fills more than a quarter of a field on the picture"
    assert result.picture.as_dict()["measured_on"] == "picture"


def test_a_pillarboxed_clip_is_measured_on_the_picture(hazard_clip):
    def build(band: bool):
        frame = clipgen.solid(W, H, BLACK)
        frame[:, 16:48] = GRAY
        if band:
            frame[:, 16:26] = WHITE
        return frame

    frames = clipgen.alternating(40, build(False), build(True))
    path = hazard_clip("pillarbox.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert result.picture.pillarbox
    assert result.picture.width < W
    assert not result.passes


def test_the_report_says_where_the_area_was_measured(hazard_clip):
    frames = clipgen.alternating(40, _letterboxed(GRAY), _letterboxed(GRAY, band=True))
    path = hazard_clip("says.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    described = result.picture.as_dict()
    assert described["measured_on"] == "picture"
    assert "not on the full coded frame" in str(described["note"])
    assert described["letterbox"] is True
