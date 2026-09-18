"""The step that blocks publishing.

A title may appear in kid mode only when every one of these passes:

1. the source file still hashes to the SHA-256 the title is filed under, and
   every map is bound to that same hash;
2. the analyzer verifies each map's signature against the public key;
3. flashmap on each kid safe rendition reports zero violations for that
   preset;
4. the on-device cover schedule rendered over the ORIGINAL video (poster,
   black or dim modelled in linear light, whichever is stricter) reports zero
   violations for that preset;
5. every BIF frame and every poster comes from a calm moment;
6. the stored hide plan is the plan the map produces, and the rendition really
   shows the cover still across each covered span;
7. the kid safe rendition has the source's picture rectangle and the source's
   frame timing. A title is analyzed from the source file and never from a
   re-encode, so the map that ships describes the source. The rendition is what
   plays. A hide plan built from one only lines up with the other while the two
   agree on where the picture sits and when each frame arrives.

Checks 1, 5 and 6 do not go through the analyzer, so a broken or missing
analyzer cannot turn them off quietly. Anything that cannot be read counts as
a failure: a map we cannot parse is never a clean bill of health.

Exit codes: 0 pass, 1 fail, 2 the request itself was wrong.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence

from . import PipelineError
from .catalog import STATUS_FAILED, STATUS_VERIFIED, read_entry, update_index, write_entry
from .flashmap_adapter import FlashMapDoc, FlashmapAdapter, MapFormatError, load_map
from .hashing import sha256_file
from .hideplan import DEFAULT_CALM_MARGIN_MS, HidePlan, build_cover_intervals, is_calm
from .layout import TitleLayout
from .probe import VideoProbe
from .render import cover_psnr, render_cover_model

# A covered span must match the cover still at least this closely, in dB.
# Identical frames give inf. A span that still shows the film scores far lower.
COVER_PSNR_MIN_DB = 30.0
# How many covered spans to sample for that check. Sampling keeps verify
# affordable on a feature length title.
COVER_SAMPLE_LIMIT = 6

# How far a rendition's timing may sit from the source's and still be showing
# the same picture at the same moment: half a frame. Less than that and nothing
# has moved by a whole frame anywhere. This is an engineering tolerance, not a
# number from a spec, and docs/SPEC_SOURCES.md is where spec numbers live.
TIMING_TOLERANCE_FRAMES = 0.5


@dataclass
class Check:
    name: str
    passed: bool
    detail: str
    data: dict = field(default_factory=dict)


@dataclass
class VerifyReport:
    sha256: str
    source_path: str
    presets: list[str]
    checks: list[Check] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [check for check in self.checks if not check.passed]

    def add(self, name: str, passed: bool, detail: str, **data) -> Check:
        check = Check(name=name, passed=passed, detail=detail, data=data)
        self.checks.append(check)
        return check

    def to_dict(self) -> dict:
        return {
            "sha256": self.sha256,
            "source_path": self.source_path,
            "presets": self.presets,
            "passed": self.passed,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "checks": [asdict(check) for check in self.checks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VerifyReport":
        report = cls(
            sha256=str(data.get("sha256", "")),
            source_path=str(data.get("source_path", "")),
            presets=list(data.get("presets", [])),
            started_at=float(data.get("started_at", 0.0)),
            finished_at=float(data.get("finished_at", 0.0)),
        )
        report.checks = [
            Check(
                name=str(item.get("name", "")),
                passed=bool(item.get("passed")),
                detail=str(item.get("detail", "")),
                data=dict(item.get("data", {})),
            )
            for item in data.get("checks", [])
        ]
        return report

    def summary(self) -> str:
        if self.passed:
            return f"VERIFY PASSED for {self.sha256[:12]} ({len(self.checks)} checks)"
        lines = [
            f"VERIFY FAILED for {self.sha256[:12]}: "
            f"{len(self.failures)} of {len(self.checks)} checks failed"
        ]
        for check in self.failures:
            lines.append(f"  FAIL {check.name}: {check.detail}")
        return "\n".join(lines)


def _geometry(doc: FlashMapDoc) -> dict:
    """The shape and the timing a map reports, or None for anything it does not say.

    Nothing here is guessed. A field the map does not carry comes back None and the
    comparison below treats that as a mismatch, because a rendition we cannot measure
    against the source is a rendition we cannot publish.
    """
    raw = doc.raw if isinstance(doc.raw, dict) else {}
    source = raw.get("source")
    source = source if isinstance(source, dict) else {}
    picture = raw.get("picture")
    picture = picture if isinstance(picture, dict) else {}
    coded = picture.get("coded")
    intervals = source.get("frame_interval_ms")
    intervals = intervals if isinstance(intervals, dict) else {}

    rect = None
    if isinstance(coded, dict):
        values = [coded.get(key) for key in ("left", "top", "width", "height")]
        if all(isinstance(value, (int, float)) for value in values):
            rect = tuple(int(value) for value in values)

    def number(value):
        return float(value) if isinstance(value, (int, float)) else None

    return {
        "coded_width": number(source.get("coded_width")),
        "coded_height": number(source.get("coded_height")),
        "picture_coded": rect,
        "picture_source": picture.get("source"),
        "frame_count": number(source.get("frame_count")),
        "first_pts_ms": number(source.get("first_pts_ms")),
        "last_pts_ms": number(source.get("last_pts_ms")),
        "median_interval_ms": number(intervals.get("median")),
    }


def compare_rendition_to_source(
    source_map: FlashMapDoc,
    rendition_map: FlashMapDoc,
    *,
    tolerance_frames: float = TIMING_TOLERANCE_FRAMES,
) -> tuple[bool, list[str], dict]:
    """Is the rendition the same picture, in the same place, at the same times?

    A title is always analyzed from the source file, never from a re-encode, so the map that
    ships describes the source. The rendition is the file that actually plays, and the hide
    plan built from the source only lines up with it if the two agree on where the picture is
    and when each frame arrives. So: the same coded frame, the same picture rectangle, the
    same number of frames, and a timeline that has not slid or stretched by as much as half a
    frame.

    Returns (passed, problems, data). Anything that cannot be read is a problem, never a pass.
    """
    src = _geometry(source_map)
    ren = _geometry(rendition_map)
    problems: list[str] = []

    if ren["picture_source"] != "carried":
        problems.append(
            "the rendition was measured on a rectangle of its own "
            f"({ren['picture_source']!r}), not the one carried over from the source map"
        )
    for key, name in (("coded_width", "coded width"), ("coded_height", "coded height")):
        if src[key] is None or ren[key] is None or src[key] != ren[key]:
            problems.append(f"{name} is {src[key]} in the source and {ren[key]} here")
    if src["picture_coded"] is None or ren["picture_coded"] is None:
        problems.append(
            f"picture rectangle in coded pixels is {src['picture_coded']} in the source "
            f"and {ren['picture_coded']} here, and both have to be readable"
        )
    elif src["picture_coded"] != ren["picture_coded"]:
        problems.append(
            f"picture rectangle is {src['picture_coded']} in the source and "
            f"{ren['picture_coded']} here, as left, top, width, height in coded pixels"
        )
    if src["frame_count"] is None or ren["frame_count"] is None:
        problems.append("one of the two maps does not say how many frames it measured")
    elif src["frame_count"] != ren["frame_count"]:
        problems.append(
            f"the source has {src['frame_count']:.0f} frames and the rendition has "
            f"{ren['frame_count']:.0f}"
        )

    median = src["median_interval_ms"]
    tolerance_ms = None
    if median is None or median <= 0:
        problems.append("the source map does not say how far apart its frames are")
    else:
        tolerance_ms = tolerance_frames * median
        for key, name in (("first_pts_ms", "first frame"), ("last_pts_ms", "last frame")):
            if src[key] is None or ren[key] is None:
                problems.append(f"one of the two maps does not say when its {name} is")
        if all(src[k] is not None and ren[k] is not None for k in ("first_pts_ms", "last_pts_ms")):
            start_shift = abs(ren["first_pts_ms"] - src["first_pts_ms"])
            src_span = src["last_pts_ms"] - src["first_pts_ms"]
            ren_span = ren["last_pts_ms"] - ren["first_pts_ms"]
            span_change = abs(ren_span - src_span)
            if start_shift > tolerance_ms:
                problems.append(
                    f"the rendition starts {start_shift:.3f} ms away from the source, "
                    f"and half a frame is {tolerance_ms:.3f} ms"
                )
            if span_change > tolerance_ms:
                problems.append(
                    f"the rendition runs {span_change:.3f} ms longer or shorter than the "
                    f"source, and half a frame is {tolerance_ms:.3f} ms"
                )

    return (
        not problems,
        problems,
        {"source": src, "rendition": ren, "tolerance_ms": tolerance_ms},
    )


def _load_plan(layout: TitleLayout, preset: str) -> HidePlan:
    path = layout.plan_path(preset)
    if not path.exists():
        raise PipelineError(f"no hide plan for preset {preset} at {path}")
    return HidePlan.from_dict(json.loads(path.read_text()))


def verify_title(
    layout: TitleLayout,
    *,
    source: str | Path,
    presets: Sequence[str],
    adapter: FlashmapAdapter,
    pub_key: str | Path | None,
    diag_in: float | None = None,
    distance_ft: float | None = None,
    calm_margin_ms: float = DEFAULT_CALM_MARGIN_MS,
    rerender_cover_model: bool = True,
) -> VerifyReport:
    source = Path(source)
    report = VerifyReport(
        sha256=layout.sha256,
        source_path=str(source),
        presets=list(presets),
        started_at=time.time(),
    )

    # 1. The source is the file this title was built from.
    if not source.exists():
        report.add("source_present", False, f"source file is missing: {source}")
        report.finished_at = time.time()
        return report
    actual_sha = sha256_file(source)
    report.add(
        "source_hash",
        actual_sha == layout.sha256,
        f"source hashes to {actual_sha}, title is filed under {layout.sha256}",
        actual=actual_sha,
        expected=layout.sha256,
    )

    probe_data = json.loads(layout.probe_path.read_text())
    probe = VideoProbe.from_dict(probe_data)

    for preset in presets:
        prefix = f"[{preset}] "

        # The map has to parse. An unreadable map is a failure, not an empty
        # list of segments.
        try:
            source_map = load_map(layout.map_path(preset))
        except MapFormatError as exc:
            report.add(f"map_readable:{preset}", False, f"{prefix}{exc}")
            continue
        report.add(f"map_readable:{preset}", True, f"{prefix}map parsed")

        # 1b. The map is bound to this file.
        bound = source_map.source_sha256 == layout.sha256
        report.add(
            f"map_hash:{preset}",
            bound,
            f"{prefix}map says source {source_map.source_sha256}, "
            f"title is {layout.sha256}",
            map_sha=source_map.source_sha256,
        )

        # 2. The signature.
        if pub_key is None:
            report.add(
                f"map_signature:{preset}",
                False,
                f"{prefix}no public key was given, so the map signature could "
                "not be checked. A title cannot publish on an unchecked map.",
            )
        else:
            result = adapter.verify(layout.map_path(preset), source, pub_key=pub_key)
            report.add(
                f"map_signature:{preset}",
                result.ok,
                f"{prefix}flashmap verify exited {result.returncode}: "
                f"{(result.stderr or result.stdout).strip()[-400:]}",
                returncode=result.returncode,
            )

        # 6a. The stored plan is the plan this map produces.
        try:
            plan = _load_plan(layout, preset)
        except PipelineError as exc:
            report.add(f"plan_present:{preset}", False, f"{prefix}{exc}")
            continue
        expected = build_cover_intervals(
            source_map.segments,
            guard_band_ms=plan.guard_band_ms,
            min_cover_ms=plan.min_cover_ms,
            duration_ms=plan.duration_ms,
        )
        expected_pairs = [(i.start_ms, i.end_ms, i.reason) for i in expected]
        stored_pairs = [(i.start_ms, i.end_ms, i.reason) for i in plan.intervals]
        report.add(
            f"plan_matches_map:{preset}",
            expected_pairs == stored_pairs,
            f"{prefix}hide plan has {len(stored_pairs)} intervals, the map "
            f"produces {len(expected_pairs)}",
            stored=len(stored_pairs),
            expected=len(expected_pairs),
        )

        # Red segments are never dimmed.
        red_dimmed = [
            (i.start_ms, i.end_ms) for i in plan.dim_intervals() if i.reason == "red"
        ]
        report.add(
            f"red_always_opaque:{preset}",
            not red_dimmed,
            f"{prefix}{len(red_dimmed)} red interval(s) were marked dim",
            red_dimmed=red_dimmed,
        )

        # 3. The kid safe rendition has no violations left.
        safe_master = layout.safe_master(preset)
        if not safe_master.exists():
            report.add(
                f"safe_rendition_present:{preset}",
                False,
                f"{prefix}no safe rendition at {safe_master}",
            )
        else:
            out_map = layout.verify_map_path(preset, "safe")
            try:
                safe_map = adapter.analyze(
                    safe_master,
                    profile=preset,
                    out_path=out_map,
                    diag_in=diag_in,
                    distance_ft=distance_ft,
                    picture_from=layout.map_path(preset),
                )
                report.add(
                    f"safe_rendition_clean:{preset}",
                    safe_map.is_clean,
                    f"{prefix}flashmap found {safe_map.violation_count} violation(s) "
                    f"in the kid safe rendition",
                    violations=safe_map.violation_count,
                )
                matched, problems, data = compare_rendition_to_source(source_map, safe_map)
                report.add(
                    f"rendition_matches_source:{preset}",
                    matched,
                    f"{prefix}"
                    + (
                        "the rendition has the source's picture rectangle and frame timing"
                        if matched
                        else "; ".join(problems)
                    ),
                    **data,
                )
            except PipelineError as exc:
                report.add(
                    f"safe_rendition_clean:{preset}",
                    False,
                    f"{prefix}could not analyze the safe rendition: {exc}",
                )
                report.add(
                    f"rendition_matches_source:{preset}",
                    False,
                    f"{prefix}the rendition could not be measured against the source: {exc}",
                )

            # 6b. The rendition really shows the still across covered spans.
            sampled = plan.intervals[:COVER_SAMPLE_LIMIT]
            still = layout.still_path
            if sampled and still.exists():
                worst = None
                worst_at = None
                for interval in sampled:
                    midpoint_s = (interval.start_ms + interval.end_ms) / 2000.0
                    score = cover_psnr(safe_master, still, time_s=midpoint_s)
                    if worst is None or score < worst:
                        worst = score
                        worst_at = midpoint_s
                report.add(
                    f"cover_actually_drawn:{preset}",
                    worst is not None and worst >= COVER_PSNR_MIN_DB,
                    f"{prefix}worst covered span matched the cover still at "
                    f"{worst} dB (need {COVER_PSNR_MIN_DB}) at {worst_at} s",
                    worst_db=None if worst == float("inf") else worst,
                    worst_at_s=worst_at,
                )

        # 4. The on-device cover schedule over the original video.
        cover_model = layout.cover_model_path(preset)
        try:
            if rerender_cover_model or not cover_model.exists():
                render_cover_model(
                    source, plan=plan, out_path=cover_model, probe=probe
                )
            out_map = layout.verify_map_path(preset, "cover_model")
            model_map = adapter.analyze(
                cover_model,
                profile=preset,
                out_path=out_map,
                diag_in=diag_in,
                distance_ft=distance_ft,
                picture_from=layout.map_path(preset),
            )
            hint = ""
            if not model_map.is_clean and plan.allow_dim and plan.dim_intervals():
                # A dim cover keeps a tenth of the light, so a flash that ran
                # the whole luminance range still changes by 0.1, which is
                # exactly the WCAG general flash threshold. Content like that
                # needs an opaque cover, not a dim one.
                hint = (
                    ". This plan allows a dim cover. Re-run ingest with --no-dim "
                    "so every cover is opaque, then verify again."
                )
            report.add(
                f"cover_model_clean:{preset}",
                model_map.is_clean,
                f"{prefix}the cover schedule over the original video left "
                f"{model_map.violation_count} violation(s){hint}",
                violations=model_map.violation_count,
                dim_intervals=len(plan.dim_intervals()),
            )
        except PipelineError as exc:
            report.add(
                f"cover_model_clean:{preset}",
                False,
                f"{prefix}could not model the on-device cover: {exc}",
            )

        # 5. Trickplay frames and posters come from calm moments.
        bif_manifest = layout.bif_manifest(preset)
        if not bif_manifest.exists():
            report.add(
                f"bif_calm:{preset}", False, f"{prefix}no trickplay manifest at {bif_manifest}"
            )
        else:
            manifest = json.loads(bif_manifest.read_text())
            frames = manifest.get("frames", [])
            # A title built with a weaker calm rule than the one publishing it
            # must not slip through on the strength of its own settings.
            built_with = float(manifest.get("calm_margin_ms", -1))
            report.add(
                f"calm_margin_policy:{preset}",
                built_with >= calm_margin_ms,
                f"{prefix}trickplay was built with a {built_with:.0f} ms calm "
                f"margin, publishing needs at least {calm_margin_ms:.0f} ms",
                built_with=built_with,
                required=calm_margin_ms,
            )
            bad = [
                frame
                for frame in frames
                if not is_calm(
                    plan.intervals, float(frame["source_ms"]), margin_ms=calm_margin_ms
                )
            ]
            report.add(
                f"bif_calm:{preset}",
                not bad and bool(frames),
                f"{prefix}{len(bad)} of {len(frames)} trickplay frame(s) came "
                f"from a flagged moment",
                bad_times=[frame["source_ms"] for frame in bad][:20],
                frame_count=len(frames),
            )
            from_safe = manifest.get("from") == "safe_rendition"
            report.add(
                f"bif_from_safe_rendition:{preset}",
                from_safe,
                f"{prefix}trickplay manifest says the frames came from "
                f"{manifest.get('from')!r}",
            )

        posters_manifest = layout.posters_manifest(preset)
        if not posters_manifest.exists():
            report.add(
                f"posters_calm:{preset}",
                False,
                f"{prefix}no poster manifest at {posters_manifest}",
            )
        else:
            manifest = json.loads(posters_manifest.read_text())
            posters = manifest.get("posters", [])
            bad = [
                poster
                for poster in posters
                if not is_calm(
                    plan.intervals, float(poster["time_ms"]), margin_ms=calm_margin_ms
                )
            ]
            missing = [
                poster["path"] for poster in posters if not Path(poster["path"]).exists()
            ]
            report.add(
                f"posters_calm:{preset}",
                not bad and bool(posters) and not missing,
                f"{prefix}{len(bad)} of {len(posters)} poster(s) came from a "
                f"flagged moment, {len(missing)} missing on disk",
                bad_times=[poster["time_ms"] for poster in bad][:20],
                missing=missing[:20],
            )

    # The cover still is shared across presets, so it is checked against every
    # preset's plan.
    if layout.still_manifest_path.exists():
        still_info = json.loads(layout.still_manifest_path.read_text())
        still_ms = float(still_info.get("time_ms", -1))
        bad_presets = []
        for preset in presets:
            try:
                plan = _load_plan(layout, preset)
            except PipelineError:
                continue
            if not is_calm(plan.intervals, still_ms, margin_ms=calm_margin_ms):
                bad_presets.append(preset)
        report.add(
            "cover_still_calm",
            not bad_presets,
            f"the cover still at {still_ms:.0f} ms is inside a flagged span for "
            f"{', '.join(bad_presets) if bad_presets else 'no preset'}",
            still_ms=still_ms,
            bad_presets=bad_presets,
        )
    else:
        report.add(
            "cover_still_calm", False, "no cover still manifest, so its moment is unknown"
        )

    report.finished_at = time.time()
    return report


def write_report(layout: TitleLayout, report: VerifyReport) -> Path:
    layout.verify_dir.mkdir(parents=True, exist_ok=True)
    layout.verify_report_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True)
    )
    return layout.verify_report_path


def apply_to_catalog(layout: TitleLayout, report: VerifyReport) -> None:
    """Record the verdict where kid mode reads it."""
    if not layout.entry_path.exists():
        return
    entry = read_entry(layout.entry_path)
    entry.verified = report.passed
    entry.status = STATUS_VERIFIED if report.passed else STATUS_FAILED
    entry.verify_report = str(layout.verify_report_path)
    entry.notes["failed_checks"] = [check.name for check in report.failures]
    write_entry(layout.entry_path, entry)
    update_index(layout.index_path, entry)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.verify",
        description="Check a title and block publishing if anything fails.",
    )
    parser.add_argument("--workdir", required=True, help="the ingest work directory")
    parser.add_argument("--sha", required=True, help="the source SHA-256 of the title")
    parser.add_argument(
        "--source", help="path to the original video (default: the path ingest recorded)"
    )
    parser.add_argument("--pub", help="public key the map signature is checked against")
    parser.add_argument(
        "--presets", help="comma separated preset list (default: the presets on disk)"
    )
    parser.add_argument("--diag", type=float, help="television diagonal in inches")
    parser.add_argument("--distance-ft", type=float, help="seat distance in feet")
    parser.add_argument(
        "--no-rerender",
        action="store_true",
        help="reuse the cover model render from a previous run if it is there",
    )
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    layout = TitleLayout(args.workdir, args.sha)
    if not layout.root.exists():
        print(f"VERIFY FAILED: no title directory at {layout.root}", file=sys.stderr)
        return 2

    ledger_source = None
    state_path = layout.root / "state.json"
    if state_path.exists():
        try:
            ledger_source = (json.loads(state_path.read_text()).get("source") or {}).get(
                "path"
            )
        except json.JSONDecodeError:
            ledger_source = None
    source = args.source or ledger_source
    if not source:
        print(
            "VERIFY FAILED: no source path given and none recorded by ingest",
            file=sys.stderr,
        )
        return 2

    if args.presets:
        presets = [p.strip() for p in args.presets.split(",") if p.strip()]
    else:
        presets = sorted(p.stem for p in (layout.root / "maps").glob("*.json"))
    if not presets:
        print(f"VERIFY FAILED: no maps in {layout.root / 'maps'}", file=sys.stderr)
        return 2

    adapter = FlashmapAdapter()
    try:
        report = verify_title(
            layout,
            source=source,
            presets=presets,
            adapter=adapter,
            pub_key=args.pub,
            diag_in=args.diag,
            distance_ft=args.distance_ft,
            rerender_cover_model=not args.no_rerender,
        )
    except PipelineError as exc:
        print(f"VERIFY FAILED: {exc}", file=sys.stderr)
        return 1

    write_report(layout, report)
    apply_to_catalog(layout, report)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    stream = sys.stdout if report.passed else sys.stderr
    print(report.summary(), file=stream)
    return 0 if report.passed else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
