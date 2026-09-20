#!/usr/bin/env python3
"""One baseline directory, one tool version.

A baseline table is a comparison. It is only a comparison if every row in it
came off the same build of the same tool, and nothing in the repository used to
enforce that. What made it worth enforcing: building EA IRIS pulled in
Homebrew's opencv@4, which upgraded ffmpeg from 8.1.2 to 9.0.1 underneath us
(docs/ENVIRONMENT.md, "The three ffmpegs"). Re-running one clip after that would
have left a directory holding two versions and a table nobody could read, with
nothing saying which row came from which.

Every baseline report carries the build string it ran under in `tool_version`.
This walks the report directories and fails if one of them holds more than one.

    python eval/baseline_versions.py            # check, exit 1 on a mixed set
    python eval/baseline_versions.py --list     # print what each directory holds

It reads reports and never runs a tool, so it is cheap enough for CI and works
on a machine with no media.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINES = REPO / "results" / "baselines"


def reports(root: Path) -> dict[Path, dict[str, list[str]]]:
    """Map each baseline directory to {tool_version: [file names]}.

    Files with no `tool_version` are not reports: `iris_failures.json` is a
    record of what could not be analyzed, and it belongs to no single build.
    """
    found: dict[Path, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for path in sorted(root.glob("*/*.json")):
        try:
            doc = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"{path}: cannot be read as JSON: {exc}")
        if not isinstance(doc, dict):
            continue
        version = doc.get("tool_version")
        if not version:
            continue
        found[path.parent][version].append(path.name)
    return {directory: dict(versions) for directory, versions in found.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=BASELINES,
        help="the directory holding one subdirectory per baseline",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print what every directory holds, then still check it",
    )
    args = parser.parse_args()

    if not args.root.is_dir():
        print(f"no baseline results at {args.root}: nothing to check")
        return 0

    found = reports(args.root)
    if not found:
        print(f"no baseline reports under {args.root}: nothing to check")
        return 0

    mixed = []
    for directory in sorted(found):
        versions = found[directory]
        name = directory.name
        count = sum(len(files) for files in versions.values())
        if len(versions) == 1:
            only = next(iter(versions))
            print(f"ok    {name}: {count} reports, all on {only}")
            if args.list:
                for filename in sorted(versions[only]):
                    print(f"        {filename}")
        else:
            mixed.append(directory)
            print(f"MIXED {name}: {count} reports across {len(versions)} tool versions")
            for version in sorted(versions):
                files = sorted(versions[version])
                print(f"        {len(files):3d} on {version}")
                for filename in files:
                    print(f"            {filename}")

    if mixed:
        print()
        print(
            "A baseline table built from these would put rows from different tools "
            "beside each other with nothing saying which is which."
        )
        print(
            "Re-run the whole directory on one build, or move the older reports out "
            "of it. docs/ENVIRONMENT.md says which builds exist here."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
