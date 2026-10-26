"""Paired protocol results cannot gain recall by silently changing the denominator."""

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

import conformance_comparison as comparison
from test_conformance_recheck import clip, row


def measurement(rows):
    return {"design_sha256": "frozen", "source_sha256": {
        "flashmap/src/flashmap/analyze.py": "same-detector",
        "eval/conformance/truth.py": "same-truth",
        "eval/conformance/report.py": hashlib.sha256((Path(__file__).resolve().parents[2]
            / "eval/conformance/report.py").read_bytes()).hexdigest(),
        "eval/conformance/geometry.py": "same-geometry",
        "eval/metrics.py": hashlib.sha256((Path(__file__).resolve().parents[2]
            / "eval/metrics.py").read_bytes()).hexdigest(),
        "eval/conformance/recheck.py": hashlib.sha256((Path(__file__).resolve().parents[2]
            / "eval/conformance/recheck.py").read_bytes()).hexdigest(),
    }, "environment": {"python": "fixture", "pyav": "fixture", "numpy": "fixture", "libav": {}},
    "rows": rows}


@pytest.mark.parametrize("change", ["design", "detector", "truth", "new_detector_source",
                                    "scoring", "geometry", "metrics"])
def test_confounded_protocol_comparison_is_refused(change):
    before = measurement([row()])
    after = copy.deepcopy(before)
    if change == "design":
        after["design_sha256"] = "changed"
    elif change == "new_detector_source":
        after["source_sha256"]["flashmap/src/flashmap/new.py"] = "new"
    else:
        name = {"detector": "flashmap/src/flashmap/analyze.py", "truth": "eval/conformance/truth.py",
                "scoring": "eval/conformance/report.py", "geometry": "eval/conformance/geometry.py",
                "metrics": "eval/metrics.py"}[change]
        after["source_sha256"][name] = "changed"
    with pytest.raises(ValueError, match="changed|confounded"):
        comparison.compare({"clips": [clip()]}, before, after)


def test_codec_or_runtime_environment_changes_are_not_called_only_a_protocol_effect():
    before = measurement([row()])
    after = copy.deepcopy(before)
    after["environment"]["pyav"] = "different"
    with pytest.raises(ValueError, match="environment"):
        comparison.compare({"clips": [clip()]}, before, after)


@pytest.mark.parametrize("name", ["eval/metrics.py", "eval/conformance/recheck.py"])
def test_recalculation_requires_the_measured_scoring_source(name):
    before = measurement([row()])
    before["source_sha256"][name] = "not-the-current-source"
    with pytest.raises(ValueError, match="scoring source"):
        comparison.compare({"clips": [clip()]}, before, copy.deepcopy(before))


def test_before_runner_may_differ_when_after_matches_the_local_scorer():
    before = measurement([row()])
    after = copy.deepcopy(before)
    before["source_sha256"]["eval/conformance/recheck.py"] = "older-runner"
    assert comparison.compare({"clips": [clip()]}, before, after)["paired_clips_measured"] == 1


@pytest.mark.parametrize("rows", [[], [row(), row()], [row("unknown")]])
def test_missing_or_duplicate_reference_measurements_are_refused(rows):
    with pytest.raises(ValueError, match="exactly once"):
        comparison.compare({"clips": [clip()]}, measurement([row()]), measurement(rows))


def test_exclusions_and_common_kept_denominators_are_both_reported():
    excluded = row("excluded")
    excluded["fidelity"]["max_abs_deviation"] = 1
    before = measurement([row(positive=False), excluded])
    after = measurement([row(), row("excluded"), row("new")])
    design = {"clips": [clip(), clip("excluded", 1), clip("new", 2)]}
    result = comparison.compare(design, before, after)
    assert result["paired_clips_measured"] == 2
    assert result["before_own_exclusions"]["all_windows"]["recall"]["denominator"] == 2
    assert result["after_own_exclusions"]["all_windows"]["recall"]["denominator"] == 4
    assert result["common_kept_clips"] == 1
    assert result["common_kept_before"]["all_windows"]["counts"]["fn"] == 2
    assert result["common_kept_after"]["all_windows"]["counts"]["tp"] == 2
    assert result["common_kept_after"]["all_windows"]["recall"]["denominator"] == 2


@pytest.fixture
def files(tmp_path, monkeypatch):
    design = tmp_path / "design.json"
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    output = tmp_path / "comparison.json"
    design.write_text(json.dumps({"clips": [clip()]}))
    data = measurement([row()])
    data["design_sha256"] = hashlib.sha256(design.read_bytes()).hexdigest()
    before.write_text(json.dumps(data))
    after.write_text(json.dumps(data))
    monkeypatch.setattr(sys, "argv", ["compare", "--design", str(design),
        "--before", str(before), "--after", str(after), "--out", str(output)])
    return design, output


def test_cli_preserves_existing_evidence(files):
    _, output = files
    output.write_text("existing")
    with pytest.raises(SystemExit):
        comparison.main()
    assert output.read_text() == "existing"


def test_cli_requires_the_actual_frozen_design_bytes(files):
    design, output = files
    design.write_text(design.read_text() + " ")
    with pytest.raises(ValueError, match="design digest"):
        comparison.main()
    assert not output.exists()
