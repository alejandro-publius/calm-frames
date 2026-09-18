#!/usr/bin/env python3
"""Every table and figure, rebuilt offline from the committed result files.

This is what `make reproduce` runs. It reads results/*.json and writes results/figures/. It
decodes no video, generates no clip, calls no network and imports no flashmap: on a clean
checkout with the results committed, it produces the same pictures and the same tables.

Anything missing is said out loud rather than drawn as an empty axis: a figure that exists but
is built on nothing is worse than a figure that is not there.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
FIGURES = RESULTS / "figures"

CURVE_TITLES = {
    "flash_rate_hz": "flash rate asked for (Hz)",
    "observed_flash_rate_hz": "flash rate the frames actually show (Hz)",
    "luminance_step_over_limit": "luminance step, as a multiple of the general flash limit",
    "field_coverage_over_limit": "10 degree field coverage, as a multiple of the area limit",
    "area_fraction_of_picture": "flashing area, as a fraction of the picture",
    "ucs_distance_over_limit": "UCS distance, as a multiple of the red flash limit",
    "frame_rate": "frame rate (fps)",
    "timing": "frame timing pattern",
    "resolution": "resolution",
    "compression_crf": "libx264 quantiser",
    "color_tagging": "colour tagging",
    "shape": "shape of the flashing region",
    "red_mode": "colour pair under test",
    "letterbox": "letterbox bars, as a fraction of the coded height",
    "near_threshold": "is some governing quantity within 15% of its limit",
}
DETECTOR_STYLE = {
    "flashmap": ("#1f4e79", "o", "flashmap"),
    "naive_luma_diff": ("#7a7a3b", "s", "naive luminance differencing"),
    "ffmpeg_photosensitivity": ("#a33", "^", "ffmpeg photosensitivity filter"),
}


def detector_key(name: str) -> str:
    return name.split("@")[0]


def number(value, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def interval(row: dict, metric: str) -> str:
    value = row[metric]["value"]
    if value is None:
        return "n/a"
    return (
        f"{value:.3f} [{row[metric]['wilson_lo']:.3f}, {row[metric]['wilson_hi']:.3f}] "
        f"({row[metric]['numerator']}/{row[metric]['denominator']})"
    )


def pyplot():
    """matplotlib, or None with a clear reason. The tables do not need it and still get written."""
    try:
        import matplotlib

        matplotlib.use("Agg")  # no window, ever
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        return None


def curve_figure(axis: str, points: list[dict], out_dir: Path) -> Path | None:
    plt = pyplot()
    if plt is None:
        return None
    usable = [point for point in points if any(isinstance(v, dict) for v in point.values())]
    if not usable:
        return None
    labels = [str(point["bucket"]) for point in usable]
    x = range(len(labels))

    figure, (top, bottom) = plt.subplots(2, 1, figsize=(max(7, len(labels) * 0.55), 6.5), sharex=True)
    for metric, axes in (("recall", top), ("precision", bottom)):
        for name in sorted({k for point in usable for k, v in point.items() if isinstance(v, dict)}):
            colour, marker, label = DETECTOR_STYLE.get(
                detector_key(name), ("#555", "x", detector_key(name))
            )
            values, los, his, xs = [], [], [], []
            for index, point in enumerate(usable):
                row = point.get(name)
                if not isinstance(row, dict) or row.get(metric) is None:
                    continue
                values.append(row[metric])
                los.append(row[f"{metric}_wilson"][0])
                his.append(row[f"{metric}_wilson"][1])
                xs.append(index)
            if not values:
                continue
            axes.plot(xs, values, marker=marker, color=colour, linewidth=1.2, markersize=4, label=label)
            axes.fill_between(xs, los, his, color=colour, alpha=0.12)
        axes.set_ylabel(metric)
        axes.set_ylim(-0.02, 1.02)
        axes.grid(alpha=0.25)
    top.legend(fontsize=8, loc="lower right")
    bottom.set_xticks(list(x))
    bottom.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    bottom.set_xlabel(CURVE_TITLES.get(axis, axis))
    counts = [point.get("clips", 0) for point in usable]
    figure.suptitle(
        f"Conformance error curve: {CURVE_TITLES.get(axis, axis)}\n"
        f"{sum(counts)} clips in this panel, shaded bands are Wilson 95% intervals",
        fontsize=10,
    )
    figure.text(
        0.01,
        0.012,
        "A missing point is a rate with no denominator, not missing data.\n"
        "No precision point means the detector predicted nothing in that bucket; no recall\n"
        "point means the bucket holds no true positives.",
        fontsize=7.5,
        color="#444",
    )
    figure.tight_layout(rect=(0, 0.05, 1, 0.94))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"conformance_{axis}.png"
    figure.savefig(path, dpi=120)
    plt.close(figure)
    return path


def conformance_tables(report: dict) -> str:
    sample = report["sample"]
    lines = [
        "# Conformance suite",
        "",
        f"Sample: {sample['statement']}",
        "",
        f"- clips designed: {sample['clips_designed']}",
        f"- clips measured: {sample['clips_measured']}",
        f"- clips kept after exclusions: {sample['clips_kept']}",
        f"- one second windows kept: {sample['windows_kept']}",
        f"- ground truth positive windows: {sample['ground_truth_positive_windows']}",
        f"- complete run: {'yes' if sample['is_complete_run'] else 'no, this is a partial run'}",
        "",
        "Exclusions: "
        + (", ".join(f"{key} ({value})" for key, value in report["exclusions"].items()) or "none"),
        "",
        "## Over every window",
        "",
        "| detector | precision (Wilson 95%) | recall (Wilson 95%) | F1 |",
        "|---|---|---|---|",
    ]
    for name, row in report["headline_all_windows"].items():
        lines.append(
            f"| {name} | {interval(row, 'precision')} | {interval(row, 'recall')} | "
            f"{number(row['f1'])} |"
        )
    lines += [
        "",
        "## Over the windows every detector saw",
        "",
        "ffmpeg's filter has its first second dropped, so window 0 of every clip is missing from "
        "its denominator. This table puts every detector on the windows that are left.",
        "",
        "| detector | precision (Wilson 95%) | recall (Wilson 95%) | F1 |",
        "|---|---|---|---|",
    ]
    for name, row in report["baseline_table_windows_every_detector_saw"].items():
        lines.append(
            f"| {name} | {interval(row, 'precision')} | {interval(row, 'recall')} | "
            f"{number(row['f1'])} |"
        )
    flashmap = report["headline_all_windows"]["flashmap (this project)"]
    lines += [
        "",
        "## Secondary",
        "",
        f"- clip level (does the clip fail at all): precision "
        f"{interval(report['clip_level'], 'precision')}, recall "
        f"{interval(report['clip_level'], 'recall')}",
        f"- segment recall: {interval(flashmap, 'segment_recall')}",
        f"- false positive seconds per minute of calm: "
        f"{number(flashmap.get('false_positive_seconds_per_minute_of_calm'), 2)} over "
        f"{flashmap.get('calm_windows')} calm windows",
    ]
    if "onset_lead_windows" in flashmap:
        lead = flashmap["onset_lead_windows"]
        lines.append(
            f"- onset lead: median {lead['median']} window(s), "
            f"{lead['share_early_or_on_time']:.0%} of found segments hidden before the flashing "
            f"started (n={lead['n']})"
        )
    lines += ["", "## Known disagreements", ""]
    for key, text in report["known_disagreements"].items():
        lines.append(f"- **{key}**: {text}")
    return "\n".join(lines) + "\n"


def baseline_table(report: dict) -> str:
    lines = [
        "# Baselines",
        "",
        f"Set: {report['set']}",
        "",
        report["table_universe"],
        "",
        "| detector | precision | recall | F1 |",
        "|---|---|---|---|",
    ]
    for name, row in report["table"].items():
        lines.append(
            f"| {name} | {interval(row, 'precision')} | {interval(row, 'recall')} | "
            f"{number(row['f1'])} |"
        )
    lines += ["", "## Not run", ""]
    for name, row in report["not_run"].items():
        lines.append(f"- **{name}**: {row['why']}")
    lines += ["", "## Operating points", ""]
    for name, block in report["operating_points"].items():
        if not isinstance(block, dict) or "best_f1_operating_point" not in block:
            continue
        best = block["best_f1_operating_point"]
        if best:
            lines.append(
                f"- {name}: best F1 at threshold {best['threshold']} "
                f"(precision {number(best['precision'])}, recall {number(best['recall'])}, "
                f"F1 {number(best['f1'])}), chosen on the conformance suite"
            )
    return "\n".join(lines) + "\n"


def ablation_table(report: dict) -> str:
    lines = ["# Ablations", ""]
    detection = report.get("detection")
    if detection:
        check = detection["default_arm_matches_main_run"]
        lines += [
            f"{detection['clips']} clips, {detection['errors']} errors. Default arm compared "
            f"against the main run on {check['clips_compared']} clips, "
            f"{check['mismatched']} mismatched.",
            "",
            "| arm | precision | recall | change in precision | change in recall |",
            "|---|---|---|---|---|",
        ]
        for arm, row in detection["arms"].items():
            lines.append(
                f"| {arm} | {interval(row, 'precision')} | {interval(row, 'recall')} | "
                f"{number(row.get('precision_change_vs_default'))} | "
                f"{number(row.get('recall_change_vs_default'))} |"
            )
    guard = report.get("guard_band")
    if guard and "covered_before_onset" in guard:
        lines += [
            "",
            "## Guard band (simulated, not measured on a device)",
            "",
            guard["latency_is_assumed_not_measured"],
            "",
            "| guard band (ms) | "
            + " | ".join(f"latency {value} ms" for value in guard["assumed_render_latency_ms"])
            + " |",
            "|---" * (1 + len(guard["assumed_render_latency_ms"])) + "|",
        ]
        for band, row in guard["covered_before_onset"].items():
            cells = [
                f"{number(row[str(latency)]['value'])} "
                f"({row[str(latency)]['numerator']}/{row[str(latency)]['denominator']})"
                for latency in guard["assumed_render_latency_ms"]
            ]
            lines.append(f"| {band} | " + " | ".join(cells) + " |")
    cover = report.get("cover")
    if cover and "all" in cover:
        lines += [
            "",
            "## Cover: dim against opaque",
            "",
            cover["why_red_is_always_opaque"],
            "",
            "| segments | uncovered still flagged | dim still flagged | opaque still flagged |",
            "|---|---|---|---|",
        ]
        for label, key in (
            ("all", "all"),
            ("red", "red_segments"),
            ("non red", "non_red_segments"),
        ):
            row = cover.get(key)
            if not row:
                continue
            lines.append(
                f"| {label} ({row['all']['clips'] if 'all' in row else row['uncovered']['clips']}) | "
                f"{row['uncovered']['clips_still_flagged']} | "
                f"{row['dim_10_percent']['clips_still_flagged']} | "
                f"{row['opaque']['clips_still_flagged']} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--out-dir", type=Path, default=FIGURES)
    arguments = parser.parse_args()

    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    made: list[str] = []
    missing: list[str] = []

    conformance_path = arguments.results / "conformance.json"
    if conformance_path.exists():
        report = json.loads(conformance_path.read_text())
        (arguments.out_dir / "conformance_table.md").write_text(conformance_tables(report))
        made.append("conformance_table.md")
        if pyplot() is None:
            missing.append(
                "the error curve figures: matplotlib is not installed in this interpreter. "
                "The tables above were written without it."
            )
        else:
            for axis, points in report["error_curves"].items():
                path = curve_figure(axis, points, arguments.out_dir)
                if path:
                    made.append(path.name)
    else:
        missing.append("results/conformance.json (run make conformance)")

    baselines_path = arguments.results / "baselines.json"
    if baselines_path.exists():
        (arguments.out_dir / "baselines_table.md").write_text(
            baseline_table(json.loads(baselines_path.read_text()))
        )
        made.append("baselines_table.md")
    else:
        missing.append("results/baselines.json (run make baselines)")

    ablations_path = arguments.results / "ablations.json"
    if ablations_path.exists():
        (arguments.out_dir / "ablations_table.md").write_text(
            ablation_table(json.loads(ablations_path.read_text()))
        )
        made.append("ablations_table.md")
    else:
        missing.append("results/ablations.json (run make ablations)")

    realclips_path = arguments.results / "realclips.json"
    if not realclips_path.exists():
        missing.append(
            "results/realclips.json, which needs human labels. "
            "results/realclips_status.json says what is ready and what is not."
        )

    print(f"wrote {len(made)} artifacts to {arguments.out_dir}")
    for name in made:
        print(f"  {name}")
    if missing:
        print("not built, because their input is not here:")
        for name in missing:
            print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
