#!/usr/bin/env python3
"""Validate real inputs, then render an unsubmitted review copy outside the repo."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).with_name("narration-cues.json")
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    return json.loads(result.stdout)


def stream_duration(stream: dict) -> float:
    """Return conservative stream coverage; container length is not evidence.

    The renderer seeks from a zero media origin. Refuse unknown or nonzero
    stream origins instead of silently shifting picture or app audio.
    """
    def known(key: str) -> bool:
        return stream.get(key) not in (None, "N/A")

    def number(key: str) -> Fraction:
        return Fraction(str(stream[key]))

    starts = []
    if known("start_time"):
        starts.append(number("start_time"))
    if known("start_pts") and known("time_base"):
        if number("time_base") <= 0:
            raise ValueError("nonpositive stream time base")
        starts.append(number("start_pts") * number("time_base"))
    if not starts or any(start != 0 for start in starts):
        raise ValueError("stream start must be known and zero; nonzero origins are unsupported")
    durations = []
    if known("duration"):
        durations.append(number("duration"))
    if known("duration_ts") and known("time_base"):
        if number("time_base") <= 0:
            raise ValueError("nonpositive stream time base")
        durations.append(number("duration_ts") * number("time_base"))
    if not durations or any(duration <= 0 for duration in durations):
        raise ValueError("finite positive stream coverage is unknown")
    # When both are reported, never extend a stream past the shorter bound.
    duration = float(min(durations))
    if not math.isfinite(duration):
        raise ValueError("stream duration is not finite")
    return duration


def validate(plan: dict, probe_file=probe) -> tuple[list[str], dict]:
    errors: list[str] = []
    measured: dict = {}
    if plan.get("schema_version") != 1:
        errors.append("Unsupported plan schema")
    total = plan.get("duration_seconds")
    if not isinstance(total, (int, float)) or not math.isfinite(total) or not 150 <= total <= 170:
        errors.append("Planned duration must be 150 to 170 seconds, strictly below 180")
    if not COMMIT.fullmatch(str(plan.get("source_commit", ""))):
        errors.append("An exact selected production source commit is required")
    if not SHA.fullmatch(str(plan.get("package_sha256", ""))):
        errors.append("The selected installed package SHA256 is required")
    if (plan.get("width"), plan.get("height"), plan.get("fps")) != (1920, 1080, 30):
        errors.append("This recipe is reviewed only for 1920x1080 at 30 fps")
    cues = plan.get("narration_cues", [])
    script_hash = hashlib.sha256((json.dumps(cues, indent=2) + "\n").encode()).hexdigest()
    if script_hash != plan.get("narration_script_sha256"):
        errors.append("Narration text no longer matches its recorded script hash")
    if script_hash != digest(SCRIPT):
        errors.append("Narration differs from the version reviewed with this render recipe")
    approval = plan.get("approvals", {})
    if approval.get("script_sha256") != script_hash:
        errors.append("Exact narration approval is missing")
    voice = approval.get("authorized_voice_id")
    if not isinstance(voice, str) or not voice.strip():
        errors.append("Authorized narration voice is missing")
    assets = plan.get("assets", {})
    required = {s.get("asset") for s in plan.get("segments", [])} | {c.get("id") for c in cues}
    if None in required or not required <= assets.keys():
        errors.append("A referenced asset is missing from the inventory")
    for name in sorted(required - {None}):
        asset = assets.get(name, {})
        raw = asset.get("path")
        if not isinstance(raw, str) or not Path(raw).is_absolute() or not Path(raw).is_file():
            errors.append(f"{name}: actual absolute local file is missing")
            continue
        path = Path(raw)
        expected = asset.get("sha256")
        if not isinstance(expected, str) or not SHA.fullmatch(expected) or digest(path) != expected:
            errors.append(f"{name}: byte hash is missing or does not match")
            continue
        if asset.get("provenance_reviewed") is not True:
            errors.append(f"{name}: provenance/capture review is missing")
        kind = asset.get("kind")
        if kind not in {"native_video", "illustration", "narration"}:
            errors.append(f"{name}: unsupported asset kind")
        if kind == "native_video":
            if asset.get("source_commit") != plan.get("source_commit"):
                errors.append(f"{name}: capture source differs from selected source")
            if asset.get("capture_scope") != "app_window_and_app_audio_only":
                errors.append(f"{name}: capture scope is not app-only")
            if asset.get("production_capture") is not True or asset.get("raw_take") is not True:
                errors.append(f"{name}: requires a reviewed raw production take, not a harness or mockup")
            if asset.get("package_sha256") != plan.get("package_sha256"):
                errors.append(f"{name}: installed package differs from selected package")
            receipt_path = asset.get("capture_receipt_path")
            try:
                receipt_file = Path(receipt_path) if isinstance(receipt_path, str) else None
                if receipt_file is None or not receipt_file.is_absolute() or not receipt_file.is_file():
                    raise ValueError("receipt missing")
                if digest(receipt_file) != asset.get("capture_receipt_sha256"):
                    raise ValueError("receipt hash differs")
                receipt = json.loads(receipt_file.read_text())
                expected_receipt = {
                    "source_commit": plan.get("source_commit"),
                    "package_sha256": plan.get("package_sha256"),
                    "raw_take_sha256": expected,
                    "capture_scope": "app_window_and_app_audio_only",
                    "production_capture": True,
                }
                if any(receipt.get(k) != value for k, value in expected_receipt.items()):
                    raise ValueError("receipt identity differs")
            except (OSError, ValueError, TypeError):
                errors.append(f"{name}: capture receipt is missing, changed or inconsistent")
        if kind == "narration" and asset.get("authorized_voice_id") != voice:
            errors.append(f"{name}: voice differs from approval")
        try:
            info = probe_file(path)
            streams = info.get("streams", [])
            video = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
            if kind in {"native_video", "illustration"} and video is None:
                errors.append(f"{name}: no picture stream")
            if kind == "narration" and audio is None:
                errors.append(f"{name}: no narration audio stream")
            if name == "native_ambient" and audio is None:
                errors.append("native_ambient: actual app audio is required")
            coverage = {"video_duration": None, "audio_duration": None}
            for stream_type, stream in (("video", video), ("audio", audio)):
                needed = kind == "native_video" or (kind == "narration" and stream_type == "audio")
                if needed and stream is not None:
                    try:
                        coverage[f"{stream_type}_duration"] = stream_duration(stream)
                    except (ValueError, ZeroDivisionError, OverflowError):
                        errors.append(f"{name}: first mapped {stream_type} stream requires finite positive coverage and a known zero start")
            measured[name] = {
                **coverage,
                "duration": coverage["audio_duration" if kind == "narration" else "video_duration"],
                "audio": audio is not None, "bytes": path.stat().st_size,
            }
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            errors.append(f"{name}: media probe failed ({type(error).__name__})")
    cursor = 0.0
    for segment in plan.get("segments", []):
        start, duration, offset = (segment.get(k) for k in ("start", "duration", "source_start"))
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in (start, duration, offset)):
            errors.append("Segment timing is not finite")
            continue
        if abs(start - cursor) > 0.001 or duration <= 0 or offset < 0:
            errors.append("Segments must form a continuous positive-duration timeline")
        cursor = start + duration
        name = segment.get("asset")
        kind = assets.get(name, {}).get("kind")
        if name and name.startswith("native_") and kind != "native_video":
            errors.append(f"{name}: native slot cannot contain an illustration")
        if name and name.startswith("manga_") and kind != "illustration":
            errors.append(f"{name}: story slot requires an illustration")
        if kind == "native_video" and name in measured:
            for stream_type in ("video", "audio"):
                coverage = measured[name][f"{stream_type}_duration"]
                if coverage is not None and offset + duration > coverage:
                    errors.append(f"{name}: first mapped {stream_type} stream take is too short for the selected interval; looping, freezing or padding is forbidden")
        gain = segment.get("native_audio_gain")
        if not isinstance(gain, (int, float)) or not 0 <= gain <= 1:
            errors.append(f"{name}: invalid audio gain")
    if isinstance(total, (int, float)) and abs(cursor - total) > 0.001:
        errors.append("Segment sum differs from target duration")
    ambient = [s for s in plan.get("segments", []) if s.get("asset") == "native_ambient"]
    if len(ambient) != 1 or ambient[0].get("duration") != 70:
        errors.append("The planned uncut 70-second ambient passage is missing")
    previous_end = 0.0
    for cue in cues:
        start, end = cue.get("start"), cue.get("end")
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in (start, end)):
            errors.append("Narration timing is not finite")
            continue
        if start < previous_end or end <= start or (isinstance(total, (int, float)) and end > total):
            errors.append("Narration windows overlap or exceed the film")
        previous_end = end
        if ambient and start < ambient[0]["start"] + 70 and end > ambient[0]["start"]:
            errors.append("Narration cannot cover the ambient passage")
        speech_duration = measured.get(cue.get("id"), {}).get("audio_duration")
        if speech_duration is not None and speech_duration > end - start:
            errors.append(f"{cue['id']}: measured speech exceeds its window; do not speed it up")
    return errors, measured


def timestamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def render(plan: dict, measured: dict, out: Path, manifest: Path) -> None:
    if out.exists() or out.is_relative_to(REPO):
        raise ValueError("Output directory must be new and outside the repository")
    out.mkdir(parents=True, exist_ok=False)
    ff = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n"]
    with tempfile.TemporaryDirectory(prefix="calm-edit-") as scratch:
        temp = Path(scratch)
        for index, segment in enumerate(plan["segments"]):
            asset = plan["assets"][segment["asset"]]
            inputs = ["-loop", "1", "-framerate", "30", "-i", asset["path"]] if asset["kind"] == "illustration" else [
                "-ss", str(segment["source_start"]), "-i", asset["path"]
            ]
            has_audio = measured[segment["asset"]]["audio"] and asset["kind"] == "native_video"
            if not has_audio:
                inputs += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
            command = ff + inputs + [
                "-t", str(segment["duration"]), "-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x183a38,setsar=1,fps=30",
                "-af", f"volume={segment['native_audio_gain']},aresample=48000",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-ac", "2", str(temp / f"part-{index:02}.mp4"),
            ]
            run(command)
        (temp / "concat.txt").write_text("".join(f"file 'part-{i:02}.mp4'\n" for i in range(len(plan["segments"]))))
        run(ff + ["-f", "concat", "-safe", "1", "-i", str(temp / "concat.txt"), "-c", "copy", str(temp / "picture.mp4")])
        inputs = ["-i", str(temp / "picture.mp4")]
        filters = ["[0:a:0]asetpts=PTS-STARTPTS[base]"]
        labels = ["[base]"]
        subtitles = []
        for index, cue in enumerate(plan["narration_cues"], 1):
            inputs += ["-i", plan["assets"][cue["id"]]["path"]]
            delay = round(cue["start"] * 1000)
            filters.append(f"[{index}:a:0]aresample=48000,adelay={delay}:all=1[v{index}]")
            labels.append(f"[v{index}]")
            subtitles.append((cue["start"], cue["start"] + measured[cue["id"]]["duration"], cue["text"]))
        filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0:dropout_transition=0[a]")
        video = out / "calm-frames-story-review.mp4"
        run(ff + inputs + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]",
                          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(plan["duration_seconds"]),
                          "-movflags", "+faststart", str(video)])
    # Merge labels into existing cues instead of emitting overlapping SRT blocks.
    subtitles[0] = (subtitles[0][0], subtitles[0][1], "Illustrated story; fictional character.\n" + subtitles[0][2])
    subtitles[1] = (subtitles[1][0], subtitles[1][1], "Native Fire TV / Vega app capture.\n" + subtitles[1][2])
    subtitles += [(45, 51, "Native excerpt at natural speed; uncut until the next story frame."),
                  (164, 170, "Not a medical device.\nMcWay: MoneySavingVideos, CC BY 3.0.\nFull credits in description.")]
    subtitles.sort()
    srt = out / "calm-frames-story-review.srt"
    srt.write_text("\n".join(f"{i}\n{timestamp(a)} --> {timestamp(b)}\n{text}\n" for i, (a, b, text) in enumerate(subtitles, 1)))
    result = probe(video)
    duration = float(result["format"]["duration"])
    if not 150 <= duration <= 170.1 or duration >= 180:
        raise ValueError(f"Rendered duration rejected: {duration}")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(video), "-f", "null", "-"])
    receipt = {
        "source_commit": plan["source_commit"], "manifest_sha256": digest(manifest),
        "narration_script_sha256": plan["narration_script_sha256"], "measured_duration_seconds": duration,
        "inputs": {k: {"sha256": a["sha256"], **measured[k]} for k, a in plan["assets"].items() if k in measured},
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": digest(p)} for p in (video, srt)},
        "full_decode": "passed", "existing_video_gate": "not_run",
        "human_audio_palette_full_video_acceptance": "pending", "published": False,
    }
    (out / "render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (out / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in (video, srt, out / "render-receipt.json")))
    print(json.dumps({"review_output": str(out), "human_acceptance": "pending"}))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--outdir", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-only", action="store_true")
    action.add_argument("--render", action="store_true")
    args = parser.parse_args()
    try:
        plan = json.loads(args.manifest.read_text())
        errors, measured = validate(plan)
        if errors:
            print(json.dumps({"status": "blocked", "errors": errors}, indent=2))
            return 2
        if args.check_only:
            print(json.dumps({"status": "inputs_valid", "measured_inputs": measured}, indent=2))
            return 0
        if args.outdir is None:
            raise ValueError("--outdir is required for rendering")
        render(plan, measured, args.outdir.resolve(), args.manifest)
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Render refused: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
