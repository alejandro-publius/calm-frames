#!/usr/bin/env python3
"""Exercise the encoder with a labelled still card and digital silence only.

This does not produce a product demo, generate narration or impersonate a native
capture. Normal production preflight must refuse its synthetic input manifest.
All generated media stays outside Git and is never opened in a player.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from render_demo import REPO, digest, probe, render, stream_duration, validate

HERE = Path(__file__).resolve().parent


def smoke(out: Path) -> dict:
    out = out.resolve()
    if out.exists() or out.is_relative_to(REPO):
        raise ValueError("Choose a new smoke-test directory outside the repository")
    out.mkdir(parents=True)
    inputs = out / "inputs"
    inputs.mkdir()
    label = inputs / "TEST_ONLY.txt"
    label.write_text("TEST ONLY\nSYNTHETIC ENCODER FIXTURE\nNo native app capture. No narration.\nStatic picture and digital silence.")
    picture, take, voice = (inputs / name for name in ("TEST_ONLY.png", "TEST_ONLY.mp4", "SILENCE_ONLY.m4a"))
    font = REPO / "app/assets/fonts/CalmSansRegular.ttf"
    if not font.is_file():
        raise ValueError("The repository's existing fixture font is missing")
    ff = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n"]
    subprocess.run(ff + [
        "-f", "lavfi", "-i", "color=c=0x183a38:s=640x360:r=30",
        "-vf", f"drawtext=fontfile='{font}':textfile='{label}':fontcolor=0xf6ebd1:fontsize=24:x=24:y=80:line_spacing=12",
        "-frames:v", "1", "-threads", "1", str(picture),
    ], check=True)
    subprocess.run(ff + [
        "-loop", "1", "-framerate", "30", "-i", str(picture),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "70",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-threads", "2", "-c:a", "aac", "-b:a", "128k", str(take),
    ], check=True)
    subprocess.run(ff + [
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "1",
        "-c:a", "aac", "-b:a", "128k", str(voice),
    ], check=True)
    plan = json.loads((HERE / "timeline.json").read_text())
    plan.update(artifact_role="synthetic_tool_test", source_commit=None, package_sha256=None)
    plan["approvals"]["authorized_voice_id"] = None
    measured = {}
    for name, asset in plan["assets"].items():
        path = {"illustration": picture, "native_video": take, "narration": voice}[asset["kind"]]
        asset.update(path=str(path), sha256=digest(path), provenance_reviewed=False)
        if asset["kind"] == "native_video":
            asset.update(source_commit=None, package_sha256=None, production_capture=False, raw_take=False)
        info = probe(path)
        video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
        audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
        vd = stream_duration(video) if asset["kind"] == "native_video" else None
        ad = stream_duration(audio) if audio else None
        measured[name] = {"video_duration": vd, "audio_duration": ad,
                          "duration": ad if asset["kind"] == "narration" else vd,
                          "audio": audio is not None, "bytes": path.stat().st_size}
    manifest = out / "TEST_ONLY-manifest.json"
    manifest.write_text(json.dumps(plan, indent=2) + "\n")
    errors, _ = validate(plan)
    if not any("Synthetic fixtures cannot" in error for error in errors):
        raise ValueError("Production preflight did not refuse the synthetic fixture")
    render(plan, measured, out / "TEST_ONLY-output", manifest, test_fixture=True)
    receipt_path = out / "TEST_ONLY-output/render-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if receipt["artifact_role"] != "synthetic_tool_test" or receipt["source_commit"] is not None:
        raise ValueError("Synthetic output was incorrectly attributed to an app source")
    result = {
        "artifact_role": "synthetic_tool_test", "real_app_capture_used": False,
        "speech_generated": False, "paid_calls": 0, "media_opened_in_player": False,
        "production_preflight": "refused synthetic assets as required",
        "production_preflight_errors": errors, "render_receipt_sha256": digest(receipt_path),
        "outputs": receipt["outputs"], "full_decode": receipt["full_decode"],
        "duration_seconds": receipt["measured_duration_seconds"],
        "human_audio_palette_full_video_acceptance": "not_applicable_to_test_fixture",
    }
    (out / "smoke-result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(smoke(args.outdir), indent=2))


if __name__ == "__main__":
    main()
