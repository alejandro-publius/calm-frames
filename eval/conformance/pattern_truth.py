#!/usr/bin/env python3
"""The true answer for one generated pattern clip, from the spec text and from what was drawn.

**This module must not import flashmap.** `pattern_run.py` reads its syntax tree, and the
syntax trees of pattern_spec.py and pattern_geometry.py, before it measures anything, and
refuses to run if any of them reaches flashmap. If truth and flashmap disagree, that is a
finding to report, not a bug to be fixed by making truth agree (docs/EVAL_PLAN.md section 4).

Every threshold used here is parsed out of flashmap/docs/SPEC_SOURCES.md by pattern_spec.py at
run time. No number in this file is a threshold.

How a window is judged
----------------------
A clip is three seconds: one second of calm background, then two seconds of pattern. Windows
are one second of media time, `[k, k+1)`, so window 0 is calm and windows 1 and 2 hold the
pattern.

A pattern window is a ground truth positive when all four of Attachment 1's conditions hold on
what was drawn:

1. more than five light and dark pairs of clearly discernible stripes. The generator drew
   exactly `2 * pairs` bars, so this is a fact about the drawing;
2. the bar to bar difference reaches the Guideline 1 flash difference, with the darker bar
   under the darker image ceiling. Computed from the two grey codes that were drawn, through
   the same BT.1886 mapping the broadcast profile uses;
3. the pattern occupies more than its area limit. The limit is 40% when the stripes were drawn
   stationary and 25% when they were drawn reversing, oscillating or flashing;
4. the pattern was not drawn flowing smoothly one way, which the attachment exempts outright.

Window 0 is a negative for every clip: there is no pattern on the screen.

Two things this ground truth does on purpose
--------------------------------------------
It uses the motion the generator *drew*, where flashmap has to infer it from the pictures. That
is the point: the motion class is the risky judgement in this rule and the suite exists to
measure how often the inference is right and in which direction it is wrong.

And it gives a drift clip no positive window at all, even when the pattern is enormous. A
detector that is not sure the flow is smooth will hide it anyway, which is the fail safe this
project chose, and it will show up here as a false positive rather than being quietly excused.
The report separates those from every other false positive so the cost of that choice is a
number and not an opinion.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.pattern_geometry import block_for  # noqa: E402
from conformance.pattern_spec import PatternNumbers, load_pattern_spec  # noqa: E402

__all__ = ["PatternTruth", "clip_truth"]


@dataclass(frozen=True)
class PatternTruth:
    n_windows: int
    window_ms: int
    pattern_windows: list[int]
    positive_windows: list[int]
    establishing_window: int
    pairs_drawn: int
    pairs_qualify: bool
    drawn_area_fraction: float
    area_limit: float | None
    area_qualifies: bool
    contrast_qualifies: bool
    bar_nits: list[float]
    bar_delta_nits: float
    darker_bar_nits: float
    exempt: bool
    drawn_motion: str

    def as_dict(self) -> dict[str, object]:
        return {
            "n_windows": self.n_windows,
            "window_ms": self.window_ms,
            "pattern_windows": self.pattern_windows,
            "positive_windows": self.positive_windows,
            "establishing_window": self.establishing_window,
            "pairs_drawn": self.pairs_drawn,
            "pairs_qualify": self.pairs_qualify,
            "drawn_area_fraction": round(self.drawn_area_fraction, 6),
            "area_limit": self.area_limit,
            "area_qualifies": self.area_qualifies,
            "contrast_qualifies": self.contrast_qualifies,
            "bar_nits": [round(v, 4) for v in self.bar_nits],
            "bar_delta_nits": round(self.bar_delta_nits, 4),
            "darker_bar_nits": round(self.darker_bar_nits, 4),
            "exempt": self.exempt,
            "drawn_motion": self.drawn_motion,
        }


def clip_truth(clip: dict, spec: PatternNumbers | None = None) -> PatternTruth:
    spec = spec or load_pattern_spec()
    width, height = int(clip["width"]), int(clip["height"])
    pairs = int(clip["pairs"])
    motion = str(clip["motion"])

    block = block_for(width, height, str(clip["orientation"]), float(clip["area_fraction"]), pairs)
    drawn_area = block.area / float(width * height)

    dark_code, bright_code = int(clip["dark_code"]), int(clip["bright_code"])
    dark_nits = spec.nits_of_grey_code(min(dark_code, bright_code))
    bright_nits = spec.nits_of_grey_code(max(dark_code, bright_code))
    contrast = spec.contrast_qualifies(dark_code, bright_code)

    pairs_qualify = pairs > spec.more_than_pairs
    limit = spec.area_limit(motion)
    exempt = limit is None
    area_qualifies = (not exempt) and drawn_area > float(limit)

    window_ms = 1000
    n_windows = int(float(clip["duration_ms"]) // window_ms)
    first_pattern_window = int(float(clip["pattern_start_ms"]) // window_ms)
    pattern_windows = list(range(first_pattern_window, n_windows))

    fails = pairs_qualify and contrast and area_qualifies and not exempt
    positive = pattern_windows if fails else []

    return PatternTruth(
        n_windows=n_windows,
        window_ms=window_ms,
        pattern_windows=pattern_windows,
        positive_windows=positive,
        # The window the pattern arrives in. A causal detector cannot know how a pattern moves
        # until it has watched it for a few frames, so this window carries the cost of the fail
        # safe rule and the report scores it separately rather than burying it.
        establishing_window=first_pattern_window,
        pairs_drawn=pairs,
        pairs_qualify=pairs_qualify,
        drawn_area_fraction=drawn_area,
        area_limit=limit,
        area_qualifies=area_qualifies,
        contrast_qualifies=contrast,
        bar_nits=[dark_nits, bright_nits],
        bar_delta_nits=bright_nits - dark_nits,
        darker_bar_nits=dark_nits,
        exempt=exempt,
        drawn_motion=motion,
    )
