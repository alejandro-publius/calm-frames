"""Preflight and capture the current household/Harbor native smoke journey.

Run from a terminal with ``source ~/vega/env``. Default is read-only:
  .venv/bin/python -m eval.benign_native_smoke --device Simulator \
    --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg

Add --execute to install, launch and capture fresh device logs while operating
the visible app. Add --restart to capture a second launch without clearing data.
A physical target also needs --checkpoint-b-confirmed. This runner never starts
or resets a simulator, guesses D-pad focus, serves media, or claims camera proof.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.benign_hardware_validation import (
    PACKAGE_ID, REPO, _serial, build_plan as physical_plan,
    collect_inventory, inspect_package,
)

HARBOR_URI = "file:///pkg/assets/raw/benign-story/harbor.precovered.mp4"
LOAD_MARKER = "[VideoHandler.ts] - loadStaticMediaPlayer - Loading static player with: "
MAX_LOG_BYTES = 32 * 1024 * 1024
JOURNEY = [
    "If first run appears, choose and confirm your own PIN, then finish preset, room and explanation. "
    "If settings already exist, keep them; never reset data to make this check pass.",
    "On the checked shelf, open Harbor story (benign demo). Read its fixed Extra cautious "
    "practice plan, then choose Play. Do not open a different title.",
    "Open captions and select English practice captions. Observe readable captions and "
    "continuous gentle audio through both labelled holds. Record visual findings separately.",
    "Replay Harbor, pause/resume and seek into/back into a hold. Observe the opaque fallback "
    "on interruption. Software events alone cannot establish image/caption composition.",
    "For --restart, after the runner relaunches confirm the saved profile, preset and room "
    "remain; open Parent area and check that its PIN is required. Do not put PIN digits in logs.",
]


def build_plan(inventory: dict, package: dict, *, checkpoint_b_confirmed: bool = False) -> dict:
    if inventory.get("kind") == "physical":
        blockers = physical_plan(inventory, package,
                                 checkpoint_b_confirmed=checkpoint_b_confirmed)["blockers"]
    else:
        blockers = []
        if inventory.get("source") != "live-sdk-read-only":
            blockers.append("live_device_inventory_required")
        if inventory.get("connected") is not True or inventory.get("kind") != "virtual":
            blockers.append("connected_known_target_required")
        if inventory.get("explicit_target") is not True:
            blockers.append("explicit_device_target_required")
        description = inventory.get("identity", {}).get("buildDescription") or ""
        if not re.search(r"\bOS\s+1\.2(?=\s|$)", description):
            blockers.append("vega_os_1_2_required")
        if package.get("ok") is not True:
            blockers.append("checked_benign_debug_package_required")
        elif inventory.get("identity", {}).get("architecture") != package.get("architecture"):
            blockers.append("package_device_architecture_mismatch")
    if package.get("captions_available") is not True or package.get("scene_holds_available") is not True:
        blockers.append("reviewed_harbor_fixture_required")
    return {
        "version": 1, "mode": "benign-native-smoke",
        "status": "blocked" if blockers else "ready_to_capture",
        "blockers": blockers, "inventory": inventory, "package": package,
        "journey": JOURNEY, "executed": False,
        "physical_tv_validated": False, "composition_tested": False,
        "household_durability_observed": False, "gate_1_passed": False,
    }


def summarize_log(log: str, start_ms: int, end_ms: int) -> dict:
    """Require this file's load and fresh app events, not generic play messages.

    A suppressed or incomplete device log is inconclusive. The native renderer,
    captions, household state and actual screen timing need separate observation.
    """
    active = False
    harbor_harness = False
    load = 0
    events = []
    seen = set()
    decoder = json.JSONDecoder()
    for line in log.splitlines():
        if LOAD_MARKER in line:
            load += 1
            uri = line.split(LOAD_MARKER, 1)[1].strip()
            active = uri == HARBOR_URI
        if "CALM_TIMING " not in line:
            continue
        try:
            event, _ = decoder.raw_decode(line.split("CALM_TIMING ", 1)[1])
        except (ValueError, TypeError):
            continue
        if not isinstance(event, dict):
            continue
        wall = event.get("wallClockMs")
        if type(wall) not in (int, float) or not start_ms <= wall <= end_ms:
            continue
        if event.get("kind") == "harness-start":
            extra = event.get("extra")
            harbor_harness = (isinstance(extra, dict) and extra.get("scheduleLabel") ==
                              "flash-guard:calm-frames-benign-story")
            continue
        if event.get("kind") == "harness-stop":
            harbor_harness = False
            continue
        media = event.get("mediaTimeMs")
        if not active or not harbor_harness or type(media) not in (int, float) or not 0 <= media <= 20_000:
            continue
        identity = (event.get("kind"), wall, media, event.get("reason"))
        try:
            if identity in seen:
                continue
            seen.add(identity)
        except TypeError:
            continue
        events.append({**event, "_load": load})
    kinds = {event["kind"] for event in events if isinstance(event.get("kind"), str)}
    # A seek jump is not evidence of continuous playback. Require a sequence
    # of time updates between seek/pause/wait boundaries with wall time passing.
    run = []
    progressed = False
    for event in events:
        if run and event["_load"] != run[-1]["_load"]:
            run = []
        if event.get("kind") in {"seeking", "seeked", "pause", "waiting", "stalled", "ended", "error"}:
            run = []
        if event.get("kind") != "timeupdate":
            continue
        if run and (event["mediaTimeMs"] <= run[-1]["mediaTimeMs"]
                    or event["wallClockMs"] <= run[-1]["wallClockMs"]):
            run = []
        run.append(event)
        if len(run) >= 3 and event["wallClockMs"] - run[0]["wallClockMs"] >= 1000:
            progressed = True
    errors = "error" in kinds or bool(re.search(r"(?i)\bsegfault\b|fatal signal|app crashed", log))
    return {
        "status": "error_observed" if errors else
                  "software_playback_observed" if progressed and "playing" in kinds else "inconclusive",
        "fresh_harbor_event_count": len(events), "media_clock_advanced": progressed,
        "playing_event": "playing" in kinds, "pause_event": "pause" in kinds,
        "seek_event": "seeking" in kinds or "seeked" in kinds,
        "scheduled_cover_event": any(event.get("kind") == "cover-on"
                                     and isinstance(event.get("reason"), str)
                                     and event["reason"].startswith("interval ") for event in events),
        "physical_tv_validated": False, "composition_tested": False,
        "household_durability_observed": False, "gate_1_passed": False,
    }


def command(arguments: list[str], timeout: int = 120) -> bool:
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    # Some SDK commands have returned exit zero alongside an explicit failure.
    return result.returncode == 0 and not re.search(
        r"(?i)\bfailed\b|\bfatal\b|irrecoverable", result.stdout + result.stderr,
    )


def capture(device: str, log_path: Path, seconds: int) -> dict:
    """Start logs before launch. Always stop our own stream, never the device."""
    target = ["--device", _serial(device)]
    with log_path.open("x") as output:
        stream = subprocess.Popen(["vega", "device", "start-log-stream", *target],
                                  stdout=output, stderr=subprocess.STDOUT)
        try:
            time.sleep(1)
            if stream.poll() is not None:
                raise RuntimeError("device log stream exited before launch")
            started = int(time.time() * 1000)
            if not command(["vega", "device", "launch-app", *target,
                            "--appName", PACKAGE_ID + ".main"]):
                raise RuntimeError("SDK reported launch failure")
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if stream.poll() is not None:
                    raise RuntimeError("device log stream exited during capture")
                if log_path.stat().st_size > MAX_LOG_BYTES:
                    raise RuntimeError("device log exceeded capture bound")
                time.sleep(min(1, max(0, deadline - time.monotonic())))
            ended = int(time.time() * 1000)
        finally:
            stream.terminate()
            try:
                stream.wait(timeout=5)
            except subprocess.TimeoutExpired:
                stream.kill()
                stream.wait(timeout=5)
    result = summarize_log(log_path.read_text(errors="replace"), started, ended)
    return {**result, "log": str(log_path), "start_ms": started, "end_ms": ended}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vpkg", type=Path, required=True)
    parser.add_argument("--device", type=_serial)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--checkpoint-b-confirmed", action="store_true")
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--output-dir", type=Path,
                        default=REPO / ".logs" / ("benign-native-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")))
    args = parser.parse_args(argv)
    if not 15 <= args.seconds <= 600:
        parser.error("--seconds must be between 15 and 600")
    package_path = args.vpkg.absolute()
    plan = build_plan(collect_inventory(args.device), inspect_package(package_path),
                      checkpoint_b_confirmed=args.checkpoint_b_confirmed)
    if not args.execute or plan["blockers"]:
        print(json.dumps(plan, indent=2))
        return 2 if plan["blockers"] else 0
    args.output_dir.mkdir(parents=True, exist_ok=False)
    print("Operate the visible app during each capture:", flush=True)
    for step in JOURNEY:
        print("- " + step, flush=True)
    plan["executed"] = True
    plan["sessions"] = []
    target = ["--device", args.device]
    try:
        # Recheck immediately before installation; a previous receipt is not
        # authority for a replacement package or a newly connected target.
        current = build_plan(collect_inventory(args.device), inspect_package(package_path),
                             checkpoint_b_confirmed=args.checkpoint_b_confirmed)
        if current["blockers"] or current["package"] != plan["package"] or current["inventory"] != plan["inventory"]:
            raise RuntimeError("target or package changed after preflight")
        if not command(["vega", "device", "install-app", *target,
                        "--packagePath", str(package_path), "--buildType", "Debug"]):
            raise RuntimeError("SDK reported installation failure")
        print(f"Capturing first launch for {args.seconds} seconds.", flush=True)
        plan["sessions"].append(capture(args.device, args.output_dir / "first-launch.log", args.seconds))
        if args.restart:
            if not command(["vega", "device", "terminate-app", *target,
                            "--appName", PACKAGE_ID + ".main"]):
                raise RuntimeError("SDK reported app termination failure")
            print("Restarting without clearing data. Check saved setup and the parent PIN gate.", flush=True)
            plan["sessions"].append(capture(args.device, args.output_dir / "restart.log", args.seconds))
        plan["status"] = "capture_complete"
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        plan["status"] = "capture_failed"
        plan["problem"] = str(exc)
    (args.output_dir / "receipt.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps(plan, indent=2))
    return 0 if plan["status"] == "capture_complete" and all(
        item["status"] == "software_playback_observed" for item in plan["sessions"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
