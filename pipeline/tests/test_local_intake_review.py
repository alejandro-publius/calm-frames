"""Caregiver review exports and permission boundaries; no signing or playback."""

import json

import pytest

from pipeline import local_intake as intake
from pipeline.hashing import fingerprint, sha256_file


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(intake.IntakeStore, "launch", lambda *_: None)
    value = intake.IntakeStore(tmp_path / "intake")
    yield value
    value.close()


def reviewed(store):
    job = store.create("clip.mp4", b"CONTRACT FIXTURE, NOT MEDIA", "Fictional pond", permission_confirmed=True)
    path = intake.job_dir(store.root, job["id"])
    for profile in ("wcag", "broadcast"):
        (path / (profile + ".json")).write_text("{}")
    review = {
        "analysis_complete": True,
        "source_sha256": job["source_sha256"],
        "duration_ms": 1000,
        "frame_count": 24,
        "playable": False,
        "review_map_hashes": {
            p: sha256_file(path / (p + ".json")) for p in ("wcag", "broadcast")
        },
        "presets": {
            preset: {"intervals": [], "covered_ms": 0}
            for preset in ("wcag", "broadcast", "extra-cautious")
        },
    }
    intake.update(path, status="review", review=review, review_digest=fingerprint(review))
    return path, job


def test_missing_permission_refuses_before_retaining_the_file(store):
    with pytest.raises(intake.IntakeError, match="permission"):
        store.create("clip.mp4", b"fixture", "Clip")
    assert store.poll() == []
    assert not list(store.root.glob("*/original.mp4"))


@pytest.mark.parametrize("value", [False, None, 1, "true", "confirmed"])
def test_permission_is_an_explicit_boolean_not_a_truthy_value(store, value):
    with pytest.raises(intake.IntakeError, match="permission"):
        store.create("clip.mp4", b"fixture", "Clip", permission_confirmed=value)
    assert store.poll() == []


def test_caregiver_review_keeps_exact_analysis_without_authorizing_playback(store):
    path, job = reviewed(store)
    report = store.export_review(job["id"])
    assert report["schema"] == "calm-frames-caregiver-review-v1"
    assert report["source"] == {"sha256": job["source_sha256"], "bytes": job["bytes"]}
    assert report["analysis"] == intake.read_job(path)["review"]
    assert report["processing_permission_confirmed"] is True
    assert report["permission_verified_by_application"] is False
    assert report["tv_playback_authorized"] is False
    assert "medical" in " ".join(report["limitations"])
    assert "DRM" in " ".join(report["limitations"])
    assert str(store.root) not in json.dumps(report)
    assert intake.read_job(path)["status"] == "review"
    assert store.children == {}


@pytest.mark.parametrize("tamper", ["source", "map", "review"])
def test_export_refuses_stale_or_changed_inputs(store, tamper):
    path, job = reviewed(store)
    if tamper == "source":
        (path / "original.mp4").write_bytes(b"changed")
    elif tamper == "map":
        (path / "wcag.json").write_text('{"changed":true}')
    else:
        changed = intake.read_job(path)["review"]
        changed["duration_ms"] = 2
        intake.update(path, review=changed)
    with pytest.raises(intake.IntakeError, match="changed"):
        store.export_review(job["id"])


@pytest.mark.parametrize("state", ["queued", "analyzing", "failed", "canceled", "interrupted"])
def test_export_requires_a_finished_current_review(store, state):
    path, job = reviewed(store)
    intake.update(path, status=state)
    with pytest.raises(intake.IntakeError, match="complete"):
        store.export_review(job["id"])


def test_preexisting_review_does_not_invent_a_permission_record(store):
    path, job = reviewed(store)
    saved = intake.read_job(path)
    saved.pop("permission_confirmed", None)
    intake._write_json(path / "job.json", saved, path)
    assert store.export_review(job["id"])["processing_permission_confirmed"] is False
