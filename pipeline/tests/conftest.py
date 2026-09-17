"""Fixtures shared by the pipeline tests."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline import ffmpegtool

from .clips import make_calm_clip

FAKE_FLASHMAP = Path(__file__).with_name("fake_flashmap.py")


def ffmpeg_present() -> bool:
    return bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe"))


needs_ffmpeg = pytest.mark.skipif(
    not ffmpeg_present(), reason="ffmpeg and ffprobe are needed for this test"
)


class FakeAnalyzer:
    """Drives the fake flashmap CLI and reads back what was asked of it."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.plan_path = tmp_path / "flashmap_plan.json"
        self.log_path = tmp_path / "flashmap_calls.jsonl"
        self.plan: dict = {"log": str(self.log_path), "rules": []}
        self.write()
        command = f"{shlex.quote(sys.executable)} {shlex.quote(str(FAKE_FLASHMAP))}"
        monkeypatch.setenv("CALM_FRAMES_FLASHMAP_CMD", command)
        monkeypatch.setenv("FAKE_FLASHMAP_PLAN", str(self.plan_path))

    def write(self) -> None:
        self.plan_path.write_text(json.dumps(self.plan, indent=2))

    def flag(
        self,
        match: str,
        *,
        segments: dict[str, list] | None = None,
        segments_all: list | None = None,
    ) -> None:
        """Make the analyzer report these spans for anything matching ``match``.

        Rules are checked in the order they were added, so a narrow rule that
        is added first wins over a wider one added later.
        """
        rule: dict = {"match": match}
        if segments_all is not None:
            rule["segments_all"] = segments_all
        else:
            rule["segments"] = segments or {}
        self.plan["rules"].append(rule)
        self.write()

    def fail_on(self, match: str, message: str = "analysis failed") -> None:
        self.plan["fail"] = {"match": match, "message": message}
        self.write()

    def calls(self, command: str | None = None) -> list[dict]:
        if not self.log_path.exists():
            return []
        entries = [
            json.loads(line)
            for line in self.log_path.read_text().splitlines()
            if line.strip()
        ]
        if command:
            entries = [entry for entry in entries if entry.get("cmd") == command]
        return entries


@pytest.fixture
def analyzer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeAnalyzer:
    return FakeAnalyzer(tmp_path, monkeypatch)


@pytest.fixture
def keypair(tmp_path: Path) -> tuple[Path, Path]:
    """An Ed25519 pair for signing test maps. Never written into the repo."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    private = ed25519.Ed25519PrivateKey.generate()
    private_path = tmp_path / "test_key.pem"
    public_path = tmp_path / "test_key.pub.pem"
    private_path.write_bytes(
        private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path, public_path


@pytest.fixture
def calm_clip(tmp_path: Path) -> Path:
    if not ffmpeg_present():
        pytest.skip("ffmpeg is needed to build a test clip")
    return make_calm_clip(tmp_path / "clip.mp4")


@pytest.fixture
def ffmpeg_calls(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Every ffmpeg command the pipeline runs, in order."""
    seen: list[list[str]] = []
    original = ffmpegtool.run_ffmpeg

    def counting(args, **kwargs):
        seen.append([str(a) for a in args])
        return original(args, **kwargs)

    monkeypatch.setattr(ffmpegtool, "run_ffmpeg", counting)
    return seen


def ffprobe_json(path: Path, *args: str) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", *args, "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)
