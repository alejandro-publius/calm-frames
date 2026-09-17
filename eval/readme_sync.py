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

MARKER = re.compile(
    r"<!--n\s+(?P<source>[^\s:]+):(?P<path>[^\s]+)\s*-->(?P<value>.*?)<!--/n-->",
    re.DOTALL,
)

DEFAULT_TARGETS = ["README.md", "docs", "eval/harness_runs/README.md"]


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
    files: list[Path] = []
    for target in targets:
        path = REPO / target
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.is_file():
            files.append(path)
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
