#!/usr/bin/env python3
"""Make the fixtures for the map registry test.

    .venv/bin/python pipeline/tests/make_registry_fixture.py

The test in app/test/calmframes/mapRegistry.test.ts needs a signed index and
the signed maps it points at. The app can check an Ed25519 signature and cannot
make one, which is right for a player and useless for writing this fixture, so
the signing happens here.

The idea is borrowed from scripts/make_revoked_key_fixture.py: derive the key at
run time from a phrase in this file rather than storing one, so there is no
private key anywhere in the repository and anyone who can read this script can
rebuild the fixture.

What is real and what is not, said plainly:

- the two map bodies are real analyzer output that is already in this
  repository. bursts.flashmap.json was made by flashmap from a generated strobe
  clip that was deleted in the same job, and calm_gradient.flashmap.json is the
  map for the calm clip the app ships. Their segments, timings and hashes are
  untouched;
- only their signature blocks are new, because a fixture map has to be signed by
  the key the fixture index is signed by, and we do not hold the key that signed
  the originals;
- the index itself is built by pipeline/registry.py, the same code that would
  build a published one;
- one file is a sham and is named like one. ``swapped_map.json`` is the bursts
  map with its segments taken out and an older date put on it, signed by the
  same key and bound to the same file. It stands for the map an attacker who
  can serve the files would like to hand back in place of the current one: the
  same title, checked, with nothing to hide. It is never indexed. It lives
  outside the registry directory so the builder cannot see it, and the app test
  serves it by hand.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey,
)

from pipeline import registry  # noqa: E402

PHRASE = b"calm frames map registry fixture, the key that signs the index and its maps"

FIXTURES = REPO / "app" / "test" / "calmframes" / "fixtures" / "registry"
SOURCES = {
    "maps/bursts.wcag.json": REPO
    / "app"
    / "test"
    / "calmframes"
    / "fixtures"
    / "bursts.flashmap.json",
    "maps/calm_gradient.wcag.json": REPO
    / "app"
    / "assets"
    / "raw"
    / "offline"
    / "calm_gradient.flashmap.json",
}


def main() -> int:
    private = Ed25519PrivateKey.from_private_bytes(hashlib.sha256(PHRASE).digest())
    public = private.public_key()
    public_raw = public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    (FIXTURES / "maps").mkdir(parents=True, exist_ok=True)
    public_pem = FIXTURES / "key.pub.pem"
    public_pem.write_bytes(
        public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    for name, source in SOURCES.items():
        body = json.loads(source.read_text(encoding="utf-8"))
        body.pop("signature", None)
        signed = registry.sign_document(body, private)
        target = FIXTURES / name
        target.write_bytes(
            (json.dumps(signed, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )
        print(f"wrote {target.relative_to(REPO)}")

    swapped = json.loads(SOURCES["maps/bursts.wcag.json"].read_text(encoding="utf-8"))
    swapped.pop("signature", None)
    swapped["created_utc"] = "2026-09-01T00:00:00Z"
    swapped["segments"] = []
    swapped["summary"] = dict(swapped.get("summary", {}))
    swapped["summary"].update({"pass": True, "segment_count": 0, "hidden_ms": 0})
    swapped_path = FIXTURES.parent / "registry_swapped_map.json"
    swapped_path.write_bytes(
        (json.dumps(registry.sign_document(swapped, private), indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(f"wrote {swapped_path.relative_to(REPO)}")

    document = registry.build_registry(FIXTURES, public_key_path=public_pem)
    path = registry.write_registry(
        registry.sign_registry(document, private), FIXTURES / registry.REGISTRY_NAME
    )
    print(f"wrote {path.relative_to(REPO)}")
    print(f"public key base64: {base64.b64encode(public_raw).decode('ascii')}")
    print(f"index created_utc: {document['created_utc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
