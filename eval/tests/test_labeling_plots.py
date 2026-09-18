"""The figures the labellers read: blind, and never quietly missing.

The series drawn in these tests are FABRICATED FOR TEST ONLY. They are a sine wave and a square
wave invented here, they describe no real clip, no video file is opened, and no figure written
here goes near eval/labeling/plots/.

What this holds the plots to:

- the figure names the segment by its opaque id and says nothing that could identify the title,
  the source or which detector proposed it. The whole exercise is worthless if the labeller can
  tell where a segment came from;
- a plot that failed to render makes the run fail. A segment with no figure still sits on the
  sheet asking for an answer, so a silent failure hands the labeller an impossible row;
- the status report refuses while any segment has no plot, rather than reporting the set as
  ready for labelling.

To see them fail on purpose: see the note on each test. All three were verified Sep 17, 2026.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

EVAL_DIR = Path(__file__).resolve().parents[1]
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from labeling import plots as labelling_plots  # noqa: E402

REPO = EVAL_DIR.parent
FABRICATED_FOR_TEST_ONLY = True

# What the labeller must never be able to read off a figure.
GIVEAWAYS = (
    "tears_of_steel",
    "HAZARD_",
    "Blender",
    "Wikimedia",
    "DVIDS",
    "NASA",
    "flashmap",
    "ffmpeg_photosensitivity",
    "naive_luma_diff",
    "proposed",
)


def fabricated_series(frames: int = 250, fps: float = 25.0) -> dict:
    """A square wave and a ramp. Invented here, and not a measurement of anything."""
    times = np.arange(frames) / fps
    square = np.where((np.arange(frames) // 3) % 2 == 0, 0.6, 0.1)
    return {
        "times_s": times,
        "whole_picture_luminance": square,
        "changing_region_luminance": square,
        "changing_area_fraction": np.full(frames, 0.4),
        "changing_field_coverage": np.full(frames, 0.8),
        "changing_region_red_ratio": np.linspace(0.2, 0.9, frames),
        "frames": frames,
        "fps": fps,
    }


def figure_text(figure) -> str:
    """Every word drawn on a figure: its own texts, and each axis's labels and annotations."""
    parts = [text.get_text() for text in figure.texts]
    for axis in figure.axes:
        parts.append(axis.get_title())
        parts.append(axis.get_xlabel())
        parts.append(axis.get_ylabel())
        parts.extend(text.get_text() for text in axis.texts)
        legend = axis.get_legend()
        if legend is not None:
            parts.extend(entry.get_text() for entry in legend.get_texts())
    return "\n".join(part for part in parts if part)


def test_the_figure_names_the_segment_and_nothing_else(monkeypatch, tmp_path):
    """Break it: draw the file name in the suptitle, and this goes red naming it."""
    monkeypatch.setattr(
        labelling_plots, "trace", lambda *args, **kwargs: fabricated_series()
    )

    captured = {}
    real_subplots = labelling_plots.plt.subplots

    def spy(*args, **kwargs):
        figure, axes = real_subplots(*args, **kwargs)
        captured["figure"] = figure
        return figure, axes

    monkeypatch.setattr(labelling_plots.plt, "subplots", spy)

    png = labelling_plots.render(
        "seg999",
        Path("media/HAZARD_tears_of_steel_720p.mov"),
        120.0,
        10.0,
        tmp_path,
    )
    assert png.is_file()

    drawn = figure_text(captured["figure"])
    assert "seg999" in drawn
    for giveaway in GIVEAWAYS:
        assert giveaway not in drawn, f"the figure shows {giveaway!r}"


def test_a_plot_that_failed_makes_the_run_fail(tmp_path):
    """Break it: return 0 from main() whatever happened, and this goes red."""
    key = tmp_path / "pool_key.json"
    key.write_text(
        json.dumps(
            {
                "segments": [
                    {
                        "segment_id": "seg999",
                        "file": "invented_missing_clip_for_test_only.mp4",
                        "start_s": 0.0,
                        "end_s": 10.0,
                    }
                ]
            }
        )
    )
    finished = subprocess.run(
        [
            sys.executable,
            str(EVAL_DIR / "labeling" / "plots.py"),
            "--pool-key",
            str(key),
            "--out-dir",
            str(tmp_path / "plots"),
            "--media",
            str(tmp_path / "no-media-here"),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert finished.returncode != 0, finished.stdout
    assert "seg999" in finished.stderr


def test_the_status_report_refuses_while_a_plot_is_missing(tmp_path):
    """Break it: drop the missing_plots check in report.py, and this goes red."""
    real_key = EVAL_DIR / "labeling" / "pool_key.json"
    if not real_key.is_file():
        pytest.skip("the blinded pool has not been built yet")
    key = json.loads(real_key.read_text())
    key["segments"] = key["segments"][:1] + [
        {
            "segment_id": "seg_invented_no_plot",
            "file": "invented_for_test_only.mp4",
            "source": "Invented source",
            "start_s": 0.0,
            "end_s": 10.0,
            "proposed_by": [],
            "from_unflagged_time": True,
        }
    ]
    key_path = tmp_path / "pool_key.json"
    key_path.write_text(json.dumps(key))

    finished = subprocess.run(
        [
            sys.executable,
            str(EVAL_DIR / "realclips" / "report.py"),
            "--pool-key",
            str(key_path),
            "--status-out",
            str(tmp_path / "status.json"),
            "--labels",
            str(EVAL_DIR / "labeling" / "labels_labeller_a.csv"),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert finished.returncode == 2, finished.stdout
    assert "no plot" in finished.stderr
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["state"].startswith("not ready")
    assert status["plots"]["missing"] == ["seg_invented_no_plot"]


def test_a_stale_figure_is_removed_before_the_render_that_might_fail(tmp_path):
    """A figure from an earlier pool must not survive a failed re-render.

    The PNG written here is FABRICATED FOR TEST ONLY: four bytes that are not an image. It
    stands for seg999's figure from a previous pool, where seg999 was a different segment.

    Break it: take the unlink out of main(), and this goes red with the stale bytes still
    there, which is the labeller reading the wrong picture under the right name.
    """
    out = tmp_path / "plots"
    out.mkdir()
    stale = out / "seg999.png"
    stale.write_bytes(b"old!")

    key = tmp_path / "pool_key.json"
    key.write_text(
        json.dumps(
            {
                "segments": [
                    {
                        "segment_id": "seg999",
                        "file": "invented_missing_clip_for_test_only.mp4",
                        "start_s": 0.0,
                        "end_s": 10.0,
                    }
                ]
            }
        )
    )
    finished = subprocess.run(
        [
            sys.executable,
            str(EVAL_DIR / "labeling" / "plots.py"),
            "--pool-key",
            str(key),
            "--out-dir",
            str(out),
            "--media",
            str(tmp_path / "no-media-here"),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert finished.returncode != 0
    assert not stale.exists(), "the figure from the earlier pool is still there"
