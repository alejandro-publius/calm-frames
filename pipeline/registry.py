"""The map registry: a signed index of published maps, keyed by file hash.

A map is written next to the video it describes, which is enough when the app
already knows where the map is. The registry is for the other case: some Vega
app has a video file, it has hashed it, and it wants to know whether a checked
map for that file exists in a published set at all.

Format: docs/SIDECAR_SPEC.md, section "The registry, version 1". One JSON
object, served beside the maps, keyed by the SHA-256 of the video file, which
is the key the maps are already bound to through ``source.sha256``.

    python -m pipeline.registry MAPS_DIR --out registry.json \\
        --key team_key.pem --pub team_key.pub.pem
    python -m pipeline.registry --check registry.json --pub team_key.pub.pem

Two things this module refuses to do, both for the same reason:

- it will not index a map whose signature does not check out against the public
  key it was given. An index entry is a claim that a checked map exists, so an
  index built from maps nobody checked is a lie told at scale;
- it will not choose between two maps claiming the same file and profile. A
  build either indexes maps that all check out, or it fails and writes nothing.

Reproducible: same maps in, same bytes out. Keys are sorted, paths are stored
relative to the maps directory and sorted, ``created_utc`` comes from the newest
map rather than from the clock, and Ed25519 signatures are deterministic. Two
builds of the same directory on two machines produce the same file, which is
what lets a mirror be compared rather than trusted.

Where the signature check comes from: ``flashmap_adapter`` is the pipeline's one
reader of the map format and it is used here for everything about the format.
It checks a signature by running ``flashmap verify``, which needs the video file
next to the map, and an index is built from a directory of maps with no videos
in sight. So the Ed25519 check itself is done here, over the canonical bytes the
sidecar spec defines, which is the same rule the app's reader follows in
``app/src/calmframes/flashMap.ts``. Nothing here imports flashmap.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from . import PipelineError
from .flashmap_adapter import FlashMapDoc, MapFormatError, load_map
from .hashing import sha256_bytes

REGISTRY_SCHEMA = "https://calm-frames.github.io/schemas/flashmap-registry-v1.json"
REGISTRY_VERSION = 1
REGISTRY_NAME = "registry.json"
GENERATOR = {"name": "calm-frames-registry", "version": "1.0.0"}

SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
RFC3339_UTC = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(\.\d+)?Z$")


class RegistryError(PipelineError):
    """The index could not be built, or could not be checked."""


def canonical_bytes(document: dict[str, Any]) -> bytes:
    """The exact bytes a signature covers: the document without its signature.

    Word for word the rule in docs/SIDECAR_SPEC.md, so an index is signed and
    checked the same way a map is.
    """
    payload = {key: value for key, value in document.items() if key != "signature"}
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _public_key_bytes(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _key_id(key: Ed25519PublicKey) -> str:
    return "sha256:" + sha256_bytes(_public_key_bytes(key))


def load_public_key(path: str | Path) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(Path(path).read_bytes())
    except (OSError, ValueError) as exc:
        raise RegistryError(f"{path} could not be read as a public key: {exc}") from exc
    if not isinstance(key, Ed25519PublicKey):
        raise RegistryError(f"{path} is not an Ed25519 public key")
    return key


def load_private_key(path: str | Path) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    except (OSError, ValueError) as exc:
        raise RegistryError(f"{path} could not be read as a private key: {exc}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise RegistryError(f"{path} is not an Ed25519 private key")
    return key


def _decode_base64(value: Any, what: str, *, length: int | None = None) -> bytes:
    if not isinstance(value, str):
        raise RegistryError(f"{what} is not a string")
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RegistryError(f"{what} is not base64: {exc}") from exc
    if length is not None and len(raw) != length:
        raise RegistryError(f"{what} is {len(raw)} bytes, not {length}")
    return raw


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise RegistryError(f"{path} is not inside {root}") from exc


def parse_created_utc(value: Any, what: str) -> datetime:
    """RFC 3339 in UTC, the one shape the spec allows, as a real datetime.

    Strings are not compared as strings anywhere in this module. A timestamp
    with a fractional part sorts before the same second without one, which would
    pick the wrong map as the newest exactly when two maps land in one second.
    """
    if not isinstance(value, str) or not RFC3339_UTC.match(value):
        raise RegistryError(
            f"{what} is not an RFC 3339 UTC timestamp like 2026-09-17T22:00:00Z: "
            f"{value!r}"
        )
    match = RFC3339_UTC.match(value)
    assert match is not None  # the regex above already matched
    stamp = datetime.strptime(
        f"{match.group(1)}T{match.group(2)}", "%Y-%m-%dT%H:%M:%S"
    ).replace(tzinfo=timezone.utc)
    if match.group(3):
        fraction = min(999_999, int(float(match.group(3)) * 1_000_000))
        stamp = stamp.replace(microsecond=fraction)
    return stamp


def format_created_utc(stamp: datetime) -> str:
    """Seconds precision, UTC, the way every map writes it."""
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def merged_hidden_ms(doc: FlashMapDoc) -> int:
    """Total milliseconds the map's segments cover, overlaps counted once.

    Taken from the segments this pipeline read, not from the map's own
    ``summary.hidden_ms``, so the index never repeats a number it did not work
    out itself.
    """
    total = 0.0
    current_start: float | None = None
    current_end = 0.0
    for segment in sorted(doc.segments, key=lambda one: (one.start_ms, one.end_ms)):
        if current_start is None:
            current_start, current_end = segment.start_ms, segment.end_ms
            continue
        if segment.start_ms <= current_end:
            current_end = max(current_end, segment.end_ms)
            continue
        total += current_end - current_start
        current_start, current_end = segment.start_ms, segment.end_ms
    if current_start is not None:
        total += current_end - current_start
    return int(round(total))


def find_maps(maps_dir: str | Path) -> list[Path]:
    """Every map file under the directory, in one order whatever the disk says.

    The index itself is skipped, so rebuilding it in place does not index it.
    """
    root = Path(maps_dir)
    if not root.is_dir():
        raise RegistryError(f"{root} is not a directory of maps")
    found = [
        path
        for path in root.rglob("*.json")
        if path.is_file() and path.name != REGISTRY_NAME
    ]
    return sorted(found, key=lambda path: path.relative_to(root).as_posix())


def _check_map_signature(
    document: dict[str, Any], public: Ed25519PublicKey, path: Path
) -> str:
    """Check the map against the key we were given. Returns its signature.

    The key inside the map is not the one that is trusted. It has to be equal
    to the key we hold, and then the signature is checked against ours, so a map
    signed by anyone else is refused rather than self checked.
    """
    signature = document.get("signature")
    if not isinstance(signature, dict):
        raise RegistryError(f"{path} carries no signature, so it cannot be indexed")
    if signature.get("algorithm") != "ed25519":
        raise RegistryError(
            f"{path} is signed with {signature.get('algorithm')!r}, not ed25519"
        )
    held = _public_key_bytes(public)
    carried = _decode_base64(
        signature.get("public_key"), f"{path} signature.public_key", length=32
    )
    if carried != held:
        raise RegistryError(
            f"{path} was signed by a key this build does not hold, so it cannot "
            "be indexed"
        )
    value = signature.get("value")
    raw_signature = _decode_base64(value, f"{path} signature.value", length=64)
    payload = canonical_bytes(document)
    try:
        public.verify(raw_signature, payload)
    except InvalidSignature as exc:
        raise RegistryError(
            f"{path} signature does not match the map body, so it cannot be indexed"
        ) from exc
    carried_digest = signature.get("payload_sha256")
    if carried_digest is not None and carried_digest != sha256_bytes(payload):
        raise RegistryError(f"{path} signature payload_sha256 does not match its body")
    assert isinstance(value, str)  # _decode_base64 already refused anything else
    return value


def _entry_for(path: Path, root: Path, public: Ed25519PublicKey) -> tuple[str, str, dict]:
    """One map, checked, as (file sha256, profile, entry)."""
    try:
        doc = load_map(path)
    except MapFormatError as exc:
        raise RegistryError(f"{path} could not be read as a map: {exc}") from exc
    if doc.version != REGISTRY_VERSION and str(doc.version) != str(REGISTRY_VERSION):
        raise RegistryError(
            f"{path} is map version {doc.version!r}, this build indexes version "
            f"{REGISTRY_VERSION}"
        )
    sha256 = (doc.source_sha256 or "").lower()
    if not SHA256_HEX.match(sha256):
        raise RegistryError(f"{path} has no usable source.sha256, so nothing to key on")
    profile = doc.profile
    if not isinstance(profile, str) or not profile.strip():
        raise RegistryError(f"{path} has no usable profile name")
    signature_value = _check_map_signature(doc.raw, public, path)
    created = doc.raw.get("created_utc")
    stamp = parse_created_utc(created, f"{path} created_utc")
    key_id = doc.raw.get("signature", {}).get("key_id")
    if not isinstance(key_id, str) or not key_id:
        key_id = _key_id(public)
    entry = {
        "path": _relative(path, root),
        "signature": signature_value,
        "key_id": key_id,
        "created_utc": format_created_utc(stamp),
        "segment_count": len(doc.segments),
        "hidden_ms": merged_hidden_ms(doc),
    }
    return sha256, profile.strip(), entry


def build_registry(
    maps_dir: str | Path,
    *,
    public_key_path: str | Path,
    created_utc: str | None = None,
    maps: Iterable[Path] | None = None,
) -> dict[str, Any]:
    """Build the index from a directory of published maps. Unsigned as yet.

    Every map is checked before it is indexed, and anything that does not check
    out stops the build.
    """
    root = Path(maps_dir)
    public = load_public_key(public_key_path)
    paths = list(maps) if maps is not None else find_maps(root)

    files: dict[str, dict[str, Any]] = {}
    seen: dict[tuple[str, str], str] = {}
    newest: datetime | None = None
    for path in sorted(paths, key=lambda one: _relative(Path(one), root)):
        sha256, profile, entry = _entry_for(Path(path), root, public)
        key = (sha256, profile)
        if key in seen:
            raise RegistryError(
                f"two maps claim file {sha256[:16]}... at profile {profile}: "
                f"{seen[key]} and {entry['path']}. An index cannot choose between "
                "them, so nothing was written."
            )
        seen[key] = entry["path"]
        files.setdefault(sha256, {"maps": {}})["maps"][profile] = entry
        stamp = parse_created_utc(entry["created_utc"], f"{path} created_utc")
        newest = stamp if newest is None or stamp > newest else newest

    if created_utc is not None:
        stamp_text = format_created_utc(parse_created_utc(created_utc, "--created-utc"))
    elif newest is not None:
        stamp_text = format_created_utc(newest)
    else:
        raise RegistryError(
            f"{root} holds no maps, so there is no map date to take the index's "
            "own date from. Pass --created-utc to build an empty index."
        )

    return {
        "schema": REGISTRY_SCHEMA,
        "version": REGISTRY_VERSION,
        "generator": dict(GENERATOR),
        "created_utc": stamp_text,
        "files": files,
    }


def sign_document(
    document: dict[str, Any], private: Ed25519PrivateKey
) -> dict[str, Any]:
    """Put a signature block on a document, the way the sidecar spec says.

    The index is signed exactly the way a map is, so this is the one function
    for both, and a reader can check either with the same two steps.
    """
    payload = canonical_bytes(document)
    public = private.public_key()
    signed = dict(document)
    signed["signature"] = {
        "algorithm": "ed25519",
        "key_id": _key_id(public),
        "public_key": base64.b64encode(_public_key_bytes(public)).decode("ascii"),
        "payload_sha256": sha256_bytes(payload),
        "value": base64.b64encode(private.sign(payload)).decode("ascii"),
    }
    return signed


def sign_registry(
    document: dict[str, Any], private: Ed25519PrivateKey
) -> dict[str, Any]:
    return sign_document(document, private)


def registry_bytes(document: dict[str, Any]) -> bytes:
    """What the file on disk holds: pretty printed, sorted, one trailing line."""
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_registry(document: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(registry_bytes(document))
    os.replace(tmp, path)
    return path


def load_registry(path: str | Path) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"{path} could not be read as JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise RegistryError(f"{path} is not a JSON object")
    return document


def verify_registry(
    document: dict[str, Any], *, public_key_path: str | Path
) -> list[str]:
    """Every reason this index would be refused, named. Empty means it passes.

    This is the producer side of the reader rules in the spec. The player side
    is ``app/src/calmframes/mapRegistry.ts`` and it checks the same things.
    """
    problems: list[str] = []
    if document.get("version") != REGISTRY_VERSION:
        problems.append(
            f"index version is {document.get('version')!r}, this build reads "
            f"version {REGISTRY_VERSION}"
        )
    try:
        parse_created_utc(document.get("created_utc"), "created_utc")
    except RegistryError as exc:
        problems.append(str(exc))

    files = document.get("files")
    if not isinstance(files, dict):
        problems.append("index has no files object")
        files = {}
    for sha256, block in files.items():
        if not isinstance(sha256, str) or not SHA256_HEX.match(sha256):
            problems.append(f"{sha256!r} is not a lowercase hex SHA-256")
            continue
        maps = block.get("maps") if isinstance(block, dict) else None
        if not isinstance(maps, dict) or not maps:
            problems.append(f"{sha256[:16]}... has no maps")
            continue
        for profile, entry in maps.items():
            where = f"{sha256[:16]}... at profile {profile}"
            if not isinstance(entry, dict):
                problems.append(f"{where} is not an object")
                continue
            path = entry.get("path")
            if not isinstance(path, str) or not path:
                problems.append(f"{where} has no path")
            elif not is_inside_path(path):
                problems.append(f"{where} has a path that leaves the index: {path!r}")
            for field in ("signature", "key_id", "created_utc"):
                if not isinstance(entry.get(field), str) or not entry[field]:
                    problems.append(f"{where} has no {field}")

    signature = document.get("signature")
    if not isinstance(signature, dict):
        problems.append("index is not signed")
        return problems
    if signature.get("algorithm") != "ed25519":
        problems.append(f"unknown signature algorithm {signature.get('algorithm')!r}")
        return problems
    try:
        public = load_public_key(public_key_path)
        held = _public_key_bytes(public)
        carried = _decode_base64(signature.get("public_key"), "signature.public_key")
        if carried != held:
            problems.append("index was signed by a key this build does not hold")
        payload = canonical_bytes(document)
        if signature.get("payload_sha256") not in (None, sha256_bytes(payload)):
            problems.append("signature payload_sha256 does not match the index body")
        public.verify(_decode_base64(signature.get("value"), "signature.value"), payload)
    except InvalidSignature:
        problems.append("signature does not match the index body")
    except RegistryError as exc:
        problems.append(str(exc))
    return problems


def is_inside_path(path: str) -> bool:
    """True when this entry path stays under the index it came from.

    An index entry is resolved against the index's own URL, so a path that is
    absolute, carries a scheme, starts with a slash or steps up with ``..``
    would send a player somewhere else. The player refuses those too. This is
    the same refusal on the producer side, so a bad one never ships.
    """
    if not path or path.startswith("/") or path.startswith("\\"):
        return False
    if "\\" in path or "://" in path or path.startswith("//"):
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path):
        return False
    return all(part not in ("..", "") for part in path.split("/"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline.registry",
        description="Build or check the signed index of published maps.",
    )
    parser.add_argument(
        "maps_dir",
        nargs="?",
        help="directory of published maps to index",
    )
    parser.add_argument("--out", help="where to write the index")
    parser.add_argument("--key", help="Ed25519 private key that signs the index")
    parser.add_argument("--pub", required=True, help="public key every map is checked against")
    parser.add_argument(
        "--created-utc",
        help="the index's own date, instead of the newest map's date",
    )
    parser.add_argument(
        "--check",
        help="check an index that already exists instead of building one",
    )
    args = parser.parse_args(argv)

    try:
        if args.check:
            problems = verify_registry(
                load_registry(args.check), public_key_path=args.pub
            )
            if problems:
                for problem in problems:
                    print(f"refused: {problem}")
                return 1
            print(f"{args.check} verifies against {args.pub}")
            return 0

        if not args.maps_dir or not args.out or not args.key:
            parser.error("building an index needs MAPS_DIR, --out and --key")
        document = build_registry(
            args.maps_dir,
            public_key_path=args.pub,
            created_utc=args.created_utc,
        )
        signed = sign_registry(document, load_private_key(args.key))
        path = write_registry(signed, args.out)
    except RegistryError as exc:
        print(f"refused: {exc}")
        return 2
    count = sum(len(block["maps"]) for block in signed["files"].values())
    print(f"{path}: {count} map(s) for {len(signed['files'])} file(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover - the CLI entry point
    raise SystemExit(main())
