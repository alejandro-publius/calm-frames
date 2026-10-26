"""The design page, tokens.json and the app's palette say the same thing.

Until Oct 11, 2026 the palette was written down three ways that disagreed:
`CALM_COLORS` in app/src/calmframes/calmStyles.ts held thirteen colours,
docs/design/tokens.json held seven (one of them a second teal that appears
nowhere in the app) with contrast numbers nothing checked, and the brand page
held nine. docs/design/README.md is now the one design page, and this test
holds it, tokens.json and the code to each other:

- the palette table on the page and the colours in tokens.json are exactly
  `CALM_COLORS`, the same names and the same hex values;
- every contrast ratio the page or tokens.json lists is recomputed here from
  the hex values with WCAG 2.2 relative luminance, as quoted in
  flashmap/docs/SPEC_SOURCES.md section 3, and truncated to two decimals the
  way `roundRatio` in app/src/calmframes/uiContrast.ts truncates;
- every text pair the page lists clears 4.5 to 1 and every focus ring pair
  clears 3 to 1, the floors calmStyles.ts names;
- the type roles, spacing, focus width and floors on the page and in
  tokens.json are the ones calmStyles.ts defines;
- the original logo palette is preserved independently of the approved UI
  palette, and the brand page records its original roles.

Code is the source of truth. When this fails, change the page and
tokens.json to match calmStyles.ts, not the other way round.

Seen to fail on purpose, Oct 11, 2026, each change made, run and restored:

- `BORDER` in the page's palette table changed from #66A0B4 to #66A0B5: the
  palette test went red naming BORDER;
- the TEXT_DIM on SURFACE_FOCUSED ratio on the page changed from 5.92 to
  5.93: the ratio test and the tokens.json test went red;
- `INK` in calmStyles.ts temporarily lightened to #5A7380, which puts ink on
  saffron at 2.42 to 1 and cream on ink at 4.11: nine tests went red, among
  them the palette, tokens.json, both ratio, both floor and the logo tests;
- `textOnSurface` in tokens.json changed to 9.10: the tokens.json test went
  red;
- `SAFFD` in the brand page's logo table mapped to FOCUS_RING: the logo test
  went red.

The three negative controls at the bottom keep the comparisons honest on
every run, by feeding the same helpers an altered input and expecting a
complaint.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
STYLES = REPO / "app/src/calmframes/calmStyles.ts"
PAGE = REPO / "docs/design/README.md"
TOKENS = REPO / "docs/design/tokens.json"
LOGO = REPO / "app/tools/brand/make_logo.py"
BRAND = REPO / "docs/brand/README.md"

# The floors the brief and calmStyles.ts set. The code's own constants are
# read below and must not be looser than these.
TEXT_FLOOR = 4.5
RING_FLOOR = 3.0

# WCAG 2.2's sRGB break point, as quoted in flashmap/docs/SPEC_SOURCES.md.
# uiContrast.ts uses the pre-2021 0.03928, which WCAG's Note 2 says makes no
# practical difference; test_both_break_points_agree holds that to be true.
BREAK_POINT = 0.04045
OLD_BREAK_POINT = 0.03928

HEX = re.compile(r"#[0-9A-Fa-f]{6}")


# ---------------------------------------------------------------- the code


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", text)


def _object_literal(source: str, name: str) -> str:
    match = re.search(
        rf"export const {name} = \{{(?P<body>.*?)\}} as const;", source, re.DOTALL
    )
    assert match, f"{name} is not an object literal in {STYLES.relative_to(REPO)}"
    return _strip_comments(match.group("body"))


def _number_constant(source: str, name: str) -> float:
    match = re.search(rf"export const {name} = ([0-9.]+);", source)
    assert match, f"{name} is not a plain number in {STYLES.relative_to(REPO)}"
    return float(match.group(1))


def parse_calm_colors(source: str) -> dict[str, str]:
    """CALM_COLORS as {NAME: '#RRGGBB'}, refusing any entry it cannot read.

    Since Oct 16 calmStyles.ts names the palette COASTAL_COLORS and makes
    CALM_COLORS an alias of it, so the alias is followed, and nothing else.
    """
    alias = re.search(r"export const CALM_COLORS = ([A-Z_]+);", source)
    body = _object_literal(source, alias.group(1) if alias else "CALM_COLORS")
    entries = re.findall(r"([A-Z_]+)\s*:", body)
    colours = dict(re.findall(r"([A-Z_]+)\s*:\s*'(#[0-9A-Fa-f]{6})'", body))
    unread = sorted(set(entries) - set(colours))
    assert not unread, (
        f"CALM_COLORS entries this test cannot read as #RRGGBB: {unread}. "
        "Teach the parser, do not let a colour slip past it."
    )
    assert len(entries) == len(set(entries)), "CALM_COLORS repeats a name"
    return {name: value.upper() for name, value in colours.items()}


@pytest.fixture(scope="module")
def source() -> str:
    return STYLES.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def calm_colors(source: str) -> dict[str, str]:
    colours = parse_calm_colors(source)
    assert colours, "found no colours in CALM_COLORS"
    return colours


@pytest.fixture(scope="module")
def calm_text(source: str) -> dict[str, tuple[str, int, int]]:
    """CALM_TEXT as {role: (face, size, line height)}."""
    fonts = dict(re.findall(r"(\w+)\s*:\s*'(\w+)'", _object_literal(source, "CALM_FONT")))
    body = _object_literal(source, "CALM_TEXT")
    roles = re.findall(r"^\s*(\w+)\s*:", body, re.MULTILINE)
    found = {
        role: (fonts[face], int(size), int(height))
        for role, size, height, face in re.findall(
            r"(\w+)\s*:\s*typography\((\d+),\s*(\d+),\s*CALM_FONT\.(\w+)\)", body
        )
    }
    assert sorted(found) == sorted(roles), "a CALM_TEXT role is not a typography() call"
    return found


@pytest.fixture(scope="module")
def calm_space(source: str) -> dict[str, int]:
    body = _object_literal(source, "CALM_SPACE")
    return {name: int(value) for name, value in re.findall(r"([A-Z_]+)\s*:\s*(\d+)", body)}


# ---------------------------------------------------------------- the page


def section(markdown: str, heading: str) -> str:
    """The text under `heading`, up to the next heading at its level or above."""
    lines = markdown.splitlines()
    level = len(heading) - len(heading.lstrip("#"))
    try:
        start = lines.index(heading)
    except ValueError:
        pytest.fail(f"{PAGE.relative_to(REPO)} has no '{heading}' heading")
    body: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.lstrip("#")
        if line.startswith("#") and stripped.startswith(" ") and len(line) - len(stripped) <= level:
            break
        body.append(line)
    return "\n".join(body)


def table(text: str) -> list[list[str]]:
    """The body rows of the first Markdown table in `text`, cells unquoted."""
    rows = [line for line in text.splitlines() if line.startswith("|")]
    assert len(rows) >= 3, "expected a table with a header, a rule and rows"
    body = []
    for row in rows[2:]:
        cells = [cell.strip().strip("`").strip() for cell in row.strip().strip("|").split("|")]
        body.append(cells)
    return body


def page_palette(markdown: str) -> list[list[str]]:
    return table(section(markdown, "## Palette"))


@pytest.fixture(scope="module")
def page() -> str:
    return PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def tokens() -> dict:
    return json.loads(TOKENS.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- arithmetic


def _channel(value: int, break_point: float) -> float:
    unit = value / 255
    return unit / 12.92 if unit <= break_point else ((unit + 0.055) / 1.055) ** 2.4


def relative_luminance(colour: str, break_point: float = BREAK_POINT) -> float:
    digits = colour.lstrip("#")
    r, g, b = (int(digits[i : i + 2], 16) for i in (0, 2, 4))
    return (
        0.2126 * _channel(r, break_point)
        + 0.7152 * _channel(g, break_point)
        + 0.0722 * _channel(b, break_point)
    )


def contrast(one: str, other: str, break_point: float = BREAK_POINT) -> float:
    first = relative_luminance(one, break_point)
    second = relative_luminance(other, break_point)
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


def truncated(ratio: float) -> str:
    """Two decimals, never rounded up: Math.floor(ratio * 100) / 100 in uiContrast.ts."""
    return f"{math.floor(ratio * 100) / 100:.2f}"


def camel(name: str) -> str:
    head, *rest = name.lower().split("_")
    return head + "".join(part.capitalize() for part in rest)


def pair_key(foreground: str, background: str) -> str:
    return camel(foreground) + "On" + camel(background)[0].upper() + camel(background)[1:]


def ratio_rows(markdown: str, heading: str) -> list[tuple[str, str, str]]:
    rows = table(section(markdown, heading))
    assert rows, f"no pairs under {heading}"
    return [(row[0], row[1], row[2]) for row in rows]


def text_pairs(markdown: str) -> list[tuple[str, str, str]]:
    return ratio_rows(markdown, "### Text on background")


def ring_pairs(markdown: str) -> list[tuple[str, str, str]]:
    return ratio_rows(markdown, "### Focus ring")


# ---------------------------------------------------------------- the palette


def palette_mismatches(markdown: str, colours: dict[str, str]) -> list[str]:
    """What differs between the page's palette table and `colours`, as sentences."""
    rows = page_palette(markdown)
    problems = []
    names = [row[0] for row in rows]
    if len(names) != len(set(names)):
        problems.append("the palette table repeats a token")
    on_page = {row[0]: row[2].upper() for row in rows}
    for name in sorted(set(on_page) | set(colours)):
        if on_page.get(name) != colours.get(name):
            problems.append(
                f"{name}: the page says {on_page.get(name, 'nothing')}, "
                f"calmStyles.ts says {colours.get(name, 'nothing')}"
            )
    return problems


def ratio_mismatches(rows: list[tuple[str, str, str]], colours: dict[str, str]) -> list[str]:
    """Every listed ratio that is not the one the two colours give."""
    problems = []
    for one, other, listed in rows:
        if one not in colours or other not in colours:
            problems.append(f"{one} and {other}: not both CALM_COLORS names")
            continue
        computed = truncated(contrast(colours[one], colours[other]))
        if listed != computed:
            problems.append(f"{one} with {other}: the page says {listed}, the colours give {computed}")
    return problems


def floor_failures(rows: list[tuple[str, str, str]], colours: dict[str, str], floor: float) -> list[str]:
    """Every listed pair under `floor`, by its computed ratio or its listed one."""
    problems = []
    for one, other, listed in rows:
        ratio = contrast(colours[one], colours[other])
        if ratio < floor or float(listed) < floor:
            problems.append(f"{one} with {other} is {truncated(ratio)} to 1, under {floor}")
    return problems


def test_the_page_palette_is_calm_colors(page, calm_colors):
    problems = palette_mismatches(page, calm_colors)
    assert not problems, "the palette on docs/design/README.md is not CALM_COLORS: " + "; ".join(problems)


def test_the_page_names_each_tokens_json_key(page):
    for row in page_palette(page):
        assert row[1] == camel(row[0]), f"{row[0]} maps to {camel(row[0])}, the page says {row[1]}"


def test_tokens_json_colours_are_calm_colors(tokens, calm_colors):
    expected = {camel(name): value for name, value in calm_colors.items()}
    actual = {key: value.upper() for key, value in tokens["colors"].items()}
    assert actual == expected, (
        "docs/design/tokens.json colours are not CALM_COLORS. "
        f"Only in tokens.json: {sorted(set(actual.items()) - set(expected.items()))}. "
        f"Only in calmStyles.ts: {sorted(set(expected.items()) - set(actual.items()))}."
    )


def test_tokens_json_says_where_the_truth_is(tokens):
    assert tokens["source"] == "app/src/calmframes/calmStyles.ts"
    assert "calmStyles.ts" in tokens["status"]
    assert "test_design_page.py" in tokens["status"]
    assert "proposed" not in tokens["status"].lower()


# ---------------------------------------------------------------- contrast


def test_every_listed_text_ratio_is_the_computed_one(page, calm_colors):
    problems = ratio_mismatches(text_pairs(page), calm_colors)
    assert not problems, "; ".join(problems)


def test_every_listed_ring_ratio_is_the_computed_one(page, calm_colors):
    problems = ratio_mismatches(ring_pairs(page), calm_colors)
    assert not problems, "; ".join(problems)


def test_every_text_pair_clears_the_text_floor(page, calm_colors, source):
    floor = _number_constant(source, "MINIMUM_TEXT_CONTRAST")
    assert floor >= TEXT_FLOOR, f"MINIMUM_TEXT_CONTRAST is {floor}, looser than {TEXT_FLOOR}"
    problems = floor_failures(text_pairs(page), calm_colors, floor)
    assert not problems, "; ".join(problems)


def test_every_ring_pair_clears_the_focus_floor(page, calm_colors, source):
    floor = _number_constant(source, "MINIMUM_FOCUS_CONTRAST")
    assert floor >= RING_FLOOR, f"MINIMUM_FOCUS_CONTRAST is {floor}, looser than {RING_FLOOR}"
    problems = floor_failures(ring_pairs(page), calm_colors, floor)
    assert not problems, "; ".join(problems)


def test_no_text_is_listed_in_a_colour_the_page_says_carries_none(page):
    for foreground, background, _ in text_pairs(page):
        assert foreground not in {"ACCENT_DARK", "BORDER", "COVER"}, (
            f"{foreground} on {background}: the page says {foreground} never carries text"
        )


def test_tokens_json_ratios_are_the_page_ones(page, tokens, calm_colors):
    measured = tokens["contrastMeasurements"]
    for group, rows in (("text", text_pairs(page)), ("focusRing", ring_pairs(page))):
        expected = {pair_key(a, b): listed for a, b, listed in rows}
        actual = {key: f"{value:.2f}" for key, value in measured[group].items()}
        assert actual == expected, f"tokens.json contrastMeasurements.{group} is not the page's list"
        # The page's ratios are truncated to two decimals; tokens.json has to
        # hold exactly those, not a longer value that happens to print the same.
        for key, value in measured[group].items():
            assert round(value, 2) == value, f"tokens.json {group}.{key} is {value}, not two decimals"
    floors = tokens["contrastFloors"]
    assert floors == {"text": TEXT_FLOOR, "focusRing": RING_FLOOR}


def test_both_break_points_agree(page, calm_colors):
    """The app's 0.03928 and the spec's 0.04045 give the same ratios here.

    For 8-bit colours they always do, because no n/255 falls between them;
    this keeps that true of the listed pairs rather than taking it on trust.
    """
    assert not [n for n in range(256) if OLD_BREAK_POINT < n / 255 <= BREAK_POINT]
    for foreground, background, _ in text_pairs(page) + ring_pairs(page):
        one, other = calm_colors[foreground], calm_colors[background]
        assert truncated(contrast(one, other)) == truncated(contrast(one, other, OLD_BREAK_POINT))


def test_the_arithmetic_matches_the_wcag_examples():
    assert truncated(contrast("#000000", "#FFFFFF")) == "21.00"
    assert truncated(contrast("#777777", "#777777")) == "1.00"
    assert contrast("#102F3A", "#F3E8D3") == pytest.approx(contrast("#F3E8D3", "#102F3A"))


# ---------------------------------------------------------------- type, space, focus


def test_the_type_roles_are_calm_text(page, tokens, calm_text):
    on_page = {}
    for role, face, size_line, _ in table(section(page, "## Type")):
        size, line = (int(part) for part in size_line.split("/"))
        on_page[role] = (face, size, line)
    assert on_page == calm_text, "the type table on the page is not CALM_TEXT"
    in_tokens = {
        role: (spec["face"], spec["fontSize"], spec["lineHeight"])
        for role, spec in tokens["type"].items()
    }
    assert in_tokens == calm_text, "tokens.json type is not CALM_TEXT"


def test_every_face_is_drawn_at_400(source, tokens):
    match = re.search(r"const typography = .*?\}\);", source, re.DOTALL)
    assert match and "fontWeight: '400'" in match.group(0)
    assert tokens["font"]["fontWeight"] == "400"
    fonts = dict(re.findall(r"(\w+)\s*:\s*'(\w+)'", _object_literal(source, "CALM_FONT")))
    assert tokens["font"]["faces"] == fonts


def test_the_spacing_is_calm_space(page, tokens, calm_space):
    on_page = {name: int(units) for name, units, _ in table(section(page, "## Spacing and layout"))}
    assert on_page == calm_space, "the spacing table on the page is not CALM_SPACE"
    assert tokens["spacing"] == {camel(name): value for name, value in calm_space.items()}
    assert tokens["canvas"]["safeX"] == calm_space["SAFE_X"]
    assert tokens["canvas"]["safeY"] == calm_space["SAFE_Y"]


def test_focus_width_and_text_floor_agree(page, tokens, source):
    width = _number_constant(source, "FOCUS_RING_WIDTH")
    smallest = _number_constant(source, "MINIMUM_TEXT_SIZE")
    assert tokens["focus"]["width"] == width
    assert tokens["font"]["minimumSize"] == smallest
    # The page names these constants in prose; the number beside each name
    # has to be the constant's.
    for pattern, value in (
        (r"`FOCUS_RING_WIDTH` border, (\d+) units", width),
        (r"`MINIMUM_TEXT_SIZE`, (\d+) units", smallest),
        (r"`MINIMUM_TEXT_CONTRAST` is ([0-9.]+) to 1", _number_constant(source, "MINIMUM_TEXT_CONTRAST")),
        (r"`MINIMUM_FOCUS_CONTRAST` is ([0-9.]+) to 1", _number_constant(source, "MINIMUM_FOCUS_CONTRAST")),
    ):
        found = re.findall(pattern, page)
        assert found, f"the page no longer says {pattern!r}; update this test with it"
        assert all(float(one) == value for one in found), (pattern, found, value)


# ---------------------------------------------------------------- the mark and the renders


def test_the_original_logo_palette_is_preserved_independently_of_ui():
    # User-approved UI palette changes must not recolor existing artwork. The
    # one addition is the warm-sand inset border Alex asked for on Oct 14,
    # which maps to no token; anything beyond these six is a recolour.
    original = {"TEAL": ("BACKGROUND", "#102F3A"), "CREAM": ("TEXT", "#F3E8D3"),
                "SAFF": ("FOCUS_RING", "#E6A957"), "SAFFD": ("ACCENT_DARK", "#B87A2C"),
                "INK": ("INK", "#17323C")}
    added = {"SAND": ("none", "#E5D9BA")}
    logo = dict(re.findall(r'([A-Z]+)="(#[0-9A-Fa-f]{6})"', LOGO.read_text(encoding="utf-8")))
    assert logo == {name: value for name, (_, value) in {**original, **added}.items()}
    rows = table(section(BRAND.read_text(encoding="utf-8"), "## The palette"))
    assert {row[0]: (row[1], row[2].upper()) for row in rows} == {**original, **added}


def test_every_render_the_page_shows_is_there(page):
    images = re.findall(r"\]\(((?:polish|seamless)/[^)\s]+\.png)\)", page)
    assert images, "the page shows no renders"
    missing = [image for image in images if not (PAGE.parent / image).is_file()]
    assert not missing, f"the page points at renders that are not there: {missing}"


# ---------------------------------------------------------------- negative controls


def test_the_palette_check_notices_one_changed_hex(page, calm_colors):
    """Kept in the suite so the comparison cannot quietly become a no-op."""
    border = calm_colors["BORDER"]
    altered = page.replace(f"`{border}`", "`#66A0B5`", 1)
    assert altered != page, "BORDER's hex is not on the page to alter"
    problems = palette_mismatches(altered, calm_colors)
    assert len(problems) == 1 and problems[0].startswith("BORDER:"), problems


def test_the_ratio_check_notices_one_changed_ratio(page, calm_colors):
    rows = text_pairs(page)
    one, other, listed = rows[0]
    altered = [(one, other, f"{float(listed) + 0.01:.2f}")] + rows[1:]
    problems = ratio_mismatches(altered, calm_colors)
    assert len(problems) == 1 and problems[0].startswith(f"{one} with {other}"), problems


def test_the_floor_check_refuses_a_pair_under_the_floor(calm_colors):
    # BORDER is never text: on a focused surface it sits between the two floors,
    # under 4.5 and over 3, so one row tests both. (Until Oct 19 this was
    # TEXT_DISABLED, which the current palette lifts above 4.5.)
    row = ("BORDER", "SURFACE_FOCUSED", truncated(contrast(calm_colors["BORDER"], calm_colors["SURFACE_FOCUSED"])))
    assert ratio_mismatches([row], calm_colors) == []
    assert floor_failures([row], calm_colors, TEXT_FLOOR) != []
    assert floor_failures([row], calm_colors, RING_FLOOR) == []
