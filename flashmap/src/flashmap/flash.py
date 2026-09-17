"""Per pixel transition tracking, for general flashes and for red flashes.

WCAG says a transition is the change in relative luminance between adjacent peaks and valleys,
and a flash is two opposing transitions. Two things had to be decided because the spec does not
say them, and both are written up in docs/SPEC_SOURCES.md under implementation decisions:

1. a transition is declared on the first frame where the swing away from the last confirmed
   extreme is big enough, not later when the peak turns out to have been a peak;
2. transitions pair up without overlapping, so a square wave at 5 Hz is 5 flashes a second and
   not 9.

Both machines run on whole frames at once through numpy, so state is one array per pixel.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

__all__ = ["GeneralFlashTracker", "RedFlashTracker"]


class GeneralFlashTracker:
    """Counts general flashes per pixel from a stream of relative luminance frames."""

    def __init__(self, min_delta: float, dark_image_below: float) -> None:
        self.min_delta = float(min_delta)
        self.dark_image_below = float(dark_image_below)
        self._anchor: NDArray[np.float32] | None = None
        self._extreme: NDArray[np.float32] | None = None
        self._direction: NDArray[np.int8] | None = None
        self._pending: NDArray[np.int8] | None = None

    @property
    def started(self) -> bool:
        return self._anchor is not None

    def step(self, luminance: NDArray[np.floating]) -> NDArray[np.bool_]:
        """Feed one frame. Returns the pixels that completed a flash on this frame."""
        values = np.asarray(luminance, dtype=np.float32)
        if self._anchor is None:
            self._anchor = values.copy()
            self._extreme = values.copy()
            self._direction = np.zeros(values.shape, dtype=np.int8)
            self._pending = np.zeros(values.shape, dtype=np.int8)
            return np.zeros(values.shape, dtype=bool)

        anchor = self._anchor
        extreme = self._extreme
        direction = self._direction
        pending = self._pending
        assert extreme is not None and direction is not None and pending is not None

        # A swing that turned around before it was big enough to count is a peak or a valley
        # all the same. Move the anchor onto it and start measuring the new swing from there,
        # otherwise the tracker would sit facing the wrong way for the rest of the file.
        reversing = ((direction > 0) & (values < extreme)) | (
            (direction < 0) & (values > extreme)
        )
        anchor = np.where(reversing, extreme, anchor).astype(np.float32)
        direction = np.where(reversing, np.int8(0), direction).astype(np.int8)
        extreme = np.where(reversing, anchor, extreme).astype(np.float32)

        unknown = direction == 0
        direction = np.where(
            unknown & (values > anchor),
            np.int8(1),
            np.where(unknown & (values < anchor), np.int8(-1), direction),
        ).astype(np.int8)

        extreme = np.where(
            direction > 0,
            np.maximum(extreme, values),
            np.where(direction < 0, np.minimum(extreme, values), extreme),
        ).astype(np.float32)

        delta = extreme - anchor
        darker = np.minimum(anchor, extreme)
        confirmed = (np.abs(delta) >= np.float32(self.min_delta)) & (
            darker < np.float32(self.dark_image_below)
        )
        sign = np.where(delta > 0, np.int8(1), np.int8(-1)).astype(np.int8)

        flashed = confirmed & (pending != 0) & (pending != sign)
        pending = np.where(
            flashed, np.int8(0), np.where(confirmed, sign, pending)
        ).astype(np.int8)
        anchor = np.where(confirmed, extreme, anchor).astype(np.float32)
        extreme = np.where(confirmed, anchor, extreme).astype(np.float32)
        direction = np.where(confirmed, np.int8(0), direction).astype(np.int8)

        self._anchor = anchor
        self._extreme = extreme
        self._direction = direction
        self._pending = pending
        return flashed


class RedFlashTracker:
    """Counts red flashes per pixel.

    A pixel is in the saturated red state when R/(R + G + B) is at or above the ratio. A
    transition is a move into or out of that state that also moves further than `min_distance`
    in the CIE 1976 UCS chromaticity diagram. Entering and leaving are the opposing pair.
    """

    def __init__(self, saturated_ratio: float, min_distance: float) -> None:
        self.saturated_ratio = float(saturated_ratio)
        self.min_distance = float(min_distance)
        self._u: NDArray[np.float32] | None = None
        self._v: NDArray[np.float32] | None = None
        self._is_red: NDArray[np.bool_] | None = None
        self._pending: NDArray[np.int8] | None = None

    @property
    def started(self) -> bool:
        return self._u is not None

    def step(
        self,
        u_prime: NDArray[np.floating],
        v_prime: NDArray[np.floating],
        red_ratio: NDArray[np.floating],
    ) -> NDArray[np.bool_]:
        u = np.asarray(u_prime, dtype=np.float32)
        v = np.asarray(v_prime, dtype=np.float32)
        is_red = np.asarray(red_ratio, dtype=np.float32) >= np.float32(self.saturated_ratio)

        if self._u is None:
            self._u = u.copy()
            self._v = v.copy()
            self._is_red = is_red.copy()
            self._pending = np.zeros(u.shape, dtype=np.int8)
            return np.zeros(u.shape, dtype=bool)

        anchor_u = self._u
        anchor_v = self._v
        anchor_red = self._is_red
        pending = self._pending
        assert anchor_v is not None and anchor_red is not None and pending is not None

        distance = np.hypot(u - anchor_u, v - anchor_v)
        confirmed = (is_red != anchor_red) & (distance > np.float32(self.min_distance))
        sign = np.where(is_red, np.int8(1), np.int8(-1)).astype(np.int8)

        flashed = confirmed & (pending != 0) & (pending != sign)
        pending = np.where(
            flashed, np.int8(0), np.where(confirmed, sign, pending)
        ).astype(np.int8)

        self._u = np.where(confirmed, u, anchor_u).astype(np.float32)
        self._v = np.where(confirmed, v, anchor_v).astype(np.float32)
        self._is_red = np.where(confirmed, is_red, anchor_red)
        self._pending = pending
        return flashed
