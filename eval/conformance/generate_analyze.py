#!/usr/bin/env python3
"""Generate one conformance clip, measure it with every detector, delete it. Then the next one.

SAFETY, NOT NEGOTIABLE. Read this before changing anything in this file.
-----------------------------------------------------------------------
These clips are hazardous by design. They are strobes built to sit on and around the flash
thresholds, at every rate from 1 to 30 Hz, and some of them are worse than anything a player of
ours would ever be allowed to show. So:

- each clip is written under a scratch directory outside the repository, owner only, with a
  `HAZARD_` name, and is deleted in a `finally` block in the same job that made it, before the
  next clip starts. At no point does the set of them exist;
- nothing here opens, plays, thumbnails or previews a clip, and neither does a person. The only
  thing that ever sees these pixels is a decoder;
- the run asserts at exit that no `HAZARD_` file survived. If one did, it is removed and the
  run fails, because a hazard file that outlives its job is the one failure mode that can hurt
  somebody;
- the scratch directory is never inside `media/`, never inside the repository, and never a
  place anything else scans. It is not a cache: nothing is kept to save time later. Regenerating
  is cheap and a stored strobe is not.

That is also why this file is the only thing that touches the clips, and why the results are
JSON rather than video.

What it records per clip
------------------------
- flashmap's segments, at the pinned version, through the public `analyze_file` API;
- an encoding fidelity check: the decoded per frame mean relative luminance against the
  waveform the design asked for, so a clip the encoder mangled can be excluded and counted;
- the two local baselines, on the same file, in the same job, so the comparison is on identical
  bytes: ffmpeg's photosensitivity filter and naive mean luminance differencing. Both are
  recorded per window as a sweepable quantity, so their operating points can be chosen offline
  on this suite rather than guessed here.

The job is resumable. Rows are appended to results/conformance_raw.jsonl, and a clip whose id
is already in that file is skipped, so the run can be stopped and restarted, or run in the
background in several passes.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.render import HAZARD_PREFIX, decode_mean_luminance, render_clip, scratch_dir  # noqa: E402
from conformance.spec import load_spec  # noqa: E402

REPO = _EVAL_DIR.parent
DESIGN = REPO / "results" / "conformance_design.json"
RAW = REPO / "results" / "conformance_raw.jsonl"

# Sweep ladders for the two tunable baselines. Recording counts at every rung means the
# operating point can be chosen on this suite afterwards, which is what EVAL_PLAN section 6
# asks for, without running either baseline again.
NAIVE_LADDER = [2, 4, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60]
FFMPEG_DIFF_LADDER = [1, 2, 4, 8, 16, 32]


def _baseline_module(name: str, filename: str):
    """Import a committed baseline runner by path, so the same measurement code is used."""
    import importlib.util

    path = _EVAL_DIR / "baselines" / name / filename
    spec = importlib.util.spec_from_file_location(f"baseline_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _window_index(time_ms: float, window_ms: float, n_windows: int) -> int | None:
    index = int(time_ms // window_ms)
    return index if 0 <= index < n_windows else None


def analyze_flashmap(path: Path) -> dict:
    from flashmap import PROFILES, analyze_file

    started = time.time()
    result = analyze_file(path, PROFILES["wcag"])
    return {
        "version": __import__("flashmap").__version__,
        "profile": "wcag",
        "segments": [
            {
                "start_ms": segment.start_ms,
                "end_ms": segment.end_ms,
                "flash_first_ms": segment.flash_first_ms,
                "flash_last_ms": segment.flash_last_ms,
                "reason": segment.reason,
                "area_fraction": segment.area_fraction,
                "max_flashes_in_window": segment.max_flashes_in_window,
            }
            for segment in result.segments
        ],
        "frame_count": result.frame_count,
        "first_pts_ms": result.first_pts_ms,
        "last_pts_ms": result.last_pts_ms,
        "variable_frame_rate": result.variable_frame_rate,
        "picture": [result.picture.width, result.picture.height],
        "seconds": round(time.time() - started, 3),
    }


def fidelity(path: Path, clip: dict, spec) -> dict:
    """Did the encoder give back the waveform the design asked for?

    EVAL_PLAN section 4. The intended mean relative luminance of each state is known from what
    was drawn, so the check is per frame: take the decoded mean, compare it against the
    intended value for whichever state that frame was meant to show, and keep the worst gap.
    """
    from conformance.geometry import frame_plan
    from conformance.truth import clip_truth

    truth = clip_truth(clip, spec)
    # The decoder returns the coded frame, bars and all, so the comparison is against the mean
    # over the coded frame and not over the picture inside it.
    intended_by_state = truth.coded_frame_mean_luminance_by_state
    times, states = frame_plan(
        duration_ms=float(clip["duration_ms"]),
        fps=float(clip["fps"]),
        timing=str(clip["timing"]),
        flash_start_ms=float(clip["flash_start_ms"]),
        flash_hz=float(clip["flash_hz"]),
        seed=int(clip.get("seed", 0)),
    )
    decoded_times, decoded_means = decode_mean_luminance(path, spec)
    if not decoded_times:
        return {"frames_decoded": 0, "max_abs_deviation": None, "timestamps_match": False}

    planned = np.asarray(times)
    worst = 0.0
    for time_ms, mean in zip(decoded_times, decoded_means):
        nearest = int(np.argmin(np.abs(planned - time_ms)))
        worst = max(worst, abs(mean - intended_by_state[states[nearest]]))

    timestamp_gap = 0.0
    if len(decoded_times) == len(times):
        timestamp_gap = float(np.max(np.abs(np.asarray(decoded_times) - planned)))
    return {
        "frames_decoded": len(decoded_times),
        "frames_planned": len(times),
        "max_abs_deviation": round(float(worst), 6),
        "max_timestamp_gap_ms": round(timestamp_gap, 4),
        "timestamps_match": len(decoded_times) == len(times) and timestamp_gap < 1.0,
    }


def baseline_rows(path: Path, clip: dict, modules: dict) -> dict:
    """Both local baselines on the same bytes, recorded per window and sweepable offline."""
    window_ms = 1000.0
    n_windows = int(float(clip["duration_ms"]) // window_ms)
    out: dict[str, object] = {}

    naive = modules["naive"]
    rows = naive.per_frame_luma(path, timeout=300)
    max_delta = [0.0] * n_windows
    counts = {str(rung): [0] * n_windows for rung in NAIVE_LADDER}
    for (_, previous), (time_ms_s, current) in zip(rows, rows[1:]):
        index = _window_index(time_ms_s * 1000.0, window_ms, n_windows)
        if index is None:
            continue
        delta = abs(current - previous)
        max_delta[index] = max(max_delta[index], delta)
        for rung in NAIVE_LADDER:
            if delta >= rung:
                counts[str(rung)][index] += 1
    out["naive_luma_diff"] = {
        "frames": len(rows),
        "max_delta_per_window": [round(v, 3) for v in max_delta],
        "frames_over_per_window": counts,
        "units": "8 bit luma codes of frame to frame change in ffmpeg signalstats YAVG",
    }

    photo = modules["ffmpeg"]
    rows = photo.per_frame_difference(
        path, photo.DEFAULT_FRAMES, photo.DEFAULT_THRESHOLD, photo.DEFAULT_SKIP, 300
    )
    warmup_s = photo.DEFAULT_WARMUP_S
    max_ymax = [0.0] * n_windows
    dropped = 0
    seen = [0] * n_windows
    for time_s, ymax in rows:
        if time_s < warmup_s:
            dropped += 1
            continue
        index = _window_index(time_s * 1000.0, window_ms, n_windows)
        if index is None:
            continue
        seen[index] += 1
        max_ymax[index] = max(max_ymax[index], ymax)
    out["ffmpeg_photosensitivity"] = {
        "frames": len(rows),
        "frames_dropped_as_warmup": dropped,
        "frames_seen_per_window": seen,
        "max_ymax_per_window": [round(v, 3) for v in max_ymax],
        "params": {
            "frames": photo.DEFAULT_FRAMES,
            "threshold": photo.DEFAULT_THRESHOLD,
            "skip": photo.DEFAULT_SKIP,
            "warmup_dropped_s": warmup_s,
        },
        "note": (
            "The filter rewrites frames instead of reporting, so a flag is inferred from where "
            "its output differs from the unfiltered decode. The first second is dropped, so "
            "window 0 of every clip is an exclusion for this baseline, never a negative."
        ),
    }
    return out


def run_one(clip: dict, with_baselines: bool) -> dict:
    """One clip, start to finish, with the file gone before this function returns."""
    spec = load_spec()
    path = scratch_dir() / f"{HAZARD_PREFIX}{clip['clip_id']}.mp4"
    row: dict[str, object] = {
        "clip_id": clip["clip_id"],
        "order_index": clip.get("order_index"),
        "axis": clip.get("axis"),
    }
    try:
        row["encode"] = render_clip(clip, path)
        row["flashmap"] = analyze_flashmap(path)
        row["fidelity"] = fidelity(path, clip, spec)
        if with_baselines:
            modules = {
                "naive": _baseline_module("naive_luma_diff", "run.py"),
                "ffmpeg": _baseline_module("ffmpeg_photosensitivity", "run.py"),
            }
            row["baselines"] = baseline_rows(path, clip, modules)
    except Exception as error:  # noqa: BLE001 - one bad clip must not stop the suite
        row["error"] = f"{type(error).__name__}: {error}"
    finally:
        # The clip goes away here whatever happened above. Nothing keeps a strobe.
        try:
            if path.exists():
                path.unlink()
        except OSError as error:  # pragma: no cover
            row["delete_error"] = str(error)
    return row


def _terminate(signum, frame):  # noqa: ARG001
    """Turn a kill signal into an exception so the `finally` that deletes the clip runs.

    Learned the hard way on Sep 17, 2026: this job was stopped with SIGTERM to restart it with
    more workers, the default handler tore the workers down where they stood, and two hazard
    clips outlived their job. Python's default SIGTERM does not run `finally` blocks. This one
    does, and the parent sweeps at start and at exit as well, so it now takes two failures in a
    row rather than one for a strobe to survive.
    """
    raise SystemExit(f"stopped by signal {signum}")


def _init_worker() -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, _terminate)


def already_done(raw_path: Path) -> set[str]:
    done: set[str] = set()
    if not raw_path.exists():
        return done
    with raw_path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["clip_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def sweep_leftovers(fail: bool = True) -> int:
    """No hazard file outlives the job. Anything still here is removed and the run fails."""
    directory = scratch_dir()
    leftovers = sorted(directory.glob(f"{HAZARD_PREFIX}*"))
    for path in leftovers:
        try:
            path.unlink()
        except OSError:
            pass
    if leftovers and fail:
        print(
            f"SAFETY: {len(leftovers)} hazard file(s) outlived their job and were removed. "
            "That must not happen, so this run is a failure.",
            file=sys.stderr,
        )
    return len(leftovers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--out", type=Path, default=RAW)
    parser.add_argument("--limit", type=int, default=None, help="stop after this many new clips")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--axis", action="append", default=None, help="only these design axes")
    parser.add_argument("--no-baselines", action="store_true")
    parser.add_argument("--progress-every", type=int, default=25)
    arguments = parser.parse_args()

    # Anything left over from an earlier job goes before this one starts. A hazard file with
    # nobody responsible for it is the thing this whole design exists to prevent.
    swept = sweep_leftovers(fail=False)
    if swept:
        print(f"swept {swept} hazard file(s) left by an earlier run", file=sys.stderr)
    signal.signal(signal.SIGTERM, _terminate)

    design = json.loads(arguments.design.read_text())
    clips = sorted(design["clips"], key=lambda row: row["order_index"])
    if arguments.axis:
        clips = [clip for clip in clips if clip["axis"] in set(arguments.axis)]

    done = already_done(arguments.out)
    todo = [clip for clip in clips if clip["clip_id"] not in done]
    if arguments.limit is not None:
        todo = todo[: arguments.limit]

    print(
        f"{len(done)} already measured, {len(todo)} to go "
        f"(of {len(clips)} in the design), {arguments.workers} workers, "
        f"baselines {'off' if arguments.no_baselines else 'on'}",
        flush=True,
    )
    if not todo:
        sweep_leftovers(fail=False)
        return 0

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    completed = 0
    failures = 0
    with arguments.out.open("a") as handle:
        with ProcessPoolExecutor(
            max_workers=arguments.workers, initializer=_init_worker
        ) as pool:
            futures = {
                pool.submit(run_one, clip, not arguments.no_baselines): clip for clip in todo
            }
            try:
                for future in as_completed(futures):
                    row = future.result()
                    if "error" in row:
                        failures += 1
                    handle.write(json.dumps(row) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    completed += 1
                    if completed % arguments.progress_every == 0:
                        rate = completed / max(1e-9, time.time() - started)
                        left = (len(todo) - completed) / max(1e-9, rate)
                        print(
                            f"{completed}/{len(todo)} clips, {failures} failed, "
                            f"{rate:.2f} clips/s, about {left / 60:.1f} min left",
                            flush=True,
                        )
            except BaseException as stop:  # noqa: BLE001 - Ctrl-C, SIGTERM, anything
                # cancel_futures matters more than it looks. Leaving the executor by any other
                # route calls shutdown(wait=True), which keeps handing the workers the whole
                # remaining queue while nobody is reading the answers: the job looks stopped,
                # the rows stop appearing, and it quietly carries on making strobes. Seen on
                # Sep 17, 2026 when this run was stopped to give the ablations the cores.
                print(
                    f"stopping ({type(stop).__name__}), cancelling the queue. "
                    "The rows already written stay valid.",
                    file=sys.stderr,
                )
                pool.shutdown(cancel_futures=True, wait=True)
                sweep_leftovers(fail=False)
                if not isinstance(stop, KeyboardInterrupt):
                    raise

    leftovers = sweep_leftovers()
    elapsed = time.time() - started
    print(
        f"done: {completed} clips in {elapsed / 60:.1f} min, {failures} failed, "
        f"{leftovers} hazard files leaked",
        flush=True,
    )
    return 1 if leftovers else 0


if __name__ == "__main__":
    raise SystemExit(main())
