"""Colour maths against the wording in flashmap/docs/SPEC_SOURCES.md sections 3 and 4."""

from __future__ import annotations

import math

import numpy as np
import pytest

from flashmap import color


def test_srgb_break_point_uses_the_linear_segment():
    # WCAG: "if RsRGB <= 0.04045 then R = RsRGB/12.92 else R = ((RsRGB+0.055)/1.055) ^ 2.4".
    # Pin the break from both sides, or moving it would go unnoticed.
    below = 0.04
    assert color.srgb_to_linear(np.array([below])).item() == pytest.approx(below / 12.92, rel=1e-6)

    # The two segments meet at the break point, so a value right next to it cannot tell them
    # apart. This one is well clear of it and the two readings are more than twice apart.
    above = 0.2
    linear_reading = above / 12.92
    power_reading = ((above + 0.055) / 1.055) ** 2.4
    assert power_reading > 2 * linear_reading, "pick a value where the two segments differ"
    assert color.srgb_to_linear(np.array([above])).item() == pytest.approx(
        power_reading, rel=1e-6
    )


def test_srgb_above_the_break_point_uses_the_power_segment():
    value = 0.5
    expected = ((value + 0.055) / 1.055) ** 2.4
    assert color.srgb_to_linear(np.array([value])).item() == pytest.approx(expected, rel=1e-6)


def test_srgb_is_continuous_at_the_break_point():
    below = color.srgb_to_linear(np.array([0.04045])).item()
    above = color.srgb_to_linear(np.array([0.040451])).item()
    assert abs(below - above) < 1e-5


def test_black_and_white_relative_luminance():
    black = color.relative_luminance(color.srgb_to_linear(np.zeros((1, 1, 3))))
    white = color.relative_luminance(color.srgb_to_linear(np.ones((1, 1, 3))))
    assert black.item() == pytest.approx(0.0, abs=1e-7)
    assert white.item() == pytest.approx(1.0, abs=1e-6)


def test_relative_luminance_weights_are_the_published_ones():
    red = color.relative_luminance(np.array([[[1.0, 0.0, 0.0]]]))
    green = color.relative_luminance(np.array([[[0.0, 1.0, 0.0]]]))
    blue = color.relative_luminance(np.array([[[0.0, 0.0, 1.0]]]))
    assert red.item() == pytest.approx(0.2126, abs=1e-6)
    assert green.item() == pytest.approx(0.7152, abs=1e-6)
    assert blue.item() == pytest.approx(0.0722, abs=1e-6)


def test_xyz_of_white_is_d65_and_y_is_one():
    xyz = color.linear_rgb_to_xyz(np.array([[[1.0, 1.0, 1.0]]]))[0, 0]
    assert xyz[1].item() == pytest.approx(1.0, abs=1e-5)
    # D65 white in the CIE 1976 UCS diagram.
    u, v = color.ucs_1976(xyz[None, None, :])
    assert u.item() == pytest.approx(0.1978, abs=5e-4)
    assert v.item() == pytest.approx(0.4683, abs=5e-4)


def test_ucs_matches_the_published_formula_for_a_sample_colour():
    linear = np.array([[[0.3, 0.1, 0.05]]])
    xyz = color.linear_rgb_to_xyz(linear)[0, 0]
    big_x, big_y, big_z = (v.item() for v in xyz)
    denominator = big_x + 15 * big_y + 3 * big_z
    u, v = color.ucs_1976(xyz[None, None, :])
    assert u.item() == pytest.approx(4 * big_x / denominator, rel=1e-5)
    assert v.item() == pytest.approx(9 * big_y / denominator, rel=1e-5)


def test_ucs_of_black_is_defined_and_not_a_nan():
    u, v = color.ucs_1976(np.zeros((1, 1, 3)))
    assert not math.isnan(u.item())
    assert not math.isnan(v.item())
    assert u.item() == 0.0 and v.item() == 0.0


def test_red_ratio_of_pure_red_is_one_and_of_gray_is_a_third():
    assert color.red_ratio((np.array([[[1.0, 0.0, 0.0]]]))) == pytest.approx(1.0)
    assert color.red_ratio((np.array([[[0.5, 0.5, 0.5]]]))) == pytest.approx(1 / 3)
    assert color.red_ratio((np.zeros((1, 1, 3)))) == 0.0


def test_pure_red_is_saturated_but_orange_is_not():
    # R/(R+G+B) >= 0.8 is the saturated red state, SPEC_SOURCES section 2 Note 3.
    pure_red = color.red_ratio((np.array([[[1.0, 0.0, 0.0]]])))
    orange = color.red_ratio((np.array([[[1.0, 0.5, 0.0]]])))
    assert pure_red >= 0.8
    assert orange < 0.8
