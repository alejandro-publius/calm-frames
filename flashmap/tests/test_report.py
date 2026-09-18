"""The report page, and the two things that have to be true of it.

**It is one file.** Nothing is fetched when it opens, there is no sibling
asset, and every picture is inside it as a data URI.

**Every picture in it passes flashmap.** The timeline is a picture this project
puts in front of people, and this project's whole claim is that it checks
pictures, so the pictures it draws are checked by the same analyzer as
everything else. eval/brand_assets_check.py set that pattern, and one thing it
learned the hard way is copied here on purpose: each picture is analysed on its
own, held for two seconds, and nothing is cut against anything else.

Why not a worst case. The first version of the brand check alternated each
image with the app's background at 5 Hz, and failed, and that failure was the
test's fault: those images do not follow one another anywhere a person sees
them. The same is true here and more so. A lane is a static PNG in a static
HTML page. It does not animate, it does not follow another picture, and
nothing a reader can do makes one lane replace another five times a second.
Inventing that case would fail and mean nothing. What a shipped picture is
worth asking is whether the picture itself holds anything over the thresholds,
which is what a still analysed alone answers.

A still cannot flash, so the flash rule alone would pass any drawing this
module could make and the check would be one that cannot fail. So every
picture goes through two profiles. ``wcag`` is the flash rule. ``broadcast``
also carries the regular pattern criterion from ITU-R BT.1702-3, more than
five light and dark pairs, which is the hazard a drawn timeline could really
hold: two hundred segments drawn one thin bright bar each is a fine high
contrast pattern.

Neither profile is what keeps the timeline safe, and this file says where each
guard stops. The block cap keeps a lane under the attachment's count. The lane
colours keep every step in a lane under the luminance difference that makes a
light and dark pair at all, which is ``TestNoStepInALaneCanBeABar`` below and
is the one that holds however many blocks are drawn. And the page a reader
actually sees, lanes at layout size with the text around them, is measured by
eval/report_page_check.py, which renders it in a browser and runs the analyzer
over display sized frames of it.

There are two negative controls, one for each. A file that flashes at 10 Hz,
which ``wcag`` refuses. A full frame of forty stripe pairs, which
``broadcast`` refuses and ``wcag`` passes. Without both, a green run here
would say nothing.

SAFETY. The flashing negative control is built in pytest's temporary
directory, analysed, and gone when the test ends. Nothing here opens it in a
player.
"""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

from flashmap import report as report_module
from flashmap.cli import build_parser, main
from flashmap.pngout import encode_png
from flashmap.report import (
    MAX_BLOCKS_PER_LANE,
    MIN_BLOCK_PX,
    MIN_GAP_PX,
    PRESETS,
    Block,
    LanePlan,
    ReportDocument,
    Span,
    bar_difference_nits,
    build_report,
    cover_intervals,
    lane_nits,
    looks_like_a_map,
    plan_blocks,
    render_lane,
    widest_lane_step_nits,
)

REPO = Path(__file__).resolve().parents[2]

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg is needed to build a still to analyse"
)


# ---------------------------------------------------------------------------
# A map to report on
# ---------------------------------------------------------------------------


def a_map(segments: list[dict], duration_ms: float = 30_000.0) -> dict:
    return {
        "schema": "https://calm-frames.github.io/schemas/flashmap-map-v1.json",
        "version": 1,
        "generator": {"name": "flashmap", "version": "1.0.0"},
        "created_utc": "2026-09-17T12:00:00Z",
        "source": {
            "path": "HAZARD_example.mp4",
            "sha256": "a" * 64,
            "size_bytes": 1234,
            "coded_width": 640,
            "coded_height": 360,
            "duration_ms": duration_ms,
            "frame_count": 900,
        },
        "picture": {"left": 0, "top": 0, "width": 192, "height": 108},
        "profile": {
            "name": "wcag",
            "title": "WCAG 2.2 Success Criterion 2.3.1",
            "flash_limit_per_second": 3,
            "window_ms": 1000,
            "area_fraction_limit": 0.25,
            "area_window_mode": "ten-degree-field",
            "rules_not_implemented": ["the fine balanced pattern exception", "any HDR rule"],
        },
        "segments": segments,
        "summary": {
            "pass": not segments,
            "segment_count": len(segments),
            "hidden_ms": 0,
            "general_segment_count": sum(1 for s in segments if s.get("reason") == "general"),
            "red_segment_count": sum(1 for s in segments if s.get("reason") == "red"),
        },
    }


def a_segment(start_ms: float, end_ms: float, reason: str = "general") -> dict:
    return {
        "start_ms": start_ms,
        "end_ms": end_ms,
        "reason": reason,
        "area_fraction": 1.0,
        "area_window": "wcag-10deg",
        "max_flashes_in_window": 11,
    }


@pytest.fixture
def built() -> ReportDocument:
    document = a_map(
        [
            a_segment(4_367, 7_767),
            a_segment(14_367, 17_767, "red"),
            a_segment(24_367, 27_767),
        ]
    )
    return build_report({"wcag": document}, title="Example", primary="wcag")


# ---------------------------------------------------------------------------
# One file, nothing fetched
# ---------------------------------------------------------------------------

LOADING_ATTRIBUTE = re.compile(r"""\b(?:src|href|data|poster)\s*=\s*["']([^"']*)["']""", re.I)
FORBIDDEN_TAGS = ("<script", "<link", "<iframe", "<object", "<embed", "<video", "<audio", "<svg")


class TestSelfContained:
    def test_every_loaded_thing_is_inside_the_file(self, built: ReportDocument):
        loaded = LOADING_ATTRIBUTE.findall(built.html)
        assert loaded, "the report should have at least one picture in it"
        outside = [value for value in loaded if not value.startswith("data:")]
        assert not outside, (
            "these are loaded from somewhere other than this file, so the report is not "
            f"self contained: {outside}"
        )

    def test_nothing_can_pull_anything_in(self, built: ReportDocument):
        lowered = built.html.lower()
        found = [tag for tag in FORBIDDEN_TAGS if tag in lowered]
        assert not found, f"the report has {found} in it, and any of those can fetch"
        assert "@import" not in lowered
        assert "url(" not in lowered, "a CSS url() can reach off the page"

    def test_no_web_address_is_ever_fetched(self, built: ReportDocument):
        """A URL may appear as text. None may appear as something to load.

        A license row names the page the file came from, and printing that is
        the point of the row. What must never happen is a URL in an attribute
        the browser acts on, which the test above covers, so this one only
        holds the line that nothing else smuggles one in.
        """
        for match in re.finditer(r"https?://\S+", built.html):
            snippet = built.html[max(0, match.start() - 60) : match.start()]
            assert "src=" not in snippet and "href=" not in snippet, (
                f"a web address sits in a loading attribute: {match.group(0)!r}"
            )

    def test_it_opens_as_html(self, built: ReportDocument):
        assert built.html.startswith("<!doctype html>")
        assert "<style>" in built.html and "</html>" in built.html


# ---------------------------------------------------------------------------
# No frame of the film
# ---------------------------------------------------------------------------


class TestNoFrameOfTheFilm:
    def test_the_only_pictures_are_lanes_this_module_drew(self, built: ReportDocument):
        assert set(built.images) == {
            "lane-flashes",
            "lane-hidden-wcag",
            "lane-hidden-broadcast",
            "lane-hidden-extra-cautious",
        }

    def test_the_report_says_it_shows_no_frame(self, built: ReportDocument):
        assert "never shows a frame of the film" in built.html
        assert "It is not displayed." in built.html

    def test_a_lane_holds_no_colour_but_the_palette(self):
        """A lane is drawn from numbers, so it can only hold the three fills.

        If a frame of the film ever leaked into a lane, the lane would hold
        colours that are not in this list.
        """
        plan = plan_blocks([Span(1_000, 2_000), Span(5_000, 6_000, "red")], 10_000.0)
        lane = render_lane(plan)
        allowed = {
            report_module._rgb(report_module.LANE_GROUND),
            report_module._rgb(report_module.LANE_GENERAL),
            report_module._rgb(report_module.LANE_RED),
        }
        used = {tuple(int(v) for v in colour) for colour in np.unique(lane.reshape(-1, 3), axis=0)}
        assert used <= allowed, f"a lane holds colours that are not the palette: {used - allowed}"


# ---------------------------------------------------------------------------
# The drawing cannot become a hazard of its own
# ---------------------------------------------------------------------------


def blocks_of(lane: np.ndarray) -> list[tuple[int, int]]:
    """Read the drawn blocks back out of the pixels, by column."""
    ground = np.array(report_module._rgb(report_module.LANE_GROUND), dtype=np.uint8)
    painted = (lane != ground).any(axis=2).any(axis=0)
    runs: list[tuple[int, int]] = []
    start = None
    for x, on in enumerate(painted):
        if on and start is None:
            start = x
        elif not on and start is not None:
            runs.append((start, x))
            start = None
    if start is not None:
        runs.append((start, len(painted)))
    return runs


class TestTheTimelineIsNotAStripePattern:
    """The hazard the flash thresholds do not reach.

    flashmap measures flashes over time. A still cannot flash, so a still
    always passes, and a timeline drawn one thin bright bar per segment would
    pass while being a fine high contrast pattern, which is a photosensitive
    hazard of a different kind. These are the limits that stop that, and they
    are the drawing's own, not a threshold read off a spec.
    """

    def test_two_hundred_short_flashes_do_not_become_two_hundred_bars(self):
        """Close together, so the minimum gap joins them before the cap does."""
        spans = [Span(i * 100.0, i * 100.0 + 40.0) for i in range(200)]
        plan = plan_blocks(spans, 30_000.0)
        assert len(plan.blocks) == 1
        assert "drawn as one block" in " ".join(plan.notes)

    def test_forty_flashes_spread_across_a_film_hit_the_cap(self):
        """Far enough apart to survive the minimum gap, so the cap catches them."""
        spans = [Span(i * 7_000.0, i * 7_000.0 + 200.0) for i in range(40)]
        plan = plan_blocks(spans, 300_000.0)
        assert plan.collapsed
        assert 1 <= len(plan.blocks) <= MAX_BLOCKS_PER_LANE
        assert "Neighbours were joined" in " ".join(plan.notes)

    def test_the_limits_are_the_numbers_the_page_was_designed_around(self):
        """Written out, not read back from the module.

        Every other test here reads the limits from flashmap.report, so on
        their own they would follow the constants anywhere: raise the cap to a
        hundred thousand and they all still pass. This one pins the numbers, so
        loosening a limit is a red test and a decision somebody made on
        purpose.
        """
        assert MIN_BLOCK_PX == 8
        assert MIN_GAP_PX == 8
        assert MAX_BLOCKS_PER_LANE == 5

    def test_the_block_cap_is_the_pattern_criterion_and_not_a_number_we_liked(self):
        """The cap is read off the profile that measures patterns.

        ITU-R BT.1702-3 Attachment 1 to Annex 1 says more than five light and
        dark pairs. A lane that draws at most five blocks shows at most five
        pairs, so it cannot reach the criterion however large the bars are.
        If the broadcast profile's number ever changes, this goes red rather
        than the report quietly drawing one pair too many.
        """
        from flashmap.profiles import PROFILES

        rule = PROFILES["broadcast"].pattern
        assert rule is not None, "the broadcast profile no longer carries a pattern rule"
        assert MAX_BLOCKS_PER_LANE == rule.more_than_pairs

    def test_no_lane_ever_draws_more_blocks_than_the_limit(self):
        for count in (1, 5, 9, 40, 200):
            spans = [Span(i * 1_000.0, i * 1_000.0 + 200.0) for i in range(count)]
            plan = plan_blocks(spans, 300_000.0)
            drawn = blocks_of(render_lane(plan))
            assert len(drawn) <= 5, (
                f"{count} spans drew {len(drawn)} bars, over the limit of 5"
            )

    def test_no_bar_and_no_gap_is_finer_than_the_limits(self):
        # Spans a few milliseconds long and a few milliseconds apart: every one
        # of them is far under a pixel at this scale.
        spans = [Span(10_000 + i * 12.0, 10_000 + i * 12.0 + 5.0) for i in range(6)]
        plan = plan_blocks(spans, 600_000.0)
        drawn = blocks_of(render_lane(plan))
        assert drawn, "the spans have to be drawn, not dropped"
        for left, right in drawn:
            assert right - left >= 8, f"a {right - left} px bar is a hairline"
        for (_, end), (start, _) in zip(drawn, drawn[1:]):
            assert start - end >= 8, f"a {start - end} px gap reads as a stripe"

    def test_the_cap_joins_neighbours_and_does_not_flatten_the_film(self):
        """A real title has flashes in clumps, and the lane has to show where.

        The first version collapsed everything over the cap into one block from
        the first span to the last. Safe, and on a real title (fifty three
        spans between 19 s and 590 s of a ten minute film) it drew one bar
        across almost the whole lane, which told a reader nothing at all. This
        joins the closest neighbours instead, so the bars stay where the
        flashes are.
        """
        # Two clumps at the ends and nothing in the middle, spaced far enough
        # apart that the minimum gap leaves them separate and the cap is what
        # has to deal with them.
        spans = [Span(1_000.0 + i * 4_000.0, 1_000.0 + i * 4_000.0 + 600.0) for i in range(6)]
        spans += [Span(250_000.0 + i * 4_000.0, 250_000.0 + i * 4_000.0 + 600.0) for i in range(6)]
        plan = plan_blocks(spans, 300_000.0)

        assert plan.collapsed
        assert len(plan.blocks) <= MAX_BLOCKS_PER_LANE
        drawn = blocks_of(render_lane(plan))
        assert len(drawn) >= 2, "the two clumps were flattened into one bar"
        # The quiet middle of the film stays quiet.
        middle = report_module.LANE_WIDTH_PX // 2
        assert not any(left <= middle < right for left, right in drawn), (
            "a bar covers the middle of the film, where nothing was flagged"
        )

    def test_the_picture_saying_less_than_the_numbers_is_written_down(self):
        spans = [Span(10_000 + i * 12.0, 10_000 + i * 12.0 + 5.0) for i in range(4)]
        plan = plan_blocks(spans, 600_000.0)
        notes = " ".join(plan.notes)
        assert notes, "a drawing that was made coarser has to say so on the page"
        assert "wider than the time they cover" in notes or "one block" in notes

    def test_a_span_is_never_drawn_narrower_than_it_is(self):
        """The limits may only make the picture coarser, never smaller."""
        span = Span(10_000.0, 20_000.0)
        plan = plan_blocks([span], 30_000.0)
        drawn = blocks_of(render_lane(plan))
        assert len(drawn) == 1
        left, right = drawn[0]
        assert left <= int(10_000 / 30_000 * report_module.LANE_WIDTH_PX)
        assert right >= int(20_000 / 30_000 * report_module.LANE_WIDTH_PX)


# ---------------------------------------------------------------------------
# A bar that cannot be a bar
# ---------------------------------------------------------------------------


def nits_of(picture: np.ndarray) -> np.ndarray:
    """A drawn picture in cd/m2, the way the broadcast profile measures one.

    BT.709 luma of the sRGB bytes, then color.bt1886_nits at the profile's own
    peak white. The analyzer reaches the same place through the decoder's luma
    plane; this starts from the pixels, because what is being asked about here
    is the drawing rather than a re-encode of it.
    """
    from flashmap.color import LUMA_B, LUMA_G, LUMA_R, bt1886_nits
    from flashmap.profiles import PROFILES

    peak = PROFILES["broadcast"].peak_nits
    assert peak is not None
    weights = np.array([LUMA_R, LUMA_G, LUMA_B], dtype=np.float32)
    level = (picture.astype(np.float32) * weights).sum(axis=-1) / np.float32(255.0)
    return np.asarray(bt1886_nits(level, peak))


def bars_in(picture: np.ndarray) -> int:
    """The most bars the pattern rule's own scanner finds on any line of this.

    `flashmap.pattern.scan_bars` is the rule's own bar counter, handed the
    profile's own Guideline 1 numbers. Rows and columns both, because a lane is
    a wide short picture and a bar boundary in it could run either way.
    """
    from flashmap.pattern import scan_bars
    from flashmap.profiles import PROFILES

    rule = PROFILES["broadcast"].general
    values = nits_of(picture)
    rows, _, _ = scan_bars(values, rule.min_delta, rule.dark_image_below)
    columns, _, _ = scan_bars(values.T, rule.min_delta, rule.dark_image_below)
    return max(int(rows.max()) if rows.size else 0, int(columns.max()) if columns.size else 0)


RED = "red"
GENERAL = "general"


def a_lane_the_cap_would_never_allow(blocks: int = 200) -> LanePlan:
    """A lane with forty times as many blocks as plan_blocks will ever draw.

    Built by hand, past `plan_blocks`, because that is the point: this is the
    lane the block cap exists to prevent, and the question is what the drawing
    would be worth if the cap came off tomorrow.
    """
    width = report_module.LANE_WIDTH_PX
    step = width // blocks
    drawn = [
        Block(index * step, index * step + max(1, step // 2), RED if index % 2 else GENERAL)
        for index in range(blocks)
    ]
    return LanePlan(drawn, blocks, 0, 0, False)


class TestNoStepInALaneCanBeABar:
    """The limit the block cap is not.

    The cap keeps a lane under the attachment's count of more than five light
    and dark pairs. It is one number, and one number away from being wrong: at
    six it stops working. This is the other half, and it fails in a different
    direction. A light and dark pair only exists where the step between the two
    levels reaches the Guideline 1 flash difference, so a lane drawn entirely
    under that difference holds no pair at any count, at any width, at any area.
    """

    def test_the_widest_step_a_lane_can_hold_is_well_under_the_difference(self):
        from flashmap.profiles import PROFILES

        difference = PROFILES["broadcast"].general.min_delta
        assert bar_difference_nits() == difference
        step = widest_lane_step_nits()
        assert step < difference / 2.0, (
            f"a lane can hold a {step:.2f} cd/m2 step against a {difference:.0f} cd/m2 "
            "difference, which is not the comfortable margin this was designed for"
        )

    def test_the_numbers_are_the_ones_the_drawing_was_designed_around(self):
        """Written out, not read back from the module.

        Every other test here reads the colours from flashmap.report, so on
        their own they would follow them anywhere. This one pins them, so
        brightening a lane is a red test and a decision somebody made on
        purpose. The cd/m2 figures are the ones in the comment beside the
        colours in flashmap/src/flashmap/report.py.
        """
        assert report_module.LANE_GROUND == "#000000"
        assert report_module.LANE_GENERAL == "#173B47"
        assert report_module.LANE_RED == "#1F4D5C"
        assert round(lane_nits(report_module.LANE_GROUND), 2) == 0.00
        assert round(lane_nits(report_module.LANE_GENERAL), 2) == 4.45
        assert round(lane_nits(report_module.LANE_RED), 2) == 8.47
        assert round(widest_lane_step_nits(), 2) == 8.47
        assert bar_difference_nits() == 20.0

    def test_the_rules_own_scanner_finds_no_bar_in_a_drawn_lane(self):
        plan = plan_blocks(
            [Span(1_000, 2_000), Span(5_000, 6_000, "red"), Span(8_000, 8_100)], 10_000.0
        )
        assert bars_in(render_lane(plan)) == 0

    def test_it_finds_none_in_a_lane_the_cap_would_never_allow(self):
        """Two hundred bars, alternating kinds, and still not one pair."""
        lane = render_lane(a_lane_the_cap_would_never_allow())
        drawn = blocks_of(lane)
        assert len(drawn) > MAX_BLOCKS_PER_LANE * 10, (
            "this test is worthless unless the lane it builds really is past the cap"
        )
        assert bars_in(lane) == 0, (
            "a lane with two hundred blocks in it holds a light and dark pair, so the block "
            "cap is the only thing keeping the timeline safe after all"
        )

    def test_the_scanner_does_find_the_bars_in_a_stripe_pattern(self):
        """The negative control, and without it the two above say nothing.

        They could mean the lane holds no bar, or they could mean this test's
        scanner never finds one. The same scan over a lane sized stripe pattern
        has to count bars, and plenty of them.
        """
        stripes = np.zeros((report_module.LANE_HEIGHT_PX, report_module.LANE_WIDTH_PX, 3),
                           dtype=np.uint8)
        for x in range(report_module.LANE_WIDTH_PX):
            light = (x // 20) % 2 == 0
            stripes[:, x] = report_module._rgb(
                report_module.TEXT if light else report_module.INK
            )
        assert bars_in(stripes) > 2 * (MAX_BLOCKS_PER_LANE + 1), (
            "the bar scanner cannot find a stripe pattern, so it cannot say anything about "
            "a lane either"
        )

    def test_the_page_prints_the_step_it_measured(self, built: ReportDocument):
        """The number on the page is computed, never typed."""
        assert f"{widest_lane_step_nits():.2f} cd/m2" in built.html
        assert f"{bar_difference_nits():.0f} cd/m2 difference" in built.html

    def test_the_key_shows_the_colours_the_lane_actually_draws(self, built: ReportDocument):
        """A key that named other colours would be a lie about the picture."""
        for colour in (
            report_module.LANE_GROUND,
            report_module.LANE_GENERAL,
            report_module.LANE_RED,
        ):
            assert f"background:{colour}" in built.html, f"the key does not show {colour}"

    def test_no_block_ever_reaches_the_edge_of_the_lane(self):
        """The readability half of the same decision.

        A red block is drawn in the page's own ground colour, so a block that
        ran to the top and bottom of the lane would join the page behind it and
        read as a hole rather than as a mark. It was drawn that way first, and
        on a worst case page forty spans joined into five wide red blocks looked
        like the page with a few black notches in it.
        """
        lane = render_lane(plan_blocks([Span(0, 10_000, "red")], 10_000.0))
        track = np.array(report_module._rgb(report_module.LANE_GROUND), dtype=np.uint8)
        assert (lane[0] == track).all(), "a block runs to the top edge of the lane"
        assert (lane[-1] == track).all(), "a block runs to the bottom edge of the lane"

    def test_the_bright_fills_are_gone_from_the_drawing(self):
        """Saffron may still be an edge on the page. It may not be in a picture."""
        gone = {
            report_module._rgb(report_module.FOCUS_RING),
            report_module._rgb(report_module.ACCENT_DARK),
            report_module._rgb(report_module.BORDER),
            report_module._rgb(report_module.TEXT),
        }
        plan = plan_blocks([Span(1_000, 2_000), Span(5_000, 6_000, "red")], 10_000.0)
        used = {
            tuple(int(v) for v in colour)
            for colour in np.unique(render_lane(plan).reshape(-1, 3), axis=0)
        }
        assert not (used & gone), f"a lane still holds a bright fill: {used & gone}"


# ---------------------------------------------------------------------------
# Every picture passes flashmap
# ---------------------------------------------------------------------------

WIDTH, HEIGHT, FPS = 640, 360, 24
HOLD_SECONDS = 2
# CALM_COLORS.BACKGROUND, used only to pad a lane out to the frame. Nothing is
# cut against it.
PAD = report_module.BACKGROUND


def check_still(image: Path, profile: str = "wcag") -> tuple[bool, str]:
    """Analyse one image on its own, held two seconds, exactly as a still.

    The same shape as eval/brand_assets_check.py's check_one, and for the same
    reason: this is the honest question to ask of a picture that ships.

    Both profiles are run over every picture, because they answer different
    questions. ``wcag`` is the flash rule, and a still cannot flash, so on its
    own it passes any static picture, a full frame stripe pattern included.
    ``broadcast`` carries the regular pattern criterion from BT.1702-3, which
    is the rule a drawn timeline could actually break. Two negative controls
    below show each one refusing something.
    """
    with tempfile.TemporaryDirectory() as work:
        video = Path(work) / "still.mkv"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                # No -loop: an animated file has to play its own frames, or
                # this would freeze the first one and miss what it looks for.
                "-t", str(HOLD_SECONDS), "-i", str(image),
                "-vf",
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color={PAD},"
                f"setsar=1,fps={FPS},format=rgb24",
                "-c:v", "ffv1",  # lossless, so the analyzer sees the pixels we drew
                str(video),
            ],
            check=True,
        )
        result = subprocess.run(
            [sys.executable, "-m", "flashmap", "check", str(video), "--profile", profile],
            capture_output=True,
            text=True,
        )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def a_stripe_pattern(pairs: int = 40) -> bytes:
    """A full frame stripe pattern: the hazard a drawn timeline could become."""
    stripes = np.zeros((360, 640, 3), dtype=np.uint8)
    half = max(1, 640 // (pairs * 2))
    for x in range(640):
        light = (x // half) % 2 == 0
        stripes[:, x] = (243, 232, 211) if light else (23, 59, 71)
    return encode_png(stripes)


@needs_ffmpeg
class TestEveryPictureInTheReportPassesFlashmap:
    def test_the_html_holds_no_picture_the_inventory_missed(self, built: ReportDocument):
        """Nothing can ship in the report without being checked.

        The check below runs over ``document.images``. If the page could hold a
        picture that is not in there, the check would pass while covering less
        than the page, which reads exactly like a check that works.
        """
        in_page = {
            base64.b64decode(value)
            for value in re.findall(r"src='data:image/png;base64,([^']+)'", built.html)
        }
        assert in_page, "no picture was found in the page"
        assert in_page == set(built.images.values()), (
            "the page holds a picture the image check never looks at"
        )
        assert "data:image/" not in built.html.replace("data:image/png;base64,", ""), (
            "there is an embedded image that is not one of the PNGs checked here"
        )

    @pytest.mark.parametrize("profile", ["wcag", "broadcast"])
    def test_every_picture_passes(self, built: ReportDocument, tmp_path: Path, profile: str):
        failed = []
        for name, png in sorted(built.images.items()):
            path = tmp_path / f"{name}.png"
            path.write_bytes(png)
            passed, output = check_still(path, profile)
            if not passed:
                failed.append((name, output))
        assert not failed, (
            f"pictures in the report are over the {profile} thresholds: {failed}"
        )

    def test_a_worst_case_title_still_draws_a_picture_that_passes(self, tmp_path: Path):
        """Not the easy title: the one with a flash every few seconds.

        A report made from a calm map draws four almost empty lanes, and
        checking those would prove very little. This is the shape that would
        break if the drawing limits ever came off: two hundred spans across the
        film, which without the limits is two hundred bright bars.
        """
        document = a_map(
            [a_segment(i * 140.0, i * 140.0 + 60.0, "red" if i % 3 else "general")
             for i in range(200)],
            duration_ms=30_000.0,
        )
        built = build_report({"wcag": document}, title="Worst case", primary="wcag")
        for name, png in sorted(built.images.items()):
            path = tmp_path / f"{name}.png"
            path.write_bytes(png)
            for profile in ("wcag", "broadcast"):
                passed, output = check_still(path, profile)
                assert passed, f"{name} is over the {profile} thresholds: {output}"

    def test_the_check_says_no_to_something_that_really_flashes(self, tmp_path: Path):
        """Negative control one: the flash rule is live.

        Without this the passing runs above say nothing: they could mean the
        lanes are calm, or they could mean the check cannot tell the
        difference. This builds a full frame black to white alternation at
        10 Hz, which is five flashes a second against a limit of three, and
        asserts the check refuses it. The file is analysed and deleted here and
        never opened.
        """
        flashing = tmp_path / "HAZARD_report_negative_control.apng"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=320x180:r=20:d=2",
                # Frame number drives the luminance, so it swings between 16
                # and 235 every two frames at 20 fps: a 10 Hz alternation.
                "-vf", "geq=lum='if(eq(mod(floor(N/2),2),0),16,235)':cb=128:cr=128",
                "-plays", "0",
                str(flashing),
            ],
            check=True,
        )
        try:
            passed, output = check_still(flashing, "wcag")
        finally:
            flashing.unlink(missing_ok=True)

        assert not passed, (
            "the report's picture check passed a file alternating black and white five "
            "times a second, so it would pass anything"
        )
        assert "over the thresholds" in output

    def test_the_check_says_no_to_a_stripe_pattern(self, tmp_path: Path):
        """Negative control two: the pattern rule is live, and wcag is not it.

        A still cannot flash, so the flash rule alone would pass any drawing
        this module could make, and the passing runs above would be a check
        that cannot fail. This is the hazard a drawn timeline could actually
        become: a full frame of forty light and dark pairs. The broadcast
        profile refuses it. The WCAG profile passes it, which is not a bug in
        the analyzer, it is why both profiles are run over every picture.
        """
        striped = tmp_path / "stripes.png"
        striped.write_bytes(a_stripe_pattern(40))

        passed_wcag, _ = check_still(striped, "wcag")
        assert passed_wcag, (
            "the WCAG profile is expected to pass a still, because a still cannot flash. "
            "If this ever fails, the pattern check below is no longer the only thing "
            "covering a drawn timeline and this comment is wrong."
        )

        passed, output = check_still(striped, "broadcast")
        assert not passed, (
            "the report's picture check passed a full frame stripe pattern, so it says "
            "nothing about the one hazard a drawn timeline could hold"
        )
        assert "FAIL" in output

    def test_where_the_picture_check_stops_and_the_block_cap_takes_over(self, tmp_path: Path):
        """What the image check does not cover, written down rather than assumed.

        The same stripe pattern drawn at the size of a lane, padded out to the
        analysis frame the way every picture here is, passes the broadcast
        profile. It is the same stripes: what changed is that a 1200 by 48 lane
        fills about a fourteenth of the frame, and the pattern criterion has an
        area limit the stripes no longer reach.

        So the image check is not what keeps the timeline safe. It is worth
        running, it catches a picture that decodes to something other than what
        was drawn, and its negative controls are real. But the thing that stops
        a busy title becoming a stripe pattern is the block cap, and the tests
        for that are above. Believing otherwise would be the same mistake
        eval/brand_assets_check.py made in the other direction.

        If this ever goes red the analyzer has got stricter, which is good news
        and means this note needs rewriting rather than restoring.
        """
        lane_sized = tmp_path / "lane_stripes.png"
        stripes = np.zeros((48, 1200, 3), dtype=np.uint8)
        for x in range(1200):
            stripes[:, x] = (243, 232, 211) if (x // 15) % 2 == 0 else (23, 59, 71)
        lane_sized.write_bytes(encode_png(stripes))

        passed, _ = check_still(lane_sized, "broadcast")
        assert passed, (
            "a lane sized stripe pattern now fails the picture check. That is stricter "
            "than when this was written, so read the docstring above and rewrite it."
        )


# ---------------------------------------------------------------------------
# The numbers on the page
# ---------------------------------------------------------------------------


class TestTheCoverSchedule:
    def test_the_guard_band_widens_and_the_minimum_grows_at_the_end(self):
        intervals = cover_intervals(
            [Span(10_000, 10_100)], guard_band_ms=500, min_cover_ms=400, duration_ms=30_000
        )
        assert len(intervals) == 1
        assert intervals[0].start_ms == 9_500
        assert intervals[0].end_ms == 10_600

    def test_red_wins_a_merge(self):
        intervals = cover_intervals(
            [Span(1_000, 2_000, "red"), Span(2_100, 3_000)],
            guard_band_ms=500,
            min_cover_ms=400,
            duration_ms=30_000,
        )
        assert len(intervals) == 1
        assert intervals[0].reason == "red"

    def test_it_agrees_with_the_pipeline_to_the_millisecond(self):
        """The drift guard.

        pipeline/hideplan.py owns this rule and the app has a third copy of it
        in coverSchedule.ts. A fourth that quietly disagreed would put a number
        on the report that the player does not do.
        """
        sys.path.insert(0, str(REPO))
        try:
            from pipeline.flashmap_adapter import MapSegment
            from pipeline.hideplan import (
                DEFAULT_GUARD_BAND_MS,
                DEFAULT_MIN_COVER_MS,
                build_cover_intervals,
            )
        except ImportError:  # flashmap installed on its own, without the repo
            pytest.skip("the pipeline is not importable here")

        assert PRESETS[0].guard_band_ms == DEFAULT_GUARD_BAND_MS
        assert PRESETS[0].min_cover_ms == DEFAULT_MIN_COVER_MS

        cases = [
            [(1_000.0, 2_000.0, "general")],
            [(1_000.0, 1_050.0, "general"), (1_400.0, 1_450.0, "red")],
            [(0.0, 100.0, "general"), (29_900.0, 30_000.0, "red")],
            [(5_000.0, 6_000.0, "red"), (6_500.0, 7_000.0, "general")],
            [(100.0, 200.0, "general"), (100.0, 200.0, "general")],
        ]
        for case in cases:
            mine = cover_intervals(
                [Span(*row) for row in case],
                guard_band_ms=DEFAULT_GUARD_BAND_MS,
                min_cover_ms=DEFAULT_MIN_COVER_MS,
                duration_ms=30_000.0,
            )
            theirs = build_cover_intervals(
                [MapSegment(*row) for row in case],
                guard_band_ms=DEFAULT_GUARD_BAND_MS,
                min_cover_ms=DEFAULT_MIN_COVER_MS,
                duration_ms=30_000.0,
            )
            assert [(s.start_ms, s.end_ms, s.reason) for s in mine] == [
                (i.start_ms, i.end_ms, i.reason) for i in theirs
            ], f"the report and the pipeline disagree on {case}"


class TestThePalette:
    def test_it_is_the_app_palette(self):
        """The colours here are the app's. A drift guard, not a copy."""
        styles = REPO / "app/src/calmframes/calmStyles.ts"
        if not styles.is_file():
            pytest.skip("the app is not in this checkout")
        text = styles.read_text(encoding="utf-8")
        for name, value in (
            ("BACKGROUND", report_module.BACKGROUND),
            ("SURFACE", report_module.SURFACE),
            ("BORDER", report_module.BORDER),
            ("FOCUS_RING", report_module.FOCUS_RING),
            ("ACCENT_DARK", report_module.ACCENT_DARK),
            ("TEXT", report_module.TEXT),
            ("INK", report_module.INK),
            ("COVER", report_module.COVER),
        ):
            assert f"{name}: '{value}'" in text, (
                f"{name} in flashmap/report.py is {value}, which is not what "
                "app/src/calmframes/calmStyles.ts says"
            )

    def test_every_lane_colour_is_one_of_the_app_colours(self):
        """The lane fills are dim, and they are still the app's own colours.

        Picking a new hex because it measured well would leave the report
        looking like something else. These three are CALM_COLORS entries and the
        test above holds each of them to the app's file.
        """
        palette = {
            report_module.BACKGROUND,
            report_module.SURFACE,
            report_module.BORDER,
            report_module.FOCUS_RING,
            report_module.ACCENT_DARK,
            report_module.TEXT,
            report_module.TEXT_DIM,
            report_module.INK,
            report_module.COVER,
        }
        for colour in (
            report_module.LANE_GROUND,
            report_module.LANE_GENERAL,
            report_module.LANE_RED,
        ):
            assert colour in palette, f"{colour} is not one of the app's colours"

    def test_saffron_is_only_ever_a_fill(self, built: ReportDocument):
        """4.47:1 on teal, which misses the 4.5:1 text floor by 0.03.

        So it may be a bar and a border and it may never be a colour text is
        drawn in.
        """
        for match in re.finditer(r"color:\s*([^;'\"]+)", built.html, re.I):
            assert report_module.FOCUS_RING.lower() not in match.group(1).lower()
            assert report_module.ACCENT_DARK.lower() not in match.group(1).lower()


class TestThePage:
    def test_it_holds_the_four_things_it_promises(self, built: ReportDocument):
        for heading in ("Timeline", "Hidden segments", "Presets", "License and credit", "Hashes"):
            assert f">{heading}</h2>" in built.html, f"the report has no {heading} section"

    def test_every_preset_is_on_the_page(self, built: ReportDocument):
        for preset in PRESETS:
            assert preset.title in built.html
            assert preset.description in built.html

    def test_the_hashes_are_there(self, built: ReportDocument):
        assert "a" * 64 in built.html, "the source hash is not on the page"
        assert "Picture SHA-256" in built.html

    def test_a_missing_license_is_said_and_not_guessed(self, built: ReportDocument):
        assert "No license line was supplied" in built.html

    def test_a_preset_that_was_not_measured_is_a_lower_bound(self, built: ReportDocument):
        """Only the wcag map was supplied, so Broadcast cannot be complete.

        Nothing mocked is shown as real. A preset whose maps are not all here
        is a number the report cannot stand behind, so the row has to say which
        map is missing and that the figure is a floor. The whole phrase is
        asserted: "lower bound" on its own also appears on the lane label, so
        matching that alone would pass a row that claimed to be complete.
        """
        assert (
            "lower bound: no broadcast map was supplied, so this preset would hide at "
            "least this much and possibly more"
        ) in built.html

    def test_a_stricter_preset_never_hides_less(self):
        """The page says a household setting can only make this stricter.

        That is a claim, so it is measured. Interval counts alone do not show
        it and can mislead: on a real title Extra cautious came out with 24
        intervals against Broadcast's 43, because a wider guard band merges
        more of them. What must never go down is the time hidden.
        """
        both = {
            "wcag": a_map([a_segment(i * 3_000.0, i * 3_000.0 + 400.0) for i in range(8)]),
            "broadcast": a_map(
                [a_segment(i * 3_000.0 + 1_200.0, i * 3_000.0 + 1_600.0) for i in range(8)]
            ),
        }
        both["broadcast"]["profile"]["name"] = "broadcast"
        spans = {name: report_module.spans_from_map(doc) for name, doc in both.items()}

        hidden = []
        for preset in PRESETS:
            union = [span for name in preset.map_profiles for span in spans[name]]
            intervals = cover_intervals(
                union,
                guard_band_ms=preset.guard_band_ms,
                min_cover_ms=preset.min_cover_ms,
                duration_ms=30_000.0,
            )
            hidden.append((preset.title, sum(i.duration_ms for i in intervals)))

        for (softer, less), (stricter, more) in zip(hidden, hidden[1:]):
            assert more >= less, (
                f"{stricter} hides {more} ms and {softer} hides {less} ms, so the page's "
                "claim that a preset can only make this stricter is false"
            )

    def test_a_preset_whose_maps_are_all_here_is_not_hedged(self):
        """The other side of it: a measured row must not read as a guess."""
        both = {"wcag": a_map([a_segment(1_000, 2_000)]), "broadcast": a_map([])}
        both["broadcast"]["profile"]["name"] = "broadcast"
        page = build_report(both, title="Both", primary="wcag").html
        assert "no broadcast map was supplied" not in page

    def test_a_map_with_no_duration_is_refused(self):
        document = a_map([a_segment(1_000, 2_000)])
        document["source"]["duration_ms"] = None
        with pytest.raises(ValueError, match="duration_ms"):
            build_report({"wcag": document}, title="No duration", primary="wcag")

    def test_an_unknown_reason_is_read_as_red(self):
        """Fail safe: red is always an opaque cover, never a dimmed one."""
        document = a_map([a_segment(1_000, 2_000, "something new")])
        built = build_report({"wcag": document}, title="Odd", primary="wcag")
        assert "lane-flashes" in built.images
        intervals = cover_intervals(
            [Span(1_000, 2_000, "something new")], guard_band_ms=500, min_cover_ms=400
        )
        assert intervals[0].reason == "red"

    def test_a_calm_title_says_so(self):
        built = build_report({"wcag": a_map([])}, title="Calm", primary="wcag")
        assert "Nothing in this title went over the thresholds." in built.html
        assert "Nothing is hidden in this title." in built.html


class TestTheCommandLine:
    def test_report_is_a_subcommand(self):
        args = build_parser().parse_args(["report", "map.json", "--out", "r.html"])
        assert args.command == "report"
        assert args.out == "r.html"

    def test_it_writes_a_file(self, tmp_path: Path, capsys):
        map_path = tmp_path / "map.json"
        map_path.write_text(json.dumps(a_map([a_segment(1_000, 2_000)])), encoding="utf-8")
        out = tmp_path / "report.html"
        assert main(["report", str(map_path), "--out", str(out)]) == 0
        page = out.read_text(encoding="utf-8")
        assert page.startswith("<!doctype html>")
        assert "data:image/png;base64," in page

    def test_a_license_csv_lands_on_the_page(self, tmp_path: Path):
        csv_path = tmp_path / "LICENSES.csv"
        csv_path.write_text(
            "file,source_page_url,license,credit_line,sha256,license_checked_on,notes\n"
            f"HAZARD_example.mp4,https://example.invalid/about,CC BY 3.0,Somebody,{'a' * 64},"
            "2026-09-17,none\n",
            encoding="utf-8",
        )
        map_path = tmp_path / "map.json"
        map_path.write_text(json.dumps(a_map([a_segment(1_000, 2_000)])), encoding="utf-8")
        out = tmp_path / "report.html"
        assert (
            main(
                ["report", str(map_path), "--out", str(out), "--license-csv", str(csv_path)]
            )
            == 0
        )
        page = out.read_text(encoding="utf-8")
        assert "CC BY 3.0" in page
        assert "No license line was supplied" not in page

    def test_a_map_named_for_the_wrong_profile_is_refused(self, tmp_path: Path):
        map_path = tmp_path / "map.json"
        map_path.write_text(json.dumps(a_map([a_segment(1_000, 2_000)])), encoding="utf-8")
        out = tmp_path / "report.html"
        with pytest.raises(SystemExit, match="measured against"):
            main(
                [
                    "report", str(map_path), "--out", str(out),
                    "--map", f"broadcast={map_path}",
                ]
            )

    def test_a_map_is_told_from_a_video(self, tmp_path: Path):
        map_path = tmp_path / "map.json"
        map_path.write_text(json.dumps(a_map([])), encoding="utf-8")
        assert looks_like_a_map(map_path)

        not_json = tmp_path / "clip.mp4"
        not_json.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\xff" * 64)
        assert not looks_like_a_map(not_json)

        other_json = tmp_path / "other.json"
        other_json.write_text('{"hello": 1}', encoding="utf-8")
        assert not looks_like_a_map(other_json)


class TestThePngWriter:
    def test_it_round_trips(self):
        pixels = np.zeros((3, 4, 3), dtype=np.uint8)
        pixels[1, 2] = (17, 34, 51)
        png = encode_png(pixels)
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        assert encode_png(pixels) == png, "the same array has to give the same bytes"

    def test_it_refuses_the_wrong_shape(self):
        with pytest.raises(ValueError):
            encode_png(np.zeros((2, 2), dtype=np.uint8))
        with pytest.raises(ValueError):
            encode_png(np.zeros((2, 2, 3), dtype=np.float32))
