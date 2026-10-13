#!/usr/bin/env python3
"""The pictures the pattern rule's precision is measured on: text, UI and real gratings.

Nothing here imports flashmap. It draws, and it says what it drew. That is the whole of the
ground truth and it is the same rule the grating conformance suite works to: a generated
picture is worth measuring because the generator knows exactly what went into it.

  * a page of text has no stripes drawn in it, so a pattern finding on one is a false
    positive. Whatever a scan line makes of a paragraph, no light and dark pair was drawn;
  * a grating has a known pair count, a known area and a known bar difference, so whether it
    is over the rule is a fact about the drawing;
  * a mixed picture is a grating drawn over a known share of a page of text, and it is
    positive when the grating's own area is over the limit.

The colours are the ones the product ships: teal ground, cream text, saffron and ink, from
docs/brand. Cream on teal is the pair that started this, at 160.77 against 8.47 cd/m2.

Fonts come from matplotlib's bundled DejaVu rather than from the machine, so a CI runner and
this Mac draw the same glyphs. DejaVu Sans Mono is in here on purpose: a monospaced table is
the most regular thing a page of text can be, and it is the case a periodicity test is most
likely to get wrong.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFont

__all__ = ["Frame", "frames", "WIDTH", "HEIGHT"]

WIDTH = 1280
HEIGHT = 720

TEAL = (31, 77, 92)
CREAM = (243, 232, 211)
SAFFRON = (230, 169, 87)
INK = (23, 50, 60)
BRONZE = (184, 122, 44)
SURFACE = (23, 59, 71)
"""#173B47, a card on the ground. flashmap/src/flashmap/report.py SURFACE."""
TEXT_DIM = (207, 224, 220)
"""#CFE0DC. report.py TEXT_DIM."""

# The type this product actually sets, at the size a 1280 wide display frame draws it. Two
# scales, because there are two surfaces and they are not the same.
#
# The app's sizes are 1080p units from app/src/calmframes/calmStyles.ts CALM_TYPE, scaled by
# 1280/1920 the way scaleUxToDp does: SMALL 32, BODY 36, CARD_DETAIL and BUTTON 38, SECTION
# 44, CARD_TITLE 56, SCREEN_TITLE 64. The report page's are the px in report.py's stylesheet.
APP_TYPE_PX = {"small": 21, "body": 24, "card-detail": 25, "section": 29,
               "card-title": 37, "screen-title": 43}
REPORT_TYPE_PX = {"table": 13, "body": 14, "lead": 17, "h3": 21, "h1": 30}

# The pairs a reader actually sees on these surfaces, with their contrast ratios as
# report.py records them. Cream on teal is the one that started this: 160.77 against
# 8.47 cd/m2 through the profile's own curve.
SHIPPED_PAIRS = (
    ("cream-on-teal", TEAL, CREAM),
    ("cream-on-surface", SURFACE, CREAM),
    ("dim-on-teal", TEAL, TEXT_DIM),
    ("ink-on-saffron", SAFFRON, INK),
)

WORDS = (
    "every title is scanned frame by frame before it can play and the map it "
    "produces is signed against the file hash so a player can refuse a title "
    "whose map has moved on it reduces exposure to flashing above published "
    "limits in the videos it plays it is not a medical device the cover goes on "
    "before the flashing starts and the sound and the captions carry on through "
    "it a parent sets the room size and the preset behind a pin and the house "
    "floor can only ever be made stricter than the published limit never looser"
).split()


@lru_cache(maxsize=None)
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    import matplotlib

    root = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    return ImageFont.truetype(os.path.join(root, name), size)


@dataclass(frozen=True)
class Frame:
    """One picture and what was drawn into it.

    There is no `truth` field on purpose. Whether a drawing is over the rule depends on the
    rule's own numbers, and those live in the spec file, so the runner works it out from
    `drawn_pairs` and `drawn_area` rather than this module asserting a verdict. A page of
    text has `drawn_pairs` 0, which is the whole of its ground truth: no pair was drawn.
    """

    clip_id: str
    kind: str
    """text, ui, grating or mixed."""
    draw: Callable[[], np.ndarray] = field(repr=False)
    note: str = ""
    drawn_area: float = 0.0
    """The share of the picture the drawn stripe block covers. Zero when none was drawn."""
    drawn_pairs: int = 0
    """Light and dark pairs drawn into the block. Zero when none was drawn."""


# ---- text and UI, none of which has a stripe in it --------------------------------------


def _wrapped(drawer: ImageDraw.ImageDraw, text_font, width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    index = 0
    while len(lines) < 200:
        word = WORDS[index % len(WORDS)]
        index += 1
        candidate = f"{line} {word}".strip()
        if drawer.textlength(candidate, font=text_font) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
        if len(lines) > 60:
            break
    return lines


def text_page(
    size: int, leading: float, columns: int, ground: tuple[int, int, int],
    ink: tuple[int, int, int], face: str = "DejaVuSans.ttf", margin: int = 64,
) -> np.ndarray:
    image = Image.new("RGB", (WIDTH, HEIGHT), ground)
    drawer = ImageDraw.Draw(image)
    text_font = font(face, size)
    gap = 32
    column_width = (WIDTH - 2 * margin - gap * (columns - 1)) // columns
    step = max(1, int(round(size * leading)))
    lines = _wrapped(drawer, text_font, column_width)
    per_column = max(1, (HEIGHT - 2 * margin) // step)
    for column in range(columns):
        left = margin + column * (column_width + gap)
        for row in range(per_column):
            index = column * per_column + row
            if index >= len(lines):
                break
            drawer.text((left, margin + row * step), lines[index], font=text_font, fill=ink)
    return np.asarray(image, dtype=np.uint8)


def number_table(rows: int, size: int, ground, ink, face: str = "DejaVuSansMono.ttf") -> np.ndarray:
    """The hardest negative: monospaced digits on a fixed grid, rows and columns both regular."""
    image = Image.new("RGB", (WIDTH, HEIGHT), ground)
    drawer = ImageDraw.Draw(image)
    table_font = font(face, size)
    step = max(1, (HEIGHT - 96) // rows)
    rng = np.random.default_rng(20260919)
    for row in range(rows):
        y = 48 + row * step
        cells = "  ".join(f"{int(v):7d}" for v in rng.integers(1000, 9_999_999, 7))
        drawer.text((64, y), cells, font=table_font, fill=ink)
    return np.asarray(image, dtype=np.uint8)


def card_grid(across: int, down: int, ground, card, label) -> np.ndarray:
    """A shelf of cards, which is what the app's own screens are."""
    image = Image.new("RGB", (WIDTH, HEIGHT), ground)
    drawer = ImageDraw.Draw(image)
    pad = 28
    card_w = (WIDTH - pad * (across + 1)) // across
    card_h = (HEIGHT - pad * (down + 1)) // down
    title = font("DejaVuSans.ttf", max(14, card_h // 6))
    for row in range(down):
        for column in range(across):
            x = pad + column * (card_w + pad)
            y = pad + row * (card_h + pad)
            drawer.rectangle([x, y, x + card_w, y + card_h], fill=card)
            drawer.text((x + 12, y + 12), WORDS[(row * across + column) % len(WORDS)],
                        font=title, fill=label)
    return np.asarray(image, dtype=np.uint8)


# ---- gratings, which are the thing the rule is for --------------------------------------


def grating(
    pairs: int, area_fraction: float, orientation: str,
    light: tuple[int, int, int] = CREAM, dark: tuple[int, int, int] = INK,
    ground: tuple[int, int, int] = TEAL, over_text: bool = False,
) -> np.ndarray:
    base = (
        text_page(26, 1.55, 1, TEAL, CREAM)
        if over_text
        else np.full((HEIGHT, WIDTH, 3), ground, dtype=np.uint8)
    )
    picture = base.copy()
    if orientation == "vertical":
        block_w = max(2 * pairs, int(round(WIDTH * area_fraction)))
        x0 = (WIDTH - block_w) // 2
        bar = block_w / (2 * pairs)
        xs = np.arange(block_w)
        light_bar = (np.floor(xs / bar).astype(int) % 2) == 0
        block = np.where(light_bar[None, :, None], np.array(light), np.array(dark))
        picture[:, x0 : x0 + block_w] = block.astype(np.uint8)
    elif orientation == "horizontal":
        block_h = max(2 * pairs, int(round(HEIGHT * area_fraction)))
        y0 = (HEIGHT - block_h) // 2
        bar = block_h / (2 * pairs)
        ys = np.arange(block_h)
        light_bar = (np.floor(ys / bar).astype(int) % 2) == 0
        block = np.where(light_bar[:, None, None], np.array(light), np.array(dark))
        picture[y0 : y0 + block_h] = block.astype(np.uint8)
    elif orientation == "diagonal":
        # The block keeps the picture's aspect and is scaled by the square root, so its area
        # really is `area_fraction` of the picture. A square of side sqrt(a) * min(w, h) is
        # not: on a 16:9 picture that block covers a * h / w, which is a little over half of
        # what it claims, and every diagonal row of this suite was mislabelled by exactly
        # that factor until it was caught by the detector disagreeing with the label.
        block_w = max(4 * pairs, int(round(WIDTH * np.sqrt(area_fraction))))
        block_h = max(4 * pairs, int(round(HEIGHT * np.sqrt(area_fraction))))
        y0 = max(0, (HEIGHT - block_h) // 2)
        x0 = max(0, (WIDTH - block_w) // 2)
        ys, xs = np.mgrid[0:block_h, 0:block_w]
        bar = (block_w + block_h) / (2 * pairs)
        light_bar = (np.floor((xs + ys) / bar).astype(int) % 2) == 0
        block = np.where(light_bar[:, :, None], np.array(light), np.array(dark))
        picture[y0 : y0 + block_h, x0 : x0 + block_w] = block.astype(np.uint8)
    else:
        raise ValueError(f"unknown orientation {orientation!r}")
    return picture


def _drawn_area(orientation: str, area_fraction: float) -> float:
    return area_fraction


# ---- the set ----------------------------------------------------------------------------


def frames() -> list[Frame]:
    """Every picture, with what was drawn into it.

    The negatives are pages a person reads: body text at three sizes and two leadings, one
    and two columns, three of the product's own colour pairs, a monospaced number table at
    three row counts, and card grids at three densities. The positives are gratings at the
    pair counts and areas either side of the rule, in three orientations, and the mixed cases
    put a grating over a page of text so a picture can hold both.
    """
    out: list[Frame] = []

    def add(clip_id, kind, draw, note="", drawn_area=0.0, drawn_pairs=0):
        out.append(Frame(clip_id, kind, draw, note, drawn_area, drawn_pairs))

    pairs_on_text = ((26, 1.55), (26, 1.25), (20, 1.8), (34, 1.4), (16, 2.0), (44, 1.2))
    palettes = (("cream-on-teal", TEAL, CREAM), ("ink-on-saffron", SAFFRON, INK),
                ("cream-on-ink", INK, CREAM))
    for size, leading in pairs_on_text:
        for columns in (1, 2):
            for name, ground, ink in palettes:
                add(
                    f"text-{size}px-{leading}-{columns}col-{name}",
                    "text",
                    lambda s=size, ld=leading, c=columns, g=ground, i=ink: text_page(s, ld, c, g, i),
                    note=f"{size} px body text, {leading} leading, {columns} column(s), {name}",
                )
    for size, leading in ((26, 1.55), (20, 1.8)):
        for name, ground, ink in palettes[:2]:
            add(
                f"text-serif-{size}px-{leading}-{name}",
                "text",
                lambda s=size, ld=leading, g=ground, i=ink: text_page(s, ld, 1, g, i, "DejaVuSerif.ttf"),
                note=f"{size} px serif body text, {name}",
            )
    # The type this product sets, at the size it is drawn, in the colours it is drawn in.
    # Every combination, because the question is whether any surface we ship reads as a
    # pattern and a sample of them cannot answer that.
    roles: dict[int, list[str]] = {}
    for surface, sizes in (("app", APP_TYPE_PX), ("report", REPORT_TYPE_PX)):
        for role, size in sizes.items():
            roles.setdefault(size, []).append(f"{surface} {role}")
    for size in sorted(roles):
        who = " and ".join(roles[size])
        for name, ground, ink in SHIPPED_PAIRS:
            add(
                f"shipped-{size}px-{name}",
                "text",
                lambda s=size, g=ground, i=ink: text_page(s, 1.45, 1, g, i),
                note=f"{who} at {size} px on a 1280 wide display, {name}",
            )
    # The leading a paragraph is set at is the thing the line rhythm is made of, so the
    # shipped body sizes are also drawn at the tightest and loosest leading either surface
    # uses. Tight leading is the harder case and it is the one that was failing.
    for surface, size in (("app", APP_TYPE_PX["body"]), ("report", REPORT_TYPE_PX["body"])):
        for leading in (1.2, 1.35, 1.6, 1.9):
            add(
                f"shipped-{surface}-body-{size}px-leading-{leading}",
                "text",
                lambda s=size, ld=leading: text_page(s, ld, 1, TEAL, CREAM),
                note=f"{surface} body at {size} px, {leading} leading, cream on teal",
            )
    # 26 px at 1.55 cream on teal, which is what the report page sets its body at, is
    # already in the generic sweep above as text-26px-1.55-1col-cream-on-teal. It is not
    # added again here: a suite that draws the same picture twice counts one case as two.
    for rows in (10, 16, 24):
        for name, ground, ink in palettes[:2]:
            add(
                f"table-{rows}rows-{name}",
                "text",
                lambda r=rows, g=ground, i=ink: number_table(r, max(12, 520 // r), g, i),
                note=f"monospaced number table, {rows} rows, {name}",
            )
    for across, down in ((3, 2), (4, 3), (6, 4), (5, 2)):
        for ground, card, label in ((TEAL, INK, CREAM), (INK, TEAL, CREAM), (TEAL, SAFFRON, INK)):
            add(
                f"cards-{across}x{down}-{ground[0]}{card[0]}",
                "ui",
                lambda a=across, d=down, g=ground, c=card, lb=label: card_grid(a, d, g, c, lb),
                note=f"{across} by {down} card grid",
            )

    for orientation in ("vertical", "horizontal", "diagonal"):
        for pairs in (6, 8, 12, 20, 32):
            for area in (0.30, 0.50, 0.80):
                add(
                    f"grating-{orientation}-{pairs}pairs-{int(area * 100)}pct",
                    "grating",
                    lambda o=orientation, p=pairs, a=area: grating(p, a, o),
                    note=f"{pairs} pair {orientation} grating over {area:.0%} of the picture",
                    drawn_area=area, drawn_pairs=pairs,
                )
    for orientation in ("vertical", "horizontal", "diagonal"):
        for pairs in (2, 3, 4, 5):
            add(
                f"under-count-{orientation}-{pairs}pairs-80pct",
                "grating",
                lambda o=orientation, p=pairs: grating(p, 0.80, o),
                note=f"{pairs} pairs, which is not more than five, over 80% of the picture",
                drawn_area=0.80, drawn_pairs=pairs,
            )
    for orientation in ("vertical", "horizontal"):
        for pairs in (8, 16):
            for area in (0.30, 0.60):
                add(
                    f"mixed-{orientation}-{pairs}pairs-{int(area * 100)}pct",
                    "mixed",
                    lambda o=orientation, p=pairs, a=area: grating(p, a, o, over_text=True),
                    note=f"{pairs} pair {orientation} grating over {area:.0%} of a page of text",
                    drawn_area=area, drawn_pairs=pairs,
                )
    return out
