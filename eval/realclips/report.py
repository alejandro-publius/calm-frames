#!/usr/bin/env python3
"""Real clip metrics, from human labels. Everything is ready except the labels.

docs/EVAL_PLAN.md section 5. This script does the whole analysis: window level precision and
recall for every detector against the adjudicated labels, a bootstrap over titles, unweighted
Cohen's kappa between the two labellers on the labels as first given, and the per source
breakdown. What it will not do is invent a label, and what it cannot do is run without any.

Rules it enforces, from the plan:

- labels are frozen before any comparison: it refuses to run on label files that are dirty in
  the working tree, and it records their SHA-256 in its output;
- a window a labeller could not call is an exclusion, not a negative;
- the headline interval on this set is the bootstrap over titles, not Wilson, because windows
  inside one title are not independent. Wilson is reported beside it and marked optimistic;
- both window overlap rules are computed in the same run.

With no labels yet it writes results/realclips_status.json, which says what exists and what is
missing, and it does not write results/realclips.json. A file of real numbers gets written when
there are real numbers, and not before.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from metrics import (  # noqa: E402
    bootstrap_groups,
    confusion,
    f1,
    rate_with_interval,
    windows_from_intervals,
)

REPO = _EVAL_DIR.parent
LABELING = _EVAL_DIR / "labeling"
SCREENING = REPO / "results" / "screening.json"
BASELINES = REPO / "results" / "baselines"
OUT = REPO / "results" / "realclips.json"
STATUS_OUT = REPO / "results" / "realclips_status.json"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_state(path: Path) -> str:
    """committed, modified, untracked, outside the repository, or unknown.

    Only "committed" counts as frozen. Asking git whether a file has changes is not enough: a
    file git has never heard of, or one sitting outside the repository altogether, comes back
    with no changes at all, which would read as frozen and is the opposite of frozen. The first
    version of this function had exactly that hole and a test found it.
    """
    try:
        if not path.resolve().is_relative_to(REPO.resolve()):
            return "outside the repository"
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(path)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if tracked.returncode != 0:
            return "untracked"
        changes = subprocess.run(
            ["git", "status", "--porcelain", "--", str(path)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if changes.returncode != 0:
            return "unknown"
        return "modified" if changes.stdout.strip() else "committed"
    except Exception:  # noqa: BLE001
        return "unknown"


def read_labels(path: Path) -> dict[tuple[str, int], str]:
    """(segment id, window) to "1", "0" or "x" for unlabelable. Blank rows are not answers."""
    labels: dict[tuple[str, int], str] = {}
    with path.open() as handle:
        for row in csv.DictReader(handle):
            key = (row["segment_id"], int(row["window_index"]))
            if (row.get("unlabelable") or "").strip():
                labels[key] = "x"
            elif (row.get("label") or "").strip():
                value = row["label"].strip()
                if value not in ("0", "1"):
                    raise SystemExit(f"{path.name}: label {value!r} is not 0, 1 or unlabelable")
                labels[key] = value
    return labels


def cohens_kappa(a: dict, b: dict) -> dict:
    """Unweighted Cohen's kappa on the windows both labellers called 0 or 1."""
    shared = [
        (a[key], b[key])
        for key in a
        if key in b and a[key] in ("0", "1") and b[key] in ("0", "1")
    ]
    n = len(shared)
    if n == 0:
        return {"kappa": None, "windows": 0, "why": "no window was called by both labellers"}
    agree = sum(1 for x, y in shared if x == y)
    observed = agree / n
    p_a1 = sum(1 for x, _ in shared if x == "1") / n
    p_b1 = sum(1 for _, y in shared if y == "1") / n
    expected = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)
    kappa = None if expected == 1 else (observed - expected) / (1 - expected)
    return {
        "kappa": kappa,
        "windows": n,
        "observed_agreement": observed,
        "expected_agreement": expected,
        "positives_labeller_a": round(p_a1 * n),
        "positives_labeller_b": round(p_b1 * n),
        "note": "on the labels as first given, before any discussion",
    }


def detector_windows(key: dict, min_overlap: float) -> dict[str, dict[str, set[int]]]:
    """Each detector's positive windows per segment, through the shared window mapping."""
    from labeling.make_pool import CANDIDATE_LISTS, title_key  # noqa: PLC0415

    flags: dict[str, dict[str, list[tuple[float, float]]]] = defaultdict(dict)
    screening = json.loads(SCREENING.read_text())
    for entry in screening["per_file"]:
        if entry.get("error"):
            continue
        flags[title_key(entry["file"])]["flashmap"] = [
            (float(s["start_s"]) * 1000.0, float(s["end_s"]) * 1000.0)
            for s in entry.get("segments", [])
        ]
    # The baselines, taken from the same list the pool was cut from. Naming them here a second
    # time is how a detector ends up in the pool and then never scored against the labels.
    for folder in (name for name in CANDIDATE_LISTS if name != "flashmap"):
        for path in sorted((BASELINES / folder).glob("*.json")):
            data = json.loads(path.read_text())
            flags[title_key(data["video"])][folder] = [
                (s["start_s"] * 1000.0, s["end_s"] * 1000.0) for s in data.get("segments", [])
            ]

    out: dict[str, dict[str, set[int]]] = defaultdict(dict)
    for segment in key["segments"]:
        name = title_key(segment["file"])
        start_ms = float(segment["start_s"]) * 1000.0
        end_ms = float(segment["end_s"]) * 1000.0
        n_windows = int(round((end_ms - start_ms) / 1000.0))
        for detector, intervals in flags.get(name, {}).items():
            clipped = [
                (max(a, start_ms), min(b, end_ms))
                for a, b in intervals
                if b > start_ms and a < end_ms
            ]
            out[segment["segment_id"]][detector] = windows_from_intervals(
                clipped, n_windows=n_windows, origin_ms=start_ms, min_overlap=min_overlap
            )
    return out


def build(key: dict, labels: dict[str, dict], adjudicated: dict, min_overlap: float) -> dict:
    by_segment = {row["segment_id"]: row for row in key["segments"]}
    predictions = detector_windows(key, min_overlap)
    detectors = sorted({name for row in predictions.values() for name in row})

    totals = {name: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for name in detectors}
    per_title: dict[str, dict[str, list]] = {name: defaultdict(list) for name in detectors}
    per_source: dict[str, dict] = defaultdict(lambda: {"segments": 0, "positive_windows": 0})
    excluded = {"unlabelable": 0, "no_label_given": 0}
    positive_windows = 0
    labelled_windows = 0

    for segment_id, row in sorted(by_segment.items()):
        n_windows = int(round(float(row["end_s"]) - float(row["start_s"])))
        truth: set[int] = set()
        universe: list[int] = []
        for index in range(n_windows):
            value = adjudicated.get((segment_id, index))
            if value is None:
                excluded["no_label_given"] += 1
                continue
            if value == "x":
                excluded["unlabelable"] += 1
                continue
            universe.append(index)
            if value == "1":
                truth.add(index)
        labelled_windows += len(universe)
        positive_windows += len(truth)
        source = row["source"]
        per_source[source]["segments"] += 1
        per_source[source]["positive_windows"] += len(truth)

        for name in detectors:
            predicted = predictions.get(segment_id, {}).get(name, set())
            counts = confusion(predicted, truth, universe=universe)
            for field in ("tp", "fp", "fn", "tn"):
                totals[name][field] += counts[field]
            per_title[name][row["file"]].append(counts)

    table = {}
    for name in detectors:
        counts = totals[name]
        precision = rate_with_interval(counts["tp"], counts["tp"] + counts["fp"])
        recall = rate_with_interval(counts["tp"], counts["tp"] + counts["fn"])
        recall_groups = [
            (
                sum(c["tp"] for c in rows),
                sum(c["tp"] + c["fn"] for c in rows),
            )
            for rows in per_title[name].values()
        ]
        precision_groups = [
            (
                sum(c["tp"] for c in rows),
                sum(c["tp"] + c["fp"] for c in rows),
            )
            for rows in per_title[name].values()
        ]
        table[name] = {
            "counts": counts,
            "precision_wilson_optimistic": precision,
            "recall_wilson_optimistic": recall,
            "precision_bootstrap_over_titles": bootstrap_groups(precision_groups),
            "recall_bootstrap_over_titles": bootstrap_groups(recall_groups),
            "f1": f1(precision["value"], recall["value"]),
            "titles": len(per_title[name]),
        }

    return {
        "window_rule": "any overlap" if min_overlap == 0 else f"at least {min_overlap:.0%} of the window",
        "headline_interval": "bootstrap over titles, 10000 resamples",
        "wilson_note": "reported as the optimistic bound, because windows in one title are not independent",
        "labelled_windows": labelled_windows,
        "ground_truth_positive_windows": positive_windows,
        "exclusions": excluded,
        "per_source": dict(per_source),
        "table": table,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--pool-key", type=Path, default=LABELING / "pool_key.json")
    parser.add_argument("--labels", type=Path, action="append", default=None)
    parser.add_argument(
        "--adjudicated",
        type=Path,
        default=None,
        help=(
            "the sheet the two labellers agreed after discussing their disagreements. Its "
            "answers are the ones the metrics use. Kappa stays on the two original sheets, "
            "because kappa is about the answers as first given."
        ),
    )
    parser.add_argument("-o", "--out", type=Path, default=OUT)
    parser.add_argument("--status-out", type=Path, default=STATUS_OUT)
    parser.add_argument(
        "--allow-uncommitted",
        action="store_true",
        help="for tests only. The output is stamped do_not_publish.",
    )
    arguments = parser.parse_args()

    key = json.loads(arguments.pool_key.read_text())
    label_paths = arguments.labels or sorted(LABELING.glob("labels_*.csv"))
    if arguments.adjudicated is not None:
        # The agreed sheet is read with the others, so it is hashed, frozen and reported the
        # same way, but it is never one of the two the kappa is computed between.
        label_paths = [path for path in label_paths if path != arguments.adjudicated]
        label_paths = label_paths + [arguments.adjudicated]
    sheets = {}
    for path in label_paths:
        answers = read_labels(path)
        sheets[path.name] = {
            "path": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path),
            "sha256": sha256_of(path),
            "answered_windows": sum(1 for value in answers.values() if value in ("0", "1")),
            "unlabelable_windows": sum(1 for value in answers.values() if value == "x"),
            "git_state": label_state(path),
            "answers": answers,
        }

    # Every segment on the sheet needs a figure, because the figure is the only thing the
    # labeller is allowed to look at. A segment whose plot failed to render would sit on the
    # sheet asking for an answer nobody can give.
    plots_dir = LABELING / "plots"
    missing_plots = [
        row["segment_id"]
        for row in key["segments"]
        if not (plots_dir / f"{row['segment_id']}.png").is_file()
    ]

    answered = {name: row for name, row in sheets.items() if row["answered_windows"]}
    if not answered:
        status = {
            "generated_on": "2026-09-17",
            "state": "awaiting labels" if not missing_plots else "not ready: plots are missing",
            "what_is_ready": [
                "the blinded pool (eval/labeling/pool.json) and its key",
                "one plot per segment (eval/labeling/plots/), no detector output on any of them",
                "blank sheets for two labellers (eval/labeling/labels_*.csv)",
                "the written guide (eval/labeling/GUIDE.md), which quotes the spec",
                "this analysis, which computes the metrics, the kappa and the bootstrap "
                "as soon as the sheets have answers in them",
            ],
            "what_is_missing": "the labels. Nobody on this lane labels anything.",
            "segments": len(key["segments"]),
            "titles": key["titles"],
            "sources": key["sources"],
            "source_count": len(key["sources"]),
            "windows_to_label": sum(
                int(round(float(row["end_s"]) - float(row["start_s"]))) for row in key["segments"]
            ),
            "sheets": {
                name: {k: v for k, v in row.items() if k != "answers"}
                for name, row in sheets.items()
            },
            "pool_key_sha256": sha256_of(arguments.pool_key),
            "plots": {
                "directory": str(plots_dir.relative_to(REPO)),
                "one_per_segment": len(key["segments"]) - len(missing_plots),
                "missing": missing_plots,
            },
        }
        arguments.status_out.write_text(json.dumps(status, indent=1) + "\n")
        if missing_plots:
            print(
                f"{len(missing_plots)} segments have no plot: {', '.join(missing_plots[:5])}"
                f"{' ...' if len(missing_plots) > 5 else ''}. Run `make labeling-plots`.",
                file=sys.stderr,
            )
            return 2
        print(
            f"no labels yet: {status['segments']} segments, "
            f"{status['windows_to_label']} windows waiting. wrote {arguments.status_out}"
        )
        return 0

    not_frozen = [
        f"{name} ({row['git_state']})"
        for name, row in answered.items()
        if row["git_state"] != "committed"
    ]
    if not_frozen and not arguments.allow_uncommitted:
        print(
            "these label files are not frozen: "
            + ", ".join(not_frozen)
            + ". EVAL_PLAN section 5 freezes labels before any comparison, so commit them "
            "first and run again.",
            file=sys.stderr,
        )
        return 2

    agreed_name = arguments.adjudicated.name if arguments.adjudicated else None
    names = sorted(name for name in answered if name != agreed_name)
    if not names:
        print(
            "the only sheet with answers in it is the agreed one. Pass the two labellers' "
            "sheets as well, because kappa is computed between them.",
            file=sys.stderr,
        )
        return 2
    primary = answered[names[0]]["answers"]
    second = answered[names[1]]["answers"] if len(names) > 1 else {}
    agreed = answered.get(agreed_name, {}).get("answers", {}) if agreed_name else {}

    # Adjudication: where both labellers gave the same answer, that is the answer. Where they
    # disagree, the window is held out until a human resolves it, because the plan says the
    # adjudicated labels are the ones the metrics use and nothing here may adjudicate. An agreed
    # sheet, written after the two of them talked, is that human resolution: its answers win
    # wherever it has one, including over a window they both got the same way.
    adjudicated: dict[tuple[str, int], str] = {}
    unresolved = 0
    for key_tuple, value in primary.items():
        other = second.get(key_tuple)
        if other is None or other == value:
            adjudicated[key_tuple] = value
        elif key_tuple not in agreed:
            unresolved += 1
    resolved_by_hand = 0
    for key_tuple, value in agreed.items():
        if adjudicated.get(key_tuple) != value:
            resolved_by_hand += 1
        adjudicated[key_tuple] = value

    report = {
        "generated_on": "2026-09-17",
        "set": "real clips, blind labelled from plots",
        "labels": {
            name: {k: v for k, v in row.items() if k != "answers"} for name, row in sheets.items()
        },
        "labels_committed": not not_frozen,
        "do_not_publish": bool(not_frozen),
        "pool_key_sha256": sha256_of(arguments.pool_key),
        "segments": len(key["segments"]),
        "titles": key["titles"],
        "sources": key["sources"],
        "adjudication": {
            "rule": (
                "agreement between the two sheets is the label; a disagreement is held out "
                "unless the agreed sheet answers it"
            ),
            "labeller_sheets": names,
            "agreed_sheet": agreed_name,
            "windows_held_out_for_discussion": unresolved,
            "windows_answered_by_the_agreed_sheet": len(agreed),
            "windows_the_agreed_sheet_changed": resolved_by_hand,
            "note": (
                "this script never picks a side. Resolve the disagreements together, write the "
                "agreed answers into a third sheet, and re-run passing it as --adjudicated."
            ),
        },
        "kappa": cohens_kappa(primary, second) if second else {"kappa": None, "why": "one sheet"},
        "kappa_is_between": names[:2],
        "any_overlap": build(key, sheets, adjudicated, 0.0),
        "half_window": build(key, sheets, adjudicated, 0.5),
    }
    arguments.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(f"wrote {arguments.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
