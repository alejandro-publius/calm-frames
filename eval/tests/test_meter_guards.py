"""The meter's guards, and the mutations that were watched going red.

A guard with a green test beside it proves nothing. Every guard below was broken on purpose, the
whole meter test suite was run, the failure text was read, and the guard was put back and its
file checked back to the same SHA-256. Nineteen mutations, on Sep 17, 2026. Eighteen went red.
**One survived, and finding it was the point of doing this.**

| Guard | Mutation | What the failure said |
|---|---|---|
| no flashmap import | added `import flashmap` to eval/meter.py | `meter.py imports flashmap: ['line 62: import flashmap']`, and the subprocess check printed `True` where it wanted `False` |
| nothing opens a player | added `PREVIEW_COMMAND = ["ffplay", "-autoexit"]` to meter.py | `["meter.py line 89 reaches for a player: 'ffplay'"]` |
| hazard clips are deleted | replaced the body of the `finally` in `run_trial` with `pass` | `assert [PosixPath('/..._camera.mp4')] == []`, on both the clean path and the one where the meter raises |
| the scratch directory is outside the repo | pointed the default at `media/_mutation` | `/Users/<user>/calm-frames/media/_mutation is inside the repository` |
| an uncalibrated run is not publishable | made `publishable` unconditionally True | `assert True is False`, on the uncalibrated report and on the clipped one |
| a clipped run is not publishable | dropped the clipped term from `publishable` | `assert True is False` |
| the area rule | changed `> area_fraction_limit` to `>= 0.0` | `assert 240 == 1`: a 1 Hz strobe read as 240 flashes a second, and 21 tests fell over |
| thresholds come from the spec file | typed `0.10` in place of `self.spec.general_min_delta` | `assert 11 == 0`: the meter kept counting under an edited spec file that forbids it |
| same direction transitions collapse | put flashmap's pairing back | `assert 12 == 6` |
| the gray field flicker check | made `passes` unconditionally True | `assert True is False` |
| a screen too small to be a TV is refused | lowered the floor to 0 | `Failed: DID NOT RAISE RoiError` |
| a mostly clipped chart is refused | lowered the patch floor to 0 | `Failed: DID NOT RAISE CalibrationError` |
| a chart read in the wrong place is refused | replaced the monotone test with `if False` | `Regex pattern did not match` |
| a fit an affine model cannot follow is refused | raised the residual ceiling to 99 | `Failed: DID NOT RAISE CalibrationError` |
| the ingest refuses to write with no footage | replaced `if not usable` with `if False` | `assert 0 == 2`, and the empty report file appeared |
| a log out by more than half a period is refused | raised the slip ceiling to 1e9 | `assert True is False` |
| the covered reference is a low percentile | swapped the tenth percentile for the median | `assert 0.5 < 0.1`: a cover that went on late dragged the reference up to meet it |

**The survivor.** The ceiling on how much of the camera frame a screen may fill was raised to 99
and nothing went red. The guard was unreachable: the area was measured after the bezel inset
came off the rectangle, and a box covering the entire frame came out at 0.895 against a ceiling
of 0.90. Both area checks now run on the lit rectangle before the inset, and
`test_a_screen_that_fills_the_whole_frame_is_refused` covers the ceiling. Mutated again
afterwards: `Failed: DID NOT RAISE RoiError`.

Two guards in this file are about the committed `results/meter_validation.json` rather than
about code, so they were checked by editing that file instead, restoring it and checking its
SHA-256 back. Removing a `denominator` from one of its rates:
`AssertionError: verdict_agreement is missing denominator`.

The other one is worth reading twice. Deleting "Simulated footage only. " from the front of the
statement changed nothing, because the statement says "simulated" again further along. The guard
was fine; the mutation was too weak to reach it. Taking out every spelling of the word did it:
`the validation file does not say it is simulated`. A mutation that survives is a question, not
an answer, and the question here was which of the two was broken.

Running these also found a test of mine that was wrong rather than a guard that was missing. A
Wilson interval on zero successes comes back with a lower end of 2.8e-17, and an assertion that
the rate sits inside its own interval failed on that, on the real committed file. The assertion
now carries a nanosecond of slack and says why.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import meter
import meter_camera
import meter_validate

EVAL_DIR = Path(__file__).resolve().parents[1]
REPO = EVAL_DIR.parent
METER_MODULES = sorted(EVAL_DIR.glob("meter*.py"))
VALIDATION = REPO / "results" / "meter_validation.json"

# Anything that would put moving pictures in front of a person. The meter reads hazard footage
# and must never show it: plots only, per CLAUDE.md.
PLAYER_WORDS = (
    "ffplay",
    "vlc",
    "mpv",
    "quicktime",
    "imshow",
    "webbrowser",
    "plt.show",
    "pyplot.show",
    "open -a",
    "xdg-open",
    "startfile",
)


def test_there_are_meter_modules_to_check():
    """A glob that matched nothing would make every guard below vacuously green."""
    assert len(METER_MODULES) >= 3, [p.name for p in METER_MODULES]


def _flashmap_imports(source: str) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "flashmap":
                    found.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == "flashmap":
                found.append(f"line {node.lineno}: from {node.module} import ...")
    return found


@pytest.mark.parametrize("path", METER_MODULES, ids=lambda p: p.name)
def test_the_meter_does_not_import_flashmap(path: Path):
    """The meter checks whether the thing flashmap protects stayed covered on a real screen.

    If it counted flashes with flashmap's own code, a flash pattern flashmap cannot see would be
    invisible to both, and the check would agree with the thing it is checking for the worst
    possible reason.
    """
    offenders = _flashmap_imports(path.read_text())
    assert not offenders, f"{path.name} imports flashmap: {offenders}"


def test_importing_the_meter_does_not_pull_flashmap_in():
    """The syntax tree cannot see flashmap arriving through something else."""
    program = (
        "import sys; sys.path.insert(0, %r);"
        "import meter, meter_camera, meter_validate, meter_ingest;"
        "print(any(n == 'flashmap' or n.startswith('flashmap.') for n in sys.modules))"
        % str(EVAL_DIR)
    )
    out = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, timeout=180
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False", "importing the meter reached flashmap"


@pytest.mark.parametrize("path", METER_MODULES, ids=lambda p: p.name)
def test_nothing_in_the_meter_opens_a_player(path: Path):
    """Hazard footage is inspected as a plot or not at all."""
    offenders = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'"):
            continue
        lowered = line.lower()
        for word in PLAYER_WORDS:
            if word in lowered:
                offenders.append(f"{path.name} line {number} reaches for a player: {word!r}")
    assert not offenders, offenders


def test_the_scratch_directory_is_outside_the_repository_and_owner_only(tmp_path, monkeypatch):
    monkeypatch.setenv("CALM_METER_SCRATCH", str(tmp_path / "hazard"))
    directory = meter_camera.scratch_dir()
    assert not directory.resolve().is_relative_to(REPO.resolve()), (
        f"{directory} is inside the repository"
    )
    assert (os.stat(directory).st_mode & 0o777) == 0o700


def test_the_default_scratch_directory_is_outside_the_repository_too(tmp_path, monkeypatch):
    monkeypatch.delenv("CALM_METER_SCRATCH", raising=False)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    directory = meter_camera.scratch_dir()
    assert not directory.resolve().is_relative_to(REPO.resolve()), (
        f"{directory} is inside the repository"
    )


@pytest.fixture()
def scratch(tmp_path, monkeypatch):
    monkeypatch.setenv("CALM_METER_SCRATCH", str(tmp_path / "hazard"))
    return meter_camera.scratch_dir()


def tiny_trial(name: str = "guard") -> meter_validate.Trial:
    """The smallest trial that still renders, films and meters a real file."""
    return meter_validate.Trial(
        name=name,
        arm="rate",
        clip=meter_camera.DisplayClip(
            name=name, flash_hz=6.0, duration_ms=250.0, width=96, height=64, display_fps=120
        ),
        model=meter_camera.CameraModel(fps=120.0, width=128, height=96, blur_sigma=0.6),
        expected_peak_per_second=6.0,
        expected_above_limit=True,
        expected_leaks=1,
        what_it_tests="the guard tests use it, nothing is published from it",
    )


def test_a_hazard_clip_is_gone_by_the_time_the_trial_returns(scratch):
    pytest.importorskip("av")
    settings = meter.InstrumentSettings(analysis_width=32)
    roi = meter.Roi(0.0, 0.0, 1.0, 1.0, method="explicit")
    row = meter_validate.run_trial(tiny_trial(), settings, scratch, roi, None, {})
    assert "error" not in row, row.get("error")
    assert list(scratch.glob("HAZARD_*")) == []


def test_a_hazard_clip_is_gone_even_when_the_meter_blows_up(scratch, monkeypatch):
    pytest.importorskip("av")

    def explode(*args, **kwargs):
        raise RuntimeError("pretend the meter fell over")

    monkeypatch.setattr(meter, "run_file", explode)
    settings = meter.InstrumentSettings(analysis_width=32)
    roi = meter.Roi(0.0, 0.0, 1.0, 1.0, method="explicit")
    row = meter_validate.run_trial(tiny_trial("blowup"), settings, scratch, roi, None, {})
    assert "error" in row and "fell over" in row["error"]
    assert list(scratch.glob("HAZARD_*")) == []


def test_the_sweep_removes_anything_a_crash_left_behind(scratch):
    leftover = scratch / f"{meter_camera.HAZARD_PREFIX}left_over.mp4"
    leftover.write_bytes(b"not a real clip, but it has the name")
    assert meter_camera.sweep_leftovers(fail=False) == 1
    assert not leftover.exists()
    assert meter_camera.sweep_leftovers(fail=False) == 0


def test_the_sweep_can_be_made_to_fail_loudly(scratch):
    leftover = scratch / f"{meter_camera.HAZARD_PREFIX}loud.mp4"
    leftover.write_bytes(b"x")
    with pytest.raises(AssertionError, match="outlived their job"):
        meter_camera.sweep_leftovers(fail=True)


def test_a_clipped_run_is_not_publishable():
    """A camera that clips reads bright states low, so it can only under-count. Never publish."""
    import numpy as np

    settings = meter.InstrumentSettings(analysis_width=16)
    calibration = meter.calibrate(
        _filmed_chart(), meter.Roi(0.0, 0.0, 1.0, 1.0, method="explicit"), steps=10
    )
    frames = ((np.full((16, 16, 3), 255, dtype=np.uint8), index * 4.0) for index in range(8))
    report = meter.run_frames(
        frames,
        roi=meter.Roi(0.0, 0.0, 1.0, 1.0, method="explicit"),
        calibration=calibration,
        settings=settings,
    ).report()
    assert report.quality["clipped_frame_fraction"] > 0
    assert report.publishable is False
    assert any("clipped" in w for w in report.quality["warnings"])


def _filmed_chart():
    import numpy as np

    from conformance.spec import load_spec

    spec = load_spec()
    chart = meter.step_chart_image(200, 120, 10)
    linear = meter._linear_from_srgb8(spec, chart.astype(np.float64))
    sensor = np.clip(linear * 0.8 + 0.01, 0.0, 1.0)
    return [np.clip(np.round(255.0 * sensor ** (1 / 2.2)), 0, 255).astype(np.uint8)]


# ---------------------------------------------------------------- the committed numbers


@pytest.mark.skipif(not VALIDATION.exists(), reason="results/meter_validation.json not written")
def test_the_validation_file_says_what_it_is():
    payload = json.loads(VALIDATION.read_text())
    statement = payload["statement"].lower()
    assert "simulated" in statement, "the validation file does not say it is simulated"
    assert payload["summary"]["interval_method"].lower().startswith("wilson")
    assert payload["thresholds"]["source"].endswith("SPEC_SOURCES.md")
    assert payload["what_this_does_not_cover"], "nothing is listed as out of scope"


@pytest.mark.skipif(not VALIDATION.exists(), reason="results/meter_validation.json not written")
def test_every_published_rate_carries_its_counts_and_its_interval():
    payload = json.loads(VALIDATION.read_text())
    summary = payload["summary"]
    for key, entry in summary.items():
        if not isinstance(entry, dict) or "value" not in entry:
            continue
        for field in ("numerator", "denominator", "wilson_lo", "wilson_hi"):
            assert field in entry, f"{key} is missing {field}"
        assert entry["wilson_lo"] <= entry["wilson_hi"]
        if entry["denominator"]:
            # The slack is float noise, not room for a wrong number. A Wilson interval on zero
            # successes comes back with a lower end of 2.8e-17 rather than 0, which is the
            # quadratic being solved in floating point and not a claim that the rate is above
            # zero. Anything a reader could see is still caught.
            slack = 1e-9
            assert entry["wilson_lo"] - slack <= entry["value"] <= entry["wilson_hi"] + slack


@pytest.mark.skipif(not VALIDATION.exists(), reason="results/meter_validation.json not written")
def test_no_trial_in_the_committed_run_left_a_hazard_clip_behind():
    """Belt and braces: the scratch directory named in the run holds nothing now."""
    directory = meter_camera.scratch_dir()
    assert list(directory.glob("HAZARD_*")) == []
