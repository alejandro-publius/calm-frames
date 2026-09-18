#!/usr/bin/env python3
"""Find dependency versions that are not pinned.

    make pins

A range is a promise that someone else's release will not break us, and that
promise gets broken on the morning of a deadline. Everything we install should
say exactly which version, so a build today and a build in October are the same
build.

Three kinds of finding:

  LOOSE  a version we install with a range or no version at all. Fix it.
  NOTE   a range that a lock file already pins in practice, for example
         app/package.json next to app/package-lock.json with npm ci.
  OK     pinned.

Exit code 1 if anything is LOOSE.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

EXACT_PYTHON = re.compile(r"^[A-Za-z0-9._-]+==[^\s,;]+$")
ACTION_REF = re.compile(r"uses:\s*([^\s@]+)@([^\s#]+)")
PIP_INSTALL = re.compile(r"pip install\s+(?!-)(.+)")


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
    for path in workflow_files():
        for number, line in enumerate(path.read_text().splitlines(), 1):
            where = f"{path.relative_to(REPO)}:{number}"
            action = ACTION_REF.search(line)
            if action:
                name, ref = action.groups()
                # A major tag such as v4 moves. It is what almost every project
                # uses and GitHub's own actions are the lower risk ones, so this
                # is a note rather than a failure. A digest is the strict form.
                verdict = "OK" if len(ref) == 40 and all(c in "0123456789abcdef" for c in ref) else "NOTE"
                findings.append((verdict, where, f"{name}@{ref}"))
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
        for name, spec in (data.get(section) or {}).items():
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
