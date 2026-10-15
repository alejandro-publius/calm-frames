"""The evidence summary keeps its four states apart and refuses a collapsed or overclaiming one."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from pipeline import evidence_summary as ev


def _map(path: Path, *, profile: str, segments: list[dict], room: dict | None = None, signed: bool = False) -> Path:
    doc = {
        "schema": "x", "version": 1, "generator": {"name": "flashmap", "version": "test"}, "created_utc": "2026-10-15T00:00:00Z",
        "source": {"path": "clip.mp4", "sha256": "a" * 64, "size_bytes": 10, "coded_width": 16, "coded_height": 9,
                   "container_frame_rate": "25/1", "duration_ms": 1000.0, "frame_count": 25, "first_pts_ms": 0.0,
                   "last_pts_ms": 960.0, "variable_frame_rate": False, "frame_interval_ms": {"min": 40.0, "max": 40.0, "median": 40.0},
                   "timestamp_source": "container-pts"},
        "picture": {"measured_on": "picture"},
        "color": {"analysis_width": 16, "analysis_height": 9, "luminance_model": "wcag-relative-luminance-srgb", "matrix": "bt709"},
        "profile": {"name": profile, "flash_limit_per_second": 3, "window_ms": 1000, "area_fraction_limit": 0.25,
                    "area_windows": [{"name": "wcag-10deg", "width_px": 5, "height_px": 3}], "room": room},
        "summary": {"pass": not segments, "flash_pass": not segments, "pattern_pass": True, "segment_count": len(segments),
                    "general_segment_count": len(segments), "red_segment_count": 0, "pattern_segment_count": 0,
                    "hidden_ms": sum(s["end_ms"] - s["start_ms"] for s in segments), "pattern_rule_applied": False},
        "segments": segments,
        "signature": {"alg": "ed25519"} if signed else None,
    }
    path.write_text(json.dumps(doc))
    return path


def _ledger(path: Path, filename: str) -> Path:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "source_page_url", "license", "credit_line", "sha256", "duration_s", "resolution", "license_checked_on", "notes"])
        writer.writerow([filename, "https://example.invalid/asset", "Public domain", "Example credit", "a" * 64, "1.0", "16x9", "2026-10-15", "test"])
    return path


SEGMENT = {"reason": "general", "start_ms": 100, "end_ms": 1100, "flash_first_ms": 100, "flash_last_ms": 1100,
           "max_flashes_in_window": 4, "area_fraction": 0.5, "area_window": "wcag-10deg", "triggered_by": ["wcag-10deg"], "breaks_baseline": True}


def test_actual_findings_are_listed_per_profile_with_their_room_and_simulated_events_stay_separate(tmp_path: Path):
    ledger = _ledger(tmp_path / "LICENSES.csv", "HAZARD_clip.mp4")
    wcag = _map(tmp_path / "clip.wcag.json", profile="wcag", segments=[SEGMENT])
    broadcast = _map(tmp_path / "clip.broadcast.json", profile="broadcast", segments=[], room={"tv_diagonal_in": 85, "seat_distance_in": 48, "display_aspect": "16:9"})
    simulated = [{"kind": "practice hold", "start_ms": 5000, "end_ms": 9000, "detected": False}]
    summary = ev.build_summary(repo=tmp_path, ledger=ledger, ledger_file="HAZARD_clip.mp4", maps=[wcag, broadcast],
                               receipt=None, manifest=None, plots=[], negative_controls=None, test_file=None,
                               simulated=simulated, not_analyzed=["audio"], report=None, extra_limitations=[])
    assert ev.validate(summary) == []
    assert summary["findings"]["actual_count"] == 1
    [finding] = summary["findings"]["actual"]
    assert finding["profile"] == "wcag" and finding["room"] is None and finding["start_ms"] == 100
    assert summary["findings"]["simulated"] == simulated
    assert summary["findings"]["independent_validation"] == "pending"
    assert summary["analysis"]["runs"][1]["settings"]["room"]["tv_diagonal_in"] == 85
    assert summary["source"]["hazard_prefix"] is True
    assert summary["preparation"]["status"] == "not run"
    assert set(summary["states"]) == {"actual_findings", "simulated_events", "unsupported_or_not_analyzed", "independent_validation_pending"}


def test_zero_findings_say_zero_rather_than_safe(tmp_path: Path):
    ledger = _ledger(tmp_path / "LICENSES.csv", "clip.mp4")
    clean = _map(tmp_path / "clip.wcag.json", profile="wcag", segments=[])
    summary = ev.build_summary(repo=tmp_path, ledger=ledger, ledger_file="clip.mp4", maps=[clean], receipt=None, manifest=None,
                               plots=[], negative_controls=None, test_file=None, simulated=[], not_analyzed=[], report=None, extra_limitations=[])
    assert ev.validate(summary) == []
    assert summary["findings"]["actual"] == [] and summary["findings"]["actual_count"] == 0
    text = json.dumps(summary).lower()
    assert "safe" not in text.replace("safe_master", "").replace("unsafe", "")
    assert "not a medical device" in text


@pytest.mark.parametrize("mutate, problem", [
    (lambda s: s["findings"].__setitem__("independent_validation", "done by us"), "independent_validation must be pending or done"),
    (lambda s: s["findings"]["simulated"].append({"kind": "x", "detected": True}), "a simulated event must say detected: false"),
    (lambda s: s["states"].pop("simulated_events"), "the four states must all be present"),
    (lambda s: s["limitations"].append("This makes the television seizure-proof."), "forbidden claim: seizure-proof"),
    (lambda s: s["findings"].__setitem__("actual_count", 7), "actual_count disagrees with the list"),
])
def test_a_collapsed_or_overclaiming_summary_is_refused(tmp_path: Path, mutate, problem):
    ledger = _ledger(tmp_path / "LICENSES.csv", "clip.mp4")
    clean = _map(tmp_path / "clip.wcag.json", profile="wcag", segments=[])
    summary = ev.build_summary(repo=tmp_path, ledger=ledger, ledger_file="clip.mp4", maps=[clean], receipt=None, manifest=None,
                               plots=[], negative_controls=None, test_file=None, simulated=[], not_analyzed=[], report=None, extra_limitations=[])
    mutate(summary)
    assert problem in ev.validate(summary)


def test_the_command_line_writes_a_file_that_validates(tmp_path: Path):
    ledger = _ledger(tmp_path / "LICENSES.csv", "clip.mp4")
    _map(tmp_path / "clip.wcag.json", profile="wcag", segments=[SEGMENT], signed=True)
    out = tmp_path / "summary.json"
    assert ev.main(["--repo", str(tmp_path), "--ledger", str(ledger), "--ledger-file", "clip.mp4",
                    "--map", str(tmp_path / "clip.wcag.json"), "--not-analyzed", "audio", "--out", str(out)]) == 0
    written = json.loads(out.read_text())
    assert ev.validate(written) == []
    assert written["analysis"]["runs"][0]["signature_present"] is True
    assert written["analysis"]["runs"][0]["signature_verification"] == "not performed by this summary"


def test_overlapping_segments_in_one_map_are_one_run_and_broadcast_is_not_wcag(tmp_path: Path):
    path = _map(tmp_path / "broadcast.json", profile="broadcast", segments=[SEGMENT, {**SEGMENT, "start_ms": 200}])
    [span] = ev.distinct_spans([ev.run_block(path, tmp_path)])
    assert span["found_in_runs"] == 1
    assert span["segment_observations"] == 2
    assert span["breaks_wcag_baseline"] is False


def test_profile_luminance_rules_survive_summary_without_confusing_working_color(tmp_path: Path):
    path = _map(tmp_path / "broadcast.json", profile="broadcast", segments=[])
    data = json.loads(path.read_text())
    rules = {"metric": "bt1886-nits", "min_delta": 20, "dark_image_below": 160}
    data["profile"].update({"general_flash": rules, "peak_nits": 200, "transition_pairing": "non-overlapping"})
    path.write_text(json.dumps(data))
    settings = ev.run_block(path, tmp_path)["settings"]
    assert settings["general_flash"] == rules
    assert settings["peak_nits"] == 200
    assert settings["transition_pairing"] == "non-overlapping"
    assert settings["working_color_luminance_model"] == "wcag-relative-luminance-srgb"



def test_the_same_flashing_found_by_several_runs_is_one_distinct_span(tmp_path: Path):
    ledger = _ledger(tmp_path / "LICENSES.csv", "clip.mp4")
    room = {"tv_diagonal_in": 85, "seat_distance_in": 48, "display_aspect": "16:9"}
    a = _map(tmp_path / "a.json", profile="wcag", segments=[SEGMENT])
    wider = {**SEGMENT, "start_ms": 50, "end_ms": 1300, "breaks_baseline": False, "area_window": "room-10deg", "triggered_by": ["room-10deg"]}
    later = {**SEGMENT, "start_ms": 5000, "end_ms": 6000, "breaks_baseline": False}
    b = _map(tmp_path / "b.json", profile="wcag", segments=[wider, later], room=room)
    summary = ev.build_summary(repo=tmp_path, ledger=ledger, ledger_file="clip.mp4", maps=[a, b], receipt=None, manifest=None,
                               plots=[], negative_controls=None, test_file=None, simulated=[], not_analyzed=[], report=None, extra_limitations=[])
    assert ev.validate(summary) == []
    assert summary["findings"]["actual_count"] == 3
    spans = summary["findings"]["distinct_spans"]
    assert summary["findings"]["distinct_span_count"] == len(spans) == 2
    assert spans[0]["start_ms"] == 50 and spans[0]["end_ms"] == 1300 and spans[0]["found_in_runs"] == 2
    assert spans[0]["breaks_wcag_baseline"] is True
    assert spans[1]["found_in_runs"] == 1 and spans[1]["breaks_wcag_baseline"] is False
    assert {f["room"] is None for f in spans[0]["found_by"]} == {True, False}
