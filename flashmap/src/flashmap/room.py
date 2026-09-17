"""The room rule.

A household tells flashmap its TV diagonal and how far away people sit. From those two numbers
flashmap works out how much of the picture a 10 degree visual field really covers in that room,
and adds that as a second area window.

The 10 degrees is WCAG's, from docs/SPEC_SOURCES.md section 2. The rest is trigonometry, not a
threshold: a field of 10 degrees at distance d spans 2 * d * tan(5 degrees).

The room window is always used **in addition to** the WCAG window, never instead of it. A
segment is hidden when the WCAG window fails or the room window fails. Because the analyser
takes the largest coverage over the list of windows, adding a room window can only push
coverage up, so a room setting can only add hides. `flashmap.analyze` has a check that asserts
this, and tests/test_room.py proves it on real clips.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .area import AreaWindow

__all__ = ["RoomSetting", "FIELD_DEGREES", "room_window"]

# WCAG 2.2, "any 10 degree visual field on the screen". SPEC_SOURCES section 2.
FIELD_DEGREES = 10.0


@dataclass(frozen=True)
class RoomSetting:
    tv_diagonal_in: float
    seat_distance_in: float
    display_aspect_w: float = 16.0
    display_aspect_h: float = 9.0

    def __post_init__(self) -> None:
        if self.tv_diagonal_in <= 0:
            raise ValueError("tv diagonal must be positive")
        if self.seat_distance_in <= 0:
            raise ValueError("seat distance must be positive")

    @property
    def display_width_in(self) -> float:
        ratio = self.display_aspect_w / math.hypot(self.display_aspect_w, self.display_aspect_h)
        return self.tv_diagonal_in * ratio

    @property
    def display_height_in(self) -> float:
        ratio = self.display_aspect_h / math.hypot(self.display_aspect_w, self.display_aspect_h)
        return self.tv_diagonal_in * ratio

    @property
    def field_inches(self) -> float:
        """How wide a 10 degree visual field is on the screen surface, in inches."""
        return 2.0 * self.seat_distance_in * math.tan(math.radians(FIELD_DEGREES / 2.0))

    def as_dict(self) -> dict[str, object]:
        return {
            "tv_diagonal_in": self.tv_diagonal_in,
            "seat_distance_in": self.seat_distance_in,
            "display_aspect": f"{self.display_aspect_w:g}:{self.display_aspect_h:g}",
            "display_width_in": round(self.display_width_in, 3),
            "display_height_in": round(self.display_height_in, 3),
            "field_degrees": FIELD_DEGREES,
            "field_inches": round(self.field_inches, 3),
        }


def room_window(
    setting: RoomSetting,
    frame_width: int,
    frame_height: int,
    picture_width: int,
    picture_height: int,
) -> AreaWindow:
    """The 10 degree field for this room, as a box in analysis pixels on the picture.

    The whole coded frame is what fills the TV, bars included, so pixels per inch comes from
    the frame size. The window is then clipped to the picture, because a window bigger than the
    picture cannot be filled by more picture than there is.
    """
    px_per_inch_x = frame_width / setting.display_width_in
    px_per_inch_y = frame_height / setting.display_height_in
    width = max(1, int(round(setting.field_inches * px_per_inch_x)))
    height = max(1, int(round(setting.field_inches * px_per_inch_y)))
    width = min(width, picture_width)
    height = min(height, picture_height)
    return AreaWindow(
        name="room-10deg",
        width_px=width,
        height_px=height,
        source="10 degrees from WCAG 2.2, sized by TV diagonal and seat distance",
        detail={"room": setting.as_dict()},
    )
