"""One unreadable local record must not hide unrelated caregiver reviews."""
import json

import pytest

from pipeline import local_intake as intake

from .test_local_intake import ready


@pytest.mark.parametrize('damage', ['truncated', 'missing', 'invalid-shape', 'oversized-time'])
def test_unreadable_record_is_preserved_and_does_not_block_restart(tmp_path, monkeypatch, damage):
    monkeypatch.setattr(intake.IntakeStore, 'launch', lambda *_: None)
    root = tmp_path / 'imports'
    first = intake.IntakeStore(root)
    bad_path, bad = ready(first)
    good_path, good = ready(first)
    first.close()
    record = bad_path / 'job.json'
    if damage == 'missing':
        record.unlink()
    elif damage == 'truncated':
        record.write_text('{"id":')
    elif damage == 'oversized-time':
        record.write_text(json.dumps({**bad, 'created_at': 10 ** 400}))
    else:
        record.write_text(json.dumps({'id': bad['id'], 'status': None}))
    original = record.read_bytes() if record.exists() else None
    good_before = (good_path / 'job.json').read_bytes()
    source_before = (bad_path / 'original.mp4').read_bytes()
    second = intake.IntakeStore(root)
    try:
        jobs = {job['id']: job for job in second.poll()}
        assert jobs[good['id']]['status'] == 'review'
        assert jobs[bad['id']]['status'] == 'unreadable'
        assert jobs[bad['id']]['playable'] is False
        assert 'review' not in jobs[bad['id']]
        assert 'source_sha256' not in jobs[bad['id']]
        assert str(root) not in json.dumps(jobs[bad['id']])
        assert (record.read_bytes() if record.exists() else None) == original
        assert (good_path / 'job.json').read_bytes() == good_before
        assert (bad_path / 'original.mp4').read_bytes() == source_before
        for action in ['approve', 'retry', 'stage-delivery', 'plan-delivery']:
            with pytest.raises(intake.IntakeError):
                second.action(bad['id'], action)
        with pytest.raises(intake.IntakeError):
            second.export_review(bad['id'])
        assert second.action(bad['id'], 'delete') == {'deleted': bad['id']}
        assert not bad_path.exists()
        assert (good_path / 'job.json').read_bytes() == good_before
    finally:
        second.close()


def test_corrupt_record_during_owned_work_can_be_stopped_without_publishing(tmp_path, monkeypatch):
    monkeypatch.setattr(intake.IntakeStore, 'launch', lambda *_: None)
    store = intake.IntakeStore(tmp_path / 'imports')
    path, job = ready(store)
    calls = []
    class Child:
        pid = 987654
        stopped = False
        def poll(self):
            return 0 if self.stopped else None
        def wait(self, timeout=None):
            self.stopped = True
            return 0
    child = Child()
    monkeypatch.setattr(intake.os, 'killpg', lambda pid, signal: calls.append((pid, signal)))
    store.children[job['id']] = (child, intake.time.monotonic())
    (path / 'job.json').write_text('{')
    try:
        assert store.poll()[0]['status'] in intake.ACTIVE
        with pytest.raises(intake.IntakeError):
            store.create('other.mp4', b'fixture', 'Other', permission_confirmed=True)
        with pytest.raises(intake.IntakeError):
            store.action(job['id'], 'delete')
        store.action(job['id'], 'cancel')
        assert calls == [(child.pid, intake.signal.SIGTERM)]
        assert not store.children
        assert store.poll()[0]['status'] == 'unreadable'
        assert (path / 'job.json').read_text() == '{'
    finally:
        store.close()


def test_saved_review_waits_for_its_owned_worker_before_enabling_actions(tmp_path, monkeypatch):
    monkeypatch.setattr(intake.IntakeStore, 'launch', lambda *_: None)
    store = intake.IntakeStore(tmp_path / 'imports')
    path, job = ready(store)
    class Child:
        pid = 987654
        stopped = False
        def poll(self):
            return 0 if self.stopped else None
        def wait(self, timeout=None):
            assert timeout == 0.1
            raise intake.subprocess.TimeoutExpired('fictional-worker', timeout)
    child = Child()
    store.children[job['id']] = (child, intake.time.monotonic())
    saved = (path / 'job.json').read_bytes()
    try:
        assert store.poll()[0]['status'] in intake.ACTIVE
        with pytest.raises(intake.IntakeError, match='running'):
            store.action(job['id'], 'approve')
        assert (path / 'job.json').read_bytes() == saved
        child.stopped = True
        assert store.poll()[0]['status'] == 'review'
        assert not store.children
        assert (path / 'job.json').read_bytes() == saved
    finally:
        child.stopped = True
        store.close()


@pytest.mark.parametrize("damage", [
    "missing-review", "list-review", "missing-preset", "missing-map",
    "invalid-span", "wrong-total", "list-flags", "invalid-run", "changed-digest",
])
def test_damaged_saved_review_cannot_hide_other_imports_or_authorize_work(
    tmp_path, monkeypatch, damage,
):
    from pipeline.hashing import fingerprint

    monkeypatch.setattr(intake.IntakeStore, "launch", lambda *_: None)
    root = tmp_path / "imports"
    store = intake.IntakeStore(root)
    bad_path, bad = ready(store)
    good_path, good = ready(store)
    saved = intake.read_job(bad_path)
    review = saved["review"]
    if damage == "missing-review":
        saved.pop("review")
    elif damage == "list-review":
        saved["review"] = ["unreadable"]
    elif damage == "missing-preset":
        review["presets"].pop("extra-cautious")
    elif damage == "missing-map":
        review["review_map_hashes"] = {}
    elif damage == "invalid-span":
        review["presets"]["wcag"]["intervals"] = [{"start_ms": 900, "end_ms": 1, "reason": "general"}]
    elif damage == "wrong-total":
        review["presets"]["wcag"]["covered_ms"] = 1000
    elif damage == "list-flags":
        review["flagged_intervals"] = {"wcag": [None]}
    elif damage == "invalid-run":
        review["analysis_run"] = ["not-a-run-id"]
    else:
        saved["review_digest"] = "0" * 64
    # A recomputed checksum cannot make an incomplete review usable either.
    if damage != "changed-digest":
        saved["review_digest"] = fingerprint(saved.get("review"))
    intake._write_json(bad_path / "job.json", saved, bad_path)
    before = (bad_path / "job.json").read_bytes()
    source_before = (bad_path / "original.mp4").read_bytes()
    good_before = (good_path / "job.json").read_bytes()
    try:
        listed = {j["id"]: j for j in store.poll()}
        assert listed[bad["id"]]["status"] == "unreadable"
        assert "review" not in listed[bad["id"]]
        assert listed[good["id"]]["status"] == "review"
        for action in ("approve", "stage-delivery", "plan-delivery", "retry"):
            with pytest.raises(intake.IntakeError):
                store.action(bad["id"], action)
        with pytest.raises(intake.IntakeError):
            store.export_review(bad["id"])
        assert (bad_path / "job.json").read_bytes() == before
        assert (bad_path / "original.mp4").read_bytes() == source_before
        assert (good_path / "job.json").read_bytes() == good_before
    finally:
        store.close()
    restarted = intake.IntakeStore(root)
    try:
        assert any(j["id"] == good["id"] and j["status"] == "review" for j in restarted.poll())
        restarted.action(bad["id"], "delete")
        assert not bad_path.exists()
        assert (good_path / "job.json").read_bytes() == good_before
    finally:
        restarted.close()


@pytest.mark.parametrize("damage", [
    "missing-package", "list-package", "missing-bundle", "outside-package",
    "list-delivery", "unknown-delivery", "invalid-ticket", "list-plan",
    "missing-files", "different-plan-ticket", "canceled-plan",
])
def test_damaged_delivery_snapshot_keeps_other_imports_reachable(tmp_path, monkeypatch, damage):
    monkeypatch.setattr(intake.IntakeStore, "launch", lambda *_: None)
    store = intake.IntakeStore(tmp_path / "imports")
    path, job = ready(store)
    good_path, good = ready(store)
    package = {
        "bundle_id": "a" * 64, "catalog_sha256": "b" * 64,
        "public_key_fingerprint": "sha256:" + "c" * 64,
        "relative_directory": "runs/fixture/package",
    }
    delivery = {
        "state": "approved_for_build", "ticket_id": "d" * 32,
        "can_watch": False, "message": "Fixture snapshot only", "blockers": [],
    }
    plan = {
        "state": "ready_to_apply", "ticket_id": delivery["ticket_id"],
        "can_watch": False, "blockers": [], "files_to_add": [], "files_already_present": [],
        "app_directory": "/fictional/app", "staging_root": "/fictional/staging",
    }
    saved = {**job, "status": "package_review", "package": package,
             "delivery": delivery, "delivery_plan": plan}
    if damage == "missing-package":
        saved.pop("package")
    elif damage == "list-package":
        saved["package"] = ["damaged"]
    elif damage == "missing-bundle":
        package.pop("bundle_id")
    elif damage == "outside-package":
        package["relative_directory"] = "../../outside"
    elif damage == "list-delivery":
        saved["delivery"] = ["damaged"]
    elif damage == "unknown-delivery":
        delivery["state"] = "installed"
    elif damage == "invalid-ticket":
        delivery["ticket_id"] = ["damaged"]
    elif damage == "list-plan":
        saved["delivery_plan"] = ["damaged"]
    elif damage == "missing-files":
        plan.pop("files_to_add")
    elif damage == "different-plan-ticket":
        plan["ticket_id"] = "e" * 32
    else:
        delivery["state"] = "canceled"
    intake._write_json(path / "job.json", saved, path)
    original = (path / "original.mp4").read_bytes()
    bad_before = (path / "job.json").read_bytes()
    good_before = (good_path / "job.json").read_bytes()
    try:
        jobs = {j["id"]: j for j in store.poll()}
        assert jobs[job["id"]]["status"] == "unreadable"
        assert jobs[good["id"]]["status"] == "review"
        for action in ("approve", "stage-delivery", "check-delivery", "plan-delivery"):
            with pytest.raises(intake.IntakeError):
                store.action(job["id"], action)
        assert (path / "job.json").read_bytes() == bad_before
        assert (path / "original.mp4").read_bytes() == original
        assert (good_path / "job.json").read_bytes() == good_before
    finally:
        store.close()
