#!/usr/bin/env python3
"""Guard: eval/plots.py must stay independent of flashmap.

plots.py is how a human inspects a hazard clip without playing it. If it ever
imported flashmap, then a bug in flashmap could quietly change what that human
sees, and the plots would stop being an independent check. This test reads the
file's syntax tree rather than its text, so a comment mentioning flashmap is
fine and a real import is not, however it is spelled.

Run:
    .venv/bin/python eval/test_plots_standalone.py
    .venv/bin/python -m pytest eval/test_plots_standalone.py

To confirm the guard is live, add `import flashmap` to plots.py and watch this
go red. Verified Sep 17, 2026: it does.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

PLOTS = Path(__file__).resolve().parent / "plots.py"
FORBIDDEN_ROOT = "flashmap"


def _forbidden_imports(source: str) -> list[str]:
    """Every import in `source` whose top-level package is flashmap."""
    found: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == FORBIDDEN_ROOT:
                    found.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            # `from . import x` has module None; only absolute names can be flashmap.
            if node.module and node.module.split(".")[0] == FORBIDDEN_ROOT:
                found.append(f"line {node.lineno}: from {node.module} import ...")
        elif isinstance(node, ast.Call):
            # importlib.import_module("flashmap") and __import__("flashmap")
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in ("import_module", "__import__") and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.split(".")[0] == FORBIDDEN_ROOT:
                        found.append(f"line {node.lineno}: dynamic import of {arg.value}")
    return found


def test_plots_does_not_import_flashmap() -> None:
    assert PLOTS.is_file(), f"missing {PLOTS}"
    hits = _forbidden_imports(PLOTS.read_text())
    assert not hits, (
        "eval/plots.py must not import flashmap, so hazard inspection stays "
        "independent of the analyzer. Found:\n  " + "\n  ".join(hits)
    )


def test_guard_catches_a_real_import() -> None:
    """The guard itself, checked against source that does import flashmap.

    Without this, a guard that always returned [] would look green forever.
    """
    for bad in (
        "import flashmap\n",
        "import flashmap.analyze as a\n",
        "from flashmap.thresholds import WCAG\n",
        "import importlib\nm = importlib.import_module('flashmap')\n",
        "m = __import__('flashmap')\n",
    ):
        assert _forbidden_imports(bad), f"guard missed: {bad!r}"
    for ok in (
        "# flashmap is deliberately not imported here\n",
        "flashmap = 'a local name, not an import'\n",
        "import matplotlib\n",
    ):
        assert not _forbidden_imports(ok), f"guard false-positived on: {ok!r}"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
