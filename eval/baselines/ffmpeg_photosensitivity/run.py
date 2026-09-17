#!/usr/bin/env python3
"""Baseline: ffmpeg's built-in `photosensitivity` filter, used as a detector.

The filter is a mitigator, not a reporter: it rewrites frames it considers unsafe
and tells you nothing. So we run it against an unfiltered copy of the same
decode and record where the two differ. A frame the filter left alone is a frame
it did not flag.

    [0:v]split=2[o][s]; [s]photosensitivity[p]; [o][p]blend=difference,signalstats

YMAX of the difference is 0 exactly when the filter passed the frame through.

THE FIRST SECOND
----------------
The brief says to drop the filter's first second of output because it misfires
even on a static gray clip. We drop it (DEFAULT_WARMUP_S below), because dropping
it is the conservative choice and keeps our numbers comparable with whatever
produced that note.

Measured here on ffmpeg 8.1.2 (Sep 17, 2026), the misfire did NOT reproduce: a
6 s 25 fps static mid-gray clip came back with 150 frames in, 150 out, and YMAX 0
on every single frame, including the first second. Either the behavior is
build-dependent or it was fixed upstream. Do not restate the misfire as a fact
about this build without re-measuring. `make ffmpeg-ps-selftest` re-runs that
check so the next person does not have to take this comment on faith.

The filter also has no concept of area, color or the WCAG red rule. It keys on
whole-frame change. That is exactly why it is a baseline and not a candidate.

Output: one JSON file per clip, in the shared baseline schema.
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

# The filter's own defaults, spelled out so a change is visible in the diff.
DEFAULT_FRAMES = 30
DEFAULT_THRESHOLD = 1.0
DEFAULT_SKIP = 1
# Seconds of filter output ignored at the head of the clip. See THE FIRST SECOND.
DEFAULT_WARMUP_S = 1.0
# A frame counts as flagged when the filter changed any pixel by more than this
# many 8-bit codes. 0 would make encoder noise look like a flag; 2 is slack for
# rounding in the difference blend, not a threshold about flashing.
DEFAULT_DIFF_CODES = 2

FRAME_RE = re.compile(r"^frame:(\d+)\s+pts:(-?\d+)\s+pts_time:([-\d.eE+]+)")
META_RE = re.compile(r"^lavfi\.signalstats\.YMAX=([\d.]+)")


def tool_version() -> str:
    out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
    return out.splitlines()[0] if out else "unknown"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def per_frame_difference(video: Path, frames: int, threshold: float, skip: int,
                         timeout: int) -> list[tuple[float, float]]:
    graph = (
        f"[0:v]split=2[o][s];"
        f"[s]photosensitivity=f={frames}:t={threshold}:skip={skip}[p];"
        f"[o][p]blend=all_mode=difference,format=gray,signalstats,"
        f"metadata=print:key=lavfi.signalstats.YMAX:file=-[x]"
    )
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(video),
         "-filter_complex", graph, "-map", "[x]", "-f", "null", "-"],
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


def to_segments(flagged_times: list[float], gap_s: float) -> list[dict]:
    """Merge flagged frame times into segments, closing gaps shorter than gap_s."""
    segs: list[dict] = []
    for t in flagged_times:
        if segs and t - segs[-1]["end_s"] <= gap_s:
            segs[-1]["end_s"] = t
        else:
            segs.append({"start_s": t, "end_s": t})
    return segs


def analyze(video: Path, args) -> dict:
    rows = per_frame_difference(video, args.frames, args.threshold, args.skip,
                                args.timeout)
    warmup_dropped = [(t, y) for t, y in rows if t < args.warmup]
    kept = [(t, y) for t, y in rows if t >= args.warmup]
    flagged = [t for t, y in kept if y > args.diff_codes]
    segs = to_segments(flagged, args.gap)
    return {
        "baseline": "ffmpeg_photosensitivity",
        "tool_version": tool_version(),
        "video": video.name,
        "sha256": sha256_of(video),
        "params": {
            "frames": args.frames,
            "threshold": args.threshold,
            "skip": args.skip,
            "warmup_dropped_s": args.warmup,
            "diff_codes": args.diff_codes,
            "merge_gap_s": args.gap,
        },
        "frames_seen": len(rows),
        "frames_dropped_as_warmup": len(warmup_dropped),
        "frames_analyzed": len(kept),
        "flagged_frames": len(flagged),
        "segment_count": len(segs),
        "segments": [{"start_s": round(s["start_s"], 3),
                      "end_s": round(s["end_s"], 3),
                      "duration_s": round(s["end_s"] - s["start_s"], 3)} for s in segs],
        "warmup_would_have_flagged": sum(1 for _, y in warmup_dropped
                                         if y > args.diff_codes),
        "notes": (
            "The filter is a mitigator; flags are inferred from where its output "
            "differs from the unfiltered decode. No area rule, no color rule, no "
            "red-flash rule. Not a conformance result."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("videos", nargs="+", type=Path)
    ap.add_argument("-o", "--out-dir", type=Path,
                    default=Path("results/baselines/ffmpeg_photosensitivity"))
    ap.add_argument("--frames", type=int, default=DEFAULT_FRAMES)
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--skip", type=int, default=DEFAULT_SKIP)
    ap.add_argument("--warmup", type=float, default=DEFAULT_WARMUP_S)
    ap.add_argument("--diff-codes", type=float, default=DEFAULT_DIFF_CODES)
    ap.add_argument("--gap", type=float, default=0.25,
                    help="merge flagged frames closer than this into one segment")
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
