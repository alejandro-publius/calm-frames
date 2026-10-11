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

A pass is not one thing, and `VerifyReport.outcome` says which kind it was.
A title whose plan has intervals passes only when the check that measures the
cover against the cover still ran for that preset and passed, which is
`cover_proof:{preset}`. A title with no flagged segment has nothing to cover,
so it gets `no flagged segments` rather than the same word as a title whose
cover was measured. `--pool-summary` counts a whole work directory that way.

Exit codes: 0 pass, 1 fail, 2 the request itself was wrong.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence

from . import PipelineError, ffmpegtool
from .catalog import (
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_VERIFIED,
    CatalogEntry,
    read_entry,
    update_index,
    write_entry,
)
from .flashmap_adapter import PATTERN, FlashmapAdapter, FlashMapDoc, MapFormatError, load_map
from .hashing import sha256_file
from .hideplan import (
    APP_PLAYBACK_MAPS,
    APP_PLAYBACK_RECIPE,
    DEFAULT_CALM_MARGIN_MS,
    DEFAULT_GUARD_BAND_MS,
    CoverInterval,
    HidePlan,
    build_app_playback_plan,
    build_cover_intervals,
    is_calm,
    may_be_sampled,
    union_intervals,
)
from .layout import TitleLayout
from .posters import STILL_FROM_NEUTRAL_CARD, STILL_FROM_SOURCE
from .probe import VideoProbe
from .render import cover_psnr, make_neutral_still, render_cover_model, still_is_flat
from .sceneholds import SceneHold, verify_scene_assets

# A covered span must match the cover still at least this closely, in dB.
# Identical frames give inf. A span that still shows the film scores far lower.
COVER_PSNR_MIN_DB = 30.0
# How many covered spans to sample for that check. Sampling keeps verify
# affordable on a feature length title.
COVER_SAMPLE_LIMIT = 6

# How far a rendition may run longer or shorter than the source and still be
# showing the same pictures at the same moments: half a frame. Less than that
# and nothing has moved by a whole frame anywhere.
TIMING_TOLERANCE_FRAMES = 0.5

# How far a rendition's timeline may start from the source's.
#
# Not the guard band, even though the guard band is what would absorb it. That
# band is shared. The app schedules live covers from the signed map, and the
# map's intervals are on the SOURCE timeline, so a rendition that starts late
# draws every live cover that much late and spends the same 500 ms the
# scheduler needs. The software lead time run measured a cover going on 86 ms
# AFTER its marker, because the JavaScript thread was unavailable for about
# 335 ms (results/gate1_software_vvd.json, and docs/GATES.md on why that is the
# thread and not the scheduler). Handing a media offset the rest of that band
# would leave nothing for the pause nobody has measured on hardware yet.
#
# So the offset is given a tolerance of its own, and the measured offset is
# recorded per preset in the verify report and in the catalog entry, so a player
# can subtract it and stop it costing the band anything at all.
#
# The worst offset in this pool is 67 ms, from a source whose first frame sits
# two frames in. 150 ms is that with room to spare and still leaves the band
# most of its headroom. An engineering tolerance, not a number from a spec, and
# docs/SPEC_SOURCES.md is where spec numbers live.
START_OFFSET_LIMIT_MS = 150.0

# What a report proves, in four words that never stand in for one another.
#
# Until 2026-09-17 a title with no flagged segment collected the same "verified" as a
# title whose cover had been measured on the rendition, because the check that measures
# it only ran when there was an interval to sample. Fourteen of the twenty-one verified
# titles were in that state. Finding nothing over the thresholds is a real outcome and
# for gentle cloud and sunset footage it is the right one. It is not evidence that any
# cover works, so it gets a name of its own. docs/DECISIONS.md has the reasoning.
OUTCOME_NO_FLAGGED_SEGMENTS = "no flagged segments"
OUTCOME_COVER_PROVEN_DRAWN = "cover proven drawn"
# A report that passed while a flagged preset had no passing cover proof. Verify now
# refuses that, so only a report written before this rule can carry it. It is kept
# because a report from then is still read, and folding it into either neighbour would
# be the friendlier answer rather than the true one.
OUTCOME_COVER_NOT_PROVEN = "cover not proven"
OUTCOME_FAILED = "failed"
OUTCOMES = (
    OUTCOME_NO_FLAGGED_SEGMENTS,
    OUTCOME_COVER_PROVEN_DRAWN,
    OUTCOME_COVER_NOT_PROVEN,
    OUTCOME_FAILED,
)


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

    @property
    def flagged_presets(self) -> list[str]:
        """The presets whose hide plan has at least one interval to cover.

        Read from the checks rather than from the plans on disk, so a report written
        months ago answers the same question the same way.
        """
        return [
            check.name.split(":", 1)[1]
            for check in self.checks
            if check.name.startswith("plan_matches_map:")
            and float(check.data.get("stored") or 0) > 0
        ]

    @property
    def outcome(self) -> str:
        """What this report proves, as one of `OUTCOMES`.

        A pass is not one thing. A title with no flagged segment was looked at and
        nothing was over the thresholds, which is worth saying out loud and is not
        worth anything as evidence that a cover works. A title with flagged segments
        only counts as proven when the check that measures the cover against the cover
        still ran for every preset that had something to cover, and passed.
        """
        if not self.passed:
            return OUTCOME_FAILED
        flagged = self.flagged_presets
        if not flagged:
            return OUTCOME_NO_FLAGGED_SEGMENTS
        drawn = {
            check.name.split(":", 1)[1]: check.passed
            for check in self.checks
            if check.name.startswith("cover_actually_drawn:")
        }
        if all(drawn.get(preset) for preset in flagged):
            return OUTCOME_COVER_PROVEN_DRAWN
        return OUTCOME_COVER_NOT_PROVEN

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
            "outcome": self.outcome,
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
            return (
                f"VERIFY PASSED for {self.sha256[:12]} ({len(self.checks)} checks, "
                f"{self.outcome})"
            )
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
        numbers = [value for value in values if isinstance(value, (int, float))]
        if len(numbers) == len(values):
            rect = tuple(int(value) for value in numbers)

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
    guard_band_ms: float = DEFAULT_GUARD_BAND_MS,
) -> tuple[bool, list[str], dict]:
    """Is the rendition the same picture, in the same place, at the same times?

    A title is always analyzed from the source file, never from a re-encode, so the map that
    ships describes the source. The rendition is the file that actually plays, and the hide
    plan built from the source only lines up with it if the two agree on where the picture is
    and when each frame arrives. So: the same coded frame, the same picture rectangle, the
    same number of frames, a span that has not stretched by as much as half a frame, and a
    start that has not moved by more than `START_OFFSET_LIMIT_MS`.

    The two bars differ on purpose. A re-encode routinely renumbers the first presentation
    timestamp to zero while leaving every picture where it was, and the source files in this
    pool start anywhere from 3 to 67 ms in, so a bar of half a frame would refuse most of
    them. It is not tied to the guard band either: the band is shared with scheduler jitter,
    and a cover has already been measured going on 86 ms after its marker. See
    `START_OFFSET_LIMIT_MS`. Whatever the offset turns out to be, it is reported so a player
    can subtract it rather than spend the band on it.

    Returns (passed, problems, data). Anything that cannot be read is a problem, never a pass.
    """
    src = _geometry(source_map)
    ren = _geometry(rendition_map)
    problems: list[str] = []
    # What a player needs in order to line the map up with the rendition itself.
    measured: dict = {"start_offset_ms": None}

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
            measured["start_offset_ms"] = round(
                ren["first_pts_ms"] - src["first_pts_ms"], 3
            )
            src_span = src["last_pts_ms"] - src["first_pts_ms"]
            ren_span = ren["last_pts_ms"] - ren["first_pts_ms"]
            span_change = abs(ren_span - src_span)
            # A household may only ever make things stricter, so a guard band narrower than
            # the tolerance narrows the tolerance with it.
            start_limit = min(START_OFFSET_LIMIT_MS, guard_band_ms)
            if start_shift > start_limit:
                problems.append(
                    f"the rendition starts {start_shift:.3f} ms away from the source, and "
                    f"{start_limit:.0f} ms is as far as that may go. The guard band cannot "
                    "be asked to absorb it: it is already holding the scheduler's own "
                    "lateness"
                )
            if span_change > tolerance_ms:
                problems.append(
                    f"the rendition runs {span_change:.3f} ms longer or shorter than the "
                    f"source, and half a frame is {tolerance_ms:.3f} ms"
                )

    return (
        not problems,
        problems,
        {
            "source": src,
            "rendition": ren,
            "tolerance_ms": tolerance_ms,
            "guard_band_ms": guard_band_ms,
            "start_offset_limit_ms": min(START_OFFSET_LIMIT_MS, guard_band_ms),
            **measured,
        },
    )


def _load_plan(layout: TitleLayout, preset: str) -> HidePlan:
    path = layout.plan_path(preset)
    if not path.exists():
        raise PipelineError(f"no hide plan for preset {preset} at {path}")
    return HidePlan.from_dict(json.loads(path.read_text()))


COVER_SAMPLES_PER_INTERVAL = 3


def _cover_sample_times(interval: CoverInterval, probe: VideoProbe) -> list[float]:
    """Where a covered span is measured: its first frame, its middle, its last frame.

    One midpoint used to be the whole proof. A cover that is drawn at the
    middle of a span and gone before its end, or late to its start, passed it.
    The first and last samples sit one frame inside the span, because the
    boundary frame itself belongs to whichever side the encoder's timestamps
    put it on, and the span's edges are what the analyzer's own entry and exit
    checks cover. A span shorter than three frames is measured at its middle.
    """
    start_s = interval.start_ms / 1000.0
    end_s = interval.end_ms / 1000.0
    middle_s = (start_s + end_s) / 2.0
    frame_s = probe.frame_interval_median_s or (
        1.0 / probe.avg_frame_rate if probe.avg_frame_rate else 1.0 / 30.0
    )
    if end_s - start_s < 3 * frame_s:
        return [middle_s]
    return [start_s + frame_s, middle_s, end_s - frame_s]


def _scene_cover_proof(
    video: Path, plan: HidePlan, images: Sequence[SceneHold], probe: VideoProbe
) -> list[float]:
    """Measure every described asset and a bounded sample of black fallbacks.

    Full-output analysis separately checks all entry and exit transitions.
    This proof makes a missing or wrong image visible even on calm source
    footage where the analyzer would report no violations either way. Each
    span is measured at its first frame, its middle and its last frame.
    """
    by_interval = {(h.start_ms, h.end_ms): h for h in images}
    scores = []
    fallbacks = 0
    with TemporaryDirectory(prefix="scene_cover_proof_") as scratch:
        black = Path(scratch) / "black.png"
        for interval in plan.intervals:
            image = by_interval.get((interval.start_ms, interval.end_ms))
            if image is not None:
                still = image.path
            else:
                if fallbacks >= COVER_SAMPLE_LIMIT:
                    continue
                fallbacks += 1
                if not black.exists():
                    make_neutral_still(black, width=probe.width, height=probe.height, rgb=(0, 0, 0))
                still = black
            for time_s in _cover_sample_times(interval, probe):
                scores.append(cover_psnr(video, still, time_s=time_s))
    return scores


def _scene_output_pattern_check(
    layout: TitleLayout, *, preset: str, kind: str, video: Path,
    plan: HidePlan, adapter: FlashmapAdapter,
) -> tuple[bool, int]:
    """Check images as presented after scaling and encoding, not just JPEGs.

    This additional check is about patterns introduced or held by a new cover.
    It does not turn a WCAG source verdict into a broadcast source verdict.
    Findings outside covered intervals stay outside this added check.
    """
    checked = adapter.analyze(
        video, profile="broadcast",
        out_path=layout.verify_map_path(preset, f"scene_patterns_{kind}"),
        picture_from=layout.map_path(preset),
    )
    # MPEG-TS changes the time origin. Cover intervals are on the MP4 player's
    # timeline, so normalize those transport pattern timestamps to that origin.
    shift = 0.0
    if kind == "hls":
        master = load_map(layout.verify_map_path(preset, "safe"))
        shift = _geometry(checked)["first_pts_ms"] - _geometry(master)["first_pts_ms"]
    patterns = [
        segment for segment in checked.segments if segment.reason == PATTERN
        and any(segment.start_ms - shift < interval.end_ms
                and segment.end_ms - shift > interval.start_ms for interval in plan.intervals)
    ]
    return not patterns, len(patterns)


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
    playback_compatible: bool | None = None,
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
    entry = read_entry(layout.entry_path) if layout.entry_path.exists() else None
    recorded_recipe = entry.notes.get("playback_recipe") if entry is not None else None
    if playback_compatible is None:
        playback_compatible = recorded_recipe == APP_PLAYBACK_RECIPE
    if recorded_recipe not in (None, APP_PLAYBACK_RECIPE):
        report.add("playback_recipe", False, "the preparation names an unknown playback recipe")
    if playback_compatible:
        required = {name for preset in presets for name in APP_PLAYBACK_MAPS.get(preset, ())}
        report.add("playback_recipe_profiles", required.issubset(presets),
                   "every map used by the app recipe must receive independent signature and source checks")
        if entry is not None:
            room = entry.notes.get("analysis_room", {})
            diag_in = diag_in if diag_in is not None else room.get("diag_in")
            distance_ft = distance_ft if distance_ft is not None else room.get("distance_ft")

    # No preset means no map was looked at, and a report that reached the end without
    # looking at one would otherwise pass on the two checks that do not need a preset.
    if not presets:
        report.add(
            "presets_checked",
            False,
            "no preset was given, so no map, plan or cover was checked",
        )

    # An image must be calm under every requested preset, even when this
    # preset alone would permit the preceding frame.
    all_plans = []
    union_error = None
    for name in presets:
        try:
            all_plans.append(_load_plan(layout, name))
        except (PipelineError, ValueError, KeyError, TypeError) as exc:
            union_error = str(exc)
    all_intervals = union_intervals(all_plans)

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
        try:
            if playback_compatible:
                canonical = build_app_playback_plan(
                    {name: load_map(layout.map_path(name)) for name in APP_PLAYBACK_MAPS[preset]},
                    source_sha256=layout.sha256, duration_ms=probe.duration_ms, preset=preset,
                )
                expected = canonical.intervals
                recipe_matches = (
                    plan.recipe == APP_PLAYBACK_RECIPE and plan.profile == preset
                    and plan.source_sha256 == layout.sha256
                    and plan.duration_ms == canonical.duration_ms
                    and plan.guard_band_ms == canonical.guard_band_ms
                    and plan.min_cover_ms == canonical.min_cover_ms
                    and plan.allow_dim is False
                )
            else:
                expected = build_cover_intervals(
                    source_map.segments, guard_band_ms=plan.guard_band_ms,
                    min_cover_ms=plan.min_cover_ms, duration_ms=plan.duration_ms,
                )
                recipe_matches = plan.recipe is None
        except (PipelineError, OSError, ValueError, TypeError, KeyError) as exc:
            report.add(f"plan_matches_map:{preset}", False, f"{prefix}{exc}")
            continue
        expected_pairs = [(i.start_ms, i.end_ms, i.reason) for i in expected]
        stored_pairs = [(i.start_ms, i.end_ms, i.reason) for i in plan.intervals]
        report.add(
            f"plan_matches_map:{preset}",
            recipe_matches and expected_pairs == stored_pairs,
            f"{prefix}hide plan has {len(stored_pairs)} intervals, the map "
            f"produces {len(expected_pairs)}",
            stored=len(stored_pairs),
            expected=len(expected_pairs),
            recipe=plan.recipe,
        )

        scene_images: list[SceneHold] | None = None
        if "scene_holds" in source_map.raw:
            try:
                if union_error:
                    raise PipelineError(f"another preset's plan cannot be read: {union_error}")
                scene_images = verify_scene_assets(
                    layout, preset=preset, source_document=source_map.raw,
                    source=source, intervals=plan.intervals, union=all_intervals,
                    probe=probe, margin_ms=calm_margin_ms, adapter=adapter,
                )
                report.add(f"scene_assets:{preset}", True,
                           f"{prefix}{len(scene_images)} signed images match checked local assets and provenance")
            except (PipelineError, OSError, ValueError, TypeError, KeyError) as exc:
                report.add(f"scene_assets:{preset}", False, f"{prefix}{exc}")
                # Invalid image data is not a legacy plan. Never quietly model
                # it with the old global still or a dim cover instead.
                scene_images = []

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
                matched, problems, data = compare_rendition_to_source(
                    source_map, safe_map, guard_band_ms=plan.guard_band_ms
                )
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
            if scene_images is not None and plan.intervals:
                try:
                    scores = _scene_cover_proof(safe_master, plan, scene_images, probe)
                    report.add(
                        f"cover_actually_drawn:{preset}",
                        bool(scores) and min(scores) >= COVER_PSNR_MIN_DB,
                        f"{prefix}each described scene hold and sampled black fallback match the "
                        "rendition at the first frame, the middle and the last frame of the span",
                        samples=len(scores), worst_db=min(scores) if min(scores) != float("inf") else None,
                        samples_per_interval=COVER_SAMPLES_PER_INTERVAL,
                        ffmpeg=ffmpegtool.ffmpeg_version(),
                    )
                except (PipelineError, OSError) as exc:
                    report.add(f"cover_actually_drawn:{preset}", False, f"{prefix}{exc}")
            elif sampled and still.exists():
                worst = None
                worst_at = None
                for interval in sampled:
                    for time_s in _cover_sample_times(interval, probe):
                        score = cover_psnr(safe_master, still, time_s=time_s)
                        if worst is None or score < worst:
                            worst = score
                            worst_at = time_s
                report.add(
                    f"cover_actually_drawn:{preset}",
                    worst is not None and worst >= COVER_PSNR_MIN_DB,
                    f"{prefix}worst sample across the first frame, middle and last frame of "
                    f"each covered span matched the cover still at {worst} dB "
                    f"(need {COVER_PSNR_MIN_DB}) at {worst_at} s",
                    worst_db=None if worst == float("inf") else worst,
                    worst_at_s=worst_at,
                    samples_per_interval=COVER_SAMPLES_PER_INTERVAL,
                    ffmpeg=ffmpegtool.ffmpeg_version(),
                )

        # 6c. Either there was nothing to cover, or the cover was proven drawn.
        #
        # The check above sits behind `if sampled and still.exists()`, so a missing
        # cover still, an empty sample or a plan with no interval used to take it out
        # of the report without taking the title out of kid mode. This is the line that
        # says a preset with intervals may not pass on a check that never ran. It is
        # deliberately asked after the fact, of the report, rather than inside the
        # branch: a check that is skipped cannot notice its own absence.
        drawn = next(
            (c for c in report.checks if c.name == f"cover_actually_drawn:{preset}"),
            None,
        )
        proven = drawn is not None and drawn.passed
        if not plan.intervals:
            detail = (
                f"{prefix}the hide plan has no interval, so there is nothing to cover "
                f"and nothing about covering is shown: {OUTCOME_NO_FLAGGED_SEGMENTS}"
            )
        elif proven:
            detail = (
                f"{prefix}{len(plan.intervals)} interval(s) to cover, and the cover was "
                "measured on the rendition"
            )
        elif drawn is None:
            detail = (
                f"{prefix}{len(plan.intervals)} interval(s) to cover and no cover proof "
                "at all: cover_actually_drawn never ran, which happens when the cover "
                "still is missing or nothing was sampled"
            )
        else:
            detail = (
                f"{prefix}{len(plan.intervals)} interval(s) to cover and the cover proof "
                "did not pass"
            )
        report.add(
            f"cover_proof:{preset}",
            not plan.intervals or proven,
            detail,
            intervals=len(plan.intervals),
            proof_ran=drawn is not None,
            proof_passed=proven,
        )

        # 4. The on-device cover schedule over the original video.
        cover_model = layout.cover_model_path(preset)
        try:
            if rerender_cover_model or not cover_model.exists():
                render_cover_model(
                    source, plan=plan, out_path=cover_model, probe=probe,
                    scene_holds=scene_images,
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
            if scene_images is None and not model_map.is_clean and plan.allow_dim and plan.dim_intervals():
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
                dim_intervals=len(plan.dim_intervals()) if scene_images is None else 0,
            )
            if scene_images is not None:
                scores = _scene_cover_proof(cover_model, plan, scene_images, probe)
                report.add(f"scene_model_drawn:{preset}",
                           not plan.intervals or bool(scores) and min(scores) >= COVER_PSNR_MIN_DB,
                           f"{prefix}the live opaque cover model uses the same interval images and black fallback")
        except PipelineError as exc:
            report.add(
                f"cover_model_clean:{preset}",
                False,
                f"{prefix}could not model the on-device cover: {exc}",
            )

        if scene_images is not None or playback_compatible:
            # The transport files are the delivered output. Analyze them too,
            # rather than assuming a clean intermediate MP4 proves delivery.
            try:
                hls_map = adapter.analyze(
                    layout.master_playlist(preset), profile=preset,
                    out_path=layout.verify_map_path(preset, "hls"),
                    diag_in=diag_in, distance_ft=distance_ft,
                    picture_from=layout.map_path(preset),
                )
                report.add(f"hls_rendition_clean:{preset}", hls_map.is_clean,
                           f"{prefix}the complete HLS output has {hls_map.violation_count} violations including boundaries")
                master_map = load_map(layout.verify_map_path(preset, "safe"))
                master_geometry, hls_geometry = _geometry(master_map), _geometry(hls_map)
                # MPEG-TS changes the PTS origin; its relative picture timeline
                # must still match the checked MP4, frame for frame in length.
                relative_hls = dict(hls_map.raw)
                relative_hls["source"] = dict(relative_hls.get("source", {}))
                shift = hls_geometry["first_pts_ms"] - master_geometry["first_pts_ms"]
                for field in ("first_pts_ms", "last_pts_ms"):
                    relative_hls["source"][field] -= shift
                normalized = FlashMapDoc(
                    hls_map.version, hls_map.source_sha256, hls_map.profile,
                    hls_map.segments, raw=relative_hls,
                )
                matched, problems, data = compare_rendition_to_source(
                    master_map, normalized, guard_band_ms=plan.guard_band_ms
                )
                report.add(f"hls_timing_matches_master:{preset}", matched,
                           f"{prefix}HLS relative frame timing matches the checked MP4" if matched else "; ".join(problems),
                           transport_pts_shift_ms=shift, **data)
                if plan.intervals and scene_images is not None:
                    scores = _scene_cover_proof(layout.master_playlist(preset), plan, scene_images, probe)
                    report.add(f"scene_hls_drawn:{preset}", bool(scores) and min(scores) >= COVER_PSNR_MIN_DB,
                               f"{prefix}the delivered HLS uses the checked interval images")
            except (PipelineError, OSError, ValueError, TypeError, KeyError) as exc:
                report.add(f"hls_rendition_clean:{preset}", False, f"{prefix}could not verify delivered HLS: {exc}")

        if scene_images is not None:
            for kind, output in (("safe", safe_master), ("model", cover_model),
                                 ("hls", layout.master_playlist(preset))):
                try:
                    clean, count = _scene_output_pattern_check(
                        layout, preset=preset, kind=kind, video=output,
                        plan=plan, adapter=adapter,
                    )
                    report.add(f"scene_output_patterns:{kind}:{preset}", clean,
                               f"{prefix}{count} full-size pattern finding(s) intersect a covered interval in {kind}",
                               intersecting_patterns=count)
                except (PipelineError, OSError, ValueError, TypeError, KeyError) as exc:
                    report.add(f"scene_output_patterns:{kind}:{preset}", False,
                               f"{prefix}could not check the presented image patterns: {exc}")

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
            # A frame may come from a calm moment, or from one where the cover is down the
            # whole way, because the rendition shows the cover still there and not the film.
            # A title that flashes end to end only has the second kind.
            bad = [
                frame
                for frame in frames
                if not may_be_sampled(
                    plan.intervals,
                    float(frame["source_ms"]),
                    plan.duration_ms,
                    margin_ms=calm_margin_ms,
                )
            ]
            report.add(
                f"bif_calm:{preset}",
                not bad and bool(frames),
                f"{prefix}{len(bad)} of {len(frames)} trickplay frame(s) came "
                f"from a moment that is neither calm nor under the cover",
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
                if not may_be_sampled(
                    plan.intervals,
                    float(poster["time_ms"]),
                    plan.duration_ms,
                    margin_ms=calm_margin_ms,
                )
            ]
            missing = [
                poster["path"] for poster in posters if not Path(poster["path"]).exists()
            ]
            report.add(
                f"posters_calm:{preset}",
                not bad and bool(posters) and not missing,
                f"{prefix}{len(bad)} of {len(posters)} poster(s) came from a moment "
                f"that is neither calm nor under the cover, {len(missing)} missing on disk",
                bad_times=[poster["time_ms"] for poster in bad][:20],
                missing=missing[:20],
            )

    # The cover still is shared across presets, so it is checked against every
    # preset's plan.
    if layout.still_manifest_path.exists():
        still_info = json.loads(layout.still_manifest_path.read_text())
        still_from = str(still_info.get("from", STILL_FROM_SOURCE))
    else:
        still_info, still_from = {}, ""

    if still_from == STILL_FROM_NEUTRAL_CARD:
        # A title that flashes end to end has no frame that may be shown, so the cover is a
        # flat card instead of a refusal. "Flat" is measured here, not believed: a frame of
        # the film is never one colour, so this is what stops a neutral card being a way to
        # smuggle a flagged frame through.
        try:
            flat, flat_detail = still_is_flat(layout.still_path)
        except PipelineError as exc:
            flat, flat_detail = False, {"error": str(exc)}
        report.add(
            "cover_still_calm",
            flat,
            "the cover is a neutral card because every moment in this title is inside a "
            "flagged span"
            + (
                ", and it measures as one flat colour"
                if flat
                else f", but it is not one flat colour: {flat_detail}"
            ),
            still_from=still_from,
            **flat_detail,
        )
    elif still_info and still_info.get("time_ms") is None:
        # A still that says it came out of the film has to say when. Without that there is no
        # way to ask whether the moment was calm, and an unanswerable question is a failure.
        report.add(
            "cover_still_calm",
            False,
            f"the cover still says it came from {still_from!r} but not from when, so "
            "whether that moment was calm cannot be checked",
            still_from=still_from,
        )
    elif still_info:
        still_ms = float(still_info["time_ms"])
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
    # Which kind of pass this was. `status` still decides whether kid mode may list the
    # title, because a title with no flagged segment is safe to play and hiding it would
    # be a worse answer than publishing it. The outcome is what stops the two kinds of
    # pass being counted as one thing.
    entry.notes["verify_outcome"] = report.outcome
    # How far each rendition's timeline sits from the source's, in milliseconds. The map's
    # intervals are on the source timeline, so a player scheduling live covers over the
    # rendition adds this to every one of them. Recorded rather than absorbed: the guard band
    # is already holding the scheduler's own lateness, and there is a measured cover that went
    # on 86 ms after its marker.
    offsets = {
        check.name.split(":", 1)[1]: check.data.get("start_offset_ms")
        for check in report.checks
        if check.name.startswith("rendition_matches_source:")
        and check.data.get("start_offset_ms") is not None
    }
    if offsets:
        entry.notes["rendition_start_offset_ms"] = offsets
    write_entry(layout.entry_path, entry)
    update_index(layout.index_path, entry)


def outcome_for_entry(entry: CatalogEntry) -> str | None:
    """The outcome behind one catalog entry, or None when verify never gave it a verdict.

    The report on disk is read first, because it is the evidence and it can be read
    again. The note verify writes beside it is the fallback for an entry whose report
    has been moved or deleted. A title that has not been through verify has no outcome
    at all, and is counted as not analyzed rather than quietly as one of the passes.
    """
    # `is_file` rather than `exists`, because an entry that never ran verify has no
    # report path at all and Path("") is the working directory, which does exist.
    path = Path(entry.verify_report or "")
    if entry.verify_report and path.is_file():
        try:
            return VerifyReport.from_dict(json.loads(path.read_text())).outcome
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    recorded = entry.notes.get("verify_outcome")
    if isinstance(recorded, str) and recorded in OUTCOMES:
        return recorded
    if entry.status == STATUS_FAILED:
        return OUTCOME_FAILED
    return None


def pool_summary(workdir: str | Path) -> dict:
    """Count every title in a work directory by what verify proved about it.

    The four published counts are `analyzed` and the three it is made of, so a title
    cannot move between them without the total moving too. Everything verify has not
    given a verdict on is counted separately, by name, so the directory count and the
    analyzed count can be told apart instead of one being read as the other.
    """
    titles_dir = Path(workdir) / "titles"
    counts = dict.fromkeys(OUTCOMES, 0)
    not_analyzed = {"pending": 0, "no_entry_json": 0, "no_verdict": 0}
    directories = 0

    children = sorted(titles_dir.iterdir()) if titles_dir.is_dir() else []
    for child in children:
        if not child.is_dir():
            continue
        directories += 1
        entry_path = child / "entry.json"
        if not entry_path.exists():
            not_analyzed["no_entry_json"] += 1
            continue
        try:
            entry = read_entry(entry_path)
        except (json.JSONDecodeError, TypeError, ValueError):
            not_analyzed["no_verdict"] += 1
            continue
        outcome = outcome_for_entry(entry)
        if outcome is None:
            key = "pending" if entry.status == STATUS_PENDING else "no_verdict"
            not_analyzed[key] += 1
            continue
        counts[outcome] += 1

    analyzed = sum(counts.values())
    # Written out rather than summed again, so that an outcome added to OUTCOMES and
    # not published here turns `adds_up` false instead of hiding inside the total. The
    # second half is the invariant that a title cannot fall out of every count.
    published = (
        counts[OUTCOME_NO_FLAGGED_SEGMENTS]
        + counts[OUTCOME_COVER_PROVEN_DRAWN]
        + counts[OUTCOME_COVER_NOT_PROVEN]
        + counts[OUTCOME_FAILED]
    )
    adds_up = analyzed == published and directories == analyzed + sum(
        not_analyzed.values()
    )
    home = Path.home()
    root = Path(workdir).resolve()
    try:
        shown = f"~/{root.relative_to(home)}"
    except ValueError:
        shown = str(root)
    return {
        "generated_on": time.strftime("%Y-%m-%d"),
        "work_directory": shown,
        "title_directories": directories,
        "analyzed": analyzed,
        "no_flagged_segments": counts[OUTCOME_NO_FLAGGED_SEGMENTS],
        "cover_proven_drawn": counts[OUTCOME_COVER_PROVEN_DRAWN],
        "cover_not_proven": counts[OUTCOME_COVER_NOT_PROVEN],
        "failed": counts[OUTCOME_FAILED],
        "not_analyzed": not_analyzed,
        "adds_up": adds_up,
        "statement": (
            "analyzed is no_flagged_segments plus cover_proven_drawn plus "
            "cover_not_proven plus failed. A title counted under no_flagged_segments "
            "passed verify and had no segment over the thresholds, so nothing was "
            "covered and nothing about covering was shown. Only cover_proven_drawn "
            "titles had the cover measured on the rendition. The titles under "
            "not_analyzed have no verdict and are in none of the four counts."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.verify",
        description="Check a title and block publishing if anything fails.",
    )
    parser.add_argument("--workdir", required=True, help="the ingest work directory")
    parser.add_argument("--sha", help="the source SHA-256 of the title")
    parser.add_argument(
        "--pool-summary",
        metavar="PATH",
        help=(
            "count every title in the work directory by what verify proved about it, "
            "write that to PATH as JSON, and check nothing else"
        ),
    )
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

    if args.pool_summary:
        summary = pool_summary(args.workdir)
        out = Path(args.pool_summary)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
        print(
            f"{summary['analyzed']} title(s) analyzed: "
            f"{summary['no_flagged_segments']} with no flagged segment, "
            f"{summary['cover_proven_drawn']} with the cover proven drawn, "
            f"{summary['cover_not_proven']} with the cover unproven, "
            f"{summary['failed']} failed. Written to {out}"
        )
        if not summary["adds_up"]:
            print(
                "VERIFY FAILED: the counts do not add up to the titles on disk",
                file=sys.stderr,
            )
            return 1
        return 0

    if not args.sha:
        print("VERIFY FAILED: --sha is required", file=sys.stderr)
        return 2

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
