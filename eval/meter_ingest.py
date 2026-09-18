#!/usr/bin/env python3
"""Turn the screen-level recordings into results/screen_level.json.

    make ingest-recordings
    .venv/bin/python eval/meter_ingest.py --recordings media/screen_level

**There is no footage yet.** With none, this prints exactly what it is looking for and exits
non-zero, and `results/screen_level.json` is not written at all. A missing file is honest. A file
full of zeros would read as a real result in three weeks' time, and that is the mistake
`eval/screen.py` was written to avoid making twice.

What one take is
----------------
Three recordings and one event file, all sharing a stem, as docs/SCREEN_TEST_PROTOCOL.md sets
out:

    20261008_marker_t01_gray.mov      a still gray screen, for the flicker check and the region
    20261008_marker_t01_chart.mov     the step chart, for the exposure correction
    20261008_marker_t01_run.mov       the run itself, filter on, nobody watching
    20261008_marker_t01_events.json   what the app posted during that take

What comes out
--------------
Per event, from docs/EVAL_PLAN.md section 8:

- **leaks**, of two kinds, counted and reported separately. A *cover leak* is a frame inside a
  declared interval where the screen region is brighter than the covered state by more than the
  tolerance this take's calibration earned. A *flash leak* is a stretch where the meter counts
  more flashes in a second than the spec allows. The first is the sensitive one and the second is
  the one that matters.
- **cover lead time**, where the recording can be tied to the media clock.

How the clock is recovered
--------------------------
`eval/marker_clip.py` draws a reference patch in a corner that the cover leaves uncovered, and
flips it between two close grays every 500 ms. Those flips are a clock written on the screen, so
the recording can be tied to media time without trusting either machine's idea of the hour.

The patch gives **rate and phase**, not absolute media time: every flip looks like every other
one, so an alignment half a second out fits just as well. The absolute part comes from the app's
own event log, and where the log cannot supply it the event is excluded and counted rather than
guessed. That limit is real and it is why the GATE 1 harness, not this file, is the authority on
lead time until both have been run against the same footage.

Safety
------
Run recordings are footage of a screen that was playing flagged content with the filter on. A
leak would make them hazardous, so nothing here opens, plays or previews one. They are decoded,
measured and plotted, and that is all.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

_EVAL_DIR = Path(__file__).resolve().parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

import meter  # noqa: E402
from metrics import wilson  # noqa: E402

REPO = _EVAL_DIR.parent
DEFAULT_RECORDINGS = REPO / "media" / "screen_level"
DEFAULT_SCHEDULE = REPO / "eval" / "harness_runs" / "marker_schedule.json"
OUT = REPO / "results" / "screen_level.json"

VIDEO_SUFFIXES = (".mov", ".mp4", ".m4v", ".mkv")
STEM = re.compile(
    r"^(?P<date>\d{8})_(?P<session>[a-z0-9-]+)_(?P<take>t\d+)_(?P<kind>gray|chart|run)$"
)

# How far into the covered plateau a frame has to rise to count as a cover leak, on top of the
# tolerance the calibration earned. Instrument tuning, not a threshold from a spec.
COVER_LEAK_MARGIN = 0.01
# A cover counts as fully on once the screen region has been inside the covered band for this
# long. Shorter than any cover the app holds, long enough to ignore one noisy frame.
COVER_SETTLE_MS = 40.0


@dataclass
class Take:
    stem: str
    session: str
    take: str
    gray: Path | None = None
    chart: Path | None = None
    run: Path | None = None
    events: Path | None = None
    problems: list[str] = field(default_factory=list)

    def complete(self) -> bool:
        return all((self.gray, self.chart, self.run, self.events))

    def missing(self) -> list[str]:
        return [
            name
            for name, value in (
                ("gray", self.gray),
                ("chart", self.chart),
                ("run", self.run),
                ("events", self.events),
            )
            if value is None
        ]


def discover_takes(directory: Path) -> list[Take]:
    """Group the files in the recordings directory into takes by their stem."""
    takes: dict[str, Take] = {}
    if not directory.is_dir():
        return []
    for path in sorted(directory.iterdir()):
        if path.name.startswith("."):
            continue
        stem = path.stem
        if path.suffix.lower() in VIDEO_SUFFIXES:
            match = STEM.match(stem)
            if not match:
                continue
            key = f"{match['date']}_{match['session']}_{match['take']}"
            entry = takes.setdefault(
                key, Take(stem=key, session=match["session"], take=match["take"])
            )
            setattr(entry, match["kind"], path)
        elif path.suffix.lower() == ".json" and stem.endswith("_events"):
            key = stem[: -len("_events")]
            match = re.match(r"^(\d{8})_([a-z0-9-]+)_(t\d+)$", key)
            if not match:
                continue
            entry = takes.setdefault(
                key, Take(stem=key, session=match.group(2), take=match.group(3))
            )
            entry.events = path
    return [takes[key] for key in sorted(takes)]


# ----------------------------------------------------------------- reading a recording


def patch_rect(schedule: dict) -> tuple[float, float, float, float]:
    """The reference patch, as fractions of the picture, from the committed schedule."""
    clip = schedule["clip"]
    patch = schedule["reference_patch"]
    return (
        patch["x"] / clip["width"],
        patch["y"] / clip["height"],
        (patch["x"] + patch["width"]) / clip["width"],
        (patch["y"] + patch["height"]) / clip["height"],
    )


def series_from_recording(
    path: Path,
    roi: meter.Roi,
    calibration: meter.Calibration,
    settings: meter.InstrumentSettings,
    patch: tuple[float, float, float, float] | None,
) -> dict[str, object]:
    """Luminance over time for the picture and for the reference patch, plus a meter run.

    One decode, two questions. The meter answers "was anything flashing"; the two luminance
    series answer "when did the cover go on" and "what time was it on the screen".
    """
    spec = meter.load_spec()
    instrument = meter.Meter(roi=roi, calibration=calibration, settings=settings, spec=spec)
    times: list[float] = []
    picture: list[float] = []
    patch_series: list[float] = []
    for frame, time_ms in meter.decode_frames(str(path), width=settings.working_width):
        instrument.feed(frame, time_ms)
        # The same grid the meter counts on. A two minute take at 240 fps is 28,800 frames, and
        # doing this at full crop resolution would take longer than the filming did.
        grid = meter._downsample(roi.crop(np.asarray(frame)), settings.analysis_width)
        linear = calibration.apply(grid)
        luminance = meter._luminance(spec, linear)
        height, width = luminance.shape
        if patch is not None:
            px0 = int(patch[0] * width)
            py0 = int(patch[1] * height)
            px1 = max(px0 + 1, int(patch[2] * width))
            py1 = max(py0 + 1, int(patch[3] * height))
            patch_series.append(float(luminance[py0:py1, px0:px1].mean()))
            masked = luminance.copy()
            masked[py0:py1, px0:px1] = np.nan
            picture.append(float(np.nanmean(masked)))
        else:
            picture.append(float(luminance.mean()))
        times.append(time_ms)
    return {
        "times_ms": times,
        "picture": picture,
        "patch": patch_series,
        "report": instrument.report({"source": str(path)}),
        "meter": instrument,
    }


def detect_edges(times: list[float], values: list[float]) -> list[dict[str, float]]:
    """Times at which a two level signal crossed the middle, by linear interpolation.

    The two levels are taken as the 10th and 90th percentiles of the signal, so a slow drift in
    exposure moves both and the middle with them. A crossing counts only after the signal has
    been on one side by a quarter of the gap, which keeps noise from ringing the doorbell.
    """
    if len(values) < 4:
        return []
    array = np.asarray(values, dtype=np.float64)
    low, high = np.percentile(array, [10, 90])
    gap = float(high - low)
    if gap <= 0:
        return []
    middle = (low + high) / 2.0
    hysteresis = gap * 0.25
    edges: list[dict[str, float]] = []
    state = 1 if array[0] > middle else -1
    for index in range(1, len(array)):
        value = array[index]
        if state > 0 and value < middle - hysteresis:
            crossing = _interpolate_crossing(times, array, index, middle)
            edges.append({"time_ms": crossing, "direction": -1.0})
            state = -1
        elif state < 0 and value > middle + hysteresis:
            crossing = _interpolate_crossing(times, array, index, middle)
            edges.append({"time_ms": crossing, "direction": 1.0})
            state = 1
    return edges


def _interpolate_crossing(
    times: list[float], values: np.ndarray, index: int, level: float
) -> float:
    """Where between two samples the signal passed the level. Sub frame, which is the point."""
    for back in range(index, 0, -1):
        a, b = values[back - 1], values[back]
        if (a - level) * (b - level) <= 0 and a != b:
            span = times[back] - times[back - 1]
            return float(times[back - 1] + span * (level - a) / (b - a))
    return float(times[index])


def fit_clock(
    edges: list[dict[str, float]],
    period_ms: float,
    anchor_media_ms: float | None,
    recording_start_ms: float,
) -> dict[str, object]:
    """Tie recording time to media time, using the reference patch as the clock on the screen.

    Returns the fit `recording_ms = rate * media_ms + offset`, its residuals, and how it was
    anchored.

    The patch gives rate and phase. It cannot give absolute media time, because every flip looks
    exactly like every other one. The absolute part comes from `anchor_media_ms`, the media
    position the app says the recording opens at. The check on that claim is the first flip: the
    log says where in the media we are, so it says when the next flip is due, and if the flip
    that actually turned up is more than half a period away from that, the log is wrong by more
    than this method can repair and the take is refused rather than aligned to the wrong flip.
    """
    if len(edges) < 4:
        return {"anchored": False, "reason": f"only {len(edges)} patch edges in the recording"}
    observed = np.asarray([e["time_ms"] for e in edges], dtype=np.float64)
    steps = np.diff(observed)
    rate = float(np.median(steps) / period_ms)
    if not (0.9 <= rate <= 1.1):
        return {
            "anchored": False,
            "reason": (
                f"the patch flips every {np.median(steps):.1f} ms in the recording against "
                f"{period_ms:.0f} ms in the media, which is a rate of {rate:.3f}. That is not a "
                "clock, it is a different signal."
            ),
        }
    if anchor_media_ms is None:
        return {
            "anchored": False,
            "rate": rate,
            "reason": "the event file did not say what media time the recording starts at",
        }

    first_index = int(np.floor(anchor_media_ms / period_ms)) + 1
    expected_first = recording_start_ms + (first_index * period_ms - anchor_media_ms)
    slip_ms = float(observed[0] - expected_first)
    if abs(slip_ms) > period_ms / 2.0:
        return {
            "anchored": False,
            "rate": rate,
            "anchor_slip_ms": slip_ms,
            "reason": (
                f"the log puts the first patch flip at {expected_first:.0f} ms into the "
                f"recording and it arrives at {observed[0]:.0f} ms, {slip_ms:+.0f} ms away. That "
                f"is more than half of the {period_ms:.0f} ms period, so the flips cannot be "
                "matched to the media without guessing which one is which."
            ),
        }

    media_times = np.asarray(
        [(first_index + step) * period_ms for step in range(len(observed))], dtype=np.float64
    )
    design = np.stack([media_times, np.ones_like(media_times)], axis=1)
    solution, *_ = np.linalg.lstsq(design, observed, rcond=None)
    fitted = design @ solution
    residuals = observed - fitted
    return {
        "anchored": True,
        "rate": float(solution[0]),
        "offset_ms": float(solution[1]),
        "edges": len(observed),
        "max_residual_ms": float(np.abs(residuals).max()),
        "rms_residual_ms": float(np.sqrt((residuals**2).mean())),
        "anchor_slip_ms": slip_ms,
        "anchor_media_ms": float(anchor_media_ms),
    }


def to_recording_ms(clock: dict, media_ms: float) -> float:
    return float(clock["rate"]) * media_ms + float(clock["offset_ms"])


def covered_reference(
    picture: list[float], times: list[float], from_ms: float, to_ms: float
) -> float:
    """The covered level, read off the recording itself.

    The tenth percentile of the picture over the interval and the half second before it, rather
    than the median. A cover that went on late leaves bright frames at the start, and a median
    would pull the reference up to meet them, which is the one direction that hides a leak. The
    darkest sustained level is the cover, and anything above it by more than the tolerance is
    light getting through.

    It is still taken from the take under test, so a cover that leaked for most of an interval
    would raise this floor. The reference and the minimum are both reported so that case is
    visible rather than silent.
    """
    window = [
        value
        for value, time_ms in zip(picture, times)
        if from_ms - 500.0 <= time_ms <= to_ms
    ]
    if not window:
        return float(np.percentile(picture, 10))
    return float(np.percentile(window, 10))


# ----------------------------------------------------------------- one take


def ingest_take(
    take: Take,
    schedule: dict,
    settings: meter.InstrumentSettings,
) -> dict[str, object]:
    """Everything one take can say. Refusals are recorded, never worked around."""
    row: dict[str, object] = {"take": take.stem, "session": take.session}
    if not take.complete():
        row["excluded"] = f"missing {', '.join(take.missing())}"
        return row

    # Any failure here excludes this take and no other. One recording the decoder cannot open
    # must not cost the other 199 events, so this catches everything and records it, which is
    # also why the caller can trust that a take either has numbers or has a reason.
    try:
        gray_frames, gray_times = meter.sample_frames_and_times(
            str(take.gray), width=settings.working_width, count=settings.roi_sample_frames
        )
        roi = meter.find_roi(gray_frames, settings)
        chart_frames = meter.sample_frames(
            str(take.chart), width=settings.working_width, count=settings.roi_sample_frames
        )
        calibration = meter.calibrate(chart_frames, roi, settings=settings)
    except Exception as exc:  # noqa: BLE001
        row["excluded"] = f"{type(exc).__name__}: {exc}"
        return row

    flicker = meter.flicker_check(gray_frames, gray_times, roi, calibration, settings=settings)
    row["roi"] = roi.as_dict()
    row["calibration"] = calibration.as_dict()
    row["flicker_check"] = flicker
    if not flicker["passes"]:
        row["excluded"] = (
            f"the gray field ripples by {flicker['peak_to_peak']:.4f} in relative luminance, "
            f"over this take's tolerance of {flicker['tolerance']:.4f}"
        )
        return row

    events = json.loads(Path(take.events).read_text())
    if events.get("aborted"):
        row["excluded"] = "the take was marked aborted"
        return row

    measured = series_from_recording(
        Path(take.run), roi, calibration, settings, patch_rect(schedule)
    )
    report = measured["report"]
    row["meter"] = {
        "peak_flashes_per_second": report.headline["peak_flashes_per_second"],
        "above_limit": report.headline["above_limit"],
        "flash_leaks": report.headline["leaks"],
        "publishable": report.publishable,
        "warnings": report.quality["warnings"],
        "frames": report.quality["frames"],
        "fps_measured": report.quality["fps_measured"],
    }
    times = measured["times_ms"]
    clock = fit_clock(
        detect_edges(times, measured["patch"]),
        period_ms=500.0,
        anchor_media_ms=events.get("recording_start_media_ms"),
        recording_start_ms=times[0] if times else 0.0,
    )
    row["clock"] = clock

    tolerance = calibration.max_residual + COVER_LEAK_MARGIN
    intervals = events.get("intervals") or []
    row["events"] = [
        _score_interval(interval, measured, clock, tolerance, settings)
        for interval in intervals
    ]
    return row


def _score_interval(
    interval: dict,
    measured: dict,
    clock: dict,
    tolerance: float,
    settings: meter.InstrumentSettings,
) -> dict[str, object]:
    """One scheduled cover, against what the recording shows."""
    out: dict[str, object] = {
        "interval": interval,
        "tolerance": tolerance,
    }
    if not clock.get("anchored"):
        out["excluded"] = f"no media clock: {clock.get('reason')}"
        return out

    times = measured["times_ms"]
    picture = measured["picture"]
    start_media = float(interval["start_ms"])
    cover_media = float(interval.get("cover_on_ms", start_media))
    start_rec = to_recording_ms(clock, start_media)
    cover_rec = to_recording_ms(clock, cover_media)
    end_rec = to_recording_ms(clock, float(interval["end_ms"]))

    # Condition 1 of docs/EVAL_PLAN.md section 8.
    if not times or times[0] > cover_rec - 1000.0 or times[-1] < start_rec + 500.0:
        out["excluded"] = (
            "the recording does not cover from 1 s before the cover to 0.5 s after the interval "
            "starts"
        )
        return out

    reference = covered_reference(picture, times, start_rec, end_rec)
    ceiling = reference + tolerance
    leaks = [
        {"time_ms": time_ms, "luminance": value, "over_by": value - ceiling}
        for time_ms, value in zip(times, picture)
        if start_rec <= time_ms <= end_rec and value > ceiling
    ]

    # When did the cover go on? Walk back from the interval start through the frames that are
    # inside the covered band, and the earliest one still in that unbroken run is the answer.
    # Walking forwards would find the first quiet moment in the take instead, which is not the
    # same thing when a cover goes on, off and on again.
    last_before = None
    for index, time_ms in enumerate(times):
        if time_ms > start_rec:
            break
        last_before = index
    settled = None
    if last_before is not None:
        index = last_before
        while index >= 0 and picture[index] <= ceiling:
            settled = times[index]
            index -= 1
        if settled is not None and times[last_before] - settled < COVER_SETTLE_MS:
            settled = None

    out["cover_on_recording_ms"] = settled
    out["interval_start_recording_ms"] = start_rec
    out["lead_ms"] = None if settled is None else start_rec - settled
    out["cover_leak_frames"] = len(leaks)
    out["worst_leak"] = max((leak["over_by"] for leak in leaks), default=0.0)
    out["covered_reference"] = reference
    out["lowest_in_interval"] = min(
        (value for time_ms, value in zip(times, picture) if start_rec <= time_ms <= end_rec),
        default=None,
    )
    return out


# ----------------------------------------------------------------- the report


def _rate(successes: int, trials: int) -> dict[str, object]:
    lo, hi = wilson(successes, trials)
    return {
        "numerator": successes,
        "denominator": trials,
        "value": (successes / trials) if trials else None,
        "wilson_lo": lo,
        "wilson_hi": hi,
    }


def summarise(rows: list[dict]) -> dict[str, object]:
    events = [
        event
        for row in rows
        for event in row.get("events", [])
        if "excluded" not in event
    ]
    excluded = [
        event for row in rows for event in row.get("events", []) if "excluded" in event
    ]
    leads = [e["lead_ms"] for e in events if e.get("lead_ms") is not None]
    leaked = sum(1 for e in events if e["cover_leak_frames"] > 0)
    flash_leaks = sum(int(row.get("meter", {}).get("flash_leaks", 0)) for row in rows)
    summary: dict[str, object] = {
        "takes": len(rows),
        "takes_excluded": sum(1 for row in rows if "excluded" in row),
        "events_counted": len(events),
        "events_excluded": len(excluded),
        "events_with_a_cover_leak": _rate(leaked, len(events)),
        "flash_leaks_across_all_takes": flash_leaks,
        "interval_method": (
            "Wilson score interval, 95%, two sided, no continuity correction, from "
            "eval/metrics.py. Events inside one take are not independent, so this interval is "
            "read as the spread over events and not as a confidence statement about a household."
        ),
    }
    if leads:
        array = np.asarray(leads, dtype=np.float64)
        summary["cover_lead_ms"] = {
            "n": len(leads),
            "median": float(np.median(array)),
            "p95": float(np.percentile(array, 95)),
            "worst": float(array.min()),
        }
    else:
        summary["cover_lead_ms"] = None
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--recordings", type=Path, default=DEFAULT_RECORDINGS)
    parser.add_argument("--schedule", type=Path, default=DEFAULT_SCHEDULE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)

    takes = discover_takes(args.recordings)
    usable = [take for take in takes if take.complete()]
    print(f"{len(takes)} takes in {args.recordings}, {len(usable)} of them complete")
    for take in takes:
        if not take.complete():
            print(f"  {take.stem}: missing {', '.join(take.missing())}")

    if not usable:
        print(
            "\nNothing written. results/screen_level.json stays absent rather than carrying "
            "numbers nobody filmed.",
            file=sys.stderr,
        )
        print("Each take needs four files with the same stem:", file=sys.stderr)
        print("  <date>_<session>_<take>_gray.mov", file=sys.stderr)
        print("  <date>_<session>_<take>_chart.mov", file=sys.stderr)
        print("  <date>_<session>_<take>_run.mov", file=sys.stderr)
        print("  <date>_<session>_<take>_events.json", file=sys.stderr)
        print("docs/SCREEN_TEST_PROTOCOL.md has the whole thing.", file=sys.stderr)
        return 2

    schedule = json.loads(args.schedule.read_text())
    rows = [ingest_take(take, schedule, meter.InstrumentSettings()) for take in usable]
    for row in rows:
        state = row.get("excluded") or (
            f"{len(row.get('events', []))} events, "
            f"{row.get('meter', {}).get('flash_leaks', 0)} flash leaks"
        )
        print(f"  {row['take']}: {state}")

    payload = {
        "generated_on": date.today().isoformat(),
        "tool": "eval/meter_ingest.py",
        "meter_version": meter.METER_VERSION,
        "schedule": {
            "path": str(args.schedule.relative_to(REPO)),
            "clip_sha256": schedule.get("clip", {}).get("sha256"),
        },
        "thresholds": meter.load_spec().as_dict(),
        "instrument": meter.InstrumentSettings().as_dict(),
        "statement": (
            "Measured through a camera on a filmed screen. Cover leaks are luminance above the "
            "covered state for that take, flash leaks are the WCAG limit being passed. Lead "
            "times are tied to media time through the reference patch and the app's own event "
            "log, so an event whose log did not say where it started is excluded and counted."
        ),
        "summary": summarise(rows),
        "takes": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
