"""What the camera meter counts, and what it refuses to count.

These are the unit tests. The guards, and the mutations that were watched going red, are in
test_meter_guards.py.

Nothing here decodes a video. Frames are made with numpy, so the whole file runs in a second and
CI never has to encode anything.
"""

from __future__ import annotations

import numpy as np
import pytest

import meter
from conformance.spec import SPEC_PATH, load_spec

SPEC = load_spec()
FULL_FRAME = meter.Roi(0.0, 0.0, 1.0, 1.0, method="explicit")


def grey_frame(code: int, height: int = 36, width: int = 64) -> np.ndarray:
    return np.full((height, width, 3), code, dtype=np.uint8)


def square_wave(hz: float, fps: int, seconds: float, low: int = 40, high: int = 230):
    """(frame, time_ms) pairs for a full field strobe, the way a display would show it."""
    for index in range(int(round(fps * seconds))):
        seconds_in = index / fps
        high_now = int(seconds_in * hz * 2) % 2 == 1
        yield grey_frame(high if high_now else low), seconds_in * 1000.0


def run(frames, roi=FULL_FRAME, calibration=None, settings=None, spec=None) -> meter.Meter:
    settings = settings or meter.InstrumentSettings(analysis_width=32)
    return meter.run_frames(
        frames, roi=roi, calibration=calibration, settings=settings, spec=spec
    )


# ---------------------------------------------------------------- counting


@pytest.mark.parametrize("hz", [1, 2, 3, 4, 5, 6, 10, 12])
def test_the_peak_rate_is_the_rate_that_was_played(hz):
    report = run(square_wave(hz, 240, 3.0)).report()
    assert report.general["peak_per_second"] == hz


@pytest.mark.parametrize("hz,expected", [(1, False), (3, False), (4, True), (10, True)])
def test_the_verdict_turns_over_at_the_spec_limit(hz, expected):
    report = run(square_wave(hz, 240, 3.0)).report()
    assert report.headline["above_limit"] is expected
    assert report.headline["limit_per_second"] == SPEC.flash_limit_per_second


def test_one_edge_seen_as_two_steps_is_still_one_transition():
    """The camera bug that the validation found: an exposure window across an edge.

    A camera whose shutter is open while the screen changes records the middle of the change.
    Pairing that middle step as a transition of its own turns one flash into two, and a 6 Hz
    strobe was read as 12 flashes a second before this was fixed.
    """

    def smeared():
        previous = None
        for frame, time_ms in square_wave(6, 240, 3.0):
            value = int(frame[0, 0, 0])
            if previous is not None and value != previous:
                middle = (value + previous) // 2
                yield grey_frame(middle), time_ms - 2.0
            yield frame, time_ms
            previous = value

    assert run(smeared()).report().general["peak_per_second"] == 6


def test_a_slow_fade_is_not_flashing():
    frames = (
        (grey_frame(int(40 + (230 - 40) * index / 719)), index / 240 * 1000.0)
        for index in range(720)
    )
    report = run(frames).report()
    assert report.general["flashes"] == 0
    assert report.headline["leaks"] == 0


def test_a_swing_under_the_general_threshold_is_not_counted():
    """Two grays whose relative luminance differs by less than the spec's minimum."""
    low, high = 128, 145
    delta = SPEC.luminance_of_srgb8((high, high, high)) - SPEC.luminance_of_srgb8(
        (low, low, low)
    )
    assert 0 < delta < SPEC.general_min_delta, delta
    report = run(square_wave(8, 240, 2.0, low=low, high=high)).report()
    assert report.general["flashes"] == 0


def test_a_swing_over_the_general_threshold_is_counted():
    low, high = 128, 190
    delta = SPEC.luminance_of_srgb8((high, high, high)) - SPEC.luminance_of_srgb8(
        (low, low, low)
    )
    assert delta > SPEC.general_min_delta, delta
    report = run(square_wave(8, 240, 2.0, low=low, high=high)).report()
    assert report.general["peak_per_second"] == 8


def test_two_bright_states_are_not_a_flash():
    """The darker image has to be below the spec's ceiling, and both of these are above it."""
    low, high = 240, 255
    assert SPEC.luminance_of_srgb8((low, low, low)) > SPEC.general_dark_image_below
    report = run(square_wave(8, 240, 2.0, low=low, high=high)).report()
    assert report.general["flashes"] == 0


# ---------------------------------------------------------------- the area rule


def patch_wave(hz: float, fps: int, seconds: float, side_fraction: float):
    height, width = 72, 128
    side_w = max(1, int(round(width * side_fraction)))
    side_h = max(1, int(round(height * side_fraction)))
    y0 = (height - side_h) // 2
    x0 = (width - side_w) // 2
    for index in range(int(round(fps * seconds))):
        seconds_in = index / fps
        high = int(seconds_in * hz * 2) % 2 == 1
        frame = np.full((height, width, 3), 40, dtype=np.uint8)
        frame[y0 : y0 + side_h, x0 : x0 + side_w] = 230 if high else 40
        yield frame, seconds_in * 1000.0


def test_a_strobe_too_small_for_a_ten_degree_window_is_not_counted():
    """A square of side 1/8 of the picture fills (3/8)^2 of the window, under the area limit."""
    settings = meter.InstrumentSettings(analysis_width=96)
    report = run(patch_wave(8, 240, 2.0, 0.125), settings=settings).report()
    assert report.general["flashes"] == 0
    assert report.headline["above_limit"] is False


def test_the_same_strobe_at_half_the_picture_is_counted():
    settings = meter.InstrumentSettings(analysis_width=96)
    report = run(patch_wave(8, 240, 2.0, 0.5), settings=settings).report()
    assert report.general["peak_per_second"] == 8


def test_the_window_coverage_is_the_busiest_position_not_the_average():
    mask = np.zeros((30, 30), dtype=bool)
    mask[0:10, 0:10] = True
    assert meter.max_window_coverage(mask, 10, 10) == pytest.approx(1.0)
    assert meter.max_window_coverage(mask, 30, 30) == pytest.approx(100 / 900)


# ---------------------------------------------------------------- red


def red_wave(hz: float, fps: int, seconds: float, other=(128, 128, 128), red=(255, 0, 0)):
    for index in range(int(round(fps * seconds))):
        seconds_in = index / fps
        colour = red if int(seconds_in * hz * 2) % 2 else other
        frame = np.zeros((36, 64, 3), dtype=np.uint8)
        frame[:, :] = colour
        yield frame, seconds_in * 1000.0


def test_red_against_gray_is_counted_by_the_red_rule():
    report = run(red_wave(6, 240, 2.0)).report()
    assert report.red["peak_per_second"] == 6
    # Mid gray and pure red sit within a hundredth of each other in relative luminance, so the
    # general rule has nothing to say here. That is what makes this a red only test.
    assert report.general["flashes"] == 0


def test_blue_against_gray_is_not_a_red_flash():
    report = run(red_wave(6, 240, 2.0, red=(0, 0, 255))).report()
    assert report.red["flashes"] == 0


def test_a_dull_red_is_not_a_saturated_red():
    dull = (150, 90, 90)
    linear = meter._linear_from_srgb8(SPEC, np.asarray(dull, dtype=np.float64))
    ratio = float(linear[0] / linear.sum())
    assert ratio < SPEC.red_saturated_ratio
    assert run(red_wave(6, 240, 2.0, red=dull)).report().red["flashes"] == 0


# ---------------------------------------------------------------- leaks


def test_one_strobe_is_one_leak():
    report = run(square_wave(8, 240, 3.0)).report()
    assert report.headline["leaks"] == 1
    assert len(report.leak_events) == 1


def test_two_strobes_with_a_quiet_gap_are_two_leaks():
    def two_bursts():
        time_ms = 0.0
        for _burst in range(2):
            for frame, offset in square_wave(8, 240, 1.5):
                yield frame, time_ms + offset
            time_ms += 1500.0
            for index in range(240 * 3):  # three quiet seconds
                yield grey_frame(40), time_ms + index / 240 * 1000.0
            time_ms += 3000.0

    report = run(two_bursts()).report()
    assert report.headline["leaks"] == 2


def test_a_covered_screen_reads_zero():
    frames = ((grey_frame(24), index / 240 * 1000.0) for index in range(480))
    report = run(frames).report()
    assert report.headline["peak_flashes_per_second"] == 0
    assert report.headline["leaks"] == 0
    assert report.headline["above_limit"] is False


# ---------------------------------------------------------------- the screen region


def scene_with_a_screen(code: int = 200, noise: float = 0.0, seed: int = 1) -> np.ndarray:
    frame = np.full((108, 192, 3), 12, dtype=np.uint8)
    frame[20:88, 30:160] = code
    if noise:
        rng = np.random.default_rng(seed)
        frame = np.clip(
            frame.astype(np.float64) + rng.normal(0, noise, frame.shape), 0, 255
        ).astype(np.uint8)
    return frame


def test_the_screen_region_is_found_inside_the_lit_rectangle():
    frames = [scene_with_a_screen(noise=2.0, seed=index) for index in range(6)]
    roi = meter.find_roi(frames)
    y0, y1, x0, x1 = roi.pixels(108, 192)
    assert 20 <= y0 and y1 <= 88
    assert 30 <= x0 and x1 <= 160
    assert roi.method == "otsu-profile"


def test_a_step_chart_does_not_fool_the_region_finder():
    """Half the chart is dark. A rule that wanted every column lit would keep the white half."""
    frame = np.full((108, 192, 3), 12, dtype=np.uint8)
    chart = meter.step_chart_image(130, 68, 10)
    frame[20:88, 30:160] = chart
    roi = meter.find_roi([frame, frame])
    _, _, x0, x1 = roi.pixels(108, 192)
    assert x1 - x0 > 100, "the region finder kept only part of the chart"


def test_a_frame_with_no_screen_in_it_is_refused():
    flat = [np.full((60, 80, 3), 90, dtype=np.uint8) for _ in range(4)]
    with pytest.raises(meter.RoiError):
        meter.find_roi(flat)


def test_a_screen_that_fills_the_whole_frame_is_refused():
    """With no room visible around the TV there is nothing to tell a screen from a wall.

    This test exists because the guard it covers survived its first mutation. The flat frame
    test above never reached it: a frame where every pixel is identical is refused one check
    earlier, so raising the area ceiling to 99 broke nothing and the suite stayed green. This
    frame has structure, so it gets past the first check and has to be stopped by the second.
    """
    rng = np.random.default_rng(11)
    frames = [
        np.clip(
            np.full((120, 160, 3), 215, dtype=np.float64) + rng.normal(0, 3, (120, 160, 3)),
            0,
            255,
        ).astype(np.uint8)
        for _ in range(4)
    ]
    with pytest.raises(meter.RoiError, match="over the"):
        meter.find_roi(frames)


def test_a_screen_too_small_to_be_a_tv_is_refused():
    frame = np.full((120, 200, 3), 8, dtype=np.uint8)
    frame[60:64, 100:106] = 240
    with pytest.raises(meter.RoiError, match="under the"):
        meter.find_roi([frame, frame])


# ---------------------------------------------------------------- calibration


def filmed_chart(
    gain: float = 0.8,
    flare: float = 0.01,
    gamma: float = 2.2,
    steps: int = 10,
    height: int = 120,
    width: int = 200,
    noise: float = 0.0,
    seed: int = 3,
) -> list[np.ndarray]:
    """A step chart seen through a camera with a known gain, flare and encoding gamma."""
    chart = meter.step_chart_image(width, height, steps)
    linear = meter._linear_from_srgb8(SPEC, chart.astype(np.float64))
    sensor = np.clip(linear * gain + flare, 0.0, 1.0)
    encoded = np.clip(np.round(255.0 * sensor ** (1.0 / gamma)), 0, 255)
    if noise:
        rng = np.random.default_rng(seed)
        encoded = np.clip(encoded + rng.normal(0, noise, encoded.shape), 0, 255)
    return [encoded.astype(np.uint8)]


def test_the_calibration_recovers_the_camera_it_was_filmed_with():
    calibration = meter.calibrate(filmed_chart(), FULL_FRAME, steps=10)
    assert calibration.usable_patches == 10
    assert calibration.max_residual < 0.02
    assert calibration.r_squared > 0.999
    # White comes back as white, which is the whole point of the fit. x=170 is inside the last
    # patch: the chart's own border runs from x=180 to the edge.
    white = calibration.apply(np.asarray(filmed_chart()[0][60, 170], dtype=np.float64))
    assert float(meter._luminance(SPEC, white)) == pytest.approx(1.0, abs=0.03)


def test_a_clipped_chart_loses_its_bright_patches_and_says_so():
    calibration = meter.calibrate(filmed_chart(gain=1.6), FULL_FRAME, steps=10)
    assert calibration.usable_patches < 10
    assert calibration.saturation_luminance is not None


def test_a_chart_that_is_mostly_clipped_is_refused():
    with pytest.raises(meter.CalibrationError, match="survived clipping"):
        meter.calibrate(filmed_chart(gain=40.0), FULL_FRAME, steps=10)


def test_a_chart_read_in_the_wrong_place_is_refused():
    """Reading the chart off the right hand third: the patches stop increasing."""
    wrong = meter.Roi(0.62, 0.1, 0.98, 0.9, method="explicit")
    with pytest.raises(meter.CalibrationError, match="do not get brighter"):
        meter.calibrate(filmed_chart(), wrong, steps=10)


def test_a_camera_that_an_affine_fit_cannot_follow_is_refused():
    """A hard S curve, the kind a TV's contrast enhancement puts on the signal."""
    chart = meter.step_chart_image(200, 120, 10)
    linear = meter._linear_from_srgb8(SPEC, chart.astype(np.float64))
    bent = np.clip(linear**0.35, 0.0, 1.0)
    encoded = np.clip(np.round(255.0 * bent ** (1.0 / 2.2)), 0, 255).astype(np.uint8)
    with pytest.raises(meter.CalibrationError, match="worst patch"):
        meter.calibrate([encoded], FULL_FRAME, steps=10)


def test_a_calibrated_run_reads_the_luminance_that_was_displayed():
    """The reason the calibration exists: without it the numbers are the camera's, not the TV's."""
    settings = meter.InstrumentSettings(analysis_width=32)
    calibration = meter.calibrate(filmed_chart(), FULL_FRAME, steps=10)

    def filmed(code: int):
        linear = meter._linear_from_srgb8(SPEC, np.full((36, 64, 3), code, dtype=np.float64))
        sensor = np.clip(linear * 0.8 + 0.01, 0, 1)
        return np.clip(np.round(255 * sensor ** (1 / 2.2)), 0, 255).astype(np.uint8)

    frames = [(filmed(180), index * 4.0) for index in range(8)]
    calibrated = meter.run_frames(
        iter(frames), roi=FULL_FRAME, calibration=calibration, settings=settings
    )
    raw = meter.run_frames(iter(frames), roi=FULL_FRAME, settings=settings)
    displayed = SPEC.luminance_of_srgb8((180, 180, 180))
    assert calibrated.readings[-1].mean_luminance == pytest.approx(displayed, abs=0.02)
    assert abs(raw.readings[-1].mean_luminance - displayed) > 0.05


# ---------------------------------------------------------------- the gray field check


def test_a_still_gray_field_passes_the_flicker_check():
    frames = [grey_frame(128) for _ in range(32)]
    times = [index * 1000.0 / 240.0 for index in range(32)]
    result = meter.flicker_check(frames, times, FULL_FRAME)
    assert result["passes"] is True
    assert result["peak_to_peak"] == pytest.approx(0.0, abs=1e-9)


def test_a_pulsing_backlight_fails_the_flicker_check():
    times = [index * 1000.0 / 240.0 for index in range(64)]
    frames = [
        grey_frame(int(round(128 + 25 * np.sin(2 * np.pi * 60 * t / 1000.0))))
        for t in times
    ]
    result = meter.flicker_check(frames, times, FULL_FRAME)
    assert result["passes"] is False
    assert result["dominant_hz"] == pytest.approx(60.0, abs=5.0)


# ---------------------------------------------------------------- the report


def test_an_uncalibrated_run_is_not_publishable_and_says_why():
    report = run(square_wave(6, 240, 1.5)).report()
    assert report.publishable is False
    assert any("calibration" in w for w in report.quality["warnings"])


def test_a_calibrated_clean_run_is_publishable():
    calibration = meter.calibrate(filmed_chart(), FULL_FRAME, steps=10)
    report = run(square_wave(6, 240, 1.5), calibration=calibration).report()
    assert report.publishable is True


def test_the_report_carries_the_thresholds_and_where_they_came_from():
    report = run(square_wave(2, 240, 1.0)).report().as_dict()
    assert report["thresholds"]["source"].endswith("SPEC_SOURCES.md")
    assert report["thresholds"]["source_sha256"] == SPEC.source_sha256
    assert report["instrument"]["note"].startswith("Instrument tuning")


def test_the_trailing_window_counts_the_second_that_ends_now():
    times = [100.0, 300.0, 700.0, 1100.0]
    # (100, 1100]: the flash on the opening edge is out, the one on the closing edge is in.
    assert meter._count_in_window(times, 1100.0, 1000.0) == 3
    # (50, 1050]: the flash at 1100 has not happened yet.
    assert meter._count_in_window(times, 1050.0, 1000.0) == 3
    # (200, 1200]: the flash at 100 has fallen out of the back of the window.
    assert meter._count_in_window(times, 1200.0, 1000.0) == 3
    assert meter._count_in_window(times, 2200.0, 1000.0) == 0
    assert meter._peak_in_window(times, 1000.0) == 3


def test_six_flashes_a_second_are_six_and_not_seven():
    """Exactly periodic instants land on the window edge, where floating point decides."""
    times = [index * 1000.0 / 6.0 for index in range(13)]
    assert meter._peak_in_window(times, 1000.0) == 6


# ---------------------------------------------------------------- thresholds from the spec


def test_the_general_threshold_really_comes_from_the_spec_file(tmp_path):
    """Change the quoted number in the spec file and the meter changes with it.

    A threshold typed into meter.py would pass every other test in this file. This one it cannot
    pass, because the only thing that moves is the text in flashmap/docs/SPEC_SOURCES.md.
    """
    original = SPEC_PATH.read_text()
    edited = original.replace(
        "| 0.10 | a general flash transition", "| 0.50 | a general flash transition"
    )
    assert edited != original, "the spec table row moved; update this test"
    path = tmp_path / "SPEC_SOURCES.md"
    path.write_text(edited)
    strict = load_spec(str(path))
    assert strict.general_min_delta == 0.5

    # A swing of about 0.35 in relative luminance: a flash under the real threshold, and not one
    # under the edited threshold.
    frames = list(square_wave(6, 240, 2.0, low=90, high=190))
    assert run(iter(frames)).report().general["flashes"] > 0
    assert run(iter(frames), spec=strict).report().general["flashes"] == 0
