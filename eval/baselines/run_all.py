#!/usr/bin/env python3
"""The baseline comparison table: every detector on the same clips, windows and metrics.

Writes results/baselines.json. It measures nothing itself. The two local baselines ran on the
same bytes as flashmap, inside the conformance job, before each clip was deleted, and their
per window numbers are in results/conformance_raw.jsonl. This script scores them through the
same code that scores flashmap (eval/conformance/report.py, which uses eval/metrics.py), so
there is one implementation of precision and recall in this repository and not four.

It also records, in the file, which baselines did not run and why, with what was on the machine
at the time. A baseline that is missing for a reason is a fact about the comparison, and the
place for it is the result file, not a footnote somebody has to remember.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.report import build  # noqa: E402

REPO = _EVAL_DIR.parent
OUT = REPO / "results" / "baselines.json"

# Axis slices where a baseline's blind spots have to show up if they are real. Each one is a
# claim in eval/baselines/*/README.md that this file turns into a measurement.
BLIND_SPOT_AXES = {
    "area_fraction_of_picture": (
        "neither baseline has an area rule, so a small strobe that WCAG excuses should still "
        "move their numbers"
    ),
    "red_mode": (
        "neither baseline has a red rule. A luminance matched red flash is invisible to a "
        "relative luminance detector and visible to one that reads gamma encoded luma, so what "
        "they score here is an accident of their colour handling and not the red rule"
    ),
    "flash_rate_hz": (
        "neither baseline has a one second window, so three flashes in a second and three in "
        "ten seconds look the same to them"
    ),
    "near_threshold": "the clips that sit within 15% of a limit, against the ones that do not",
}


def probe_environment() -> dict:
    """What was on this machine when the table was written. Recorded, not assumed."""
    out: dict[str, object] = {}
    try:
        out["ffmpeg"] = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=30
        ).stdout.splitlines()[0]
    except Exception as error:  # noqa: BLE001
        out["ffmpeg"] = f"not available: {error}"

    out["xcode_select_path"] = (
        subprocess.run(["xcode-select", "-p"], capture_output=True, text=True, timeout=30).stdout.strip()
        if shutil.which("xcode-select")
        else "xcode-select not on PATH"
    )

    if shutil.which("docker"):
        try:
            info = subprocess.run(
                [
                    "docker",
                    "info",
                    "--format",
                    "{{.MemTotal}}|{{.NCPU}}|{{.ContainersRunning}}|{{.ServerVersion}}",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            ).stdout.strip()
            memory, cpus, running, version = info.split("|")
            names = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=60,
            ).stdout.split()
            images = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}"],
                capture_output=True,
                text=True,
                timeout=60,
            ).stdout.split()
            out["docker"] = {
                "server_version": version,
                "vm_memory_bytes": int(memory),
                "vm_cpus": int(cpus),
                "containers_running": int(running),
                "container_names": names,
                "iris_image_built": any("iris" in name.lower() for name in images),
            }
        except Exception as error:  # noqa: BLE001
            out["docker"] = f"probe failed: {error}"
    else:
        out["docker"] = "docker not on PATH"
    return out


def not_run(environment: dict) -> dict:
    docker = environment.get("docker")
    if isinstance(docker, dict):
        busy = (
            f"the shared colima VM had {docker['containers_running']} containers from another "
            f"project running on {docker['vm_cpus']} CPUs and "
            f"{docker['vm_memory_bytes'] / 2**30:.1f} GiB"
        )
    else:
        busy = "the Docker VM could not be probed"
    return {
        "EA IRIS": {
            "ran": False,
            "why": (
                "the pinned image at eval/baselines/iris/ has never built, and building it here "
                f"would have taken the shared machine for a long time: {busy}. CLAUDE.md "
                "forbids touching containers, images or volumes this project did not create, "
                "and the build is a vcpkg source build of the whole IRIS dependency tree on "
                "two jobs. Skipped rather than fought, as the lane brief asked."
            ),
            "how_to_run_it_later": "make iris-build, then make iris-run VIDEO=... OUT=...",
            "effect_on_this_table": (
                "no IRIS number appears anywhere in this repository. The cross-check of our "
                "ground truth against IRIS that EVAL_PLAN section 4 asks for has not happened, "
                "so the ground truth stands on the spec text alone."
            ),
        },
        "Apple VideoFlashingReduction": {
            "ran": False,
            "why": (
                "it needs Xcode, and xcode-select reports "
                f"{environment.get('xcode_select_path')!r}, which is Command Line Tools only. "
                "It is also cut list item 4 in EVAL_PLAN section 6, so it was never part of the "
                "committed comparison."
            ),
            "effect_on_this_table": "none, it was never in it",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--design", type=Path, default=REPO / "results" / "conformance_design.json")
    parser.add_argument("--raw", type=Path, default=REPO / "results" / "conformance_raw.jsonl")
    parser.add_argument("-o", "--out", type=Path, default=OUT)
    arguments = parser.parse_args()

    conformance = build(arguments.design, arguments.raw)
    environment = probe_environment()

    blind_spots = {}
    for axis, why in BLIND_SPOT_AXES.items():
        blind_spots[axis] = {"why_this_axis": why, "points": conformance["error_curves"][axis]}

    report = {
        "generated_on": conformance["generated_on"],
        "git_commit": conformance["git_commit"],
        "set": "the generated conformance suite, the same clips and windows for every detector",
        "sample": conformance["sample"],
        "exclusions": conformance["exclusions"],
        "table": conformance["baseline_table_windows_every_detector_saw"],
        "table_universe": (
            "the windows every detector saw. ffmpeg's photosensitivity filter has its first "
            "second dropped, so window 0 of every clip is missing from its denominator, and "
            "leaving it in the others' denominators would compare them on different windows."
        ),
        "flashmap_over_all_windows": conformance["headline_all_windows"],
        "flashmap_over_all_windows_note": (
            "flashmap hides the whole failing one second period, which begins in the calm "
            "second before the flashing. Over all windows that shows as false positives, and "
            "it is the difference between the two tables here. Neither number is the flattering "
            "one to quote on its own."
        ),
        "operating_points": conformance["baseline_operating_points"],
        "blind_spots_measured": blind_spots,
        "environment_when_written": environment,
        "not_run": not_run(environment),
        "what_the_baselines_are": {
            "naive mean luminance differencing": (
                "one number per frame, the mean of the luma plane, thresholded on the change "
                "between frames. No area, no colour, no one second window, no linear light. "
                "eval/baselines/naive_luma_diff/run.py"
            ),
            "ffmpeg photosensitivity filter": (
                "a mitigator, not a reporter: it rewrites frames it thinks are unsafe, so a "
                "flag is inferred from where its output differs from the unfiltered decode. "
                "Its first second is dropped. eval/baselines/ffmpeg_photosensitivity/run.py"
            ),
            "not a safety claim": (
                "neither baseline is a safety tool and neither one's output is a conformance "
                "result. They are here to show what has to be added on top."
            ),
        },
    }
    report["published"] = {
        **conformance["published"],
        "iris_ran": False,
        "apple_videoflashingreduction_ran": False,
        "detectors_compared": len(report["table"]),
    }
    arguments.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(f"wrote {arguments.out}")
    for name, row in report["table"].items():
        print(
            f"  {name[:64]:64s} P={row['precision']['value']} R={row['recall']['value']} "
            f"F1={row['f1']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
