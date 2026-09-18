#!/usr/bin/env python3
"""Blinded plots for the real clip labelling. No detector output, no title, no playback.

docs/EVAL_PLAN.md section 5: the labeller sees per frame relative luminance for the whole
picture and for the largest changing region, the area fraction of that region, and the red
chromaticity trace. Nothing else. Not the file name, not the source, not the position in the
film, and above all not what any detector said, because a plot with a detector's answer drawn
on it measures agreement with the detector rather than agreement with the spec.

This module does not import flashmap, and eval/tests/test_conformance_standalone.py holds it to
that. It reuses the probing and timestamp helpers from eval/plots.py, which is the sanctioned
way to look at a hazard clip, and adds the two panels the labelling needs.

The thresholds printed on the figure come from flashmap/docs/SPEC_SOURCES.md through
eval/conformance/spec.py, which parses the quoted text. They are the same numbers the labelling
guide quotes, because the labeller is applying the spec, not guessing.

SAFETY: nothing here opens a window, plays audio or shows a frame. It decodes to numbers and
writes a PNG of two line charts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window, ever
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

import plots as inspection  # noqa: E402  (eval/plots.py)
from conformance.spec import load_spec  # noqa: E402

REPO = _EVAL_DIR.parent
DEFAULT_WIDTH = 192
# Inspection knob for "this pixel changed", not a spec number. It decides which pixels count as
# the changing region for the second and third panels, nothing else.
DEFAULT_DELTA = 0.05


def decode_rgb(path: Path, start_s: float, seconds: float, width: int):
    """Yield linear light RGB frames for a window of a file, downscaled. Never shown."""
    info = inspection.probe(path)
    source_width = info["width"] or width
    source_height = info["height"] or width
    out_width = min(width, source_width)
    out_height = max(2, int(round(out_width * source_height / source_width / 2)) * 2)

    command = [
        "ffmpeg", "-v", "error", "-nostdin",
        "-ss", f"{start_s:.3f}", "-t", f"{seconds:.3f}",
        "-i", str(path),
        "-vsync", "0",
        "-vf", f"scale={out_width}:{out_height}:flags=area",
        "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
    ]
    frame_bytes = out_width * out_height * 3
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None

    spec = load_spec()
    table = spec.srgb_to_linear(np.arange(256, dtype=np.float64) / 255.0)
    try:
        while True:
            buffer = process.stdout.read(frame_bytes)
            if len(buffer) < frame_bytes:
                break
            rgb = np.frombuffer(buffer, dtype=np.uint8).reshape(out_height, out_width, 3)
            yield table[rgb]
    finally:
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.read()
        process.wait()


def field_coverage(mask, spec) -> float:
    """The largest share of any 10 degree field on the picture that this mask fills.

    The spec's area rule is about a 10 degree field, not about the whole picture, and the two
    are different by a factor of about nine for anything compact. Drawing the 25% line on a
    whole picture axis, which the first version of this figure did, would have told a labeller
    that a strobe filling a tenth of the screen was well under the limit when it is comfortably
    over it.

    A summed area table gives the busiest position of the field in one pass. This is written
    here rather than imported, because this module must not reach into flashmap.
    """
    array = np.asarray(mask, dtype=np.float64)
    height, width = array.shape
    field_h = max(1, min(height, int(round(height * spec.field_height_fraction))))
    field_w = max(1, min(width, int(round(width * spec.field_width_fraction))))
    integral = np.zeros((height + 1, width + 1), dtype=np.float64)
    integral[1:, 1:] = array.cumsum(axis=0).cumsum(axis=1)
    sums = (
        integral[field_h:, field_w:]
        - integral[:-field_h, field_w:]
        - integral[field_h:, :-field_w]
        + integral[:-field_h, :-field_w]
    )
    if sums.size == 0:
        return 0.0
    return float(sums.max()) / float(field_h * field_w)


def trace(path: Path, start_s: float, seconds: float, width: int, delta: float) -> dict:
    """The series the labeller reads, plus the frame times they sit on."""
    spec = load_spec()
    weights = np.asarray(spec.luma_weights)

    whole: list[float] = []
    region: list[float] = []
    area: list[float] = []
    coverage: list[float] = []
    red: list[float] = []
    previous = None
    for linear in decode_rgb(path, start_s, seconds, width):
        luminance = linear @ weights
        whole.append(float(luminance.mean()))
        if previous is None:
            region.append(float(luminance.mean()))
            area.append(0.0)
            coverage.append(0.0)
            red.append(float(_red_ratio(linear.reshape(-1, 3).mean(axis=0))))
        else:
            changing = np.abs(luminance - previous) >= delta
            area.append(float(changing.mean()))
            coverage.append(field_coverage(changing, spec))
            if changing.any():
                region.append(float(luminance[changing].mean()))
                red.append(float(_red_ratio(linear[changing].mean(axis=0))))
            else:
                region.append(float(luminance.mean()))
                red.append(float(_red_ratio(linear.reshape(-1, 3).mean(axis=0))))
        previous = luminance

    count = len(whole)
    info = inspection.probe(path)
    fps = info["fps"] or 25.0
    times = np.arange(count) / fps
    return {
        "times_s": times,
        "whole_picture_luminance": np.asarray(whole),
        "changing_region_luminance": np.asarray(region),
        "changing_area_fraction": np.asarray(area),
        "changing_field_coverage": np.asarray(coverage),
        "changing_region_red_ratio": np.asarray(red),
        "frames": count,
        "fps": fps,
    }


def _red_ratio(linear_rgb) -> float:
    total = float(np.sum(linear_rgb))
    return 0.0 if total <= 0 else float(linear_rgb[0]) / total


def render(
    segment_id: str,
    path: Path,
    start_s: float,
    seconds: float,
    out_dir: Path,
    width: int = DEFAULT_WIDTH,
    delta: float = DEFAULT_DELTA,
) -> Path:
    spec = load_spec()
    series = trace(path, start_s, seconds, width, delta)
    if series["frames"] == 0:
        raise RuntimeError(f"no frames decoded for {segment_id}")

    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{segment_id}.png"
    times = series["times_s"]

    figure, (top, middle, bottom) = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
    figure.suptitle(f"segment {segment_id}   -   plots only, this clip was never played", fontsize=11)

    top.plot(times, series["whole_picture_luminance"], linewidth=0.8, color="#1f4e79")
    top.set_ylabel("whole picture\nrelative luminance")
    top.set_ylim(0, max(0.05, float(series["whole_picture_luminance"].max()) * 1.1))
    top.grid(alpha=0.25)

    middle.plot(times, series["changing_region_luminance"], linewidth=0.8, color="#7a3b8f")
    middle.set_ylabel("changing region\nrelative luminance")
    middle.set_ylim(0, max(0.05, float(series["changing_region_luminance"].max()) * 1.1))
    middle.grid(alpha=0.25)
    twin = middle.twinx()
    twin.plot(
        times, series["changing_field_coverage"] * 100.0, linewidth=0.8, color="#a33", alpha=0.85
    )
    twin.plot(
        times,
        series["changing_area_fraction"] * 100.0,
        linewidth=0.6,
        color="#a33",
        alpha=0.35,
        linestyle="--",
    )
    twin.set_ylabel("changing area: busiest 10 degree field (%)\nand whole picture (dashed)", color="#a33")
    twin.set_ylim(0, 100)
    twin.axhline(
        spec.area_fraction_limit * 100.0,
        color="#a33",
        linestyle=":",
        linewidth=1.0,
    )

    bottom.plot(times, series["changing_region_red_ratio"], linewidth=0.8, color="#c0392b")
    bottom.axhline(spec.red_saturated_ratio, color="#c0392b", linestyle=":", linewidth=0.8)
    bottom.set_ylabel("changing region\nred ratio R/(R+G+B)")
    bottom.set_ylim(0, 1.0)
    bottom.set_xlabel("time within the segment (s)")
    bottom.grid(alpha=0.25)

    # The window boundaries are the thing being labelled, so they are drawn to be seen.
    for index in range(1, int(seconds)):
        for axis in (top, middle, bottom):
            axis.axvline(index, color="#444", linewidth=0.8, linestyle="--", alpha=0.55)
    for index in range(int(seconds)):
        top.annotate(
            f"w{index}",
            xy=(index + 0.5, 1.0),
            xycoords=("data", "axes fraction"),
            ha="center",
            va="bottom",
            fontsize=7,
            color="#444",
        )

    caption = (
        f"{series['frames']} frames, {series['fps']:.3f} fps nominal, {seconds:.0f} s. "
        f"Vertical lines are the one second windows you are labelling.\n"
        f"Dotted lines: the area limit, {spec.area_fraction_limit:.0%} of a 10 degree field, "
        f"which the solid red line is measured against; and the saturated red ratio "
        f"{spec.red_saturated_ratio}.\n"
        f"A general flash needs a luminance change of at least {spec.general_min_delta} with "
        f"the darker state below {spec.general_dark_image_below}. GUIDE.md quotes all three."
    )
    figure.text(0.01, 0.045, caption, fontsize=7.5, color="#444", va="bottom")
    figure.text(
        0.01,
        0.008,
        "The region series follows whichever pixels changed between frames, an inspection knob "
        "and not a spec rule. Cuts move every panel, so a single step is not a flash.\n"
        "No detector output appears on this figure.",
        fontsize=7.5,
        color="#a33",
        va="bottom",
    )
    figure.tight_layout(rect=(0, 0.10, 1, 0.96))
    figure.savefig(png, dpi=120)
    plt.close(figure)
    return png


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--pool-key", type=Path, default=_EVAL_DIR / "labeling" / "pool_key.json")
    parser.add_argument("--out-dir", type=Path, default=_EVAL_DIR / "labeling" / "plots")
    parser.add_argument("--media", type=Path, default=REPO / "media")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--delta", type=float, default=DEFAULT_DELTA)
    parser.add_argument("--only", action="append", default=None)
    arguments = parser.parse_args()

    key = json.loads(arguments.pool_key.read_text())
    done = 0
    failed = []
    for row in key["segments"]:
        if arguments.only and row["segment_id"] not in set(arguments.only):
            continue
        path = arguments.media / row["file"]
        try:
            render(
                row["segment_id"],
                path,
                float(row["start_s"]),
                float(row["end_s"]) - float(row["start_s"]),
                arguments.out_dir,
                arguments.width,
                arguments.delta,
            )
            done += 1
        except Exception as error:  # noqa: BLE001
            failed.append({"segment_id": row["segment_id"], "error": f"{type(error).__name__}: {error}"})
    print(f"{done} plots written to {arguments.out_dir}, {len(failed)} failed")
    for row in failed:
        print(f"  {row['segment_id']}: {row['error']}", file=sys.stderr)
    # A segment with no figure is a segment nobody can label, and the sheet still asks for it.
    # Exiting 0 with plots missing would let `make labeling-plots` look finished when it is not.
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
