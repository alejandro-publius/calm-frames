"""Boundaries the detector is held to, fed as numbers rather than files.

Written for the October 15 video reset. Each test states its expected outcome from the spec
text and the implementation decisions in docs/SPEC_SOURCES.md, not from what the code happened
to return. Nothing here writes a flashing file: frames are arrays handed straight to the
analyzer, and the only files made are an audio-only file and an empty one.

SAFETY. No clip is played, drawn or saved. The bright frames below are solid grey arrays.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from flashmap import WCAG
from flashmap.analyze import StreamingAnalyzer, build_area_windows
from flashmap.area import max_coverage
from flashmap.decode import AnalysisFrame, UnsupportedInput, probe
from flashmap.picture import PictureRect

W, H = 192, 108
DARK = 0.0
# sRGB 0.8 is a relative luminance of about 0.60: a swing of 0.60 clears the 0.1 threshold
# with the darker image at 0, well under the 0.8 ceiling.
BRIGHT = 0.8


def _picture() -> PictureRect:
    return PictureRect(left=0, top=0, width=W, height=H, letterbox=False, pillarbox=False,
                       frame_width=W, frame_height=H)


def _frame(index: int, pts_ms: float, level: float, region: tuple[int, int, int, int] | None = None,
           base: float = DARK) -> AnalysisFrame:
    """A solid frame at `level`, or a frame at `base` with one rectangle at `level`."""
    rgb = np.full((H, W, 3), base, dtype=np.float32)
    if region is None:
        rgb[:] = level
    else:
        top, left, height, width = region
        rgb[top:top + height, left:left + width, :] = level
    video_level = rgb[:, :, 0].copy()
    return AnalysisFrame(index=index, pts_ms=float(pts_ms), rgb=rgb, video_level=video_level)


def _analyzer() -> StreamingAnalyzer:
    picture = _picture()
    return StreamingAnalyzer(WCAG, picture, build_area_windows(WCAG, picture, None))


def _strobe(stamps: list[float], region=None) -> list[AnalysisFrame]:
    """Alternate dark and bright at the given timestamps. A flash completes on every second
    bright-to-dark return, so with frames dark, bright, dark, bright, ... the flashes land on
    the frames at stamps[2], stamps[4], stamps[6], ..."""
    frames = []
    for index, stamp in enumerate(stamps):
        level = BRIGHT if index % 2 else DARK
        frames.append(_frame(index, stamp, level, region))
    return frames


def _segments(frames):
    analyzer = _analyzer()
    analyzer.push(frames)
    return [segment.as_dict() for segment in analyzer.segments()], analyzer


# ---- the one-second period -----------------------------------------------------------------


def test_four_flashes_whose_first_and_last_are_exactly_one_second_apart_fail():
    """WCAG counts flashes "in any one-second period". Implementation decision 3 evaluates the
    trailing window [t - 1000 ms, t] at every frame, closed at both ends, so a flash exactly one
    second before the fourth still belongs to its period."""
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]  # flashes complete at 100, 433, 767, 1100
    segments, _ = _segments(_strobe(stamps))
    assert len(segments) == 1, segments
    assert segments[0]["max_flashes_in_window"] == 4
    assert segments[0]["flash_first_ms"] == pytest.approx(100.0)
    assert segments[0]["flash_last_ms"] == pytest.approx(1100.0)


def test_the_same_four_flashes_one_millisecond_wider_than_a_second_pass():
    """Move the fourth flash to 1101 ms and no one-second period holds more than three."""
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1101]  # flashes at 100, 433, 767, 1101
    segments, _ = _segments(_strobe(stamps))
    assert segments == [], segments


def test_a_gap_in_the_timestamps_does_not_carry_old_flashes_into_the_new_period():
    """Three flashes, a gap, then one more: 4 flashes in 1.8 seconds is not 4 in one second."""
    stamps = [0, 50, 100, 300, 433, 600, 767, 1700, 1800]  # flashes at 100, 433, 767, 1800
    segments, _ = _segments(_strobe(stamps))
    assert segments == [], segments


def test_the_hidden_interval_starts_one_second_before_the_fourth_flash_and_covers_them_all():
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]
    segments, _ = _segments(_strobe(stamps))
    [segment] = segments
    assert segment["start_ms"] == pytest.approx(100.0)  # 1100 - window
    assert segment["end_ms"] >= 1100.0
    assert segment["start_ms"] <= segment["flash_first_ms"] <= segment["flash_last_ms"] <= segment["end_ms"]


# ---- timestamps --------------------------------------------------------------------------------


def test_a_frame_that_repeats_the_previous_timestamp_is_not_counted_twice():
    """A decoder can hand back two frames with one presentation time. The second is dropped:
    it is not a new moment, so it can neither complete a flash nor lengthen the file."""
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]
    plain = _strobe(stamps)
    doubled = []
    for frame in plain:
        doubled.append(frame)
        doubled.append(AnalysisFrame(index=frame.index, pts_ms=frame.pts_ms, rgb=frame.rgb,
                                     video_level=frame.video_level))
    plain_segments, plain_analyzer = _segments(plain)
    doubled_segments, doubled_analyzer = _segments(doubled)
    assert doubled_analyzer.frame_count == plain_analyzer.frame_count == len(stamps)
    assert doubled_segments == plain_segments


def test_a_frame_whose_timestamp_goes_backwards_is_dropped_rather_than_rewinding_the_window():
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1101]
    frames = _strobe(stamps)
    # A stray bright frame stamped before the last one: dropped, so the sequence still passes.
    frames.insert(8, _frame(99, 20.0, BRIGHT))
    segments, analyzer = _segments(frames)
    assert analyzer.frame_count == len(stamps)
    assert analyzer.last_pts_ms == pytest.approx(1101.0)
    assert segments == []


def test_a_48000_over_1001_cadence_is_constant_rate_and_its_timing_is_kept_to_the_microsecond():
    """The NPS Acadia proxy is 48000/1001 frames a second: 20.854 ms apart, never a whole number.
    Frame interval statistics must call that constant, and the last timestamp must be the
    container's, not a count divided by a nominal rate."""
    count = 480
    stamps = [index * 1001.0 / 48.0 for index in range(count)]
    frames = [_frame(index, stamp, 0.3) for index, stamp in enumerate(stamps)]
    analyzer = _analyzer()
    analyzer.push(frames)
    variable, stats = analyzer.interval_stats()
    assert variable is False
    assert stats["min"] == pytest.approx(1001.0 / 48.0, abs=1e-6)
    assert stats["max"] == pytest.approx(1001.0 / 48.0, abs=1e-6)
    assert analyzer.last_pts_ms == pytest.approx(stamps[-1], abs=1e-9)
    assert analyzer.frame_count == count
    assert analyzer.segments() == []


def test_the_same_flashes_at_the_acadia_cadence_are_counted_by_timestamp_not_by_frame_number():
    """Four flashes inside one second at 47.952 fps is the hazard it would be at 48 or 50 fps."""
    period = 1001.0 / 48.0
    # 48 frames, bright on every sixth frame for one frame: a flash completes on the frame after
    # each bright one, at 2, 8, 14, 20, 26, ... frames; four of them fit in one second.
    frames = []
    for index in range(48):
        level = BRIGHT if index % 6 == 1 else DARK
        frames.append(_frame(index, index * period, level))
    segments, _ = _segments(frames)
    assert len(segments) == 1
    assert segments[0]["max_flashes_in_window"] >= 4


# ---- the quarter of the window ----------------------------------------------------------------


def test_flashing_over_exactly_a_quarter_of_the_reference_window_passes():
    """Condition 2 fails when the flashing area is "more than" 25% of the 10 degree field.
    Exactly 25% is not more than 25%."""
    picture = _picture()
    [window] = [w for w in build_area_windows(WCAG, picture, None) if w.name == "wcag-10deg"]
    assert (window.width_px, window.height_px) == (64, 36)
    quarter = window.width_px * window.height_px // 4  # 576 pixels of 2304
    region = (0, 0, 24, 24)  # 576 pixels, inside one window placement
    assert 24 * 24 == quarter
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]
    segments, _ = _segments(_strobe(stamps, region))
    assert segments == [], segments


def test_flashing_over_a_24_by_25_block_more_than_a_quarter_fails():
    """600 of 2304 pixels, 24 more than a quarter. Kept as the plain case; the exact boundary
    is the two tests below."""
    region = (0, 0, 24, 25)  # 600 pixels, more than 576
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]
    segments, _ = _segments(_strobe(stamps, region))
    assert len(segments) == 1
    assert segments[0]["area_fraction"] == pytest.approx(600 / 2304, abs=1e-6)
    assert segments[0]["area_window"] == "wcag-10deg"


def _strobe_with_extra_pixel(stamps: list[float], region: tuple[int, int, int, int], extra: tuple[int, int] | None):
    """The region flashes, plus one more pixel just outside it when `extra` is given."""
    frames = []
    for index, stamp in enumerate(stamps):
        level = BRIGHT if index % 2 else DARK
        frame = _frame(index, stamp, level, region)
        if extra is not None:
            row, col = extra
            frame.rgb[row, col, :] = level
            frame.video_level[row, col] = level
        frames.append(frame)
    return frames


def test_exactly_576_of_the_2304_window_pixels_flashing_is_a_quarter_and_passes():
    """The WCAG window on the 192 by 108 working frame is 64 by 36, 2304 pixels. A 24 by 24
    block is 576 of them: exactly 25%, which is not "more than" 25%. max_coverage sums a 0/1
    mask through float64 integral images, so 576 and 577 are exact, and nothing here is
    resampled: these are working-frame pixels, which is the layer the rule is applied at."""
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]
    segments, _ = _segments(_strobe_with_extra_pixel(stamps, (0, 0, 24, 24), None))
    assert 24 * 24 == 576 and 64 * 36 == 2304 and 576 / 2304 == 0.25
    assert segments == [], segments


def test_577_of_the_2304_window_pixels_flashing_is_more_than_a_quarter_and_fails():
    """The same block plus one pixel at (24, 0), still inside one placement of the 64 by 36
    window: 577 / 2304, which is 0.2504, more than a quarter."""
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]
    segments, _ = _segments(_strobe_with_extra_pixel(stamps, (0, 0, 24, 24), (24, 0)))
    assert len(segments) == 1, segments
    assert segments[0]["area_fraction"] == pytest.approx(577 / 2304, abs=5e-7)  # the map rounds to six decimals
    assert segments[0]["area_fraction"] > 0.25
    assert segments[0]["area_window"] == "wcag-10deg"


def test_max_coverage_reads_a_quarter_as_a_quarter():
    mask = np.zeros((36, 64), dtype=bool)
    mask[:24, :24] = True
    assert max_coverage(mask, 36, 64) == pytest.approx(0.25)
    mask[24, 0] = True
    assert max_coverage(mask, 36, 64) > 0.25


# ---- the hidden interval over time ----------------------------------------------------------


def test_the_hidden_interval_lasts_until_the_fourth_flash_ages_out_of_the_window():
    """Flashes complete at 1100, 1400, 1700 and 2000 ms, then the picture is calm. The trailing
    window still holds four flashes at every frame up to 2100 ms ([1100, 2100] keeps the first),
    and three from 2150 ms on, so the hide runs from 1000 ms (one second before the fourth
    flash) to 2100 ms: not to the last flash at 2000, and not to the end of the file."""
    stamps = [1000, 1050, 1100, 1250, 1400, 1550, 1700, 1850, 2000]  # flashes at 1100, 1400, 1700, 2000
    frames = _strobe(stamps)
    index = len(frames)
    for stamp in range(2050, 3001, 50):
        frames.append(_frame(index, float(stamp), DARK))
        index += 1
    segments, _ = _segments(frames)
    [segment] = segments
    assert segment["start_ms"] == pytest.approx(1000.0)
    assert segment["end_ms"] == pytest.approx(2100.0)
    assert segment["flash_first_ms"] == pytest.approx(1100.0)
    assert segment["flash_last_ms"] == pytest.approx(2000.0)


def test_the_hidden_interval_cannot_start_before_the_file_does():
    """Four flashes in the first second: the hide starts at 0, not at a negative time."""
    stamps = [0, 50, 100, 200, 300, 400, 500, 600, 700]  # flashes at 100, 300, 500, 700
    segments, _ = _segments(_strobe(stamps))
    [segment] = segments
    assert segment["start_ms"] == 0.0
    assert segment["end_ms"] >= 700.0


# ---- red and general flashes are two tallies ------------------------------------------------


RED = (1.0, 0.0, 0.0)
# sRGB 0.5 grey has a relative luminance of 0.214, within 0.002 of pure red's 0.2126: a swing
# between the two is far under the 10% that makes a general flash, while the red ratio goes
# from 1.0 to 1/3 and the chromaticity moves 0.259 in the CIE 1976 UCS diagram, which is a
# red transition under WCAG 2.2 Note 3.
GREY_LIKE_RED = (0.5, 0.5, 0.5)


def _colour_frame(index: int, pts_ms: float, rgb: tuple[float, float, float]) -> AnalysisFrame:
    array = np.zeros((H, W, 3), dtype=np.float32)
    array[:] = rgb
    return AnalysisFrame(index=index, pts_ms=float(pts_ms), rgb=array, video_level=array[:, :, 1].copy())


def _red_strobe(stamps: list[float]) -> list[AnalysisFrame]:
    """Grey, red, grey, red... so a red flash completes on every second grey frame."""
    return [_colour_frame(index, stamp, RED if index % 2 else GREY_LIKE_RED) for index, stamp in enumerate(stamps)]


def test_four_red_flashes_in_a_second_are_a_red_segment_and_not_a_general_one():
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1100]  # red flashes complete at 100, 433, 767, 1100
    segments, _ = _segments(_red_strobe(stamps))
    assert [segment["reason"] for segment in segments] == ["red"], segments
    assert segments[0]["max_flashes_in_window"] == 4


def test_two_red_and_two_general_flashes_in_a_second_are_two_tallies_of_two_and_pass():
    """WCAG counts "no more than three general flashes and / or no more than three red
    flashes": two separate tallies. Two of each inside one second is two and two, not four."""
    # Two general flashes (dark, bright, dark, bright, dark) complete at 100 and 300 ms; the
    # picture then sits on grey, and two red flashes complete at 650 and 900 ms.
    frames = _strobe([0, 50, 100, 200, 300])
    tail = [(400, GREY_LIKE_RED), (520, RED), (650, GREY_LIKE_RED), (780, RED), (900, GREY_LIKE_RED), (950, GREY_LIKE_RED)]
    frames += [_colour_frame(10 + index, stamp, rgb) for index, (stamp, rgb) in enumerate(tail)]
    segments, _ = _segments(frames)
    assert segments == [], segments


# ---- a single pass, not a loop ---------------------------------------------------------------


def test_a_single_pass_does_not_count_flashes_across_a_loop_seam():
    """Two flashes in the last half second and two in the first: a player that loops the clip
    would show four inside one second across the seam, and the analyzer reports none, because
    it reads one pass from first frame to last. This pins the limitation; it is not loop safety."""
    head = [0, 50, 100, 200, 300]  # flashes at 100 and 300
    tail = [1700, 1750, 1800, 1900, 2000]  # flashes at 1800 and 2000, file ends at 2000
    frames = _strobe(head)
    frames += [_frame(10 + index, stamp, DARK) for index, stamp in enumerate(range(400, 1700, 100))]
    offset = len(frames)
    frames += [_frame(offset + index, stamp, BRIGHT if index % 2 else DARK) for index, stamp in enumerate(tail)]
    segments, analyzer = _segments(frames)
    assert analyzer.last_pts_ms == pytest.approx(2000.0)
    assert segments == [], segments


# ---- data the detector must not be fooled by -----------------------------------------------------


def test_a_frame_of_nan_neither_crashes_the_tracker_nor_counts_as_a_flash():
    stamps = [0, 50, 100, 300, 433, 600, 767, 900, 1101]
    frames = _strobe(stamps)
    bad = _frame(99, 1000.0, DARK)
    bad.rgb[:] = np.nan
    frames.insert(8, bad)
    segments, analyzer = _segments(frames)
    assert analyzer.frame_count == len(stamps) + 1
    assert segments == []


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not on PATH")
def test_an_audio_only_file_is_refused_as_having_no_video_stream(tmp_path: Path):
    path = tmp_path / "silence.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", "1", "-c:a", "aac", str(path)], check=True)
    with pytest.raises(UnsupportedInput, match="no video stream"):
        probe(path)


def test_an_empty_file_is_refused_rather_than_measured(tmp_path: Path):
    path = tmp_path / "empty.mp4"
    path.write_bytes(b"")
    with pytest.raises(UnsupportedInput):
        probe(path)


def test_a_file_of_noise_is_refused_rather_than_measured(tmp_path: Path):
    path = tmp_path / "noise.mp4"
    path.write_bytes(bytes(range(256)) * 64)
    with pytest.raises(UnsupportedInput):
        probe(path)
