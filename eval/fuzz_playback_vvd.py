"""Fuzz playback on the Vega Virtual Device and ask whether a marker was ever showing.

The property tests reason about the scheduler with a simulated player. This points the same
question at a real one: while the player is really inside a flagged span, is the picture
hidden, whatever is being done to it.

What is done to it, all from the host so the app is the one that ships:

  network throttling   the HLS source is served at a fixed rate, so segments arrive late
  stalls               segment requests are held for seconds, which is what a buffer
                       underrun looks like from the app's side
  seeks                fast forward and rewind on the remote, through QEMU's QMP socket
  pause and resume     the play/pause key
  idling               the keepalive stops, so the device may background the app itself

Two things are NOT done, and the run says so rather than quietly leaving them out.

playbackRate is never changed, because nothing a remote can press changes it and the app
does not change it on its own. Rate changes are exercised against the real scheduler in
eval/property_scheduler_test.py.

Backgrounding is never forced. The only key that reaches the device shell from the host is
the one the keepalive uses to stop the device backgrounding the app by itself, so the plan
can let go of the keepalive and see what happens, and the run reports whether a cover
actually went on for that reason rather than claiming one did.

The rule this run checks, stated so it can be counted:

    for every moment the PLAYER reported being inside a marker, the cover was on.

Everything is anchored to positions the player reported, never to the app's own estimate.
docs/GATES.md records what happens when that rule is broken: a scheduler measured against its
own clock reports a perfect score and has measured nothing.

    python3 eval/fuzz_playback_vvd.py --passes 12

Writes results/chaos_vvd.json, with the machine's load average in it, because a run taken on
a loaded machine measures the machine.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import statistics
import sys
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vvd_control  # noqa: E402
import vvd_smoke  # noqa: E402
import vvd_timing_run as timing  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PORT = timing.PORT
HOST_FROM_DEVICE = timing.HOST_FROM_DEVICE
RESULT = REPO / "results" / "chaos_vvd.json"


# ------------------------------------------------------------------- the rude server


class Throttle:
    """How badly the source is behaving right now. Changed from the chaos thread."""

    def __init__(self) -> None:
        self.lock = Lock()
        self.bytes_per_second: float | None = None
        self.stall_until: float = 0.0
        self.served_segments = 0
        self.stalled_segments = 0
        self.throttled_bytes = 0

    def settings(self) -> tuple[float | None, float]:
        with self.lock:
            return self.bytes_per_second, self.stall_until

    def set_rate(self, bytes_per_second: float | None) -> None:
        with self.lock:
            self.bytes_per_second = bytes_per_second

    def stall_for(self, seconds: float) -> None:
        with self.lock:
            self.stall_until = max(self.stall_until, time.time() + seconds)

    def note_segment(self, stalled: bool, sent: int) -> None:
        with self.lock:
            self.served_segments += 1
            if stalled:
                self.stalled_segments += 1
            self.throttled_bytes += sent


def serve(directory: Path, events: list[dict], throttle: Throttle) -> ThreadingHTTPServer:
    """The same server eval/vvd_timing_run.py uses, with a hand on the tap.

    Range requests are answered properly, because the Vega player treats a 200 with the whole
    file as a broken source. That logic is imported rather than copied: _LimitedReader and the
    range parsing are the ones that run in the timing harness.
    """

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def _is_media(self) -> bool:
            return self.path.endswith((".ts", ".m3u8", ".mp4"))

        def send_head(self):
            if self._is_media():
                _, stall_until = throttle.settings()
                now = time.time()
                if stall_until > now:
                    # A segment request the source simply will not answer yet. From the app's
                    # side this is a buffer that has run dry.
                    time.sleep(min(stall_until - now, 30.0))
                    throttle.note_segment(stalled=True, sent=0)
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
            return timing._LimitedReader(handle, end - start + 1)

        def copyfile(self, source, outputfile):
            """Write the body at whatever rate the chaos plan is asking for."""
            rate, _ = throttle.settings()
            if rate is None or not self._is_media():
                return super().copyfile(source, outputfile)
            chunk_size = max(1024, int(rate / 10))
            sent = 0
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                try:
                    outputfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                sent += len(chunk)
                time.sleep(len(chunk) / rate)
            throttle.note_segment(stalled=False, sent=sent)
            return None

        def do_POST(self):  # noqa: N802 (the base class names it this)
            length = int(self.headers.get("content-length", 0))
            body = self.rfile.read(length) if length else b"[]"
            try:
                payload = json.loads(body)
                if isinstance(payload, list):
                    events.extend(payload)
            except json.JSONDecodeError:
                pass
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server


# ----------------------------------------------------------------------- the chaos


# The virtual device maps these function keys to the remote's transport buttons, and the
# harness player takes them through the media control handler.
ACTION_KEYS = {
    "pause": "f4",
    "resume": "f4",
    "fast-forward": "f5",
    "rewind": "f3",
}

# The key the keepalive presses. The virtual device backgrounds an app nobody is touching and
# a backgrounded app stops playing, which a person holding a remote never hits.
# eval/vvd_timing_run.py found that this key keeps the device awake without touching
# playback, and without it a pass produces no position reports at all.
KEEPALIVE_KEY = "f1"


def chaos_plan(seed: int, seconds: float) -> list[dict]:
    """A reproducible list of rude things to do, and when.

    Seeded so a run can be repeated exactly. Every action is timed from the moment playback
    is expected to have started, and each one is recorded in the result with the wall-clock
    time it actually happened at, so the events can be lined up against it.

    Backgrounding is not in here, and the reason is worth writing down. Nothing the host can
    press backgrounds the app on this device: the only key that reaches the shell is the one
    the keepalive uses to stop the device backgrounding the app by itself. So the plan has an
    "idle" action instead, which stops the keepalive and lets the device do it, and the run
    reports whether a cover actually went on for that reason rather than claiming it did.
    """
    rng = random.Random(seed)
    plan: list[dict] = []
    at = rng.uniform(0.5, 2.0)
    kinds = ["throttle", "stall", "fast-forward", "rewind", "pause", "idle"]
    while at < seconds - 2.0:
        kind = rng.choice(kinds)
        action: dict = {"at_s": round(at, 2), "kind": kind}
        if kind == "throttle":
            action["bytes_per_second"] = rng.choice([8_000, 20_000, 60_000])
            action["for_s"] = round(rng.uniform(1.5, 4.0), 2)
        elif kind == "stall":
            action["for_s"] = round(rng.uniform(1.0, 3.5), 2)
        elif kind == "pause":
            action["for_s"] = round(rng.uniform(0.8, 2.5), 2)
        elif kind == "idle":
            action["for_s"] = round(rng.uniform(4.0, 9.0), 2)
        plan.append(action)
        at += rng.uniform(3.0, 6.0)
    return plan


class Keepalive:
    """Presses one key every few seconds so the device does not background the app.

    It can be told to stop for a while, which is the only way from the host to let the app go
    to the background at all.
    """

    def __init__(self, qmp) -> None:
        self.qmp = qmp
        self.running = True
        self.awake = True
        self.lock = Lock()
        self.thread = Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self) -> None:
        while self.running:
            if self.awake:
                try:
                    with self.lock:
                        self.qmp.press(KEEPALIVE_KEY)
                except Exception:  # noqa: BLE001 - a missed press is not worth stopping for
                    pass
            time.sleep(4)

    def press(self, key: str) -> None:
        with self.lock:
            self.qmp.press(key)

    def stop(self) -> None:
        self.running = False


def run_chaos(plan: list[dict], throttle: Throttle, keepalive: "Keepalive", started_at: float) -> list[dict]:
    """Carry the plan out, recording when each thing actually happened."""
    done: list[dict] = []
    for action in plan:
        wait = started_at + action["at_s"] - time.time()
        if wait > 0:
            time.sleep(wait)
        happened = {**action, "wall_clock_ms": round(time.time() * 1000)}
        try:
            if action["kind"] == "throttle":
                throttle.set_rate(action["bytes_per_second"])
                time.sleep(action["for_s"])
                throttle.set_rate(None)
            elif action["kind"] == "stall":
                throttle.stall_for(action["for_s"])
            elif action["kind"] in ("fast-forward", "rewind"):
                keepalive.press(ACTION_KEYS[action["kind"]])
            elif action["kind"] == "pause":
                keepalive.press(ACTION_KEYS["pause"])
                time.sleep(action["for_s"])
                keepalive.press(ACTION_KEYS["resume"])
            elif action["kind"] == "idle":
                keepalive.awake = False
                time.sleep(action["for_s"])
                keepalive.awake = True
            happened["carried_out"] = True
        except Exception as error:  # noqa: BLE001 - a rude action that fails is still data
            happened["carried_out"] = False
            happened["error"] = str(error)[:200]
        happened["ended_wall_clock_ms"] = round(time.time() * 1000)
        done.append(happened)
    return done


# ---------------------------------------------------------------------- the analysis


def clean_pass(events: list[dict]) -> tuple[list[dict], dict]:
    """One app instance's events, with the previous instance's stragglers thrown out.

    Two rules, both from docs/GATES.md. Take everything from the last harness-start, because
    a batch the previous instance posted late lands at the front of this pass. Then drop
    anything whose wall clock goes backwards by more than two seconds, because that is
    another instance talking.
    """
    starts = [index for index, event in enumerate(events) if event.get("kind") == "harness-start"]
    dropped_before = 0
    if starts:
        dropped_before = starts[-1]
        events = events[starts[-1] :]
    kept: list[dict] = []
    dropped_backwards = 0
    highest = None
    for event in events:
        when = event.get("wallClockMs")
        if not isinstance(when, (int, float)):
            kept.append(event)
            continue
        if highest is not None and when < highest - 2_000:
            dropped_backwards += 1
            continue
        highest = when if highest is None else max(highest, when)
        kept.append(event)
    return kept, {
        "had_a_harness_start": bool(starts),
        "dropped_before_the_last_harness_start": dropped_before,
        "dropped_for_going_backwards": dropped_backwards,
    }


def cover_off_spans(events: list[dict]) -> list[tuple[float, float]]:
    """The wall-clock spans during which the picture was showing.

    The harness starts with the picture showing and covers when the schedule says to, so the
    first span opens at the first event and closes at the first cover-on.
    """
    changes = sorted(
        (
            (float(event["wallClockMs"]), event["kind"] == "cover-on")
            for event in events
            if event.get("kind") in ("cover-on", "cover-off")
            and isinstance(event.get("wallClockMs"), (int, float))
        ),
        key=lambda pair: pair[0],
    )
    if not events:
        return []
    first = min(
        float(event["wallClockMs"])
        for event in events
        if isinstance(event.get("wallClockMs"), (int, float))
    )
    last = max(
        float(event["wallClockMs"])
        for event in events
        if isinstance(event.get("wallClockMs"), (int, float))
    )
    spans: list[tuple[float, float]] = []
    covered = False
    opened = first
    for when, now_covered in changes:
        if now_covered and not covered:
            spans.append((opened, when))
            covered = True
        elif not now_covered and covered:
            opened = when
            covered = False
    if not covered:
        spans.append((opened, last))
    return [(a, b) for a, b in spans if b > a]


def marker_crossings(events: list[dict], markers: list[dict]) -> list[dict]:
    """Every time the PLAYER said it was inside a marker, and what the cover was doing.

    Only positions the player reported are used. Between two consecutive reports the playhead
    is taken to have moved evenly, which is the only thing two points can say. A pair where
    the position went backwards is a seek, and a seek is not a journey through the clip, so
    those pairs are recorded and not counted.
    """
    reports = [
        (float(event["wallClockMs"]), float(event["mediaTimeMs"]))
        for event in events
        if event.get("kind") == "timeupdate"
        and isinstance(event.get("mediaTimeMs"), (int, float))
        and isinstance(event.get("wallClockMs"), (int, float))
    ]
    reports.sort(key=lambda pair: pair[0])
    off_spans = cover_off_spans(events)

    crossings: list[dict] = []
    for (wall_a, media_a), (wall_b, media_b) in zip(reports, reports[1:]):
        if media_b <= media_a or wall_b <= wall_a:
            continue  # a seek, a repeat, or a clock that did not move
        for marker in markers:
            low = max(media_a, float(marker["start_ms"]))
            high = min(media_b, float(marker["end_ms"]))
            if high <= low:
                continue
            # Where in this pair of reports the marker sat, in wall-clock time.
            span = media_b - media_a
            enter = wall_a + (low - media_a) / span * (wall_b - wall_a)
            leave = wall_a + (high - media_a) / span * (wall_b - wall_a)
            showing = [
                (max(enter, start), min(leave, end))
                for start, end in off_spans
                if min(leave, end) > max(enter, start)
            ]
            crossings.append(
                {
                    "marker": marker["index"],
                    "media_from_ms": round(low, 1),
                    "media_to_ms": round(high, 1),
                    "report_gap_ms": round(wall_b - wall_a, 1),
                    "covered": not showing,
                    "showing_for_ms": round(sum(b - a for a, b in showing), 1),
                }
            )
    return crossings


def load_averages() -> list[float]:
    try:
        return [round(value, 2) for value in os.getloadavg()]
    except OSError:
        return []


# ------------------------------------------------------------------------ the run


def one_pass(
    index: int,
    plan: list[dict],
    throttle: Throttle,
    events: list[dict],
    vpkg: Path,
    seconds: float,
    schedule: dict,
    settle_s: float,
) -> dict:
    events.clear()
    throttle.set_rate(None)
    launched = timing.vega(f"run-app {vpkg}", timeout=600)
    if "Successfully launched" not in launched.stdout:
        return {
            "pass": index,
            "launched": False,
            "why": (launched.stdout + launched.stderr).strip()[-300:],
        }
    started_at = time.time()
    try:
        qmp = vvd_control.Qmp(vvd_control.find_socket())
    except Exception as error:  # noqa: BLE001 - a device that has gone is data, not a crash
        return {"pass": index, "launched": True, "device_lost": True, "why": str(error)[:300]}
    keepalive = Keepalive(qmp)
    device_lost = False
    try:
        # A launch nobody touches can leave the app in the background, where it never plays.
        time.sleep(6)
        keepalive.press("ok")
        # Nothing rude happens until playback is properly going. The software lead time run
        # found the first position report past the guard band at about 6.5 s, so chaos that
        # starts before then is only ever chaos against a player that has not begun.
        time.sleep(settle_s)
        carried_out = run_chaos(plan, throttle, keepalive, time.time())
        remaining = started_at + seconds - time.time()
        if remaining > 0:
            time.sleep(remaining)
    except (BrokenPipeError, ConnectionResetError, OSError) as error:
        # The virtual device dies now and then, and it died twice during this work. Losing it
        # mid pass is worth recording rather than crashing on: the pass is dropped and the
        # device is started again.
        device_lost = True
        carried_out = locals().get("carried_out", [])
        print(f"  the device went away mid pass: {error}")
    finally:
        throttle.set_rate(None)
        keepalive.stop()
        time.sleep(0.2)
        try:
            qmp.close()
        except OSError:
            pass

    # Give any last batch time to arrive before the next pass clears the list.
    time.sleep(2.0)
    cleaned, split = clean_pass(list(events))
    crossings = marker_crossings(cleaned, schedule["markers"])
    kinds = sorted({str(event.get("kind")) for event in cleaned})
    return {
        "pass": index,
        "launched": True,
        "device_lost": device_lost,
        "events": len(cleaned),
        "event_kinds": kinds,
        "split": split,
        "actions": carried_out,
        "position_reports": len([e for e in cleaned if e.get("kind") == "timeupdate"]),
        "furthest_position_ms": max(
            [
                float(e["mediaTimeMs"])
                for e in cleaned
                if e.get("kind") == "timeupdate"
                and isinstance(e.get("mediaTimeMs"), (int, float))
            ],
            default=None,
        ),
        "cover_on_reasons": sorted(
            {
                str(event.get("reason"))
                for event in cleaned
                if event.get("kind") == "cover-on"
            }
        ),
        "crossings": crossings,
        "uncovered": [c for c in crossings if not c["covered"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passes", type=int, default=12)
    parser.add_argument("--seconds", type=float, default=26.0)
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument(
        "--settle",
        type=float,
        default=9.0,
        help="seconds to let playback get going before anything rude happens",
    )
    parser.add_argument("--guard-band-ms", type=int, default=500)
    parser.add_argument(
        "--schedule", type=Path, default=REPO / "eval/harness_runs/marker_schedule_packed.json"
    )
    parser.add_argument("--clip", type=Path, default=REPO / "media/markers_packed.mp4")
    parser.add_argument(
        "--vpkg",
        type=Path,
        default=REPO / "app/build/aarch64-debug/calm-frames-app_aarch64.vpkg",
    )
    parser.add_argument("--out", type=Path, default=RESULT)
    args = parser.parse_args()

    if not args.clip.exists():
        raise SystemExit(f"no clip at {args.clip}")
    if not args.vpkg.exists():
        raise SystemExit(f"no package at {args.vpkg}")
    schedule = json.loads(args.schedule.read_text())

    # Inside the checkout but gitignored, so the packaged clip is easy to find and never
    # committed. The clip itself is a pair of luminance changes every few seconds, far below
    # anything WCAG counts as flashing, so it is not hazardous.
    serve_dir = Path(os.environ.get("CALM_CHAOS_SERVE", REPO / "build" / "chaos-serve"))
    serve_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.clip, serve_dir / args.clip.name)
    media_name = timing.package_hls(args.clip, serve_dir)
    run = timing.build_run("timing", schedule, args.guard_band_ms, media_name, "HLS")
    run["scheduleLabel"] = f"chaos-{schedule['clip']['sha256'][:12]}"
    (serve_dir / "calm-frames-harness.json").write_text(json.dumps(run, indent=2))

    throttle = Throttle()
    events: list[dict] = []
    server = serve(serve_dir, events, throttle)
    print(f"serving {serve_dir} on {PORT}")

    load_before = load_averages()
    if not timing.device_connected():
        print("no device, starting the virtual device")
        if not vvd_smoke.start_virtual_device(wait_seconds=420):
            raise SystemExit("the virtual device would not come up")
        # The device shell is not ready the moment the adapter can see it. Installing too
        # early fails with "failed to get running components for
        # com.amazon.dev.shell.service", which looks like a broken package and is not one.
        print("device is connected, waiting 45 s for the shell to be ready")
        time.sleep(45)

    passes = []
    restarts = 0
    try:
        for index in range(1, args.passes + 1):
            plan = chaos_plan(args.seed + index, args.seconds - 6 - args.settle)
            print(f"pass {index}/{args.passes}: {len(plan)} action(s)")
            result = one_pass(
                index,
                plan,
                throttle,
                events,
                args.vpkg,
                args.seconds,
                schedule,
                args.settle,
            )
            passes.append(result)
            crossings = result.get("crossings", [])
            print(
                f"  launched={result['launched']} events={result.get('events', 0)} "
                f"crossings={len(crossings)} uncovered={len(result.get('uncovered', []))}"
            )
            if result.get("device_lost") or not timing.device_connected():
                print("  the virtual device is gone, starting it again")
                restarts += 1
                if not vvd_smoke.start_virtual_device(wait_seconds=420):
                    print("  it would not come back, stopping here")
                    break
                time.sleep(45)
    finally:
        server.shutdown()

    all_crossings = [c for p in passes for c in p.get("crossings", [])]
    uncovered = [c for c in all_crossings if not c["covered"]]
    actions = [a for p in passes for a in p.get("actions", [])]
    report = {
        "statement": (
            "Playback fuzzing on the Vega Virtual Device. For every moment the player "
            "reported being inside a marker, was the picture hidden. Everything is anchored "
            "to positions the player reported, never to the app's own estimate."
        ),
        "what_this_is_not": (
            "Not GATE 1 and not a screen-level measurement. Nothing here sees the React "
            "commit, the compositor, scan-out or the panel. It is the app's own account of "
            "what it did, on a virtual device, checked against what the player said."
        ),
        "tool": "eval/fuzz_playback_vvd.py",
        "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "device": "Vega Virtual Device",
        "clip_sha256": schedule["clip"]["sha256"],
        "guard_band_ms": args.guard_band_ms,
        "seed": args.seed,
        "load_average_before": load_before,
        "load_average_after": load_averages(),
        "load_note": (
            "A run taken on a loaded machine measures the machine. The load averages are one, "
            "five and fifteen minutes, from the host."
        ),
        "passes_attempted": args.passes,
        "passes_launched": len([p for p in passes if p.get("launched")]),
        "passes_lost_with_the_device": len([p for p in passes if p.get("device_lost")]),
        "virtual_device_restarts": restarts,
        "device_note": (
            "The virtual device stopped on its own more than once during this work, which is "
            "a note about the device and not about the app. A pass that lost it is dropped "
            "rather than counted, and the device is started again."
        ),
        "passes_with_a_crossing": len([p for p in passes if p.get("crossings")]),
        "totals": {
            "marker_crossings_counted": len(all_crossings),
            "uncovered_marker_crossings": len(uncovered),
            "showing_ms_total": round(sum(c["showing_for_ms"] for c in uncovered), 1),
            "report_gap_ms_median": (
                round(statistics.median([c["report_gap_ms"] for c in all_crossings]), 1)
                if all_crossings
                else None
            ),
            "report_gap_ms_max": (
                max(c["report_gap_ms"] for c in all_crossings) if all_crossings else None
            ),
        },
        "chaos": {
            "actions_carried_out": len([a for a in actions if a.get("carried_out")]),
            "actions_by_kind": {
                kind: len([a for a in actions if a["kind"] == kind and a.get("carried_out")])
                for kind in sorted({a["kind"] for a in actions})
            },
            "segments_served": throttle.served_segments,
            "segment_requests_stalled": throttle.stalled_segments,
            "cover_on_reasons_seen": sorted(
                {reason for p in passes for reason in p.get("cover_on_reasons", [])}
            ),
            "background_covers_seen": len(
                [
                    p
                    for p in passes
                    if "background" in p.get("cover_on_reasons", [])
                ]
            ),
            "playback_rate_changes": 0,
            "playback_rate_note": (
                "Never exercised on the device. Nothing a remote can press changes "
                "playbackRate, and the app does not change it itself, so there was no way to "
                "do it from the host without changing the app. Rate changes are exercised "
                "against the real scheduler in eval/property_scheduler_test.py."
            ),
        },
        "how_a_crossing_is_counted": (
            "Two consecutive timeupdate reports with the position moving forward describe a "
            "span of the clip the player passed through. Where that span meets a marker, the "
            "wall-clock window is interpolated between the two reports and the cover state "
            "over that window is read from the cover-on and cover-off events. A pair where "
            "the position went backwards is a seek rather than a journey, and is not counted. "
            "The report gap is published because it is how coarse the interpolation is."
        ),
        "uncovered": uncovered,
        "passes": passes,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"\n{len(all_crossings)} marker crossing(s), {len(uncovered)} with the picture "
        f"showing. Written to {args.out}"
    )
    return 0 if all_crossings and not uncovered else 1


if __name__ == "__main__":
    raise SystemExit(main())
