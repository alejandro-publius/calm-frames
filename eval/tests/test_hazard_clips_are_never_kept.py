"""The safety guarantee, as a test: a generated strobe never outlives the job that made it.

CLAUDE.md and docs/EVAL_PLAN.md section 1 both say generated conformance clips are hazardous by
design and are generated, analysed and deleted inside one job. That is a property of the code,
so it gets a test rather than a comment.

The clips here are tiny, dull and deleted by the thing under test. They are still written under
the scratch directory, never inside the repository, and never opened.

To see these fail on purpose: take the `finally` out of `run_one`, or make `sweep_leftovers`
return without unlinking, and watch. Verified Sep 17, 2026: both go red.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from conformance import generate_analyze, render
from conformance.spec import load_spec

REPO = Path(__file__).resolve().parents[2]

TINY_CLIP = {
    "clip_id": "testtiny0000000",
    "order_index": -1,
    "axis": "test",
    "resolution": "tiny",
    "width": 160,
    "height": 120,
    "letterbox_fraction": 0.0,
    "shape": "center_rect",
    "area_fraction": 0.25,
    "flash_hz": 6.0,
    "fps": 24,
    "timing": "cfr",
    "crf": 28,
    "color_tagging": "bt709",
    "red_mode": "gray_only",
    "step_multiple": 2.0,
    "dark_multiple": None,
    "duration_ms": 1000.0,
    "flash_start_ms": 250.0,
    "background_rgb": [64, 64, 64],
    "state_a_rgb": [40, 40, 40],
    "state_b_rgb": [200, 200, 200],
    "seed": 1,
}


@pytest.fixture(autouse=True)
def scratch(tmp_path, monkeypatch):
    monkeypatch.setenv("CALM_CONFORMANCE_SCRATCH", str(tmp_path / "hazard"))
    yield tmp_path / "hazard"


def test_the_scratch_directory_is_outside_the_repository_and_owner_only(scratch):
    directory = render.scratch_dir()
    assert not directory.resolve().is_relative_to(REPO.resolve())
    assert (os.stat(directory).st_mode & 0o777) == 0o700


def test_the_default_scratch_directory_is_outside_the_repository_too(tmp_path, monkeypatch):
    """With nothing configured, the fallback still has to land outside the checkout.

    The other test sets CALM_CONFORMANCE_SCRATCH, so it can never exercise the default. TMPDIR
    is pointed at a temporary directory here so the default branch runs for real without
    leaving anything behind.
    """
    monkeypatch.delenv("CALM_CONFORMANCE_SCRATCH", raising=False)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    directory = render.scratch_dir()
    assert not directory.resolve().is_relative_to(REPO.resolve())
    assert directory.resolve().is_relative_to(tmp_path.resolve())


def test_a_clip_is_gone_by_the_time_the_job_returns(scratch):
    pytest.importorskip("av")
    row = generate_analyze.run_one(dict(TINY_CLIP), with_baselines=False)
    assert "error" not in row, row.get("error")
    assert list(scratch.glob("HAZARD_*")) == []


def test_a_clip_is_gone_even_when_the_analysis_blows_up(scratch, monkeypatch):
    pytest.importorskip("av")

    def explode(path):
        raise RuntimeError("pretend the decoder fell over")

    monkeypatch.setattr(generate_analyze, "analyze_flashmap", explode)
    row = generate_analyze.run_one(dict(TINY_CLIP), with_baselines=False)
    assert "error" in row and "decoder fell over" in row["error"]
    assert list(scratch.glob("HAZARD_*")) == []


def test_the_sweep_removes_anything_left_behind_and_says_so(scratch):
    directory = render.scratch_dir()
    leftover = directory / f"{render.HAZARD_PREFIX}left_over.mp4"
    leftover.write_bytes(b"not a real clip, but it has the name")
    assert generate_analyze.sweep_leftovers(fail=False) == 1
    assert not leftover.exists()
    assert generate_analyze.sweep_leftovers(fail=False) == 0


def test_a_rendered_clip_is_owner_readable_only(scratch):
    pytest.importorskip("av")
    directory = render.scratch_dir()
    path = directory / f"{render.HAZARD_PREFIX}permissions.mp4"
    try:
        render.render_clip(dict(TINY_CLIP), path)
        assert (os.stat(path).st_mode & 0o777) == 0o600
    finally:
        if path.exists():
            path.unlink()
    assert list(scratch.glob("HAZARD_*")) == []


def test_the_truth_module_knows_this_clip_without_decoding_it():
    """The ground truth comes from what was drawn, so it needs no file at all."""
    from conformance.truth import clip_truth

    truth = clip_truth(dict(TINY_CLIP), load_spec())
    assert truth.general_qualifies
    assert truth.n_windows == 1
