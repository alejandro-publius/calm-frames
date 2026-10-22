"""The catalog entry, and the index kid mode reads.

A title becomes visible in kid mode only when its entry says ``verified`` is
true, and only verify writes that. Anything else, including a run that skipped
verify, leaves the entry at ``pending`` or ``failed``, so a title that was
never checked can never appear.

The index is a JSON file in the work directory. On AWS it is either this same
file in the private bucket or a DynamoDB table with the same fields.

Both files are replaced atomically and flushed (``durable``). The index is the
publication point: a re-ingest withdraws a title from the index before anything
else, and verify publishes it there last. Updates to the shared index hold a
short lock, so two titles prepared side by side cannot write back each other's
stale entries.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .durable import atomic_write_text, exclusive_lock

CATALOG_NAME = "catalog.json"
# How long an index update waits for another process's update to finish. Each one
# holds the lock for a single read and write, so this is never reached in practice.
INDEX_LOCK_WAIT_S = 30.0

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
    return atomic_write_text(path, json.dumps(entry.to_dict(), indent=2, sort_keys=True))


def read_entry(path: str | Path) -> CatalogEntry:
    return CatalogEntry.from_dict(json.loads(Path(path).read_text()))


def _index_lock(index_path: Path):
    return exclusive_lock(index_path.with_name(f".{index_path.name}.lock"),
                          what="catalog index", wait_s=INDEX_LOCK_WAIT_S)


def _read_index(index_path: Path) -> dict[str, Any]:
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text())
        except json.JSONDecodeError:
            index = {"titles": {}}
        if isinstance(index, dict) and isinstance(index.get("titles", {}), dict):
            return index
    return {"titles": {}}


def update_index(index_path: str | Path, entry: CatalogEntry) -> Path:
    """Put this title into the index, replacing any older entry for the hash."""
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with _index_lock(index_path):
        index = _read_index(index_path)
        index.setdefault("titles", {})[entry.sha256] = entry.to_dict()
        atomic_write_text(index_path, json.dumps(index, indent=2, sort_keys=True))
    return index_path


def withdraw_title(index_path: str | Path, entry_path: str | Path, sha256: str) -> None:
    """Take a title out of kid mode before anything it was verified with is touched.

    The index is what kid mode reads, so it is withdrawn first and durably, and the
    entry beside the title after it. An entry that cannot be read is left alone: the
    run that called this rebuilds it as pending before anything can verify it.
    """
    index_path = Path(index_path)
    if index_path.exists():
        with _index_lock(index_path):
            index = _read_index(index_path)
            listed = index.get("titles", {}).get(sha256)
            if isinstance(listed, dict) and (listed.get("verified") is not False
                                             or listed.get("status") != STATUS_PENDING):
                index["titles"][sha256] = {**listed, "verified": False, "status": STATUS_PENDING,
                                           "kid_mode_visible": False}
                atomic_write_text(index_path, json.dumps(index, indent=2, sort_keys=True))
    entry_path = Path(entry_path)
    if not entry_path.exists():
        return
    try:
        entry = read_entry(entry_path)
    except (OSError, ValueError, TypeError, KeyError):
        return
    entry.status = STATUS_PENDING
    entry.verified = False
    write_entry(entry_path, entry)


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
