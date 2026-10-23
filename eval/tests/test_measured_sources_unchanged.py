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
    "flashmap/src/flashmap/decode.py": (
        "one check after the last frame (Oct 22, eff3ca4) refuses a file that decodes fewer "
        "frames than it declares. It changes no decoded frame, so it can only turn a short "
        "decode into an error, and test_no_measured_clip_decoded_short shows that none of the "
        "measured clips decoded short"
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


def short_decodes(rows: list[dict]) -> list[str]:
    """Rows the decode completeness check would have refused: an error, or fewer frames read than written."""
    return [
        row["clip_id"]
        for row in rows
        if "error" in row or row["flashmap"]["frame_count"] < row["encode"]["frames_written"]
    ]


def test_no_measured_clip_decoded_short() -> None:
    """Why decode.py may differ from the record.

    The completeness check added on Oct 22 raises only when a file decodes fewer
    frames than it declares, and every clip behind the published numbers decoded
    every frame its encoder wrote. So the current decode.py reads the same frames
    from each of those clips and reaches the same rows.
    """
    rows = json.loads(RECORD.read_text())["rows"]
    assert len(rows) == 3000
    assert short_decodes(rows) == []


def test_a_short_decode_is_named() -> None:
    """Seen to fail on purpose, Oct 23 2026: with the comparison loosened to <= this named the
    clean row as well, and test_no_measured_clip_decoded_short named every measured row."""
    rows = [
        {"clip_id": "clean", "flashmap": {"frame_count": 90}, "encode": {"frames_written": 90}},
        {"clip_id": "short", "flashmap": {"frame_count": 60}, "encode": {"frames_written": 90}},
        {"clip_id": "failed", "error": "decode", "encode": {"frames_written": 90}},
        {"clip_id": "extra", "flashmap": {"frame_count": 91}, "encode": {"frames_written": 90}},
    ]
    assert short_decodes(rows) == ["short", "failed"]


def test_a_changed_file_is_named(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("one\n")
    (tmp_path / "b.py").write_text("two\n")
    sources = {
        "a.py": hashlib.sha256(b"one\n").hexdigest(),
        "b.py": hashlib.sha256(b"not two\n").hexdigest(),
        "gone.py": "0" * 64,
    }
    assert changed_sources(sources, tmp_path) == ["b.py", "gone.py"]
