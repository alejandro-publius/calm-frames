"""Synthetic privacy controls; no production report or signature is rewritten."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from pipeline.layout import TitleLayout
from pipeline.packaged_library import PackagedLibraryError, _check_report
from pipeline.verify import VerifyReport, verify_title

ROOT = Path(__file__).resolve().parents[2]


def report_fixture():
    # Copy historical evidence into memory only; mutations are test inputs.
    root = ROOT / "app/assets/raw/prepared-library"
    manifest = json.loads((root / "catalog.json").read_text())
    title = manifest["titles"][0]
    raw = (root / "reports" / (title["verification"]["reportSha256"] + ".json")).read_bytes()
    data = json.loads(raw)
    # A synthetic passing report retaining the historical measurement shape.
    # Successful CLI chatter used to contain workspace paths too.
    data["source_path"] = "sha256:" + data["sha256"]
    for item in data["checks"]:
        if item["name"].startswith("map_signature:"):
            item["detail"] = "SYNTHETIC signature check detail"
    return data, title


def check(data, title, **options):
    raw = json.dumps(data).encode()
    _check_report(raw, hashlib.sha256(raw).hexdigest(), [title], **options)


def test_generator_uses_exact_media_id_and_keeps_failure_diagnostics(tmp_path):
    source = tmp_path / "private-household" / "missing.mp4"
    report = verify_title(TitleLayout(tmp_path / "work", "a" * 64), source=source,
                          presets=["wcag"], adapter=None, pub_key=None)
    assert report.source_path == "sha256:" + "a" * 64
    assert str(source) in report.failures[0].detail
    assert report.passed is False
    assert VerifyReport.from_dict(report.to_dict()).to_dict() == report.to_dict()


@pytest.mark.parametrize("private_path", [
    "/Users/fictional/Movies/clip.mp4", "/home/fictional/clip.mp4",
    r"C:\Users\fictional\clip.mp4", r"\\server\household\clip.mp4",
    "file:///Users/fictional/clip.mp4", "~/Movies/clip.mp4",
    "/家/fictional/clip.mp4", "//server/household/clip.mp4", "FILE:///Users/fictional/clip.mp4",
])
@pytest.mark.parametrize("field", ["source_path", "detail", "nested"])
def test_distribution_rejects_paths_even_with_matching_report_hash(private_path, field):
    data, title = report_fixture()
    data["source_path"] = "sha256:" + data["sha256"]
    if field == "source_path":
        data[field] = private_path
    elif field == "detail":
        data["checks"][0]["detail"] = "checked " + private_path
    else:
        data["checks"][0]["data"]["diagnostics"] = json.dumps({"path": private_path})
    before = copy.deepcopy(data)
    with pytest.raises(PackagedLibraryError, match="local filesystem path"):
        check(data, title, distributable=True)
    assert data == before


def test_portable_report_keeps_schema_and_binding_and_rejects_tamper():
    data, title = report_fixture()
    data["source_path"] = "sha256:" + data["sha256"]
    check(data, title, distributable=True)
    data["source_path"] = "sha256:" + "0" * 64
    with pytest.raises(PackagedLibraryError, match="media identifier"):
        check(data, title, distributable=True)


def test_historical_paths_can_be_inspected_but_not_distributed():
    data, title = report_fixture()
    data["source_path"] = "/Users/fictional/clip.mp4"
    check(data, title)
    with pytest.raises(PackagedLibraryError, match="local filesystem path"):
        check(data, title, distributable=True)


@pytest.mark.parametrize("group", ["ambientAnalysis", "outputAnalysis"])
def test_nested_ambient_analysis_refuses_paths_after_all_hashes_are_rebound(group):
    from pipeline.tests.test_ambient_report import fixture, refresh

    value = fixture()
    entry = value["report"]["presets"]["wcag"][group]["wcag"]
    analysis = json.loads(entry["raw"])
    analysis["source"]["path"] = "/Users/fictional/clip.mp4"
    entry["raw"] = json.dumps(analysis)
    refresh(value)
    check(value["report"], value["title"])
    with pytest.raises(PackagedLibraryError, match="local filesystem path"):
        check(value["report"], value["title"], distributable=True)
