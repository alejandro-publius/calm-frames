#!/usr/bin/env python3
"""Write the blank labelling sheets, one per labeller, from the blinded pool.

One row per one second window, in the shuffled order the pool file fixes. The sheets carry no
detector output and no title: the only thing on a row is the segment id, the window number and
three empty columns.

Two sheets are written because docs/EVAL_PLAN.md section 5 wants a second labeller on at least
15 segments and an unweighted Cohen's kappa on the labels as first given. The second sheet is
the same rows, so the overlap is every segment rather than a subset, which costs the second
labeller more time and gives a kappa on the whole set. If the second labeller only gets through
part of it, the kappa is computed on what both of them labelled and the count is reported.

This script refuses to overwrite a sheet that already has any label in it. Nobody's afternoon
gets erased by a re-run.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = _EVAL_DIR / "labeling"
COLUMNS = ["segment_id", "window_index", "window_start_s", "label", "unlabelable", "notes"]


def has_labels(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open() as handle:
        for row in csv.DictReader(handle):
            if (row.get("label") or "").strip() or (row.get("unlabelable") or "").strip():
                return True
            if (row.get("notes") or "").strip():
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--pool", type=Path, default=OUT_DIR / "pool.json")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--labeller", action="append", default=None, help="repeatable, defaults to two sheets"
    )
    arguments = parser.parse_args()

    labellers = arguments.labeller or ["labeller_a", "labeller_b"]
    pool = json.loads(arguments.pool.read_text())

    written = []
    for name in labellers:
        path = arguments.out_dir / f"labels_{name}.csv"
        if has_labels(path):
            print(f"{path.name} already has answers in it, leaving it alone", file=sys.stderr)
            continue
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            for segment in pool["segments"]:
                for index in range(int(segment["windows"])):
                    writer.writerow(
                        {
                            "segment_id": segment["segment_id"],
                            "window_index": index,
                            "window_start_s": index,
                            "label": "",
                            "unlabelable": "",
                            "notes": "",
                        }
                    )
        written.append(path)

    rows = sum(int(segment["windows"]) for segment in pool["segments"])
    print(f"{len(written)} sheet(s), {rows} windows each, in {arguments.out_dir}")
    for path in written:
        print(f"  {path}")
    print("Read GUIDE.md first. Do not open pool_key.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
