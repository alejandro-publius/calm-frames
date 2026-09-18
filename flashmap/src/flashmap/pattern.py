"""Guideline 2, potentially harmful regular patterns.

This is a separate hazard from the general flash and red flash rules, with a separate rule
object on the profile, a segment kind of its own and a verdict that can be read on its own.
Every number it uses is quoted in flashmap/docs/SPEC_SOURCES.md section 8, from ITU-R BT.1702-3
Attachment 1 to Annex 1, which the recommendation labels **informative** and which says its
criteria are what some administrations use. Nothing flashmap reports from it is a requirement,
and WCAG 2.2 SC 2.3.1 has no regular pattern rule at all, so a pattern hide is never a WCAG
finding. The sidecar says both of those things beside every pattern segment.

What the rule checks, and where each part comes from:

1. more than five light and dark pairs of clearly discernible stripes in any orientation, so
   six pairs, which is twelve bars, is the first count that can fail;
2. the light to dark bar difference has to reach the same difference as a potentially harmful
   flash in Guideline 1, which for SDR is a darker bar below 160 cd/m2 and a difference of
   20 cd/m2 or more. That arithmetic is already in the profile's general flash rule and is
   reused here rather than restated, so the pattern rule introduces no luminance number;
3. more than 40% of the picture when the stripes are stationary, or more than 25% when they
   change direction, oscillate, flash or reverse in contrast;
4. a pattern that obviously flows smoothly across, into or out of the screen in one direction
   is exempt.

Point 4 is the risky judgement, and it fails safe. A wrongly applied exemption hides a hazard
from a child. A wrongly withheld one covers a few safe seconds. So the exemption is applied
only when the flow is unambiguous, an uncertain motion class takes the stricter 25% area, and
every exemption that was applied is recorded in the map as its own interval, so a reviewer can
see what was let through instead of finding a silence.

Detector tuning, not thresholds
-------------------------------
`PatternSettings` holds the numbers this detector needs to work that no spec supplies: how many
frames of motion evidence it wants, how still is still, how well two frames have to match
before a shift estimate counts as evidence. They are written out with their defaults, the same
way `picture.LetterboxSettings` is, and they go into the sidecar so a reviewer can see them.
BT.1702-3 gives no persistence time, no stripe width and no spatial frequency band, and none is
invented here.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "MOTION_STATIONARY",
    "MOTION_CHANGING",
    "MOTION_SMOOTH_FLOW",
    "MOTION_UNCERTAIN",
    "PatternSettings",
    "PatternObservation",
    "PatternTracker",
    "scan_bars",
    "stripe_mask",
]

MOTION_STATIONARY = "stationary"
"""The stripes did not move. BT.1702-3 Attachment 1 gives this case the 40% area."""
MOTION_CHANGING = "changing"
"""The stripes changed direction, oscillated, flashed or reversed in contrast. 25% area."""
MOTION_SMOOTH_FLOW = "smooth-flow"
"""The pattern flows smoothly in one direction, which the attachment exempts."""
MOTION_UNCERTAIN = "uncertain"
"""Not enough evidence to call it. Takes the stricter 25% area and never the exemption."""


@dataclass(frozen=True)
class PatternSettings:
    """Detector tuning. None of these is a threshold and none comes from a spec.

    They are the pattern rule's equivalent of `picture.LetterboxSettings`, written out here
    with their defaults and recorded in the sidecar under `profile.pattern_rule.tuning`.
    """

    orientations: tuple[str, ...] = ("rows", "columns", "diagonal", "antidiagonal")
    """Which scan directions are walked. Stripes may be in any orientation and may be radial or
    curved, so four families are scanned and the pattern area is their union."""

    motion_history_frames: int = 12
    """How many frame to frame comparisons the motion class is decided on."""

    min_motion_frames: int = 6
    """How many of those comparisons have to be in hand before any confident class is allowed.
    Below this the class is uncertain, which is what the first frames of a pattern get."""

    still_fraction_of_min_delta: float = 0.10
    """How still is still, as a share of the rule's own bar to bar difference. The mean absolute
    change of the stripe profile has to sit under this share for a frame pair to be still."""

    min_match_peak: float = 0.30
    """A correlation peak below this is noise, not a measured shift."""

    ambiguity_ratio: float = 0.90
    """If a rival lag reaches this share of the best one, the shift could be either and the
    frame pair counts as no evidence. A repeating pattern does this to itself as soon as it
    moves further than a bar in one frame, which is the aliasing case a person cannot follow
    either, so it comes out uncertain rather than exempt."""

    min_profile_samples: int = 8
    """A stripe profile shorter than this says nothing about motion."""

    contrast_reversal_correlation: float = -0.30
    """Zero lag correlation at or below this means light bars became dark bars."""

    flow_direction_agreement: float = 0.90
    """Length of the mean unit direction vector over the history, from 0 (scattered) to 1 (one
    direction). The smooth flow exemption needs at least this."""

    flow_speed_spread: float = 0.50
    """Largest allowed standard deviation of the per frame speed as a share of its mean."""

    min_flow_px: float = 0.75
    """Mean speed in analysis pixels per frame below which nothing is flowing anywhere."""

    segment_bridge_ms: float = 200.0
    """A gap this short between two failing frames keeps one segment open rather than starting a
    second. BT.1702-3 gives no persistence time, so this is about not shredding one pattern into
    a hundred intervals, and it never creates a segment that was not failing at both ends."""

    def as_dict(self) -> dict[str, object]:
        return {
            "orientations": list(self.orientations),
            "motion_history_frames": self.motion_history_frames,
            "min_motion_frames": self.min_motion_frames,
            "still_fraction_of_min_delta": self.still_fraction_of_min_delta,
            "min_match_peak": self.min_match_peak,
            "ambiguity_ratio": self.ambiguity_ratio,
            "min_profile_samples": self.min_profile_samples,
            "contrast_reversal_correlation": self.contrast_reversal_correlation,
            "flow_direction_agreement": self.flow_direction_agreement,
            "flow_speed_spread": self.flow_speed_spread,
            "min_flow_px": self.min_flow_px,
            "segment_bridge_ms": self.segment_bridge_ms,
            "what_these_are": (
                "detector tuning, not thresholds. BT.1702-3 gives no persistence time, no "
                "stripe width and no spatial frequency band, so none is used as a threshold. "
                "See flashmap/docs/SPEC_SOURCES.md implementation decision 9."
            ),
        }


@dataclass(frozen=True)
class PatternObservation:
    """What the detector saw on one frame."""

    pts_ms: float
    stripe_pairs: int
    """The largest light and dark pair count on any scanline, in any scanned orientation. The
    bar to bar difference condition is already inside this count: a boundary is only a boundary
    when it meets the Guideline 1 flash difference."""
    area_fraction: float
    motion: str
    motion_confidence: float
    area_limit: float
    over_limit: bool
    """Count, contrast and area all met. Before the exemption."""
    exempt: bool
    """`over_limit` and the flow was unambiguous, so the attachment exempts it."""

    @property
    def fails(self) -> bool:
        return self.over_limit and not self.exempt

    def as_dict(self) -> dict[str, object]:
        return {
            "pts_ms": round(float(self.pts_ms), 3),
            "stripe_pairs": int(self.stripe_pairs),
            "area_fraction": round(float(self.area_fraction), 6),
            "motion": self.motion,
            "motion_confidence": round(float(self.motion_confidence), 4),
            "area_limit": self.area_limit,
        }


# ---- scanning for stripes ---------------------------------------------------------------


def scan_bars(
    values: NDArray[np.floating], min_delta: float, dark_below: float
) -> tuple[NDArray[np.int32], NDArray[np.int32], NDArray[np.int32]]:
    """Find the bar boundaries on every scanline of `values`, walking along axis 1.

    A boundary is a swing away from the current bar's level that reaches `min_delta` while the
    darker of the two levels is under `dark_below`. That is the Guideline 1 flash difference,
    read across the picture instead of across time, which is what the attachment asks for when
    it says the bar to bar difference is the same as a flash difference. Once a swing is
    confirmed, the level it reached becomes the new bar level.

    Only boundaries that oppose the one before them count, so a smooth ramp across the picture
    produces no bars however far it travels: every step of a ramp swings the same way, and a
    same way swing only moves the level. Stripes alternate; a gradient does not.

    Returns (bars, first, last): the bar count on each line, and the positions of its first and
    last counted boundary, or -1 where there was none.
    """
    array = np.asarray(values, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError("scan_bars wants a two dimensional array of scanlines")
    lines, length = array.shape
    delta_limit = np.float32(min_delta)
    dark_limit = np.float32(dark_below)

    level = array[:, 0].astype(np.float32).copy()
    last_sign = np.zeros(lines, dtype=np.int8)
    counted = np.zeros(lines, dtype=np.int32)
    first = np.full(lines, -1, dtype=np.int32)
    last = np.full(lines, -1, dtype=np.int32)
    ones = np.ones(lines, dtype=np.int8)

    for index in range(1, length):
        value = array[:, index]
        swing = value - level
        up = swing >= delta_limit
        down = swing <= -delta_limit
        confirmed = (up | down) & (np.minimum(level, value) < dark_limit)
        if not confirmed.any():
            continue
        sign = np.where(up, ones, -ones)
        opposing = confirmed & (sign != last_sign)

        counted += opposing
        np.copyto(first, index, where=opposing & (first < 0))
        np.copyto(last, index, where=opposing)
        np.copyto(last_sign, sign, where=confirmed)
        np.copyto(level, value, where=confirmed)

    # Boundaries separate bars, so n counted boundaries mean n + 1 bars on that line. Twelve
    # bars is six light and dark pairs, which is the first count the attachment can fail.
    bars = np.where(counted > 0, counted + 1, 0).astype(np.int32)
    return bars, first, last


def _shear(array: NDArray[np.float32], flip: bool) -> NDArray[np.float32]:
    """Rows of the result are diagonal lines of `array`.

    Positions that fall outside the picture repeat the nearest real pixel, so the padding is
    flat and cannot invent a bar boundary. A wrapped shear would have invented one per line.
    """
    height, width = array.shape
    rows = np.arange(height)
    offsets = (height - 1 - rows) if flip else rows
    columns = np.arange(width + height - 1)[None, :] - offsets[:, None]
    return np.take_along_axis(array, np.clip(columns, 0, width - 1), axis=1)


def _span_mask(
    bars: NDArray[np.int32],
    first: NDArray[np.int32],
    last: NDArray[np.int32],
    length: int,
    min_bars: int,
) -> NDArray[np.bool_]:
    """The stretch of each qualifying scanline that lies between its outer bar boundaries."""
    qualifies = bars >= min_bars
    index = np.arange(length)[None, :]
    return qualifies[:, None] & (index >= first[:, None]) & (index <= last[:, None])


@dataclass(frozen=True)
class _Scan:
    """What one scan orientation found on one frame."""

    orientation: str
    bars: int
    mask: NDArray[np.bool_]
    profile: NDArray[np.float32] | None
    """The average scanline of the lines that qualified, which is the one dimensional signal
    the stripes live in. Motion is measured on this and not on the picture, because a grating
    can only be seen to move along its own normal: shifting it along its stripes changes
    nothing, and a two dimensional match would call that a diagonal flow."""
    bar_width: float


@dataclass(frozen=True)
class PatternScan:
    """The whole frame's answer: the union mask, the pair count and the dominant orientation."""

    mask: NDArray[np.bool_]
    stripe_pairs: int
    area_fraction: float
    orientation: str | None
    profile: NDArray[np.float32] | None
    bar_width: float


def _median_bar_width(
    bars: NDArray[np.int32], first: NDArray[np.int32], last: NDArray[np.int32], min_bars: int
) -> float:
    qualifies = bars >= min_bars
    if not qualifies.any():
        return 0.0
    spans = (last[qualifies] - first[qualifies]).astype(np.float64)
    counts = np.maximum(1, bars[qualifies] - 2).astype(np.float64)
    return float(np.median(spans / counts))


def _lines_for(array: NDArray[np.float32], orientation: str) -> NDArray[np.float32]:
    if orientation == "rows":
        return array
    if orientation == "columns":
        return array.T
    if orientation in ("diagonal", "antidiagonal"):
        return _shear(array, flip=orientation == "antidiagonal")
    raise ValueError(f"unknown scan orientation {orientation!r}")


def _finish_scan(
    orientation: str,
    lines: NDArray[np.float32],
    bars: NDArray[np.int32],
    first: NDArray[np.int32],
    last: NDArray[np.int32],
    shape: tuple[int, int],
    min_bars: int,
    min_profile_samples: int,
) -> _Scan:
    height, width = shape
    span = _span_mask(bars, first, last, lines.shape[1], min_bars)
    qualifies = bars >= min_bars
    best = int(bars.max()) if bars.size else 0
    bar_width = _median_bar_width(bars, first, last, min_bars)

    mask = np.zeros((height, width), dtype=bool)
    profile: NDArray[np.float32] | None = None
    if orientation == "rows":
        mask |= span[:, :width]
        if qualifies.any():
            profile = lines[qualifies].mean(axis=0).astype(np.float32)
    elif orientation == "columns":
        mask |= span[:, :height].T
        if qualifies.any():
            profile = lines[qualifies].mean(axis=0).astype(np.float32)
    else:
        rows = np.arange(height)
        offsets = (height - 1 - rows) if orientation == "antidiagonal" else rows
        columns = np.arange(lines.shape[1])[None, :] - offsets[:, None]
        inside = (columns >= 0) & (columns < width)
        hits = span[:, : lines.shape[1]] & inside
        if hits.any():
            line_index, shear_index = np.nonzero(hits)
            mask[line_index, columns[line_index, shear_index]] = True
        # Every sheared line is padded differently, so only the stretch that is real picture on
        # all of them can be averaged. Below `min_profile_samples` there is nothing to average.
        low, high = height - 1, width
        if qualifies.any() and high - low >= min_profile_samples:
            profile = lines[qualifies, low:high].mean(axis=0).astype(np.float32)

    return _Scan(orientation, best, mask, profile, bar_width)


def stripe_mask(
    metric: NDArray[np.floating],
    *,
    min_delta: float,
    dark_below: float,
    min_bars: int,
    orientations: tuple[str, ...],
    min_profile_samples: int = 8,
) -> PatternScan:
    """The pixels inside a qualifying run of stripes, and what was found there.

    The four scan families are rows, columns and the two diagonal shears, which is how an
    orientation agnostic count is done without rotating the picture. Their masks are unioned,
    because a pattern the picture holds is a pattern whichever way it was found. The orientation
    that counted the most bars is the dominant one, and it is the one motion is measured in.

    All four families are walked in one pass over a stacked array. Short families are padded by
    repeating their last sample, which is flat and so cannot invent a bar.
    """
    array = np.asarray(metric, dtype=np.float32)
    height, width = array.shape
    families = [(orientation, _lines_for(array, orientation)) for orientation in orientations]
    if not families:
        return PatternScan(np.zeros((height, width), dtype=bool), 0, 0.0, None, None, 0.0)

    longest = max(lines.shape[1] for _, lines in families)
    stacked = np.concatenate(
        [
            lines
            if lines.shape[1] == longest
            else np.pad(lines, ((0, 0), (0, longest - lines.shape[1])), mode="edge")
            for _, lines in families
        ],
        axis=0,
    )
    bars, first, last = scan_bars(stacked, min_delta, dark_below)

    mask = np.zeros((height, width), dtype=bool)
    dominant: _Scan | None = None
    offset = 0
    for orientation, lines in families:
        count = lines.shape[0]
        piece = slice(offset, offset + count)
        offset += count
        scan = _finish_scan(
            orientation,
            lines,
            bars[piece],
            first[piece],
            last[piece],
            (height, width),
            min_bars,
            min_profile_samples,
        )
        mask |= scan.mask
        if dominant is None or scan.bars > dominant.bars:
            dominant = scan

    pairs = (dominant.bars // 2) if dominant is not None else 0
    qualifying = dominant is not None and dominant.bars >= min_bars
    return PatternScan(
        mask=mask,
        stripe_pairs=pairs,
        area_fraction=float(mask.mean()) if mask.size else 0.0,
        orientation=dominant.orientation if qualifying and dominant else None,
        profile=dominant.profile if qualifying and dominant else None,
        bar_width=dominant.bar_width if qualifying and dominant else 0.0,
    )


# ---- motion -----------------------------------------------------------------------------


class _Comparison:
    """One frame to frame comparison, reduced to what the motion class needs."""

    __slots__ = ("still", "reversed_contrast", "flashed", "turned", "lag", "peak", "ambiguous")

    def __init__(
        self,
        still: bool,
        reversed_contrast: bool,
        flashed: bool,
        turned: bool,
        lag: int,
        peak: float,
        ambiguous: bool,
    ) -> None:
        self.still = still
        self.reversed_contrast = reversed_contrast
        self.flashed = flashed
        self.turned = turned
        """The stripes changed orientation, which the attachment lists as changing direction."""
        self.lag = lag
        self.peak = peak
        self.ambiguous = ambiguous


def _best_lag(
    previous: NDArray[np.float32],
    current: NDArray[np.float32],
    max_shift: int,
    ratio: float,
    min_samples: int,
) -> tuple[int, float, bool]:
    """How far the stripe profile slid, by normalised cross correlation over whole pixel lags.

    The search runs to just under one bar width, because a pattern that travels a whole bar
    between two frames lands on top of itself and no measurement can say which way it went.
    That is the wagon wheel case, and it is reported ambiguous rather than guessed at, which
    keeps it out of the smooth flow exemption.
    """
    length = min(len(previous), len(current))
    if length < min_samples or max_shift < 1:
        return (0, 0.0, True)
    a = np.asarray(previous[:length], dtype=np.float64)
    b = np.asarray(current[:length], dtype=np.float64)

    lags = list(range(-max_shift, max_shift + 1))
    scores: list[float] = []
    for lag in lags:
        if lag >= 0:
            x, y = a[: length - lag], b[lag:]
        else:
            x, y = a[-lag:], b[: length + lag]
        if len(x) < min_samples:
            scores.append(-2.0)
            continue
        xc = x - x.mean()
        yc = y - y.mean()
        denominator = float(np.sqrt(float((xc * xc).sum()) * float((yc * yc).sum())))
        scores.append(float((xc * yc).sum() / denominator) if denominator > 0 else -2.0)

    best = int(np.argmax(scores))
    peak = scores[best]
    if peak <= 0:
        return (0, peak, True)
    rivals = [
        score for index, score in enumerate(scores) if abs(index - best) >= 2 and score > 0
    ]
    ambiguous = bool(rivals) and max(rivals) >= ratio * peak
    return (lags[best], peak, ambiguous)


class PatternTracker:
    """Per frame pattern detection and the motion class the area limit turns on.

    One instance per analysis. `step` takes the same metric frame the general flash rule reads,
    already cropped to the picture, and returns what the rule saw on that frame.
    """

    def __init__(
        self,
        *,
        min_delta: float,
        dark_image_below: float,
        more_than_pairs: int,
        stationary_area_limit: float,
        changing_area_limit: float,
        settings: PatternSettings = PatternSettings(),
    ) -> None:
        self.min_delta = float(min_delta)
        self.dark_image_below = float(dark_image_below)
        self.more_than_pairs = int(more_than_pairs)
        self.stationary_area_limit = float(stationary_area_limit)
        self.changing_area_limit = float(changing_area_limit)
        self.settings = settings
        # A pair is a light bar and a dark bar, so the first failing pair count is
        # `more_than_pairs + 1` pairs, which is twice that many bars. This is the only place
        # the stripe count gate is applied: a scanline under it contributes nothing to the
        # mask, so a picture with too few stripes has a pattern area of zero and cannot be over
        # any limit. Checking it a second time downstream would make both copies untestable,
        # because either one alone would go on holding the line while the other was broken.
        self.min_bars = 2 * (self.more_than_pairs + 1)
        self._previous: PatternScan | None = None
        self._previous_mean: float | None = None
        self._history: deque[_Comparison] = deque(maxlen=settings.motion_history_frames)

    # ---- one frame ----

    def step(self, pts_ms: float, metric: NDArray[np.floating]) -> PatternObservation:
        frame = np.asarray(metric, dtype=np.float32)
        scan = stripe_mask(
            frame,
            min_delta=self.min_delta,
            dark_below=self.dark_image_below,
            min_bars=self.min_bars,
            orientations=self.settings.orientations,
            min_profile_samples=self.settings.min_profile_samples,
        )
        region_mean = (
            float(frame[scan.mask].mean()) if scan.mask.any() else float(frame.mean())
        )

        self._compare(scan, region_mean)
        motion, confidence = self._classify()
        limit = (
            self.stationary_area_limit
            if motion == MOTION_STATIONARY
            else self.changing_area_limit
        )
        # The stripe count and the bar difference are both already inside the area: a scanline
        # that did not reach `min_bars`, or whose bars did not reach the Guideline 1 flash
        # difference, put no pixels in the mask.
        over = scan.area_fraction > limit
        exempt = over and motion == MOTION_SMOOTH_FLOW

        self._previous = scan
        self._previous_mean = region_mean
        return PatternObservation(
            pts_ms=float(pts_ms),
            stripe_pairs=int(scan.stripe_pairs),
            area_fraction=scan.area_fraction,
            motion=motion,
            motion_confidence=confidence,
            area_limit=limit,
            over_limit=bool(over),
            exempt=bool(exempt),
        )

    def _compare(self, scan: PatternScan, region_mean: float) -> None:
        previous = self._previous
        if previous is None or previous.profile is None or scan.profile is None:
            # No pattern on one of the two frames, so there is no motion to measure and no
            # evidence to carry forward. The history restarts, which means the class is
            # uncertain again until it has filled, which is the fail safe direction.
            self._history.clear()
            return
        if previous.orientation != scan.orientation or len(previous.profile) != len(scan.profile):
            # "the stripes change direction" is one of the four changing cases in the
            # attachment, and a new dominant orientation is exactly that.
            self._history.append(_Comparison(False, False, False, True, 0, 0.0, True))
            return

        flashed = (
            self._previous_mean is not None
            and abs(region_mean - self._previous_mean) >= self.min_delta
        )
        difference = float(np.abs(scan.profile - previous.profile).mean())
        still_level = self.settings.still_fraction_of_min_delta * self.min_delta
        still = difference <= still_level

        a = previous.profile.astype(np.float64)
        b = scan.profile.astype(np.float64)
        a = a - a.mean()
        b = b - b.mean()
        denominator = float(np.sqrt(float((a * a).sum()) * float((b * b).sum())))
        correlation = float((a * b).sum() / denominator) if denominator > 0 else 0.0
        reversed_contrast = correlation <= self.settings.contrast_reversal_correlation

        if still:
            self._history.append(
                _Comparison(True, reversed_contrast, flashed, False, 0, 1.0, False)
            )
            return
        max_shift = max(1, int(scan.bar_width) - 1)
        lag, peak, ambiguous = _best_lag(
            previous.profile,
            scan.profile,
            max_shift,
            self.settings.ambiguity_ratio,
            self.settings.min_profile_samples,
        )
        self._history.append(
            _Comparison(False, reversed_contrast, flashed, False, lag, peak, ambiguous)
        )

    def _classify(self) -> tuple[str, float]:
        """Stationary, changing, smooth flow or uncertain, and how sure the detector is.

        The order matters and it is the fail safe order. Anything that oscillates, flashes,
        reverses contrast or turns is changing, whatever else it also did. Stationary and smooth
        flow both need a full run of agreeing evidence. Everything else is uncertain, which
        takes the stricter area and never the exemption.
        """
        history = list(self._history)
        if any(item.reversed_contrast or item.flashed or item.turned for item in history):
            return MOTION_CHANGING, 1.0
        if len(history) < self.settings.min_motion_frames:
            return MOTION_UNCERTAIN, 0.0

        if all(item.still for item in history):
            return MOTION_STATIONARY, 1.0
        if any(item.ambiguous or item.peak < self.settings.min_match_peak for item in history):
            return MOTION_UNCERTAIN, 0.0

        lags = np.array([item.lag for item in history], dtype=np.float64)
        moving = lags[lags != 0]
        if moving.size == 0:
            return MOTION_UNCERTAIN, 0.0
        if not (np.all(moving > 0) or np.all(moving < 0)):
            # It went one way and then the other. That is oscillation, not one direction.
            return MOTION_CHANGING, 1.0
        speeds = np.abs(lags)
        if float(speeds.mean()) < self.settings.min_flow_px:
            return MOTION_UNCERTAIN, 0.0
        spread = float(np.abs(moving).std() / np.abs(moving).mean())
        agreement = float(moving.size) / float(lags.size)
        if (
            agreement >= self.settings.flow_direction_agreement
            and spread <= self.settings.flow_speed_spread
        ):
            return MOTION_SMOOTH_FLOW, agreement
        return MOTION_UNCERTAIN, 0.0
