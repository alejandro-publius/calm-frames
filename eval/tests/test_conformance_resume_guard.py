"""Protocol checks never generate video or modify archived measurements."""

import json
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

import conformance_resume_guard as guard

MAKEFILE = guard.REPO / "eval/reproduce.mk"


def test_missing_empty_and_current_protocol_archives_can_resume(tmp_path):
    archive = tmp_path / "raw.jsonl"
    assert guard.check_archive(archive) == 0
    archive.write_text("\n")
    assert guard.check_archive(archive) == 0
    row = {"encode": {"protocol": guard.ENCODING_PROTOCOL}}
    archive.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
    before = archive.read_bytes()
    assert guard.check_archive(archive) == 2
    assert archive.read_bytes() == before


@pytest.mark.parametrize("bad", [{}, {"encode": {}}, {"encode": None},
                                  {"encode": {"protocol": "old"}}, [], None])
def test_one_unidentified_or_different_row_blocks_the_entire_resume(tmp_path, bad):
    archive = tmp_path / "raw.jsonl"
    archive.write_text(json.dumps({"encode": {"protocol": guard.ENCODING_PROTOCOL}})
                       + "\n" + json.dumps(bad) + "\n")
    before = archive.read_bytes()
    with pytest.raises(ValueError, match="row 2.*protocol"):
        guard.check_archive(archive)
    assert archive.read_bytes() == before


def test_invalid_archive_is_preserved_and_cli_refuses(tmp_path, capsys):
    archive = tmp_path / "raw.jsonl"
    archive.write_text("truncated evidence{")
    assert guard.main(["--archive", str(archive)]) == 2
    assert "Preserve the archive" in capsys.readouterr().err
    assert archive.read_text() == "truncated evidence{"


@pytest.mark.parametrize("target", ["conformance", "conformance-full"])
def test_make_refuses_before_it_can_start_the_generator(tmp_path, target):
    # Every Python command is intercepted. Even a broken Makefile can only
    # leave a marker; it cannot invoke a real generator or produce a clip.
    archive = tmp_path / "legacy.jsonl"
    archive.write_text(json.dumps({"clip_id": "old", "encode": {}}) + "\n")
    marker = tmp_path / "generator-would-start"
    dispatch = tmp_path / "intercept.py"
    dispatch.write_text(
        "from pathlib import Path\nimport subprocess, sys\n"
        "name = Path(sys.argv[1]).name\n"
        "if name == 'conformance_resume_guard.py':\n"
        f" result = subprocess.run([sys.executable, {str(guard.REPO / 'eval/conformance_resume_guard.py')!r}, '--archive', {str(archive)!r}])\n"
        " raise SystemExit(result.returncode)\n"
        "if name == 'generate_analyze.py':\n"
        f" Path({str(marker)!r}).write_text('intercepted; no video generated')\n"
        " raise SystemExit(90)\n"
        "raise SystemExit(91)\n"
    )
    result = subprocess.run(
        ["make", "--no-print-directory", "-f", str(MAKEFILE), target,
         f"PY={shlex.quote(sys.executable)} {shlex.quote(str(dispatch))}",
         f"EVAL_DIR={guard.REPO / 'eval'}", f"EVAL_REPO_DIR={guard.REPO}"],
        cwd=guard.REPO, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert not marker.exists(), "Make reached the generator despite the incompatible archive"
    assert "Refusing conformance resumption" in result.stderr
    assert json.loads(archive.read_text())["clip_id"] == "old"
