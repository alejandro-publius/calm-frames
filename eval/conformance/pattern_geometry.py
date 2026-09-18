#!/usr/bin/env python3
"""What a generated pattern clip looks like: the stripes, their area, how they move.

The renderer and the ground truth share this module on purpose. The ground truth has to be
independent of *flashmap*, not of the thing that drew the pixels: generated clips are only
worth measuring because the generator knows exactly what it drew. So every frame is built here
and both `pattern_run.py` and `pattern_truth.py` read it.

Nothing here imports flashmap.

The pattern is a block of exactly `2 * pairs` equal bars inside a centred rectangle that covers
`area_fraction` of the picture. Bars are equal whole steps along the stripe normal, so the pair
count a detector should find is a fact about the drawing rather than a matter of opinion, and
so is the area: the block is the pattern, and the block's share of the picture is its area.

Orientations: `vertical` (bars run up and down, the pattern varies along x), `horizontal`, and
`diagonal` (bars at 45 degrees, the pattern varies along x + y). Radial and dotted patterns are
in BT.1702-3's wording and are not drawn here; that gap is named in the report rather than
being left for a reader to notice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "ORIENTATIONS",
    "MOTIONS",
    "Block",
    "block_for",
    "draw_frame",
    "frame_times",
    "phase_for",
]

ORIENTATIONS = ("vertical", "horizontal", "diagonal")
MOTIONS = ("stationary", "drift", "reversing", "oscillating", "flashing")


@dataclass(frozen=True)
class Block:
    """The rectangle the stripes are drawn in, and how wide one bar is inside it."""

    x0: int
    y0: int
    x1: int
    y1: int
    bar_px: float
    """One bar, measured along the stripe normal, in coded pixels."""

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0

    @property
    def area(self) -> int:
        return max(0, self.width) * max(0, self.height)


def block_for(width: int, height: int, orientation: str, area_fraction: float, pairs: int) -> Block:
    """The centred block that covers `area_fraction` of the picture, and its bar width.

    For vertical stripes the block is full height and `area_fraction` of the width, so the area
    is exact and the stripe normal runs across the block's width. Horizontal is the transpose.
    For diagonal the block keeps the picture's aspect and is scaled by the square root, so the
    area is again `area_fraction`, and the normal extent is (w + h) / sqrt(2).
    """
    if orientation not in ORIENTATIONS:
        raise ValueError(f"unknown orientation {orientation!r}")
    if not 0.0 < area_fraction <= 1.0:
        raise ValueError("area_fraction must be over 0 and at most 1")
    if pairs < 1:
        raise ValueError("a pattern needs at least one pair")

    if orientation == "vertical":
        block_width = max(2 * pairs, int(round(width * area_fraction)))
        block_height = height
        extent = float(block_width)
    elif orientation == "horizontal":
        block_width = width
        block_height = max(2 * pairs, int(round(height * area_fraction)))
        extent = float(block_height)
    else:
        scale = math.sqrt(area_fraction)
        block_width = max(2 * pairs, int(round(width * scale)))
        block_height = max(2 * pairs, int(round(height * scale)))
        extent = (block_width + block_height) / math.sqrt(2.0)

    x0 = (width - block_width) // 2
    y0 = (height - block_height) // 2
    return Block(x0, y0, x0 + block_width, y0 + block_height, extent / (2.0 * pairs))


def phase_for(motion: str, index: int, bar_px: float, speed_bars: float) -> float:
    """How far the stripes have slid along their normal by frame `index`, in coded pixels.

    `speed_bars` is in bars per frame. Drift moves one way for ever. Oscillating goes four
    frames one way and four back, which is a pattern that changes direction without ever
    reversing contrast, so it exercises the changing branch on its own.
    """
    step = speed_bars * bar_px
    if motion == "drift":
        return index * step
    if motion == "oscillating":
        leg = index % 8
        return (leg if leg < 4 else 8 - leg) * step
    return 0.0


def draw_frame(
    width: int,
    height: int,
    *,
    orientation: str,
    block: Block,
    pairs: int,
    dark_code: int,
    bright_code: int,
    background_code: int,
    phase_px: float,
    invert: bool,
    lift_code: int,
) -> np.ndarray:
    """One frame, 8 bit grey in all three channels.

    `invert` swaps light and dark, for contrast reversal. `lift_code` is added to both bar
    codes, for a pattern that flashes as a whole while staying a pattern.
    """
    frame = np.full((height, width, 3), background_code, dtype=np.uint8)
    dark = int(min(255, max(0, dark_code + lift_code)))
    bright = int(min(255, max(0, bright_code + lift_code)))
    if invert:
        dark, bright = bright, dark

    ys = np.arange(block.y0, block.y1) - block.y0
    xs = np.arange(block.x0, block.x1) - block.x0
    if orientation == "vertical":
        normal = xs[None, :] + np.zeros((len(ys), 1))
    elif orientation == "horizontal":
        normal = ys[:, None] + np.zeros((1, len(xs)))
    else:
        normal = (xs[None, :] + ys[:, None]) / math.sqrt(2.0)

    index = np.floor((normal - phase_px) / block.bar_px).astype(np.int64)
    light = (index % 2) == 0
    patch = np.where(light[..., None], np.uint8(bright), np.uint8(dark)).astype(np.uint8)
    frame[block.y0 : block.y1, block.x0 : block.x1] = np.repeat(patch, 3, axis=2)
    return frame


def frame_times(duration_ms: float, fps: float) -> list[float]:
    count = int(round(duration_ms * fps / 1000.0))
    return [index * 1000.0 / fps for index in range(count)]
