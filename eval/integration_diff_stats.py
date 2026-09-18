"""Count the integration diff, so the size of it is a measured number.

docs/INTEGRATION_DIFF.md holds the real `git diff` that adds the flash guard to
a clean vega-video-sample checkout. The README says how big that change is, and
the rule in CLAUDE.md is that a published number comes from results/ through a
marker. So this script counts the diff that is actually committed and writes
results/integration_diff.json for the markers to point at.

    python3 eval/integration_diff_stats.py            write results/integration_diff.json
    python3 eval/integration_diff_stats.py --check    fail if the file has drifted

It counts the committed document rather than regenerating the patch, because
regenerating needs the pinned sample checkout and this has to run in CI. What
keeps the document honest is hook/tools/make_integration_diff.mjs, which rebuilds
the patch from that checkout. What keeps the README honest is this.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "INTEGRATION_DIFF.md"
OUT = REPO / "results" / "integration_diff.json"

DIFF_BLOCK = re.compile(r"```diff\n(?P<body>.*?)\n```", re.DOTALL)


def measure(text: str) -> dict:
    blocks = DIFF_BLOCK.findall(text)
    if len(blocks) != 1:
        raise SystemExit(
            f"{DOC}: expected exactly one ```diff block, found {len(blocks)}"
        )
    body = blocks[0]
    lines = body.splitlines()

    added = [ln for ln in lines if ln.startswith("+") and not ln.startswith("+++")]
    removed = [ln for ln in lines if ln.startswith("-") and not ln.startswith("---")]
    files = [ln for ln in lines if ln.startswith("diff --git ")]

    if not files:
        raise SystemExit(f"{DOC}: the diff block has no 'diff --git' header")

    # Per file, because the shape of the change matters as much as its size:
    # the work is concentrated in one file and the other three are small.
    per_file: dict[str, dict[str, int]] = {}
    current: str | None = None
    for ln in lines:
        if ln.startswith("diff --git "):
            current = ln.split()[-1]
            per_file[current] = {"added": 0, "replaced": 0}
        elif current is None:
            continue
        elif ln.startswith("+") and not ln.startswith("+++"):
            per_file[current]["added"] += 1
        elif ln.startswith("-") and not ln.startswith("---"):
            per_file[current]["replaced"] += 1

    busiest = max(per_file.items(), key=lambda kv: kv[1]["added"] + kv[1]["replaced"])

    return {
        "generated_from": "docs/INTEGRATION_DIFF.md",
        "what_this_is": (
            "the size of the real git diff that adds the flash guard to a clean "
            "vega-video-sample checkout at tag v0.24-RN83"
        ),
        "lines_added": len(added),
        "lines_replaced": len(removed),
        "files_touched": len(files),
        "per_file": per_file,
        "busiest_file": busiest[0],
        "busiest_file_lines_added": busiest[1]["added"],
        "other_files_lines_added_each": sorted(
            {counts["added"] for name, counts in per_file.items() if name != busiest[0]}
        ),
        "diff_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing, if the committed file does not match",
    )
    args = parser.parse_args(argv)

    if not DOC.exists():
        print(f"{DOC} is missing", file=sys.stderr)
        return 1

    measured = measure(DOC.read_text(encoding="utf-8"))

    if args.check:
        if not OUT.exists():
            print(f"{OUT} is missing. Run this script without --check.", file=sys.stderr)
            return 1
        committed = json.loads(OUT.read_text(encoding="utf-8"))
        if committed != measured:
            print(
                f"{OUT} has drifted from {DOC}.\n"
                f"  committed: {json.dumps(committed, sort_keys=True)}\n"
                f"  measured:  {json.dumps(measured, sort_keys=True)}",
                file=sys.stderr,
            )
            return 1
        print(f"{OUT.relative_to(REPO)} matches the committed diff")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
