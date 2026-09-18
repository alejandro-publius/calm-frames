"""ffmpeg work: the kid safe rendition, and the cover model verify checks.

Two renders live here.

1. The kid safe rendition (Plan B). The picture is replaced by a still poster
   frame for every flagged span plus its guard band, using an overlay gated by
   ``enable='between(t,a,b)'``. Audio is stream copied and caption cues are
   carried through, because hiding the picture must never take the sound or
   the captions with it.

2. The cover model. The on-device cover schedule is drawn over the ORIGINAL
   video so flashmap can be run on what a child would actually see if the
   pre-covered rendition were not there. Red intervals are modelled as an
   opaque black cover. General intervals are modelled as dim, because dim is
   the least protective cover the device may draw and therefore the strictest
   test of the plan.

Dim and linear light
--------------------
Dim mode means the covered picture keeps at most 10 percent of its light,
measured in linear light. This ffmpeg build has no zscale filter, so the
multiplication is done on code values using the identity that holds for a
power law transfer function:

    out_code = OETF(alpha * EOTF(in_code))
             = ((alpha * (in_code ** gamma)) ** (1 / gamma))
             = in_code * alpha ** (1 / gamma)

So scaling code values by ``alpha ** (1 / gamma)`` is the same as scaling
light by ``alpha``. The gamma comes from the file's transfer tag: 2.4 for
BT.1886, which is what a television applies to BT.709 content, and 2.2 for
sRGB. An untagged file is modelled with 2.4, which gives the brighter, and so
the harder to pass, result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from . import PipelineError
from . import ffmpegtool
from .hideplan import DIM, DIM_MAX_LUMINANCE, OPAQUE, CoverInterval, HidePlan, cover_mode
from .probe import VideoProbe

BT1886_GAMMA = 2.4
SRGB_GAMMA = 2.2

DEFAULT_CRF = 20
DEFAULT_PRESET = "veryfast"
# The verify render feeds an analyzer, so it is kept close to lossless: codec
# noise must not be able to hide a flash that the cover failed to stop.
DEFAULT_VERIFY_CRF = 10
DEFAULT_HLS_SEGMENT_S = 4.0

TEXT_SUBTITLE_CODECS = {"subrip", "srt", "mov_text", "ass", "ssa", "webvtt", "text"}

# The cover card for a title that flashes end to end and has no calm frame to take a still
# from. A flat dark neutral grey: dark enough that it can never be the bright side of a flash,
# light enough to read as a card someone meant to put there rather than a dead screen. It is
# a look choice, not a number from a spec, and verify does not take it on trust: it measures
# the card and refuses anything that is not one flat colour.
NEUTRAL_STILL_RGB = (40, 40, 40)


@dataclass
class RenderResult:
    path: Path
    cmd: list[str] = field(default_factory=list)
    notes: dict = field(default_factory=dict)


def transfer_gamma(probe: VideoProbe) -> float:
    """The display gamma used to model dimming in linear light."""
    transfer = (probe.color_transfer or "").lower()
    if transfer in {"iec61966-2-1", "srgb"}:
        return SRGB_GAMMA
    # bt709, bt470bg, smpte170m, unspecified and anything else: a television
    # applies the BT.1886 2.4 power law. 2.4 also gives the brighter result of
    # the two, so an untagged file is modelled the stricter way.
    return BT1886_GAMMA


def linear_dim_code_scale(alpha: float, gamma: float) -> float:
    """Code value multiplier that scales light by ``alpha``."""
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be greater than 0 and at most 1")
    if gamma <= 0:
        raise ValueError("gamma must be positive")
    return alpha ** (1.0 / gamma)


def enable_expression(intervals: Sequence[CoverInterval]) -> str | None:
    """``between(t,a,b)`` terms, summed, for an ffmpeg timeline ``enable``.

    ffmpeg treats any non zero value as enabled, so summing the terms is an OR
    over the spans. Returns None when there is nothing to cover, which callers
    use to skip the filter rather than pass an expression that is always 0.
    """
    terms = []
    for interval in intervals:
        start_s = max(0.0, interval.start_ms / 1000.0)
        end_s = max(start_s, interval.end_ms / 1000.0)
        terms.append(f"between(t,{start_s:.6f},{end_s:.6f})")
    if not terms:
        return None
    return "+".join(terms)


def _colour_tag_args(probe: VideoProbe) -> list[str]:
    args: list[str] = []
    if probe.color_primaries and probe.color_primaries != "unknown":
        args += ["-color_primaries", probe.color_primaries]
    if probe.color_transfer and probe.color_transfer != "unknown":
        args += ["-color_trc", probe.color_transfer]
    if probe.color_space and probe.color_space != "unknown":
        args += ["-colorspace", probe.color_space]
    if probe.color_range and probe.color_range != "unknown":
        args += ["-color_range", probe.color_range]
    return args


def _try_seeked_frame(args: list[str], out_path: Path) -> list[str] | None:
    """Run a seek and grab, and say nothing rather than raising when it lands past the end.

    Seeking past a file's last coded frame makes ffmpeg exit non zero, which is fine and not
    a reason to give up on the title. The caller has a second way to get the frame.
    """
    try:
        return ffmpegtool.run_ffmpeg(args).cmd
    except ffmpegtool.FFmpegError:
        out_path.unlink(missing_ok=True)
        return None


def _last_frame_up_to(
    source: str | Path,
    *,
    time_s: float,
    out_path: Path,
    filters: list[str],
) -> list[str]:
    """The last frame at or before ``time_s``, for a file that has none after it.

    A container can run on past its last coded frame. Ogg Theora does it as a matter of
    course: a frame that repeats the one before it is written as an empty packet, and a file
    whose tail is all repeats has a last decodable frame well before the end of its duration.
    Seeking into that tail gives nothing back at all. The picture a player shows there is the
    last real frame, so that is what gets taken.

    ``-update 1`` writes every frame over the same file, so the last one written wins.
    """
    args = ["-i", str(source), "-t", f"{max(0.0, time_s):.6f}"]
    args += filters
    args += ["-update", "1", str(out_path)]
    return ffmpegtool.run_ffmpeg(args).cmd


def extract_still(
    source: str | Path,
    *,
    time_s: float,
    out_path: str | Path,
    width: int | None = None,
    height: int | None = None,
) -> RenderResult:
    """One frame, written as a PNG. Used for the cover still and for posters."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    filters = ["-vf", f"scale={width}:{height}"] if width and height else []
    args = ["-ss", f"{max(0.0, time_s):.6f}", "-i", str(source), "-frames:v", "1"]
    args += filters
    args += ["-update", "1", str(out_path)]
    cmd = _try_seeked_frame(args, out_path)
    if cmd is None or not out_path.exists():
        cmd = _last_frame_up_to(
            source, time_s=time_s, out_path=out_path, filters=filters
        )
    if not out_path.exists():
        raise PipelineError(f"no still frame was written at {time_s} s of {source}")
    return RenderResult(path=out_path, cmd=cmd)


def extract_jpeg(
    source: str | Path,
    *,
    time_s: float,
    out_path: str | Path,
    width: int,
    height: int,
    quality: int = 5,
) -> RenderResult:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    filters = ["-vf", f"scale={width}:{height}", "-q:v", str(quality)]
    args = ["-ss", f"{max(0.0, time_s):.6f}", "-i", str(source), "-frames:v", "1"]
    args += filters
    args += ["-update", "1", str(out_path)]
    cmd = _try_seeked_frame(args, out_path)
    if cmd is None or not out_path.exists():
        cmd = _last_frame_up_to(
            source, time_s=time_s, out_path=out_path, filters=filters
        )
    if not out_path.exists():
        raise PipelineError(f"no jpeg was written at {time_s} s of {source}")
    return RenderResult(path=out_path, cmd=cmd)


def make_neutral_still(
    out_path: str | Path,
    *,
    width: int,
    height: int,
    rgb: tuple[int, int, int] = NEUTRAL_STILL_RGB,
) -> RenderResult:
    """A flat neutral card, for a title with no calm frame to take a cover from.

    A title that flashes from end to end has no frame that may be shown, so refusing it was
    the only safe answer while the cover had to come out of the film. It does not have to. A
    card made here comes from nothing in the title, which is what makes it safe, and the
    manifest says plainly that the cover is a card and not a frame of the film.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    colour = "0x{:02X}{:02X}{:02X}".format(*rgb)
    result = ffmpegtool.run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            f"color=c={colour}:s={int(width)}x{int(height)}",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(out_path),
        ]
    )
    if not out_path.exists():
        raise PipelineError(f"no neutral cover still was written at {out_path}")
    return RenderResult(path=out_path, cmd=result.cmd, notes={"rgb": list(rgb)})


_FLAT_RE = re.compile(r"lavfi\.signalstats\.([YUV])(MIN|MAX)=([0-9.]+)")


def still_is_flat(still_path: str | Path) -> tuple[bool, dict]:
    """Is this image one flat colour?

    This is the check that makes "the cover is a neutral card" something verify knows rather
    than something the pipeline claims. A frame lifted out of a film is never flat. It reads
    the extremes of each plane straight out of ffmpeg, so nothing in the pipeline gets to say
    what the picture was.
    """
    still_path = Path(still_path)
    if not still_path.exists():
        raise PipelineError(f"no cover still to measure at {still_path}")
    result = ffmpegtool.run_ffmpeg(
        [
            "-i",
            str(still_path),
            "-vf",
            "signalstats,metadata=print",
            "-f",
            "null",
            "-",
        ]
    )
    found: dict[str, float] = {}
    for line in (result.stderr or "").splitlines():
        match = _FLAT_RE.search(line)
        if match:
            found[f"{match.group(1)}{match.group(2)}"] = float(match.group(3))
    wanted = [f"{plane}{end}" for plane in ("Y", "U", "V") for end in ("MIN", "MAX")]
    missing = [key for key in wanted if key not in found]
    if missing:
        # Fail closed. A statistic that did not come back is not a statistic that said the
        # picture was flat, and treating an absent number as zero would read every gap as
        # proof of the thing being checked for.
        raise PipelineError(
            f"ffmpeg did not report {', '.join(missing)} for {still_path}, so whether it is "
            "one flat colour is unknown"
        )
    spreads = {
        plane: found[f"{plane}MAX"] - found[f"{plane}MIN"] for plane in ("Y", "U", "V")
    }
    return all(value == 0.0 for value in spreads.values()), {
        "extremes": found,
        "spreads": spreads,
    }


_PSNR_RE = re.compile(r"average:([0-9.]+|inf)")


def cover_psnr(video: str | Path, still_path: str | Path, *, time_s: float) -> float:
    """How close the frame at ``time_s`` is to the cover still, in dB.

    This is the check that does not go through the analyzer: a rendition that
    quietly covered nothing would still report zero violations on calm source
    footage, but it would not match the still. ``inf`` means the two frames
    are identical.
    """
    result = ffmpegtool.run_ffmpeg(
        [
            "-loglevel",
            "info",
            "-ss",
            f"{max(0.0, time_s):.6f}",
            "-i",
            str(video),
            "-i",
            str(still_path),
            "-frames:v",
            "1",
            "-lavfi",
            "[0:v]scale=320:180,format=rgb24[a];[1:v]scale=320:180,format=rgb24[b];[a][b]psnr",
            "-f",
            "null",
            "-",
        ]
    )
    match = None
    for line in (result.stderr or "").splitlines():
        found = _PSNR_RE.search(line)
        if found:
            match = found
    if match is None:
        raise PipelineError(f"could not read a PSNR value for {video} at {time_s} s")
    value = match.group(1)
    return float("inf") if value == "inf" else float(value)


def _subtitle_plan(probe: VideoProbe) -> tuple[bool, list[str]]:
    """Whether caption streams can ride along, and which ones."""
    text_streams = [
        s
        for s in probe.subtitle_streams
        if (s.codec_name or "").lower() in TEXT_SUBTITLE_CODECS
    ]
    skipped = [
        f"{s.index}:{s.codec_name}"
        for s in probe.subtitle_streams
        if (s.codec_name or "").lower() not in TEXT_SUBTITLE_CODECS
    ]
    return bool(text_streams), skipped


def render_safe_master(
    source: str | Path,
    *,
    intervals: Sequence[CoverInterval],
    still_path: str | Path,
    out_path: str | Path,
    probe: VideoProbe,
    crf: int = DEFAULT_CRF,
    x264_preset: str = DEFAULT_PRESET,
    segment_seconds: float = DEFAULT_HLS_SEGMENT_S,
    pad_tail_ms: float = 0.0,
) -> RenderResult:
    """One MP4 with every flagged span plus guard band replaced by the still.

    The HLS rendition is packaged from this file by stream copy, and the same
    file is what verify re-analyzes, so what the analyzer sees is exactly what
    the player streams.

    ``pad_tail_ms`` holds the last frame for that much longer at the end. A
    container can outlive its last coded frame: Ogg Theora writes a repeated
    frame as an empty packet, so a file ending on repeats has a last coded
    frame well before its duration, and ffmpeg drops those packets when it
    re-encodes. Without the hold the rendition comes out that much shorter
    than the title, which is both a missing tail and a rendition that no
    longer has the source's frame timing. Holding the last frame puts the
    time back and shows exactly what the source shows there.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    expression = enable_expression(intervals)
    hold = (
        f"tpad=stop_mode=clone:stop_duration={pad_tail_ms / 1000.0:.6f},"
        if pad_tail_ms > 0
        else ""
    )

    args: list[str] = ["-i", str(source)]
    if expression:
        args += ["-loop", "1", "-i", str(still_path)]
        filtergraph = (
            f"[0:v]{hold}null[base];"
            f"[1:v]scale={probe.width}:{probe.height},setsar=1[still];"
            f"[base][still]overlay=0:0:shortest=1:enable='{expression}'[v]"
        )
        args += ["-filter_complex", filtergraph, "-map", "[v]"]
    elif hold:
        args += ["-map", "0:v:0", "-vf", hold.rstrip(",")]
    else:
        args += ["-map", "0:v:0"]

    if probe.has_audio:
        args += ["-map", "0:a"]
    keep_subs, skipped_subs = _subtitle_plan(probe)
    if keep_subs:
        args += ["-map", "0:s"]

    args += [
        "-c:v",
        "libx264",
        "-preset",
        x264_preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        # Key frames on the segment grid so HLS packaging is a stream copy.
        "-force_key_frames",
        f"expr:gte(t,n_forced*{segment_seconds:g})",
    ]
    args += _colour_tag_args(probe)
    if probe.has_audio:
        args += ["-c:a", "copy"]
    if keep_subs:
        args += ["-c:s", "mov_text"]
    if probe.duration_s > 0:
        args += ["-t", f"{probe.duration_s:.6f}"]
    args += ["-movflags", "+faststart", str(out_path)]

    result = ffmpegtool.run_ffmpeg(args)
    return RenderResult(
        path=out_path,
        cmd=result.cmd,
        notes={
            "covered_spans": len(intervals),
            "enable_expression": expression,
            "audio_copied": probe.has_audio,
            "subtitles_carried": keep_subs,
            "subtitles_skipped": skipped_subs,
        },
    )


def package_hls(
    master_path: str | Path,
    *,
    out_dir: str | Path,
    probe: VideoProbe,
    segment_seconds: float = DEFAULT_HLS_SEGMENT_S,
) -> RenderResult:
    """Package the safe master into HLS without touching the pictures again."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    keep_subs, _ = _subtitle_plan(probe)

    args: list[str] = ["-i", str(master_path), "-map", "0:v:0"]
    if probe.has_audio:
        args += ["-map", "0:a"]
    if keep_subs:
        args += ["-map", "0:s"]
    args += ["-c:v", "copy"]
    if probe.has_audio:
        args += ["-c:a", "copy"]
    if keep_subs:
        args += ["-c:s", "webvtt"]
    args += [
        "-f",
        "hls",
        "-hls_time",
        f"{segment_seconds:g}",
        "-hls_playlist_type",
        "vod",
        "-hls_flags",
        "independent_segments",
        "-hls_segment_filename",
        str(out_dir / "seg_%v_%05d.ts"),
    ]
    if keep_subs:
        stream_map = "v:0,a:0,s:0,sgroup:subs" if probe.has_audio else "v:0,s:0,sgroup:subs"
    else:
        stream_map = "v:0,a:0" if probe.has_audio else "v:0"
    args += [
        "-var_stream_map",
        stream_map,
        "-master_pl_name",
        "master.m3u8",
        str(out_dir / "stream_%v.m3u8"),
    ]
    result = ffmpegtool.run_ffmpeg(args)
    master = out_dir / "master.m3u8"
    if not master.exists():
        raise PipelineError(f"HLS packaging wrote no master playlist in {out_dir}")
    return RenderResult(
        path=master,
        cmd=result.cmd,
        notes={"subtitles_carried": keep_subs, "var_stream_map": stream_map},
    )


def render_cover_model(
    source: str | Path,
    *,
    plan: HidePlan,
    out_path: str | Path,
    probe: VideoProbe,
    crf: int = DEFAULT_VERIFY_CRF,
    x264_preset: str = "veryfast",
    dim_alpha: float = DIM_MAX_LUMINANCE,
) -> RenderResult:
    """Draw the on-device cover schedule over the original video.

    This is what verify analyzes. Red intervals become an opaque black cover.
    General intervals are dimmed to ``dim_alpha`` of their light when the plan
    allows dim, which is the least protective cover the device may draw.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dim_spans = [i for i in plan.intervals if cover_mode(i, allow_dim=plan.allow_dim) == DIM]
    opaque_spans = [
        i for i in plan.intervals if cover_mode(i, allow_dim=plan.allow_dim) == OPAQUE
    ]

    gamma = transfer_gamma(probe)
    code_scale = linear_dim_code_scale(dim_alpha, gamma) if dim_spans else None

    chain: list[str] = []
    if dim_spans:
        chain.append("format=rgb24")
        chain.append(
            f"colorchannelmixer=rr={code_scale:.6f}:gg={code_scale:.6f}:"
            f"bb={code_scale:.6f}:enable='{enable_expression(dim_spans)}'"
        )
    if opaque_spans:
        chain.append(
            "drawbox=x=0:y=0:w=iw:h=ih:color=black@1:t=fill:"
            f"enable='{enable_expression(opaque_spans)}'"
        )
    chain.append("format=yuv420p")

    args: list[str] = [
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-an",
        "-sn",
        "-vf",
        ",".join(chain),
        "-c:v",
        "libx264",
        "-preset",
        x264_preset,
        "-crf",
        str(crf),
    ]
    args += _colour_tag_args(probe)
    if probe.duration_s > 0:
        args += ["-t", f"{probe.duration_s:.6f}"]
    args += [str(out_path)]

    result = ffmpegtool.run_ffmpeg(args)
    return RenderResult(
        path=out_path,
        cmd=result.cmd,
        notes={
            "dim_spans": len(dim_spans),
            "opaque_spans": len(opaque_spans),
            "dim_alpha_linear": dim_alpha if dim_spans else None,
            "gamma": gamma,
            "dim_code_scale": code_scale,
        },
    )
