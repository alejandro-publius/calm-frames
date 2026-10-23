#!/usr/bin/env python3
"""Recheck an explicitly selected archive sample on the current detector source.

The original design, labels, exclusions and archived results are never changed.
The default rechecks the archive sample; --selection design measures the whole
committed design afresh. Neither path reuses old detector output as new evidence.
Generated clips live in one private temporary directory outside the repository
and are generated, analyzed and deleted by run_one in the same job.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tempfile
import time

EVAL = Path(__file__).resolve().parents[1]
REPO = EVAL.parent
if str(EVAL) not in sys.path:
    sys.path.insert(0, str(EVAL))

from conformance.generate_analyze import _init_worker, _terminate, run_one, sweep_leftovers
from conformance.report import Tally, excluded_reason, flashmap_windows
from conformance.render import ENCODING_PROTOCOL


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_fingerprint() -> dict[str, str]:
    paths = sorted({
        *REPO.glob("flashmap/src/flashmap/*.py"),
        *REPO.glob("eval/conformance/*.py"),
        REPO / "eval/metrics.py",
        REPO / "flashmap/docs/SPEC_SOURCES.md",
    })
    return {str(path.relative_to(REPO)): digest(path) for path in paths}


def selected_clips(design: dict, archive: list[dict], limit: int | None,
                   selection: str = "archive") -> list[dict]:
    """Select unchanged design rows in their original order, without relabelling."""
    clips = {clip["clip_id"]: clip for clip in design["clips"]}
    if len(clips) != len(design["clips"]):
        raise ValueError("design contains duplicate clip identities")
    ids = [row["clip_id"] for row in archive]
    if len(set(ids)) != len(ids) or not set(ids).issubset(clips):
        raise ValueError("archive clip identities are duplicated or absent from the design")
    if limit is not None and limit <= 0:
        raise ValueError("limit must select at least one clip")
    if selection == "design":
        ids = list(clips)
    elif selection != "archive":
        raise ValueError("selection must be archive or design")
    return sorted((clips[key] for key in ids), key=lambda clip: clip["order_index"])[:limit]


def summarize(clips: list[dict], rows: list[dict], archive: list[dict]) -> dict:
    """Apply the original truth and exclusion rules, including every selected row."""
    lookup = {row["clip_id"]: row for row in rows}
    if (len(lookup) != len(rows)
            or set(lookup) != {clip["clip_id"] for clip in clips}):
        raise ValueError("measurement rows must cover the exact selected clip set once")
    prior = {row["clip_id"]: row for row in archive}
    tally = Tally()
    near = Tally()
    away = Tally()
    exclusions: Counter[str] = Counter()
    misses = []
    changes = []
    kept = near_kept = away_kept = 0
    for clip in clips:
        row = lookup[clip["clip_id"]]
        reason = excluded_reason(row, clip)
        prior_row = prior.get(clip["clip_id"])
        prior_reason = excluded_reason(prior_row, clip) if prior_row else None
        n_windows = int(clip["duration_ms"] // 1000)
        prediction = flashmap_windows(row, n_windows, 0, False)
        prior_prediction = flashmap_windows(prior_row, n_windows, 0, False) if prior_row else None
        truth = set(clip["truth"]["positive_windows"])
        if prior_row is not None and (reason != prior_reason or prediction != prior_prediction):
            changes.append({
                "clip_id": clip["clip_id"], "previous_exclusion": prior_reason,
                "current_exclusion": reason, "truth_positive_windows": sorted(truth),
                "previous_predicted_windows": sorted(prior_prediction),
                "current_predicted_windows": sorted(prediction),
            })
        if reason:
            exclusions[reason] += 1
            continue
        kept += 1
        tally.add(prediction, truth, list(range(n_windows)))
        if clip["near_threshold"]:
            near_kept += 1
            near.add(prediction, truth, list(range(n_windows)))
        else:
            away_kept += 1
            away.add(prediction, truth, list(range(n_windows)))
        if truth - prediction:
            misses.append({
                "clip_id": clip["clip_id"], "axis": clip["axis"],
                "near_threshold": clip["near_threshold"],
                "missed_positive_windows": sorted(truth - prediction),
                "truth": clip["truth"],
            })
    return {
        "clips_measured": len(rows), "clips_kept": kept,
        "clips_excluded": sum(exclusions.values()), "exclusions": dict(exclusions),
        "previously_unmeasured_clips": sum(clip["clip_id"] not in prior for clip in clips),
        "all_windows": tally.as_dict(),
        "near_limits": {"clips_kept": near_kept, **near.as_dict()},
        "away_from_limits": {"clips_kept": away_kept, **away.as_dict()},
        "missed_clips": misses, "changed_clip_outcomes": changes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", type=Path, default=REPO / "results/conformance_design.json")
    parser.add_argument("--archive", type=Path, default=REPO / "results/conformance_raw.jsonl")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--selection", choices=("archive", "design"), default="archive")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output already exists; use a new path to preserve previous evidence")
    journal_path = args.out.with_suffix(".journal.jsonl")
    if journal_path.exists():
        parser.error("measurement journal already exists; incomplete evidence is never reused")
    if not 1 <= args.workers <= 4:
        parser.error("workers must be between one and four")
    design_hash, archive_hash = digest(args.design), digest(args.archive)
    design = json.loads(args.design.read_text())
    archive = [json.loads(line) for line in args.archive.read_text().splitlines() if line.strip()]
    clips = selected_clips(design, archive, args.limit, args.selection)
    if not clips:
        parser.error("the archive sample is empty")
    source_before = source_fingerprint()
    previous_scratch = os.environ.get("CALM_CONFORMANCE_SCRATCH")
    previous_handler = signal.signal(signal.SIGTERM, _terminate)
    started = time.monotonic()
    rows = []
    leaked = 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="calm-conformance-recheck-") as scratch, \
            journal_path.open("x") as journal:
        journal.write(json.dumps({
            "kind": "fresh_conformance_journal",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "encoding_protocol": ENCODING_PROTOCOL,
            "source_sha256": source_before, "design_sha256": design_hash,
            "archive_sha256": archive_hash,
            "selected_clip_ids": [clip["clip_id"] for clip in clips],
            "limits": "Partial until final result exists and its source/cleanup checks pass.",
        }, sort_keys=True) + "\n")
        journal.flush()
        os.fsync(journal.fileno())
        os.environ["CALM_CONFORMANCE_SCRATCH"] = scratch
        try:
            with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_worker) as pool:
                futures = {pool.submit(run_one, clip, False): clip for clip in clips}
                try:
                    for future in as_completed(futures):
                        row = future.result()
                        rows.append(row)
                        journal.write(json.dumps(row, sort_keys=True) + "\n")
                        if len(rows) % 25 == 0 or len(rows) == len(clips):
                            journal.flush()
                            os.fsync(journal.fileno())
                            print(f"{len(rows)}/{len(clips)} clips; "
                                  f"{time.monotonic() - started:.1f}s elapsed; "
                                  f"{sum('error' in item for item in rows)} errors", flush=True)
                except BaseException:
                    pool.shutdown(wait=True, cancel_futures=True)
                    raise
        finally:
            leaked = sweep_leftovers()
            signal.signal(signal.SIGTERM, previous_handler)
            if previous_scratch is None:
                os.environ.pop("CALM_CONFORMANCE_SCRATCH", None)
            else:
                os.environ["CALM_CONFORMANCE_SCRATCH"] = previous_scratch
    if leaked or any("delete_error" in row for row in rows):
        raise RuntimeError("hazard cleanup failed; this measurement cannot be published")
    if (source_fingerprint() != source_before
            or digest(args.design) != design_hash or digest(args.archive) != archive_hash):
        raise RuntimeError("source or evaluation inputs changed during the run")
    import av
    import numpy
    result = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "kind": "fresh_conformance_evaluation",
        "encoding_protocol": ENCODING_PROTOCOL,
        "journal_sha256": digest(journal_path),
        "selection": args.selection,
        "selection_rule": "unchanged clip IDs in original design order, optionally limited",
        "selected_clip_ids": [clip["clip_id"] for clip in clips],
        "designed_clips": len(design["clips"]), "archive_clips": len(archive),
        "complete_design_evaluation": (len(clips) == len(design["clips"])
                                       and not any("error" in row for row in rows)),
        "baselines_rerun": False,
        "archived_results_modified": False, "truth_labels_modified": False,
        "design_sha256": design_hash, "archive_sha256": archive_hash,
        "source_sha256": source_before,
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     capture_output=True, text=True, check=True).stdout.strip(),
        "environment": {"python": platform.python_version(), "pyav": av.__version__,
                        "numpy": numpy.__version__, "libav": av.library_versions},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "hazard_files_remaining": leaked,
        "limits": "Same preregistered intended-signal labels and exclusion rules. "
                  "See selection and complete_design_evaluation for coverage. Not a clinical study. "
                  "Encoding may move near-limit signals; misses remain scored as misses. "
                  "Baselines were not remeasured and are not a current matched comparison.",
        "summary": summarize(clips, rows, archive),
        "rows": sorted(rows, key=lambda row: row["order_index"]),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = args.out.with_suffix(args.out.suffix + ".tmp")
    try:
        temporary_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        temporary_output.replace(args.out)
    finally:
        temporary_output.unlink(missing_ok=True)
    print(f"Wrote {args.out}; no hazard files retained", flush=True)
    return 2 if any("error" in row for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
