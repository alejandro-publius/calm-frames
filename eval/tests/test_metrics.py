"""Tests for eval/metrics.py, the one place intervals become windows and windows become rates.

The Wilson test does not compare against a number someone remembered. It checks that each
endpoint solves the equation the interval is defined by, found independently by bisection. That
catches an algebra slip that a single memorised pair of digits would sail past.

To see these fail on purpose: change `overlap > 0` to `overlap >= 0` in windows_from_intervals,
or drop the `z * z / (4 * n * n)` term from wilson, and watch. Verified Sep 17, 2026.
"""

from __future__ import annotations

import math

import pytest

from metrics import (
    Z_95,
    bootstrap_groups,
    confusion,
    rate_with_interval,
    wilson,
    window_count,
    windows_from_intervals,
)


def test_a_segment_inside_one_window_marks_only_that_window():
    assert windows_from_intervals([(1200, 1800)], n_windows=3) == {1}


def test_any_overlap_marks_every_window_it_touches():
    assert windows_from_intervals([(400, 1400)], n_windows=3) == {0, 1}


def test_touching_a_boundary_is_not_overlapping_it():
    assert windows_from_intervals([(1000, 2000)], n_windows=3) == {1}


def test_the_half_window_rule_drops_a_sliver():
    intervals = [(900, 1100)]
    assert windows_from_intervals(intervals, n_windows=3) == {0, 1}
    assert windows_from_intervals(intervals, n_windows=3, min_overlap=0.5) == set()


def test_the_half_window_rule_keeps_a_full_window():
    assert windows_from_intervals([(1000, 2000)], n_windows=3, min_overlap=0.5) == {1}


def test_windows_are_measured_from_the_first_presentation_timestamp():
    # A file whose first frame is at 5000 ms has its window 0 there, not at zero.
    assert windows_from_intervals([(5200, 5400)], n_windows=3, origin_ms=5000) == {0}


def test_an_empty_or_backwards_interval_marks_nothing():
    assert windows_from_intervals([(1500, 1500), (2000, 1000)], n_windows=3) == set()


def test_intervals_past_the_end_are_clipped_not_counted():
    assert windows_from_intervals([(2500, 9000)], n_windows=3) == {2}


def test_window_count_drops_the_trailing_remainder():
    assert window_count(2999.0) == 2
    assert window_count(3000.0) == 3
    assert window_count(0.0) == 0


def test_confusion_counts_only_the_universe_it_is_given():
    counts = confusion({0, 1}, {1, 2}, universe=[1, 2])
    assert counts == {"tp": 1, "fp": 0, "fn": 1, "tn": 0}


def _wilson_endpoint_by_bisection(successes: int, trials: int, upper: bool) -> float:
    """Solve |phat - p| = z sqrt(p(1-p)/n) for p, without using the closed form."""
    phat = successes / trials

    def gap(p: float) -> float:
        return abs(phat - p) - Z_95 * math.sqrt(max(p * (1 - p), 0.0) / trials)

    low, high = (phat, 1.0) if upper else (0.0, phat)
    for _ in range(200):
        mid = (low + high) / 2
        inside = gap(mid) <= 0
        if upper:
            if inside:
                low = mid
            else:
                high = mid
        else:
            if inside:
                high = mid
            else:
                low = mid
    return (low + high) / 2


@pytest.mark.parametrize(
    "successes,trials", [(1, 10), (5, 10), (9, 10), (37, 100), (500, 1000), (3, 7)]
)
def test_wilson_endpoints_solve_the_equation_that_defines_them(successes, trials):
    low, high = wilson(successes, trials)
    assert low == pytest.approx(
        _wilson_endpoint_by_bisection(successes, trials, upper=False), abs=1e-9
    )
    assert high == pytest.approx(
        _wilson_endpoint_by_bisection(successes, trials, upper=True), abs=1e-9
    )


def test_wilson_at_the_ends_stays_inside_zero_and_one_and_says_something():
    low, high = wilson(0, 20)
    assert low == 0.0
    assert 0.0 < high < 0.25  # zero out of twenty is not proof of zero
    low, high = wilson(20, 20)
    assert high == 1.0
    assert 0.75 < low < 1.0


def test_no_trials_means_no_claim():
    assert wilson(0, 0) == (0.0, 1.0)
    assert rate_with_interval(0, 0)["value"] is None


def test_wilson_interval_narrows_as_the_denominator_grows():
    small = wilson(50, 100)
    large = wilson(5000, 10000)
    assert (large[1] - large[0]) < (small[1] - small[0])


def test_a_rate_carries_its_counts():
    out = rate_with_interval(3, 4)
    assert out["numerator"] == 3 and out["denominator"] == 4
    assert out["value"] == pytest.approx(0.75)


def test_nonsense_counts_are_refused():
    with pytest.raises(ValueError):
        wilson(5, 4)


def test_the_bootstrap_is_reproducible_and_resamples_whole_groups():
    groups = [(8, 10), (0, 10), (5, 10), (10, 10)]
    first = bootstrap_groups(groups, resamples=2000, seed=7)
    second = bootstrap_groups(groups, resamples=2000, seed=7)
    assert first == second
    assert first["lo"] < 0.575 < first["hi"]
    # Resampling groups has to be wider than pretending every window is its own group.
    pooled = wilson(23, 40)
    assert (first["hi"] - first["lo"]) > (pooled[1] - pooled[0])
