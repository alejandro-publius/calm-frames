"""Export verified local receipts into an immutable library for a Vega package.

The analyzed source hash and the delivered rendition hash are distinct. Only
prepared MP4s, authenticated maps, extracted text captions and the original
verification report bytes are exported. Report attachments do not change the
immutable media manifests or replace missing evidence with a new analysis.
Nothing serves a network endpoint, opens a player or copies a signing key.

    python -m pipeline.packaged_library export --workdir build/library \
        --output app/assets/raw/prepared-library --pub signer.pub.pem
    python -m pipeline.packaged_library check --output app/assets/raw/prepared-library
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Sequence

from cryptography.hazmat.primitives import serialization

from . import PipelineError
from . import local_library as local
from .catalog import read_entry
from .ffmpegtool import run_ffmpeg
from .flashmap_adapter import PRESETS, load_map, parse_map
from .hashing import fingerprint, sha256_file
from .hideplan import APP_PLAYBACK_TIMING, HidePlan, build_app_playback_plan
from .layout import TitleLayout
from .probe import probe_video
from .registry import _check_map_signature, load_public_key
from .verify import START_OFFSET_LIMIT_MS, OUTCOMES, VerifyReport

VERSION = 1
ASSET_ROOT = "assets/raw/prepared-library"
MAX_TITLES = 16
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
MAX_MAP_BYTES = 2 * 1024 * 1024 + 256 * 1024
MAX_CAPTION_BYTES = 256 * 1024
MAX_CATALOG_BYTES = 16 * 1024 * 1024
MAX_REPORT_BYTES = local.MAX_METADATA_BYTES
_SHA = re.compile(r"[0-9a-f]{64}")
_PATH = re.compile(r"titles/[0-9a-f]{64}/(?:wcag|broadcast|extra-cautious)\.(?:mp4|json|vtt)")
TIMING = APP_PLAYBACK_TIMING


def _verification_metadata(title: dict) -> dict:
    value = title.get("verification")
    if (not isinstance(value, dict)
            or set(value) != {"reportSha256", "checkedInputsSha256", "outcome"}
            or any(not isinstance(value.get(key), str) or not _SHA.fullmatch(value[key])
                   for key in ("reportSha256", "checkedInputsSha256"))
            or value.get("outcome") not in OUTCOMES[:-1]):
        raise PackagedLibraryError("A packaged verification reference is invalid.")
    return value


def _report_references(destination: Path) -> dict[str, list[dict]]:
    references: dict[str, list[dict]] = {}
    for directory in destination.iterdir():
        if _SHA.fullmatch(directory.name) and directory.is_dir():
            manifest = json.loads(_bounded_file(directory / "manifest.json", destination, MAX_CATALOG_BYTES).read_bytes())
            for title in manifest["titles"]:
                digest = _verification_metadata(title)["reportSha256"]
                references.setdefault(digest, []).append(title)
    return references


def _read_report(path: Path) -> bytes:
    # Resolve only after rejecting aliases, including aliases in an input's parents.
    path = _root(path)
    _bounded_file(path, path.parent, MAX_REPORT_BYTES)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise PackagedLibraryError("A verification report must be an owned regular file.")
        with os.fdopen(descriptor, "rb", closefd=False) as reader:
            raw = reader.read(MAX_REPORT_BYTES + 1)
        after = os.fstat(descriptor)
        if (len(raw) > MAX_REPORT_BYTES or (before.st_size, before.st_mtime_ns, before.st_ino)
                != (after.st_size, after.st_mtime_ns, after.st_ino)):
            raise PackagedLibraryError("A verification report changed or exceeded its byte bound.")
        return raw
    finally:
        os.close(descriptor)


def _check_report(raw: bytes, digest: str, titles: list[dict]) -> None:
    if len(raw) > MAX_REPORT_BYTES or hashlib.sha256(raw).hexdigest() != digest:
        raise PackagedLibraryError("Verification report bytes differ from the recorded report hash.")
    # Never turn a key file into an attachment, even inside otherwise valid JSON.
    if re.search(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----", raw):
        raise PackagedLibraryError("A verification report must not contain a private key.")
    def constant(value):
        # VerifyReport's historical writer permits infinite PSNR measurements.
        # Keep these numeric values while refusing an undefined measurement.
        if value in {"Infinity", "-Infinity"}:
            return float(value)
        raise PackagedLibraryError("The verification report contains an undefined measurement.")
    data = json.loads(raw, parse_constant=constant)
    checks = data.get("checks") if isinstance(data, dict) else None
    if (not isinstance(data, dict) or set(data) != {
            "sha256", "source_path", "presets", "passed", "outcome", "started_at", "finished_at", "checks"}
            or data.get("passed") is not True or not isinstance(data.get("source_path"), str)
            or not data["source_path"] or data.get("presets") != list(PRESETS)
            or not isinstance(checks, list) or not checks
            or any(not isinstance(check, dict) or set(check) != {"name", "passed", "detail", "data"}
                   or not isinstance(check.get("name"), str) or not check["name"]
                   or check.get("passed") is not True or not isinstance(check.get("detail"), str)
                   or not isinstance(check.get("data"), dict) for check in checks)
            or any(isinstance(data.get(key), bool) or not isinstance(data.get(key), (int, float))
                   or not math.isfinite(data[key]) for key in ("started_at", "finished_at"))):
        raise PackagedLibraryError("The verification report is not a complete passing report.")
    names = [check["name"] for check in checks]
    required = {"source_hash"} | {f"{name}:{preset}" for preset in PRESETS for name in local._CORE_CHECKS}
    if len(set(names)) != len(names) or not required.issubset(names):
        raise PackagedLibraryError("The verification report is missing required unique checks.")
    for check in checks:
        if check["name"].startswith("plan_matches_map:") and "stored" in check["data"]:
            stored = check["data"]["stored"]
            if isinstance(stored, bool) or not isinstance(stored, (int, float)) or not math.isfinite(stored):
                raise PackagedLibraryError("The verification report has an invalid plan measurement.")
    report = VerifyReport.from_dict(data)
    if any(data["sha256"] != title["sourceSha256"]
           or data["outcome"] != _verification_metadata(title)["outcome"]
           or report.outcome != data["outcome"] for title in titles):
        raise PackagedLibraryError("The verification report source or outcome differs from its title.")


def _check_reports(destination: Path, references: dict[str, list[dict]], *,
                   require_reports: bool = False) -> tuple[int, dict]:
    directory = destination / "reports"
    present, total = set(), 0
    if directory.exists() or directory.is_symlink():
        local._path_inside(directory, destination)
        if not directory.is_dir():
            raise PackagedLibraryError("The verification report namespace must be a directory.")
        for path in directory.iterdir():
            digest = path.name.removesuffix(".json")
            if path.name != f"{digest}.json" or digest not in references:
                raise PackagedLibraryError("An unreferenced verification report is present.")
            raw = _read_report(path)
            _check_report(raw, digest, references[digest])
            present.add(digest)
            total += len(raw)
    missing = sorted(set(references) - present)
    if require_reports and missing:
        raise PackagedLibraryError("Original verification reports are missing: " + ", ".join(missing))
    return total, {"required": len(references), "present": len(present), "missing": missing}


def _publish_reports(destination: Path, reports: dict[str, bytes], references: dict[str, list[dict]], *,
                     projected_total: int | None = None) -> None:
    """Validate the entire batch before writing; roll back new attachments on failure."""
    # Export already checked its locked inputs and final pointer sizes before
    # committing the new generation. Backfill checks its unchanged library here.
    total = _check_output_root(destination) if projected_total is None else 0
    for digest, raw in reports.items():
        if digest not in references:
            raise PackagedLibraryError("The supplied report is not referenced by a packaged title.")
        _check_report(raw, digest, references[digest])
    directory = destination / "reports"
    fresh = {digest: raw for digest, raw in reports.items() if not (directory / f"{digest}.json").exists()}
    final_size = total + sum(map(len, fresh.values())) if projected_total is None else projected_total
    if final_size > MAX_BUNDLE_BYTES:
        raise PackagedLibraryError("Verification reports exceed the package byte budget.")
    if not fresh:
        return
    created_directory = not directory.exists()
    attached = []
    try:
        # Staging is outside the shipped namespace. An exclusive link publishes a
        # complete file without overwriting any concurrently created destination.
        with tempfile.TemporaryDirectory(prefix=".reports-", dir=destination.parent) as temporary:
            stage = Path(temporary)
            for digest, raw in fresh.items():
                (stage / f"{digest}.json").write_bytes(raw)
            directory.mkdir(exist_ok=True)
            local._path_inside(directory, destination)
            for digest in fresh:
                target = directory / f"{digest}.json"
                staged = stage / target.name
                os.link(staged, target)
                attached.append(target)
                staged.unlink()
    except BaseException:
        for path in attached:
            path.unlink(missing_ok=True)
        if created_directory and directory.is_dir() and not directory.is_symlink() and not any(directory.iterdir()):
            directory.rmdir()
        raise


class PackagedLibraryError(local.LocalLibraryError):
    """An export refusal that is safe to show without disclosing key paths."""


def _json_text(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def catalog_module(text: str) -> str:
    digest = hashlib.sha256(text.encode()).hexdigest()
    return (
        "/** Generated by pipeline.packaged_library. Verify before building the app. */\n"
        f"export const PACKAGED_LIBRARY_JSON = {json.dumps(text)};\n"
        f"export const PACKAGED_LIBRARY_SHA256 = {json.dumps(digest)};\n"
    )


def _root(path: str | Path) -> Path:
    candidate = Path(path).absolute()
    # Reject aliases even if resolving one would end at an otherwise valid root.
    for parent in (candidate, *candidate.parents):
        if parent.is_symlink():
            raise PackagedLibraryError("The package output must not use a symlink.")
    return candidate.resolve()


def _bounded_file(path: Path, root: Path, limit: int) -> Path:
    local._file(path, root)
    if path.stat().st_size > limit:
        raise PackagedLibraryError("A package input exceeds its byte bound.")
    return path


def _copy_checked(source: Path, destination: Path, expected: str, root: Path) -> int:
    """Hash the same bytes that are copied, and detect a concurrent writer."""
    _bounded_file(source, root, MAX_BUNDLE_BYTES)
    descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise PackagedLibraryError("A package input is not an owned regular file.")
        with os.fdopen(descriptor, "rb", closefd=False) as reader, destination.open("xb") as writer:
            for block in iter(lambda: reader.read(1024 * 1024), b""):
                size += len(block)
                if size > MAX_BUNDLE_BYTES:
                    raise PackagedLibraryError("A package input grew beyond its byte bound.")
                writer.write(block)
                digest.update(block)
        after = os.fstat(descriptor)
        if ((before.st_size, before.st_mtime_ns, before.st_ino) !=
                (after.st_size, after.st_mtime_ns, after.st_ino) or digest.hexdigest() != expected):
            raise PackagedLibraryError("A prepared artifact changed while it was being packaged.")
    finally:
        os.close(descriptor)
    return size


def _schedule(intervals) -> list[tuple[float, float, str]]:
    return [(item.start_ms, item.end_ms, item.reason) for item in intervals]


def require_runtime_plan(layout: TitleLayout, maps: dict, preset: str, duration_ms: float) -> None:
    """The prepared picture must follow the app's complete per-preset schedule.

    A profile-only Broadcast plan or short Extra cautious plan is refused.
    This does not relax the production verifier's independent map/plan check.
    """
    data = local._json(layout.plan_path(preset), layout.workdir)
    plan = HidePlan.from_dict(data)
    expected = build_app_playback_plan(maps, source_sha256=layout.sha256,
                                       duration_ms=duration_ms, preset=preset)
    if (plan.source_sha256 != layout.sha256 or plan.profile != preset
            or not math.isfinite(plan.duration_ms) or abs(plan.duration_ms - duration_ms) > 1
            or _schedule(plan.intervals) != _schedule(expected.intervals)):
        raise PackagedLibraryError(
            f"The {preset} prepared picture does not match the app's complete cover schedule. "
            "Prepare the title with the required profile union and timing before exporting."
        )


def _caption(prepared: Path, staged: Path, relative: str) -> tuple[dict | None, int]:
    probe = probe_video(prepared)
    if not probe.subtitle_streams:
        return None, 0
    first = probe.subtitle_streams[0]
    if first.codec_name not in {"mov_text", "subrip", "webvtt", "ass", "ssa"}:
        raise PackagedLibraryError("The prepared caption stream cannot be exported as checked text.")
    destination = staged / relative
    # Use a file output rather than retaining an unbounded subprocess stdout.
    run_ffmpeg(["-i", str(prepared), "-map", "0:s:0", "-f", "webvtt",
                "-fs", str(MAX_CAPTION_BYTES + 1), str(destination)])
    _bounded_file(destination, staged, MAX_CAPTION_BYTES)
    text = destination.read_text()
    if not text.startswith("WEBVTT") or "-->" not in text or "\x00" in text:
        raise PackagedLibraryError("The prepared subtitle stream did not produce valid text cues.")
    language = first.language or "und"
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?", language):
        language = "und"
    if language in {"eng", "en"}:
        language, label = "en", "English"
    else:
        label = "Captions" if language == "und" else f"Captions ({language})"
    return {"path": relative, "sha256": sha256_file(destination), "label": label,
            "language": language, "mimeType": "text/vtt"}, destination.stat().st_size


def _title(receipt: dict, root: Path, staged: Path, public, files: dict, reports: dict) -> tuple[dict, int]:
    sha = receipt["source_sha256"]
    if receipt["presets"] != list(PRESETS):
        raise PackagedLibraryError("A packaged title needs all three verified preparation presets.")
    if not local._still_ready(receipt, root, sha):
        raise PackagedLibraryError("A local receipt is no longer ready; prepare it again.")
    layout = TitleLayout(root, sha)
    entry = read_entry(layout.entry_path)
    duration = entry.duration_s * 1000
    if not math.isfinite(duration) or duration <= 0 or duration > 24 * 60 * 60 * 1000:
        raise PackagedLibraryError("The prepared title has an invalid duration.")
    report_bytes = _read_report(layout.verify_report_path)
    report = json.loads(report_bytes)
    maps, map_entries, renditions = {}, {}, {}
    total = 0
    for preset in PRESETS:
        path = _bounded_file(layout.map_path(preset), root, MAX_MAP_BYTES)
        document = load_map(path)
        _check_map_signature(document.raw, public, path)
        if (document.source_sha256 != sha or document.profile != ("broadcast" if preset == "broadcast" else "wcag")):
            raise PackagedLibraryError("An authenticated map belongs to the wrong source or profile.")
        maps[preset] = document
        relative = f"titles/{sha}/{preset}.json"
        expected = receipt["artifacts"][preset]["sha256"][str(path.relative_to(root))]
        total += _copy_checked(path, staged / relative, expected, root)
        text = (staged / relative).read_text()
        files[relative] = expected
        map_entries[preset] = {"path": relative, "sha256": expected, "text": text}
    for preset in PRESETS:
        require_runtime_plan(layout, maps, preset, duration)
        path = layout.safe_master(preset)
        relative = f"titles/{sha}/{preset}.mp4"
        expected = receipt["artifacts"][preset]["sha256"][str(path.relative_to(root))]
        total += _copy_checked(path, staged / relative, expected, root)
        files[relative] = expected
        offsets = [check["data"].get("start_offset_ms") for check in report["checks"]
                   if check["name"] == f"rendition_matches_source:{preset}"]
        if (len(offsets) != 1 or isinstance(offsets[0], bool)
                or not isinstance(offsets[0], (int, float)) or not math.isfinite(offsets[0])
                or abs(offsets[0]) > START_OFFSET_LIMIT_MS):
            raise PackagedLibraryError("The verified rendition is missing its measured start offset.")
        probe = probe_video(staged / relative)
        guard, minimum = TIMING[preset]
        rendition = {"path": relative, "sha256": expected, "durationMs": probe.duration_ms,
                     "startOffsetMs": offsets[0], "guardBandMs": guard, "minCoverMs": minimum}
        caption, size = _caption(staged / relative, staged, f"titles/{sha}/{preset}.vtt")
        total += size
        if caption is not None:
            files[caption["path"]] = caption["sha256"]
            rendition["captions"] = [caption]
        renditions[preset] = rendition
    # Recheck the receipt after every read and subtitle extraction. Cooperating
    # imports are locked out; an unrelated workspace mutation still refuses.
    if not local._still_ready(receipt, root, sha):
        raise PackagedLibraryError("The verified preparation changed during export.")
    verification = receipt["verification"]
    title = {"id": f"prepared-{sha}", "title": receipt["title"], "sourceSha256": sha,
            "durationMs": duration, "maps": map_entries, "renditions": renditions,
            "verification": {"reportSha256": verification["report_sha256"],
                             "checkedInputsSha256": verification["checked_inputs_sha256"],
                             "outcome": verification["outcome"]}}
    _check_report(report_bytes, verification["report_sha256"], [title])
    reports[verification["report_sha256"]] = report_bytes
    return title, total


def _replace_text(path: Path, text: str, root: Path) -> None:
    local._path_inside(path, root)
    if path.exists():
        local._file(path, root)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=root,
                                         prefix=".publish-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _check_output_root(destination: Path, *, staging: Path | None = None,
                       require_reports: bool = False) -> int:
    """Vega packages this whole directory, including retained generations."""
    total = 0
    names = sorted(destination.iterdir())
    if len(names) > MAX_TITLES + 5:
        raise PackagedLibraryError("Too many retained package generations; use a fresh output directory.")
    for path in names:
        if path == staging:
            continue
        local._path_inside(path, destination)
        if path.name == "reports":
            continue
        if path.name in {"catalog.json", "catalog.ts", ".local-library.lock"}:
            limit = 0 if path.name == ".local-library.lock" else MAX_CATALOG_BYTES * 2
            _bounded_file(path, destination, limit)
            total += path.stat().st_size
            continue
        if not _SHA.fullmatch(path.name) or not path.is_dir():
            raise PackagedLibraryError("An unexpected file is present in the package output directory.")
        proof = _bounded_file(path / "manifest.json", destination, MAX_CATALOG_BYTES)
        document = json.loads(proof.read_text())
        if not isinstance(document, dict) or document.get("bundleId") != path.name:
            raise PackagedLibraryError("A retained generation has an invalid manifest identity.")
        _check_bundle(document, path)
        total += sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
        if total > MAX_BUNDLE_BYTES:
            raise PackagedLibraryError("Retained package generations exceed the byte budget; use a fresh output directory.")
    report_size, _ = _check_reports(destination, _report_references(destination), require_reports=require_reports)
    total += report_size
    if total > MAX_BUNDLE_BYTES:
        raise PackagedLibraryError("The full package output exceeds its byte budget.")
    return total


def export_packaged_library(workdir: str | Path, output: str | Path, *, pub: str | Path,
                           source_shas: Sequence[str] | None = None) -> dict:
    root, destination = _root(workdir), _root(output)
    if destination == root or destination.is_relative_to(root) or root.is_relative_to(destination):
        raise PackagedLibraryError("The package output and preparation workspace must be separate.")
    public = load_public_key(pub)
    public_raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    selected = set(source_shas) if source_shas is not None else None
    if selected is not None and (not selected or any(not _SHA.fullmatch(sha) for sha in selected)):
        raise PackagedLibraryError("Select complete source SHA-256 identifiers.")
    destination.mkdir(parents=True, exist_ok=True)
    with local._lock(root), local._lock(destination):
        _check_output_root(destination)
        catalog = local._snapshot(root)
        receipts = [item for item in catalog["titles"] if selected is None or item["source_sha256"] in selected]
        if selected is not None and {item["source_sha256"] for item in receipts} != selected:
            raise PackagedLibraryError("A selected title has no current verified local receipt.")
        if not receipts or len(receipts) > MAX_TITLES:
            raise PackagedLibraryError("Export between one and sixteen verified local titles.")
        with tempfile.TemporaryDirectory(prefix=".stage-", dir=destination) as temporary:
            staged = Path(temporary)
            files, titles, reports, total = {}, [], {}, 0
            for receipt in receipts:
                title, size = _title(receipt, root, staged, public, files, reports)
                total += size
                if total > MAX_BUNDLE_BYTES:
                    raise PackagedLibraryError("The prepared library exceeds the package byte budget.")
                titles.append(title)
            manifest = {"version": VERSION, "assetRoot": ASSET_ROOT,
                        "publicKeyBase64": base64.b64encode(public_raw).decode(),
                        "titles": titles, "files": files}
            manifest["bundleId"] = fingerprint(manifest)
            text = _json_text(manifest)
            if len(text.encode()) > MAX_CATALOG_BYTES:
                raise PackagedLibraryError("The packaged catalog exceeds its byte budget.")
            (staged / "manifest.json").write_text(text)
            _check_bundle(manifest, staged)
            immutable = destination / manifest["bundleId"]
            local._path_inside(immutable, destination)
            existing_size = _check_output_root(destination, staging=staged)
            pointer_size = sum(path.stat().st_size for path in
                               (destination / "catalog.json", destination / "catalog.ts")
                               if path.exists())
            staged_size = sum(path.stat().st_size for path in staged.rglob("*") if path.is_file())
            projected = (existing_size - pointer_size + len(text.encode())
                         + len(catalog_module(text).encode())
                         + (0 if immutable.exists() else staged_size)
                         + sum(len(raw) for digest, raw in reports.items()
                               if not (destination / "reports" / f"{digest}.json").exists()))
            if projected > MAX_BUNDLE_BYTES:
                raise PackagedLibraryError("The full package output exceeds its byte budget; use a fresh output directory.")
            if immutable.exists():
                _check_bundle(manifest, immutable)
            else:
                os.rename(staged, immutable)
                # TemporaryDirectory owns only its original path, not the committed bundle.
                staged.mkdir()
            # Reports stay outside manifests so existing catalog, signed map and
            # rendition identities remain unchanged. They are content addressed
            # by the verification reference the export already records.
            _publish_reports(destination, reports, _report_references(destination), projected_total=projected)
            # The module is the app's sole entrypoint and is published last.
            # Older complete bundles are retained while a previous app build may reference them.
            _replace_text(destination / "catalog.json", text, destination)
            _replace_text(destination / "catalog.ts", catalog_module(text), destination)
            return manifest


def _check_bundle(manifest: dict, bundle: Path) -> None:
    body = {key: value for key, value in manifest.items() if key != "bundleId"}
    if (set(manifest) != {"version", "assetRoot", "bundleId", "publicKeyBase64", "titles", "files"}
            or manifest.get("version") != VERSION or manifest.get("assetRoot") != ASSET_ROOT
            or not _SHA.fullmatch(manifest.get("bundleId", ""))
            or fingerprint(body) != manifest["bundleId"]):
        raise PackagedLibraryError("The packaged manifest identity is invalid.")
    files = manifest.get("files")
    if not isinstance(files, dict) or len(files) > MAX_TITLES * 9:
        raise PackagedLibraryError("The packaged artifact allowlist is invalid.")
    expected = set(files) | {"manifest.json"}
    actual = set()
    total = 0
    for directory, directories, names in os.walk(bundle, followlinks=False):
        for name in directories:
            local._path_inside(Path(directory) / name, bundle)
        for name in names:
            path = local._file(Path(directory) / name, bundle)
            relative = path.relative_to(bundle).as_posix()
            actual.add(relative)
            if relative == "manifest.json":
                if _bounded_file(path, bundle, MAX_CATALOG_BYTES).read_text() != _json_text(manifest):
                    raise PackagedLibraryError("The packaged manifest bytes differ from the catalog.")
                continue
            if (not _PATH.fullmatch(relative) or relative not in files
                    or not isinstance(files[relative], str) or not _SHA.fullmatch(files[relative])):
                raise PackagedLibraryError("An unexpected asset is present in the packaged library.")
            total += path.stat().st_size
            if total > MAX_BUNDLE_BYTES or sha256_file(path) != files[relative]:
                raise PackagedLibraryError("A packaged artifact differs from the verified export.")
    if actual != expected:
        raise PackagedLibraryError("The packaged library is incomplete.")
    titles = manifest.get("titles")
    if not isinstance(titles, list) or not titles or len(titles) > MAX_TITLES:
        raise PackagedLibraryError("The packaged title list is invalid.")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        raw = base64.b64decode(manifest["publicKeyBase64"], validate=True)
        public = Ed25519PublicKey.from_public_bytes(raw)
    except (KeyError, TypeError, ValueError) as exc:
        raise PackagedLibraryError("The packaged signer is invalid.") from exc
    referenced, seen = set(), set()
    for title in titles:
        if (not isinstance(title, dict) or set(title) != {
                "id", "title", "sourceSha256", "durationMs", "maps", "renditions", "verification"}
                or not isinstance(title.get("title"), str) or not title["title"].strip()
                or len(title["title"]) > 200 or not _positive_time(title.get("durationMs"))):
            raise PackagedLibraryError("A packaged title has invalid metadata.")
        sha = title.get("sourceSha256", "")
        if not _SHA.fullmatch(sha) or sha in seen or title.get("id") != f"prepared-{sha}":
            raise PackagedLibraryError("The packaged title identity is invalid.")
        seen.add(sha)
        _verification_metadata(title)
        if set(title.get("maps", {})) != set(PRESETS) or set(title.get("renditions", {})) != set(PRESETS):
            raise PackagedLibraryError("A packaged title is missing a required preset.")
        for preset in PRESETS:
            mapped, rendition = title["maps"][preset], title["renditions"][preset]
            if (not isinstance(mapped, dict) or set(mapped) != {"path", "sha256", "text"}
                    or not isinstance(rendition, dict)
                    or not {"path", "sha256", "durationMs", "startOffsetMs", "guardBandMs", "minCoverMs"}.issubset(rendition)
                    or set(rendition) - {"path", "sha256", "durationMs", "startOffsetMs", "guardBandMs", "minCoverMs", "captions"}
                    or not _positive_time(rendition.get("durationMs"))):
                raise PackagedLibraryError("A packaged rendition has invalid metadata.")
            for record, extension in ((mapped, "json"), (rendition, "mp4")):
                relative = f"titles/{sha}/{preset}.{extension}"
                if record.get("path") != relative or record.get("sha256") != files.get(relative):
                    raise PackagedLibraryError("A title points outside its exact packaged artifacts.")
                referenced.add(relative)
            map_path = bundle / mapped["path"]
            if _bounded_file(map_path, bundle, MAX_MAP_BYTES).read_text() != mapped.get("text"):
                raise PackagedLibraryError("Compiled map text differs from the packaged map bytes.")
            document = parse_map(json.loads(mapped["text"]))
            _check_map_signature(document.raw, public, map_path)
            if document.source_sha256 != sha or document.profile != ("broadcast" if preset == "broadcast" else "wcag"):
                raise PackagedLibraryError("A packaged map belongs to another source or profile.")
            guard, minimum = TIMING[preset]
            offset = rendition.get("startOffsetMs")
            if (rendition.get("guardBandMs") != guard or rendition.get("minCoverMs") != minimum
                    or isinstance(offset, bool) or not isinstance(offset, (int, float))
                    or not math.isfinite(offset) or abs(offset) > START_OFFSET_LIMIT_MS):
                raise PackagedLibraryError("The packaged rendition timing is invalid.")
            captions = rendition.get("captions", [])
            if not isinstance(captions, list) or len(captions) > 1:
                raise PackagedLibraryError("The packaged caption list is invalid.")
            for caption in captions:
                relative = f"titles/{sha}/{preset}.vtt"
                if (not isinstance(caption, dict) or set(caption) != {"path", "sha256", "mimeType", "language", "label"}
                        or caption.get("path") != relative or caption.get("sha256") != files.get(relative)
                        or not isinstance(caption.get("label"), str) or not caption["label"].strip()
                        or len(caption["label"]) > 80 or not isinstance(caption.get("language"), str)
                        or not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?", caption["language"])
                        or caption.get("mimeType") != "text/vtt"):
                    raise PackagedLibraryError("A caption points outside its checked packaged text.")
                _bounded_file(bundle / relative, bundle, MAX_CAPTION_BYTES)
                referenced.add(relative)
    if referenced != set(files):
        raise PackagedLibraryError("The package contains an unreferenced artifact.")


def _positive_time(value) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and 0 < value <= 24 * 60 * 60 * 1000)


def check_packaged_library(output: str | Path, *, require_reports: bool = False) -> dict:
    destination = _root(output)
    path = _bounded_file(destination / "catalog.json", destination, MAX_CATALOG_BYTES)
    text = path.read_text()
    manifest = json.loads(text)
    if text == '{"version":1,"titles":[]}':
        module = _bounded_file(destination / "catalog.ts", destination, MAX_CATALOG_BYTES * 2)
        if module.read_text() != catalog_module(text):
            raise PackagedLibraryError("The empty compiled catalog differs from its sentinel.")
        if any(path.name not in {"catalog.json", "catalog.ts", ".local-library.lock"}
               for path in destination.iterdir()):
            raise PackagedLibraryError("An empty library must not carry bundled media.")
        _check_output_root(destination)
        return manifest
    if not isinstance(manifest, dict) or text != _json_text(manifest):
        raise PackagedLibraryError("The packaged catalog is not canonical export text.")
    module = _bounded_file(destination / "catalog.ts", destination, MAX_CATALOG_BYTES * 2)
    if module.read_text() != catalog_module(text):
        raise PackagedLibraryError("The compiled catalog does not match the checked manifest.")
    bundle_id = manifest.get("bundleId", "")
    if not isinstance(bundle_id, str) or not _SHA.fullmatch(bundle_id):
        raise PackagedLibraryError("The packaged bundle identifier is invalid.")
    bundle = local._path_inside(destination / bundle_id, destination)
    _check_bundle(manifest, bundle)
    _check_output_root(destination, require_reports=require_reports)
    return manifest


def verification_report_status(output: str | Path, *, require_reports: bool = False) -> dict:
    destination = _root(output)
    check_packaged_library(destination, require_reports=require_reports)
    return _check_reports(destination, _report_references(destination), require_reports=require_reports)[1]


def attach_reports(output: str | Path, reports: Sequence[str | Path]) -> dict:
    """Attach existing original reports without rewriting a catalog or media asset."""
    destination = _root(output)
    if not reports:
        raise PackagedLibraryError("Supply at least one original verification report.")
    # Do not create a new library when the caller supplied an incorrect path.
    check_packaged_library(destination)
    with local._lock(destination):
        manifest = check_packaged_library(destination)
        references = _report_references(destination)
        candidates = {}
        for path in reports:
            raw = _read_report(Path(path))
            candidates[hashlib.sha256(raw).hexdigest()] = raw
        _publish_reports(destination, candidates, references)
        return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    export = actions.add_parser("export")
    export.add_argument("--workdir", required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--pub", required=True)
    export.add_argument("--source-sha", action="append")
    check = actions.add_parser("check")
    check.add_argument("--output", required=True)
    check.add_argument("--require-reports", action="store_true")
    attach = actions.add_parser("attach-reports")
    attach.add_argument("--output", required=True)
    attach.add_argument("--report", required=True, action="append")
    args = parser.parse_args(argv)
    try:
        if args.action == "check":
            manifest = check_packaged_library(args.output, require_reports=args.require_reports)
        elif args.action == "attach-reports":
            manifest = attach_reports(args.output, args.report)
        else:
            manifest = export_packaged_library(args.workdir, args.output, pub=args.pub,
                                               source_shas=args.source_sha)
        print(json.dumps({"version": VERSION, "status": "ready", "bundleId": manifest.get("bundleId"),
                          "titles": len(manifest["titles"]), "physical_tv_validated": False,
                          "verification_reports": verification_report_status(args.output)}))
        return 0
    except (PipelineError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"version": VERSION, "status": "failed", "message": (
            str(exc) if isinstance(exc, PackagedLibraryError)
            else "The prepared library could not be exported or checked.")}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
