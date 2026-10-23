"""Make the timing marker clip and its schedule.

GATE 1 measures one thing: is the cover fully on before the thing it is meant
to hide appears. To measure that you need a clip where you know, to the
millisecond, when something appears. That is what this makes.

    python3 eval/marker_clip.py --out media/markers.mp4 \
        --schedule eval/harness_runs/marker_schedule.json

The clip is deliberately not hazardous. Each marker is a single step from a
mid gray to a light gray, held for one second, then a single step back. That
is one pair of opposing changes every six seconds, which is 0.17 per second
against WCAG's limit of three per second, so the clip can be watched at full
speed by anyone. The cover is what we are testing, not the content.

It carries a reference patch in the top left corner that the cover leaves
uncovered. The patch alternates between two close grays once per second, so a
recording can show that the screen was live and the player was running even
while the rest of the picture is hidden. The patch change is under the ten
percent of maximum relative luminance that WCAG counts as a flash, and it
covers a small part of the screen.

The clip is never committed: media/ is gitignored. The schedule is, along
with the clip's SHA-256, so we always know which video a set of numbers
belongs to.

The head-start kits were meant to bring calm-timing for this. They were never
delivered, so this is our own. Replace it if the kit turns up, and re-record
any numbers taken with this one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent

# sRGB values. The step is large enough for a camera to see through a TV and
# slow enough that it is nowhere near a flash.
BASE_GRAY = 110
MARKER_GRAY = 235
PATCH_LIGHT = 170
PATCH_DARK = 150


def srgb_to_relative_luminance(value: int) -> float:
    """WCAG relative luminance for a neutral sRGB value, 0 to 1."""
    channel = value / 255
    linear = (
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
    )
    return linear  # neutral gray: 0.2126 R + 0.7152 G + 0.0722 B = the same value


def build(
    out: Path,
    schedule_path: Path,
    duration_s: float,
    fps: int,
    width: int,
    height: int,
    marker_count: int,
    first_marker_ms: int,
    spacing_ms: int,
    marker_hold_ms: int,
    patch: dict,
) -> dict:
    total_frames = int(round(duration_s * fps))
    frame_ms = 1000 / fps

    markers = []
    for index in range(marker_count):
        start_ms = first_marker_ms + index * spacing_ms
        end_ms = start_ms + marker_hold_ms
        if end_ms > duration_s * 1000:
            raise SystemExit(
                f"marker {index + 1} ends at {end_ms} ms, past the {duration_s} s clip"
            )
        markers.append({"index": index + 1, "start_ms": start_ms, "end_ms": end_ms})

    out.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",
        # A silent audio track. A video-only stream made the Vega player pause
        # a few seconds in, and a measurement run that stops after four
        # seconds measures nothing. Silence also keeps the layering test
        # honest, because that test asks whether audio keeps going while the
        # picture is hidden.
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-shortest",
        "-c:a", "aac",
        "-b:a", "64k",
        "-c:v", "libx264",
        "-preset", "medium",
        # Keyframe every second keeps seeking predictable, which matters for
        # the seek-safety work later.
        "-g", str(fps),
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        str(out),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert process.stdin is not None

    marker_spans = [(m["start_ms"], m["end_ms"]) for m in markers]
    patch_x, patch_y = patch["x"], patch["y"]
    patch_w, patch_h = patch["width"], patch["height"]

    for frame_index in range(total_frames):
        now_ms = frame_index * frame_ms
        level = BASE_GRAY
        for start_ms, end_ms in marker_spans:
            if start_ms <= now_ms < end_ms:
                level = MARKER_GRAY
                break
        frame = np.full((height, width, 3), level, dtype=np.uint8)

        # One patch cycle per second: light for the first half, dark for the
        # second half.
        patch_level = PATCH_LIGHT if int(now_ms / 500) % 2 == 0 else PATCH_DARK
        frame[patch_y : patch_y + patch_h, patch_x : patch_x + patch_w] = patch_level

        process.stdin.write(frame.tobytes())

    process.stdin.close()
    if process.wait() != 0:
        raise SystemExit("ffmpeg failed to write the clip")

    digest = hashlib.sha256(out.read_bytes()).hexdigest()

    schedule = {
        "version": 1,
        "generator": "eval/marker_clip.py",
        "note": (
            "Timing markers for the GATE 1 rehearsal. Not hazardous: one pair "
            "of opposing luminance changes every six seconds, far below the "
            "three per second WCAG counts as flashing."
        ),
        "clip": {
            "file_name": out.name,
            "sha256": digest,
            "duration_s": duration_s,
            "fps": fps,
            "width": width,
            "height": height,
            "base_srgb": BASE_GRAY,
            "marker_srgb": MARKER_GRAY,
            "base_relative_luminance": round(srgb_to_relative_luminance(BASE_GRAY), 4),
            "marker_relative_luminance": round(
                srgb_to_relative_luminance(MARKER_GRAY), 4
            ),
        },
        "reference_patch": patch,
        "markers": markers,
    }
    schedule_path.parent.mkdir(parents=True, exist_ok=True)
    schedule_path.write_text(json.dumps(schedule, indent=2) + "\n")
    return schedule


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO / "media" / "markers.mp4")
    parser.add_argument(
        "--schedule",
        type=Path,
        default=REPO / "eval" / "harness_runs" / "marker_schedule.json",
    )
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--markers", type=int, default=20)
    parser.add_argument("--first-marker-ms", type=int, default=4000)
    parser.add_argument("--spacing-ms", type=int, default=6000)
    parser.add_argument("--hold-ms", type=int, default=1000)
    args = parser.parse_args()

    patch = {"x": 48, "y": 48, "width": 96, "height": 96}
    schedule = build(
        out=args.out,
        schedule_path=args.schedule,
        duration_s=args.duration,
        fps=args.fps,
        width=args.width,
        height=args.height,
        marker_count=args.markers,
        first_marker_ms=args.first_marker_ms,
        spacing_ms=args.spacing_ms,
        marker_hold_ms=args.hold_ms,
        patch=patch,
    )
    print(json.dumps({"clip": str(args.out), "schedule": str(args.schedule)}, indent=2))
    print(
        f"{len(schedule['markers'])} markers, first at "
        f"{schedule['markers'][0]['start_ms']} ms, last ending at "
        f"{schedule['markers'][-1]['end_ms']} ms"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
