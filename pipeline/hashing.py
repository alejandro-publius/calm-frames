"""Content hashing.

The source SHA-256 is the key for everything: the work directory, the ledger,
the map binding and the catalog entry. It is computed one way, here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CHUNK_BYTES = 1024 * 1024


def sha256_file(path: str | Path) -> str:
    """Hex SHA-256 of a file, read in chunks so a 2 hour title fits in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(payload: Any) -> str:
    """Stable hash of a step's inputs.

    Used by the ledger to decide whether finished work is still valid. Sorted
    keys and a compact separator keep the value stable across runs and across
    Python versions.
    """
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
