"""Prepare a local video and issue a receipt for checked renditions only.

This wraps the existing pipeline; it does not analyze, serve, play or deploy
anything itself. A local receipt is not a playback signature check, a clinical
claim, a connection to the app shelf or evidence from a physical television.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Iterator, Sequence

from . import PipelineError
from .catalog import STATUS_VERIFIED, read_entry
from .flashmap_adapter import PRESETS, FlashmapAdapter, iter_presets
from .hashing import fingerprint, sha256_file
from .ingest import IngestOptions, IngestResult, ingest_title
from .layout import TitleLayout
from .state import Ledger
from .verify import VerifyReport

VERSION = 1
CATALOG_NAME = "local-library.json"
RECEIPTS_DIR = "local-receipts"
MAX_TITLES = 256
MAX_TITLE_FILES = 20_000
MAX_METADATA_BYTES = 4 * 1024 * 1024
READY_MESSAGE = "ready for local playback of the prepared rendition"
_SHA = re.compile(r"[0-9a-f]{64}")
_HLS_NAME = re.compile(
    r"(?:master\.m3u8|stream_[0-9]+(?:_vtt)?\.m3u8|"
    r"seg_[0-9]+_[0-9]+\.ts|stream_[0-9]+\.vtt)"
)
_CORE_CHECKS = (
    "map_hash", "map_signature", "plan_matches_map", "safe_rendition_clean",
    "rendition_matches_source", "cover_proof", "cover_model_clean",
    "hls_rendition_clean", "hls_timing_matches_master",
)
_NEXT_STEPS = [
    "Read the verification report and its outcome before choosing a rendition.",
    "Use only artifacts[preset].safe_master or its prepared HLS playlist locally.",
    "Do not play the original source or the cover model. Nothing opens automatically.",
    "The app shelf is not connected to this receipt. TV composition still needs measurement.",
]
_RECEIPT_KEYS = {
    "version", "status", "readiness", "source_sha256", "title", "presets",
    "artifacts", "verification", "app_shelf_connected", "physical_tv_validated", "next_steps",
}
_VERIFICATION_KEYS = {
    "status", "outcome", "report", "report_sha256", "checked_inputs_sha256", "failed_checks",
}


class LocalLibraryError(PipelineError):
    """An actionable wrapper error whose message contains no analyzer stderr."""


def _presets(values: Sequence[str] | None) -> list[str]:
    try:
        requested = iter_presets(values)
    except PipelineError as exc:
        raise LocalLibraryError("Choose wcag, broadcast or extra-cautious presets.") from exc
    if not requested:
        raise LocalLibraryError("Choose at least one supported preset.")
    return [preset for preset in PRESETS if preset in requested]


def _path_inside(path: Path, root: Path) -> Path:
    """No publication or write may follow an existing workspace symlink."""
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise LocalLibraryError("An artifact path is outside the local workspace.") from exc
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise LocalLibraryError("A local artifact or directory is a symlink.")
        cursor = cursor.parent
    if path.resolve().is_relative_to(root):
        return path
    raise LocalLibraryError("An artifact resolves outside the local workspace.")


def _file(path: Path, root: Path) -> Path:
    _path_inside(path, root)
    if not path.is_file() or path.stat().st_nlink != 1:
        raise LocalLibraryError("A required artifact is missing or is not an owned regular file.")
    return path


def _json(path: Path, root: Path) -> dict:
    _file(path, root)
    if path.stat().st_size > MAX_METADATA_BYTES:
        raise LocalLibraryError("Local receipt metadata is too large.")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise LocalLibraryError("Local receipt metadata is not an object.")
    return data


def _write_json(path: Path, value: dict, root: Path) -> None:
    _path_inside(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique temporary files avoid following a planted fixed .tmp symlink.
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextlib.contextmanager
def _lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".local-library.lock"
    _path_inside(path, root)
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        if os.fstat(descriptor).st_nlink != 1:
            raise LocalLibraryError("The local workspace lock is not an owned file.")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LocalLibraryError("This local workspace is busy. Retry after its import finishes.") from exc
        yield
    finally:
        os.close(descriptor)


def _workspace_files(layout: TitleLayout) -> list[Path]:
    """Bound input bookkeeping and reject unsafe existing paths before ingest."""
    root = layout.workdir
    _path_inside(layout.root, root)
    files: list[Path] = []
    if not layout.root.exists():
        return files
    for directory, directories, names in os.walk(layout.root, followlinks=False):
        for name in directories:
            _path_inside(Path(directory) / name, root)
        for name in names:
            path = _file(Path(directory) / name, root)
            files.append(path)
            if len(files) > MAX_TITLE_FILES:
                raise LocalLibraryError("This title has too many workspace files.")
    return sorted(files)


def _inputs_digest(layout: TitleLayout) -> str:
    # These files include the source-bound maps, plans, cover models, previews,
    # report and ledger. Only the digest leaves the workspace, not their paths.
    return fingerprint({
        str(path.relative_to(layout.root)): sha256_file(path)
        for path in _workspace_files(layout)
    })


def _hls_files(layout: TitleLayout, preset: str) -> list[Path]:
    directory = layout.hls_dir(preset)
    _path_inside(directory, layout.workdir)
    paths = sorted(directory.iterdir())
    if not paths or len(paths) > MAX_TITLE_FILES:
        raise LocalLibraryError("The prepared HLS output is absent or too large.")
    for path in paths:
        if not _HLS_NAME.fullmatch(path.name):
            raise LocalLibraryError("An unexpected file is present in prepared HLS output.")
        _file(path, layout.workdir)
    names = {path.name for path in paths}
    if "master.m3u8" not in names:
        raise LocalLibraryError("The prepared HLS master playlist is missing.")
    for playlist in (path for path in paths if path.suffix == ".m3u8"):
        text = playlist.read_text()
        references = re.findall(r'URI="([^"]+)"', text)
        references += [line.strip() for line in text.splitlines()
                       if line.strip() and not line.startswith("#")]
        if any(not _HLS_NAME.fullmatch(name) or name not in names for name in references):
            raise LocalLibraryError("An HLS reference leaves the checked output allowlist.")
    return paths


def _artifacts(layout: TitleLayout, presets: list[str]) -> dict:
    root = layout.workdir
    result: dict = {}
    for preset in presets:
        paths = [layout.safe_master(preset), layout.map_path(preset),
                 layout.master_playlist(preset), *_hls_files(layout, preset)]
        hashes = {str(path.relative_to(root)): sha256_file(_file(path, root))
                  for path in sorted(set(paths))}
        result[preset] = {
            "safe_master": str(layout.safe_master(preset).relative_to(root)),
            "master_playlist": str(layout.master_playlist(preset).relative_to(root)),
            "map": str(layout.map_path(preset).relative_to(root)),
            "sha256": hashes,
        }
    return result


def _verification(layout: TitleLayout, presets: list[str]) -> tuple[dict, VerifyReport]:
    data = _json(layout.verify_report_path, layout.workdir)
    checks = data.get("checks")
    if (data.get("sha256") != layout.sha256 or data.get("presets") != presets
            or data.get("passed") is not True or not isinstance(checks, list) or not checks
            or any(not isinstance(check, dict) or check.get("passed") is not True
                   for check in checks)):
        raise LocalLibraryError("Verification did not pass for this source and every requested preset.")
    names = [check.get("name") for check in checks]
    required = {"source_hash"} | {f"{name}:{preset}" for preset in presets for name in _CORE_CHECKS}
    if (any(not isinstance(name, str) for name in names) or len(set(names)) != len(names)
            or not required.issubset(names)):
        raise LocalLibraryError("Verification is incomplete for the requested presets.")
    report = VerifyReport.from_dict(data)
    record = Ledger(layout.root).get("verify")
    if (record is None or record.extra.get("passed") is not True
            or record.extra.get("report_sha256") != sha256_file(layout.verify_report_path)):
        raise LocalLibraryError("The verification report does not match the pipeline's recorded result.")
    return data, report


def _checked_entry(layout: TitleLayout, presets: list[str]) -> None:
    _file(layout.entry_path, layout.workdir)
    entry = read_entry(layout.entry_path)
    if (entry.sha256 != layout.sha256 or entry.verified is not True
            or entry.status != STATUS_VERIFIED or set(entry.renditions) != set(presets)
            or entry.verify_report != str(layout.verify_report_path)):
        raise LocalLibraryError("The prepared catalog entry is incomplete or not verified.")
    for preset in presets:
        rendition = entry.renditions[preset]
        expected = (layout.safe_master(preset), layout.master_playlist(preset), layout.map_path(preset))
        actual = (rendition.safe_master, rendition.master_playlist, rendition.map_path)
        if actual != tuple(str(path) for path in expected):
            raise LocalLibraryError("The catalog points outside the intended prepared artifacts.")


def _ready_receipt(result: IngestResult, source: Path, root: Path,
                   presets: list[str], title: str) -> dict:
    layout = TitleLayout(root, sha256_file(source))
    if (result.sha256 != layout.sha256 or result.verify_passed is not True
            or result.layout.root != layout.root or not result.publishable):
        raise LocalLibraryError("The pipeline did not return a verified result for this source.")
    data, report = _verification(layout, presets)
    # The verifier's geometry data uses tuples in memory; JSON records arrays.
    # Compare their JSON representations, without coercing unsupported objects.
    recorded_result = json.loads(json.dumps(result.verify_report, allow_nan=False))
    if recorded_result != data or Path(report.source_path).resolve() != source:
        raise LocalLibraryError("The verification result belongs to a different preparation.")
    _checked_entry(layout, presets)
    return {
        "version": VERSION, "status": "ready", "readiness": READY_MESSAGE,
        "source_sha256": layout.sha256, "title": title, "presets": presets,
        "artifacts": _artifacts(layout, presets),
        "verification": {
            "status": "passed", "outcome": report.outcome,
            "report": str(layout.verify_report_path.relative_to(root)),
            "report_sha256": sha256_file(layout.verify_report_path),
            "checked_inputs_sha256": _inputs_digest(layout),
            "failed_checks": [],
        },
        "app_shelf_connected": False, "physical_tv_validated": False,
        "next_steps": list(_NEXT_STEPS),
    }


def _still_ready(receipt: dict, root: Path, expected_sha: str) -> bool:
    try:
        presets = receipt.get("presets")
        if (set(receipt) != _RECEIPT_KEYS or receipt.get("version") != VERSION
                or receipt.get("status") != "ready" or receipt.get("readiness") != READY_MESSAGE
                or not isinstance(receipt.get("title"), str) or not receipt["title"].strip()
                or len(receipt["title"]) > 200 or receipt.get("next_steps") != _NEXT_STEPS
                or receipt.get("source_sha256") != expected_sha
                or not isinstance(presets, list) or presets != _presets(presets)):
            return False
        layout = TitleLayout(root, expected_sha)
        _checked_entry(layout, presets)
        _, report = _verification(layout, presets)
        verification = receipt.get("verification", {})
        return (
            set(verification) == _VERIFICATION_KEYS
            and verification.get("status") == "passed"
            and verification.get("failed_checks") == []
            and verification.get("outcome") == report.outcome
            and verification.get("report") == str(layout.verify_report_path.relative_to(root))
            and verification.get("report_sha256") == sha256_file(layout.verify_report_path)
            and verification.get("checked_inputs_sha256") == _inputs_digest(layout)
            and receipt.get("artifacts") == _artifacts(layout, presets)
            and receipt.get("app_shelf_connected") is False
            and receipt.get("physical_tv_validated") is False
        )
    except (PipelineError, OSError, ValueError, TypeError, KeyError, AttributeError):
        return False


def _snapshot(root: Path) -> dict:
    directory = _path_inside(root / RECEIPTS_DIR, root)
    titles: list[dict] = []
    if directory.exists():
        paths = sorted(directory.iterdir())
        if len(paths) > MAX_TITLES:
            raise LocalLibraryError("The local library has too many receipts.")
        for path in paths:
            if path.suffix != ".json" or not _SHA.fullmatch(path.stem):
                continue
            try:
                receipt = _json(path, root)
            except (PipelineError, OSError, ValueError):
                continue
            if _still_ready(receipt, root, path.stem):
                titles.append(receipt)
    catalog = {"version": VERSION, "scope": "prepared_local_renditions_only", "titles": titles}
    _write_json(root / CATALOG_NAME, catalog, root)
    return catalog


def refresh_local_catalog(workdir: str | Path) -> dict:
    """Recheck receipt inputs and rebuild the verified-only local snapshot."""
    root = Path(workdir).resolve()
    with _lock(root):
        return _snapshot(root)


def prepare_local_title(source: str | Path, workdir: str | Path, *,
                        key: str | Path, pub: str | Path,
                        presets: Sequence[str] | None = None, title: str | None = None,
                        adapter: FlashmapAdapter | None = None) -> dict:
    """One source, required external keys, normal pipeline verify, one receipt."""
    source = Path(source).resolve()
    root = Path(workdir).resolve()
    requested = _presets(presets)
    name = (title if title is not None else source.stem).strip()
    if not name or len(name) > 200:
        raise LocalLibraryError("Use a nonempty title of at most 200 characters.")
    with _lock(root):
        if not source.is_file() or source.is_relative_to(root):
            raise LocalLibraryError("Choose an existing source file outside the artifact workspace.")
        sha = sha256_file(source)
        receipt_path = root / RECEIPTS_DIR / f"{sha}.json"
        receipt = {
            "version": VERSION, "status": "failed", "source_sha256": sha,
            "title": name, "presets": requested, "artifacts": {},
            "verification": {"status": "not_completed", "failed_checks": []},
            "app_shelf_connected": False, "physical_tv_validated": False,
            "next_steps": ["Fix the preparation error and run this local import again."],
        }
        # Withdraw a previous ready receipt before touching any pipeline state.
        _write_json(receipt_path, receipt, root)
        _snapshot(root)
        try:
            for label, value in (("signing", key), ("public", pub)):
                path = Path(value).resolve()
                if not path.is_file() or path.is_relative_to(root):
                    raise LocalLibraryError(f"Keep the {label} key in an existing file outside the artifact workspace.")
            layout = TitleLayout(root, sha)
            # The pipeline's shared catalog has fixed temporary paths outside
            # the title subtree. Check those too before its existing writer runs.
            for path in (layout.index_path, layout.index_path.with_suffix(".json.tmp")):
                if path.exists() or path.is_symlink():
                    _file(path, root)
            _workspace_files(layout)
            result = ingest_title(
                source, root,
                IngestOptions(presets=requested, key=str(Path(key).resolve()),
                              pub=str(Path(pub).resolve()), title=name, skip_verify=False),
                adapter=adapter,
            )
            if result.verify_report is not None and result.verify_passed is not True:
                receipt["verification"] = {
                    "status": "failed", "failed_checks": [
                        {"name": check.get("name", "")}
                        for check in result.verify_report.get("checks", [])
                        if check.get("passed") is not True
                    ],
                }
            receipt = _ready_receipt(result, source, root, requested, name)
        except (PipelineError, OSError, ValueError, TypeError, KeyError) as exc:
            # Do not copy analyzer stderr, command lines, key paths or key bytes
            # into the receipt. Detailed measurement evidence stays in report.json.
            receipt["error"] = {"type": type(exc).__name__, "message": (
                str(exc) if isinstance(exc, LocalLibraryError)
                else "Preparation could not complete. Check the input, keys and workspace files."
            )}
        _write_json(receipt_path, receipt, root)
        _snapshot(root)
        return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue a local library receipt for prepared renditions.")
    subcommands = parser.add_subparsers(dest="action", required=True)
    prepare = subcommands.add_parser("prepare", help="Prepare and verify one local video.")
    prepare.add_argument("source")
    prepare.add_argument("--workdir", required=True)
    prepare.add_argument("--key", required=True)
    prepare.add_argument("--pub", required=True)
    prepare.add_argument("--title")
    prepare.add_argument("--presets", default=",".join(PRESETS))
    catalog = subcommands.add_parser("catalog", help="Recheck receipts and refresh the local snapshot.")
    catalog.add_argument("--workdir", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "catalog":
            result = refresh_local_catalog(args.workdir)
        else:
            result = prepare_local_title(
                args.source, args.workdir, key=args.key, pub=args.pub, title=args.title,
                presets=args.presets.split(","),
            )
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0 if args.action == "catalog" or result["status"] == "ready" else 1
    except (PipelineError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"version": VERSION, "status": "failed", "artifacts": {},
                          "error": {"type": type(exc).__name__,
                                    "message": str(exc) if isinstance(exc, LocalLibraryError)
                                    else "The local workspace could not be opened."}}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
