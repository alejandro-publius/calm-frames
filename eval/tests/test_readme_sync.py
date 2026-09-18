"""The drift checker is the guard every published number rests on, so guard it.

eval/readme_sync.py is what makes the rule in CLAUDE.md real: a number in the
README, the Devpost text or the video comes from results/ and CI fails if the
document drifts away from it. Until these tests existed, that script had no test
of its own, and it had a hole: its pattern ended the dotted path at the first
space, so every marker pointing at a JSON key with a space in its name matched
nothing and was skipped in silence. Fifteen of them were live in the README. All
fifteen happened to be right, which is the bad case, not the good one: the guard
would not have said a word if they had gone wrong.

So there are two things to hold here, and both are tested:

1. the pattern reads a dotted path that contains spaces, and
2. anything shaped like a marker that the pattern cannot read is reported as a
   problem rather than walked past.

Seen to fail on purpose, Sep 17 2026, four ways: putting the old `[^\\s]+` path
pattern back, deleting the unparseable-marker loop, making --check return 0 when
problems exist, and making resolve() return the first key it finds. Each one
turned at least one of these red.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "eval" / "readme_sync.py"

spec = importlib.util.spec_from_file_location("readme_sync", SCRIPT)
assert spec and spec.loader
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def run(tmp_path, monkeypatch, argv: list[str]) -> int:
    """Run main() against a throwaway repository root."""
    monkeypatch.setattr(sync, "REPO", tmp_path)
    monkeypatch.setattr("sys.argv", ["readme_sync.py", *argv])
    return sync.main()


def make_repo(tmp_path, markdown: str, data: dict) -> Path:
    (tmp_path / "results").mkdir(parents=True, exist_ok=True)
    (tmp_path / "results" / "r.json").write_text(json.dumps(data), encoding="utf-8")
    doc = tmp_path / "DOC.md"
    doc.write_text(markdown, encoding="utf-8")
    return doc


# ---------------------------------------------------------------- the pattern


def test_the_pattern_reads_a_path_with_no_spaces():
    text = "<!--n results/r.json:a.b -->7<!--/n-->"
    match = sync.MARKER.search(text)
    assert match is not None
    assert match.group("source") == "results/r.json"
    assert match.group("path") == "a.b"
    assert match.group("value") == "7"


def test_the_pattern_reads_a_path_with_spaces_in_a_key():
    # This is the case that used to match nothing at all.
    text = "<!--n results/r.json:per_source.NASA SVS 5011.files -->1<!--/n-->"
    match = sync.MARKER.search(text)
    assert match is not None
    assert match.group("path") == "per_source.NASA SVS 5011.files"
    assert match.group("value") == "1"


def test_the_pattern_does_not_run_past_the_end_of_a_line():
    # A path is on one line. Without that, a broken marker would swallow the
    # rest of the document looking for a closing arrow.
    text = "<!--n results/r.json:a\nb -->7<!--/n-->"
    assert sync.MARKER.search(text) is None


def test_two_markers_on_one_line_stay_separate():
    text = "from <!--n results/r.json:a -->1<!--/n--> to <!--n results/r.json:b -->2<!--/n-->"
    found = sync.MARKER.findall(text)
    assert len(found) == 2
    assert [f[1] for f in found] == ["a", "b"]


# --------------------------------------------------------- reading the values


def test_resolve_walks_objects_and_lists():
    data = {"a": {"b c": [10, 20]}}
    assert sync.resolve(data, "a.b c.1") == 20


def test_resolve_raises_on_a_key_that_is_not_there():
    with pytest.raises(KeyError):
        sync.resolve({"a": 1}, "a.b")


def test_render_keeps_a_float_readable():
    assert sync.render(488.4) == "488.4"
    assert sync.render(5219.0) == "5219"
    assert sync.render(True) == "yes"


# ------------------------------------------------------------- end to end


def test_check_passes_when_every_number_agrees(tmp_path, monkeypatch, capsys):
    make_repo(
        tmp_path,
        "a <!--n results/r.json:x -->5<!--/n--> and "
        "<!--n results/r.json:per_source.NASA SVS 5011.files -->1<!--/n-->\n",
        {"x": 5, "per_source": {"NASA SVS 5011": {"files": 1}}},
    )
    assert run(tmp_path, monkeypatch, ["--check", "DOC.md"]) == 0
    assert "2 published number(s) match" in capsys.readouterr().out


def test_check_fails_when_a_spaced_key_drifts(tmp_path, monkeypatch, capsys):
    # The whole point of the fix. Before it, this marker was invisible and this
    # document passed.
    make_repo(
        tmp_path,
        "<!--n results/r.json:per_source.NASA SVS 5011.files -->999<!--/n-->\n",
        {"per_source": {"NASA SVS 5011": {"files": 1}}},
    )
    assert run(tmp_path, monkeypatch, ["--check", "DOC.md"]) == 1
    assert "says '1', the document says '999'" in capsys.readouterr().err


def test_a_marker_it_cannot_parse_is_a_problem_not_a_shrug(tmp_path, monkeypatch, capsys):
    # No colon, so there is no path. The old script said nothing about this.
    make_repo(
        tmp_path,
        "<!--n results/r.json -->0.65<!--/n-->\n",
        {"x": 1},
    )
    assert run(tmp_path, monkeypatch, ["--check", "DOC.md"]) == 1
    assert "cannot parse the marker" in capsys.readouterr().err


def test_a_marker_with_no_closing_tag_is_a_problem(tmp_path, monkeypatch, capsys):
    make_repo(tmp_path, "<!--n results/r.json:x -->5\n", {"x": 5})
    assert run(tmp_path, monkeypatch, ["--check", "DOC.md"]) == 1
    assert "cannot parse the marker" in capsys.readouterr().err


def test_a_missing_source_file_is_a_problem(tmp_path, monkeypatch, capsys):
    make_repo(tmp_path, "<!--n results/gone.json:x -->5<!--/n-->\n", {"x": 5})
    assert run(tmp_path, monkeypatch, ["--check", "DOC.md"]) == 1
    assert "does not exist" in capsys.readouterr().err


def test_a_missing_key_is_a_problem(tmp_path, monkeypatch, capsys):
    make_repo(tmp_path, "<!--n results/r.json:nope -->5<!--/n-->\n", {"x": 5})
    assert run(tmp_path, monkeypatch, ["--check", "DOC.md"]) == 1
    assert "has no key nope" in capsys.readouterr().err


def test_without_check_it_rewrites_the_number(tmp_path, monkeypatch):
    doc = make_repo(
        tmp_path,
        "<!--n results/r.json:per_source.NASA SVS 5011.files -->999<!--/n-->\n",
        {"per_source": {"NASA SVS 5011": {"files": 1}}},
    )
    assert run(tmp_path, monkeypatch, ["DOC.md"]) == 0
    assert doc.read_text(encoding="utf-8").strip() == (
        "<!--n results/r.json:per_source.NASA SVS 5011.files -->1<!--/n-->"
    )


def test_the_real_repository_has_no_unparseable_markers():
    """Every marker committed in this repository is one the checker reads.

    This is the regression guard for the fifteen. If someone writes a marker in a
    shape the pattern cannot read, this goes red without waiting for the number
    inside it to drift.
    """
    unparseable: list[str] = []
    for path in sorted(REPO.glob("**/*.md")):
        if any(
            part in {".venv", "node_modules", "build", ".git", ".pytest_cache"}
            for part in path.parts
        ):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        whole = [match.group(0) for match in sync.MARKER.finditer(text)]
        for opening in sync.ANY_MARKER_OPENING.finditer(text):
            if not any(opening.group(0) in one for one in whole):
                unparseable.append(f"{path.relative_to(REPO)}: {opening.group(0)}")
    assert unparseable == []
