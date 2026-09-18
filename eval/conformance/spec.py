#!/usr/bin/env python3
"""The thresholds, read out of the quoted spec text at run time.

CLAUDE.md: thresholds come only from flashmap/docs/SPEC_SOURCES.md, and two copies of a
threshold is one copy too many. So this module does not restate any number. It parses them out
of the quoted blocks and tables in that file, and fails loudly if a number it needs is not
there. If someone edits the quoted text, the ground truth for the whole conformance suite moves
with it, which is the only way a spec file can be the single source.

It also rebuilds the colour arithmetic from the same quoted formulas: the sRGB transfer
function, the relative luminance weights, the sRGB to XYZ matrix and the CIE 1976 UCS
coordinates. The coefficients are parsed, not typed in here.

**This module must not import flashmap**, directly or through anything it imports. It is half
of the independent ground truth for the conformance suite, and a ground truth that shares code
with the thing it grades is not a ground truth. eval/tests/test_conformance_standalone.py reads
the syntax tree of this file and of truth.py and fails on any flashmap import.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

__all__ = ["SpecNumbers", "load_spec", "SPEC_PATH"]

SPEC_PATH = Path(__file__).resolve().parents[2] / "flashmap" / "docs" / "SPEC_SOURCES.md"


class SpecParseError(RuntimeError):
    """The spec file did not contain a number this evaluation needs, in the form expected."""


@dataclass(frozen=True)
class SpecNumbers:
    """Every number this suite measures against, with where in the file it was read."""

    source_path: str
    source_sha256: str

    flash_limit_per_second: int
    window_ms: int
    general_min_delta: float
    general_dark_image_below: float
    area_fraction_limit: float
    field_width_fraction: float
    field_height_fraction: float
    red_saturated_ratio: float
    red_min_ucs_distance: float

    srgb_break: float
    srgb_divisor: float
    srgb_offset: float
    srgb_scale: float
    srgb_exponent: float
    luma_weights: tuple[float, float, float]
    xyz_matrix: tuple[tuple[float, float, float], ...]
    ucs_u_numerator: float
    ucs_v_numerator: float
    ucs_denominator: tuple[float, float, float]

    # ---- the arithmetic, built from the parsed constants ------------------------------

    def srgb_to_linear(self, values: NDArray[np.floating]) -> NDArray[np.float64]:
        """WCAG 2.2 relative luminance, Note 1: the 8-bit to linear light step."""
        v = np.asarray(values, dtype=np.float64)
        return np.where(
            v <= self.srgb_break,
            v / self.srgb_divisor,
            ((v + self.srgb_offset) / self.srgb_scale) ** self.srgb_exponent,
        )

    def relative_luminance(self, linear_rgb: NDArray[np.floating]) -> NDArray[np.float64]:
        w = np.asarray(self.luma_weights, dtype=np.float64)
        return np.asarray(linear_rgb, dtype=np.float64) @ w

    def xyz(self, linear_rgb: NDArray[np.floating]) -> NDArray[np.float64]:
        m = np.asarray(self.xyz_matrix, dtype=np.float64)
        return np.asarray(linear_rgb, dtype=np.float64) @ m.T

    def ucs(self, linear_rgb: NDArray[np.floating]) -> tuple[float, float]:
        x, y, z = self.xyz(linear_rgb)
        a, b, c = self.ucs_denominator
        denominator = a * x + b * y + c * z
        if denominator == 0:
            return (0.0, 0.0)
        return (
            self.ucs_u_numerator * x / denominator,
            self.ucs_v_numerator * y / denominator,
        )

    def red_ratio(self, linear_rgb: NDArray[np.floating]) -> float:
        r, g, b = (float(v) for v in linear_rgb)
        total = r + g + b
        return 0.0 if total <= 0 else r / total

    def luminance_of_srgb8(self, rgb8: tuple[int, int, int]) -> float:
        linear = self.srgb_to_linear(np.asarray(rgb8, dtype=np.float64) / 255.0)
        return float(self.relative_luminance(linear))

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source_path,
            "source_sha256": self.source_sha256,
            "flash_limit_per_second": self.flash_limit_per_second,
            "window_ms": self.window_ms,
            "general_min_delta": self.general_min_delta,
            "general_dark_image_below": self.general_dark_image_below,
            "area_fraction_limit": self.area_fraction_limit,
            "field_fraction": [self.field_width_fraction, self.field_height_fraction],
            "red_saturated_ratio": self.red_saturated_ratio,
            "red_min_ucs_distance": self.red_min_ucs_distance,
            "srgb_transfer": {
                "break": self.srgb_break,
                "divisor": self.srgb_divisor,
                "offset": self.srgb_offset,
                "scale": self.srgb_scale,
                "exponent": self.srgb_exponent,
            },
            "luma_weights": list(self.luma_weights),
            "xyz_matrix": [list(row) for row in self.xyz_matrix],
        }


# ---- parsing ---------------------------------------------------------------------------

_NUM = r"([0-9]*\.?[0-9]+)"


def _table_rows(text: str) -> dict[str, str]:
    """Every `| number | meaning | `where.it.is.used` |` row, keyed by the code name."""
    rows: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        key = cells[2].replace("`", "").strip()
        key = key.split("=")[0].strip()  # `profiles.WCAG.window_ms = 1000`
        if not key or key == "Where it is used":
            continue
        rows[key] = cells[0]
    return rows


def _one_number(cell: str, where: str) -> float:
    found = re.findall(_NUM, cell)
    if not found:
        raise SpecParseError(f"no number in the cell for {where!r}: {cell!r}")
    return float(found[0])


def _search(pattern: str, text: str, what: str) -> re.Match[str]:
    match = re.search(pattern, text)
    if match is None:
        raise SpecParseError(f"could not read {what} out of {SPEC_PATH}")
    return match


@lru_cache(maxsize=4)
def load_spec(path: str | None = None) -> SpecNumbers:
    """Read every threshold and colour constant this suite needs out of SPEC_SOURCES.md."""
    import hashlib

    spec_path = Path(path) if path else SPEC_PATH
    raw = spec_path.read_bytes()
    text = raw.decode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()

    rows = _table_rows(text)
    required = [
        "profiles.WCAG.flash_limit_per_second",
        "profiles.WCAG.window_ms",
        "profiles.WCAG.general.min_delta",
        "profiles.WCAG.general.dark_image_below",
        "profiles.WCAG.area_fraction_limit",
        "area.wcag_reference_window",
        "profiles.WCAG.red.saturated_red_ratio",
        "profiles.WCAG.red.min_ucs_distance",
    ]
    missing = [name for name in required if name not in rows]
    if missing:
        raise SpecParseError(f"{spec_path} has no row for: {', '.join(missing)}")

    field_cell = rows["area.wcag_reference_window"]
    field_numbers = [float(n) for n in re.findall(_NUM, field_cell)]
    if len(field_numbers) != 4:
        raise SpecParseError(
            f"expected two fractions for the 10 degree field, read {field_cell!r}"
        )
    width_fraction = field_numbers[0] / field_numbers[1]
    height_fraction = field_numbers[2] / field_numbers[3]

    transfer = _search(
        r"if RsRGB <= " + _NUM + r" then R = RsRGB/" + _NUM
        + r" else R = \(\(RsRGB\+" + _NUM + r"\)/" + _NUM + r"\) \^ " + _NUM,
        text,
        "the sRGB transfer function",
    )
    weights = _search(
        r"L = " + _NUM + r" \* R \+ " + _NUM + r" \* G \+ " + _NUM + r" \* B",
        text,
        "the relative luminance weights",
    )
    xyz_rows = []
    for axis in ("X", "Y", "Z"):
        match = _search(
            axis + r" = " + _NUM + r" \* R \+ " + _NUM + r" \* G \+ " + _NUM + r" \* B",
            text,
            f"the sRGB to XYZ row for {axis}",
        )
        xyz_rows.append(tuple(float(g) for g in match.groups()))
    u_line = _search(
        r"u' = " + _NUM + r" \* X / \(X \+ " + _NUM + r" \* Y \+ " + _NUM + r" \* Z\)",
        text,
        "the CIE 1976 UCS u' formula",
    )
    v_line = _search(
        r"v' = " + _NUM + r" \* Y / \(X \+ " + _NUM + r" \* Y \+ " + _NUM + r" \* Z\)",
        text,
        "the CIE 1976 UCS v' formula",
    )
    if u_line.group(2) != v_line.group(2) or u_line.group(3) != v_line.group(3):
        raise SpecParseError("the two UCS formulas disagree about their denominator")

    window_seconds = _one_number(rows["profiles.WCAG.window_ms"], "window")
    return SpecNumbers(
        source_path=str(spec_path.relative_to(spec_path.parents[2])),
        source_sha256=digest,
        flash_limit_per_second=int(
            _one_number(rows["profiles.WCAG.flash_limit_per_second"], "flash limit")
        ),
        window_ms=int(round(window_seconds * 1000)),
        general_min_delta=_one_number(rows["profiles.WCAG.general.min_delta"], "min delta"),
        general_dark_image_below=_one_number(
            rows["profiles.WCAG.general.dark_image_below"], "darker image"
        ),
        area_fraction_limit=_one_number(
            rows["profiles.WCAG.area_fraction_limit"], "area limit"
        ),
        field_width_fraction=width_fraction,
        field_height_fraction=height_fraction,
        red_saturated_ratio=_one_number(
            rows["profiles.WCAG.red.saturated_red_ratio"], "red ratio"
        ),
        red_min_ucs_distance=_one_number(
            rows["profiles.WCAG.red.min_ucs_distance"], "red distance"
        ),
        srgb_break=float(transfer.group(1)),
        srgb_divisor=float(transfer.group(2)),
        srgb_offset=float(transfer.group(3)),
        srgb_scale=float(transfer.group(4)),
        srgb_exponent=float(transfer.group(5)),
        luma_weights=tuple(float(g) for g in weights.groups()),  # type: ignore[arg-type]
        xyz_matrix=tuple(xyz_rows),  # type: ignore[arg-type]
        ucs_u_numerator=float(u_line.group(1)),
        ucs_v_numerator=float(v_line.group(1)),
        ucs_denominator=(1.0, float(u_line.group(2)), float(u_line.group(3))),
    )


if __name__ == "__main__":  # pragma: no cover - a look at what was parsed
    import json

    print(json.dumps(load_spec().as_dict(), indent=2))
