#!/usr/bin/env python3
"""The one place that turns detector intervals into windows, and windows into numbers.

docs/EVAL_PLAN.md section 2 says every detector, ours included, goes through the same
interval-to-window function, so no detector gets a mapping of its own. That function is
`windows_from_intervals` here. Everything downstream (conformance, baselines, ablations, real
clips) counts windows the same way because it calls the same code.

Nothing in this module imports flashmap. It only sees numbers.

Definitions, all from docs/EVAL_PLAN.md:

- a window is one second of media time, `[k, k+1)` from the first presentation timestamp;
- a predicted positive window is one that any detector interval overlaps (primary rule), or
  that an interval covers at least half of (the sensitivity rule reported beside it);
- precision is TP / (TP + FP), recall is TP / (TP + FN), both pooled over windows;
- the headline interval on the conformance suite is Wilson 95%, no continuity correction.

The Wilson interval treats windows as independent Bernoulli trials, which windows inside one
clip are not. That is why the real clip set uses a bootstrap over groups instead, and why both
are reported for both sets.

Which of the two comes out wider depends on how the errors cluster, and it is not always the
bootstrap. On the conformance suite the recall bootstrap is wider than Wilson, because a clip
tends to be found or missed as a whole, while the precision bootstrap is narrower, because
nearly every positive clip carries the same two false positive windows by construction and so
there is almost nothing for a resample to move. Both are reported and neither is picked after
the fact.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

__all__ = [
    "Z_95",
    "windows_from_intervals",
    "window_count",
    "confusion",
    "wilson",
    "rate_with_interval",
    "f1",
    "bootstrap_groups",
]

# Two sided 95%: the standard normal quantile at 0.975, from the normal distribution itself
# rather than a table. Not a threshold about flashing.
Z_95 = 1.959963984540054


def window_count(duration_ms: float, window_ms: float = 1000.0) -> int:
    """Whole windows in a clip. The trailing remainder is dropped (EVAL_PLAN section 9)."""
    if duration_ms <= 0:
        return 0
    return int(math.floor(duration_ms / window_ms))


def windows_from_intervals(
    intervals: Iterable[Sequence[float]],
    *,
    n_windows: int,
    window_ms: float = 1000.0,
    origin_ms: float = 0.0,
    min_overlap: float = 0.0,
) -> set[int]:
    """Window indices that these intervals mark as positive.

    `intervals` are (start_ms, end_ms) pairs in media time. `origin_ms` is the first
    presentation timestamp of the file, so windows are measured from the media, not from an
    assumed frame index.

    `min_overlap` is the fraction of the window an interval has to cover for the window to
    count: 0.0 is the primary "any overlap at all" rule, 0.5 is the sensitivity rule. An
    interval that touches a window boundary exactly overlaps nothing and does not count.
    """
    if n_windows <= 0:
        return set()
    if not 0.0 <= min_overlap <= 1.0:
        raise ValueError("min_overlap must be between 0 and 1")

    hits: set[int] = set()
    need = min_overlap * window_ms
    for interval in intervals:
        start = float(interval[0]) - origin_ms
        end = float(interval[1]) - origin_ms
        if end <= start:
            continue
        # The candidate range is deliberately one window wider than it needs to be on each
        # side, so that the overlap test below is the only thing that decides. An interval
        # that ends exactly on a window boundary has to be rejected by measuring its overlap
        # with the next window and finding it zero, not by arithmetic that quietly never
        # considered that window at all. Dead guards cannot be tested, so this one is live.
        first = max(0, int(math.floor(start / window_ms)) - 1)
        last = min(n_windows - 1, int(math.ceil(end / window_ms)))
        for index in range(first, last + 1):
            if index in hits:
                continue
            w_start = index * window_ms
            w_end = w_start + window_ms
            overlap = min(end, w_end) - max(start, w_start)
            if overlap > 0 and overlap >= need:
                hits.add(index)
    return hits


def confusion(
    predicted: set[int], truth: set[int], *, universe: Iterable[int]
) -> dict[str, int]:
    """TP, FP, FN, TN over an explicit universe of window indices.

    The universe is passed in rather than inferred so that excluded windows (a dropped warmup
    second, a window a labeler could not call) are missing from every count instead of being
    silently counted as negatives.
    """
    tp = fp = fn = tn = 0
    for index in universe:
        p = index in predicted
        t = index in truth
        if p and t:
            tp += 1
        elif p and not t:
            fp += 1
        elif t:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def wilson(successes: int, trials: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval, no continuity correction.

    The interval is the set of p for which |phat - p| <= z * sqrt(p(1-p)/n), solved as a
    quadratic. With no trials there is nothing to say, so the interval is the whole of [0, 1].
    tests/test_metrics.py checks the endpoints against that defining equation by bisection,
    which is a stricter check than matching a remembered table value.
    """
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError(f"nonsense counts: {successes} of {trials}")
    if trials == 0:
        return (0.0, 1.0)
    n = float(trials)
    phat = successes / n
    denominator = 1.0 + z * z / n
    center = (phat + z * z / (2 * n)) / denominator
    half = (z / denominator) * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return (max(0.0, center - half), min(1.0, center + half))


def rate_with_interval(successes: int, trials: int, z: float = Z_95) -> dict[str, object]:
    """A rate, its Wilson interval and the counts it came from, in one dict.

    The counts travel with the number on purpose: EVAL_PLAN section 3 says a metric without its
    denominator does not get published.
    """
    lo, hi = wilson(successes, trials, z=z)
    return {
        "value": (successes / trials) if trials else None,
        "wilson_lo": lo,
        "wilson_hi": hi,
        "numerator": successes,
        "denominator": trials,
    }


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def bootstrap_groups(
    groups: Sequence[tuple[int, int]],
    *,
    resamples: int = 10000,
    seed: int = 20260917,
    percentiles: tuple[float, float] = (2.5, 97.5),
) -> dict[str, object]:
    """Percentile bootstrap over groups, resampling whole groups with replacement.

    Each group is (successes, trials): a title for the real clip set, a clip for the
    conformance suite. Resampling whole groups is what keeps the interval honest when windows
    inside a group are correlated, which they always are.

    numpy is used for the draw, so the seed fully determines the answer.
    """
    import numpy as np

    if not groups:
        return {"lo": None, "hi": None, "resamples": 0, "groups": 0}
    successes = np.asarray([g[0] for g in groups], dtype=np.float64)
    trials = np.asarray([g[1] for g in groups], dtype=np.float64)
    rng = np.random.default_rng(seed)
    n = len(groups)
    draws = rng.integers(0, n, size=(resamples, n))
    num = successes[draws].sum(axis=1)
    den = trials[draws].sum(axis=1)
    keep = den > 0
    if not keep.any():
        return {"lo": None, "hi": None, "resamples": resamples, "groups": n}
    rates = num[keep] / den[keep]
    lo, hi = np.percentile(rates, percentiles)
    return {
        "lo": float(lo),
        "hi": float(hi),
        "resamples": int(keep.sum()),
        "groups": n,
        "seed": seed,
    }
