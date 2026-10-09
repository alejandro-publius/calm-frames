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
import subprocess
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
        "iris": [(11.0, 11.4)],
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
    for missing in ("ffmpeg_photosensitivity", "naive_luma_diff", "iris"):
        assert missing in reason, f"the skip reason does not name {missing}"

    chosen = {row["file"] for row in built["key"]["segments"]}
    assert "HAZARD_invented_seen_by_one.webm" not in chosen
    assert "HAZARD_invented_seen_by_all.mp4" in chosen


def test_a_clip_the_ledger_calls_ours_is_kept_out(monkeypatch, tmp_path):
    """Our own generated clips never join, even when every list has analysed them.

    The row below is FABRICATED FOR TEST ONLY, shaped like the one media/markers_packed.mp4 got
    on Oct 9, 2026: a note that starts "Ours.", a result from every candidate list and a length
    of more than one segment. Nothing but the ledger's own word keeps a clip like that out.

    Break it: drop the "Ours." half of make_pool.is_our_own, and this goes red with the clip
    in the pool. Seen to fail that way on Oct 9, 2026.
    """
    licenses = dict(FABRICATED_LICENSES)
    licenses["media/invented_ours.mp4"] = {
        "file": "media/invented_ours.mp4",
        "license": "CC0-1.0",
        "duration_s": "120",
        "notes": "Ours. FABRICATED FOR TEST ONLY.",
    }
    flags = dict(FABRICATED_FLAGS)
    flags["invented_ours"] = {name: [] for name in make_pool.CANDIDATE_LISTS}
    _patch(monkeypatch, tmp_path)
    monkeypatch.setattr(make_pool, "load_licenses", lambda: licenses)

    titles, skipped = make_pool.eligible_titles(flags)

    assert "invented_ours.mp4" not in [name for name, _, _ in titles]
    assert skipped.get("media/invented_ours.mp4") == "our own generated clip, not real content"
    assert "HAZARD_invented_seen_by_all.mp4" in [name for name, _, _ in titles]


def test_the_real_ledger_keeps_every_clip_of_ours_out(monkeypatch):
    """The committed ledger and the committed candidate lists, with every file found.

    find_media is the only stand-in: it says every file is on disk, as it is on the machine that
    builds the pool, so the only thing left between our own clips and the pool is the rule
    above. No media file is opened.

    Break it: drop the "Ours." half of make_pool.is_our_own, and this goes red naming
    markers_packed.mp4, which every candidate list has a result for. Seen to fail that way on
    Oct 9, 2026.
    """
    licenses = make_pool.load_licenses()
    ours = {
        name
        for name, row in licenses.items()
        if (row.get("notes") or "").startswith("Ours.") or name in make_pool.NOT_REAL_CONTENT
    }
    assert "media/markers_packed.mp4" in ours
    monkeypatch.setattr(make_pool, "find_media", lambda name: Path("/nonexistent") / Path(name).name)

    titles, skipped = make_pool.eligible_titles(make_pool.detector_intervals())

    joined = {name for name, _, _ in titles}
    assert joined.isdisjoint({Path(name).name for name in ours}), (
        f"our own clips joined the pool: {sorted(joined & {Path(n).name for n in ours})}"
    )
    for name in ours:
        assert skipped.get(name) == "our own generated clip, not real content"


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
        "iris",
        "proposed_by",
        "from_unflagged_time",
    ):
        assert giveaway not in sheet_text, f"the blinded sheet leaks {giveaway!r}"

    # The key is the other half of the pair, and it does hold the mapping back.
    key_text = json.dumps(built["key"])
    assert "invented_seen_by_all" in key_text
    assert "proposed_by" in key_text


def test_the_pool_refuses_to_rebuild_once_somebody_has_started_labelling(tmp_path):
    """The dangerous half of a re-run.

    make_sheets.py already refuses to overwrite a filled sheet, so a re-run leaves the answers
    on disk while the pool underneath them is reshuffled. The answers then point at different
    segments and nothing says so. The sheet below is FABRICATED FOR TEST ONLY: one answered row.

    Break it: drop the started check in make_pool.main(), and this goes red.
    """
    sheet = tmp_path / "labels_labeller_a.csv"
    sheet.write_text(
        "segment_id,window_index,window_start_s,label,unlabelable,notes\n"
        "seg000,0,0,1,,FABRICATED FOR TEST ONLY\n"
    )
    finished = subprocess.run(
        [sys.executable, str(EVAL_DIR / "labeling" / "make_pool.py"), "--out-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert finished.returncode == 2, finished.stdout
    assert "labels_labeller_a.csv" in finished.stderr
    assert not (tmp_path / "pool.json").exists(), "it wrote a new pool anyway"
    assert not (tmp_path / "pool_key.json").exists()


def test_the_csv_sheet_has_nothing_on_it_but_the_id_and_the_window(tmp_path):
    """The file the labeller types into. FABRICATED FOR TEST ONLY pool of two segments.

    Break it: add the file name, the source or a detector column to make_sheets.COLUMNS, and
    this goes red.
    """
    pool = tmp_path / "pool.json"
    pool.write_text(
        json.dumps(
            {
                "segments": [
                    {"segment_id": "seg000", "seconds": 10.0, "windows": 10, "plot": "plots/seg000.png"},
                    {"segment_id": "seg001", "seconds": 10.0, "windows": 10, "plot": "plots/seg001.png"},
                ]
            }
        )
    )
    finished = subprocess.run(
        [
            sys.executable,
            str(EVAL_DIR / "labeling" / "make_sheets.py"),
            "--pool",
            str(pool),
            "--out-dir",
            str(tmp_path),
            "--labeller",
            "invented_for_test_only",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert finished.returncode == 0, finished.stderr

    sheet = tmp_path / "labels_invented_for_test_only.csv"
    lines = sheet.read_text().splitlines()
    assert lines[0] == "segment_id,window_index,window_start_s,label,unlabelable,notes"
    assert len(lines) == 21, "two segments of ten windows, plus the header"
    for line in lines[1:]:
        cells = line.split(",")
        assert cells[0].startswith("seg")
        assert cells[3:] == ["", "", ""], f"a sheet row arrives with something already on it: {line}"
