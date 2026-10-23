"""Every relative link in the repository's Markdown has to land somewhere.

A reader who follows a link from the README into the docs and finds nothing
stops trusting the rest. The documents here move often and link to each other
by path and by heading, so this reads every tracked Markdown file, follows each
relative link to a file and, for a link into a Markdown file with a heading
anchor, checks that the heading still exists under GitHub's anchor rules.

Links to the web, line links into source (#L123, which test_doc_line_links.py
checks against the symbol beside them) and anything inside code are left out.

Seen to fail on purpose, Oct 11 2026: a link to a file that does not exist and
a link to a heading that does not exist each turned the repository check red,
and the unit cases below keep both failure modes pinned.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parents[2]

# [text](target) and ![alt](target), with an optional "title".
LINK = re.compile(r"!?\[(?:[^\]\n]|\](?!\())*\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"`[^`\n]*`")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(?P<text>.*?)\s*#*\s*$")
HTML_ANCHOR = re.compile(r"<a\s+(?:name|id)=\"([^\"]+)\"")


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"<[^>]+>", "", heading).strip().lower().replace("`", "")
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def outside_code(text: str):
    """Yield (line number, line) for lines outside fenced code, with code spans removed."""
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            yield number, CODE_SPAN.sub("", line)


def anchors(text: str) -> set[str]:
    """Every anchor a Markdown file offers, with GitHub's -1, -2 suffixes for repeats."""
    found: set[str] = set()
    seen: dict[str, int] = {}
    for _, line in outside_code(text):
        match = HEADING.match(line)
        if match:
            base = slug(match.group("text"))
            count = seen.get(base, 0)
            seen[base] = count + 1
            found.add(base if count == 0 else f"{base}-{count}")
        found.update(HTML_ANCHOR.findall(line))
    return found


def broken_links(source: Path, text: str, root: Path) -> list[str]:
    """What is wrong with each relative link in one document, as readable lines."""
    problems: list[str] = []
    cache: dict[Path, set[str]] = {}
    for number, line in outside_code(text):
        for match in LINK.finditer(line):
            target = unquote(match.group("target"))
            if SCHEME.match(target) or target.startswith("//"):
                continue
            path, _, anchor = target.partition("#")
            resolved = (source.parent / path).resolve() if path else source.resolve()
            where = f"{source.relative_to(root)}:{number}: {target}"
            if not resolved.is_relative_to(root.resolve()):
                problems.append(f"{where} points outside the repository")
                continue
            if path and not resolved.exists():
                problems.append(f"{where} names a file that does not exist")
                continue
            if anchor and not re.fullmatch(r"L\d+(-L\d+)?", anchor) and resolved.suffix == ".md" and resolved.is_file():
                if resolved not in cache:
                    cache[resolved] = anchors(resolved.read_text(errors="replace"))
                if anchor.lower() not in cache[resolved]:
                    problems.append(f"{where} names a heading that does not exist")
    return problems


def tracked_markdown() -> list[Path]:
    listed = subprocess.run(["git", "ls-files", "*.md"], cwd=REPO, capture_output=True, text=True, check=True)
    return [REPO / name for name in listed.stdout.splitlines() if (REPO / name).is_file()]


def test_every_relative_link_in_the_repository_resolves() -> None:
    problems: list[str] = []
    for document in tracked_markdown():
        problems += broken_links(document, document.read_text(errors="replace"), REPO)
    assert not problems, "broken links:\n" + "\n".join(problems)


def test_a_link_to_a_missing_file_is_caught(tmp_path: Path) -> None:
    page = tmp_path / "page.md"
    page.write_text("See [the plan](docs/PLAN.md).\n")
    assert broken_links(page, page.read_text(), tmp_path) == [
        "page.md:1: docs/PLAN.md names a file that does not exist"
    ]


def test_a_link_to_a_missing_heading_is_caught_and_a_present_one_passes(tmp_path: Path) -> None:
    (tmp_path / "other.md").write_text("# Other\n\n## What has never been run\n\n## Limits\n\n## Limits\n")
    page = tmp_path / "page.md"
    page.write_text(
        "[ok](other.md#what-has-never-been-run) [repeat](other.md#limits-1) "
        "[gone](other.md#what-was-run) [self](#nowhere)\n"
    )
    assert broken_links(page, page.read_text(), tmp_path) == [
        "page.md:1: other.md#what-was-run names a heading that does not exist",
        "page.md:1: #nowhere names a heading that does not exist",
    ]


def test_web_links_line_links_and_code_are_left_alone(tmp_path: Path) -> None:
    (tmp_path / "src.ts").write_text("x\n")
    page = tmp_path / "page.md"
    page.write_text(
        "[web](https://example.com/missing) [mail](mailto:a@b.c) [line](src.ts#L1)\n"
        "`[span](missing.md)`\n"
        "```\n[fenced](missing.md)\n```\n"
    )
    assert broken_links(page, page.read_text(), tmp_path) == []


def test_github_anchor_rules() -> None:
    assert slug("Oct 11, later still: the cover proof") == "oct-11-later-still-the-cover-proof"
    assert slug("`make` targets and 5% of it") == "make-targets-and-5-of-it"
    assert anchors("# A\n## A\n## A\n") == {"a", "a-1", "a-2"}
