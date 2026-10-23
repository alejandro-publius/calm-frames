"""Content hashing.

The source SHA-256 is the key for everything: the work directory, the ledger,
the map binding and the catalog entry. It is computed one way, here.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
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


def sha256_regular_file(path: str | Path) -> str:
    """Hex SHA-256 of a regular file, refusing to follow a link at the last component.

    Used where a hash vouches for a file the pipeline owns, so a link planted in
    place of an output can never stand in for the bytes it was recorded with.
    """
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(f"{path} is not a regular file")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(fd)


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
