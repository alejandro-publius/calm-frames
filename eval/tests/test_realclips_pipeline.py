"""The real clip analysis runs end to end, so that labelling is the only missing step.

The labels in this test are FABRICATED FOR TEST ONLY. They are a fixed pattern invented here to
exercise the arithmetic, they describe nothing about any real segment, they live in a temporary
directory, and nothing they produce is ever written into results/. Nobody on this lane labels a
real segment, and a test fixture is not a label.

What this holds the analysis to:

- it refuses to publish over label files that are not committed, and stamps do_not_publish;
- a window marked unlabelable is an exclusion, not a negative;
- kappa is computed on the two sheets as first given;
- a disagreement between the sheets is held out rather than settled by the script;
- the bootstrap interval over titles comes out wider than the Wilson interval, which is the
  whole reason the plan makes it the headline for this set.

To see it fail on purpose: make the unlabelable branch in report.py count as a negative, and
watch the exclusion test go red. Verified Sep 17, 2026.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parents[1]
POOL = EVAL_DIR / "labeling" / "pool.json"
KEY = EVAL_DIR / "labeling" / "pool_key.json"
REPORT = EVAL_DIR / "realclips" / "report.py"

FABRICATED_FOR_TEST_ONLY = True


def _write_sheet(path: Path, pool: dict, flip_every: int, unlabelable_every: int) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["segment_id", "window_index", "window_start_s", "label", "unlabelable", "notes"],
        )
        writer.writeheader()
        counter = 0
        for segment in pool["segments"]:
            for index in range(int(segment["windows"])):
                counter += 1
                unlabelable = "x" if counter % unlabelable_every == 0 else ""
                label = "" if unlabelable else ("1" if counter % flip_every == 0 else "0")
                writer.writerow(
                    {
                        "segment_id": segment["segment_id"],
                        "window_index": index,
                        "window_start_s": index,
                        "label": label,
                        "unlabelable": unlabelable,
                        "notes": "FABRICATED FOR TEST ONLY",
                    }
                )


@pytest.fixture(scope="module")
def report(tmp_path_factory) -> dict:
    if not POOL.exists() or not KEY.exists():
        pytest.skip("the blinded pool has not been built yet")
    tmp = tmp_path_factory.mktemp("realclips")
    pool = json.loads(POOL.read_text())
    sheet_a = tmp / "labels_test_a.csv"
    sheet_b = tmp / "labels_test_b.csv"
    _write_sheet(sheet_a, pool, flip_every=3, unlabelable_every=17)
    _write_sheet(sheet_b, pool, flip_every=4, unlabelable_every=23)
    out = tmp / "realclips.json"
    finished = subprocess.run(
        [
            sys.executable,
            str(REPORT),
            "--pool-key",
            str(KEY),
            "--labels",
            str(sheet_a),
            "--labels",
            str(sheet_b),
            "--out",
            str(out),
            "--allow-uncommitted",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert finished.returncode == 0, finished.stderr
    return json.loads(out.read_text())


def test_uncommitted_labels_are_marked_not_for_publication(report):
    assert report["do_not_publish"] is True
    assert report["labels_committed"] is False


def test_every_detector_we_have_is_scored_on_the_same_windows(report):
    table = report["any_overlap"]["table"]
    assert "flashmap" in table
    assert "ffmpeg_photosensitivity" in table
    assert "naive_luma_diff" in table
    denominators = {
        name: sum(row["counts"][field] for field in ("tp", "fp", "fn", "tn"))
        for name, row in table.items()
    }
    assert len(set(denominators.values())) == 1, denominators


def test_unlabelable_windows_are_excluded_and_counted(report):
    any_overlap = report["any_overlap"]
    assert any_overlap["exclusions"]["unlabelable"] > 0
    counted = sum(
        any_overlap["table"]["flashmap"]["counts"][field] for field in ("tp", "fp", "fn", "tn")
    )
    assert counted == any_overlap["labelled_windows"]


def test_a_disagreement_is_held_out_rather_than_settled_by_the_script(report):
    assert report["adjudication"]["windows_held_out_for_discussion"] > 0


def test_kappa_is_computed_on_the_two_sheets(report):
    kappa = report["kappa"]
    assert kappa["windows"] > 0
    assert -1.0 <= kappa["kappa"] <= 1.0


def test_the_bootstrap_over_titles_is_wider_than_wilson(report):
    row = report["any_overlap"]["table"]["flashmap"]
    wilson = row["recall_wilson_optimistic"]
    boot = row["recall_bootstrap_over_titles"]
    if boot["lo"] is None or wilson["value"] is None:
        pytest.skip("no positive windows in the fabricated pattern for this detector")
    assert (boot["hi"] - boot["lo"]) > (wilson["wilson_hi"] - wilson["wilson_lo"])


def test_both_window_rules_are_computed_in_the_same_run(report):
    assert report["any_overlap"]["window_rule"] == "any overlap"
    assert "half" in report["half_window"]["window_rule"] or "50" in report["half_window"]["window_rule"]


def test_per_source_counts_are_reported(report):
    per_source = report["any_overlap"]["per_source"]
    assert len(per_source) >= 4
    assert all("segments" in row for row in per_source.values())
