#!/usr/bin/env python3
"""Check the meter against footage whose answer is known, and write results/meter_validation.json.

    .venv/bin/python eval/meter_validate.py            # the committed run
    .venv/bin/python eval/meter_validate.py --quick    # a few trials, for a smoke test

What this is
------------
Every trial renders a display clip whose flash rate, amplitude and area are chosen on purpose,
films it with the simulated camera in `eval/meter_camera.py`, and asks the meter what it saw.
The truth is the design of the clip, not another detector, so this measures the meter and
nothing else.

**Everything here is simulated.** No phone, no TV and no stick are involved. It answers "does
the meter count what is in front of it, through blur, noise, an unknown gamma, an exposure
window and a codec", and it cannot answer "does a real phone filming a real TV give the same
number". That question needs the screen-level test in docs/SCREEN_TEST_PROTOCOL.md, and until
those recordings exist, nobody should quote these numbers as camera performance.

Safety
------
Rendered flashing clips and simulated recordings of them are hazardous. Each one is written
under a scratch directory outside the repository, analysed, and deleted in the same `finally`
block. The run sweeps and asserts that none survived. Nothing is opened, played or previewed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

import meter  # noqa: E402
import meter_camera as camera  # noqa: E402
from conformance.spec import load_spec  # noqa: E402
from metrics import wilson  # noqa: E402

REPO = _EVAL_DIR.parent
OUT = REPO / "results" / "meter_validation.json"

# Rates to film. Each one divides the display frame rate into a whole number of frames per half
# period, so the clip really does show the rate it is named after.
RATES_HZ = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 12.0)
QUICK_RATES_HZ = (2.0, 6.0)


@dataclass
class Trial:
    name: str
    arm: str
    clip: camera.DisplayClip
    model: camera.CameraModel
    expected_peak_per_second: float
    expected_above_limit: bool
    expected_leaks: int
    what_it_tests: str


def _code_for_delta(spec, base_code: int, delta: float) -> int:
    """The gray code whose relative luminance sits `delta` above `base_code`."""
    base = float(
        meter._luminance(spec, meter._linear_from_srgb8(spec, np.array([base_code] * 3)))
    )
    target = base + delta
    codes = np.arange(0, 256)
    luminances = np.array(
        [
            float(meter._luminance(spec, meter._linear_from_srgb8(spec, np.array([c] * 3))))
            for c in codes
        ]
    )
    return int(codes[int(np.argmin(np.abs(luminances - target)))])


def build_trials(quick: bool = False) -> list[Trial]:
    spec = load_spec()
    limit = spec.flash_limit_per_second
    duration = 2000.0 if quick else 2500.0
    fast = camera.CameraModel(fps=240.0, exposure_ms=1000.0 / 240.0)
    slow = camera.CameraModel(fps=60.0, exposure_ms=1000.0 / 240.0)
    rates = QUICK_RATES_HZ if quick else RATES_HZ
    trials: list[Trial] = []

    for model, label in ((fast, "240fps"), (slow, "60fps")):
        for rate in rates:
            trials.append(
                Trial(
                    name=f"rate_{rate:g}hz_{label}",
                    arm="rate",
                    clip=camera.DisplayClip(
                        name=f"rate_{rate:g}hz", flash_hz=rate, duration_ms=duration
                    ),
                    model=model,
                    expected_peak_per_second=rate,
                    expected_above_limit=rate > limit,
                    expected_leaks=1 if rate > limit else 0,
                    what_it_tests="does the count match the rate that was filmed",
                )
            )

    if not quick:
        # Red. Gray at code 128 and pure red have almost the same relative luminance, so the
        # general rule stays quiet and only the red rule can fire.
        for model, label in ((fast, "240fps"), (slow, "60fps")):
            trials.append(
                Trial(
                    name=f"red_6hz_{label}",
                    arm="red",
                    clip=camera.DisplayClip(
                        name="red_6hz",
                        flash_hz=6.0,
                        duration_ms=duration,
                        low_rgb=(128, 128, 128),
                        high_rgb=(255, 0, 0),
                        background_rgb=(128, 128, 128),
                    ),
                    model=model,
                    expected_peak_per_second=6.0,
                    expected_above_limit=True,
                    expected_leaks=1,
                    what_it_tests="the red rule, on a pair that barely moves in luminance",
                )
            )

        # Area. A square of side 1/8 of the picture fills (3/8)^2 of a 10 degree window, which is
        # under the area limit, so nothing should be counted. The half width control is over it.
        trials.append(
            Trial(
                name="area_small_patch_240fps",
                arm="area",
                clip=camera.DisplayClip(
                    name="area_small", flash_hz=8.0, duration_ms=duration, patch_fraction=0.125
                ),
                model=fast,
                expected_peak_per_second=0.0,
                expected_above_limit=False,
                expected_leaks=0,
                what_it_tests="a strobe too small to fill a 10 degree window is not counted",
            )
        )
        trials.append(
            Trial(
                name="area_half_patch_240fps",
                arm="area",
                clip=camera.DisplayClip(
                    name="area_half", flash_hz=8.0, duration_ms=duration, patch_fraction=0.5
                ),
                model=fast,
                expected_peak_per_second=8.0,
                expected_above_limit=True,
                expected_leaks=1,
                what_it_tests="the same strobe, big enough to count, still counts",
            )
        )

        # Amplitude, either side of the general flash threshold.
        below = _code_for_delta(spec, 128, spec.general_min_delta * 0.7)
        above = _code_for_delta(spec, 128, spec.general_min_delta * 1.4)
        trials.append(
            Trial(
                name="amplitude_below_threshold_240fps",
                arm="amplitude",
                clip=camera.DisplayClip(
                    name="amp_below",
                    flash_hz=8.0,
                    duration_ms=duration,
                    low_rgb=(128, 128, 128),
                    high_rgb=(below, below, below),
                    background_rgb=(128, 128, 128),
                ),
                model=fast,
                expected_peak_per_second=0.0,
                expected_above_limit=False,
                expected_leaks=0,
                what_it_tests="a swing under the general flash threshold is not counted",
            )
        )
        trials.append(
            Trial(
                name="amplitude_above_threshold_240fps",
                arm="amplitude",
                clip=camera.DisplayClip(
                    name="amp_above",
                    flash_hz=8.0,
                    duration_ms=duration,
                    low_rgb=(128, 128, 128),
                    high_rgb=(above, above, above),
                    background_rgb=(128, 128, 128),
                ),
                model=fast,
                expected_peak_per_second=8.0,
                expected_above_limit=True,
                expected_leaks=1,
                what_it_tests="a swing just over the threshold still counts",
            )
        )

    # Covered runs. This is the reading that matters on the night: with the cover in place the
    # meter beside the TV has to sit at zero.
    covered_models = (fast,) if quick else (fast, slow)
    for model in covered_models:
        label = f"{int(model.fps)}fps"
        trials.append(
            Trial(
                name=f"covered_static_{label}",
                arm="covered",
                clip=camera.DisplayClip(
                    name="covered_static",
                    flash_hz=0.0,
                    duration_ms=duration,
                    background_rgb=(24, 24, 24),
                ),
                model=model,
                expected_peak_per_second=0.0,
                expected_above_limit=False,
                expected_leaks=0,
                what_it_tests="an opaque cover: zero flashes and zero leaks",
            )
        )
    if not quick:
        # The covered runs that are actually worth worrying about. Nothing on the screen is
        # moving, so the only thing that could make the meter count a flash is the camera's own
        # noise, and noise is worst in a dark room at a high ISO. These three turn the noise up
        # and put the screen where the relative noise is largest.
        noisy = dataclasses.replace(
            fast, read_noise=fast.read_noise * 4, shot_noise=fast.shot_noise * 3, seed=4242
        )
        noisy_slow = dataclasses.replace(
            slow, read_noise=slow.read_noise * 4, shot_noise=slow.shot_noise * 3, seed=4243
        )
        for model, label, level in (
            (noisy, "240fps_noisy", 24),
            (noisy_slow, "60fps_noisy", 24),
            (noisy, "240fps_noisy_dark", 8),
        ):
            trials.append(
                Trial(
                    name=f"covered_{label}_{level}",
                    arm="covered",
                    clip=camera.DisplayClip(
                        name=f"covered_{label}",
                        flash_hz=0.0,
                        duration_ms=duration,
                        background_rgb=(level, level, level),
                    ),
                    model=model,
                    expected_peak_per_second=0.0,
                    expected_above_limit=False,
                    expected_leaks=0,
                    what_it_tests=(
                        "a cover filmed with four times the read noise and three times the "
                        "shot noise: the meter still has to sit at zero"
                    ),
                )
            )

        trials.append(
            Trial(
                name="covered_ramp_240fps",
                arm="covered",
                clip=camera.DisplayClip(
                    name="covered_ramp",
                    flash_hz=0.0,
                    duration_ms=duration,
                    background_rgb=(24, 24, 24),
                    ramp_to_rgb=(200, 200, 200),
                ),
                model=fast,
                expected_peak_per_second=0.0,
                expected_above_limit=False,
                expected_leaks=0,
                what_it_tests="a slow fade is a ramp, not flashing, so it stays at zero",
            )
        )
        trials.append(
            Trial(
                name="covered_bright_60fps",
                arm="covered",
                clip=camera.DisplayClip(
                    name="covered_bright",
                    flash_hz=0.0,
                    duration_ms=duration,
                    background_rgb=(180, 180, 180),
                ),
                model=slow,
                expected_peak_per_second=0.0,
                expected_above_limit=False,
                expected_leaks=0,
                what_it_tests="a bright still screen, where camera noise is largest, stays at zero",
            )
        )
    return trials


# How many frames of the gray field and of the chart the reference takes average. The protocol
# asks for about two seconds, which at 240 fps is hundreds, so this is conservative: the fit here
# sees more noise than a real take would. It is not free, because every frame runs the whole
# camera model, which is why it is not hundreds.
REFERENCE_FRAMES = 24


def reference_takes(model: camera.CameraModel, settings: meter.InstrumentSettings):
    """The gray field and the step chart, filmed with this camera. Neither is hazardous.

    This is the protocol in miniature: the region comes from the gray field take, the exposure
    correction from the step chart take, and the run is measured with both. A camera the
    calibration refuses raises here, and the caller records that against every trial that needed
    it instead of losing the run.
    """
    picture = (180, 320)
    gray = np.full((*picture, 3), 128, dtype=np.uint8)
    gray_frames = camera.simulate_static_frames(gray, model, REFERENCE_FRAMES)
    times = [index * 1000.0 / model.fps for index in range(len(gray_frames))]
    roi = meter.find_roi(gray_frames, settings)
    chart = meter.step_chart_image(picture[1], picture[0], 10, settings)
    chart_frames = camera.simulate_static_frames(chart, model, REFERENCE_FRAMES)
    calibration = meter.calibrate(chart_frames, roi, steps=10, settings=settings)
    flicker = meter.flicker_check(
        gray_frames, times, roi, calibration, settings=settings
    )
    flicker["frames_averaged"] = REFERENCE_FRAMES
    return roi, calibration, flicker


def run_trial(
    trial: Trial, settings: meter.InstrumentSettings, scratch: Path, roi, calibration, flicker
) -> dict:
    """One trial, start to finish, leaving nothing behind."""
    started = time.time()
    source = scratch / f"{camera.HAZARD_PREFIX}{trial.name}_display.mp4"
    recording = scratch / f"{camera.HAZARD_PREFIX}{trial.name}_camera.mp4"
    row: dict[str, object] = {
        "trial": trial.name,
        "arm": trial.arm,
        "what_it_tests": trial.what_it_tests,
        "clip": trial.clip.as_dict(),
        "camera": trial.model.as_dict(),
        "expected": {
            "peak_flashes_per_second": trial.expected_peak_per_second,
            "above_limit": trial.expected_above_limit,
            "leaks": trial.expected_leaks,
        },
    }
    try:
        row["display_encode"] = camera.render_display_clip(trial.clip, source)
        display_frames, display_times = camera.decode_display_frames(source)
        frames, stamps = camera.simulate_camera_frames(
            display_frames, display_times, trial.model
        )
        camera.write_recording(frames, stamps, recording, trial.model)
        report = meter.run_file(
            recording, roi=roi, calibration=calibration, settings=settings
        )
        headline = report.headline
        measured_peak = int(headline["peak_flashes_per_second"])
        row["measured"] = {
            "peak_flashes_per_second": measured_peak,
            "general_peak_per_second": report.general["peak_per_second"],
            "red_peak_per_second": report.red["peak_per_second"],
            "above_limit": bool(headline["above_limit"]),
            "leaks": int(headline["leaks"]),
            "frames": report.quality["frames"],
            "fps_measured": report.quality["fps_measured"],
            "clipped_frame_fraction": report.quality["clipped_frame_fraction"],
            "publishable": report.publishable,
        }
        row["verdict_correct"] = bool(headline["above_limit"]) == trial.expected_above_limit
        row["rate_exact"] = measured_peak == int(round(trial.expected_peak_per_second))
        row["rate_within_one"] = (
            abs(measured_peak - trial.expected_peak_per_second) <= 1.0
        )
        row["leaks_correct"] = int(headline["leaks"]) == trial.expected_leaks
        row["flicker_check"] = flicker
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        for path in (source, recording):
            if path.exists():
                path.unlink()
    row["seconds"] = round(time.time() - started, 2)
    return row


def _rate(successes: int, trials: int) -> dict[str, object]:
    lo, hi = wilson(successes, trials)
    return {
        "numerator": successes,
        "denominator": trials,
        "value": (successes / trials) if trials else None,
        "wilson_lo": lo,
        "wilson_hi": hi,
    }


def summarise(rows: list[dict]) -> dict[str, object]:
    done = [r for r in rows if "error" not in r]
    covered = [r for r in done if r["arm"] == "covered"]
    counted = [r for r in done if r["arm"] in {"rate", "red", "area", "amplitude"}]
    qualifying = [
        r for r in counted if float(r["expected"]["peak_flashes_per_second"]) > 0
    ]
    by_fps: dict[str, dict[str, object]] = {}
    for label in sorted({str(int(r["camera"]["fps"])) for r in done}):
        arm = [r for r in qualifying if str(int(r["camera"]["fps"])) == label]
        if arm:
            by_fps[f"{label}fps"] = {
                "exact_rate": _rate(sum(1 for r in arm if r["rate_exact"]), len(arm)),
                "within_one_per_second": _rate(
                    sum(1 for r in arm if r["rate_within_one"]), len(arm)
                ),
                "verdict": _rate(sum(1 for r in arm if r["verdict_correct"]), len(arm)),
            }
    return {
        "trials_run": len(rows),
        "trials_with_an_error": len(rows) - len(done),
        "verdict_agreement": _rate(
            sum(1 for r in done if r["verdict_correct"]), len(done)
        ),
        "exact_rate_agreement_on_flashing_clips": _rate(
            sum(1 for r in qualifying if r["rate_exact"]), len(qualifying)
        ),
        "within_one_per_second_on_flashing_clips": _rate(
            sum(1 for r in qualifying if r["rate_within_one"]), len(qualifying)
        ),
        "covered_runs_with_a_leak": _rate(
            sum(1 for r in covered if int(r["measured"]["leaks"]) > 0), len(covered)
        ),
        "covered_runs_with_any_flash_counted": _rate(
            sum(1 for r in covered if int(r["measured"]["peak_flashes_per_second"]) > 0),
            len(covered),
        ),
        "by_camera_frame_rate": by_fps,
        "interval_method": (
            "Wilson score interval, 95%, two sided, no continuity correction, from "
            "eval/metrics.py. The trials are simulated clips chosen by hand, not a sample from "
            "any population, so the interval describes this simulation and nothing else. A rate "
            "of 0 of n still has an upper bound, which is why it is reported that way."
        ),
    }


def publishable_numbers(rows: list[dict]) -> dict[str, object]:
    """The handful of numbers a document is allowed to quote, each with its counts.

    Nothing reaches a document except through these keys and `eval/readme_sync.py`, which is
    what CLAUDE.md asks for. Every one of them carries its denominator, because a rate without
    one is not a number.
    """
    done = [r for r in rows if "error" not in r]
    counted = [r for r in done if r["arm"] in {"rate", "red", "area", "amplitude"}]
    flashing = [r for r in counted if float(r["expected"]["peak_flashes_per_second"]) > 0]
    covered = [r for r in done if r["arm"] == "covered"]
    errors = [
        int(r["measured"]["peak_flashes_per_second"])
        - float(r["expected"]["peak_flashes_per_second"])
        for r in flashing
    ]

    # The highest designed rate at which every trial, at every camera frame rate, read the rate
    # back exactly. Read off the trials rather than asserted.
    rates = sorted({float(r["expected"]["peak_flashes_per_second"]) for r in flashing})
    exact_up_to = 0.0
    for rate in rates:
        at_rate = [r for r in flashing if float(r["expected"]["peak_flashes_per_second"]) == rate]
        if all(r["rate_exact"] for r in at_rate):
            exact_up_to = rate
        else:
            break

    leaked = sum(1 for r in covered if int(r["measured"]["leaks"]) > 0)
    _, leak_hi = wilson(leaked, len(covered))
    return {
        "trials": len(rows),
        "trials_with_an_error": len(rows) - len(done),
        "verdict_correct": sum(1 for r in done if r["verdict_correct"]),
        "verdict_total": len(done),
        "exact_rate_correct": sum(1 for r in flashing if r["rate_exact"]),
        "exact_rate_total": len(flashing),
        "within_one_correct": sum(1 for r in flashing if r["rate_within_one"]),
        "within_one_total": len(flashing),
        "exact_up_to_hz": exact_up_to,
        "worst_overcount_per_second": max(list(errors) + [0.0]) + 0.0,
        "worst_undercount_per_second": abs(min(list(errors) + [0.0])),
        "covered_runs": len(covered),
        "covered_runs_with_a_leak": leaked,
        "covered_leak_upper_95": leak_hi,
        "note": (
            "Simulated footage, from eval/meter_validate.py. Not a measurement of any phone, "
            "TV or stick."
        ),
    }


def git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--quick", action="store_true", help="a few trials, for a smoke test")
    parser.add_argument("--limit", type=int, help="stop after this many trials")
    args = parser.parse_args(argv)

    settings = meter.InstrumentSettings()
    scratch = camera.scratch_dir()
    trials = build_trials(quick=args.quick)
    if args.limit:
        trials = trials[: args.limit]

    references: dict[str, tuple] = {}
    rows: list[dict] = []
    started = time.time()
    try:
        for index, trial in enumerate(trials, start=1):
            print(f"[{index}/{len(trials)}] {trial.name}", flush=True)
            key = json.dumps(trial.model.as_dict(), sort_keys=True)
            if key not in references:
                # A camera the region finder or the calibration refuses is a result about that
                # camera, not a reason to lose the other twenty-eight trials. It is recorded
                # against every trial that needed it, and it counts as an error.
                try:
                    references[key] = reference_takes(trial.model, settings)
                except Exception as exc:  # noqa: BLE001
                    references[key] = (f"{type(exc).__name__}: {exc}", None, None)
            reference = references[key]
            if isinstance(reference[0], str):
                rows.append(
                    {
                        "trial": trial.name,
                        "arm": trial.arm,
                        "camera": trial.model.as_dict(),
                        "clip": trial.clip.as_dict(),
                        "expected": {
                            "peak_flashes_per_second": trial.expected_peak_per_second,
                            "above_limit": trial.expected_above_limit,
                            "leaks": trial.expected_leaks,
                        },
                        "error": f"the reference takes for this camera were refused: {reference[0]}",
                    }
                )
                print(f"      {rows[-1]['error']}", flush=True)
                continue
            roi, calibration, flicker = reference
            row = run_trial(trial, settings, scratch, roi, calibration, flicker)
            state = row.get("error") or (
                f"peak {row['measured']['peak_flashes_per_second']}/s "
                f"(expected {trial.expected_peak_per_second:g}), "
                f"leaks {row['measured']['leaks']}, {row['seconds']}s"
            )
            print(f"      {state}", flush=True)
            rows.append(row)
    finally:
        left = camera.sweep_leftovers(fail=False)
        if left:
            print(f"swept {left} hazard clips that a failure left behind", file=sys.stderr)

    first_reference = next(
        (r for r in references.values() if not isinstance(r[0], str)), None
    )
    payload = {
        "generated_on": date.today().isoformat(),
        "tool": "eval/meter_validate.py",
        "meter_version": meter.METER_VERSION,
        "git_commit": git_commit(),
        "statement": (
            "Simulated footage only. Every trial is a rendered clip filmed by the camera model "
            "in eval/meter_camera.py, so these numbers say how well the meter reads a simulated "
            "recording whose answer is known. They are not a measurement of any phone, TV or "
            "stick, and they are not evidence that the app covered anything."
        ),
        "thresholds": load_spec().as_dict(),
        "instrument": settings.as_dict(),
        "reference_takes": (
            {
                "roi": first_reference[0].as_dict(),
                "calibration": first_reference[1].as_dict(),
                "gray_field_flicker_check": first_reference[2],
            }
            if first_reference
            else None
        ),
        "summary": summarise(rows),
        "published": publishable_numbers(rows),
        "trials": rows,
        "what_this_does_not_cover": [
            "any real camera: rolling shutter, autoexposure hunting, the camera's colour "
            "matrix, and the beat between the shutter and the panel's refresh are all absent "
            "from the model",
            "any real TV: panel response time, local dimming, motion interpolation and "
            "contrast enhancement are all absent",
            "camera shake, an off-axis view and a reflection on the screen",
            "red flash through a real camera. The step chart is neutral gray, so the fit "
            "corrects luminance and per channel gain, not colour",
            "the live capture path. It is the same code as the file path, with the input "
            "format set, and it has never been run against a physical camera here",
        ],
        "known_issues": [
            {
                "found": "2026-09-17",
                "what": (
                    "the meter read a 6 Hz strobe as 12 flashes a second on simulated camera "
                    "footage, because an exposure window that straddles an edge records a "
                    "middle value and one edge arrived as two steps"
                ),
                "fix": (
                    "a run of transitions in the same direction now counts once for pairing, "
                    "which is what WCAG's 'adjacent peaks and valleys' asks for. See "
                    "GeneralFlashCounter in eval/meter.py"
                ),
                "note": (
                    "flashmap does not need this rule, because a file changes on a frame "
                    "boundary and never shows the middle of an edge. It is worth a look all "
                    "the same, for footage that was itself filmed off a screen."
                ),
            }
        ],
        "runtime_seconds": round(time.time() - started, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")

    summary = payload["summary"]
    print()
    print(f"{summary['trials_run']} trials, {summary['trials_with_an_error']} errors")
    for key in (
        "verdict_agreement",
        "exact_rate_agreement_on_flashing_clips",
        "within_one_per_second_on_flashing_clips",
        "covered_runs_with_a_leak",
    ):
        entry = summary[key]
        print(
            f"  {key:46s} {entry['numerator']}/{entry['denominator']}  "
            f"[{entry['wilson_lo']:.3f}, {entry['wilson_hi']:.3f}]"
        )
    print(f"-> {args.out}")
    failures = [r for r in rows if "error" in r or not r["verdict_correct"]]
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
