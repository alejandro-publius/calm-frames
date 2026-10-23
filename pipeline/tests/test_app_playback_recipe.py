"""App-plan contracts and real ffmpeg preparation with labelled sham intervals.

The source clip is benign. The test analyzer fabricates only flagged intervals;
hashes, signatures, encoding, cover proofs and package checks execute normally.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from pipeline import PipelineError
from pipeline.flashmap_adapter import FlashmapAdapter, load_map, parse_map
from pipeline.hideplan import (
    APP_PLAYBACK_RECIPE,
    APP_PLAYBACK_TIMING,
    HidePlan,
    build_app_playback_plan,
)
from pipeline.ingest import IngestOptions, ingest_title
from pipeline.local_library import prepare_local_title
from pipeline.registry import load_private_key, sign_document, write_registry
from pipeline.verify import verify_title

from .clips import make_calm_clip
from .conftest import needs_ffmpeg

SHA = "a" * 64


def maps():
    return {profile: parse_map({
        "version": 1, "source": {"sha256": SHA}, "profile": {"name": profile},
        "segments": [{"start_ms": start, "end_ms": end, "reason": reason}],
        "summary": {"pass": False},
    }) for profile, start, end, reason in (
        ("wcag", 2500, 3000, "general"), ("broadcast", 5000, 5500, "red"),
    )}


def pairs(plan):
    return [(interval.start_ms, interval.end_ms, interval.reason) for interval in plan.intervals]


class RealAnalyzerWithShamProfileUnion(FlashmapAdapter):
    """Production measurements with distinct, labelled sham source intervals."""

    def __init__(self, source, private):
        super().__init__(command=[sys.executable, "-m", "flashmap"])
        self.source, self.private = source.resolve(), private
        self.measured_profiles = set()

    def analyze(self, video, **kwargs):
        measured = super().analyze(video, **kwargs)
        if Path(video).resolve() != self.source:
            return measured
        assert measured.is_clean
        assert measured.raw["generator"]["name"] == "flashmap"
        self.measured_profiles.add(kwargs["profile"])
        start, end, reason = ((5000, 5500, "red") if kwargs["profile"] == "broadcast"
                              else (2500, 3000, "general"))
        document = dict(measured.raw)
        document["test_sham_intervals"] = {
            "label": "Synthetic app-union integration interval, not a measured finding",
            "original_measured_segment_count": 0,
        }
        document["segments"] = [{"start_ms": start, "end_ms": end, "reason": reason}]
        document["summary"] = {**document["summary"], "pass": False, "flash_pass": False,
                               "segment_count": 1, "hidden_ms": end - start}
        output = Path(kwargs["out_path"])
        write_registry(sign_document(document, load_private_key(self.private)), output)
        sham = load_map(output)
        sham.preset = kwargs["profile"]
        return sham


@pytest.mark.parametrize("preset,expected", [
    ("wcag", [(2000, 3500, "general")]),
    ("broadcast", [(2000, 3500, "general"), (4500, 6000, "red")]),
    ("extra-cautious", [(1500, 6500, "red")]),
])
def test_complete_required_profile_union_uses_the_app_timing(preset, expected):
    plan = build_app_playback_plan(maps(), source_sha256=SHA, duration_ms=8000, preset=preset)
    assert pairs(plan) == expected
    assert (plan.guard_band_ms, plan.min_cover_ms) == APP_PLAYBACK_TIMING[preset]
    assert plan.allow_dim is False
    assert plan.recipe == APP_PLAYBACK_RECIPE
    assert HidePlan.from_dict(plan.to_dict()) == plan


@pytest.mark.parametrize("damage", ["missing", "source", "profile"])
def test_recipe_refuses_missing_or_misidentified_input_maps(damage):
    documents = maps()
    if damage == "missing":
        del documents["wcag"]
    elif damage == "source":
        documents["wcag"].source_sha256 = "b" * 64
    else:
        documents["wcag"].profile = "broadcast"
    with pytest.raises(PipelineError, match="required source-bound"):
        build_app_playback_plan(documents, source_sha256=SHA, duration_ms=8000, preset="broadcast")


def test_compatible_ingest_requires_all_profiles_that_will_be_verified(tmp_path):
    with pytest.raises(PipelineError, match="WCAG and Broadcast"):
        ingest_title(tmp_path / "missing.mp4", tmp_path / "work",
                     IngestOptions(presets=["broadcast"], playback_compatible=True))


@pytest.mark.parametrize("preset,duration", [("unknown", 8000), ("wcag", 0),
                                             ("wcag", float("nan"))])
def test_recipe_rejects_an_unknown_policy_or_invalid_duration(preset, duration):
    with pytest.raises(PipelineError, match="known preset and finite duration"):
        build_app_playback_plan(maps(), source_sha256=SHA, duration_ms=duration, preset=preset)


@needs_ffmpeg
def test_verifier_rejects_changed_recipe_fields_and_unchecked_union_inputs(tmp_path, analyzer, keypair):
    private, public = keypair
    source = make_calm_clip(tmp_path / "sham-source.mp4", seconds=8, fps=10,
                            width=160, height=90)
    analyzer.flag("sham-source.mp4", segments={
        "wcag": [[2500, 3000, "general"]], "broadcast": [[5000, 5500, "red"]],
    })
    result = ingest_title(source, tmp_path / "out", IngestOptions(
        key=str(private), pub=str(public), playback_compatible=True,
        skip_verify=True, x264_preset="ultrafast", poster_count=1,
    ))
    layout = result.layout
    presets = ["wcag", "broadcast", "extra-cautious"]

    def verify(requested=presets):
        return verify_title(layout, source=source, presets=requested,
                            adapter=FlashmapAdapter(), pub_key=public, rerender_cover_model=False)

    assert verify().passed
    plan_path = layout.plan_path("broadcast")
    original = json.loads(plan_path.read_text())
    for field, bad in (("recipe", "unknown"), ("profile", "wcag"), ("source_sha256", "b" * 64),
                       ("duration_ms", 9000), ("guard_band_ms", 0), ("min_cover_ms", 0),
                       ("allow_dim", True), ("intervals", original["intervals"][1:])):
        plan_path.write_text(json.dumps({**original, field: bad}))
        report = verify()
        assert "plan_matches_map:broadcast" in [c.name for c in report.failures], field
    plan_path.write_text(json.dumps(original))
    assert "playback_recipe_profiles" in [c.name for c in verify(["broadcast"]).failures]

    entry = json.loads(layout.entry_path.read_text())
    entry["notes"]["playback_recipe"] = "unknown"
    layout.entry_path.write_text(json.dumps(entry))
    assert "playback_recipe" in [c.name for c in verify().failures]


@needs_ffmpeg
def test_flagged_local_preparation_reaches_packaged_export_and_plan_tampering_fails(
    tmp_path, keypair,
):
    from pipeline.layout import TitleLayout
    from pipeline.packaged_library import check_packaged_library, export_packaged_library
    private, public = keypair
    source = make_calm_clip(tmp_path / "sham-source.mp4", seconds=8, fps=10,
                            width=160, height=90, subtitles=True)
    analyzer = RealAnalyzerWithShamProfileUnion(source, private)
    root = tmp_path / "library"
    receipt = prepare_local_title(source, root, key=private, pub=public,
                                  title="Benign integration clip with synthetic intervals",
                                  adapter=analyzer)
    assert receipt["status"] == "ready", receipt
    assert analyzer.measured_profiles == {"wcag", "broadcast", "extra-cautious"}
    layout = TitleLayout(root, receipt["source_sha256"])
    plans = {name: HidePlan.from_dict(json.loads(layout.plan_path(name).read_text()))
             for name in ("wcag", "broadcast", "extra-cautious")}
    assert pairs(plans["broadcast"]) == [(2000, 3500, "general"), (4500, 6000, "red")]
    assert pairs(plans["extra-cautious"]) == [(1500, 6500, "red")]
    for name in plans:
        assert "scene_holds" not in json.loads(layout.map_path(name).read_text())
        assert plans[name].allow_dim is False
    manifest = export_packaged_library(root, tmp_path / "package", pub=public)
    assert check_packaged_library(tmp_path / "package") == manifest
    assert manifest["titles"][0]["sourceSha256"] == receipt["source_sha256"]

    # Recompute from maps and fixed policy, never accept the stored recipe's
    # self-reported shortened interval or weaker timing as the expected answer.
    damaged = plans["broadcast"].to_dict()
    damaged["intervals"] = damaged["intervals"][1:]
    damaged["guard_band_ms"] = 0
    layout.plan_path("broadcast").write_text(json.dumps(damaged))
    report = verify_title(layout, source=source, presets=list(plans),
                          adapter=FlashmapAdapter(), pub_key=public, rerender_cover_model=False)
    assert not report.passed
    assert "plan_matches_map:broadcast" in [check.name for check in report.failures]
    with pytest.raises(PipelineError):
        export_packaged_library(root, tmp_path / "package", pub=public)
