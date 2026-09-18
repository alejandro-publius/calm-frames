"""The map sidecar: version 1 of the JSON that other parts of Calm Frames read.

The schema is written out in docs/SIDECAR_SPEC.md. Change one, change the other, and bump
`SIDECAR_VERSION` if the change is not backward compatible.

Signing rule: the signature covers the canonical JSON of the whole document with the
`signature` key removed. Canonical means sorted keys, no spaces, UTF-8, and no NaN or infinity.
A verifier rebuilds those bytes from the file it was handed, so a single changed character
anywhere in the map breaks the signature.
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from . import signing
from .analyze import AnalysisResult
from .picture import DETECTED

__all__ = [
    "SIDECAR_VERSION",
    "SIDECAR_SCHEMA",
    "VerificationError",
    "VerifyReport",
    "build_map",
    "canonical_bytes",
    "sign_map",
    "write_map",
    "load_map",
    "verify_map",
]

SIDECAR_VERSION = 1
SIDECAR_SCHEMA = "https://calm-frames.github.io/schemas/flashmap-map-v1.json"


class VerificationError(Exception):
    """The map does not stand up. Callers must fail closed when they see this."""


@dataclass
class VerifyReport:
    ok: bool
    problems: list[str]
    checked_signature: bool
    source_hash_matches: bool | None


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _picture_block(result: AnalysisResult) -> dict[str, Any]:
    """The `picture` block, including the rectangle in the source file's own coded pixels.

    `coded` is what a re-encode of this file is measured against later. Analysis pixels depend
    on the analysis width, which is a setting, so they are no use for carrying a rectangle from
    one file to another. Coded pixels are the file.
    """
    source = result.source
    block: dict[str, Any] = {
        **result.picture.as_dict(),
        "source": result.picture_source,
        "coded": result.picture.scaled_to(source.coded_width, source.coded_height),
    }
    if result.picture_source != DETECTED and result.detected_picture is not None:
        detected = result.detected_picture
        block["detected"] = {
            "left": detected.left,
            "top": detected.top,
            "width": detected.width,
            "height": detected.height,
            "letterbox": detected.letterbox,
            "pillarbox": detected.pillarbox,
            "coded": detected.scaled_to(source.coded_width, source.coded_height),
        }
        block["note"] = (
            "The rectangle in this map was carried in from another file's map, not detected "
            "here. Area fractions were measured on it, not on the full coded frame. What this "
            "file's own detector found is under `detected`."
        )
    return block


def build_map(result: AnalysisResult, created_utc: str | None = None) -> dict[str, Any]:
    """Turn an analysis into the version 1 document, unsigned."""
    from . import __version__

    source = result.source
    return {
        "schema": SIDECAR_SCHEMA,
        "version": SIDECAR_VERSION,
        "generator": {"name": "flashmap", "version": __version__},
        "created_utc": created_utc or _now_iso(),
        "source": {
            "path": Path(source.path).name,
            "sha256": source.sha256,
            "size_bytes": source.size_bytes,
            "coded_width": source.coded_width,
            "coded_height": source.coded_height,
            "container_frame_rate": source.container_frame_rate,
            "duration_ms": None if source.duration_ms is None else round(source.duration_ms, 3),
            "frame_count": result.frame_count,
            "first_pts_ms": None if result.first_pts_ms is None else round(result.first_pts_ms, 3),
            "last_pts_ms": None if result.last_pts_ms is None else round(result.last_pts_ms, 3),
            "variable_frame_rate": result.variable_frame_rate,
            "frame_interval_ms": {k: round(v, 3) for k, v in result.frame_interval_ms.items()},
            "timestamp_source": source.timestamp_source,
        },
        "picture": _picture_block(result),
        "color": {
            **source.color.as_dict(),
            "analysis_width": source.analysis_width,
            "analysis_height": source.analysis_height,
        },
        "profile": {
            **result.profile.as_dict(),
            "area_windows": [window.as_dict() for window in result.area_windows],
            "room": None if result.room is None else result.room.as_dict(),
        },
        "segments": [segment.as_dict() for segment in result.segments],
        "summary": {
            "pass": result.passes,
            "segment_count": len(result.segments),
            "hidden_ms": int(round(result.hidden_ms)),
            "general_segment_count": sum(1 for s in result.segments if s.reason == "general"),
            "red_segment_count": sum(1 for s in result.segments if s.reason == "red"),
            "area_measured_on": "picture",
        },
    }


def canonical_bytes(document: dict[str, Any]) -> bytes:
    """The exact bytes a signature covers: the document without its `signature` key."""
    payload = {key: value for key, value in document.items() if key != "signature"}
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sign_map(document: dict[str, Any], private: Ed25519PrivateKey) -> dict[str, Any]:
    payload = canonical_bytes(document)
    public = private.public_key()
    signed = dict(document)
    signed["signature"] = {
        "algorithm": "ed25519",
        "key_id": signing.key_id(public),
        "public_key": base64.b64encode(signing.public_key_bytes(public)).decode("ascii"),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "value": base64.b64encode(signing.sign(private, payload)).decode("ascii"),
    }
    return signed


def write_map(document: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_map(path: str | Path) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"{path} could not be read as JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise VerificationError(f"{path} is not a JSON object")
    return document


def verify_map(
    document: dict[str, Any],
    video_path: str | Path | None = None,
    public_key_path: str | Path | None = None,
    require_signature: bool = True,
) -> VerifyReport:
    """Check a map fails closed: right version, right file, right signature.

    Nothing here trusts the map. Every field it reads is checked before it is used.
    """
    problems: list[str] = []
    checked_signature = False
    source_hash_matches: bool | None = None

    if document.get("version") != SIDECAR_VERSION:
        problems.append(
            f"map version is {document.get('version')!r}, this build reads version "
            f"{SIDECAR_VERSION}"
        )
    for required in ("source", "segments", "profile", "picture", "summary"):
        if required not in document:
            problems.append(f"map has no {required!r} section")

    source = document.get("source")
    expected_hash = source.get("sha256") if isinstance(source, dict) else None
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        problems.append("map has no usable source.sha256")
        expected_hash = None

    if video_path is not None:
        from .decode import sha256_file

        try:
            actual = sha256_file(video_path)
        except OSError as exc:
            problems.append(f"could not hash {video_path}: {exc}")
        else:
            if expected_hash is None:
                source_hash_matches = False
            else:
                source_hash_matches = actual == expected_hash
                if not source_hash_matches:
                    problems.append(
                        "this map was not made for this file: map says "
                        f"{expected_hash[:16]}..., file is {actual[:16]}..."
                    )

    signature = document.get("signature")
    if signature is None:
        if require_signature:
            problems.append("map is not signed")
    elif not isinstance(signature, dict):
        problems.append("signature is not an object")
    else:
        if signature.get("algorithm") != "ed25519":
            problems.append(f"unknown signature algorithm {signature.get('algorithm')!r}")
        else:
            payload = canonical_bytes(document)
            digest = hashlib.sha256(payload).hexdigest()
            if signature.get("payload_sha256") not in (None, digest):
                problems.append("signature payload_sha256 does not match the map body")
            try:
                if public_key_path is not None:
                    public = signing.load_public_key(public_key_path)
                else:
                    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

                    raw = base64.b64decode(str(signature.get("public_key", "")), validate=True)
                    public = Ed25519PublicKey.from_public_bytes(raw)
                    problems.append(
                        "no public key was given. The signature was checked against the key "
                        "carried inside the map, which proves the map is self consistent and "
                        "nothing more. Pass the public key you already hold."
                    )
                signing.verify(
                    public,
                    base64.b64decode(str(signature.get("value", "")), validate=True),
                    payload,
                )
                checked_signature = True
            except signing.InvalidSignature:
                problems.append("signature does not match the map body")
            except Exception as exc:  # noqa: BLE001 - any failure here is a failed verify
                problems.append(f"signature could not be checked: {exc}")

    ok = not problems
    return VerifyReport(
        ok=ok,
        problems=problems,
        checked_signature=checked_signature,
        source_hash_matches=source_hash_matches,
    )
