"""The pull request check and the GitHub Action that runs it.

SAFETY. The failing fixture is generated into a temporary directory and deleted in the same
test. The only media file committed to the repository is a calm one.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import clipgen
from flashmap import ci

ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "action.yml"
SAMPLE_WORKFLOW = ROOT / "examples" / "flash-check.yml"
CALM_FIXTURE = Path(__file__).parent / "fixtures" / "calm_sweep.mp4"

W, H = 64, 48


@pytest.fixture
def flashing_gif(tmp_path):
    """A small animated image that breaks the thresholds. Deleted when the test ends."""
    path = tmp_path / "HAZARD_strobe.gif"
    clipgen.write_clip(
        path,
        clipgen.alternating(30, clipgen.solid(W, H, (0, 0, 0)), clipgen.solid(W, H, (255, 255, 255))),
        fps=20,
        codec="gif",
        pix_fmt="rgb8",
    )
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


# ---- file selection ------------------------------------------------------------------------


def test_the_committed_fixture_exists_and_is_small():
    assert CALM_FIXTURE.is_file()
    assert CALM_FIXTURE.stat().st_size < 50_000


def test_media_files_are_selected_and_source_files_are_not(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"x")
    (tmp_path / "b.gif").write_bytes(b"x")
    (tmp_path / "c.py").write_bytes(b"x")
    (tmp_path / "d.md").write_bytes(b"x")
    chosen = ci.select_media([str(tmp_path / name) for name in ("a.mp4", "b.gif", "c.py", "d.md")])
    assert [path.name for path in chosen] == ["a.mp4", "b.gif"]


def test_a_deleted_file_is_not_selected(tmp_path):
    assert ci.select_media([str(tmp_path / "gone.mp4")]) == []


def test_selection_is_case_insensitive(tmp_path):
    (tmp_path / "SHOT.MP4").write_bytes(b"x")
    assert len(ci.select_media([str(tmp_path / "SHOT.MP4")])) == 1


# ---- the check itself ----------------------------------------------------------------------


def test_a_calm_file_passes(capsys):
    assert ci.main([str(CALM_FIXTURE)]) == 0
    assert "PASS" in capsys.readouterr().out


def test_a_flashing_image_fails_the_check(flashing_gif, capsys):
    assert ci.main([str(flashing_gif)]) == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "measured on the picture" in captured.out
    assert "WCAG 2.2 Success Criterion 2.3.1" in captured.err


def test_one_bad_file_among_good_ones_still_fails(flashing_gif):
    assert ci.main([str(CALM_FIXTURE), str(flashing_gif)]) == 1


def test_a_change_with_no_media_passes(capsys):
    assert ci.main([__file__]) == 0
    assert "no image or video files" in capsys.readouterr().out


def test_the_file_list_can_come_from_a_file(tmp_path, flashing_gif):
    listing = tmp_path / "changed.txt"
    listing.write_text(f"README.md\n{flashing_gif}\nsrc/flashmap/ci.py\n", encoding="utf-8")
    assert ci.main(["--changed-from", str(listing)]) == 1


def test_the_job_summary_is_written_when_github_asks_for_one(tmp_path, flashing_gif, monkeypatch):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    ci.main([str(flashing_gif)])
    text = summary.read_text(encoding="utf-8")
    assert "WCAG 2.2 Success Criterion 2.3.1" in text
    assert "not a medical device" in text
    assert "Do not open a failing file in a player" in text


def test_an_unmeasurable_file_is_skipped_by_default_and_can_be_made_fatal(tmp_path):
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"not a video at all")
    assert ci.main([str(broken)]) == 0
    assert ci.main([str(broken), "--fail-on-error"]) == 1


# ---- the action wrapper ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def action():
    return yaml.safe_load(ACTION.read_text(encoding="utf-8"))


def test_the_action_is_a_composite_action(action):
    assert action["runs"]["using"] == "composite"
    assert action["name"]
    assert "2.3.1" in action["description"]


def test_the_action_takes_the_inputs_the_readme_promises(action):
    for name in ("profile", "paths", "peak-nits", "analysis-width", "fail-on-error"):
        assert name in action["inputs"], name
    assert action["inputs"]["profile"]["default"] == "wcag"


def test_every_action_step_has_a_shell_or_an_action(action):
    for step in action["runs"]["steps"]:
        assert "shell" in step or "uses" in step, step


def test_the_action_calls_the_module_this_suite_tests(action):
    body = "\n".join(step.get("run", "") for step in action["runs"]["steps"])
    assert "python -m flashmap.ci" in body
    assert "--changed-from" in body


def test_an_unmeasurable_file_fails_the_action_by_default(action):
    # Fail closed, as the player does: a file nobody measured has not been shown to be under
    # the thresholds, so skipping it has to be asked for.
    assert action["inputs"]["fail-on-error"]["default"] == "true"


def test_failed_count_is_a_count_of_failing_files(action):
    check = [step for step in action["runs"]["steps"] if step.get("id") == "check"][0]
    assert "grep -c '^FAIL '" in check["run"], "failed-count has to count the FAIL lines"
    assert 'failed-count=$status' not in check["run"], "the exit status is not a count"


def test_the_action_does_not_swallow_a_failure(action):
    check = [step for step in action["runs"]["steps"] if step.get("id") == "check"][0]
    assert "exit $status" in check["run"]
    assert "continue-on-error" not in check


def test_the_sample_workflow_parses_and_uses_the_action():
    workflow = yaml.safe_load(SAMPLE_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["flash-check"]
    assert job["runs-on"] == "ubuntu-latest"
    uses = [step.get("uses", "") for step in job["steps"]]
    assert any("flashmap" in entry for entry in uses)
    checkout = job["steps"][0]
    assert checkout["with"]["fetch-depth"] == 0, "the diff needs history"
