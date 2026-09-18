"""Write a PNG from an RGB array, with nothing but the standard library.

flashmap depends on av, numpy and cryptography and nothing else. The report
draws its own pictures, so it needs to write a PNG, and adding an imaging
library to an analyzer that studios install for one job is a poor trade for
about thirty lines of format.

What this writes is the plainest PNG there is: colour type 2 (truecolour), 8
bits a channel, no interlacing, filter type 0 on every row. Every decoder
reads it, and ffmpeg reads it, which is what the image check needs.

The output is deterministic: the same array gives the same bytes, so the
SHA-256 the report prints beside an image is a hash a reader can reproduce.
"""

from __future__ import annotations

import struct
import zlib

import numpy as np
from numpy.typing import NDArray

__all__ = ["encode_png"]

_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def encode_png(pixels: NDArray[np.uint8]) -> bytes:
    """Encode an (height, width, 3) uint8 array as a truecolour PNG."""
    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError(f"expected an (h, w, 3) array, got shape {pixels.shape}")
    if pixels.dtype != np.uint8:
        raise ValueError(f"expected uint8, got {pixels.dtype}")
    height, width = int(pixels.shape[0]), int(pixels.shape[1])
    if height == 0 or width == 0:
        raise ValueError("an image needs at least one row and one column")

    # A filter byte of 0 in front of every row: store the bytes as they are.
    rows = np.zeros((height, width * 3 + 1), dtype=np.uint8)
    rows[:, 1:] = np.ascontiguousarray(pixels).reshape(height, width * 3)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"".join(
        [
            _SIGNATURE,
            _chunk(b"IHDR", header),
            # Level 9 and no dictionary reset, so the bytes are reproducible.
            _chunk(b"IDAT", zlib.compress(rows.tobytes(), 9)),
            _chunk(b"IEND", b""),
        ]
    )
