"""Evidence accounting contracts; fabricated rows are never detector measurements."""

import copy
import json
from concurrent.futures import Future

import pytest

from conformance import recheck


def clip(identity="known", order=0, near=True):
    return {"clip_id": identity, "order_index": order, "axis": "synthetic-test",
            "duration_ms": 3000, "crf": 23, "timing": "cfr",
            "near_threshold": near, "truth": {"positive_windows": [1, 2]}}


def row(identity="known", positive=True):
    return {"clip_id": identity, "order_index": 0,
            "flashmap": {"segments": [{"start_ms": 1000, "end_ms": 3000}]
                         if positive else [], "first_pts_ms": 0},
            "fidelity": {"max_abs_deviation": 0, "timestamps_match": True}}


def test_archive_and_full_design_selection_keep_original_rows_and_labels():
    design = {"clips": [clip("later", 1), clip("known", 0)]}
    original = copy.deepcopy(design)
    assert recheck.selected_clips(design, [row()], None) == [design["clips"][1]]
    assert recheck.selected_clips(design, [row()], None, "design") == list(reversed(design["clips"]))
    assert recheck.selected_clips(design, [row()], 1, "design") == [design["clips"][1]]
    assert design == original


@pytest.mark.parametrize("archive", [[row(), row()], [row("unknown")]])
def test_unknown_or_duplicate_archive_identity_is_refused(archive):
    with pytest.raises(ValueError, match="archive clip identities"):
        recheck.selected_clips({"clips": [clip()]}, archive, None)


def test_duplicate_design_identity_is_refused():
    with pytest.raises(ValueError, match="design contains duplicate"):
        recheck.selected_clips({"clips": [clip(), clip()]}, [row()], None)


@pytest.mark.parametrize("limit", [0, -1])
def test_nonpositive_limit_cannot_silently_redefine_the_sample(limit):
    with pytest.raises(ValueError, match="at least one clip"):
        recheck.selected_clips({"clips": [clip()]}, [row()], limit)


@pytest.mark.parametrize("rows", [[], [row(), row()], [row("unknown")]])
def test_summary_requires_every_selected_identity_exactly_once(rows):
    with pytest.raises(ValueError, match="exact selected clip set"):
        recheck.summarize([clip()], rows, [row()])


def test_misses_keep_the_frozen_positive_labels_and_denominators():
    design = [clip()]
    frozen = copy.deepcopy(design)
    summary = recheck.summarize(design, [row(positive=False)], [row()])
    assert summary["all_windows"]["counts"] == {"tp": 0, "fp": 0, "fn": 2, "tn": 1}
    assert summary["near_limits"]["recall"]["denominator"] == 2
    assert summary["missed_clips"][0]["missed_positive_windows"] == [1, 2]
    assert summary["changed_clip_outcomes"][0]["truth_positive_windows"] == [1, 2]
    assert design == frozen


def test_fidelity_exclusions_are_counted_without_turning_misses_into_negatives():
    bad = row("excluded")
    bad["fidelity"]["max_abs_deviation"] = 1
    summary = recheck.summarize([clip(), clip("excluded", 1, False)],
                                [row(positive=False), bad], [row()])
    assert summary["clips_measured"] == 2
    assert summary["clips_kept"] == 1
    assert summary["clips_excluded"] == 1
    assert summary["exclusions"] == {"decoded luminance off the intended waveform": 1}
    assert summary["previously_unmeasured_clips"] == 1
    assert summary["all_windows"]["recall"]["denominator"] == 2


@pytest.fixture
def fake_run(tmp_path, monkeypatch):
    design = tmp_path / "design.json"
    archive = tmp_path / "archive.jsonl"
    output = tmp_path / "new-evidence.json"
    design.write_text(json.dumps({"clips": [clip()]}))
    archive.write_text(json.dumps(row()) + "\n")
    class Executor:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def submit(self, function, selected, baselines):
            future = Future()
            future.set_result(row(selected["clip_id"]))
            return future
        def shutdown(self, **kwargs):
            pass
    monkeypatch.setattr(recheck, "ProcessPoolExecutor", Executor)
    args = ["--design", str(design), "--archive", str(archive), "--out", str(output)]
    return args, output


def test_changed_source_cannot_be_published_as_one_measurement(fake_run, monkeypatch):
    args, output = fake_run
    values = iter([{"detector": "before"}, {"detector": "after"}])
    monkeypatch.setattr(recheck, "source_fingerprint", lambda: next(values))
    refused = False
    try:
        recheck.main(args)
    except RuntimeError as error:
        refused = "changed during the run" in str(error)
    assert refused is True
    assert not output.exists()


def test_cleanup_failure_cannot_be_published_as_success(fake_run, monkeypatch):
    args, output = fake_run
    monkeypatch.setattr(recheck, "sweep_leftovers", lambda: 1)
    refused = False
    try:
        recheck.main(args)
    except RuntimeError as error:
        refused = "hazard cleanup failed" in str(error)
    assert refused is True
    assert not output.exists()


def test_existing_evidence_is_not_overwritten(fake_run):
    args, output = fake_run
    output.write_text("keep this evidence")
    with pytest.raises(SystemExit):
        recheck.main(args)
    assert output.read_text() == "keep this evidence"


def test_source_fingerprint_covers_detector_generator_truth_and_thresholds():
    names = recheck.source_fingerprint()
    for name in ("flashmap/src/flashmap/analyze.py", "flashmap/src/flashmap/decode.py",
                 "eval/conformance/render.py", "eval/conformance/truth.py",
                 "eval/conformance/recheck.py", "flashmap/docs/SPEC_SOURCES.md"):
        assert len(names[name]) == 64


def test_success_keeps_a_durable_provenance_and_measurement_journal(fake_run):
    args, output = fake_run
    assert recheck.main(args) == 0
    journal = output.with_suffix(".journal.jsonl")
    assert journal.exists()
    records = [json.loads(line) for line in journal.read_text().splitlines()]
    result = json.loads(output.read_text())
    assert records[0]["source_sha256"] == result["source_sha256"]
    assert records[0]["design_sha256"] == result["design_sha256"]
    assert records[0]["encoding_protocol"] == result["encoding_protocol"]
    assert records[1:] == result["rows"]
    assert result["journal_sha256"] == recheck.digest(journal)


def test_existing_partial_journal_is_never_reused_or_overwritten(fake_run):
    args, output = fake_run
    journal = output.with_suffix(".journal.jsonl")
    journal.write_text("preserve incomplete evidence")
    with pytest.raises(SystemExit):
        recheck.main(args)
    assert journal.read_text() == "preserve incomplete evidence"
    assert not output.exists()
