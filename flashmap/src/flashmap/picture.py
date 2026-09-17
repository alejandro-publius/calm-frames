"""Finding the picture inside the coded frame.

Letterbox bars (top and bottom) and pillarbox bars (left and right) are not picture. If they
were counted, every area fraction would come out smaller than it really is and content would
pass that should not. So flashmap finds the bars, drops them, measures on what is left, and
writes the geometry it removed into the sidecar.

None of the numbers in `LetterboxSettings` come from a spec. They are detector tuning and
docs/SPEC_SOURCES.md says so under implementation decision 6.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

__all__ = ["LetterboxSettings", "PictureRect", "detect_picture"]


@dataclass(frozen=True)
class LetterboxSettings:
    max_bar_luminance: float = 0.02
    """A row or column counts as a bar only if its brightest pixel, across every sampled
    frame, stays at or below this relative luminance."""

    max_bar_fraction: float = 0.45
    """No single bar may eat more than this share of its dimension."""

    max_total_bar_fraction: float = 0.80
    """Opposite bars together may not eat more than this share of a dimension."""

    erode_px: int = 1
    """Analysis pixels trimmed from each edge that had a bar, because scaling blends the last
    bar row into the first picture row."""


@dataclass(frozen=True)
class PictureRect:
    left: int
    top: int
    width: int
    height: int
    letterbox: bool
    pillarbox: bool
    frame_width: int
    frame_height: int

    def crop(self, array: NDArray[np.floating]) -> NDArray[np.floating]:
        return array[self.top : self.top + self.height, self.left : self.left + self.width]

    def scaled_to(self, width: int, height: int) -> dict[str, int]:
        """The same rectangle expressed in another frame size, for the sidecar."""
        sx = width / self.frame_width
        sy = height / self.frame_height
        return {
            "left": int(round(self.left * sx)),
            "top": int(round(self.top * sy)),
            "width": int(round(self.width * sx)),
            "height": int(round(self.height * sy)),
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "measured_on": "picture",
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
            "letterbox": self.letterbox,
            "pillarbox": self.pillarbox,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "note": (
                "Area fractions in this map were measured on the picture rectangle above, "
                "not on the full coded frame. Letterbox and pillarbox bars were removed first."
            ),
        }


def _leading_run(flags: NDArray[np.bool_]) -> int:
    count = 0
    for value in flags:
        if not value:
            break
        count += 1
    return count


def detect_picture(
    luminances: list[NDArray[np.floating]],
    settings: LetterboxSettings = LetterboxSettings(),
) -> PictureRect:
    """Find the picture rectangle from a handful of sampled relative luminance frames."""
    if not luminances:
        raise ValueError("detect_picture needs at least one sampled frame")
    stack = np.maximum.reduce([np.asarray(frame, dtype=np.float32) for frame in luminances])
    height, width = stack.shape

    row_max = stack.max(axis=1)
    col_max = stack.max(axis=0)
    dark_rows = row_max <= settings.max_bar_luminance
    dark_cols = col_max <= settings.max_bar_luminance

    top = _leading_run(dark_rows)
    bottom = _leading_run(dark_rows[::-1])
    left = _leading_run(dark_cols)
    right = _leading_run(dark_cols[::-1])

    # A frame that is dark all over is not a letterboxed frame, it is a dark frame.
    if top + bottom >= height:
        top = bottom = 0
    if left + right >= width:
        left = right = 0

    top = min(top, int(height * settings.max_bar_fraction))
    bottom = min(bottom, int(height * settings.max_bar_fraction))
    left = min(left, int(width * settings.max_bar_fraction))
    right = min(right, int(width * settings.max_bar_fraction))

    if top + bottom > height * settings.max_total_bar_fraction:
        top = bottom = 0
    if left + right > width * settings.max_total_bar_fraction:
        left = right = 0

    letterbox = top > 0 or bottom > 0
    pillarbox = left > 0 or right > 0

    if top > 0:
        top += settings.erode_px
    if bottom > 0:
        bottom += settings.erode_px
    if left > 0:
        left += settings.erode_px
    if right > 0:
        right += settings.erode_px

    picture_height = max(1, height - top - bottom)
    picture_width = max(1, width - left - right)
    return PictureRect(
        left=left,
        top=top,
        width=picture_width,
        height=picture_height,
        letterbox=letterbox,
        pillarbox=pillarbox,
        frame_width=width,
        frame_height=height,
    )
