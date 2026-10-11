#!/usr/bin/env python3
"""Find dependency versions that are not pinned.

    make pins

A range is a promise that someone else's release will not break us, and that
promise gets broken on the morning of a deadline. Everything we install should
say exactly which version, so a build today and a build in October are the same
build.

Three kinds of finding:

  LOOSE  a version we install with a range or no version at all. Fix it.
         An action referenced by a tag or a branch is LOOSE too, unless it is
         written down in ACTION_TAG_EXCEPTIONS with its reason.
  NOTE   a range that a lock file already pins in practice, for example
         app/package.json next to app/package-lock.json with npm ci, or an
         action tag that has a written exception.
  OK     pinned.

Exit code 1 if anything is LOOSE, and 2 if the built in negative control is
not refused, because a checker that passes a tag ref proves nothing about the
workflows it then reads. CI runs this in the numbers job.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

EXACT_PYTHON = re.compile(r"^[A-Za-z0-9._-]+==[^\s,;]+$")
ACTION_REF = re.compile(r"uses:\s*([^\s@]+)@([^\s#]+)")
PIP_INSTALL = re.compile(r"pip install\s+(?!-)(.+)")

# A tag such as v4 moves: whoever controls the action's repository can point it
# at new code, and the next run takes that code with this repository's token.
# A full commit is the only ref that names fixed bytes. Write it with the
# release as a trailing comment, `uses: owner/action@<40 hex> # v4.4.0`.
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")

# Action tags still allowed, by file and exact ref, each with its reason. An
# exception that no longer matches any line is itself LOOSE, so one cannot
# outlive the reason written beside it.
ACTION_TAG_EXCEPTIONS: dict[tuple[str, str], str] = {}


def action_verdict(
    where_file: str,
    action: str,
    exceptions: dict[tuple[str, str], str],
    used: set[tuple[str, str]],
) -> tuple[str, str]:
    """OK for a full commit, NOTE for a written exception, LOOSE otherwise."""
    ref = action.split("@", 1)[1]
    if FULL_COMMIT.match(ref):
        return "OK", action
    key = (where_file, action)
    if key in exceptions:
        used.add(key)
        return "NOTE", f"{action}, excepted: {exceptions[key]}"
    return "LOOSE", f"{action} is a tag or a branch; pin the full commit with the release as a comment"


def scan_actions(
    where_file: str,
    text: str,
    findings: list[tuple[str, str, str]],
    exceptions: dict[tuple[str, str], str],
    used: set[tuple[str, str]],
) -> None:
    for number, line in enumerate(text.splitlines(), 1):
        match = ACTION_REF.search(line)
        if match:
            name, ref = match.groups()
            verdict, what = action_verdict(where_file, f"{name}@{ref}", exceptions, used)
            findings.append((verdict, f"{where_file}:{number}", what))


def stale_exceptions(
    exceptions: dict[tuple[str, str], str],
    used: set[tuple[str, str]],
    findings: list[tuple[str, str, str]],
) -> None:
    for key in sorted(set(exceptions) - used):
        findings.append(("LOOSE", key[0], f"the exception for {key[1]} matches nothing; delete it"))


NEGATIVE_CONTROL = """\
jobs:
  control:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@main
      - uses: actions/checkout@11d5960
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
"""


def negative_control() -> bool:
    """The checker refuses a tag, a branch, a short commit and a stale exception.

    It runs on every call, before the real files are read. A checker edited so
    that it waves a tag through would otherwise go on printing a clean report.
    """
    findings: list[tuple[str, str, str]] = []
    exceptions = {("control.yml", "actions/setup-python@v5"): "never matched"}
    used: set[tuple[str, str]] = set()
    scan_actions("control.yml", NEGATIVE_CONTROL, findings, exceptions, used)
    stale_exceptions(exceptions, used, findings)
    verdicts = [verdict for verdict, _, _ in findings]
    return verdicts == ["LOOSE", "LOOSE", "LOOSE", "OK", "LOOSE"]


def check_requirements(path: Path, findings: list[tuple[str, str, str]]) -> None:
    if not path.exists():
        return
    for number, line in enumerate(path.read_text().splitlines(), 1):
        stripped = line.split("#")[0].strip()
        if not stripped or stripped.startswith("-"):
            continue
        where = f"{path.relative_to(REPO)}:{number}"
        if EXACT_PYTHON.match(stripped):
            findings.append(("OK", where, stripped))
        else:
            findings.append(("LOOSE", where, stripped))


def check_pyproject(path: Path, findings: list[tuple[str, str, str]]) -> None:
    if not path.exists():
        return
    text = path.read_text()
    for block in re.findall(r"dependencies = \[(.*?)\]", text, re.DOTALL):
        for raw in re.findall(r'"([^"]+)"', block):
            where = str(path.relative_to(REPO))
            if EXACT_PYTHON.match(raw):
                findings.append(("OK", where, raw))
            else:
                findings.append(("LOOSE", where, raw))


def workflow_files() -> list[Path]:
    """CI, plus the action we publish and the example we tell people to copy.

    A loose version in an example someone pastes into their own repository is
    still a loose version, and it is one we asked them to take.
    """
    paths = sorted((REPO / ".github" / "workflows").glob("*.yml"))
    for extra in (
        REPO / "flashmap" / "action.yml",
        REPO / "flashmap" / "examples" / "flash-check.yml",
    ):
        if extra.exists():
            paths.append(extra)
    return paths


def check_workflows(findings: list[tuple[str, str, str]]) -> None:
    used: set[tuple[str, str]] = set()
    for path in workflow_files():
        text = path.read_text()
        scan_actions(path.relative_to(REPO).as_posix(), text, findings, ACTION_TAG_EXCEPTIONS, used)
        for number, line in enumerate(text.splitlines(), 1):
            where = f"{path.relative_to(REPO)}:{number}"
            install = PIP_INSTALL.search(line)
            if install:
                for package in install.group(1).split():
                    if package.startswith(("-", "$", '"', "'", ".", "/")) or "==" in package:
                        continue
                    if package in ("pip", "install"):
                        continue
                    findings.append(("LOOSE", where, f"pip install {package}"))
            version_assign = re.match(r"\s*VERSION=([0-9][0-9A-Za-z.\-]*)\s*$", line)
            if version_assign:
                findings.append(("OK", where, f"VERSION={version_assign.group(1)}"))
    stale_exceptions(ACTION_TAG_EXCEPTIONS, used, findings)


def check_precommit(findings: list[tuple[str, str, str]]) -> None:
    path = REPO / ".pre-commit-config.yaml"
    if not path.exists():
        return
    for number, line in enumerate(path.read_text().splitlines(), 1):
        match = re.match(r"\s*rev:\s*(\S+)", line)
        if match:
            ref = match.group(1).strip("'\"")
            verdict = "LOOSE" if ref in ("main", "master", "HEAD") else "OK"
            findings.append((verdict, f"{path.relative_to(REPO)}:{number}", f"rev: {ref}"))


def check_node(findings: list[tuple[str, str, str]]) -> None:
    path = REPO / "app" / "package.json"
    if not path.exists():
        return
    lock = REPO / "app" / "package-lock.json"
    data = json.loads(path.read_text())
    ranged = 0
    for section in ("dependencies", "devDependencies"):
        for spec in (data.get(section) or {}).values():
            if spec[:1] in "^~><" or spec == "*":
                ranged += 1
    where = str(path.relative_to(REPO))
    if ranged and lock.exists():
        findings.append((
            "NOTE",
            where,
            f"{ranged} ranged versions, pinned in practice by package-lock.json and npm ci",
        ))
    elif ranged:
        findings.append(("LOOSE", where, f"{ranged} ranged versions and no lock file"))


def check_makefile_tools(findings: list[tuple[str, str, str]]) -> None:
    for path in (REPO / "pipeline" / "infra" / "Makefile", REPO / "scripts" / "aws_guard.sh"):
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if "aws-cdk@" in line:
                ref = line.split("aws-cdk@")[1].split()[0].strip('"\'}')
                where = f"{path.relative_to(REPO)}:{number}"
                verdict = "OK" if re.match(r"^\d+\.\d+\.\d+$", ref) else "LOOSE"
                findings.append((verdict, where, f"aws-cdk@{ref}"))


def main() -> int:
    if not negative_control():
        print(
            "negative control FAILED: the checker passed a tag, a branch, a short "
            "commit or a stale exception, so its report below would mean nothing"
        )
        return 2
    print("negative control: a tag, a branch, a short commit and a stale exception are refused")
    print()

    findings: list[tuple[str, str, str]] = []
    check_requirements(REPO / "pipeline" / "infra" / "requirements.txt", findings)
    check_pyproject(REPO / "flashmap" / "pyproject.toml", findings)
    check_workflows(findings)
    check_precommit(findings)
    check_node(findings)
    check_makefile_tools(findings)

    loose = [f for f in findings if f[0] == "LOOSE"]
    notes = [f for f in findings if f[0] == "NOTE"]
    ok = [f for f in findings if f[0] == "OK"]

    for verdict, where, what in loose + notes:
        print(f"{verdict:<6} {where}: {what}")
    print()
    print(f"{len(ok)} pinned, {len(notes)} note(s), {len(loose)} loose.")
    if loose:
        print()
        print("Pin the loose ones to an exact version and rerun.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
