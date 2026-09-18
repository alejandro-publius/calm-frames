#!/usr/bin/env python3
"""Baseline: EA IRIS, through its own example console app.

IRIS (https://github.com/electronicarts/IRIS, BSD-3-Clause) is the closest thing to a peer this
project has: a published photosensitivity analyser with a luminance flash rule, a red flash
rule, an area rule and a one second transition window. It is not our code and it is not a
conformance oracle. It is here so that flashmap's candidate list is not the only list the real
clip pool is drawn from, which is the difference between a recall estimate and a recall
estimate that flatters the detector that produced the pool.

What this script does, and nothing more: it runs `IrisApp -v <clip> -j 1` in a scratch working
directory, reads the per frame `framedata.csv` that IRIS writes, and turns the failing frames
into intervals in the shared report schema of eval/baselines/README.md. It never opens a clip
in a player. IRIS itself only decodes frames; its one `cv::imshow` call sits behind
`DEBUG_PATTERN_DETECTION`, which this build does not define, so no window is ever drawn.

Which frames count as flagged. `framedata.csv` carries `LuminanceFrameResult` and
`RedFrameResult` per frame, each one of 0 pass, 1 pass with warning, 2 extended fail, 3 flash
fail, and `PatternFrameResult`, 0 pass or 1 fail. A frame joins a segment when any of the three
is a failure, which is 2 or above for the two flash results and 1 for the pattern result. IRIS's
"pass with warning" is flashing between 2 and 3 Hz, which IRIS passes, so it is counted and
reported as `warning_frames` and is not a segment. `--include-warnings` moves that line, and
whichever way it is set is recorded in `params`.

A flagged frame covers the frame it is, so its interval is [t, t + one frame), and consecutive
flagged frames merge when the gap between them is under `--gap`. Without the frame duration a
single flagged frame would be a zero length interval, and the shared window mapping in
eval/metrics.py drops an interval whose end is not after its start, which would lose it in
silence.

Every run is cross-checked against IRIS's own verdict. IRIS writes `result.json` beside the
frame data and calls a video Fail when any frame is an extended fail or a flash fail, which is
the same line this script draws. If the two disagree the run stops rather than writing a report,
because a parse that read the wrong column would pass every other check here and hand the pool
an empty candidate list without a word.

The IrisApp binary is not in this repository and is not committed. Build it with
`eval/baselines/iris/build-native.sh`, which installs it and its `appsettings.json` outside the
repo, or point `--iris-app` or `$IRIS_APP` at one you built another way.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_GAP_S = 0.25
# Where build-native.sh installs the app. Outside the repository on purpose: it is a build
# artefact of somebody else's project and nothing here commits a binary.
DEFAULT_APP = Path.home() / ".cache" / "calm-frames" / "iris" / "IrisApp"

# framedata.csv column names, from include/iris/FrameData.h at the pinned commit.
FLASH_FAIL_FROM = 2  # ExtendedFail, then FlashFail
PATTERN_FAIL_FROM = 1  # Fail
WARNING_VALUE = 1  # PassWithWarning


def find_app(explicit: Path | None) -> Path:
    for candidate in (explicit, Path(os.environ["IRIS_APP"]) if os.environ.get("IRIS_APP") else None, DEFAULT_APP):
        if candidate is not None and candidate.is_file():
            return candidate
    raise SystemExit(
        "no IrisApp found. Build it with eval/baselines/iris/build-native.sh, or pass "
        f"--iris-app. Looked at {DEFAULT_APP} and $IRIS_APP."
    )


def build_info(app: Path) -> dict:
    """What was built and what it linked against, read off the build rather than assumed."""
    info_file = app.parent / "BUILD_INFO.txt"
    out: dict[str, str] = {}
    if info_file.is_file():
        for line in info_file.read_text().splitlines():
            if "=" in line:
                name, _, value = line.partition("=")
                out[name.strip()] = value.strip()
    return out


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_timestamp(value: str) -> float:
    """IRIS writes hh:mm:ss.ffffff, built by msToTimeSpan in include/iris/FrameData.h.

    That function pads the seconds field with a leading zero whenever it is under ten, and it
    does not exclude negative seconds, so a frame with a presentation time before zero comes
    out as `00:00:0-0.001000`. Four Theora clips in this pool have one. The leading zero is
    dropped here rather than allowed to fail the whole clip, because a negative first timestamp
    is a real thing in a real container and losing a title over its formatting would take that
    title out of the pool without anybody deciding to.
    """
    parts = value.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"not an IRIS timestamp: {value!r}")
    hours, minutes, seconds = parts
    if len(seconds) > 1 and seconds[0] == "0" and seconds[1] == "-":
        seconds = seconds[1:]
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def read_frames(csv_path: Path) -> list[dict]:
    """Every row of framedata.csv, as times and the three per frame verdicts.

    IRIS ends each row with a NUL byte (FrameData::ToCSV appends '\\0'), so the last field is
    stripped of it before it is read as a number.
    """
    rows: list[dict] = []
    with csv_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("Frame") is None:
                continue
            cleaned = {
                name: (value or "").replace("\x00", "").strip() for name, value in row.items() if name
            }
            if not cleaned["Frame"]:
                continue
            rows.append(
                {
                    "frame": int(cleaned["Frame"]),
                    "t": parse_timestamp(cleaned["TimeStamp"]),
                    "luminance": int(cleaned["LuminanceFrameResult"]),
                    "red": int(cleaned["RedFrameResult"]),
                    "pattern": int(cleaned["PatternFrameResult"]),
                }
            )
    return rows


def frame_seconds(rows: list[dict]) -> float:
    """One frame in seconds, as the median step between the timestamps IRIS wrote.

    Read from the file rather than from a declared frame rate, because several clips in this
    pool are variable frame rate and `results/screening.json` records which.
    """
    steps = [b["t"] - a["t"] for a, b in zip(rows, rows[1:]) if b["t"] > a["t"]]
    if not steps:
        return 0.0
    return statistics.median(steps)


def to_segments(flagged: list[dict], step: float, gap: float) -> list[dict]:
    segments: list[dict] = []
    for row in flagged:
        start = row["t"]
        end = row["t"] + step
        if segments and start - segments[-1]["end_s"] <= gap:
            segments[-1]["end_s"] = max(segments[-1]["end_s"], end)
            segments[-1]["frames"] += 1
            continue
        segments.append({"start_s": start, "end_s": end, "frames": 1})
    return segments


def run_iris(app: Path, video: Path, args) -> tuple[Path, Path, str]:
    """Run IrisApp on one clip in a scratch directory and hand back its two result files."""
    work = Path(tempfile.mkdtemp(prefix="iris-run-"))
    settings = app.parent / "appsettings.json"
    if not settings.is_file():
        raise RuntimeError(f"no appsettings.json beside {app}")
    shutil.copy(settings, work / "appsettings.json")

    command = [str(app), "-v", str(video.resolve()), "-j", "1"]
    if args.pattern_detection is not None:
        command += ["-p", "1" if args.pattern_detection else "0"]
    if args.safe_area is not None:
        command += ["-a", str(args.safe_area)]
    finished = subprocess.run(command, cwd=work, capture_output=True, text=True, timeout=args.timeout)

    results = work / "Results" / video.name
    csv_path = results / "framedata.csv"
    json_path = results / "result.json"
    # IrisApp returns 0 even when the analysis never ran, and worse: on a file its OpenCV build
    # cannot decode it writes a frame data file with nothing but a header, writes "Elapsed time:
    # 0 ms", and reports the video as PASS. A tool that passes what it never looked at is the
    # one failure mode a candidate list must not inherit, so the files are the test and not the
    # exit code, and a clip with no frames in it becomes a recorded failure rather than a report
    # saying IRIS found nothing.
    if not csv_path.is_file() or csv_path.stat().st_size == 0:
        shutil.rmtree(work, ignore_errors=True)
        raise RuntimeError(
            f"IrisApp wrote no frame data (exit {finished.returncode}): "
            f"{finished.stderr.strip()[-400:] or finished.stdout.strip()[-400:]}"
        )
    return csv_path, json_path, str(work)


def analyze(app: Path, video: Path, args) -> dict:
    csv_path, json_path, work = run_iris(app, video, args)
    try:
        rows = read_frames(csv_path)
        overall = json.loads(json_path.read_text()) if json_path.is_file() else {}
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if not rows:
        raise RuntimeError(
            "IrisApp wrote a frame data file with no frames in it, which is what this build "
            "does when OpenCV cannot decode the file. IRIS called it PASS anyway."
        )

    step = frame_seconds(rows)
    if step <= 0:
        # Four Theora clips here declare avg_frame_rate 0/0, so IRIS logs "Video FPS: 0" and
        # "Duration: infs" and stamps every one of their frames with the same timestamp. It
        # still analyses every frame and still reaches a verdict, but with no time base its
        # own one second transition window has nothing to measure against, and a flag that
        # cannot be placed in time is no use to a candidate list. Refused rather than repaired:
        # computing a time base from r_frame_rate afterwards would put real looking timestamps
        # on an analysis that never had them.
        raise RuntimeError(
            f"every frame carries the same timestamp ({rows[0]['t']} s over {len(rows)} "
            "frames), because IRIS read this container's frame rate as 0. Its analysis has no "
            "time base, so its flags cannot be placed in the clip."
        )

    def failed(row: dict) -> bool:
        if row["luminance"] >= FLASH_FAIL_FROM or row["red"] >= FLASH_FAIL_FROM:
            return True
        if row["pattern"] >= PATTERN_FAIL_FROM:
            return True
        if args.include_warnings and (row["luminance"] == WARNING_VALUE or row["red"] == WARNING_VALUE):
            return True
        return False

    flagged = [row for row in rows if failed(row)]
    segments = to_segments(flagged, step, args.gap)
    warned = [
        row
        for row in rows
        if row["luminance"] == WARNING_VALUE or row["red"] == WARNING_VALUE
    ]
    warnings = len(warned)
    # Kept beside the segments rather than thrown away. IRIS passes 2 to 3 Hz flashing, so it
    # is not a flag and it is not in `segments`, but it is the one place IRIS says it saw
    # something. If IRIS turns out to flag nothing at all on a pool, this is what says whether
    # it saw nothing or saw something and forgave it, and the two are not the same finding.
    warning_segments = to_segments(warned, step, args.gap) if not args.include_warnings else []
    info = build_info(app)

    # Cross-check: the frames this script read out of framedata.csv against the verdict IRIS
    # reached on its own and wrote into result.json. IRIS calls a video Fail when any frame is
    # an extended fail or a flash fail, which is the same line this script draws, so the two
    # have to agree. They are two different files written by the same run, and a parse that
    # read the wrong column would pass every other check in here and quietly hand the pool an
    # empty candidate list. Not a warning: a candidate list nobody can trust is worse than no
    # candidate list, so this stops.
    #
    # The check is only meaningful at IRIS's own line, so --include-warnings skips it and the
    # report says the check did not run rather than claiming agreement it never tested.
    checked = not args.include_warnings
    if checked:
        iris_says_fail = overall.get("OverallResult") == "Fail"
        if iris_says_fail != bool(flagged):
            raise RuntimeError(
                f"this script and IRIS disagree about {video.name}: IRIS's own result.json says "
                f"{overall.get('OverallResult')!r} and framedata.csv gave "
                f"{len(flagged)} failing frames of {len(rows)}"
            )

    return {
        "baseline": "iris",
        "tool_version": (
            f"EA IRIS {info.get('iris_commit', 'unknown commit')}, built by "
            f"{info.get('built_by', 'unknown')} on {info.get('machine', 'unknown')}"
        ),
        "video": video.name,
        "sha256": sha256_of(video),
        "params": {
            "iris_commit": info.get("iris_commit"),
            "appsettings": "upstream config/appsettings.json, unchanged",
            "pattern_detection": bool(args.pattern_detection),
            "frame_resize": False,
            "safe_area_proportion": 0.25 if args.safe_area is None else args.safe_area,
            "safe_area_is_the_upstream_default": args.safe_area is None,
            "flagged_from_frame_result": FLASH_FAIL_FROM,
            "include_warnings": bool(args.include_warnings),
            "merge_gap_s": args.gap,
            "frame_seconds": round(step, 6),
        },
        "build": info,
        "frames_analyzed": len(rows),
        "flagged_frames": len(flagged),
        "warning_frames": warnings,
        "segment_count": len(segments),
        "segments": [
            {
                "start_s": round(s["start_s"], 3),
                "end_s": round(s["end_s"], 3),
                "duration_s": round(s["end_s"] - s["start_s"], 3),
                "frames": s["frames"],
            }
            for s in segments
        ],
        "warning_segment_count": len(warning_segments),
        "warning_segments": [
            {
                "start_s": round(s["start_s"], 3),
                "end_s": round(s["end_s"], 3),
                "duration_s": round(s["end_s"] - s["start_s"], 3),
                "frames": s["frames"],
            }
            for s in warning_segments
        ],
        "agrees_with_iris_own_verdict": (
            True if checked else "not checked: --include-warnings moves the line IRIS draws"
        ),
        "iris_overall_result": overall.get("OverallResult"),
        "iris_results": overall.get("Results", []),
        "iris_total_luminance_incidents": overall.get("TotalLuminanceIncidents"),
        "iris_total_red_incidents": overall.get("TotalRedIncidents"),
        "notes": (
            "EA IRIS through its own example app, at the upstream settings. A frame joins a "
            "segment when its luminance or red result is an extended fail or a flash fail, or "
            "its pattern result is a fail. Pass with warning is 2 to 3 Hz flashing that IRIS "
            "passes, and is counted in warning_frames rather than flagged. Not a conformance "
            "result and not a safety claim: it is a second opinion, so that the real clip pool "
            "is not drawn from our own detector alone."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("videos", nargs="+", type=Path)
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("results/baselines/iris"))
    parser.add_argument(
        "--failures-out",
        type=Path,
        default=Path("results/baselines/iris_failures.json"),
        help="where the list of clips IRIS could not analyse goes. Deliberately not inside "
        "--out-dir, which is globbed for candidate lists.",
    )
    parser.add_argument("--iris-app", type=Path, default=None)
    parser.add_argument("--gap", type=float, default=DEFAULT_GAP_S)
    parser.add_argument(
        "--pattern-detection",
        action="store_true",
        default=False,
        help="turn IRIS's regular pattern rule on. Off is the upstream default.",
    )
    parser.add_argument(
        "--safe-area",
        type=float,
        default=None,
        help="IRIS's safe area proportion, its -a flag. Leaving it alone keeps upstream's "
        "0.25, which is what the pool was run at. Anything else is a diagnostic and the "
        "report says so in params.",
    )
    parser.add_argument(
        "--include-warnings",
        action="store_true",
        help="count IRIS's 2 to 3 Hz pass-with-warning frames as flagged. Off by default, "
        "because IRIS passes them.",
    )
    parser.add_argument("--timeout", type=int, default=7200)
    arguments = parser.parse_args()

    app = find_app(arguments.iris_app)
    arguments.out_dir.mkdir(parents=True, exist_ok=True)

    failures: dict[str, str] = {}
    for video in arguments.videos:
        if not video.is_file():
            print(f"skip (not a file): {video}", file=sys.stderr)
            continue
        try:
            report = analyze(app, video, arguments)
        except Exception as error:  # noqa: BLE001
            print(f"FAILED {video.name}: {error}", file=sys.stderr)
            failures[video.name] = f"{type(error).__name__}: {error}"
            # No report file for a clip IRIS could not analyse, on purpose. Anything that reads
            # this directory treats one JSON file per clip as "IRIS has a candidate list for
            # this title", and a report saying it found nothing would be indistinguishable from
            # a report saying it never looked. The pool builder then keeps the title out, which
            # is the answer that is true.
            (arguments.out_dir / f"{video.stem}.json").unlink(missing_ok=True)
            continue
        stem = video.stem
        destination = arguments.out_dir / f"{stem}.json"
        destination.write_text(json.dumps(report, indent=2) + "\n")
        print(
            f"{video.name}: {report['segment_count']} segments, "
            f"{report['flagged_frames']}/{report['frames_analyzed']} frames, "
            f"IRIS says {report['iris_overall_result']} -> {destination}"
        )

    # Outside out_dir, because everything that reads out_dir globs *.json and counts each file
    # as a title IRIS analysed. A failure list in there would put these titles back into the
    # pool as titles IRIS had seen.
    if arguments.failures_out is not None:
        arguments.failures_out.parent.mkdir(parents=True, exist_ok=True)
        arguments.failures_out.write_text(
            json.dumps(
                {
                    "generated_on": "2026-09-18",
                    "what_this_is": (
                        "clips EA IRIS could not analyse on this build, and why. They have no "
                        "report in results/baselines/iris/, so they have no IRIS candidate "
                        "list, so eval/labeling/make_pool.py keeps them out of the pool."
                    ),
                    "clips_attempted_in_this_run": len(arguments.videos),
                    "failed": len(failures),
                    "how_to_count_the_pool": (
                        "one report in results/baselines/iris/ per clip IRIS analysed, plus "
                        "the failures here, is the whole pool. This file is rewritten by each "
                        "run, so clips_attempted_in_this_run is that run and not the pool."
                    ),
                    "failures": failures,
                },
                indent=2,
            )
            + "\n"
        )
        print(f"{len(failures)} clip(s) IRIS could not analyse -> {arguments.failures_out}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
