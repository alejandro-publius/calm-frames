"""Profiles: the rule sets flashmap can measure against.

Every number here is quoted in docs/SPEC_SOURCES.md with its source. Nothing in this file may
carry a number that is not on that page.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["GeneralRule", "RedRule", "Profile", "WCAG", "BROADCAST_SDR", "PROFILES", "get_profile"]


@dataclass(frozen=True)
class GeneralRule:
    metric: str
    min_delta: float
    dark_image_below: float
    source: str


@dataclass(frozen=True)
class RedRule:
    saturated_red_ratio: float
    min_ucs_distance: float
    source: str


@dataclass(frozen=True)
class Profile:
    name: str
    title: str
    general: GeneralRule
    red: RedRule
    flash_limit_per_second: int
    window_ms: int
    area_fraction_limit: float
    area_window_mode: str
    peak_nits: float | None = None
    rules_not_implemented: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "title": self.title,
            "flash_limit_per_second": self.flash_limit_per_second,
            "window_ms": self.window_ms,
            "area_fraction_limit": self.area_fraction_limit,
            "area_window_mode": self.area_window_mode,
            "peak_nits": self.peak_nits,
            "general_flash": {
                "metric": self.general.metric,
                "min_delta": self.general.min_delta,
                "dark_image_below": self.general.dark_image_below,
                "source": self.general.source,
            },
            "red_flash": {
                "saturated_red_ratio": self.red.saturated_red_ratio,
                "min_ucs_distance": self.red.min_ucs_distance,
                "source": self.red.source,
            },
            "transition_pairing": "non-overlapping",
            "transition_rule": "declared-on-first-frame-meeting-threshold",
            "window_placement": "trailing-closed-window-at-every-frame",
            "red_opposing_rule": "enter-saturated-red-paired-with-leave",
            "rules_not_implemented": list(self.rules_not_implemented),
            "exceptions_not_implemented": [
                "WCAG fine balanced pattern exception (white noise, checkerboards under "
                "0.1 degree). Content the exception would excuse is still reported."
            ],
            "spec_sources": "flashmap/docs/SPEC_SOURCES.md",
        }


WCAG = Profile(
    name="wcag",
    title="WCAG 2.2 Success Criterion 2.3.1, general and red flash thresholds",
    general=GeneralRule(
        metric="wcag-relative-luminance",
        min_delta=0.10,
        dark_image_below=0.80,
        source="WCAG 2.2 general flash and red flash thresholds (SPEC_SOURCES section 2)",
    ),
    red=RedRule(
        saturated_red_ratio=0.8,
        min_ucs_distance=0.2,
        source="WCAG 2.2 thresholds Note 3 and Understanding 2.3.1 (SPEC_SOURCES sections 2, 4)",
    ),
    flash_limit_per_second=3,
    window_ms=1000,
    area_fraction_limit=0.25,
    area_window_mode="ten-degree-field",
    rules_not_implemented=(
        "the fine balanced pattern exception",
        "any HDR rule",
    ),
)

BROADCAST_SDR = Profile(
    name="broadcast",
    title="ITU-R BT.1702-3 Annex 1 Guideline 1, standard dynamic range only",
    general=GeneralRule(
        metric="bt1886-nits",
        min_delta=20.0,
        dark_image_below=160.0,
        source="ITU-R BT.1702-3 Annex 1 Guideline 1 (SPEC_SOURCES section 5)",
    ),
    red=RedRule(
        saturated_red_ratio=0.8,
        min_ucs_distance=0.2,
        source=(
            "BT.1702-3 calls a transition to or from a saturated red harmful but gives no "
            "numbers, so the WCAG 2.2 and ISO 9241-391 working definition is reused "
            "(SPEC_SOURCES sections 4 and 5)"
        ),
    ),
    flash_limit_per_second=3,
    window_ms=1000,
    area_fraction_limit=0.25,
    area_window_mode="whole-picture",
    peak_nits=200.0,
    rules_not_implemented=(
        "the HDR branch, Michelson contrast 1/17 above 160 cd/m2",
        "the 360 ms and 334 ms leading edge allowance, which could only excuse flashes",
        "Guideline 2, potentially harmful regular patterns",
        "the overscan allowance in Note 4",
    ),
)

PROFILES = {WCAG.name: WCAG, BROADCAST_SDR.name: BROADCAST_SDR}


def get_profile(name: str, peak_nits: float | None = None) -> Profile:
    try:
        profile = PROFILES[name]
    except KeyError:
        raise ValueError(
            f"unknown profile {name!r}, pick one of {sorted(PROFILES)}"
        ) from None
    if peak_nits is not None:
        if profile.peak_nits is None:
            raise ValueError(f"profile {name!r} does not use a peak luminance")
        from dataclasses import replace

        profile = replace(profile, peak_nits=float(peak_nits))
    return profile
