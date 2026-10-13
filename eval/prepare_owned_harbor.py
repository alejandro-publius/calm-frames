"""Reproduce the real prepared-library proof using owned, non-flashing media.

The Apache-2.0 cinematic Harbor source supplies its picture and synthesized
ambience unchanged. New neutral story captions describe that picture without
claiming practice holds. No synthetic detector intervals are added. The normal
local preparation and package export run, and nothing is played. A temporary
private key is deleted after preparation; the public key remains for checking.

    .venv/bin/python -m eval.prepare_owned_harbor \
        --output app/assets/raw/prepared-library
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from eval.benign_story import CAPTIONS
from pipeline.ffmpegtool import run_ffmpeg
from pipeline.local_library import prepare_local_title
from pipeline.packaged_library import check_packaged_library, export_packaged_library

REPO = Path(__file__).resolve().parent.parent

def prepare_owned_harbor(output: Path, workdir: Path, source_media: Path | None = None) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    captions = workdir / "harbor.vtt"
    captions.write_text(CAPTIONS)
    source = workdir / "owned-harbor-import.mp4"
    run_ffmpeg([
        "-i", str(source_media or REPO / "app/assets/raw/benign-story/harbor.mp4"), "-i", str(captions),
        "-map", "0:v:0", "-map", "0:a:0", "-map", "1:s:0", "-c:v", "copy", "-c:a", "copy",
        "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", str(source),
    ])
    public = workdir / "import.pub.pem"
    with TemporaryDirectory(prefix="calm-frames-import-key-") as directory:
        private = Ed25519PrivateKey.generate()
        key = Path(directory) / "private.pem"
        key.write_bytes(private.private_bytes(serialization.Encoding.PEM,
                        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        key.chmod(0o600)
        public.write_bytes(private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        receipt = prepare_local_title(source, workdir / "work", key=key, pub=public,
                                      title="Harbor story (prepared locally)")
        if receipt["status"] != "ready":
            raise RuntimeError("The owned harbor source did not complete normal preparation.")
        manifest = export_packaged_library(workdir / "work", output, pub=public)
        if check_packaged_library(output) != manifest:
            raise RuntimeError("The exported library did not match its prepared manifest.")
    return {"status": "ready", "sourceSha256": receipt["source_sha256"],
            "bundleId": manifest["bundleId"], "physical_tv_validated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPO / "build/packaged-library-proof/export")
    parser.add_argument("--workdir", type=Path, default=REPO / "build/packaged-library-proof")
    parser.add_argument("--source", type=Path, help="An existing Harbor source; normal preparation still runs.")
    arguments = parser.parse_args()
    print(json.dumps(prepare_owned_harbor(arguments.output, arguments.workdir, arguments.source), indent=2))
