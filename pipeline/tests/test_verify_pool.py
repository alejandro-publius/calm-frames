"""Counting the titles by what verify proved about each one.

One number, "21 titles verified", was doing the work of two for weeks: fourteen
of those titles had no flagged segment and had never had a cover measured, and
seven had. These tests are about the counts never collapsing back into one, and
about a title never falling out of every count.

No ffmpeg here. Every title is written by hand, because what is being counted is
what verify left on disk, not what it takes to produce it.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.catalog import (
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_VERIFIED,
    CatalogEntry,
    write_entry,
)
from pipeline.verify import (
    OUTCOME_COVER_NOT_PROVEN,
    OUTCOME_COVER_PROVEN_DRAWN,
    OUTCOME_FAILED,
    OUTCOME_NO_FLAGGED_SEGMENTS,
    VerifyReport,
    outcome_for_entry,
    pool_summary,
)
from pipeline.verify import main as verify_main


def write_title(
    workdir: Path,
    sha: str,
    *,
    status: str,
    checks: list[tuple[str, bool, dict]] | None = None,
    write_report: bool = True,
    notes: dict | None = None,
) -> Path:
    """A title directory with the two files the counter reads."""
    root = workdir / "titles" / sha
    report_path = root / "verify" / "report.json"
    if write_report:
        report = VerifyReport(sha256=sha, source_path="clip.mp4", presets=["wcag"])
        for name, passed, data in checks or []:
            report.add(name, passed, "", **data)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    entry = CatalogEntry(
        sha256=sha,
        title=f"title {sha[:4]}",
        source_name="clip.mp4",
        duration_s=8.0,
        width=640,
        height=360,
        status=status,
        verified=status == STATUS_VERIFIED,
        verify_report=str(report_path),
        notes=dict(notes or {}),
    )
    write_entry(root / "entry.json", entry)
    return root


CALM = [("plan_matches_map:wcag", True, {"stored": 0, "expected": 0})]
COVERED = [
    ("plan_matches_map:wcag", True, {"stored": 2, "expected": 2}),
    ("cover_actually_drawn:wcag", True, {"worst_db": 45.3}),
    ("cover_proof:wcag", True, {"intervals": 2, "proof_ran": True}),
]
# A report from before the cover proof existed: it passed, it had intervals, and
# nothing ever measured the cover. This is the shape the old count hid.
LEGACY_UNPROVEN = [("plan_matches_map:wcag", True, {"stored": 2, "expected": 2})]
BROKEN = [
    ("plan_matches_map:wcag", True, {"stored": 2, "expected": 2}),
    ("cover_actually_drawn:wcag", False, {"worst_db": 8.1}),
]


class TestTheFourCounts:
    def test_each_kind_of_title_lands_in_its_own_count(self, tmp_path):
        write_title(tmp_path, "a" * 64, status=STATUS_VERIFIED, checks=CALM)
        write_title(tmp_path, "b" * 64, status=STATUS_VERIFIED, checks=CALM)
        write_title(tmp_path, "c" * 64, status=STATUS_VERIFIED, checks=COVERED)
        write_title(tmp_path, "d" * 64, status=STATUS_FAILED, checks=BROKEN)

        summary = pool_summary(tmp_path)
        assert summary["analyzed"] == 4
        assert summary["no_flagged_segments"] == 2
        assert summary["cover_proven_drawn"] == 1
        assert summary["failed"] == 1
        assert summary["cover_not_proven"] == 0
        assert summary["adds_up"] is True

    def test_the_parts_add_up_to_the_whole(self, tmp_path):
        write_title(tmp_path, "a" * 64, status=STATUS_VERIFIED, checks=CALM)
        write_title(tmp_path, "b" * 64, status=STATUS_VERIFIED, checks=COVERED)
        write_title(tmp_path, "c" * 64, status=STATUS_FAILED, checks=BROKEN)
        write_title(tmp_path, "d" * 64, status=STATUS_PENDING, write_report=False)
        (tmp_path / "titles" / ("e" * 64)).mkdir(parents=True)

        summary = pool_summary(tmp_path)
        parts = (
            summary["no_flagged_segments"]
            + summary["cover_proven_drawn"]
            + summary["cover_not_proven"]
            + summary["failed"]
        )
        assert parts == summary["analyzed"] == 3
        assert summary["not_analyzed"] == {
            "pending": 1,
            "no_entry_json": 1,
            "no_verdict": 0,
        }
        assert summary["title_directories"] == 5
        assert summary["adds_up"] is True

    def test_a_title_with_no_entry_is_not_counted_as_a_pass(self, tmp_path):
        (tmp_path / "titles" / ("a" * 64)).mkdir(parents=True)
        summary = pool_summary(tmp_path)
        assert summary["analyzed"] == 0
        assert summary["not_analyzed"]["no_entry_json"] == 1
        assert summary["adds_up"] is True

    def test_a_pending_title_is_not_counted_as_a_pass(self, tmp_path):
        write_title(tmp_path, "a" * 64, status=STATUS_PENDING, write_report=False)
        summary = pool_summary(tmp_path)
        assert summary["analyzed"] == 0
        assert summary["not_analyzed"]["pending"] == 1

    def test_an_empty_work_directory_counts_nothing_rather_than_failing(self, tmp_path):
        summary = pool_summary(tmp_path)
        assert summary["analyzed"] == 0
        assert summary["title_directories"] == 0
        assert summary["adds_up"] is True

    def test_the_work_directory_is_recorded_without_the_home_path(self, tmp_path):
        summary = pool_summary(tmp_path)
        assert str(Path.home()) not in summary["work_directory"]


class TestAPassThatProvedNothingIsNotCountedAsOneThatDid:
    """The count is the whole point, so this is the test that matters most.

    Seen to fail first. Replacing the last two lines of `VerifyReport.outcome`
    with a plain `return OUTCOME_COVER_PROVEN_DRAWN`, which is what counting a
    pass as proof looks like in code, gives

        FAILED pipeline/tests/test_verify_pool.py::
        TestAPassThatProvedNothingIsNotCountedAsOneThatDid::
        test_a_legacy_pass_with_no_cover_proof_is_counted_on_its_own
        assert summary["cover_not_proven"] == 1
        E       assert 0 == 1

    and it passes again once the rule is restored.
    """

    def test_a_legacy_pass_with_no_cover_proof_is_counted_on_its_own(self, tmp_path):
        write_title(
            tmp_path, "a" * 64, status=STATUS_VERIFIED, checks=LEGACY_UNPROVEN
        )
        summary = pool_summary(tmp_path)
        assert summary["cover_not_proven"] == 1
        assert summary["cover_proven_drawn"] == 0
        assert summary["no_flagged_segments"] == 0
        assert summary["analyzed"] == 1

    def test_a_calm_title_is_never_counted_as_a_covered_one(self, tmp_path):
        write_title(tmp_path, "a" * 64, status=STATUS_VERIFIED, checks=CALM)
        summary = pool_summary(tmp_path)
        assert summary["cover_proven_drawn"] == 0
        assert summary["no_flagged_segments"] == 1


class TestReadingOneEntry:
    def test_the_report_on_disk_beats_the_label_on_the_entry(self, tmp_path):
        root = write_title(
            tmp_path,
            "a" * 64,
            status=STATUS_VERIFIED,
            checks=LEGACY_UNPROVEN,
            notes={"verify_outcome": OUTCOME_COVER_PROVEN_DRAWN},
        )
        entry = CatalogEntry.from_dict(json.loads((root / "entry.json").read_text()))
        assert outcome_for_entry(entry) == OUTCOME_COVER_NOT_PROVEN

    def test_the_note_stands_in_when_the_report_is_gone(self, tmp_path):
        root = write_title(
            tmp_path,
            "a" * 64,
            status=STATUS_VERIFIED,
            write_report=False,
            notes={"verify_outcome": OUTCOME_NO_FLAGGED_SEGMENTS},
        )
        entry = CatalogEntry.from_dict(json.loads((root / "entry.json").read_text()))
        assert outcome_for_entry(entry) == OUTCOME_NO_FLAGGED_SEGMENTS

    def test_a_verified_title_with_nothing_to_read_has_no_outcome(self, tmp_path):
        root = write_title(
            tmp_path, "a" * 64, status=STATUS_VERIFIED, write_report=False
        )
        entry = CatalogEntry.from_dict(json.loads((root / "entry.json").read_text()))
        assert outcome_for_entry(entry) is None

    def test_a_failed_title_with_nothing_to_read_is_still_a_failure(self, tmp_path):
        root = write_title(
            tmp_path, "a" * 64, status=STATUS_FAILED, write_report=False
        )
        entry = CatalogEntry.from_dict(json.loads((root / "entry.json").read_text()))
        assert outcome_for_entry(entry) == OUTCOME_FAILED


class TestTheCommandLineWritesTheCounts:
    def test_it_writes_the_file_and_exits_zero(self, tmp_path, capsys):
        write_title(tmp_path, "a" * 64, status=STATUS_VERIFIED, checks=CALM)
        write_title(tmp_path, "b" * 64, status=STATUS_VERIFIED, checks=COVERED)
        out = tmp_path / "results" / "verify_pool.json"

        code = verify_main(
            ["--workdir", str(tmp_path), "--pool-summary", str(out)]
        )

        assert code == 0
        written = json.loads(out.read_text())
        assert written["no_flagged_segments"] == 1
        assert written["cover_proven_drawn"] == 1
        assert "no flagged segment" in capsys.readouterr().out

    def test_a_title_without_a_sha_is_still_refused(self, tmp_path, capsys):
        code = verify_main(["--workdir", str(tmp_path)])
        assert code == 2
        assert "--sha is required" in capsys.readouterr().err
