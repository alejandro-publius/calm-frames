"""flashmap: flash analysis for video against the WCAG 2.2 flash thresholds.

Every threshold flashmap uses is quoted, with its source, in docs/SPEC_SOURCES.md. No number
in this package may come from memory.

flashmap reduces exposure to flashing above published limits in the videos it measures. It is
not a medical device and it does not prevent seizures.
"""

from __future__ import annotations

__version__ = "1.0.0"

from .analyze import (
    AnalysisResult,
    PatternExemption,
    PatternSegment,
    Segment,
    StreamingAnalyzer,
    analyze_file,
)
from .decode import ColorPolicy, UnsupportedInput
from .pattern import PatternSettings
from .picture import LetterboxSettings, PictureRect
from .profiles import BROADCAST_SDR, PROFILES, WCAG, PatternRule, Profile, get_profile
from .room import RoomSetting
from .sidecar import (
    SIDECAR_VERSION,
    VerificationError,
    build_map,
    load_map,
    sign_map,
    verify_map,
    write_map,
)

__all__ = [
    "__version__",
    "AnalysisResult",
    "BROADCAST_SDR",
    "ColorPolicy",
    "LetterboxSettings",
    "PROFILES",
    "PatternExemption",
    "PatternRule",
    "PatternSegment",
    "PatternSettings",
    "PictureRect",
    "Profile",
    "RoomSetting",
    "SIDECAR_VERSION",
    "Segment",
    "StreamingAnalyzer",
    "UnsupportedInput",
    "VerificationError",
    "WCAG",
    "analyze_file",
    "build_map",
    "get_profile",
    "load_map",
    "sign_map",
    "verify_map",
    "write_map",
]
