"""Locked CI installs propagate failure without falling back to dependency resolution.

Runs only a temporary npm stub, never npm or the project test suites.
Also runnable without pytest: python3 -m unittest eval.tests.test_ci_locked_install.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
INSTALL_JOBS = {
    "ci.yml": ("app", "ui-flashmap", "hardening"),
    "audit.yml": ("dependencies",),
}


class LockedInstallTests(unittest.TestCase):
    def assert_locked_install(self, script: str, ci_exit: int) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = root / "calls"
            after = root / "after"
            npm = root / "npm"
            npm.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >> "$NPM_CALLS"\n'
                'if [ "$1" = ci ]; then exit "$NPM_CI_EXIT"; fi\nexit 0\n'
            )
            npm.chmod(0o700)
            result = subprocess.run(
                ["/bin/bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c",
                 script + '\nprintf reached > "$AFTER_INSTALL"\n'],
                cwd=root,
                env={
                    "PATH": directory,
                    "NPM_CALLS": str(calls),
                    "NPM_CI_EXIT": str(ci_exit),
                    "AFTER_INSTALL": str(after),
                },
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            self.assertEqual(result.returncode, ci_exit, "must propagate locked install failure")
            self.assertEqual(calls.read_text().splitlines(), ["ci --ignore-scripts"])
            self.assertEqual(after.exists(), ci_exit == 0)

    def test_workflow_installs_preserve_success_and_failure(self) -> None:
        for filename, job_names in INSTALL_JOBS.items():
            workflow = yaml.safe_load((REPO / ".github/workflows" / filename).read_text())
            actual = {
                job_name
                for job_name, job in workflow["jobs"].items()
                if any("npm ci" in step.get("run", "") for step in job["steps"])
            }
            self.assertEqual(actual, set(job_names))
            for job_name in job_names:
                job = workflow["jobs"][job_name]
                steps = [step for step in job["steps"] if "npm ci" in step.get("run", "")]
                self.assertEqual(len(steps), 1)
                self.assertFalse(job.get("continue-on-error", False))
                self.assertFalse(steps[0].get("continue-on-error", False))
                for ci_exit in (0, 23):
                    with self.subTest(workflow=filename, job=job_name, ci_exit=ci_exit):
                        self.assert_locked_install(steps[0]["run"], ci_exit)

    def test_old_fallback_is_rejected(self) -> None:
        old = "npm ci --ignore-scripts || npm install --ignore-scripts --no-audit --no-fund"
        with self.assertRaisesRegex(AssertionError, "must propagate locked install failure"):
            self.assert_locked_install(old, 23)


if __name__ == "__main__":
    unittest.main()
