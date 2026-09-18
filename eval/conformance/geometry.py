#!/usr/bin/env python3
"""What each generated clip looks like: the picture, the flashing region, the frame timing.

The generator and the ground truth share this module on purpose. The ground truth has to be
independent of *flashmap*, not of the thing that drew the pixels: the whole reason generated
clips can carry a true answer is that the generator knows exactly what it drew. So the shape of
the region and the timestamp of every frame are computed once, here, and both the renderer and
truth.py read them.

Nothing here imports flashmap.

Coordinates are integer pixels on the coded frame. The picture is the coded frame minus any
letterbox bars, and every area fraction in a clip spec is a fraction of the picture, never of
the coded frame (flashmap/docs/SPEC_SOURCES.md, implementation decision 5).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "Rect",
    "picture_rect",
    "region_rects",
    "frame_plan",
    "SHAPES",
    "TIMING_PATTERNS",
]

SHAPES = ("center_rect", "offset_rect", "scatter", "band")
TIMING_PATTERNS = ("cfr", "vfr_alternating", "vfr_dropped")


@dataclass(frozen=True)
class Rect:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0

    @property
    def area(self) -> int:
        return max(0, self.width) * max(0, self.height)

    def as_list(self) -> list[int]:
        return [self.x0, self.y0, self.x1, self.y1]


def picture_rect(width: int, height: int, letterbox_fraction: float = 0.0) -> Rect:
    """The picture inside the coded frame.

    `letterbox_fraction` is the share of the coded height taken by the two black bars together,
    split evenly top and bottom. Bar heights are rounded to even numbers so that 4:2:0 chroma
    siting cannot smear a bar edge into the picture.
    """
    if not 0.0 <= letterbox_fraction < 0.9:
        raise ValueError("letterbox_fraction must be at least 0 and well under 1")
    bar = int(round(height * letterbox_fraction / 2.0))
    bar -= bar % 2
    return Rect(0, bar, width, height - bar)


def region_rects(
    picture: Rect, shape: str, area_fraction: float, *, blocks: int = 9
) -> list[Rect]:
    """The rectangles that flash, laid out inside the picture.

    Every shape is built to hit `area_fraction` of the picture area as closely as integer
    pixels allow. The exact drawn area comes back in the rectangles, and truth.py measures what
    is actually there rather than what was asked for.

    - center_rect: one rectangle in the middle, picture aspect ratio.
    - offset_rect: the same rectangle pushed into the top left, so it straddles a different set
      of 10 degree window placements.
    - scatter: `blocks` equal squares on a grid across the whole picture, which is the case
      where the total flashing area is large but no single 10 degree field sees much of it.
    - band: a full width horizontal band, the case where the area rule turns on the height of
      the band alone.
    """
    if shape not in SHAPES:
        raise ValueError(f"unknown shape {shape!r}")
    if not 0.0 < area_fraction <= 1.0:
        raise ValueError("area_fraction must be over 0 and at most 1")

    pw, ph = picture.width, picture.height
    target = area_fraction * pw * ph

    if shape in ("center_rect", "offset_rect"):
        scale = math.sqrt(area_fraction)
        w = max(2, int(round(pw * scale)))
        h = max(2, int(round(ph * scale)))
        w -= w % 2
        h -= h % 2
        w = max(2, min(w, pw))
        h = max(2, min(h, ph))
        if shape == "center_rect":
            x0 = (pw - w) // 2
            y0 = (ph - h) // 2
        else:
            x0 = max(0, int(round(pw * 0.04)))
            y0 = max(0, int(round(ph * 0.06)))
            x0 = min(x0, pw - w)
            y0 = min(y0, ph - h)
        x0 -= x0 % 2
        y0 -= y0 % 2
        return [Rect(picture.x0 + x0, picture.y0 + y0, picture.x0 + x0 + w, picture.y0 + y0 + h)]

    if shape == "band":
        h = max(2, int(round(ph * area_fraction)))
        h -= h % 2
        h = max(2, min(h, ph))
        y0 = (ph - h) // 2
        y0 -= y0 % 2
        return [Rect(picture.x0, picture.y0 + y0, picture.x0 + pw, picture.y0 + y0 + h)]

    # scatter: a grid of equal squares, spread so that no 10 degree field holds many of them
    side_count = int(round(math.sqrt(blocks)))
    per_block = target / (side_count * side_count)
    side = max(2, int(round(math.sqrt(per_block))))
    side -= side % 2
    # A block can grow to its whole grid cell and no further, or blocks would overlap and the
    # drawn area would stop being the sum of their areas.
    side = max(2, min(side, pw // side_count, ph // side_count))
    rects: list[Rect] = []
    for row in range(side_count):
        for column in range(side_count):
            cx = int(round(pw * (column + 0.5) / side_count))
            cy = int(round(ph * (row + 0.5) / side_count))
            x0 = min(max(0, cx - side // 2), pw - side)
            y0 = min(max(0, cy - side // 2), ph - side)
            x0 -= x0 % 2
            y0 -= y0 % 2
            rects.append(
                Rect(
                    picture.x0 + x0,
                    picture.y0 + y0,
                    picture.x0 + x0 + side,
                    picture.y0 + y0 + side,
                )
            )
    return rects


def frame_plan(
    *,
    duration_ms: float,
    fps: float,
    timing: str,
    flash_start_ms: float,
    flash_hz: float,
    seed: int = 0,
) -> tuple[list[float], list[int]]:
    """Every frame of the clip: its presentation time in ms and which state it shows.

    State 0 is the calm state, which is also the state the lead-in sits in. From
    `flash_start_ms` the region alternates as a square wave at `flash_hz`, so one full cycle is
    one flash (a pair of opposing transitions) and the rate in hertz is the number of flashes
    per second the picture is asked for. What the frames actually show can be fewer, which is
    the point of the frame rate axis: a 30 Hz square wave sampled at 30 fps never changes.

    Timing patterns:
      - cfr: frame k at k / fps.
      - vfr_alternating: frame durations alternate between 1/fps and 1/(2 fps) seconds, so the
        stream has real, uneven timestamps rather than a constant rate with a variable flag.
      - vfr_dropped: a constant grid at fps with a deterministic 1 in 7 of the frames missing.
    """
    if timing not in TIMING_PATTERNS:
        raise ValueError(f"unknown timing pattern {timing!r}")
    if fps <= 0:
        raise ValueError("fps must be positive")

    times: list[float] = []
    if timing == "cfr":
        count = int(round(duration_ms * fps / 1000.0))
        times = [k * 1000.0 / fps for k in range(count)]
    elif timing == "vfr_alternating":
        long_step = 1000.0 / fps
        short_step = long_step / 2.0
        t = 0.0
        index = 0
        while t < duration_ms - 1e-9:
            times.append(t)
            t += long_step if index % 2 == 0 else short_step
            index += 1
    else:  # vfr_dropped
        count = int(round(duration_ms * fps / 1000.0))
        offset = seed % 7
        times = [
            k * 1000.0 / fps for k in range(count) if (k + offset) % 7 != 0 or k == 0
        ]

    states: list[int] = []
    for t in times:
        if t < flash_start_ms or flash_hz <= 0:
            states.append(0)
        else:
            phase = (t - flash_start_ms) * 2.0 * flash_hz / 1000.0
            states.append(int(math.floor(phase + 1e-9)) % 2)
    return times, states
