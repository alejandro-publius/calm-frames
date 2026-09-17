"""Smoke test: install the app on the Vega Virtual Device and play a title.

This is the day-one proof that our renamed, stripped app builds, installs,
launches and plays video on the virtual device. It writes the evidence to
results/vvd_smoke.json so the numbers we publish come from a recorded run and
not from someone's memory of a terminal.

    python3 eval/vvd_smoke.py --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg

What it does:
  1. starts the Vega Virtual Device if it is not running;
  2. installs and launches the app package;
  3. presses remote buttons to reach a title and start playback;
  4. streams device logs while the title plays;
  5. records what the media pipeline and the player actually did.

The key presses match the sample's home screen layout (second row, first tile).
They will need updating when Calm Frames replaces that UI in phase 4.

Use a debug package. Release builds strip console.log, so the log evidence is
thinner.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VEGA = "source ~/vega/env >/dev/null 2>&1 && NO_COLOR=1 "


def vega(arguments: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-lc", VEGA + "vega " + arguments],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def virtual_device_running() -> bool:
    result = vega("virtual-device status", timeout=120)
    return '"running":true' in result.stdout.replace(" ", "")


def device_connected() -> bool:
    result = vega("device is-connected", timeout=120)
    return "is connected" in result.stdout


def wait_for_device(wait_seconds: int = 300) -> bool:
    """QEMU reports running as soon as it starts, well before the guest has
    booted and the device adapter can see it, so wait for the device itself."""
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if device_connected():
            return True
        time.sleep(5)
    return False


def start_virtual_device(wait_seconds: int = 300) -> bool:
    if virtual_device_running():
        return wait_for_device(wait_seconds)
    print("starting the virtual device")
    # Detach it, so it keeps running after this script exits.
    subprocess.Popen(
        ["bash", "-lc", VEGA + "exec vega virtual-device start -t 300"],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if virtual_device_running():
            return wait_for_device(int(max(deadline - time.time(), 60)))
        time.sleep(10)
    return False


PLAY_MARKERS = (
    "notifyPlaybackStarted",
    "MediaPlayerMPBImpl::play()",
    "MediaPlayerMPBImpl::playInternal()",
    "MediaPlayer:play resolved",
)


def playback_has_started(log: str) -> bool:
    return any(marker in log for marker in PLAY_MARKERS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vpkg",
        default="app/build/aarch64-debug/calm-frames-app_aarch64.vpkg",
        help="package to install, relative to the repo root",
    )
    parser.add_argument("--package-id", default="io.github.alejandropublius.calmframes")
    parser.add_argument(
        "--play-seconds", type=float, default=30.0, help="how long to let it play"
    )
    parser.add_argument("--out", default="results/vvd_smoke.json")
    parser.add_argument(
        "--log-out", default="", help="also keep the raw device log here"
    )
    args = parser.parse_args()

    vpkg = (REPO / args.vpkg).resolve()
    if not vpkg.exists():
        raise SystemExit(f"package not found: {vpkg}. Run npm run build:app first.")

    if not start_virtual_device():
        raise SystemExit("the virtual device did not come up")

    device_info = {}
    info = vega("device info", timeout=120)
    try:
        device_info = json.loads(info.stdout[info.stdout.index("{") :])
    except (ValueError, json.JSONDecodeError):
        print("could not parse device info")

    print(f"installing {vpkg.name}")
    launched = vega(f"run-app {vpkg}", timeout=600)
    if "Successfully launched" not in launched.stdout:
        raise SystemExit(f"launch failed: {launched.stdout} {launched.stderr}")
    time.sleep(14)  # let the home screen settle

    log_path = Path(args.log_out) if args.log_out else REPO / "results" / ".vvd_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as log_file:
        stream = subprocess.Popen(
            ["bash", "-lc", VEGA + "vega device start-log-stream"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        try:
            time.sleep(3)
            control = [str(REPO / ".venv" / "bin" / "python"), str(REPO / "eval" / "vvd_control.py")]
            # Home -> second row -> open the title.
            subprocess.run(
                control + ["keys", "down", "down", "ok", "--gap-ms", "2500"],
                check=True,
                capture_output=True,
            )
            time.sleep(7)

            # Press select to start playback. The details screen takes a moment
            # to settle and to give its play button focus, so watch the log and
            # press again if the media pipeline has not started.
            started = False
            for attempt in range(3):
                subprocess.run(control + ["keys", "ok"], check=True, capture_output=True)
                deadline = time.time() + 15
                while time.time() < deadline:
                    time.sleep(2)
                    if playback_has_started(log_path.read_text(errors="ignore")):
                        started = True
                        break
                if started:
                    print(f"playback started after {attempt + 1} select press(es)")
                    break
            if not started:
                print("playback did not start, recording what happened anyway")
            time.sleep(args.play_seconds)
        finally:
            stream.terminate()
            stream.wait(timeout=30)

    log = log_path.read_text(errors="ignore")
    streams = sorted(set(re.findall(r"https://\S+?\.m3u8", log)))
    segment_fetches = len(re.findall(r"request filter type = 1", log))
    playback_started = len(re.findall(r"notifyPlaybackStarted", log))
    play_calls = len(re.findall(r"MediaPlayerMPBImpl::play(?:Internal)?\(\)", log))
    crashes = len(re.findall(r"(?i)\bsegfault|fatal signal|app crashed", log))
    # The app logs one line per streaming failure, and the log stream repeats
    # each line, so count distinct timestamps rather than raw matches.
    streaming_errors = len(
        set(re.findall(r"(\w{3} +\d+ [\d:.]+).{0,200}?Streaming Error", log))
    )
    play_resolved = len(re.findall(r"MediaPlayer:play resolved", log))
    memory = re.findall(r"pss\((\d+)kb\).*?pcpu\(([\d.]+)%\)", log)

    result = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "package_id": args.package_id,
        "package_file": str(vpkg.relative_to(REPO)),
        "device": {
            "build": device_info.get("buildDescription"),
            "architecture": device_info.get("architecture"),
            "product": device_info.get("product"),
            "simulated": device_info.get("simulated"),
        },
        "launched": True,
        "streams_requested": streams,
        "playback_started_events": playback_started,
        "media_play_calls": play_calls,
        "app_play_resolved": play_resolved,
        "streaming_errors": streaming_errors,
        "segment_fetches_during_play": segment_fetches,
        "play_seconds": args.play_seconds,
        "crash_lines": crashes,
        "peak_pss_kb": max((int(m[0]) for m in memory), default=None),
        "played": (playback_started > 0 or play_calls > 0) and segment_fetches >= 2,
        "reached_player_screen": "[PlayerScreen.tsx] - playVideo" in log
        or play_resolved > 0,
    }

    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not args.log_out:
        log_path.unlink(missing_ok=True)
    return 0 if result["played"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
