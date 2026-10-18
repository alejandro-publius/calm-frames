"""Read-only package validation and revocable operator handoff, never TV installation.

Only review receipts are written to a separate staging directory. Packages, approval
records, signers and app assets remain unchanged. A passing signature proves integrity
under the package's declared key; exact build approval is a separate decision.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import time
import uuid
from pathlib import Path

from . import PipelineError
from .hashing import fingerprint, sha256_file
from .local_library import _file, _json, _lock, _path_inside, _write_json
from .packaged_library import check_packaged_library

APP = Path(__file__).resolve().parents[1] / "app"
SHA = re.compile(r"[0-9a-f]{64}")
TICKET = re.compile(r"[0-9a-f]{32}")
MAX_TICKETS = 64


class DeliveryError(PipelineError):
    pass


def approvals() -> list[dict]:
    path = APP / "config/approved-prepared-libraries.json"
    if path.stat().st_size > 65536:
        raise DeliveryError("The exact-approval registry is too large.")
    value = json.loads(path.read_text())
    if (not isinstance(value, dict) or set(value) != {"version", "catalogs"}
            or value["version"] != 1 or not isinstance(value["catalogs"], list)
            or len(value["catalogs"]) > 16):
        raise DeliveryError("The exact-approval registry is invalid.")
    seen = set()
    for entry in value["catalogs"]:
        if (not isinstance(entry, dict) or set(entry) != {
                "bundleId", "catalogSha256", "publicKeyFingerprint", "consumer", "label",
                "approvalReference"}
                or any(not isinstance(entry[k], str) or not SHA.fullmatch(entry[k])
                       for k in ["bundleId", "catalogSha256", "publicKeyFingerprint"])
                or type(entry["consumer"]) is not bool
                or any(not isinstance(entry[k], str) or not entry[k].strip()
                       or len(entry[k]) > 300 for k in ["label", "approvalReference"])
                or entry["bundleId"] in seen):
            raise DeliveryError("The exact-approval registry has an invalid or repeated record.")
        seen.add(entry["bundleId"])
    return value["catalogs"]


def _inventory(directory: Path) -> dict:
    # The strict checker bounds directories, counts, sizes and allowable names first.
    return {str(p.relative_to(directory)): sha256_file(_file(p, directory))
            for p in sorted(directory.rglob("*")) if not p.is_dir()}


def inspect_delivery(directory: Path, expected_source: str) -> dict:
    if not isinstance(expected_source, str) or not SHA.fullmatch(expected_source):
        raise DeliveryError("Choose the complete expected source SHA-256.")
    directory = Path(directory).absolute()
    if directory.resolve() != directory:
        raise DeliveryError("The package path cannot contain symlinks.")
    manifest = check_packaged_library(directory, require_reports=True)
    titles = manifest.get("titles", [])
    selected = [title for title in titles if title["sourceSha256"] == expected_source]
    if len(selected) != 1:
        raise DeliveryError("The package does not contain the selected source identity.")
    inventory = _inventory(directory)
    # A replaced pointer or changed bytes during validation cannot retain readiness.
    if check_packaged_library(directory, require_reports=True) != manifest or _inventory(directory) != inventory:
        raise DeliveryError("The package changed during validation. Check a stable export.")
    catalog_hash = inventory["catalog.json"]
    public_fingerprint = hashlib.sha256(base64.b64decode(manifest["publicKeyBase64"], validate=True)).hexdigest()
    registry = approvals()
    approved = next((entry for entry in registry if
                     entry["bundleId"] == manifest["bundleId"]
                     and entry["catalogSha256"] == catalog_hash
                     and entry["publicKeyFingerprint"] == public_fingerprint), None)
    known_signer = any(entry["publicKeyFingerprint"] == public_fingerprint for entry in registry)
    return {
        "version": 1,
        "state": "approved_for_build" if approved else "ready_for_approval",
        "message": ("Existing exact-approved package; this staging action does not build or install it."
                    if approved else "Verified package ready for exact approval; blocked from TV playback."),
        "approval_label": approved["label"] if approved else None,
        "approval_required": not bool(approved),
        "blockers": [] if approved else [
            "Exact bundle and catalog membership are not approved.",
            *([] if known_signer else ["This public signer is not approved by the current registry."]),
        ],
        "can_watch": False,
        "installed_by_staging": False,
        "package_directory": str(directory),
        "source_sha256": expected_source,
        "title": selected[0]["title"],
        "bundle_id": manifest["bundleId"],
        "catalog_sha256": catalog_hash,
        "public_key_fingerprint": public_fingerprint,
        "approval_request": {
            "bundleId": manifest["bundleId"], "catalogSha256": catalog_hash,
            "publicKeyFingerprint": public_fingerprint,
        },
        "verification": selected[0]["verification"],
        "inventory_sha256": fingerprint(inventory),
        "files": inventory,
    }


def _root(root: Path) -> Path:
    root = Path(root).absolute()
    if root.resolve() != root:
        raise DeliveryError("The staging path cannot contain symlinks.")
    if root == APP or root.is_relative_to(APP):
        raise DeliveryError("Staging receipts must stay outside app assets and source.")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root


def _ticket(root: Path, ticket: str) -> Path:
    if not isinstance(ticket, str) or not TICKET.fullmatch(ticket):
        raise DeliveryError("Invalid delivery review identifier.")
    return _path_inside(root / (ticket + ".json"), root)


def stage_delivery(directory: Path, expected_source: str, root: Path) -> dict:
    root = _root(root)
    directory = Path(directory).absolute()
    if root == directory or root.is_relative_to(directory) or directory.is_relative_to(root):
        raise DeliveryError("Staging receipts and the exported package must be separate.")
    with _lock(root):
        result = inspect_delivery(directory, expected_source)
        tickets = sorted(root.glob("*.json"))
        for path in tickets:
            previous = _json(path, root)
            if (previous.get("state") != "canceled"
                    and previous.get("package_directory") == str(directory)
                    and previous.get("source_sha256") == expected_source):
                if (previous.get("inventory_sha256") != result["inventory_sha256"]
                        or previous.get("catalog_sha256") != result["catalog_sha256"]):
                    raise DeliveryError("This staged package was replaced. Cancel its review before staging again.")
                # Return freshly checked state, never a cached readiness or approval assertion.
                return dict(result, ticket_id=previous["ticket_id"], staged_at=previous["staged_at"])
        if len(tickets) >= MAX_TICKETS:
            raise DeliveryError("This staging workspace has reached its 64-review limit. Use a new workspace.")
        result.update(ticket_id=uuid.uuid4().hex, staged_at=time.time())
        _write_json(_ticket(root, result["ticket_id"]), result, root)
        return result


def check_delivery(root: Path, ticket: str) -> dict:
    root = _root(root)
    with _lock(root):
        previous = _json(_ticket(root, ticket), root)
        if previous.get("state") == "canceled":
            raise DeliveryError("This delivery review was canceled. Stage a fresh review.")
        result = inspect_delivery(Path(previous["package_directory"]), previous["source_sha256"])
        if (result["inventory_sha256"] != previous["inventory_sha256"]
                or result["catalog_sha256"] != previous["catalog_sha256"]):
            raise DeliveryError("The staged package changed. Its old review is no longer valid.")
        return dict(result, ticket_id=ticket, staged_at=previous["staged_at"])


def cancel_delivery(root: Path, ticket: str) -> dict:
    root = _root(root)
    with _lock(root):
        path = _ticket(root, ticket)
        previous = _json(path, root)
        previous.update(state="canceled", can_watch=False,
                        message="Delivery review canceled. Exported files and app library are unchanged.")
        _write_json(path, previous, root)
        return previous


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["inspect", "stage"]:
        command = commands.add_parser(name)
        command.add_argument("--package", type=Path, required=True)
        command.add_argument("--expected-source", required=True)
        if name == "stage":
            command.add_argument("--staging-root", type=Path, required=True)
    for name in ["check", "cancel"]:
        command = commands.add_parser(name)
        command.add_argument("--staging-root", type=Path, required=True)
        command.add_argument("--ticket", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_delivery(args.package, args.expected_source)
        elif args.command == "stage":
            result = stage_delivery(args.package, args.expected_source, args.staging_root)
        elif args.command == "check":
            result = check_delivery(args.staging_root, args.ticket)
        else:
            result = cancel_delivery(args.staging_root, args.ticket)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, PipelineError) as exc:
        print(json.dumps({"state": "blocked", "can_watch": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
