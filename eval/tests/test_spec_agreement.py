"""Cross-check: the numbers the evaluation reads out of SPEC_SOURCES.md are the numbers
flashmap was built with.

Two readings of one page. eval/conformance/spec.py parses the quoted text at run time and never
imports flashmap; flashmap's profiles.py carries the same numbers as Python literals. This test
is the only place the two meet, and it is a test rather than an import on purpose: if they ever
disagree, that is a finding about the analyser, and the conformance suite has to keep measuring
against the spec, not against the code.

If this goes red, do not edit the evaluation to agree. Read the spec file, work out which side
is wrong, and say so in the result file.
"""

from __future__ import annotations

import pytest

from conformance.spec import load_spec

flashmap = pytest.importorskip("flashmap", reason="flashmap is not installed in this env")


def test_the_two_readings_of_the_flash_thresholds_agree():
    spec = load_spec()
    profile = flashmap.WCAG
    assert spec.flash_limit_per_second == profile.flash_limit_per_second
    assert spec.window_ms == profile.window_ms
    assert spec.general_min_delta == pytest.approx(profile.general.min_delta)
    assert spec.general_dark_image_below == pytest.approx(profile.general.dark_image_below)
    assert spec.area_fraction_limit == pytest.approx(profile.area_fraction_limit)
    assert spec.red_saturated_ratio == pytest.approx(profile.red.saturated_red_ratio)
    assert spec.red_min_ucs_distance == pytest.approx(profile.red.min_ucs_distance)


def test_the_two_readings_of_the_ten_degree_field_agree():
    from flashmap.area import WCAG_FIELD_HEIGHT_FRACTION, WCAG_FIELD_WIDTH_FRACTION

    spec = load_spec()
    assert spec.field_width_fraction == pytest.approx(WCAG_FIELD_WIDTH_FRACTION)
    assert spec.field_height_fraction == pytest.approx(WCAG_FIELD_HEIGHT_FRACTION)


def test_the_two_readings_of_the_colour_arithmetic_agree():
    import numpy as np

    from flashmap import color as flashmap_color

    spec = load_spec()
    samples = np.asarray(
        [[0.0, 0.0, 0.0], [0.02, 0.5, 0.9], [1.0, 1.0, 1.0], [0.25, 0.25, 0.25]],
        dtype=np.float64,
    )
    assert np.allclose(spec.srgb_to_linear(samples), flashmap_color.srgb_to_linear(samples))
    linear = spec.srgb_to_linear(samples)
    assert np.allclose(
        spec.relative_luminance(linear), flashmap_color.relative_luminance(linear)
    )
    ours = spec.xyz(linear)
    theirs = flashmap_color.linear_rgb_to_xyz(linear)
    assert np.allclose(ours, theirs)
