"""Intake contracts and existing signed package negatives; no keys generated."""

import json
import shutil
from pathlib import Path

import pytest

from pipeline import PipelineError
from pipeline import local_intake as intake
from pipeline.flashmap_adapter import FlashMapDoc, MapSegment
from pipeline.hashing import fingerprint, sha256_file
from pipeline.packaged_library import catalog_module
from pipeline.probe import StreamInfo, VideoProbe

REPO = Path(__file__).resolve().parents[2]
ACADIA = "2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28"
BUNDLE = "4bab8d81f779d7cf0eac3f5e2fe5372e88e95088fb068680818b28865dc6ad13"


def probe(**changes):
    data = dict(
        path="fixture",
        duration_s=1,
        width=1280,
        height=720,
        pix_fmt="yuv420p",
        codec_name="h264",
        color_primaries="bt709",
        color_transfer="bt709",
        color_space="bt709",
        color_range="tv",
        avg_frame_rate=2,
        frame_count=2,
        frame_timestamps_s=[0, 0.5],
        frame_interval_median_s=0.5,
        audio_streams=[StreamInfo(1, "audio", "aac")],
    )
    data.update(changes)
    return VideoProbe(**data)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(intake.IntakeStore, "launch", lambda *_: None)
    value = intake.IntakeStore(tmp_path / "intake")
    yield value
    value.close()


def ready(store):
    job = store.create("clip.mp4", b"CONTRACT FIXTURE, NOT MEDIA", "Chosen clip")
    path = intake.job_dir(store.root, job["id"])
    for p in ["wcag", "broadcast"]:
        (path / (p + ".json")).write_text("{}")
    review = {
        "analysis_complete": True,
        "source_sha256": job["source_sha256"],
        "review_map_hashes": {p: sha256_file(path / (p + ".json")) for p in ["wcag", "broadcast"]},
        "presets": {},
    }
    return path, intake.update(
        path, status="review", review=review, review_digest=fingerprint(review)
    )


@pytest.mark.parametrize(
    "changes",
    [
        dict(duration_s=61),
        dict(duration_s=float("nan")),
        dict(width=1920),
        dict(height=1080),
        dict(codec_name="hevc"),
        dict(pix_fmt="yuv420p10le"),
        dict(color_transfer="smpte2084"),
        dict(avg_frame_rate=120),
        dict(audio_streams=[]),
        dict(audio_streams=[StreamInfo(1, "audio", "opus")]),
        dict(subtitle_streams=[StreamInfo(2, "subtitle", "mov_text")]),
    ],
)
def test_unsupported_format_is_refused(changes):
    with pytest.raises(intake.IntakeError):
        intake.validate_probe(probe(**changes))


def test_only_bounded_mp4_intake(store):
    for name, data in [("clip.mov", b"bytes"), ("clip.mp4", b"")]:
        with pytest.raises(intake.IntakeError):
            store.create(name, data, "Title")
    assert store.poll() == []


def test_repeat_import_is_not_stale(store):
    first = store.create("clip.mp4", b"not media", "First")
    with pytest.raises(intake.IntakeError):
        store.create("clip.mp4", b"not media", "Second")
    store.action(first["id"], "cancel")
    second = store.create("clip.mp4", b"not media", "Second")
    assert first["id"] != second["id"] and "review" not in second and second["playable"] is False


def test_cancel_revokes_review(store):
    path, job = ready(store)
    store.action(job["id"], "cancel")
    assert intake.read_job(path)["review"] is None
    with pytest.raises(intake.IntakeError):
        store.action(job["id"], "approve")
    store.action(job["id"], "retry")
    assert intake.read_job(path)["status"] == "queued"


def test_changed_source_refused(store):
    path, _ = ready(store)
    (path / "original.mp4").write_bytes(b"swapped")
    with pytest.raises(intake.IntakeError, match="changed"):
        intake.checked_review(path)


def test_changed_map_refused(store):
    path, job = ready(store)
    (path / "wcag.json").write_text('{"swapped":true}')
    with pytest.raises(intake.IntakeError, match="changed"):
        store.action(job["id"], "approve")


def test_changed_review_refused(store):
    path, job = ready(store)
    job["review"]["duration_ms"] = 1
    intake._write_json(path / "job.json", job, path)
    with pytest.raises(intake.IntakeError):
        store.action(job["id"], "approve")


def test_no_signer_is_blocked(store, monkeypatch):
    path, job = ready(store)
    monkeypatch.undo()
    store.action(job["id"], "approve")
    result = intake.read_job(path)
    assert result["status"] == "signing_blocked" and result["playable"] is False
    assert store.children == {} and not (path / "package").exists()


def test_restart_marks_incomplete_work(tmp_path, monkeypatch):
    monkeypatch.setattr(intake.IntakeStore, "launch", lambda *_: None)
    first = intake.IntakeStore(tmp_path / "intake")
    job = first.create("clip.mp4", b"fixture", "Clip")
    first.close()
    second = intake.IntakeStore(tmp_path / "intake")
    try:
        assert second.poll()[0]["status"] == "interrupted"
        with pytest.raises(intake.IntakeError):
            second.action(job["id"], "approve")
    finally:
        second.close()


def test_competing_server_refused(store):
    with pytest.raises(PipelineError):
        intake.IntakeStore(store.root)


def test_paths_cannot_escape(store, tmp_path):
    with pytest.raises(intake.IntakeError):
        intake.job_dir(store.root, "../outside")
    outside = tmp_path / "outside"
    outside.mkdir()
    (store.root / ("a" * 32)).symlink_to(outside)
    with pytest.raises(PipelineError):
        intake.job_dir(store.root, "a" * 32)
    (store.root / ("a" * 32)).unlink()


@pytest.mark.parametrize("fault", ["identity", "frames", "tail", "profile", "throw"])
def test_incomplete_analysis_refused(tmp_path, monkeypatch, fault):
    source = tmp_path / "original.mp4"
    source.write_bytes(b"CONTRACT ONLY")
    sha = sha256_file(source)
    monkeypatch.setattr(intake, "validate_container", lambda _: None)
    monkeypatch.setattr(intake, "probe_video", lambda *_a, **_k: probe())

    class Analyzer:
        def __init__(self, **_):
            pass

        def analyze(self, _source, *, profile, out_path, **_):
            if fault == "throw":
                raise PipelineError("decoder failed")
            out_path.write_text("{}")
            return FlashMapDoc(
                1,
                "f" * 64 if fault == "identity" else sha,
                "wrong" if fault == "profile" else profile,
                [],
                raw={
                    "source": {
                        "frame_count": 1 if fault == "frames" else 2,
                        "last_pts_ms": -1000 if fault == "tail" else 500,
                    }
                },
            )

    monkeypatch.setattr(intake, "FlashmapAdapter", Analyzer)
    with pytest.raises(PipelineError):
        intake.review_analysis(source, tmp_path)


def test_review_uses_app_guard_union(tmp_path, monkeypatch):
    source = tmp_path / "original.mp4"
    source.write_bytes(b"CONTRACT ONLY")
    sha = sha256_file(source)
    monkeypatch.setattr(intake, "validate_container", lambda _: None)
    monkeypatch.setattr(
        intake, "probe_video", lambda *_a, **_k: probe(duration_s=10, frame_timestamps_s=[0, 9.5])
    )
    calls = []

    class Analyzer:
        def __init__(self, **_):
            pass

        def analyze(self, _source, *, profile, out_path, **kwargs):
            calls.append(kwargs)
            out_path.write_text("{}")
            return FlashMapDoc(
                1,
                sha,
                profile,
                [MapSegment(5000, 6000)],
                raw={"source": {"frame_count": 2, "last_pts_ms": 9500}},
            )

    monkeypatch.setattr(intake, "FlashmapAdapter", Analyzer)
    result = intake.review_analysis(source, tmp_path)
    assert result["playable"] is False and result["analysis_complete"] is True
    assert all(c["diag_in"] == 85 and c["distance_ft"] == 4 for c in calls)
    assert result["presets"]["wcag"]["covered_ms"] == 2000
    assert result["presets"]["extra-cautious"]["covered_ms"] == 3000


@pytest.fixture
def signed_package(tmp_path):
    root = tmp_path / "package"
    root.mkdir()
    original = REPO / "app/assets/raw/prepared-library" / BUNDLE
    shutil.copytree(original, root / BUNDLE)
    text = (original / "manifest.json").read_text()
    (root / "catalog.json").write_text(text)
    (root / "catalog.ts").write_text(catalog_module(text))
    report = json.loads(text)["titles"][0]["verification"]["reportSha256"]
    (root / "reports").mkdir()
    shutil.copy2(
        REPO / "results/video-reset/acadia/verification-report.json",
        root / "reports" / (report + ".json"),
    )
    return root


def test_valid_package_inspected_not_authorized(signed_package):
    result = intake.inspect_package(signed_package, ACADIA)
    assert result["bundle_id"] == BUNDLE and result["playable_in_current_tv_app"] is False


def test_package_identity_mismatch(signed_package):
    with pytest.raises(intake.IntakeError):
        intake.inspect_package(signed_package, "f" * 64)


def test_package_tampered_media(signed_package):
    media = next((signed_package / BUNDLE).rglob("extra-cautious.mp4"))
    with media.open("r+b") as f:
        f.write(b"BAD")
    with pytest.raises(PipelineError):
        intake.inspect_package(signed_package, ACADIA)


def test_unsigned_map_after_rehash_still_refused(signed_package):
    manifest = json.loads((signed_package / "catalog.json").read_text())
    item = manifest["titles"][0]["maps"]["wcag"]
    raw = json.loads(item["text"])
    raw.pop("signature", None)
    text = json.dumps(raw, indent=2, sort_keys=True) + "\n"
    path = signed_package / BUNDLE / item["path"]
    path.write_text(text)
    item["text"] = text
    item["sha256"] = sha256_file(path)
    manifest["files"][item["path"]] = item["sha256"]
    manifest.pop("bundleId")
    new_id = fingerprint(manifest)
    manifest["bundleId"] = new_id
    (signed_package / BUNDLE).rename(signed_package / new_id)
    canonical = json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    (signed_package / new_id / "manifest.json").write_text(canonical)
    (signed_package / "catalog.json").write_text(canonical)
    (signed_package / "catalog.ts").write_text(catalog_module(canonical))
    with pytest.raises(PipelineError):
        intake.inspect_package(signed_package, ACADIA)


def test_missing_report_refused(signed_package):
    shutil.rmtree(signed_package / "reports")
    with pytest.raises(PipelineError):
        intake.inspect_package(signed_package, ACADIA)


def test_old_run_cannot_publish_after_cancel_or_retry(store, monkeypatch):
    path, job = ready(store)
    intake.update(path, run_id="a" * 32)
    store.action(job["id"], "cancel")
    monkeypatch.setattr(intake, "WORKER_RUN", ("a" * 32, intake.os.getppid()))
    with pytest.raises(intake.IntakeError, match="no longer current"):
        intake.update(path, status="review")
    assert intake.read_job(path)["status"] == "canceled"
    monkeypatch.setattr(intake, "WORKER_RUN", None)
    store.action(job["id"], "retry")
    intake.update(path, run_id="b" * 32)
    monkeypatch.setattr(intake, "WORKER_RUN", ("a" * 32, intake.os.getppid()))
    with pytest.raises(intake.IntakeError):
        intake.update(path, status="package_review")
    assert intake.read_job(path)["status"] == "queued"
    monkeypatch.setattr(intake, "WORKER_RUN", None)


def test_dead_parent_cannot_publish(store, monkeypatch):
    path, _ = ready(store)
    intake.update(path, run_id="a" * 32)
    monkeypatch.setattr(intake, "WORKER_RUN", ("a" * 32, -1))
    with pytest.raises(intake.IntakeError):
        intake.update(path, status="package_review")
    assert intake.read_job(path)["status"] == "review"
    monkeypatch.setattr(intake, "WORKER_RUN", None)


def test_review_approval_respects_active_import(store):
    _, reviewed = ready(store)
    store.create("clip.mp4", b"second", "Second")
    with pytest.raises(intake.IntakeError, match="already running"):
        store.action(reviewed["id"], "approve")


@pytest.mark.parametrize(
    "header",
    [b"not mp4", b"\x00\x00\x00\x14ftypqt  \x00\x00\x00\x00qt  ", b"\x00\x00\x10\x01ftypisom"],
)
def test_renamed_container_refused(tmp_path, header):
    source = tmp_path / "renamed.mp4"
    source.write_bytes(header)
    with pytest.raises(intake.IntakeError):
        intake.validate_container(source)


def test_standard_mp4_container(tmp_path):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"\x00\x00\x00\x14ftypisom\x00\x00\x00\x00mp42")
    intake.validate_container(source)


def test_worker_deadline_without_http_poll(monkeypatch):
    class Stop:
        def wait(self, _):
            return False

    monkeypatch.setattr(intake, "JOB_TIMEOUT_S", 0)
    monkeypatch.setattr(intake.os, "getpid", lambda: 123)
    monkeypatch.setattr(intake.os, "getpgrp", lambda: 123)

    def killed(pid, signal):
        assert pid == 123 and signal == intake.signal.SIGKILL
        raise SystemExit()

    monkeypatch.setattr(intake.os, "killpg", killed)
    with pytest.raises(SystemExit):
        intake.worker_watchdog(intake.os.getppid(), Stop())
