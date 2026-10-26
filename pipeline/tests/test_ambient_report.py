"""Synthetic bindings test schema/semantics; actual signature/media checks live in export."""

import hashlib
import json
from pathlib import Path

import pytest

from pipeline import PipelineError
from pipeline.ambient_report import check_ambient_report, strict_json
from pipeline.packaged_library import _check_report


def fixture():
    return json.loads((Path(__file__).parent / "fixtures/ambient-report.json").read_text())


def refresh(value):
    report, title = value["report"], value["title"]
    binding = json.loads(report["inputBindingRaw"])
    for p, proof in report["presets"].items():
        meta = json.loads(proof["metadataRaw"])
        for group in ["ambientAnalysis", "outputAnalysis"]:
            for q, entry in proof[group].items():
                entry["sha256"] = hashlib.sha256(entry["raw"].encode()).hexdigest()
                if group == "outputAnalysis":
                    meta["analysis"][q] = entry["sha256"]
        proof["metadataRaw"] = json.dumps(meta)
        binding["metadataSha512"][p] = hashlib.sha512(proof["metadataRaw"].encode()).hexdigest()
    report["inputBindingRaw"] = json.dumps(binding)
    title["verification"]["checkedInputsSha256"] = hashlib.sha256(
        report["inputBindingRaw"].encode()
    ).hexdigest()


def test_report_uses_distinct_verified_recipe_and_rejects_duplicate_json():
    value = fixture()
    raw = json.dumps(value["report"]).encode()
    _check_report(raw, hashlib.sha256(raw).hexdigest(), [value["title"]])
    with pytest.raises(PipelineError):
        strict_json('{"recipe":1,"recipe":2}')
    with pytest.raises(PipelineError):
        strict_json('{"x":NaN}')
    with pytest.raises(PipelineError):
        check_ambient_report(value["report"], [])


@pytest.mark.parametrize(
    "field,value",
    [
        ("renditionSha256", "f" * 64),
        ("durationMs", 10001),
        ("renditionStartOffsetMs", 1),
        ("preset", "broadcast"),
        ("audioPreserved", False),
        ("frameTimingPreserved", False),
        ("ambientSha256", "f" * 64),
        ("intervals", [{"startMs": 501, "endMs": 2500}]),
        ("version", True),
    ],
)
def test_semantic_changes_rejected_even_with_recomputed_checksums(field, value):
    data = fixture()
    proof = data["report"]["presets"]["wcag"]
    meta = json.loads(proof["metadataRaw"])
    meta[field] = value
    proof["metadataRaw"] = json.dumps(meta)
    refresh(data)
    with pytest.raises(PipelineError):
        check_ambient_report(data["report"], [data["title"]])


@pytest.mark.parametrize("change", ["source", "flags", "thresholds", "profile", "failed"])
def test_rebound_analysis_cannot_weaken_or_replace_evidence(change):
    data = fixture()
    proof = data["report"]["presets"]["wcag"]
    entry = proof["outputAnalysis"]["wcag"]
    raw = json.loads(entry["raw"])
    if change == "source":
        raw["source"]["sha256"] = "e" * 64
    if change == "flags":
        raw["segments"] = [{"start_ms": 0, "end_ms": 1}]
    if change == "thresholds":
        raw["profile"]["room"]["seat_distance_in"] = 96
    if change == "profile":
        raw["profile"]["name"] = "broadcast"
    if change == "failed":
        raw["summary"]["pass"] = False
    entry["raw"] = json.dumps(raw)
    refresh(data)
    with pytest.raises(PipelineError):
        check_ambient_report(data["report"], [data["title"]])


@pytest.mark.parametrize(
    "field,value",
    [
        ("sourceEqualsOutput", False),
        ("frameCount", 0),
        ("audioPacketCount", -1),
        ("videoDurationRational", "9"),
        ("frameTimesSha256", "wrong"),
    ],
)
def test_timing_audio_proof_cannot_be_dropped(field, value):
    data = fixture()
    data["report"]["presets"]["wcag"]["timingAudio"][field] = value
    with pytest.raises(PipelineError):
        check_ambient_report(data["report"], [data["title"]])


def test_signer_and_reproduction_and_missing_presets_are_rejected():
    for field in ["signer", "reproduction", "preset"]:
        data = fixture()
        report = data["report"]
        if field == "signer":
            report["publicKeyFingerprint"] = "f" * 64
        if field == "reproduction":
            report["presets"]["wcag"]["reproductionSha256"] = "f" * 64
        if field == "preset":
            del report["presets"]["broadcast"]
        with pytest.raises(PipelineError):
            check_ambient_report(report, [data["title"]])
