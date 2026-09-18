"""Segments in, cover intervals out.

This is the Python twin of app/src/calmframes/coverSchedule.ts. The app and the
pipeline have to agree to the millisecond, because the pipeline pre-covers the
rendition and the app draws the cover on top of it. The rules, which must not
drift:

- a guard band widens every segment on both sides, default 500 ms;
- every interval is at least ``min_cover_ms`` long, grown at the end first so a
  cover never starts later than the guard band promised;
- intervals that overlap or touch are merged, so the cover cannot flicker off
  and on between two segments that nearly meet;
- if any part of a merged interval is red, the whole interval is red;
- a red interval is always opaque. WCAG's red rule keys on the ratio of red to
  total, which dimming does not change, so a dim cover cannot satisfy it.

Dim is allowed only for general intervals and only at 10 percent of the
original light or less (90 percent darker or more). Verify models the dim
case, because dim is the least protective cover the device may draw and so it
is the strictest test of the plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .flashmap_adapter import GENERAL, PATTERN, RED, MapSegment

DEFAULT_GUARD_BAND_MS = 500.0
DEFAULT_MIN_COVER_MS = 400.0

# A poster, a BIF frame or a cover still must be this far outside every cover
# interval before it counts as a calm moment.
DEFAULT_CALM_MARGIN_MS = 1000.0

# Dim mode ceiling: the covered picture may keep at most this share of its
# light, measured in linear light.
DIM_MAX_LUMINANCE = 0.10

OPAQUE = "opaque"
DIM = "dim"


@dataclass
class CoverInterval:
    start_ms: float
    end_ms: float
    reason: str = GENERAL
    sources: list[MapSegment] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms

    def contains(self, time_ms: float) -> bool:
        return self.start_ms <= time_ms < self.end_ms

    def to_dict(self) -> dict:
        return {
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "reason": self.reason,
            "sources": [s.to_dict() for s in self.sources],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoverInterval":
        return cls(
            start_ms=float(data["start_ms"]),
            end_ms=float(data["end_ms"]),
            reason=str(data.get("reason", GENERAL)),
            sources=[
                MapSegment(
                    start_ms=float(s["start_ms"]),
                    end_ms=float(s["end_ms"]),
                    reason=str(s.get("reason", GENERAL)),
                )
                for s in data.get("sources", [])
            ],
        )


def build_cover_intervals(
    segments: Sequence[MapSegment],
    *,
    guard_band_ms: float = DEFAULT_GUARD_BAND_MS,
    min_cover_ms: float = DEFAULT_MIN_COVER_MS,
    duration_ms: float | None = None,
) -> list[CoverInterval]:
    if guard_band_ms < 0:
        raise ValueError("guard_band_ms cannot be negative")
    if min_cover_ms < 0:
        raise ValueError("min_cover_ms cannot be negative")

    widened: list[CoverInterval] = []
    for segment in segments:
        if segment.end_ms <= segment.start_ms:
            continue
        start_ms = segment.start_ms - guard_band_ms
        end_ms = segment.end_ms + guard_band_ms
        if end_ms - start_ms < min_cover_ms:
            end_ms = start_ms + min_cover_ms
        if start_ms < 0:
            start_ms = 0.0
        if duration_ms is not None and end_ms > duration_ms:
            end_ms = duration_ms
        if end_ms <= start_ms:
            continue
        widened.append(
            CoverInterval(
                start_ms=start_ms,
                end_ms=end_ms,
                reason=(
                    segment.reason
                    if segment.reason in (RED, PATTERN)
                    else GENERAL
                ),
                sources=[segment],
            )
        )

    widened.sort(key=lambda i: (i.start_ms, i.end_ms))

    merged: list[CoverInterval] = []
    for interval in widened:
        previous = merged[-1] if merged else None
        if previous is not None and interval.start_ms <= previous.end_ms:
            previous.end_ms = max(previous.end_ms, interval.end_ms)
            # Strength wins when two intervals merge, and red is the strongest.
            # A pattern merged with a general flash stays a pattern, so the
            # merged interval keeps the opaque cover the pattern needs.
            if interval.reason == RED:
                previous.reason = RED
            elif interval.reason == PATTERN and previous.reason != RED:
                previous.reason = PATTERN
            previous.sources.extend(interval.sources)
            continue
        merged.append(
            CoverInterval(
                start_ms=interval.start_ms,
                end_ms=interval.end_ms,
                reason=interval.reason,
                sources=list(interval.sources),
            )
        )
    return merged


def interval_at(
    intervals: Sequence[CoverInterval], time_ms: float
) -> CoverInterval | None:
    for interval in intervals:
        if interval.contains(time_ms):
            return interval
    return None


def is_covered(intervals: Sequence[CoverInterval], time_ms: float) -> bool:
    return interval_at(intervals, time_ms) is not None


def cover_mode(interval: CoverInterval, *, allow_dim: bool = True) -> str:
    """What the device is allowed to draw over this interval.

    Red is always opaque, and so is a regular pattern. General may be dimmed
    when the household allows it, which is why verify models the dim case for
    general intervals.

    A pattern is opaque because dimming does not remove the hazard it is there
    for in a way this code can prove. Dim keeps a tenth of the linear light, and
    the pattern rule's bar to bar condition is a luminance difference, so dimming
    scales that difference down by the same tenth and a pattern just over the
    line would land under it. That may well be true, and it is not something to
    rest on arithmetic done once: verify models a dim cover by re-measuring the
    rendered result, and until a pattern has been through that measurement the
    opaque cover is the one we can defend.
    """
    if interval.reason in (RED, PATTERN):
        return OPAQUE
    return DIM if allow_dim else OPAQUE


def total_covered_ms(intervals: Sequence[CoverInterval]) -> float:
    return sum(interval.duration_ms for interval in intervals)


def is_calm(
    intervals: Sequence[CoverInterval],
    time_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> bool:
    """True when a still taken here shows nothing that was flagged.

    The margin keeps a poster away from the edge of a flagged span, where the
    flash is already building.
    """
    for interval in intervals:
        if interval.start_ms - margin_ms <= time_ms < interval.end_ms + margin_ms:
            return False
    return True


def is_fully_covered(
    intervals: Sequence[CoverInterval],
    time_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> bool:
    """True when the cover is already down here, with the margin to spare on both sides.

    Stricter than ``is_covered``, which only asks whether the time falls inside an interval.

    A picture taken here shows the cover still and not the film, so it is safe even though the
    moment is not calm. That matters for a title that flashes end to end: it has no calm moment
    at all, and refusing to give it a poster or a trickplay strip would refuse the title.

    This is only ever true of the kid safe rendition, where the cover is burned in. What holds
    the rendition to it is verify's cover_actually_drawn check, which measures the rendition
    against the cover still rather than taking the plan's word for it.
    """
    return any(
        interval.start_ms <= time_ms - margin_ms and time_ms + margin_ms <= interval.end_ms
        for interval in intervals
    )


def may_be_sampled(
    intervals: Sequence[CoverInterval],
    time_ms: float,
    duration_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> bool:
    """May a poster or a trickplay frame come from this moment?

    A calm moment always may. A moment under the cover may only when the title has no calm
    moment anywhere, which is the one case where the strict rule would refuse the title
    rather than protect anyone. While there is somewhere calm to take a picture from, that is
    where it has to come from.

    What must never happen either way is a frame taken close enough to a flagged span to show
    the flash building, which is what the margin is for.
    """
    if is_calm(intervals, time_ms, margin_ms=margin_ms):
        return True
    if calm_ranges(intervals, duration_ms, margin_ms=margin_ms):
        return False
    return is_fully_covered(intervals, time_ms, margin_ms=margin_ms)


def covered_ranges(
    intervals: Sequence[CoverInterval],
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> list[tuple[float, float]]:
    """The spans where the cover is down with the margin to spare on both sides."""
    ranges = [
        (interval.start_ms + margin_ms, interval.end_ms - margin_ms)
        for interval in intervals
    ]
    return sorted((a, b) for a, b in ranges if b - a > 0)


def calm_ranges(
    intervals: Sequence[CoverInterval],
    duration_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> list[tuple[float, float]]:
    """The spans of the title that no interval, widened by the margin, touches."""
    blocked = sorted(
        (max(0.0, i.start_ms - margin_ms), min(duration_ms, i.end_ms + margin_ms))
        for i in intervals
    )
    ranges: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in blocked:
        if start > cursor:
            ranges.append((cursor, min(start, duration_ms)))
        cursor = max(cursor, end)
        if cursor >= duration_ms:
            break
    if cursor < duration_ms:
        ranges.append((cursor, duration_ms))
    return [(a, b) for a, b in ranges if b - a > 0]


def nearest_calm_time_ms(
    intervals: Sequence[CoverInterval],
    time_ms: float,
    duration_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> float | None:
    """The calm time closest to ``time_ms``, or None when the title has none."""
    return _nearest_in_ranges(
        calm_ranges(intervals, duration_ms, margin_ms=margin_ms), time_ms
    )


def nearest_covered_time_ms(
    intervals: Sequence[CoverInterval],
    time_ms: float,
    *,
    margin_ms: float = DEFAULT_CALM_MARGIN_MS,
) -> float | None:
    """The closest moment that is under the cover, or None when nothing is."""
    return _nearest_in_ranges(covered_ranges(intervals, margin_ms=margin_ms), time_ms)


def _nearest_in_ranges(
    ranges: Sequence[tuple[float, float]], time_ms: float
) -> float | None:
    if not ranges:
        return None
    best: float | None = None
    best_distance = float("inf")
    for start, end in ranges:
        # Stay a hair inside the range so a time exactly on the boundary of a
        # widened interval is never picked.
        low = start
        high = max(start, end - 1.0)
        candidate = min(max(time_ms, low), high)
        distance = abs(candidate - time_ms)
        if distance < best_distance:
            best = candidate
            best_distance = distance
    return best


@dataclass
class HidePlan:
    profile: str
    source_sha256: str
    guard_band_ms: float
    min_cover_ms: float
    duration_ms: float
    allow_dim: bool
    intervals: list[CoverInterval]

    @property
    def has_red(self) -> bool:
        return any(i.reason == RED for i in self.intervals)

    def modes(self) -> list[str]:
        return [cover_mode(i, allow_dim=self.allow_dim) for i in self.intervals]

    def dim_intervals(self) -> list[CoverInterval]:
        return [
            i
            for i in self.intervals
            if cover_mode(i, allow_dim=self.allow_dim) == DIM
        ]

    def opaque_intervals(self) -> list[CoverInterval]:
        return [
            i
            for i in self.intervals
            if cover_mode(i, allow_dim=self.allow_dim) == OPAQUE
        ]

    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "source_sha256": self.source_sha256,
            "guard_band_ms": self.guard_band_ms,
            "min_cover_ms": self.min_cover_ms,
            "duration_ms": self.duration_ms,
            "allow_dim": self.allow_dim,
            "dim_max_luminance": DIM_MAX_LUMINANCE,
            "total_covered_ms": total_covered_ms(self.intervals),
            "intervals": [i.to_dict() for i in self.intervals],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HidePlan":
        return cls(
            profile=str(data["profile"]),
            source_sha256=str(data["source_sha256"]),
            guard_band_ms=float(data["guard_band_ms"]),
            min_cover_ms=float(data["min_cover_ms"]),
            duration_ms=float(data["duration_ms"]),
            allow_dim=bool(data.get("allow_dim", True)),
            intervals=[CoverInterval.from_dict(i) for i in data.get("intervals", [])],
        )


def build_hide_plan(
    map_doc,
    *,
    source_sha256: str,
    duration_ms: float,
    preset: str | None = None,
    guard_band_ms: float = DEFAULT_GUARD_BAND_MS,
    min_cover_ms: float = DEFAULT_MIN_COVER_MS,
    allow_dim: bool = True,
) -> HidePlan:
    """Turn a map into the plan the rendition and the player both follow.

    ``preset`` is the pipeline preset the map was made for. It can differ from
    the analyzer profile inside the map: extra-cautious is the wcag profile
    measured in a room window.

    A note on the last frame: the spec says a segment's ``end_ms`` includes the
    last offending frame, while an interval here is treated as ending at
    ``end_ms``. The guard band is 500 ms and a frame is tens of milliseconds,
    so the cover still runs well past the last flash.
    """
    intervals = build_cover_intervals(
        map_doc.segments,
        guard_band_ms=guard_band_ms,
        min_cover_ms=min_cover_ms,
        duration_ms=duration_ms,
    )
    return HidePlan(
        profile=preset or getattr(map_doc, "preset", None) or map_doc.profile or "unknown",
        source_sha256=source_sha256,
        guard_band_ms=guard_band_ms,
        min_cover_ms=min_cover_ms,
        duration_ms=duration_ms,
        allow_dim=allow_dim,
        intervals=intervals,
    )


def union_intervals(plans: Iterable[HidePlan]) -> list[CoverInterval]:
    """Every interval from every preset, merged.

    A still that is calm in this union is calm for every preset, which is what
    the shared cover still and the poster frames need.
    """
    everything: list[MapSegment] = []
    for plan in plans:
        for interval in plan.intervals:
            everything.append(
                MapSegment(
                    start_ms=interval.start_ms,
                    end_ms=interval.end_ms,
                    reason=interval.reason,
                )
            )
    return build_cover_intervals(everything, guard_band_ms=0.0, min_cover_ms=0.0)
