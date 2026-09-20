"""The one-version check, and the mixed directory it exists to refuse.

Every guard here has been broken on purpose and seen to go red; the mutations
are named in each docstring.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "eval" / "baseline_versions.py"


def write_report(directory: Path, name: str, version: str, video: str | None = None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(
        json.dumps(
            {
                "baseline": directory.name,
                "tool_version": version,
                "video": video or f"{Path(name).stem}.mp4",
                "segments": [],
            }
        )
    )
    return path


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


EIGHT = "ffmpeg version 8.1.2 Copyright (c) 2000-2026 the FFmpeg developers"
NINE = "ffmpeg version 9.0.1 Copyright (c) 2000-2026 the FFmpeg developers"


def test_one_version_in_a_directory_passes(tmp_path):
    directory = tmp_path / "ffmpeg_photosensitivity"
    write_report(directory, "a.json", NINE)
    write_report(directory, "b.json", NINE)

    result = run(tmp_path)

    assert result.returncode == 0, result.stdout
    assert "ok    ffmpeg_photosensitivity: 2 reports" in result.stdout


def test_two_versions_in_one_directory_fail(tmp_path):
    """The guard, and the exact shape of the accident it is here for.

    Re-running one clip after ffmpeg moved under us leaves the directory
    holding both. Seen to fail by returning 0 unconditionally from main(): the
    assertion on returncode goes red with `assert 0 == 1`.
    """
    directory = tmp_path / "ffmpeg_photosensitivity"
    write_report(directory, "old.json", EIGHT)
    write_report(directory, "new.json", NINE)

    result = run(tmp_path)

    assert result.returncode == 1, result.stdout
    assert "MIXED ffmpeg_photosensitivity" in result.stdout
    assert "old.json" in result.stdout
    assert "new.json" in result.stdout


def test_each_directory_is_judged_on_its_own(tmp_path):
    """Two baselines on two tools is normal. Only a mix inside one is not."""
    write_report(tmp_path / "ffmpeg_photosensitivity", "a.json", NINE)
    write_report(tmp_path / "iris", "a.json", "EA IRIS d96978ac, built here")

    result = run(tmp_path)

    assert result.returncode == 0, result.stdout


def test_a_file_with_no_tool_version_is_not_a_report(tmp_path):
    """`iris_failures.json` belongs to no build and must not count as one.

    Seen to fail by dropping the `if not version: continue` line: the failure
    reads `assert 1 == 0` on the return code, because the missing version
    becomes a second value in the set.
    """
    directory = tmp_path / "iris"
    write_report(directory, "a.json", "EA IRIS d96978ac, built here")
    (directory / "iris_failures.json").write_text(json.dumps({"failed": 6}))

    result = run(tmp_path)

    assert result.returncode == 0, result.stdout
    assert "1 reports" in result.stdout


def test_a_results_tree_that_does_not_exist_is_not_a_failure(tmp_path):
    result = run(tmp_path / "nothing_here")

    assert result.returncode == 0
    assert "nothing to check" in result.stdout


def test_unreadable_json_stops_the_check_rather_than_being_skipped(tmp_path):
    """A report that cannot be parsed is not a report that passed.

    Seen to fail by catching the error and continuing: the return code comes
    back 0 and this goes red.
    """
    directory = tmp_path / "ffmpeg_photosensitivity"
    directory.mkdir(parents=True)
    (directory / "broken.json").write_text("{not json")

    result = run(tmp_path)

    assert result.returncode != 0
    assert "cannot be read as JSON" in result.stderr + result.stdout


def test_the_real_results_tree_holds_one_version_per_baseline():
    """The check, run over what is actually committed.

    This is the row that turns the script into a gate rather than a tool. If it
    is red, a baseline directory holds two tool versions right now.
    """
    root = REPO / "results" / "baselines"
    if not root.is_dir():
        pytest.skip("no baseline results in this checkout")

    result = run(root)

    assert result.returncode == 0, result.stdout
