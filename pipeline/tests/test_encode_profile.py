"""Delivery encoding remains downstream of source maps and cover decisions.

No signing credentials or approved media are needed for these renderer tests.
"""
from pathlib import Path

import av
import pytest

from pipeline import PipelineError, ffmpegtool, local_library
from pipeline.flashmap_adapter import MapSegment
from pipeline.hideplan import build_cover_intervals
from pipeline.ingest import _Steps, build_parser
from pipeline.probe import probe_video
from pipeline.render import cover_psnr, encode_profile_settings, extract_still, render_safe_master
from pipeline.state import Ledger

from .clips import make_calm_clip
from .conftest import needs_ffmpeg


@pytest.fixture
def source720(tmp_path):
    return make_calm_clip(tmp_path / "source.mp4", seconds=2, width=1280, height=720)


def packets(path, kind):
    with av.open(str(path)) as container:
        return [(bytes(p), float(p.pts * p.time_base)) for p in container.demux()
                if p.stream.type == kind and p.pts is not None]


@needs_ffmpeg
def test_two_pass_repeatability_covers_audio_and_frame_timing(source720, tmp_path):
    probe = probe_video(source720)
    still = tmp_path / "still.png"
    extract_still(source720, time_s=0, out_path=still)
    intervals = build_cover_intervals([MapSegment(750, 1250, "general")],
                                     guard_band_ms=0, min_cover_ms=0)
    outputs = [tmp_path / "one.mp4", tmp_path / "two.mp4"]
    for path in outputs:
        render_safe_master(source720, intervals=intervals, still_path=still,
                           out_path=path, probe=probe, encode_profile="ambient-720p-v1")
        actual = probe_video(path)
        assert (actual.width, actual.height) == (probe.width, probe.height)
        assert actual.frame_timestamps_s == probe.frame_timestamps_s
        assert packets(path, "audio") == packets(source720, "audio")
        assert cover_psnr(path, still, time_s=1) >= 30
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    assert not list(tmp_path.glob(".encode-*"))


@needs_ffmpeg
def test_invalid_profile_and_size_are_refused_without_encoding(tmp_path, monkeypatch):
    source = make_calm_clip(tmp_path / "small.mp4", seconds=1)
    probe = probe_video(source)
    monkeypatch.setattr(ffmpegtool, "run_ffmpeg", lambda *a, **kw: pytest.fail("encoded"))
    for profile in ["unknown", "ambient-720p-v1"]:
        with pytest.raises(PipelineError):
            render_safe_master(source, intervals=[], still_path=source,
                               out_path=tmp_path / "out.mp4", probe=probe, encode_profile=profile)


@needs_ffmpeg
@pytest.mark.parametrize("failed_pass", [1, 2])
def test_failed_pass_cleans_private_logs_and_does_not_continue(source720, tmp_path, monkeypatch, failed_pass):
    calls = []

    def fail(args):
        number = int(args[args.index("-pass") + 1])
        calls.append(number)
        Path(args[args.index("-passlogfile") + 1] + "-0.log").write_text("test log")
        if number == failed_pass:
            raise PipelineError("simulated encoder failure")

    monkeypatch.setattr(ffmpegtool, "run_ffmpeg", fail)
    with pytest.raises(PipelineError, match="simulated"):
        render_safe_master(source720, intervals=[], still_path=source720,
                           out_path=tmp_path / "out.mp4", probe=probe_video(source720),
                           encode_profile="ambient-720p-v1")
    assert calls == list(range(1, failed_pass + 1))
    assert not list(tmp_path.glob(".encode-*"))


def test_receipt_wrapper_forwards_profile_but_never_skips_verification(tmp_path, monkeypatch):
    source = tmp_path / "source.bin"
    source.write_bytes(b"test only")
    key = tmp_path / "not-a-signing-key"
    key.write_text("inert placeholder, not a credential")
    seen = []

    def stop(source, workdir, options, **kwargs):
        seen.append(options)
        raise PipelineError("stop before signing")

    monkeypatch.setattr(local_library, "ingest_title", stop)
    result = local_library.prepare_local_title(source, tmp_path / "work", key=key, pub=key,
                                               encode_profile="ambient-720p-v1")
    assert result["status"] == "failed"
    assert seen[0].encode_profile == "ambient-720p-v1"
    assert seen[0].skip_verify is False
    assert seen[0].playback_compatible is True
    assert seen[0].presets == ["wcag", "broadcast", "extra-cautious"]
    args = build_parser().parse_args([str(source), "--workdir", str(tmp_path / "work"),
                                     "--encode-profile", "ambient-720p-v1"])
    assert args.encode_profile == "ambient-720p-v1"
    assert args.skip_verify is False


def test_profile_change_invalidates_rendition_and_dependent_verification(tmp_path):
    executed = []

    def run(profile):
        steps = _Steps(Ledger(tmp_path), force=False)
        for name, payload, parents in [
            ("rendition:wcag", {"encode_profile": encode_profile_settings(profile)}, []),
            ("verify", {}, ["rendition:wcag"]),
        ]:
            output = tmp_path / name.replace(":", "-")

            def work(name=name, output=output):
                executed.append(name)
                output.write_text("test artifact")

            steps.run(name, payload, [output], work, depends_on=parents)

    run("default")
    run("default")
    assert executed == ["rendition:wcag", "verify"]
    run("ambient-720p-v1")
    assert executed == ["rendition:wcag", "verify"] * 2


@needs_ffmpeg
@pytest.mark.parametrize("custom", [{"crf": 30}, {"x264_preset": "ultrafast"}, {"segment_seconds": 2}])
def test_fixed_profile_rejects_conflicting_overrides(source720, tmp_path, monkeypatch, custom):
    probe = probe_video(source720)
    monkeypatch.setattr(ffmpegtool, "run_ffmpeg", lambda *a, **kw: pytest.fail("encoded"))
    with pytest.raises(PipelineError, match="cannot be combined"):
        render_safe_master(source720, intervals=[], still_path=source720,
                           out_path=tmp_path / "out.mp4", probe=probe,
                           encode_profile="ambient-720p-v1", **custom)
