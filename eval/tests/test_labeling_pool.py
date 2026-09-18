"""The blinded pool: what joins it, what is kept out, and what the labeller can see.

Every title, interval and licence row in this file is FABRICATED FOR TEST ONLY. The names are
invented, no file on disk is opened, and nothing written here reaches eval/labeling/ or results/.

What this holds the pool to:

- a title only joins when every candidate list has analysed it. One detector's silence on a
  title the others never saw is not unflagged time, and counting it as such would hand the
  detector that did run a free false positive on windows nobody measured;
- the sheet the labeller reads carries no file name, no source, no position in the film and no
  detector name, anywhere in it, at any depth.

To see them fail on purpose: see the note on each test. Both were verified on Sep 17, 2026.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from labeling import make_pool  # noqa: E402

FABRICATED_FOR_TEST_ONLY = True

# One title every list looked at, and one that only flashmap looked at. The second stands for
# the calm clips that arrived after the baselines had already run.
FABRICATED_LICENSES = {
    "HAZARD_invented_seen_by_all.mp4": {
        "file": "HAZARD_invented_seen_by_all.mp4",
        "license": "CC BY 4.0",
        "duration_s": "120",
        "notes": "source: Invented source. FABRICATED FOR TEST ONLY.",
    },
    "HAZARD_invented_seen_by_one.webm": {
        "file": "HAZARD_invented_seen_by_one.webm",
        "license": "CC BY 4.0",
        "duration_s": "120",
        "notes": "source: Invented source. FABRICATED FOR TEST ONLY.",
    },
}

FABRICATED_FLAGS = {
    "invented_seen_by_all": {
        "flashmap": [(10.0, 12.0), (40.0, 41.5)],
        "ffmpeg_photosensitivity": [(10.5, 11.0), (80.0, 81.0)],
        "naive_luma_diff": [(40.2, 40.9)],
    },
    "invented_seen_by_one": {"flashmap": []},
}

FABRICATED_SCREENING = {
    "per_file": [
        {"file": "HAZARD_invented_seen_by_all.mp4", "source": "Invented source", "segments": []},
        {"file": "HAZARD_invented_seen_by_one.webm", "source": "Invented source", "segments": []},
    ]
}


def _patch(monkeypatch, tmp_path: Path) -> None:
    screening = tmp_path / "screening.json"
    screening.write_text(json.dumps(FABRICATED_SCREENING))
    monkeypatch.setattr(make_pool, "SCREENING", screening)
    monkeypatch.setattr(make_pool, "load_licenses", lambda: FABRICATED_LICENSES)
    monkeypatch.setattr(make_pool, "detector_intervals", lambda: FABRICATED_FLAGS)
    monkeypatch.setattr(make_pool, "find_media", lambda name: tmp_path / name)


def test_a_title_only_one_list_has_seen_is_kept_out(monkeypatch, tmp_path):
    """Break it: drop the `missing` check in build() and this goes red."""
    _patch(monkeypatch, tmp_path)
    built = make_pool.build()
    skipped = built["key"]["titles_skipped"]

    assert "HAZARD_invented_seen_by_one.webm" in skipped
    reason = skipped["HAZARD_invented_seen_by_one.webm"]
    assert "ffmpeg_photosensitivity" in reason and "naive_luma_diff" in reason

    chosen = {row["file"] for row in built["key"]["segments"]}
    assert "HAZARD_invented_seen_by_one.webm" not in chosen
    assert "HAZARD_invented_seen_by_all.mp4" in chosen


def test_the_sheet_the_labeller_reads_gives_nothing_away(monkeypatch, tmp_path):
    """Break it: copy `file`, `source` or `proposed_by` into a sheet row, and this goes red."""
    _patch(monkeypatch, tmp_path)
    built = make_pool.build()
    sheet_text = json.dumps(built["sheet"])

    for giveaway in (
        "invented_seen_by_all",
        "Invented source",
        "flashmap",
        "ffmpeg_photosensitivity",
        "naive_luma_diff",
        "proposed_by",
        "from_unflagged_time",
    ):
        assert giveaway not in sheet_text, f"the blinded sheet leaks {giveaway!r}"

    # The key is the other half of the pair, and it does hold the mapping back.
    key_text = json.dumps(built["key"])
    assert "invented_seen_by_all" in key_text
    assert "proposed_by" in key_text
