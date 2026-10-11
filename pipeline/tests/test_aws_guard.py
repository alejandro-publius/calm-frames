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

import importlib.metadata
import importlib.util
import json
import os
import re
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


def would_run(result: subprocess.CompletedProcess) -> str:
    """The one command line the guard handed to the stand-in CDK."""
    lines = [line for line in result.stdout.splitlines() if line.startswith("[would run]")]
    assert len(lines) == 1, f"expected one CDK command, got {lines!r}"
    return lines[0]


class TestTheSigningKeyIsNeverDroppedQuietly:
    """SIGNING_KEY_PARAMETER keeps the cloud key wired in, and leaving it out is said aloud.

    The stack wires the ingest task to a signing key only when the
    calmframes:signingKeyParameter context is passed. On Oct 9 that context was
    added by hand inside the CDK variable, and the guard had no way to pass it,
    so the next routine `make deploy` would have taken the key away without a
    word and every later upload would have published nothing.

    Seen to fail, Oct 9 2026, one mutation at a time: dropping the line that
    adds the context turned the deploy and diff tests red; loosening the name
    check to match anything let `*`, the first of the six bad names tried,
    through with exit 0; and dropping the call that reports the key turned the
    "none" test and the deploy test red. Each restore went green.
    """

    PARAMETER = "/calm-frames/cloud-signing-key"

    def test_a_named_parameter_reaches_the_deploy(self, fake_repo):
        confirm_status(fake_repo)
        result = run_guard(fake_repo, CHECKPOINT_D="confirmed", SIGNING_KEY_PARAMETER=self.PARAMETER)
        assert result.returncode == 0
        command = would_run(result)
        assert command.startswith("[would run] deploy CalmFramesStack ")
        assert f"-c calmframes:signingKeyParameter={self.PARAMETER}" in command
        assert f"Signing key: the task may read the SSM parameter {self.PARAMETER}" in result.stdout

    def test_a_diff_shows_the_same_template_the_deploy_would(self, fake_repo):
        confirm_status(fake_repo)
        result = run_guard(
            fake_repo, "diff", CHECKPOINT_D="confirmed", SIGNING_KEY_PARAMETER=self.PARAMETER
        )
        assert result.returncode == 0
        assert f"-c calmframes:signingKeyParameter={self.PARAMETER}" in would_run(result)

    def test_without_it_the_deploy_says_the_key_goes(self, fake_repo):
        confirm_status(fake_repo)
        result = run_guard(fake_repo, CHECKPOINT_D="confirmed")
        assert result.returncode == 0
        assert "signingKeyParameter" not in would_run(result)
        assert "Signing key: none." in result.stdout
        assert f"SIGNING_KEY_PARAMETER={self.PARAMETER} to keep it" in result.stdout

    def test_a_name_ssm_would_refuse_is_refused_here(self, fake_repo):
        """The value lands in a word-split command line and in an IAM resource ARN."""
        confirm_status(fake_repo)
        for bad in ("*", "/calm-frames/*", "/calm-frames/key extra", "/calm-frames/key;id", "$(id)", "/a//b"):
            result = run_guard(fake_repo, CHECKPOINT_D="confirmed", SIGNING_KEY_PARAMETER=bad)
            assert result.returncode == 2, f"{bad!r} was accepted"
            assert "is not an SSM parameter name" in result.stderr
            assert "[would run]" not in result.stdout

    def test_the_locks_still_come_first(self, fake_repo):
        result = run_guard(fake_repo, SIGNING_KEY_PARAMETER=self.PARAMETER)
        assert result.returncode == 1
        assert "is blocked" in result.stderr
        assert "[would run]" not in result.stdout

    def test_the_infra_makefile_sends_the_same_context(self):
        """`make -C pipeline/infra diff` is the other road to the CDK.

        Dry run only (`make -n`), with echo as the CDK, so nothing runs. Seen
        to fail, Oct 9 2026: without the `$(if ...)` line in
        pipeline/infra/Makefile the key's context was missing and this went red.
        """
        env = dict(os.environ)
        env.update(NO_CREDENTIALS)
        env.pop("SIGNING_KEY_PARAMETER", None)

        def dry_run(*extra: str) -> str:
            finished = subprocess.run(
                ["make", "-n", "-C", str(REPO / "pipeline" / "infra"), "diff", "CDK=echo [would run]", *extra],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
            assert finished.returncode == 0, finished.stderr
            return finished.stdout

        assert f"-c calmframes:signingKeyParameter={self.PARAMETER}" in dry_run(
            f"SIGNING_KEY_PARAMETER={self.PARAMETER}"
        )
        assert "signingKeyParameter" not in dry_run()


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

    def test_a_document_that_only_talks_about_the_line_does_not_open_it(self, fake_repo):
        """The Sep 17 defect, still alive in the second script until Oct 9.

        The guard's pattern was anchored on Sep 17 after a row of
        docs/STATUS.md that quotes the line opened its lock. This script kept
        an unanchored copy, so the same row opened its lock too. `aws` and
        `docker` are stubs on PATH here, so even with the lock wrongly open the
        script reaches no account and no daemon.

        Seen to fail, Oct 9 2026: with the pattern unanchored again, the script
        walked past both locks into the stubs and exited 0, and this test and
        the one below went red.
        """
        status = fake_repo / "docs" / "STATUS.md"
        status.write_text(
            "| Before any deploy | then add the line `AWS Paid plan: confirmed` "
            "to this file. |\n"
        )
        stubs = fake_repo / "stubs"
        stubs.mkdir()
        for tool in ("aws", "docker"):
            stub = stubs / tool
            stub.write_text(f'#!/usr/bin/env bash\necho "[stub {tool}] $*"\n')
            stub.chmod(0o755)
        result = self.run_push(
            fake_repo, CHECKPOINT_D="confirmed", PATH=f"{stubs}{os.pathsep}{os.environ['PATH']}"
        )
        assert result.returncode == 1
        assert "blocked" in result.stderr
        assert "[stub" not in result.stdout

    def test_both_scripts_read_the_line_the_same_way(self):
        def pattern(path: Path) -> str:
            found = re.findall(r"^STATUS_PATTERN='([^']*)'$", path.read_text(), re.MULTILINE)
            assert len(found) == 1, f"{path.name} should set STATUS_PATTERN once"
            return found[0]

        assert pattern(PUSH) == pattern(GUARD)
        assert pattern(PUSH).startswith("^")


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


CLI_PIN = re.compile(r"aws-cdk@(\d+)\.(\d+)\.(\d+)")
# Every place a person or a script reads the CDK CLI version from.
PINNED_IN = (
    REPO / "scripts" / "aws_guard.sh",
    REPO / "pipeline" / "infra" / "Makefile",
    REPO / "pipeline" / "infra" / "README.md",
)


def cli_pins() -> dict[str, set[tuple[int, int, int]]]:
    return {
        str(path.relative_to(REPO)): {
            tuple(int(part) for part in match.groups())
            for match in CLI_PIN.finditer(path.read_text(encoding="utf-8"))
        }
        for path in PINNED_IN
    }


class TestTheCliCanReadWhatTheLibraryWrites:
    """The pinned CDK CLI is one version, and it reads what the pinned library writes.

    The Oct 9 deploy could not use the pin it found here. CLI 2.1032.0 stops
    right after synth with "Cloud assembly schema version mismatch: Maximum
    schema version supported is 48.x.x, but found 54.0.0. You need at least
    CLI version 2.1142.0 to read this manifest.", so the deploy ran with the
    CLI named on the command line instead. A pin that only works when somebody
    overrides it is not a pin.

    The minimum is declared by the aws-cdk.cloud-assembly-schema package, not
    by aws-cdk-lib, which only asks for a schema in a range. The first hosted
    run of the test below, on dcb27a1 the same day, installed that range fresh
    and got a newer schema declaring 2.1144.0, so it went red there while the
    frozen venv here stayed green. The class after this one pins the schema.

    Seen to fail, Oct 9 2026: putting 2.1032.0 back in scripts/aws_guard.sh
    alone turned both tests red, one for the disagreement and one for the
    version; putting it back in all three files turned only the version test
    red, with the schema's own minimum, 2.1142.0, in the message.
    """

    def test_every_place_names_one_version(self):
        pins = cli_pins()
        assert all(pins.values()), f"a file lost its aws-cdk@ pin: {pins}"
        versions = set().union(*pins.values())
        assert len(versions) == 1, f"the CDK CLI is pinned to more than one version: {pins}"

    def test_the_pin_is_at_least_the_minimum_the_library_declares(self):
        schema = pytest.importorskip(
            "aws_cdk.cloud_assembly_schema", reason="aws-cdk-lib is needed for this check"
        )
        minimum = tuple(int(part) for part in schema.Manifest.cli_version().split("."))
        declared_by = f"aws-cdk.cloud-assembly-schema {installed_version('aws-cdk.cloud-assembly-schema')}"
        for where, versions in cli_pins().items():
            for version in versions:
                assert version >= minimum, (
                    f"{where} pins aws-cdk@{'.'.join(map(str, version))}, and the installed "
                    f"{declared_by} declares at least {'.'.join(map(str, minimum))}"
                )


INFRA_REQUIREMENTS = REPO / "pipeline" / "infra" / "requirements.txt"
# An exact pin on a line of its own, the way pip reads it: name==version, then
# at most a comment.
EXACT_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s#;,]+)", re.MULTILINE)


def infra_pins() -> dict[str, str]:
    """Every exact pin in pipeline/infra/requirements.txt, by lower case name."""
    text = INFRA_REQUIREMENTS.read_text(encoding="utf-8")
    return {name.lower(): version for name, version in EXACT_PIN.findall(text)}


def installed_version(package: str) -> str:
    """The version in this interpreter, or a skip that the hosted job turns into a failure."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        pytest.skip(f"{package} is not installed; aws-cdk-lib is needed for this check")


class TestWhatAwsCdkLibPullsInIsPinnedToo:
    """aws-cdk-lib declares ranges for its own runtime, and a fresh install takes the newest.

    pipeline/infra/requirements.txt pinned aws-cdk-lib and constructs and
    nothing else. aws-cdk-lib 2.270.0 asks for aws-cdk.cloud-assembly-schema
    >=54.11.0,<55.0.0, jsii >=1.139.0,<2.0.0 and
    aws-cdk.asset-node-proxy-agent-v6 >=2.1.2,<3.0.0. The schema writes the
    manifest and declares the oldest CLI that reads it; jsii is the bridge
    every construct runs through; the proxy agent is a Lambda layer asset
    whose hash can reach the template. This venv froze 54.24.0, 1.140.0 and
    2.1.3, which is what the Oct 9, 2026 deploy ran with, and the hosted Audit
    runner on dcb27a1 installed the ranges fresh and got a schema that
    declares CLI 2.1144.0. Each of the three is pinned now at the version
    installed here, and this test keeps the file and the venv saying the same
    thing, so `make ci` and a fresh install test one set of packages.

    Seen to fail, Oct 9 2026: with the three lines absent from the
    requirements file, all three cases went red naming the missing pin and
    the version this venv has; adding the lines turned them green.
    """

    FLOATING_IN_AWS_CDK_LIB = (
        "aws-cdk.cloud-assembly-schema",
        "jsii",
        "aws-cdk.asset-node-proxy-agent-v6",
    )

    @pytest.mark.parametrize("package", FLOATING_IN_AWS_CDK_LIB)
    def test_it_is_pinned_to_the_version_installed_here(self, package):
        installed = installed_version(package)
        pins = infra_pins()
        assert package in pins, (
            f"pipeline/infra/requirements.txt does not pin {package}; aws-cdk-lib declares "
            f"only a range for it, so a fresh install floats where this venv has {installed}"
        )
        assert pins[package] == installed, (
            f"pipeline/infra/requirements.txt pins {package}=={pins[package]} and this venv "
            f"has {installed}; a fresh install and `make ci` would test two different things"
        )


SBOM_SCRIPT = REPO / "scripts" / "sbom.py"
AUDIT_WORKFLOW = REPO / ".github" / "workflows" / "audit.yml"
PYTHON_BILLS = (REPO / "docs" / "SBOM.ingest.cdx.json", REPO / "docs" / "SBOM.cdk.cdx.json")
APP_BILL = REPO / "docs" / "SBOM.app.cdx.json"
# Where the sbom job tells scripts/sbom.py to leave the fresh bills, and what
# the job uploads when the compare fails. Under .logs/, which is gitignored.
KEPT_BILLS = ".logs/sbom-check"


def recorded_tools(bill: Path) -> dict[str, str]:
    """name -> version of every generator a committed bill says wrote it."""
    document = json.loads(bill.read_text(encoding="utf-8"))
    return {tool["name"]: tool["version"] for tool in document["metadata"]["tools"]["components"]}


def sbom_job() -> str:
    """The sbom job of the Audit workflow as text, the way test_mutate_gate reads ci.yml."""
    workflow = AUDIT_WORKFLOW.read_text(encoding="utf-8")
    return workflow.split("\n  sbom:\n", 1)[1].split("\n  infra:\n", 1)[0]


class TestTheBillsRecordThePinnedGenerators:
    """What a bill says wrote it is content to the byte compare, so it is pinned too.

    These live in this file rather than one of their own because the Audit
    workflow's infra job runs this file on the hosted runner, which is where
    the drift showed. On dcb27a1 (Oct 9, 2026) the app bill failed the compare
    with the same package-lock.json on both sides: scripts/sbom.py pinned
    @cyclonedx/cyclonedx-npm@6.0.1 and left its library to a caret range, so
    the runner's fresh install resolved a different @cyclonedx/cyclonedx-library
    than the 10.3.0 the committed bill records under metadata.tools. The two
    Python bills matched by luck. cyclonedx-bom==7.4.0 leaves
    cyclonedx-python-lib floating the same way, and both sides happened to
    resolve 11.12.0. Every version asserted here is read from the committed
    bills, so a bill regenerated by a different generator fails these tests
    instead of being committed quietly.

    Seen to fail, Oct 9 2026: with the library pins absent from
    scripts/sbom.py and the workflow, the Node version taken from .nvmrc and
    no artifact step, the four tests after the first went red one cause each;
    adding the pins, the exact Node and the artifact step turned them green.
    """

    def test_the_python_bills_were_written_by_one_pair(self):
        tools = {bill.name: recorded_tools(bill) for bill in PYTHON_BILLS}
        pairs = {(t["cyclonedx-py"], t["cyclonedx-python-lib"]) for t in tools.values()}
        assert len(pairs) == 1, f"the Python bills were written by different generators: {tools}"

    def test_the_script_pins_the_generator_and_its_library(self):
        script = SBOM_SCRIPT.read_text(encoding="utf-8")
        python = recorded_tools(PYTHON_BILLS[0])
        app = recorded_tools(APP_BILL)
        for pin in (
            f"cyclonedx-bom=={python['cyclonedx-py']}",
            f"cyclonedx-python-lib=={python['cyclonedx-python-lib']}",
            f"@cyclonedx/cyclonedx-npm@{app['cyclonedx-npm']}",
            f"@cyclonedx/cyclonedx-library@{app['cyclonedx-library']}",
        ):
            assert pin in script, (
                f"scripts/sbom.py does not pin {pin}, which the committed bills record "
                f"under metadata.tools; without it the bytes depend on the day's resolve"
            )

    def test_the_audit_workflow_installs_the_same_python_pair(self):
        python = recorded_tools(PYTHON_BILLS[0])
        job = sbom_job()
        for pin in (
            f"cyclonedx-bom=={python['cyclonedx-py']}",
            f"cyclonedx-python-lib=={python['cyclonedx-python-lib']}",
        ):
            assert pin in job, f"the sbom job in .github/workflows/audit.yml does not install {pin}"

    def test_the_sbom_job_pins_node_exactly(self):
        """npm is a tool entry in the app bill, and npm comes with Node.

        .nvmrc says 22, which is right for the app and floats for this one job:
        every Node 22 release that bundles a newer npm would fail the compare
        with no change in this repository. The committed bill records npm
        10.9.8, which the local Node 22.23.2 ships with; the dcb27a1 run took
        22.23.3 from .nvmrc.
        """
        job = sbom_job()
        assert "node-version-file" not in job, "the sbom job takes its Node from .nvmrc, which floats"
        assert re.search(r"^\s+node-version:\s*\d+\.\d+\.\d+\s*$", job, re.MULTILINE), (
            "the sbom job does not pin an exact Node version"
        )

    def test_a_failed_compare_keeps_what_it_wrote(self):
        """The next failure names itself: the fresh bills and the report become an artifact."""
        job = sbom_job()
        assert f"scripts/sbom.py --check --keep {KEPT_BILLS}" in job, (
            "the sbom job does not tell scripts/sbom.py where to leave the fresh bills"
        )
        retain = job.split("uses: actions/upload-artifact@", 1)
        assert len(retain) == 2, "the sbom job has no artifact step"
        assert "if: failure()" in retain[0].rsplit("      - name:", 1)[1]
        assert f"path: {KEPT_BILLS}" in retain[1]
        assert "include-hidden-files: true" in retain[1], ".logs is a hidden directory"
        assert ".logs/" in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()


def load_sbom_script():
    """scripts/sbom.py as a module. Importing it runs no generator."""
    spec = importlib.util.spec_from_file_location("calm_frames_sbom", SBOM_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestACompareFailureNamesItsCause:
    """scripts/sbom.py --check tells the environment, a dependency and anything else apart.

    The dcb27a1 failure said "does not match what is installed" about a bill
    whose components were identical on both sides, and the fresh bill was gone
    with the runner. explain() now reads both bills back and says which of
    three things happened, with the first differing line, and report.json
    carries the same as data for the artifact. These tests run it on small
    synthetic bills, one cause at a time, and run the generator readback on
    the committed app bill, which ties the script's pins to the bills a second
    way, through the script's own reader.

    Seen to fail, Oct 9 2026: with the tools comparison in explain() disabled,
    the environment case went red for the missing "generators differ" line and
    the pins case stayed green; restoring it turned everything green.
    """

    @staticmethod
    def bill(**changes) -> dict:
        document = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "metadata": {
                "tools": {
                    "components": [
                        {"type": "application", "name": "npm", "version": "10.9.8"},
                        {
                            "type": "library",
                            "name": "cyclonedx-library",
                            "group": "@cyclonedx",
                            "version": "10.3.0",
                        },
                    ]
                }
            },
            "components": [
                {"type": "library", "name": "a", "version": "1.0.0", "purl": "pkg:npm/a@1.0.0"},
                {
                    "type": "library",
                    "name": "b",
                    "version": "2.0.0",
                    "purl": "pkg:npm/b@2.0.0",
                    "licenses": [{"license": {"id": "MIT"}}],
                },
            ],
        }
        document.update(changes)
        return document

    @staticmethod
    def write(path: Path, document: dict) -> Path:
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        return path

    def test_a_different_generator_is_called_the_environment(self, tmp_path):
        sbom = load_sbom_script()
        committed = self.write(tmp_path / "committed.json", self.bill())
        fresh = self.bill()
        fresh["metadata"]["tools"]["components"][0]["version"] = "10.9.9"
        lines, report = sbom.explain(committed, self.write(tmp_path / "fresh.json", fresh))
        assert any("the generators differ" in line for line in lines), lines
        assert any("npm: committed 10.9.8, fresh 10.9.9" in line for line in lines), lines
        assert not any("added:" in line or "removed:" in line for line in lines), lines
        assert report["committed"]["tools"]["npm"] == "10.9.8"
        assert report["fresh"]["tools"]["npm"] == "10.9.9"
        assert report["added"] == [] and report["removed"] == []

    def test_a_moved_dependency_is_listed_by_purl(self, tmp_path):
        sbom = load_sbom_script()
        committed = self.write(tmp_path / "committed.json", self.bill())
        fresh = self.bill()
        fresh["components"] = fresh["components"][1:] + [
            {"type": "library", "name": "c", "version": "3.0.0", "purl": "pkg:npm/c@3.0.0"}
        ]
        lines, report = sbom.explain(committed, self.write(tmp_path / "fresh.json", fresh))
        assert not any("the generators differ" in line for line in lines), lines
        assert any("components: 2 committed, 2 fresh, 1 added, 1 removed" in line for line in lines), lines
        assert any(line.strip() == "added: pkg:npm/c@3.0.0" for line in lines), lines
        assert any(line.strip() == "removed: pkg:npm/a@1.0.0" for line in lines), lines
        assert report["added"] == ["pkg:npm/c@3.0.0"]
        assert report["removed"] == ["pkg:npm/a@1.0.0"]

    def test_anything_else_is_shown_by_its_first_differing_line(self, tmp_path):
        sbom = load_sbom_script()
        committed = self.write(tmp_path / "committed.json", self.bill())
        fresh = self.bill()
        fresh["components"][1]["licenses"][0]["license"]["id"] = "Apache-2.0"
        fresh_path = self.write(tmp_path / "fresh.json", fresh)
        lines, report = sbom.explain(committed, fresh_path)
        assert any("same generators and the same components" in line for line in lines), lines
        expected = next(
            number
            for number, (left, right) in enumerate(
                zip(committed.read_text().splitlines(), fresh_path.read_text().splitlines()), 1
            )
            if left != right
        )
        assert report["first_difference"] == {
            "line": expected,
            "committed": '"id": "MIT"',
            "fresh": '"id": "Apache-2.0"',
        }
        assert f"first difference at line {expected}:" in lines

    def test_the_readback_knows_the_pinned_generators(self, tmp_path):
        sbom = load_sbom_script()
        assert sbom.pinned_version("cyclonedx-bom==7.4.0") == "7.4.0"
        assert sbom.pinned_version("@cyclonedx/cyclonedx-library@10.3.0") == "10.3.0"
        wrong = self.bill()
        wrong["metadata"]["tools"]["components"][1]["version"] = "10.4.0"
        found = sbom.unpinned_generators(self.write(tmp_path / "SBOM.app.cdx.json", wrong))
        assert len(found) == 1 and "cyclonedx-library 10.4.0 wrote it" in found[0], found
        assert f"pins {sbom.PINNED_TOOLS['cyclonedx-library']}" in found[0]
        # The committed bills were written by the pinned generators, read the
        # same way the script reads a fresh one.
        for bill in (*PYTHON_BILLS, APP_BILL):
            assert sbom.unpinned_generators(bill) == [], bill.name


class TestTheDeployRecordNamesNoAccount:
    """What the repository says about the Oct 9 deploy gives the account away nowhere.

    The record in results/aws_deploy_2026-10-09.json was written from describe
    calls whose raw output is full of the account id, the bucket names, the
    distribution domain, ARNs and the ECR repository URI. The repository goes
    public on Oct 21, so each of those shapes is looked for here, in the record
    and in the two documents that describe the deploy. A failure names the shape
    and the file, never the value, so the CI log does not repeat the leak.

    Seen to fail, Oct 9 2026: a twelve digit number put in the record's
    region field, an ARN in its stack name, the real distribution domain in
    pipeline/infra/README.md and an email address in the record each turned
    this red, and each went green again when taken out.
    """

    # The shapes, not the values. A placeholder account id that every AWS
    # document uses is allowed, and so is the all zeros one `make synth` passes.
    PLACEHOLDER_ACCOUNTS = {"000000000000", "123456789012"}
    SHAPES = {
        "an account id": re.compile(r"(?<!\d)\d{12}(?!\d)"),
        "an ARN": re.compile(r"arn:aws[a-z-]*:"),
        "a CloudFront distribution domain": re.compile(r"\b[a-z0-9]{8,}\.cloudfront\.net\b"),
        "an ECR repository URI": re.compile(r"\.dkr\.ecr\."),
        "a generated bucket, table or log group name": re.compile(
            r"(?i)\bcalmframesstack-[a-z0-9]+-[a-z0-9]{6,}"
        ),
    }
    EMAIL = re.compile(r"[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")

    def records(self) -> list[Path]:
        return sorted((REPO / "results").glob("aws_*.json"))

    def documents(self) -> list[Path]:
        return [REPO / "docs" / "SECURITY.md", REPO / "pipeline" / "infra" / "README.md"]

    def leaks(self, path: Path, shapes: dict[str, re.Pattern[str]]) -> list[str]:
        text = path.read_text(encoding="utf-8")
        found = []
        for what, shape in shapes.items():
            hits = [hit for hit in shape.findall(text) if hit not in self.PLACEHOLDER_ACCOUNTS]
            if hits:
                found.append(f"{path.relative_to(REPO)} has {len(hits)} x {what}")
        return found

    def test_the_record_exists(self):
        assert [path.name for path in self.records()] == ["aws_deploy_2026-10-09.json"]

    def test_the_record_names_no_account_bucket_domain_or_person(self):
        shapes = dict(self.SHAPES, **{"an email address": self.EMAIL})
        found = [leak for path in self.records() for leak in self.leaks(path, shapes)]
        assert found == []

    def test_the_documents_about_the_deploy_name_no_account(self):
        found = [leak for path in self.documents() for leak in self.leaks(path, self.SHAPES)]
        assert found == []
