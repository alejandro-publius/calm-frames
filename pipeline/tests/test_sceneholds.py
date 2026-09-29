"""Scene continuity on benign footage and sham intervals, never hazardous playback."""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import pytest

from pipeline import PipelineError
from pipeline.catalog import kid_mode_titles
from pipeline.flashmap_adapter import FlashmapAdapter, MapSegment
from pipeline.hideplan import CoverInterval, HidePlan, build_cover_intervals, is_calm
from pipeline.ingest import IngestOptions, ingest_title
from pipeline.probe import probe_video
from pipeline.registry import canonical_bytes, load_private_key, load_public_key
from pipeline.registry import sign_document, write_registry
from pipeline.render import cover_psnr, render_cover_model, render_safe_master
from pipeline.sceneholds import (
    MAX_HOLDS,
    MAX_IMAGE_BYTES,
    MAX_IMAGE_STRINGS,
    extract_exact_frame,
    image_dimensions,
    preceding_frame_ms,
    read_scene_holds,
    scene_payload,
    validate_jpeg,
)
from pipeline.verify import verify_title

from .clips import make_calm_clip
from .conftest import needs_ffmpeg


def test_preceding_frame_respects_every_preset_and_the_calm_margin():
    target = CoverInterval(7000, 8500)
    union = [CoverInterval(4500, 6000), target]
    probe = SimpleNamespace(frame_timestamps_s=[0.0, 1.0, 2.0, 3.0, 4.0, 4.5, 5.5, 6.5, 7.0])
    assert preceding_frame_ms(target, union, probe, margin_ms=500) == 3000


def test_no_preceding_context_in_the_lookback_uses_neutral():
    target = CoverInterval(7000, 8500)
    probe = SimpleNamespace(frame_timestamps_s=[0.0, 1.0, 6.5, 7.0])
    assert preceding_frame_ms(target, [target], probe, margin_ms=1000) is None
    assert preceding_frame_ms(CoverInterval(0, 1500), [], probe, margin_ms=1000) is None


def test_portrait_and_landscape_images_fit_the_wire_bounds():
    assert image_dimensions(SimpleNamespace(width=480, height=1920)) == (320, 1280)
    assert image_dimensions(SimpleNamespace(width=3840, height=2160)) == (640, 360)


def test_jpeg_envelope_rejects_unbounded_or_fake_image_data():
    for raw in (b"not a JPEG", b"\xff\xd8\xff\xd9", b"x" * (MAX_IMAGE_BYTES + 1)):
        with pytest.raises(PipelineError):
            validate_jpeg(raw)


@pytest.fixture
def built_scenes(tmp_path, analyzer, keypair):
    private, public = keypair
    source = make_calm_clip(tmp_path / "story.mp4", seconds=10, subtitles=True)
    analyzer.flag("story.mp4", segments={"wcag": [[3000, 4000, "general"], [8000, 8500, "red"]]})
    result = ingest_title(source, tmp_path / "out", IngestOptions(
        presets=["wcag"], key=str(private), pub=str(public),
        x264_preset="ultrafast", poster_count=1, bif_interval_ms=3000,
    ))
    assert result.verify_passed, result.verify_report
    return result, source, private, public


@needs_ffmpeg
def test_two_intervals_use_different_preceding_images_with_the_same_signed_schedule(built_scenes):
    result, source, _, public = built_scenes
    layout = result.layout
    document = json.loads(layout.map_path("wcag").read_text())
    load_public_key(public).verify(base64.b64decode(document["signature"]["value"]), canonical_bytes(document))
    assert document["segments"][0]["start_ms"] == 3000
    assert document["segments"][1]["end_ms"] == 8500
    plan = HidePlan.from_dict(json.loads(layout.plan_path("wcag").read_text()))
    images = read_scene_holds(layout, "wcag")
    assert [(i.start_ms, i.end_ms) for i in plan.intervals] == [(2500, 4500), (7500, 9000)]
    assert len(images) == 2
    assert images[0].sha256 != images[1].sha256
    assert images[0].frame_ms < images[1].frame_ms
    for interval, image in zip(plan.intervals, images):
        assert image.frame_ms < interval.start_ms
        assert is_calm(plan.intervals, image.frame_ms, margin_ms=1000)
        assert interval.start_ms - image.frame_ms <= 5000
        time_s = (interval.start_ms + interval.end_ms) / 2000
        assert cover_psnr(layout.safe_master("wcag"), image.path, time_s=time_s) >= 30
        assert cover_psnr(layout.cover_model_path("wcag"), image.path, time_s=time_s) >= 30
        with pytest.raises(PipelineError):
            validate_jpeg(image.path.read_bytes()[:-2] + b"x" * MAX_IMAGE_BYTES + b"\xff\xd9")
    assert document["scene_holds"] == scene_payload(images)
    assert len(document["scene_holds"]["holds"]) <= MAX_HOLDS
    assert sum(len(h["image_data_uri"]) for h in document["scene_holds"]["holds"]) <= MAX_IMAGE_STRINGS
    checks = {c["name"]: c["passed"] for c in result.verify_report["checks"]}
    assert checks["hls_rendition_clean:wcag"]
    assert checks["hls_timing_matches_master:wcag"]
    assert checks["scene_hls_drawn:wcag"]


@needs_ffmpeg
def test_decoder_returns_exact_source_pts_instead_of_rounding_a_seek_forward(tmp_path):
    source = make_calm_clip(tmp_path / "pts.mp4", seconds=2, audio=False)
    probe = probe_video(source)
    target = probe.frame_timestamps_s[17] * 1000
    assert abs(extract_exact_frame(source, target, tmp_path / "exact.jpg", probe) - target) < 0.001
    with pytest.raises(PipelineError):
        extract_exact_frame(source, target + 15, tmp_path / "between.jpg", probe)


@needs_ffmpeg
@pytest.mark.parametrize("damage", ["missing_asset", "changed_asset", "changed_manifest", "changed_signed_image"])
def test_scene_integrity_failure_blocks_publication(built_scenes, damage):
    result, source, _, public = built_scenes
    layout = result.layout
    images = read_scene_holds(layout, "wcag")
    if damage == "missing_asset":
        images[0].path.unlink()
    elif damage == "changed_asset":
        images[0].path.write_bytes(images[1].path.read_bytes())
    elif damage == "changed_manifest":
        manifest = json.loads(layout.scene_manifest("wcag").read_text())
        manifest["holds"][0]["frame_ms"] = manifest["holds"][0]["start_ms"] + 1
        layout.scene_manifest("wcag").write_text(json.dumps(manifest))
    else:
        document = json.loads(layout.map_path("wcag").read_text())
        document["scene_holds"]["holds"][0]["image_data_uri"] = document["scene_holds"]["holds"][1]["image_data_uri"]
        layout.map_path("wcag").write_text(json.dumps(document))
    report = verify_title(layout, source=source, presets=["wcag"], adapter=FlashmapAdapter(),
                          pub_key=public, rerender_cover_model=False)
    assert not report.passed
    assert "scene_assets:wcag" in [c.name for c in report.failures]


@needs_ffmpeg
def test_same_path_asset_tamper_cannot_reuse_a_cached_publishing_verdict(built_scenes):
    result, source, private, public = built_scenes
    images = read_scene_holds(result.layout, "wcag")
    images[0].path.write_bytes(images[1].path.read_bytes())
    with pytest.raises(PipelineError):
        ingest_title(source, result.layout.workdir, IngestOptions(
            presets=["wcag"], key=str(private), pub=str(public),
            x264_preset="ultrafast", poster_count=1, bif_interval_ms=3000,
        ))
    assert kid_mode_titles(result.layout.index_path) == []


@needs_ffmpeg
def test_valid_signature_cannot_paper_over_a_false_source_frame_timestamp(built_scenes):
    result, source, private, public = built_scenes
    layout = result.layout
    manifest = json.loads(layout.scene_manifest("wcag").read_text())
    manifest["holds"][0]["frame_ms"] = 0
    layout.scene_manifest("wcag").write_text(json.dumps(manifest))
    document = json.loads(layout.map_path("wcag").read_text())
    document["scene_holds"]["holds"][0]["frame_ms"] = 0
    write_registry(sign_document(document, load_private_key(private)), layout.map_path("wcag"))
    report = verify_title(layout, source=source, presets=["wcag"], adapter=FlashmapAdapter(),
                          pub_key=public, rerender_cover_model=False)
    assert "scene_assets:wcag" in [c.name for c in report.failures]
    detail = next(c.detail for c in report.failures if c.name == "scene_assets:wcag")
    assert "provenance" in detail


@needs_ffmpeg
def test_a_title_starting_covered_uses_signed_neutral_and_restarts_without_work(
    tmp_path, analyzer, keypair, ffmpeg_calls
):
    private, public = keypair
    source = make_calm_clip(tmp_path / "start.mp4", seconds=8)
    analyzer.flag("start.mp4", segments={"wcag": [[0, 1000, "red"]]})
    options = IngestOptions(presets=["wcag"], key=str(private), pub=str(public),
                            x264_preset="ultrafast", poster_count=1, bif_interval_ms=3000)
    first = ingest_title(source, tmp_path / "out", options)
    assert first.verify_passed, first.verify_report
    hold = read_scene_holds(first.layout, "wcag")[0]
    assert hold.start_ms == 0
    assert hold.frame_ms is None
    assert hold.origin == "neutral"
    document = json.loads(first.layout.map_path("wcag").read_text())
    assert document["scene_holds"]["holds"][0]["frame_ms"] is None
    load_public_key(public).verify(base64.b64decode(document["signature"]["value"]), canonical_bytes(document))
    ffmpeg_calls.clear()
    second = ingest_title(source, tmp_path / "out", options)
    assert second.steps_run == []
    assert "scene_holds:wcag" in second.steps_skipped
    assert "rendition:wcag" in second.steps_skipped
    assert "verify" in second.steps_skipped
    assert not ffmpeg_calls
    assert second.publishable
    assert kid_mode_titles(second.layout.index_path)


@needs_ffmpeg
@pytest.mark.parametrize("output,kind", [("safe.mp4", "safe"),
                                         ("cover_model_wcag.mp4", "model"),
                                         ("master.m3u8", "hls")])
def test_full_size_output_pattern_in_a_hold_blocks_publishing(built_scenes, analyzer, output, kind):
    result, source, _, public = built_scenes
    analyzer.flag(output, segments={"broadcast": [[3000, 4000, "pattern"]]})
    report = verify_title(result.layout, source=source, presets=["wcag"], adapter=FlashmapAdapter(),
                          pub_key=public, rerender_cover_model=False)
    assert not report.passed
    assert f"scene_output_patterns:{kind}:wcag" in [c.name for c in report.failures]


@needs_ffmpeg
def test_source_pattern_outside_the_holds_does_not_change_the_wcag_verdict(built_scenes, analyzer):
    result, source, _, public = built_scenes
    analyzer.flag("safe.mp4", segments={"broadcast": [[100, 500, "pattern"]]})
    report = verify_title(result.layout, source=source, presets=["wcag"], adapter=FlashmapAdapter(),
                          pub_key=public, rerender_cover_model=False)
    assert report.passed, [c.name for c in report.failures]


@needs_ffmpeg
@pytest.mark.parametrize("source_bounds,expected", [([3000, 4000], False), ([100, 500], True)])
def test_hls_pattern_intersection_subtracts_the_transport_pts_origin(built_scenes, analyzer, source_bounds, expected):
    result, source, _, public = built_scenes
    analyzer.set_geometry("master.m3u8", first_pts_ms=1500, last_pts_ms=4800)
    analyzer.flag("master.m3u8", segments={
        "broadcast": [[source_bounds[0] + 1500, source_bounds[1] + 1500, "pattern"]]
    })
    report = verify_title(result.layout, source=source, presets=["wcag"], adapter=FlashmapAdapter(),
                          pub_key=public, rerender_cover_model=False)
    check = next(c for c in report.checks if c.name == "scene_output_patterns:hls:wcag")
    assert check.passed is expected
    assert report.passed is expected, [c.name for c in report.failures]


@needs_ffmpeg
def test_runtime_black_fallback_is_also_the_rendition_and_model_fallback(tmp_path):
    source = make_calm_clip(tmp_path / "fallback.mp4", seconds=3, audio=False)
    probe = probe_video(source)
    intervals = build_cover_intervals([MapSegment(1000, 2000)], guard_band_ms=0)
    safe = tmp_path / "safe.mp4"
    model = tmp_path / "model.mp4"
    render_safe_master(source, intervals=intervals, still_path=tmp_path / "unused.png",
                       out_path=safe, probe=probe, scene_holds=[])
    plan = HidePlan("wcag", "a" * 64, 0, 400, probe.duration_ms, True, intervals)
    result = render_cover_model(source, plan=plan, out_path=model, probe=probe, scene_holds=[])
    assert result.notes["dim_spans"] == 0
    assert result.notes["opaque_spans"] == 1
    from pipeline.render import make_neutral_still
    black = tmp_path / "black.png"
    make_neutral_still(black, width=probe.width, height=probe.height, rgb=(0, 0, 0))
    assert cover_psnr(safe, black, time_s=1.5) >= 30
    assert cover_psnr(model, black, time_s=1.5) >= 30
