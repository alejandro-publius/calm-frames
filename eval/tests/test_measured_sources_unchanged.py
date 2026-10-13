"""The files the published conformance numbers were measured with are the files in the tree.

results/conformance_current_full_2026-10-02.json records the SHA-256 of every
detector, scorer and spec file behind the complete conformance run, and the
README's recall and precision come from that run. If one of those files
changes, the published numbers describe code that is no longer here, and the
honest move is a new run, not a quiet edit. On Oct 11, 2026 a documentation
edit to flashmap/docs/SPEC_SOURCES.md did exactly that, and nothing noticed.

The one file allowed to differ is named below with its reason. Anything else
that differs fails here; the fix is to revert the edit or re-run the
conformance suite and commit the new record.

Seen to fail on purpose, Oct 11 2026: with one line added to
flashmap/docs/SPEC_SOURCES.md the test named that file, and with the line
removed it passed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RECORD = REPO / "results" / "conformance_current_full_2026-10-02.json"

# Allowed to differ from the record, each with why it cannot move a measured number.
ALLOWED = {
    "flashmap/src/flashmap/report.py": (
        "the self-contained HTML report page, which draws a finished map and is never called "
        "by analysis; its palette changed on Oct 10 (eb20225) and one annotation on Oct 11 "
        "(561ad28)"
    ),
}


def recorded_sources() -> dict[str, str]:
    record = json.loads(RECORD.read_text())
    sources = record["source_sha256"]
    assert isinstance(sources, dict) and sources, "the record lists no source files"
    return sources


def changed_sources(sources: dict[str, str], root: Path) -> list[str]:
    changed = []
    for name, digest in sorted(sources.items()):
        path = root / name
        current = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if current != digest:
            changed.append(name)
    return changed


def test_the_measured_sources_are_the_ones_in_the_tree() -> None:
    changed = [name for name in changed_sources(recorded_sources(), REPO) if name not in ALLOWED]
    assert changed == [], (
        "these files differ from the ones the published conformance numbers were measured "
        "with; revert the change or re-run the suite and commit a new record: " + ", ".join(changed)
    )


def test_every_allowance_is_still_needed() -> None:
    changed = changed_sources(recorded_sources(), REPO)
    stale = [name for name in ALLOWED if name not in changed]
    assert stale == [], f"these allowances no longer match a changed file; remove them: {stale}"


def test_a_changed_file_is_named(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("one\n")
    (tmp_path / "b.py").write_text("two\n")
    sources = {
        "a.py": hashlib.sha256(b"one\n").hexdigest(),
        "b.py": hashlib.sha256(b"not two\n").hexdigest(),
        "gone.py": "0" * 64,
    }
    assert changed_sources(sources, tmp_path) == ["b.py", "gone.py"]
