#!/usr/bin/env python3
"""Audit every dependency, and make each exception say why in writing.

    make audit           run both audits and write results/audit.json
    make audit-check     the same, but fail if anything is not accounted for

Two ecosystems, four inputs:

  pip-audit over the container's hash pinned requirements, the CDK's
  requirements and the development venv. These are what we install.

  npm audit over app/, which is the Vega sample's dependency tree plus ours.

The rule this enforces: a finding is either fixed or written down. An exception
in scripts/audit_exceptions.toml names the package, the advisory ids that were
read, who accepted it, why, and the date it has to be looked at again. A new
advisory against an already accepted package fails the check, because the ids
will not match, and so does an exception whose review date has passed.

Nothing here reaches AWS or any private service. npm audit and pip-audit both
query public advisory databases.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXCEPTIONS = REPO / "scripts" / "audit_exceptions.toml"
OUTPUT = REPO / "results" / "audit.json"

PIP_AUDIT_VERSION = "2.9.0"

PYTHON_SOURCES = [
    ("ingest container", "pipeline/infra/ingest/requirements.txt"),
    ("cdk", "pipeline/infra/requirements.txt"),
]


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, cwd=REPO, **kwargs)


def pip_audit_available() -> list[str] | None:
    """How to run pip-audit here: installed, or through uvx, or not at all."""
    if shutil.which("pip-audit"):
        return ["pip-audit"]
    if shutil.which("uvx"):
        return ["uvx", "--from", f"pip-audit=={PIP_AUDIT_VERSION}", "pip-audit"]
    return None


def audit_python(freeze_file: Path | None) -> dict:
    runner = pip_audit_available()
    if runner is None:
        return {"ran": False, "reason": "pip-audit is not installed and uvx is not available"}

    sources = list(PYTHON_SOURCES)
    if freeze_file is not None:
        sources.append(("development venv", str(freeze_file)))

    results = []
    for name, relative in sources:
        path = Path(relative)
        if not path.is_absolute():
            path = REPO / relative
        if not path.exists():
            results.append({"name": name, "path": relative, "ran": False, "reason": "no such file"})
            continue
        completed = run(
            runner + ["-r", str(path), "--no-deps", "--progress-spinner", "off", "--format", "json"]
        )
        try:
            payload = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            results.append(
                {
                    "name": name,
                    "path": relative,
                    "ran": False,
                    "reason": (completed.stderr or completed.stdout)[-400:],
                }
            )
            continue
        findings = [
            {
                "package": entry.get("name"),
                "version": entry.get("version"),
                "ids": sorted(v.get("id", "") for v in entry.get("vulns", [])),
            }
            for entry in payload.get("dependencies", [])
            if entry.get("vulns")
        ]
        results.append(
            {
                "name": name,
                "path": relative,
                "ran": True,
                "packages_audited": len(payload.get("dependencies", [])),
                "findings": findings,
            }
        )
    return {"ran": True, "sources": results}


def audit_npm() -> dict:
    app = REPO / "app"
    if not (app / "package-lock.json").exists():
        return {"ran": False, "reason": "app/package-lock.json is missing"}
    if not (app / "node_modules").exists():
        return {"ran": False, "reason": "app/node_modules is missing, run npm ci first"}
    completed = subprocess.run(
        ["npm", "audit", "--json"], capture_output=True, text=True, cwd=app
    )
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return {"ran": False, "reason": (completed.stderr or completed.stdout)[-400:]}

    findings = []
    for name, entry in sorted(payload.get("vulnerabilities", {}).items()):
        ids = sorted(
            {
                str(via.get("source"))
                for via in entry.get("via", [])
                if isinstance(via, dict) and via.get("source")
            }
        )
        findings.append(
            {
                "package": name,
                "severity": entry.get("severity"),
                "direct": bool(entry.get("isDirect")),
                "ids": ids,
                "fix_available": bool(entry.get("fixAvailable")),
            }
        )
    return {
        "ran": True,
        "totals": payload.get("metadata", {}).get("vulnerabilities", {}),
        "findings": findings,
    }


def load_exceptions() -> list[dict]:
    if not EXCEPTIONS.exists():
        return []
    data = tomllib.loads(EXCEPTIONS.read_text())
    return data.get("exception", [])


def index_exceptions(exceptions: list[dict]) -> dict[tuple[str, str], dict]:
    index: dict[tuple[str, str], dict] = {}
    for exception in exceptions:
        for package in exception.get("packages", []):
            index[(exception["ecosystem"], package)] = exception
    return index


def compare(report: dict, exceptions: list[dict]) -> list[str]:
    """Every reason this audit should fail. An empty list means it passes."""
    problems: list[str] = []
    index = index_exceptions(exceptions)
    today = date.today()

    for exception in exceptions:
        review = exception.get("review_by")
        if review and date.fromisoformat(review) < today:
            problems.append(
                f"the exception '{exception['group']}' was due for review on {review}"
            )
        for field in ("group", "ecosystem", "why", "accepted_by", "review_by"):
            if not exception.get(field):
                problems.append(f"an exception is missing its {field}")

    python = report.get("python", {})
    if not python.get("ran"):
        problems.append(f"pip-audit did not run: {python.get('reason')}")
    for source in python.get("sources", []):
        if not source.get("ran"):
            problems.append(f"pip-audit did not run for {source['name']}: {source.get('reason')}")
        for finding in source.get("findings", []):
            exception = index.get(("pip", finding["package"]))
            if exception is None:
                problems.append(
                    f"{finding['package']} {finding['version']} has "
                    f"{len(finding['ids'])} advisory(s) and no exception: {', '.join(finding['ids'])}"
                )

    npm = report.get("npm", {})
    if not npm.get("ran"):
        problems.append(f"npm audit did not run: {npm.get('reason')}")
    for finding in npm.get("findings", []):
        exception = index.get(("npm", finding["package"]))
        if exception is None:
            problems.append(
                f"npm: {finding['package']} ({finding['severity']}) has no exception"
            )
            continue
        known = set(exception.get("advisories", {}).get(finding["package"], []))
        new = set(finding["ids"]) - known
        if new:
            problems.append(
                f"npm: {finding['package']} has advisory(s) nobody has read yet: "
                f"{', '.join(sorted(new))}"
            )
    return problems


def published_numbers(report: dict, exceptions: list[dict]) -> dict:
    npm = report.get("npm", {})
    totals = npm.get("totals", {}) if npm.get("ran") else {}
    python_findings = sum(
        len(source.get("findings", []))
        for source in report.get("python", {}).get("sources", [])
    )
    return {
        "python_packages_with_advisories": python_findings,
        "npm_packages_with_advisories": len(npm.get("findings", [])) if npm.get("ran") else 0,
        "npm_advisories_total": sum(
            len(finding["ids"]) for finding in npm.get("findings", [])
        )
        if npm.get("ran")
        else 0,
        "npm_critical": totals.get("critical", 0),
        "npm_high": totals.get("high", 0),
        "exception_groups": len(exceptions),
        "exceptions_in_the_shipped_bundle": sum(
            1 for exception in exceptions if exception.get("ships") is True
        ),
    }


def update_exception_ids(report: dict) -> None:
    """Write today's advisory ids into the exceptions file, for review.

    The text of an exception is written by a person. The list of advisory ids
    is not: it is what npm reported when the exception was accepted, and it is
    what makes a new advisory fail the check tomorrow.
    """
    text = EXCEPTIONS.read_text()
    exceptions = load_exceptions()
    index = index_exceptions(exceptions)
    per_group: dict[str, dict[str, list[str]]] = {
        exception["group"]: {} for exception in exceptions
    }
    for finding in report.get("npm", {}).get("findings", []):
        exception = index.get(("npm", finding["package"]))
        if exception is not None:
            per_group[exception["group"]][finding["package"]] = finding["ids"]

    for group, advisories in per_group.items():
        # Quoted keys: an npm package name has @ and / in it, which bare TOML
        # keys may not.
        block = "\n".join(
            f"{json.dumps(package)} = {json.dumps(ids)}"
            for package, ids in sorted(advisories.items())
        )
        pattern = re.compile(
            rf'(group = "{re.escape(group)}".*?\[exception\.advisories\]\n)(.*?)(?=\n\[|\Z)',
            re.DOTALL,
        )
        if pattern.search(text):
            text = pattern.sub(lambda m: m.group(1) + block + "\n", text, count=1)
    EXCEPTIONS.write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail on anything unaccounted for")
    parser.add_argument("--update-ids", action="store_true", help="refresh the advisory ids")
    parser.add_argument("--freeze", help="a requirements file for the development venv")
    args = parser.parse_args(argv)

    report = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": audit_python(Path(args.freeze) if args.freeze else None),
        "npm": audit_npm(),
    }
    exceptions = load_exceptions()
    report["published"] = published_numbers(report, exceptions)
    report["statement"] = (
        "pip-audit and npm audit over the scanned project dependencies. Findings, "
        "exception coverage and expired reviews are recorded below. Nonempty "
        "problems block audit acceptance; listing a finding does not waive it."
    )

    if args.update_ids:
        update_exception_ids(report)
        exceptions = load_exceptions()

    problems = compare(report, exceptions)
    report["problems"] = problems

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")

    published = report["published"]
    print(f"python: {published['python_packages_with_advisories']} package(s) with advisories")
    print(
        f"npm: {published['npm_packages_with_advisories']} package(s), "
        f"{published['npm_advisories_total']} advisory(s), "
        f"{published['npm_critical']} critical, {published['npm_high']} high"
    )
    print(f"{published['exception_groups']} exception group(s) in {EXCEPTIONS.name}")
    print(f"written to {OUTPUT.relative_to(REPO)}")

    if problems:
        print()
        print("Not accounted for:")
        for problem in problems:
            print(f"  {problem}")
        if args.check:
            print()
            print("Fix it, or add an exception that says why, with a review date.")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
