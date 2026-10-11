"""Exercise the upload gate against actual benign encoded boundary durations."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("duration,allowed", [(179.5, True), (180, False), (180.5, False)])
def test_final_video_is_strictly_under_three_minutes(tmp_path, duration, allowed):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg and ffprobe are required")
    video = tmp_path / "benign-static.mp4"
    result = tmp_path / "check.json"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "color=c=0x18232b:s=32x32:r=2", "-t", str(duration),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)], check=True)
    # The script picks the repository's .venv when there is one and falls back
    # to whatever python3 is on PATH, which in a fresh clone has no flashmap.
    # Name the interpreter running this test, which does.
    run = subprocess.run(["bash", str(REPO / "eval/check_video.sh"), str(video),
                          "--out", str(result)], cwd=REPO, capture_output=True, text=True,
                         env={**os.environ, "PY": sys.executable})
    evidence = json.loads(result.read_text())
    assert evidence["duration_s"] == duration
    assert evidence["duration_verdict"] == ("pass" if allowed else "fail")
    assert run.returncode == (0 if allowed else 1), run.stdout + run.stderr
