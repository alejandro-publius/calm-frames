"""Shared fixtures.

SAFETY. `hazard_clip` is the only way the suite makes a flashing file. It writes into pytest's
temporary directory, hands back the path, and deletes the file when the test ends, pass or fail.
Nothing in this suite opens a generated clip in a player, and nothing writes one into the
repository.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

sys.path.insert(0, str(Path(__file__).parent))

import clipgen  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def hazard_clip(tmp_path: Path) -> Callable[..., Path]:
    """Make a flashing clip that is deleted as soon as the test finishes."""
    made: list[Path] = []

    def make(name: str, frames: Sequence[NDArray[np.uint8]], **kwargs: object) -> Path:
        path = tmp_path / f"HAZARD_{name}"
        clipgen.write_clip(path, frames, **kwargs)  # type: ignore[arg-type]
        made.append(path)
        return path

    try:
        yield make
    finally:
        for path in made:
            path.unlink(missing_ok=True)


@pytest.fixture
def calm_clip(tmp_path: Path) -> Callable[..., Path]:
    """Make a clip that does not flash. Still temporary, still cleaned up."""
    made: list[Path] = []

    def make(name: str, frames: Sequence[NDArray[np.uint8]], **kwargs: object) -> Path:
        path = tmp_path / name
        clipgen.write_clip(path, frames, **kwargs)  # type: ignore[arg-type]
        made.append(path)
        return path

    try:
        yield make
    finally:
        for path in made:
            path.unlink(missing_ok=True)
