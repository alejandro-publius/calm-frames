"""Putting it together: decode, find the picture, track flashes, slide the windows.

The analyser is a stream. `StreamingAnalyzer.push` takes any number of frames at a time and
carries its state forward, so feeding a file in chunks gives exactly the same answer as feeding
it whole. Frames whose timestamp has already been seen are dropped, which is what makes an
overlap between chunks harmless.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from . import color as color_math
from .area import AreaWindow, max_coverage, wcag_reference_window
from .decode import (
    AnalysisFrame,
    ColorPolicy,
    SourceInfo,
    UnsupportedInput,
    iter_frames,
    probe,
)
from .flash import GeneralFlashTracker, RedFlashTracker
from .picture import (
    CARRIED,
    DETECTED,
    CarriedPicture,
    LetterboxSettings,
    PictureRect,
    detect_picture,
    rect_in_frame,
)
from .profiles import Profile
from .room import RoomSetting, room_window

__all__ = [
    "Segment",
    "AnalysisResult",
    "StreamingAnalyzer",
    "analyze_file",
    "build_area_windows",
]


@dataclass
class Segment:
    start_ms: float
    end_ms: float
    flash_first_ms: float
    flash_last_ms: float
    reason: str
    area_fraction: float
    area_window: str
    triggered_by: list[str]
    breaks_baseline: bool
    max_flashes_in_window: int

    def as_dict(self) -> dict[str, object]:
        return {
            "start_ms": int(round(self.start_ms)),
            "end_ms": int(round(self.end_ms)),
            "flash_first_ms": int(round(self.flash_first_ms)),
            "flash_last_ms": int(round(self.flash_last_ms)),
            "reason": self.reason,
            "area_fraction": round(float(self.area_fraction), 6),
            "area_window": self.area_window,
            "triggered_by": sorted(self.triggered_by),
            "breaks_baseline": self.breaks_baseline,
            "max_flashes_in_window": int(self.max_flashes_in_window),
        }


@dataclass
class AnalysisResult:
    source: SourceInfo
    picture: PictureRect
    profile: Profile
    area_windows: list[AreaWindow]
    room: RoomSetting | None
    segments: list[Segment]
    frame_count: int
    first_pts_ms: float | None
    last_pts_ms: float | None
    variable_frame_rate: bool
    frame_interval_ms: dict[str, float]
    picture_source: str = DETECTED
    """`detected` or `carried`, see flashmap.picture."""
    detected_picture: PictureRect | None = None
    """What this file's own detector found. Recorded even when a rectangle was carried in, so
    a reader can see how far the two are apart without analysing the file again."""

    @property
    def passes(self) -> bool:
        return not self.segments

    @property
    def hidden_ms(self) -> float:
        merged: list[list[float]] = []
        for segment in sorted(self.segments, key=lambda s: s.start_ms):
            if merged and segment.start_ms <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], segment.end_ms)
            else:
                merged.append([segment.start_ms, segment.end_ms])
        return sum(end - start for start, end in merged)


def build_area_windows(
    profile: Profile,
    picture: PictureRect,
    room: RoomSetting | None,
) -> list[AreaWindow]:
    """The baseline window for the profile, then the room window if there is one.

    The room window is appended. It never replaces the baseline, so the analyser's "largest
    coverage over all windows" can only go up when a room is given.
    """
    if profile.area_window_mode == "whole-picture":
        windows = [
            AreaWindow(
                name="bt1702-screen",
                width_px=picture.width,
                height_px=picture.height,
                source="ITU-R BT.1702-3 Annex 1 Guideline 1, 25% of the displayed screen area",
            )
        ]
    else:
        windows = [wcag_reference_window(picture.width, picture.height)]
    if room is not None:
        windows.append(
            room_window(
                room,
                frame_width=picture.frame_width,
                frame_height=picture.frame_height,
                picture_width=picture.width,
                picture_height=picture.height,
            )
        )
    return windows


class _OpenSegment:
    __slots__ = (
        "start",
        "end",
        "flash_first",
        "flash_last",
        "area_fraction",
        "area_window",
        "triggers",
        "flashes",
    )

    def __init__(self, start: float, end: float) -> None:
        self.start = start
        self.end = end
        self.flash_first = float("inf")
        self.flash_last = float("-inf")
        self.area_fraction = 0.0
        self.area_window = ""
        self.triggers: set[str] = set()
        self.flashes = 0


class StreamingAnalyzer:
    """Feed it frames, in any grouping, and ask for the result at the end."""

    def __init__(
        self,
        profile: Profile,
        picture: PictureRect,
        area_windows: list[AreaWindow],
        baseline_window_names: frozenset[str] | None = None,
    ) -> None:
        self.profile = profile
        self.picture = picture
        self.area_windows = area_windows
        self.baseline_window_names = (
            baseline_window_names
            if baseline_window_names is not None
            else frozenset(w.name for w in area_windows if not w.name.startswith("room"))
        )
        self._general = GeneralFlashTracker(
            min_delta=profile.general.min_delta,
            dark_image_below=profile.general.dark_image_below,
        )
        self._red = RedFlashTracker(
            saturated_ratio=profile.red.saturated_red_ratio,
            min_distance=profile.red.min_ucs_distance,
        )
        self._events: dict[str, deque[tuple[float, NDArray[np.bool_]]]] = {
            "general": deque(),
            "red": deque(),
        }
        self._open: dict[str, _OpenSegment | None] = {"general": None, "red": None}
        self._closed: list[Segment] = []
        self._last_pts: float | None = None
        self._first_pts: float | None = None
        self.frame_count = 0
        self._intervals: list[float] = []

    # ---- feeding ----------------------------------------------------------------

    def push(self, frames: Iterable[AnalysisFrame]) -> None:
        for frame in frames:
            if self._last_pts is not None and frame.pts_ms <= self._last_pts:
                continue
            if self._last_pts is not None:
                self._intervals.append(frame.pts_ms - self._last_pts)
            if self._first_pts is None:
                self._first_pts = frame.pts_ms
            self._last_pts = frame.pts_ms
            self.frame_count += 1
            self._step(frame)

    def _step(self, frame: AnalysisFrame) -> None:
        rgb = self.picture.crop(frame.rgb)
        linear = color_math.srgb_to_linear(rgb)

        if self.profile.general.metric == "wcag-relative-luminance":
            metric = color_math.relative_luminance(linear)
        elif self.profile.general.metric == "bt1886-nits":
            level = self.picture.crop(frame.video_level)
            peak = self.profile.peak_nits if self.profile.peak_nits is not None else 200.0
            metric = color_math.bt1886_nits(level, peak)
        else:  # pragma: no cover - guarded by profiles
            raise ValueError(f"unknown metric {self.profile.general.metric!r}")

        general_mask = self._general.step(metric)
        self._record("general", frame.pts_ms, general_mask)

        xyz = color_math.linear_rgb_to_xyz(linear)
        u_prime, v_prime = color_math.ucs_1976(xyz)
        ratio = color_math.red_ratio(linear)
        red_mask = self._red.step(u_prime, v_prime, ratio)
        self._record("red", frame.pts_ms, red_mask)

    def _record(self, kind: str, pts_ms: float, mask: NDArray[np.bool_]) -> None:
        events = self._events[kind]
        events.append((pts_ms, mask))
        window_ms = float(self.profile.window_ms)
        while events and events[0][0] < pts_ms - window_ms:
            events.popleft()

        counts = np.zeros(mask.shape, dtype=np.int16)
        for _, older in events:
            counts += older
        failing = counts > self.profile.flash_limit_per_second
        if not failing.any():
            self._close_if_stale(kind, pts_ms)
            return

        coverages = {
            window.name: max_coverage(failing, window.height_px, window.width_px)
            for window in self.area_windows
        }
        over = [name for name, value in coverages.items() if value > self.profile.area_fraction_limit]
        if not over:
            self._close_if_stale(kind, pts_ms)
            return

        best_name = max(coverages, key=lambda name: coverages[name])
        # The hidden interval is the failing one-second period itself. That always contains the
        # flashing, and it starts before it, which is the direction a safety layer wants to err
        # in. The tight bounds of the offending flashes go in the map as well.
        start = max(0.0, pts_ms - window_ms)
        flash_first = flash_last = pts_ms
        for stamp, older in events:
            if bool((older & failing).any()):
                flash_first = stamp
                break
        for stamp, older in reversed(events):
            if bool((older & failing).any()):
                flash_last = stamp
                break

        open_segment = self._open[kind]
        if open_segment is not None and start <= open_segment.end:
            open_segment.end = max(open_segment.end, pts_ms)
        else:
            if open_segment is not None:
                self._flush(kind)
            open_segment = _OpenSegment(start, pts_ms)
            self._open[kind] = open_segment
        open_segment.flash_first = min(open_segment.flash_first, flash_first)
        open_segment.flash_last = max(open_segment.flash_last, flash_last)
        open_segment.triggers.update(over)
        value = coverages[best_name]
        if value > open_segment.area_fraction:
            open_segment.area_fraction = value
            open_segment.area_window = best_name
        open_segment.flashes = max(open_segment.flashes, int(counts[failing].max()))

    def _close_if_stale(self, kind: str, pts_ms: float) -> None:
        open_segment = self._open[kind]
        if open_segment is not None and pts_ms > open_segment.end:
            self._flush(kind)

    def _flush(self, kind: str) -> None:
        open_segment = self._open[kind]
        if open_segment is None:
            return
        self._closed.append(
            Segment(
                start_ms=open_segment.start,
                end_ms=open_segment.end,
                flash_first_ms=open_segment.flash_first,
                flash_last_ms=open_segment.flash_last,
                reason=kind,
                area_fraction=open_segment.area_fraction,
                area_window=open_segment.area_window,
                triggered_by=sorted(open_segment.triggers),
                breaks_baseline=bool(open_segment.triggers & self.baseline_window_names),
                max_flashes_in_window=open_segment.flashes,
            )
        )
        self._open[kind] = None

    # ---- results ----------------------------------------------------------------

    def segments(self) -> list[Segment]:
        for kind in ("general", "red"):
            self._flush(kind)
        return sorted(self._closed, key=lambda s: (s.start_ms, s.reason))

    def interval_stats(self) -> tuple[bool, dict[str, float]]:
        if not self._intervals:
            return False, {"min": 0.0, "max": 0.0, "median": 0.0}
        values = np.asarray(self._intervals, dtype=np.float64)
        stats = {
            "min": float(values.min()),
            "max": float(values.max()),
            "median": float(np.median(values)),
        }
        variable = bool(stats["max"] - stats["min"] > 1.0)
        return variable, stats

    @property
    def first_pts_ms(self) -> float | None:
        return self._first_pts

    @property
    def last_pts_ms(self) -> float | None:
        return self._last_pts


def _chunked(
    frames: Iterator[AnalysisFrame], chunk_frames: int, overlap: int
) -> Iterator[list[AnalysisFrame]]:
    """Cut a frame stream into chunks that re-send the last `overlap` frames of the one before."""
    if chunk_frames < 1:
        raise ValueError("chunk_frames must be at least 1")
    if overlap < 0 or overlap >= chunk_frames:
        raise ValueError("overlap must be at least 0 and smaller than chunk_frames")
    carry: list[AnalysisFrame] = []
    batch: list[AnalysisFrame] = []
    for frame in frames:
        batch.append(frame)
        if len(batch) == chunk_frames:
            yield carry + batch
            carry = batch[len(batch) - overlap :] if overlap else []
            batch = []
    if batch:
        yield carry + batch


def analyze_file(
    path: str | Path,
    profile: Profile,
    room: RoomSetting | None = None,
    policy: ColorPolicy = ColorPolicy(),
    analysis_width: int = 192,
    letterbox: LetterboxSettings = LetterboxSettings(),
    sample_frames: int = 16,
    chunk_frames: int | None = None,
    chunk_overlap: int = 0,
    carried_picture: CarriedPicture | None = None,
) -> AnalysisResult:
    """Analyse one file end to end.

    `chunk_frames` only changes how frames are handed to the analyser. The answer is the same
    either way, and tests/test_chunking.py holds that to it.

    `carried_picture` is the picture rectangle out of another file's map, for when this file is
    a re-encode of that one. Re-encoding nudges the outermost rows and columns, so a detector
    run on the re-encode can find a bar one row taller or shorter than the one in the original.
    Every area fraction is measured against the picture, so one row is enough to lift a span
    over the limit and flag content the original did not. Carrying the rectangle keeps both
    measured on the same ground. The detector still runs, and what it found is reported.
    """
    info = probe(path, policy=policy, analysis_width=analysis_width)
    detected = _detect_picture(path, info, letterbox, sample_frames)
    if carried_picture is None:
        picture, picture_source = detected, DETECTED
    else:
        if (
            carried_picture.coded_width != info.coded_width
            or carried_picture.coded_height != info.coded_height
        ):
            raise UnsupportedInput(
                f"the carried picture rectangle came from a "
                f"{carried_picture.coded_width}x{carried_picture.coded_height} frame and "
                f"{path} is {info.coded_width}x{info.coded_height}. A rectangle from a "
                "different frame size does not describe this file."
            )
        picture = rect_in_frame(carried_picture, info.analysis_width, info.analysis_height)
        picture_source = CARRIED
    windows = build_area_windows(profile, picture, room)
    analyzer = StreamingAnalyzer(profile, picture, windows)

    frames = iter_frames(path, info)
    if chunk_frames is None:
        analyzer.push(frames)
    else:
        for batch in _chunked(frames, chunk_frames, chunk_overlap):
            analyzer.push(batch)

    variable, stats = analyzer.interval_stats()
    return AnalysisResult(
        source=info,
        picture=picture,
        profile=profile,
        area_windows=windows,
        room=room,
        segments=analyzer.segments(),
        frame_count=analyzer.frame_count,
        first_pts_ms=analyzer.first_pts_ms,
        last_pts_ms=analyzer.last_pts_ms,
        variable_frame_rate=variable,
        frame_interval_ms=stats,
        picture_source=picture_source,
        detected_picture=detected,
    )


def _detect_picture(
    path: str | Path,
    info: SourceInfo,
    letterbox: LetterboxSettings,
    sample_frames: int,
) -> PictureRect:
    samples: list[NDArray[np.float32]] = []
    stride = 1
    index = 0
    for frame in iter_frames(path, info):
        if index % stride == 0:
            linear = color_math.srgb_to_linear(frame.rgb)
            samples.append(color_math.relative_luminance(linear))
            if len(samples) > sample_frames:
                # Budget is full, so keep every second sample and widen the stride. The kept
                # samples stay spread over the whole file however long it turns out to be.
                samples = samples[::2]
                stride *= 2
        index += 1
    if not samples:
        raise UnsupportedInput(f"{path} decoded no frames")
    return detect_picture(samples, letterbox)
