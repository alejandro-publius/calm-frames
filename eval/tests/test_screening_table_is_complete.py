"""The README's per-source screening table has to hold every source, and add up.

A mock judge added the Files column in the README and got 15 against a row two
tables up saying 16 clips were analyzed cleanly. results/screening.json had a
seventh source the table had quietly dropped. Adding the row fixed it for about
an hour, until the screening lane added an eighth source and the table was wrong
again.

So this is the part that lasts. Two properties, both cheap:

1. every source in results/screening.json has a row in the README table, and
2. the Files column adds up to clips_analyzed_ok.

Between them a reader can add the column and get the number the page already
gave them, which is all the table was ever promising.

Seen to fail on purpose, Sep 17 2026, three ways: deleting a row from the
README, changing one Files cell, and adding a source to a copy of the results
file. All three turned it red.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
README = REPO / "README.md"
SCREENING = REPO / "results" / "screening.json"

# | Some source name | <!--n results/screening.json:per_source.Some source name.files -->3<!--/n--> | ...
ROW = re.compile(
    r"^\|\s*`?(?P<name>[^|`]+?)`?\s*\|\s*"
    r"<!--n results/screening\.json:per_source\.(?P<key>[^.]+)\.files\s*-->"
    r"(?P<files>\d+)<!--/n-->",
    re.MULTILINE,
)


def table_rows() -> dict[str, int]:
    text = README.read_text(encoding="utf-8")
    return {m.group("key"): int(m.group("files")) for m in ROW.finditer(text)}


def sources() -> dict[str, int]:
    data = json.loads(SCREENING.read_text(encoding="utf-8"))
    return {name: block["files"] for name, block in data["per_source"].items()}


def test_every_source_in_the_results_file_has_a_row():
    missing = sorted(set(sources()) - set(table_rows()))
    assert missing == [], (
        f"results/screening.json has {missing} and the README's per-source table "
        f"does not. A reader who adds the Files column gets a number that matches "
        f"nothing on the page."
    )


def test_the_table_invents_no_sources():
    extra = sorted(set(table_rows()) - set(sources()))
    assert extra == [], f"the README's table has rows for {extra}, which are not in the results file"


def test_the_files_column_adds_up_to_the_clips_analyzed_cleanly():
    data = json.loads(SCREENING.read_text(encoding="utf-8"))
    rows = table_rows()
    assert rows, "no per-source rows were found in the README at all"
    assert sum(rows.values()) == data["clips_analyzed_ok"], (
        f"the README's Files column sums to {sum(rows.values())} and "
        f"clips_analyzed_ok is {data['clips_analyzed_ok']}"
    )


def test_each_row_carries_the_number_the_results_file_has():
    # readme_sync.py already checks this, and it checks it as a marker rather than
    # as a table. Doing it here too costs nothing and means this file fails for the
    # obvious reason rather than the subtle one.
    rows = table_rows()
    for name, files in sources().items():
        if name in rows:
            assert rows[name] == files, f"{name}: README says {rows[name]}, results says {files}"
