"""A demo gate cannot pass when its verification record could not be written.

Uses a fake flashmap module and ffprobe command, with no media decoding,
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
    def run_gate(self, *, output_is_directory: bool, flash_exit: int = 0):
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
                "path = pathlib.Path(sys.argv[sys.argv.index('--json') + 1])\n"
                "path.write_text(json.dumps({'segments': [{}] if code == 1 else []}))\n"
                "sys.exit(code)\n"
            )
            probe = stubs / "ffprobe"
            probe.write_text("#!/bin/sh\nprintf '1.0\\n'\n")
            probe.chmod(0o700)
            video = root / "fixture.mp4"
            video.write_text("Fixture bytes, not playable media.")
            output = root / "check.json"
            if output_is_directory:
                output.mkdir()
            result = subprocess.run(
                ["bash", str(SCRIPT), str(video), "--out", str(output)],
                cwd=root,
                env={
                    "PATH": str(stubs) + os.pathsep + os.defpath,
                    "PY": sys.executable,
                    "PYTHONPATH": str(stubs),
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "FLASHMAP_EXIT": str(flash_exit),
                },
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            evidence = json.loads(output.read_text()) if output.is_file() else None
            self.assertEqual(output.is_dir(), output_is_directory)
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


if __name__ == "__main__":
    unittest.main()
