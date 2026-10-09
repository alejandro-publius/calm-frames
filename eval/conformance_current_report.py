#!/usr/bin/env python3
"""Build both preregistered window rules and error curves from one complete fresh run.

This reuses the committed scoring implementation. It never generates video,
changes truth labels, pools archived detector rows, or implies new baseline runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from conformance import report

REPO = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_current(design_path: Path, measurement_path: Path) -> dict:
    design = json.loads(design_path.read_text())
    measurement = json.loads(measurement_path.read_text())
    if measurement["design_sha256"] != digest(design_path):
        raise ValueError("measured design digest does not match the supplied frozen design")
    if (measurement.get("hazard_files_remaining") != 0
            or any("error" in row or "delete_error" in row for row in measurement["rows"])):
        raise ValueError("cleanup or analysis errors prevent a successful complete report")
    if (measurement.get("baselines_rerun") is not False
            or any("baselines" in row for row in measurement["rows"])):
        raise ValueError("baseline rows or claims do not belong in this detector-only report")
    ids = [row["clip_id"] for row in measurement["rows"]]
    intended = [clip["clip_id"] for clip in design["clips"]]
    if (not measurement.get("complete_design_evaluation")
            or len(ids) != len(set(ids)) or len(intended) != len(set(intended))
            or set(ids) != set(intended)):
        raise ValueError("a complete measurement of every frozen identity exactly once is required")
    for name in ("eval/conformance/report.py", "eval/metrics.py"):
        if measurement["source_sha256"].get(name) != digest(REPO / name):
            raise ValueError("scoring source changed since the measurement")
    with tempfile.TemporaryDirectory(prefix="calm-conformance-offline-report-") as directory:
        rows_path = Path(directory) / "measurements.jsonl"
        rows_path.write_text("".join(json.dumps(row) + "\n" for row in measurement["rows"]))
        result = report.build(design_path, rows_path)
    result["generated_on"] = measurement["generated_utc"][:10]
    result["git_commit"] = measurement["git_commit"]
    result["kind"] = "complete_current_source_conformance_report"
    result["encoding_protocol"] = measurement["encoding_protocol"]
    result["measurement_sha256"] = digest(measurement_path)
    result["source_sha256"] = measurement["source_sha256"]
    result["report_wrapper_sha256"] = digest(Path(__file__))
    result["environment"] = measurement["environment"]
    result["hazard_files_remaining"] = measurement["hazard_files_remaining"]
    result["sample"]["statement"] = (
        f"All {len(intended)} frozen clip identities were measured afresh with one recorded "
        "source tree and encoding protocol. Every exclusion is counted. Both preregistered "
        "window-overlap rules and the diagnostic tight-bounds rule use these same rows."
    )
    # The legacy report computes a 'shared' table even if only flashmap ran.
    # Remove that table and its flat copies rather than presenting a comparison.
    result["baseline_table_windows_every_detector_saw"] = {}
    result["baseline_operating_points"] = {}
    result["baselines_not_run"] = {name: "Not measured in this fresh current-source run."
        for name in ("EA IRIS", "Apple VideoFlashingReduction", "naive_luma_diff",
                     "ffmpeg_photosensitivity")}
    result["published"] = {name: value for name, value in result["published"].items()
        if not name.startswith(("flashmap_shared", "naive_", "ffmpeg_"))}
    # The old report inferred lead-in FPs from the baseline's missing first second.
    # No baselines ran here, so count actual false-positive windows directly.
    clips = {clip["clip_id"]: clip for clip in design["clips"]}
    lead_in_false_positives = elsewhere_false_positives = 0
    for row in measurement["rows"]:
        clip = clips[row["clip_id"]]
        if report.excluded_reason(row, clip):
            continue
        predicted = report.flashmap_windows(row, clip["truth"]["n_windows"], 0, False)
        false_positives = predicted - set(clip["truth"]["positive_windows"])
        lead_in = set(range(int(clip["flash_start_ms"] // 1000)))
        lead_in_false_positives += len(false_positives & lead_in)
        elsewhere_false_positives += len(false_positives - lead_in)
    result["published"]["false_positives_in_the_calm_lead_in"] = lead_in_false_positives
    result["published"]["false_positives_elsewhere"] = elsewhere_false_positives
    result["limits"] = (
        "Synthetic SDR intended-signal conformance, not clinical validation or a device test. "
        "Matrix/range conversion was corrected after the archived evaluation under a logged "
        "protocol deviation. Production detector thresholds and resolution are unchanged. "
        "Encoded near-limit signals can still cross thresholds. Baselines, IRIS ground-truth "
        "cross-checks and real-clip human labeling were not completed by this run."
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--measurement", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists; preserve previous evidence")
    result = build_current(args.design, args.measurement)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Wrote full current-source report: {args.out}")


if __name__ == "__main__":
    main()
