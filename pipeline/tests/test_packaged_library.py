"""Package contracts use fabricated media; real CLI integration is separate."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline import packaged_library as packaged
from pipeline.hashing import sha256_file
from pipeline.hideplan import HidePlan
from pipeline.registry import load_private_key, sign_document, write_registry

from .test_local_library import _replace_report, stub_workspace  # noqa: F401


@pytest.fixture
def ready(stub_workspace, monkeypatch, tmp_path):
    state = stub_workspace
    state.presets = list(packaged.PRESETS)
    state.output = tmp_path / "package"
    def artifacts(result):
        for preset in state.presets:
            doc = {"version": 1, "source": {"sha256": result.sha256, "duration_ms": 1000},
                   "profile": {"name": "broadcast" if preset == "broadcast" else "wcag"},
                   "segments": [], "summary": {"pass": True, "segment_count": 0}}
            write_registry(sign_document(doc, load_private_key(state.private)), result.layout.map_path(preset))
            plan = HidePlan(preset, result.sha256, 500, 400, 1000, True, [])
            result.layout.plan_path(preset).write_text(json.dumps(plan.to_dict()))
        def offsets(data):
            for check in data["checks"]:
                if check["name"].startswith("rendition_matches_source:"):
                    check["data"]["start_offset_ms"] = 0
        _replace_report(result, offsets)
    state.fault = artifacts
    monkeypatch.setattr(packaged, "probe_video", lambda _path: SimpleNamespace(duration_ms=1000, subtitle_streams=[]))
    assert state.run()["status"] == "ready"
    return state


def export(state):
    return packaged.export_packaged_library(state.root, state.output, pub=state.public)


def test_private_report_is_rejected_before_replacing_catalog_and_without_rewriting_evidence(ready):
    export(ready)
    before = (ready.output / "catalog.ts").read_bytes()
    _replace_report(ready.result, lambda data: data.update(source_path="/Users/fictional/clip.mp4"))
    path = ready.result.layout.verify_report_path
    original = path.read_bytes()
    receipt_path = ready.root / "local-receipts" / f"{ready.result.sha256}.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["verification"]["report_sha256"] = sha256_file(path)
    receipt["verification"]["checked_inputs_sha256"] = packaged.local._inputs_digest(ready.result.layout)
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(packaged.PackagedLibraryError, match="local filesystem path"):
        export(ready)
    assert path.read_bytes() == original
    assert (ready.output / "catalog.ts").read_bytes() == before


def test_complete_export_has_separate_source_and_delivered_hashes_and_no_source_or_key(ready):
    manifest = export(ready)
    title = manifest["titles"][0]
    assert title["sourceSha256"] == sha256_file(ready.source)
    assert title["id"] == "prepared-" + title["sourceSha256"]
    assert set(title["maps"]) == set(packaged.PRESETS)
    assert set(title["renditions"]) == set(packaged.PRESETS)
    for preset, rendition in title["renditions"].items():
        actual = ready.output / manifest["bundleId"] / rendition["path"]
        assert sha256_file(actual) == rendition["sha256"] != title["sourceSha256"]
        assert rendition["startOffsetMs"] == 0
        assert rendition["guardBandMs"] == packaged.TIMING[preset][0]
    assert packaged.check_packaged_library(ready.output) == manifest
    assert not list(ready.output.rglob("*.pem"))
    assert not any(path.name == ready.source.name for path in ready.output.rglob("*"))
    encoded = json.dumps(manifest)
    assert str(ready.source) not in encoded
    assert ready.private.read_text() not in encoded
    assert ready.public.read_text() not in encoded
    assert export(ready) == manifest


@pytest.mark.parametrize("kind", ["map", "media", "report", "plan", "receipt"])
def test_modified_preparation_cannot_replace_existing_export(ready, kind):
    manifest = export(ready)
    before = (ready.output / "catalog.ts").read_bytes()
    paths = {"map": ready.result.layout.map_path("wcag"),
             "media": ready.result.layout.safe_master("wcag"),
             "report": ready.result.layout.verify_report_path,
             "plan": ready.result.layout.plan_path("wcag"),
             "receipt": ready.root / "local-receipts" / f"{ready.result.sha256}.json"}
    paths[kind].write_text("changed")
    with pytest.raises(packaged.PackagedLibraryError):
        export(ready)
    assert (ready.output / "catalog.ts").read_bytes() == before
    assert packaged.check_packaged_library(ready.output) == manifest


def test_wrong_trusted_signer_and_partial_presets_refuse(ready, tmp_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    other = tmp_path / "other.pub.pem"
    other.write_bytes(Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    with pytest.raises(Exception, match="key|signed|public"):
        packaged.export_packaged_library(ready.root, ready.output, pub=other)
    assert not (ready.output / "catalog.ts").exists()
    ready.presets = ["wcag", "broadcast"]
    assert ready.run()["status"] == "ready"
    with pytest.raises(packaged.PackagedLibraryError, match="all three"):
        export(ready)


@pytest.mark.parametrize("changed", ["source", "profile"])
def test_valid_signature_does_not_override_required_source_and_profile(ready, changed):
    path = ready.result.layout.map_path("broadcast")
    document = json.loads(path.read_text())
    if changed == "source":
        document["source"]["sha256"] = "0" * 64
    else:
        document["profile"]["name"] = "wcag"
    write_registry(sign_document(document, load_private_key(ready.private)), path)
    receipt_path = ready.root / "local-receipts" / f"{ready.result.sha256}.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["artifacts"] = packaged.local._artifacts(ready.result.layout, ready.presets)
    receipt["verification"]["checked_inputs_sha256"] = packaged.local._inputs_digest(ready.result.layout)
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(packaged.PackagedLibraryError, match="wrong source or profile"):
        export(ready)


@pytest.mark.parametrize("change", ["module", "manifest", "missing", "bytes", "extra", "symlink", "hardlink"])
def test_package_checker_refuses_changed_or_unexpected_bytes(ready, tmp_path, change):
    manifest = export(ready)
    bundle = ready.output / manifest["bundleId"]
    media = bundle / manifest["titles"][0]["renditions"]["wcag"]["path"]
    if change == "module":
        (ready.output / "catalog.ts").write_text("export const PACKAGED_LIBRARY_JSON = '{}';")
    elif change == "manifest":
        (bundle / "manifest.json").write_text("{}")
    elif change == "missing":
        media.unlink()
    elif change == "bytes":
        media.write_bytes(b"CHANGED BYTES")
    elif change == "extra":
        (bundle / "private.pem").write_text("not a real key")
    else:
        other = tmp_path / "unowned.mp4"
        other.write_bytes(media.read_bytes())
        media.unlink()
        if change == "symlink":
            media.symlink_to(other)
        else:
            os.link(other, media)
    with pytest.raises(packaged.local.LocalLibraryError):
        packaged.check_packaged_library(ready.output)


@pytest.mark.parametrize("kind", ["output", "ancestor", "input"])
def test_symlink_roots_or_inputs_are_never_followed(ready, tmp_path, kind):
    if kind == "input":
        media = ready.result.layout.safe_master("wcag")
        outside = tmp_path / "unowned"
        outside.write_bytes(media.read_bytes())
        media.unlink()
        media.symlink_to(outside)
    elif kind == "output":
        other = tmp_path / "outside"
        other.mkdir()
        ready.output.symlink_to(other)
    else:
        parent = tmp_path / "alias"
        parent.symlink_to(tmp_path)
        ready.output = parent / "package"
    with pytest.raises(packaged.local.LocalLibraryError):
        export(ready)


def test_selected_missing_title_is_not_silently_omitted(ready):
    with pytest.raises(packaged.PackagedLibraryError, match="selected title"):
        packaged.export_packaged_library(ready.root, ready.output, pub=ready.public,
                                         source_shas=["0" * 64])


def test_stream_copy_hashes_the_bytes_read_instead_of_a_previous_filename_hash(ready, tmp_path):
    destination = tmp_path / "copied.mp4"
    with pytest.raises(packaged.PackagedLibraryError, match="changed"):
        packaged._copy_checked(ready.result.layout.safe_master("wcag"), destination,
                               "0" * 64, ready.root)


def test_prepared_plan_must_include_both_profiles_and_extra_cautious_timing(ready):
    from pipeline.flashmap_adapter import MapSegment, load_map
    layout = ready.result.layout
    maps = {preset: load_map(layout.map_path(preset)) for preset in packaged.PRESETS}
    maps["wcag"].segments = [MapSegment(300, 400, "general")]
    with pytest.raises(packaged.PackagedLibraryError, match="complete cover schedule"):
        packaged.require_runtime_plan(layout, maps, "broadcast", 1000)
    maps["wcag"].segments = []
    maps["broadcast"].segments = [MapSegment(300, 400, "red")]
    with pytest.raises(packaged.PackagedLibraryError, match="complete cover schedule"):
        packaged.require_runtime_plan(layout, maps, "extra-cautious", 1000)


def test_empty_sentinel_is_explicit_and_cannot_hide_bundle_assets(tmp_path):
    text = '{"version":1,"titles":[]}'
    (tmp_path / "catalog.json").write_text(text)
    (tmp_path / "catalog.ts").write_text(packaged.catalog_module(text))
    assert packaged.check_packaged_library(tmp_path) == {"version": 1, "titles": []}
    (tmp_path / "unexpected.mp4").write_bytes(b"not media")
    with pytest.raises(packaged.PackagedLibraryError, match="empty library"):
        packaged.check_packaged_library(tmp_path)


@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("change", ["bytes", "symlink", "hardlink", "directory"])
def test_export_lock_cannot_carry_unreviewed_data_or_aliases(ready, tmp_path, empty, change):
    if empty:
        ready.output.mkdir()
        text = '{"version":1,"titles":[]}'
        (ready.output / "catalog.json").write_text(text)
        (ready.output / "catalog.ts").write_text(packaged.catalog_module(text))
    else:
        export(ready)
    lock = ready.output / ".local-library.lock"
    lock.unlink(missing_ok=True)
    if change == "bytes":
        lock.write_bytes(b"UNREVIEWED DATA")
    elif change == "directory":
        lock.mkdir()
    else:
        outside = tmp_path / "external-lock"
        outside.write_bytes(b"")
        if change == "symlink":
            lock.symlink_to(outside)
        else:
            os.link(outside, lock)
    with pytest.raises(packaged.local.LocalLibraryError):
        packaged.check_packaged_library(ready.output)


def test_entire_output_namespace_is_checked_including_retained_generations(ready):
    original = export(ready)
    receipt_path = ready.root / "local-receipts" / f"{ready.result.sha256}.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["title"] = "Another title for the same checked artifact"
    receipt_path.write_text(json.dumps(receipt))
    current = export(ready)
    assert current["bundleId"] != original["bundleId"]
    assert packaged.check_packaged_library(ready.output) == current
    old = ready.output / original["bundleId"] / original["titles"][0]["renditions"]["wcag"]["path"]
    old.write_bytes(b"CHANGED RETAINED BYTES")
    with pytest.raises(packaged.PackagedLibraryError, match="differs"):
        packaged.check_packaged_library(ready.output)


def test_arbitrary_sibling_file_never_ships_unchecked(ready):
    export(ready)
    (ready.output / "unexpected.bin").write_bytes(b"UNEXPECTED")
    with pytest.raises(packaged.PackagedLibraryError, match="unexpected file"):
        packaged.check_packaged_library(ready.output)
    with pytest.raises(packaged.PackagedLibraryError, match="unexpected file"):
        export(ready)


def test_retained_generation_byte_budget_applies_before_publication(ready, monkeypatch):
    export(ready)
    before = (ready.output / "catalog.ts").read_bytes()
    receipt_path = ready.root / "local-receipts" / f"{ready.result.sha256}.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["title"] = "A second generation"
    receipt_path.write_text(json.dumps(receipt))
    size = sum(path.stat().st_size for path in ready.output.rglob("*") if path.is_file())
    monkeypatch.setattr(packaged, "MAX_BUNDLE_BYTES", size + 1)
    with pytest.raises(packaged.PackagedLibraryError, match="byte budget"):
        export(ready)
    assert (ready.output / "catalog.ts").read_bytes() == before
    assert not list(ready.output.glob(".stage-*"))


def test_export_retains_original_report_bytes_without_changing_the_media_manifest(ready):
    manifest = export(ready)
    digest = manifest["titles"][0]["verification"]["reportSha256"]
    assert (ready.output / "reports" / f"{digest}.json").read_bytes() == ready.result.layout.verify_report_path.read_bytes()
    assert not any(name.startswith("reports/") for name in manifest["files"])
    assert packaged.check_packaged_library(ready.output, require_reports=True) == manifest
    assert packaged.verification_report_status(ready.output) == {"required": 1, "present": 1, "missing": []}


def test_missing_legacy_report_is_explicit_and_exact_backfill_is_idempotent(ready):
    manifest = export(ready)
    digest = manifest["titles"][0]["verification"]["reportSha256"]
    shutil.rmtree(ready.output / "reports")
    before = {str(path.relative_to(ready.output)): path.read_bytes()
              for path in ready.output.rglob("*") if path.is_file()}
    assert packaged.check_packaged_library(ready.output) == manifest
    assert packaged.verification_report_status(ready.output) == {"required": 1, "present": 0, "missing": [digest]}
    with pytest.raises(packaged.PackagedLibraryError, match="Original verification reports are missing"):
        packaged.check_packaged_library(ready.output, require_reports=True)
    for _ in range(2):
        assert packaged.attach_reports(ready.output, [ready.result.layout.verify_report_path]) == manifest
    assert all((ready.output / name).read_bytes() == raw for name, raw in before.items())
    assert packaged.check_packaged_library(ready.output, require_reports=True) == manifest


def test_backfill_preflights_every_input_and_rejects_reserialized_reports(ready, tmp_path):
    export(ready)
    shutil.rmtree(ready.output / "reports")
    original = ready.result.layout.verify_report_path
    different = tmp_path / "different.json"
    different.write_bytes(original.read_bytes() + b"\n")
    with pytest.raises(packaged.PackagedLibraryError, match="not referenced"):
        packaged.attach_reports(ready.output, [original, different])
    assert not (ready.output / "reports").exists()
    packaged.attach_reports(ready.output, [original])
    report = next((ready.output / "reports").iterdir())
    report.write_bytes(report.read_bytes() + b"\n")
    with pytest.raises(packaged.PackagedLibraryError, match="report bytes differ"):
        packaged.check_packaged_library(ready.output)


@pytest.mark.parametrize("change", ["source", "presets", "failed", "missing", "duplicate", "outcome", "derived", "plan", "key"])
def test_report_identity_does_not_override_its_required_evidence(ready, change):
    manifest = export(ready)
    title = manifest["titles"][0]
    data = json.loads(ready.result.layout.verify_report_path.read_bytes())
    if change == "source":
        data["sha256"] = "0" * 64
    elif change == "presets":
        data["presets"] = ["wcag"]
    elif change == "failed":
        data["checks"][0]["passed"] = False
    elif change == "missing":
        data["checks"].pop()
    elif change == "duplicate":
        data["checks"].append(data["checks"][0])
    elif change == "outcome":
        data["outcome"] = "cover proven drawn"
    elif change == "derived":
        data["outcome"] = title["verification"]["outcome"] = "cover proven drawn"
    elif change == "plan":
        next(item for item in data["checks"] if item["name"] == "plan_matches_map:wcag")["data"]["stored"] = True
    else:
        data["source_path"] = "-----BEGIN PRIVATE KEY-----"
    raw = json.dumps(data).encode()
    digest = packaged.hashlib.sha256(raw).hexdigest()
    title["verification"]["reportSha256"] = digest
    # These are fabricated contract reports. Updating their digest deliberately
    # reaches the semantic guard instead of merely failing the byte comparison.
    with pytest.raises(packaged.PackagedLibraryError, match="report"):
        packaged._check_report(raw, digest, [title])


@pytest.mark.parametrize("change", ["symlink", "parent", "hardlink", "large", "unreferenced"])
def test_report_attachments_are_bounded_owned_allowlisted_files(ready, tmp_path, monkeypatch, change):
    manifest = export(ready)
    report = ready.output / "reports" / f'{manifest["titles"][0]["verification"]["reportSha256"]}.json'
    if change == "large":
        monkeypatch.setattr(packaged, "MAX_REPORT_BYTES", report.stat().st_size - 1)
    elif change == "unreferenced":
        (report.parent / ("0" * 64 + ".json")).write_bytes(report.read_bytes())
    elif change == "parent":
        outside = tmp_path / "outside"
        report.parent.rename(outside)
        report.parent.symlink_to(outside, target_is_directory=True)
    else:
        outside = tmp_path / "outside.json"
        outside.write_bytes(report.read_bytes())
        report.unlink()
        if change == "symlink":
            report.symlink_to(outside)
        else:
            os.link(outside, report)
    with pytest.raises(packaged.local.LocalLibraryError):
        packaged.check_packaged_library(ready.output)


def test_failed_batch_publication_rolls_back_all_new_report_files(ready, monkeypatch):
    original = export(ready)
    _replace_report(ready.result, lambda data: data.update(finished_at=1))
    receipt_path = ready.root / "local-receipts" / f"{ready.result.sha256}.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["verification"]["report_sha256"] = sha256_file(ready.result.layout.verify_report_path)
    receipt["verification"]["checked_inputs_sha256"] = packaged.local._inputs_digest(ready.result.layout)
    receipt_path.write_text(json.dumps(receipt))
    current = export(ready)
    assert current["bundleId"] != original["bundleId"]
    reports = {path.stem: path.read_bytes() for path in (ready.output / "reports").iterdir()}
    shutil.rmtree(ready.output / "reports")
    real_link = packaged.os.link
    calls = []
    def broken_link(source, target):
        calls.append(target)
        if len(calls) == 2:
            raise OSError("fabricated failure after the first attachment")
        return real_link(source, target)
    monkeypatch.setattr(packaged.os, "link", broken_link)
    with pytest.raises(OSError, match="fabricated failure"):
        packaged._publish_reports(ready.output, reports, packaged._report_references(ready.output))
    assert not (ready.output / "reports").exists()
    assert packaged.check_packaged_library(ready.output) == current


def test_report_cli_exposes_missing_originals_and_strict_mode_fails(ready, capsys):
    export(ready)
    shutil.rmtree(ready.output / "reports")
    assert packaged.main(["check", "--output", str(ready.output)]) == 0
    assert json.loads(capsys.readouterr().out)["verification_reports"]["present"] == 0
    assert packaged.main(["check", "--output", str(ready.output), "--require-reports"]) == 2
    assert "missing" in json.loads(capsys.readouterr().out)["message"]
    assert packaged.main(["attach-reports", "--output", str(ready.output),
                          "--report", str(ready.result.layout.verify_report_path)]) == 0
    assert json.loads(capsys.readouterr().out)["verification_reports"]["missing"] == []


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is needed for the delivery contract roundtrip")
def test_python_export_with_infinite_measurements_passes_node_without_rewriting_report(ready):
    def measurements(data):
        data["checks"][0]["data"] = {"psnr": float("inf"), "lower": float("-inf")}
        data["checks"][0]["detail"] = 'Infinity " quoted -Infinity'
    _replace_report(ready.result, measurements)
    receipt_path = ready.root / "local-receipts" / f"{ready.result.sha256}.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["verification"]["report_sha256"] = sha256_file(ready.result.layout.verify_report_path)
    receipt["verification"]["checked_inputs_sha256"] = packaged.local._inputs_digest(ready.result.layout)
    receipt_path.write_text(json.dumps(receipt))
    manifest = export(ready)
    script = Path(__file__).resolve().parents[2] / "app/tools/check_prepared_library.mjs"
    result = subprocess.run(["node", "--input-type=module", "-e",
                             f"import {{checkPreparedDirectory}} from {json.dumps(script.as_uri())};"
                             "console.log(JSON.stringify(checkPreparedDirectory(process.argv[1], {requireReports:true})));",
                             str(ready.output)], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["verification_reports"] == {"required": 1, "present": 1, "missing": []}
    digest = manifest["titles"][0]["verification"]["reportSha256"]
    assert (ready.output / "reports" / f"{digest}.json").read_bytes() == ready.result.layout.verify_report_path.read_bytes()


def test_export_budget_uses_final_catalog_pointer_sizes_when_the_title_gets_shorter(ready, tmp_path, monkeypatch):
    receipt_path = ready.root / "local-receipts" / f"{ready.result.sha256}.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["title"] = "A" * 200
    receipt_path.write_text(json.dumps(receipt))
    export(ready)
    original_output = ready.output
    predicted = tmp_path / "predicted"
    shutil.copytree(original_output, predicted)
    receipt["title"] = "A"
    receipt_path.write_text(json.dumps(receipt))
    ready.output = predicted
    expected = export(ready)
    final_size = sum(path.stat().st_size for path in predicted.rglob("*") if path.is_file())
    ready.output = original_output
    monkeypatch.setattr(packaged, "MAX_BUNDLE_BYTES", final_size)
    assert export(ready) == expected
    assert packaged.check_packaged_library(original_output, require_reports=True) == expected
