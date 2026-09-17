"""The only place in the pipeline that starts ffmpeg or ffprobe.

Keeping both behind one function means tests can count the calls (which is how
idempotency is proved) and every failure comes back with the tail of stderr
instead of a bare non-zero exit code.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from . import PipelineError

FFMPEG_ENV = "CALM_FRAMES_FFMPEG"
FFPROBE_ENV = "CALM_FRAMES_FFPROBE"

DEFAULT_TIMEOUT_S = 60 * 60


class FFmpegError(PipelineError):
    def __init__(self, cmd: Sequence[str], returncode: int, stderr: str) -> None:
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr
        tail = "\n".join(stderr.strip().splitlines()[-12:])
        super().__init__(
            f"{Path(cmd[0]).name} exited {returncode}\n"
            f"  command: {' '.join(str(part) for part in cmd)}\n"
            f"  stderr tail:\n{tail}"
        )


@dataclass
class ToolResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str
    extra: dict = field(default_factory=dict)


def ffmpeg_binary() -> str:
    return os.environ.get(FFMPEG_ENV) or "ffmpeg"


def ffprobe_binary() -> str:
    return os.environ.get(FFPROBE_ENV) or "ffprobe"


def tools_available() -> bool:
    return bool(shutil.which(ffmpeg_binary())) and bool(shutil.which(ffprobe_binary()))


def require_tools() -> None:
    if not tools_available():
        raise PipelineError(
            "ffmpeg and ffprobe must be on PATH "
            f"(looked for {ffmpeg_binary()!r} and {ffprobe_binary()!r})"
        )


def _run(cmd: Sequence[str], timeout_s: float | None) -> ToolResult:
    cmd = [str(part) for part in cmd]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S,
        )
    except FileNotFoundError as exc:
        raise PipelineError(f"{cmd[0]} is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise PipelineError(f"{cmd[0]} timed out after {exc.timeout} s") from exc
    if completed.returncode != 0:
        raise FFmpegError(cmd, completed.returncode, completed.stderr or "")
    return ToolResult(
        cmd=cmd,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def run_ffmpeg(args: Sequence[str], *, timeout_s: float | None = None) -> ToolResult:
    """Run ffmpeg with the flags every call in this pipeline wants.

    ``-nostdin`` matters: a pipeline step must never sit waiting for a key
    press, and ffmpeg reads stdin by default.
    """
    cmd = [ffmpeg_binary(), "-hide_banner", "-nostdin", "-y", *[str(a) for a in args]]
    return _run(cmd, timeout_s)


def run_ffprobe(args: Sequence[str], *, timeout_s: float | None = None) -> ToolResult:
    cmd = [ffprobe_binary(), "-hide_banner", "-v", "error", *[str(a) for a in args]]
    return _run(cmd, timeout_s)


def ffprobe_json(args: Sequence[str], *, timeout_s: float | None = None) -> dict:
    result = run_ffprobe([*args, "-of", "json"], timeout_s=timeout_s)
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise PipelineError(f"ffprobe returned output that is not JSON: {exc}") from exc
