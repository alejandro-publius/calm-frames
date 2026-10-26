"""Local receipt guards, plus an actual CLI run on generated benign media.

The stub preparer below only tests wrapper contracts. Its bytes and reports
are explicitly fabricated and are not analyzer, rendition or TV evidence.
The separate real CLI test invokes the unchanged pipeline and flashmap CLI.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from types import SimpleNamespace

import pytest

from pipeline import PipelineError
from pipeline import local_library as library
from pipeline.catalog import (
    STATUS_VERIFIED,
    CatalogEntry,
    RenditionEntry,
    update_index,
    write_entry,
)
from pipeline.hashing import sha256_file
from pipeline.ingest import IngestResult
from pipeline.layout import TitleLayout
from pipeline.state import Ledger
from pipeline.verify import OUTCOME_NO_FLAGGED_SEGMENTS, VerifyReport, write_report

from .clips import make_calm_clip
from .conftest import needs_ffmpeg


def _fabricated_verify_extra(layout, **overrides):
    """The verify record the real pipeline writes: its verdict and the bytes it checked."""
    extra = {
        "passed": True, "report_sha256": sha256_file(layout.verify_report_path),
        "artifact_sha256": {
            str(path.relative_to(layout.root)): sha256_file(path)
            for path in sorted(layout.root.rglob("*"))
            if path.is_file() and not path.is_symlink() and path.name != "state.json"
        },
    }
    extra.update(overrides)
    return extra


@pytest.fixture
def stub_workspace(tmp_path, monkeypatch, keypair):
    """Fabricated producer outputs for wrapper guard tests, never real media."""
    source = tmp_path / "fabricated-source.bin"
    source.write_bytes(b"FABRICATED WRAPPER CONTRACT SOURCE, NOT A VIDEO")
    root = tmp_path / "library"
    private, public = keypair
    state = SimpleNamespace(source=source, root=root, private=private, public=public,
                            presets=["wcag", "broadcast"], fault=None, calls=0, result=None)

    def prepare(source_path, workdir, options, *, adapter=None):
        state.calls += 1
        assert options.skip_verify is False
        assert options.presets == state.presets
        assert options.key == str(private.resolve())
        assert options.pub == str(public.resolve())
        layout = TitleLayout(workdir, sha256_file(source_path))
        layout.root.mkdir(parents=True, exist_ok=True)
        for path in (layout.probe_path, layout.still_path, layout.still_manifest_path):
            path.write_bytes(b"FABRICATED WRAPPER INPUT")
        renditions = {}
        for preset in options.presets:
            files = (
                layout.safe_master(preset), layout.map_path(preset), layout.plan_path(preset),
                layout.bif_path(preset), layout.bif_manifest(preset),
                layout.posters_manifest(preset), layout.cover_model_path(preset),
                layout.scene_image(preset, 0), layout.scene_manifest(preset),
            )
            for path in files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"FABRICATED WRAPPER ARTIFACT, NOT MEDIA OR A SIGNED MAP")
            hls = layout.hls_dir(preset)
            hls.mkdir(parents=True, exist_ok=True)
            (hls / "master.m3u8").write_text("#EXTM3U\nstream_0.m3u8\n")
            (hls / "stream_0.m3u8").write_text("#EXTM3U\n#EXTINF:1,\nseg_0_00000.ts\n#EXT-X-ENDLIST\n")
            (hls / "seg_0_00000.ts").write_bytes(b"FABRICATED TRANSPORT BYTES")
            renditions[preset] = RenditionEntry(
                preset=preset, safe_master=str(layout.safe_master(preset)),
                master_playlist=str(layout.master_playlist(preset)),
                map_path=str(layout.map_path(preset)), plan_path=str(layout.plan_path(preset)),
                bif_path=str(layout.bif_path(preset)), bif_manifest=str(layout.bif_manifest(preset)),
            )
        report = VerifyReport(layout.sha256, f"sha256:{layout.sha256}", options.presets)
        report.add("source_hash", True, "FABRICATED WRAPPER CHECK")
        for preset in options.presets:
            for name in library._CORE_CHECKS:
                report.add(f"{name}:{preset}", True, "FABRICATED WRAPPER CHECK")
        write_report(layout, report)
        entry = CatalogEntry(
            sha256=layout.sha256, title=options.title, source_name=source_path.name,
            duration_s=1, width=160, height=90, status=STATUS_VERIFIED, verified=True,
            verify_report=str(layout.verify_report_path), renditions=renditions,
        )
        write_entry(layout.entry_path, entry)
        update_index(layout.index_path, entry)
        ledger = Ledger(layout.root)
        ledger.record("verify", "fabricated-wrapper-record", [layout.verify_report_path],
                      _fabricated_verify_extra(layout))
        result = IngestResult(layout.sha256, source_path, layout, entry,
                              verify_passed=True, verify_report=report.to_dict())
        state.result = result
        if state.fault is not None:
            state.fault(result)
        return result

    monkeypatch.setattr(library, "ingest_title", prepare)

    def run():
        return library.prepare_local_title(source, root, key=private, pub=public,
                                           title="Fabricated wrapper title", presets=state.presets)

    state.run = run
    return state


def _replace_report(result, change):
    data = json.loads(result.layout.verify_report_path.read_text())
    change(data)
    result.layout.verify_report_path.write_text(json.dumps(data))
    result.verify_report = data
    Ledger(result.layout.root).record(
        "verify", "fabricated-wrapper-record", [result.layout.verify_report_path],
        _fabricated_verify_extra(result.layout),
    )


def _assert_failed(state, receipt):
    assert receipt["status"] == "failed"
    assert receipt["artifacts"] == {}
    assert library.refresh_local_catalog(state.root)["titles"] == []


def test_stub_receipt_only_exposes_prepared_outputs_and_snapshot_is_deterministic(stub_workspace):
    state = stub_workspace
    receipt = state.run()
    assert receipt["status"] == "ready"
    assert receipt["readiness"] == library.READY_MESSAGE
    assert receipt["presets"] == state.presets
    assert receipt["verification"]["status"] == "passed"
    assert receipt["verification"]["outcome"] == OUTCOME_NO_FLAGGED_SEGMENTS
    assert receipt["app_shelf_connected"] is False
    assert receipt["physical_tv_validated"] is False
    text = json.dumps(receipt)
    assert str(state.private) not in text
    assert state.private.read_text() not in text
    assert str(state.source) not in text
    assert str(state.result.layout.cover_model_path("wcag")) not in text
    assert not list(state.root.rglob("*.pem"))
    assert library.refresh_local_catalog(state.root)["titles"] == [receipt]
    first = (state.root / library.CATALOG_NAME).read_bytes()
    library.refresh_local_catalog(state.root)
    assert (state.root / library.CATALOG_NAME).read_bytes() == first


def test_report_identity_compares_the_actual_json_representation(stub_workspace):
    def geometry_tuple(result):
        _replace_report(result, lambda data: data["checks"][0]["data"].update(
            {"geometry": {"picture_coded": (0, 0, 160, 90)}}
        ))
    stub_workspace.fault = geometry_tuple
    assert stub_workspace.run()["status"] == "ready"


@pytest.mark.parametrize("fault", ["result_sha", "unverified", "not_publishable", "other_layout"])
def test_a_pipeline_result_is_not_ready_merely_because_artifacts_exist(stub_workspace, fault):
    def break_result(result):
        if fault == "result_sha":
            result.sha256 = "0" * 64
        elif fault == "unverified":
            result.verify_passed = False
        elif fault == "not_publishable":
            result.entry.verified = False
        else:
            result.layout = TitleLayout(result.layout.workdir / "elsewhere", result.sha256)
    stub_workspace.fault = break_result
    _assert_failed(stub_workspace, stub_workspace.run())


@pytest.mark.parametrize("fault", [
    "missing_report", "source_sha", "source_path", "media_identifier", "partial_presets", "passed_false",
    "empty_checks", "failed_check", "truthy_string", "missing_core", "duplicate_check",
    "ledger_missing", "ledger_report_hash", "result_report_mismatch",
])
def test_report_must_be_current_complete_and_belong_to_the_source(stub_workspace, fault):
    def break_report(result):
        if fault == "missing_report":
            result.layout.verify_report_path.unlink()
        elif fault in {"ledger_missing", "ledger_report_hash"}:
            ledger = Ledger(result.layout.root)
            if fault == "ledger_missing":
                ledger.forget("verify")
            else:
                ledger.record("verify", "fabricated-wrapper-record", [],
                              {"passed": True, "report_sha256": "0" * 64})
        elif fault == "result_report_mismatch":
            result.verify_report = {**result.verify_report, "source_path": "other"}
        else:
            def change(data):
                if fault == "source_sha":
                    data["sha256"] = "0" * 64
                elif fault == "source_path":
                    data["source_path"] = str(stub_workspace.source.with_name("other.bin"))
                elif fault == "media_identifier":
                    data["source_path"] = "sha256:" + "0" * 64
                elif fault == "partial_presets":
                    data["presets"] = ["wcag"]
                elif fault == "passed_false":
                    data["passed"] = False
                elif fault == "empty_checks":
                    data["checks"] = []
                elif fault == "failed_check":
                    data["checks"][0]["passed"] = False
                elif fault == "truthy_string":
                    data["checks"][0]["passed"] = "yes"
                elif fault == "missing_core":
                    data["checks"] = data["checks"][:-1]
                else:
                    data["checks"].append(dict(data["checks"][0]))
            _replace_report(result, change)
    stub_workspace.fault = break_report
    _assert_failed(stub_workspace, stub_workspace.run())


@pytest.mark.parametrize("target", ["private", "source", "cover_model", "outside", "traversal"])
def test_catalog_paths_cannot_publish_keys_original_media_or_models(stub_workspace, target):
    state = stub_workspace
    def break_entry(result):
        choices = {
            "private": state.private, "source": state.source,
            "cover_model": result.layout.cover_model_path("wcag"),
            "outside": state.root.parent / "outside.mp4",
            "traversal": result.layout.safe_dir("wcag") / ".." / "wcag" / "safe.mp4",
        }
        result.entry.renditions["wcag"].safe_master = str(choices[target])
        write_entry(result.layout.entry_path, result.entry)
    state.fault = break_entry
    _assert_failed(state, state.run())


@pytest.mark.parametrize("reference", [
    "../../../../original.mp4", "/tmp/original.mp4", "https://example.test/original.mp4",
    "../maps/wcag.json", "private.pem",
])
def test_hls_references_cannot_leave_the_prepared_output_allowlist(stub_workspace, reference):
    stub_workspace.fault = lambda result: result.layout.master_playlist("wcag").write_text(
        f'#EXTM3U\n#EXT-X-MEDIA:TYPE=SUBTITLES,URI="{reference}"\nstream_0.m3u8\n'
    )
    _assert_failed(stub_workspace, stub_workspace.run())


@pytest.mark.parametrize("target", ["private", "source", "cover_model", "hardlink"])
def test_existing_unsafe_artifact_links_are_rejected_before_ingest(stub_workspace, target):
    state = stub_workspace
    assert state.run()["status"] == "ready"
    safe = state.result.layout.safe_master("wcag")
    outside = state.private if target in {"private", "hardlink"} else (
        state.source if target == "source" else state.result.layout.cover_model_path("wcag")
    )
    sentinel = outside.read_bytes()
    safe.unlink()
    if target == "hardlink":
        os.link(outside, safe)
    else:
        safe.symlink_to(outside)
    _assert_failed(state, state.run())
    assert state.calls == 1
    assert outside.read_bytes() == sentinel


@pytest.mark.parametrize("name", ["catalog.json", "catalog.json.tmp"])
def test_pipeline_shared_catalog_links_cannot_write_an_external_sentinel(stub_workspace, name):
    state = stub_workspace
    state.root.mkdir()
    sentinel = state.root.parent / "external-sentinel.json"
    sentinel.write_text('{"sentinel": "must not change"}')
    (state.root / name).symlink_to(sentinel)
    receipt = state.run()
    assert sentinel.read_text() == '{"sentinel": "must not change"}'
    _assert_failed(state, receipt)
    assert state.calls == 0


@pytest.mark.parametrize("artifact", [
    "safe", "map", "hls", "report", "probe", "model", "entry", "ledger", "scene_image",
])
def test_catalog_refresh_withdraws_a_receipt_when_any_recorded_input_changes(stub_workspace, artifact):
    state = stub_workspace
    assert state.run()["status"] == "ready"
    layout = state.result.layout
    path = {
        "safe": layout.safe_master("wcag"), "map": layout.map_path("wcag"),
        "hls": layout.hls_dir("wcag") / "seg_0_00000.ts", "report": layout.verify_report_path,
        "probe": layout.probe_path, "model": layout.cover_model_path("wcag"),
        "entry": layout.entry_path, "ledger": layout.root / "state.json",
        "scene_image": layout.scene_image("wcag", 0),
    }[artifact]
    path.write_bytes(path.read_bytes() + b"\n ")
    assert library.refresh_local_catalog(state.root)["titles"] == []


def test_catalog_refresh_rejects_added_unapproved_receipt_fields(stub_workspace):
    state = stub_workspace
    receipt = state.run()
    path = state.root / library.RECEIPTS_DIR / f'{receipt["source_sha256"]}.json'
    receipt["source_master"] = str(state.source)
    path.write_text(json.dumps(receipt))
    assert library.refresh_local_catalog(state.root)["titles"] == []


@pytest.mark.parametrize("field", ["private_key", "source_path", "cover_model"])
def test_catalog_refresh_does_not_export_unapproved_verification_fields(stub_workspace, field):
    state = stub_workspace
    receipt = state.run()
    path = state.root / library.RECEIPTS_DIR / f'{receipt["source_sha256"]}.json'
    receipt["verification"][field] = str(state.private)
    path.write_text(json.dumps(receipt))
    assert library.refresh_local_catalog(state.root)["titles"] == []
    assert str(state.private) not in (state.root / library.CATALOG_NAME).read_text()


def test_a_ready_receipt_cannot_claim_failed_checks(stub_workspace):
    state = stub_workspace
    receipt = state.run()
    path = state.root / library.RECEIPTS_DIR / f'{receipt["source_sha256"]}.json'
    receipt["verification"]["failed_checks"] = [{"private_key": str(state.private)}]
    path.write_text(json.dumps(receipt))
    assert library.refresh_local_catalog(state.root)["titles"] == []


def test_failed_reimport_withdraws_old_ready_item_and_does_not_export_engine_secrets(stub_workspace, monkeypatch):
    state = stub_workspace
    assert state.run()["status"] == "ready"
    def fail(*args, **kwargs):
        assert json.loads((state.root / library.CATALOG_NAME).read_text())["titles"] == []
        receipt = state.root / library.RECEIPTS_DIR / f'{state.result.sha256}.json'
        assert json.loads(receipt.read_text())["status"] == "failed"
        raise PipelineError(f"private command {state.private}: {state.private.read_text()}")
    monkeypatch.setattr(library, "ingest_title", fail)
    receipt = state.run()
    _assert_failed(state, receipt)
    assert receipt["verification"]["status"] == "not_completed"
    text = json.dumps(receipt)
    assert state.private.read_text() not in text
    assert str(state.private) not in text


def test_overlapping_cli_import_refuses_without_changing_active_workspace(stub_workspace):
    state = stub_workspace
    state.run()
    before = (state.root / library.CATALOG_NAME).read_bytes()
    with library._lock(state.root):
        completed = subprocess.run(
            [sys.executable, "-m", "pipeline.local_library", "prepare", str(state.source),
             "--workdir", str(state.root), "--key", str(state.private), "--pub", str(state.public)],
            capture_output=True, text=True, check=False,
        )
    assert completed.returncode == 2
    answer = json.loads(completed.stdout)
    assert answer["status"] == "failed"
    assert "busy" in answer["error"]["message"]
    assert (state.root / library.CATALOG_NAME).read_bytes() == before


@pytest.mark.parametrize("bound", ["MAX_METADATA_BYTES", "MAX_TITLE_FILES", "MAX_TITLES"])
def test_workspace_bookkeeping_is_bounded_without_publishing(stub_workspace, monkeypatch, bound):
    state = stub_workspace
    monkeypatch.setattr(library, bound, 1)
    if bound == "MAX_TITLES":
        state.root.mkdir()
        receipts = state.root / library.RECEIPTS_DIR
        receipts.mkdir()
        (receipts / f'{"0" * 64}.json').write_text("{}")
        with pytest.raises(library.LocalLibraryError, match="too many receipts"):
            state.run()
    else:
        _assert_failed(state, state.run())


@needs_ffmpeg
def test_real_cli_prepares_all_presets_with_actual_analyzer_and_no_source_publication(tmp_path, keypair):
    private, public = keypair
    source = make_calm_clip(tmp_path / "benign-local-story.mp4", seconds=2, fps=10,
                            width=160, height=90, subtitles=True)
    root = tmp_path / "real-library"
    environment = os.environ.copy()
    environment["CALM_FRAMES_FLASHMAP_CMD"] = f"{shlex.quote(sys.executable)} -m flashmap"
    environment.pop("FAKE_FLASHMAP_PLAN", None)
    completed = subprocess.run(
        [sys.executable, "-m", "pipeline.local_library", "prepare", str(source),
         "--workdir", str(root), "--key", str(private), "--pub", str(public),
         "--title", "Benign local story"],
        capture_output=True, text=True, env=environment, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["status"] == "ready"
    assert receipt["source_sha256"] == sha256_file(source)
    assert receipt["presets"] == list(library.PRESETS)
    assert receipt["verification"]["outcome"] == OUTCOME_NO_FLAGGED_SEGMENTS
    assert receipt["app_shelf_connected"] is False
    assert receipt["physical_tv_validated"] is False
    report = json.loads((root / receipt["verification"]["report"]).read_text())
    checks = {check["name"]: check["passed"] for check in report["checks"]}
    for preset in library.PRESETS:
        artifacts = receipt["artifacts"][preset]
        assert (root / artifacts["safe_master"]).is_file()
        assert (root / artifacts["master_playlist"]).is_file()
        document = json.loads((root / artifacts["map"]).read_text())
        assert document["generator"]["name"] == "flashmap"
        assert document["signature"]["algorithm"] == "ed25519"
        assert "scene_holds" not in document
        for name in (*library._CORE_CHECKS, "bif_calm", "posters_calm"):
            assert checks[f"{name}:{preset}"] is True
    assert not list(root.rglob("*.pem"))
    assert str(source) not in completed.stdout
    assert str(private) not in completed.stdout
    assert private.read_text() not in completed.stdout
    assert library.refresh_local_catalog(root)["titles"] == [receipt]
