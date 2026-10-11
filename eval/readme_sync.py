"""Keep every published number tied to a file in results/.

The rule for this project is that any number in the README, the Devpost text
or the video comes from results/*.json, and that CI fails if a document drifts
away from what was measured. The head-start kits were meant to bring
evkit.readme_sync for this. They were never delivered, so this is our own, and
it does the same job.

Mark a number in any markdown file like this:

    the app used <!--n results/vvd_smoke.json:peak_pss_kb -->353178<!--/n--> kB

The part after the file name is a dotted path into the JSON, so
`device.build` reaches into an object and `segments.0.start_ms` reaches into a
list.

    python3 eval/readme_sync.py            rewrite the numbers in place
    python3 eval/readme_sync.py --check    fail if any of them has drifted

A marker pointing at a file or key that does not exist is an error in both
modes, because a number nobody can trace is worse than no number.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The dotted path may contain spaces, because a JSON key can: results/screening.json
# has keys like "Blender open movies" and "NASA SVS 5011" under per_source. An earlier
# version of this pattern ended the path at the first space, so fifteen markers in the
# README matched nothing and were skipped without a word. They happened to be right,
# which is worse: the guard would not have noticed them going wrong.
MARKER = re.compile(
    r"<!--n\s+(?P<source>[^\s:]+):(?P<path>[^\n]+?)\s*-->(?P<value>.*?)<!--/n-->",
    re.DOTALL,
)

# Every way of opening a marker, however badly written. Anything this finds that MARKER
# does not is a marker nobody is checking, and this script refuses to be quiet about it.
ANY_MARKER_OPENING = re.compile(r"<!--n\b.*?-->", re.DOTALL)

# "eval" covers the evaluation lane's own write-ups, including eval/harness_runs/README.md,
# so every number in them is checked by the same CI step as the README.
DEFAULT_TARGETS = ["README.md", "WRITEUP.md", "CHANGELOG.md", "CONTRIBUTING.md", "docs", "eval"]


def resolve(data: object, dotted: str) -> object:
    current = data
    for part in dotted.split("."):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as error:
                raise KeyError(f"{dotted}: {error}") from error
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(dotted)
            current = current[part]
        else:
            raise KeyError(dotted)
    return current


def render(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        # Keep it readable: no trailing zeros, no scientific notation.
        return f"{value:.6g}"
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


def markdown_files(targets: list[str]) -> list[Path]:
    """Every markdown file under the targets, each one once.

    Deduplicated because a file and a directory that contains it can both be named, and
    checking one file twice would count its numbers twice.
    """
    files: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        path = REPO / target
        candidates = sorted(path.rglob("*.md")) if path.is_dir() else [path] if path.is_file() else []
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail on drift instead of rewriting"
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="markdown files or directories to scan",
    )
    args = parser.parse_args()

    cache: dict[str, object] = {}
    problems: list[str] = []
    rewritten = 0
    checked = 0

    for file in markdown_files(args.targets):
        text = file.read_text(encoding="utf-8")
        changed = False

        def replace(match: re.Match) -> str:
            nonlocal changed, checked
            checked += 1
            source = match.group("source")
            dotted = match.group("path")
            shown = match.group("value")
            relative = file.relative_to(REPO)

            if source not in cache:
                source_path = REPO / source
                if not source_path.exists():
                    problems.append(f"{relative}: {source} does not exist")
                    return match.group(0)
                cache[source] = json.loads(source_path.read_text())

            try:
                expected = render(resolve(cache[source], dotted))
            except KeyError:
                problems.append(f"{relative}: {source} has no key {dotted}")
                return match.group(0)

            if expected != shown:
                if args.check:
                    problems.append(
                        f"{relative}: {source}:{dotted} says {expected!r}, "
                        f"the document says {shown!r}"
                    )
                else:
                    changed = True
                    return f"<!--n {source}:{dotted} -->{expected}<!--/n-->"
            return match.group(0)

        updated = MARKER.sub(replace, text)

        # A marker this script cannot parse is a number nobody is checking, and the
        # README says every number on the page is checked. So say so and fail, rather
        # than walking past it.
        parsed = {match.group(0) for match in MARKER.finditer(text)}
        for opening in ANY_MARKER_OPENING.finditer(text):
            if not any(opening.group(0) in whole for whole in parsed):
                problems.append(
                    f"{file.relative_to(REPO)}: cannot parse the marker "
                    f"{opening.group(0)!r}, so nothing checks the number inside it"
                )

        if changed and not args.check:
            file.write_text(updated, encoding="utf-8")
            rewritten += 1

    if problems:
        for problem in problems:
            print(f"drift: {problem}", file=sys.stderr)
        print(f"\n{len(problems)} problem(s) in {checked} marked number(s)", file=sys.stderr)
        return 1

    if args.check:
        print(f"{checked} published number(s) match results/")
    else:
        print(f"{checked} published number(s) checked, {rewritten} file(s) rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
