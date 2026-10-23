"""Test refusal boundaries without generating or opening any media."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("render_demo", HERE / "render_demo.py")
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


def fake_probe(path):
    duration = "400" if "native" in path.name else "1"
    return {"format": {"duration": duration}, "streams": [
        {"codec_type": "video", "start_time": "0", "duration": duration},
        {"codec_type": "audio", "start_time": "0", "duration": duration},
    ]}


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.plan = json.loads((HERE / "timeline.json").read_text())
        self.plan["approvals"]["script_sha256"] = self.plan["narration_script_sha256"]
        self.plan["approvals"]["authorized_voice_id"] = "test-voice-not-a-real-authorization"
        self.plan["package_sha256"] = "a" * 64
        for name, asset in self.plan["assets"].items():
            path = self.directory / name
            path.write_bytes(b"Non-media fixture: no recording or picture.")
            asset.update(path=str(path), sha256=render.digest(path), provenance_reviewed=True)
            if asset["kind"] == "native_video":
                asset["production_capture"] = True
                asset["package_sha256"] = self.plan["package_sha256"]
                receipt = self.directory / (name + ".json")
                receipt.write_text(json.dumps({
                    "source_commit": self.plan["source_commit"],
                    "package_sha256": self.plan["package_sha256"],
                    "raw_take_sha256": asset["sha256"],
                    "capture_scope": "app_window_and_app_audio_only",
                    "production_capture": True,
                }))
                asset["capture_receipt_path"] = str(receipt)
                asset["capture_receipt_sha256"] = render.digest(receipt)
            if asset["kind"] == "narration":
                asset["authorized_voice_id"] = self.plan["approvals"]["authorized_voice_id"]

    def tearDown(self):
        self.temp.cleanup()

    def errors(self):
        return render.validate(self.plan, fake_probe)[0]

    def test_complete_metadata_reaches_input_validation(self):
        self.assertEqual(self.errors(), [])

    def test_changed_bytes_are_rejected(self):
        Path(self.plan["assets"]["native_ambient"]["path"]).write_bytes(b"Different bytes")
        self.assertTrue(any("byte hash" in e for e in self.errors()))

    def test_harness_or_unreviewed_capture_is_rejected(self):
        self.plan["assets"]["native_return"]["production_capture"] = False
        self.assertTrue(any("raw production take" in e for e in self.errors()))

    def test_wrong_installed_package_or_changed_receipt_is_rejected(self):
        self.plan["assets"]["native_home"]["package_sha256"] = "b" * 64
        Path(self.plan["assets"]["native_details"]["capture_receipt_path"]).write_text("{}")
        errors = self.errors()
        self.assertTrue(any("installed package differs" in e for e in errors))
        self.assertTrue(any("capture receipt is missing" in e for e in errors))

    def test_stale_source_and_illustration_in_native_slot_are_rejected(self):
        self.plan["assets"]["native_home"]["source_commit"] = "d" * 40
        self.plan["assets"]["native_return"]["kind"] = "illustration"
        errors = self.errors()
        self.assertTrue(any("capture source differs" in e for e in errors))
        self.assertTrue(any("native slot cannot" in e for e in errors))

    def test_unapproved_text_or_voice_is_rejected(self):
        self.plan["narration_cues"][0]["text"] += " Changed."
        self.plan["assets"]["n01"]["authorized_voice_id"] = "different-voice"
        errors = self.errors()
        self.assertTrue(any("Narration text no longer" in e for e in errors))
        self.assertTrue(any("voice differs" in e for e in errors))

    def test_short_take_and_long_narration_are_rejected(self):
        def probe_lengths(path):
            data = fake_probe(path)
            for stream in data["streams"]:
                stream["duration"] = "1" if "native" in path.name else "400"
            return data
        errors = render.validate(self.plan, probe_lengths)[0]
        self.assertTrue(any("take is too short" in e for e in errors))
        self.assertTrue(any("speech exceeds" in e for e in errors))

    def test_long_container_and_second_video_do_not_cover_short_first_video(self):
        def probe_short_video(path):
            data = fake_probe(path)
            if path.name == "native_ambient":
                data["streams"][0]["duration"] = "1"
                data["streams"].append({"codec_type": "video", "start_time": "0", "duration": "400"})
            return data
        errors = render.validate(self.plan, probe_short_video)[0]
        self.assertTrue(any("native_ambient: first mapped video stream take is too short" in e for e in errors))

    def test_long_container_and_second_audio_do_not_cover_short_first_audio(self):
        def probe_short_audio(path):
            data = fake_probe(path)
            if path.name == "native_ambient":
                data["streams"][1]["duration"] = "1"
                data["streams"].append({"codec_type": "audio", "start_time": "0", "duration": "400"})
            return data
        errors = render.validate(self.plan, probe_short_audio)[0]
        self.assertTrue(any("native_ambient: first mapped audio stream take is too short" in e for e in errors))

    def test_unknown_or_nonfinite_stream_coverage_is_rejected(self):
        for stream_index in (0, 1):
            for duration in (None, "N/A", "nan", "inf", "0", "-1"):
                with self.subTest(stream=stream_index, duration=duration):
                    def probe_unknown(path):
                        data = fake_probe(path)
                        if path.name == "native_ambient":
                            data["streams"][stream_index]["duration"] = duration
                        return data
                    errors = render.validate(self.plan, probe_unknown)[0]
                    stream_type = "video" if stream_index == 0 else "audio"
                    self.assertTrue(any(f"native_ambient: first mapped {stream_type} stream requires finite positive coverage" in e for e in errors))

    def test_exact_tick_coverage_and_zero_origin_are_supported(self):
        def probe_ticks(path):
            data = fake_probe(path)
            for stream in data["streams"]:
                duration = int(stream.pop("duration"))
                stream.pop("start_time")
                stream.update(duration_ts=duration * 48000, time_base="1/48000", start_pts=0)
            return data
        errors, measured = render.validate(self.plan, probe_ticks)
        self.assertEqual(errors, [])
        self.assertEqual(measured["native_ambient"]["video_duration"], 400)
        self.assertEqual(measured["native_ambient"]["audio_duration"], 400)

    def test_nonzero_or_unknown_stream_origins_are_rejected(self):
        for stream_index in (0, 1):
            for origin in (None, "N/A", "0.1", "-0.1", "nan", "inf"):
                with self.subTest(stream=stream_index, origin=origin):
                    def probe_offset(path):
                        data = fake_probe(path)
                        if path.name == "native_ambient":
                            data["streams"][stream_index]["start_time"] = origin
                        return data
                    errors = render.validate(self.plan, probe_offset)[0]
                    self.assertTrue(any("native_ambient: first mapped" in e and "known zero start" in e for e in errors))

    def test_selected_interval_must_fit_both_mapped_streams(self):
        ambient = next(s for s in self.plan["segments"] if s["asset"] == "native_ambient")
        ambient["source_start"] = 331
        errors = self.errors()
        self.assertTrue(any("native_ambient: first mapped video stream take is too short" in e for e in errors))
        self.assertTrue(any("native_ambient: first mapped audio stream take is too short" in e for e in errors))
        ambient["source_start"] = 330
        self.assertEqual(self.errors(), [])

    def test_shorter_reported_duration_is_the_coverage_limit(self):
        def probe_conflict(path):
            data = fake_probe(path)
            if path.name == "native_ambient":
                data["streams"][0].update(duration_ts=30, time_base="1/30", start_pts=0)
            return data
        errors = render.validate(self.plan, probe_conflict)[0]
        self.assertTrue(any("native_ambient: first mapped video stream take is too short" in e for e in errors))

    def test_breathing_room_and_sub_three_minute_limit_are_enforced(self):
        self.plan["duration_seconds"] = 180
        self.plan["narration_cues"][3]["end"] = 46
        errors = self.errors()
        self.assertTrue(any("strictly below 180" in e for e in errors))
        self.assertTrue(any("Narration cannot cover" in e for e in errors))

    def test_missing_real_inputs_refuse_before_output_is_created(self):
        target = self.directory / "must-not-exist"
        result = subprocess.run([
            sys.executable, str(HERE / "render_demo.py"),
            "--manifest", str(HERE / "timeline.json"), "--render", "--outdir", str(target),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(target.exists())
        self.assertIn("actual absolute local file is missing", result.stdout)


if __name__ == "__main__":
    unittest.main()
