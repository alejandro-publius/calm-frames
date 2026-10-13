"""Build the original, explicitly labelled, non-flashing scene-hold demo.

Every source profile must measure clean before demonstration intervals are
added. All later image, rendition, HLS and signature checks use the production
pipeline. A temporary signing key is deleted with its directory; only its
public half is exported. No player is opened.

Run from the repository: .venv/bin/python -m eval.benign_story
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from eval.render_harbor import render_harbor
from pipeline.flashmap_adapter import FlashmapAdapter, load_map
from pipeline.hashing import sha256_file
from pipeline.ingest import IngestOptions, ingest_title
from pipeline.probe import probe_video
from pipeline.registry import load_private_key, sign_document, write_registry

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "app/assets/raw/benign-story"
GENERATED = REPO / "app/src/calmframes/benignStoryData.ts"
PRESETS = ["wcag", "broadcast", "extra-cautious"]
DURATION_MS = 20_000
DEMO_LABEL = "Benign demonstration: scheduled practice holds, no flashing."
SHAM_SEGMENTS = [
    {"start_ms": 6000, "end_ms": 8000, "reason": "general"},
    {"start_ms": 13000, "end_ms": 15000, "reason": "general"},
]
CAPTIONS = """WEBVTT

00:00:00.400 --> 00:00:02.300
Evening settles over the water.

00:00:03.000 --> 00:00:06.000
A small boat rests in the harbor.

00:00:07.000 --> 00:00:10.000
Sunlight follows the ripples.

00:00:11.000 --> 00:00:14.000
The lighthouse watches over the bay.

00:00:15.000 --> 00:00:19.500
A quiet moment before home.
"""


def make_story(path: Path, rendered: Path | None = None) -> Path:
    """Mux the cinematic water/harbor render with original ambience and captions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if rendered is None:
        rendered = path.parent / "picture.mp4"
        render_harbor(rendered)
    picture = probe_video(rendered)
    if ((picture.width, picture.height, picture.frame_count) != (1280, 720, 480)
            or abs(picture.duration_ms - DURATION_MS) > 50):
        raise ValueError("Harbor requires the full 20 second, 1280x720, 24 fps render.")
    captions = path.with_suffix(".vtt")
    captions.write_text(CAPTIONS)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(rendered), "-f", "lavfi", "-i",
        "anoisesrc=color=pink:amplitude=0.14:seed=23:d=20:r=48000",
        "-i", str(captions), "-map", "0:v:0", "-map", "1:a", "-map", "2:s",
        "-c:v", "copy", "-c:a", "aac", "-af",
        "highpass=f=100,lowpass=f=1300,volume='0.24+0.08*sin(2*PI*t/7)':eval=frame,"
        "afade=t=in:d=1,afade=t=out:st=19:d=1",
        "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", "-t", "20",
        "-movflags", "+faststart", str(path),
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=120)
    return path


class DemonstrationAnalyzer(FlashmapAdapter):
    """Only explicitly labelled source intervals are synthetic, never checks."""

    def __init__(self, source: Path, key: Path, evidence: Path):
        super().__init__(command=[sys.executable, "-m", "flashmap"])
        self.source = source.resolve()
        self.key = key
        self.evidence = evidence
        self.clean_profiles: set[str] = set()

    def analyze(self, video, **kwargs):
        measured = super().analyze(video, **kwargs)
        if Path(video).resolve() != self.source:
            return measured
        if not measured.is_clean or measured.raw.get("generator", {}).get("name") != "flashmap":
            raise ValueError("The demonstration source must measure clean before sham holds.")
        preset = kwargs["profile"]
        self.clean_profiles.add(preset)
        self.evidence.mkdir(parents=True, exist_ok=True)
        write_registry(measured.raw, self.evidence / f"measured-source.{preset}.json")
        document = dict(measured.raw)
        document["demonstration"] = {
            "label": DEMO_LABEL,
            "synthetic_intervals": True,
            "original_measured_segment_count": measured.violation_count,
        }
        document["segments"] = SHAM_SEGMENTS
        document["summary"] = {
            **document["summary"], "pass": False, "flash_pass": False,
            "segment_count": 2, "general_segment_count": 2,
            "red_segment_count": 0, "hidden_ms": 4000,
        }
        output = Path(kwargs["out_path"])
        write_registry(sign_document(document, load_private_key(self.key)), output)
        result = load_map(output)
        result.preset = preset
        return result


def build_demo(rendered: Path | None = None) -> dict:
    work = REPO / "build/benign-story"
    work.mkdir(parents=True, exist_ok=True)
    source = make_story(work / "harbor.mp4", rendered)
    with TemporaryDirectory(prefix="calm-frames-demo-key-") as private_dir:
        private = Ed25519PrivateKey.generate()
        key = Path(private_dir) / "signing.pem"
        pub = Path(private_dir) / "signing.pub.pem"
        key.write_bytes(private.private_bytes(serialization.Encoding.PEM,
                        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        key.chmod(0o600)
        public_pem = private.public_key().public_bytes(serialization.Encoding.PEM,
                                                      serialization.PublicFormat.SubjectPublicKeyInfo)
        pub.write_bytes(public_pem)
        public_raw = private.public_key().public_bytes(serialization.Encoding.Raw,
                                                      serialization.PublicFormat.Raw)
        adapter = DemonstrationAnalyzer(source, key, work / "evidence")
        result = ingest_title(source, work / "pipeline", IngestOptions(
            presets=PRESETS, key=str(key), pub=str(pub), force=True,
            diag_in=85, distance_ft=4, guard_band_ms=1000, min_cover_ms=800,
            poster_count=1, bif_interval_ms=5000, x264_preset="veryfast",
            title="Harbor story (benign practice holds)",
        ), adapter=adapter)
        if not result.verify_passed or not result.publishable or adapter.clean_profiles != set(PRESETS):
            raise ValueError("Every demonstration source profile and production verification must pass.")
        probe = probe_video(source)
        if not probe.has_audio or not probe.has_subtitles:
            raise ValueError("The demonstration must contain audio and captions.")
        ASSETS.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, ASSETS / "harbor.mp4")
        rendition = result.layout.safe_master("extra-cautious")
        shutil.copyfile(rendition, ASSETS / "harbor.precovered.mp4")
        shutil.copyfile(source.with_suffix(".vtt"), ASSETS / "harbor.vtt")
        (ASSETS / "demo.pub.pem").write_bytes(public_pem)
        maps = {}
        for preset in PRESETS:
            original = work / "evidence" / f"measured-source.{preset}.json"
            shutil.copyfile(original, ASSETS / original.name)
            path = result.layout.map_path(preset)
            shutil.copyfile(path, ASSETS / f"harbor.{preset}.json")
            maps[preset] = path.read_text()
        report = result.verify_report
        assert report is not None
        # Keep the actual check details, without ephemeral machine/key paths.
        evidence = {
            "version": 1, "label": DEMO_LABEL, "source_sha256": sha256_file(source),
            "playback": "bundled verified extra-cautious pre-covered master with live guard",
            "playback_sha256": sha256_file(rendition),
            "source_license": "Apache-2.0; generated Harbor artwork, Blender animation, original captions and synthesized ambience",
            "source_measured_clean_presets": sorted(adapter.clean_profiles),
            "synthetic_intervals": SHAM_SEGMENTS,
            "production_pipeline_passed": report["passed"],
            "checks": json.loads(json.dumps(report["checks"]).replace(str(REPO) + "/", "")),
            "physical_tv_validated": False,
            "assets_sha256": {path.name: sha256_file(path) for path in sorted(ASSETS.iterdir())
                              if path.is_file() and path.suffix in {".mp4", ".vtt", ".json", ".pem", ".md"}
                              and path.name != "verification.json"},
            "prepared_renditions": {
                preset: {"sha256": sha256_file(result.layout.safe_master(preset)),
                         "path": str(result.layout.safe_master(preset).relative_to(REPO))}
                for preset in PRESETS
            },
        }
        write_registry(evidence, ASSETS / "verification.json")
        GENERATED.write_text(
            "/** Generated by eval/benign_story.py. Explicitly synthetic demo intervals. */\n"
            f"export const BENIGN_STORY_PUBLIC_KEY = {json.dumps(base64.b64encode(public_raw).decode())};\n"
            f"export const BENIGN_STORY_SHA256 = {json.dumps(sha256_file(source))};\n"
            f"export const BENIGN_STORY_RENDITION_SHA256 = {json.dumps(sha256_file(rendition))};\n"
            f"export const BENIGN_STORY_MAPS: Record<string, string> = {json.dumps(maps, indent=2)};\n"
        )
        return {"passed": True, "source_sha256": evidence["source_sha256"],
                "assets": str(ASSETS.relative_to(REPO)), "physical_tv_validated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rendered", type=Path, help="Existing silent Harbor render; the real source analysis still runs.")
    args = parser.parse_args()
    print(json.dumps(build_demo(args.rendered), indent=2))
