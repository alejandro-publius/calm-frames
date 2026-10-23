"""Synthetic contracts for the smoke runner, never device evidence."""
from __future__ import annotations

import copy
import json
import subprocess

import pytest

import benign_native_smoke as smoke


@pytest.fixture
def inventory():
    return {
        "source": "live-sdk-read-only", "explicit_target": True,
        "connected": True, "kind": "virtual", "in_developer_mode": True,
        "identity": {"architecture": "aarch64", "buildDescription": "Vega OS 1.2 (test/101520710)"},
    }


@pytest.fixture
def package():
    return {"ok": True, "architecture": "aarch64", "sha256": "synthetic-test",
            "captions_available": True, "scene_holds_available": True}


def event(kind, wall, media, **extra):
    return "native log CALM_TIMING " + json.dumps({
        "kind": kind, "wallClockMs": wall, "mediaTimeMs": media, **extra,
    })


def playback(uri=smoke.HARBOR_URI, offset=0):
    return "\n".join([
        smoke.LOAD_MARKER + uri,
        event("harness-start", 1000 + offset, None,
              extra={"scheduleLabel": "flash-guard:calm-frames-benign-story"}),
        event("playing", 1000 + offset, 0),
        event("timeupdate", 1100 + offset, 100),
        event("timeupdate", 1600 + offset, 600),
        event("timeupdate", 2200 + offset, 1200),
        event("cover-on", 6000 + offset, 5000, reason="interval 5000-9000"),
    ])


def test_current_harbor_clock_is_software_evidence_only():
    result = smoke.summarize_log(playback(), 1000, 7000)
    assert result["status"] == "software_playback_observed"
    assert result["scheduled_cover_event"]
    assert not result["composition_tested"]
    assert not result["household_durability_observed"]
    assert not result["physical_tv_validated"]
    assert not result["gate_1_passed"]


@pytest.mark.parametrize("log", [
    "notifyPlaybackStarted MediaPlayer:play resolved " + event("playing", 1000, 0),
    playback("https://example.invalid/not-harbor.mp4"),
    playback(offset=-10000),
    playback(offset=10000),
    playback().split(smoke.LOAD_MARKER + smoke.HARBOR_URI)[1],
    "\n".join([smoke.LOAD_MARKER + smoke.HARBOR_URI,
               event("harness-start", 1000, None,
                     extra={"scheduleLabel": "flash-guard:calm-frames-benign-story"}),
               event("playing", 1000, 0), event("timeupdate", 1100, 100),
               event("seeking", 1200, 8000), event("timeupdate", 1600, 8500),
               event("timeupdate", 2200, 9100)]),
])
def test_unrelated_stale_missing_or_seek_only_logs_are_inconclusive(log):
    assert smoke.summarize_log(log, 1000, 7000)["status"] == "inconclusive"


def test_duplicate_and_malformed_events_do_not_inflate_evidence():
    text = playback() + "\n" + playback() + "\nCALM_TIMING [1,2]\nCALM_TIMING {broken"
    assert smoke.summarize_log(text, 1000, 7000)["fresh_harbor_event_count"] == 5


def test_loading_a_different_title_closes_harbor_scope():
    log = smoke.LOAD_MARKER + smoke.HARBOR_URI + "\n" + playback("file:///different.mp4")
    assert smoke.summarize_log(log, 1000, 7000)["fresh_harbor_event_count"] == 0


def test_buffered_harbor_load_cannot_identify_a_new_different_guard_session():
    log = playback().replace("flash-guard:calm-frames-benign-story", "flash-guard:calm-frames-offline")
    assert smoke.summarize_log(log, 1000, 7000)["status"] == "inconclusive"


def test_crashes_and_media_errors_cannot_be_reported_as_success():
    for error in ("fatal signal", event("error", 3000, 2000)):
        assert smoke.summarize_log(playback() + "\n" + error, 1000, 7000)["status"] == "error_observed"


@pytest.mark.parametrize("field,value", [
    ("source", "saved-report"), ("explicit_target", False),
    ("connected", False), ("kind", "unknown"),
])
def test_refuses_unverified_or_ambiguous_targets(inventory, package, field, value):
    inventory[field] = value
    assert smoke.build_plan(inventory, package)["blockers"]


def test_refuses_architecture_mismatch_and_old_fixture(inventory, package):
    assert smoke.build_plan(inventory, package)["status"] == "ready_to_capture"
    package["architecture"] = "armv7"
    assert "package_device_architecture_mismatch" in smoke.build_plan(inventory, package)["blockers"]
    package["architecture"] = "aarch64"
    package["captions_available"] = False
    assert "reviewed_harbor_fixture_required" in smoke.build_plan(inventory, package)["blockers"]


def test_physical_target_keeps_checkpoint_and_pinned_os_guards(inventory, package):
    inventory["kind"] = "physical"
    result = smoke.build_plan(inventory, package)
    assert "human_checkpoint_b_required" in result["blockers"]
    assert "pinned_vega_os_1_2_build_required" in result["blockers"]
    inventory["identity"]["buildDescription"] = "Vega OS 1.2 (test/2101020054720)"
    result = smoke.build_plan(inventory, package, checkpoint_b_confirmed=True)
    assert not result["blockers"]
    assert not result["physical_tv_validated"]


def test_default_preflight_never_installs_or_launches(monkeypatch, inventory, package, tmp_path, capsys):
    monkeypatch.setattr(smoke, "collect_inventory", lambda device: inventory)
    monkeypatch.setattr(smoke, "inspect_package", lambda path: package)
    monkeypatch.setattr(smoke, "command", lambda *args, **kwargs: pytest.fail("unexpected mutation"))
    output = tmp_path / "capture"
    assert smoke.main(["--vpkg", "fixture.vpkg", "--device", "Simulator", "--output-dir", str(output)]) == 0
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["executed"] is False


def test_explicit_execute_still_refuses_disconnected_target(monkeypatch, inventory, package, tmp_path):
    inventory["connected"] = False
    monkeypatch.setattr(smoke, "collect_inventory", lambda device: inventory)
    monkeypatch.setattr(smoke, "inspect_package", lambda path: package)
    monkeypatch.setattr(smoke, "command", lambda *args, **kwargs: pytest.fail("unexpected mutation"))
    assert smoke.main(["--vpkg", "fixture.vpkg", "--device", "Simulator", "--execute",
                       "--output-dir", str(tmp_path / "capture")]) == 2


def test_changed_package_is_refused_before_install(monkeypatch, inventory, package, tmp_path):
    responses = iter([package, {**package, "sha256": "changed"}])
    monkeypatch.setattr(smoke, "collect_inventory", lambda device: copy.deepcopy(inventory))
    monkeypatch.setattr(smoke, "inspect_package", lambda path: next(responses))
    monkeypatch.setattr(smoke, "command", lambda *args, **kwargs: pytest.fail("unexpected mutation"))
    assert smoke.main(["--vpkg", "fixture.vpkg", "--device", "Simulator", "--execute",
                       "--output-dir", str(tmp_path / "capture")]) == 1
    report = json.loads((tmp_path / "capture/receipt.json").read_text())
    assert report["status"] == "capture_failed"
    assert not report["sessions"]


def test_sdk_zero_exit_with_failure_message_is_not_success(monkeypatch):
    monkeypatch.setattr(smoke.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess(args[0], 0, "Failed to launch: operation not permitted", ""))
    assert not smoke.command(["vega", "device", "launch-app"])


def test_restart_uses_explicit_target_and_never_clears_data(monkeypatch, inventory, package, tmp_path):
    monkeypatch.setattr(smoke, "collect_inventory", lambda device: inventory)
    monkeypatch.setattr(smoke, "inspect_package", lambda path: package)
    commands = []
    monkeypatch.setattr(smoke, "command", lambda argv: commands.append(argv) or True)
    captures = []
    monkeypatch.setattr(smoke, "capture", lambda device, path, seconds:
                        captures.append((device, path.name)) or {"status": "software_playback_observed"})
    assert smoke.main(["--vpkg", "fixture.vpkg", "--device", "Simulator", "--execute", "--restart",
                       "--output-dir", str(tmp_path / "capture")]) == 0
    assert [argv[2] for argv in commands] == ["install-app", "terminate-app"]
    assert all(argv[argv.index("--device") + 1] == "Simulator" for argv in commands)
    assert captures == [("Simulator", "first-launch.log"), ("Simulator", "restart.log")]
