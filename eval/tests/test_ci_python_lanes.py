"""The CI Python job runs every Python lane, by name, with source coverage.

From Sep 17 to Oct 11, 2026 the job chose its lanes with a loop around `ls`,
and `ls` fails when any one of its patterns matches nothing. Neither flashmap/
nor pipeline/ has a test file at its top level, so both were dropped every
time and only eval/ ran: the analyzer's and the pipeline's tests, verify's
among them, never ran in that job, while the job stayed green. The log said
`testing: eval` and nobody read it.

This keeps the three lanes named in the Test step, keeps the detection loop
out, and keeps the coverage step pointed at the source configuration.

Seen to fail on purpose, Oct 11 2026: run against the workflow as it stood
before the fix (`git show ca64dcc:.github/workflows/ci.yml`), the lane test
went red naming the missing lanes.
"""

from __future__ import annotations

import configparser
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
LANES = ("flashmap", "pipeline", "eval")


def python_test_step(workflow_text: str) -> str:
    workflow = yaml.safe_load(workflow_text)
    steps = workflow["jobs"]["python"]["steps"]
    named = [step for step in steps if step.get("name") == "Test"]
    assert len(named) == 1, "the python job has no single step named Test"
    return named[0]["run"]


def lane_problems(run: str) -> list[str]:
    problems = []
    commands = [line.strip() for line in run.splitlines() if line.strip() and not line.strip().startswith("#")]
    script = " ".join(commands).replace("\\", " ")
    pytest_call = re.search(r"\bpytest\b(?P<args>[^;&|]*)", script)
    if not pytest_call:
        return ["the Test step does not run pytest"]
    arguments = pytest_call.group("args").split()
    for lane in LANES:
        if lane not in arguments:
            problems.append(f"the Test step's pytest does not name {lane}")
    if re.search(r"\bls\b", script) or "$targets" in script:
        problems.append("the Test step chooses its lanes at run time instead of naming them")
    if "--cov-config=.coveragerc" not in arguments:
        problems.append("the Test step does not measure coverage with .coveragerc")
    return problems


def test_the_python_job_names_every_lane() -> None:
    run = python_test_step((REPO / ".github/workflows/ci.yml").read_text())
    assert lane_problems(run) == []


def test_the_old_detection_loop_is_refused() -> None:
    old = """targets=""
for dir in flashmap pipeline eval; do
  if [ -d "$dir" ] && ls "$dir"/**/test_*.py "$dir"/test_*.py "$dir"/tests >/dev/null 2>&1; then
    targets="$targets $dir"
  fi
done
pytest -q -m "not slow" $targets
"""
    problems = lane_problems(old)
    assert "the Test step's pytest does not name flashmap" in problems
    assert "the Test step chooses its lanes at run time instead of naming them" in problems


def test_coverage_is_of_the_source_with_a_floor() -> None:
    config = configparser.ConfigParser()
    assert config.read(REPO / ".coveragerc"), ".coveragerc is missing"
    sources = config.get("run", "source").split()
    assert sources == ["flashmap/src/flashmap", "pipeline"]
    omitted = config.get("run", "omit").split()
    assert "*/tests/*" in omitted, "test files would lift the number without measuring the code"
    assert 0 < config.getint("report", "fail_under") <= 100
