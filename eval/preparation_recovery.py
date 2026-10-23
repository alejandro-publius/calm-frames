"""Interrupt, damage and restart real preparations, and write down what happened.

    .venv/bin/python -m eval.preparation_recovery \\
        --out results/preparation-recovery-2026-10-21/evidence.json

Every scenario runs the pipeline through its own command lines, each in a process of
its own: ``python -m pipeline.local_library prepare``, which issues the local ready
receipt, and ``python -m pipeline.ingest``, which publishes to the kid mode index.
Interruptions are SIGKILL sent to the whole process group, at exact points where a
test double pauses (the fake analyzer, or a wrapper around ffmpeg that writes half of
one file and stops), or at timed points across a whole run. Damage is done between
runs to files this script created.

Fixtures are one generated calm clip (a slowly drifting grey gradient with a sine
tone, the same generator the pipeline tests use) and fresh Ed25519 test keys, all in
a temporary directory this script creates and removes. Nothing is played, nothing
goes to the network, and no repository file is written except ``--out``.

The fake analyzer from pipeline/tests stands in for flashmap in every scenario but
one: its flagged spans are scripted, while hashing, source binding and Ed25519
signing are real. The last scenario runs the real flashmap CLI.

A recovered or repaired result is compared with an uninterrupted run of the same
source, keys and settings at the same path. Compared: each step's fingerprint and
recorded output hashes from the ledger, the SHA-256 of every file in the title, the
verify report and the receipt. Left out, because they record when something ran:
ledger completion times, the verify report's start and finish times, and the two
receipt digests that cover those files. Lock and temporary files are left out too.

``--code-root DIR`` runs the same scenarios against another checkout, for example
the commit before this change, to show what failed there. The harness, the fake
analyzer, the clip and the ffmpeg wrapper always come from this checkout.

``--mutations`` also breaks each recovery guard in a copy of the code, using the
mutation gate's own harness (eval/mutate_gate.py), and records that its tests fail.

Exit status 0 means every scenario met its expectation.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import platform
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from pipeline.tests.clips import make_calm_clip

HARNESS_ROOT = Path(__file__).resolve().parent.parent
FAKE_ANALYZER = HARNESS_ROOT / "pipeline" / "tests" / "fake_flashmap.py"
SOURCE_NAME = "calm-source.mp4"
CLIP = {"seconds": 5.0, "width": 320, "height": 180, "fps": 30}
FLAGGED = [[2000, 2500, "general"]]
PRESETS = ("wcag", "broadcast", "extra-cautious")
TITLE = "Calm recovery fixture"
KILL_WAIT_S = 300.0
RUN_TIMEOUT_S = 900.0
SWEEP_FRACTIONS = (0.1, 0.25, 0.4, 0.55, 0.7, 0.85)
RUN_TIME_FILES = {"state.json", "state.json.malformed", "verify/report.json"}

FFMPEG_WRAPPER = '''#!{python}
"""Test double for ffmpeg: one named output is cut in half, then the process stops."""
import os, shutil, subprocess, sys, tempfile, time
real = os.environ["RECOVERY_REAL_FFMPEG"]
args = sys.argv[1:]
suffix = os.environ.get("RECOVERY_BLOCK_SUFFIX", "")
marker = os.environ.get("RECOVERY_BLOCK_MARKER", "")
if args and suffix and marker and args[-1].endswith(suffix) and not os.path.exists(marker):
    out = args[-1]
    scratch = tempfile.mkdtemp(prefix="recovery-ffmpeg-")
    full = os.path.join(scratch, os.path.basename(out))
    done = subprocess.run([real, *args[:-1], full])
    if done.returncode != 0:
        sys.exit(done.returncode)
    with open(full, "rb") as handle:
        data = handle.read()
    shutil.rmtree(scratch)
    with open(out, "wb") as handle:
        handle.write(data[: len(data) // 2])
    with open(marker, "w") as handle:
        handle.write(str(os.getpid()))
    time.sleep(120)
    sys.exit(1)
os.execv(real, [real, *args])
'''


class ScenarioError(RuntimeError):
    """The harness could not carry a scenario out, which counts as a failure."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else ""


class Run:
    def __init__(self, returncode: int, stdout: str, stderr: str, seconds: float) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.seconds = round(seconds, 2)

    @property
    def receipt(self) -> dict | None:
        try:
            value = json.loads(self.stdout)
        except ValueError:
            return None
        return value if isinstance(value, dict) else None

    @property
    def ingest_summary(self) -> dict | None:
        start = self.stdout.find("\n[")
        text = self.stdout[start + 1:] if start >= 0 else self.stdout
        try:
            value = json.loads(text)
        except ValueError:
            return None
        return value[0] if isinstance(value, list) and value and isinstance(value[0], dict) else None

    @property
    def status(self) -> str:
        receipt = self.receipt
        if receipt is not None:
            return str(receipt.get("status"))
        return f"no receipt (exit {self.returncode})"


class Lab:
    """One temporary directory: the clip, the keys, and the paths every scenario reuses."""

    def __init__(self, code_root: Path, base: Path) -> None:
        self.code_root = code_root
        self.base = base
        self.fixtures = base / "fixtures"
        self.markers = base / "markers"
        self.live = base / "library"
        self.reference_copy = base / "reference-library"
        self.ingest_work = base / "ingest-work"
        self.fixtures.mkdir(parents=True)
        self.markers.mkdir()
        self.source = make_calm_clip(self.fixtures / SOURCE_NAME, **CLIP)
        self.sha = sha256(self.source.read_bytes())
        self.keys = {name: self._keypair(name) for name in ("a", "b")}
        self.plan_path = self.fixtures / "analyzer-plan.json"
        self.write_plan()
        self.real_ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        self.ffmpeg_wrapper = self.fixtures / "ffmpeg-wrapper"
        self.ffmpeg_wrapper.write_text(FFMPEG_WRAPPER.format(python=sys.executable))
        self.ffmpeg_wrapper.chmod(0o755)

    def _keypair(self, name: str) -> tuple[Path, Path]:
        key = ed25519.Ed25519PrivateKey.generate()
        private, public = self.fixtures / f"{name}.pem", self.fixtures / f"{name}.pub.pem"
        private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption()))
        public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                         serialization.PublicFormat.SubjectPublicKeyInfo))
        return private, public

    def write_plan(self, *, block: dict | None = None, extra_rules: tuple[dict, ...] = ()) -> None:
        plan: dict[str, Any] = {"rules": [*extra_rules, {"match": SOURCE_NAME, "segments_all": FLAGGED}]}
        if block:
            plan["block"] = [block]
        self.plan_path.write_text(json.dumps(plan, indent=2))

    def env(self, *, real_analyzer: bool = False, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(self.code_root), str(self.code_root / "flashmap" / "src")])
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.pop("CALM_FRAMES_FFMPEG", None)
        if real_analyzer:
            env["CALM_FRAMES_FLASHMAP_CMD"] = f"{shlex.quote(sys.executable)} -m flashmap"
            env.pop("FAKE_FLASHMAP_PLAN", None)
        else:
            env["CALM_FRAMES_FLASHMAP_CMD"] = f"{shlex.quote(sys.executable)} {shlex.quote(str(FAKE_ANALYZER))}"
            env["FAKE_FLASHMAP_PLAN"] = str(self.plan_path)
        env.update(extra or {})
        return env

    def prepare_command(self, key: str = "a") -> list[str]:
        private, public = self.keys[key]
        return [sys.executable, "-m", "pipeline.local_library", "prepare", str(self.source),
                "--workdir", str(self.live), "--key", str(private), "--pub", str(public),
                "--presets", ",".join(PRESETS), "--title", TITLE]

    def catalog_command(self) -> list[str]:
        return [sys.executable, "-m", "pipeline.local_library", "catalog", "--workdir", str(self.live)]

    def ingest_command(self, *extra: str) -> list[str]:
        private, public = self.keys["a"]
        return [sys.executable, "-m", "pipeline.ingest", str(self.source), "--workdir", str(self.ingest_work),
                "--presets", "wcag", "--key", str(private), "--pub", str(public),
                "--x264-preset", "ultrafast", "--poster-count", "1", "--json", *extra]

    def run(self, command: list[str], *, env: dict[str, str] | None = None) -> Run:
        started = time.monotonic()
        completed = subprocess.run(command, cwd=self.code_root, env=env or self.env(), capture_output=True,
                                   text=True, timeout=RUN_TIMEOUT_S, check=False)
        return Run(completed.returncode, completed.stdout, completed.stderr, time.monotonic() - started)

    def start(self, command: list[str], *, env: dict[str, str] | None = None) -> subprocess.Popen:
        process = subprocess.Popen(command, cwd=self.code_root, env=env or self.env(), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True)
        process.started = time.monotonic()  # type: ignore[attr-defined]
        return process

    def _kill(self, process: subprocess.Popen) -> dict:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass  # already ending; macOS answers EPERM for a group of zombies
        process.communicate(timeout=60)
        deadline = time.monotonic() + 10
        group_gone = False
        while time.monotonic() < deadline:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                group_gone = True
                break
            except PermissionError:
                pass  # macOS: killed children that are not yet reaped answer EPERM
            time.sleep(0.05)
        return {"signal": "SIGKILL", "sent_to": "the whole process group", "exit": process.returncode,
                "every_process_in_the_group_ended": group_gone,
                "after_s": round(time.monotonic() - process.started, 2)}  # type: ignore[attr-defined]

    def kill_at(self, process: subprocess.Popen, ready: Callable[[], bool]) -> dict:
        deadline = time.monotonic() + KILL_WAIT_S
        while not ready():
            if process.poll() is not None:
                _, err = process.communicate()
                raise ScenarioError(f"the run ended with exit {process.returncode} before the kill point: "
                                    f"{self.scrub(err)[-600:]}")
            if time.monotonic() > deadline:
                self._kill(process)
                raise ScenarioError("the run never reached the kill point")
            time.sleep(0.02)
        return self._kill(process)

    def kill_after(self, process: subprocess.Popen, seconds: float) -> dict:
        deadline = process.started + seconds  # type: ignore[attr-defined]
        while time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.005)
        if process.poll() is not None:
            process.communicate()
            return {"completed_before_the_kill": True, "exit": process.returncode}
        return {"completed_before_the_kill": False, **self._kill(process)}

    def reset(self, *, from_reference: bool) -> None:
        if self.live.exists():
            shutil.rmtree(self.live)
        if from_reference:
            shutil.copytree(self.reference_copy, self.live, symlinks=True)

    def reset_ingest(self) -> None:
        if self.ingest_work.exists():
            shutil.rmtree(self.ingest_work)

    def title(self, workdir: Path | None = None) -> Path:
        return (workdir or self.live) / "titles" / self.sha

    def ledger(self, workdir: Path | None = None) -> dict[str, dict]:
        try:
            data = json.loads((self.title(workdir) / "state.json").read_text())
        except (OSError, ValueError):
            return {}
        steps = data.get("steps") if isinstance(data, dict) else None
        view: dict[str, dict] = {}
        for name, record in (steps if isinstance(steps, dict) else {}).items():
            if isinstance(record, dict):
                digests = record.get("output_sha256")
                view[name] = {
                    "fingerprint": record.get("fingerprint"),
                    "completed_at": record.get("completed_at"),
                    "outputs": ({k: v for k, v in digests.items() if k not in RUN_TIME_FILES}
                                if isinstance(digests, dict) else None),
                }
        return view

    def receipt_status(self) -> str | None:
        try:
            return json.loads((self.live / "local-receipts" / f"{self.sha}.json").read_text()).get("status")
        except (OSError, ValueError, AttributeError):
            return None

    def listed(self) -> int | None:
        try:
            return len(json.loads((self.live / "local-library.json").read_text())["titles"])
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def refresh(self) -> int | None:
        run = self.run(self.catalog_command())
        titles = run.receipt.get("titles") if run.receipt else None
        return len(titles) if isinstance(titles, list) else None

    def tree(self, workdir: Path) -> dict[str, str]:
        """Every file under a work directory by SHA-256, locks left out."""
        return {path.relative_to(workdir).as_posix(): sha256(path.read_bytes())
                for path in sorted(workdir.rglob("*"))
                if path.is_file() and not path.is_symlink() and not path.name.endswith(".lock")}

    def kid_mode(self, workdir: Path) -> list[str]:
        try:
            titles = json.loads((workdir / "catalog.json").read_text())["titles"]
        except (OSError, ValueError, KeyError, TypeError):
            return []
        return sorted(sha for sha, entry in titles.items()
                      if entry.get("verified") is True and entry.get("status") == "verified")

    def identity(self, receipt: dict | None, *, workdir: Path | None = None, real_analyzer: bool = False) -> dict:
        root = self.title(workdir)
        files: dict[str, str] = {}
        if root.is_dir():
            for path in sorted(root.rglob("*")):
                name = path.relative_to(root).as_posix()
                if (not path.is_file() or path.is_symlink() or name in RUN_TIME_FILES
                        or path.name.startswith(".") or name.endswith(".tmp")):
                    continue
                data = path.read_bytes()
                if real_analyzer and name.endswith(".json"):
                    data = normalized_map(data)
                files[name] = sha256(data)
        ledger = {name: {"fingerprint": v["fingerprint"], "outputs": v["outputs"]} for name, v in self.ledger(workdir).items()}
        if real_analyzer:
            # Maps carry created_utc and a signature over it, which every analyzer run
            # changes. Step fingerprints chain those maps, so only the step names and
            # the hashes of outputs that are not maps are compared here.
            ledger = {name: {"outputs": {k: v for k, v in (record["outputs"] or {}).items()
                                         if not k.endswith(".json")}} for name, record in ledger.items()}
        try:
            report = json.loads((root / "verify" / "report.json").read_text())
            report.pop("started_at", None)
            report.pop("finished_at", None)
        except (OSError, ValueError):
            report = None
        return {"ledger": ledger, "files": files, "report": report,
                "receipt": receipt_view(receipt, real_analyzer=real_analyzer)}

    def scrub(self, text: str) -> str:
        """Keep machine paths out of the evidence."""
        for path, label in ((self.base, "<tmp>"), (self.code_root, "<code>"), (HARNESS_ROOT, "<harness>"),
                            (Path.home(), "<home>")):
            text = text.replace(str(path), label)
        return text


def normalized_map(data: bytes) -> bytes:
    try:
        document = json.loads(data)
    except ValueError:
        return data
    if not isinstance(document, dict) or "created_utc" not in document:
        return data
    document.pop("created_utc")
    signature = document.get("signature")
    if isinstance(signature, dict):
        document["signature"] = {k: v for k, v in signature.items() if k not in ("value", "payload_sha256")}
    return json.dumps(document, sort_keys=True).encode()


def receipt_view(receipt: dict | None, *, real_analyzer: bool = False) -> dict | None:
    if not isinstance(receipt, dict):
        return None
    view = json.loads(json.dumps(receipt))
    verification = view.get("verification")
    if isinstance(verification, dict):
        verification.pop("checked_inputs_sha256", None)
        verification.pop("report_sha256", None)
    if real_analyzer:
        for artifact in (view.get("artifacts") or {}).values():
            if isinstance(artifact, dict) and isinstance(artifact.get("sha256"), dict):
                artifact["sha256"] = {k: v for k, v in artifact["sha256"].items() if "/maps/" not in k}
    return view


def differences(expected: dict, actual: dict) -> list[str]:
    found = []
    for section in ("ledger", "files", "report", "receipt"):
        a, b = expected.get(section), actual.get(section)
        if a == b:
            continue
        if isinstance(a, dict) and isinstance(b, dict):
            changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            found.append(f"{section}: {len(changed)} differ ({', '.join(changed[:6])})")
        else:
            found.append(f"{section} differs")
    return found


def reran(before: dict, after: dict) -> list[str]:
    changed = [name for name, record in after.items()
               if name not in before or record["completed_at"] != before[name]["completed_at"]]
    return sorted(changed, key=lambda name: after[name]["completed_at"] or 0)


def flip_byte(path: Path) -> None:
    data = bytearray(path.read_bytes())
    data[len(data) // 2] ^= 0x01
    path.write_bytes(bytes(data))


def zero_middle(path: Path, length: int = 4096) -> None:
    data = bytearray(path.read_bytes())
    middle = len(data) // 2
    data[middle:middle + length] = bytes(min(length, len(data) - middle))
    path.write_bytes(bytes(data))


def flip_digit(path: Path) -> None:
    text = path.read_text()
    index = next(i for i, ch in enumerate(text) if ch.isdigit() and ch != "9" and i > len(text) // 3)
    path.write_text(text[:index] + str(int(text[index]) + 1) + text[index + 1:])


def signed_by(document: dict, public_path: Path) -> bool:
    """Whether this map's Ed25519 signature checks against this public key."""
    signature = document.get("signature") or {}
    body = {k: v for k, v in document.items() if k != "signature"}
    payload = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                         allow_nan=False).encode("utf-8")
    key = serialization.load_pem_public_key(public_path.read_bytes())
    try:
        key.verify(base64.b64decode(signature["value"]), payload)  # type: ignore[union-attr]
    except (InvalidSignature, KeyError, TypeError, ValueError):
        return False
    return True


class Outcome:
    def __init__(self, sid: str, requirements: list[str], procedure: str, expected: str) -> None:
        self.record: dict[str, Any] = {"id": sid, "requirements": requirements, "procedure": procedure,
                                       "expected": expected, "observed": {}, "result": "", "unmet": []}

    def observe(self, **values: Any) -> None:
        self.record["observed"].update(values)

    def expect(self, condition: bool, description: str) -> None:
        if not condition:
            self.record["unmet"].append(description)

    def done(self) -> dict:
        self.record["result"] = "pass" if not self.record["unmet"] else "fail"
        return self.record


class Reference:
    def __init__(self, identity: dict, seconds: float, receipt: dict) -> None:
        self.identity = identity
        self.seconds = seconds
        self.receipt = receipt


def artifact_hashes(receipt: dict | None) -> dict[str, str]:
    found: dict[str, str] = {}
    for artifact in ((receipt or {}).get("artifacts") or {}).values():
        found.update(artifact.get("sha256") or {})
    return found


READY_SEEN: list[tuple[str, dict, dict]] = []


def note_ready(scenario: str, receipt: dict | None, expected: dict, *, real_analyzer: bool = False) -> None:
    """Every ready receipt anyone saw, for the closing check of what ready receipts named.

    With the real analyzer a rebuilt map has a new created_utc, so its bytes differ
    from the reference's while being exactly what verify checked; map hashes are
    left out of that one comparison, as everywhere else for the real analyzer.
    """
    if isinstance(receipt, dict) and receipt.get("status") == "ready":
        READY_SEEN.append((scenario, receipt_view(receipt, real_analyzer=real_analyzer) or {},
                           receipt_view(expected, real_analyzer=real_analyzer) or {}))


# ------------------------------------------------------------------------- scenarios


def no_op_restart(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome("no_op_restart", ["unaffected cached work is reused"],
                  "Run the same preparation again over the finished reference library.",
                  "Ready again, no step runs again, and the identity equals the reference.")
    lab.reset(from_reference=True)
    before = lab.ledger()
    run = lab.run(lab.prepare_command())
    rerun = reran(before, lab.ledger())
    diff = differences(ref.identity, lab.identity(run.receipt))
    note_ready(out.record["id"], run.receipt, ref.receipt)
    out.observe(status=run.status, steps_run_again=rerun, identity_differences=diff, seconds=run.seconds)
    out.expect(run.status == "ready", "the run is ready")
    out.expect(rerun == [], "no step runs again")
    out.expect(not diff, "the identity equals the uninterrupted reference")
    return out


def sigkill_after_commit(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "sigkill_after_step_commit",
        ["interruption after step commit", "interruption before step commit",
         "real subprocess kill and restart", "unaffected cached work is reused"],
        "Prepare from nothing; the analyzer pauses inside the broadcast analysis after "
        "writing 300 bytes of its map, by which time the WCAG analysis has committed. "
        "SIGKILL the process group there, then run the same command again.",
        "While killed the receipt is not ready and nothing is listed. The restart reuses the "
        "committed WCAG analysis, redoes the torn one, is ready, and its identity equals the reference.")
    lab.reset(from_reference=False)
    marker = lab.markers / "after-commit"
    lab.write_plan(block={"match": SOURCE_NAME, "profile": "broadcast", "partial_bytes": 300,
                          "marker": str(marker), "seconds": 120})
    kill = lab.kill_at(lab.start(lab.prepare_command()), marker.exists)
    lab.write_plan()
    at_kill = lab.ledger()
    torn = {name: (lab.title() / name).stat().st_size for name in ("work/analysis/broadcast.json", "maps/broadcast.json")
            if (lab.title() / name).exists()}
    observed = {"kill": kill, "committed_at_kill": sorted(at_kill), "receipt_status_at_kill": lab.receipt_status(),
                "listed_at_kill": lab.listed(), "torn_analysis_map_bytes": torn}
    run = lab.run(lab.prepare_command())
    after = lab.ledger()
    diff = differences(ref.identity, lab.identity(run.receipt))
    note_ready(out.record["id"], run.receipt, ref.receipt)
    out.observe(**observed, restart_status=run.status, steps_run_again=reran(at_kill, after),
                identity_differences=diff)
    out.expect(kill["every_process_in_the_group_ended"], "every process of the killed run ended")
    out.expect("analyze:wcag" in at_kill, "the WCAG analysis had committed before the kill")
    out.expect(observed["receipt_status_at_kill"] != "ready" and not observed["listed_at_kill"],
               "nothing is ready or listed while the run is dead")
    out.expect(run.status == "ready", "the restart is ready")
    out.expect(at_kill.get("analyze:wcag", {}).get("completed_at") == after.get("analyze:wcag", {}).get("completed_at"),
               "the committed WCAG analysis is reused, not redone")
    out.expect(not diff, "the identity equals the uninterrupted reference")
    return out


def sigkill_mid_rewrite(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "sigkill_before_step_commit_with_partial_output",
        ["interruption before step commit", "missing output", "real subprocess kill and restart",
         "invalidated work is regenerated"],
        "From the finished reference, delete the WCAG safe master so its rendition step has to "
        "run again. An ffmpeg wrapper writes half of the new master at the real path and stops; "
        "SIGKILL the process group there, then run the same command with the real ffmpeg.",
        "No record vouches for the half-written master, nothing is ready while the run is dead, "
        "and the restart rebuilds the rendition, is ready, and equals the reference.")
    lab.reset(from_reference=True)
    master = lab.title() / "safe" / "wcag" / "safe.mp4"
    reference_size = master.stat().st_size
    master.unlink()
    marker = lab.markers / "mid-encode"
    env = lab.env(extra={"CALM_FRAMES_FFMPEG": str(lab.ffmpeg_wrapper), "RECOVERY_REAL_FFMPEG": lab.real_ffmpeg,
                         "RECOVERY_BLOCK_SUFFIX": "/safe/wcag/safe.mp4", "RECOVERY_BLOCK_MARKER": str(marker)})
    kill = lab.kill_at(lab.start(lab.prepare_command(), env=env), marker.exists)
    at_kill = lab.ledger()
    observed = {"kill": kill, "master_bytes_at_kill": master.stat().st_size if master.exists() else None,
                "reference_master_bytes": reference_size,
                "rendition_record_at_kill": "rendition:wcag" in at_kill,
                "receipt_status_at_kill": lab.receipt_status(), "listed_at_kill": lab.listed()}
    run = lab.run(lab.prepare_command())
    diff = differences(ref.identity, lab.identity(run.receipt))
    note_ready(out.record["id"], run.receipt, ref.receipt)
    out.observe(**observed, restart_status=run.status, steps_run_again=reran(at_kill, lab.ledger()),
                identity_differences=diff)
    out.expect(kill["every_process_in_the_group_ended"], "every process of the killed run ended")
    out.expect(observed["master_bytes_at_kill"] is not None and observed["master_bytes_at_kill"] < reference_size,
               "a partial master was on disk when the run died")
    out.expect(not observed["rendition_record_at_kill"], "no rendition record vouched for the partial master")
    out.expect(observed["receipt_status_at_kill"] != "ready" and not observed["listed_at_kill"],
               "nothing is ready or listed while the run is dead")
    out.expect(run.status == "ready", "the restart is ready")
    out.expect(not diff, "the identity equals the uninterrupted reference")
    return out


def sigkill_during_verify(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "sigkill_during_verification",
        ["interruption after step commit", "real subprocess kill and restart", "unaffected cached work is reused"],
        "From the finished reference, remove the verify report so verification has to run; the "
        "analyzer pauses while verify measures the broadcast safe master. SIGKILL the group, restart.",
        "Nothing is ready while the run is dead; the restart runs only verification again, is "
        "ready, and equals the reference.")
    lab.reset(from_reference=True)
    (lab.title() / "verify" / "report.json").unlink()
    before = lab.ledger()
    marker = lab.markers / "verify"
    lab.write_plan(block={"match": "/safe/broadcast/safe.mp4", "marker": str(marker), "seconds": 120})
    kill = lab.kill_at(lab.start(lab.prepare_command()), marker.exists)
    lab.write_plan()
    observed = {"kill": kill, "verify_record_at_kill": "verify" in lab.ledger(),
                "receipt_status_at_kill": lab.receipt_status(), "listed_at_kill": lab.listed()}
    run = lab.run(lab.prepare_command())
    rerun = reran(before, lab.ledger())
    diff = differences(ref.identity, lab.identity(run.receipt))
    note_ready(out.record["id"], run.receipt, ref.receipt)
    out.observe(**observed, restart_status=run.status, steps_run_again=rerun, identity_differences=diff)
    out.expect(kill["every_process_in_the_group_ended"], "every process of the killed run ended")
    out.expect(observed["receipt_status_at_kill"] != "ready" and not observed["listed_at_kill"],
               "nothing is ready or listed while the run is dead")
    out.expect(run.status == "ready", "the restart is ready")
    out.expect(rerun == ["verify"], "only verification runs again")
    out.expect(not diff, "the identity equals the uninterrupted reference")
    return out


def sigkill_sweep(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "sigkill_sweep",
        ["real subprocess kill and restart", "interruption before step commit", "interruption after step commit"],
        f"Prepare from nothing and SIGKILL the process group at {len(SWEEP_FRACTIONS)} times spread "
        "across the reference run's duration, then restart each one.",
        "Every killed run is not ready and not listed at the moment of the kill, and every "
        "restart is ready with the reference identity.")
    kills = []
    for fraction in SWEEP_FRACTIONS:
        lab.reset(from_reference=False)
        kill = lab.kill_after(lab.start(lab.prepare_command()), ref.seconds * fraction)
        at_kill = lab.ledger()
        point = {"fraction_of_reference_run": fraction, **kill, "committed_at_kill": len(at_kill),
                 "last_committed": max(at_kill, key=lambda n: at_kill[n]["completed_at"] or 0) if at_kill else None,
                 "receipt_status_at_kill": lab.receipt_status(), "listed_at_kill": lab.listed(),
                 "temporary_files_left": sorted(p.name for p in lab.title().glob(".*.tmp")) if lab.title().exists() else []}
        run = lab.run(lab.prepare_command())
        diff = differences(ref.identity, lab.identity(run.receipt))
        note_ready(out.record["id"], run.receipt, ref.receipt)
        point.update(restart_status=run.status, steps_run_again=len(reran(at_kill, lab.ledger())),
                     identity_differences=diff)
        kills.append(point)
        if not kill["completed_before_the_kill"]:
            out.expect(kill["every_process_in_the_group_ended"], f"every process ended after the kill at {fraction}")
            out.expect(point["receipt_status_at_kill"] != "ready" and not point["listed_at_kill"],
                       f"nothing is ready while killed at {fraction}")
        out.expect(run.status == "ready" and not diff, f"the restart after {fraction} is ready and identical")
    out.observe(kills=kills, interrupted=sum(1 for k in kills if not k["completed_before_the_kill"]))
    out.expect(any(not k["completed_before_the_kill"] for k in kills), "at least one run was interrupted")
    return out


def truncated_ledger(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "truncated_ledger",
        ["truncated ledger", "malformed state is never trusted"],
        "From the finished reference, cut the ledger to half its length, refresh the catalog, then prepare again.",
        "The refresh withdraws the receipt; the run keeps the unreadable ledger as "
        "state.json.malformed, prepares the title again, is ready, and equals the reference.")
    lab.reset(from_reference=True)
    ledger = lab.title() / "state.json"
    torn = ledger.read_bytes()[: ledger.stat().st_size // 2]
    ledger.write_bytes(torn)
    listed = lab.refresh()
    run = lab.run(lab.prepare_command())
    kept = lab.title() / "state.json.malformed"
    diff = differences(ref.identity, lab.identity(run.receipt))
    note_ready(out.record["id"], run.receipt, ref.receipt)
    out.observe(listed_after_refresh=listed, status=run.status,
                malformed_ledger_kept=kept.exists() and kept.read_bytes() == torn, identity_differences=diff)
    out.expect(listed == 0, "the refresh lists nothing")
    out.expect(run.status == "ready", "the run is ready")
    out.expect(kept.exists() and kept.read_bytes() == torn, "the unreadable ledger is kept aside, unchanged")
    out.expect(not diff, "the identity equals the uninterrupted reference")
    return out


def malformed_ledgers(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "malformed_ledger_shapes",
        ["malformed state is never trusted", "truncated ledger"],
        "From the finished reference, replace the ledger with valid JSON that is not an object, "
        "with bytes that are not UTF-8, and with an object whose steps are a list; prepare each.",
        "Each run handles the ledger predictably, is ready, and equals the reference.")
    shapes = {
        "not_an_object": b"[]",
        "not_utf8": b"\xff\xfe\x00\x81 not text",
        "steps_not_an_object": json.dumps({"pipeline_version": "1", "source": {}, "steps": []}).encode(),
    }
    results = {}
    for shape, content in shapes.items():
        lab.reset(from_reference=True)
        (lab.title() / "state.json").write_bytes(content)
        run = lab.run(lab.prepare_command())
        diff = differences(ref.identity, lab.identity(run.receipt))
        note_ready(out.record["id"], run.receipt, ref.receipt)
        results[shape] = {"status": run.status, "identity_differences": diff,
                          "stderr_tail": lab.scrub(run.stderr)[-300:] if run.returncode not in (0, 1) else ""}
        out.expect(run.status == "ready" and not diff, f"{shape}: ready and identical")
    out.observe(runs=results)
    return out


def missing_output(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "missing_output",
        ["missing output", "invalidated work is regenerated", "unaffected cached work is reused"],
        "From the finished reference, delete the first broadcast HLS segment, refresh, then prepare.",
        "The refresh withdraws the receipt; only the broadcast rendition runs again; ready and identical.")
    lab.reset(from_reference=True)
    before = lab.ledger()
    sorted((lab.title() / "safe" / "broadcast" / "hls").glob("seg_*.ts"))[0].unlink()
    listed = lab.refresh()
    run = lab.run(lab.prepare_command())
    rerun = reran(before, lab.ledger())
    diff = differences(ref.identity, lab.identity(run.receipt))
    note_ready(out.record["id"], run.receipt, ref.receipt)
    out.observe(listed_after_refresh=listed, status=run.status, steps_run_again=rerun, identity_differences=diff)
    out.expect(listed == 0, "the refresh lists nothing")
    out.expect(run.status == "ready", "the run is ready")
    out.expect(rerun == ["rendition:broadcast"], "only the broadcast rendition runs again")
    out.expect(not diff, "the identity equals the uninterrupted reference")
    return out


CORRUPTIONS = {
    # name: (path in the title, damage, the step that owns it)
    "safe_master_wcag": ("safe/wcag/safe.mp4", zero_middle, "rendition:wcag"),
    "hls_segment_extra_cautious": ("safe/extra-cautious/hls/seg_0_00000.ts", flip_byte, "rendition:extra-cautious"),
    "plan_broadcast": ("plans/broadcast.json", flip_digit, "plan:broadcast"),
    "published_map_wcag": ("maps/wcag.json", flip_digit, "signed_map:wcag"),
    "luminance": ("luma.json", flip_digit, "luma"),
}


def same_size_corruption(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "same_size_corruption",
        ["same-size corruption", "invalidated work is regenerated", "unaffected cached work is reused",
         "corruption never yields a ready receipt"],
        "From the finished reference, change bytes without changing the size of a safe master, "
        "an HLS segment, a plan, a published map and the luminance record, one at a time; refresh "
        "the catalog; then prepare.",
        "Each refresh withdraws the receipt. Each run redoes only the step that owns the damaged "
        "file, is ready, and equals the reference, so no ready receipt names a damaged byte.")
    results = {}
    for name, (relative, damage, owner) in CORRUPTIONS.items():
        lab.reset(from_reference=True)
        path = lab.title() / relative
        if not path.exists():
            results[name] = {"skipped": f"{relative} does not exist in this checkout's layout"}
            out.expect(False, f"{name}: the file to damage exists")
            continue
        size = path.stat().st_size
        before = lab.ledger()
        damage(path)
        damaged_hash = sha256(path.read_bytes())
        listed = lab.refresh()
        run = lab.run(lab.prepare_command())
        rerun = reran(before, lab.ledger())
        diff = differences(ref.identity, lab.identity(run.receipt))
        note_ready(out.record["id"], run.receipt, ref.receipt)
        named = damaged_hash in artifact_hashes(run.receipt).values()
        results[name] = {"same_size": path.stat().st_size == size, "listed_after_refresh": listed,
                         "status": run.status, "steps_run_again": rerun,
                         "ready_receipt_names_damaged_bytes": named, "identity_differences": diff}
        out.expect(listed == 0, f"{name}: the refresh lists nothing")
        out.expect(run.status == "ready", f"{name}: the run is ready")
        out.expect(rerun == [owner], f"{name}: only {owner} runs again")
        out.expect(not named, f"{name}: no ready receipt names the damaged bytes")
        out.expect(not diff, f"{name}: the identity equals the reference")
    out.observe(corruptions=results)
    return out


def changed_signing_key(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "changed_settings_signing_key",
        ["changed settings", "invalidated work is regenerated", "signing requirements preserved"],
        "From the finished reference (key A), prepare with a new key pair B. Then prepare with B "
        "from nothing at the same path and compare.",
        "The analyses run again, every published map checks against B and not A, the run is "
        "ready, and its identity equals the clean run with B.")
    lab.reset(from_reference=True)
    before = lab.ledger()
    run = lab.run(lab.prepare_command(key="b"))
    rerun = reran(before, lab.ledger())
    maps = {}
    for preset in PRESETS:
        path = lab.title() / "maps" / f"{preset}.json"
        try:
            document = json.loads(path.read_text())
            maps[preset] = {"checks_with_b": signed_by(document, lab.keys["b"][1]),
                            "checks_with_a": signed_by(document, lab.keys["a"][1])}
        except (OSError, ValueError) as exc:
            maps[preset] = {"error": type(exc).__name__}
    incremental = lab.identity(run.receipt)
    lab.reset(from_reference=False)
    fresh_run = lab.run(lab.prepare_command(key="b"))
    fresh = lab.identity(fresh_run.receipt)
    diff = differences(fresh, incremental)
    note_ready(out.record["id"], run.receipt, fresh_run.receipt or {})
    out.observe(status=run.status, steps_run_again=rerun, maps=maps, clean_run_status=fresh_run.status,
                differences_from_clean_run=diff)
    out.expect(run.status == "ready", "the run with B is ready")
    out.expect(all(f"analyze:{p}" in rerun for p in PRESETS), "every analysis runs again")
    out.expect(all(m.get("checks_with_b") and not m.get("checks_with_a") for m in maps.values()),
               "every published map checks against B and not A")
    out.expect(fresh_run.status == "ready" and not diff, "the result equals a clean run with B")
    return out


def changed_guard_band(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "changed_settings_guard_band",
        ["changed settings", "invalidated work is regenerated", "unaffected cached work is reused"],
        "With the bare ingest command (one preset, ultrafast), prepare, then prepare again with "
        "a 1000 ms guard band; then prepare with 1000 ms from nothing at the same path.",
        "The second run redoes the plan and what depends on it but not probe, analysis or "
        "luminance, publishes to the kid mode index, and equals the clean 1000 ms run.")
    lab.reset_ingest()
    first = lab.run(lab.ingest_command())
    second = lab.run(lab.ingest_command("--guard-band-ms", "1000"))
    summary = second.ingest_summary or {}
    incremental = lab.identity(None, workdir=lab.ingest_work)
    listed = lab.kid_mode(lab.ingest_work)
    lab.ingest_work.rename(lab.base / "ingest-incremental")
    fresh_run = lab.run(lab.ingest_command("--guard-band-ms", "1000"))
    fresh = lab.identity(None, workdir=lab.ingest_work)
    diff = differences(fresh, incremental)
    out.observe(first_publishable=(first.ingest_summary or {}).get("publishable"),
                steps_run=summary.get("steps_run"), steps_skipped=summary.get("steps_skipped"),
                kid_mode_lists_title=listed == [lab.sha], clean_run_publishable=(fresh_run.ingest_summary or {}).get("publishable"),
                differences_from_clean_run=diff)
    out.expect(summary.get("publishable") is True and listed == [lab.sha], "the second run publishes")
    out.expect({"plan:wcag", "rendition:wcag", "cover_model:wcag"} <= set(summary.get("steps_run") or []),
               "the plan and its dependents run again")
    out.expect({"probe", "analyze:wcag", "luma"} <= set(summary.get("steps_skipped") or []),
               "probe, analysis and luminance are reused")
    out.expect(not diff, "the result equals a clean run with the new guard band")
    return out


def duplicate_invocation(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "duplicate_invocation",
        ["duplicate invocation", "locking preserved"],
        "Start a preparation that pauses for ten seconds inside its first analysis, and start a "
        "second identical one meanwhile: once through the local library command and once through "
        "the bare ingest command. Let the first finish.",
        "Both second invocations refuse at once as busy and change nothing; both first runs then "
        "finish, ready or published, and the library one equals the reference.")
    lab.reset(from_reference=False)
    marker = lab.markers / "duplicate-library"
    lab.write_plan(block={"match": SOURCE_NAME, "profile": "wcag", "marker": str(marker), "seconds": 10})
    first = lab.start(lab.prepare_command())
    deadline = time.monotonic() + KILL_WAIT_S
    while not marker.exists() and first.poll() is None and time.monotonic() < deadline:
        time.sleep(0.02)
    before = lab.tree(lab.live)
    second = lab.run(lab.prepare_command())
    library_unchanged = lab.tree(lab.live) == before
    stdout, _ = first.communicate(timeout=RUN_TIMEOUT_S)
    first_run = Run(first.returncode, stdout, "", 0.0)
    diff = differences(ref.identity, lab.identity(first_run.receipt))
    note_ready(out.record["id"], first_run.receipt, ref.receipt)
    library = {"second_exit": second.returncode, "second_said": (second.receipt or {}).get("error", {}).get("message"),
               "second_changed_no_file": library_unchanged, "second_seconds": second.seconds,
               "first_status": first_run.status, "identity_differences": diff}
    lab.reset_ingest()
    marker = lab.markers / "duplicate-ingest"
    lab.write_plan(block={"match": SOURCE_NAME, "profile": "wcag", "marker": str(marker), "seconds": 10})
    first = lab.start(lab.ingest_command())
    deadline = time.monotonic() + KILL_WAIT_S
    while not marker.exists() and first.poll() is None and time.monotonic() < deadline:
        time.sleep(0.02)
    before = lab.tree(lab.ingest_work)
    second = lab.run(lab.ingest_command())
    ingest_unchanged = lab.tree(lab.ingest_work) == before
    stdout, _ = first.communicate(timeout=RUN_TIMEOUT_S)
    lab.write_plan()
    first_ingest = Run(first.returncode, stdout, "", 0.0).ingest_summary or {}
    ingest = {"second_exit": second.returncode, "second_refused_as_busy": "busy" in second.stderr,
              "second_changed_no_file": ingest_unchanged, "second_seconds": second.seconds,
              "second_published": (second.ingest_summary or {}).get("publishable"),
              "first_published": first_ingest.get("publishable"),
              "kid_mode_lists_title": lab.kid_mode(lab.ingest_work) == [lab.sha]}
    out.observe(local_library=library, bare_ingest=ingest)
    out.expect(library["second_exit"] == 2 and "busy" in str(library["second_said"]),
               "the second library run refuses as busy")
    out.expect(library_unchanged, "the second library run changes no file")
    out.expect(ingest_unchanged, "the second ingest changes no file")
    out.expect(library["first_status"] == "ready" and not diff, "the first library run finishes ready and identical")
    out.expect(ingest["second_exit"] == 1 and ingest["second_refused_as_busy"], "the second ingest refuses as busy")
    out.expect(ingest["first_published"] is True and ingest["kid_mode_lists_title"], "the first ingest publishes")
    return out


def failed_verification(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "failed_verification",
        ["failed verification", "corruption never yields a ready receipt", "verification thresholds preserved"],
        "From the finished reference, make the analyzer report a flagged span in the broadcast safe "
        "master, prepare twice, then remove that and prepare again.",
        "Both runs fail verification, issue no ready receipt and list nothing, and the second one "
        "verifies again rather than reusing a verdict. Once the master measures clean the run is "
        "ready, redoes only verification, and equals the reference.")
    lab.reset(from_reference=True)
    (lab.title() / "verify" / "report.json").unlink()
    lab.write_plan(extra_rules=({"match": "/safe/broadcast/safe.mp4", "segments_all": [[1000, 1500, "general"]]},))
    first = lab.run(lab.prepare_command())
    first_ledger = lab.ledger()
    failed_checks = [c.get("name") for c in ((first.receipt or {}).get("verification") or {}).get("failed_checks", [])]
    listed_first = lab.listed()
    second = lab.run(lab.prepare_command())
    second_ledger = lab.ledger()
    lab.write_plan()
    third = lab.run(lab.prepare_command())
    diff = differences(ref.identity, lab.identity(third.receipt))
    note_ready(out.record["id"], third.receipt, ref.receipt)
    out.observe(first_status=first.status, failed_checks=failed_checks, listed_after_first=listed_first,
                second_status=second.status, second_ran_verify_again=reran(first_ledger, second_ledger),
                third_status=third.status, third_steps_run_again=reran(second_ledger, lab.ledger()),
                identity_differences=diff)
    out.expect(first.status == "failed" and second.status == "failed", "both flagged runs fail")
    out.expect(any(str(name).startswith("safe_rendition_clean:broadcast") for name in failed_checks),
               "the failing check is the broadcast rendition measurement")
    out.expect(listed_first == 0, "nothing is listed after a failed run")
    out.expect(reran(first_ledger, second_ledger) == ["verify"], "the second run verifies again")
    out.expect(third.status == "ready" and not diff, "once clean, the run is ready and identical")
    out.expect(reran(second_ledger, lab.ledger()) == ["verify"], "once clean, only verification runs again")
    return out


def negative_controls(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "negative_controls",
        ["corruption never yields a ready receipt", "the comparison can see a difference"],
        "Corrupt a finished library without preparing again and refresh the catalog: a safe master, "
        "an HLS segment, the verify report and the ledger, one at a time. Separately, feed the identity "
        "comparison a copy of the reference with one file hash changed.",
        "Every refresh lists nothing, and the comparison reports exactly the changed file.")
    targets = {"safe_master": "safe/wcag/safe.mp4", "hls_segment": "safe/broadcast/hls/seg_0_00000.ts",
               "verify_report": "verify/report.json", "ledger": "state.json"}
    refreshed = {}
    for name, relative in targets.items():
        lab.reset(from_reference=True)
        listed_before = lab.refresh()
        flip_byte(lab.title() / relative)
        refreshed[name] = {"listed_before": listed_before, "listed_after_corruption": lab.refresh()}
        out.expect(listed_before == 1 and refreshed[name]["listed_after_corruption"] == 0,
                   f"{name}: listed before, withdrawn after the corruption")
    tampered = json.loads(json.dumps(ref.identity))
    first_file = sorted(tampered["files"])[0]
    tampered["files"][first_file] = "0" * 64
    found = differences(ref.identity, tampered)
    out.observe(refresh=refreshed, comparison_of_identical=differences(ref.identity, ref.identity),
                comparison_with_one_changed_file=found)
    out.expect(differences(ref.identity, ref.identity) == [], "identical identities compare equal")
    out.expect(found == [f"files: 1 differ ({first_file})"], "one changed hash is reported, by name")
    return out


def real_analyzer(lab: Lab, ref: Reference) -> Outcome:
    out = Outcome(
        "real_analyzer_kill_and_restart",
        ["real subprocess kill and restart", "interruption after step commit",
         "nondeterministic timestamps accounted for"],
        "With the real flashmap CLI: prepare from nothing as a reference; then prepare from nothing "
        "again at the same path and SIGKILL the group as soon as the WCAG analysis commits; restart.",
        "Nothing is ready while the run is dead; the restart is ready with the same verification "
        "outcome, and everything equals the reference once maps are compared without created_utc "
        "and the signature over it.")
    env = lab.env(real_analyzer=True)
    lab.reset(from_reference=False)
    reference_run = lab.run(lab.prepare_command(), env=env)
    reference = lab.identity(reference_run.receipt, real_analyzer=True)
    lab.reset(from_reference=False)
    kill = lab.kill_at(lab.start(lab.prepare_command(), env=env), lambda: "analyze:wcag" in lab.ledger())
    at_kill = lab.ledger()
    observed = {"kill": kill, "committed_at_kill": sorted(at_kill), "receipt_status_at_kill": lab.receipt_status(),
                "listed_at_kill": lab.listed()}
    run = lab.run(lab.prepare_command(), env=env)
    diff = differences(reference, lab.identity(run.receipt, real_analyzer=True))
    note_ready(out.record["id"], run.receipt, reference_run.receipt or {}, real_analyzer=True)
    outcome = ((run.receipt or {}).get("verification") or {}).get("outcome")
    reference_outcome = ((reference_run.receipt or {}).get("verification") or {}).get("outcome")
    out.observe(**observed, reference_status=reference_run.status, restart_status=run.status,
                outcome=outcome, reference_outcome=reference_outcome,
                steps_run_again=reran(at_kill, lab.ledger()), identity_differences=diff,
                reference_seconds=reference_run.seconds)
    out.expect(reference_run.status == "ready", "the real reference is ready")
    out.expect(kill["every_process_in_the_group_ended"], "every process of the killed run ended")
    out.expect(observed["receipt_status_at_kill"] != "ready" and not observed["listed_at_kill"],
               "nothing is ready or listed while the run is dead")
    out.expect(run.status == "ready" and outcome == reference_outcome,
               "the restart is ready with the reference's verification outcome")
    out.expect(not diff, "the identity equals the reference after normalizing map timestamps")
    return out


def closing_check() -> Outcome:
    out = Outcome(
        "ready_receipts_name_only_reference_bytes",
        ["corruption never yields a ready receipt"],
        "Collect every ready receipt seen in every scenario above and compare the artifact hashes "
        "it names with the uninterrupted run it should equal.",
        "Every ready receipt names exactly the reference's artifact hashes.")
    mismatched = []
    for scenario, receipt, expected in READY_SEEN:
        if artifact_hashes(receipt) != artifact_hashes(expected):
            mismatched.append(scenario)
    out.observe(ready_receipts_seen=len(READY_SEEN), naming_other_bytes=sorted(set(mismatched)))
    out.expect(READY_SEEN != [], "ready receipts were seen")
    out.expect(not mismatched, "no ready receipt named bytes other than the reference's")
    return out


SCENARIOS: list[Callable[[Lab, Reference], Outcome]] = [
    no_op_restart, sigkill_after_commit, sigkill_mid_rewrite, sigkill_during_verify, sigkill_sweep,
    truncated_ledger, malformed_ledgers, missing_output, same_size_corruption, changed_signing_key,
    changed_guard_band, duplicate_invocation, failed_verification, negative_controls, real_analyzer,
]
SLOW = {"sigkill_sweep", "real_analyzer"}


# ------------------------------------------------------------------- guard mutations

RECOVERY_TESTS = ("pipeline/tests/test_preparation_recovery.py",)


def recovery_mutations() -> list:
    from eval import mutate_gate as gate

    def mutation(mid: str, path: str, old: str, new: str, why: str) -> Any:
        return gate.Mutation(mid=mid, prop="preparation recovers and never reuses damaged cached work",
                             lane="py", path=path, old=old, new=new, tests=RECOVERY_TESTS, why=why)

    return [
        mutation("ledger-reuse-checks-recorded-output-bytes", "pipeline/state.py",
                 "            if actual != record.output_sha256.get(relative):", "            if False:",
                 "a cached step is reused whatever its outputs now contain"),
        mutation("step-record-withdrawn-before-work", "pipeline/ingest.py",
                 "        self.ledger.withdraw(name)\n        extra = work() or {}", "        extra = work() or {}",
                 "a killed rebuild leaves its old record vouching for half-written outputs"),
        mutation("dependents-follow-upstream-bytes", "pipeline/ingest.py",
                 "        parents = {dep: self.identities[dep] for dep in depends_on}",
                 "        parents = {dep: self.fingerprints[dep] for dep in depends_on}",
                 "a rebuilt input that comes out different leaves its dependents stale"),
        mutation("maps-follow-the-signing-key", "pipeline/ingest.py",
                 '                "signed": bool(options.key),\n                "signer": signer,\n',
                 '                "signed": bool(options.key),\n',
                 "maps signed with an old key are reused under a new one"),
        mutation("ledger-file-flushed-before-rename", "pipeline/durable.py",
                 "            handle.flush()\n            fsync_fd(handle.fileno())\n", "            handle.flush()\n",
                 "a renamed ledger can be empty after a power loss"),
        mutation("ledger-rename-made-durable", "pipeline/durable.py",
                 "    fsync_directory(directory)\n    return path", "    return path",
                 "the rename of a new ledger may not survive a power loss"),
        mutation("temporary-names-are-unpredictable", "pipeline/durable.py",
                 '        candidate = directory / f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"',
                 '        candidate = directory / f"{path.name}.tmp"',
                 "a planted file at a fixed temporary name stops the ledger being written"),
        mutation("unreadable-ledger-not-trusted", "pipeline/state.py",
                 '        if (not isinstance(data, dict) or not isinstance(data.get("source", {}), dict)\n'
                 '                or not isinstance(data.get("steps", {}), dict)):',
                 "        if not isinstance(data, dict):",
                 "a ledger whose steps are not an object crashes the run"),
        mutation("unreadable-ledger-kept-aside", "pipeline/state.py",
                 "                os.replace(self.path, self.title_dir / MALFORMED_NAME)", "                pass",
                 "an unreadable ledger is overwritten instead of kept for inspection"),
        mutation("step-without-its-output-is-not-committed", "pipeline/state.py",
                 '            except LedgerError as exc:\n                raise LedgerError(f"step {step} cannot be recorded: {exc}") from exc',
                 "            except LedgerError:\n                continue",
                 "a step that did not write its output is committed anyway"),
        mutation("title-withdrawn-before-cached-work-is-trusted", "pipeline/ingest.py",
                 "    withdraw_title(layout.index_path, layout.entry_path, sha)\n", "    pass  # withdrawal removed\n",
                 "a title stays listed while its artifacts are being rebuilt"),
        mutation("verified-bytes-must-hold-still", "pipeline/ingest.py",
                 "    if artifact_bytes() != checked_bytes:\n        # Something wrote",
                 "    if False:\n        # Something wrote",
                 "bytes that changed during verification are published"),
        mutation("published-bytes-flushed-first", "pipeline/ingest.py",
                 "        sync_files([layout.root / name for name in checked_bytes])", "        pass",
                 "a verified verdict can reach the disk before the bytes it vouches for"),
        mutation("receipt-names-only-verified-bytes", "pipeline/local_library.py",
                 "            if checked.get(str((layout.workdir / name).relative_to(layout.root))) != digest:",
                 "            if False:",
                 "a receipt names bytes that changed after verification"),
        mutation("one-preparation-per-title", "pipeline/ingest.py",
                 '    with exclusive_lock(layout.ingest_lock_path, what=f"preparation of title {sha[:12]}"):',
                 '    with exclusive_lock(layout.root / f".lock-{time.time_ns()}", what="unshared"):',
                 "two preparations of one title run at once"),
        mutation("hls-files-are-recorded-outputs", "pipeline/ingest.py",
                 "            rendition_outputs.extend(  # noqa: B023 - steps.run calls it before the loop moves on\n"
                 "                sorted(path for path in layout.hls_dir(preset).iterdir() if path.is_file())\n"
                 "            )",
                 "            rendition_outputs.extend([])",
                 "a damaged HLS segment is not traced to the rendition step"),
        mutation("relative-workdir-anchored", "pipeline/ingest.py",
                 "    layout = TitleLayout(Path(workdir).absolute(), sha)", "    layout = TitleLayout(Path(workdir), sha)",
                 "a relative work directory can never reuse finished work"),
        mutation("analysis-map-kept-apart", "pipeline/layout.py",
                 '        return self.root / "work" / "analysis" / f"{preset}.json"',
                 '        return self.root / "maps" / f"{preset}.json"',
                 "the published map overwrites the analysis it was made from"),
        mutation("failed-verdict-never-reused", "pipeline/ingest.py",
                 '        and previous.extra.get("passed") is True\n', '        and True\n',
                 "a failed verification is reused instead of run again"),
        mutation("lock-refuses-links", "pipeline/durable.py",
                 "        fd = os.open(path, os.O_CREAT | os.O_RDWR | _NOFOLLOW | _CLOEXEC, 0o600)",
                 "        fd = os.open(path, os.O_CREAT | os.O_RDWR | _CLOEXEC, 0o600)",
                 "a link planted where a lock file belongs is followed"),
        mutation("index-update-holds-the-index-lock", "pipeline/catalog.py",
                 "    with _index_lock(index_path):\n        index = _read_index(index_path)\n        index.setdefault",
                 '    with _index_lock(index_path.with_name("unshared.json")):\n'
                 "        index = _read_index(index_path)\n        index.setdefault",
                 "two writers of the kid mode index can write back each other's stale entries"),
        mutation("withdrawal-reaches-the-index", "pipeline/catalog.py",
                 "    if index_path.exists():\n        with _index_lock(index_path):",
                 "    if False:\n        with _index_lock(index_path):",
                 "a withdrawn title stays listed in the kid mode index"),
        mutation("scene-holds-bound-to-publication", "pipeline/ingest.py",
                 '                *layout.scene_manifest(preset).parent.glob("*"),\n',
                 "                *(),  # scene-hold images left out of the checked bytes\n",
                 "a scene-hold image that changes after verification is published"),
        mutation("oversized-timestamp-drops-only-its-record", "pipeline/state.py",
                 "    try:\n        if not math.isfinite(completed):\n"
                 '            raise ValueError("completed_at is not a finite number")\n'
                 "    except OverflowError as exc:\n"
                 '        raise ValueError("completed_at is outside the supported numeric range") from exc\n',
                 "    if not math.isfinite(completed):  # an oversized integer is not caught\n"
                 '        raise ValueError("completed_at is not a finite number")\n',
                 "a ledger record with an integer timestamp too large for a float crashes the run"),
    ]


def run_mutations() -> dict:
    from eval import mutate_gate as gate

    mutations = recovery_mutations()
    gate.prepare({"py"})
    controls, green = gate.negative_control(mutations)
    records = [gate.apply_and_run(mutation) for mutation in mutations] if green else []
    for record in records:
        print(f"  {'killed  ' if record['killed'] else 'SURVIVED'} {record['id']}", file=sys.stderr)
    killed = sum(1 for record in records if record["killed"])
    return {"harness": "eval/mutate_gate.py (copy, canary, whole test files, named failing test)",
            "negative_control": {"all_green": green, "selections": controls},
            "totals": {"mutations": len(mutations), "killed": killed, "survived": len(records) - killed},
            "mutations": records}


# --------------------------------------------------------------------------- main

LIMITATIONS = [
    "No power was cut. Durability rests on fsync, and on macOS F_FULLFSYNC, as the operating system and "
    "filesystem implement them; these runs used one machine and one filesystem.",
    "Every scenario but the last uses the fake analyzer, whose flagged spans are scripted. Hashing, source "
    "binding, Ed25519 signing, rendering, HLS packaging and the verification gates are real, so outcomes show "
    "the pipeline's recovery and publication gates, not flash measurement.",
    "Sweep kills are timed, so where each one lands varies between runs; each landing point is recorded.",
    "A SIGKILL sent only to the Python process, not its group, can leave an ffmpeg or analyzer child writing "
    "until it finishes. Such late writes can only cause a mismatch and a rebuild: verification refuses bytes "
    "that change under it and a receipt must name exactly the bytes verification recorded. That case is "
    "covered by the in-process tests, not by a scenario here.",
    "Locks are advisory flock locks on one machine. Work directories shared between machines, for example "
    "over NFS, are not serialized.",
    "Comparisons assume ffmpeg and x264 produce the same bytes for the same input on one machine, which these "
    "runs observed; a different build or thread count can change encoded bytes between runs.",
    "Work directories prepared before this change carry no output hashes, so their first run redoes every step. "
    "With the real analyzer that issues new maps with a new created_utc and signature.",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="where the evidence JSON is written")
    parser.add_argument("--code-root", default=str(HARNESS_ROOT),
                        help="the checkout whose pipeline is run (default: this one)")
    parser.add_argument("--quick", action="store_true", help="skip the timed sweep and the real analyzer")
    parser.add_argument("--only", action="append", default=[], help="run only these scenario functions")
    parser.add_argument("--mutations", action="store_true", help="also break each recovery guard and run its tests")
    parser.add_argument("--keep", action="store_true", help="keep the temporary directory for inspection")
    args = parser.parse_args(argv)
    code_root = Path(args.code_root).resolve()
    if not (code_root / "pipeline" / "local_library.py").is_file():
        print(f"{code_root} is not a Calm Frames checkout", file=sys.stderr)
        return 2
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg and ffprobe are needed", file=sys.stderr)
        return 2

    started, clock = now_utc(), time.monotonic()
    base = Path(tempfile.mkdtemp(prefix="calm-recovery-")).resolve()
    scenarios: list[dict] = []
    reference_record: dict = {}
    try:
        lab = Lab(code_root, base)
        print("reference: an uninterrupted preparation", file=sys.stderr)
        first = lab.run(lab.prepare_command())
        if first.status != "ready":
            raise SystemExit(f"the uninterrupted reference is not ready: {lab.scrub(first.stdout + first.stderr)[-1500:]}")
        ref = Reference(lab.identity(first.receipt), first.seconds, first.receipt or {})
        shutil.copytree(lab.live, lab.reference_copy, symlinks=True)
        reference_record = {"status": first.status, "seconds": first.seconds,
                            "steps": sorted(ref.identity["ledger"]),
                            "files_compared": len(ref.identity["files"]),
                            "verification_outcome": (first.receipt or {}).get("verification", {}).get("outcome")}
        for scenario in SCENARIOS:
            if args.only and scenario.__name__ not in args.only:
                continue
            if args.quick and scenario.__name__ in SLOW:
                continue
            print(f"scenario: {scenario.__name__}", file=sys.stderr)
            lab.write_plan()
            began = time.monotonic()
            try:
                record = scenario(lab, ref).done()
            except (ScenarioError, subprocess.TimeoutExpired, OSError, ValueError, KeyError, StopIteration) as exc:
                record = Outcome(scenario.__name__, [], "", "").done()
                where = traceback.extract_tb(exc.__traceback__)[-1]
                record.update(result="fail", unmet=[f"the harness could not complete it: {type(exc).__name__}: "
                                                    f"{lab.scrub(str(exc))[:600]} (at {Path(where.filename).name}:"
                                                    f"{where.lineno} in {where.name})"])
            record["seconds"] = round(time.monotonic() - began, 1)
            print(f"  {record['result']}: {'; '.join(record['unmet'])}" if record["unmet"] else "  pass",
                  file=sys.stderr)
            scenarios.append(record)
        if not args.only and not args.quick:
            scenarios.append(closing_check().done())
    finally:
        if not args.keep:
            shutil.rmtree(base, ignore_errors=True)
        else:
            print(f"kept {base}", file=sys.stderr)

    mutations = run_mutations() if args.mutations else None
    passed = sum(1 for record in scenarios if record["result"] == "pass")
    # Absolute paths name this machine and its user, so the evidence shows a placeholder.
    shown = ["<checkout of the tested commit>" if os.path.isabs(arg) and Path(arg).resolve() == code_root
             else "<path>" if os.path.isabs(arg) else arg
             for arg in (argv if argv is not None else sys.argv[1:])]
    evidence = {
        "tool": "eval/preparation_recovery.py",
        "command": " ".join(["python -m eval.preparation_recovery", *shown]),
        "tested_commit": git(code_root, "rev-parse", "HEAD"),
        "tested_tree_has_uncommitted_changes": bool(git(code_root, "status", "--porcelain", "--untracked-files=no")),
        "harness_commit": git(HARNESS_ROOT, "rev-parse", "HEAD"),
        "started_utc": started,
        "finished_utc": now_utc(),
        "seconds": round(time.monotonic() - clock, 1),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "ffmpeg": (subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
                       .splitlines() or [""])[0],
        },
        "fixture": {
            "clip": "generated calm gradient with a sine tone (pipeline/tests/clips.py), never played",
            **CLIP,
            "analyzer_flagged_spans_ms": FLAGGED,
            "presets": list(PRESETS),
            "keys": "two Ed25519 pairs generated for this run and deleted with its directory",
        },
        "comparison": {
            "compared": ["ledger step fingerprints and output SHA-256", "SHA-256 of every file in the title",
                         "verify report", "receipt"],
            "left_out_as_run_times": ["ledger completed_at and the source's ingested_at",
                                      "verify report started_at and finished_at",
                                      "receipt checked_inputs_sha256 and report_sha256, which cover those files",
                                      "lock files and temporary files"],
            "real_analyzer_only": "maps are compared without created_utc and the signature value and payload hash "
                                  "computed over it, and step fingerprints, which chain those maps, are not compared",
        },
        "reference": reference_record,
        "scenarios": scenarios,
        "summary": {"scenarios": len(scenarios), "passed": passed, "failed": len(scenarios) - passed},
        "limitations": LIMITATIONS,
    }
    if mutations is not None:
        evidence["guard_mutations"] = mutations
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"{passed} of {len(scenarios)} scenarios met their expectation; evidence in {out}", file=sys.stderr)
    failed_mutations = mutations is not None and mutations["totals"]["survived"] > 0
    return 0 if passed == len(scenarios) and not failed_mutations else 1


if __name__ == "__main__":
    raise SystemExit(main())
