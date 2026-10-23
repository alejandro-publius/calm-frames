"""Cached metadata and previews stay bound to the bytes that were produced."""

from __future__ import annotations

import json

import pytest

from pipeline.ingest import IngestOptions, ingest_title

from .clips import make_calm_clip
from .conftest import needs_ffmpeg


@pytest.fixture
def cached_title(tmp_path, analyzer, keypair):
    private, public = keypair
    source = make_calm_clip(tmp_path / "cached.mp4", seconds=6)
    analyzer.flag("cached.mp4", segments={"wcag": [[2000, 2500, "general"]]})
    options = IngestOptions(
        presets=["wcag"], key=str(private), pub=str(public),
        x264_preset="ultrafast", poster_count=1, bif_interval_ms=3000,
    )
    result = ingest_title(source, tmp_path / "out", options)
    assert result.verify_passed, result.verify_report
    return source, options, result


def _artifact(layout, name):
    return {
        "probe": (layout.probe_path, "probe"),
        "still": (layout.still_path, "still"),
        "still_manifest": (layout.still_manifest_path, "still"),
        "bif": (layout.bif_path("wcag"), "bif:wcag"),
        "bif_manifest": (layout.bif_manifest("wcag"), "bif:wcag"),
        "poster": (next(layout.posters_dir("wcag").glob("*.jpg")), "posters:wcag"),
        "posters_manifest": (layout.posters_manifest("wcag"), "posters:wcag"),
    }[name]


@needs_ffmpeg
@pytest.mark.parametrize("name", [
    "probe", "still", "still_manifest", "bif", "bif_manifest", "poster", "posters_manifest",
])
def test_same_path_changed_cached_artifact_is_regenerated_before_publication(cached_title, name):
    source, options, first = cached_title
    path, step = _artifact(first.layout, name)
    original = path.read_bytes()
    # Invalid harmless bytes also exercise regeneration before JSON or image
    # decoding. No damaged preview is ever displayed or played.
    path.write_bytes(b"changed cached output, not a picture or a manifest")
    second = ingest_title(source, first.layout.workdir, options)
    assert step in second.steps_run
    assert path.read_bytes() == original
    assert second.publishable, second.verify_report


@needs_ffmpeg
def test_missing_poster_is_a_recorded_output_and_is_regenerated(cached_title):
    source, options, first = cached_title
    poster, step = _artifact(first.layout, "poster")
    original = poster.read_bytes()
    poster.unlink()
    second = ingest_title(source, first.layout.workdir, options)
    assert step in second.steps_run
    assert poster.read_bytes() == original
    assert second.publishable, second.verify_report


@needs_ffmpeg
def test_unchanged_checked_outputs_preserve_a_work_free_restart(cached_title, ffmpeg_calls):
    source, options, first = cached_title
    state = json.loads((first.layout.root / "state.json").read_text())
    # Every committed step, not only these four, records the hash of each output.
    for step in ("probe", "still", "bif:wcag", "posters:wcag"):
        assert state["steps"][step]["output_sha256"]
    for step, record in state["steps"].items():
        assert set(record["output_sha256"]) == set(record["outputs"]) != set(), step
    poster, _ = _artifact(first.layout, "poster")
    assert first.layout.relative(poster) in state["steps"]["posters:wcag"]["outputs"]
    ffmpeg_calls.clear()
    second = ingest_title(source, first.layout.workdir, options)
    assert second.steps_run == []
    assert "verify" in second.steps_skipped
    assert not ffmpeg_calls
    assert second.publishable
