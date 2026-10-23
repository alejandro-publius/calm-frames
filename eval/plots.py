#!/usr/bin/env python3
"""Look at a hazard clip as plots instead of playing it.

Nobody watches strobes at full speed. This script is the only sanctioned way to
inspect a HAZARD_ file: it decodes frames through ffmpeg, never opens a window,
never plays audio, and writes two PNG panels.

    1. Luminance over time    - mean relative luminance of each frame.
    2. Flagged area over time - the share of the picture whose luminance changed
                                by more than an inspection threshold since the
                                previous frame.

Deliberately standalone. It does NOT import flashmap, so a bug in flashmap can
never change what a human sees when they inspect a clip, and a human can sanity
check flashmap's output against something that shares no code with it.

WHAT THIS IS NOT
----------------
This is an inspection aid, not a conformance tool and not a second opinion on
WCAG. The default --delta is a plotting knob picked so that plots are readable;
it is not a spec threshold and must never be quoted as one. Real thresholds live
in flashmap/docs/SPEC_SOURCES.md and only flashmap applies them. Nothing here
decides whether a clip is safe.

Luminance model: gamma-decoded to linear light, then the BT.709 luma weights.
Untagged SD, BT.601 primaries, full-range yuvj and HDR transfer functions are all
treated as BT.709 here. That is wrong for those cases and it is fine for a
plot; flashmap is the path that handles color correctly.

Usage:
    .venv/bin/python eval/plots.py media/HAZARD_clip.mp4 -o results/plots/
    .venv/bin/python eval/plots.py clip.mp4 --max-seconds 60 --csv out.csv
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window, ever
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Plotting knob, not a spec number. See the module docstring.
DEFAULT_DELTA = 0.10
DEFAULT_WIDTH = 192


def _run(cmd: list[str], timeout: int = 300) -> str:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, check=True
    ).stdout


def probe(path: Path) -> dict:
    out = _run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,r_frame_rate,pix_fmt,color_space,color_transfer"
        ":format=duration",
        "-of", "json", str(path),
    ])
    d = json.loads(out)
    s = (d.get("streams") or [{}])[0]

    def ratio(v: str | None) -> float:
        if not v or "/" not in v:
            return 0.0
        n, den = v.split("/")
        return float(n) / float(den) if float(den) else 0.0

    return {
        "width": s.get("width"),
        "height": s.get("height"),
        "fps": ratio(s.get("avg_frame_rate")) or ratio(s.get("r_frame_rate")) or 0.0,
        "pix_fmt": s.get("pix_fmt"),
        "color_space": s.get("color_space"),
        "color_transfer": s.get("color_transfer"),
        "duration": float(d.get("format", {}).get("duration") or 0.0),
    }


def frame_times(path: Path, max_seconds: float | None) -> list[float]:
    """Real presentation timestamps, so a variable frame rate clip plots at its true times."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0"]
    if max_seconds:
        cmd += ["-read_intervals", f"%+{max_seconds}"]
    cmd += ["-show_entries", "frame=best_effort_timestamp_time,pts_time",
            "-of", "csv=p=0", str(path)]
    try:
        raw = _run(cmd, timeout=900)
    except subprocess.CalledProcessError:
        return []
    times = []
    for line in raw.splitlines():
        for tok in line.split(","):
            tok = tok.strip()
            if tok and tok != "N/A":
                try:
                    times.append(float(tok))
                except ValueError:
                    continue
                break
    return times


def decode_luma(path: Path, width: int, max_seconds: float | None):
    """Yield per-frame linear-light luminance planes, downscaled.

    -fps_mode passthrough keeps every decoded frame instead of resampling to a
    constant rate, so the frame count lines up with the timestamps from
    frame_times(). It used to be spelled -vsync 0; ffmpeg 9 removed that spelling
    and exits with "Unrecognized option 'vsync'" before it opens the file, which
    reads downstream as a clip with no frames in it rather than as a bad command
    line. fps_mode has been there since ffmpeg 5.0.
    """
    probe_info = probe(path)
    w = probe_info["width"] or width
    h = probe_info["height"] or width
    out_w = min(width, w)
    out_h = max(2, int(round(out_w * h / w / 2)) * 2)

    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if max_seconds:
        cmd += ["-t", str(max_seconds)]
    cmd += [
        "-i", str(path),
        "-fps_mode", "passthrough",
        "-vf", f"scale={out_w}:{out_h}:flags=area",
        "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
    ]
    frame_bytes = out_w * out_h * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None

    # sRGB / BT.709 electro-optical transfer, applied once as a lookup table.
    c = np.arange(256, dtype=np.float64) / 255.0
    lut = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

    try:
        while True:
            buf = proc.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            rgb = np.frombuffer(buf, dtype=np.uint8).reshape(out_h, out_w, 3)
            lin = lut[rgb]
            yield 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    finally:
        if proc.stdout:
            proc.stdout.close()
        err = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        proc.wait()
        if proc.returncode not in (0, None) and err.strip():
            print(f"ffmpeg said: {err.strip()[:400]}", file=sys.stderr)


def analyze(path: Path, width: int, delta: float, max_seconds: float | None):
    mean_lum: list[float] = []
    flagged_area: list[float] = []
    prev = None
    for plane in decode_luma(path, width, max_seconds):
        mean_lum.append(float(plane.mean()))
        if prev is None:
            flagged_area.append(0.0)
        else:
            changed = np.abs(plane - prev) >= delta
            flagged_area.append(float(changed.mean()))
        prev = plane
    return np.asarray(mean_lum), np.asarray(flagged_area)


def time_axis(path: Path, n: int, info: dict, max_seconds: float | None):
    """Real timestamps when we can get them, uniform spacing when we cannot."""
    times = frame_times(path, max_seconds)
    if len(times) >= n:
        return np.asarray(times[:n]), True
    fps = info["fps"] or 25.0
    return np.arange(n) / fps, False


def render(path: Path, out_dir: Path, width: int, delta: float,
           max_seconds: float | None, csv_path: Path | None) -> Path:
    info = probe(path)
    lum, area = analyze(path, width, delta, max_seconds)
    if lum.size == 0:
        raise SystemExit(f"no frames decoded from {path}")
    t, real_times = time_axis(path, lum.size, info, max_seconds)

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    png = out_dir / f"{stem}_luminance_and_area.png"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    fig.suptitle(
        f"{path.name}  -  inspection plots only, this clip was never played",
        fontsize=11,
    )

    ax1.plot(t, lum, linewidth=0.7, color="#1f4e79")
    ax1.set_ylabel("mean relative luminance\n(linear light, BT.709 weights)")
    ax1.set_ylim(0, max(0.02, float(lum.max()) * 1.08))
    ax1.grid(alpha=0.25)

    ax2.plot(t, area * 100.0, linewidth=0.7, color="#a33")
    ax2.set_ylabel(f"picture area changing\nby >= {delta:.2f} linear (%)")
    ax2.set_xlabel("time (s)" + ("" if real_times else ", assumed constant frame rate"))
    ax2.set_ylim(0, max(1.0, float(area.max()) * 100.0 * 1.08))
    ax2.grid(alpha=0.25)

    src = (
        f"{info['width']}x{info['height']}  {info['fps']:.3f} fps nominal  "
        f"{info['duration']:.1f} s  pix_fmt={info['pix_fmt']}  "
        f"color_space={info['color_space'] or 'untagged'}  "
        f"{lum.size} frames analyzed"
    )
    fig.text(0.01, 0.035, src, fontsize=7.5, color="#444")
    fig.text(
        0.01, 0.010,
        "Inspection aid. The area threshold is a plotting knob, not a spec number. "
        "flashmap decides what is flagged. Cuts spike the lower panel too, so a "
        "spike is not by itself a flash.",
        fontsize=7.5, color="#a33",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    fig.savefig(png, dpi=130)
    plt.close(fig)

    if csv_path:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w") as fh:
            fh.write("time_s,mean_luminance,flagged_area_fraction\n")
            for ti, li, ai in zip(t, lum, area):
                fh.write(f"{ti:.6f},{li:.8f},{ai:.8f}\n")

    print(f"wrote {png}")
    print(
        f"  frames={lum.size}  luminance min/mean/max="
        f"{lum.min():.4f}/{lum.mean():.4f}/{lum.max():.4f}  "
        f"peak changing area={area.max() * 100:.1f}%"
    )
    return png


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video", type=Path)
    ap.add_argument("-o", "--out-dir", type=Path, default=Path("results/plots"))
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                    help="analysis width in pixels (default %(default)s)")
    ap.add_argument("--delta", type=float, default=DEFAULT_DELTA,
                    help="inspection threshold in linear luminance, NOT a spec number "
                         "(default %(default)s)")
    ap.add_argument("--max-seconds", type=float, default=None)
    ap.add_argument("--csv", type=Path, default=None)
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found on PATH")
    if not args.video.exists():
        raise SystemExit(f"no such file: {args.video}")

    render(args.video, args.out_dir, args.width, args.delta,
           args.max_seconds, args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
