#!/usr/bin/env python3
"""Rebuild every table and figure we publish, from what is committed.

    make reproduce

The rule for this project is that a published number comes from a file in
results/ and that anyone can rebuild it. This does the rebuilding, offline, in
a fresh clone, with no device, no AWS account and no network.

It rebuilds into build/reproduce/ and compares against what is committed rather
than overwriting results/. Two reasons: a rebuild that quietly rewrites the
thing it is checking against can never fail, and several lanes work in this
checkout at once, so nothing here should dirty their tree.

What cannot be rebuilt offline is named rather than skipped in silence. The
media pool is licence checked downloads that are not committed, and the device
runs need a device.

    make reproduce REPRODUCE_ARGS=--with-baselines   also the two baselines
    make reproduce REPRODUCE_ARGS=--with-screening   also the GATE 2 screening
    make reproduce REPRODUCE_ARGS=--strict           a figure whose bytes moved fails
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "build" / "reproduce"
# The repository .venv when there is one, PY when the caller names one, and
# otherwise the interpreter running this script, so a clone with no .venv
# still gets a clear failure from the check and not a missing file.
_VENV = REPO / ".venv" / "bin" / "python"
PY = os.environ.get("PY") or (str(_VENV) if _VENV.exists() else sys.executable)

# Fields that move every run and say nothing about the result.
VOLATILE = {"recorded_utc", "source_events"}

MEDIA_SUFFIXES = (".mp4", ".mov", ".webm", ".ogv", ".mkv", ".m4v")


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []
        self.failed = False

    def add(self, what: str, verdict: str, detail: str = "") -> None:
        self.rows.append((what, verdict, detail))
        if verdict in ("DRIFT", "ERROR"):
            self.failed = True

    def print(self) -> None:
        width = max(len(row[0]) for row in self.rows)
        print()
        print("Result")
        print("-" * (width + 30))
        for what, verdict, detail in self.rows:
            print(f"  {what.ljust(width)}  {verdict:<8} {detail}")
        print()


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=REPO, capture_output=True, text=True, **kwargs)


def strip_volatile(data: object) -> object:
    if isinstance(data, dict):
        return {k: strip_volatile(v) for k, v in data.items() if k not in VOLATILE}
    if isinstance(data, list):
        return [strip_volatile(v) for v in data]
    return data


def first_difference(left: object, right: object, path: str = "") -> str | None:
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            if key not in left:
                return f"{path}.{key} only in the rebuilt file"
            if key not in right:
                return f"{path}.{key} only in the committed file"
            found = first_difference(left[key], right[key], f"{path}.{key}")
            if found:
                return found
        return None
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return f"{path} has {len(left)} entries, committed has {len(right)}"
        for index, (a, b) in enumerate(zip(left, right)):
            found = first_difference(a, b, f"{path}[{index}]")
            if found:
                return found
        return None
    if left != right:
        return f"{path}: rebuilt {left!r}, committed {right!r}"
    return None


def published_numbers(report: Report) -> None:
    """Every marked number in README.md and docs/ against results/."""
    result = run([PY, "eval/readme_sync.py", "--check"])
    tail = (result.stdout + result.stderr).strip().splitlines()
    detail = tail[-1] if tail else ""
    if result.returncode == 0:
        report.add("published numbers", "PASS", detail)
    else:
        report.add("published numbers", "DRIFT", detail)
        print(result.stdout)
        print(result.stderr, file=sys.stderr)


def gate1_rehearsal(report: Report) -> None:
    """The GATE 1 analysis, rebuilt from the events committed beside it."""
    committed = REPO / "results/gate1_rehearsal_vvd.json"
    events = REPO / "results/vvd_timeupdate_stats_events.json"
    schedule = REPO / "eval/harness_runs/marker_schedule.json"
    for needed in (committed, events, schedule):
        if not needed.exists():
            report.add("GATE 1 rehearsal", "SKIP", f"{needed.relative_to(REPO)} is missing")
            return

    rebuilt = OUT / "gate1_rehearsal_vvd.json"
    result = run(
        [
            PY,
            "eval/gate1_rehearsal.py",
            "--events",
            str(events),
            "--schedule",
            str(schedule),
            "--out",
            str(rebuilt),
        ]
    )
    if result.returncode != 0:
        report.add("GATE 1 rehearsal", "ERROR", result.stderr.strip().splitlines()[-1:][0] if result.stderr.strip() else "")
        return

    difference = first_difference(
        strip_volatile(json.loads(rebuilt.read_text())),
        strip_volatile(json.loads(committed.read_text())),
    )
    if difference is None:
        # The eval lane owns this analysis and its fields move as they sharpen
        # what the rehearsal may claim, so read it by asking, not by assuming.
        counts = json.loads(rebuilt.read_text())
        in_schedule = counts.get("markers_in_schedule", "?")
        counted = counts.get("markers_counted", counts.get("markers_reached_during_run"))
        covered = counts.get("markers_covered_in_time", "?")
        detail = f"matches results/. It counts {counted} of {in_schedule} markers"
        if counted in (0, None):
            detail += " (the run it came from reached no marker, so it claims nothing)"
        else:
            detail += f", {covered} covered in time, worst lead {counts.get('worst_lead_ms')} ms"
        report.add("GATE 1 rehearsal", "PASS", detail)
    else:
        report.add("GATE 1 rehearsal", "DRIFT", difference)


def source_for_plot(png: Path) -> Path | None:
    stem = png.name.replace("_luminance_and_area.png", "")
    for candidate_stem in (stem, f"HAZARD_{stem}", stem.replace("HAZARD_", "")):
        for suffix in MEDIA_SUFFIXES:
            candidate = REPO / "media" / f"{candidate_stem}{suffix}"
            if candidate.exists():
                return candidate
    return None


def figures(report: Report, strict: bool) -> None:
    """The inspection plots in results/plots, rebuilt from the media pool.

    One wrinkle worth knowing before reading the output: the plot prints the
    file name across the top, and the screening run renames anything it flags
    to HAZARD_<name>. So a figure made before its clip was renamed can never
    match byte for byte again, and that is not drift. It is counted and named
    separately.
    """
    committed_dir = REPO / "results" / "plots"
    pngs = sorted(committed_dir.glob("*_luminance_and_area.png"))
    if not pngs:
        report.add("figures", "SKIP", "no figures committed")
        return

    out_dir = OUT / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    same = 0
    renamed: list[str] = []
    moved: list[str] = []
    skipped: list[str] = []

    for png in pngs:
        source = source_for_plot(png)
        if source is None:
            skipped.append(png.name)
            continue
        result = run([PY, "eval/plots.py", str(source), "-o", str(out_dir)])
        if result.returncode != 0:
            report.add("figures", "ERROR", f"{png.name}: {result.stderr.strip()[-200:]}")
            return
        new = out_dir / f"{source.stem}_luminance_and_area.png"
        if not new.exists():
            moved.append(f"{png.name}: nothing was written")
        elif new.name != png.name:
            renamed.append(f"{png.name} is now {new.name}")
        elif new.read_bytes() == png.read_bytes():
            same += 1
        else:
            moved.append(png.name)

    rebuilt = len(pngs) - len(skipped)
    detail = f"{rebuilt} rebuilt, {same} byte for byte identical"
    if renamed:
        detail += f", {len(renamed)} from a clip that screening renamed ({renamed[0]})"
    if skipped:
        detail += f", {len(skipped)} skipped (source not in media/)"
    if moved:
        detail += f", {len(moved)} differ: {moved[0]}"
        report.add("figures", "DRIFT" if strict else "NOTE", detail)
        return
    report.add("figures", "PASS" if rebuilt else "SKIP", detail)


def baselines(report: Report) -> None:
    """The two baselines. They read the media pool, which is not committed."""
    if not any((REPO / "media").glob("*.mp4")):
        report.add("baselines", "SKIP", "no media pool in this checkout")
        return
    for target, label in (
        ("ffmpeg-ps-pool", "ffmpeg photosensitivity"),
        ("naive-luma-pool", "naive luminance"),
    ):
        result = subprocess.run(
            ["make", target, f"FFPS_OUT={OUT}/baselines/ffmpeg_photosensitivity",
             f"NL_OUT={OUT}/baselines/naive_luma_diff"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        verdict = "PASS" if result.returncode == 0 else "ERROR"
        report.add(f"baseline: {label}", verdict, f"into {OUT.name}/baselines")


def screening(report: Report) -> None:
    """The GATE 2 screening table. Reads the media pool, so not offline."""
    if not any((REPO / "media").glob("*.mp4")):
        report.add("screening", "SKIP", "no media pool in this checkout")
        return
    rebuilt = OUT / "screening.json"
    result = run([PY, "eval/screen.py", "--out", str(rebuilt), "--no-rename"])
    if result.returncode != 0:
        report.add("screening", "ERROR", result.stderr.strip()[-200:])
        return
    committed = json.loads((REPO / "results/screening.json").read_text())
    fresh = json.loads(rebuilt.read_text())
    left = committed.get("totals", {}).get("flagged_segments")
    right = fresh.get("totals", {}).get("flagged_segments")
    verdict = "PASS" if left == right else "DRIFT"
    report.add("screening", verdict, f"flagged segments: rebuilt {right}, committed {left}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--with-baselines", action="store_true", help="also rerun the two baselines over the media pool")
    parser.add_argument("--with-screening", action="store_true", help="also rerun the GATE 2 screening")
    parser.add_argument("--strict", action="store_true", help="a figure whose bytes moved is a failure")
    parser.add_argument("--clean", action="store_true", help="throw away build/reproduce first")
    args = parser.parse_args()

    # Line buffering, so a run through tee or into a log file shows its
    # progress rather than arriving all at once at the end.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    if args.clean and OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    print("Reproduce: rebuild what the documents publish, from what is committed.")
    print(f"Rebuilding into {OUT.relative_to(REPO)}. Nothing in results/ is overwritten.")
    print()

    report = Report()
    published_numbers(report)
    gate1_rehearsal(report)
    figures(report, args.strict)
    if args.with_baselines:
        baselines(report)
    if args.with_screening:
        screening(report)

    report.print()

    print("Not rebuildable offline, and why:")
    print("  results/baselines/*   needs the media pool. Get it with eval/fetch_media.py,")
    print("                        then: make reproduce REPRODUCE_ARGS=--with-baselines")
    print("  results/screening.json")
    print("                        the same pool. make reproduce REPRODUCE_ARGS=--with-screening")
    print("  results/vvd_*.json    needs a device. make stick-day")
    print("  media/*               licence checked downloads, never committed. See media/LICENSES.csv")
    print()

    if report.failed:
        print("Reproduce FAILED. A published number or a rebuilt table moved.")
        return 1
    print("Reproduce passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
