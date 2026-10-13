"""Scanner failures must not become a clean dependency-audit report.

These tests run the real acceptance gate with offline scanner responses. A
scanner's exit status 1 can mean real findings, so rejecting every nonzero
status would hide useful results just as accepting an error object does.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "dep_audit.py"
spec = importlib.util.spec_from_file_location("dep_audit", SCRIPT)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def npm_report(findings: bool = False) -> dict:
    return {
        "auditReportVersion": 2,
        "vulnerabilities": {
            "example": {
                "severity": "high",
                "isDirect": True,
                "via": [{"source": 12345}],
                "fixAvailable": True,
            }
        } if findings else {},
        "metadata": {
            "vulnerabilities": {
                "info": 0, "low": 0, "moderate": 0,
                "high": int(findings), "critical": 0, "total": int(findings),
            }
        },
    }


def pip_report(findings: bool = False) -> dict:
    return {"dependencies": [{
        "name": "example", "version": "1.0",
        "vulns": [{"id": "PYSEC-2026-1"}] if findings else [],
    }]}


@pytest.fixture
def scanners(tmp_path, monkeypatch):
    app = tmp_path / "app"
    app.mkdir()
    (app / "package-lock.json").write_text("{}")
    (app / "node_modules").mkdir()
    (tmp_path / "requirements.txt").write_text("example==1.0\n")
    monkeypatch.setattr(audit, "REPO", tmp_path)
    monkeypatch.setattr(audit, "OUTPUT", tmp_path / "results" / "audit.json")
    monkeypatch.setattr(audit, "EXCEPTIONS", tmp_path / "exceptions.toml")
    monkeypatch.setattr(audit, "PYTHON_SOURCES", [("test requirements", "requirements.txt")])
    monkeypatch.setattr(audit, "pip_audit_available", lambda: ["pip-audit"])

    def set_response(ecosystem, code=0, payload=None, raw=None, error=None):
        stdout = raw if raw is not None else json.dumps(payload)

        def completed(*args, **kwargs):
            if error:
                raise error
            return subprocess.CompletedProcess(args, code, stdout, "scanner diagnostic")

        if ecosystem == "npm":
            monkeypatch.setattr(audit.subprocess, "run", completed)
        else:
            monkeypatch.setattr(audit, "run", completed)

    set_response("npm", payload=npm_report())
    set_response("pip", payload=pip_report())
    return set_response


@pytest.mark.parametrize("ecosystem", ["npm", "pip"])
@pytest.mark.parametrize("code,raw", [
    (1, ""),
    (1, '{"error":{"code":"EPERM","summary":"audit endpoint returned an error"}}'),
    (0, "{}"),
    (0, "[]"),
    (0, "null"),
    (0, "<html>unavailable</html>"),
])
def test_missing_or_error_output_blocks_acceptance(scanners, ecosystem, code, raw):
    scanners(ecosystem, code=code, raw=raw)
    assert audit.main(["--check"]) == 1
    report = json.loads(audit.OUTPUT.read_text())
    assert any("did not run" in problem for problem in report["problems"])


@pytest.mark.parametrize("ecosystem", ["npm", "pip"])
@pytest.mark.parametrize("code", [2, -9])
def test_unexpected_status_blocks_even_valid_json(scanners, ecosystem, code):
    scanners(ecosystem, code=code, payload=npm_report() if ecosystem == "npm" else pip_report())
    assert audit.main(["--check"]) == 1


@pytest.mark.parametrize("ecosystem", ["npm", "pip"])
def test_missing_scanner_is_recorded_as_failure(scanners, ecosystem):
    scanners(ecosystem, error=FileNotFoundError("scanner is missing"))
    assert audit.main(["--check"]) == 1
    report = json.loads(audit.OUTPUT.read_text())
    assert any("scanner is missing" in problem for problem in report["problems"])


@pytest.mark.parametrize("ecosystem", ["npm", "pip"])
def test_exit_one_with_real_findings_keeps_advisory_details(scanners, ecosystem):
    scanners(ecosystem, code=1, payload=npm_report(True) if ecosystem == "npm" else pip_report(True))
    assert audit.main(["--check"]) == 1
    report = json.loads(audit.OUTPUT.read_text())
    assert not any("did not run" in problem for problem in report["problems"])
    findings = report["npm"]["findings"] if ecosystem == "npm" else report["python"]["sources"][0]["findings"]
    assert findings[0]["package"] == "example"
    assert findings[0]["ids"] == (["12345"] if ecosystem == "npm" else ["PYSEC-2026-1"])


@pytest.mark.parametrize("ecosystem", ["npm", "pip"])
def test_exit_one_without_findings_is_not_a_clean_result(scanners, ecosystem):
    scanners(ecosystem, code=1, payload=npm_report() if ecosystem == "npm" else pip_report())
    assert audit.main(["--check"]) == 1


def test_valid_clean_reports_pass(scanners):
    assert audit.main(["--check"]) == 0


def test_valid_empty_requirements_report_passes(scanners):
    (audit.REPO / "requirements.txt").write_text("")
    scanners("pip", payload={"dependencies": []})
    assert audit.main(["--check"]) == 0


def test_skipped_python_dependency_blocks_acceptance(scanners):
    scanners("pip", payload={"dependencies": [{"name": "example", "skip_reason": "not found"}]})
    assert audit.main(["--check"]) == 1


@pytest.mark.parametrize("ecosystem,payload", [
    ("pip", {"dependencies": [{"name": "example", "version": "1.0", "vulns": [{}]}]}),
    ("pip", {"dependencies": [{"name": "example", "version": "1.0"}]}),
    ("npm", {"auditReportVersion": 2, "vulnerabilities": {}}),
    ("npm", {**npm_report(), "vulnerabilities": {"example": {"via": [{}]}}}),
])
def test_incomplete_scanner_records_block_acceptance(scanners, ecosystem, payload):
    scanners(ecosystem, payload=payload)
    assert audit.main(["--check"]) == 1


def test_npm_advisory_without_id_cannot_be_silently_waived(scanners):
    payload = npm_report(True)
    payload["vulnerabilities"]["example"]["via"] = [{"title": "new advisory"}]
    scanners("npm", code=1, payload=payload)
    audit.EXCEPTIONS.write_text('''[[exception]]
group = "existing review"
ecosystem = "npm"
packages = ["example"]
why = "Reviewed earlier advisories only"
accepted_by = "test reviewer"
review_by = "2099-01-01"
[exception.advisories]
example = []
''')
    assert audit.main(["--check"]) == 1


def test_npm_missing_findings_cannot_hide_nonzero_totals(scanners):
    payload = npm_report(True)
    payload["vulnerabilities"] = {}
    scanners("npm", payload=payload)
    assert audit.main(["--check"]) == 1
