"""Calm moments: where a poster, a cover still or a BIF frame may come from.

A moment counts as calm when it is outside every cover interval of every
preset, widened by a margin. Among the calm moments the quiet ones are
preferred: the picture there barely changes from frame to frame, so the still
looks like a held frame rather than a smear of motion.

The luminance series is sampled once per file with ffmpeg's signalstats filter
and kept on disk, because verify and the poster step both want it and a second
pass over a 2 hour title is not free.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, pstdev
from typing import Sequence

from . import PipelineError
from . import ffmpegtool
from .hideplan import (
    DEFAULT_CALM_MARGIN_MS,
    CoverInterval,
    calm_ranges,
    is_calm,
    nearest_calm_time_ms,
)
from .render import extract_jpeg, extract_still

DEFAULT_SAMPLE_FPS = 2.0
DEFAULT_POSTER_COUNT = 3
DEFAULT_POSTER_WIDTH = 640

_PTS_RE = re.compile(r"pts_time:([0-9.]+)")
_YAVG_RE = re.compile(r"lavfi\.signalstats\.YAVG=([0-9.]+)")


@dataclass
class LumaSeries:
    times_s: list[float]
    yavg: list[float]

    def to_dict(self) -> dict:
        return {"times_s": self.times_s, "yavg": self.yavg}

    @classmethod
    def from_dict(cls, data: dict) -> "LumaSeries":
        return cls(times_s=list(data.get("times_s", [])), yavg=list(data.get("yavg", [])))

    def window(self, centre_s: float, half_width_s: float) -> list[float]:
        return [
            value
            for time_s, value in zip(self.times_s, self.yavg)
            if abs(time_s - centre_s) <= half_width_s
        ]


def luminance_series(
    source: str | Path,
    *,
    metadata_path: str | Path,
    sample_fps: float = DEFAULT_SAMPLE_FPS,
) -> LumaSeries:
    """Average luminance over time, sampled at ``sample_fps``."""
    metadata_path = Path(metadata_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpegtool.run_ffmpeg(
        [
            "-i",
            str(source),
            "-vf",
            f"fps={sample_fps:g},scale=64:36,signalstats,"
            f"metadata=print:file={metadata_path}",
            "-an",
            "-sn",
            "-f",
            "null",
            "-",
        ]
    )
    times: list[float] = []
    values: list[float] = []
    pending_time: float | None = None
    for line in metadata_path.read_text(errors="replace").splitlines():
        match = _PTS_RE.search(line)
        if match:
            pending_time = float(match.group(1))
            continue
        match = _YAVG_RE.search(line)
        if match and pending_time is not None:
            times.append(pending_time)
            values.append(float(match.group(1)))
            pending_time = None
    if not times:
        raise PipelineError(f"no luminance samples came back for {source}")
    return LumaSeries(times_s=times, yavg=values)


def quietness(series: LumaSeries, time_s: float, half_width_s: float = 1.0) -> float:
    """Spread of luminance around a moment. Lower is quieter."""
    window = series.window(time_s, half_width_s)
    if len(window) < 2:
        return float("inf")
    return pstdev(window)


def choose_calm_times(
    intervals: Sequence[CoverInterval],
    duration_ms: float,
    *,
    count: int,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
    series: LumaSeries | None = None,
) -> list[float]:
    """Calm moments in milliseconds, spread across the title.

    Candidates are taken from the middle of each calm range and from an even
    grid inside it. When a luminance series is available the quietest
    candidate per slot wins.
    """
    if count <= 0:
        return []
    ranges = calm_ranges(intervals, duration_ms, margin_ms=margin_ms)
    if not ranges:
        raise PipelineError(
            "this title has no calm moment outside the flagged spans, so no "
            "poster, cover still or trickplay frame can be taken from it"
        )

    candidates: list[float] = []
    for start, end in ranges:
        span = end - start
        steps = max(1, min(8, int(span // 2000)))
        for step in range(steps):
            fraction = (step + 0.5) / steps
            candidates.append(start + span * fraction)
    candidates.sort()

    picks: list[float] = []
    for slot in range(count):
        target = duration_ms * (slot + 0.5) / count
        pool = sorted(candidates, key=lambda c: abs(c - target))[:5]
        if series is not None:
            pool.sort(key=lambda c: (quietness(series, c / 1000.0), abs(c - target)))
        for candidate in pool:
            if all(abs(candidate - chosen) > 1.0 for chosen in picks):
                picks.append(candidate)
                break
        else:
            if pool:
                picks.append(pool[0])
    picks.sort()
    return picks


def choose_cover_still_time(
    intervals: Sequence[CoverInterval],
    duration_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
    series: LumaSeries | None = None,
) -> float:
    """The single frame used as the cover inside the safe rendition."""
    picks = choose_calm_times(
        intervals, duration_ms, count=1, margin_ms=margin_ms, series=series
    )
    if not picks:
        raise PipelineError("no calm moment is available for the cover still")
    return picks[0]


def snap_to_calm(
    intervals: Sequence[CoverInterval],
    time_ms: float,
    duration_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> float:
    """Move a time to the nearest calm moment, or fail loudly."""
    if is_calm(intervals, time_ms, margin_ms=margin_ms):
        return time_ms
    snapped = nearest_calm_time_ms(intervals, time_ms, duration_ms, margin_ms=margin_ms)
    if snapped is None:
        raise PipelineError(
            f"no calm moment near {time_ms:.0f} ms, so no frame may be taken there"
        )
    return snapped


@dataclass
class Poster:
    time_ms: float
    path: Path
    width: int
    height: int

    def to_dict(self) -> dict:
        return {
            "time_ms": self.time_ms,
            "path": str(self.path),
            "width": self.width,
            "height": self.height,
        }


def extract_posters(
    source: str | Path,
    *,
    times_ms: Sequence[float],
    out_dir: str | Path,
    width: int,
    height: int,
) -> list[Poster]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    posters: list[Poster] = []
    for index, time_ms in enumerate(times_ms):
        path = out_dir / f"poster_{index:02d}.jpg"
        extract_jpeg(
            source,
            time_s=time_ms / 1000.0,
            out_path=path,
            width=width,
            height=height,
        )
        posters.append(Poster(time_ms=time_ms, path=path, width=width, height=height))
    return posters


def extract_cover_still(
    source: str | Path,
    *,
    time_ms: float,
    out_path: str | Path,
    width: int,
    height: int,
) -> Path:
    extract_still(
        source,
        time_s=time_ms / 1000.0,
        out_path=out_path,
        width=width,
        height=height,
    )
    return Path(out_path)


def mean_luma(series: LumaSeries) -> float:
    return fmean(series.yavg) if series.yavg else 0.0
