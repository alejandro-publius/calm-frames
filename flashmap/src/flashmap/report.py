"""One self-contained HTML report for one title.

    python -m flashmap report VIDEO_OR_MAP --out report.html

Self-contained means one file. It opens with the network off, it has no
sibling assets, the CSS is inline and every picture is a PNG this module drew,
embedded as a data URI. Nothing in it is fetched.

What it holds: the flash timeline, the hidden segments, the presets, the
licence line and the hashes.

Two rules run through the whole file.

**No frame of flagged content, ever.** The report describes a hazard, it never
shows one. There is no poster, no thumbnail and no still from the film
anywhere in it, and the report says so in its own text. The only pictures are
the timeline lanes this module draws out of numbers, and the lanes carry no
frame data at all.

**The timeline must not itself be a hazard.** A title with two hundred short
segments drawn one thin bright bar each is a fine high contrast stripe
pattern, which is a photosensitive hazard of a different kind than the one
this project measures. So the drawing has three limits:

- nothing narrower than ``MIN_BLOCK_PX`` is drawn, and no two blocks sit closer
  than ``MIN_GAP_PX``: blocks that would fall closer are drawn as one. Both are
  ours, chosen so no bar is a hairline on a television across a room;
- a lane draws at most ``MAX_BLOCKS_PER_LANE`` blocks, and past that the
  closest neighbours are joined until it holds no more. That one is not ours:
  it is the regular pattern criterion the broadcast profile measures, more
  than five light and dark pairs, so a lane cannot reach the criterion however
  many spans a title has;
- every bar is drawn below the luminance difference that makes a light and
  dark pair at all, so a bar boundary is never a bar boundary. The three
  colours a lane may hold are ``LANE_GROUND``, ``LANE_GENERAL`` and
  ``LANE_RED``, and the arithmetic that picked them is beside them below.

The third is there because the second is one number away from being wrong.
The cap is the whole of the argument today: raise it by one and a lane can
show six pairs. A bar that cannot reach the bar to bar difference cannot be
counted as a bar however many of them there are, so the two limits fail in
different directions and neither has to be right on its own.

The first two make the picture say less than the numbers do, so both are named
on the page next to the lane they changed, and the tables underneath carry the
exact milliseconds. The picture is a picture. The table is the truth.

The palette is the app's own, from app/src/calmframes/calmStyles.ts. Saffron is
an edge here and never a label, because it is 4.47:1 on the teal ground and the
text floor is 4.5:1. It is not a lane fill any more: at 82 cd/m2 on a 4 cd/m2
ground it was 78 cd/m2 of step, which is four times a flash difference.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from numpy.typing import NDArray

from . import __version__
from .color import LUMA_B, LUMA_G, LUMA_R, bt1886_nits
from .pngout import encode_png

__all__ = [
    "PRESETS",
    "Preset",
    "Span",
    "ReportDocument",
    "bar_difference_nits",
    "build_report",
    "cover_intervals",
    "lane_nits",
    "plan_blocks",
    "render_lane_png",
    "widest_lane_step_nits",
    "write_report",
]

# ---------------------------------------------------------------------------
# Palette. The five brand colours and their rules are in
# app/src/calmframes/calmStyles.ts; flashmap/tests/test_report.py reads that
# file and fails if these drift from it.
# ---------------------------------------------------------------------------

BACKGROUND = "#102F3A"  # teal ground, every Calm Frames screen sits on it
SURFACE = "#1A414B"  # a card on the ground
BORDER = "#66A0B4"
FOCUS_RING = "#E6A957"  # saffron: rings and edges only, never a label
ACCENT_DARK = "#B87A2C"  # dark saffron: edges only, carries nothing
TEXT = "#F3E8D3"  # cream on teal
TEXT_DIM = "#BDD0CF"
INK = "#17323C"  # text on a light surface
COVER = "#000000"  # the cover itself, and the lane's own track

# ---------------------------------------------------------------------------
# Drawing limits. Ours, not a spec's. See the module docstring.
# ---------------------------------------------------------------------------

LANE_WIDTH_PX = 1200
LANE_HEIGHT_PX = 48

# Ours: nothing thinner than this is drawn, and nothing sits closer than this
# to its neighbour. A hairline on a television across a room is not readable
# anyway, and a hairline beside a hairline is the start of a pattern.
MIN_BLOCK_PX = 8
MIN_GAP_PX = 8

# Not ours. PROFILES["broadcast"].pattern is the regular pattern criterion from
# ITU-R BT.1702-3 Attachment 1 to Annex 1, quoted in docs/SPEC_SOURCES.md
# section 8: more than five light and dark pairs. A lane that draws at most
# five blocks presents at most five pairs, so it cannot reach the criterion
# whatever the area, and the count never has to be argued from area.
#
# flashmap/tests/test_report.py reads the number off that profile rather than
# trusting this line, and runs every picture in the report through the
# broadcast profile, which is the one that measures patterns. The WCAG profile
# passes a full frame forty pair stripe pattern, because a still cannot flash
# and WCAG 2.2 SC 2.3.1 has no pattern rule at all.
MAX_BLOCKS_PER_LANE = 5

# Not ours either, and the reason the cap above is not the only thing holding
# the line. A bar is only a bar when the step to it reaches the Guideline 1
# flash difference: for SDR that is 20 cd/m2 with the darker state below
# 160 cd/m2 (docs/SPEC_SOURCES.md section 5, which section 8 reuses because the
# attachment gives the bar to bar condition no number of its own). Every colour
# a lane may hold is picked so the widest step inside it is well under that
# difference. pattern.scan_bars then counts no boundary anywhere in a lane, so
# no number of blocks can make a light and dark pair, cap or no cap.
#
# The arithmetic, through color.bt1886_nits, the curve the broadcast profile
# measures with: nits = peak * V ** 2.4, with V the luma signal normalised black
# 0 to white 1 and peak the profile's own 200 cd/m2 assumed SDR white. V here is
# the BT.709 luma of the sRGB bytes, (0.2126 R + 0.7152 G + 0.0722 B) / 255,
# which is what the decoder hands back for a picture 720 lines or taller:
#
# Approved October 10 palette, measured with lane_nits below:
#   LANE_GROUND   #000000    0.00 cd/m2
#   LANE_GENERAL  #1A414B    5.59 cd/m2
#   LANE_RED      #102F3A    2.52 cd/m2
# The maximum step is 5.59 cd/m2, leaving 14.41 cd/m2 below the unchanged
# 20 cd/m2 difference. The half-threshold margin, block cap and scanner
# tests remain unchanged; the explicit palette pin records the new measurement.
LANE_GROUND = COVER
LANE_GENERAL = SURFACE
LANE_RED = BACKGROUND

# A general block is drawn short and a red block full height, so the two are
# told apart by shape and not by colour alone.
GENERAL_BLOCK_INSET_PX = 9

# A hairline of track above and below every block, so no block ever runs to the
# edge of the lane. A red block is drawn in the page's own ground colour, and one
# that reached the lane's edge would join the page behind it and read as a hole
# rather than as a mark. This was found on a real drawing: forty spans joined
# into five wide red blocks left a lane that looked like the page with a few
# black notches in it.
BLOCK_EDGE_PX = 1

RED = "red"
GENERAL = "general"

# The same exit codes cli.py uses. They are repeated rather than imported
# because cli.py imports this module, and a circular import would break the
# command line for everyone.
EXIT_OK = 0
EXIT_ERROR = 2


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Preset:
    """One household preset, as the app applies it.

    Copied from ``PRESETS`` in app/src/calmframes/household.ts. A preset never
    replaces the map: it names the maps whose segments are unioned, and it can
    only widen what is hidden.
    """

    name: str
    title: str
    description: str
    map_profiles: tuple[str, ...]
    guard_band_ms: float
    min_cover_ms: float


# The guard band and minimum cover defaults are the twin of
# DEFAULT_GUARD_BAND_MS and DEFAULT_MIN_COVER_MS in pipeline/hideplan.py, which
# is itself the twin of app/src/calmframes/coverSchedule.ts. Three copies is
# two too many, so flashmap/tests/test_report.py parses the pipeline file and
# fails if these two numbers drift from it.
DEFAULT_GUARD_BAND_MS = 500.0
DEFAULT_MIN_COVER_MS = 400.0

PRESETS: tuple[Preset, ...] = (
    Preset(
        name="wcag",
        title="Standard",
        description=(
            "Hides what goes over the WCAG 2.3.1 flash thresholds. This is the floor. "
            "Nothing can go below it."
        ),
        map_profiles=("wcag",),
        guard_band_ms=DEFAULT_GUARD_BAND_MS,
        min_cover_ms=DEFAULT_MIN_COVER_MS,
    ),
    Preset(
        name="broadcast",
        title="Broadcast",
        description=(
            "Everything Standard hides, plus what goes over the broadcast rules for a "
            "bright television."
        ),
        map_profiles=("wcag", "broadcast"),
        guard_band_ms=DEFAULT_GUARD_BAND_MS,
        min_cover_ms=DEFAULT_MIN_COVER_MS,
    ),
    Preset(
        name="extra-cautious",
        title="Extra cautious",
        description=(
            "Everything Broadcast hides, and the picture goes dark a little earlier and "
            "comes back a little later."
        ),
        map_profiles=("wcag", "broadcast"),
        guard_band_ms=1000.0,
        min_cover_ms=800.0,
    ),
)


# ---------------------------------------------------------------------------
# Spans and the cover schedule
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Span:
    start_ms: float
    end_ms: float
    reason: str = GENERAL

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms


def _reason_of(raw: Any) -> str:
    """Anything that is not plainly "general" is treated as red.

    The same fail-safe reading pipeline/flashmap_adapter.py uses: red is the
    strictest handling, so an unknown reason string is never softened into one
    the report would draw as dimmable.
    """
    return GENERAL if str(raw).strip().lower() == GENERAL else RED


def spans_from_map(document: dict[str, Any]) -> list[Span]:
    segments = document.get("segments")
    if not isinstance(segments, list):
        raise ValueError("this map has no segment list, so it cannot be reported on")
    spans: list[Span] = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"segment {index} is not an object")
        try:
            start = float(segment["start_ms"])
            end = float(segment["end_ms"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"segment {index} has no usable times: {exc}") from exc
        spans.append(Span(start, end, _reason_of(segment.get("reason"))))
    return spans


def cover_intervals(
    spans: Iterable[Span],
    *,
    guard_band_ms: float,
    min_cover_ms: float,
    duration_ms: float | None = None,
) -> list[Span]:
    """Flash segments in, cover intervals out.

    The rules are pipeline/hideplan.py's, kept to the millisecond: widen by the
    guard band on both sides, grow to the minimum cover at the end first, clamp
    to the film, merge what overlaps or touches, and let red win any merge.
    flashmap/tests/test_report.py checks this against the pipeline's own
    implementation on the same inputs, so the two cannot drift apart quietly.
    """
    widened: list[Span] = []
    for span in spans:
        if span.end_ms <= span.start_ms:
            continue
        start_ms = span.start_ms - guard_band_ms
        end_ms = span.end_ms + guard_band_ms
        if end_ms - start_ms < min_cover_ms:
            end_ms = start_ms + min_cover_ms
        if start_ms < 0:
            start_ms = 0.0
        if duration_ms is not None and end_ms > duration_ms:
            end_ms = duration_ms
        if end_ms <= start_ms:
            continue
        # Normalised here as well as at parse time, so calling this directly
        # with a reason string nobody has cleaned is still fail safe. The
        # pipeline reads an unknown reason as red before its schedule ever sees
        # it, and softening one to general here would turn an interval that
        # must be opaque into one a household may dim.
        widened.append(Span(start_ms, end_ms, _reason_of(span.reason)))

    widened.sort(key=lambda span: (span.start_ms, span.end_ms))

    merged: list[Span] = []
    for span in widened:
        if merged and span.start_ms <= merged[-1].end_ms:
            previous = merged[-1]
            merged[-1] = Span(
                previous.start_ms,
                max(previous.end_ms, span.end_ms),
                RED if RED in (previous.reason, span.reason) else GENERAL,
            )
            continue
        merged.append(span)
    return merged


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------


@dataclass
class Block:
    """One rectangle in a lane, in pixels."""

    left: int
    right: int
    reason: str

    @property
    def width(self) -> int:
        return self.right - self.left


@dataclass
class LanePlan:
    blocks: list[Block]
    span_count: int
    widened: int
    joined: int
    collapsed: bool

    @property
    def notes(self) -> list[str]:
        """What the picture does not say, in words, for the page to print."""
        lines: list[str] = []
        if self.collapsed:
            lines.append(
                f"{self.span_count} spans are drawn as {len(self.blocks)} block(s). "
                "Neighbours were joined, closest first, until the lane held no more "
                f"than {MAX_BLOCKS_PER_LANE}: more bright bars than that is a striped "
                "pattern, and this report does not draw one. A block therefore covers "
                "calm time as well as flagged time. The table below has every span."
            )
            return lines
        if self.widened:
            lines.append(
                f"{self.widened} block(s) are drawn wider than the time they cover, "
                f"because nothing narrower than {MIN_BLOCK_PX} pixels is drawn."
            )
        if self.joined:
            lines.append(
                f"{self.joined} pair(s) of neighbouring spans are drawn as one block, "
                f"because a gap under {MIN_GAP_PX} pixels would read as a stripe."
            )
        return lines


def plan_blocks(
    spans: Sequence[Span], duration_ms: float, width_px: int = LANE_WIDTH_PX
) -> LanePlan:
    """Turn spans into the rectangles a lane draws, under the two limits.

    Both limits make the drawing coarser than the numbers, never finer, so a
    span can be drawn wider than it is but never narrower or missing.
    """
    if duration_ms <= 0:
        return LanePlan([], len(spans), 0, 0, False)

    ordered = sorted(spans, key=lambda span: (span.start_ms, span.end_ms))
    scale = width_px / duration_ms

    raw: list[Block] = []
    widened = 0
    for span in ordered:
        left = int(np.floor(max(0.0, span.start_ms) * scale))
        right = int(np.ceil(min(duration_ms, span.end_ms) * scale))
        if right - left < MIN_BLOCK_PX:
            widened += 1
            # Grow around the middle, then push back inside the lane.
            middle = (left + right) / 2.0
            left = int(round(middle - MIN_BLOCK_PX / 2.0))
            right = left + MIN_BLOCK_PX
        if left < 0:
            left, right = 0, MIN_BLOCK_PX
        if right > width_px:
            right, left = width_px, max(0, width_px - MIN_BLOCK_PX)
        raw.append(Block(left, right, span.reason))

    joined = 0
    blocks: list[Block] = []
    for block in raw:
        if blocks and block.left - blocks[-1].right < MIN_GAP_PX:
            joined += 1
            previous = blocks[-1]
            previous.right = max(previous.right, block.right)
            if block.reason == RED:
                previous.reason = RED
            continue
        blocks.append(block)

    if len(blocks) > MAX_BLOCKS_PER_LANE:
        # Join the closest pair of neighbours, over and over, until the lane
        # holds no more than the cap. Collapsing everything into one block from
        # first to last would also be safe and would say almost nothing: a real
        # title with fifty spans drew a single bar across the whole film. This
        # keeps the bars where the flashes actually are, at the cost of each
        # bar covering some calm time as well, which the note says out loud.
        while len(blocks) > MAX_BLOCKS_PER_LANE:
            gaps = [blocks[i + 1].left - blocks[i].right for i in range(len(blocks) - 1)]
            closest = gaps.index(min(gaps))
            first, second = blocks[closest], blocks[closest + 1]
            merged_block = Block(
                first.left,
                max(first.right, second.right),
                RED if RED in (first.reason, second.reason) else GENERAL,
            )
            blocks[closest : closest + 2] = [merged_block]
        return LanePlan(blocks, len(ordered), widened, joined, True)

    return LanePlan(blocks, len(ordered), widened, joined, False)


def _rgb(colour: str) -> tuple[int, int, int]:
    value = colour.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def lane_nits(colour: str) -> float:
    """Screen luminance of one lane colour, through the profile's own curve.

    The peak white and the curve are read off the broadcast profile rather than
    written here, so this cannot drift from what the analyzer measures with. The
    luma weights are color.LUMA_*, quoted in docs/SPEC_SOURCES.md section 3.
    """
    from .profiles import PROFILES

    peak = PROFILES["broadcast"].peak_nits
    if peak is None:  # pragma: no cover - the broadcast profile carries one
        raise ValueError("the broadcast profile no longer has a peak white to measure with")
    red, green, blue = _rgb(colour)
    level = (LUMA_R * red + LUMA_G * green + LUMA_B * blue) / 255.0
    return float(bt1886_nits(np.array([level], dtype=np.float32), peak).item())


def widest_lane_step_nits() -> float:
    """The largest luminance step a lane can hold, in cd/m2.

    A lane is three colours and nothing else, so the widest step it can put in
    front of the pattern rule is the spread of those three.
    """
    values = [lane_nits(colour) for colour in (LANE_GROUND, LANE_GENERAL, LANE_RED)]
    return max(values) - min(values)


def bar_difference_nits() -> float:
    """The luminance difference that makes a light and dark pair, in cd/m2.

    Guideline 1's flash difference, which Attachment 1 reuses for the bar to bar
    condition. Read off the broadcast profile, never written down here.
    """
    from .profiles import PROFILES

    return float(PROFILES["broadcast"].general.min_delta)


def render_lane(plan: LanePlan, width_px: int = LANE_WIDTH_PX) -> NDArray[np.uint8]:
    """Draw one lane: a calm band with the flagged blocks on it.

    No text, no tick marks and no hairlines. The page puts the labels and the
    time axis around the picture in HTML, where they are real text a screen
    reader can read and a television can scale.
    """
    lane = np.zeros((LANE_HEIGHT_PX, width_px, 3), dtype=np.uint8)
    lane[:, :] = _rgb(LANE_GROUND)
    for block in plan.blocks:
        left = max(0, min(width_px, block.left))
        right = max(0, min(width_px, block.right))
        if right <= left:
            continue
        if block.reason == RED:
            inset = BLOCK_EDGE_PX
            lane[inset : LANE_HEIGHT_PX - inset, left:right] = _rgb(LANE_RED)
        else:
            inset = GENERAL_BLOCK_INSET_PX
            lane[inset : LANE_HEIGHT_PX - inset, left:right] = _rgb(LANE_GENERAL)
    return lane


def render_lane_png(plan: LanePlan, width_px: int = LANE_WIDTH_PX) -> bytes:
    return encode_png(render_lane(plan, width_px))


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@dataclass
class ReportDocument:
    """The finished report, and every picture in it.

    ``images`` is the whole inventory: flashmap/tests/test_report.py runs every
    one of them through the analyzer and fails if the HTML holds a picture that
    is not in here.
    """

    html: str
    images: dict[str, bytes] = field(default_factory=dict)


def _ms(value: float) -> str:
    """A time as m:ss.mmm, which is how the tables read a timeline."""
    if value != value:  # NaN
        return "unknown"
    total = max(0.0, value)
    minutes, seconds = divmod(total / 1000.0, 60.0)
    return f"{int(minutes)}:{seconds:06.3f}"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def _license_from_csv(path: Path, source_name: str, sha256: str) -> dict[str, str] | None:
    """Find this file's row in a media/LICENSES.csv, by hash first then by name."""
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except OSError:
        return None
    for row in rows:
        if sha256 and (row.get("sha256") or "").strip().lower() == sha256.lower():
            return row
    for row in rows:
        if source_name and (row.get("file") or "").strip() == source_name:
            return row
    return None


def _table(headings: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    head = "".join(f"<th scope='col'>{_esc(text)}</th>" for text in headings)
    body = "".join(
        "<tr>" + "".join(f"<td>{_esc(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _axis(duration_ms: float, ticks: int = 7) -> str:
    marks = []
    for index in range(ticks):
        at = duration_ms * index / (ticks - 1)
        marks.append(f"<span>{_esc(_ms(at))}</span>")
    return "<div class='axis'>" + "".join(marks) + "</div>"


_STYLE = f"""
:root {{
  --ground: {BACKGROUND};
  --surface: {SURFACE};
  --border: {BORDER};
  --ring: {FOCUS_RING};
  --accent-dark: {ACCENT_DARK};
  --text: {TEXT};
  --text-dim: {TEXT_DIM};
  --ink: {INK};
  --lane-ground: {LANE_GROUND};
  --lane-general: {LANE_GENERAL};
  --lane-red: {LANE_RED};
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  padding: 32px 24px 64px;
  background: var(--ground);
  color: var(--text);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}
main {{ max-width: 1120px; margin: 0 auto; }}
h1 {{ font-size: 30px; margin: 0 0 4px; }}
h2 {{ font-size: 21px; margin: 40px 0 12px; border-bottom: 1px solid var(--border);
      padding-bottom: 6px; }}
h3 {{ font-size: 17px; margin: 24px 0 8px; }}
p, li {{ max-width: 80ch; }}
.sub {{ color: var(--text-dim); margin: 0 0 20px; }}
.callout {{
  background: var(--surface);
  border: 2px solid var(--ring);
  border-radius: 10px;
  padding: 16px 20px;
  margin: 20px 0;
}}
.callout h3 {{ margin-top: 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 8px; }}
th, td {{
  border: 1px solid var(--border);
  padding: 7px 10px;
  text-align: left;
  vertical-align: top;
  font-variant-numeric: tabular-nums;
}}
th {{ background: var(--surface); }}
.lane-row {{ display: grid; grid-template-columns: 220px 1fr; gap: 14px;
             align-items: center; margin: 10px 0; }}
.lane-row .name {{ font-weight: 600; }}
.lane-row .name small {{ display: block; font-weight: 400; color: var(--text-dim); }}
/* The lane's own outline is part of the lane a reader sees, so it is drawn in a
   lane colour and not in the page's border colour. A 55 cd/m2 line around a
   0 cd/m2 track is a 55 cd/m2 step, which is a bar boundary, and
   eval/report_page_check.py found exactly that when this was var(--border). */
.lane-row img {{ width: 100%; height: auto; display: block; border-radius: 4px;
                 border: 1px solid var(--lane-general); }}
.axis {{ display: flex; justify-content: space-between; color: var(--text-dim);
         font-size: 13px; margin-left: 234px; font-variant-numeric: tabular-nums; }}
.key {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 16px 0 4px;
        color: var(--text-dim); font-size: 14px; }}
.key span.swatch {{ display: inline-block; width: 26px; height: 12px;
                    vertical-align: middle; margin-right: 7px; border-radius: 2px; }}
.note {{ color: var(--text-dim); font-size: 14px; margin: 4px 0 0 234px; }}
code, .hash {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
               font-size: 13px; word-break: break-all; }}
footer {{ margin-top: 48px; color: var(--text-dim); font-size: 14px;
          border-top: 1px solid var(--border); padding-top: 16px; }}
@media print {{ body {{ background: #fff; color: var(--ink); }} }}
"""

_NO_FRAMES = (
    "This report never shows a frame of the film. Nothing here is a still, a poster or a "
    "thumbnail, and no flagged moment is reproduced anywhere in this file. The pictures "
    "below are bars drawn from the numbers in the map, and they carry no picture data from "
    "the title at all. A flagged span is described. It is not displayed."
)

_DISCLAIMER = (
    "flashmap reduces exposure to flashing above published limits in the videos it measures. "
    "It is not a medical device."
)


def _lane_row(name: str, sub: str, key: str, plan: LanePlan, images: dict[str, bytes]) -> str:
    png = render_lane_png(plan)
    images[key] = png
    notes = "".join(f"<p class='note'>{_esc(line)}</p>" for line in plan.notes)
    return (
        "<div class='lane-row'>"
        f"<div class='name'>{_esc(name)}<small>{_esc(sub)}</small></div>"
        f"<img alt='{_esc(name)}: {_esc(sub)}' src='{_data_uri(png)}'>"
        "</div>" + notes
    )


def build_report(
    maps: dict[str, dict[str, Any]],
    *,
    title: str,
    primary: str,
    map_files: dict[str, Path] | None = None,
    license_row: dict[str, str] | None = None,
    license_line: str | None = None,
) -> ReportDocument:
    """Build the whole report for one title.

    ``maps`` is profile name to map document. ``primary`` names the one whose
    source, hashes and profile describe the title.
    """
    if primary not in maps:
        raise ValueError(f"no {primary!r} map was given")
    document = maps[primary]
    source = document.get("source") or {}
    profile = document.get("profile") or {}
    summary = document.get("summary") or {}
    map_files = map_files or {}

    duration_ms = source.get("duration_ms")
    if not isinstance(duration_ms, (int, float)) or duration_ms <= 0:
        raise ValueError(
            "this map has no usable source.duration_ms, so a timeline cannot be drawn "
            "against the length of the film"
        )
    duration_ms = float(duration_ms)

    spans = {name: spans_from_map(doc) for name, doc in maps.items()}
    images: dict[str, bytes] = {}
    parts: list[str] = []

    parts.append(f"<h1>{_esc(title)}</h1>")
    parts.append(
        f"<p class='sub'>Flash report. Source file <code>{_esc(source.get('path', 'unknown'))}</code>, "
        f"{_esc(_ms(duration_ms))} long, {_esc(source.get('coded_width', '?'))}"
        f"x{_esc(source.get('coded_height', '?'))}, "
        f"{_esc(source.get('frame_count', '?'))} frames. Measured by flashmap "
        f"{_esc((document.get('generator') or {}).get('version', 'unknown'))} on "
        f"{_esc(document.get('created_utc', 'unknown'))}. Report written by flashmap "
        f"{_esc(__version__)}.</p>"
    )

    parts.append(
        "<div class='callout'><h3>What this report will not do</h3>"
        f"<p>{_esc(_NO_FRAMES)}</p></div>"
    )

    verdict = (
        "Nothing in this title went over the thresholds."
        if summary.get("pass")
        else f"{_esc(summary.get('segment_count', len(spans[primary])))} span(s) went over the "
        f"thresholds: {_esc(summary.get('general_segment_count', 0))} general flash and "
        f"{_esc(summary.get('red_segment_count', 0))} red flash."
    )
    parts.append(f"<h2>Verdict</h2><p>{verdict}</p>")

    # --- timeline ---------------------------------------------------------
    parts.append("<h2>Timeline</h2>")
    parts.append(
        "<p>Left is the start of the film and right is the end. Every lane is the whole "
        "film at the same scale.</p>"
    )
    # Each swatch is a mark on a piece of track, which is what a lane shows: the
    # fill inside, the track colour around it, and a thin light outline so the
    # whole swatch can be found on the page. The fills are dim on purpose (see
    # the arithmetic in this module) and on the teal ground alone two of the
    # three would be all but invisible.
    swatch = f"border:3px solid {LANE_GROUND};outline:1px solid {BORDER}"
    parts.append(
        "<div class='key'>"
        f"<div><span class='swatch' style='background:{LANE_GENERAL};height:6px;{swatch}'>"
        "</span>general flash, drawn short</div>"
        f"<div><span class='swatch' style='background:{LANE_RED};{swatch}'></span>"
        "red flash, drawn tall</div>"
        f"<div><span class='swatch' style='background:{LANE_GROUND};{swatch}'></span>"
        "nothing flagged</div>"
        "</div>"
    )
    parts.append(
        f"<p class='note' style='margin-left:0'>The bars are drawn dim on purpose. The widest "
        f"luminance step a lane can hold is {widest_lane_step_nits():.2f} cd/m2, against the "
        f"{bar_difference_nits():.0f} cd/m2 difference that makes a light and dark pair in "
        "ITU-R BT.1702-3, so no number of bars in a lane can be a regular pattern. That is why "
        "a bar is a quiet mark on a dark track rather than a bright block, and why the tables "
        "below carry every span rather than the picture.</p>"
    )

    primary_plan = plan_blocks(spans[primary], duration_ms)
    parts.append(
        _lane_row(
            "Flashes found",
            f"{primary} map, {len(spans[primary])} span(s)",
            "lane-flashes",
            primary_plan,
            images,
        )
    )

    preset_rows: list[list[object]] = []
    for preset in PRESETS:
        have = [name for name in preset.map_profiles if name in maps]
        missing = [name for name in preset.map_profiles if name not in maps]
        union = [span for name in have for span in spans[name]]
        intervals = cover_intervals(
            union,
            guard_band_ms=preset.guard_band_ms,
            min_cover_ms=preset.min_cover_ms,
            duration_ms=duration_ms,
        )
        hidden_ms = sum(interval.duration_ms for interval in intervals)
        note = (
            "complete"
            if not missing
            else "lower bound: no " + ", ".join(missing) + " map was supplied, so this "
            "preset would hide at least this much and possibly more"
        )
        parts.append(
            _lane_row(
                f"Hidden: {preset.title}",
                f"{len(intervals)} interval(s)" + ("" if not missing else ", lower bound"),
                f"lane-hidden-{preset.name}",
                plan_blocks(intervals, duration_ms),
                images,
            )
        )
        preset_rows.append(
            [
                preset.title,
                preset.name,
                ", ".join(preset.map_profiles),
                f"{preset.guard_band_ms:.0f} ms",
                f"{preset.min_cover_ms:.0f} ms",
                len(intervals),
                _ms(hidden_ms),
                f"{100.0 * hidden_ms / duration_ms:.2f}%",
                note,
            ]
        )

    parts.append(_axis(duration_ms))

    # --- the spans themselves --------------------------------------------
    parts.append("<h2>Flash spans</h2>")
    raw_segments = document.get("segments") or []
    if raw_segments:
        parts.append(
            _table(
                [
                    "Start",
                    "End",
                    "Length",
                    "Kind",
                    "Area fraction",
                    "Area window",
                    "Flashes in window",
                ],
                [
                    [
                        _ms(float(segment.get("start_ms", 0))),
                        _ms(float(segment.get("end_ms", 0))),
                        _ms(float(segment.get("end_ms", 0)) - float(segment.get("start_ms", 0))),
                        segment.get("reason", "unknown"),
                        segment.get("area_fraction", "unknown"),
                        segment.get("area_window", "unknown"),
                        segment.get("max_flashes_in_window", "unknown"),
                    ]
                    for segment in raw_segments
                ],
            )
        )
    else:
        parts.append("<p>No span in this title went over the thresholds.</p>")

    # --- hidden segments --------------------------------------------------
    standard = PRESETS[0]
    standard_intervals = cover_intervals(
        spans[primary],
        guard_band_ms=standard.guard_band_ms,
        min_cover_ms=standard.min_cover_ms,
        duration_ms=duration_ms,
    )
    parts.append("<h2>Hidden segments</h2>")
    parts.append(
        f"<p>What the player hides on the {_esc(standard.title)} preset, from the "
        f"{_esc(primary)} map. Each flash span is widened by the "
        f"{standard.guard_band_ms:.0f} ms guard band on both sides, grown to at least "
        f"{standard.min_cover_ms:.0f} ms, and anything that overlaps or touches is one "
        "cover. Sound and captions keep playing under the cover. A red interval is always "
        "opaque, because dimming does not change the ratio of red the rule keys on.</p>"
    )
    if standard_intervals:
        parts.append(
            _table(
                ["Cover starts", "Cover ends", "Length", "Kind", "Cover"],
                [
                    [
                        _ms(interval.start_ms),
                        _ms(interval.end_ms),
                        _ms(interval.duration_ms),
                        interval.reason,
                        "opaque" if interval.reason == RED else "opaque, or dim if the "
                        "household allows it",
                    ]
                    for interval in standard_intervals
                ],
            )
        )
    else:
        parts.append("<p>Nothing is hidden in this title.</p>")

    # --- presets ----------------------------------------------------------
    parts.append("<h2>Presets</h2>")
    parts.append(
        "<p>A household setting can only make this stricter. Every preset includes the "
        "WCAG map, and the guard band and minimum cover are floored at the defaults, so "
        "no preset can hide less than Standard does.</p>"
    )
    parts.append(
        _table(
            [
                "Preset",
                "Name",
                "Maps unioned",
                "Guard band",
                "Minimum cover",
                "Intervals",
                "Hidden",
                "Share of film",
                "Coverage of this report",
            ],
            preset_rows,
        )
    )
    parts.append(
        "<ul>"
        + "".join(
            f"<li><strong>{_esc(preset.title)}</strong>: {_esc(preset.description)}</li>"
            for preset in PRESETS
        )
        + "</ul>"
    )

    # --- licence ----------------------------------------------------------
    parts.append("<h2>License and credit</h2>")
    if license_row:
        parts.append(
            _table(
                ["Field", "Value"],
                [
                    ["Source page", license_row.get("source_page_url", "")],
                    ["License", license_row.get("license", "")],
                    ["Credit line", license_row.get("credit_line", "")],
                    ["License checked on", license_row.get("license_checked_on", "")],
                    ["Notes", license_row.get("notes", "")],
                ],
            )
        )
    elif license_line:
        parts.append(f"<p>{_esc(license_line)}</p>")
    else:
        parts.append(
            "<p>No license line was supplied for this file, so this report does not claim "
            "one. Pass <code>--license-csv media/LICENSES.csv</code> or "
            "<code>--license-line</code> to put it here.</p>"
        )

    # --- hashes -----------------------------------------------------------
    parts.append("<h2>Hashes</h2>")
    hash_rows: list[list[object]] = [
        ["Source file SHA-256", source.get("sha256", "unknown")],
        ["Source file size", f"{source.get('size_bytes', 'unknown')} bytes"],
    ]
    for name, doc in sorted(maps.items()):
        path = map_files.get(name)
        if path is not None and path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hash_rows.append([f"Map file SHA-256 ({name})", digest])
        signature = doc.get("signature")
        if isinstance(signature, dict):
            hash_rows.append([f"Signing key id ({name})", signature.get("key_id", "unknown")])
            hash_rows.append(
                [f"Signed payload SHA-256 ({name})", signature.get("payload_sha256", "unknown")]
            )
        else:
            hash_rows.append([f"Signature ({name})", "none. This map is not signed."])
    for key in sorted(images):
        hash_rows.append(
            [f"Picture SHA-256 ({key})", hashlib.sha256(images[key]).hexdigest()]
        )
    parts.append(_table(["What", "Value"], hash_rows))
    parts.append(
        "<p>Every picture above is embedded in this file and nothing else is, so these "
        "hashes are reproducible from the file you are reading.</p>"
    )

    # --- what this does not measure ---------------------------------------
    not_implemented = list(profile.get("rules_not_implemented") or [])
    not_implemented += list(profile.get("exceptions_not_implemented") or [])
    parts.append("<h2>What this does not measure</h2>")
    if not_implemented:
        parts.append(
            "<ul>" + "".join(f"<li>{_esc(rule)}</li>" for rule in not_implemented) + "</ul>"
        )
    else:
        parts.append("<p>The map names no unimplemented rule.</p>")
    parts.append(
        f"<p>Rule set: {_esc(profile.get('title', 'unknown'))} "
        f"({_esc(profile.get('name', 'unknown'))}), {_esc(profile.get('flash_limit_per_second', '?'))} "
        f"flashes in any {_esc(profile.get('window_ms', '?'))} ms, area limit "
        f"{_esc(profile.get('area_fraction_limit', '?'))} of the "
        f"{_esc(profile.get('area_window_mode', '?'))}.</p>"
    )

    parts.append(
        f"<footer><p>{_esc(_DISCLAIMER)}</p>"
        "<p>This file is self contained. It loads nothing over the network and needs no "
        "file beside it.</p></footer>"
    )

    body = "\n".join(parts)
    page = (
        "<!doctype html>\n"
        "<html lang='en'>\n<head>\n<meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>{_esc(title)}: flash report</title>\n"
        f"<style>{_STYLE}</style>\n</head>\n<body>\n<main>\n{body}\n</main>\n</body>\n</html>\n"
    )
    return ReportDocument(html=page, images=images)


def write_report(path: str | Path, document: ReportDocument) -> Path:
    path = Path(path)
    path.write_text(document.html, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Command line plumbing, called from cli.py
# ---------------------------------------------------------------------------


def looks_like_a_map(path: Path) -> bool:
    """True when this file is a map sidecar rather than a video.

    Read as JSON and asked for the two keys every map has. A video is not going
    to parse as JSON, and a JSON file that is not a map fails the key check.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(document, dict) and "segments" in document and "source" in document


def add_report_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target", help="a video file, or a map sidecar already made for one")
    parser.add_argument("--out", required=True, help="where to write the HTML report")
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        metavar="PROFILE=PATH",
        help=(
            "another profile's map for the same file, for example broadcast=map.json. "
            "A preset whose maps are not all here is reported as a lower bound."
        ),
    )
    parser.add_argument("--title", default=None, help="what to call this title on the page")
    parser.add_argument(
        "--license-csv",
        default=None,
        help="a media/LICENSES.csv to take the license and credit line from",
    )
    parser.add_argument("--license-line", default=None, help="the license line, as text")


def _load_map_file(path: Path) -> dict[str, Any]:
    from .sidecar import load_map

    document = load_map(path)
    if not looks_like_a_map(path):
        raise SystemExit(f"{path} is not a flashmap map sidecar")
    return document


def _profile_name(document: dict[str, Any], fallback: str) -> str:
    profile = document.get("profile")
    if isinstance(profile, dict) and isinstance(profile.get("name"), str):
        return profile["name"]
    return fallback


def run_report(args: argparse.Namespace) -> int:
    """`flashmap report`. Returns 0 when the report was written.

    The exit code says whether the report exists, not whether the title is
    calm: a title that flashes is exactly the one worth a report. What the
    title did is on the page, and `flashmap check` is the command that passes
    or fails a file.
    """
    from .analyze import analyze_file
    from .decode import ColorPolicy, UnsupportedInput
    from .picture import LetterboxSettings
    from .profiles import get_profile
    from .sidecar import build_map

    target = Path(args.target)
    if not target.is_file():
        raise SystemExit(f"{target} is not a file")

    map_files: dict[str, Path] = {}
    if looks_like_a_map(target):
        document = _load_map_file(target)
        primary = _profile_name(document, "wcag")
        map_files[primary] = target
    else:
        # A video was handed in, so measure it here, with the analyzer's own
        # defaults and the WCAG rule set. Anything else (a room window, a
        # carried picture rectangle, another analysis width) is a measurement
        # decision, and those belong to `flashmap analyze`, whose map this
        # command will happily take instead.
        try:
            result = analyze_file(
                target,
                profile=get_profile("wcag"),
                room=None,
                policy=ColorPolicy(),
                analysis_width=192,
                letterbox=LetterboxSettings(),
            )
        except UnsupportedInput as exc:
            print(f"flashmap cannot measure {target}: {exc}", file=sys.stderr)
            return EXIT_ERROR
        document = build_map(result)
        primary = _profile_name(document, "wcag")

    maps: dict[str, dict[str, Any]] = {primary: document}
    for pair in args.map:
        label, _, raw_path = str(pair).partition("=")
        if not raw_path:
            raise SystemExit(f"--map wants PROFILE=PATH, got {pair!r}")
        extra_path = Path(raw_path)
        extra = _load_map_file(extra_path)
        found = _profile_name(extra, label)
        if found != label:
            raise SystemExit(
                f"--map {pair} says {label!r}, but that map was measured against "
                f"{found!r}. Name it for the profile it holds."
            )
        maps[label] = extra
        map_files[label] = extra_path

    source = maps[primary].get("source") or {}
    source_name = str(source.get("path", target.name))
    sha256 = str(source.get("sha256", ""))

    license_row = None
    if args.license_csv:
        license_row = _license_from_csv(Path(args.license_csv), source_name, sha256)
        if license_row is None:
            print(
                f"no row for {source_name} in {args.license_csv}. The report says no "
                "license line was supplied rather than guessing one.",
                file=sys.stderr,
            )

    document_out = build_report(
        maps,
        title=args.title or Path(source_name).stem,
        primary=primary,
        map_files=map_files,
        license_row=license_row,
        license_line=args.license_line,
    )
    written = write_report(args.out, document_out)
    print(f"report written to {written}")
    print(
        f"{len(document_out.images)} picture(s) embedded, no network reference, "
        "no frame of the film."
    )
    return EXIT_OK
