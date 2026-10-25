"""Worker transaction tests with fabricated producer results, never media evidence."""
import json

import pytest

from pipeline import local_intake as intake
from pipeline.hashing import fingerprint
from pipeline.hideplan import HidePlan
from pipeline.layout import TitleLayout

from .test_local_intake import ready


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(intake.IntakeStore, "launch", lambda *_: None)
    value = intake.IntakeStore(tmp_path / "intake")
    yield value
    value.close()


def test_analysis_worker_binds_review_to_its_current_run(store, monkeypatch):
    path, job = ready(store)
    job = intake.update(path, run_id="b" * 32)
    def analyze(source, destination, progress):
        assert source.read_bytes() == b"CONTRACT FIXTURE, NOT MEDIA"
        progress("Synthetic analyzer stage")
        for profile in ("wcag", "broadcast"):
            (destination / f"{profile}.json").write_text("{}")
        return job["review"].copy()
    monkeypatch.setattr(intake, "review_analysis", analyze)
    intake.analysis_worker(path)
    result, _ = intake.checked_review(path)
    assert result["status"] == "review"
    assert result["review"]["analysis_run"] == job["run_id"]
    assert result["review_digest"] == fingerprint(result["review"])


@pytest.mark.parametrize("failure", [None, "unapproved", "internal-key", "failed", "plan", "source"])
def test_preparation_publishes_only_after_approved_plan_and_unchanged_source(
    store, tmp_path, monkeypatch, failure,
):
    path, job = ready(store)
    job = intake.update(path, run_id="b" * 32)
    review = job["review"]
    digest = fingerprint(review)
    intake.update(path, review=review, review_digest=digest,
                  approved_review=None if failure == "unapproved" else digest)
    # These are path-policy markers, not generated credentials. The stub producer never reads them.
    key = (path if failure == "internal-key" else tmp_path) / "signer-path-marker"
    pub = tmp_path / "public-path-marker"
    key.write_text("NOT A KEY")
    pub.write_text("NOT A KEY")
    calls = []
    def prepare(source, work, **_):
        calls.append("prepare")
        layout = TitleLayout(work, job["source_sha256"])
        plan = HidePlan("wcag", job["source_sha256"], 500, 400, 1000, False, []).to_dict()
        if failure == "plan":
            plan["intervals"] = [{"start_ms": 1, "end_ms": 20, "reason": "general"}]
        for preset in ("wcag", "broadcast", "extra-cautious"):
            layout.plan_path(preset).parent.mkdir(parents=True, exist_ok=True)
            layout.plan_path(preset).write_text(json.dumps({**plan, "preset": preset}))
        if failure == "source":
            source.write_bytes(b"changed after review")
        return {"status": "failed" if failure == "failed" else "ready"}
    monkeypatch.setattr(intake, "prepare_local_title", prepare)
    monkeypatch.setattr(intake, "export_packaged_library", lambda *a, **kw: calls.append("export"))
    monkeypatch.setattr(intake, "inspect_package", lambda *a: {"bundle_id": "fabricated", "playable_in_current_tv_app": False})
    if failure:
        with pytest.raises(intake.IntakeError):
            intake.prepare_worker(path, key, pub)
        assert "export" not in calls
        assert intake.read_job(path)["status"] != "package_review"
    else:
        intake.prepare_worker(path, key, pub)
        result = intake.read_job(path)
        assert calls == ["prepare", "export"]
        assert result["status"] == "package_review"
        assert result["package"]["playable_in_current_tv_app"] is False
        assert result["package"]["relative_directory"] == f"runs/{job['run_id']}/package"
        assert result["delivery"] is None and result["delivery_plan"] is None


@pytest.mark.parametrize("mode,failure", [("analyze", None), ("prepare", None),
                                         ("analyze", "typed"), ("analyze", "unexpected"),
                                         ("prepare", "missing-key"), ("analyze", "superseded")])
def test_worker_cli_stops_failure_and_never_overwrites_superseded_job(store, monkeypatch, mode, failure):
    path, job = ready(store)
    job = intake.update(path, run_id="b" * 32)
    monkeypatch.setattr(intake, "WORKER_RUN", None)
    # The CLI dispatch is tested in-process without starting a watchdog or child process.
    class NoThread:
        def __init__(self, **_):
            pass
        def start(self):
            pass
    monkeypatch.setattr(intake.threading, "Thread", NoThread)
    def worker(*_):
        if failure == "typed":
            raise intake.IntakeError("Explicit refused input")
        if failure == "unexpected":
            raise RuntimeError("private producer diagnostic")
        intake.update(path, stage="stub completed")
    monkeypatch.setattr(intake, "analysis_worker", worker)
    monkeypatch.setattr(intake, "prepare_worker", worker)
    args = ["worker", "--job", str(path), "--mode", mode, "--run-id",
            "a" * 32 if failure == "superseded" else job["run_id"],
            "--parent-pid", str(intake.os.getppid())]
    if mode == "prepare" and failure != "missing-key":
        args += ["--key", "unused-test-key-path", "--pub", "unused-test-public-path"]
    assert intake.main(args) == (1 if failure else 0)
    result = intake.read_job(path)
    if failure == "superseded":
        assert result == job
    elif failure:
        assert result["status"] == "failed"
        assert result["review"] is None and result["package"] is None
        assert "private producer diagnostic" not in result["error"]
    else:
        assert result["stage"] == "stub completed"
