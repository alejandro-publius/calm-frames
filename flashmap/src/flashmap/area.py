"""Sliding area windows.

WCAG asks whether the flashing area fills more than 25% of *any* 10 degree visual field on the
screen, so one window is slid over every position on the picture and the busiest position wins.

The size of the 10 degree field comes from WCAG 2.2 Note 1: a 341 by 256 pixel block on a
1024 by 768 screen. That is 341/1024 of the width by 256/768 of the height, and the
Understanding document argues that the same fraction holds on any screen, so flashmap uses the
fractions rather than the pixel counts. See docs/SPEC_SOURCES.md sections 2 and 4.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "WCAG_FIELD_WIDTH_FRACTION",
    "WCAG_FIELD_HEIGHT_FRACTION",
    "AreaWindow",
    "wcag_reference_window",
    "max_coverage",
    "best_window",
]

# WCAG 2.2, definition of the thresholds, Note 1.
WCAG_FIELD_WIDTH_FRACTION = 341.0 / 1024.0
WCAG_FIELD_HEIGHT_FRACTION = 256.0 / 768.0


@dataclass(frozen=True)
class AreaWindow:
    name: str
    width_px: int
    height_px: int
    source: str
    detail: dict[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "name": self.name,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "source": self.source,
        }
        if self.detail:
            out.update(self.detail)
        return out


def wcag_reference_window(picture_width: int, picture_height: int) -> AreaWindow:
    """The 10 degree visual field at WCAG's reference geometry, as a box on the picture."""
    width = max(1, int(round(picture_width * WCAG_FIELD_WIDTH_FRACTION)))
    height = max(1, int(round(picture_height * WCAG_FIELD_HEIGHT_FRACTION)))
    return AreaWindow(
        name="wcag-10deg",
        width_px=width,
        height_px=height,
        source="WCAG 2.2 general flash and red flash thresholds, Note 1 (341/1024 by 256/768)",
    )


def max_coverage(mask: NDArray[np.bool_], window_height: int, window_width: int) -> float:
    """The largest share of any window of this size that the mask fills.

    The window is slid to every position that fits inside the mask. If the window is bigger
    than the picture it is clipped to the picture, which is the most conservative reading:
    a small screen cannot show more than a screenful.
    """
    array = np.asarray(mask, dtype=np.float64)
    height, width = array.shape
    win_h = max(1, min(int(window_height), height))
    win_w = max(1, min(int(window_width), width))

    integral = np.zeros((height + 1, width + 1), dtype=np.float64)
    integral[1:, 1:] = array.cumsum(axis=0).cumsum(axis=1)
    sums = (
        integral[win_h:, win_w:]
        - integral[:-win_h, win_w:]
        - integral[win_h:, :-win_w]
        + integral[:-win_h, :-win_w]
    )
    if sums.size == 0:
        return 0.0
    return float(sums.max()) / float(win_h * win_w)


def best_window(
    mask: NDArray[np.bool_], windows: list[AreaWindow]
) -> tuple[AreaWindow | None, float]:
    """The window that the mask fills most, and that fraction.

    Adding a window to the list can only raise the answer, never lower it. That is what makes
    the room rule able to add hides and never remove them.
    """
    best: AreaWindow | None = None
    best_value = 0.0
    for window in windows:
        value = max_coverage(mask, window.height_px, window.width_px)
        if best is None or value > best_value:
            best = window
            best_value = value
    return best, best_value
