"""The two renders: the kid safe rendition and the cover model.

The ffmpeg tests here run on a generated calm clip of a few seconds. They
check the things a reviewer would want to see with their own eyes but which
nobody may look at on real content: that the covered span really shows the
still, that the sound and the captions came through untouched, and that a dim
cover takes the light down by the amount the plan promises.
"""

from __future__ import annotations

import json
import math
import subprocess

import pytest

from pipeline.flashmap_adapter import MapSegment
from pipeline.hideplan import HidePlan, build_cover_intervals
from pipeline.posters import luminance_series
from pipeline.probe import probe_video
from pipeline.render import (
    BT1886_GAMMA,
    SRGB_GAMMA,
    cover_psnr,
    enable_expression,
    extract_still,
    linear_dim_code_scale,
    package_hls,
    render_cover_model,
    render_safe_master,
    transfer_gamma,
)

from .clips import make_calm_clip
from .conftest import ffprobe_json, needs_ffmpeg


def seg(start, end, reason="general"):
    return MapSegment(start_ms=start, end_ms=end, reason=reason)


class FakeProbe:
    color_transfer = None


class TestEnableExpression:
    def test_one_span(self):
        intervals = build_cover_intervals([seg(1000, 2000)], guard_band_ms=0, min_cover_ms=0)
        assert enable_expression(intervals) == "between(t,1.000000,2.000000)"

    def test_spans_are_joined_with_a_plus_which_ffmpeg_reads_as_or(self):
        intervals = build_cover_intervals(
            [seg(1000, 2000), seg(5000, 6000)], guard_band_ms=0, min_cover_ms=0
        )
        assert enable_expression(intervals) == (
            "between(t,1.000000,2.000000)+between(t,5.000000,6.000000)"
        )

    def test_nothing_to_cover_gives_no_expression(self):
        assert enable_expression([]) is None


class TestDimIsModelledInLinearLight:
    def test_scaling_code_values_scales_light_by_alpha(self):
        alpha = 0.10
        scale = linear_dim_code_scale(alpha, BT1886_GAMMA)
        # Light out over light in, for a power law display.
        assert math.isclose(scale**BT1886_GAMMA, alpha, rel_tol=1e-9)

    def test_ten_percent_of_light_is_about_thirty_eight_percent_of_code_value(self):
        assert math.isclose(
            linear_dim_code_scale(0.10, BT1886_GAMMA), 0.3831, abs_tol=0.001
        )

    def test_a_naive_code_value_dim_would_leave_far_more_light(self):
        # Multiplying code values by 0.10 instead would leave 0.10 ** 2.4 of
        # the light, which is 250 times darker than asked for. The point of
        # doing this in linear light is that neither mistake is silent.
        naive_light = 0.10**BT1886_GAMMA
        assert naive_light < 0.005

    def test_untagged_files_use_the_brighter_and_so_stricter_gamma(self):
        probe = FakeProbe()
        assert transfer_gamma(probe) == BT1886_GAMMA
        assert linear_dim_code_scale(0.1, BT1886_GAMMA) > linear_dim_code_scale(
            0.1, SRGB_GAMMA
        )

    def test_srgb_content_uses_the_srgb_gamma(self):
        probe = FakeProbe()
        probe.color_transfer = "iec61966-2-1"
        assert transfer_gamma(probe) == SRGB_GAMMA

    def test_alpha_out_of_range_is_refused(self):
        with pytest.raises(ValueError):
            linear_dim_code_scale(0.0, BT1886_GAMMA)
        with pytest.raises(ValueError):
            linear_dim_code_scale(1.5, BT1886_GAMMA)


def yavg_at(path, time_s, tmp_path, name):
    series = luminance_series(
        path, metadata_path=tmp_path / f"{name}.txt", sample_fps=4
    )
    index = min(
        range(len(series.times_s)), key=lambda i: abs(series.times_s[i] - time_s)
    )
    return series.yavg[index]


@needs_ffmpeg
class TestSafeRendition:
    @pytest.fixture
    def rendered(self, tmp_path):
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0, subtitles=True)
        probe = probe_video(source)
        intervals = build_cover_intervals([seg(3000, 4000)], guard_band_ms=500)
        still = tmp_path / "still.png"
        extract_still(
            source, time_s=1.0, out_path=still, width=probe.width, height=probe.height
        )
        out = tmp_path / "safe.mp4"
        result = render_safe_master(
            source,
            intervals=intervals,
            still_path=still,
            out_path=out,
            probe=probe,
        )
        return {
            "source": source,
            "probe": probe,
            "intervals": intervals,
            "still": still,
            "safe": out,
            "result": result,
            "tmp": tmp_path,
        }

    def test_the_covered_span_shows_the_still(self, rendered):
        # 2.5 s to 4.5 s is covered: the flagged span plus the guard band.
        for time_s in (2.6, 3.5, 4.4):
            assert cover_psnr(rendered["safe"], rendered["still"], time_s=time_s) >= 30

    def test_the_guard_band_is_covered_too(self, rendered):
        # 2.7 s is inside the guard band, before the flagged span starts.
        assert cover_psnr(rendered["safe"], rendered["still"], time_s=2.7) >= 30

    def test_the_rest_of_the_title_is_not_covered(self, rendered):
        outside = cover_psnr(rendered["safe"], rendered["still"], time_s=7.0)
        assert outside < 30

    def test_the_audio_track_is_untouched(self, rendered):
        before = ffprobe_json(
            rendered["source"], "-select_streams", "a", "-show_streams"
        )["streams"]
        after = ffprobe_json(rendered["safe"], "-select_streams", "a", "-show_streams")[
            "streams"
        ]
        assert len(after) == len(before) == 1
        assert after[0]["codec_name"] == before[0]["codec_name"]
        assert after[0]["sample_rate"] == before[0]["sample_rate"]
        assert after[0]["channels"] == before[0]["channels"]
        assert abs(float(after[0]["duration"]) - float(before[0]["duration"])) < 0.2

    def test_the_caption_track_is_untouched(self, rendered):
        after = ffprobe_json(rendered["safe"], "-select_streams", "s", "-show_streams")[
            "streams"
        ]
        assert len(after) == 1
        cues = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(rendered["safe"]), "-f", "webvtt", "-"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "hello from the caption track" in cues
        assert "still talking" in cues

    def test_hls_packaging_keeps_the_audio_and_the_captions(self, rendered):
        hls = package_hls(
            rendered["safe"],
            out_dir=rendered["tmp"] / "hls",
            probe=rendered["probe"],
        )
        master = hls.path.read_text()
        assert "#EXT-X-STREAM-INF" in master
        assert "SUBTITLES" in master
        assert list((rendered["tmp"] / "hls").glob("*.ts"))
        assert list((rendered["tmp"] / "hls").glob("*.vtt"))

    def test_a_title_with_nothing_flagged_still_gets_a_rendition(self, tmp_path):
        source = make_calm_clip(tmp_path / "plain.mp4", seconds=4.0)
        probe = probe_video(source)
        out = tmp_path / "safe_plain.mp4"
        result = render_safe_master(
            source,
            intervals=[],
            still_path=tmp_path / "missing.png",
            out_path=out,
            probe=probe,
        )
        assert out.exists()
        assert result.notes["enable_expression"] is None


@needs_ffmpeg
class TestCoverModel:
    def test_a_general_span_is_dimmed_by_the_amount_the_plan_promises(self, tmp_path):
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0, audio=False)
        probe = probe_video(source)
        plan = HidePlan(
            profile="wcag",
            source_sha256="a" * 64,
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=probe.duration_ms,
            allow_dim=True,
            intervals=build_cover_intervals([seg(3000, 4000)], guard_band_ms=500),
        )
        out = tmp_path / "cover_model.mp4"
        result = render_cover_model(source, plan=plan, out_path=out, probe=probe)
        assert result.notes["dim_spans"] == 1
        assert result.notes["opaque_spans"] == 0

        before = yavg_at(source, 3.5, tmp_path, "before")
        after = yavg_at(out, 3.5, tmp_path, "after")
        # Limited range video puts black at 16, so the part that scales is
        # what sits above it.
        ratio = (after - 16.0) / (before - 16.0)
        expected = result.notes["dim_code_scale"]
        assert abs(ratio - expected) < 0.06, (before, after, ratio, expected)

    def test_a_red_span_is_covered_opaque_black_not_dimmed(self, tmp_path):
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0, audio=False)
        probe = probe_video(source)
        plan = HidePlan(
            profile="wcag",
            source_sha256="a" * 64,
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=probe.duration_ms,
            allow_dim=True,
            intervals=build_cover_intervals([seg(3000, 4000, "red")], guard_band_ms=500),
        )
        out = tmp_path / "cover_model.mp4"
        result = render_cover_model(source, plan=plan, out_path=out, probe=probe)
        assert result.notes["opaque_spans"] == 1
        assert result.notes["dim_spans"] == 0
        assert yavg_at(out, 3.5, tmp_path, "red") < 18.0

    def test_the_picture_outside_the_span_is_left_alone(self, tmp_path):
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0, audio=False)
        probe = probe_video(source)
        plan = HidePlan(
            profile="wcag",
            source_sha256="a" * 64,
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=probe.duration_ms,
            allow_dim=True,
            intervals=build_cover_intervals([seg(3000, 4000)], guard_band_ms=500),
        )
        out = tmp_path / "cover_model.mp4"
        render_cover_model(source, plan=plan, out_path=out, probe=probe)
        before = yavg_at(source, 7.0, tmp_path, "before_out")
        after = yavg_at(out, 7.0, tmp_path, "after_out")
        assert abs(after - before) < 2.0

    def test_dim_is_refused_for_red_even_when_the_house_allows_dim(self, tmp_path):
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=4.0, audio=False)
        probe = probe_video(source)
        plan = HidePlan(
            profile="wcag",
            source_sha256="a" * 64,
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=probe.duration_ms,
            allow_dim=True,
            intervals=build_cover_intervals(
                [seg(1000, 1500, "red"), seg(2500, 3000, "general")], guard_band_ms=100
            ),
        )
        result = render_cover_model(
            source, plan=plan, out_path=tmp_path / "model.mp4", probe=probe
        )
        assert result.notes["opaque_spans"] == 1
        assert result.notes["dim_spans"] == 1


@needs_ffmpeg
class TestProbe:
    def test_real_frame_timestamps_come_back(self, tmp_path):
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=2.0, fps=30, audio=False)
        probe = probe_video(source)
        assert probe.frame_count >= 55
        assert probe.frame_timestamps_s[0] == pytest.approx(0.0, abs=0.05)
        assert not probe.variable_frame_rate
        assert probe.frame_interval_median_s == pytest.approx(1 / 30, abs=0.002)

    def test_resolution_duration_and_streams(self, tmp_path):
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=3.0, subtitles=True)
        probe = probe_video(source)
        assert (probe.width, probe.height) == (320, 180)
        assert probe.duration_s == pytest.approx(3.0, abs=0.2)
        assert probe.has_audio
        assert probe.has_subtitles

    def test_the_probe_survives_json(self, tmp_path):
        from pipeline.probe import VideoProbe

        source = make_calm_clip(tmp_path / "clip.mp4", seconds=2.0)
        probe = probe_video(source)
        restored = VideoProbe.from_dict(json.loads(json.dumps(probe.to_dict())))
        assert restored.frame_timestamps_s == probe.frame_timestamps_s
        assert restored.audio_streams[0].codec_name == probe.audio_streams[0].codec_name
