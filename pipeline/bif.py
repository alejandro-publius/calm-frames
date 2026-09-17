"""BIF trickplay files.

BIF is the Roku thumbnail format Fire TV players use for scrubbing previews.
Layout, little endian throughout:

    0      8 bytes   magic 89 42 49 46 0d 0a 1a 0a
    8      uint32    version, 0
    12     uint32    number of images
    16     uint32    timestamp multiplier in milliseconds, default 1000
    20     44 bytes  reserved, zero
    64     index     (timestamp, absolute offset) per image, then
                     (0xffffffff, offset of end of file)
    ...    JPEG data

Two rules this module exists to keep:

- trickplay frames come only from the kid safe rendition, never from the
  original, so scrubbing can never show a frame the pipeline hid;
- every frame is taken from a calm moment. A slot that lands inside a cover
  interval is sampled from the nearest calm moment instead, and the manifest
  records both times so verify can check the claim.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from . import PipelineError
from .hideplan import DEFAULT_CALM_MARGIN_MS, CoverInterval, is_calm
from .posters import snap_to_calm
from .render import extract_jpeg

BIF_MAGIC = bytes([0x89, 0x42, 0x49, 0x46, 0x0D, 0x0A, 0x1A, 0x0A])
BIF_VERSION = 0
HEADER_BYTES = 64
INDEX_ENTRY_BYTES = 8
DEFAULT_MULTIPLIER_MS = 1000
DEFAULT_INTERVAL_MS = 10_000
DEFAULT_THUMB_WIDTH = 320


@dataclass
class BifFrame:
    """One trickplay thumbnail.

    ``slot_ms`` is where the player will show it. ``source_ms`` is where the
    picture was taken from, which is the number that has to be calm.
    """

    index: int
    slot_ms: float
    source_ms: float
    path: Path | None = None
    snapped: bool = False

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "slot_ms": self.slot_ms,
            "source_ms": self.source_ms,
            "path": str(self.path) if self.path else None,
            "snapped": self.snapped,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BifFrame":
        return cls(
            index=int(data["index"]),
            slot_ms=float(data["slot_ms"]),
            source_ms=float(data["source_ms"]),
            path=Path(data["path"]) if data.get("path") else None,
            snapped=bool(data.get("snapped", False)),
        )


@dataclass
class BifFile:
    version: int
    count: int
    multiplier_ms: int
    timestamps_ms: list[int] = field(default_factory=list)
    sizes: list[int] = field(default_factory=list)


def write_bif(
    out_path: str | Path,
    images: Sequence[bytes],
    *,
    timestamps: Sequence[int] | None = None,
    multiplier_ms: int = DEFAULT_MULTIPLIER_MS,
) -> Path:
    """Write a BIF file. ``timestamps`` are in units of ``multiplier_ms``."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = len(images)
    if timestamps is None:
        timestamps = list(range(count))
    if len(timestamps) != count:
        raise PipelineError("a BIF needs one timestamp per image")

    header = bytearray(HEADER_BYTES)
    header[0:8] = BIF_MAGIC
    struct.pack_into("<I", header, 8, BIF_VERSION)
    struct.pack_into("<I", header, 12, count)
    struct.pack_into("<I", header, 16, multiplier_ms)

    index_bytes = (count + 1) * INDEX_ENTRY_BYTES
    offset = HEADER_BYTES + index_bytes
    index = bytearray()
    for timestamp, image in zip(timestamps, images):
        index += struct.pack("<II", int(timestamp), offset)
        offset += len(image)
    index += struct.pack("<II", 0xFFFFFFFF, offset)

    with open(out_path, "wb") as handle:
        handle.write(bytes(header))
        handle.write(bytes(index))
        for image in images:
            handle.write(image)
    return out_path


def read_bif(path: str | Path) -> BifFile:
    path = Path(path)
    data = path.read_bytes()
    if len(data) < HEADER_BYTES or data[0:8] != BIF_MAGIC:
        raise PipelineError(f"not a BIF file: {path}")
    version, count, multiplier = struct.unpack_from("<III", data, 8)
    entries: list[tuple[int, int]] = []
    for i in range(count + 1):
        start = HEADER_BYTES + i * INDEX_ENTRY_BYTES
        if start + INDEX_ENTRY_BYTES > len(data):
            raise PipelineError(f"BIF index runs past the end of the file: {path}")
        entries.append(struct.unpack_from("<II", data, start))
    timestamps = [entry[0] for entry in entries[:-1]]
    offsets = [entry[1] for entry in entries]
    sizes = [offsets[i + 1] - offsets[i] for i in range(count)]
    if any(size <= 0 for size in sizes):
        raise PipelineError(f"BIF index has a non positive image size: {path}")
    if offsets[-1] != len(data):
        raise PipelineError(
            f"BIF end offset {offsets[-1]} does not match the file size {len(data)}: {path}"
        )
    return BifFile(
        version=version,
        count=count,
        multiplier_ms=multiplier,
        timestamps_ms=[t * multiplier for t in timestamps],
        sizes=sizes,
    )


def plan_bif_frames(
    intervals: Sequence[CoverInterval],
    duration_ms: float,
    *,
    interval_ms: int = DEFAULT_INTERVAL_MS,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> list[BifFrame]:
    """Even slots across the title, each sampled from a calm moment."""
    if duration_ms <= 0:
        raise PipelineError("cannot plan trickplay frames for a zero length title")
    frames: list[BifFrame] = []
    index = 0
    slot_ms = 0.0
    while slot_ms < duration_ms:
        source_ms = snap_to_calm(intervals, slot_ms, duration_ms, margin_ms=margin_ms)
        frames.append(
            BifFrame(
                index=index,
                slot_ms=slot_ms,
                source_ms=source_ms,
                snapped=abs(source_ms - slot_ms) > 0.5,
            )
        )
        index += 1
        slot_ms += interval_ms
    return frames


def build_bif(
    safe_rendition: str | Path,
    *,
    frames: Sequence[BifFrame],
    out_path: str | Path,
    work_dir: str | Path,
    width: int = DEFAULT_THUMB_WIDTH,
    height: int | None = None,
    source_width: int = 1920,
    source_height: int = 1080,
    interval_ms: int = DEFAULT_INTERVAL_MS,
) -> tuple[Path, list[BifFrame]]:
    """Extract each frame from the safe rendition and write the BIF."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    if height is None:
        aspect = source_height / source_width if source_width else 9 / 16
        height = max(2, int(round(width * aspect)))
        if height % 2:
            height += 1

    images: list[bytes] = []
    written: list[BifFrame] = []
    for frame in frames:
        jpeg_path = work_dir / f"bif_{frame.index:05d}.jpg"
        extract_jpeg(
            safe_rendition,
            time_s=frame.source_ms / 1000.0,
            out_path=jpeg_path,
            width=width,
            height=height,
        )
        images.append(jpeg_path.read_bytes())
        written.append(
            BifFrame(
                index=frame.index,
                slot_ms=frame.slot_ms,
                source_ms=frame.source_ms,
                path=jpeg_path,
                snapped=frame.snapped,
            )
        )

    multiplier = DEFAULT_MULTIPLIER_MS
    timestamps = [int(round(frame.slot_ms / multiplier)) for frame in written]
    if len(set(timestamps)) != len(timestamps):
        # Slots closer together than the multiplier would collide in the index.
        multiplier = max(1, int(interval_ms))
        timestamps = [int(round(frame.slot_ms / multiplier)) for frame in written]
    write_bif(out_path, images, timestamps=timestamps, multiplier_ms=multiplier)
    return Path(out_path), written


def frames_from_manifest(data: dict) -> list[BifFrame]:
    return [BifFrame.from_dict(item) for item in data.get("frames", [])]


def all_frames_calm(
    frames: Sequence[BifFrame],
    intervals: Sequence[CoverInterval],
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> list[BifFrame]:
    """The frames that were taken from a moment that is not calm."""
    return [
        frame
        for frame in frames
        if not is_calm(intervals, frame.source_ms, margin_ms=margin_ms)
    ]
