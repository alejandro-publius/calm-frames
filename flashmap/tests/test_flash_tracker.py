"""The two trackers on their own, fed numbers instead of pixels.

Working at this level pins things a clip cannot pin cleanly: the exact frame a flash lands on,
the pairing rule, and the boundary values of the thresholds.
"""

from __future__ import annotations

import numpy as np
import pytest

from flashmap import WCAG
from flashmap.area import AreaWindow, best_window, max_coverage
from flashmap.color import linear_rgb_to_xyz, ucs_1976
from flashmap.flash import GeneralFlashTracker, RedFlashTracker

SRGB_TO_XYZ_COLUMNS = {
    "red": (0.4124564, 0.2126729, 0.0193339),
    "green": (0.3575761, 0.7151522, 0.1191920),
    "blue": (0.1804375, 0.0721750, 0.9503041),
}


# ---- the published matrix, one coefficient at a time ---------------------------------------


@pytest.mark.parametrize("name", sorted(SRGB_TO_XYZ_COLUMNS))
def test_every_coefficient_of_the_srgb_to_xyz_matrix(name):
    """XYZ of a primary is that primary's column of the published matrix, so this checks all
    nine numbers rather than only the row that sums to one for white."""
    primary = {"red": [1.0, 0.0, 0.0], "green": [0.0, 1.0, 0.0], "blue": [0.0, 0.0, 1.0]}[name]
    xyz = linear_rgb_to_xyz(np.array([[primary]]))[0, 0]
    assert tuple(float(value) for value in xyz) == pytest.approx(
        SRGB_TO_XYZ_COLUMNS[name], abs=1e-6
    )


def test_the_ucs_of_pure_red_is_where_the_srgb_primary_sits():
    """sRGB red has CIE 1931 chromaticity x 0.640, y 0.330 (ITU-R BT.709-6 item 1.3), which is
    u' 0.4507, v' 0.5229 in the 1976 diagram."""
    xyz = linear_rgb_to_xyz(np.array([[[1.0, 0.0, 0.0]]]))
    u, v = ucs_1976(xyz)
    assert float(u[0, 0]) == pytest.approx(0.4507, abs=5e-4)
    assert float(v[0, 0]) == pytest.approx(0.5229, abs=5e-4)


# ---- the general tracker --------------------------------------------------------------------


def _run_general(values, min_delta=0.10, dark_below=0.80):
    tracker = GeneralFlashTracker(min_delta=min_delta, dark_image_below=dark_below)
    return [bool(tracker.step(np.array([[value]], dtype=np.float32))[0, 0]) for value in values]


def test_the_first_frame_can_never_be_a_flash():
    assert _run_general([0.0])[0] is False


def test_a_square_wave_gives_one_flash_per_cycle():
    flashes = _run_general([0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
    assert sum(flashes) == 3, flashes


def test_a_single_pulse_is_one_flash_and_not_two():
    assert sum(_run_general([0.0, 1.0, 0.0])) == 1


def test_a_staircase_up_is_never_a_flash():
    assert sum(_run_general([0.0, 0.2, 0.4, 0.6, 0.79])) == 0


def test_a_staircase_up_then_down_is_one_flash():
    assert sum(_run_general([0.0, 0.2, 0.4, 0.6, 0.4, 0.2, 0.0])) == 1


def test_a_swing_that_turns_around_below_the_threshold_leaves_the_tracker_facing_the_right_way():
    """The dip of 0.02 is too small to count. The pulse right after it still has to."""
    flashes = _run_general([0.10, 0.08, 1.0, 0.0, 1.0, 0.0])
    assert sum(flashes) >= 2, flashes


@pytest.mark.parametrize(
    ("swing", "expected"), [(0.099, 0), (0.101, 1)], ids=["under", "over"]
)
def test_the_ten_percent_boundary(swing, expected):
    assert sum(_run_general([0.0, swing, 0.0])) == expected


@pytest.mark.parametrize(
    ("darker", "expected"), [(0.799, 1), (0.801, 0)], ids=["dark enough", "too bright"]
)
def test_the_darker_image_boundary(darker, expected):
    assert sum(_run_general([darker, 1.0, darker])) == expected


# ---- the red tracker -------------------------------------------------------------------------


def _run_red(states, ratio_limit=0.8, distance_limit=0.2):
    tracker = RedFlashTracker(saturated_ratio=ratio_limit, min_distance=distance_limit)
    out = []
    for u, v, ratio in states:
        mask = tracker.step(
            np.array([[u]], dtype=np.float32),
            np.array([[v]], dtype=np.float32),
            np.array([[ratio]], dtype=np.float32),
        )
        out.append(bool(mask[0, 0]))
    return out


RED = (0.4507, 0.5229, 1.0)
GRAY = (0.1978, 0.4683, 1 / 3)
BLUE = (0.1754, 0.1579, 0.0)


def test_red_to_gray_and_back_is_one_flash():
    assert sum(_run_red([RED, GRAY, RED])) == 1


def test_going_into_red_and_staying_there_is_not_a_flash():
    assert sum(_run_red([GRAY, RED, RED, RED])) == 0


def test_a_colour_change_that_does_not_involve_red_is_not_a_transition():
    """Gray to blue is a long way in the 1976 UCS diagram and neither state is a saturated red.
    The move into red after it is a single transition, so there is no pair and no flash."""
    assert sum(_run_red([GRAY, BLUE, RED])) == 0


def test_a_move_shorter_than_the_ucs_limit_is_not_a_transition():
    near_red = (RED[0] - 0.05, RED[1], 0.9)
    just_under = (RED[0] - 0.05, RED[1], 0.5)
    assert sum(_run_red([near_red, just_under, near_red])) == 0


def test_a_redness_flip_with_no_chromaticity_move_does_not_shift_the_reference_state():
    """The reference state is the last confirmed transition, not the last frame. A pixel whose
    redness ticks over without its chromaticity moving has not made a transition, so the state
    the next move is measured from must not follow it."""
    near = (0.45, 0.52)
    far = (0.20, 0.47)
    assert np.hypot(near[0] - far[0], near[1] - far[1]) > 0.2
    sequence = [
        (near[0], near[1], 0.9),   # saturated red
        (near[0], near[1], 0.5),   # same colour point, no longer counted as red
        (far[0], far[1], 0.9),     # a long way off, saturated red again
        (near[0], near[1], 0.5),   # back, not red
    ]
    assert sum(_run_red(sequence)) == 0, "nothing here is a pair of opposing red transitions"


@pytest.mark.parametrize(("ratio", "expected"), [(0.79, 0), (0.81, 1)], ids=["under", "over"])
def test_the_saturated_red_ratio_boundary(ratio, expected):
    candidate = (RED[0], RED[1], ratio)
    assert sum(_run_red([GRAY, candidate, GRAY])) == expected


@pytest.mark.parametrize(
    ("distance", "expected"), [(0.19, 0), (0.21, 1)], ids=["under", "over"]
)
def test_the_ucs_distance_boundary(distance, expected):
    far = (GRAY[0] + distance, GRAY[1], 1.0)
    assert sum(_run_red([GRAY, far, GRAY])) == expected


def test_the_two_red_thresholds_overlap_against_a_neutral_background():
    """Worth knowing before trusting either number on its own. Against a mid gray, an sRGB
    colour whose red ratio sits between about 0.45 and 0.79 cannot get 0.2 away in the 1976 UCS
    diagram at all, so for gray to colour flashing the ratio only bites together with the
    distance. A clip test cannot separate the two. The boundary tests above do."""
    from flashmap.color import red_ratio, srgb_to_linear

    def state(rgb):
        linear = srgb_to_linear(np.array(rgb, dtype=np.float64)[None, None, :] / 255.0)
        xyz = linear_rgb_to_xyz(linear)
        u, v = ucs_1976(xyz)
        return float(red_ratio(linear)[0, 0]), float(u[0, 0]), float(v[0, 0])

    _, gray_u, gray_v = state((128, 128, 128))
    reachable = 0.0
    for red in range(0, 256, 9):
        for green in range(0, 256, 9):
            for blue in range(0, 256, 9):
                ratio, u, v = state((red, green, blue))
                if 0.5 <= ratio <= 0.78:
                    reachable = max(reachable, float(np.hypot(u - gray_u, v - gray_v)))
    assert reachable < WCAG.red.min_ucs_distance, reachable


def test_the_profile_thresholds_are_the_ones_the_tracker_boundaries_use():
    assert WCAG.general.min_delta == 0.10
    assert WCAG.general.dark_image_below == 0.80
    assert WCAG.red.saturated_red_ratio == 0.8
    assert WCAG.red.min_ucs_distance == 0.2


# ---- best_window -------------------------------------------------------------------------------


def test_best_window_returns_the_window_with_the_largest_coverage():
    rng = np.random.default_rng(11)
    mask = rng.random((24, 32)) < 0.25
    windows = [
        AreaWindow("wide", 20, 6, "test"),
        AreaWindow("tall", 6, 20, "test"),
        AreaWindow("small", 3, 3, "test"),
    ]
    values = {
        window.name: max_coverage(mask, window.height_px, window.width_px) for window in windows
    }
    chosen, value = best_window(mask, windows)
    assert chosen is not None
    assert value == pytest.approx(max(values.values()))
    assert values[chosen.name] == pytest.approx(value)
    assert value > min(values.values()), "the windows must not all score the same"


def test_best_window_on_an_empty_list_is_nothing():
    assert best_window(np.ones((4, 4), dtype=bool), []) == (None, 0.0)
