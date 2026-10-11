#!/usr/bin/env python3
"""Refuse the two things the style rule forbids, in what this project wrote.

CLAUDE.md: no em dashes or en dashes anywhere, in docs, UI text, code comments
or commit messages, and never the words "genuinely", "honestly" or
"straightforward". Four jest tests hold the app's own copy to that, and
nothing held the rest of the repository to it until Oct 11, 2026, when two
dashes in a design brief had sat on a green build for a day.

    python3 eval/style_check.py            scan every tracked text file, exit 1 on a hit
    python3 eval/style_check.py --staged   the files staged for the next commit only

What it reads: tracked files by extension (Markdown, Python, TypeScript,
JavaScript, TOML, YAML, CSV, shell, plain text) plus the Makefile. What it
leaves alone, each for a reason: app/test, where four tests spell the rule
out as a regular expression; app/src/w3cmedia and app/shaka-setup, which are
Amazon's files with Amazon's notices; app/vendor, other people's code; the
licence texts, quoted verbatim; and the one line in CLAUDE.md and
docs/BUILD_PROMPT.md that states the rule, which has to name the words it
bans. A line that names all three banned words is taken to be that rule.

Commit messages are not read here. The hook in scripts/hooks/ is the place
for that, and this script's `--text` flag reads one message from stdin so
the hook can share the rule.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

DASHES = re.compile("[—–]")
WORDS = re.compile(r"\b(genuinely|honestly|straightforward)\b", re.IGNORECASE)
RULE_STATEMENT = ("genuinely", "honestly", "straightforward")

EXTENSIONS = {
    ".md", ".py", ".ts", ".tsx", ".js", ".mjs", ".cjs",
    ".toml", ".yml", ".yaml", ".csv", ".sh", ".txt",
}
NAMES = {"Makefile", "NOTICE"}
EXCLUDED_PREFIXES = (
    "app/test/",
    "app/src/w3cmedia/",
    "app/shaka-setup/",
    "app/vendor/",
    "hook/vendor/",
    "docs/design/assets/",
)
EXCLUDED_BASENAMES = {"LICENSE", "LICENSE-Inter", "Inter-LICENSE.txt", "LICENSE.txt"}


def tracked_files(staged: bool = False) -> list[str]:
    command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else ["git", "ls-files"]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=REPO, check=True)
    return [line for line in completed.stdout.splitlines() if line]


def in_scope(relative: str) -> bool:
    if relative.startswith(EXCLUDED_PREFIXES):
        return False
    path = Path(relative)
    if path.name in EXCLUDED_BASENAMES or path.name.startswith("LICENSE"):
        return False
    return path.suffix in EXTENSIONS or path.name in NAMES


def violations(text: str, where: str) -> list[str]:
    """Every line of `text` that breaks the rule, as "where:line: what"."""
    found: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if all(word in lowered for word in RULE_STATEMENT):
            continue
        if DASHES.search(line):
            found.append(f"{where}:{number}: em or en dash")
        match = WORDS.search(line)
        if match:
            found.append(f"{where}:{number}: the word {match.group(1)!r}")
    return found


def scan(files: list[str]) -> list[str]:
    found: list[str] = []
    for relative in files:
        if not in_scope(relative):
            continue
        path = REPO / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found.extend(violations(text, relative))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--staged", action="store_true", help="only the files staged for commit")
    parser.add_argument("--text", action="store_true", help="read one text, such as a commit message, from stdin")
    args = parser.parse_args(argv)

    if args.text:
        found = violations(sys.stdin.read(), "stdin")
    else:
        found = scan(tracked_files(staged=args.staged))

    for line in found:
        print(line)
    if found:
        print(f"\n{len(found)} line(s) break the style rule in CLAUDE.md: no em or en dashes, and none of the three words.")
        return 1
    print("style: no dashes and none of the three words in what we wrote")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
