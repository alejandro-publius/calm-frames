"""The boundary to the analyzer.

docs/SIDECAR_SPEC.md version 1 is the contract. These tests pin both halves of
it: what this reader accepts, and what it must never quietly accept. The rules
the spec sets for readers (fail closed, hide start_ms to end_ms, ignore
unknown keys, refuse another version) each have a test here.
"""

from __future__ import annotations

import json

import pytest

from pipeline import PipelineError
from pipeline.flashmap_adapter import (
    GENERAL,
    PRESET_SPECS,
    PRESETS,
    RED,
    FlashmapAdapter,
    FlashmapFailed,
    MapFormatError,
    iter_presets,
    load_map,
    normalise_reason,
    parse_map,
)


class TestMapReading:
    def test_reads_the_documented_shape(self):
        doc = parse_map(
            {
                "version": 1,
                "source_sha256": "a" * 64,
                "profile": "wcag",
                "segments": [{"start_ms": 1000, "end_ms": 1500, "reason": "general"}],
            }
        )
        assert doc.version == 1
        assert doc.source_sha256 == "a" * 64
        assert doc.profile == "wcag"
        assert doc.violation_count == 1
        assert doc.segments[0].reason == GENERAL

    def test_an_empty_segment_list_is_clean(self):
        doc = parse_map({"version": 1, "source_sha256": "a" * 64, "segments": []})
        assert doc.is_clean
        assert doc.violation_count == 0

    def test_segments_come_back_in_time_order(self):
        doc = parse_map(
            {
                "segments": [
                    {"start_ms": 9000, "end_ms": 9500},
                    {"start_ms": 1000, "end_ms": 1500},
                ]
            }
        )
        assert [s.start_ms for s in doc.segments] == [1000, 9000]

    def test_a_map_with_no_segment_list_is_an_error_not_an_empty_list(self):
        # This is the one that matters: a map we cannot read must never look
        # like a title with nothing wrong with it.
        with pytest.raises(MapFormatError):
            parse_map({"version": 1, "source_sha256": "a" * 64})

    def test_a_segment_with_no_times_is_an_error(self):
        with pytest.raises(MapFormatError):
            parse_map({"segments": [{"reason": "red"}]})

    def test_a_segment_that_ends_before_it_starts_is_an_error(self):
        with pytest.raises(MapFormatError):
            parse_map({"segments": [{"start_ms": 2000, "end_ms": 1000}]})

    def test_a_missing_file_is_an_error(self, tmp_path):
        with pytest.raises(MapFormatError):
            load_map(tmp_path / "nothing.json")

    def test_a_file_that_is_not_json_is_an_error(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("{not json")
        with pytest.raises(MapFormatError):
            load_map(path)

    def test_the_version_one_shape_from_the_spec_is_read(self):
        doc = parse_map(
            {
                "schema": "https://calm-frames.github.io/schemas/flashmap-map-v1.json",
                "version": 1,
                "source": {"path": "clip.mkv", "sha256": "D" * 64, "size_bytes": 5797},
                "profile": {"name": "wcag", "flash_limit_per_second": 3},
                "segments": [
                    {
                        "start_ms": 0,
                        "end_ms": 1450,
                        "flash_first_ms": 100,
                        "flash_last_ms": 1400,
                        "reason": "general",
                        "area_fraction": 1.0,
                        "breaks_baseline": True,
                    }
                ],
                "summary": {"pass": False, "segment_count": 1},
            }
        )
        assert doc.source_sha256 == "d" * 64
        assert doc.profile == "wcag"
        # The interval to hide, not the tight span of the flashes themselves.
        assert (doc.segments[0].start_ms, doc.segments[0].end_ms) == (0, 1450)

    def test_unknown_keys_are_ignored_rather_than_refused(self):
        doc = parse_map(
            {
                "version": 1,
                "source": {"sha256": "a" * 64},
                "segments": [{"start_ms": 0, "end_ms": 10, "some_new_key": 7}],
                "a_key_from_a_later_release": {"anything": True},
            }
        )
        assert doc.violation_count == 1

    def test_another_version_is_refused_rather_than_guessed_at(self):
        with pytest.raises(MapFormatError):
            parse_map({"version": 2, "source": {"sha256": "a" * 64}, "segments": []})

    def test_a_summary_that_contradicts_the_segments_is_refused(self):
        with pytest.raises(MapFormatError):
            parse_map(
                {
                    "version": 1,
                    "source": {"sha256": "a" * 64},
                    "segments": [],
                    "summary": {"pass": False},
                }
            )

    def test_older_spellings_still_read(self):
        doc = parse_map(
            {
                "version": 1,
                "sha256": "C" * 64,
                "preset": "broadcast",
                "flashes": [{"start": 10, "end": 20, "kind": "red_flash"}],
            }
        )
        assert doc.source_sha256 == "c" * 64
        assert doc.profile == "broadcast"
        assert doc.segments[0].reason == RED

    def test_signature_is_reported(self, tmp_path):
        path = tmp_path / "map.json"
        path.write_text(
            json.dumps({"segments": [], "signature": {"alg": "ed25519", "value": "x"}})
        )
        assert load_map(path).is_signed

    def test_a_map_with_no_signature_says_so(self):
        assert not parse_map({"segments": []}).is_signed


class TestReasonNormalising:
    @pytest.mark.parametrize("value", ["general", "GENERAL", "general_flash", "luminance"])
    def test_general_spellings(self, value):
        assert normalise_reason(value) == GENERAL

    @pytest.mark.parametrize("value", ["red", "Red", "saturated_red", "red-flash"])
    def test_red_spellings(self, value):
        assert normalise_reason(value) == RED

    def test_an_unknown_reason_is_treated_as_red(self):
        # Red is the strict reading: always an opaque cover. Guessing red can
        # only ever hide more, never less.
        assert normalise_reason("something new") == RED

    def test_a_missing_reason_is_treated_as_red(self):
        assert normalise_reason(None) == RED


class TestPresets:
    def test_the_three_presets(self):
        assert PRESETS == ("wcag", "broadcast", "extra-cautious")

    def test_no_presets_means_all_of_them(self):
        assert iter_presets(None) == list(PRESETS)

    def test_an_unknown_preset_is_refused(self):
        with pytest.raises(PipelineError):
            iter_presets(["wcag", "whatever"])


class TestAdapterCommandLine:
    def test_the_command_comes_from_the_environment(self, analyzer):
        adapter = FlashmapAdapter()
        assert "fake_flashmap.py" in adapter.describe()
        assert adapter.available()

    def test_analyze_writes_a_map_the_reader_understands(self, analyzer, tmp_path):
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"not really a video, the fake analyzer only hashes it")
        analyzer.flag("clip.mp4", segments={"wcag": [[1000, 1500, "general"]]})

        adapter = FlashmapAdapter()
        doc = adapter.analyze(
            video, profile="wcag", out_path=tmp_path / "map.json", diag_in=55
        )
        assert doc.violation_count == 1
        assert doc.profile == "wcag"
        assert (tmp_path / "map.json").exists()

    def test_the_room_settings_are_passed_through(self, analyzer, tmp_path):
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"x")
        adapter = FlashmapAdapter()
        adapter.analyze(
            video,
            profile="wcag",
            out_path=tmp_path / "map.json",
            diag_in=55,
            distance_ft=8,
        )
        written = json.loads((tmp_path / "map.json").read_text())
        assert written["profile"]["room"] == {
            "tv_diagonal_in": 55.0,
            "seat_distance_in": 8.0,
        }

    def test_extra_cautious_is_the_wcag_rules_in_a_room_window(self, analyzer, tmp_path):
        # The analyzer has two profiles. The third preset is the WCAG rules
        # measured for a big television at close seating, which can only add
        # hides, never remove them.
        spec = PRESET_SPECS["extra-cautious"]
        assert spec.profile == "wcag"
        assert spec.is_room_preset

        video = tmp_path / "clip.mp4"
        video.write_bytes(b"x")
        adapter = FlashmapAdapter()
        doc = adapter.analyze(
            video, profile="extra-cautious", out_path=tmp_path / "map.json"
        )
        written = json.loads((tmp_path / "map.json").read_text())
        assert written["profile"]["name"] == "wcag"
        assert written["profile"]["room"]["tv_diagonal_in"] == spec.diag_in
        assert doc.preset == "extra-cautious"

    def test_a_map_for_the_wrong_rule_set_is_refused(self, analyzer, tmp_path):
        # If the analyzer answers for a different profile than the one that
        # was asked for, the map says nothing about this preset.
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"x")
        analyzer.plan["force_profile"] = "broadcast"
        analyzer.write()
        adapter = FlashmapAdapter()
        with pytest.raises(FlashmapFailed) as caught:
            adapter.analyze(video, profile="wcag", out_path=tmp_path / "map.json")
        assert "profile" in str(caught.value)

    def test_content_over_the_thresholds_is_an_answer_not_a_crash(self, analyzer, tmp_path):
        # flashmap exits 1 when a file is over the thresholds. That is the
        # normal case for the content this project exists for, so treating a
        # non zero exit as a crash would throw away every map that found
        # something.
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"x")
        analyzer.flag("clip.mp4", segments={"wcag": [[1000, 1500, "general"]]})
        adapter = FlashmapAdapter()
        doc = adapter.analyze(video, profile="wcag", out_path=tmp_path / "map.json")
        assert doc.violation_count == 1
        assert analyzer.calls("analyze")

    def test_an_exit_code_that_disagrees_with_the_map_is_refused(self, analyzer, tmp_path):
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"x")
        analyzer.flag("clip.mp4", segments={"wcag": [[1000, 1500, "general"]]})
        analyzer.plan["force_exit"] = 0  # says clean, writes a segment
        analyzer.write()
        adapter = FlashmapAdapter()
        with pytest.raises(FlashmapFailed) as caught:
            adapter.analyze(video, profile="wcag", out_path=tmp_path / "map.json")
        assert "exited 0" in str(caught.value)

    def test_an_error_exit_is_still_a_failure(self, analyzer, tmp_path):
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"x")
        analyzer.plan["force_exit"] = 2
        analyzer.write()
        adapter = FlashmapAdapter()
        with pytest.raises(FlashmapFailed):
            adapter.analyze(video, profile="wcag", out_path=tmp_path / "map.json")

    def test_an_analyzer_failure_is_raised_not_swallowed(self, analyzer, tmp_path):
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"x")
        analyzer.fail_on("clip.mp4", "the decoder gave up")
        adapter = FlashmapAdapter()
        with pytest.raises(FlashmapFailed) as caught:
            adapter.analyze(video, profile="wcag", out_path=tmp_path / "map.json")
        assert "the decoder gave up" in str(caught.value)

    def test_an_analyzer_that_cannot_start_is_reported(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CALM_FRAMES_FLASHMAP_CMD", "/nonexistent/flashmap")
        adapter = FlashmapAdapter()
        assert not adapter.available()

    def test_signing_and_verifying_a_map(self, analyzer, keypair, tmp_path):
        private, public = keypair
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"pretend video bytes")
        adapter = FlashmapAdapter()
        doc = adapter.analyze(
            video, profile="wcag", out_path=tmp_path / "map.json", key=private
        )
        assert doc.is_signed
        assert adapter.verify(tmp_path / "map.json", video, pub_key=public).ok

    def test_verify_refuses_a_tampered_map(self, analyzer, keypair, tmp_path):
        private, public = keypair
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"pretend video bytes")
        analyzer.flag("clip.mp4", segments={"wcag": [[1000, 1500, "red"]]})
        adapter = FlashmapAdapter()
        map_path = tmp_path / "map.json"
        doc = adapter.analyze(video, profile="wcag", out_path=map_path, key=private)
        assert doc.violation_count == 1

        # Someone deletes the flagged span from a signed map.
        data = json.loads(map_path.read_text())
        data["segments"] = []
        map_path.write_text(json.dumps(data))

        assert not adapter.verify(map_path, video, pub_key=public).ok

    def test_verify_refuses_a_map_bound_to_another_file(self, analyzer, keypair, tmp_path):
        private, public = keypair
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"pretend video bytes")
        other = tmp_path / "other.mp4"
        other.write_bytes(b"a different film entirely")
        adapter = FlashmapAdapter()
        map_path = tmp_path / "map.json"
        adapter.analyze(video, profile="wcag", out_path=map_path, key=private)

        assert not adapter.verify(map_path, other, pub_key=public).ok
