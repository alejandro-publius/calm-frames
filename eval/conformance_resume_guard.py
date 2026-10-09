#!/usr/bin/env python3
"""Refuse legacy Makefile resumption across conformance encoding protocols.

Read-only: no clips are generated and no archive row is rewritten. The direct
legacy generator remains frozen during the current full measurement; its
entrypoint guard must follow after that measurement and its reports finish.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

EVAL = Path(__file__).resolve().parent
if str(EVAL) not in sys.path:
    sys.path.insert(0, str(EVAL))

from conformance.render import ENCODING_PROTOCOL

REPO = Path(__file__).resolve().parents[1]
ARCHIVE = REPO / "results/conformance_raw.jsonl"


def check_archive(path: Path) -> int:
    """Return the resumable row count only when every row names this protocol."""
    if not path.exists():
        return 0
    count = 0
    with path.open() as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"archive row {line_number} is not valid JSON") from exc
            encode = row.get("encode") if isinstance(row, dict) else None
            protocol = encode.get("protocol") if isinstance(encode, dict) else None
            if protocol != ENCODING_PROTOCOL:
                raise ValueError(
                    f"archive row {line_number} has a missing or different encoding protocol"
                )
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args(argv)
    try:
        count = check_archive(args.archive)
    except (OSError, ValueError) as exc:
        print(f"Refusing conformance resumption: {exc}. Preserve the archive. "
              "For a separate fresh run, use eval/conformance/recheck.py "
              "--selection design --out NEW_RESULT.json.", file=sys.stderr)
        return 2
    print(f"Conformance resume protocol checked: {count} existing rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
