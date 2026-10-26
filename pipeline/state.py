"""The ledger that makes a second run cheap and an interrupted run safe to resume.

Every step writes down a fingerprint of its inputs and the SHA-256 of every file it
produced. A step is reused only while the fingerprint still matches and every
recorded output is still a regular file inside the title directory with exactly
the recorded bytes. A missing, truncated or same-size modified output, or one
replaced by a link, makes the step run again. Each fingerprint includes the
identity of every step it depends on, which is that step's fingerprint and output
hashes, so a rebuilt step that comes out different redoes what depends on it.
Change the guard band, the preset list or the pipeline version and the fingerprint
changes, so the work that depended on it is done again and nothing else is.

Output paths are stored relative to the title directory, so the same work
directory can be mounted at a different path in the ingest container.

Crash safety, in the order a step meets it:

1. Before a step does any work its record is withdrawn, durably. A run killed while
   it rewrites an output therefore never leaves a record vouching for half a file.
2. The record is written only after the step returned and every output it names
   exists as a regular file. Writing the record is the commit.
3. The ledger itself is replaced atomically and flushed (``durable``), so it is
   always one complete version or the next.
4. A ledger that cannot be read is never trusted. Readers treat it as empty; the
   next write moves it aside to ``state.json.malformed`` and the title is prepared
   again from its source. One record with the wrong shape is dropped on its own,
   and the step it described simply runs again.

Records written before output hashes were kept are still readable, so receipts
issued from them can be checked, but they are never trusted to skip work.
"""

from __future__ import annotations

import json
import math
import os
import re
import stat
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from . import VERSION, PipelineError
from .durable import atomic_write_bytes, fsync_directory
from .hashing import sha256_regular_file

LEDGER_NAME = "state.json"
# Format 2 records the SHA-256 of every output. A ledger with no format is format 1.
LEDGER_FORMAT = 2
MALFORMED_NAME = "state.json.malformed"
# Far above any ledger this pipeline writes. Anything bigger is not read at all.
MAX_LEDGER_BYTES = 16 * 1024 * 1024
MAX_FINGERPRINT_CHARS = 512
_SHA256 = re.compile(r"[0-9a-f]{64}")


class LedgerError(PipelineError):
    """The ledger, or a file it names, is not something this pipeline may trust."""


def _relative_parts(text: object) -> tuple[str, ...]:
    """A recorded output path: relative, normalised, and never leaving the title."""
    if not isinstance(text, str) or not text or "\x00" in text or "\\" in text:
        raise ValueError("an output path is not a plain relative path")
    pure = PurePosixPath(text)
    if (pure.is_absolute() or str(pure) != text
            or any(part in ("", ".", "..") for part in pure.parts)):
        raise ValueError(f"output path {text[:200]!r} is not a normalised path inside the title")
    return pure.parts


def _checked_record(name: object, value: object, *, legacy: bool) -> dict:
    """The record as stored, or ValueError naming the first thing wrong with it."""
    if not isinstance(name, str) or not name or len(name) > 200:
        raise ValueError("a step name is not a short string")
    if not isinstance(value, dict):
        raise ValueError("the record is not an object")
    if value.get("name") != name:
        raise ValueError("the record names a different step")
    fingerprint = value.get("fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint or len(fingerprint) > MAX_FINGERPRINT_CHARS:
        raise ValueError("the fingerprint is not a short string")
    outputs = value.get("outputs", [])
    if not isinstance(outputs, list):
        raise ValueError("outputs is not a list")
    for output in outputs:
        _relative_parts(output)
    if len(set(outputs)) != len(outputs):
        raise ValueError("an output is listed twice")
    completed = value.get("completed_at", 0.0)
    if isinstance(completed, bool) or not isinstance(completed, (int, float)):
        raise ValueError("completed_at is not a finite number")
    try:
        if not math.isfinite(completed):
            raise ValueError("completed_at is not a finite number")
    except OverflowError as exc:
        raise ValueError("completed_at is outside the supported numeric range") from exc
    extra = value.get("extra", {})
    if not isinstance(extra, dict):
        raise ValueError("extra is not an object")
    digests = value.get("output_sha256")
    if digests is None:
        if not legacy:
            raise ValueError("the record has no output hashes")
    elif (not isinstance(digests, dict) or set(digests) != set(outputs)
          or any(not isinstance(v, str) or not _SHA256.fullmatch(v) for v in digests.values())):
        raise ValueError("the output hashes do not cover exactly the recorded outputs")
    return dict(value)


@dataclass
class StepRecord:
    name: str
    fingerprint: str
    outputs: list[str] = field(default_factory=list)
    completed_at: float = 0.0
    extra: dict = field(default_factory=dict)
    # None for a record written before output hashes were kept.
    output_sha256: dict[str, str] | None = None

    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "fingerprint": self.fingerprint,
            "outputs": self.outputs,
            "completed_at": self.completed_at,
            "extra": self.extra,
        }
        if self.output_sha256 is not None:
            data["output_sha256"] = self.output_sha256
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "StepRecord":
        digests = data.get("output_sha256")
        return cls(
            name=str(data.get("name", "")),
            fingerprint=str(data.get("fingerprint", "")),
            outputs=list(data.get("outputs", [])),
            completed_at=float(data.get("completed_at", 0.0)),
            extra=dict(data.get("extra", {})),
            output_sha256=dict(digests) if isinstance(digests, dict) else None,
        )


@dataclass(frozen=True)
class StepCheck:
    """Whether a recorded step may be reused, and why not when it may not."""

    valid: bool
    reason: str
    output_sha256: dict[str, str] = field(default_factory=dict)


class Ledger:
    def __init__(self, title_dir: str | Path) -> None:
        self.title_dir = Path(title_dir)
        self.path = self.title_dir / LEDGER_NAME
        self.data: dict[str, Any] = self._empty()
        # What loading and saving found and did, for the run's result and evidence.
        self.events: list[dict] = []
        self._malformed: str | None = None
        self.load()

    @staticmethod
    def _empty(source: dict | None = None) -> dict[str, Any]:
        return {
            "ledger_format": LEDGER_FORMAT,
            "pipeline_version": VERSION,
            "source": dict(source or {}),
            "steps": {},
        }

    def _reject(self, reason: str) -> None:
        # Nothing is renamed while reading, so a reader never changes the title.
        self._malformed = reason
        self.data = self._empty()
        self.events.append({"event": "ledger_malformed", "reason": reason})

    def load(self) -> None:
        try:
            info = os.lstat(self.path)
        except FileNotFoundError:
            return
        if not stat.S_ISREG(info.st_mode):
            raise LedgerError("the step ledger is not a regular file, so it was not read")
        if info.st_size > MAX_LEDGER_BYTES:
            self._reject("the ledger is larger than any ledger this pipeline writes")
            return
        try:
            data = json.loads(self.path.read_bytes().decode("utf-8"))
        except (ValueError, RecursionError) as exc:
            # A truncated, torn or overwritten ledger. Redoing work is cheap next to
            # publishing a title whose artifacts do not match its plan.
            self._reject(f"the ledger is not readable JSON ({type(exc).__name__})")
            return
        if (not isinstance(data, dict) or not isinstance(data.get("source", {}), dict)
                or not isinstance(data.get("steps", {}), dict)):
            self._reject("the ledger is not an object with source and steps objects")
            return
        source = data.get("source", {})
        if data.get("pipeline_version") != VERSION:
            self.data = self._empty(source)
            self.events.append({"event": "ledger_outdated", "reason": "written by another pipeline version"})
            return
        form = data.get("ledger_format", 1)
        if isinstance(form, bool) or form not in (1, LEDGER_FORMAT):
            self.data = self._empty(source)
            self.events.append({"event": "ledger_outdated", "reason": "an unknown ledger format"})
            return
        steps: dict[str, dict] = {}
        for name, value in data.get("steps", {}).items():
            try:
                steps[name] = _checked_record(name, value, legacy=form == 1)
            except ValueError as exc:
                self.events.append({"event": "record_dropped", "step": str(name)[:200], "reason": str(exc)})
        if form == 1 and steps:
            self.events.append({"event": "legacy_records",
                                "reason": "written before output hashes were kept; read, never reused"})
        self.data = {"ledger_format": LEDGER_FORMAT, "pipeline_version": VERSION,
                     "source": source, "steps": steps}

    def save(self) -> None:
        self.title_dir.mkdir(parents=True, exist_ok=True)
        if self._malformed is not None:
            # Keep the unreadable ledger for inspection, beside the title, instead of
            # writing over it. An earlier copy of the same name is replaced.
            try:
                info = os.lstat(self.path)
            except FileNotFoundError:
                info = None
            if info is not None:
                if not stat.S_ISREG(info.st_mode):
                    raise LedgerError("the step ledger is not a regular file, so it was not replaced")
                os.replace(self.path, self.title_dir / MALFORMED_NAME)
                fsync_directory(self.title_dir)
                self.events.append({"event": "ledger_moved_aside", "to": MALFORMED_NAME})
            self._malformed = None
        self.data["ledger_format"] = LEDGER_FORMAT
        atomic_write_bytes(self.path, json.dumps(self.data, indent=2, sort_keys=True).encode("utf-8"))

    @property
    def malformed(self) -> str | None:
        """Why the ledger on disk could not be trusted, or None."""
        return self._malformed

    @property
    def steps(self) -> dict[str, StepRecord]:
        return {
            name: StepRecord.from_dict(value)
            for name, value in self.data.get("steps", {}).items()
        }

    def get(self, step: str) -> StepRecord | None:
        raw = self.data.get("steps", {}).get(step)
        return StepRecord.from_dict(raw) if raw else None

    def owned_file(self, relative: str) -> Path:
        """The recorded output as a regular file reached without following a link."""
        try:
            parts = _relative_parts(relative)
        except ValueError as exc:
            raise LedgerError(str(exc)) from exc
        cursor = self.title_dir
        info = None
        for part in parts:
            cursor = cursor / part
            try:
                info = os.lstat(cursor)
            except FileNotFoundError as exc:
                raise LedgerError(f"{relative} is missing") from exc
            if stat.S_ISLNK(info.st_mode):
                raise LedgerError(f"{relative} is reached through a link")
        if info is None or not stat.S_ISREG(info.st_mode):
            raise LedgerError(f"{relative} is not a regular file")
        return cursor

    def relative_output(self, output: str | Path) -> str:
        """An output named by the caller, as the path recorded for it.

        Relative paths are taken as relative to the title directory. An absolute path
        has to be inside it, reached by any spelling of the directory (macOS names the
        same temporary directory /var and /private/var).
        """
        path = Path(output)
        relative = None if path.is_absolute() else path.as_posix()
        if path.is_absolute():
            for candidate, root in (
                (path, self.title_dir.absolute()),
                (path.parent.resolve() / path.name, self.title_dir.resolve()),
            ):
                try:
                    relative = candidate.relative_to(root).as_posix()
                    break
                except ValueError:
                    continue
        try:
            if relative is not None:
                _relative_parts(relative)
                return relative
        except ValueError:
            pass
        raise LedgerError(f"{output} is outside the title directory, so no step may record it")

    def check(self, step: str, fingerprint: str) -> StepCheck:
        """May this step be skipped? Only when every output still has its recorded bytes."""
        record = self.get(step)
        if record is None:
            return StepCheck(False, "no completed record")
        if record.fingerprint != fingerprint:
            return StepCheck(False, "its inputs or an upstream output changed")
        if record.output_sha256 is None:
            return StepCheck(False, "recorded before output hashes were kept")
        digests: dict[str, str] = {}
        for relative in record.outputs:
            try:
                actual = sha256_regular_file(self.owned_file(relative))
            except (LedgerError, OSError) as exc:
                return StepCheck(False, f"output {exc}" if isinstance(exc, LedgerError)
                                 else f"output {relative} cannot be read")
            if actual != record.output_sha256.get(relative):
                return StepCheck(False, f"output {relative} no longer has the recorded bytes")
            digests[relative] = actual
        return StepCheck(True, "every recorded output has its recorded bytes", digests)

    def is_done(self, step: str, fingerprint: str) -> bool:
        return self.check(step, fingerprint).valid

    def record(
        self,
        step: str,
        fingerprint: str,
        outputs: Iterable[str | Path] = (),
        extra: dict | None = None,
    ) -> StepRecord:
        """Commit a finished step. Every output must exist as a regular file in the title."""
        relative: list[str] = []
        for output in outputs:
            name = self.relative_output(output)
            if name not in relative:
                relative.append(name)
        digests: dict[str, str] = {}
        for name in relative:
            try:
                digests[name] = sha256_regular_file(self.owned_file(name))
            except LedgerError as exc:
                raise LedgerError(f"step {step} cannot be recorded: {exc}") from exc
        record = StepRecord(
            name=step,
            fingerprint=fingerprint,
            outputs=relative,
            completed_at=time.time(),
            extra=extra or {},
            output_sha256=digests,
        )
        self.data.setdefault("steps", {})[step] = record.to_dict()
        self.save()
        return record

    def withdraw(self, *steps: str) -> bool:
        """Remove these records durably, before their outputs are touched again."""
        table = self.data.setdefault("steps", {})
        removed = [step for step in steps if table.pop(step, None) is not None]
        if removed or self._malformed is not None:
            self.save()
        return bool(removed)

    def forget(self, step: str) -> None:
        self.data.get("steps", {}).pop(step, None)
        self.save()

    def set_source(self, info: dict) -> None:
        self.data["source"] = info
        self.save()

    @property
    def source(self) -> dict:
        return dict(self.data.get("source", {}))
