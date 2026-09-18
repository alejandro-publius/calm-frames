"""The integration diff counter has to notice when the diff changes.

The README publishes four numbers about the size of the flash guard integration:
lines added, lines replaced, files touched, and how many of the added lines land
in the busiest file. They come from results/integration_diff.json, which
eval/integration_diff_stats.py counts out of the patch committed in
docs/INTEGRATION_DIFF.md, and CI runs that script with --check.

A counter that quietly agreed with a stale file would be worse than no counter,
so these tests feed it patches and check the numbers, and one of them takes the
real document and changes a single line to watch --check go red.

Seen to fail on purpose, Sep 17 2026, three ways: returning a fixed
lines_added, comparing only lines_added in --check instead of the whole record,
and dropping the diff_sha256 field. All three turned these tests red.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "eval" / "integration_diff_stats.py"

spec = importlib.util.spec_from_file_location("integration_diff_stats", SCRIPT)
assert spec and spec.loader
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


TINY = """# heading

```diff
diff --git src/a.tsx src/a.tsx
@@ -1,2 +1,3 @@
 keep
-gone
+one
+two
diff --git src/b.tsx src/b.tsx
@@ -1,1 +1,2 @@
 keep
+three
```
"""


def test_it_counts_a_small_patch():
    got = stats.measure(TINY)
    assert got["lines_added"] == 3
    assert got["lines_replaced"] == 1
    assert got["files_touched"] == 2
    assert got["busiest_file"] == "src/a.tsx"
    assert got["busiest_file_lines_added"] == 2
    assert got["other_files_lines_added_each"] == [1]


def test_the_file_headers_are_not_counted_as_changed_lines():
    # "+++ b/x" and "--- a/x" start with + and - and are not changes.
    text = TINY.replace(
        "diff --git src/b.tsx src/b.tsx",
        "diff --git src/b.tsx src/b.tsx\n--- src/b.tsx\n+++ src/b.tsx",
    )
    got = stats.measure(text)
    assert got["lines_added"] == 3
    assert got["lines_replaced"] == 1


def test_changing_one_line_changes_the_hash():
    before = stats.measure(TINY)
    after = stats.measure(TINY.replace("+two", "+deux"))
    assert before["diff_sha256"] != after["diff_sha256"]
    assert before["lines_added"] == after["lines_added"]


def test_a_document_with_no_diff_block_is_an_error():
    with pytest.raises(SystemExit):
        stats.measure("# heading\n\nno patch here\n")


def test_a_document_with_two_diff_blocks_is_an_error():
    with pytest.raises(SystemExit):
        stats.measure(TINY + "\n" + TINY)


def test_the_committed_file_matches_the_committed_document():
    assert stats.main(["--check"]) == 0


def test_check_goes_red_when_the_document_loses_a_line(tmp_path, monkeypatch):
    doc = REPO / "docs" / "INTEGRATION_DIFF.md"
    out = REPO / "results" / "integration_diff.json"

    edited = tmp_path / "INTEGRATION_DIFF.md"
    original = doc.read_text(encoding="utf-8")
    broken = original.replace("+  requestSeek,\n", "", 1)
    assert broken != original, "the line this test removes is no longer in the document"
    edited.write_text(broken, encoding="utf-8")

    # Point the module at the edited copy and the real, unchanged results file.
    monkeypatch.setattr(stats, "DOC", edited)
    monkeypatch.setattr(stats, "OUT", out)
    assert stats.main(["--check"]) == 1


def test_check_goes_red_when_a_line_changes_but_the_counts_do_not(tmp_path, monkeypatch):
    # The dangerous edit is the one that leaves every count alone: someone
    # rewrites a line of the patch and the README's numbers still "match".
    # Only the hash catches that, so --check has to compare the whole record.
    doc = REPO / "docs" / "INTEGRATION_DIFF.md"
    out = REPO / "results" / "integration_diff.json"

    original = doc.read_text(encoding="utf-8")
    reworded = original.replace("+  requestSeek,\n", "+  requestSeekX,\n", 1)
    assert reworded != original, "the line this test rewrites is no longer in the document"

    edited = tmp_path / "INTEGRATION_DIFF.md"
    edited.write_text(reworded, encoding="utf-8")

    monkeypatch.setattr(stats, "DOC", edited)
    monkeypatch.setattr(stats, "OUT", out)

    # The counts are untouched on purpose. Only the content moved.
    measured = stats.measure(reworded)
    committed = json.loads(out.read_text(encoding="utf-8"))
    assert measured["lines_added"] == committed["lines_added"]
    assert measured["lines_replaced"] == committed["lines_replaced"]
    assert measured["files_touched"] == committed["files_touched"]
    assert measured["per_file"] == committed["per_file"]

    assert stats.main(["--check"]) == 1


def test_writing_then_checking_agrees(tmp_path, monkeypatch):
    edited = tmp_path / "doc.md"
    edited.write_text(TINY, encoding="utf-8")
    written = tmp_path / "out.json"
    monkeypatch.setattr(stats, "DOC", edited)
    monkeypatch.setattr(stats, "OUT", written)

    assert stats.main([]) == 0
    assert stats.main(["--check"]) == 0
    assert json.loads(written.read_text(encoding="utf-8"))["files_touched"] == 2
