"""The per source positives table says which rule fired, and says so from the data.

Every screening row in this file is FABRICATED FOR TEST ONLY. The numbers are invented here to
exercise the arithmetic, they describe no real clip, and nothing they produce is written into
results/. The one test that reads the real results/screening.json only checks it for drift; it
never changes it.

What this holds the table to:

- a red segment in the rows turns the red counts on, so "no segment fired the red rule" is
  read off the data and never asserted;
- while there is no red segment, every red clip on the shooting list stays marked still needed;
- overlapping segments are counted once in flagged seconds, so a file with heavy overlap does
  not read as flashing for three times its own length;
- a title that failed to decode is counted as a failure, not as a clean title with no flashing;
- --check fails on a hand-edited count, which is what keeps the committed file honest.

To see them fail on purpose: see the notes on each test. All five were verified on
Sep 17, 2026.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parents[1]
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

import screening_table  # noqa: E402

REPO = EVAL_DIR.parent
SCRIPT = EVAL_DIR / "screening_table.py"

FABRICATED_FOR_TEST_ONLY = True

# Two fabricated sources. "Invented source A" has one title that flashes on the general rule
# with two overlapping segments, and one title that failed to decode. "Invented source B" has a
# title with one red segment, so the red path is exercised without any real red footage.
FABRICATED_PER_FILE = [
    {
        "file": "HAZARD_invented_a.mp4",
        "source": "Invented source A",
        "flagged_segments": 2,
        "frame_count": 100,
        "variable_frame_rate": False,
        "segments": [
            {
                "start_s": 1.0,
                "end_s": 3.0,
                "reason": "general",
                "area_fraction": 0.5,
                "triggered_by": ["wcag-10deg"],
                "breaks_baseline": True,
                "max_flashes_in_window": 7,
            },
            {
                "start_s": 2.0,
                "end_s": 4.0,
                "reason": "general",
                "area_fraction": 0.4,
                "triggered_by": ["wcag-10deg"],
                "breaks_baseline": True,
                "max_flashes_in_window": 5,
            },
        ],
    },
    {
        "file": "HAZARD_invented_broken.ogv",
        "source": "Invented source A",
        "error": "fabricated decode failure, for test only",
    },
    {
        "file": "HAZARD_invented_b.webm",
        "source": "Invented source B",
        "flagged_segments": 0,
        "frame_count": 50,
        "variable_frame_rate": False,
        "segments": [],
    },
]

FABRICATED_RED_SEGMENT = {
    "file": "HAZARD_invented_red.mp4",
    "source": "Invented source B",
    "flagged_segments": 1,
    "frame_count": 60,
    "variable_frame_rate": False,
    "segments": [
        {
            "start_s": 0.5,
            "end_s": 2.5,
            "reason": "red",
            "area_fraction": 0.9,
            "triggered_by": ["wcag-10deg"],
            "breaks_baseline": True,
            "max_flashes_in_window": 9,
        }
    ],
}


def fabricated_report(with_red: bool = False) -> dict:
    rows = list(FABRICATED_PER_FILE)
    if with_red:
        rows = rows + [FABRICATED_RED_SEGMENT]
    return {
        "generated_on": "2026-09-17",
        "profile": "wcag",
        "note": "FABRICATED FOR TEST ONLY",
        "per_file": rows,
        "totals": {"clips": len(rows)},
    }


def test_a_red_segment_turns_the_red_counts_on():
    """Break it: hardcode red_rule_segments to 0 in enrich() and this goes red."""
    without = screening_table.enrich(fabricated_report(with_red=False))
    assert without["totals"]["red_rule_segments"] == 0
    assert without["totals"]["red_rule_statement"] == "no segment in this pool fired the red flash rule"

    with_red = screening_table.enrich(fabricated_report(with_red=True))
    assert with_red["totals"]["red_rule_segments"] == 1
    assert with_red["totals"]["sources_with_a_red_segment"] == 1
    assert "red" in with_red["per_source"]["Invented source B"]["segments_by_rule"]
    assert with_red["per_source"]["Invented source B"]["titles_with_a_red_segment"] == [
        "HAZARD_invented_red.mp4"
    ]
    assert with_red["totals"]["red_rule_statement"] != without["totals"]["red_rule_statement"]


def test_the_red_shooting_list_clears_itself_once_red_footage_exists():
    """Break it: set still_needed to True unconditionally and this goes red."""
    without = screening_table.enrich(fabricated_report(with_red=False))
    red_clips = [c for c in without["self_filmed_needed"]["clips"] if c["gap"].startswith("red")]
    assert red_clips, "the shooting list has no red clips on it"
    assert all(clip["still_needed"] for clip in red_clips)

    with_red = screening_table.enrich(fabricated_report(with_red=True))
    red_clips = [c for c in with_red["self_filmed_needed"]["clips"] if c["gap"].startswith("red")]
    assert not any(clip["still_needed"] for clip in red_clips)


def test_overlapping_segments_are_counted_once():
    """Break it: sum the segment lengths instead of merging them, and this goes red."""
    report = screening_table.enrich(fabricated_report())
    # 1.0 to 3.0 and 2.0 to 4.0 overlap, so the flagged time is 3 s, not 4 s.
    assert report["per_source"]["Invented source A"]["flagged_seconds"] == 3.0


def test_a_decode_failure_is_counted_as_a_failure_not_as_a_clean_title():
    """Break it: drop the error branch so a failed clip falls through, and this goes red."""
    report = screening_table.enrich(fabricated_report())
    row = report["per_source"]["Invented source A"]
    assert row["files_failed_to_decode"] == 1
    assert row["files"] == 1, "a title that never decoded must not count as analysed"
    assert row["flagged_files"] == 1


def test_check_fails_on_a_hand_edited_count(tmp_path):
    """Break it: make check() return an empty list, and this goes red."""
    path = tmp_path / "screening.json"
    report = screening_table.enrich(fabricated_report())
    path.write_text(json.dumps(report, indent=2) + "\n")

    clean = subprocess.run(
        [sys.executable, str(SCRIPT), "--file", str(path), "--check"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert clean.returncode == 0, clean.stderr

    report["per_source"]["Invented source A"]["flagged_segments"] = 99
    path.write_text(json.dumps(report, indent=2) + "\n")
    drifted = subprocess.run(
        [sys.executable, str(SCRIPT), "--file", str(path), "--check"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert drifted.returncode == 2
    assert "drifted" in drifted.stderr


def test_the_committed_screening_file_carries_a_current_table():
    """The real file, checked for drift only. Nothing here writes to it."""
    path = REPO / "results" / "screening.json"
    if not path.is_file():
        pytest.skip("results/screening.json has not been written yet")
    report = json.loads(path.read_text())
    assert screening_table.check(report) == []
