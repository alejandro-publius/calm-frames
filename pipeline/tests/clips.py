"""Tiny generated clips for the tests.

These are calm by construction: a soft grey gradient sliding slowly sideways.
Every frame differs a little from the one before it, which is what the tests
need, but the whole frame luminance barely moves, so there is no flash in
them. Nothing here is hazardous, and no test ever opens one in a player.

The pipeline is never handed a flashing clip. Where a test needs the pipeline
to believe something is flagged, the fake analyzer says so.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# A two stop grey gradient, drifting, then scrolled sideways about a third of
# a percent of the width per frame. Distant frames look clearly different to a
# comparison, neighbouring frames almost identical.
CALM_SOURCE = (
    "gradients=s={width}x{height}:r={fps}:d={seconds}:speed=0.02:type=linear:"
    "c0=0x303030:c1=0x9a9a9a:nb_colors=2,scroll=horizontal=0.004"
)


def make_calm_clip(
    path: str | Path,
    *,
    seconds: float = 8.0,
    fps: int = 30,
    width: int = 320,
    height: int = 180,
    audio: bool = True,
    subtitles: bool = False,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    args: list[str] = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-f",
        "lavfi",
        "-i",
        CALM_SOURCE.format(width=width, height=height, fps=fps, seconds=seconds),
    ]
    inputs = 1
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}"]
        audio_index = inputs
        inputs += 1
    if subtitles:
        srt = path.with_suffix(".srt")
        srt.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\nhello from the caption track\n\n"
            "2\n00:00:05,000 --> 00:00:07,000\nstill talking\n"
        )
        args += ["-i", str(srt)]
        subtitle_index = inputs
        inputs += 1

    args += ["-map", "0:v"]
    if audio:
        args += ["-map", f"{audio_index}:a"]
    if subtitles:
        args += ["-map", f"{subtitle_index}:s"]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    if audio:
        args += ["-c:a", "aac"]
    if subtitles:
        args += ["-c:s", "mov_text"]
    args += ["-t", str(seconds), str(path)]

    completed = subprocess.run(args, capture_output=True, text=True)
    if completed.returncode != 0 or not path.exists():
        raise RuntimeError(f"could not build a test clip:\n{completed.stderr[-2000:]}")
    return path
