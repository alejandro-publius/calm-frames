"""Synthetic SDK/tar contracts, not hardware or playback evidence."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import tarfile

import pytest

import benign_hardware_validation as hardware


@pytest.fixture
def physical():
    # Deliberately labelled synthetic inventory for guard assertions only.
    return {
        "source": "live-sdk-read-only", "explicit_target": True,
        "connected": True, "kind": "physical", "in_developer_mode": True,
        "identity": {
            "architecture": "armv7", "product": "synthetic-test-not-a-device",
            "buildDescription": "Vega OS 1.2 (test/2101020054720)",
        },
    }


@pytest.fixture
def package(tmp_path):
    destination = tmp_path / "armv7-debug" / "calm-frames-app_armv7.vpkg"
    destination.parent.mkdir()
    members = {
        hardware.VIDEO_MEMBER: (hardware.REPO / "app" / hardware.VIDEO_MEMBER).read_bytes(),
        hardware.MAP_MEMBER: (hardware.REPO / "app" / hardware.MAP_MEMBER).read_bytes(),
        "manifest.toml": b'[package]\nid = "io.github.alejandropublius.calmframes"\n',
        # Fake native bytes are used only to test the archive membership guard.
        "lib/armv7/com.amazon.keplerscript.carousel.so": b"synthetic-not-a-native-library",
    }
    def write(overrides=None, extra_members=()):
        data = dict(members)
        data.update(overrides or {})
        with tarfile.open(destination, "w:gz") as archive:
            for name, value in [*data.items(), *extra_members]:
                if value is not None:
                    member = tarfile.TarInfo(name)
                    member.size = len(value)
                    archive.addfile(member, io.BytesIO(value))
        return destination
    return write


@pytest.fixture
def story_package(package):
    members = {
        hardware.STORY_PREFIX + name:
            (hardware.REPO / "app" / hardware.STORY_PREFIX / name).read_bytes()
        for name in [*hardware.STORY_ASSET_NAMES, "verification.json"]
    }
    def write(overrides=None, extra_members=()):
        return package({**members, **(overrides or {})}, extra_members=extra_members)
    return write


def test_exact_bundled_bytes_allow_only_preflight_not_physical_proof(package, physical):
    checked = hardware.inspect_package(package())
    assert checked["ok"] is True
    plan = hardware.build_plan(physical, checked, checkpoint_b_confirmed=True)
    assert plan["status"] == "ready_for_human_reviewed_benign_smoke"
    assert plan["physical_tv_validated"] is False
    assert plan["composition_tested"] is False
    assert plan["gate_1_passed"] is False
    assert plan["installed"] is False and plan["launched"] is False
    assert checked["captions_available"] is False
    assert checked["scene_holds_available"] is False
    steps = {item["id"]: item["status"] for item in plan["steps"]}
    assert steps["caption_image_composition"] == "blocked_missing_fixture"
    assert steps["uncertainty_latch"] == "blocked_missing_fixture"
    assert steps["benign_launch_seek"] == "not_run"
    assert steps["camera_timing"] == "pending_human_checkpoint_e1"


def test_exact_story_assets_allow_composition_steps_but_never_physical_proof(
        story_package, physical):
    checked = hardware.inspect_package(story_package())
    assert checked["ok"] is True
    assert checked["benign_story_proof_sha256"] == hardware.STORY_PROOF_SHA256
    assert checked["captions_available"] is True
    assert checked["scene_holds_available"] is True
    assert checked["benign_story_uses_sham_intervals"] is True
    plan = hardware.build_plan(physical, checked, checkpoint_b_confirmed=True)
    assert plan["status"] == "ready_for_human_reviewed_benign_smoke"
    steps = {item["id"]: item for item in plan["steps"]}
    assert steps["caption_image_composition"]["status"] == "not_run"
    assert "practice holds, not detections" in steps["caption_image_composition"]["action"]
    assert steps["uncertainty_latch"]["status"] == "not_run"
    assert steps["camera_timing"]["status"] == "pending_human_checkpoint_e1"
    for key in ("physical_tv_validated", "composition_tested", "gate_1_passed",
                "installed", "launched"):
        assert plan[key] is False


@pytest.mark.parametrize("name", sorted(hardware.STORY_ASSET_NAMES | {"verification.json"}))
@pytest.mark.parametrize("replacement", [None, b"changed-unreviewed-story-bytes"])
def test_absent_or_changed_story_member_rejects_entire_package(
        story_package, name, replacement):
    checked = hardware.inspect_package(story_package({hardware.STORY_PREFIX + name: replacement}))
    assert checked["ok"] is False


def test_story_proof_cannot_authorize_itself_with_rewritten_hashes(story_package):
    proof = json.loads((hardware.REPO / "app" / hardware.STORY_PROOF_MEMBER).read_text())
    # A locally fabricated success record must not authorize different bytes.
    replacement = b"not-the-reviewed-caption"
    proof["assets_sha256"]["harbor.vtt"] = hashlib.sha256(replacement).hexdigest()
    proof["production_pipeline_passed"] = True
    checked = hardware.inspect_package(story_package({
        hardware.STORY_PREFIX + "harbor.vtt": replacement,
        hardware.STORY_PROOF_MEMBER: json.dumps(proof).encode(),
    }))
    assert checked["ok"] is False


@pytest.mark.parametrize("extra", ["unreviewed.mp4", "harbor.vtt"])
def test_extra_or_duplicate_story_archive_members_are_rejected(story_package, extra):
    path = story_package(extra_members=[(hardware.STORY_PREFIX + extra, b"unreviewed")])
    assert hardware.inspect_package(path)["ok"] is False


def test_claimed_caption_and_hold_availability_without_reviewed_proof_stays_unavailable(
        package, physical):
    checked = hardware.inspect_package(package())
    checked.update(captions_available=True, scene_holds_available=True)
    plan = hardware.build_plan(physical, checked, checkpoint_b_confirmed=True)
    assert plan["steps"][1]["status"] == "blocked_missing_fixture"
    assert plan["steps"][2]["status"] == "blocked_missing_fixture"


def test_failed_package_cannot_offer_composition_steps(story_package, physical):
    checked = hardware.inspect_package(story_package())
    checked["ok"] = False
    plan = hardware.build_plan(physical, checked, checkpoint_b_confirmed=True)
    assert plan["steps"][1]["status"] == "blocked_missing_fixture"
    assert plan["steps"][2]["status"] == "blocked_missing_fixture"


@pytest.mark.parametrize("field", ["captions_available", "scene_holds_available"])
@pytest.mark.parametrize("value", [False, "true"])
def test_story_availability_requires_confirmed_capabilities(story_package, physical, field, value):
    checked = hardware.inspect_package(story_package())
    checked[field] = value
    plan = hardware.build_plan(physical, checked, checkpoint_b_confirmed=True)
    assert plan["steps"][1]["status"] == "blocked_missing_fixture"
    assert plan["steps"][2]["status"] == "blocked_missing_fixture"


@pytest.mark.parametrize("field,value,blocker", [
    ("connected", False, "connected_physical_device_required"),
    ("connected", "true", "connected_physical_device_required"),
    ("kind", "virtual", "connected_physical_device_required"),
    ("kind", "unknown", "connected_physical_device_required"),
    ("source", "saved-device-info", "live_device_inventory_required"),
    ("explicit_target", False, "explicit_device_serial_required"),
    ("in_developer_mode", False, "developer_mode_confirmation_required"),
    ("in_developer_mode", "true", "developer_mode_confirmation_required"),
])
def test_physical_live_explicit_device_guards(package, physical, field, value, blocker):
    physical[field] = value
    plan = hardware.build_plan(physical, hardware.inspect_package(package()),
                               checkpoint_b_confirmed=True)
    assert plan["status"] == "blocked"
    assert blocker in plan["blockers"]


@pytest.mark.parametrize("description", [
    "", "Vega OS 1.1 (test/2101020054720)",
    "Vega OS 1.20 (test/2101020054720)", "Vega OS 1.2.3 (test/2101020054720)",
    "Vega OS 1.2-beta (test/2101020054720)", "Vega OS 1.2 (test/999999)",
])
def test_pinned_os_and_build_guard(package, physical, description):
    physical["identity"]["buildDescription"] = description
    plan = hardware.build_plan(physical, hardware.inspect_package(package()),
                               checkpoint_b_confirmed=True)
    assert "pinned_vega_os_1_2_build_required" in plan["blockers"]


def test_human_checkpoint_and_package_architecture_guards(package, physical):
    checked = hardware.inspect_package(package())
    plan = hardware.build_plan(physical, checked)
    assert "human_checkpoint_b_required" in plan["blockers"]
    physical["identity"]["architecture"] = "aarch64"
    plan = hardware.build_plan(physical, checked, checkpoint_b_confirmed=True)
    assert "package_device_architecture_mismatch" in plan["blockers"]
    plan = hardware.build_plan(physical, {"ok": False}, checkpoint_b_confirmed=True)
    assert "checked_benign_debug_package_required" in plan["blockers"]


@pytest.mark.parametrize("member,value", [
    (hardware.VIDEO_MEMBER, b"different-unreviewed-media"),
    (hardware.MAP_MEMBER, b"{}"),
    (hardware.MAP_MEMBER, None),
    ("manifest.toml", b'[package]\nid = "com.amazon.unrelated"\n'),
    ("lib/armv7/com.amazon.keplerscript.carousel.so", None),
    ("lib/armv7/com.amazon.keplerscript.carousel.so", b""),
])
def test_actual_package_asset_identity_and_membership_guards(package, member, value):
    checked = hardware.inspect_package(package({member: value}))
    assert checked["ok"] is False


def test_package_path_and_size_guards(package, tmp_path, monkeypatch):
    real = package()
    link = tmp_path / "linked" / "armv7-debug" / real.name
    link.parent.mkdir(parents=True)
    link.symlink_to(real)
    assert hardware.inspect_package(link)["ok"] is False
    assert hardware.inspect_package(tmp_path)["ok"] is False
    release = tmp_path / "armv7-release" / real.name
    release.parent.mkdir()
    release.write_bytes(real.read_bytes())
    assert hardware.inspect_package(release)["ok"] is False
    monkeypatch.setattr(hardware, "MAX_PACKAGE_BYTES", 1)
    assert hardware.inspect_package(real)["ok"] is False


def test_package_member_bound(package, monkeypatch):
    real = package()
    monkeypatch.setattr(hardware, "MAX_MEMBER_BYTES", 1)
    with pytest.raises(ValueError, match="exceeds preflight bound"):
        hardware._member(real, "manifest.toml")
    assert hardware.inspect_package(real)["ok"] is False


@pytest.mark.parametrize("value", [b'package = "bad"\n', b'package = ["bad"]\n',
                                  b'package = 1\n'])
def test_malformed_package_metadata_is_structured_blocked(package, value):
    path = package({"manifest.toml": value})
    try:
        checked = hardware.inspect_package(path)
    except Exception as exc:
        # A leaked parser exception must be assertion-red, never a blocked pass.
        checked = {"ok": type(exc).__name__}
    assert checked["ok"] is False


def test_changing_package_bytes_fail_preflight(package, monkeypatch):
    real = package()
    original = hardware._member
    def changed(path, member):
        value = original(path, member)
        if member.startswith("lib/"):
            with path.open("ab") as handle:
                handle.write(b"changed-during-read")
        return value
    monkeypatch.setattr(hardware, "_member", changed)
    assert hardware.inspect_package(real)["ok"] is False


@pytest.mark.parametrize("simulated,kind", [(True, "virtual"), (False, "physical"),
                                         (None, "unknown"), ("false", "unknown"), (0, "unknown")])
def test_inventory_requires_literal_physical_identity(monkeypatch, simulated, kind):
    commands = []
    info = {"simulated": simulated, "inDeveloperMode": True, "architecture": "armv7",
            "product": "synthetic", "account": "must-not-be-copied"}
    def reader(argv):
        commands.append(argv)
        if argv[1:3] == ["device", "info"]:
            return subprocess.CompletedProcess(argv, 0, json.dumps(info), "")
        if argv[1:3] == ["device", "is-connected"]:
            return subprocess.CompletedProcess(argv, 0, "Device TEST is connected", "")
        return subprocess.CompletedProcess(argv, 0, '{"running":false}', "")
    monkeypatch.setattr(hardware, "_read_command", reader)
    result = hardware.collect_inventory("TEST")
    assert result["kind"] == kind
    assert result["virtual_device_running"] is False
    assert "must-not-be-copied" not in json.dumps(result)
    assert commands == [
        ["vega", "device", "is-connected", "--device", "TEST"],
        ["vega", "device", "info", "--device", "TEST"],
        ["vega", "virtual-device", "status"],
    ]


@pytest.mark.parametrize("code,output", [(2, "Device TEST is connected"),
                                       (0, "Device TEST is not connected"), (0, "")])
def test_inventory_connection_command_must_succeed(monkeypatch, code, output):
    monkeypatch.setattr(hardware, "_read_command", lambda argv:
                        subprocess.CompletedProcess(argv, code, output, ""))
    assert hardware.collect_inventory("TEST")["connected"] is False


def test_missing_cli_and_timeout_fail_closed(monkeypatch):
    def missing(argv):
        raise FileNotFoundError("synthetic missing tool")
    monkeypatch.setattr(hardware, "_read_command", missing)
    result = hardware.collect_inventory()
    assert result["kind"] == "none" and result["connected"] is False
    def timeout(argv):
        raise subprocess.TimeoutExpired(argv, 15)
    monkeypatch.setattr(hardware, "_read_command", timeout)
    assert hardware.collect_inventory("TEST")["connected"] is False


def test_cli_no_device_reports_actual_missing_fixture_and_no_install_commands(
        package, monkeypatch, capsys):
    monkeypatch.setattr(hardware, "collect_inventory", lambda device: {
        "source": "live-sdk-read-only", "connected": False, "kind": "none",
        "explicit_target": False, "identity": {},
    })
    assert hardware.main(["--vpkg", str(package())]) == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "blocked"
    assert "connected_physical_device_required" in receipt["blockers"]
    assert receipt["steps"][1]["status"] == "blocked_missing_fixture"
    assert "after_root_acknowledgement_only" not in receipt
    assert receipt["physical_tv_validated"] is False


def test_cli_safe_commands_are_targeted_and_only_printed(package, physical, monkeypatch, capsys):
    monkeypatch.setattr(hardware, "collect_inventory", lambda device: copy.deepcopy(physical))
    def no_sdk_writes(argv):
        raise AssertionError("preflight must not execute install/launch commands")
    monkeypatch.setattr(hardware, "_read_command", no_sdk_writes)
    path = package()
    assert hardware.main(["--vpkg", str(path), "--device", "TEST",
                          "--checkpoint-b-confirmed"]) == 0
    result = json.loads(capsys.readouterr().out)
    commands = result["after_root_acknowledgement_only"]
    assert commands[0] == ["vega", "device", "install-app", "--device", "TEST",
                           "--packagePath", str(path), "--buildType", "Debug"]
    assert commands[1][-1] == hardware.PACKAGE_ID + ".main"
    assert result["installed"] is False and result["launched"] is False


@pytest.mark.parametrize("serial", ["", "-all", "Simulator;reboot", "a b", "x\nreboot"])
def test_serial_cannot_inject_or_select_an_ambiguous_target(serial):
    with pytest.raises(ValueError):
        hardware._serial(serial)
