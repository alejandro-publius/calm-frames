#!/usr/bin/env python3
"""Cut the real clip pool, blind it, and write the sheets two people will label.

docs/EVAL_PLAN.md section 5. The pool is not "the segments flashmap flagged", because recall
against a pool chosen by the detector under test cannot be measured. It is the union of what
every detector we have flagged, plus time that none of them flagged, sampled with a committed
seed:

- about 28 segments from the union, capped so that no one detector is the sole source of more
  than half of them;
- about 12 segments from time no detector flagged, in the same titles;
- every segment a fixed 10 s window.

Blinding. The labeller gets an opaque id, a plot and nothing else: no title, no source, no
duration in the film, no hint of which detector proposed the window, and no detector output of
any kind. The mapping back to the titles goes in pool_key.json, which the labeller does not
open. Two files, on purpose: a sheet that cannot leak an answer, and a key that the analysis
needs.

Nobody plays anything. The plots come from eval/labeling/plots.py, which does not import
flashmap, and the clips are never opened by a person at any point.

IRIS is one of the four candidate lists in the plan and it is not here, because the image has
never built on this machine. The pool file says so, and says what that costs: segments only
IRIS would have proposed are missing from the union.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parents[1]
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

REPO = _EVAL_DIR.parent
SCREENING = REPO / "results" / "screening.json"
LICENSES = REPO / "media" / "LICENSES.csv"
MEDIA = REPO / "media"
BASELINES = REPO / "results" / "baselines"
OUT_DIR = _EVAL_DIR / "labeling"

# The candidate lists the pool is the union of. A title only joins the pool if every one of them
# has looked at it. IRIS is not here: see `candidate_list_missing` in the key.
CANDIDATE_LISTS = ("flashmap", "ffmpeg_photosensitivity", "naive_luma_diff")

SEED = 20260917
SEGMENT_SECONDS = 10.0
FLAGGED_TARGET = 28
UNFLAGGED_TARGET = 12
MAX_PER_TITLE = 4
GRID_SECONDS = 0.5

# Our own generated clips are not real content and have no place in a real clip set.
NOT_REAL_CONTENT = {"markers.mp4"}


def title_key(name: str) -> str:
    """One name for one title, whatever stage of the pipeline wrote it down.

    Screening renames a file to `HAZARD_...` once it has been shown to flash, and the baselines
    and the license list were written on either side of that rename. Joining on the raw file
    name silently loses every title that was renamed in between, which is how the first version
    of this pool came out with no ffmpeg or naive segments in it at all.
    """
    stem = Path(name).stem
    return stem[len("HAZARD_") :] if stem.startswith("HAZARD_") else stem


def find_media(name: str) -> Path | None:
    """The file on disk for a title, under whichever of the two names it has."""
    key = title_key(name)
    for candidate in (MEDIA / f"HAZARD_{key}", MEDIA / key):
        for path in MEDIA.glob(f"{candidate.name}.*"):
            return path
    direct = MEDIA / name
    return direct if direct.exists() else None


def load_licenses() -> dict[str, dict]:
    rows = {}
    with LICENSES.open() as handle:
        for row in csv.DictReader(handle):
            name = row["file"].strip()
            if not name or name.startswith("("):
                continue
            rows[name] = row
    return rows


def detector_intervals() -> dict[str, dict[str, list[tuple[float, float]]]]:
    """Every detector's flagged intervals, per media file, in seconds."""
    out: dict[str, dict[str, list[tuple[float, float]]]] = {}

    screening = json.loads(SCREENING.read_text())
    for entry in screening["per_file"]:
        if entry.get("error"):
            continue
        intervals = [
            (float(segment["start_s"]), float(segment["end_s"]))
            for segment in entry.get("segments", [])
        ]
        out.setdefault(title_key(entry["file"]), {})["flashmap"] = intervals

    for baseline, folder in (
        ("ffmpeg_photosensitivity", "ffmpeg_photosensitivity"),
        ("naive_luma_diff", "naive_luma_diff"),
    ):
        for path in sorted((BASELINES / folder).glob("*.json")):
            data = json.loads(path.read_text())
            intervals = [(s["start_s"], s["end_s"]) for s in data.get("segments", [])]
            out.setdefault(title_key(data["video"]), {})[baseline] = intervals
    return out


def snap(value: float) -> float:
    return round(value / GRID_SECONDS) * GRID_SECONDS


def candidate_windows(
    intervals: dict[str, list[tuple[float, float]]], duration: float
) -> list[dict]:
    """One 10 s window per flagged moment, merged when two windows would overlap."""
    if duration <= SEGMENT_SECONDS:
        return []
    moments: list[tuple[float, str]] = []
    for detector, spans in intervals.items():
        for start, end in spans:
            moments.append((max(0.0, (start + end) / 2.0), detector))
    moments.sort()

    windows: list[dict] = []
    for centre, detector in moments:
        start = snap(min(max(0.0, centre - SEGMENT_SECONDS / 2), duration - SEGMENT_SECONDS))
        if windows and start < windows[-1]["start_s"] + SEGMENT_SECONDS:
            windows[-1]["detectors"].add(detector)
            continue
        windows.append({"start_s": start, "detectors": {detector}})

    # Which detectors flagged anything inside each finished window, not just the moment that
    # opened it. A window's sole source is only sole if nothing else fired inside it.
    for window in windows:
        start = window["start_s"]
        end = start + SEGMENT_SECONDS
        for detector, spans in intervals.items():
            if any(s < end and e > start for s, e in spans):
                window["detectors"].add(detector)
    return windows


def unflagged_windows(
    intervals: dict[str, list[tuple[float, float]]], duration: float, rng: random.Random
) -> list[dict]:
    """Windows in the same title that no detector flagged at all."""
    if duration <= SEGMENT_SECONDS:
        return []
    spans = [span for detector_spans in intervals.values() for span in detector_spans]
    out = []
    for _ in range(40):
        start = snap(rng.uniform(0.0, duration - SEGMENT_SECONDS))
        end = start + SEGMENT_SECONDS
        if any(s < end and e > start for s, e in spans):
            continue
        if any(abs(start - window["start_s"]) < SEGMENT_SECONDS for window in out):
            continue
        out.append({"start_s": start, "detectors": set()})
    return out


def build() -> dict:
    rng = random.Random(SEED)
    licenses = load_licenses()
    flags = detector_intervals()
    screening = json.loads(SCREENING.read_text())
    source_by_file = {
        title_key(entry["file"]): entry.get("source", "unknown")
        for entry in screening["per_file"]
    }

    titles = []
    skipped = {}
    for name, row in sorted(licenses.items()):
        if name in NOT_REAL_CONTENT:
            skipped[name] = "our own generated clip, not real content"
            continue
        path = find_media(name)
        if path is None:
            skipped[name] = "file not in media/ under either name"
            continue
        if "not verified" in row["license"].lower() or "verify" in row["notes"].lower():
            skipped[name] = "license line not confirmed, dropped at screening"
            continue
        looked = flags.get(title_key(name), {})
        missing = [detector for detector in CANDIDATE_LISTS if detector not in looked]
        if missing:
            # Every detector has to have looked at a title before any of its time can join the
            # pool. Time is "unflagged" only when every candidate list ran and none of them
            # flagged it. One detector's silence on a title nobody else analysed is not the same
            # thing, and it would put windows nobody has measured into the negative half, where
            # they would count as false positives for whichever detector did run.
            ran = sorted(looked) or ["nothing"]
            skipped[name] = (
                f"only {', '.join(ran)} has a candidate list for it; "
                f"{', '.join(missing)} never ran on it"
            )
            continue
        duration = float(row["duration_s"] or 0.0)
        if duration <= SEGMENT_SECONDS:
            skipped[name] = f"shorter than one {SEGMENT_SECONDS:.0f} s segment"
            continue
        titles.append((path.name, row, duration))

    flagged_pool: list[dict] = []
    unflagged_pool: list[dict] = []
    for name, row, duration in titles:
        intervals = flags.get(title_key(name), {})
        for window in candidate_windows(intervals, duration):
            window.update(
                {"file": name, "source": source_by_file.get(title_key(name), "unknown")}
            )
            flagged_pool.append(window)
        for window in unflagged_windows(intervals, duration, rng):
            window.update(
                {"file": name, "source": source_by_file.get(title_key(name), "unknown")}
            )
            unflagged_pool.append(window)

    rng.shuffle(flagged_pool)
    rng.shuffle(unflagged_pool)

    chosen: list[dict] = []
    per_title: dict[str, int] = {}
    sole_source: dict[str, int] = {}
    cap = FLAGGED_TARGET // 2
    for window in flagged_pool:
        if len(chosen) >= FLAGGED_TARGET:
            break
        if per_title.get(window["file"], 0) >= MAX_PER_TITLE:
            continue
        detectors = sorted(window["detectors"])
        if len(detectors) == 1 and sole_source.get(detectors[0], 0) >= cap:
            continue
        if len(detectors) == 1:
            sole_source[detectors[0]] = sole_source.get(detectors[0], 0) + 1
        per_title[window["file"]] = per_title.get(window["file"], 0) + 1
        chosen.append(window)

    for window in unflagged_pool:
        if len([w for w in chosen if not w["detectors"]]) >= UNFLAGGED_TARGET:
            break
        if per_title.get(window["file"], 0) >= MAX_PER_TITLE + 1:
            continue
        per_title[window["file"]] = per_title.get(window["file"], 0) + 1
        chosen.append(window)

    rng.shuffle(chosen)
    key_rows = []
    sheet_rows = []
    for index, window in enumerate(chosen):
        segment_id = f"seg{index:03d}"
        key_rows.append(
            {
                "segment_id": segment_id,
                "file": window["file"],
                "source": window["source"],
                "start_s": round(window["start_s"], 3),
                "end_s": round(window["start_s"] + SEGMENT_SECONDS, 3),
                "proposed_by": sorted(window["detectors"]),
                "from_unflagged_time": not window["detectors"],
            }
        )
        sheet_rows.append(
            {
                "segment_id": segment_id,
                "seconds": SEGMENT_SECONDS,
                "windows": int(SEGMENT_SECONDS),
                "plot": f"plots/{segment_id}.png",
            }
        )

    return {
        "sheet": {
            "generated_on": "2026-09-17",
            "what_this_is": (
                "the blinded segment pool for the real clip labelling. Each row is a ten second "
                "segment of some video, with an opaque id and a plot. No title, no source, no "
                "detector output. Label from the plot alone, following GUIDE.md."
            ),
            "segment_seconds": SEGMENT_SECONDS,
            "window_seconds": 1,
            "segments": sheet_rows,
        },
        "key": {
            "generated_on": "2026-09-17",
            "warning": (
                "THE LABELLERS DO NOT OPEN THIS FILE. It maps each blinded id back to its title, "
                "its place in that title and which detectors proposed it. Opening it before "
                "labelling would unblind the review and waste the whole exercise."
            ),
            "seed": SEED,
            "segment_seconds": SEGMENT_SECONDS,
            "titles": len({row["file"] for row in key_rows}),
            "sources": sorted({row["source"] for row in key_rows}),
            "counts": {
                "segments": len(key_rows),
                "from_flagged_time": sum(1 for row in key_rows if not row["from_unflagged_time"]),
                "from_unflagged_time": sum(1 for row in key_rows if row["from_unflagged_time"]),
                "sole_source": sole_source,
                "per_title": per_title,
            },
            "candidate_lists_used": list(CANDIDATE_LISTS),
            "titles_need_every_candidate_list": (
                "a title joins the pool only when every list above has analysed it. A title only "
                "one of them has seen has no unflagged time in the sense this pool means, because "
                "the other lists never had the chance to flag it."
            ),
            "candidate_list_missing": {
                "EA IRIS": (
                    "the image has never built on this machine, so no segment in this pool was "
                    "proposed by IRIS. Anything only IRIS would have caught is not in the union, "
                    "which makes this pool's recall estimate optimistic by an unknown amount."
                )
            },
            "known_decoder_gap": (
                "the four Theora .ogv titles have no flashmap intervals in the screening run "
                "this pool was cut from: they failed with avcodec_send_packet returning 22, "
                "which results/screening.json still records. Their windows therefore come from "
                "the two ffmpeg based lists only. flashmap's Theora decoding has since been "
                "fixed (see flashmap/tests/test_theora.py), so the right order is: rescreen "
                "those four titles, then run `make labeling-pool` again, and only then start "
                "labelling. Rebuilding after labelling has begun would throw the labels away, "
                "because the segment ids are positions in a shuffled list."
            ),
            "titles_skipped": skipped,
            "segments": key_rows,
        },
    }


def sheets_with_answers(out_dir: Path) -> list[Path]:
    """Any sheet in this directory that somebody has started filling in."""
    from labeling.make_sheets import has_labels  # noqa: PLC0415

    return [path for path in sorted(out_dir.glob("labels_*.csv")) if has_labels(path)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("-o", "--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--force",
        action="store_true",
        help="rebuild even though a sheet has answers in it. It will not mean what it says.",
    )
    arguments = parser.parse_args()

    # A segment id is a position in a shuffled list, so rebuilding the pool after labelling has
    # started does not erase the answers, which would at least be obvious. It quietly points
    # them at different segments. make_sheets.py refuses to overwrite a filled sheet, which is
    # what made this the dangerous half: the sheet survives and stops meaning anything.
    started = sheets_with_answers(arguments.out_dir)
    if started and not arguments.force:
        print(
            "these sheets already have answers in them: "
            + ", ".join(path.name for path in started),
            file=sys.stderr,
        )
        print(
            "Rebuilding the pool now would leave those answers pointing at different segments, "
            "because a segment id is a position in a shuffled list. Nothing was written. "
            "Finish the labelling, or move the sheets aside first.",
            file=sys.stderr,
        )
        return 2

    built = build()
    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = arguments.out_dir / "pool.json"
    key_path = arguments.out_dir / "pool_key.json"
    sheet_path.write_text(json.dumps(built["sheet"], indent=1) + "\n")
    key_path.write_text(json.dumps(built["key"], indent=1) + "\n")

    digest = hashlib.sha256(key_path.read_bytes()).hexdigest()[:16]
    counts = built["key"]["counts"]
    print(
        f"{counts['segments']} segments from {built['key']['titles']} titles "
        f"({counts['from_flagged_time']} flagged, {counts['from_unflagged_time']} unflagged), "
        f"sources {built['key']['sources']}, key sha256 {digest}"
    )
    print(f"wrote {sheet_path} and {key_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
