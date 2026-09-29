"""The mutation harness must target current code and reject meaningless red runs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

import mutate_gate as gate
import property_runner


@pytest.mark.parametrize("mutation", gate.MUTATIONS, ids=lambda mutation: mutation.mid)
def test_every_mutation_targets_exactly_one_current_guard(mutation):
    root = gate.REPO / "app" if mutation.lane in ("app", "pyapp") else gate.REPO
    target = root / mutation.path
    assert target.is_file(), f"{mutation.mid}: missing source file {target}"
    assert target.read_text().count(mutation.old) == 1, (
        f"{mutation.mid}: the mutation no longer targets exactly one guard. "
        "Retarget the same fault and remeasure the gate; do not drop the mutation."
    )
    assert mutation.new != mutation.old
    assert mutation.new.strip()


def test_mutation_ids_are_unique():
    ids = [mutation.mid for mutation in gate.MUTATIONS]
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize(
    "output",
    [
        "Test Suites: 1 failed, 1 total\nTests: 0 total\n",
        "Test Suites: 1 failed, 1 passed, 2 total\nTests: 2 passed, 2 total\n",
        "Test Suites: 1 passed, 1 total\nTests: 2 passed, 2 total\n",
    ],
)
def test_a_compile_or_runner_error_is_not_a_mutation_kill(output):
    result = gate.RunResult(command=[], returncode=1, seconds=0, stdout=output, stderr="")
    gate._read_jest(result)
    assert result.broken
    assert not result.is_a_kill


def test_a_named_assertion_failure_is_a_mutation_kill():
    result = gate.RunResult(
        command=[],
        returncode=1,
        seconds=0,
        stdout=(
            "  ● guard stays covered before a map is checked\n"
            "Test Suites: 1 failed, 1 total\n"
            "Tests: 1 failed, 2 passed, 3 total\n"
        ),
        stderr="",
    )
    gate._read_jest(result)
    assert result.is_a_kill
    assert result.failing == ["guard stays covered before a map is checked"]
    assert result.ran == 3


def test_app_mutation_runner_disables_watchman_without_skipping_tests(monkeypatch, tmp_path):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="Test Suites: 1 passed, 1 total\nTests: 1 passed, 1 total\n",
            stderr="",
        )

    monkeypatch.setattr(gate, "APP_LANE", tmp_path)
    monkeypatch.setattr(gate.subprocess, "run", run)
    result = gate.run_tests("app", ("test/guard.test.tsx",))
    command, options = calls[0]
    assert "--watchman=false" in command
    assert command[-1] == "test/guard.test.tsx"
    assert Path(options["cwd"]) == tmp_path
    assert result.returncode == 0
    assert result.ran == 1


def test_an_edit_to_scene_holds_invalidates_the_property_compile(monkeypatch, tmp_path):
    app = tmp_path / "app"
    compiled = tmp_path / "compiled"
    compiled.mkdir()
    built = compiled / "coverSchedule.js"
    built.write_text("previous compile")
    os.utime(built, (1500, 1500))
    for name in property_runner.SCHEDULER_SOURCES:
        source = app / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("source")
        os.utime(source, (1000, 1000))
    scene_parser = app / "src/calmframes/sceneHolds.ts"
    scene_parser.parent.mkdir(parents=True, exist_ok=True)
    scene_parser.write_text("updated parser")
    os.utime(scene_parser, (2000, 2000))
    compiler = app / "node_modules/.bin/tsc"
    compiler.parent.mkdir(parents=True, exist_ok=True)
    compiler.touch()
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(property_runner, "APP", app)
    monkeypatch.setattr(property_runner, "JS_DIR", compiled)
    monkeypatch.setattr(property_runner, "_IS_MUTANT", False)
    monkeypatch.setattr(property_runner, "node_path", lambda: "node")
    monkeypatch.setattr(property_runner.subprocess, "run", run)
    assert property_runner.compile_scheduler() == compiled
    assert len(calls) == 1
    assert "src/calmframes/sceneHolds.ts" in calls[0]


def _check_fixture(monkeypatch, tmp_path, *, baseline_killed=True, measured_killed=True):
    mutation = gate.MUTATIONS[0]
    record = {
        "id": mutation.mid,
        "property": mutation.prop,
        "killed": measured_killed,
        "evidence": "a named assertion failed" if measured_killed else "",
        "survived_because": "" if measured_killed else "all assertions passed",
        "seconds": 0,
    }
    baseline_record = {**record, "killed": baseline_killed}
    baseline = gate.build_report([baseline_record], [], True)
    path = tmp_path / "mutation.json"
    path.write_text(json.dumps(baseline, indent=2) + "\n")
    monkeypatch.setattr(gate, "MUTATIONS", [mutation])
    monkeypatch.setattr(gate, "REPORT_PATH", path)
    monkeypatch.setattr(gate, "prepare", lambda lanes: None)
    monkeypatch.setattr(gate, "negative_control", lambda selected: ([], True))
    monkeypatch.setattr(gate, "apply_and_run", lambda selected: dict(record))
    return path, baseline


@pytest.mark.parametrize("separate_output", [False, True])
@pytest.mark.parametrize("drift", ["totals", "survivor"])
def test_check_rejects_drift_without_overwriting_baseline(
    monkeypatch, tmp_path, separate_output, drift,
):
    path, baseline = _check_fixture(
        monkeypatch, tmp_path, measured_killed=drift != "survivor",
    )
    if drift == "totals":
        baseline["totals"]["mutations"] += 1
        path.write_text(json.dumps(baseline, indent=2) + "\n")
    before = path.read_bytes()
    measured = tmp_path / "diagnostics" / "measured.json"
    args = ["--check"] + (["--out", str(measured)] if separate_output else [])
    assert gate.main(args) == 1
    assert path.read_bytes() == before
    if separate_output:
        actual = json.loads(measured.read_text())
        assert actual["totals"]["mutations"] == 1
        assert actual["totals"]["killed"] == int(drift != "survivor")


@pytest.mark.parametrize("separate_output", [False, True])
def test_a_matching_check_preserves_its_baseline(monkeypatch, tmp_path, separate_output):
    path, _ = _check_fixture(monkeypatch, tmp_path)
    before = path.read_bytes()
    measured = tmp_path / "measured.json"
    args = ["--check"] + (["--out", str(measured)] if separate_output else [])
    assert gate.main(args) == 0
    assert path.read_bytes() == before
    assert measured.exists() == separate_output


def test_check_fails_for_a_non_equivalent_survivor_even_if_baseline_contains_it(
    monkeypatch, tmp_path,
):
    path, _ = _check_fixture(
        monkeypatch, tmp_path, baseline_killed=False, measured_killed=False,
    )
    before = path.read_bytes()
    assert gate.main(["--check"]) == 1
    assert path.read_bytes() == before


def test_red_negative_controls_do_not_create_a_complete_report(monkeypatch, tmp_path):
    path, _ = _check_fixture(monkeypatch, tmp_path)
    before = path.read_bytes()
    measured = tmp_path / "measured.json"
    monkeypatch.setattr(gate, "negative_control", lambda selected: ([], False))
    assert gate.main(["--check", "--out", str(measured)]) == 2
    assert path.read_bytes() == before
    assert not measured.exists()


def test_check_uses_the_original_baseline_snapshot(monkeypatch, tmp_path):
    path, original = _check_fixture(monkeypatch, tmp_path)
    original["totals"]["mutations"] += 1
    path.write_text(json.dumps(original) + "\n")
    replacement = gate.build_report([
        {"id": gate.MUTATIONS[0].mid, "property": gate.MUTATIONS[0].prop, "killed": True},
    ], [], True)
    replacement_text = json.dumps(replacement) + "\n"

    def control(selected):
        # A concurrent writer cannot change what this invocation compares to.
        path.write_text(replacement_text)
        return [], True

    monkeypatch.setattr(gate, "negative_control", control)
    assert gate.main(["--check"]) == 1
    assert path.read_text() == replacement_text


def test_ci_checks_the_baseline_and_keeps_separate_failure_diagnostics():
    workflow = (gate.REPO / ".github/workflows/ci.yml").read_text()
    hardening = workflow.split("  hardening:\n", 1)[1].split("\n  secrets:\n", 1)[0]
    mutation_step = hardening.split("      - name: The mutation gate\n", 1)[1]
    assert '--check --out .logs/mutation-ci.json' in mutation_step
    assert "continue-on-error" not in hardening
    artifact = mutation_step.split("uses: actions/upload-artifact@v4", 1)
    assert len(artifact) == 2
    assert "if: always()" in artifact[0].rsplit("      - name:", 1)[1]
    assert "path: .logs/mutation-ci.json" in artifact[1]
    assert "include-hidden-files: true" in artifact[1]
    assert "retention-days: 7" in artifact[1]


def test_check_cannot_skip_its_negative_controls(monkeypatch, tmp_path):
    path, _ = _check_fixture(monkeypatch, tmp_path)
    before = path.read_bytes()
    measured = tmp_path / "measured.json"
    assert gate.main(["--check", "--skip-control", "--out", str(measured)]) == 2
    assert path.read_bytes() == before
    assert not measured.exists()


def test_a_quick_look_does_not_claim_green_controls(monkeypatch, tmp_path):
    path, _ = _check_fixture(monkeypatch, tmp_path)
    before = path.read_bytes()
    measured = tmp_path / "quick-look.json"
    assert gate.main(["--skip-control", "--out", str(measured)]) == 0
    assert path.read_bytes() == before
    actual = json.loads(measured.read_text())
    assert actual["negative_control"]["performed"] is False
    assert actual["negative_control"]["all_green"] is False
    assert actual["negative_control"]["selections"] == []
    assert "no green baseline" in actual["negative_control"]["description"]


@pytest.mark.parametrize("alias_kind", ["hardlink", "symlink"])
def test_check_preserves_baseline_through_an_output_path_alias(monkeypatch, tmp_path, alias_kind):
    path, baseline = _check_fixture(monkeypatch, tmp_path)
    baseline["totals"]["mutations"] += 1
    path.write_text(json.dumps(baseline) + "\n")
    before = path.read_bytes()
    alias = tmp_path / "alias.json"
    if alias_kind == "hardlink":
        alias.hardlink_to(path)
    else:
        alias.symlink_to(path)
    assert gate.main(["--check", "--out", str(alias)]) == 1
    assert path.read_bytes() == before
    assert alias.read_bytes() == before
