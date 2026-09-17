"""Verify has to say no.

Each test here builds a real title, breaks one thing about it, and checks that
verify catches that one thing and refuses to let the title publish. The first
test proves the unbroken title passes, so a failure in the others means the
break was caught rather than that nothing ever passes.
"""

from __future__ import annotations

import json
import shutil

import pytest

from pipeline.catalog import STATUS_FAILED, kid_mode_titles, read_entry
from pipeline.flashmap_adapter import FlashmapAdapter
from pipeline.hideplan import HidePlan
from pipeline.ingest import IngestOptions, ingest_title
from pipeline.verify import main as verify_main
from pipeline.verify import verify_title

from .clips import make_calm_clip
from .conftest import needs_ffmpeg

pytestmark = needs_ffmpeg

FLAGGED = [[3000, 4000, "general"]]


@pytest.fixture
def built(tmp_path, analyzer, keypair):
    """A title with every artifact built, but not yet verified."""
    private, public = keypair
    source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0)
    analyzer.flag("clip.mp4", segments={"wcag": FLAGGED})
    options = IngestOptions(
        presets=["wcag"],
        key=str(private),
        pub=str(public),
        poster_count=2,
        bif_interval_ms=2000,
        x264_preset="ultrafast",
        skip_verify=True,
    )
    result = ingest_title(source, tmp_path / "out", options)
    return {
        "result": result,
        "layout": result.layout,
        "source": source,
        "analyzer": analyzer,
        "public": public,
        "workdir": tmp_path / "out",
    }


def run_verify(built, **overrides):
    kwargs = dict(
        source=built["source"],
        presets=["wcag"],
        adapter=FlashmapAdapter(),
        pub_key=built["public"],
        rerender_cover_model=False,
    )
    kwargs.update(overrides)
    return verify_title(built["layout"], **kwargs)


def failed_names(report):
    return [check.name for check in report.failures]


class TestAGoodTitlePasses:
    def test_nothing_broken_means_it_passes(self, built):
        report = run_verify(built)
        assert report.passed, failed_names(report)
        assert len(report.checks) > 10


class TestARenditionWithAViolation:
    def test_a_violation_left_in_the_safe_rendition_blocks_publishing(self, built):
        # The analyzer now reports a flash inside the kid safe rendition.
        built["analyzer"].flag("safe.mp4", segments={"wcag": [[1000, 1200, "general"]]})
        report = run_verify(built)
        assert not report.passed
        assert "safe_rendition_clean:wcag" in failed_names(report)

    def test_a_violation_left_under_the_on_device_cover_blocks_publishing(self, built):
        built["analyzer"].flag(
            "cover_model_wcag.mp4", segments={"wcag": [[3100, 3300, "general"]]}
        )
        report = run_verify(built)
        assert not report.passed
        assert "cover_model_clean:wcag" in failed_names(report)

    def test_an_analyzer_that_cannot_read_the_rendition_blocks_publishing(self, built):
        built["analyzer"].fail_on("safe.mp4", "could not decode")
        report = run_verify(built)
        assert not report.passed
        assert "safe_rendition_clean:wcag" in failed_names(report)

    def test_a_rendition_that_covered_nothing_is_caught_without_the_analyzer(self, built):
        # The analyzer still says the rendition is clean, because the source
        # clip has no flash in it. Only the check against the cover still can
        # tell that the covering step did nothing.
        layout = built["layout"]
        shutil.copyfile(built["source"], layout.safe_master("wcag"))
        report = run_verify(built)
        assert not report.passed
        assert "cover_actually_drawn:wcag" in failed_names(report)

    def test_a_missing_rendition_blocks_publishing(self, built):
        built["layout"].safe_master("wcag").unlink()
        report = run_verify(built)
        assert not report.passed
        assert "safe_rendition_present:wcag" in failed_names(report)


class TestATamperedMap:
    def test_removing_a_flagged_span_from_a_signed_map_is_caught(self, built):
        layout = built["layout"]
        data = json.loads(layout.map_path("wcag").read_text())
        # A careful tamper: the segment goes, and the summary is edited to
        # match, so the map still reads as a consistent clean map. Only the
        # signature can tell.
        data["segments"] = []
        data["summary"] = {**data["summary"], "pass": True, "segment_count": 0}
        layout.map_path("wcag").write_text(json.dumps(data))

        report = run_verify(built)
        assert not report.passed
        assert "map_signature:wcag" in failed_names(report)

    def test_a_careless_tamper_is_caught_before_the_signature_check(self, built):
        layout = built["layout"]
        data = json.loads(layout.map_path("wcag").read_text())
        data["segments"] = []
        layout.map_path("wcag").write_text(json.dumps(data))

        report = run_verify(built)
        assert not report.passed
        assert "map_readable:wcag" in failed_names(report)

    def test_a_map_that_cannot_be_parsed_is_caught(self, built):
        built["layout"].map_path("wcag").write_text("{ not json")
        report = run_verify(built)
        assert not report.passed
        assert "map_readable:wcag" in failed_names(report)

    def test_a_map_with_no_segment_list_is_not_read_as_clean(self, built):
        layout = built["layout"]
        data = json.loads(layout.map_path("wcag").read_text())
        data.pop("segments")
        layout.map_path("wcag").write_text(json.dumps(data))
        report = run_verify(built)
        assert not report.passed
        assert "map_readable:wcag" in failed_names(report)

    def test_no_public_key_means_no_publishing(self, built):
        report = run_verify(built, pub_key=None)
        assert not report.passed
        assert "map_signature:wcag" in failed_names(report)

    def test_a_plan_that_does_not_match_its_map_is_caught(self, built):
        layout = built["layout"]
        plan = json.loads(layout.plan_path("wcag").read_text())
        plan["intervals"] = []
        layout.plan_path("wcag").write_text(json.dumps(plan))
        report = run_verify(built)
        assert not report.passed
        assert "plan_matches_map:wcag" in failed_names(report)

    def test_a_plan_whose_reasons_do_not_match_its_map_is_caught(self, built):
        layout = built["layout"]
        plan = json.loads(layout.plan_path("wcag").read_text())
        plan["intervals"][0]["reason"] = "red"
        layout.plan_path("wcag").write_text(json.dumps(plan))

        report = run_verify(built)
        assert not report.passed
        assert "plan_matches_map:wcag" in failed_names(report)

    def test_verify_catches_a_dim_rule_that_lets_red_through(self, built, monkeypatch):
        """Break the red rule in the code and watch verify notice.

        Red intervals are opaque by construction, so no plan file on disk can
        put one in the dim list. The only way this guard can fail is if the
        rule itself changes, which is what this test does on purpose.
        """
        from pipeline import hideplan

        layout = built["layout"]
        plan = json.loads(layout.plan_path("wcag").read_text())
        plan["intervals"][0]["reason"] = "red"
        layout.plan_path("wcag").write_text(json.dumps(plan))

        def dims_everything(interval, *, allow_dim: bool = True) -> str:
            return hideplan.DIM if allow_dim else hideplan.OPAQUE

        monkeypatch.setattr(hideplan, "cover_mode", dims_everything)

        report = run_verify(built)
        assert not report.passed
        assert "red_always_opaque:wcag" in failed_names(report)


class TestAWrongHash:
    def test_a_map_bound_to_another_file_is_caught(self, built):
        layout = built["layout"]
        data = json.loads(layout.map_path("wcag").read_text())
        data["source_sha256"] = "b" * 64
        layout.map_path("wcag").write_text(json.dumps(data))

        report = run_verify(built)
        assert not report.passed
        names = failed_names(report)
        assert "map_hash:wcag" in names
        assert "map_signature:wcag" in names

    def test_a_source_file_that_changed_since_ingest_is_caught(self, built, tmp_path):
        other = make_calm_clip(tmp_path / "other.mp4", seconds=6.0)
        report = run_verify(built, source=other)
        assert not report.passed
        assert "source_hash" in failed_names(report)

    def test_a_missing_source_file_is_caught(self, built, tmp_path):
        report = run_verify(built, source=tmp_path / "gone.mp4")
        assert not report.passed
        assert "source_present" in failed_names(report)


class TestFramesFromFlaggedMoments:
    def test_a_poster_taken_from_a_flagged_moment_is_caught(self, built):
        layout = built["layout"]
        manifest = json.loads(layout.posters_manifest("wcag").read_text())
        manifest["posters"][0]["time_ms"] = 3500  # inside the flagged span
        layout.posters_manifest("wcag").write_text(json.dumps(manifest))

        report = run_verify(built)
        assert not report.passed
        assert "posters_calm:wcag" in failed_names(report)

    def test_a_poster_taken_from_the_guard_band_is_caught(self, built):
        layout = built["layout"]
        manifest = json.loads(layout.posters_manifest("wcag").read_text())
        manifest["posters"][0]["time_ms"] = 2600  # guard band, before the span
        layout.posters_manifest("wcag").write_text(json.dumps(manifest))

        report = run_verify(built)
        assert not report.passed
        assert "posters_calm:wcag" in failed_names(report)

    def test_a_poster_file_that_is_not_there_is_caught(self, built):
        layout = built["layout"]
        manifest = json.loads(layout.posters_manifest("wcag").read_text())
        from pathlib import Path

        Path(manifest["posters"][0]["path"]).unlink()
        report = run_verify(built)
        assert not report.passed
        assert "posters_calm:wcag" in failed_names(report)

    def test_a_trickplay_frame_from_a_flagged_moment_is_caught(self, built):
        layout = built["layout"]
        manifest = json.loads(layout.bif_manifest("wcag").read_text())
        manifest["frames"][0]["source_ms"] = 3500
        layout.bif_manifest("wcag").write_text(json.dumps(manifest))

        report = run_verify(built)
        assert not report.passed
        assert "bif_calm:wcag" in failed_names(report)

    def test_trickplay_taken_from_the_original_is_caught(self, built):
        layout = built["layout"]
        manifest = json.loads(layout.bif_manifest("wcag").read_text())
        manifest["from"] = "source"
        layout.bif_manifest("wcag").write_text(json.dumps(manifest))

        report = run_verify(built)
        assert not report.passed
        assert "bif_from_safe_rendition:wcag" in failed_names(report)

    def test_a_title_built_with_a_weaker_calm_rule_is_caught(
        self, tmp_path, analyzer, keypair
    ):
        private, public = keypair
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0)
        analyzer.flag("clip.mp4", segments={"wcag": FLAGGED})
        result = ingest_title(
            source,
            tmp_path / "out",
            IngestOptions(
                presets=["wcag"],
                key=str(private),
                pub=str(public),
                poster_count=2,
                bif_interval_ms=2000,
                calm_margin_ms=200,
                x264_preset="ultrafast",
                skip_verify=True,
            ),
        )
        report = verify_title(
            result.layout,
            source=source,
            presets=["wcag"],
            adapter=FlashmapAdapter(),
            pub_key=public,
            rerender_cover_model=False,
        )
        assert not report.passed
        assert "calm_margin_policy:wcag" in failed_names(report)

    def test_a_cover_still_from_a_flagged_moment_is_caught(self, built):
        layout = built["layout"]
        layout.still_manifest_path.write_text(
            json.dumps({"time_ms": 3500, "from": "source"})
        )
        report = run_verify(built)
        assert not report.passed
        assert "cover_still_calm" in failed_names(report)


class TestTheCommandLineBlocksPublishing:
    def test_a_good_title_exits_zero_and_lands_in_kid_mode(self, built, capsys):
        code = verify_main(
            [
                "--workdir",
                str(built["workdir"]),
                "--sha",
                built["result"].sha256,
                "--source",
                str(built["source"]),
                "--pub",
                str(built["public"]),
                "--no-rerender",
            ]
        )
        assert code == 0
        assert "VERIFY PASSED" in capsys.readouterr().out
        entry = read_entry(built["layout"].entry_path)
        assert entry.kid_mode_visible
        assert kid_mode_titles(built["layout"].index_path)

    def test_a_broken_title_exits_non_zero_and_stays_out_of_kid_mode(
        self, built, capsys
    ):
        built["analyzer"].flag("safe.mp4", segments={"wcag": [[1000, 1200, "general"]]})
        code = verify_main(
            [
                "--workdir",
                str(built["workdir"]),
                "--sha",
                built["result"].sha256,
                "--source",
                str(built["source"]),
                "--pub",
                str(built["public"]),
                "--no-rerender",
            ]
        )
        assert code == 1
        captured = capsys.readouterr()
        assert "VERIFY FAILED" in captured.err
        assert "safe_rendition_clean:wcag" in captured.err

        entry = read_entry(built["layout"].entry_path)
        assert entry.verified is False
        assert not entry.kid_mode_visible
        assert entry.status == STATUS_FAILED
        assert kid_mode_titles(built["layout"].index_path) == []

    def test_an_unknown_title_exits_two(self, tmp_path, capsys):
        code = verify_main(["--workdir", str(tmp_path), "--sha", "a" * 64])
        assert code == 2

    def test_the_report_is_written_where_the_catalog_points(self, built):
        verify_main(
            [
                "--workdir",
                str(built["workdir"]),
                "--sha",
                built["result"].sha256,
                "--source",
                str(built["source"]),
                "--pub",
                str(built["public"]),
                "--no-rerender",
            ]
        )
        report = json.loads(built["layout"].verify_report_path.read_text())
        assert report["passed"] is True
        assert report["sha256"] == built["result"].sha256


class TestIngestStopsAtVerify:
    def test_a_failing_verify_keeps_the_title_out_of_kid_mode(
        self, tmp_path, analyzer, keypair
    ):
        private, public = keypair
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0)
        analyzer.flag("safe.mp4", segments={"wcag": [[1000, 1200, "general"]]})
        analyzer.flag("clip.mp4", segments={"wcag": FLAGGED})
        result = ingest_title(
            source,
            tmp_path / "out",
            IngestOptions(
                presets=["wcag"],
                key=str(private),
                pub=str(public),
                poster_count=2,
                bif_interval_ms=2000,
                        x264_preset="ultrafast",
            ),
        )
        assert not result.verify_passed
        assert not result.publishable
        assert result.entry.verified is False
        assert kid_mode_titles(result.layout.index_path) == []

    def test_a_failing_verify_is_never_cached(self, tmp_path, analyzer, keypair):
        private, public = keypair
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0)
        analyzer.flag("safe.mp4", segments={"wcag": [[1000, 1200, "general"]]})
        analyzer.flag("clip.mp4", segments={"wcag": FLAGGED})
        options = IngestOptions(
            presets=["wcag"],
            key=str(private),
            pub=str(public),
            poster_count=2,
            bif_interval_ms=2000,
                x264_preset="ultrafast",
        )
        workdir = tmp_path / "out"
        first = ingest_title(source, workdir, options)
        assert not first.verify_passed

        second = ingest_title(source, workdir, options)
        assert "verify" in second.steps_run
        assert not second.verify_passed


class TestDimIsNotAlwaysEnough:
    def test_a_failing_cover_model_says_to_turn_dim_off(self, built):
        """A dim cover keeps a tenth of the light.

        A flash that ran the whole luminance range still changes by 0.1 after
        dimming, which is exactly the WCAG general flash threshold, so dim
        cannot save that content. When the cover model fails on a plan that
        allows dim, verify says which switch to reach for.
        """
        built["analyzer"].flag(
            "cover_model_wcag.mp4", segments={"wcag": [[3100, 3300, "general"]]}
        )
        report = run_verify(built)
        failed = [c for c in report.failures if c.name == "cover_model_clean:wcag"]
        assert failed
        assert "--no-dim" in failed[0].detail
        assert failed[0].data["dim_intervals"] >= 1

    def test_an_opaque_only_plan_gets_no_such_hint(self, tmp_path, analyzer, keypair):
        private, public = keypair
        source = make_calm_clip(tmp_path / "clip.mp4", seconds=8.0)
        analyzer.flag("clip.mp4", segments={"wcag": FLAGGED})
        analyzer.flag(
            "cover_model_wcag.mp4", segments={"wcag": [[3100, 3300, "general"]]}
        )
        result = ingest_title(
            source,
            tmp_path / "out",
            IngestOptions(
                presets=["wcag"],
                key=str(private),
                pub=str(public),
                poster_count=2,
                bif_interval_ms=2000,
                x264_preset="ultrafast",
                allow_dim=False,
                skip_verify=True,
            ),
        )
        report = verify_title(
            result.layout,
            source=source,
            presets=["wcag"],
            adapter=FlashmapAdapter(),
            pub_key=public,
            rerender_cover_model=False,
        )
        failed = [c for c in report.failures if c.name == "cover_model_clean:wcag"]
        assert failed
        assert "--no-dim" not in failed[0].detail
        assert failed[0].data["dim_intervals"] == 0
