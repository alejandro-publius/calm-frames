"""The room rule: a household setting can only add hides, never remove one.

The room window is appended to the profile's own window, and the analyser takes the largest
coverage across the list. Adding to a list cannot lower a maximum, so the guarantee holds by
construction. These tests hold it to that on real clips, including one where a close seat adds
a hide that WCAG on its own would not ask for.
"""

from __future__ import annotations

import pytest

import clipgen
from flashmap import WCAG, RoomSetting, analyze_file
from flashmap.analyze import build_area_windows
from flashmap.area import wcag_reference_window
from flashmap.picture import PictureRect
from flashmap.room import room_window

W, H = 64, 48
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

CLOSE = RoomSetting(tv_diagonal_in=55.0, seat_distance_in=36.0)
TYPICAL = RoomSetting(tv_diagonal_in=55.0, seat_distance_in=96.0)
FAR = RoomSetting(tv_diagonal_in=32.0, seat_distance_in=240.0)
ROOMS = [CLOSE, TYPICAL, FAR]

FULL_PICTURE = PictureRect(0, 0, W, H, False, False, W, H)


def _subtitle_clip(path_factory, name):
    background = clipgen.solid(W, H, GRAY)
    band = clipgen.patch(background, WHITE, top=0.4, left=0.0, height=3 / H, width=1.0)
    return path_factory(name, clipgen.alternating(40, background, band), fps=20)


def _strobe_clip(path_factory, name):
    frames = clipgen.alternating(40, clipgen.solid(W, H, BLACK), clipgen.solid(W, H, WHITE))
    return path_factory(name, frames, fps=20)


def _covered(result):
    return [(segment.start_ms, segment.end_ms) for segment in result.segments]


def _is_covered(interval, intervals):
    start, end = interval
    return any(other_start <= start and other_end >= end for other_start, other_end in intervals)


# ---- the geometry ------------------------------------------------------------------------


def test_a_ten_degree_field_is_the_expected_size_on_a_55_inch_screen():
    # 2 * d * tan(5 degrees), with the screen 47.93 inches wide.
    assert TYPICAL.display_width_in == pytest.approx(47.93, abs=0.05)
    assert TYPICAL.field_inches == pytest.approx(16.80, abs=0.05)


def test_sitting_closer_makes_the_window_smaller_and_so_the_test_stricter():
    close = room_window(CLOSE, W, H, W, H)
    typical = room_window(TYPICAL, W, H, W, H)
    assert close.width_px < typical.width_px
    assert close.height_px < typical.height_px


def test_the_room_window_is_added_to_the_profile_window_not_swapped_for_it():
    windows = build_area_windows(WCAG, FULL_PICTURE, CLOSE)
    names = [window.name for window in windows]
    assert names == ["wcag-10deg", "room-10deg"]
    assert windows[0] == wcag_reference_window(W, H)


def test_a_room_setting_needs_both_numbers():
    with pytest.raises(ValueError):
        RoomSetting(tv_diagonal_in=0.0, seat_distance_in=96.0)
    with pytest.raises(ValueError):
        RoomSetting(tv_diagonal_in=55.0, seat_distance_in=-1.0)


# ---- the guarantee -----------------------------------------------------------------------


def test_a_close_seat_adds_a_hide_that_wcag_alone_does_not_ask_for(calm_clip):
    path = _subtitle_clip(calm_clip, "band.mkv")
    plain = analyze_file(path, WCAG)
    assert plain.passes, "this clip is below the WCAG thresholds on its own"

    close = analyze_file(path, WCAG, room=CLOSE)
    assert not close.passes
    assert close.segments[0].triggered_by == ["room-10deg"]
    assert close.segments[0].breaks_baseline is False


def test_a_far_seat_never_removes_a_hide(hazard_clip):
    path = _strobe_clip(hazard_clip, "strobe.mkv")
    plain = analyze_file(path, WCAG)
    far = analyze_file(path, WCAG, room=FAR)
    assert not plain.passes
    for interval in _covered(plain):
        assert _is_covered(interval, _covered(far)), (interval, _covered(far))


@pytest.mark.parametrize("room", ROOMS, ids=["close", "typical", "far"])
def test_no_room_setting_can_make_the_output_weaker_than_wcag(room, hazard_clip, calm_clip):
    """The one that matters. Every interval WCAG hides has to still be hidden with a room."""
    for maker, name in ((hazard_clip, "HAZ.mkv"), (calm_clip, "band.mkv")):
        path = (
            _strobe_clip(maker, name) if name.startswith("HAZ") else _subtitle_clip(maker, name)
        )
        plain = analyze_file(path, WCAG)
        with_room = analyze_file(path, WCAG, room=room)
        assert with_room.hidden_ms >= plain.hidden_ms
        for interval in _covered(plain):
            assert _is_covered(interval, _covered(with_room)), (
                name,
                interval,
                _covered(with_room),
            )


def test_the_room_settings_land_in_the_map(hazard_clip):
    from flashmap import build_map

    path = _strobe_clip(hazard_clip, "mapped.mkv")
    document = build_map(analyze_file(path, WCAG, room=CLOSE))
    room = document["profile"]["room"]
    assert room["tv_diagonal_in"] == 55.0
    assert room["seat_distance_in"] == 36.0
    assert room["field_degrees"] == 10.0
    names = [window["name"] for window in document["profile"]["area_windows"]]
    assert names == ["wcag-10deg", "room-10deg"]
