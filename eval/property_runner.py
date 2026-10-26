"""Talk to the app's real scheduler from Python.

hypothesis lives in Python and the scheduler that GATE 1 measures is TypeScript, so the
property tests drive the real modules through one long-lived node process rather than
reimplementing them here. A reimplementation would only ever test itself.

    with SchedulerRunner() as runner:
        answer = runner.call({"job": "schedule", "segments": [...], "options": {...}})

The TypeScript is compiled once per session by the app's own tsc, straight from
app/src/calmframes, into build/property/js. Nothing is copied or edited on the way, so what
answers here is the code that ships.

`make properties` sets CALM_FRAMES_REQUIRE_NODE=1, which turns a missing node from a skip
into a failure. Without it a machine with no node skips these tests and says so, which is why
the CI job that owns them sets the variable.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# CALM_FRAMES_APP_DIR points the property tests at another copy of the app. The mutation gate
# uses it to run these tests against a copy with one guard broken, which is how a property
# test is shown to fail rather than just shown to pass. The compiled output goes to its own
# directory, so a mutant compile can never be mistaken for the real one.
APP = Path(os.environ.get("CALM_FRAMES_APP_DIR") or (REPO / "app")).resolve()
_IS_MUTANT = APP != (REPO / "app").resolve()
JS_DIR = REPO / "build" / "property" / ("js-mutant" if _IS_MUTANT else "js")
RUNNER = REPO / "eval" / "property_scheduler_runner.mjs"

# Everything the scheduler needs, in the app's own source. tsc follows the imports from here.
SCHEDULER_SOURCES = [
    "src/calmframes/coverSchedule.ts",
    "src/calmframes/mediaClock.ts",
    "src/calmframes/seekSafety.ts",
    "src/calmframes/household.ts",
    # The map reader, for eval/fuzz_maps_test.py. tsc pulls canonicalJson, ed25519 and sha512
    # in behind it, so the fuzzer reaches the real signature check and the real parser.
    "src/calmframes/flashMap.ts",
    # Scene holds are part of the signed map reader. An edit here must invalidate
    # the cached compile too, rather than replaying the prior parser.
    "src/calmframes/sceneHolds.ts",
]

REQUIRED = os.environ.get("CALM_FRAMES_REQUIRE_NODE") == "1"


class RunnerUnavailable(RuntimeError):
    pass


def _skip_or_fail(reason: str):
    if REQUIRED:
        pytest.fail(f"CALM_FRAMES_REQUIRE_NODE=1 and {reason}")
    pytest.skip(reason)


def node_path() -> str | None:
    return shutil.which("node")


def compile_scheduler(force: bool = False) -> Path:
    """Compile the scheduler to plain JavaScript with the app's own tsc.

    Raises RunnerUnavailable rather than skipping, so a caller can decide what a missing
    toolchain means. `make properties` treats it as a failure.
    """
    newest = max((APP / name).stat().st_mtime for name in SCHEDULER_SOURCES)
    built = JS_DIR / "coverSchedule.js"
    # A mutant copy always recompiles. Restoring a file from a backup puts its old timestamp
    # back, so an mtime check would happily hand the next mutation the previous one's build.
    if not force and not _IS_MUTANT and built.exists() and built.stat().st_mtime >= newest:
        return JS_DIR

    if node_path() is None:
        raise RunnerUnavailable("node is not on PATH, so the app's scheduler cannot be run")
    tsc = APP / "node_modules" / ".bin" / "tsc"
    if not tsc.exists():
        raise RunnerUnavailable(
            f"{tsc} is missing, so run npm install in app/ before the scheduler properties"
        )

    JS_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        str(tsc),
        "--outDir", str(JS_DIR),
        "--module", "commonjs",
        "--target", "es2020",
        "--moduleResolution", "node",
        "--skipLibCheck",
        "--strict", "false",
        *SCHEDULER_SOURCES,
    ]
    result = subprocess.run(command, cwd=APP, capture_output=True, text=True)
    if result.returncode != 0 or not built.exists():
        raise RunnerUnavailable(
            "tsc could not compile the scheduler:\n" + (result.stdout + result.stderr)[-2000:]
        )
    return JS_DIR


def compiled_digest(js_dir: Path | None = None) -> str:
    """A hash of the compiled scheduler.

    The mutation gate compares this before and after a mutation. A mutated TypeScript file
    that compiles to the same bytes never reached the code that runs, and a mutation that
    never reached the code cannot be said to have been killed.
    """
    target = js_dir or JS_DIR
    sha = hashlib.sha256()
    for path in sorted(target.glob("*.js")):
        sha.update(path.name.encode())
        sha.update(path.read_bytes())
    return sha.hexdigest()


class SchedulerRunner:
    """One node process, many scenarios.

    Starting node costs about fifty milliseconds and hypothesis wants hundreds of examples,
    so the process is started once and fed one JSON line per example.
    """

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None

    def __enter__(self) -> "SchedulerRunner":
        js_dir = compile_scheduler()
        self._process = subprocess.Popen(
            [node_path(), str(RUNNER), "--js", str(js_dir)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=REPO,
        )
        return self

    def __exit__(self, *exc) -> None:
        if self._process is None:
            return
        try:
            if self._process.stdin:
                self._process.stdin.close()
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
        self._process = None

    def call(self, job: dict) -> dict:
        if self._process is None or self._process.stdin is None or self._process.stdout is None:
            raise RunnerUnavailable("the scheduler runner is not started")
        self._process.stdin.write(json.dumps(job) + "\n")
        self._process.stdin.flush()
        line = self._process.stdout.readline()
        if not line:
            stderr = self._process.stderr.read() if self._process.stderr else ""
            raise RunnerUnavailable(f"the scheduler runner stopped: {stderr[-2000:]}")
        return json.loads(line)


@pytest.fixture(scope="session")
def scheduler():
    """A running scheduler, shared by every property test in the session."""
    try:
        runner = SchedulerRunner()
        runner.__enter__()
    except RunnerUnavailable as error:
        _skip_or_fail(str(error))
        return
    try:
        yield runner
    finally:
        runner.__exit__(None, None, None)


def main(argv: list[str] | None = None) -> int:
    """Compile the scheduler, for `make properties` to call before pytest."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        out = compile_scheduler(force="--force" in argv)
    except RunnerUnavailable as error:
        print(f"the scheduler property tests cannot run: {error}", file=sys.stderr)
        return 1
    print(f"the app's scheduler is compiled into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
