"""Variable frame rate input.

flashmap reads the presentation timestamp of every frame from the container. It never divides
by a nominal frame rate. The proof is two clips with identical pixels and different timestamps:
one is a hazard and one is not, and only the timestamps can tell them apart.
"""

from __future__ import annotations

import pytest

import clipgen
from flashmap import WCAG, analyze_file
from flashmap.decode import iter_frames, probe

W, H = 64, 48
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def _strobe_frames(count: int = 24):
    return clipgen.alternating(count, clipgen.solid(W, H, BLACK), clipgen.solid(W, H, WHITE))


def test_timestamps_come_from_the_container(calm_clip):
    stamps = [0, 37, 111, 250, 251, 900, 1600]
    frames = [clipgen.solid(W, H, (index * 20 % 256,) * 3) for index in range(len(stamps))]
    path = calm_clip("stamps.mkv", frames, timestamps_ms=stamps)
    info = probe(path)
    decoded = [frame.pts_ms for frame in iter_frames(path, info)]
    assert decoded == pytest.approx([float(value) for value in stamps])


def test_the_same_pixels_packed_tight_in_time_are_a_hazard(hazard_clip):
    frames = _strobe_frames()
    stamps = [index * 50.0 for index in range(len(frames))]
    path = hazard_clip("tight.mkv", frames, timestamps_ms=stamps)
    result = analyze_file(path, WCAG)
    assert not result.passes


def test_the_same_pixels_spread_out_in_time_are_not(calm_clip):
    """One flash every 800 ms is well under three a second, whatever the container's average
    frame rate says."""
    frames = _strobe_frames()
    stamps = [index * 400.0 for index in range(len(frames))]
    path = calm_clip("spread.mkv", frames, timestamps_ms=stamps)
    result = analyze_file(path, WCAG)
    assert result.passes, [segment.as_dict() for segment in result.segments]


def test_a_variable_rate_clip_is_reported_as_variable(hazard_clip):
    """Fast at the start, slow at the end. Only the fast part is a hazard."""
    fast = _strobe_frames(20)
    slow = _strobe_frames(8)
    stamps = [index * 50.0 for index in range(len(fast))]
    last = stamps[-1]
    stamps += [last + (index + 1) * 600.0 for index in range(len(slow))]
    path = hazard_clip("mixed.mkv", fast + slow, timestamps_ms=stamps)
    result = analyze_file(path, WCAG)

    assert result.variable_frame_rate
    assert result.frame_interval_ms["min"] == pytest.approx(50.0)
    assert result.frame_interval_ms["max"] == pytest.approx(600.0)
    assert not result.passes
    # The slow tail on its own is one flash every 1.2 seconds, so nothing in it is a hazard.
    # The only offending flashes are in the fast run, plus the first slow frame, which is still
    # inside the one-second window that the fast run ends in.
    first_slow_frame = last + 600.0
    second_slow_frame = last + 1200.0
    assert len(result.segments) == 1
    for segment in result.segments:
        assert segment.flash_last_ms <= first_slow_frame, segment.as_dict()
        assert segment.end_ms < second_slow_frame, segment.as_dict()


def test_a_constant_rate_clip_is_not_reported_as_variable(calm_clip):
    frames = [clipgen.solid(W, H, (100, 100, 100))] * 12
    path = calm_clip("constant.mkv", frames, fps=25)
    result = analyze_file(path, WCAG)
    assert not result.variable_frame_rate
    assert result.frame_interval_ms["min"] == pytest.approx(result.frame_interval_ms["max"])


def test_a_gap_in_the_middle_does_not_shift_later_timestamps(calm_clip):
    stamps = [0, 50, 100, 150, 5000, 5050, 5100]
    frames = [clipgen.solid(W, H, (60, 60, 60))] * len(stamps)
    path = calm_clip("gap.mkv", frames, timestamps_ms=stamps)
    info = probe(path)
    decoded = [frame.pts_ms for frame in iter_frames(path, info)]
    assert decoded[-1] == pytest.approx(5100.0)
