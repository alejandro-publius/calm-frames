"""The catalog entry, and the index kid mode reads.

A title becomes visible in kid mode only when its entry says ``verified`` is
true, and only verify writes that. Anything else, including a run that skipped
verify, leaves the entry at ``pending`` or ``failed``, so a title that was
never checked can never appear.

The index is a JSON file in the work directory. On AWS it is either this same
file in the private bucket or a DynamoDB table with the same fields.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CATALOG_NAME = "catalog.json"

STATUS_PENDING = "pending"
STATUS_VERIFIED = "verified"
STATUS_FAILED = "failed"


@dataclass
class RenditionEntry:
    preset: str
    master_playlist: str
    safe_master: str
    map_path: str
    plan_path: str
    bif_path: str
    bif_manifest: str
    posters: list[str] = field(default_factory=list)
    covered_ms: float = 0.0
    segment_count: int = 0


@dataclass
class CatalogEntry:
    sha256: str
    title: str
    source_name: str
    duration_s: float
    width: int
    height: int
    status: str = STATUS_PENDING
    verified: bool = False
    verify_report: str | None = None
    renditions: dict[str, RenditionEntry] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)

    @property
    def kid_mode_visible(self) -> bool:
        return self.verified and self.status == STATUS_VERIFIED

    def to_dict(self) -> dict:
        data = asdict(self)
        data["kid_mode_visible"] = self.kid_mode_visible
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "CatalogEntry":
        data = dict(data)
        data.pop("kid_mode_visible", None)
        data["renditions"] = {
            preset: RenditionEntry(**value)
            for preset, value in (data.get("renditions") or {}).items()
        }
        return cls(**data)


def write_entry(path: str | Path, entry: CatalogEntry) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entry.to_dict(), indent=2, sort_keys=True))
    os.replace(tmp, path)
    return path


def read_entry(path: str | Path) -> CatalogEntry:
    return CatalogEntry.from_dict(json.loads(Path(path).read_text()))


def update_index(index_path: str | Path, entry: CatalogEntry) -> Path:
    """Put this title into the index, replacing any older entry for the hash."""
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index: dict[str, Any] = {"titles": {}}
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text())
        except json.JSONDecodeError:
            index = {"titles": {}}
    index.setdefault("titles", {})[entry.sha256] = entry.to_dict()
    tmp = index_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, indent=2, sort_keys=True))
    os.replace(tmp, index_path)
    return index_path


def kid_mode_titles(index_path: str | Path) -> list[dict]:
    index_path = Path(index_path)
    if not index_path.exists():
        return []
    index = json.loads(index_path.read_text())
    return [
        entry
        for entry in index.get("titles", {}).values()
        if entry.get("verified") and entry.get("status") == STATUS_VERIFIED
    ]
