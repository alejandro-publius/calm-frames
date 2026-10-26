"""Offline reports preserve both fixed window rules and exact measurement coverage."""

import copy
import json
import sys

import pytest

import conformance_current_report as current


@pytest.fixture
def files(tmp_path):
    design = json.loads((current.REPO / "results/conformance_design.json").read_text())
    design["clips"] = design["clips"][:1]
    design_path = tmp_path / "design.json"
    design_path.write_text(json.dumps(design))
    measured_path = tmp_path / "measured.json"
    row = {"clip_id": design["clips"][0]["clip_id"], "flashmap": {
        "segments": [{"start_ms": 900, "end_ms": 1100, "flash_first_ms": 900,
                      "flash_last_ms": 1100}], "first_pts_ms": 0, "version": "fixture"},
        "fidelity": {"max_abs_deviation": 0, "timestamps_match": True}}
    measured = {"rows": [row], "complete_design_evaluation": True,
        "design_sha256": current.digest(design_path),
        "source_sha256": {name: current.digest(current.REPO / name)
                          for name in ("eval/conformance/report.py", "eval/metrics.py")},
        "generated_utc": "2026-10-02T00:00:00+00:00", "encoding_protocol": "test-fixture",
        "git_commit": "measured-source-head",
        "baselines_rerun": False,
        "environment": {}, "hazard_files_remaining": 0}
    measured_path.write_text(json.dumps(measured))
    return design_path, measured_path, measured


def test_both_window_rules_are_reported_without_implying_new_baselines(files):
    design, path, _ = files
    result = current.build_current(design, path)
    table = result["headline_all_windows"]
    assert table["flashmap (this project)"]["counts"]["fp"] == 2
    assert table["flashmap, half window rule"]["counts"]["fp"] == 0
    assert result["baseline_table_windows_every_detector_saw"] == {}
    assert result["baseline_operating_points"] == {}
    assert len(result["baselines_not_run"]) == 4
    assert result["generated_on"] == "2026-10-02"
    assert result["measurement_sha256"] == current.digest(path)
    assert result["sample"]["clips_measured"] == 1
    assert result["published"]["false_positives_in_the_calm_lead_in"] == 1
    assert result["published"]["false_positives_elsewhere"] == 1


def test_report_uses_the_measured_commit_not_the_report_time_commit(files):
    design, path, _ = files
    assert current.build_current(design, path)["git_commit"] == "measured-source-head"


@pytest.mark.parametrize("mutation", ["cleanup", "analysis_error", "delete_error",
                                     "baseline_rows", "baseline_claim"])
def test_success_and_no_baseline_claims_require_consistent_evidence(files, mutation):
    design, path, measured = files
    if mutation == "cleanup":
        measured["hazard_files_remaining"] = 1
    elif mutation == "baseline_claim":
        measured["baselines_rerun"] = True
    elif mutation == "baseline_rows":
        measured["rows"][0]["baselines"] = {}
    else:
        measured["rows"][0]["error" if mutation == "analysis_error" else "delete_error"] = "failure"
    path.write_text(json.dumps(measured))
    with pytest.raises(ValueError, match="cleanup|error|baseline"):
        current.build_current(design, path)


@pytest.mark.parametrize("mutation", ["design_digest", "incomplete", "missing", "duplicate", "scoring"])
def test_incomplete_or_inconsistent_measurement_is_refused(files, mutation):
    design, path, measured = files
    measured = copy.deepcopy(measured)
    if mutation == "design_digest":
        measured["design_sha256"] = "wrong"
    elif mutation == "incomplete":
        measured["complete_design_evaluation"] = False
    elif mutation == "missing":
        measured["rows"] = []
    elif mutation == "duplicate":
        measured["rows"] *= 2
    else:
        measured["source_sha256"]["eval/metrics.py"] = "changed"
    path.write_text(json.dumps(measured))
    with pytest.raises(ValueError, match="digest|complete measurement|scoring source"):
        current.build_current(design, path)


def test_report_does_not_replace_existing_evidence(files, monkeypatch):
    design, measurement, _ = files
    output = measurement.with_name("report.json")
    output.write_text("preserve")
    monkeypatch.setattr(sys, "argv", ["report", "--design", str(design),
        "--measurement", str(measurement), "--out", str(output)])
    with pytest.raises(SystemExit):
        current.main()
    assert output.read_text() == "preserve"
