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


def _write_sheet(
    path: Path,
    pool: dict,
    key: dict,
    flip_every: int,
    unlabelable_every: int,
    all_positive: bool = False,
) -> None:
    """A fabricated sheet whose answers cluster by title, the way real ones do.

    The pattern is arithmetic, it describes no real segment, and it exists to exercise the
    arithmetic downstream. Two properties it has to keep, because tests below depend on them
    and both used to depend on the size of the pool rather than on the pattern:

    - some window is unlabelable on BOTH sheets, so the exclusion path is reached. The two
      strides used to be coprime, so the only shared one was the 391st window; a pool with
      fewer than 391 windows had none and the exclusion test went red for a reason that had
      nothing to do with exclusions. `unlabelable_every` is now the same stride on both sheets
      plus a sheet specific extra, so the shared ones cannot run out;
    - the labels vary by title and not only by position. Windows inside one title are
      correlated in real life, which is the whole reason EVAL_PLAN makes the bootstrap over
      titles the headline for this set. Labels drawn from position alone have no such
      structure, so the bootstrap had nothing to resample and could come out narrower than
      Wilson, which `eval/metrics.py` says outright can happen. Half the titles here are
      mostly positive and half are mostly negative.
    """
    title_of = {row["segment_id"]: row["file"] for row in key["segments"]}
    titles = sorted({row["file"] for row in key["segments"]})
    mostly_positive = {name for index, name in enumerate(titles) if index % 2 == 0}

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["segment_id", "window_index", "window_start_s", "label", "unlabelable", "notes"],
        )
        writer.writeheader()
        counter = 0
        for segment in pool["segments"]:
            title = title_of[segment["segment_id"]]
            for index in range(int(segment["windows"])):
                counter += 1
                if all_positive:
                    # The agreed sheet: every window a positive and nothing unlabelable, so its
                    # effect on the metrics cannot be confused with either labeller's answers.
                    writer.writerow(
                        {
                            "segment_id": segment["segment_id"],
                            "window_index": index,
                            "window_start_s": index,
                            "label": "1",
                            "unlabelable": "",
                            "notes": "FABRICATED FOR TEST ONLY",
                        }
                    )
                    continue
                shared = counter % 11 == 0
                unlabelable = "x" if shared or counter % unlabelable_every == 0 else ""
                if unlabelable:
                    label = ""
                elif title in mostly_positive:
                    label = "0" if counter % flip_every == 0 else "1"
                else:
                    label = "1" if counter % flip_every == 0 else "0"
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


def _run(tmp: Path, arguments: list[str]) -> dict:
    out = tmp / "realclips.json"
    finished = subprocess.run(
        [sys.executable, str(REPORT), "--pool-key", str(KEY), "--out", str(out),
         "--allow-uncommitted", *arguments],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert finished.returncode == 0, finished.stderr
    return json.loads(out.read_text())


@pytest.fixture(scope="module")
def report(tmp_path_factory) -> dict:
    if not POOL.exists() or not KEY.exists():
        pytest.skip("the blinded pool has not been built yet")
    tmp = tmp_path_factory.mktemp("realclips")
    pool = json.loads(POOL.read_text())
    key = json.loads(KEY.read_text())
    sheet_a = tmp / "labels_test_a.csv"
    sheet_b = tmp / "labels_test_b.csv"
    _write_sheet(sheet_a, pool, key, flip_every=3, unlabelable_every=17)
    _write_sheet(sheet_b, pool, key, flip_every=4, unlabelable_every=23)
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
    """And that it is over titles, which the width on its own does not prove.

    Break the width half: draw the fabricated labels from window position alone, with no
    per-title structure, and the bootstrap has nothing to resample. Break the grouping half:
    key `per_title` in report.py by segment id instead of by file, and the group count stops
    matching the titles. Both were seen red on Sep 18, 2026; the width half alone was not, and
    that is why the group count is asserted here as well.
    """
    row = report["any_overlap"]["table"]["flashmap"]
    wilson = row["recall_wilson_optimistic"]
    boot = row["recall_bootstrap_over_titles"]
    if boot["lo"] is None or wilson["value"] is None:
        pytest.skip("no positive windows in the fabricated pattern for this detector")
    assert (boot["hi"] - boot["lo"]) > (wilson["wilson_hi"] - wilson["wilson_lo"])
    assert boot["groups"] == report["titles"], (
        "the bootstrap resampled something other than whole titles: "
        f"{boot['groups']} groups against {report['titles']} titles"
    )


def test_both_window_rules_are_computed_in_the_same_run(report):
    assert report["any_overlap"]["window_rule"] == "any overlap"
    assert "half" in report["half_window"]["window_rule"] or "50" in report["half_window"]["window_rule"]


def test_per_source_counts_are_reported(report):
    per_source = report["any_overlap"]["per_source"]
    assert len(per_source) >= 4
    assert all("segments" in row for row in per_source.values())


def test_the_agreed_sheet_settles_the_metrics_and_kappa_stays_on_the_first_answers(
    tmp_path_factory,
):
    """The third sheet, written after the two labellers talk.

    FABRICATED FOR TEST ONLY, like every other label in this file.

    Two things have to hold at once, and they pull in opposite directions: the agreed answers
    are the ones the metrics use, and kappa is about the answers as first given, so kappa must
    still be between the two original sheets. The trap this covers is real: the script picks its
    primary and second sheets by sorted file name, so a sheet called labels_agreed.csv sorts
    first and would have quietly become one of the two kappa was computed between.

    To see it fail: take the agreed sheet out of the exclusion in main() and let it back into
    `names`, and both halves of this go red.
    """
    if not POOL.exists() or not KEY.exists():
        pytest.skip("the blinded pool has not been built yet")
    tmp = tmp_path_factory.mktemp("adjudicated")
    pool = json.loads(POOL.read_text())
    sheet_a = tmp / "labels_labeller_a.csv"
    sheet_b = tmp / "labels_labeller_b.csv"
    agreed = tmp / "labels_agreed.csv"
    key = json.loads(KEY.read_text())
    _write_sheet(sheet_a, pool, key, flip_every=3, unlabelable_every=17)
    _write_sheet(sheet_b, pool, key, flip_every=4, unlabelable_every=23)
    # The agreed sheet calls every window a positive, which no labeller did, so its effect on
    # the metrics is impossible to confuse with either sheet's own answers.
    _write_sheet(agreed, pool, key, flip_every=1, unlabelable_every=10_000, all_positive=True)

    without = _run(tmp, ["--labels", str(sheet_a), "--labels", str(sheet_b)])
    with_agreed = _run(
        tmp,
        ["--labels", str(sheet_a), "--labels", str(sheet_b), "--adjudicated", str(agreed)],
    )

    assert without["adjudication"]["windows_held_out_for_discussion"] > 0
    assert with_agreed["adjudication"]["windows_held_out_for_discussion"] == 0
    assert with_agreed["adjudication"]["agreed_sheet"] == "labels_agreed.csv"
    assert with_agreed["adjudication"]["windows_the_agreed_sheet_changed"] > 0

    # The agreed sheet said every window is a positive, so the truth it produces has to be
    # bigger than what the two sheets agreed on their own.
    assert (
        with_agreed["any_overlap"]["ground_truth_positive_windows"]
        > without["any_overlap"]["ground_truth_positive_windows"]
    )

    # And kappa has not moved, because it is still between the same two sheets.
    assert with_agreed["kappa_is_between"] == ["labels_labeller_a.csv", "labels_labeller_b.csv"]
    assert with_agreed["kappa"]["kappa"] == without["kappa"]["kappa"]
    assert with_agreed["kappa"]["windows"] == without["kappa"]["windows"]
