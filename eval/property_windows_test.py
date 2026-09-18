"""Property tests for flashmap's window math.

WCAG asks whether the flashing fills more than a quarter of any ten degree field on the
screen, so flashmap slides one window over every position on the picture and takes the
busiest. Three things have to hold and none of them is obvious from reading the code:

* the sliding window is a maximum, bounded by nothing more than the mask it is given;
* feeding the analyser a file in pieces gives exactly the answer that feeding it whole
  gives, at any chunk size and any overlap;
* a stricter setting never removes a hide. A closer sofa or a bigger television makes the
  ten degree field a smaller part of the picture, and for a solid patch of flashing that
  means the same or more coverage, so the same or more is hidden.

The third one is stated for a solid patch on purpose, and
test_a_scattered_mask_is_the_one_case_where_a_smaller_window_is_kinder says why: a smaller
window is NOT universally stricter. Four lit corners of a three by three picture fill four
ninths of the whole and only one quarter of any two by two window inside it. Real flashing
is a lit region rather than four separate pixels, which is why the claim holds in practice
and why it is worth writing down that it is not a law.

Nothing here decodes a video. The frames are built in memory, so hypothesis can try a few
hundred timelines a second.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flashmap import WCAG, RoomSetting
from flashmap.analyze import StreamingAnalyzer, _chunked, build_area_windows
from flashmap.area import (
    WCAG_FIELD_HEIGHT_FRACTION,
    WCAG_FIELD_WIDTH_FRACTION,
    max_coverage,
    wcag_reference_window,
)
from flashmap.color import relative_luminance, srgb_to_linear
from flashmap.decode import AnalysisFrame
from flashmap.picture import detect_picture

SETTINGS = settings(max_examples=80, deadline=None)

HEIGHT, WIDTH = 12, 16

masks = st.lists(
    st.lists(st.booleans(), min_size=WIDTH, max_size=WIDTH),
    min_size=HEIGHT,
    max_size=HEIGHT,
).map(lambda rows: np.array(rows, dtype=bool))

window_sizes = st.tuples(
    st.integers(min_value=1, max_value=HEIGHT),
    st.integers(min_value=1, max_value=WIDTH),
)


# ------------------------------------------------------------------ the sliding window


@given(mask=masks, size=window_sizes)
@SETTINGS
def test_coverage_is_a_fraction(mask, size):
    value = max_coverage(mask, size[0], size[1])
    assert 0.0 <= value <= 1.0


@given(mask=masks, size=window_sizes, extra=masks)
@SETTINGS
def test_lighting_more_of_the_picture_never_lowers_the_coverage(mask, size, extra):
    """Monotone in the mask. Anything else would mean more flashing scoring less."""
    before = max_coverage(mask, size[0], size[1])
    after = max_coverage(mask | extra, size[0], size[1])
    assert after >= before - 1e-12


@given(size=window_sizes)
@SETTINGS
def test_the_ends_of_the_range(size):
    everything = np.ones((HEIGHT, WIDTH), dtype=bool)
    nothing = np.zeros((HEIGHT, WIDTH), dtype=bool)
    assert max_coverage(everything, size[0], size[1]) == pytest.approx(1.0)
    assert max_coverage(nothing, size[0], size[1]) == pytest.approx(0.0)


@given(mask=masks, over=st.integers(min_value=0, max_value=40))
@SETTINGS
def test_a_window_bigger_than_the_picture_is_the_whole_picture(mask, over):
    """A small screen cannot show more than a screenful, so the window is clipped."""
    clipped = max_coverage(mask, HEIGHT + over, WIDTH + over)
    assert clipped == pytest.approx(float(mask.mean()))


@given(
    top=st.integers(min_value=0, max_value=HEIGHT - 1),
    left=st.integers(min_value=0, max_value=WIDTH - 1),
    height=st.integers(min_value=1, max_value=HEIGHT),
    width=st.integers(min_value=1, max_value=WIDTH),
    shrink_h=st.integers(min_value=0, max_value=HEIGHT - 1),
    shrink_w=st.integers(min_value=0, max_value=WIDTH - 1),
)
@SETTINGS
def test_a_smaller_window_is_stricter_for_a_solid_patch_of_flashing(
    top, left, height, width, shrink_h, shrink_w
):
    """The claim the room rule rests on, stated where it is true.

    A closer sofa makes the ten degree field a smaller part of the picture. For a solid
    patch, shrinking the window can only let it sit more completely inside the patch, so the
    coverage goes up and the same content is hidden or more of it is.
    """
    mask = np.zeros((HEIGHT, WIDTH), dtype=bool)
    mask[top : top + height, left : left + width] = True

    big_h, big_w = HEIGHT, WIDTH
    small_h = max(1, big_h - shrink_h)
    small_w = max(1, big_w - shrink_w)

    wide = max_coverage(mask, big_h, big_w)
    narrow = max_coverage(mask, small_h, small_w)
    assert narrow >= wide - 1e-12, (
        f"a {small_h}x{small_w} window scored {narrow} where {big_h}x{big_w} scored {wide} "
        f"on a solid {height}x{width} patch"
    )


def test_a_scattered_mask_is_the_one_case_where_a_smaller_window_is_kinder():
    """Written down so nobody has to rediscover it.

    Four lit corners of a three by three picture fill four ninths of the whole, and no two
    by two window inside it holds more than one of them, which is one quarter. So "smaller
    window, stricter test" is a rule about lit regions, not a law about masks. Real flashing
    is a region, which is why the room rule holds in practice.
    """
    mask = np.zeros((3, 3), dtype=bool)
    mask[0, 0] = mask[0, 2] = mask[2, 0] = mask[2, 2] = True
    assert max_coverage(mask, 3, 3) == pytest.approx(4 / 9)
    assert max_coverage(mask, 2, 2) == pytest.approx(1 / 4)


# ----------------------------------------------------------------- the reference window


@given(
    width=st.integers(min_value=16, max_value=4096),
    height=st.integers(min_value=16, max_value=4096),
)
@SETTINGS
def test_the_reference_window_is_the_published_fraction_of_any_picture(width, height):
    window = wcag_reference_window(width, height)
    assert window.width_px == max(1, round(width * WCAG_FIELD_WIDTH_FRACTION))
    assert window.height_px == max(1, round(height * WCAG_FIELD_HEIGHT_FRACTION))
    assert 1 <= window.width_px <= width
    assert 1 <= window.height_px <= height


@given(
    width=st.integers(min_value=64, max_value=2048),
    height=st.integers(min_value=64, max_value=2048),
    scale=st.integers(min_value=2, max_value=4),
)
@SETTINGS
def test_the_reference_window_scales_with_the_picture(width, height, scale):
    """The same fraction of a bigger picture, to within the rounding."""
    small = wcag_reference_window(width, height)
    big = wcag_reference_window(width * scale, height * scale)
    assert abs(big.width_px - small.width_px * scale) <= scale
    assert abs(big.height_px - small.height_px * scale) <= scale


# ------------------------------------------------------------------------- the room


@given(
    diagonal=st.floats(min_value=24.0, max_value=98.0),
    far=st.floats(min_value=36.0, max_value=200.0),
    closer_by=st.floats(min_value=0.0, max_value=100.0),
)
@SETTINGS
def test_sitting_closer_never_widens_the_window(diagonal, far, closer_by):
    """A closer sofa is a stricter setting, and a stricter setting may only add hides."""
    near = max(12.0, far - closer_by)
    picture = _picture_rect()
    wide = _room_window_px(diagonal, far, picture)
    narrow = _room_window_px(diagonal, near, picture)
    assert narrow[0] <= wide[0] + 1
    assert narrow[1] <= wide[1] + 1


@given(
    diagonal=st.floats(min_value=24.0, max_value=98.0),
    distance=st.floats(min_value=36.0, max_value=200.0),
)
@SETTINGS
def test_a_room_window_is_added_to_the_profile_window_and_never_replaces_it(
    diagonal, distance
):
    picture = _picture_rect()
    without = build_area_windows(WCAG, picture, None)
    with_room = build_area_windows(WCAG, picture, RoomSetting(diagonal, distance))
    assert [window.name for window in without] == [
        window.name for window in with_room[: len(without)]
    ], "the baseline window was replaced rather than added to"
    assert len(with_room) == len(without) + 1


def _picture_rect():
    frame = np.zeros((48, 64), dtype=np.float32)
    frame[:] = 0.5
    return detect_picture([frame])


def _room_window_px(diagonal, distance, picture):
    windows = build_area_windows(WCAG, picture, RoomSetting(diagonal, distance))
    room = windows[-1]
    return room.height_px, room.width_px


# --------------------------------------------------------- chunked equals whole file


PALETTE = {
    "black": (0.0, 0.0, 0.0),
    "white": (1.0, 1.0, 1.0),
    "grey": (0.5, 0.5, 0.5),
    "red": (1.0, 0.0, 0.0),
}

FRAME_H, FRAME_W = 24, 32


def _frame(index: int, colour: str, half: bool) -> AnalysisFrame:
    """One solid frame, or one with the top half lit and the bottom half grey."""
    rgb = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.float32)
    rgb[:] = np.array(PALETTE["grey"], dtype=np.float32)
    lit = np.array(PALETTE[colour], dtype=np.float32)
    if half:
        rgb[: FRAME_H // 2, :] = lit
    else:
        rgb[:] = lit
    return AnalysisFrame(
        index=index,
        pts_ms=index * 50.0,
        rgb=rgb,
        video_level=rgb.mean(axis=2).astype(np.float32),
    )


def _run(frames, chunk_size, overlap):
    luminance = [relative_luminance(srgb_to_linear(frame.rgb)) for frame in frames[:4]]
    picture = detect_picture(luminance)
    analyzer = StreamingAnalyzer(WCAG, picture, build_area_windows(WCAG, picture, None))
    if chunk_size is None:
        analyzer.push(frames)
    else:
        for batch in _chunked(iter(frames), chunk_size, overlap):
            analyzer.push(batch)
    return [segment.as_dict() for segment in analyzer.segments()]


timelines = st.lists(
    st.tuples(st.sampled_from(sorted(PALETTE)), st.booleans()),
    min_size=8,
    max_size=48,
).map(lambda rows: [_frame(index, colour, half) for index, (colour, half) in enumerate(rows)])


@given(
    frames=timelines,
    chunk_size=st.integers(min_value=1, max_value=40),
    overlap_ratio=st.floats(min_value=0.0, max_value=0.95),
)
@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
def test_chunked_equals_whole_file_for_any_timeline_and_any_chunking(
    frames, chunk_size, overlap_ratio
):
    """The analyser is a stream, and a stream must not care how it was fed.

    The existing test in flashmap does this over one fixed clip. This does it over random
    timelines, which is where a boundary mistake that only shows up for one shape of content
    would be found.
    """
    overlap = min(chunk_size - 1, int(chunk_size * overlap_ratio))
    assert _run(frames, chunk_size, overlap) == _run(frames, None, 0)


def test_the_timelines_under_test_really_do_flash():
    """The negative control. Comparing two empty answers proves nothing."""
    frames = [
        _frame(index, "black" if index % 2 else "white", False) for index in range(40)
    ]
    assert _run(frames, None, 0), "a strobe at ten hertz produced no segment"
    assert _run(frames, 7, 3) == _run(frames, None, 0)
