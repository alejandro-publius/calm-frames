"""Ingest one title, or several, keyed by the source SHA-256.

Order, which is also the order of the ledger steps:

    probe
    -> flashmap analyze, once per preset
    -> hide plan: segments plus guard band, merged, red always opaque
    -> luminance pass and the cover still, taken from a calm moment
    -> kid safe HLS rendition per preset, audio and captions untouched
    -> BIF trickplay, from the safe rendition only
    -> poster frames, from calm moments
    -> signed map
    -> cover model render, which verify analyzes
    -> verify
    -> catalog entry

Every step writes a fingerprint of its inputs into the ledger, and each
fingerprint includes the fingerprints of the steps it depends on. A second run
over the same file with the same settings does no work. Change the guard band
and only the plan and what follows it is redone.

Usage:

    python -m pipeline.ingest VIDEO [VIDEO ...] --workdir out \\
        --key team_key.pem --pub team_key.pub.pem

Safety: this never opens a player and never writes anything to ``media/``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

from . import VERSION, PipelineError
from .bif import DEFAULT_INTERVAL_MS, DEFAULT_THUMB_WIDTH, build_bif, plan_bif_frames
from .catalog import (
    STATUS_FAILED,
    STATUS_PENDING,
    CatalogEntry,
    RenditionEntry,
    read_entry,
    update_index,
    write_entry,
)
from .ffmpegtool import require_tools
from .flashmap_adapter import FlashmapAdapter, iter_presets, tail_to_hold_ms
from .hashing import fingerprint, sha256_file
from .hideplan import (
    APP_PLAYBACK_MAPS,
    APP_PLAYBACK_RECIPE,
    DEFAULT_CALM_MARGIN_MS,
    DEFAULT_GUARD_BAND_MS,
    DEFAULT_MIN_COVER_MS,
    HidePlan,
    build_app_playback_plan,
    build_hide_plan,
    total_covered_ms,
    union_intervals,
)
from .layout import TitleLayout
from .posters import (
    DEFAULT_POSTER_COUNT,
    DEFAULT_POSTER_WIDTH,
    DEFAULT_SAMPLE_FPS,
    STILL_FROM_NEUTRAL_CARD,
    STILL_FROM_SOURCE,
    LumaSeries,
    choose_calm_times,
    choose_cover_still_time,
    extract_cover_still,
    extract_posters,
    luminance_series,
)
from .probe import VideoProbe, probe_video
from .render import (
    DEFAULT_CRF,
    DEFAULT_HLS_SEGMENT_S,
    DEFAULT_PRESET,
    NEUTRAL_STILL_RGB,
    make_neutral_still,
    package_hls,
    render_cover_model,
    render_safe_master,
)
from .sceneholds import (
    SCENE_HOLD_VERSION,
    build_scene_holds,
    read_scene_holds,
    scene_identity,
    scene_payload,
)
from .state import Ledger
from .verify import VerifyReport, apply_to_catalog, verify_title, write_report


@dataclass
class IngestOptions:
    presets: list[str] = field(default_factory=list)
    guard_band_ms: float = DEFAULT_GUARD_BAND_MS
    min_cover_ms: float = DEFAULT_MIN_COVER_MS
    allow_dim: bool = True
    calm_margin_ms: float = DEFAULT_CALM_MARGIN_MS
    diag_in: float | None = None
    distance_ft: float | None = None
    key: str | None = None
    pub: str | None = None
    poster_count: int = DEFAULT_POSTER_COUNT
    poster_width: int = DEFAULT_POSTER_WIDTH
    bif_interval_ms: int = DEFAULT_INTERVAL_MS
    bif_width: int = DEFAULT_THUMB_WIDTH
    crf: int = DEFAULT_CRF
    x264_preset: str = DEFAULT_PRESET
    segment_seconds: float = DEFAULT_HLS_SEGMENT_S
    sample_fps: float = DEFAULT_SAMPLE_FPS
    force: bool = False
    skip_verify: bool = False
    title: str | None = None
    scene_holds: bool = True
    playback_compatible: bool = False


@dataclass
class IngestResult:
    sha256: str
    source: Path
    layout: TitleLayout
    entry: CatalogEntry
    steps_run: list[str] = field(default_factory=list)
    steps_skipped: list[str] = field(default_factory=list)
    verify_passed: bool = False
    verify_report: dict | None = None

    @property
    def publishable(self) -> bool:
        return self.entry.kid_mode_visible


class _Steps:
    """Runs a step, or skips it when the ledger says it is already done."""

    def __init__(self, ledger: Ledger, *, force: bool) -> None:
        self.ledger = ledger
        self.force = force
        self.fingerprints: dict[str, str] = {}
        self.ran: list[str] = []
        self.skipped: list[str] = []

    def _output_hashes(self, outputs: Sequence[Path]) -> dict[str, str | None]:
        root = self.ledger.title_dir.resolve()
        return {
            str(path.resolve().relative_to(root)): sha256_file(path) if path.is_file() else None
            for path in outputs
        }

    def run(
        self,
        name: str,
        payload: dict,
        outputs: Sequence[Path],
        work: Callable[[], dict | None],
        *,
        depends_on: Sequence[str] = (),
        cache_result: bool = True,
        check_output_bytes: bool = False,
    ) -> str:
        parents = {dep: self.fingerprints.get(dep, "") for dep in depends_on}
        fp = fingerprint({"v": VERSION, "step": name, "in": payload, "parents": parents})
        self.fingerprints[name] = fp
        if cache_result and not self.force and self.ledger.is_done(name, fp):
            previous = self.ledger.get(name)
            if not check_output_bytes or (
                previous is not None
                and previous.extra.get("output_sha256") == self._output_hashes(
                    [self.ledger.title_dir / output for output in previous.outputs]
                )
            ):
                self.skipped.append(name)
                return fp
        extra = work() or {}
        if check_output_bytes:
            # Probe and preview metadata affect what can be displayed. Restore
            # changed cached artifacts from their source, not their filenames.
            extra["output_sha256"] = self._output_hashes(outputs)
        self.ledger.record(name, fp, outputs, extra)
        self.ran.append(name)
        return fp


def ingest_title(
    source: str | Path,
    workdir: str | Path,
    options: IngestOptions | None = None,
    *,
    adapter: FlashmapAdapter | None = None,
) -> IngestResult:
    options = options or IngestOptions()
    adapter = adapter or FlashmapAdapter()
    presets = iter_presets(options.presets)
    if options.playback_compatible:
        required = {name for preset in presets for name in APP_PLAYBACK_MAPS[preset]}
        if not required.issubset(presets):
            raise PipelineError("App-compatible preparation requires WCAG and Broadcast maps together.")
    # Use one explicit room for every map in the app recipe. Otherwise the
    # legacy extra-cautious preset silently picks a different analysis room.
    diag_in = options.diag_in if options.diag_in is not None else (85.0 if options.playback_compatible else None)
    distance_ft = options.distance_ft if options.distance_ft is not None else (4.0 if options.playback_compatible else None)
    # Union-only intervals may have no segment in one map. Do not attach scene
    # descriptors that imply otherwise; verified global stills remain available.
    scene_holds_enabled = options.scene_holds and not options.playback_compatible
    require_tools()

    source = Path(source).resolve()
    if not source.exists():
        raise PipelineError(f"source file does not exist: {source}")

    sha = sha256_file(source)
    layout = TitleLayout(workdir, sha)
    layout.root.mkdir(parents=True, exist_ok=True)
    # Re-ingest must withdraw a previous verdict before any cached artifact is
    # trusted. A missing or changed scene image must never leave the old title
    # playable merely because this run failed before writing the final entry.
    if layout.entry_path.exists():
        previous_entry = read_entry(layout.entry_path)
        previous_entry.status = STATUS_PENDING
        previous_entry.verified = False
        write_entry(layout.entry_path, previous_entry)
        update_index(layout.index_path, previous_entry)
    ledger = Ledger(layout.root)
    stat = source.stat()
    ledger.set_source(
        {
            "path": str(source),
            "name": source.name,
            "size_bytes": stat.st_size,
            "sha256": sha,
            "ingested_at": time.time(),
        }
    )
    steps = _Steps(ledger, force=options.force)

    # 1. Probe.
    probe_holder: dict[str, VideoProbe] = {}

    def do_probe() -> dict:
        probe = probe_video(source)
        layout.probe_path.parent.mkdir(parents=True, exist_ok=True)
        layout.probe_path.write_text(json.dumps(probe.to_dict(), indent=2))
        probe_holder["probe"] = probe
        return {
            "duration_s": probe.duration_s,
            "variable_frame_rate": probe.variable_frame_rate,
            "frames": probe.frame_count,
        }

    steps.run("probe", {"sha": sha}, [layout.probe_path], do_probe,
              check_output_bytes=True)
    probe = probe_holder.get("probe") or VideoProbe.from_dict(
        json.loads(layout.probe_path.read_text())
    )
    duration_ms = probe.duration_ms

    # 2. Analyze, once per preset.
    for preset in presets:
        def do_analyze(preset: str = preset) -> dict:
            doc = adapter.analyze(
                source,
                profile=preset,
                out_path=layout.map_path(preset),
                diag_in=diag_in,
                distance_ft=distance_ft,
                key=options.key,
            )
            return {"segments": doc.violation_count, "signed": doc.is_signed}

        steps.run(
            f"analyze:{preset}",
            {
                "sha": sha,
                "preset": preset,
                "diag_in": diag_in,
                "distance_ft": distance_ft,
                "signed": bool(options.key),
            },
            [layout.map_path(preset)],
            do_analyze,
            depends_on=["probe"],
        )

    # 3. Hide plan per preset.
    plans: dict[str, HidePlan] = {}
    for preset in presets:
        def do_plan(preset: str = preset) -> dict:
            from .flashmap_adapter import load_map

            doc = load_map(layout.map_path(preset))
            plan = build_app_playback_plan(
                {name: load_map(layout.map_path(name)) for name in APP_PLAYBACK_MAPS[preset]},
                source_sha256=sha, duration_ms=duration_ms, preset=preset,
            ) if options.playback_compatible else build_hide_plan(
                doc,
                source_sha256=sha,
                duration_ms=duration_ms,
                preset=preset,
                guard_band_ms=options.guard_band_ms,
                min_cover_ms=options.min_cover_ms,
                allow_dim=options.allow_dim,
            )
            layout.plan_path(preset).parent.mkdir(parents=True, exist_ok=True)
            layout.plan_path(preset).write_text(json.dumps(plan.to_dict(), indent=2))
            plans[preset] = plan
            return {
                "intervals": len(plan.intervals),
                "covered_ms": total_covered_ms(plan.intervals),
                "red_intervals": sum(1 for i in plan.intervals if i.reason == "red"),
            }

        steps.run(
            f"plan:{preset}",
            {
                "guard_band_ms": options.guard_band_ms,
                "min_cover_ms": options.min_cover_ms,
                "allow_dim": options.allow_dim,
                "duration_ms": duration_ms,
                "playback_recipe": APP_PLAYBACK_RECIPE if options.playback_compatible else None,
            },
            [layout.plan_path(preset)],
            do_plan,
            depends_on=[*[f"analyze:{name}" for name in (
                APP_PLAYBACK_MAPS[preset] if options.playback_compatible else (preset,)
            )], "probe"],
        )
        if preset not in plans:
            plans[preset] = HidePlan.from_dict(json.loads(layout.plan_path(preset).read_text()))

    union = union_intervals(plans.values())

    # 4. Luminance pass, used to pick the quietest calm moments.
    def do_luma() -> dict:
        series = luminance_series(
            source,
            metadata_path=layout.luma_metadata_path,
            sample_fps=options.sample_fps,
        )
        layout.luma_path.write_text(json.dumps(series.to_dict()))
        return {"samples": len(series.times_s)}

    steps.run(
        "luma",
        {"sha": sha, "sample_fps": options.sample_fps},
        [layout.luma_path],
        do_luma,
        depends_on=["probe"],
    )
    series = LumaSeries.from_dict(json.loads(layout.luma_path.read_text()))

    # 5. The cover still, one calm frame reused by every preset.
    def do_still() -> dict:
        # A title that flashes end to end has no frame that may be shown, so the cover is a
        # flat neutral card instead. That is not a quiet refusal: the manifest and the catalog
        # entry both say the cover is a card and not a frame of the film, and verify measures
        # the card rather than believing it.
        try:
            time_ms: float | None = choose_cover_still_time(
                union, duration_ms, margin_ms=options.calm_margin_ms, series=series
            )
        except PipelineError:
            time_ms = None

        if time_ms is None:
            make_neutral_still(
                layout.still_path, width=probe.width, height=probe.height
            )
            manifest = {
                "time_ms": None,
                "from": STILL_FROM_NEUTRAL_CARD,
                "calm_margin_ms": options.calm_margin_ms,
                "neutral_rgb": list(NEUTRAL_STILL_RGB),
                "why": (
                    "every moment in this title is inside a flagged span, so there is no "
                    "frame of it that may be shown. The cover is a flat neutral card that "
                    "came from nothing in the title."
                ),
            }
        else:
            extract_cover_still(
                source,
                time_ms=time_ms,
                out_path=layout.still_path,
                width=probe.width,
                height=probe.height,
            )
            manifest = {
                "time_ms": time_ms,
                "from": STILL_FROM_SOURCE,
                "calm_margin_ms": options.calm_margin_ms,
            }
        layout.still_manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return {"time_ms": time_ms, "from": manifest["from"]}

    steps.run(
        "still",
        {
            "union": [(i.start_ms, i.end_ms) for i in union],
            "calm_margin_ms": options.calm_margin_ms,
        },
        [layout.still_path, layout.still_manifest_path],
        do_still,
        depends_on=["luma", *[f"plan:{p}" for p in presets]],
        check_output_bytes=True,
    )

    # 6 to 9, per preset.
    for preset in presets:
        plan = plans[preset]

        scene_images = None
        scene_bytes = None
        if scene_holds_enabled and options.key:
            scene_outputs = [layout.scene_manifest(preset)]

            def do_scenes(preset: str = preset, plan: HidePlan = plan) -> dict:
                images = build_scene_holds(
                    source, layout=layout, preset=preset, intervals=plan.intervals,
                    union=union, probe=probe, margin_ms=options.calm_margin_ms,
                    adapter=adapter,
                )
                scene_outputs.extend(image.path for image in images)  # noqa: B023 - steps.run calls it before the loop moves on
                return {"holds": len(images)}

            steps.run(
                f"scene_holds:{preset}",
                {"version": SCENE_HOLD_VERSION, "calm_margin_ms": options.calm_margin_ms},
                scene_outputs, do_scenes,
                depends_on=["probe", *[f"plan:{p}" for p in presets]],
            )
            scene_images = read_scene_holds(layout, preset)
            scene_bytes = scene_identity(layout, preset)

        def do_rendition(preset: str = preset, plan: HidePlan = plan) -> dict:
            result = render_safe_master(
                source,
                intervals=plan.intervals,
                still_path=layout.still_path,
                out_path=layout.safe_master(preset),
                probe=probe,
                crf=options.crf,
                x264_preset=options.x264_preset,
                segment_seconds=options.segment_seconds,
                pad_tail_ms=tail_to_hold_ms(layout.map_path(preset)),
                scene_holds=scene_images,  # noqa: B023 - steps.run calls it before the loop moves on
            )
            hls = package_hls(
                layout.safe_master(preset),
                out_dir=layout.hls_dir(preset),
                probe=probe,
                segment_seconds=options.segment_seconds,
            )
            return {"master": result.notes, "hls": hls.notes}

        steps.run(
            f"rendition:{preset}",
            {
                "crf": options.crf,
                "x264_preset": options.x264_preset,
                "segment_seconds": options.segment_seconds,
                "scene_holds": scene_bytes,
            },
            [layout.safe_master(preset), layout.master_playlist(preset)],
            do_rendition,
            depends_on=[f"plan:{preset}", "still"],
        )

        def do_bif(preset: str = preset, plan: HidePlan = plan) -> dict:
            frames = plan_bif_frames(
                plan.intervals,
                duration_ms,
                interval_ms=options.bif_interval_ms,
                margin_ms=options.calm_margin_ms,
            )
            path, written = build_bif(
                layout.safe_master(preset),
                frames=frames,
                out_path=layout.bif_path(preset),
                work_dir=layout.bif_work_dir(preset),
                width=options.bif_width,
                source_width=probe.width,
                source_height=probe.height,
                interval_ms=options.bif_interval_ms,
            )
            layout.bif_manifest(preset).write_text(
                json.dumps(
                    {
                        "preset": preset,
                        "from": "safe_rendition",
                        "source_file": str(layout.safe_master(preset)),
                        "interval_ms": options.bif_interval_ms,
                        "calm_margin_ms": options.calm_margin_ms,
                        "frames": [frame.to_dict() for frame in written],
                    },
                    indent=2,
                )
            )
            return {"frames": len(written), "path": str(path)}

        steps.run(
            f"bif:{preset}",
            {
                "interval_ms": options.bif_interval_ms,
                "width": options.bif_width,
                "calm_margin_ms": options.calm_margin_ms,
            },
            [layout.bif_path(preset), layout.bif_manifest(preset)],
            do_bif,
            depends_on=[f"rendition:{preset}"],
            check_output_bytes=True,
        )

        poster_outputs = [layout.posters_manifest(preset)]

        def do_posters(preset: str = preset, plan: HidePlan = plan) -> dict:
            times = choose_calm_times(
                plan.intervals,
                duration_ms,
                count=options.poster_count,
                margin_ms=options.calm_margin_ms,
                series=series,
            )
            height = max(2, int(round(options.poster_width * probe.height / probe.width)))
            if height % 2:
                height += 1
            posters = extract_posters(
                layout.safe_master(preset),
                times_ms=times,
                out_dir=layout.posters_dir(preset),
                width=options.poster_width,
                height=height,
            )
            layout.posters_manifest(preset).write_text(
                json.dumps(
                    {
                        "preset": preset,
                        "from": "safe_rendition",
                        "calm_margin_ms": options.calm_margin_ms,
                        "posters": [poster.to_dict() for poster in posters],
                    },
                    indent=2,
                )
            )
            poster_outputs.extend(poster.path for poster in posters)  # noqa: B023 - steps.run calls it before the loop moves on
            return {"posters": len(posters)}

        steps.run(
            f"posters:{preset}",
            {
                "count": options.poster_count,
                "width": options.poster_width,
                "calm_margin_ms": options.calm_margin_ms,
            },
            poster_outputs,
            do_posters,
            depends_on=[f"rendition:{preset}"],
            check_output_bytes=True,
        )

        def do_signed_map(preset: str = preset) -> dict:
            from .flashmap_adapter import load_map

            doc = load_map(layout.map_path(preset))
            if doc.source_sha256 != sha:
                raise PipelineError(
                    f"the {preset} map is bound to {doc.source_sha256}, not to this "
                    f"file ({sha})"
                )
            if options.key and not doc.is_signed:
                raise PipelineError(
                    f"the {preset} map was analyzed with a signing key but carries "
                    "no signature"
                )
            if scene_images is not None:  # noqa: B023 - steps.run calls it before the loop moves on
                from .registry import load_private_key, sign_document, write_registry

                # Segments and profile thresholds are not edited. The new image
                # payload joins the existing canonical Ed25519 signature.
                document = dict(doc.raw, scene_holds=scene_payload(scene_images))  # noqa: B023 - steps.run calls it before the loop moves on
                write_registry(sign_document(document, load_private_key(options.key)),
                               layout.map_path(preset))
            elif "scene_holds" in doc.raw:
                from .registry import load_private_key, sign_document, write_registry

                document = dict(doc.raw)
                document.pop("scene_holds")
                if options.key:
                    document = sign_document(document, load_private_key(options.key))
                else:
                    document.pop("signature", None)
                write_registry(document, layout.map_path(preset))
            return {"signed": doc.is_signed, "bound": True}

        steps.run(
            f"signed_map:{preset}",
            {"key": bool(options.key), "scene_holds": scene_bytes},
            [layout.map_path(preset)],
            do_signed_map,
            depends_on=[f"analyze:{preset}"],
        )

        def do_cover_model(preset: str = preset, plan: HidePlan = plan) -> dict:
            result = render_cover_model(
                source,
                plan=plan,
                out_path=layout.cover_model_path(preset),
                probe=probe,
                scene_holds=scene_images,  # noqa: B023 - steps.run calls it before the loop moves on
            )
            return result.notes

        steps.run(
            f"cover_model:{preset}",
            {"allow_dim": options.allow_dim, "scene_holds": scene_bytes},
            [layout.cover_model_path(preset)],
            do_cover_model,
            depends_on=[f"plan:{preset}"],
        )

    # 10. The catalog entry, pending until verify says otherwise.
    entry = CatalogEntry(
        sha256=sha,
        title=options.title or source.stem,
        source_name=source.name,
        duration_s=probe.duration_s,
        width=probe.width,
        height=probe.height,
        status=STATUS_PENDING,
        verified=False,
        renditions={
            preset: RenditionEntry(
                preset=preset,
                master_playlist=str(layout.master_playlist(preset)),
                safe_master=str(layout.safe_master(preset)),
                map_path=str(layout.map_path(preset)),
                plan_path=str(layout.plan_path(preset)),
                bif_path=str(layout.bif_path(preset)),
                bif_manifest=str(layout.bif_manifest(preset)),
                posters=[
                    poster["path"]
                    for poster in json.loads(
                        layout.posters_manifest(preset).read_text()
                    ).get("posters", [])
                ],
                covered_ms=total_covered_ms(plans[preset].intervals),
                segment_count=len(plans[preset].intervals),
            )
            for preset in presets
        },
        notes={
            "variable_frame_rate": probe.variable_frame_rate,
            "color_transfer": probe.color_transfer,
            "audio_streams": len(probe.audio_streams),
            "subtitle_streams": len(probe.subtitle_streams),
            "guard_band_ms": options.guard_band_ms,
            "allow_dim": options.allow_dim,
            # Where the cover still came from, so kid mode can say so rather than letting a
            # neutral card pass for a frame of the film.
            "cover_still_from": json.loads(layout.still_manifest_path.read_text()).get(
                "from", STILL_FROM_SOURCE
            ),
            "scene_holds": bool(scene_holds_enabled and options.key),
            **({"playback_recipe": APP_PLAYBACK_RECIPE, "analysis_room": {
                "diag_in": diag_in, "distance_ft": distance_ft,
            }} if options.playback_compatible else {}),
        },
    )
    write_entry(layout.entry_path, entry)
    update_index(layout.index_path, entry)

    result = IngestResult(
        sha256=sha,
        source=source,
        layout=layout,
        entry=entry,
        steps_run=list(steps.ran),
        steps_skipped=list(steps.skipped),
    )

    if options.skip_verify:
        return result

    # 11. Verify. A pass is cached, a failure never is.
    previous = ledger.get("verify")
    verify_payload = {
        "scene_verification_version": 2,
        "presets": presets,
        "pub": options.pub,
        "public_key_bytes": sha256_file(options.pub) if options.pub and Path(options.pub).is_file() else None,
        "calm_margin_ms": options.calm_margin_ms,
        "playback_recipe": APP_PLAYBACK_RECIPE if options.playback_compatible else None,
        # An unchanged filename or a cached report is not evidence that the
        # same map, image or encoded output is still on disk.
        "artifact_bytes": {
            str(path): sha256_file(path) if path.is_file() else None
            for preset in presets
            for path in (
                layout.probe_path, layout.still_path, layout.still_manifest_path,
                layout.map_path(preset), layout.plan_path(preset),
                layout.safe_master(preset), layout.cover_model_path(preset),
                layout.scene_manifest(preset),
                layout.bif_path(preset), layout.bif_manifest(preset),
                layout.posters_manifest(preset),
                *sorted(layout.posters_dir(preset).glob("*")),
                *sorted(layout.hls_dir(preset).glob("*")),
            )
        },
        "scene_assets": {
            preset: scene_identity(layout, preset)
            for preset in presets if scene_holds_enabled and options.key
        },
    }
    parents = {
        name: steps.fingerprints[name]
        for name in steps.fingerprints
        if name.split(":")[0]
        in {"probe", "plan", "rendition", "bif", "posters", "still", "scene_holds", "signed_map", "cover_model"}
    }
    verify_fp = fingerprint(
        {"v": VERSION, "step": "verify", "in": verify_payload, "parents": parents}
    )
    cached_pass = (
        not options.force
        and previous is not None
        and previous.fingerprint == verify_fp
        and previous.extra.get("passed") is True
        and layout.verify_report_path.exists()
        and previous.extra.get("report_sha256") == sha256_file(layout.verify_report_path)
    )
    if cached_pass:
        report_data = json.loads(layout.verify_report_path.read_text())
        # The catalog entry was rewritten as pending a moment ago, so the
        # verdict from the cached report has to be put back on it. Without
        # this a second run would quietly drop a verified title out of kid
        # mode.
        apply_to_catalog(layout, VerifyReport.from_dict(report_data))
        result.steps_skipped.append("verify")
        result.verify_passed = bool(report_data.get("passed"))
        result.verify_report = report_data
        result.entry = _reload_entry(layout, result.entry)
        return result

    report = verify_title(
        layout,
        source=source,
        presets=presets,
        adapter=adapter,
        pub_key=options.pub,
        diag_in=diag_in,
        distance_ft=distance_ft,
        playback_compatible=options.playback_compatible,
        calm_margin_ms=options.calm_margin_ms,
        rerender_cover_model=False,
    )
    write_report(layout, report)
    apply_to_catalog(layout, report)
    ledger.record(
        "verify",
        verify_fp,
        [layout.verify_report_path],
        {"passed": report.passed, "failures": [c.name for c in report.failures],
         "report_sha256": sha256_file(layout.verify_report_path)},
    )
    result.steps_run.append("verify")
    result.verify_passed = report.passed
    result.verify_report = report.to_dict()
    result.entry = _reload_entry(layout, result.entry)
    if not report.passed:
        result.entry.status = STATUS_FAILED
    return result


def _reload_entry(layout: TitleLayout, fallback: CatalogEntry) -> CatalogEntry:
    from .catalog import read_entry

    if layout.entry_path.exists():
        return read_entry(layout.entry_path)
    return fallback


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.ingest",
        description="Build the kid safe renditions, maps and trickplay for a title.",
    )
    parser.add_argument("sources", nargs="+", help="video files to ingest")
    parser.add_argument("--workdir", required=True, help="where artifacts are written")
    parser.add_argument(
        "--presets",
        default=",".join(iter_presets(None)),
        help="comma separated presets (default: all three)",
    )
    parser.add_argument("--guard-band-ms", type=float, default=DEFAULT_GUARD_BAND_MS)
    parser.add_argument("--min-cover-ms", type=float, default=DEFAULT_MIN_COVER_MS)
    parser.add_argument("--calm-margin-ms", type=float, default=DEFAULT_CALM_MARGIN_MS)
    parser.add_argument("--diag", type=float, help="television diagonal in inches")
    parser.add_argument("--distance-ft", type=float, help="seat distance in feet")
    parser.add_argument("--key", help="private key the analyzer signs the map with")
    parser.add_argument("--pub", help="public key verify checks the signature against")
    parser.add_argument("--poster-count", type=int, default=DEFAULT_POSTER_COUNT)
    parser.add_argument("--bif-interval-ms", type=int, default=DEFAULT_INTERVAL_MS)
    parser.add_argument("--crf", type=int, default=DEFAULT_CRF)
    parser.add_argument("--x264-preset", default=DEFAULT_PRESET)
    parser.add_argument(
        "--no-dim",
        action="store_true",
        help="the household does not allow a dim cover, so every cover is opaque",
    )
    parser.add_argument("--force", action="store_true", help="redo finished work")
    parser.add_argument("--no-scene-holds", action="store_true",
                        help="use the legacy global still and black or dim live cover")
    parser.add_argument("--playback-compatible", action="store_true",
                        help="use the app's fixed profile unions, timing and opaque fallback")
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="build the artifacts but leave the title unverified, so it cannot publish",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = IngestOptions(
        presets=[p.strip() for p in args.presets.split(",") if p.strip()],
        guard_band_ms=args.guard_band_ms,
        min_cover_ms=args.min_cover_ms,
        calm_margin_ms=args.calm_margin_ms,
        allow_dim=not args.no_dim,
        diag_in=args.diag,
        distance_ft=args.distance_ft,
        key=args.key,
        pub=args.pub,
        poster_count=args.poster_count,
        bif_interval_ms=args.bif_interval_ms,
        crf=args.crf,
        x264_preset=args.x264_preset,
        force=args.force,
        skip_verify=args.skip_verify,
        scene_holds=not args.no_scene_holds,
        playback_compatible=args.playback_compatible,
    )

    adapter = FlashmapAdapter()
    if not adapter.available():
        print(
            f"cannot start the analyzer ({adapter.describe()}). Set "
            "CALM_FRAMES_FLASHMAP_CMD or install flashmap.",
            file=sys.stderr,
        )
        return 2

    summaries = []
    failures = 0
    for source in args.sources:
        try:
            result = ingest_title(source, args.workdir, options, adapter=adapter)
        except PipelineError as exc:
            print(f"INGEST FAILED for {source}: {exc}", file=sys.stderr)
            failures += 1
            continue
        state = "publishable" if result.publishable else "blocked"
        print(
            f"{Path(source).name}: {result.sha256[:12]} {state}, "
            f"{len(result.steps_run)} step(s) run, "
            f"{len(result.steps_skipped)} skipped"
        )
        if not result.publishable and not options.skip_verify:
            failures += 1
            failed = (result.verify_report or {}).get("checks", [])
            for check in failed:
                if not check.get("passed"):
                    print(f"  FAIL {check['name']}: {check['detail']}", file=sys.stderr)
        summaries.append(
            {
                "source": str(source),
                "sha256": result.sha256,
                "publishable": result.publishable,
                "steps_run": result.steps_run,
                "steps_skipped": result.steps_skipped,
            }
        )

    if args.json:
        print(json.dumps(summaries, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
