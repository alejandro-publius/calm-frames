"""A demo gate cannot pass when its verification record could not be written.

Uses fake flashmap, ffprobe and ffmpeg commands, with no media decoding,
capture or generation. Runnable directly with unittest as well as pytest.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check_video.sh"


class VideoEvidenceWriteTests(unittest.TestCase):
    def run_gate(self, *, output_is_directory: bool, flash_exit: int = 0, selftest=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stubs = root / "stubs"
            module = stubs / "flashmap"
            module.mkdir(parents=True)
            (module / "__init__.py").write_text('__version__ = "test-stub"\n')
            (module / "__main__.py").write_text(
                "import json, os, pathlib, sys\n"
                "if sys.argv[1:] == ['--version']:\n    sys.exit(0)\n"
                "assert sys.argv[1] == 'check'\n"
                "code = int(os.environ['FLASHMAP_EXIT'])\n"
                "if os.environ['SELFTEST'] == '1' and 'HAZARD_' not in sys.argv[2]:\n"
                "    code = 0\n"
                "path = pathlib.Path(sys.argv[sys.argv.index('--json') + 1])\n"
                "path.write_text(json.dumps({'segments': [{}] if code == 1 else []}))\n"
                "sys.exit(code)\n"
            )
            probe = stubs / "ffprobe"
            probe.write_text("#!/bin/sh\nprintf '1.0\\n'\n")
            probe.chmod(0o700)
            encoder = stubs / "ffmpeg"
            encoder.write_text(
                f"#!{sys.executable}\n"
                "import os, pathlib, sys\n"
                "path = pathlib.Path(sys.argv[-1])\n"
                "path.write_text('Fixture bytes, not playable media.')\n"
                "if path.name.startswith('HAZARD_') and os.environ['WRITE_FAILURE'] == '1':\n"
                "    (path.parent / 'hazard_check.json').mkdir()\n"
            )
            encoder.chmod(0o700)
            video = root / "fixture.mp4"
            video.write_text("Fixture bytes, not playable media.")
            output = root / "check.json"
            if output_is_directory and not selftest:
                output.mkdir()
            args = ["--selftest"] if selftest else [str(video), "--out", str(output)]
            result = subprocess.run(
                ["bash", str(SCRIPT), *args],
                cwd=root,
                env={
                    "PATH": str(stubs) + os.pathsep + os.defpath,
                    "PY": sys.executable,
                    "PYTHONPATH": str(stubs),
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "FLASHMAP_EXIT": str(flash_exit),
                    "SELFTEST": str(int(selftest)),
                    "WRITE_FAILURE": str(int(output_is_directory)),
                    "TMPDIR": str(root),
                },
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            evidence = json.loads(output.read_text()) if output.is_file() else None
            self.assertEqual(output.is_dir(), output_is_directory and not selftest)
            self.assertEqual(list(root.glob("calm-video-selftest.*")), [])
            return result, evidence

    def test_unwritable_record_cannot_pass(self):
        result, evidence = self.run_gate(output_is_directory=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIsNone(evidence)
        self.assertNotIn("PASS.", result.stdout)
        self.assertIn("UNVERIFIED", result.stderr)

    def test_success_still_requires_a_written_record(self):
        result, evidence = self.run_gate(output_is_directory=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(evidence["verdict"], "pass")
        self.assertEqual(evidence["flashmap_version"], "test-stub")
        self.assertIn("PASS.", result.stdout)

    def test_measured_failure_remains_distinct(self):
        result, evidence = self.run_gate(output_is_directory=False, flash_exit=1)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(evidence["verdict"], "fail")
        self.assertEqual(evidence["flashmap_verdict"], "fail")
        self.assertNotIn("PASS.", result.stdout)

    def test_selftest_refuses_unverified_hazard_record(self):
        result, _ = self.run_gate(output_is_directory=True, flash_exit=1, selftest=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("SELF TEST UNVERIFIED", result.stderr)
        self.assertNotIn("SELF TEST PASSED", result.stdout)

    def test_selftest_accepts_measured_hazard_rejection_and_calm_pass(self):
        result, _ = self.run_gate(output_is_directory=False, flash_exit=1, selftest=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SELF TEST PASSED", result.stdout)

    def test_selftest_still_rejects_a_passed_hazard(self):
        result, _ = self.run_gate(output_is_directory=False, flash_exit=0, selftest=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("SELF TEST PASSED", result.stdout)


if __name__ == "__main__":
    unittest.main()
