"""Run a timing measurement on the Vega Virtual Device and record what happened.

This serves the marker clip and a run config over HTTP, launches the app,
which picks the run up at startup, streams the device log while the clip
plays, and turns the CALM_TIMING lines into numbers:

    python3 eval/vvd_timing_run.py --mode timing
    python3 eval/vvd_timing_run.py --mode layering --seconds 40

What it measures, and why each one matters:

- how often `timeupdate` actually fires on Vega, and how regular it is. Amazon
  does not document this. It sets the floor on how late a cover would be if we
  reacted to timeupdate instead of scheduling ahead of it.
- how precise `currentTime` is: the smallest step between two reported
  positions. A coarse clock puts a floor under the timing error.
- drift: how far the wall-clock estimate ran from the position the player
  reported. This is the error the cover schedule inherits.
- what the cover did: every cover-on and cover-off with its media time, which
  is what a recording gets lined up against.

This is a rehearsal on a virtual device, not GATE 1. GATE 1 is the 240 fps
phone recording of the real stick.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

REPO = Path(__file__).resolve().parent.parent
VEGA = "source ~/vega/env >/dev/null 2>&1 && NO_COLOR=1 "
# The host machine as the virtual device sees it, through QEMU user networking.
HOST_FROM_DEVICE = "10.0.2.2"
PORT = 8000


def vega(arguments: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-lc", VEGA + "vega " + arguments],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def device_connected() -> bool:
    return "is connected" in vega("device is-connected", timeout=120).stdout


class _LimitedReader:
    """Reads at most `remaining` bytes, so a range response stops on time."""

    def __init__(self, handle, remaining: int) -> None:
        self.handle = handle
        self.remaining = remaining

    def read(self, amount: int = -1) -> bytes:
        if self.remaining <= 0:
            return b""
        if amount is None or amount < 0:
            amount = self.remaining
        chunk = self.handle.read(min(amount, self.remaining))
        self.remaining -= len(chunk)
        return chunk

    def close(self) -> None:
        self.handle.close()


def serve(directory: Path, events: list[dict]) -> ThreadingHTTPServer:
    """Serve the clip and the run, and collect the events the app posts back.

    The device log drops the app's output, so the run posts its events here
    instead and this is the evidence.
    """

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def send_head(self):
            """Serve byte ranges.

            Media players ask for ranges. Python's own handler ignores the
            Range header and returns the whole file with a 200, and the Vega
            player treats that as a broken source: the clip never loads and
            the run produces nothing. So this answers ranges properly.
            """
            range_header = self.headers.get("Range")
            if not range_header:
                return super().send_head()

            path = self.translate_path(self.path)
            try:
                size = Path(path).stat().st_size
            except OSError:
                return super().send_head()

            match = re.match(r"bytes=(\d*)-(\d*)", range_header.strip())
            if not match:
                return super().send_head()
            start_text, end_text = match.groups()
            if start_text == "":
                # A suffix range: the last N bytes.
                length = int(end_text or 0)
                start = max(0, size - length)
                end = size - 1
            else:
                start = int(start_text)
                end = int(end_text) if end_text else size - 1
            end = min(end, size - 1)
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return None

            handle = open(path, "rb")
            handle.seek(start)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            return _LimitedReader(handle, end - start + 1)

        def do_POST(self):  # noqa: N802 (the base class names it this)
            length = int(self.headers.get("content-length", 0))
            body = self.rfile.read(length) if length else b"[]"
            try:
                payload = json.loads(body)
                if self.path.endswith("/beacon"):
                    print(f"beacon: {payload}")
                elif isinstance(payload, list):
                    events.extend(payload)
            except json.JSONDecodeError:
                pass
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):  # keep the console quiet
            pass

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server


def package_hls(clip: Path, serve_dir: Path) -> str:
    """Repackage the clip as HLS.

    The Vega player loads HLS on this device and would not start a plain MP4
    served over HTTP, so the marker clip is packaged the same way the catalog
    titles are. The frames and their timestamps are untouched: this copies the
    encoded stream rather than re-encoding it, so the marker times in the
    schedule still hold.
    """
    out = serve_dir / "markers.m3u8"
    for stale in serve_dir.glob("markers*.ts"):
        stale.unlink()
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(clip),
            "-c", "copy",
            "-f", "hls",
            "-hls_time", "2",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", str(serve_dir / "markers%03d.ts"),
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out.name


def build_run(mode: str, schedule: dict, guard_band_ms: int, media_name: str, media_format: str) -> dict:
    run = {
        "mode": mode,
        "videoUrl": f"http://{HOST_FROM_DEVICE}:{PORT}/{media_name}",
        "videoFormat": media_format,
        "scheduleLabel": f"marker-clip-{schedule['clip']['sha256'][:12]}",
        "eventSinkUrl": f"http://{HOST_FROM_DEVICE}:{PORT}/timing",
    }
    if mode == "timing":
        run["guardBandMs"] = guard_band_ms
        run["referencePatch"] = schedule["reference_patch"]
        run["segments"] = [
            {
                "startMs": marker["start_ms"],
                "endMs": marker["end_ms"],
                "reason": "general",
                "label": f"marker {marker['index']}",
            }
            for marker in schedule["markers"]
        ]
    else:
        run["toggleEveryMs"] = 5000
    return run


def parse_timing_lines(log: str) -> list[dict]:
    events = []
    seen = set()
    for match in re.finditer(r"CALM_TIMING (\{.*?\})\s*$", log, re.MULTILINE):
        try:
            event = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        # The log stream repeats each line, so drop exact duplicates.
        key = (event.get("kind"), event.get("wallClockMs"), event.get("mediaTimeMs"))
        if key in seen:
            continue
        seen.add(key)
        events.append(event)
    return events


def summarize(events: list[dict], schedule: dict, mode: str, posted: bool = True) -> dict:
    timeupdates = [e for e in events if e["kind"] == "timeupdate"]
    intervals = [
        b["wallClockMs"] - a["wallClockMs"]
        for a, b in zip(timeupdates, timeupdates[1:])
        if b["wallClockMs"] >= a["wallClockMs"]
    ]
    media_steps = [
        round(b["mediaTimeMs"] - a["mediaTimeMs"], 3)
        for a, b in zip(timeupdates, timeupdates[1:])
        if a.get("mediaTimeMs") is not None
        and b.get("mediaTimeMs") is not None
        and b["mediaTimeMs"] > a["mediaTimeMs"]
    ]
    # worstDriftMs is a running maximum inside the app, so only its final
    # value means anything. A median of a running maximum would be noise
    # dressed up as a statistic.
    drifts = [
        abs(e["extra"]["worstDriftMs"])
        for e in events
        if isinstance(e.get("extra"), dict) and "worstDriftMs" in e["extra"]
    ]
    worst_drift = max(drifts) if drifts else None
    covers_on = [e for e in events if e["kind"] == "cover-on"]
    covers_off = [e for e in events if e["kind"] == "cover-off"]

    def stats(values: list[float]) -> dict | None:
        if not values:
            return None
        ordered = sorted(values)
        return {
            "count": len(values),
            "min": round(ordered[0], 3),
            "median": round(statistics.median(ordered), 3),
            "p95": round(ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))], 3),
            "max": round(ordered[-1], 3),
        }

    quality = [e.get("quality") for e in timeupdates if e.get("quality")]

    return {
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": mode,
        "device": "Vega Virtual Device (not the stick, see docs/GATES.md)",
        "clip_sha256": schedule["clip"]["sha256"],
        "events_seen": len(events),
        "event_source": "posted by the app" if posted else "device log",
        "timeupdate": {
            "count": len(timeupdates),
            "interval_ms": stats([float(i) for i in intervals]),
            "media_step_ms": stats([float(s) for s in media_steps]),
        },
        "current_time_precision_ms": (
            min((s for s in media_steps if s > 0), default=None)
        ),
        "worst_wall_clock_drift_ms": worst_drift,
        "drift_note": (
            "The app tracks the largest gap it saw between its wall-clock "
            "estimate and the position the player reported. Only the maximum "
            "is meaningful."
        ),
        "cover": {
            "on_events": len(covers_on),
            "off_events": len(covers_off),
            "reasons": sorted({str(e.get("reason")) for e in covers_on}),
        },
        "playback_quality_samples": len(quality),
        "playback_quality_last": quality[-1] if quality else None,
        "event_kinds": {
            kind: len([e for e in events if e["kind"] == kind])
            for kind in sorted({str(e["kind"]) for e in events})
        },
        "seek_events": len([e for e in events if e["kind"] in ("seeking", "seeked")]),
        "stall_events": len(
            [e for e in events if e["kind"] in ("waiting", "stalled")]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["timing", "layering"], default="timing")
    parser.add_argument("--seconds", type=float, default=130.0)
    parser.add_argument("--guard-band-ms", type=int, default=500)
    parser.add_argument(
        "--schedule", type=Path, default=REPO / "eval/harness_runs/marker_schedule.json"
    )
    parser.add_argument("--clip", type=Path, default=REPO / "media/markers.mp4")
    parser.add_argument(
        "--vpkg",
        type=Path,
        default=REPO / "app/build/aarch64-debug/calm-frames-app_aarch64.vpkg",
    )
    parser.add_argument("--out", type=Path, default=REPO / "results/vvd_timeupdate_stats.json")
    parser.add_argument("--log-out", type=Path, default=None)
    parser.add_argument(
        "--format",
        choices=["HLS", "MP4"],
        default="HLS",
        help="how to serve the clip. The device would not start a plain MP4.",
    )
    args = parser.parse_args()

    if not args.clip.exists():
        raise SystemExit(f"no clip at {args.clip}. Run eval/marker_clip.py first.")
    if not args.vpkg.exists():
        raise SystemExit(f"no package at {args.vpkg}. Build the debug package first.")
    schedule = json.loads(args.schedule.read_text())

    serve_dir = Path("/private/tmp/claude-501/-Users-alexvintera/5165b902-cbea-4907-849e-e25cde1d46e9/scratchpad/serve")
    serve_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.clip, serve_dir / args.clip.name)
    if args.format == "HLS":
        media_name = package_hls(args.clip, serve_dir)
    else:
        media_name = args.clip.name
    run = build_run(args.mode, schedule, args.guard_band_ms, media_name, args.format)
    (serve_dir / "calm-frames-harness.json").write_text(json.dumps(run, indent=2))
    posted_events: list[dict] = []
    server = serve(serve_dir, posted_events)
    print(f"serving {serve_dir} on port {PORT}")

    try:
        if not device_connected():
            raise SystemExit("no device. Start the virtual device first.")

        # The log stream has to be attached before the app starts, or the
        # startup lines, which say whether a run was picked up at all, are
        # gone before anyone is listening.
        log_path = args.log_out or (REPO / "results/.vvd_timing_log.txt")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w") as log_file:
            stream = subprocess.Popen(
                ["bash", "-lc", VEGA + "vega device start-log-stream"],
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            try:
                time.sleep(3)
                print("installing and launching")
                launched = vega(f"run-app {args.vpkg}", timeout=600)
                if "Successfully launched" not in launched.stdout:
                    raise SystemExit(
                        f"launch failed: {launched.stdout}{launched.stderr}"
                    )
                # A launch with nobody touching the device can leave the app
                # in the background, where it never plays. One key press wakes
                # it. This is a virtual device quirk, not something a person
                # with a remote in their hand would hit.
                time.sleep(8)
                subprocess.run(
                    [
                        str(REPO / ".venv/bin/python"),
                        str(REPO / "eval/vvd_control.py"),
                        "keys",
                        "ok",
                    ],
                    capture_output=True,
                )
                # The virtual device backgrounds an app that nobody is
                # touching, and a backgrounded app stops playing. A person
                # holding a remote never hits this. Press a key the app does
                # not bind, every few seconds, to keep the device awake
                # without touching playback.
                keep_going = True

                def keepalive() -> None:
                    while keep_going:
                        subprocess.run(
                            [
                                str(REPO / ".venv/bin/python"),
                                str(REPO / "eval/vvd_control.py"),
                                "keys",
                                "f1",
                            ],
                            capture_output=True,
                        )
                        time.sleep(4)

                Thread(target=keepalive, daemon=True).start()
                print(f"recording for {args.seconds} s")
                time.sleep(args.seconds)
                keep_going = False
            finally:
                stream.terminate()
                stream.wait(timeout=30)

        # Prefer what the app posted. Fall back to the device log, which is
        # lossy, only if nothing arrived.
        events = posted_events or parse_timing_lines(
            log_path.read_text(errors="ignore")
        )
        print(f"{len(posted_events)} events posted by the app")
        summary = summarize(events, schedule, args.mode, bool(posted_events))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(summary, indent=2) + "\n")
        # Keep the raw events beside the summary: a summary nobody can check
        # against the events behind it is not evidence.
        raw_path = args.out.with_name(args.out.stem + "_events.json")
        raw_path.write_text(json.dumps(events, indent=2) + "\n")
        print(f"raw events written to {raw_path}")
        print(json.dumps(summary, indent=2))
        if args.log_out is None:
            log_path.unlink(missing_ok=True)
        return 0 if summary["timeupdate"]["count"] > 0 else 1
    finally:
        server.shutdown()


if __name__ == "__main__":
    sys.exit(main())
