"""Bounded structural refusal of MP4 protection metadata, never DRM removal.

This only recognizes protection declarations in standard MP4 metadata. It is
not a proof of rights or universal DRM detection; complete decoding and the
remaining intake checks still have to succeed. Media payloads are never scanned
as box metadata, and no decryption key or license server is consulted.
"""

from pathlib import Path

from . import PipelineError

CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"moof", b"traf"}
PROTECTED = {b"encv", b"enca", b"enct", b"encs", b"drms", b"drmi", b"pssh", b"senc", b"sinf"}
MAX_BOXES = 4096
MAX_DEPTH = 12


class Mp4IntakeError(PipelineError):
    """A bounded, user-readable refusal without source paths or decoder output."""


def refuse_protected_mp4(source: Path) -> None:
    malformed = "The MP4 structure is incomplete or unsupported. Choose another non-DRM file."
    pending: list[tuple[int, int, int, int | None]] = [(0, source.stat().st_size, 0, None)]
    total = 0
    with source.open("rb") as stream:
        while pending:
            start, end, depth, expected = pending.pop()
            if depth > MAX_DEPTH:
                raise Mp4IntakeError(malformed)
            cursor, count = start, 0
            while cursor < end:
                total += 1
                count += 1
                if total > MAX_BOXES or end - cursor < 8:
                    raise Mp4IntakeError(malformed)
                stream.seek(cursor)
                header = stream.read(8)
                if len(header) != 8:
                    raise Mp4IntakeError(malformed)
                size, kind = int.from_bytes(header[:4], "big"), header[4:]
                header_size = 8
                if size == 1:
                    extended = stream.read(8)
                    if len(extended) != 8:
                        raise Mp4IntakeError(malformed)
                    size, header_size = int.from_bytes(extended, "big"), 16
                elif size == 0:
                    size = end - cursor
                if size < header_size or size > end - cursor:
                    raise Mp4IntakeError(malformed)
                payload, boundary = cursor + header_size, cursor + size
                if kind in PROTECTED:
                    raise Mp4IntakeError(
                        "Encrypted or DRM-protected MP4 is not supported. This tool cannot remove DRM."
                    )
                if kind in CONTAINERS:
                    pending.append((payload, boundary, depth + 1, None))
                elif kind == b"stsd":
                    stream.seek(payload)
                    description = stream.read(8)
                    if boundary - payload < 8 or len(description) != 8:
                        raise Mp4IntakeError(malformed)
                    entries = int.from_bytes(description[4:], "big")
                    if description[:4] != b"\x00" * 4 or not 1 <= entries <= MAX_BOXES:
                        raise Mp4IntakeError(malformed)
                    pending.append((payload + 8, boundary, depth + 1, entries))
                elif kind in {b"avc1", b"avc3"}:
                    if boundary - payload < 78:
                        raise Mp4IntakeError(malformed)
                    pending.append((payload + 78, boundary, depth + 1, None))
                elif kind == b"mp4a":
                    stream.seek(payload + 8)
                    version = int.from_bytes(stream.read(2), "big")
                    offset = {0: 28, 1: 44, 2: 64}.get(version)
                    if offset is None or boundary - payload < offset:
                        raise Mp4IntakeError(malformed)
                    pending.append((payload + offset, boundary, depth + 1, None))
                elif kind in {b"sgpd", b"sbgp"}:
                    stream.seek(payload + 4)
                    if boundary - payload >= 8 and stream.read(4) == b"seig":
                        raise Mp4IntakeError("Encrypted MP4 sample groups are not supported.")
                cursor = boundary
            if expected is not None and count != expected:
                raise Mp4IntakeError(malformed)
