"""Render the whole report page and run flashmap over it, at display size.

    python eval/report_page_check.py            # the page, then the control
    python eval/report_page_check.py --json     # the same, as a report
    python eval/report_page_check.py --only page

`flashmap report` writes one HTML page per title with a flash timeline drawn as
coloured bars. flashmap/tests/test_report.py checks each of those bars as a
picture on its own. That is not what a reader sees. A reader sees the page: the
lanes at the size the layout gives them, on the page's own ground, with the
headings and the tables around them. So this renders that page in headless
Chrome at the width the page was laid out for, cuts it into display sized
frames, and puts every frame through the analyzer under the `broadcast`
profile, which is the one that carries the regular pattern rule of
ITU-R BT.1702-3 Attachment 1 to Annex 1.

eval/brand_assets_check.py set the shape of this: build the still, hold it,
analyse it, delete it, and keep a negative control that proves the check can
say no.

What the run holds the page to
------------------------------

1. **No flash anywhere on the page.** A page is a still and a still cannot
   flash, so this is a guard against a page that decodes to something other
   than what was drawn rather than a threshold anything is expected to reach.

2. **No bar boundary inside the timeline.** A light and dark pair only exists
   where the step between two levels reaches the Guideline 1 flash difference,
   which for SDR is 20 cd/m2 with the darker state below 160 cd/m2. The lane
   colours in flashmap/report.py are picked to stay under that, so the pattern
   rule's own bar scanner should find nothing at all inside a lane, at the size
   the page draws it. This is the condition the negative control breaks.

3. **The whole page's own pattern numbers, printed every run.** Read them. The
   report page does not pass this rule, and that is not the timeline: see below.

What this check found, and did not paper over
---------------------------------------------

The report page fails the regular pattern rule on its text. Cream on teal is
160.77 cd/m2 against 8.47 cd/m2, so every glyph edge is a Guideline 1 step, and
a line of text crossed by a scan line is a row of them. On the page this check
builds, all nine display frames hold a pattern finding, at 16 to 25 pairs over
44% to 64% of the frame against a 25% area limit. Analysing more finely does not
rescue it, it sharpens it: the same nine frames at analysis widths 384, 640 and
1280 give 37 to 77, 71 to 152 and 82 to 176 pairs, over as much as 93% of the
frame.

That is a property of the detector applied to text, not a hazard the report can
design away. Readable text needs 4.5:1, and at an SDR peak of 200 cd/m2 there is
no pair of colours with that ratio whose luminance difference is under
20 cd/m2 or whose darker state is above 160 cd/m2, so any page a person can read
holds Guideline 1 steps at every glyph. BT.1702-3's own scope sentence asks for
the guidelines to be applied "when flashing or regular patterns are clearly
discernible", and a paragraph of text is not a clearly discernible stripe
pattern, but nothing in the attachment's numbers says so and flashmap does not
guess. The app's own screen check, app/tools/ui_flashmap.mjs, runs `--profile
wcag`, which has no pattern rule, so this is the first time anything in this
repo has put text in front of the pattern rule.

So the page's own verdict is printed and not asserted on, and what is asserted
is the timeline: the rule's bar scanner must find nothing in it. docs/DECISIONS.md
carries the reasoning and the cost.

SAFETY. The negative control is a deliberately striped page, which is the
hazard this whole exercise is about. It is built under a HAZARD_ name in a
temporary directory, rendered by a headless browser that shows nothing to
anybody, analysed, and deleted with the directory in the same run. Nothing here
opens it where a person can see it.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "flashmap/src"))

from flashmap import report as report_module  # noqa: E402
from flashmap.analyze import analyze_file  # noqa: E402
from flashmap.color import LUMA_B, LUMA_G, LUMA_R, bt1886_nits  # noqa: E402
from flashmap.pattern import scan_bars, stripe_mask  # noqa: E402
from flashmap.pngout import encode_png  # noqa: E402
from flashmap.profiles import get_profile  # noqa: E402

# ---------------------------------------------------------------------------
# The display the page is read on. Ours, not a spec's, and a choice rather than
# a threshold: the pattern rule is about a fraction of the displayed area, so
# the page has to be rasterised at some size, and both numbers are recorded in
# every line this prints. 1280 by 720 is a 16:9 display, and the report's own
# layout tops out at 1120 px of content (`main { max-width: 1120px }` in
# report.py) plus 24 px of body padding each side, so at 1280 the page is laid
# out at its full designed width and nothing is squeezed or reflowed.
# ---------------------------------------------------------------------------

DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

# A frame is held this long at this rate, the same as eval/brand_assets_check.py.
# It matters more here: the pattern rule's motion class needs a run of frames
# before it will call a pattern stationary, and until it has one every frame is
# uncertain, which takes the stricter 25% area rather than the 40% one. A two
# second hold therefore measures the page under both limits in one run.
HOLD_SECONDS = 2
FPS = 24

# How tall a window the page is first rendered into, and how far the search for
# the page's real height is allowed to go. Neither is a measurement: the render
# doubles until the page fits and the bottom of the picture is the page's own
# ground, and then the picture is trimmed to the last row that holds anything.
FIRST_RENDER_HEIGHT = 4000
MAX_RENDER_HEIGHT = 16000

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)

EXIT_OK = 0
EXIT_FINDING = 1
EXIT_ERROR = 2


# ---------------------------------------------------------------------------
# The page under test
# ---------------------------------------------------------------------------


def a_worst_case_map(spans: int = 40, duration_ms: float = 300_000.0) -> dict[str, Any]:
    """A map with more flagged spans than a lane can draw.

    Not the easy title. A calm map draws four empty lanes and a page with no
    table, and checking that would say very little. This one fills every lane to
    the block cap and gives the page a long table to lay out, which is the page
    at its busiest.
    """
    segments = []
    for index in range(spans):
        start = 1_000.0 + index * (duration_ms - 4_000.0) / max(1, spans)
        segments.append(
            {
                "start_ms": round(start, 3),
                "end_ms": round(start + 600.0, 3),
                "reason": "red" if index % 3 else "general",
                "area_fraction": 0.42,
                "area_window": "wcag-10deg",
                "max_flashes_in_window": 9,
            }
        )
    return {
        "schema": "https://calm-frames.github.io/schemas/flashmap-map-v1.json",
        "version": 1,
        "generator": {"name": "flashmap", "version": report_module.__version__},
        "created_utc": "2026-09-18T00:00:00Z",
        "source": {
            "path": "HAZARD_worst_case_for_the_report_page.mkv",
            "sha256": "0" * 64,
            "size_bytes": 12_345_678,
            "coded_width": 1920,
            "coded_height": 1080,
            "duration_ms": duration_ms,
            "frame_count": 7200,
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
            "pass": False,
            "segment_count": len(segments),
            "hidden_ms": 0,
            "general_segment_count": sum(1 for s in segments if s["reason"] == "general"),
            "red_segment_count": sum(1 for s in segments if s["reason"] == "red"),
        },
    }


def a_striped_lane(width: int, height: int, pairs: int = 12) -> bytes:
    """A lane sized picture that is a real stripe pattern.

    The negative control's timeline. Cream and ink, which are 160.77 and
    3.11 cd/m2 through the profile's own curve, so every edge of it is far over
    the Guideline 1 difference, and twelve pairs is over the attachment's count.
    This is what the report's timeline must never look like.
    """
    stripes = np.zeros((height, width, 3), dtype=np.uint8)
    bar = max(1, width // (pairs * 2))
    for x in range(width):
        light = (x // bar) % 2 == 0
        stripes[:, x] = report_module._rgb(
            report_module.TEXT if light else report_module.INK
        )
    return encode_png(stripes)


def a_flat_lane(width: int, height: int) -> bytes:
    """A lane with nothing drawn on it: the page with its timeline taken away."""
    flat = np.zeros((height, width, 3), dtype=np.uint8)
    flat[:, :] = report_module._rgb(report_module.LANE_GROUND)
    return encode_png(flat)


def pages() -> dict[str, str]:
    """The three pages this check renders, as HTML.

    All three are the same page: the same text, the same tables, the same
    layout, the same picture sizes. Only the pixels inside the timeline change,
    so anything the measurements disagree about is the timeline and nothing else.
    """
    document = report_module.build_report(
        {"wcag": a_worst_case_map()}, title="Worst case", primary="wcag"
    )
    width, height = report_module.LANE_WIDTH_PX, report_module.LANE_HEIGHT_PX
    flat = report_module._data_uri(a_flat_lane(width, height))
    striped = report_module._data_uri(a_striped_lane(width, height))

    page = document.html
    flattened = page
    hazard = page
    for png in document.images.values():
        original = report_module._data_uri(png)
        flattened = flattened.replace(original, flat)
        hazard = hazard.replace(original, striped)
    return {"page": page, "flattened": flattened, "HAZARD_striped_page": hazard}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def find_chrome() -> str:
    """Headless Chrome, the renderer app/assets/brand/render.sh already uses."""
    named = os.environ.get("CALM_FRAMES_CHROME")
    if named:
        if not Path(named).is_file():
            raise FileNotFoundError(f"CALM_FRAMES_CHROME points at {named}, which is not a file")
        return named
    for candidate in CHROME_CANDIDATES:
        if candidate.startswith("/") and Path(candidate).is_file():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    raise FileNotFoundError(
        "no Chrome or Chromium was found. Set CALM_FRAMES_CHROME to one, or install "
        "google-chrome. app/assets/brand/render.sh says why this repo renders with Chrome."
    )


def screenshot(chrome: str, html: Path, out: Path, width: int, height: int) -> None:
    """One page into one PNG, with the same flags app/assets/brand/render.sh uses.

    --force-device-scale-factor=1 stops a retina display doubling everything,
    and --hide-scrollbars keeps a scrollbar out of the picture, where it would
    be a bright stripe down one edge of every frame.
    """
    done = subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--virtual-time-budget={HOLD_SECONDS * 1000}",
            f"--window-size={width},{height}",
            f"--screenshot={out}",
            f"file://{html}",
        ],
        capture_output=True,
        text=True,
    )
    if not out.is_file():
        raise RuntimeError(
            f"Chrome wrote no screenshot for {html} (exit {done.returncode}): "
            f"{(done.stderr or done.stdout).strip()[:400]}"
        )


def decode_png(path: Path) -> np.ndarray:
    """A PNG as height by width by 3 uint8, through ffmpeg rather than a library.

    flashmap has a PNG writer and no reader, and this check is not a reason to
    put an imaging library in front of anybody. ffmpeg is already required.
    """
    probe = subprocess.run(
        [
            "ffprobe", "-hide_banner", "-loglevel", "error",
            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path),
        ],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    width, height = (int(value) for value in probe.split("x")[:2])
    raw = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3).copy()


def render_page(chrome: str, html: str, work: Path, name: str) -> np.ndarray:
    """One page, rasterised whole at the display width.

    The window is made taller until the page fits inside it, which is how the
    page's own height is found without asking the browser to run any script: a
    page that overflows its window paints content on the bottom row, and a page
    that fits paints its ground there. The picture is then trimmed to the last
    row that holds anything.
    """
    page_file = work / f"{name}.html"
    page_file.write_text(html, encoding="utf-8")
    ground = np.array(report_module._rgb(report_module.BACKGROUND), dtype=np.uint8)

    height = FIRST_RENDER_HEIGHT
    while True:
        shot = work / f"{name}.png"
        screenshot(chrome, page_file, shot, DISPLAY_WIDTH, height)
        picture = decode_png(shot)
        painted = np.nonzero(~(picture == ground).all(axis=2).all(axis=1))[0]
        content = int(painted.max()) + 1 if painted.size else 1
        if content < picture.shape[0]:
            return picture[:content]
        if height >= MAX_RENDER_HEIGHT:
            raise RuntimeError(
                f"{name} is taller than {MAX_RENDER_HEIGHT} px at {DISPLAY_WIDTH} px wide, "
                "so it cannot be rasterised whole. Raise MAX_RENDER_HEIGHT on purpose."
            )
        height = min(height * 2, MAX_RENDER_HEIGHT)


def display_frames(page: np.ndarray) -> list[np.ndarray]:
    """The page cut into what a viewer has on the screen at one time.

    The last frame is padded out with the page's own ground, so every frame the
    analyzer sees is exactly one display and the area fractions it reports are
    fractions of a display.
    """
    ground = np.array(report_module._rgb(report_module.BACKGROUND), dtype=np.uint8)
    frames = []
    for top in range(0, page.shape[0], DISPLAY_HEIGHT):
        piece = page[top : top + DISPLAY_HEIGHT]
        if piece.shape[0] < DISPLAY_HEIGHT:
            pad = np.zeros((DISPLAY_HEIGHT - piece.shape[0], page.shape[1], 3), dtype=np.uint8)
            pad[:, :] = ground
            piece = np.concatenate([piece, pad], axis=0)
        frames.append(np.ascontiguousarray(piece))
    return frames


# ---------------------------------------------------------------------------
# Measuring
# ---------------------------------------------------------------------------


@dataclass
class FrameFinding:
    index: int
    passes: bool
    flash_segments: list[dict[str, Any]] = field(default_factory=list)
    pattern_segments: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "frame": self.index,
            "passes": self.passes,
            "flash_segments": self.flash_segments,
            "pattern_segments": self.pattern_segments,
        }


def analyse_frame(frame: np.ndarray, work: Path, index: int) -> FrameFinding:
    """One display, held, through the analyzer under the broadcast profile."""
    picture = work / f"frame{index:02d}.png"
    picture.write_bytes(encode_png(frame))
    video = work / f"frame{index:02d}.mkv"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            # -loop is safe here and needed: the input is a still this script
            # drew, so there are no frames of its own to miss, and the pattern
            # rule needs a run of frames before it will call anything still.
            "-loop", "1", "-framerate", str(FPS), "-t", str(HOLD_SECONDS),
            "-i", str(picture),
            "-vf", "format=rgb24",
            "-c:v", "ffv1",  # lossless, so the analyzer sees the pixels Chrome drew
            str(video),
        ],
        check=True, capture_output=True,
    )
    result = analyze_file(video, profile=get_profile("broadcast"))
    picture.unlink(missing_ok=True)
    video.unlink(missing_ok=True)
    return FrameFinding(
        index=index,
        passes=result.passes,
        flash_segments=[segment.as_dict() for segment in result.segments],
        pattern_segments=[segment.as_dict() for segment in result.pattern_segments],
    )


def nits(picture: np.ndarray) -> np.ndarray:
    """Screen luminance of an sRGB picture, through the profile's own curve.

    The same arithmetic flashmap/src/flashmap/report.py writes out beside the
    lane colours: BT.709 luma of the bytes, then color.bt1886_nits at the
    profile's peak white. The analyzer gets there through the decoder's luma
    plane; this gets there from the pixels, because the assertion below is about
    the page as it was drawn and not about a re-encode of it.
    """
    profile = get_profile("broadcast")
    peak = profile.peak_nits
    if peak is None:  # pragma: no cover - the broadcast profile carries one
        raise RuntimeError("the broadcast profile has no peak white")
    weights = np.array([LUMA_R, LUMA_G, LUMA_B], dtype=np.float32)
    level = (picture.astype(np.float32) * weights).sum(axis=-1) / np.float32(255.0)
    return np.asarray(bt1886_nits(level, peak))


def _runs(flags: np.ndarray) -> list[tuple[int, int]]:
    """The stretches where `flags` is true, as (start, stop) with stop exclusive."""
    runs: list[tuple[int, int]] = []
    start = None
    for index, on in enumerate(flags):
        if on and start is None:
            start = index
        elif not on and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(flags)))
    return runs


def locate_lanes(chrome: str, html: str, work: Path) -> list[tuple[int, int, int, int]]:
    """Where the timeline sits on the page, in rendered pixels.

    Found on a twin of the page whose lanes are flat track and nothing else, so
    a lane is a solid rectangle of one known colour and its rectangle can be read
    off exactly. Nowhere else on the page is that colour. Doing it this way
    rather than hunting for the track inside the real page matters: a lane full
    of blocks holds very little bare track, and a page that drew no block at all
    would hand back a rectangle either way.

    Every page this check renders is the same HTML with different bytes inside
    the same `img` elements, so one geometry fits all three.
    """
    twin = render_page(chrome, html, work, "flattened")
    track = np.array(report_module._rgb(report_module.LANE_GROUND), dtype=np.uint8)
    solid = (twin == track).all(axis=2)
    boxes: list[tuple[int, int, int, int]] = []
    for top, bottom in _runs(solid.mean(axis=1) > 0.25):
        columns = _runs(solid[top:bottom].mean(axis=0) > 0.5)
        if not columns:
            continue
        left = min(start for start, _ in columns)
        right = max(stop for _, stop in columns)
        boxes.append((top, bottom, left, right))
    return boxes


def bars_inside(page: np.ndarray, bands: list[tuple[int, int, int, int]]) -> list[dict[str, Any]]:
    """The pattern rule's own bar scanner, run over the timeline as drawn.

    scan_bars is imported from flashmap.pattern and handed the profile's own
    Guideline 1 numbers, so this asks the rule its own question: is there a light
    and dark pair anywhere in this lane? A lane whose colours stay under the
    flash difference answers no on every scan line, in every orientation, at any
    number of blocks, which is the belt to the block cap's braces.
    """
    profile = get_profile("broadcast")
    rule = profile.pattern
    if rule is None:  # pragma: no cover - the broadcast profile carries one
        raise RuntimeError("the broadcast profile has no pattern rule")
    findings = []
    for top, bottom, left, right in bands:
        lane = nits(page[top:bottom, left:right])
        rows, _, _ = scan_bars(lane, profile.general.min_delta, profile.general.dark_image_below)
        columns, _, _ = scan_bars(lane.T, profile.general.min_delta, profile.general.dark_image_below)
        scan = stripe_mask(
            lane,
            min_delta=profile.general.min_delta,
            dark_below=profile.general.dark_image_below,
            min_bars=2 * (rule.more_than_pairs + 1),
            orientations=rule.settings.orientations,
            min_profile_samples=rule.settings.min_profile_samples,
        )
        findings.append(
            {
                "top": int(top),
                "bottom": int(bottom),
                "left": int(left),
                "right": int(right),
                "most_bars_on_a_row": int(rows.max()) if rows.size else 0,
                "most_bars_on_a_column": int(columns.max()) if columns.size else 0,
                "stripe_pairs": int(scan.stripe_pairs),
                "pattern_area_fraction": round(float(scan.area_fraction), 6),
            }
        )
    return findings


@dataclass
class PageResult:
    name: str
    height: int
    frames: list[FrameFinding]
    lanes: list[dict[str, Any]]

    @property
    def flashes(self) -> list[FrameFinding]:
        return [frame for frame in self.frames if frame.flash_segments]

    @property
    def lane_bars(self) -> int:
        return max(
            (
                max(lane["most_bars_on_a_row"], lane["most_bars_on_a_column"])
                for lane in self.lanes
            ),
            default=0,
        )

    @property
    def page_pattern_frames(self) -> list[FrameFinding]:
        return [frame for frame in self.frames if frame.pattern_segments]

    def as_dict(self) -> dict[str, Any]:
        return {
            "page": self.name,
            "rendered": f"{DISPLAY_WIDTH}x{self.height}",
            "display_frames": len(self.frames),
            "frames": [frame.as_dict() for frame in self.frames],
            "timeline_lanes": self.lanes,
            "most_bars_in_a_lane": self.lane_bars,
        }


def measure(
    chrome: str, name: str, html: str, work: Path, lanes: list[tuple[int, int, int, int]]
) -> PageResult:
    page = render_page(chrome, html, work, name)
    frames = [
        analyse_frame(frame, work, index) for index, frame in enumerate(display_frames(page))
    ]
    return PageResult(
        name=name,
        height=int(page.shape[0]),
        frames=frames,
        lanes=bars_inside(page, lanes),
    )


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------


def _worst_area(frame: FrameFinding) -> float:
    return max((float(p["area_fraction"]) for p in frame.pattern_segments), default=0.0)


def report(result: PageResult, *, quiet: bool = False) -> None:
    if quiet:
        return
    print(f"\n{result.name}: rendered {DISPLAY_WIDTH}x{result.height}, "
          f"{len(result.frames)} display frame(s) of {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    for frame in result.frames:
        kinds = []
        if frame.flash_segments:
            kinds.append(f"{len(frame.flash_segments)} flash")
        for pattern in frame.pattern_segments:
            kinds.append(
                f"pattern {pattern['stripe_pairs']} pairs over "
                f"{pattern['area_fraction']:.3f} of the frame, limit "
                f"{pattern['area_limit']:.2f}, motion {pattern['motion']}"
            )
        verdict = "PASS" if frame.passes else "FAIL"
        print(f"  frame {frame.index}: {verdict}  " + ("; ".join(kinds) if kinds else "nothing"))
    print(f"  timeline: {len(result.lanes)} lane(s), scanned where the page draws them")
    for lane in result.lanes:
        print(
            f"    rows {lane['top']} to {lane['bottom']}: "
            f"{lane['most_bars_on_a_row']} bar(s) on the busiest row, "
            f"{lane['most_bars_on_a_column']} on the busiest column, "
            f"pattern area {lane['pattern_area_fraction']:.3f}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--json", action="store_true", help="print a report instead")
    parser.add_argument(
        "--only",
        choices=["page", "control", "flattened"],
        default=None,
        help="run one page rather than the page and its negative control",
    )
    arguments = parser.parse_args()
    quiet = arguments.json

    try:
        chrome = find_chrome()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_ERROR
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("ffmpeg and ffprobe are needed to build and read the stills", file=sys.stderr)
        return EXIT_ERROR

    html = pages()
    wanted = {
        None: ["page", "HAZARD_striped_page"],
        "page": ["page"],
        "control": ["HAZARD_striped_page"],
        "flattened": ["flattened"],
    }[arguments.only]

    results: dict[str, PageResult] = {}
    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="report-page-check-") as raw_work:
        work = Path(raw_work)
        if not quiet:
            print(f"Chrome: {chrome}")
        lanes = locate_lanes(chrome, html["flattened"], work)
        if not lanes:
            print(
                "no timeline was found on the rendered page, so nothing was checked. The "
                "lane rectangles are read off a twin of the page whose lanes are flat track; "
                "if the page stopped drawing lanes, or the track colour changed, this is what "
                "it looks like.",
                file=sys.stderr,
            )
            return EXIT_ERROR
        if not quiet:
            print(f"timeline: {len(lanes)} lane(s) at {lanes}")
        for name in wanted:
            results[name] = measure(chrome, name, html[name], work, lanes)
            report(results[name], quiet=quiet)

    subject = results.get("page")
    if subject is not None:
        for frame in subject.flashes:
            problems.append(
                f"display frame {frame.index} of the report page holds a flash segment, "
                "which a still page cannot do. Something decoded as other than what was drawn."
            )
        if subject.lane_bars:
            problems.append(
                f"the report page's timeline holds {subject.lane_bars} bar boundary(ies) at "
                "display size. The lane colours are supposed to stay under the Guideline 1 "
                "flash difference, so a lane cannot hold a light and dark pair at all. "
                "See the arithmetic in flashmap/src/flashmap/report.py."
            )

    control = results.get("HAZARD_striped_page")
    if control is not None and not control.lane_bars:
        problems.append(
            "the negative control passed. Its timeline is a twelve pair cream and ink stripe "
            "pattern, so the bar scanner has to find it. A check that cannot say no says "
            "nothing when it says yes."
        )
    if control is not None and subject is not None:
        # The other half of the negative control, and it is about the analyzer
        # run rather than the bar scan. The two pages differ only inside the
        # lanes, so if every display frame of the striped page measures the same
        # as the report page's, the whole page run is blind to the timeline and
        # the lane scan above is the only thing working.
        moved = [
            frame.index
            for frame, calm in zip(control.frames, subject.frames)
            if _worst_area(frame) > _worst_area(calm) + 0.001
        ]
        if not moved:
            problems.append(
                "the negative control changed nothing the whole page run could see. Its "
                "timeline is a stripe pattern and the report page's is not, so at least one "
                "display frame has to measure more pattern area."
            )
        elif not quiet:
            print(
                f"\nnegative control: display frame(s) {moved} measured more pattern area on "
                "the whole page than the report page's own."
            )

    if arguments.json:
        print(json.dumps(
            {
                "statement": (
                    "The whole report page rendered in headless Chrome at "
                    f"{DISPLAY_WIDTH} px wide, cut into {DISPLAY_WIDTH}x{DISPLAY_HEIGHT} "
                    "display frames, each held two seconds and analysed under the broadcast "
                    "profile, which carries the ITU-R BT.1702-3 regular pattern rule. The "
                    "page's own pattern findings come from its text and are reported, not "
                    "asserted on. What is asserted is that the timeline holds no bar "
                    "boundary at all."
                ),
                "tool": "eval/report_page_check.py",
                "profile": "broadcast",
                "display": f"{DISPLAY_WIDTH}x{DISPLAY_HEIGHT}",
                "pages": [result.as_dict() for result in results.values()],
                "problems": problems,
            },
            indent=2,
        ))

    if problems:
        print("", file=sys.stderr)
        for problem in problems:
            print(f"FINDING: {problem}", file=sys.stderr)
        return EXIT_FINDING

    if not quiet:
        if control is not None:
            print(
                f"\nnegative control: refused, {control.lane_bars} bar boundary(ies) found in "
                "its striped timeline. The check can say no."
            )
        if subject is not None:
            pattern_frames = len(subject.page_pattern_frames)
            print(
                f"\nreport page: no flash, and no bar boundary anywhere in the timeline.\n"
                f"{pattern_frames} of {len(subject.frames)} display frame(s) hold a pattern "
                "finding from the page's own text, which is printed above and explained in "
                "the docstring of this file and in docs/DECISIONS.md."
            )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
