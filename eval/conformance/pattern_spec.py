#!/usr/bin/env python3
"""The regular pattern numbers, read out of the quoted spec text at run time.

CLAUDE.md: thresholds come only from flashmap/docs/SPEC_SOURCES.md. So this module restates no
number. It parses the ones the pattern suite needs out of the tables on that page, sections 5
and 8, and fails loudly if one is missing. Edit the quoted text and the ground truth for this
whole suite moves with it, which is the only way a spec file can be the single source.

**This module must not import flashmap**, directly or through anything it imports. It is part
of the independent ground truth for the pattern conformance suite, and a ground truth that
shares code with the thing it grades is not a ground truth. `pattern_run.py` checks the syntax
tree of this file and of pattern_truth.py and pattern_geometry.py before it measures anything,
and refuses to run if any of them reaches flashmap.

One measured fact lives here rather than in a spec: how an 8 bit grey drawn by the renderer
arrives at the analyser. The renderer hands full range RGB to libx264 and asks for limited
range, so a grey code c comes back out of a decoder at video level c / 255. That was measured,
not assumed: codes 64, 96, 120, 128, 160 and 200 decode to 0.2511, 0.3744, 0.4703, 0.5023,
0.6256 and 0.7854, all within 0.003 of c / 255. It is a property of the encoder and this
generator, not a threshold, and `pattern_run.py` re-measures it on every clip it makes.
"""

from __future__ import annotations

import hashlib
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from conformance.spec import SPEC_PATH, SpecParseError, table_rows  # noqa: E402

__all__ = ["PatternNumbers", "load_pattern_spec"]

_NUM = r"([0-9]*\.?[0-9]+)"


def _row_for(rows: dict[str, str], prefix: str, path: Path) -> str:
    """The table cell whose code name starts with `prefix`.

    Prefix rather than exact, because some rows on that page name the setting and then say
    something else about it in the same cell, for instance the peak white row, which adds that
    it can be overridden on the command line.
    """
    for key, cell in rows.items():
        if key.startswith(prefix):
            return cell
    raise SpecParseError(f"{path} has no number table row for {prefix}")


def _one(rows: dict[str, str], prefix: str, path: Path) -> float:
    cell = _row_for(rows, prefix, path)
    found = re.findall(_NUM, cell)
    if not found:
        raise SpecParseError(f"no number in the {prefix} cell of {path}: {cell!r}")
    return float(found[0])


@dataclass(frozen=True)
class PatternNumbers:
    """Every number the pattern suite measures against, with where it was read."""

    source_path: str
    source_sha256: str

    more_than_pairs: int
    stationary_area_limit: float
    changing_area_limit: float
    min_nits_delta: float
    dark_image_below_nits: float
    peak_nits: float
    bt1886_gamma: float

    def nits_of_grey_code(self, code: int) -> float:
        """Screen luminance of an 8 bit grey this suite draws, through BT.1886."""
        level = max(0.0, min(1.0, code / 255.0))
        return self.peak_nits * level**self.bt1886_gamma

    def grey_code_for_nits(self, nits: float) -> int:
        """The 8 bit grey whose screen luminance is closest to `nits`."""
        target = max(0.0, min(self.peak_nits, nits))
        level = (target / self.peak_nits) ** (1.0 / self.bt1886_gamma)
        return int(min(255, max(0, round(level * 255.0))))

    def contrast_qualifies(self, dark_code: int, bright_code: int) -> bool:
        """Does this bar pair reach the Guideline 1 flash difference.

        The attachment defines the bar to bar difference by reference to Guideline 1, so this
        is the same pair of numbers the general flash rule uses and not a new one.
        """
        dark = self.nits_of_grey_code(min(dark_code, bright_code))
        bright = self.nits_of_grey_code(max(dark_code, bright_code))
        return (bright - dark) >= self.min_nits_delta and dark < self.dark_image_below_nits

    def area_limit(self, drawn_motion: str) -> float | None:
        """The area limit for a pattern drawn with this motion, or None when it is exempt.

        Stationary gets 40%. Anything that changes direction, oscillates, flashes or reverses
        in contrast gets 25%. A pattern that flows smoothly one way is exempt from restriction.
        """
        if drawn_motion == "stationary":
            return self.stationary_area_limit
        if drawn_motion in ("reversing", "oscillating", "flashing"):
            return self.changing_area_limit
        if drawn_motion == "drift":
            return None
        raise ValueError(f"unknown drawn motion {drawn_motion!r}")

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source_path,
            "source_sha256": self.source_sha256,
            "more_than_pairs": self.more_than_pairs,
            "stationary_area_limit": self.stationary_area_limit,
            "changing_area_limit": self.changing_area_limit,
            "min_nits_delta": self.min_nits_delta,
            "dark_image_below_nits": self.dark_image_below_nits,
            "peak_nits": self.peak_nits,
            "bt1886_gamma": self.bt1886_gamma,
            "status": (
                "ITU-R BT.1702-3 Attachment 1 to Annex 1 is informative and says its criteria "
                "are used by some administrations. WCAG 2.2 SC 2.3.1 does not cover regular "
                "patterns at all, so nothing in this suite is a WCAG measurement."
            ),
        }


@lru_cache(maxsize=4)
def load_pattern_spec(path: str | None = None) -> PatternNumbers:
    spec_path = Path(path) if path else SPEC_PATH
    raw = spec_path.read_bytes()
    rows = table_rows(raw.decode("utf-8"))
    return PatternNumbers(
        source_path=str(spec_path.relative_to(spec_path.parents[2])),
        source_sha256=hashlib.sha256(raw).hexdigest(),
        more_than_pairs=int(
            _one(rows, "profiles.BROADCAST_SDR.pattern.more_than_pairs", spec_path)
        ),
        stationary_area_limit=_one(
            rows, "profiles.BROADCAST_SDR.pattern.stationary_area_limit", spec_path
        ),
        changing_area_limit=_one(
            rows, "profiles.BROADCAST_SDR.pattern.changing_area_limit", spec_path
        ),
        min_nits_delta=_one(rows, "profiles.BROADCAST_SDR.general.min_nits_delta", spec_path),
        dark_image_below_nits=_one(
            rows, "profiles.BROADCAST_SDR.general.dark_image_below_nits", spec_path
        ),
        peak_nits=_one(rows, "profiles.BROADCAST_SDR.peak_nits", spec_path),
        bt1886_gamma=_one(rows, "color.bt1886_nits", spec_path),
    )


if __name__ == "__main__":  # pragma: no cover - a look at what was parsed
    import json

    print(json.dumps(load_pattern_spec().as_dict(), indent=2))
