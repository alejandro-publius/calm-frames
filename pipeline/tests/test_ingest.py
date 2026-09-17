"""Ingest end to end, and the promise that a second run does no work.

These run the real pipeline on a generated calm clip, with the fake analyzer
standing in for flashmap. Every ffmpeg call is real.
"""

from __future__ import annotations

import json

import pytest

from pipeline.bif import read_bif
from pipeline.catalog import STATUS_PENDING, STATUS_VERIFIED, kid_mode_titles
from pipeline.hideplan import HidePlan
from pipeline.ingest import IngestOptions, ingest_title
from pipeline.layout import TitleLayout

from .clips import make_calm_clip
from .conftest import needs_ffmpeg

pytestmark = needs_ffmpeg

FLAGGED = [[3000, 4000, "general"]]


def options(keypair, **overrides) -> IngestOptions:
    private, public = keypair
    base = dict(
        presets=["wcag"],
        key=str(private),
        pub=str(public),
        poster_count=2,
        bif_interval_ms=2000,
        x264_preset="ultrafast",
    )
    base.update(overrides)
    return IngestOptions(**base)


@pytest.fixture
def source(tmp_path):
    return make_calm_clip(tmp_path / "clip.mp4", seconds=8.0)


@pytest.fixture
def flagged_analyzer(analyzer):
    analyzer.flag("clip.mp4", segments={"wcag": FLAGGED, "broadcast": FLAGGED,
                                        "extra-cautious": FLAGGED})
    return analyzer


class TestEndToEnd:
    def test_every_artifact_is_built_and_the_title_publishes(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        result = ingest_title(source, tmp_path / "out", options(keypair))
        layout = result.layout

        assert layout.probe_path.exists()
        assert layout.map_path("wcag").exists()
        assert layout.plan_path("wcag").exists()
        assert layout.still_path.exists()
        assert layout.safe_master("wcag").exists()
        assert layout.master_playlist("wcag").exists()
        assert layout.bif_path("wcag").exists()
        assert layout.posters_manifest("wcag").exists()
        assert layout.cover_model_path("wcag").exists()
        assert layout.verify_report_path.exists()

        assert result.verify_passed, json.dumps(result.verify_report, indent=2)
        assert result.publishable
        assert result.entry.status == STATUS_VERIFIED

    def test_the_plan_widens_the_flagged_span_by_the_guard_band(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        result = ingest_title(source, tmp_path / "out", options(keypair))
        plan = HidePlan.from_dict(
            json.loads(result.layout.plan_path("wcag").read_text())
        )
        assert [(i.start_ms, i.end_ms) for i in plan.intervals] == [(2500, 4500)]

    def test_kid_mode_lists_the_title_once_it_is_verified(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        result = ingest_title(source, tmp_path / "out", options(keypair))
        listed = kid_mode_titles(result.layout.index_path)
        assert [entry["sha256"] for entry in listed] == [result.sha256]

    def test_skip_verify_leaves_the_title_out_of_kid_mode(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        result = ingest_title(
            source, tmp_path / "out", options(keypair, skip_verify=True)
        )
        assert not result.publishable
        assert result.entry.status == STATUS_PENDING
        assert kid_mode_titles(result.layout.index_path) == []

    def test_trickplay_and_posters_come_from_the_safe_rendition(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        result = ingest_title(source, tmp_path / "out", options(keypair))
        layout = result.layout
        bif_manifest = json.loads(layout.bif_manifest("wcag").read_text())
        posters = json.loads(layout.posters_manifest("wcag").read_text())
        assert bif_manifest["from"] == "safe_rendition"
        assert bif_manifest["source_file"] == str(layout.safe_master("wcag"))
        assert posters["from"] == "safe_rendition"
        parsed = read_bif(layout.bif_path("wcag"))
        assert parsed.count == len(bif_manifest["frames"]) >= 4

    def test_every_trickplay_frame_and_poster_is_calm(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        result = ingest_title(source, tmp_path / "out", options(keypair))
        layout = result.layout
        plan = HidePlan.from_dict(json.loads(layout.plan_path("wcag").read_text()))
        covered = [(i.start_ms, i.end_ms) for i in plan.intervals]
        frames = json.loads(layout.bif_manifest("wcag").read_text())["frames"]
        posters = json.loads(layout.posters_manifest("wcag").read_text())["posters"]
        for time_ms in [f["source_ms"] for f in frames] + [
            p["time_ms"] for p in posters
        ]:
            assert not any(start <= time_ms < end for start, end in covered)

    def test_all_three_presets_get_their_own_rendition(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        result = ingest_title(
            source,
            tmp_path / "out",
            options(keypair, presets=["wcag", "broadcast", "extra-cautious"]),
        )
        for preset in ("wcag", "broadcast", "extra-cautious"):
            assert result.layout.safe_master(preset).exists()
            assert result.layout.map_path(preset).exists()
            assert result.layout.bif_path(preset).exists()
        assert result.verify_passed

    def test_a_title_with_nothing_flagged_still_gets_a_rendition_and_verifies(
        self, source, tmp_path, analyzer, keypair
    ):
        result = ingest_title(source, tmp_path / "out", options(keypair))
        plan = HidePlan.from_dict(
            json.loads(result.layout.plan_path("wcag").read_text())
        )
        assert plan.intervals == []
        assert result.verify_passed
        assert result.publishable


class TestIdempotency:
    def test_a_second_run_does_no_work(
        self, source, tmp_path, flagged_analyzer, keypair, ffmpeg_calls
    ):
        workdir = tmp_path / "out"
        first = ingest_title(source, workdir, options(keypair))
        assert first.verify_passed
        first_ffmpeg = len(ffmpeg_calls)
        first_analyze = len(flagged_analyzer.calls("analyze"))
        assert first_ffmpeg > 0

        ffmpeg_calls.clear()
        second = ingest_title(source, workdir, options(keypair))

        assert ffmpeg_calls == []
        assert len(flagged_analyzer.calls("analyze")) == first_analyze
        assert second.steps_run == []
        assert "verify" in second.steps_skipped
        assert second.publishable

    def test_a_second_run_leaves_the_files_alone(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        workdir = tmp_path / "out"
        first = ingest_title(source, workdir, options(keypair))
        layout = first.layout
        watched = [
            layout.safe_master("wcag"),
            layout.master_playlist("wcag"),
            layout.bif_path("wcag"),
            layout.still_path,
            layout.map_path("wcag"),
            layout.cover_model_path("wcag"),
        ]
        before = {path: path.stat().st_mtime_ns for path in watched}

        ingest_title(source, workdir, options(keypair))

        after = {path: path.stat().st_mtime_ns for path in watched}
        assert before == after

    def test_the_title_stays_in_kid_mode_after_a_second_run(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        workdir = tmp_path / "out"
        first = ingest_title(source, workdir, options(keypair))
        second = ingest_title(source, workdir, options(keypair))
        listed = kid_mode_titles(second.layout.index_path)
        assert [entry["sha256"] for entry in listed] == [first.sha256]
        assert second.entry.status == STATUS_VERIFIED

    def test_the_same_bytes_under_another_name_reuse_the_same_work(
        self, source, tmp_path, flagged_analyzer, keypair, ffmpeg_calls
    ):
        workdir = tmp_path / "out"
        first = ingest_title(source, workdir, options(keypair))
        copy = tmp_path / "clip_copy.mp4"
        copy.write_bytes(source.read_bytes())

        ffmpeg_calls.clear()
        second = ingest_title(copy, workdir, options(keypair))

        assert second.sha256 == first.sha256
        assert second.layout.root == first.layout.root
        assert ffmpeg_calls == []

    def test_a_different_guard_band_redoes_the_plan_but_not_the_analysis(
        self, source, tmp_path, flagged_analyzer, keypair, ffmpeg_calls
    ):
        workdir = tmp_path / "out"
        ingest_title(source, workdir, options(keypair))
        analyze_calls = len(flagged_analyzer.calls("analyze"))

        ffmpeg_calls.clear()
        second = ingest_title(source, workdir, options(keypair, guard_band_ms=1500))

        assert "plan:wcag" in second.steps_run
        assert "rendition:wcag" in second.steps_run
        assert "analyze:wcag" in second.steps_skipped
        assert ffmpeg_calls, "the rendition has to be built again"
        # Analyze ran again only for the safe rendition and the cover model
        # inside verify, never for the source.
        new_calls = flagged_analyzer.calls("analyze")[analyze_calls:]
        assert all("clip.mp4" not in call["video"] for call in new_calls)

        plan = HidePlan.from_dict(
            json.loads(second.layout.plan_path("wcag").read_text())
        )
        assert [(i.start_ms, i.end_ms) for i in plan.intervals] == [(1500, 5500)]

    def test_force_redoes_everything(
        self, source, tmp_path, flagged_analyzer, keypair, ffmpeg_calls
    ):
        workdir = tmp_path / "out"
        ingest_title(source, workdir, options(keypair))
        analyze_calls = len(flagged_analyzer.calls("analyze"))

        ffmpeg_calls.clear()
        second = ingest_title(source, workdir, options(keypair, force=True))

        assert "analyze:wcag" in second.steps_run
        assert "rendition:wcag" in second.steps_run
        assert second.steps_skipped == []
        assert len(flagged_analyzer.calls("analyze")) > analyze_calls
        assert len(ffmpeg_calls) > 5

    def test_a_deleted_artifact_is_rebuilt(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        workdir = tmp_path / "out"
        first = ingest_title(source, workdir, options(keypair))
        first.layout.safe_master("wcag").unlink()

        second = ingest_title(source, workdir, options(keypair))

        assert "rendition:wcag" in second.steps_run
        assert second.layout.safe_master("wcag").exists()

    def test_a_ledger_from_an_older_pipeline_version_starts_over(
        self, source, tmp_path, flagged_analyzer, keypair
    ):
        workdir = tmp_path / "out"
        first = ingest_title(source, workdir, options(keypair))
        state_path = first.layout.root / "state.json"
        state = json.loads(state_path.read_text())
        state["pipeline_version"] = "0"
        state_path.write_text(json.dumps(state))

        second = ingest_title(source, workdir, options(keypair))
        assert "rendition:wcag" in second.steps_run


class TestLayout:
    def test_titles_are_filed_under_their_hash(self, source, tmp_path, flagged_analyzer, keypair):
        result = ingest_title(source, tmp_path / "out", options(keypair))
        expected = TitleLayout(tmp_path / "out", result.sha256)
        assert result.layout.root == expected.root
        assert result.sha256 in str(result.layout.root)
