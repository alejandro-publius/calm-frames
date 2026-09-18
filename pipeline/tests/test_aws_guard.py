"""The two locks in front of every command that would reach AWS.

`scripts/aws_guard.sh` is the only way to `cdk deploy`, `cdk destroy`,
`cdk diff` or an ECR push in this project, and it refuses unless both of these
are true at once:

  1. docs/STATUS.md says "AWS Paid plan: confirmed"
  2. CHECKPOINT_D=confirmed is on that one command

Until today the locks were described in three documents and tested by nobody.
This is the test. It runs the real script against a fake repository in a
temporary directory, because the one thing it must never do is add the line to
the real docs/STATUS.md.

Two rules this file keeps, since this machine has an AWS CLI and credentials on
it:

  * the only case where both locks are open runs `echo` in place of the CDK, or
    a stub script, so nothing can reach an account even if something is wrong;
  * every subprocess runs with the credential files pointed at /dev/null and
    the instance metadata service switched off.

Seen to fail: with the guard changed from `and` to `or`, the four refusal tests
go red with "assert 0 == 1" and the message about what is still locked.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GUARD = REPO / "scripts" / "aws_guard.sh"
PUSH = REPO / "scripts" / "push_ingest_image.sh"
CONFIRMED_LINE = "AWS Paid plan: confirmed"

# Nothing in this file should be able to reach AWS. If a future change makes a
# command try, it finds no credentials, no config and no metadata service.
NO_CREDENTIALS = {
    "AWS_CONFIG_FILE": "/dev/null",
    "AWS_SHARED_CREDENTIALS_FILE": "/dev/null",
    "AWS_EC2_METADATA_DISABLED": "true",
    "AWS_PROFILE": "",
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
}


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """A repository shaped like this one, with the real script in it.

    The script finds its repository from its own location, so a copy two
    directories down from a temporary root behaves exactly as the real one does
    and reads the temporary docs/STATUS.md.
    """
    (tmp_path / "scripts").mkdir()
    (tmp_path / "docs").mkdir()
    # The guard cds here before running the CDK, so it has to exist.
    (tmp_path / "pipeline" / "infra").mkdir(parents=True)
    shutil.copy2(GUARD, tmp_path / "scripts" / "aws_guard.sh")
    shutil.copy2(PUSH, tmp_path / "scripts" / "push_ingest_image.sh")
    (tmp_path / "docs" / "STATUS.md").write_text(
        "# Status\n\nNothing has touched AWS.\n"
    )
    return tmp_path


def run_guard(repo: Path, action: str = "deploy", **environment) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(NO_CREDENTIALS)
    # `echo` in place of the CDK. Even in the case where both locks are open,
    # the command that runs is an echo.
    env["CDK"] = "echo [would run]"
    env.update({key: value for key, value in environment.items()})
    return subprocess.run(
        ["bash", str(repo / "scripts" / "aws_guard.sh"), action],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def confirm_status(repo: Path) -> None:
    """Add the line the way an operator is told to: at the start of a line."""
    status = repo / "docs" / "STATUS.md"
    status.write_text(status.read_text() + f"\n{CONFIRMED_LINE}, Sep 30 2026, Alex\n")


class TestNeitherLockAloneOpensIt:
    def test_with_neither_lock_it_refuses(self, fake_repo):
        result = run_guard(fake_repo)
        assert result.returncode == 1
        assert "is blocked" in result.stderr
        assert "no. docs/STATUS.md has no line" in result.stderr
        assert "CHECKPOINT_D is unset" in result.stderr
        assert "[would run]" not in result.stdout

    def test_the_variable_alone_does_not_open_it(self, fake_repo):
        result = run_guard(fake_repo, CHECKPOINT_D="confirmed")
        assert result.returncode == 1
        assert "no. docs/STATUS.md has no line" in result.stderr
        assert "[would run]" not in result.stdout

    def test_the_document_alone_does_not_open_it(self, fake_repo):
        confirm_status(fake_repo)
        result = run_guard(fake_repo)
        assert result.returncode == 1
        assert "CHECKPOINT_D is unset" in result.stderr
        assert "[would run]" not in result.stdout

    def test_a_near_miss_in_the_variable_does_not_open_it(self, fake_repo):
        confirm_status(fake_repo)
        for value in ("yes", "true", "1", "Confirmed ", "confirm"):
            result = run_guard(fake_repo, CHECKPOINT_D=value)
            assert result.returncode == 1, f"{value!r} opened the lock"
            assert "[would run]" not in result.stdout


class TestWithBothLocksOpen:
    def test_it_runs_the_cdk_command_and_nothing_else(self, fake_repo):
        confirm_status(fake_repo)
        result = run_guard(fake_repo, CHECKPOINT_D="confirmed")
        assert result.returncode == 0
        assert "[would run] deploy CalmFramesStack" in result.stdout

    def test_destroy_passes_force_and_diff_does_not(self, fake_repo):
        confirm_status(fake_repo)
        destroy = run_guard(fake_repo, "destroy", CHECKPOINT_D="confirmed")
        assert "[would run] destroy CalmFramesStack --force" in destroy.stdout
        diff = run_guard(fake_repo, "diff", CHECKPOINT_D="confirmed")
        assert "[would run] diff CalmFramesStack" in diff.stdout

    def test_the_project_venv_goes_first_on_the_path(self, fake_repo):
        """A fresh clone deploys with the venv's python, not the machine's.

        cdk.json runs the app as `python3 app.py`. On this Mac the system
        python3 is 3.9 with no aws-cdk-lib in it, so a deploy from a shell that
        had not activated the venv would synthesize nothing and fail in a way
        that looks like a CDK problem.

        Seen to fail by removing the PATH lines from the guard: the printed path
        is then whichever python3 the shell had.
        """
        confirm_status(fake_repo)
        venv = fake_repo / ".venv" / "bin"
        venv.mkdir(parents=True)
        marker = venv / "python3"
        marker.write_text("#!/usr/bin/env bash\necho fake venv python\n")
        marker.chmod(0o755)

        # A stand in for the CDK that prints which python3 it would find.
        probe = fake_repo / "probe.sh"
        probe.write_text("#!/usr/bin/env bash\ncommand -v python3\n")
        probe.chmod(0o755)

        result = run_guard(fake_repo, CHECKPOINT_D="confirmed", CDK=str(probe))
        assert result.returncode == 0
        assert str(marker) in result.stdout

    def test_an_unknown_action_is_refused_even_then(self, fake_repo):
        confirm_status(fake_repo)
        result = run_guard(fake_repo, "publish-everything", CHECKPOINT_D="confirmed")
        assert result.returncode == 2
        assert "unknown action" in result.stderr

    def test_the_image_action_hands_over_to_the_push_script(self, fake_repo):
        confirm_status(fake_repo)
        # A stub in place of the real push script, because the real one would
        # ask CloudFormation for the repository URI.
        stub = fake_repo / "scripts" / "push_ingest_image.sh"
        stub.write_text("#!/usr/bin/env bash\necho [stub push] ran\n")
        stub.chmod(0o755)
        result = run_guard(fake_repo, "image", CHECKPOINT_D="confirmed")
        assert result.returncode == 0
        assert "[stub push] ran" in result.stdout


class TestThePushScriptChecksTheLocksItself:
    """Running the push script directly is no way around the guard."""

    def run_push(self, repo: Path, **environment) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env.update(NO_CREDENTIALS)
        env.update(environment)
        return subprocess.run(
            ["bash", str(repo / "scripts" / "push_ingest_image.sh")],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

    def test_the_real_script_is_executable(self):
        """The guard execs it, so a copy without the bit set cannot be run."""
        assert os.access(PUSH, os.X_OK)

    def test_it_refuses_with_no_locks_open(self, fake_repo):
        result = self.run_push(fake_repo)
        assert result.returncode == 1
        assert "blocked" in result.stderr

    def test_it_refuses_with_only_the_variable(self, fake_repo):
        result = self.run_push(fake_repo, CHECKPOINT_D="confirmed")
        assert result.returncode == 1
        assert "blocked" in result.stderr

    def test_it_refuses_with_only_the_document(self, fake_repo):
        confirm_status(fake_repo)
        result = self.run_push(fake_repo)
        assert result.returncode == 1
        assert "blocked" in result.stderr


class TestThisRepositoryIsStillLocked:
    """The state of the real files, which is what actually protects the account."""

    def test_the_status_file_does_not_say_the_plan_is_confirmed(self):
        """Not "does not mention it": does not say it, the way the guard reads.

        The file is allowed to explain what the line is, which it does. What it
        must not have is that line at the start of a line, which is the only
        shape the guard accepts.
        """
        lines = (REPO / "docs" / "STATUS.md").read_text().splitlines()
        confirmed = [line for line in lines if line.lower().startswith(CONFIRMED_LINE.lower())]
        assert confirmed == []

    def test_a_document_that_only_talks_about_the_line_does_not_open_the_lock(self, fake_repo):
        """The defect this test was written after.

        A row of the real docs/STATUS.md says: add the line `AWS Paid plan:
        confirmed` to this file. An unanchored grep matched it, so one of the
        two locks had been open from the day it was written.
        """
        status = fake_repo / "docs" / "STATUS.md"
        status.write_text(
            "| Before any deploy | then add the line `AWS Paid plan: confirmed` "
            "to this file. |\n"
        )
        result = run_guard(fake_repo, CHECKPOINT_D="confirmed")
        assert result.returncode == 1
        assert "[would run]" not in result.stdout

    def test_the_real_guard_refuses_right_now(self):
        env = dict(os.environ)
        env.update(NO_CREDENTIALS)
        env["CDK"] = "echo [would run]"
        env.pop("CHECKPOINT_D", None)
        result = subprocess.run(
            ["bash", str(GUARD), "deploy"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        assert result.returncode == 1
        assert "[would run]" not in result.stdout

    def test_make_deploy_goes_through_the_guard(self):
        makefile = (REPO / "Makefile").read_text()
        deploy = makefile.split("\ndeploy:", 1)[1].split("\n\n", 1)[0]
        for line in deploy.splitlines():
            stripped = line.strip().lstrip("@")
            if not stripped or stripped.startswith("#"):
                continue
            assert "aws_guard.sh" in stripped, f"deploy runs {stripped!r} outside the guard"
