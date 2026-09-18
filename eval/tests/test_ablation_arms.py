"""Each ablation arm has to actually switch its rule off, and nothing else.

An arm that only nudges a threshold looks like an ablation in the result file and measures
something else entirely, so the arms are checked against the shipped profile here rather than
trusted. These are unit checks: no clip is generated and no analyser runs.

To see them fail on purpose: set the red arm's ratio to 0.9 instead of above 1, or make the
default arm return a modified profile, and watch. Verified Sep 17, 2026.
"""

from __future__ import annotations

import pytest

flashmap = pytest.importorskip("flashmap", reason="flashmap is not installed in this env")

from ablations.run import ARMS, arm_profile  # noqa: E402


def test_the_default_arm_is_the_shipped_profile_itself():
    assert arm_profile("default") is flashmap.WCAG
    assert arm_profile("srgb_linearization_off") is flashmap.WCAG


def test_the_red_arm_puts_the_red_rule_out_of_reach():
    # A red ratio is R/(R+G+B) of non-negative values, so it can never exceed 1.
    assert arm_profile("red_rule_off").red.saturated_red_ratio > 1.0


def test_the_darker_image_arm_puts_that_condition_out_of_reach():
    # Relative luminance is normalised to 1 for white, so "below this" is always true.
    assert arm_profile("darker_image_rule_off").general.dark_image_below > 1.0


def test_the_area_arm_lets_any_flashing_area_qualify():
    # The analyser asks for coverage strictly greater than the limit, so zero means any.
    assert arm_profile("area_rule_off").area_fraction_limit == 0.0


@pytest.mark.parametrize("arm", [a for a in ARMS if a != "default"])
def test_an_arm_changes_one_thing_and_leaves_the_rest_alone(arm):
    base = flashmap.WCAG
    profile = arm_profile(arm)
    assert profile.flash_limit_per_second == base.flash_limit_per_second
    assert profile.window_ms == base.window_ms
    assert profile.area_window_mode == base.area_window_mode
    if arm != "area_rule_off":
        assert profile.area_fraction_limit == base.area_fraction_limit
    if arm != "red_rule_off":
        assert profile.red.min_ucs_distance == base.red.min_ucs_distance
    if arm != "darker_image_rule_off":
        assert profile.general.dark_image_below == base.general.dark_image_below
    assert profile.general.min_delta == base.general.min_delta


def test_an_unknown_arm_is_refused_rather_than_quietly_run_as_default():
    with pytest.raises(ValueError):
        arm_profile("no_such_arm")
