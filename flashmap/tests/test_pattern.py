"""Guideline 2, potentially harmful regular patterns.

The rule, its numbers and its status are quoted in flashmap/docs/SPEC_SOURCES.md section 8,
from ITU-R BT.1702-3 Attachment 1 to Annex 1, which is informative. Nothing in this file
restates a threshold: every number it asserts is read back off the profile, so a test cannot
quietly pin a number the spec page does not carry.

SAFETY. Every clip here is made by the `hazard_clip` fixture, analysed and deleted inside the
same test. Nothing opens one.

Each guard below was broken on purpose and watched go red. The two mutations that are written
up in docs/DECISIONS.md are the stripe count gate and the smooth flow exemption.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

import clipgen
from flashmap import BROADCAST_SDR, WCAG, analyze_file, build_map
from flashmap.analyze import PATTERN
from flashmap.pattern import (
    MOTION_STATIONARY,
    MOTION_UNCERTAIN,
    PatternSettings,
    PatternTracker,
    periodic_lines,
    scan_bars,
    stripe_mask,
)
from flashmap.pattern import _spans

W, H = 384, 216

# Grey codes, not thresholds. DARK to BRIGHT clears the Guideline 1 flash difference and DARK
# to DIM does not, both with several cd/m2 of room, so neither depends on where exactly the
# encoder and the analysis downscale land. test_the_chosen_greys_sit_where_this_file_says
# checks both against the profile rather than against a number typed in here.
DARK = (96, 96, 96)
BRIGHT = (160, 160, 160)
DIM = (120, 120, 120)


def nits(code: int) -> float:
    """Screen luminance of an 8 bit grey these clips are drawn with.

    clipgen hands full range RGB to the encoder and asks for limited range, so a grey code c
    comes back out of the decoder at video level c / 255, which was measured rather than
    assumed: codes 64, 96, 120, 128, 160 and 200 decode to 0.2511, 0.3744, 0.4703, 0.5023,
    0.6256 and 0.7854. From there it is the profile's own peak white and the BT.1886 curve of
    SPEC_SOURCES section 5.
    """
    from flashmap.color import bt1886_nits

    peak = BROADCAST_SDR.peak_nits or 200.0
    return float(bt1886_nits(np.array([code / 255.0]), peak).item())


@pytest.fixture
def rule():
    assert BROADCAST_SDR.pattern is not None
    return BROADCAST_SDR.pattern


def analyse(path):
    return analyze_file(path, BROADCAST_SDR)


# ---- the greys these clips are built from ----------------------------------------------


def test_the_chosen_greys_sit_where_this_file_says():
    delta = BROADCAST_SDR.general.min_delta
    ceiling = BROADCAST_SDR.general.dark_image_below
    assert nits(DARK[0]) < ceiling
    assert nits(BRIGHT[0]) - nits(DARK[0]) >= delta, "BRIGHT must clear the flash difference"
    assert nits(DIM[0]) - nits(DARK[0]) < delta, "DIM must sit under the flash difference"


# ---- the profile flag ------------------------------------------------------------------


def test_only_the_broadcast_profile_carries_a_pattern_rule():
    assert WCAG.pattern is None, "WCAG 2.2 SC 2.3.1 does not cover regular patterns"
    assert BROADCAST_SDR.pattern is not None


def test_the_wcag_profile_never_reports_a_pattern(hazard_clip):
    frames = [clipgen.grating(W, H, 8, DARK, BRIGHT)] * 30
    path = hazard_clip("wcagpattern.mkv", frames, fps=20)
    result = analyze_file(path, WCAG)
    assert result.pattern_segments == []
    assert result.pattern_exemptions == []
    document = build_map(result)
    assert document["profile"]["pattern_rule"] is None
    assert document["summary"]["pattern_rule_applied"] is False
    assert all(segment["reason"] != PATTERN for segment in document["segments"])


# ---- the stripe count gate -------------------------------------------------------------


# The counts below are written out rather than read off the profile, on purpose. The profile is
# the thing under test here: a test that builds its clip from `rule.more_than_pairs` moves with
# the number and goes on passing while the number is wrong. Attachment 1 prints "more than five
# light and dark pairs", so six pairs fails and five does not, and
# test_broadcast_profile.py::test_the_profile_carries_the_pattern_rule_and_says_it_is_informative
# is what ties these two numbers back to the quote.
FAILING_PAIRS = 6
PASSING_PAIRS = 5


def test_six_pairs_over_the_area_limit_is_a_pattern(hazard_clip, rule):
    assert FAILING_PAIRS == rule.more_than_pairs + 1
    frames = [clipgen.grating(W, H, FAILING_PAIRS, DARK, BRIGHT)] * 40
    path = hazard_clip("sixpairs.mkv", frames, fps=20)
    result = analyse(path)
    assert result.pattern_segments, "six pairs over the whole screen has to be a pattern"
    assert result.pattern_segments[0].stripe_pairs == FAILING_PAIRS
    assert result.flash_passes, "nothing flashes here, so the flash verdict must stay clean"
    assert not result.passes, "the whole profile verdict does include the pattern rule"


def test_five_pairs_is_under_the_gate(hazard_clip, rule):
    """More than five pairs, so five pairs is not more than five however big or bright it is."""
    assert PASSING_PAIRS == rule.more_than_pairs
    frames = [clipgen.grating(W, H, PASSING_PAIRS, DARK, BRIGHT)] * 40
    path = hazard_clip("fivepairs.mkv", frames, fps=20)
    result = analyse(path)
    assert result.pattern_segments == []
    assert result.passes


def test_a_picture_under_the_stripe_gate_has_no_pattern_area_at_all(rule):
    """The count gate lives in one place: a picture with too few stripes marks no pixels, so
    it cannot be over any area limit. This is what lets the limit check downstream be a plain
    area comparison instead of a second copy of the gate."""
    frame = np.full((64, 96), 10.0, dtype=np.float32)
    bar = 96 // (2 * PASSING_PAIRS)
    for index in range(0, 2 * PASSING_PAIRS, 2):
        frame[:, index * bar : (index + 1) * bar] = 60.0
    scan = stripe_mask(
        frame,
        min_delta=BROADCAST_SDR.general.min_delta,
        dark_below=BROADCAST_SDR.general.dark_image_below,
        min_bars=2 * (rule.more_than_pairs + 1),
        orientations=PatternSettings().orientations,
    )
    assert scan.area_fraction == 0.0
    assert scan.mask.sum() == 0


def test_a_black_to_peak_white_grating_is_flagged(hazard_clip, rule):
    """The worst pattern this generator can draw, and it used to pass.

    A six pair black to peak white grating has a black bar at one edge, and black sits under
    `LetterboxSettings.max_bar_luminance` on every sampled frame, so the picture detector took
    that bar for a pillarbox and cropped it away. Eleven bars were left, eleven bars is five
    pairs, and five pairs is not more than five, so the whole frame strobe pattern with a
    200 cd/m2 bar difference came back `pass: true`. Found by the verifier on 2026-09-17.
    """
    black, white = (0, 0, 0), (255, 255, 255)
    frames = [clipgen.grating(W, H, FAILING_PAIRS, black, white)] * 40
    path = hazard_clip("blackwhite.mkv", frames, fps=20)
    result = analyse(path)
    assert result.picture.width == result.picture.frame_width, (
        "a stripe of the pattern was cropped as a pillarbox bar, so the count came up short"
    )
    assert not result.picture.pillarbox
    assert result.pattern_segments, "a full frame black to white grating has to be a pattern"
    assert result.pattern_segments[0].stripe_pairs == FAILING_PAIRS
    assert not result.passes


def test_the_pair_count_survives_a_black_edge_bar(hazard_clip, rule):
    """The same crop cost a pattern one pair even when it was still flagged."""
    black, white = (0, 0, 0), (255, 255, 255)
    frames = [clipgen.grating(W, H, FAILING_PAIRS + 1, black, white)] * 40
    path = hazard_clip("blackwhite7.mkv", frames, fps=20)
    result = analyse(path)
    assert result.pattern_segments
    assert result.pattern_segments[0].stripe_pairs == FAILING_PAIRS + 1


# ---- the contrast condition ------------------------------------------------------------


def test_a_pattern_under_the_guideline_1_difference_is_not_a_pattern(hazard_clip, rule):
    """The bar to bar difference has to reach the Guideline 1 flash difference.

    Same geometry as the failing clip, same stripe count, bars too close together in luminance.
    """
    frames = [clipgen.grating(W, H, FAILING_PAIRS, DARK, DIM)] * 40
    path = hazard_clip("lowcontrast.mkv", frames, fps=20)
    assert analyse(path).pattern_segments == []


def test_the_pattern_rule_introduces_no_luminance_number_of_its_own(rule):
    described = rule.as_dict()
    assert "Guideline 1" in described["contrast_condition"]
    for key in ("min_delta", "dark_image_below", "min_nits_delta"):
        assert key not in described


# ---- the two area limits ---------------------------------------------------------------


def test_a_stationary_pattern_between_the_two_limits_is_left_alone(hazard_clip, rule):
    """Stationary gets 40%, so a pattern at about 26% of the picture is not hidden.

    It is hidden for the first few frames, while the detector has not yet seen enough to call
    the motion. That is the fail safe direction and docs/DECISIONS.md carries the reasoning, so
    the assertion is that the hide stops, not that it never starts.
    """
    frames = [clipgen.grating(W, H, FAILING_PAIRS, DARK, BRIGHT, area=0.30)] * 40
    path = hazard_clip("stationary30.mkv", frames, fps=20)
    result = analyse(path)
    covered = sum(s.end_ms - s.start_ms for s in result.pattern_segments)
    assert covered <= 400, f"a stationary pattern under 40% stayed hidden for {covered} ms"
    for segment in result.pattern_segments:
        assert segment.area_fraction > rule.changing_area_limit
        assert segment.area_fraction < rule.stationary_area_limit


def test_the_same_pattern_reversing_in_contrast_is_hidden_throughout(hazard_clip, rule):
    """Reversing in contrast gets 25%, and the same 26% now breaks it."""
    pairs = FAILING_PAIRS
    light = clipgen.grating(W, H, pairs, DARK, BRIGHT, area=0.30)
    dark = clipgen.grating(W, H, pairs, DARK, BRIGHT, area=0.30, invert=True)
    path = hazard_clip("reversing30.mkv", clipgen.alternating(40, light, dark), fps=20)
    result = analyse(path)
    covered = sum(s.end_ms - s.start_ms for s in result.pattern_segments)
    assert covered >= 1500, "a pattern reversing in contrast over 25% must stay hidden"
    assert result.pattern_exemptions == []


# ---- the smooth flow exemption, which fails safe ---------------------------------------


def test_a_smooth_flow_is_exempt_and_every_exemption_is_written_down(hazard_clip, rule):
    pairs = FAILING_PAIRS
    frames = [
        clipgen.grating(W, H, pairs, DARK, BRIGHT, area=0.55, shift=2 * index)
        for index in range(40)
    ]
    path = hazard_clip("smoothflow.mkv", frames, fps=20)
    result = analyse(path)
    assert result.pattern_exemptions, "a pattern flowing one way at a steady speed is exempt"
    exempted = sum(e.end_ms - e.start_ms for e in result.pattern_exemptions)
    hidden = sum(s.end_ms - s.start_ms for s in result.pattern_segments)
    assert exempted >= 1000, "most of the clip should be exempt once the flow is established"
    assert hidden <= 400, "only the frames before the flow was established should be hidden"
    for exemption in result.pattern_exemptions:
        assert exemption.stripe_pairs > rule.more_than_pairs
        assert exemption.area_fraction > exemption.area_limit
        assert "exempt" in exemption.as_dict()["exemption"]


def test_a_flow_that_stutters_is_not_smooth_and_is_never_exempted(hazard_clip, rule):
    """The fail safe case. The pattern moves, stops, moves again, always the same way.

    Nothing here changes direction, so the changing branch does not catch it. The flow is not
    unambiguous either, so it must not be exempted: an uncertain motion class takes the 25%
    area and never the exemption. A wrongly applied exemption hides a hazard from a child; a
    wrongly withheld one covers a few safe seconds.
    """
    pairs = FAILING_PAIRS
    frames = []
    travelled = 0
    for index in range(40):
        if (index // 4) % 2 == 0:
            travelled += 2
        frames.append(clipgen.grating(W, H, pairs, DARK, BRIGHT, area=0.55, shift=travelled))
    path = hazard_clip("stutter.mkv", frames, fps=20)
    result = analyse(path)
    assert result.pattern_exemptions == [], "a stuttering flow is not an obvious smooth flow"
    covered = sum(s.end_ms - s.start_ms for s in result.pattern_segments)
    assert covered >= 1500, "and because it is not exempt it stays hidden"
    assert all(s.area_limit == rule.changing_area_limit for s in result.pattern_segments)


def test_an_uncertain_motion_class_takes_the_stricter_area(rule):
    """Straight at the classifier: with no history at all the class is uncertain, and
    uncertain must produce the changing limit and never the stationary one."""
    tracker = PatternTracker(
        min_delta=BROADCAST_SDR.general.min_delta,
        dark_image_below=BROADCAST_SDR.general.dark_image_below,
        more_than_pairs=rule.more_than_pairs,
        stationary_area_limit=rule.stationary_area_limit,
        changing_area_limit=rule.changing_area_limit,
    )
    frame = np.zeros((32, 64), dtype=np.float32)
    frame[:, ::4] = 60.0
    first = tracker.step(0.0, frame)
    assert first.motion == MOTION_UNCERTAIN
    assert first.motion_confidence == 0.0
    assert first.area_limit == rule.changing_area_limit
    assert not first.exempt


def test_a_still_picture_is_called_stationary_once_there_is_evidence(rule):
    tracker = PatternTracker(
        min_delta=BROADCAST_SDR.general.min_delta,
        dark_image_below=BROADCAST_SDR.general.dark_image_below,
        more_than_pairs=rule.more_than_pairs,
        stationary_area_limit=rule.stationary_area_limit,
        changing_area_limit=rule.changing_area_limit,
    )
    frame = np.zeros((32, 64), dtype=np.float32)
    frame[:, ::4] = 60.0
    settings = PatternSettings()
    last = None
    for index in range(settings.min_motion_frames + 2):
        last = tracker.step(index * 50.0, frame)
    assert last is not None
    assert last.motion == MOTION_STATIONARY
    assert last.area_limit == rule.stationary_area_limit


# ---- what is not a pattern -------------------------------------------------------------


def test_a_gradient_across_the_screen_is_not_stripes(hazard_clip):
    ramp = np.zeros((H, W, 3), dtype=np.uint8)
    ramp[:, :] = np.linspace(16, 235, W, dtype=np.uint8)[None, :, None]
    path = hazard_clip("ramp.mkv", [ramp] * 30, fps=20)
    assert analyse(path).pattern_segments == []


def test_a_flat_picture_is_not_stripes(calm_clip):
    path = calm_clip("flat.mkv", [clipgen.solid(W, H, DARK)] * 30, fps=20)
    assert analyse(path).pattern_segments == []


# ---- the scan, on its own --------------------------------------------------------------


def test_scan_bars_counts_twelve_bars_as_twelve():
    line = np.repeat(np.array([10.0, 60.0] * 6, dtype=np.float32), 8)[None, :]
    bars, first, last = scan_bars(line, min_delta=20.0, dark_below=160.0)
    assert int(bars[0]) == 12
    assert 0 <= int(first[0]) < int(last[0]) < line.shape[1]


def test_scan_bars_cannot_reach_the_gate_on_a_ramp():
    """A ramp swings one way and never back, so it has one boundary and two bars however far
    it travels. Twelve is the first count that can fail, so a gradient can never get there."""
    line = np.linspace(0.0, 150.0, 200, dtype=np.float32)[None, :]
    bars, _, _ = scan_bars(line, min_delta=20.0, dark_below=160.0)
    assert int(bars[0]) <= 2


def test_scan_bars_needs_the_darker_bar_under_the_ceiling():
    """Both bars above the darker image ceiling: a real difference, no countable boundary."""
    line = np.repeat(np.array([170.0, 220.0] * 6, dtype=np.float32), 8)[None, :]
    bars, _, _ = scan_bars(line, min_delta=20.0, dark_below=160.0)
    assert int(bars[0]) == 0


def test_the_scan_finds_stripes_whichever_way_they_run():
    base = np.full((64, 64), 10.0, dtype=np.float32)
    vertical = base.copy()
    vertical[:, ::8] = 60.0
    vertical[:, 1::8] = 60.0
    horizontal = vertical.T.copy()
    diagonal = base.copy()
    rows, columns = np.indices(diagonal.shape)
    diagonal[((rows + columns) // 4) % 2 == 0] = 60.0
    for name, frame in (("vertical", vertical), ("horizontal", horizontal), ("diagonal", diagonal)):
        scan = stripe_mask(
            frame,
            min_delta=20.0,
            dark_below=160.0,
            min_bars=12,
            orientations=PatternSettings().orientations,
        )
        assert scan.stripe_pairs >= 6, f"{name} stripes were not counted"
        assert scan.area_fraction > 0.25, name


# ---- the map ---------------------------------------------------------------------------


def test_the_diagonal_families_are_real_diagonals_and_not_rows_in_disguise():
    """A grating the row and column scans cannot reach.

    The value depends on x + y with a bar every 8, on a square picture. A row crosses 8 bars,
    which is four pairs and under the gate. A line that runs corner to corner crosses twice as
    many, because x + y moves two for every step along it, so the same picture holds eight
    pairs in that orientation. BT.1702-3 says stripes in any orientation, so it has to be found.
    """
    rows, columns = np.indices((64, 64))
    frame = np.where(((columns + rows) // 8) % 2 == 0, 60.0, 10.0).astype(np.float32)
    limits = {"min_delta": 20.0, "dark_below": 160.0, "min_bars": 12}

    flat = stripe_mask(frame, orientations=("rows", "columns"), **limits)
    assert flat.stripe_pairs < 6 and flat.area_fraction == 0.0

    found = stripe_mask(frame, orientations=PatternSettings().orientations, **limits)
    assert found.stripe_pairs >= 6
    assert found.orientation in ("diagonal", "antidiagonal")
    assert found.area_fraction > 0.25


def test_the_map_carries_pattern_segments_where_every_reader_already_looks(hazard_clip, rule):
    frames = [clipgen.grating(W, H, FAILING_PAIRS + 1, DARK, BRIGHT)] * 40
    path = hazard_clip("mappattern.mkv", frames, fps=20)
    result = analyse(path)
    document = build_map(result)

    patterns = [s for s in document["segments"] if s["reason"] == PATTERN]
    assert patterns, "a pattern segment belongs in segments, where a player already looks"
    for segment in patterns:
        assert segment["start_ms"] < segment["end_ms"]
        assert segment["is_a_wcag_finding"] is False
        assert "BT.1702-3 Attachment 1 to Annex 1" in segment["source"]
        assert "informative" in segment["source"]
        # Its own kind: none of the flash segment fields, which mean nothing here.
        for flash_only in ("flash_first_ms", "max_flashes_in_window", "breaks_baseline"):
            assert flash_only not in segment

    summary = document["summary"]
    assert summary["pattern_segment_count"] == len(result.pattern_segments)
    assert summary["pattern_rule_applied"] is True
    assert summary["flash_pass"] is True, "nothing flashed, so the flash verdict is clean"
    assert summary["pattern_pass"] is False
    assert summary["pass"] is False
    assert summary["segment_count"] == len(document["segments"])
    assert "WCAG" in summary["pattern_findings_are_not_wcag"]
    assert "Ofcom" not in json.dumps(document)


def test_the_map_stays_readable_by_a_consumer_that_knows_only_start_and_end(hazard_clip, rule):
    """The map contract a player and the pipeline rely on: sorted, non overlapping in time
    order, every segment a real interval, and summary.pass agreeing with the list."""
    frames = [clipgen.grating(W, H, FAILING_PAIRS, DARK, BRIGHT)] * 40
    path = hazard_clip("mapshape.mkv", frames, fps=20)
    document = build_map(analyse(path))
    starts = [s["start_ms"] for s in document["segments"]]
    assert starts == sorted(starts)
    for segment in document["segments"]:
        assert isinstance(segment["start_ms"], int) and isinstance(segment["end_ms"], int)
        assert segment["end_ms"] > segment["start_ms"]
        assert segment["start_ms"] >= 0
    assert document["summary"]["pass"] == (not document["segments"])


# ---- the periodicity test ---------------------------------------------------------------
#
# "Regular patterns" is the guideline's own word and scan_bars on its own does not check it:
# it counts alternating steps that reach the Guideline 1 flash difference, and a page of
# readable text is full of those. Every guard below was broken on purpose and seen red; the
# mutation is named in each docstring.


def _line(values) -> np.ndarray:
    return np.asarray(values, dtype=np.float32)[None, :]


def _bar_line(length: int, bars: int, dark: float = 5.0, light: float = 180.0) -> np.ndarray:
    bar = length / bars
    xs = np.arange(length)
    return _line(np.where((np.floor(xs / bar).astype(int) % 2) == 0, light, dark))


def _scan(frame, rule, **kwargs):
    return stripe_mask(
        frame,
        min_delta=BROADCAST_SDR.general.min_delta,
        dark_below=BROADCAST_SDR.general.dark_image_below,
        min_bars=2 * (rule.more_than_pairs + 1),
        orientations=("rows",),
        **kwargs,
    )


def test_an_even_grating_is_periodic_and_its_period_is_one_pair(rule):
    line = _bar_line(192, 12)
    bars, first, last = scan_bars(line, BROADCAST_SDR.general.min_delta,
                                  BROADCAST_SDR.general.dark_image_below)
    low, high = _spans(bars, first, last, 192)
    periodic, period, peak = periodic_lines(
        line, bars >= 12, low, high, min_cycles=PatternSettings().min_cycles_for_period,
        min_peak=PatternSettings().min_autocorrelation_peak,
    )
    assert bool(periodic[0]), "a twelve bar grating is the definition of regular"
    assert period[0] == pytest.approx(192 / 6, abs=2), (
        "one cycle is a light bar and a dark bar, so six pairs across 192 samples is 32"
    )


def test_the_cycle_floor_does_not_re_apply_the_spec_pair_count(rule):
    """The regression this constant exists for.

    A twelve bar grating filling the picture spans five and a half periods, because the run
    is measured from the first counted boundary to the last plus half a bar at each end. A
    periodicity search told to find six whole cycles inside that run cannot, so the first
    count the attachment can fail would have stopped being found at all. That is a hazard
    walking out of the detector, so the floor is three and the pair count is a gate of its
    own.

    Seen to fail by setting min_cycles to the pair gate, which is what the first version did:
    the assertion below goes red with `assert False`.
    """
    line = _bar_line(192, 12)
    bars, first, last = scan_bars(line, BROADCAST_SDR.general.min_delta,
                                  BROADCAST_SDR.general.dark_image_below)
    low, high = _spans(bars, first, last, 192)
    at_the_pair_count, _, _ = periodic_lines(line, bars >= 12, low, high, min_cycles=6, min_peak=0.5)
    at_the_floor, _, _ = periodic_lines(
        line, bars >= 12, low, high,
        min_cycles=PatternSettings().min_cycles_for_period, min_peak=0.5,
    )
    assert not bool(at_the_pair_count[0]), (
        "this documents why the floor is not the pair count; if this passes the run length "
        "arithmetic has changed and the comment above needs rewriting"
    )
    assert bool(at_the_floor[0])


def test_irregular_high_contrast_edges_are_not_a_pattern(rule):
    """A line of text, reduced to what it is: plenty of steps, no period.

    The widths and gaps below are a real scan line's worth of glyph strokes rather than a
    grating's. Every step clears the Guideline 1 difference, so scan_bars counts far more
    than twelve bars, and nothing about it repeats.

    Seen to fail by returning `qualifies` unchanged from periodic_lines, which is what the
    detector did before this: the area assertion goes red at 1.0.
    """
    rng = np.random.default_rng(20260919)
    values = []
    light = True
    while len(values) < 192:
        width = int(rng.integers(1, 9))
        values.extend([180.0 if light else 5.0] * width)
        light = not light
    line = _line(values[:192])
    bars, _, _ = scan_bars(line, BROADCAST_SDR.general.min_delta,
                           BROADCAST_SDR.general.dark_image_below)
    assert int(bars[0]) >= 2 * (rule.more_than_pairs + 1), (
        "the point of this case is that the bar count gate does let it through"
    )
    frame = np.repeat(line, 64, axis=0)
    assert _scan(frame, rule, require_periodicity=False).area_fraction == pytest.approx(1.0)
    assert _scan(frame, rule).area_fraction == 0.0


def test_turning_the_periodicity_test_off_restores_the_old_reading(rule):
    """The ablation has to be real, or the number it produces means nothing."""
    rng = np.random.default_rng(7)
    values = []
    light = True
    while len(values) < 192:
        values.extend([180.0 if light else 5.0] * int(rng.integers(1, 9)))
        light = not light
    frame = np.repeat(_line(values[:192]), 64, axis=0)
    off = _scan(frame, rule, require_periodicity=False)
    on = _scan(frame, rule)
    assert off.area_fraction > on.area_fraction
    assert on.counted_area_fraction == pytest.approx(off.area_fraction), (
        "counted_area_fraction is what the area would have been without the test, so it has "
        "to match the ablation exactly"
    )


def test_a_grating_still_fails_end_to_end_with_the_periodicity_test_on(hazard_clip, rule):
    """The whole point of the rule, checked through the shipped path rather than a helper."""
    frames = [clipgen.grating(W, H, FAILING_PAIRS, DARK, BRIGHT)] * 40
    path = hazard_clip("periodic_sixpairs.mkv", frames, fps=20)
    result = analyse(path)
    assert result.pattern_segments
    assert result.pattern_segments[0].stripe_pairs == FAILING_PAIRS


def test_the_tuning_says_which_way_it_ran(rule):
    """A map that does not record whether the periodicity test was on cannot be compared
    with one that does. Seen to fail by dropping either key from as_dict."""
    tuning = rule.settings.as_dict()
    assert tuning["require_periodicity"] is True
    assert 0.0 < tuning["min_autocorrelation_peak"] <= 1.0
    assert tuning["min_cycles_for_period"] >= 2
    assert "not thresholds" in tuning["what_these_are"]


def test_the_peak_does_not_fall_away_as_the_period_grows(rule):
    """The unbiased correction, and what it is worth.

    At lag k only run - k samples of the run overlap themselves, so a raw autocorrelation
    reports a long period as weaker than a short one for no reason but its length. A grating
    with three cycles in the run would come back at about two thirds of a grating with
    twenty, and the threshold would then mean something different at each spatial frequency.
    Dividing by the overlap takes that out.

    Seen to fail by dropping the correction: the four cycle peak comes back near 0.71 and
    this goes red.
    """
    peaks = {}
    for cycles in (4, 6, 12, 24):
        line = _bar_line(480, 2 * cycles)
        bars, first, last = scan_bars(line, BROADCAST_SDR.general.min_delta,
                                      BROADCAST_SDR.general.dark_image_below)
        low, high = _spans(bars, first, last, 480)
        _, _, peak = periodic_lines(line, bars >= 2, low, high, min_cycles=3, min_peak=0.5)
        peaks[cycles] = float(peak[0])
    assert min(peaks.values()) > 0.9, (
        f"a pure square wave should correlate with itself at its own period: {peaks}"
    )
    assert max(peaks.values()) - min(peaks.values()) < 0.1, (
        f"the peak must not depend on how many cycles happen to fit: {peaks}"
    )
