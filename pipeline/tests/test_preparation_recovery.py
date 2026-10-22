"""Preparation survives interruption and never reuses damaged cached work.

Every ingest here runs the real pipeline on a generated calm clip, with the fake
analyzer standing in for flashmap: spans are faked, but maps are hashed, bound and
signed for real. All damage is done to files the test owns, in its own temporary
directory. Nothing is ever played.

A recovered run is compared with an uninterrupted run of the same source, keys and
settings at the same path. What is compared is identity: each step's fingerprint
and the SHA-256 of every output it recorded, plus the verify report with only its
two run timestamps removed. Ledger completion times and the source's ingest time
are run times too, so they are never compared.
"""

from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline import PipelineError, durable
from pipeline import ingest as ingest_module
from pipeline import local_library as library
from pipeline.catalog import STATUS_FAILED, STATUS_VERIFIED, kid_mode_titles, read_entry
from pipeline.durable import LockBusy, exclusive_lock
from pipeline.hashing import sha256_file
from pipeline.ingest import IngestOptions, _Steps, ingest_title
from pipeline.layout import TitleLayout
from pipeline.state import LEDGER_NAME, MALFORMED_NAME, Ledger, LedgerError

from .clips import make_calm_clip
from .conftest import needs_ffmpeg

REPO_ROOT = Path(__file__).resolve().parents[2]
FLAGGED = [[2000, 2500, "general"]]


class Interrupted(BaseException):
    """Stands in for the process stopping: nothing in the pipeline catches it."""


# Ledger mechanics, without media.


def _committed(tmp_path: Path) -> tuple[Ledger, Path]:
    ledger = Ledger(tmp_path)
    output = tmp_path / "out" / "artifact.bin"
    output.parent.mkdir()
    output.write_bytes(b"0123456789" * 100)
    ledger.record("step", "fp", [output])
    return Ledger(tmp_path), output


@pytest.mark.parametrize("damage", [
    "missing", "truncated", "same_size", "same_size_same_mtime", "link", "directory",
])
def test_check_names_each_kind_of_output_damage(tmp_path, damage):
    ledger, output = _committed(tmp_path)
    assert ledger.check("step", "fp").valid
    original = output.read_bytes()
    stamp = output.stat()
    if damage == "missing":
        output.unlink()
    elif damage == "truncated":
        output.write_bytes(original[:-1])
    elif damage in ("same_size", "same_size_same_mtime"):
        output.write_bytes(original[:500] + b"X" + original[501:])
        if damage == "same_size_same_mtime":
            os.utime(output, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    elif damage == "link":
        elsewhere = tmp_path / "elsewhere.bin"
        elsewhere.write_bytes(original)
        output.unlink()
        output.symlink_to(elsewhere)
    else:
        output.unlink()
        output.mkdir()
    check = ledger.check("step", "fp")
    assert not check.valid
    assert "out/artifact.bin" in check.reason
    assert not ledger.check("step", "another fingerprint").valid


def test_record_refuses_outputs_that_are_missing_outside_or_links(tmp_path):
    ledger = Ledger(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.bin"
    outside.write_bytes(b"not owned")
    link = tmp_path / "link.bin"
    link.symlink_to(outside)
    for output in (tmp_path / "never-written.bin", outside, link):
        with pytest.raises(LedgerError):
            ledger.record("step", "fp", [output])
    assert Ledger(tmp_path).get("step") is None
    assert not (tmp_path / LEDGER_NAME).exists()


@pytest.mark.parametrize("timestamp", [10 ** 1000, -(10 ** 1000)], ids=["too-large", "too-negative"])
def test_oversized_integer_timestamp_drops_only_the_malformed_record(tmp_path, timestamp):
    ledger, output = _committed(tmp_path)
    ledger.record("other", "fp", [output])
    data = json.loads(ledger.path.read_text())
    data["steps"]["step"]["completed_at"] = timestamp
    ledger.path.write_text(json.dumps(data))
    loaded = Ledger(tmp_path)
    assert loaded.get("step") is None
    assert loaded.check("other", "fp").valid


def _nested(depth: int) -> bytes:
    return b"[" * depth + b"]" * depth


@pytest.mark.parametrize("content", [
    "truncated", "empty", "binary", "not_object", "steps_not_object", "nested", "oversized",
])
def test_an_unreadable_ledger_is_never_trusted_and_is_moved_aside_on_write(
    tmp_path, monkeypatch, content,
):
    ledger, _ = _committed(tmp_path)
    good = ledger.path.read_bytes()
    bad = {
        "truncated": good[: len(good) // 2],
        "empty": b"",
        "binary": b"\xff\xfe\x00\x81 not text",
        "not_object": b"[]",
        "steps_not_object": json.dumps({"pipeline_version": "1", "steps": []}).encode(),
        "nested": _nested(100_000),
        "oversized": good,
    }[content]
    if content == "oversized":
        monkeypatch.setattr("pipeline.state.MAX_LEDGER_BYTES", len(good) - 1)
    ledger.path.write_bytes(bad)
    reader = Ledger(tmp_path)
    assert reader.malformed
    assert reader.get("step") is None
    assert not reader.check("step", "fp").valid
    # Reading changes nothing on disk.
    assert ledger.path.read_bytes() == bad
    assert not (tmp_path / MALFORMED_NAME).exists()
    reader.set_source({"name": "fresh"})
    assert (tmp_path / MALFORMED_NAME).read_bytes() == bad
    assert Ledger(tmp_path).source == {"name": "fresh"}
    assert [event["event"] for event in reader.events] == ["ledger_malformed", "ledger_moved_aside"]


def test_one_malformed_record_is_dropped_and_the_others_are_kept(tmp_path):
    ledger, output = _committed(tmp_path)
    ledger.record("other", "fp2", [output])
    data = json.loads(ledger.path.read_text())
    data["steps"]["other"]["output_sha256"] = {"out/artifact.bin": "not a hash"}
    ledger.path.write_text(json.dumps(data))
    reloaded = Ledger(tmp_path)
    assert reloaded.check("step", "fp").valid
    assert reloaded.get("other") is None
    assert reloaded.events == [{"event": "record_dropped", "step": "other",
                                "reason": "the output hashes do not cover exactly the recorded outputs"}]


@pytest.mark.parametrize("path", ["../escape.bin", "/etc/hosts", "out/../out/artifact.bin", "out//artifact.bin"])
def test_a_record_naming_a_path_outside_the_title_is_dropped(tmp_path, path):
    ledger, _ = _committed(tmp_path)
    data = json.loads(ledger.path.read_text())
    record = data["steps"]["step"]
    digest = record["output_sha256"].pop("out/artifact.bin")
    record["outputs"] = [path]
    record["output_sha256"] = {path: digest}
    ledger.path.write_text(json.dumps(data))
    assert Ledger(tmp_path).get("step") is None


@pytest.mark.parametrize("damage", [
    "other_name", "fingerprint_not_text", "outputs_not_a_list", "output_listed_twice",
    "completion_not_a_number", "completion_infinite", "extra_not_an_object", "no_output_hashes",
    "record_not_an_object",
])
def test_a_record_with_the_wrong_shape_is_dropped_and_its_step_runs_again(tmp_path, damage):
    ledger, _ = _committed(tmp_path)
    data = json.loads(ledger.path.read_text())
    record = data["steps"]["step"]
    if damage == "other_name":
        record["name"] = "elsewhere"
    elif damage == "fingerprint_not_text":
        record["fingerprint"] = 7
    elif damage == "outputs_not_a_list":
        record["outputs"] = "out/artifact.bin"
    elif damage == "output_listed_twice":
        record["outputs"] = record["outputs"] * 2
    elif damage == "completion_not_a_number":
        record["completed_at"] = True
    elif damage == "completion_infinite":
        record["completed_at"] = float("inf")
    elif damage == "extra_not_an_object":
        record["extra"] = []
    elif damage == "no_output_hashes":
        record.pop("output_sha256")
    else:
        data["steps"]["step"] = ["not", "a", "record"]
    ledger.path.write_text(json.dumps(data))
    reloaded = Ledger(tmp_path)
    assert reloaded.get("step") is None
    assert [event["event"] for event in reloaded.events] == ["record_dropped"]


@pytest.mark.parametrize("change", ["unknown_format", "other_pipeline_version"])
def test_a_ledger_from_another_format_or_version_keeps_only_its_source(tmp_path, change):
    ledger, _ = _committed(tmp_path)
    ledger.set_source({"name": "kept"})
    data = json.loads(ledger.path.read_text())
    if change == "unknown_format":
        data["ledger_format"] = 99
    else:
        data["pipeline_version"] = "0"
    ledger.path.write_text(json.dumps(data))
    reloaded = Ledger(tmp_path)
    assert reloaded.get("step") is None
    assert reloaded.source == {"name": "kept"}
    assert [event["event"] for event in reloaded.events] == ["ledger_outdated"]


def test_an_output_that_cannot_be_read_is_not_reused(tmp_path):
    ledger, output = _committed(tmp_path)
    output.chmod(0)
    try:
        check = ledger.check("step", "fp")
    finally:
        output.chmod(0o644)
    assert not check.valid
    assert check.reason == "output out/artifact.bin cannot be read"


def test_relative_outputs_are_taken_inside_the_title(tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "artifact.bin").write_bytes(b"bytes")
    Ledger(tmp_path).record("step", "fp", ["out/artifact.bin"])
    assert Ledger(tmp_path).check("step", "fp").valid
    with pytest.raises(LedgerError):
        Ledger(tmp_path).record("step", "fp", ["../escape.bin"])


def test_a_malformed_ledger_replaced_by_a_link_is_not_moved_or_followed(tmp_path):
    ledger_path = tmp_path / LEDGER_NAME
    ledger_path.write_text("{ torn")
    reader = Ledger(tmp_path)
    target = tmp_path.parent / f"{tmp_path.name}-target.json"
    target.write_text("{}")
    ledger_path.unlink()
    ledger_path.symlink_to(target)
    with pytest.raises(LedgerError):
        reader.set_source({})
    assert target.read_text() == "{}"
    assert not (tmp_path / MALFORMED_NAME).exists()


def test_a_directory_that_cannot_be_flushed_is_tolerated_and_reported(tmp_path, monkeypatch):
    import errno

    def refuse(fd: int) -> None:
        raise OSError(errno.EINVAL, "not supported here")

    assert durable.fsync_directory(tmp_path) is True
    monkeypatch.setattr(durable, "fsync_fd", refuse)
    assert durable.fsync_directory(tmp_path) is False


def test_temporary_names_are_tried_a_bounded_number_of_times(tmp_path, monkeypatch):
    monkeypatch.setattr(durable.secrets, "token_hex", lambda n: "same")
    (tmp_path / f".state.json.{os.getpid()}.same.tmp").write_text("someone else's")
    with pytest.raises(PipelineError, match="temporary file"):
        durable.atomic_write_bytes(tmp_path / "state.json", b"{}")
    assert not (tmp_path / "state.json").exists()


def test_a_lock_on_something_that_is_not_a_regular_file_is_refused(tmp_path):
    os.mkfifo(tmp_path / ".ingest.lock")
    with pytest.raises(PipelineError, match="regular file"):
        with exclusive_lock(tmp_path / ".ingest.lock", what="test"):
            pass


def test_flushing_names_each_file_once_and_skips_missing_ones(tmp_path):
    present = tmp_path / "present.bin"
    present.write_bytes(b"bytes")
    assert durable.sync_files([present, present, tmp_path / "missing.bin"]) == 1


def test_records_from_before_output_hashes_are_read_but_never_reused(tmp_path):
    ledger, _ = _committed(tmp_path)
    data = json.loads(ledger.path.read_text())
    data.pop("ledger_format")
    record = data["steps"]["step"]
    record.pop("output_sha256")
    record["extra"] = {"passed": True}
    ledger.path.write_text(json.dumps(data))
    legacy = Ledger(tmp_path)
    assert legacy.get("step").extra == {"passed": True}
    check = legacy.check("step", "fp")
    assert not check.valid
    assert check.reason == "recorded before output hashes were kept"


def test_a_ledger_that_is_a_link_is_refused_rather_than_followed(tmp_path):
    target = tmp_path.parent / f"{tmp_path.name}-target.json"
    target.write_text(json.dumps({"pipeline_version": "1", "steps": {}}))
    (tmp_path / LEDGER_NAME).symlink_to(target)
    with pytest.raises(LedgerError):
        Ledger(tmp_path)


def test_ledger_replacement_is_flushed_then_renamed_then_the_directory_flushed(tmp_path, monkeypatch):
    ledger, _ = _committed(tmp_path)
    before = ledger.path.read_bytes()
    order: list[str] = []
    real_fsync, real_replace = durable.fsync_fd, os.replace

    def flush(fd: int) -> None:
        order.append("flush directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "flush file")
        real_fsync(fd)

    monkeypatch.setattr(durable, "fsync_fd", flush)
    monkeypatch.setattr(durable.os, "replace", lambda a, b: (order.append("rename"), real_replace(a, b))[1])
    ledger.record("step", "fp-2", [tmp_path / "out" / "artifact.bin"])
    assert order == ["flush file", "rename", "flush directory"]

    def crash(a, b):
        raise Interrupted
    monkeypatch.setattr(durable.os, "replace", crash)
    with pytest.raises(Interrupted):
        ledger.record("step", "fp-3", [tmp_path / "out" / "artifact.bin"])
    # The previous ledger is whole, and the temporary file did not stay behind.
    assert Ledger(tmp_path).get("step").fingerprint == "fp-2"
    assert ledger.path.read_bytes() != before
    assert not [path for path in tmp_path.iterdir() if path.name.endswith(".tmp")]


def test_a_planted_link_at_a_fixed_temporary_name_is_never_written_through(tmp_path):
    sentinel = tmp_path.parent / f"{tmp_path.name}-sentinel.txt"
    sentinel.write_text("must not change")
    (tmp_path / "state.json.tmp").symlink_to(sentinel)
    _committed(tmp_path)
    assert sentinel.read_text() == "must not change"


def test_a_step_is_withdrawn_on_disk_before_its_work_starts(tmp_path):
    output = tmp_path / "artifact.bin"
    seen: list[dict] = []

    def work() -> dict:
        ledger = tmp_path / LEDGER_NAME
        seen.append(json.loads(ledger.read_text())["steps"] if ledger.exists() else None)
        output.write_bytes(b"rebuilt")
        return {}

    _Steps(Ledger(tmp_path), force=False).run("step", {}, [output], work)
    output.write_bytes(b"damaged")
    _Steps(Ledger(tmp_path), force=False).run("step", {}, [output], work)
    # The second run found a record, and it was gone from disk before the work began.
    assert seen == [None, {}]
    assert Ledger(tmp_path).check("step", Ledger(tmp_path).get("step").fingerprint).valid


def test_a_step_that_does_not_produce_its_output_is_not_committed(tmp_path):
    with pytest.raises(LedgerError, match="missing"):
        _Steps(Ledger(tmp_path), force=False).run("step", {}, [tmp_path / "artifact.bin"], dict)
    assert Ledger(tmp_path).get("step") is None


def test_a_step_cannot_name_a_dependency_that_has_not_run(tmp_path):
    with pytest.raises(PipelineError, match="has not run"):
        _Steps(Ledger(tmp_path), force=False).run("step", {}, [], dict, depends_on=["probe"])


def test_a_lock_refuses_a_link_planted_in_place_of_its_file(tmp_path):
    target = tmp_path / "elsewhere"
    target.write_text("not a lock")
    (tmp_path / ".ingest.lock").symlink_to(target)
    with pytest.raises(PipelineError, match="owned file"):
        with exclusive_lock(tmp_path / ".ingest.lock", what="test"):
            pass
    assert target.read_text() == "not a lock"


def test_an_index_update_waits_a_bounded_time_for_the_index_lock(tmp_path, monkeypatch):
    from pipeline import catalog

    monkeypatch.setattr(catalog, "INDEX_LOCK_WAIT_S", 0.3)
    index = tmp_path / "catalog.json"
    entry = catalog.CatalogEntry(sha256="a" * 64, title="t", source_name="s", duration_s=1, width=2, height=2)
    with exclusive_lock(tmp_path / ".catalog.json.lock", what="test holder"):
        started = time.monotonic()
        with pytest.raises(LockBusy):
            catalog.update_index(index, entry)
        assert 0.3 <= time.monotonic() - started < 5
    assert not index.exists()
    catalog.update_index(index, entry)
    assert list(json.loads(index.read_text())["titles"]) == ["a" * 64]


def test_withdrawal_reaches_the_index_even_when_the_entry_cannot_be_read(tmp_path):
    from pipeline import catalog

    sha = "b" * 64
    entry = catalog.CatalogEntry(sha256=sha, title="t", source_name="s", duration_s=1, width=2, height=2,
                                 status=STATUS_VERIFIED, verified=True)
    index, entry_path = tmp_path / "catalog.json", tmp_path / "titles" / sha / "entry.json"
    catalog.update_index(index, entry)
    entry_path.parent.mkdir(parents=True)
    entry_path.write_text("{ torn")
    assert [item["sha256"] for item in kid_mode_titles(index)] == [sha]
    catalog.withdraw_title(index, entry_path, sha)
    assert kid_mode_titles(index) == []
    assert entry_path.read_text() == "{ torn"


# The real pipeline, interrupted and damaged.


@pytest.fixture
def title(tmp_path, analyzer, keypair):
    private, public = keypair
    source = make_calm_clip(tmp_path / "calm.mp4", seconds=5)
    analyzer.flag("calm.mp4", segments_all=FLAGGED)
    options = IngestOptions(presets=["wcag"], key=str(private), pub=str(public),
                            x264_preset="ultrafast", poster_count=1, bif_interval_ms=2000)
    return SimpleNamespace(tmp=tmp_path, source=source, options=options, analyzer=analyzer,
                           workdir=tmp_path / "out", private=private, public=public)


REPORT = "verify/report.json"


def snapshot(layout: TitleLayout) -> dict:
    """A run's identity: step fingerprints, recorded output bytes, and the verdict.

    The report's own bytes carry when verify started and finished, so its hash is
    left out and the report is compared with those two times removed instead.
    """
    ledger = Ledger(layout.root)
    steps = {
        name: (record.fingerprint, {k: v for k, v in (record.output_sha256 or {}).items() if k != REPORT})
        for name, record in ledger.steps.items()
    }
    on_disk = {
        name: sha256_file(layout.root / name)
        for record in ledger.steps.values() for name in record.outputs if name != REPORT
    }
    report = json.loads(layout.verify_report_path.read_text())
    report.pop("started_at")
    report.pop("finished_at")
    return {"steps": steps, "files": on_disk, "report": report}


def reference(title) -> dict:
    """Prepare once without interruption, keep its identity, then clear the path."""
    result = ingest_title(title.source, title.workdir, title.options)
    assert result.publishable, result.verify_report
    identity = snapshot(result.layout)
    title.workdir.rename(title.tmp / "uninterrupted")
    return identity


def _flip_byte(path: Path, offset: int | None = None) -> None:
    data = bytearray(path.read_bytes())
    index = len(data) // 2 if offset is None else offset
    data[index] ^= 0x01
    path.write_bytes(bytes(data))


def _flip_digit(path: Path) -> None:
    text = path.read_text()
    index = next(i for i, ch in enumerate(text) if ch.isdigit() and ch != "9" and i > len(text) // 3)
    path.write_text(text[:index] + str(int(text[index]) + 1) + text[index + 1:])


DAMAGE = {
    # artifact: (path inside the title, damage, the only step that may run again)
    "probe": (lambda layout: layout.probe_path, "same_size_digit", "probe"),
    "analysis_map": (lambda layout: layout.analysis_map_path("wcag"), "same_size_digit", "analyze:wcag"),
    "published_map": (lambda layout: layout.map_path("wcag"), "same_size_digit", "signed_map:wcag"),
    "plan": (lambda layout: layout.plan_path("wcag"), "same_size_digit", "plan:wcag"),
    "luma": (lambda layout: layout.luma_path, "same_size_digit", "luma"),
    "still": (lambda layout: layout.still_path, "truncated", "still"),
    "scene_image": (lambda layout: layout.scene_image("wcag", 0), "same_size", "scene_holds:wcag"),
    "safe_master": (lambda layout: layout.safe_master("wcag"), "same_size", "rendition:wcag"),
    "hls_segment": (lambda layout: sorted(layout.hls_dir("wcag").glob("seg_*.ts"))[0], "truncated",
                    "rendition:wcag"),
    "bif": (lambda layout: layout.bif_path("wcag"), "missing", "bif:wcag"),
    "poster": (lambda layout: next(layout.posters_dir("wcag").glob("*.jpg")), "same_size", "posters:wcag"),
    "cover_model": (lambda layout: layout.cover_model_path("wcag"), "missing", "cover_model:wcag"),
}


@needs_ffmpeg
@pytest.mark.parametrize("artifact", sorted(DAMAGE))
def test_damaged_output_rebuilds_only_its_step_and_restores_the_verified_identity(title, artifact):
    first = ingest_title(title.source, title.workdir, title.options)
    assert first.publishable, first.verify_report
    before = snapshot(first.layout)
    locate, damage, owner = DAMAGE[artifact]
    path = locate(first.layout)
    if damage == "same_size_digit":
        _flip_digit(path)
    elif damage == "same_size":
        _flip_byte(path)
    elif damage == "truncated":
        path.write_bytes(path.read_bytes()[: path.stat().st_size // 2])
    else:
        path.unlink()
    second = ingest_title(title.source, title.workdir, title.options)
    assert second.steps_run == [owner]
    assert set(second.invalidated) == {owner}
    assert first.layout.relative(path) in second.invalidated[owner]
    # Rebuilt bytes match what was verified, so the cached verdict holds for them.
    assert "verify" in second.steps_skipped
    assert snapshot(second.layout) == before
    assert second.publishable


@needs_ffmpeg
def test_a_rebuilt_input_that_comes_out_different_reruns_everything_built_from_it(title):
    first = ingest_title(title.source, title.workdir, title.options)
    assert first.publishable
    # The analysis is rebuilt and now flags a different span, so the plan and all
    # that rests on it must follow. Probe and luminance rest on the source alone.
    first.layout.analysis_map_path("wcag").unlink()
    title.analyzer.plan["rules"] = []
    title.analyzer.flag("calm.mp4", segments_all=[[3000, 3500, "general"]])
    second = ingest_title(title.source, title.workdir, title.options)
    assert {"probe", "luma"} <= set(second.steps_skipped)
    assert {"analyze:wcag", "plan:wcag", "still", "scene_holds:wcag", "rendition:wcag",
            "bif:wcag", "posters:wcag", "signed_map:wcag", "cover_model:wcag", "verify"} <= set(second.steps_run)
    assert second.publishable, second.verify_report
    plan = json.loads(second.layout.plan_path("wcag").read_text())
    assert [(i["start_ms"], i["end_ms"]) for i in plan["intervals"]] == [(2500, 4000)]


@needs_ffmpeg
def test_a_new_signing_key_never_reuses_maps_signed_by_the_old_one(title, tmp_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    from pipeline.registry import signer_key_id

    first = ingest_title(title.source, title.workdir, title.options)
    assert first.publishable
    key = ed25519.Ed25519PrivateKey.generate()
    private, public = tmp_path / "second.pem", tmp_path / "second.pub.pem"
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                     serialization.PublicFormat.SubjectPublicKeyInfo))
    options = IngestOptions(**{**vars(title.options), "key": str(private), "pub": str(public)})
    second = ingest_title(title.source, title.workdir, options)
    assert "analyze:wcag" in second.steps_run
    assert second.publishable, second.verify_report
    document = json.loads(second.layout.map_path("wcag").read_text())
    assert document["signature"]["key_id"] == signer_key_id(private) != signer_key_id(title.private)


@needs_ffmpeg
def test_interruption_before_a_step_commits_leaves_no_record_and_the_next_run_recovers(title, monkeypatch):
    expected = reference(title)
    real = ingest_module.package_hls

    def interrupted(*args, **kwargs):
        # The packager wrote its files and then the process stopped, with one
        # segment cut short, before the rendition step could commit.
        real(*args, **kwargs)
        segment = sorted(Path(kwargs["out_dir"]).glob("seg_*.ts"))[0]
        segment.write_bytes(segment.read_bytes()[:100])
        raise Interrupted

    monkeypatch.setattr(ingest_module, "package_hls", interrupted)
    with pytest.raises(Interrupted):
        ingest_title(title.source, title.workdir, title.options)
    layout = TitleLayout(title.workdir.absolute(), expected["report"]["sha256"])
    ledger = Ledger(layout.root)
    assert ledger.get("plan:wcag") is not None
    assert ledger.get("rendition:wcag") is None
    assert layout.safe_master("wcag").exists()
    assert kid_mode_titles(layout.index_path) == []
    monkeypatch.setattr(ingest_module, "package_hls", real)
    recovered = ingest_title(title.source, title.workdir, title.options)
    assert "plan:wcag" in recovered.steps_skipped
    assert "rendition:wcag" in recovered.steps_run
    assert snapshot(recovered.layout) == expected
    assert recovered.publishable


@needs_ffmpeg
def test_interrupting_a_rebuild_of_a_recorded_step_withdraws_its_old_record(title, monkeypatch):
    first = ingest_title(title.source, title.workdir, title.options)
    before = snapshot(first.layout)
    first.layout.safe_master("wcag").unlink()
    real = ingest_module.render_safe_master

    def interrupted(*args, **kwargs):
        real(*args, **kwargs)
        out = Path(kwargs["out_path"])
        out.write_bytes(out.read_bytes()[: out.stat().st_size // 3])
        raise Interrupted

    monkeypatch.setattr(ingest_module, "render_safe_master", interrupted)
    with pytest.raises(Interrupted):
        ingest_title(title.source, title.workdir, title.options)
    # The half written master is on disk, and no record vouches for it.
    assert first.layout.safe_master("wcag").exists()
    assert Ledger(first.layout.root).get("rendition:wcag") is None
    assert kid_mode_titles(first.layout.index_path) == []
    monkeypatch.setattr(ingest_module, "render_safe_master", real)
    recovered = ingest_title(title.source, title.workdir, title.options)
    assert recovered.steps_run == ["rendition:wcag"]
    assert snapshot(recovered.layout) == before
    assert recovered.publishable


@needs_ffmpeg
def test_interruption_after_a_step_commits_keeps_that_step(title, monkeypatch):
    expected = reference(title)
    real = ingest_module.extract_cover_still

    def interrupted(*args, **kwargs):
        raise Interrupted

    monkeypatch.setattr(ingest_module, "extract_cover_still", interrupted)
    with pytest.raises(Interrupted):
        ingest_title(title.source, title.workdir, title.options)
    monkeypatch.setattr(ingest_module, "extract_cover_still", real)
    recovered = ingest_title(title.source, title.workdir, title.options)
    assert recovered.steps_skipped == ["probe", "analyze:wcag", "plan:wcag", "luma"]
    assert recovered.steps_run[0] == "still"
    assert snapshot(recovered.layout) == expected
    assert recovered.publishable


@needs_ffmpeg
def test_a_truncated_ledger_is_moved_aside_and_the_title_is_prepared_again(title):
    first = ingest_title(title.source, title.workdir, title.options)
    before = snapshot(first.layout)
    ledger_path = first.layout.root / LEDGER_NAME
    torn = ledger_path.read_bytes()[: ledger_path.stat().st_size // 2]
    ledger_path.write_bytes(torn)
    second = ingest_title(title.source, title.workdir, title.options)
    assert [event["event"] for event in second.ledger_events] == ["ledger_malformed", "ledger_moved_aside"]
    assert (first.layout.root / MALFORMED_NAME).read_bytes() == torn
    assert second.steps_skipped == []
    assert snapshot(second.layout) == before
    assert second.publishable


@needs_ffmpeg
def test_a_second_invocation_refuses_while_the_title_is_being_prepared(title):
    first = ingest_title(title.source, title.workdir, title.options)
    watched = [first.layout.root / LEDGER_NAME, first.layout.entry_path, first.layout.index_path]
    before = {path: path.read_bytes() for path in watched}
    with exclusive_lock(first.layout.ingest_lock_path, what="test holder"):
        with pytest.raises(LockBusy):
            ingest_title(title.source, title.workdir, title.options)
        completed = subprocess.run(
            [sys.executable, "-m", "pipeline.ingest", str(title.source), "--workdir", str(title.workdir),
             "--presets", "wcag", "--key", str(title.private), "--pub", str(title.public)],
            capture_output=True, text=True, cwd=REPO_ROOT, check=False,
        )
    assert completed.returncode == 1
    assert "busy in another process" in completed.stderr
    assert {path: path.read_bytes() for path in watched} == before


@needs_ffmpeg
def test_failed_verification_publishes_nothing_and_is_never_reused_as_a_pass(title):
    title.analyzer.flag("safe.mp4", segments_all=[[2000, 2500, "general"]])
    title.analyzer.plan["rules"].insert(0, title.analyzer.plan["rules"].pop())
    title.analyzer.write()
    first = ingest_title(title.source, title.workdir, title.options)
    assert not first.verify_passed
    assert first.entry.status == STATUS_FAILED
    assert kid_mode_titles(first.layout.index_path) == []
    assert Ledger(first.layout.root).get("verify").extra["passed"] is False
    again = ingest_title(title.source, title.workdir, title.options)
    assert again.steps_run == ["verify"]
    assert not again.publishable
    # Once the rendition measures clean, the same cached work publishes.
    title.analyzer.plan["rules"].pop(0)
    title.analyzer.write()
    fixed = ingest_title(title.source, title.workdir, title.options)
    assert fixed.steps_run == ["verify"]
    assert fixed.publishable
    assert read_entry(fixed.layout.entry_path).status == STATUS_VERIFIED


@needs_ffmpeg
def test_bytes_that_change_during_verification_are_never_published(title, monkeypatch):
    first = ingest_title(title.source, title.workdir, title.options)
    before = snapshot(first.layout)
    first.layout.verify_report_path.unlink()
    real = ingest_module.verify_title

    def racing(layout, **kwargs):
        report = real(layout, **kwargs)
        _flip_byte(layout.safe_master("wcag"))
        return report

    monkeypatch.setattr(ingest_module, "verify_title", racing)
    with pytest.raises(PipelineError, match="changed while verify"):
        ingest_title(title.source, title.workdir, title.options)
    assert kid_mode_titles(first.layout.index_path) == []
    assert Ledger(first.layout.root).get("verify") is None
    monkeypatch.setattr(ingest_module, "verify_title", real)
    recovered = ingest_title(title.source, title.workdir, title.options)
    assert recovered.steps_run == ["rendition:wcag", "verify"]
    assert snapshot(recovered.layout) == before
    assert recovered.publishable


@needs_ffmpeg
def test_publication_flushes_the_checked_bytes_before_the_verdict_is_written(title, monkeypatch):
    order: list[str] = []
    flushed: set[str] = set()
    real_sync, real_apply = ingest_module.sync_files, ingest_module.apply_to_catalog

    def sync(paths):
        paths = list(paths)
        order.append("flush artifacts")
        flushed.update(Path(path).name for path in paths)
        return real_sync(paths)

    def apply(layout, report):
        order.append("publish")
        return real_apply(layout, report)

    monkeypatch.setattr(ingest_module, "sync_files", sync)
    monkeypatch.setattr(ingest_module, "apply_to_catalog", apply)
    result = ingest_title(title.source, title.workdir, title.options)
    assert result.publishable
    assert order == ["flush artifacts", "publish"]
    assert {"safe.mp4", "master.m3u8", "wcag.json", "probe.json", "still.png", "hold_000.jpg"} <= flushed


@needs_ffmpeg
@pytest.mark.parametrize("phase", ["verification", "cached_publication"])
def test_scene_image_changed_after_check_is_never_published(title, monkeypatch, phase):
    first = ingest_title(title.source, title.workdir, title.options)
    assert first.publishable
    image = first.layout.scene_image("wcag", 0)
    record = Ledger(first.layout.root).get("verify")
    assert record.extra["artifact_sha256"][first.layout.relative(image)] == sha256_file(image)
    if phase == "verification":
        first.layout.verify_report_path.unlink()
        real = ingest_module.verify_title

        def late_writer(layout, **kwargs):
            report = real(layout, **kwargs)
            assert report.passed
            _flip_byte(image)
            return report

        monkeypatch.setattr(ingest_module, "verify_title", late_writer)
    else:
        real_sync = ingest_module.sync_files

        def late_flush(paths):
            count = real_sync(paths)
            _flip_byte(image)
            return count

        monkeypatch.setattr(ingest_module, "sync_files", late_flush)
    with pytest.raises(PipelineError, match="prepared artifacts changed"):
        ingest_title(title.source, title.workdir, title.options)
    assert kid_mode_titles(first.layout.index_path) == []


@needs_ffmpeg
def test_a_relative_work_directory_reuses_finished_work(title, monkeypatch):
    monkeypatch.chdir(title.tmp)
    first = ingest_title(title.source, "out", title.options)
    assert first.publishable
    second = ingest_title(title.source, "out", title.options)
    assert second.steps_run == []
    assert second.publishable


@needs_ffmpeg
def test_a_receipt_only_names_bytes_that_verification_checked(title, monkeypatch):
    real = library.ingest_title

    def orphan_writer(*args, **kwargs):
        # Stands in for an encoder left running by a killed run, writing after the
        # verdict and before the receipt is issued.
        result = real(*args, **kwargs)
        segment = sorted(result.layout.hls_dir("wcag").glob("seg_*.ts"))[0]
        _flip_byte(segment)
        return result

    monkeypatch.setattr(library, "ingest_title", orphan_writer)
    receipt = library.prepare_local_title(title.source, title.workdir, key=title.private,
                                          pub=title.public, presets=["wcag", "broadcast"])
    assert receipt["status"] == "failed"
    assert receipt["artifacts"] == {}
    assert receipt["error"]["message"] == "A prepared artifact is not the file verification checked."
    assert library.refresh_local_catalog(title.workdir)["titles"] == []
    monkeypatch.setattr(library, "ingest_title", real)
    again = library.prepare_local_title(title.source, title.workdir, key=title.private,
                                        pub=title.public, presets=["wcag", "broadcast"])
    assert again["status"] == "ready"


# Real processes, really killed.


def _prepare_command(title) -> list[str]:
    return [sys.executable, "-m", "pipeline.local_library", "prepare", str(title.source),
            "--workdir", str(title.workdir), "--key", str(title.private), "--pub", str(title.public),
            "--presets", "wcag,broadcast", "--title", "Calm test"]


def _kill_when_blocked(title, rule: dict) -> None:
    """Start a real preparation, wait until it stops at ``rule``, then SIGKILL its group."""
    marker = Path(rule["marker"])
    title.analyzer.plan["block"] = [rule]
    title.analyzer.write()
    process = subprocess.Popen(_prepare_command(title), cwd=REPO_ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    deadline = time.monotonic() + 120
    while not marker.exists():
        if process.poll() is not None:
            out, err = process.communicate()
            pytest.fail(f"the preparation ended before it reached the kill point: {out}{err}")
        if time.monotonic() > deadline:
            os.killpg(process.pid, signal.SIGKILL)
            pytest.fail("the preparation never reached the kill point")
        time.sleep(0.05)
    os.killpg(process.pid, signal.SIGKILL)
    process.communicate(timeout=30)
    assert process.returncode == -signal.SIGKILL
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            pass  # macOS answers EPERM while killed children wait to be reaped
        time.sleep(0.05)
    else:
        pytest.fail("a process from the killed preparation is still running")
    title.analyzer.plan.pop("block")
    title.analyzer.write()


def _prepare(title) -> dict:
    completed = subprocess.run(_prepare_command(title), cwd=REPO_ROOT, capture_output=True,
                               text=True, check=False)
    return json.loads(completed.stdout)


def _receipt_state(title, sha: str) -> tuple[str, list]:
    receipt = json.loads((title.workdir / library.RECEIPTS_DIR / f"{sha}.json").read_text())
    return receipt["status"], json.loads((title.workdir / library.CATALOG_NAME).read_text())["titles"]


@needs_ffmpeg
def test_sigkill_after_a_step_commit_resumes_from_the_ledger_and_is_never_ready_meanwhile(title):
    expected = _prepare(title)
    assert expected["status"] == "ready"
    sha = expected["source_sha256"]
    layout = TitleLayout(title.workdir, sha)
    identity = snapshot(layout)
    title.workdir.rename(title.tmp / "uninterrupted")
    _kill_when_blocked(title, {"match": "calm.mp4", "profile": "broadcast", "partial_bytes": 300,
                               "marker": str(title.tmp / "blocked"), "seconds": 120})
    ledger = Ledger(layout.root)
    committed = ledger.get("analyze:wcag")
    assert committed is not None
    assert ledger.get("analyze:broadcast") is None
    assert layout.analysis_map_path("broadcast").stat().st_size == 300
    assert _receipt_state(title, sha) == ("failed", [])
    recovered = _prepare(title)
    assert recovered["status"] == "ready"
    assert Ledger(layout.root).get("analyze:wcag").completed_at == committed.completed_at
    assert snapshot(layout) == identity
    ignored = {"checked_inputs_sha256", "report_sha256"}
    assert ({k: v for k, v in recovered["verification"].items() if k not in ignored}
            == {k: v for k, v in expected["verification"].items() if k not in ignored})
    assert recovered["artifacts"] == expected["artifacts"]


@needs_ffmpeg
def test_sigkill_during_verification_redoes_only_verification(title):
    first = _prepare(title)
    assert first["status"] == "ready"
    layout = TitleLayout(title.workdir, first["source_sha256"])
    identity = snapshot(layout)
    before = {name: record.completed_at for name, record in Ledger(layout.root).steps.items()}
    layout.verify_report_path.unlink()
    _kill_when_blocked(title, {"match": "safe/broadcast/safe.mp4", "marker": str(title.tmp / "blocked"),
                               "seconds": 120})
    assert Ledger(layout.root).get("verify") is None
    assert _receipt_state(title, first["source_sha256"]) == ("failed", [])
    recovered = _prepare(title)
    assert recovered["status"] == "ready"
    after = {name: record.completed_at for name, record in Ledger(layout.root).steps.items()}
    assert [name for name in after if after[name] != before.get(name)] == ["verify"]
    assert snapshot(layout) == identity
    assert recovered["artifacts"] == first["artifacts"]
