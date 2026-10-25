"""Local-only video intake and review. Analysis is never playback authorization.

Run ``python -m pipeline.local_intake serve --root /private/local/intake``.
A signer is optional and must be an existing, separately authorized pair.
This module never creates keys, changes app trust, installs an app or plays media.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import PipelineError
from .flashmap_adapter import FlashmapAdapter
from .hashing import fingerprint, sha256_file
from .hideplan import build_app_playback_plan
from .local_intake_media import Mp4IntakeError, refuse_protected_mp4
from .local_library import _file, _lock, _path_inside, _write_json, prepare_local_title
from .packaged_library import check_packaged_library, export_packaged_library
from .probe import VideoProbe, probe_video
from .upload_server import parse_multipart

MAX_BYTES = 64 * 1024 * 1024
MAX_SECONDS = 60
MAX_JOBS = 8
JOB_TIMEOUT_S = 3600
ACTIVE = {"queued", "checking", "analyzing", "preparing", "verifying", "exporting"}
TERMINAL = {"review", "signing_blocked", "package_review", "failed", "canceled", "interrupted"}
JOB_ID = re.compile(r"[a-f0-9]{32}")
WORKER_RUN: tuple[str, int] | None = None


class IntakeError(PipelineError):
    """A short user-visible refusal, without command output or private paths."""


def job_dir(root: Path, job_id: str) -> Path:
    if not JOB_ID.fullmatch(job_id):
        raise IntakeError("Unknown import.")
    path = _path_inside(root / job_id, root)
    if not path.is_dir():
        raise IntakeError("Unknown import.")
    return path


def read_job(path: Path) -> dict:
    data = json.loads(_file(path / "job.json", path).read_text())
    if not isinstance(data, dict) or data.get("id") != path.name:
        raise IntakeError("Import metadata does not match this job.")
    if (
        not isinstance(data.get("status"), str)
        or data["status"] not in ACTIVE | TERMINAL
        or not isinstance(data.get("title"), str)
        or not data["title"].strip()
        or type(data.get("created_at")) not in {int, float}
        or not math.isfinite(data["created_at"])
    ):
        raise IntakeError("Import metadata is incomplete or unreadable.")
    return data


def update(path: Path, **fields) -> dict:
    # Serialize identity checks and publication, including cancel/restart invalidation.
    descriptor = os.open(path / ".publish.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        data = read_job(path)
        if WORKER_RUN and (data.get("run_id") != WORKER_RUN[0] or os.getppid() != WORKER_RUN[1]):
            raise IntakeError("This import run is no longer current.")
        data.update(fields, updated_at=time.time())
        _write_json(path / "job.json", data, path)
        return data
    finally:
        os.close(descriptor)


def validate_container(source: Path) -> None:
    # Restrict the file itself, rather than trusting its name or an auto-detected codec.
    with source.open("rb") as handle:
        header = handle.read(4096)
    size = int.from_bytes(header[:4], "big")
    brands = {header[8:12], *(header[i : i + 4] for i in range(16, min(size, 4096), 4))}
    if (
        header[4:8] != b"ftyp"
        or not 16 <= size <= 4096
        or size > len(header)
        or b"qt  " in brands
        or not brands & {b"isom", b"iso2", b"mp41", b"mp42", b"avc1"}
    ):
        raise IntakeError(
            "Choose a standard MP4 container; renamed or unsupported files are refused."
        )
    try:
        refuse_protected_mp4(source)
    except Mp4IntakeError as exc:
        raise IntakeError(str(exc)) from exc


def require_source(path: Path, job: dict) -> Path:
    source = _file(path / "original.mp4", path)
    if source.stat().st_size > MAX_BYTES or sha256_file(source) != job["source_sha256"]:
        raise IntakeError("The selected file changed. Start a new import.")
    return source


def validate_probe(probe: VideoProbe) -> None:
    if not math.isfinite(probe.duration_s) or not 0 < probe.duration_s <= MAX_SECONDS:
        raise IntakeError("Choose a video between 1 frame and 60 seconds long.")
    if probe.codec_name != "h264" or probe.pix_fmt != "yuv420p":
        raise IntakeError("This version supports 8-bit H.264 MP4 video only.")
    if not 16 <= probe.width <= 1280 or not 16 <= probe.height <= 720:
        raise IntakeError("Choose a video no larger than 1280 by 720 pixels.")
    if (
        not probe.avg_frame_rate
        or not math.isfinite(probe.avg_frame_rate)
        or not 1 <= probe.avg_frame_rate <= 60
    ):
        raise IntakeError("Choose a video between 1 and 60 frames per second.")
    if probe.color_transfer not in {None, "unknown", "bt709", "smpte170m", "iec61966-2-1"}:
        raise IntakeError("HDR and unsupported color transfer are not supported.")
    if not probe.has_audio or any(a.codec_name != "aac" for a in probe.audio_streams):
        raise IntakeError("Choose an MP4 with an AAC audio track for this TV workflow.")
    if probe.has_subtitles:
        raise IntakeError("Embedded subtitles are not supported by this intake version.")


def review_analysis(source: Path, destination: Path, progress=lambda _stage: None) -> dict:
    """Read the entire file, with the same app-v1 room and cover-plan rules."""
    before = sha256_file(source)
    progress("Checking format and duration")
    validate_container(source)
    basic = probe_video(source, read_frame_timestamps=False)
    validate_probe(basic)
    probe = probe_video(source)
    validate_probe(probe)
    if not probe.frame_timestamps_s or probe.frame_count != len(probe.frame_timestamps_s):
        raise IntakeError("The complete video timeline could not be read.")
    if probe.variable_frame_rate:
        raise IntakeError("Variable frame rate is not supported by this intake version.")
    maps = {}
    hashes = {}
    adapter = FlashmapAdapter(timeout_s=JOB_TIMEOUT_S)
    for profile in ("wcag", "broadcast"):
        progress("Analyzing the full video: " + profile)
        target = destination / (profile + ".json")
        doc = adapter.analyze(source, profile=profile, out_path=target, diag_in=85, distance_ft=4)
        raw_source = doc.raw.get("source", {})
        tolerance = max(50, (probe.frame_interval_median_s or 0) * 2000)
        last = raw_source.get("last_pts_ms")
        if (
            doc.source_sha256 != before
            or raw_source.get("frame_count") != probe.frame_count
            or not isinstance(last, (int, float))
            or not math.isfinite(last)
            or abs(last - probe.frame_timestamps_s[-1] * 1000) > tolerance
        ):
            raise IntakeError(
                "Analysis did not cover the complete selected file. Nothing is playable."
            )
        maps[profile] = doc
        hashes[profile] = sha256_file(target)
    if sha256_file(source) != before:
        raise IntakeError("The selected file changed during analysis. Start again.")
    presets = {}
    for preset in ("wcag", "broadcast", "extra-cautious"):
        plan = build_app_playback_plan(
            maps, source_sha256=before, duration_ms=probe.duration_ms, preset=preset
        )
        spans = [
            {"start_ms": i.start_ms, "end_ms": i.end_ms, "reason": i.reason} for i in plan.intervals
        ]
        presets[preset] = {
            "intervals": spans,
            "covered_ms": sum(i.duration_ms for i in plan.intervals),
        }
    return {
        "source_sha256": before,
        "duration_ms": probe.duration_ms,
        "frame_count": probe.frame_count,
        "analysis_width": maps["wcag"].raw.get("color", {}).get("analysis_width"),
        "review_map_hashes": hashes,
        "flagged_intervals": {
            profile: [i.to_dict() for i in doc.segments] for profile, doc in maps.items()
        },
        "presets": presets,
        "analysis_complete": True,
        "playable": False,
        "limitations": "Full temporal file analysis at the analyzer working resolution; not a medical safety assessment.",
    }


def analysis_worker(path: Path) -> None:
    job = read_job(path)
    source = require_source(path, job)
    update(path, status="checking", stage="Checking the selected file")
    run_id = job["run_id"]
    destination = path / "runs" / run_id
    destination.mkdir(parents=True, mode=0o700)
    review = review_analysis(
        source, destination, lambda stage: update(path, status="analyzing", stage=stage)
    )
    review["analysis_run"] = run_id
    update(
        path,
        status="review",
        stage="Review the planned interruptions",
        review=review,
        review_digest=fingerprint(review),
        error=None,
    )


def checked_review(path: Path) -> tuple[dict, Path]:
    job = read_job(path)
    source = require_source(path, job)
    review = job.get("review", {})
    if (
        not review.get("analysis_complete")
        or review.get("source_sha256") != job["source_sha256"]
        or fingerprint(review) != job.get("review_digest")
    ):
        raise IntakeError("The complete analysis review is missing or changed. Analyze again.")
    map_root = path
    if review.get("analysis_run"):
        if not JOB_ID.fullmatch(review["analysis_run"]):
            raise IntakeError("Invalid analysis identity. Analyze again.")
        map_root = _path_inside(path / "runs" / review["analysis_run"], path)
    for profile, expected in review["review_map_hashes"].items():
        if (
            profile not in {"wcag", "broadcast"}
            or sha256_file(_file(map_root / (profile + ".json"), path)) != expected
        ):
            raise IntakeError("An analysis file changed. Analyze again.")
    return job, source


def inspect_package(directory: Path, expected_source: str) -> dict:
    manifest = check_packaged_library(directory, require_reports=True)
    titles = manifest.get("titles", [])
    if len(titles) != 1 or titles[0].get("sourceSha256") != expected_source:
        raise IntakeError("The verified package does not match this selected video.")
    return {
        "bundle_id": manifest["bundleId"],
        "source_sha256": expected_source,
        "title": titles[0]["title"],
        "duration_ms": titles[0]["durationMs"],
        "catalog_sha256": sha256_file(directory / "catalog.json"),
        "public_key_fingerprint": "sha256:"
        + hashlib.sha256(base64.b64decode(manifest["publicKeyBase64"], validate=True)).hexdigest(),
        "verification": titles[0]["verification"],
        "status": "verified_package_awaiting_app_approval",
        "playable_in_current_tv_app": False,
    }


def prepare_worker(path: Path, key: Path, pub: Path) -> None:
    job, source = checked_review(path)
    if job.get("approved_review") != job["review_digest"]:
        raise IntakeError("Review and approve the interruption plan before preparation.")
    for credential in (key, pub):
        if not credential.is_file() or credential.resolve().is_relative_to(path.parent):
            raise IntakeError(
                "An authorized signer pair must already exist outside the intake workspace."
            )
    update(path, status="preparing", stage="Preparing and verifying all presets", error=None)
    run_root = _path_inside(path / "runs" / job["run_id"], path)
    run_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Fresh private workspace per run. Interrupted workers cannot change a retry's artifacts.
    receipt = prepare_local_title(
        source, run_root / "prepared", key=key, pub=pub, title=job["title"]
    )
    if receipt.get("status") != "ready":
        raise IntakeError("Preparation or verification failed. No playable package was published.")
    # Preparation re-analyzes; require the resulting plans to match the review the user approved.
    from .hideplan import HidePlan
    from .layout import TitleLayout

    layout = TitleLayout(run_root / "prepared", job["source_sha256"])
    for preset, expected in job["review"]["presets"].items():
        plan = HidePlan.from_dict(json.loads(layout.plan_path(preset).read_text()))
        actual = [
            {"start_ms": i.start_ms, "end_ms": i.end_ms, "reason": i.reason} for i in plan.intervals
        ]
        if actual != expected["intervals"]:
            raise IntakeError(
                "Preparation changed the interruption plan. Review a new analysis before exporting."
            )
    require_source(path, job)
    update(path, status="exporting", stage="Checking the prepared package")
    export_packaged_library(
        run_root / "prepared", run_root / "package", pub=pub, source_shas=[job["source_sha256"]]
    )
    package = inspect_package(run_root / "package", job["source_sha256"])
    package["relative_directory"] = str((run_root / "package").relative_to(path))
    update(
        path,
        status="package_review",
        stage="Verified package ready for operator review",
        package=package,
        delivery=None,
        delivery_plan=None,
        error=None,
    )


class IntakeStore:
    def __init__(self, root: Path, *, key: Path | None = None, pub: Path | None = None):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.key, self.pub = key, pub
        if bool(key) != bool(pub):
            raise IntakeError("Both existing signer files are required, or omit both.")
        self.children: dict[str, tuple[subprocess.Popen, float]] = {}
        self.mutex = threading.RLock()
        self.lease = _lock(self.root)
        self.lease.__enter__()
        for path in self.root.iterdir():
            if JOB_ID.fullmatch(path.name) and path.is_dir():
                job_dir(self.root, path.name)
                if self.display_job(path)["status"] in ACTIVE:
                    update(
                        path,
                        status="interrupted",
                        run_id=None,
                        stage="The previous session ended before completion",
                        error="Analyze again. No result from that run is playable.",
                    )

    def display_job(self, path: Path) -> dict:
        """Keep unrelated reviews reachable without repairing or trusting damaged records."""
        try:
            job = read_job(path)
            if path.name in self.children and job["status"] in TERMINAL:
                # A result can be durable just before its producer exits. Keep
                # actions disabled until ownership is released, not merely saved.
                return {**job, "status": "analyzing", "stage": "Finishing the import worker"}
            return job
        except (OSError, ValueError, PipelineError):
            active = path.name in self.children
            return {
                "id": path.name,
                "title": "Unreadable import",
                "status": "analyzing" if active else "unreadable",
                "stage": "This import record could not be read. Its files have been kept.",
                "error": (
                    "Cancel the active import before removing its local copy."
                    if active else
                    "Remove this local import and select the original file again, or restore its saved record."
                ),
                "created_at": path.stat().st_mtime,
                "record_unreadable": True,
                "playable": False,
            }

    def stop_child(self, job_id: str) -> None:
        owned = self.children.pop(job_id, None)
        if owned:
            child, _ = owned
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()

    def poll(self) -> list[dict]:
        with self.mutex:
            for job_id, (child, started) in list(self.children.items()):
                if child.poll() is None and time.monotonic() - started <= JOB_TIMEOUT_S:
                    try:
                        saved = read_job(job_dir(self.root, job_id))
                    except (OSError, ValueError, PipelineError):
                        continue
                    if saved["status"] not in TERMINAL:
                        continue
                    try:
                        child.wait(timeout=0.1)
                    except subprocess.TimeoutExpired:
                        continue
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                path = job_dir(self.root, job_id)
                del self.children[job_id]
                job = self.display_job(path)
                if not job.get("record_unreadable") and job["status"] in ACTIVE:
                    update(
                        path,
                        status="interrupted",
                        run_id=None,
                        stage="Analysis or preparation did not complete",
                        error="No completed result. Retry with a supported file.",
                    )
            jobs = [
                self.display_job(job_dir(self.root, p.name))
                for p in self.root.iterdir()
                if JOB_ID.fullmatch(p.name)
            ]
            return sorted(jobs, key=lambda j: j["created_at"], reverse=True)

    def launch(self, path: Path, mode: str) -> None:
        args = [
            sys.executable,
            "-m",
            "pipeline.local_intake",
            "worker",
            "--job",
            str(path),
            "--mode",
            mode,
        ]
        if mode == "prepare":
            if not self.key or not self.pub:
                update(
                    path,
                    status="signing_blocked",
                    stage="Developer-assisted preparation required",
                    error="No authorized signer is configured. Analysis is complete; this file is not playable on TV.",
                )
                return
            args += ["--key", str(self.key), "--pub", str(self.pub)]
        run_id = uuid.uuid4().hex
        update(path, run_id=run_id)
        args += ["--run-id", run_id, "--parent-pid", str(os.getpid())]
        # All children and their ffmpeg/analyzer descendants belong to this import only.
        child = subprocess.Popen(
            args,
            cwd=Path(__file__).resolve().parent.parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.children[path.name] = (child, time.monotonic())

    def create(
        self, filename: str, data: bytes, title: str, *, permission_confirmed: bool = False
    ) -> dict:
        with self.mutex:
            if permission_confirmed is not True:
                raise IntakeError(
                    "Confirm that you own this non-DRM video or have permission to process it."
                )
            jobs = self.poll()
            if any(j["status"] in ACTIVE for j in jobs):
                raise IntakeError("An import is already running. Finish or cancel it first.")
            if len(jobs) >= MAX_JOBS:
                raise IntakeError(
                    "Remove an old import before adding another. Eight imports is the limit."
                )
            if Path(filename).suffix.lower() != ".mp4" or not data or len(data) > MAX_BYTES:
                raise IntakeError("Choose a local MP4 file of at most 64 MiB.")
            title = title.strip()
            if not title or len(title) > 120:
                raise IntakeError("Enter a title from 1 to 120 characters.")
            path = self.root / uuid.uuid4().hex
            path.mkdir(mode=0o700)
            source = path / "original.mp4"
            source.write_bytes(data)
            source.chmod(0o600)
            job = {
                "id": path.name,
                "title": title,
                "source_sha256": sha256_file(source),
                "bytes": len(data),
                "status": "queued",
                "stage": "Waiting to analyze",
                "created_at": time.time(),
                "playable": False,
                # A user's acknowledgement, never an application verification of rights.
                "permission_confirmed": True,
            }
            _write_json(path / "job.json", job, path)
            self.launch(path, "analyze")
            return job

    def export_review(self, job_id: str) -> dict:
        """Download the exact current review without preparing or authorizing a title."""
        with self.mutex:
            self.poll()
            path = job_dir(self.root, job_id)
            if self.display_job(path)["status"] not in {"review", "signing_blocked", "package_review"}:
                raise IntakeError("Wait for a complete current analysis before saving its review.")
            job, _ = checked_review(path)
            return {
                "schema": "calm-frames-caregiver-review-v1",
                "title": job["title"],
                "source": {"sha256": job["source_sha256"], "bytes": job["bytes"]},
                "analysis": job["review"],
                "processing_permission_confirmed": job.get("permission_confirmed") is True,
                "permission_verified_by_application": False,
                "tv_playback_authorized": False,
                "limitations": [
                    "Analysis does not establish medical safety, seizure prevention or comfort.",
                    "Use only non-DRM videos you own or have permission to process. Rights are not verified by this application.",
                    "This review does not authorize original playback or add a title to the TV library.",
                    "TV delivery requires a separately authorized signer, exact edition approval and a checked app build.",
                ],
            }

    def action(self, job_id: str, action: str) -> dict:
        with self.mutex:
            self.poll()
            path = job_dir(self.root, job_id)
            job = self.display_job(path)
            if job.get("record_unreadable"):
                if action == "cancel":
                    self.stop_child(job_id)
                    return self.display_job(path)
                if action == "delete" and job_id not in self.children:
                    import shutil

                    shutil.rmtree(path)
                    return {"deleted": job_id}
                raise IntakeError(
                    "This record cannot authorize analysis, review or delivery. Cancel any active work before removing its local copy."
                )
            if action == "plan-delivery":
                from .edition_delivery import plan_delivery
                from .package_delivery import APP

                update(path, delivery_plan=None)
                if job["status"] != "package_review" or not job.get("delivery"):
                    raise IntakeError("Stage a verified package before planning delivery.")
                result = plan_delivery(path / "delivery-reviews", job["delivery"]["ticket_id"], APP)
                result["staging_root"] = str(path / "delivery-reviews")
                return update(path, delivery_plan=result)
            if action in {"stage-delivery", "check-delivery", "cancel-delivery"}:
                from .package_delivery import cancel_delivery, check_delivery, stage_delivery

                if job["status"] != "package_review" or not job.get("package"):
                    raise IntakeError("Wait for a verified export before staging TV delivery.")
                staging = path / "delivery-reviews"
                prior = job.get("delivery")
                # A failed recheck must not leave a stale ready label in the UI.
                update(path, delivery=None, delivery_plan=None)
                try:
                    if action == "stage-delivery":
                        directory = _path_inside(path / job["package"]["relative_directory"], path)
                        result = stage_delivery(directory, job["source_sha256"], staging)
                    else:
                        if not prior:
                            raise IntakeError("Stage a delivery review first.")
                        operation = check_delivery if action == "check-delivery" else cancel_delivery
                        result = operation(staging, prior["ticket_id"])
                except (OSError, ValueError, PipelineError):
                    if prior:
                        # Keep the cancellation handle, never the old ready status.
                        update(path, delivery={**prior, "state": "blocked", "can_watch": False,
                                               "message": "Delivery validation failed. Cancel this review before staging a replacement."})
                    raise
                return update(path, delivery=result)
            if action == "cancel":
                if job.get("delivery") and job["delivery"].get("state") != "canceled":
                    from .package_delivery import cancel_delivery

                    cancel_delivery(path / "delivery-reviews", job["delivery"]["ticket_id"])
                update(path, run_id=None)
                self.stop_child(job_id)
                return update(
                    path,
                    status="canceled",
                    stage="Import canceled",
                    review=None,
                    approved_review=None,
                    package=None,
                    delivery=None,
                    delivery_plan=None,
                    error=None,
                )
            if action == "approve":
                if self.children or any(j["status"] in ACTIVE for j in self.poll()):
                    raise IntakeError("An import is already running. Finish or cancel it first.")
                if job["status"] not in {"review", "signing_blocked"}:
                    raise IntakeError("Wait for a complete analysis before approving it.")
                job, _ = checked_review(path)
                update(
                    path,
                    approved_review=job["review_digest"],
                    error=None,
                    status="preparing",
                    stage="Preparing the reviewed video",
                )
                self.launch(path, "prepare")
                return read_job(path)
            if action == "retry":
                if job["status"] not in {"failed", "canceled", "interrupted"} or self.children:
                    raise IntakeError("Only a stopped import can be analyzed again.")
                require_source(path, job)
                update(
                    path,
                    status="queued",
                    review=None,
                    approved_review=None,
                    package=None,
                    delivery=None,
                    delivery_plan=None,
                    error=None,
                )
                self.launch(path, "analyze")
                return read_job(path)
            if action == "delete":
                if job["status"] in ACTIVE:
                    raise IntakeError("Cancel this import before removing it.")
                import shutil

                # This exact owned job is the only deletion scope, never another library or original.
                shutil.rmtree(job_dir(self.root, job_id))
                return {"deleted": job_id}
            raise IntakeError("Unknown import action.")

    def close(self):
        with self.mutex:
            for job_id in list(self.children):
                self.action(job_id, "cancel")
            self.lease.__exit__(None, None, None)


def serve(root: Path, port: int, key: Path | None = None, pub: Path | None = None) -> None:
    store = IntakeStore(root, key=key, pub=pub)
    origin = "http://127.0.0.1:" + str(port)

    class Handler(BaseHTTPRequestHandler):
        def send(self, code, value, mime="application/json", *, download=None):
            raw = value.encode() if isinstance(value, str) else json.dumps(value).encode()
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if download:
                self.send_header("Content-Disposition", f'attachment; filename="{download}"')
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'none'; frame-ancestors 'none'; object-src 'none'",
            )
            self.end_headers()
            self.wfile.write(raw)

        def permitted(self, post=False):
            return self.headers.get("Host") == origin.removeprefix("http://") and (
                not post or self.headers.get("Origin") == origin
            )

        def do_GET(self):
            if not self.permitted():
                self.send(403, {"error": "Open the local address printed by the server."})
                return
            if self.path == "/":
                self.send(
                    200,
                    Path(__file__).with_name("local_intake.html").read_text(),
                    "text/html; charset=utf-8",
                )
            elif self.path == "/jobs":
                self.send(200, {"jobs": store.poll(), "signer_configured": bool(key and pub)})
            elif re.fullmatch(r"/jobs/[a-f0-9]{32}/review", self.path):
                job_id = self.path.split("/")[2]
                try:
                    report = store.export_review(job_id)
                    self.send(200, report, download=f"calm-frames-review-{job_id}.json")
                except IntakeError as exc:
                    self.send(400, {"error": str(exc)})
                except (OSError, ValueError, PipelineError):
                    self.send(400, {"error": "The review files could not be verified. Analyze again."})
            else:
                self.send(
                    404, {"error": "Not found. Original and prepared media are never served here."}
                )

        def do_POST(self):
            if not self.permitted(True):
                self.send(403, {"error": "Only this local page can submit imports."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= MAX_BYTES + 16384:
                    raise IntakeError("The upload is too large.")
                self.connection.settimeout(30)
                body = self.rfile.read(length)
                if len(body) != length:
                    raise IntakeError("The upload was interrupted. Choose the file again.")
                if self.path == "/jobs":
                    item = parse_multipart(body, self.headers.get("Content-Type", ""))
                    result = store.create(
                        item.filename, item.data, item.fields.get("title", ""),
                        permission_confirmed=item.fields.get("permission") == "confirmed",
                    )
                else:
                    parts = self.path.strip("/").split("/")
                    if len(parts) != 3 or parts[0] != "jobs":
                        raise IntakeError("Unknown import action.")
                    result = store.action(parts[1], parts[2])
                self.send(200, result)
            except IntakeError as exc:
                self.send(400, {"error": str(exc)})
            except (ValueError, OSError, PipelineError):
                self.send(
                    400,
                    {
                        "error": "The request could not be completed. Check the file limits and current job state, then try again."
                    },
                )

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(
        f"Local video review: {origin}\nNo media plays or leaves this machine. Ctrl-C stops owned imports.",
        flush=True,
    )
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.close()


def worker_watchdog(parent_pid: int, stop: threading.Event) -> None:
    deadline = time.monotonic() + JOB_TIMEOUT_S
    while not stop.wait(0.25):
        if os.getppid() != parent_pid or time.monotonic() >= deadline:
            # Only the current worker's isolated session, never a persisted PID.
            if os.getpgrp() == os.getpid():
                os.killpg(os.getpgrp(), signal.SIGKILL)
            os._exit(1)


def main(argv=None) -> int:
    global WORKER_RUN
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    web = commands.add_parser("serve")
    web.add_argument("--root", required=True, type=Path)
    web.add_argument("--port", type=int, default=8766)
    web.add_argument("--key", type=Path)
    web.add_argument("--pub", type=Path)
    worker = commands.add_parser("worker")
    worker.add_argument("--job", required=True, type=Path)
    worker.add_argument("--mode", choices=["analyze", "prepare"], required=True)
    worker.add_argument("--run-id", required=True)
    worker.add_argument("--parent-pid", required=True, type=int)
    worker.add_argument("--key", type=Path)
    worker.add_argument("--pub", type=Path)
    args = parser.parse_args(argv)
    if args.command == "serve":
        serve(args.root, args.port, args.key, args.pub)
        return 0
    path = args.job.resolve()
    WORKER_RUN = (args.run_id, args.parent_pid)
    stop = threading.Event()
    threading.Thread(target=worker_watchdog, args=(args.parent_pid, stop), daemon=True).start()
    try:
        update(path)
        if args.mode == "analyze":
            analysis_worker(path)
        elif args.key and args.pub:
            prepare_worker(path, args.key, args.pub)
        else:
            raise IntakeError("An existing authorized signer is required.")
        return 0
    except Exception as exc:
        message = (
            str(exc)
            if isinstance(exc, IntakeError)
            else "The complete analysis or verification could not finish. No playable result was produced."
        )
        try:
            update(
                path,
                status="failed",
                stage="Import stopped",
                error=message,
                review=None,
                package=None,
            )
        except (IntakeError, OSError):
            pass  # A superseded worker must never publish over cancellation or a newer run.
        return 1
    finally:
        stop.set()


if __name__ == "__main__":
    raise SystemExit(main())
