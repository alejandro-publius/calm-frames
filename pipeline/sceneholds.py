"""Preceding context images, bound to the exact cover intervals and source bytes.

An image changes what an opaque cover shows, never when it covers. Missing
descriptors use black. Each selected image is a real preceding decoded frame,
outside every preset's cover and calm margin, or a flat neutral fallback.
"""

from __future__ import annotations

import base64
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence

from . import PipelineError, ffmpegtool
from .flashmap_adapter import FlashmapAdapter
from .hashing import sha256_bytes, sha256_file
from .hideplan import CoverInterval, is_calm
from .layout import TitleLayout
from .probe import VideoProbe

SCENE_HOLD_VERSION = 1
MAX_HOLDS = 32
MAX_IMAGE_BYTES = 128 * 1024
MAX_IMAGE_STRINGS = 2 * 1024 * 1024
MAX_IMAGE_WIDTH = 640
MAX_IMAGE_HEIGHT = 1280
MAX_MAP_TEXT = MAX_IMAGE_STRINGS + 256 * 1024
MAX_LOOKBACK_MS = 5000.0
JPEG_PREFIX = "data:image/jpeg;base64,"
JPEG_QUALITY = 5
_TIMEBASE = re.compile(r"config in time_base:\s*(\d+)/(\d+)")
_PTS = re.compile(r"\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:")


@dataclass(frozen=True)
class SceneHold:
    start_ms: float
    end_ms: float
    frame_ms: float | None
    path: Path
    sha256: str
    origin: str

    def descriptor(self) -> dict:
        raw = self.path.read_bytes()
        if sha256_bytes(raw) != self.sha256:
            raise PipelineError(f"scene hold bytes changed at {self.path}")
        validate_jpeg(raw)
        return {
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "frame_ms": self.frame_ms,
            "image_data_uri": JPEG_PREFIX + base64.b64encode(raw).decode("ascii"),
        }


def validate_jpeg(raw: bytes) -> None:
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise PipelineError("scene hold JPEG exceeds its byte bound or is empty")
    if not raw.startswith(b"\xff\xd8") or not raw.endswith(b"\xff\xd9"):
        raise PipelineError("scene hold is not a complete JPEG")
    cursor = 2
    while cursor + 4 <= len(raw):
        if raw[cursor] != 0xFF:
            break
        marker = raw[cursor + 1]
        length = int.from_bytes(raw[cursor + 2:cursor + 4], "big")
        if length < 2 or cursor + 2 + length > len(raw):
            break
        if marker in {0xC0, 0xC1, 0xC2} and length >= 8:
            height = int.from_bytes(raw[cursor + 5:cursor + 7], "big")
            width = int.from_bytes(raw[cursor + 7:cursor + 9], "big")
            if 0 < width <= MAX_IMAGE_WIDTH and 0 < height <= MAX_IMAGE_HEIGHT:
                return
            raise PipelineError("scene hold JPEG dimensions exceed the wire bounds")
        if marker == 0xDA:
            break
        cursor += 2 + length
    raise PipelineError("scene hold JPEG has no readable image dimensions")


def image_dimensions(probe: VideoProbe) -> tuple[int, int]:
    scale = min(1.0, MAX_IMAGE_WIDTH / probe.width, MAX_IMAGE_HEIGHT / probe.height)
    return max(1, round(probe.width * scale)), max(1, round(probe.height * scale))


def preceding_frame_ms(
    interval: CoverInterval,
    union: Sequence[CoverInterval],
    probe: VideoProbe,
    *,
    margin_ms: float,
) -> float | None:
    """Nearest packet PTS that is preceding and calm; decoding confirms it next."""
    floor = max(0.0, interval.start_ms - MAX_LOOKBACK_MS)
    for stamp in reversed(probe.frame_timestamps_s):
        time_ms = stamp * 1000.0
        if time_ms < floor:
            break
        if time_ms < interval.start_ms and is_calm(union, time_ms, margin_ms=margin_ms):
            return time_ms
    return None


def extract_exact_frame(
    source: str | Path, frame_ms: float, path: Path, probe: VideoProbe
) -> float:
    """Extract only the requested source PTS, never the frame a seek rounds up to.

    Packet times can describe repeated pictures without a decoded frame. Such a
    candidate produces no output and callers use neutral rather than guessing.
    copyts preserves the source origin. The integer PTS and time base from
    showinfo establish which decoded frame actually reached the JPEG encoder.
    """
    width, height = image_dimensions(probe)
    target_s = frame_ms / 1000.0
    seek_s = max(0.0, target_s - 1.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    result = ffmpegtool.run_ffmpeg(
        [
            "-loglevel", "info", "-copyts", "-ss", f"{seek_s:.9f}",
            "-t", f"{target_s - seek_s + 0.1:.9f}", "-i", str(source),
            "-vf", f"select='between(t,{target_s - 0.000001:.9f},"
            f"{target_s + 0.000001:.9f})',scale={width}:{height},showinfo",
            "-fps_mode", "passthrough", "-frames:v", "1", "-q:v", str(JPEG_QUALITY),
            "-update", "1", str(path),
        ]
    )
    timebase = _TIMEBASE.search(result.stderr)
    stamps = _PTS.findall(result.stderr)
    if not path.exists() or not timebase or len(stamps) != 1:
        raise PipelineError("the preceding packet did not produce one identifiable frame")
    actual_ms = int(stamps[0]) * int(timebase.group(1)) / int(timebase.group(2)) * 1000.0
    if abs(actual_ms - frame_ms) > 0.001:
        raise PipelineError("the JPEG decoder selected a different source timestamp")
    validate_jpeg(path.read_bytes())
    return actual_ms


def make_neutral_jpeg(path: Path, probe: VideoProbe) -> None:
    width, height = image_dimensions(probe)
    path.parent.mkdir(parents=True, exist_ok=True)
    ffmpegtool.run_ffmpeg(
        ["-f", "lavfi", "-i", f"color=c=0x282828:s={width}x{height}",
         "-frames:v", "1", "-q:v", str(JPEG_QUALITY), "-update", "1", str(path)]
    )
    validate_jpeg(path.read_bytes())


def build_scene_holds(
    source: Path,
    *,
    layout: TitleLayout,
    preset: str,
    intervals: Sequence[CoverInterval],
    union: Sequence[CoverInterval],
    probe: VideoProbe,
    margin_ms: float,
    adapter: FlashmapAdapter,
    map_path: Path | None = None,
) -> list[SceneHold]:
    holds: list[SceneHold] = []
    total = 0
    # Ingest passes the analyzer's own map, which is what these holds get signed into.
    source_document = json.loads((map_path or layout.map_path(preset)).read_text())
    for index, interval in enumerate(intervals[:MAX_HOLDS]):
        path = layout.scene_image(preset, index)
        selected = preceding_frame_ms(interval, union, probe, margin_ms=margin_ms)
        frame_ms = None
        if selected is not None:
            try:
                frame_ms = extract_exact_frame(source, selected, path, probe)
            except PipelineError:
                frame_ms = None
        if frame_ms is None:
            make_neutral_jpeg(path, probe)

        # A WCAG-only source check does not cover static patterns. Every new
        # displayed image is therefore checked under the broadcast profile too.
        image_map = layout.verify_map_path(preset, f"scene_image_{index:03d}")
        checked = adapter.analyze(path, profile="broadcast", out_path=image_map)
        if not checked.is_clean:
            frame_ms = None
            make_neutral_jpeg(path, probe)
            checked = adapter.analyze(path, profile="broadcast", out_path=image_map)
        if not checked.is_clean:
            raise PipelineError("the neutral scene hold failed its pattern check")

        raw = path.read_bytes()
        uri_size = len(JPEG_PREFIX) + 4 * ((len(raw) + 2) // 3)
        if total + uri_size > MAX_IMAGE_STRINGS:
            break
        candidate = SceneHold(interval.start_ms, interval.end_ms, frame_ms, path,
                              sha256_bytes(raw), "source" if frame_ms is not None else "neutral")
        prospective = dict(source_document, scene_holds=scene_payload([*holds, candidate]))
        # Leave room for the standard signature block added after this step.
        if len(json.dumps(prospective, indent=2, sort_keys=True).encode("utf-8")) > MAX_MAP_TEXT - 1024:
            break
        total += uri_size
        holds.append(candidate)

    manifest = {
        "version": SCENE_HOLD_VERSION,
        "source_sha256": layout.sha256,
        "preset": preset,
        "calm_margin_ms": margin_ms,
        "lookback_ms": MAX_LOOKBACK_MS,
        "holds": [
            {"start_ms": h.start_ms, "end_ms": h.end_ms, "frame_ms": h.frame_ms,
             "path": layout.relative(h.path), "sha256": h.sha256, "origin": h.origin}
            for h in holds
        ],
    }
    layout.scene_manifest(preset).parent.mkdir(parents=True, exist_ok=True)
    layout.scene_manifest(preset).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return holds


def read_scene_holds(layout: TitleLayout, preset: str) -> list[SceneHold]:
    try:
        doc = json.loads(layout.scene_manifest(preset).read_text())
        if doc.get("version") != SCENE_HOLD_VERSION or doc.get("source_sha256") != layout.sha256:
            raise ValueError("wrong scene manifest version or source")
        entries = doc["holds"]
        if not isinstance(entries, list) or len(entries) > MAX_HOLDS:
            raise ValueError("invalid scene hold list")
        holds = []
        previous_end = -1.0
        for entry in entries:
            start, end = entry["start_ms"], entry["end_ms"]
            frame = entry["frame_ms"]
            if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                    for v in (start, end)) or start < 0 or end <= start or start < previous_end):
                raise ValueError("scene hold times are not finite, ordered intervals")
            if frame is not None and (isinstance(frame, bool) or not isinstance(frame, (int, float))
                                      or not math.isfinite(frame) or frame < 0 or frame >= start):
                raise ValueError("a scene image is not preceding its cover")
            path = (layout.root / entry["path"]).resolve()
            path.relative_to((layout.root / "scene_holds" / preset).resolve())
            hold = SceneHold(start, end, frame, path, entry["sha256"], entry["origin"])
            hold.descriptor()  # Existence, JPEG bound and hash before a caller can render it.
            if hold.origin != ("neutral" if frame is None else "source"):
                raise ValueError("scene provenance disagrees with its timestamp")
            holds.append(hold)
            previous_end = end
        if sum(len(h.descriptor()["image_data_uri"]) for h in holds) > MAX_IMAGE_STRINGS:
            raise ValueError("scene holds exceed their map byte bound")
        return holds
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise PipelineError(f"could not read checked scene assets for {preset}: {exc}") from exc


def scene_payload(holds: Sequence[SceneHold]) -> dict:
    return {"version": SCENE_HOLD_VERSION, "holds": [h.descriptor() for h in holds]}


def scene_identity(layout: TitleLayout, preset: str) -> dict:
    """Actual bytes, not just paths, participate in every dependent cache key."""
    holds = read_scene_holds(layout, preset)
    return {"manifest": sha256_file(layout.scene_manifest(preset)),
            "images": [sha256_file(h.path) for h in holds]}


def verify_scene_assets(
    layout: TitleLayout,
    *,
    preset: str,
    source_document: dict,
    source: Path,
    intervals: Sequence[CoverInterval],
    union: Sequence[CoverInterval],
    probe: VideoProbe,
    margin_ms: float,
    adapter: FlashmapAdapter,
) -> list[SceneHold]:
    """Bind signed inline bytes, local assets, times, and exact source provenance."""
    holds = read_scene_holds(layout, preset)
    manifest = json.loads(layout.scene_manifest(preset).read_text())
    if manifest.get("preset") != preset or manifest.get("calm_margin_ms", -1) < margin_ms:
        raise PipelineError("scene hold manifest has the wrong preset or a weaker calm margin")
    if source_document.get("scene_holds") != scene_payload(holds):
        raise PipelineError("signed scene hold images or times differ from local assets")
    interval_pairs = {(i.start_ms, i.end_ms) for i in intervals}
    layout.verify_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="scene_provenance_", dir=layout.verify_dir) as scratch:
        for index, image in enumerate(holds):
            if (image.start_ms, image.end_ms) not in interval_pairs:
                raise PipelineError("scene hold times differ from the unchanged hide plan")
            if image.end_ms > probe.duration_ms:
                raise PipelineError("scene hold ends beyond the source duration")
            reproduced = Path(scratch) / f"frame_{index:03d}.jpg"
            if image.frame_ms is not None:
                if image.start_ms - image.frame_ms > MAX_LOOKBACK_MS:
                    raise PipelineError("scene hold source frame is outside the preceding lookback")
                if not is_calm(union, image.frame_ms, margin_ms=margin_ms):
                    raise PipelineError("scene hold source frame is inside another preset's calm margin")
                extract_exact_frame(source, image.frame_ms, reproduced, probe)
            else:
                make_neutral_jpeg(reproduced, probe)
            if reproduced.read_bytes() != image.path.read_bytes():
                raise PipelineError("scene hold bytes do not reproduce from their stated provenance")
            checked = adapter.analyze(
                image.path, profile="broadcast",
                out_path=layout.verify_map_path(preset, f"scene_image_{index:03d}"),
            )
            if not checked.is_clean:
                raise PipelineError("a scene hold image fails the broadcast pattern check")
    return holds
