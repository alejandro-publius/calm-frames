"""Probe a source file.

What the rest of the pipeline needs out of this, and why:

- real frame timestamps, because a variable frame rate file lies if you assume
  a constant fps, and every interval in a hide plan is a time, not a frame
  index;
- colour tags, because the dim model has to know which transfer function the
  picture is encoded with, and an untagged file is read the way flashmap reads
  it (HD as BT.709, SD as BT.601);
- resolution, because the cover still is scaled to it;
- duration, because the last interval is clamped to it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import median

from . import PipelineError
from .ffmpegtool import ffprobe_json, run_ffprobe

# A file is called variable frame rate when the spread of frame intervals is
# wider than this fraction of the median interval. Small jitter in a container
# timebase should not trip it.
VFR_TOLERANCE = 0.02


@dataclass
class StreamInfo:
    index: int
    codec_type: str
    codec_name: str | None = None
    language: str | None = None
    channels: int | None = None
    sample_rate: str | None = None
    disposition_default: bool = False


@dataclass
class VideoProbe:
    path: str
    duration_s: float
    width: int
    height: int
    pix_fmt: str | None
    codec_name: str | None
    color_primaries: str | None
    color_transfer: str | None
    color_space: str | None
    color_range: str | None
    avg_frame_rate: float | None
    frame_count: int
    frame_timestamps_s: list[float] = field(default_factory=list)
    variable_frame_rate: bool = False
    frame_interval_median_s: float | None = None
    frame_interval_min_s: float | None = None
    frame_interval_max_s: float | None = None
    keyframe_times_s: list[float] = field(default_factory=list)
    audio_streams: list[StreamInfo] = field(default_factory=list)
    subtitle_streams: list[StreamInfo] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return self.duration_s * 1000.0

    @property
    def has_audio(self) -> bool:
        return bool(self.audio_streams)

    @property
    def has_subtitles(self) -> bool:
        return bool(self.subtitle_streams)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VideoProbe":
        data = dict(data)
        data["audio_streams"] = [StreamInfo(**s) for s in data.get("audio_streams", [])]
        data["subtitle_streams"] = [
            StreamInfo(**s) for s in data.get("subtitle_streams", [])
        ]
        return cls(**data)


def _parse_rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in value:
        num, _, den = value.partition("/")
        try:
            den_f = float(den)
            if den_f == 0:
                return None
            return float(num) / den_f
        except ValueError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def _stream_info(stream: dict) -> StreamInfo:
    tags = stream.get("tags") or {}
    disposition = stream.get("disposition") or {}
    return StreamInfo(
        index=int(stream.get("index", -1)),
        codec_type=str(stream.get("codec_type", "")),
        codec_name=stream.get("codec_name"),
        language=tags.get("language"),
        channels=stream.get("channels"),
        sample_rate=stream.get("sample_rate"),
        disposition_default=bool(disposition.get("default")),
    )


def video_packet_times(path: str | Path) -> tuple[list[float], list[float]]:
    """Presentation timestamps of every video packet, and of the key packets.

    Packets are used rather than decoded frames because this has to run over a
    2 hour title without decoding it, and the packet pts is the presentation
    time the player will use.
    """
    result = run_ffprobe(
        [
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts_time,flags",
            "-of",
            "csv=print_section=0",
            str(path),
        ]
    )
    times: list[float] = []
    keys: list[float] = []
    for line in result.stdout.splitlines():
        line = line.strip().rstrip(",")
        if not line:
            continue
        parts = line.split(",")
        raw_time = parts[0]
        if raw_time in {"N/A", ""}:
            continue
        try:
            value = float(raw_time)
        except ValueError:
            continue
        times.append(value)
        flags = parts[1] if len(parts) > 1 else ""
        if "K" in flags:
            keys.append(value)
    times.sort()
    keys.sort()
    return times, keys


def probe_video(path: str | Path, *, read_frame_timestamps: bool = True) -> VideoProbe:
    path = Path(path)
    if not path.exists():
        raise PipelineError(f"source file does not exist: {path}")

    data = ffprobe_json(["-show_format", "-show_streams", str(path)])
    streams = data.get("streams") or []
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    if not video_streams:
        raise PipelineError(f"no video stream in {path}")
    video = video_streams[0]

    duration_s = 0.0
    for candidate in (video.get("duration"), (data.get("format") or {}).get("duration")):
        if candidate is None:
            continue
        try:
            duration_s = float(candidate)
            break
        except (TypeError, ValueError):
            continue

    timestamps: list[float] = []
    keyframes: list[float] = []
    if read_frame_timestamps:
        timestamps, keyframes = video_packet_times(path)

    intervals = [b - a for a, b in zip(timestamps, timestamps[1:]) if b > a]
    interval_median = median(intervals) if intervals else None
    interval_min = min(intervals) if intervals else None
    interval_max = max(intervals) if intervals else None
    variable = False
    if interval_median and interval_min is not None and interval_max is not None:
        spread = max(
            abs(interval_max - interval_median), abs(interval_median - interval_min)
        )
        variable = spread > VFR_TOLERANCE * interval_median

    if duration_s <= 0 and timestamps:
        duration_s = timestamps[-1] + (interval_median or 0.0)

    frame_count = len(timestamps)
    if not frame_count:
        try:
            frame_count = int(video.get("nb_frames"))
        except (TypeError, ValueError):
            frame_count = 0

    return VideoProbe(
        path=str(path),
        duration_s=duration_s,
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        pix_fmt=video.get("pix_fmt"),
        codec_name=video.get("codec_name"),
        color_primaries=video.get("color_primaries"),
        color_transfer=video.get("color_transfer"),
        color_space=video.get("color_space"),
        color_range=video.get("color_range"),
        avg_frame_rate=_parse_rate(video.get("avg_frame_rate")),
        frame_count=frame_count,
        frame_timestamps_s=timestamps,
        variable_frame_rate=variable,
        frame_interval_median_s=interval_median,
        frame_interval_min_s=interval_min,
        frame_interval_max_s=interval_max,
        keyframe_times_s=keyframes,
        audio_streams=[_stream_info(s) for s in streams if s.get("codec_type") == "audio"],
        subtitle_streams=[
            _stream_info(s) for s in streams if s.get("codec_type") == "subtitle"
        ],
    )
