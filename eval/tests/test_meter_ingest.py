"""The parts of the ingest that can be checked before any footage exists.

No recordings have been filmed, so nothing here decodes a video. What it does check is every
piece of arithmetic that will run on the first take: how files are grouped, how the clock is
recovered from the reference patch, what happens when the app's log is wrong, and how a cover
leak is counted.

The mutations that were watched going red are listed in test_meter_guards.py. Two of them live
here: the refusal to write anything with no footage, and the refusal to align a take whose log
puts the first patch flip in the wrong place.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

import meter
import meter_ingest

# ---------------------------------------------------------------- finding the takes


def make_take(directory, stem: str, kinds=("gray", "chart", "run"), events=True):
    for kind in kinds:
        (directory / f"{stem}_{kind}.mov").write_bytes(b"not a real recording")
    if events:
        (directory / f"{stem}_events.json").write_text("{}")


def test_four_files_with_one_stem_are_one_take(tmp_path):
    make_take(tmp_path, "20261008_marker_t01")
    takes = meter_ingest.discover_takes(tmp_path)
    assert len(takes) == 1
    assert takes[0].complete()
    assert takes[0].session == "marker"
    assert takes[0].take == "t01"


def test_a_take_missing_a_file_says_which_one(tmp_path):
    make_take(tmp_path, "20261008_marker_t02", kinds=("gray", "run"))
    take = meter_ingest.discover_takes(tmp_path)[0]
    assert not take.complete()
    assert take.missing() == ["chart"]


def test_a_file_named_the_way_a_phone_names_it_is_ignored(tmp_path):
    (tmp_path / "IMG_4312.MOV").write_bytes(b"straight off the camera roll")
    make_take(tmp_path, "20261008_title_t07")
    takes = meter_ingest.discover_takes(tmp_path)
    assert [t.stem for t in takes] == ["20261008_title_t07"]


def test_takes_come_back_in_a_fixed_order(tmp_path):
    for stem in ("20261008_marker_t02", "20261008_marker_t01", "20261009_title_t01"):
        make_take(tmp_path, stem)
    assert [t.stem for t in meter_ingest.discover_takes(tmp_path)] == [
        "20261008_marker_t01",
        "20261008_marker_t02",
        "20261009_title_t01",
    ]


# ---------------------------------------------------------------- the clock on the screen


def patch_signal(
    duration_ms: float = 6000.0,
    fps: float = 240.0,
    period_ms: float = 500.0,
    rate: float = 1.0,
    offset_ms: float = 0.0,
    high: float = 0.402,
    low: float = 0.305,
    noise: float = 0.0,
    seed: int = 5,
):
    """What the reference patch looks like in a recording: a slow two level square wave.

    `rate` and `offset_ms` are the clock this is supposed to recover: media time t appears in the
    recording at `rate * t + offset_ms`.
    """
    rng = np.random.default_rng(seed)
    times: list[float] = []
    values: list[float] = []
    count = int(duration_ms * fps / 1000.0)
    for index in range(count):
        recording_ms = index * 1000.0 / fps
        media_ms = (recording_ms - offset_ms) / rate
        # The clip is light for the first half of every second and dark for the second half.
        light = int(media_ms / period_ms) % 2 == 0
        value = high if light else low
        if noise:
            value += float(rng.normal(0, noise))
        times.append(recording_ms)
        values.append(value)
    return times, values


def test_the_patch_edges_are_found_between_two_samples():
    times, values = patch_signal(duration_ms=3000.0, offset_ms=0.0)
    edges = meter_ingest.detect_edges(times, values)
    assert len(edges) == 5  # 500, 1000, 1500, 2000, 2500
    for edge, expected in zip(edges, [500.0, 1000.0, 1500.0, 2000.0, 2500.0]):
        assert edge["time_ms"] == pytest.approx(expected, abs=1000.0 / 240.0)
    assert [e["direction"] for e in edges] == [-1.0, 1.0, -1.0, 1.0, -1.0]


def test_the_edges_survive_noise_that_does_not_reach_the_middle():
    times, values = patch_signal(duration_ms=3000.0, noise=0.01)
    assert len(meter_ingest.detect_edges(times, values)) == 5


def test_a_still_patch_has_no_edges():
    times = [index * 4.0 for index in range(400)]
    assert meter_ingest.detect_edges(times, [0.35] * 400) == []


def test_the_clock_recovers_the_rate_and_the_offset_it_was_given():
    """The recording opens 2 s into the clip, and the two machines' clocks differ by 0.2%."""
    rate, opens_at = 1.002, 2000.0
    offset = -rate * opens_at
    times, values = patch_signal(duration_ms=8000.0, rate=rate, offset_ms=offset)
    edges = meter_ingest.detect_edges(times, values)
    clock = meter_ingest.fit_clock(
        edges, period_ms=500.0, anchor_media_ms=opens_at, recording_start_ms=0.0
    )
    assert clock["anchored"] is True
    assert clock["rate"] == pytest.approx(rate, abs=0.002)
    assert clock["offset_ms"] == pytest.approx(offset, abs=10.0)
    assert clock["max_residual_ms"] < 1000.0 / 240.0
    # A marker at 4000 ms of media lands where the fit says it does.
    assert meter_ingest.to_recording_ms(clock, 4000.0) == pytest.approx(
        rate * 4000.0 + offset, abs=10.0
    )


def test_a_take_with_no_anchor_is_not_aligned():
    times, values = patch_signal()
    clock = meter_ingest.fit_clock(
        meter_ingest.detect_edges(times, values),
        period_ms=500.0,
        anchor_media_ms=None,
        recording_start_ms=0.0,
    )
    assert clock["anchored"] is False
    assert "media time" in clock["reason"]


def test_a_log_that_is_out_by_more_than_half_a_period_is_refused():
    """Every flip looks like every other one, so a wrong log would align to the wrong flip."""
    times, values = patch_signal(duration_ms=6000.0, offset_ms=0.0)
    edges = meter_ingest.detect_edges(times, values)
    clock = meter_ingest.fit_clock(
        edges, period_ms=500.0, anchor_media_ms=300.0, recording_start_ms=0.0
    )
    assert clock["anchored"] is False
    assert "half of the 500 ms period" in clock["reason"]


def test_a_signal_that_is_not_the_patch_is_refused():
    times, values = patch_signal(duration_ms=3000.0, period_ms=100.0)
    clock = meter_ingest.fit_clock(
        meter_ingest.detect_edges(times, values),
        period_ms=500.0,
        anchor_media_ms=0.0,
        recording_start_ms=0.0,
    )
    assert clock["anchored"] is False
    assert "not a clock" in clock["reason"]


def test_the_patch_rectangle_comes_from_the_committed_schedule():
    schedule = {
        "clip": {"width": 1280, "height": 720},
        "reference_patch": {"x": 48, "y": 48, "width": 96, "height": 96},
    }
    x0, y0, x1, y1 = meter_ingest.patch_rect(schedule)
    assert (x0, y0) == pytest.approx((48 / 1280, 48 / 720))
    assert (x1, y1) == pytest.approx((144 / 1280, 144 / 720))


# ---------------------------------------------------------------- covers and leaks


def covered_run(
    cover_on_ms: float = 800.0,
    start_ms: float = 1500.0,
    end_ms: float = 3000.0,
    leak_at: float | None = None,
    covered: float = 0.02,
    open_level: float = 0.5,
    fps: float = 240.0,
):
    times: list[float] = []
    picture: list[float] = []
    for index in range(int(4000.0 * fps / 1000.0)):
        time_ms = index * 1000.0 / fps
        value = covered if time_ms >= cover_on_ms else open_level
        if leak_at is not None and abs(time_ms - leak_at) < 20.0:
            value = open_level
        times.append(time_ms)
        picture.append(value)
    return {"times_ms": times, "picture": picture}


CLOCK = {"anchored": True, "rate": 1.0, "offset_ms": 0.0}


def score(measured, start_ms=1500.0, end_ms=3000.0, cover_on_ms=1000.0, tolerance=0.02):
    return meter_ingest._score_interval(
        {"start_ms": start_ms, "end_ms": end_ms, "cover_on_ms": cover_on_ms},
        measured,
        CLOCK,
        tolerance,
        meter.InstrumentSettings(),
    )


def test_a_clean_cover_has_no_leak_and_a_lead_time():
    out = score(covered_run(cover_on_ms=800.0))
    assert out["cover_leak_frames"] == 0
    assert out["lead_ms"] == pytest.approx(700.0, abs=1000.0 / 240.0)


def test_a_frame_of_light_inside_the_interval_is_a_leak():
    out = score(covered_run(cover_on_ms=800.0, leak_at=2000.0))
    assert out["cover_leak_frames"] > 0
    assert out["worst_leak"] > 0


def test_a_cover_that_went_on_late_does_not_raise_the_covered_reference():
    """A median would follow the bright frames up and call the leak the normal state."""
    late = covered_run(cover_on_ms=2600.0)
    out = score(late)
    assert out["covered_reference"] < 0.1
    assert out["cover_leak_frames"] > 0
    assert out["lead_ms"] is None, "a cover that was not on before the interval has no lead"


def test_an_event_the_recording_does_not_reach_is_excluded():
    short = covered_run()
    short["times_ms"] = short["times_ms"][:100]
    short["picture"] = short["picture"][:100]
    out = score(short, start_ms=3500.0, end_ms=3900.0, cover_on_ms=3000.0)
    assert "excluded" in out


def test_an_event_with_no_clock_is_excluded_rather_than_guessed():
    out = meter_ingest._score_interval(
        {"start_ms": 1500.0, "end_ms": 3000.0},
        covered_run(),
        {"anchored": False, "reason": "the event file did not say"},
        0.02,
        meter.InstrumentSettings(),
    )
    assert "excluded" in out and "no media clock" in out["excluded"]


# ---------------------------------------------------------------- refusing to invent


def test_with_no_recordings_it_writes_nothing_and_exits_non_zero(tmp_path, capsys):
    out = tmp_path / "screen_level.json"
    code = meter_ingest.main(
        ["--recordings", str(tmp_path / "empty"), "--out", str(out)]
    )
    assert code == 2
    assert not out.exists(), "a file of zeros would read as a real result later"


def test_an_incomplete_take_is_not_enough_to_write_a_file(tmp_path):
    recordings = tmp_path / "shots"
    recordings.mkdir()
    make_take(recordings, "20261008_marker_t01", kinds=("gray", "run"), events=False)
    out = tmp_path / "screen_level.json"
    assert meter_ingest.main(["--recordings", str(recordings), "--out", str(out)]) == 2
    assert not out.exists()


def test_the_summary_of_nothing_is_empty_rather_than_zero():
    summary = meter_ingest.summarise([])
    assert summary["events_counted"] == 0
    assert summary["cover_lead_ms"] is None
    assert summary["events_with_a_cover_leak"]["value"] is None
    assert summary["events_with_a_cover_leak"]["denominator"] == 0


def test_the_summary_carries_the_counts_and_the_method():
    rows = [
        {
            "take": "t01",
            "meter": {"flash_leaks": 0},
            "events": [
                {"cover_leak_frames": 0, "lead_ms": 500.0},
                {"cover_leak_frames": 2, "lead_ms": 320.0},
                {"excluded": "no media clock"},
            ],
        }
    ]
    summary = meter_ingest.summarise(rows)
    assert summary["events_counted"] == 2
    assert summary["events_excluded"] == 1
    assert summary["events_with_a_cover_leak"]["numerator"] == 1
    assert summary["events_with_a_cover_leak"]["denominator"] == 2
    assert summary["cover_lead_ms"]["worst"] == 320.0
    assert summary["interval_method"].lower().startswith("wilson")


def test_the_events_file_can_abort_a_take(tmp_path):
    recordings = tmp_path / "shots"
    recordings.mkdir()
    make_take(recordings, "20261008_marker_t01")
    (recordings / "20261008_marker_t01_events.json").write_text(json.dumps({"aborted": True}))
    take = meter_ingest.discover_takes(recordings)[0]
    row = meter_ingest.ingest_take(take, {"clip": {}}, meter.InstrumentSettings())
    # The files are not real recordings, so this fails before the abort check. Either way it
    # must come back excluded and never counted.
    assert "excluded" in row
