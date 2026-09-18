#!/usr/bin/env python3
"""List every file a container build would send to the docker daemon.

    make image-context

Why this exists: the build context is the one place where a file nobody meant
to ship can arrive without anybody typing its name. `.dockerignore` at the root
of this repository is an allowlist for that reason, and this is how you read it
without a docker daemon, without a network, and without waiting for a build.

It is a reimplementation of docker's matcher, not docker's matcher. The rules it
keeps are the ones docker documents: patterns are matched against the path
relative to the context root, `*` does not cross a directory separator, `**`
does, a leading `!` puts a file back, and the last pattern that matches wins.
Treat a surprise here as a reason to look, not as proof either way. What is
proof is the test that reads .dockerignore itself, in
pipeline/tests/test_infra_ingest.py.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ALWAYS_SKIP = {".git"}


def compile_pattern(pattern: str) -> re.Pattern[str]:
    """Turn one .dockerignore line into a regular expression.

    fnmatch.translate is close but lets `*` cross a separator, which docker does
    not. The pieces between separators are translated one at a time instead, and
    a `**` piece becomes the one thing that may cross.
    """
    pieces = []
    for piece in pattern.strip("/").split("/"):
        if piece == "**":
            pieces.append(".*")
        else:
            translated = fnmatch.translate(piece)
            # fnmatch wraps its output; take the middle and forbid separators.
            translated = translated.removeprefix("(?s:").removesuffix(")\\Z")
            pieces.append(translated.replace(".*", "[^/]*").replace(".", "[^/]", 0))
    body = "/".join(pieces)
    # A directory pattern also matches everything under it.
    return re.compile(rf"(?s:{body})(/.*)?\Z")


def read_rules(path: Path) -> list[tuple[bool, re.Pattern[str], str]]:
    rules: list[tuple[bool, re.Pattern[str], str]] = []
    if not path.exists():
        return rules
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        negated = stripped.startswith("!")
        if negated:
            stripped = stripped[1:].strip()
        rules.append((negated, compile_pattern(stripped), stripped))
    return rules


def included(relative: str, rules: list[tuple[bool, re.Pattern[str], str]]) -> bool:
    """Docker's rule: the last pattern that matches decides."""
    verdict = True
    for negated, pattern, _ in rules:
        if pattern.match(relative):
            verdict = negated
    return verdict


def walk(root: Path, rules) -> list[Path]:
    """Every included file, pruning directories nothing can rescue.

    Pruning matters more than it looks: without it this walks node_modules and
    .venv, which is a hundred thousand files nobody is going to read.
    """
    negations = [text for negated, _, text in rules if negated]
    kept: list[Path] = []

    def keeps_looking(relative: str) -> bool:
        # Descend into an excluded directory only if some !pattern points inside
        # it, which is the only way a file under it could come back.
        return any(text.rstrip("/").startswith(relative) for text in negations)

    def descend(directory: Path) -> None:
        for path in sorted(directory.iterdir()):
            if path.name in ALWAYS_SKIP or path.is_symlink():
                continue
            relative = path.relative_to(root).as_posix()
            if path.is_dir():
                if included(relative, rules) or keeps_looking(relative):
                    descend(path)
            elif path.is_file() and included(relative, rules):
                kept.append(path)

    descend(root)
    return kept


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO))
    parser.add_argument("--quiet", action="store_true", help="totals only")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    rules = read_rules(root / ".dockerignore")
    if not rules:
        print("there is no .dockerignore, so the whole tree would be sent", file=sys.stderr)
        return 1

    kept = walk(root, rules)
    total = sum(path.stat().st_size for path in kept)
    if not args.quiet:
        for path in kept:
            print(f"  {path.relative_to(root).as_posix()}")
        print()
    print(f"{len(kept)} file(s), {total / 1024:.0f} kB would be sent to the docker daemon.")

    # The point of the allowlist: say plainly that none of these are in it.
    for forbidden in ("media/", "results/", "app/", ".venv/", "docs/"):
        offending = [p for p in kept if p.relative_to(root).as_posix().startswith(forbidden)]
        print(f"  from {forbidden:<10} {len(offending)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
