#!/usr/bin/env python3
"""Make the fixtures for the revoked key test.

    .venv/bin/python scripts/make_revoked_key_fixture.py

The test in app/test/calmframes/revokedKey.test.ts needs one thing that cannot
be made in JavaScript here: a map that is correctly signed, by a key the app no
longer holds. The app can check an Ed25519 signature and cannot make one, which
is exactly right for a player and useless for writing this fixture.

So the map is signed here, with flashmap's own signing code, by a key derived
from a fixed phrase. The idea is borrowed from eval/fuzz_maps.py: derive the key
at run time from a phrase in this file rather than storing one, so there is no
private key anywhere in the repository and the fixture can be rebuilt by anyone
who can read the script.

Two keys:

    retired   the key that signed the map. Think of it as the key that was on
              the laptop that got lost.
    current   the key the app would be built with after a rotation.

The map is valid. It verifies against the retired key and is refused against the
current one, and the difference between those two is the whole point: a revoked
key is not a broken signature, and the app has to tell them apart.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "flashmap" / "src"))

from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey,
)

from flashmap import signing  # noqa: E402
from flashmap.sidecar import sign_map  # noqa: E402

FIXTURES = REPO / "app" / "test" / "calmframes" / "fixtures"
SOURCE_SHA256 = "9f2c1b6c1cbb4c3a9a0f0c2d5e8b7a6d4f3e2c1b0a9f8e7d6c5b4a3928170615"
CREATED_UTC = "2026-09-17T12:00:00Z"

RETIRED_PHRASE = b"calm frames revoked key fixture, the key that was retired"
CURRENT_PHRASE = b"calm frames revoked key fixture, the key that replaced it"


def key_from(phrase: bytes) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(phrase).digest())


def public_base64(private: Ed25519PrivateKey) -> str:
    return base64.b64encode(signing.public_key_bytes(private.public_key())).decode("ascii")


def a_small_map() -> dict:
    """A map the app's reader accepts: version 1, bound to a file, with segments."""
    return {
        "version": 1,
        "created_utc": CREATED_UTC,
        "generator": {"name": "flashmap", "version": "1.0.0"},
        "source": {
            "path": "titles/example/safe/wcag/safe.mp4",
            "sha256": SOURCE_SHA256,
            "duration_ms": 30000,
        },
        "picture": {"width": 192, "height": 108, "left": 0, "top": 0, "letterbox": False},
        "profile": {
            "name": "wcag",
            "area_windows": [{"name": "wcag-10deg", "width_px": 64, "height_px": 36}],
        },
        "segments": [
            {"start_ms": 1000, "end_ms": 1800, "reason": "general"},
            {"start_ms": 12000, "end_ms": 12600, "reason": "red"},
        ],
        "summary": {"hidden_ms": 1400, "general_segment_count": 1, "red_segment_count": 1},
    }


def main() -> int:
    retired = key_from(RETIRED_PHRASE)
    current = key_from(CURRENT_PHRASE)

    signed = sign_map(a_small_map(), retired)
    map_path = FIXTURES / "revoked_key.flashmap.json"
    map_path.write_text(json.dumps(signed, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    metadata = {
        "note": (
            "Public halves only. Both keys are derived from the phrases in "
            "scripts/make_revoked_key_fixture.py, so there is no private key in "
            "this repository. They sign this one test map and nothing else."
        ),
        "retired": {
            "public_key_base64": public_base64(retired),
            "key_id": signing.key_id(retired.public_key()),
            "what_it_is": "the key that signed revoked_key.flashmap.json, then was rotated out",
        },
        "current": {
            "public_key_base64": public_base64(current),
            "key_id": signing.key_id(current.public_key()),
            "what_it_is": "the key an app built after the rotation would carry",
        },
        "source_sha256": SOURCE_SHA256,
        "created_utc": CREATED_UTC,
    }
    metadata_path = FIXTURES / "revoked_key.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {map_path.relative_to(REPO)}")
    print(f"wrote {metadata_path.relative_to(REPO)}")
    print(f"retired key id {metadata['retired']['key_id']}")
    print(f"current key id {metadata['current']['key_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
