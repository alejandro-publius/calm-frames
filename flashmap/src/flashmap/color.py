"""Colour maths.

Every constant in this file is quoted in docs/SPEC_SOURCES.md. Do not add a number here
without adding the quote and the link there first.

Sections referenced below are sections of docs/SPEC_SOURCES.md.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "SRGB_LINEAR_BREAK",
    "SRGB_LINEAR_SLOPE",
    "SRGB_OFFSET",
    "SRGB_SCALE",
    "SRGB_EXPONENT",
    "LUMA_R",
    "LUMA_G",
    "LUMA_B",
    "SRGB_TO_XYZ",
    "BT1886_GAMMA",
    "srgb_to_linear",
    "relative_luminance",
    "linear_rgb_to_xyz",
    "ucs_1976",
    "red_ratio",
    "bt1886_nits",
]

# Section 3, WCAG 2.2 relative luminance. "if RsRGB <= 0.04045 then R = RsRGB/12.92 else
# R = ((RsRGB+0.055)/1.055) ^ 2.4".
SRGB_LINEAR_BREAK = 0.04045
SRGB_LINEAR_SLOPE = 12.92
SRGB_OFFSET = 0.055
SRGB_SCALE = 1.055
SRGB_EXPONENT = 2.4

# Section 3. "L = 0.2126 * R + 0.7152 * G + 0.0722 * B".
LUMA_R = 0.2126
LUMA_G = 0.7152
LUMA_B = 0.0722

# Section 4, the matrix printed in Understanding SC 2.3.1. Rows are X, Y, Z.
SRGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ],
    dtype=np.float64,
)

# Section 5. The BT.1886 reference decoding function with a zero black level. The test
# tests/test_bt1702_table.py checks this against the published BT.1702-3 Table 1.
BT1886_GAMMA = 2.4


def srgb_to_linear(encoded: NDArray[np.floating]) -> NDArray[np.float32]:
    """Undo the sRGB transfer function.

    `encoded` holds sRGB values already divided by 255, so in the range 0 to 1. The result is
    linear light, also 0 to 1.
    """
    x = np.asarray(encoded, dtype=np.float32)
    low = x / np.float32(SRGB_LINEAR_SLOPE)
    high = np.power(
        (x + np.float32(SRGB_OFFSET)) / np.float32(SRGB_SCALE), np.float32(SRGB_EXPONENT)
    )
    return np.where(x <= np.float32(SRGB_LINEAR_BREAK), low, high).astype(np.float32)


def relative_luminance(linear_rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    """WCAG relative luminance from linear light RGB.

    `linear_rgb` has its channels on the last axis. The result drops that axis.
    """
    rgb = np.asarray(linear_rgb, dtype=np.float32)
    weights = np.array([LUMA_R, LUMA_G, LUMA_B], dtype=np.float32)
    return (rgb * weights).sum(axis=-1, dtype=np.float32)


def linear_rgb_to_xyz(linear_rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    """CIE XYZ tristimulus values from linear light RGB, channels on the last axis."""
    rgb = np.asarray(linear_rgb, dtype=np.float32)
    return (rgb @ SRGB_TO_XYZ.T.astype(np.float32)).astype(np.float32)


def ucs_1976(xyz: NDArray[np.floating]) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """CIE 1976 UCS chromaticity coordinates u' and v'.

    u' = 4X / (X + 15Y + 3Z) and v' = 9Y / (X + 15Y + 3Z). Black has no chromaticity, so the
    denominator is zero there and both coordinates are reported as zero. A pixel that dark is
    never a saturated red, so it cannot start or end a red transition either way.
    """
    x = np.asarray(xyz, dtype=np.float32)
    big_x = x[..., 0]
    big_y = x[..., 1]
    big_z = x[..., 2]
    denom = big_x + np.float32(15.0) * big_y + np.float32(3.0) * big_z
    safe = np.where(denom > np.float32(0.0), denom, np.float32(1.0))
    u = np.where(denom > 0.0, np.float32(4.0) * big_x / safe, np.float32(0.0))
    v = np.where(denom > 0.0, np.float32(9.0) * big_y / safe, np.float32(0.0))
    return u.astype(np.float32), v.astype(np.float32)


def red_ratio(linear_rgb: NDArray[np.floating]) -> NDArray[np.float32]:
    """R / (R + G + B) on linear light RGB, channels on the last axis.

    Pure black gets 0, which keeps it out of the saturated red state.
    """
    rgb = np.asarray(linear_rgb, dtype=np.float32)
    total = rgb.sum(axis=-1, dtype=np.float32)
    safe = np.where(total > np.float32(0.0), total, np.float32(1.0))
    return np.where(total > 0.0, rgb[..., 0] / safe, np.float32(0.0)).astype(np.float32)


def bt1886_nits(
    video_level: NDArray[np.floating], peak_nits: float = 200.0
) -> NDArray[np.float32]:
    """Screen luminance in cd/m2 for an SDR signal level, per BT.1702-3 Annex 2.

    `video_level` is the luma signal normalised so black is 0 and white is 1.
    """
    v = np.clip(np.asarray(video_level, dtype=np.float32), 0.0, None)
    return (np.float32(peak_nits) * np.power(v, np.float32(BT1886_GAMMA))).astype(np.float32)
