"""One machine-readable summary of what the pipeline can say about one video.

Written for the October 15 video reset so the app can read evidence without
parsing an HTML report. It composes existing records and adds nothing new of
its own: the media ledger row, the analyzer's maps, the local receipt, the
packaged manifest, the plots and the test record. Four states are kept apart
and never collapsed into one badge:

- actual findings: spans the analyzer measured over a published limit;
- simulated events: covers that were scheduled on purpose and detected nothing;
- unsupported or not analyzed: what no measurement covers;
- independent validation pending: nobody outside this repository has checked.

A summary describes files by hash. It is not playback evidence, not clinical
evidence and not a verdict about any television other than the settings it
names. Re-analysis by this repository's own analyzer is not independent
validation, and the summary says so.

    python -m pipeline.evidence_summary --ledger media/LICENSES.csv \
        --ledger-file HAZARD_example.mp4 --map results/x/example.wcag.json \
        --receipt build/x/local-library/local-receipts/<sha>.json \
        --manifest build/x/prepared-library/<bundle>/manifest.json \
        --out results/x/evidence-summary.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "calm-frames-evidence-summary-v1"
STATES = {
    "actual_findings": "Spans the analyzer measured over a published limit, with the profile, the settings and the window that triggered each.",
    "simulated_events": "Covers scheduled on purpose, for practice or demonstration. The analyzer found nothing there and they are never counted as findings.",
    "unsupported_or_not_analyzed": "What no measurement in this summary covers.",
    "independent_validation_pending": "Nobody outside this repository has checked the findings, the preparation or the playback. Re-analysis by this repository's own analyzer does not count.",
}
LIMITATIONS = [
    "The analyzer measures the published WCAG 2.2 and broadcast flash and pattern limits on decoded frames at a reduced working width; it is not a medical device and detection can miss flashing.",
    "A finding depends on the settings named here, including the viewing room: a stricter room adds a smaller area window and can add findings.",
    "A prepared rendition covers the planned spans; it does not prove what a viewer sees on any physical television.",
    "Hashes establish file identity, not that anyone watched the result.",
]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def ledger_row(ledger: Path, filename: str) -> dict:
    with ledger.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("file") == filename:
                return row
    raise SystemExit(f"{filename} has no row in {ledger}")


def source_block(row: dict, map_source: dict | None, color: dict | None) -> dict:
    return {
        "file": row["file"],
        "sha256": row["sha256"],
        "origin_url": row["source_page_url"],
        "licence": row["license"],
        "credit": row["credit_line"],
        "licence_checked_on": row["license_checked_on"],
        "duration_s": float(row["duration_s"]) if row.get("duration_s") else None,
        "resolution": row.get("resolution"),
        "notes": row.get("notes", ""),
        "hazard_prefix": row["file"].startswith("HAZARD_"),
        "container": None if map_source is None else {
            "size_bytes": map_source.get("size_bytes"),
            "coded_size": f"{map_source.get('coded_width')}x{map_source.get('coded_height')}",
            "container_frame_rate": map_source.get("container_frame_rate"),
            "frame_count": map_source.get("frame_count"),
            "first_pts_ms": map_source.get("first_pts_ms"),
            "last_pts_ms": map_source.get("last_pts_ms"),
            "variable_frame_rate": map_source.get("variable_frame_rate"),
            "frame_interval_ms": map_source.get("frame_interval_ms"),
            "timestamp_source": map_source.get("timestamp_source"),
        },
        "color": None if color is None else {k: v for k, v in color.items() if k not in ("analysis_width", "analysis_height")},
    }


def run_block(path: Path, repo: Path) -> dict:
    doc = _load(path)
    profile = doc["profile"]
    try:
        relative = str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        relative = str(path)
    return {
        "profile": profile.get("name"),
        "map_path": relative,
        "map_sha256": sha256_of(path),
        "signed": bool(doc.get("signature")),
        "analyzer": doc.get("generator"),
        "created_utc": doc.get("created_utc"),
        "settings": {
            "analysis_width": doc["color"].get("analysis_width"),
            "analysis_height": doc["color"].get("analysis_height"),
            "luminance_model": doc["color"].get("luminance_model"),
            "flash_limit_per_second": profile.get("flash_limit_per_second"),
            "window_ms": profile.get("window_ms"),
            "area_fraction_limit": profile.get("area_fraction_limit"),
            "area_windows": [{"name": w["name"], "width_px": w["width_px"], "height_px": w["height_px"]} for w in profile.get("area_windows", [])],
            "room": None if not profile.get("room") else {k: profile["room"].get(k) for k in ("tv_diagonal_in", "seat_distance_in", "display_aspect")},
            "pattern_rule_applied": doc["summary"].get("pattern_rule_applied"),
            "picture_measured_on": doc.get("picture", {}).get("measured_on"),
        },
        "summary": {k: doc["summary"].get(k) for k in ("pass", "flash_pass", "pattern_pass", "segment_count", "general_segment_count", "red_segment_count", "pattern_segment_count", "hidden_ms")},
        "segments": [
            {k: s.get(k) for k in ("reason", "start_ms", "end_ms", "flash_first_ms", "flash_last_ms", "max_flashes_in_window", "area_fraction", "area_window", "triggered_by", "breaks_baseline")}
            for s in doc.get("segments", [])
        ],
    }


def distinct_spans(runs: list[dict]) -> list[dict]:
    """The same flashing found by several runs is one span, not several findings.

    Segments from every run are merged when they overlap in time. Each merged span keeps the
    widest bounds any run gave it, the runs that found it (profile, room and map), and whether
    any run broke the WCAG baseline window rather than only a room window.
    """
    items = []
    for run in runs:
        for segment in run["segments"]:
            items.append((float(segment["start_ms"]), float(segment["end_ms"]), run, segment))
    items.sort(key=lambda item: (item[0], item[1]))
    spans: list[dict] = []
    for start, end, run, segment in items:
        found = {"profile": run["profile"], "map_path": run["map_path"], "room": run["settings"]["room"],
                 "reason": segment.get("reason"), "start_ms": segment.get("start_ms"), "end_ms": segment.get("end_ms"),
                 "area_fraction": segment.get("area_fraction"), "area_window": segment.get("area_window")}
        if spans and start <= spans[-1]["end_ms"]:
            spans[-1]["end_ms"] = max(spans[-1]["end_ms"], end)
            spans[-1]["found_by"].append(found)
            spans[-1]["breaks_wcag_baseline"] = spans[-1]["breaks_wcag_baseline"] or bool(segment.get("breaks_baseline"))
        else:
            spans.append({"start_ms": start, "end_ms": end, "found_by": [found],
                          "breaks_wcag_baseline": bool(segment.get("breaks_baseline"))})
    for span in spans:
        span["reasons"] = sorted({f["reason"] for f in span["found_by"] if f["reason"]})
        span["found_in_runs"] = len(span["found_by"])
    return spans


def preparation_block(receipt_path: Path | None, manifest_path: Path | None, repo: Path) -> dict:
    block: dict = {"status": "not run", "receipt": None, "manifest": None}
    if receipt_path is not None:
        receipt = _load(receipt_path)
        artifacts = {}
        for preset, item in (receipt.get("artifacts") or {}).items():
            hashes = item.get("sha256", {}) if isinstance(item, dict) else {}
            artifacts[preset] = {"files": hashes, **{k: v for k, v in item.items() if k not in ("sha256",)}} if isinstance(item, dict) else item
        block.update({
            "status": receipt.get("status", "unknown"),
            "receipt": {
                "path": _rel(receipt_path, repo), "sha256": sha256_of(receipt_path),
                "source_sha256": receipt.get("source_sha256"), "title": receipt.get("title"),
                "presets": receipt.get("presets"), "verification": receipt.get("verification"),
                "physical_tv_validated": receipt.get("physical_tv_validated", False),
                "artifacts": artifacts,
            },
        })
    if manifest_path is not None:
        manifest = _load(manifest_path)
        titles = []
        for title in manifest.get("titles", []):
            titles.append({
                "id": title.get("id"), "title": title.get("title"), "sourceSha256": title.get("sourceSha256"),
                "durationMs": title.get("durationMs"),
                "maps": {p: {"path": m.get("path"), "sha256": m.get("sha256")} for p, m in (title.get("maps") or {}).items()},
                "renditions": {p: {k: r.get(k) for k in ("path", "sha256", "durationMs", "startOffsetMs", "guardBandMs", "minCoverMs")} for p, r in (title.get("renditions") or {}).items()},
                "verification": title.get("verification"),
            })
        block["manifest"] = {
            "path": _rel(manifest_path, repo), "sha256": sha256_of(manifest_path),
            "bundleId": manifest.get("bundleId"), "version": manifest.get("version"),
            "publicKeySha256": hashlib.sha256((manifest.get("publicKeyBase64") or "").encode()).hexdigest() if manifest.get("publicKeyBase64") else None,
            "titles": titles, "file_count": len(manifest.get("files") or {}),
        }
    return block


def _rel(path: Path, repo: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        return str(path)


def build_summary(*, repo: Path, ledger: Path, ledger_file: str, maps: list[Path], receipt: Path | None,
                  manifest: Path | None, plots: list[Path], negative_controls: Path | None,
                  test_file: str | None, simulated: list[dict], not_analyzed: list[str],
                  report: str | None, extra_limitations: list[str]) -> dict:
    row = ledger_row(ledger, ledger_file)
    runs = [run_block(path, repo) for path in maps]
    first = _load(maps[0]) if maps else None
    actual = []
    for run in runs:
        for segment in run["segments"]:
            actual.append({"profile": run["profile"], "room": run["settings"]["room"], **segment})
    distinct = distinct_spans(runs)
    try:
        commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = None
    negative = _load(negative_controls) if negative_controls else None
    summary = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": {"name": "pipeline.evidence_summary", "repository_commit": commit},
        "states": dict(STATES),
        "source": source_block(row, None if first is None else first.get("source"), None if first is None else first.get("color")),
        "analysis": {"runs": runs},
        "findings": {
            "actual": actual,
            "actual_count": len(actual),
            "distinct_spans": distinct,
            "distinct_span_count": len(distinct),
            "simulated": simulated,
            "unsupported_or_not_analyzed": not_analyzed,
            "independent_validation": "pending",
        },
        "preparation": preparation_block(receipt, manifest, repo),
        "report": {"html": report, "plots": [_rel(p, repo) for p in plots]},
        "tests": None if not test_file else {
            "file": test_file,
            "negative_controls": None if negative is None else {
                "path": _rel(negative_controls, repo), "sha256": sha256_of(negative_controls),
                "controls": [{"control": c["control"], "break": c["break"], "tests_that_failed": c["tests_that_failed"], "restored": c["restored"]} for c in negative.get("controls", [])],
            },
        },
        "limitations": LIMITATIONS + extra_limitations,
    }
    return summary


def validate(summary: dict) -> list[str]:
    """Explicit checks, so a consumer without a schema library can refuse a bad summary."""
    problems: list[str] = []
    for key in ("schema", "generated_utc", "generator", "states", "source", "analysis", "findings", "preparation", "report", "limitations"):
        if key not in summary:
            problems.append(f"missing {key}")
    if summary.get("schema") != SCHEMA:
        problems.append("wrong schema")
    if set(summary.get("states", {})) != {"actual_findings", "simulated_events", "unsupported_or_not_analyzed", "independent_validation_pending"}:
        problems.append("the four states must all be present")
    findings = summary.get("findings", {})
    for key in ("actual", "simulated", "unsupported_or_not_analyzed", "independent_validation"):
        if key not in findings:
            problems.append(f"findings missing {key}")
    if findings.get("independent_validation") not in ("pending", "done"):
        problems.append("independent_validation must be pending or done")
    if findings.get("actual_count") != len(findings.get("actual", [])):
        problems.append("actual_count disagrees with the list")
    if findings.get("distinct_span_count") != len(findings.get("distinct_spans", [])):
        problems.append("distinct_span_count disagrees with the list")
    if findings.get("actual") and not findings.get("distinct_spans"):
        problems.append("findings without distinct spans")
    for finding in findings.get("actual", []):
        for key in ("profile", "reason", "start_ms", "end_ms", "area_fraction", "area_window"):
            if key not in finding:
                problems.append(f"finding missing {key}")
    for event in findings.get("simulated", []):
        if event.get("detected") is not False:
            problems.append("a simulated event must say detected: false")
    source = summary.get("source", {})
    if not isinstance(source.get("sha256"), str) or len(source["sha256"]) != 64:
        problems.append("source sha256 must be 64 hex characters")
    if summary.get("preparation", {}).get("status") not in ("ready", "failed", "not run", "unknown"):
        problems.append("preparation status must be ready, failed, not run or unknown")
    text = json.dumps(summary).lower()
    for phrase in ("seizure-proof", "seizure proof", "prevents seizures", "clinically validated", "universal filter"):
        if phrase in text:
            problems.append(f"forbidden claim: {phrase}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--ledger-file", required=True, help="the file column of the ledger row")
    parser.add_argument("--map", type=Path, action="append", default=[], help="an analyzer map; repeat per profile")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--plot", type=Path, action="append", default=[])
    parser.add_argument("--negative-controls", type=Path)
    parser.add_argument("--test-file")
    parser.add_argument("--simulated", type=Path, help="JSON list of scheduled events, each with detected: false")
    parser.add_argument("--not-analyzed", action="append", default=[])
    parser.add_argument("--report")
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    simulated = _load(args.simulated) if args.simulated else []
    summary = build_summary(repo=args.repo, ledger=args.ledger, ledger_file=args.ledger_file, maps=args.map,
                            receipt=args.receipt, manifest=args.manifest, plots=args.plot,
                            negative_controls=args.negative_controls, test_file=args.test_file,
                            simulated=simulated, not_analyzed=args.not_analyzed, report=args.report,
                            extra_limitations=args.limitation)
    problems = validate(summary)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {args.out}: {summary['findings']['actual_count']} actual finding(s), preparation {summary['preparation']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
