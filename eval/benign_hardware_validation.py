"""Read-only physical-TV preflight; no install, launch, playback or gate result.

    .venv/bin/python eval/benign_hardware_validation.py --vpkg \
        app/build/armv7-debug/calm-frames-app_armv7.vpkg

After HUMAN CHECKPOINT B, repeat with --device SERIAL --checkpoint-b-confirmed.
The optional commands in the receipt are for a human-reviewed benign smoke
session only. The existing bundled clip cannot test caption/scene-hold layering.
Saved device reports and virtual-device software results are not physical proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
from threading import Timer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGE_ID = "io.github.alejandropublius.calmframes"
REQUIRED_BUILD = "2101020054720"
VIDEO_MEMBER = "assets/raw/offline/calm_gradient.mp4"
MAP_MEMBER = "assets/raw/offline/calm_gradient.flashmap.json"
# The reviewed, non-hazardous bundled fixture. Updating it requires new proof.
BENIGN_SHA256 = "af2934dc45c9519bcace8db253d0a9e0c10f9db6682a04ad2cf3f906e1755224"
MAP_SHA256 = "28dff7b168b97d7c31c010ffeb0bf7cbde9c66f0d7f5da7132dfb8fbe896bd4f"
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
MAX_MEMBER_BYTES = 8 * 1024 * 1024


def _serial(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value):
        raise ValueError("device must be an explicit configured serial, not a shell command")
    return value


def _read_command(arguments: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(arguments, capture_output=True, text=True, timeout=15)


def collect_inventory(device: str | None = None) -> dict:
    """Ask the existing SDK connection only. Never connect, scan, start or reset."""
    target = ["--device", _serial(device)] if device is not None else []
    commands = {
        "connection": ["vega", "device", "is-connected", *target],
        "identity": ["vega", "device", "info", *target],
        "virtual_device": ["vega", "virtual-device", "status"],
    }
    results = {}
    for name, command in commands.items():
        try:
            result = _read_command(command)
            results[name] = (result.returncode, result.stdout)
        except (OSError, subprocess.TimeoutExpired):
            results[name] = (None, "")
    info = {}
    try:
        raw = results["identity"][1]
        parsed = json.loads(raw[raw.index("{"):])
        if results["identity"][0] == 0 and isinstance(parsed, dict):
            info = parsed
    except (ValueError, json.JSONDecodeError):
        pass
    connected = results["connection"][0] == 0 and bool(
        re.search(r"\bis connected\b", results["connection"][1])
    )
    simulated = info.get("simulated")
    kind = "none" if not connected else (
        "virtual" if simulated is True else "physical" if simulated is False else "unknown"
    )
    # No device serials, account fields, full stderr or unbounded SDK metadata.
    selected = {}
    for name in ("architecture", "product", "buildDescription"):
        value = info.get(name)
        selected[name] = value[:256] if isinstance(value, str) else None
    virtual_running = None
    try:
        raw = results["virtual_device"][1]
        start = raw.index("{")
        parsed = json.loads(raw[start:])
        if results["virtual_device"][0] == 0 and isinstance(parsed, dict):
            value = parsed.get("running")
            virtual_running = value if type(value) is bool else None
    except (ValueError, json.JSONDecodeError):
        pass
    return {
        "source": "live-sdk-read-only",
        "explicit_target": device is not None,
        "connected": connected,
        "kind": kind,
        "in_developer_mode": info.get("inDeveloperMode") is True,
        "identity": selected,
        "virtual_device_running": virtual_running,
        "command_exit_codes": {name: result[0] for name, result in results.items()},
    }


def _member(package: Path, name: str) -> bytes:
    """Read one fixed member, without extracting files or following its paths."""
    # System tar supports the SDK's zstd package and ordinary test tar archives.
    # Limit the stream before retaining it, and kill an oversized member reader.
    process = subprocess.Popen(
        ["tar", "-xOf", str(package), name], stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    def stop_reader() -> None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    watchdog = Timer(15, stop_reader)
    watchdog.daemon = True
    watchdog.start()
    try:
        assert process.stdout is not None
        data = process.stdout.read(MAX_MEMBER_BYTES + 1)
        if len(data) > MAX_MEMBER_BYTES:
            raise ValueError("package member exceeds preflight bound")
        if process.wait(timeout=15) != 0:
            raise ValueError("package is missing a required bundled member")
        return data
    finally:
        watchdog.cancel()
        if process.poll() is None:
            process.kill()
        process.wait()
        if process.stdout is not None:
            process.stdout.close()


def inspect_package(package: Path) -> dict:
    """Bind a plan to actual package bytes and the exact reviewed benign assets."""
    try:
        mode = package.lstat().st_mode
        if not stat.S_ISREG(mode) or package.stat().st_size > MAX_PACKAGE_BYTES:
            raise ValueError("package must be a bounded regular file")
        architecture = next((arch for arch in ("armv7", "aarch64", "x86_64")
                             if package.name == f"calm-frames-app_{arch}.vpkg"), None)
        if architecture is None or package.parent.name != f"{architecture}-debug":
            raise ValueError("use the named native Debug package")
        before = package.stat()
        digest = hashlib.sha256()
        with package.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        video = _member(package, VIDEO_MEMBER)
        map_bytes = _member(package, MAP_MEMBER)
        if (hashlib.sha256(video).hexdigest() != BENIGN_SHA256
                or hashlib.sha256(map_bytes).hexdigest() != MAP_SHA256):
            raise ValueError("package does not contain the exact reviewed benign fixture")
        manifest = _member(package, "manifest.toml").decode("utf-8")
        import tomllib
        parsed = tomllib.loads(manifest)
        package_metadata = parsed.get("package")
        if not isinstance(package_metadata, dict) or package_metadata.get("id") != PACKAGE_ID:
            raise ValueError("package identity does not match Calm Frames")
        if not _member(package, f"lib/{architecture}/com.amazon.keplerscript.carousel.so"):
            raise ValueError("package architecture member is empty")
        after = package.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("package changed during preflight")
        return {
            "ok": True, "file": package.name, "architecture": architecture,
            "sha256": digest.hexdigest(), "benign_video_sha256": BENIGN_SHA256,
            "bundled_map_sha256": MAP_SHA256,
            "captions_available": False, "scene_holds_available": False,
        }
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        return {"ok": False, "problem": "package/benign asset identity preflight failed"}


def build_plan(inventory: dict, package: dict, *, checkpoint_b_confirmed: bool = False) -> dict:
    """Preflight is not a screen observation, timing measurement or clinical claim."""
    blockers = []
    if inventory.get("source") != "live-sdk-read-only":
        blockers.append("live_device_inventory_required")
    if inventory.get("connected") is not True or inventory.get("kind") != "physical":
        blockers.append("connected_physical_device_required")
    if inventory.get("explicit_target") is not True:
        blockers.append("explicit_device_serial_required")
    identity = inventory.get("identity", {})
    description = identity.get("buildDescription") or ""
    if not re.search(r"\bOS\s+1\.2(?=\s|$)", description) or not re.search(
            rf"/{REQUIRED_BUILD}\)", description):
        blockers.append("pinned_vega_os_1_2_build_required")
    if inventory.get("in_developer_mode") is not True:
        blockers.append("developer_mode_confirmation_required")
    if checkpoint_b_confirmed is not True:
        blockers.append("human_checkpoint_b_required")
    if package.get("ok") is not True:
        blockers.append("checked_benign_debug_package_required")
    elif identity.get("architecture") != package.get("architecture"):
        blockers.append("package_device_architecture_mismatch")
    return {
        "version": 1, "mode": "read-only-benign-hardware-preflight",
        "status": "blocked" if blockers else "ready_for_human_reviewed_benign_smoke",
        "inventory": inventory, "package": package, "blockers": blockers,
        "physical_tv_validated": False, "composition_tested": False,
        "gate_1_passed": False, "installed": False, "launched": False,
        "human_checkpoint_b": "operator_confirmed" if checkpoint_b_confirmed else "pending",
        "steps": [
            {"id": "benign_launch_seek", "status": "not_run",
             "action": "After root acknowledgement, install this exact package on the named "
                       "physical target. Manually choose Calm gradient (bundled), then pause, "
                       "resume, rewind and seek with the remote. Record crashes and black screens."},
            {"id": "caption_image_composition", "status": "blocked_missing_fixture",
             "action": "The bundled clip has audio but no captions or scheduled scene images. "
                       "Prepare and explicitly integrate a checked benign captioned fixture "
                       "with labelled sham intervals before this test. Film opaque backing, "
                       "image aspect ratio and readable captions while listening for audio gaps."},
            {"id": "uncertainty_latch", "status": "blocked_missing_fixture",
             "action": "On that benign fixture, pause/resume and seek into/back into a hold. "
                       "The interrupted hold must stay black; a later clean hold may use its image."},
            {"id": "camera_timing", "status": "pending_human_checkpoint_e1",
             "action": "Use a physical TV in game mode, smoothing off, and one continuous "
                       "240fps capture with locked exposure/focus and HDR off. Preserve all "
                       "50 benign trials and analyze screen footage, not the scheduler's clock."},
        ],
        "restrictions": [
            "Never play hazard media or unfiltered real flagged footage.",
            "No simulator screenshot, software event log or this receipt is physical-TV proof.",
            "Do not run stick_day unchanged on hardware: its runner uses QEMU host/QMP paths.",
            "No AWS, device reset, LAN scan, automatic install or autoplay is performed.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vpkg", type=Path, required=True)
    parser.add_argument("--device", type=_serial)
    parser.add_argument("--checkpoint-b-confirmed", action="store_true")
    args = parser.parse_args(argv)
    package_path = args.vpkg.absolute()
    plan = build_plan(collect_inventory(args.device), inspect_package(package_path),
                      checkpoint_b_confirmed=args.checkpoint_b_confirmed)
    # Proposed argv awaiting root acknowledgement, never executed here.
    # No default/ambiguous target is printed.
    if not plan["blockers"]:
        plan["after_root_acknowledgement_only"] = [
            ["vega", "device", "install-app", "--device", args.device,
             "--packagePath", str(package_path), "--buildType", "Debug"],
            ["vega", "device", "launch-app", "--device", args.device,
             "--appName", PACKAGE_ID + ".main"],
        ]
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 2 if plan["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
