#!/usr/bin/env python3
"""Baseline: naive mean-luminance differencing.

The dumbest thing that could possibly work, and the honest floor for the whole
comparison. One number per frame (mean luma), flag a frame when that number
moves more than a fixed amount since the previous frame, merge neighbours into
segments.

What it cannot do, by construction:
  - area. A strobe filling 2% of the picture moves the frame mean about as much
    as a gentle wash over the whole picture, and this baseline cannot tell them
    apart. WCAG's flash rules are about a proportion of the visual field.
  - color. The red-flash rule keys on saturated red content, which mean luma
    throws away completely.
  - rate. No sliding window, so three flashes in one second and three flashes in
    ten seconds score the same per frame.
  - linear light. Mean luma is read straight off the gamma-encoded Y plane, so a
    swing in the dark end and the same swing in the bright end count equally.

That list is the point of this baseline: it makes visible what flashmap has to
add on top. It is not a safety tool and must never be described as one.

Luma comes from ffmpeg's `signalstats` YAVG, which is the mean of the Y plane in
whatever range the file declares. The --threshold default is a baseline knob, not
a spec number; thresholds that mean anything live in
flashmap/docs/SPEC_SOURCES.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Baseline knob, in 8-bit luma codes. NOT a spec threshold.
DEFAULT_THRESHOLD = 20.0
DEFAULT_GAP_S = 0.25
# A segment of a single isolated frame is almost always a cut, not a flash.
DEFAULT_MIN_FRAMES = 2

FRAME_RE = re.compile(r"^frame:(\d+)\s+pts:(-?\d+)\s+pts_time:([-\d.eE+]+)")
META_RE = re.compile(r"^lavfi\.signalstats\.YAVG=([\d.]+)")


def tool_version() -> str:
    out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
    return out.splitlines()[0] if out else "unknown"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def per_frame_luma(video: Path, timeout: int) -> list[tuple[float, float]]:
    graph = "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-"
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(video),
         "-vf", graph, "-f", "null", "-"],
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {video.name}: {proc.stderr.strip()[:400]}")

    out: list[tuple[float, float]] = []
    pending_t: float | None = None
    for line in proc.stdout.splitlines():
        m = FRAME_RE.match(line)
        if m:
            pending_t = float(m.group(3))
            continue
        m = META_RE.match(line)
        if m and pending_t is not None:
            out.append((pending_t, float(m.group(1))))
            pending_t = None
    return out


def analyze(video: Path, args) -> dict:
    rows = per_frame_luma(video, args.timeout)
    flagged: list[float] = []
    max_delta = 0.0
    for (t_prev, y_prev), (t, y) in zip(rows, rows[1:]):
        delta = abs(y - y_prev)
        max_delta = max(max_delta, delta)
        if delta >= args.threshold:
            flagged.append(t)

    segs: list[dict] = []
    for t in flagged:
        if segs and t - segs[-1]["end_s"] <= args.gap:
            segs[-1]["end_s"] = t
            segs[-1]["frames"] += 1
        else:
            segs.append({"start_s": t, "end_s": t, "frames": 1})
    kept = [s for s in segs if s["frames"] >= args.min_frames]

    return {
        "baseline": "naive_luma_diff",
        "tool_version": tool_version(),
        "video": video.name,
        "sha256": sha256_of(video),
        "params": {
            "threshold_luma_codes": args.threshold,
            "merge_gap_s": args.gap,
            "min_frames_per_segment": args.min_frames,
        },
        "frames_analyzed": len(rows),
        "flagged_frames": len(flagged),
        "segment_count": len(kept),
        "segments": [{"start_s": round(s["start_s"], 3),
                      "end_s": round(s["end_s"], 3),
                      "duration_s": round(s["end_s"] - s["start_s"], 3),
                      "frames": s["frames"]} for s in kept],
        "segments_dropped_as_single_cut": len(segs) - len(kept),
        "max_frame_to_frame_delta": round(max_delta, 2),
        "notes": (
            "Whole-frame mean luma only. No area, no color, no rate window, no "
            "linear light. Not a conformance result and not a safety claim."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("videos", nargs="+", type=Path)
    ap.add_argument("-o", "--out-dir", type=Path,
                    default=Path("results/baselines/naive_luma_diff"))
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help="8-bit luma codes of frame-to-frame change (default "
                         "%(default)s). A baseline knob, not a spec number.")
    ap.add_argument("--gap", type=float, default=DEFAULT_GAP_S)
    ap.add_argument("--min-frames", type=int, default=DEFAULT_MIN_FRAMES)
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found on PATH")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for video in args.videos:
        if not video.is_file():
            print(f"skip (not a file): {video}", file=sys.stderr)
            continue
        try:
            report = analyze(video, args)
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED {video.name}: {exc}", file=sys.stderr)
            failures += 1
            continue
        dest = args.out_dir / f"{video.stem}.json"
        dest.write_text(json.dumps(report, indent=2) + "\n")
        print(f"{video.name}: {report['segment_count']} segments, "
              f"{report['flagged_frames']}/{report['frames_analyzed']} frames -> {dest}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
