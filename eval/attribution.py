#!/usr/bin/env python3
"""One source of truth for who gets credited, feeding the NOTICE and the app's credits screen.

Every clip in `media/LICENSES.csv` came with conditions. Some are the licence itself, some are
extra: the Blender logos are excluded from the Blender Studio licences, Tears of Steel is CC BY
3.0 only while its credit scroll stays in the film, DVIDS needs a non-endorsement notice, NASA
asks to be named as the source without its insignia being used, and a share alike clip makes
anything we publish from it share alike too.

Those conditions have to hold in two places at once: the `NOTICE` file in the repository, and
the credits screen inside the app. Two hand-kept lists would drift, and the one that drifts is
the one nobody is reading. So both are written from the ledger by this script:

    python eval/attribution.py            rewrite NOTICE and app/src/calmframes/credits.ts
    python eval/attribution.py --check     fail if either has drifted from the ledger

The generated part of NOTICE sits between two markers, so the hand-written part above it is
left alone. `credits.ts` is generated whole and says so at the top.

Nothing here decides what a licence means. It reads the ledger's own columns, and where an extra
condition applies it is attached by a rule below that names the ledger text it keys off, so a
new clip with the same licence gets the same condition without anyone remembering to add it.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "media" / "LICENSES.csv"
NOTICE = REPO / "NOTICE"
CREDITS_TS = REPO / "app" / "src" / "calmframes" / "credits.ts"

BEGIN = "<!-- BEGIN media credits, written by eval/attribution.py. Do not edit by hand. -->"
END = "<!-- END media credits -->"

# Titles that no page gives us a name for. Everything on Wikimedia Commons is named by its own
# file page, so the sourced titles and our own assets below need one written down.
# A ledger row that is neither a Commons
# file nor listed here fails the test in eval/tests/test_attribution.py rather than getting an
# invented name off its file name.
TITLES = {
    # Ours, generated rather than sourced. It is in the ledger so that every
    # asset that ships has one row saying where it came from, even when the
    # answer is that we made it and there is nothing to credit.
    "app/assets/raw/sound/calm-chime.mp3": "The Calm Frames chime",
    "app/assets/raw/sound/menu-select.mp3": "The Calm Frames selection sound",
    # Ours too, for the same reason: the story the app ships, and the marker
    # clip the timing harness and the Oct 9 AWS runs used.
    "app/assets/raw/benign-story/harbor.mp4": "Harbor story (benign demo)",
    "media/markers_packed.mp4": "The Calm Frames timing marker clip",
    # The presentation pictures for the shelf and details page are never film
    # frames or signed playback stills.
    "app/assets/image/tv/harbor.png": "Harbor presentation artwork",
    "app/assets/image/tv/harbor-cinematic.png": "Harbor cinematic presentation artwork",
    "app/assets/image/tv/harbor-water.png": "Harbor opening artwork",
    "app/assets/image/tv/harbor-illustrated.png": "Harbor illustrated presentation artwork",
    "app/assets/image/tv/coastal-zen.png": "Coastal presentation artwork",
    'app/assets/raw/prepared-library/51b91d7413c50cc020452d4594a493fbf78e6d1ebac40c8066753b76c776d101/titles/de53dd81f60a44409531ad1ff57ee08fb213d9650b06c92ae1fe88a2cbbb526e/wcag.mp4': "Harbor cinematic story (prepared locally)",
    "app/assets/image/tv/gradient.png": "Calm gradient presentation artwork",
    # The two videos the app ships besides the Harbor story: the bundled calm
    # gradient, and the prepared Harbor rendition kid mode plays. Both are ours.
    "app/assets/raw/offline/calm_gradient.mp4": "The calm gradient (bundled title)",
    "app/assets/raw/prepared-library/89496fc4b45528558ce35ef9140aa659b86a5f84734156098e2f29e312f2c590/titles/4b1d5997c23f181c8ceded5452f18eb39b1dfc9e5bec0e97d6320847ed671d8f/wcag.mp4": "Harbor story (prepared locally)",
    "bbb_720p_surround.mp4": "Big Buck Bunny",
    "sintel_2048_stereo_512kb.mp4": "Sintel",
    "tears_of_steel_720p.mov": "Tears of Steel",
    "nasa_svs_5011_iss_lightning_1080p.mp4": (
        "Lightning seen from the International Space Station, NASA SVS 5011"
    ),
    "dvids_illumination_flares.mp4": "Soldiers Fire Illumination Flares",
    "dvids_fireworks_safety.mp4": "Fireworks Safety",
    "pd1930_frozen_frolics.mp4": "Frozen Frolics (1930)",
    "pd1930_booze_hangs_high.mp4": "The Booze Hangs High (1930)",
}

SHARE_ALIKE = (
    "Share alike. Anything we publish that is made from this clip carries the same licence."
)
BLENDER_LOGOS = (
    "The Blender logos and trademarks are not covered by this licence. They are not used here."
)
CREDIT_SCROLL = (
    "This licence holds only while the credit scroll stays in the film, so the file is kept "
    "whole and the scroll is never cut."
)
DVIDS_NOTICE = (
    "The non-endorsement notice above is required by DVIDS and travels with the clip. Military "
    "insignia, seals and symbols are protected marks and are not used."
)
NASA_NOTICE = (
    "NASA is named as the source. The NASA insignia, logotype and identifiers are not public "
    "domain, they are not used, and nothing here implies NASA endorses this."
)
TELL_THE_AUTHOR = (
    "The author asks to be told if the work is used away from Wikimedia. Tell them before we "
    "publish anything made from it."
)


def rows() -> list[dict]:
    with LEDGER.open(newline="") as handle:
        return list(csv.DictReader(handle))


def used_rows(all_rows: list[dict]) -> list[dict]:
    return [row for row in all_rows if (row.get("sha256") or "").strip()]


def skipped_rows(all_rows: list[dict]) -> list[dict]:
    return [row for row in all_rows if not (row.get("sha256") or "").strip()]


def bare_name(file_name: str) -> str:
    return file_name[len("HAZARD_") :] if file_name.startswith("HAZARD_") else file_name


def commons_title(url: str) -> str | None:
    """The file's own name on Wikimedia Commons, which is the name of the work there."""
    from urllib.parse import unquote  # noqa: PLC0415

    decoded = unquote(url)
    for marker in ("/wiki/File:", "/wiki/File%3A", "File:"):
        if marker in decoded:
            name = decoded.split(marker, 1)[1]
            # The name as Commons holds it, with its underscores read as spaces and its file
            # extension dropped. Nothing else is changed: a credit that tidies up the name of the
            # work is no longer a credit for that work. Hyphens stay, and the house rule about
            # dashes is about en and em dashes, which none of these titles contain.
            return name.rsplit(".", 1)[0].replace("_", " ").strip()
    return None


def title_of(row: dict) -> str | None:
    name = bare_name((row.get("file") or "").strip())
    if name in TITLES:
        return TITLES[name]
    return commons_title(row.get("source_page_url") or "")


def source_label(row: dict) -> str:
    note = row.get("notes") or ""
    if note.startswith("source: "):
        return note[len("source: ") :].split(".")[0].strip()
    return "unknown"


def obligations(row: dict) -> list[str]:
    """The extra conditions on a clip, each keyed off what the ledger already records."""
    out: list[str] = []
    licence = (row.get("license") or "").lower()
    credit = row.get("credit_line") or ""
    note = row.get("notes") or ""
    name = bare_name((row.get("file") or "").strip())

    if "by-sa" in licence:
        out.append(SHARE_ALIKE)
    if "blender" in credit.lower() or source_label(row).startswith("Blender"):
        out.append(BLENDER_LOGOS)
    if name == "tears_of_steel_720p.mov":
        out.append(CREDIT_SCROLL)
    if source_label(row) == "DVIDS":
        out.append(DVIDS_NOTICE)
    if "NASA" in credit:
        out.append(NASA_NOTICE)
    if "notified" in note:
        out.append(TELL_THE_AUTHOR)
    return out


def entries() -> list[dict]:
    """One row per clip we hold, sorted by title, with everything a credit needs."""
    out = []
    for row in used_rows(rows()):
        title = title_of(row)
        if title is None:
            raise SystemExit(
                f"{row['file']}: no title. Add it to TITLES in eval/attribution.py, or give the "
                "row a Wikimedia Commons file page as its source_page_url."
            )
        out.append(
            {
                "title": title,
                "license": (row.get("license") or "").strip(),
                "credit": (row.get("credit_line") or "").strip(),
                "source": (row.get("source_page_url") or "").strip(),
                "collection": source_label(row),
                "obligations": obligations(row),
            }
        )
    return sorted(out, key=lambda entry: entry["title"].lower())


def notice_block() -> str:
    """The generated half of NOTICE."""
    lines = [
        BEGIN,
        "",
        "## Video used to build and measure Calm Frames",
        "",
        "Every clip below was downloaded only after its licence and its credit line were read on",
        "the page linked beside it. The files themselves are not in this repository. What is here",
        "is this list, and the SHA-256 of each file in media/LICENSES.csv.",
        "",
    ]
    for entry in entries():
        lines.append(f"### {entry['title']}")
        lines.append("")
        lines.append(f"- Licence: {entry['license']}")
        lines.append(f"- Credit: {entry['credit']}")
        lines.append(f"- Source: {entry['source']}")
        for condition in entry["obligations"]:
            lines.append(f"- {condition}")
        lines.append("")

    skipped = skipped_rows(rows())
    if skipped:
        lines.append("## Considered and not used")
        lines.append("")
        lines.append(
            "These were looked at and left alone, each for the reason given. Nothing from them "
            "is in this project."
        )
        lines.append("")
        for row in skipped:
            note = (row.get("notes") or "").strip()
            lines.append(f"- {row['source_page_url']}: {note}")
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def build_notice(existing: str) -> str:
    block = notice_block()
    if BEGIN in existing and END in existing:
        head = existing.split(BEGIN)[0]
        tail = existing.split(END, 1)[1]
        return head + block + tail
    return existing.rstrip("\n") + "\n\n" + block + "\n"


def ts_string(value: str) -> str:
    """A TypeScript single quoted string, with nothing in it that could close it early.

    A credit line is a CSV field, so it can legally hold a newline. A raw newline inside a
    single quoted TypeScript string is a syntax error, which would break the app's build rather
    than the credit, so line breaks are escaped rather than dropped.
    """
    escaped = (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\r\n", "\\n")
        .replace("\r", "\\n")
        .replace("\n", "\\n")
    )
    return f"'{escaped}'"


def build_credits_ts() -> str:
    head = '''/**
 * Every video Calm Frames was built and measured with, with its licence and
 * its credit line.
 *
 * GENERATED FILE. Do not edit it by hand. It is written from
 * media/LICENSES.csv by eval/attribution.py, which writes the repository's
 * NOTICE file from the same rows, so the credits on the television and the
 * credits in the repository cannot say different things.
 *
 *     python eval/attribution.py            rewrite both
 *     python eval/attribution.py --check    fail if either has drifted
 *
 * `obligations` is what we have to keep doing to be allowed to use the clip:
 * a share alike licence, the Blender logo exclusion, the Tears of Steel credit
 * scroll, the DVIDS non-endorsement notice, the NASA credit line. The credits
 * screen shows them under the credit rather than tucking them away, because a
 * condition nobody can see is a condition nobody keeps.
 */

export interface CreditEntry {
  /** The name of the work, as the page we took it from names it. */
  title: string;
  /** The licence, exactly as the ledger records it. */
  license: string;
  /** The credit line the source asks for, word for word. */
  credit: string;
  /** The page the licence was read on. */
  source: string;
  /** Which collection it came from, for grouping. */
  collection: string;
  /** What we have to keep doing. Empty for a clip with no extra condition. */
  obligations: string[];
}

export const CREDIT_ENTRIES: CreditEntry[] = [
'''
    body = []
    for entry in entries():
        body.append("  {")
        body.append(f"    title: {ts_string(entry['title'])},")
        body.append(f"    license: {ts_string(entry['license'])},")
        body.append(f"    credit: {ts_string(entry['credit'])},")
        body.append(f"    source: {ts_string(entry['source'])},")
        body.append(f"    collection: {ts_string(entry['collection'])},")
        if entry["obligations"]:
            body.append("    obligations: [")
            for condition in entry["obligations"]:
                body.append(f"      {ts_string(condition)},")
            body.append("    ],")
        else:
            body.append("    obligations: [],")
        body.append("  },")
    tail = "];\n"
    return head + "\n".join(body) + "\n" + tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write. Exit non-zero if NOTICE or credits.ts has drifted from the ledger",
    )
    arguments = parser.parse_args()

    notice = build_notice(NOTICE.read_text())
    credits = build_credits_ts()

    if arguments.check:
        stale = []
        if NOTICE.read_text() != notice:
            stale.append("NOTICE")
        if not CREDITS_TS.is_file() or CREDITS_TS.read_text() != credits:
            stale.append(str(CREDITS_TS.relative_to(REPO)))
        if stale:
            print(
                f"{' and '.join(stale)} no longer match media/LICENSES.csv. "
                "Run `python eval/attribution.py`.",
                file=sys.stderr,
            )
            return 2
        print(f"NOTICE and credits.ts match the ledger: {len(entries())} titles")
        return 0

    NOTICE.write_text(notice)
    CREDITS_TS.parent.mkdir(parents=True, exist_ok=True)
    CREDITS_TS.write_text(credits)
    listed = entries()
    print(f"wrote {NOTICE} and {CREDITS_TS}: {len(listed)} titles")
    with_conditions = sum(1 for entry in listed if entry["obligations"])
    print(f"  {with_conditions} of them carry a condition beyond the licence text")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
