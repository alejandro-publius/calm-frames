#!/usr/bin/env python3
"""GATE 2 screening: run flashmap over the media pool and count flagged segments.

One command, once lane B's flashmap package exists:

    .venv/bin/python eval/screen.py

It reads media/LICENSES.csv to learn which source each file came from, runs
flashmap over every clip, renames anything with at least one flagged segment to
HAZARD_<name>, and writes per-source counts to results/screening.json.

The per-source table, the split of segments by which rule fired, and the list of
clips we still have to film come from eval/screening_table.py, which this script
calls before it writes. That module can also refresh the table on a file an older
run wrote, and check it for drift.

FLASHMAP IS NOT READY YET (Sep 17, 2026). flashmap/ is an empty directory. This
script refuses to invent numbers: with no flashmap it prints what it found and
exits non-zero, and results/screening.json is not written at all. An absent file
is honest; a file full of zeros is not.

THE ADAPTER
-----------
`analyze_one()` calls `flashmap.analyze_file(path, profile)` and counts the
`segments` on the `AnalysisResult` it returns. That signature was read off the
landed package on Sep 17, 2026, not guessed. flashmap is being written right now,
so if the signature moves this script will say so loudly rather than quietly
returning zero: an analysis that raises is recorded as an error, and a run where
nothing at all succeeded writes no file.

Safety: this script never opens a player and never previews a frame. Flagged
files get the HAZARD_ prefix so nothing else opens them by accident either.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

import screening_table  # noqa: E402

REPO = _EVAL_DIR.parent
MEDIA = REPO / "media"
LEDGER = MEDIA / "LICENSES.csv"
OUT = REPO / "results" / "screening.json"
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".ogv", ".mkv", ".m4v", ".avi"}

# GATE 2 pass condition from docs/BUILD_PROMPT.md 2.4. A planning target, not a
# spec number.
GATE2_MIN_SEGMENTS = 15
GATE2_MIN_SOURCES = 4


def load_sources() -> dict[str, str]:
    """file name -> source label, from the notes column of the license ledger."""
    out: dict[str, str] = {}
    if not LEDGER.is_file():
        return out
    with LEDGER.open(newline="") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("file") or "").strip()
            if not name or name.startswith("("):
                continue
            note = row.get("notes") or ""
            label = "unknown"
            if note.startswith("source: "):
                label = note[len("source: "):].split(".")[0].strip()
            out[name] = label
            # The same clip may already carry the hazard prefix.
            out[f"HAZARD_{name}"] = label
            if name.startswith("HAZARD_"):
                out[name[len("HAZARD_"):]] = label
    return out


def import_flashmap():
    """Return a usable flashmap module, or None with the reason printed.

    `import flashmap` is not enough. An empty flashmap/ directory imports fine as
    an implicit namespace package (PEP 420) and yields a module with no __file__
    and no attributes, which would let this script sail on and write a
    screening.json full of zeros. That is the failure this check exists to stop,
    and it is the one that actually happened on Sep 17, 2026.
    """
    # flashmap/ is a src-layout project (flashmap/src/flashmap/). Prefer that over
    # the bare flashmap/ directory, which would otherwise win as a namespace
    # package and hand back an empty module.
    src = REPO / "flashmap" / "src"
    pkg = src / "flashmap" if src.is_dir() else REPO / "flashmap"
    contents = sorted(p.name for p in pkg.iterdir()) if pkg.is_dir() else []

    def refuse(reason: str):
        print("flashmap is not usable yet.", file=sys.stderr)
        print(f"  reason: {reason}", file=sys.stderr)
        print(f"  {pkg} contains: {contents or '(empty)'}", file=sys.stderr)
        return None

    for candidate in (src, REPO):
        if candidate.is_dir() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    try:
        import flashmap  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return refuse(str(exc))

    if getattr(flashmap, "__file__", None) is None:
        return refuse(
            "imported as an empty PEP 420 namespace package, so there is no code "
            "behind the name. Lane B has not landed flashmap yet."
        )
    public = [a for a in dir(flashmap) if not a.startswith("_")]
    if not public:
        return refuse(f"imported from {flashmap.__file__} but exposes nothing public")
    return flashmap


ENTRY_POINT = "flashmap.analyze_file(path, profile)"


def analyze_one(flashmap, path: Path, profile):
    """Run flashmap on one clip and return its flagged segments.

    Signature read off the landed package on Sep 17, 2026:
        analyze_file(path, profile, room=None, policy=..., ...) -> AnalysisResult
        AnalysisResult.segments -> list[Segment]
    """
    result = flashmap.analyze_file(str(path), profile)
    segments = getattr(result, "segments", None)
    if segments is None:
        raise RuntimeError(
            f"flashmap.analyze_file returned a {type(result).__name__} with no "
            "`segments`. The API moved; update analyze_one()."
        )
    return list(segments), result


def segment_row(seg) -> dict:
    """One flagged segment, flattened for the report."""
    def g(name, default=None):
        return getattr(seg, name, default)

    start_ms, end_ms = g("start_ms"), g("end_ms")
    return {
        "start_s": round(start_ms / 1000.0, 3) if start_ms is not None else None,
        "end_s": round(end_ms / 1000.0, 3) if end_ms is not None else None,
        "reason": g("reason"),
        "area_fraction": g("area_fraction"),
        "triggered_by": g("triggered_by"),
        "breaks_baseline": g("breaks_baseline"),
        "max_flashes_in_window": g("max_flashes_in_window"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--preset", default="wcag")
    ap.add_argument("--media-dir", type=Path, default=MEDIA)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--no-rename", action="store_true",
                    help="do not add the HAZARD_ prefix to flagged files")
    args = ap.parse_args()

    clips = sorted(p for p in args.media_dir.iterdir()
                   if p.suffix.lower() in VIDEO_SUFFIXES)
    sources = load_sources()
    unlabeled = [p.name for p in clips if p.name not in sources]

    print(f"{len(clips)} clips in {args.media_dir}")
    if unlabeled:
        print(f"  not in the license ledger: {', '.join(unlabeled)}")

    flashmap = import_flashmap()
    if flashmap is None:
        print("\nNothing written. results/screening.json stays absent rather than "
              "carrying numbers nobody measured.", file=sys.stderr)
        print("Re-run this exact command once lane B lands flashmap:", file=sys.stderr)
        print("    .venv/bin/python eval/screen.py", file=sys.stderr)
        return 2

    try:
        profile = flashmap.get_profile(args.preset)
    except Exception as exc:  # noqa: BLE001
        print(f"no such flashmap profile {args.preset!r}: {exc}", file=sys.stderr)
        print(f"  available: {list(getattr(flashmap, 'PROFILES', []))}", file=sys.stderr)
        return 2

    per_source: dict[str, dict] = {}
    per_file: list[dict] = []
    renamed: list[str] = []
    analyzed_ok = 0

    for clip in clips:
        label = sources.get(clip.name, "unlabeled")
        try:
            segments, result = analyze_one(flashmap, clip, profile)
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED {clip.name}: {exc}", file=sys.stderr)
            per_file.append({"file": clip.name, "source": label, "error": str(exc)})
            continue

        analyzed_ok += 1
        n = len(segments)
        final_name = clip.name
        if n > 0 and not args.no_rename and not clip.name.startswith("HAZARD_"):
            target = clip.with_name(f"HAZARD_{clip.name}")
            clip.rename(target)
            final_name = target.name
            renamed.append(final_name)

        bucket = per_source.setdefault(label, {"files": 0, "flagged_files": 0,
                                               "flagged_segments": 0})
        bucket["files"] += 1
        bucket["flagged_files"] += 1 if n else 0
        bucket["flagged_segments"] += n
        per_file.append({
            "file": final_name,
            "source": label,
            "flagged_segments": n,
            "frame_count": getattr(result, "frame_count", None),
            "variable_frame_rate": getattr(result, "variable_frame_rate", None),
            "segments": [segment_row(s) for s in segments],
        })
        print(f"  {label:28} {final_name:44} {n} segments")

    # An all-errors run must not leave a file of zeros behind that later reads as
    # a real screening. This is the bug that actually happened on Sep 17, 2026.
    if analyzed_ok == 0:
        errors = [r for r in per_file if "error" in r]
        print(f"\n{len(errors)} of {len(clips)} clips failed and none succeeded.",
              file=sys.stderr)
        if errors:
            print(f"  first error: {errors[0]['error']}", file=sys.stderr)
        print("Nothing written. A screening.json full of zeros would read as a "
              "real result later.", file=sys.stderr)
        return 2

    total_segments = sum(b["flagged_segments"] for b in per_source.values())
    sources_with_hits = sum(1 for b in per_source.values() if b["flagged_segments"])

    report: dict = {
        "generated_on": date.today().isoformat(),
        "profile": args.preset,
        "adapter_entry_point": ENTRY_POINT,
        "clips_analyzed_ok": analyzed_ok,
        "clips_failed": len(clips) - analyzed_ok,
        "per_source": per_source,
        "per_file": per_file,
        "totals": {
            "clips": len(clips),
            "flagged_segments": total_segments,
            "sources_with_at_least_one_flag": sources_with_hits,
        },
        "gate2": {
            "min_segments": GATE2_MIN_SEGMENTS,
            "min_sources": GATE2_MIN_SOURCES,
            "passes": total_segments >= GATE2_MIN_SEGMENTS
                      and sources_with_hits >= GATE2_MIN_SOURCES,
            "note": "Planning target from BUILD_PROMPT 2.4, not a spec number. "
                    "Self-filmed positives are counted separately in the README.",
        },
        "renamed_to_hazard": renamed,
    }
    # The per-source positives table and the shooting list for what the pool still lacks. It
    # rebuilds per_source from per_file, splitting the segments by which rule fired, because a
    # flagged segment count with no rule beside it hides whether the red rule ever fired.
    screening_table.enrich(report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")

    print(f"\n{total_segments} flagged segments across {sources_with_hits} sources "
          f"-> {args.out}")
    print(f"  by rule: {report['totals']['segments_by_rule']}")
    print(f"  {report['totals']['red_rule_statement']}")
    print(f"clips analyzed {analyzed_ok}, failed {len(clips) - analyzed_ok}")
    print(f"GATE 2 ({GATE2_MIN_SEGMENTS} segments from {GATE2_MIN_SOURCES} sources): "
          f"{'PASS' if report['gate2']['passes'] else 'short'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
