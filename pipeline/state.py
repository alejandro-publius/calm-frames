"""The ledger that makes a second run cheap.

Every step writes down a fingerprint of its inputs and the files it produced.
A step is skipped when the fingerprint still matches and every output is still
on disk. Change the guard band, the preset list or the pipeline version and the
fingerprint changes, so the work that depended on it is done again and nothing
else is.

Output paths are stored relative to the title directory, so the same work
directory can be mounted at a different path in the ingest container.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from . import VERSION

LEDGER_NAME = "state.json"


@dataclass
class StepRecord:
    name: str
    fingerprint: str
    outputs: list[str] = field(default_factory=list)
    completed_at: float = 0.0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "fingerprint": self.fingerprint,
            "outputs": self.outputs,
            "completed_at": self.completed_at,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StepRecord":
        return cls(
            name=str(data.get("name", "")),
            fingerprint=str(data.get("fingerprint", "")),
            outputs=list(data.get("outputs", [])),
            completed_at=float(data.get("completed_at", 0.0)),
            extra=dict(data.get("extra", {})),
        )


class Ledger:
    def __init__(self, title_dir: str | Path) -> None:
        self.title_dir = Path(title_dir)
        self.path = self.title_dir / LEDGER_NAME
        self.data: dict[str, Any] = {
            "pipeline_version": VERSION,
            "source": {},
            "steps": {},
        }
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            # A half written ledger means the last run died. Start over rather
            # than trust it: redoing work is cheap next to publishing a title
            # whose artifacts do not match its plan.
            return
        if data.get("pipeline_version") != VERSION:
            self.data["source"] = data.get("source", {})
            return
        self.data = data

    def save(self) -> None:
        self.title_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True))
        os.replace(tmp, self.path)

    @property
    def steps(self) -> dict[str, StepRecord]:
        return {
            name: StepRecord.from_dict(value)
            for name, value in self.data.get("steps", {}).items()
        }

    def get(self, step: str) -> StepRecord | None:
        raw = self.data.get("steps", {}).get(step)
        return StepRecord.from_dict(raw) if raw else None

    def is_done(self, step: str, fingerprint: str) -> bool:
        record = self.get(step)
        if record is None or record.fingerprint != fingerprint:
            return False
        for output in record.outputs:
            if not (self.title_dir / output).exists():
                return False
        return True

    def record(
        self,
        step: str,
        fingerprint: str,
        outputs: Iterable[str | Path] = (),
        extra: dict | None = None,
    ) -> StepRecord:
        relative: list[str] = []
        for output in outputs:
            path = Path(output)
            if path.is_absolute():
                try:
                    path = path.relative_to(self.title_dir)
                except ValueError:
                    pass
            relative.append(str(path))
        record = StepRecord(
            name=step,
            fingerprint=fingerprint,
            outputs=relative,
            completed_at=time.time(),
            extra=extra or {},
        )
        self.data.setdefault("steps", {})[step] = record.to_dict()
        self.save()
        return record

    def forget(self, step: str) -> None:
        self.data.get("steps", {}).pop(step, None)
        self.save()

    def set_source(self, info: dict) -> None:
        self.data["source"] = info
        self.save()

    @property
    def source(self) -> dict:
        return dict(self.data.get("source", {}))
