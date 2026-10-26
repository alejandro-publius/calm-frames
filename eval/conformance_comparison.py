#!/usr/bin/env python3
"""Compare two fresh encoding protocols on exactly the same frozen clip identities."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from conformance.recheck import summarize
from conformance.report import excluded_reason

REPO = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(design: dict, before: dict, after: dict) -> dict:
    if before["design_sha256"] != after["design_sha256"]:
        raise ValueError("the frozen design changed")
    def controlled_sources(result):
        return {name: value for name, value in result["source_sha256"].items()
                if name not in ("eval/conformance/render.py", "eval/conformance/recheck.py")}
    if not controlled_sources(before) or controlled_sources(before) != controlled_sources(after):
        raise ValueError("detector, truth or scoring source changed; protocol effects are confounded")
    if not before.get("environment") or before["environment"] != after.get("environment"):
        raise ValueError("runtime or codec environment changed; protocol effects are confounded")
    for name in ("eval/conformance/report.py", "eval/metrics.py", "eval/conformance/recheck.py"):
        if after["source_sha256"].get(name) != digest(REPO / name):
            raise ValueError("current scoring source differs from the measured source")
    old = {row["clip_id"]: row for row in before["rows"]}
    new = {row["clip_id"]: row for row in after["rows"]}
    if (len(old) != len(before["rows"]) or len(new) != len(after["rows"])
            or not old.keys() <= new.keys()):
        raise ValueError("every reference identity must be measured exactly once in both runs")
    clips = [clip for clip in design["clips"] if clip["clip_id"] in old]
    if len(clips) != len(old):
        raise ValueError("reference identity is absent from the frozen design")
    clips.sort(key=lambda clip: clip["order_index"])
    shared = [clip for clip in clips if not excluded_reason(old[clip["clip_id"]], clip)
              and not excluded_reason(new[clip["clip_id"]], clip)]

    def rows_for(rows, chosen):
        return [rows[clip["clip_id"]] for clip in chosen]

    return {
        "kind": "paired_encoding_protocol_comparison",
        "detector_and_truth_sources_unchanged": True,
        "runtime_environment_unchanged": True,
        "environment": before["environment"],
        "before_encoding_protocol": before.get("encoding_protocol", "unlabeled legacy renderer; see source hashes"),
        "after_encoding_protocol": after.get("encoding_protocol", "unlabeled renderer; see source hashes"),
        "comparison_wrapper_sha256": digest(Path(__file__)),
        "window_rule": "primary: any overlap between the hide interval and the one-second window",
        "paired_clip_ids": [clip["clip_id"] for clip in clips],
        "paired_clips_measured": len(clips),
        "before_own_exclusions": summarize(clips, rows_for(old, clips), []),
        "after_own_exclusions": summarize(clips, rows_for(new, clips), rows_for(old, clips)),
        "common_kept_clips": len(shared),
        "common_kept_before": summarize(shared, rows_for(old, shared), []),
        "common_kept_after": summarize(shared, rows_for(new, shared), rows_for(old, shared)),
        "limits": "Same frozen identities and labels, with exclusions reported for each run "
                  "and an additional comparison on the intersection of kept clips. "
                  "This measures an encoding protocol correction, not a detector improvement. "
                  "No current matched baseline comparison or clinical conclusion is implied.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists; preserve previous evidence")
    inputs = {name: path.read_bytes() for name, path in
              (("design", args.design), ("before", args.before), ("after", args.after))}
    design_hash = hashlib.sha256(inputs["design"]).hexdigest()
    before, after = json.loads(inputs["before"]), json.loads(inputs["after"])
    if before["design_sha256"] != design_hash:
        raise ValueError("supplied design does not match the measured design digest")
    result = compare(json.loads(inputs["design"]), before, after)
    result["input_sha256"] = {name: hashlib.sha256(data).hexdigest()
                              for name, data in inputs.items()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Wrote paired comparison of {result['paired_clips_measured']} unchanged clip IDs")


if __name__ == "__main__":
    main()
