"""Guard: the conformance ground truth and the inspection plots must not import flashmap.

The generated clips are only worth measuring because their true answer is computed from the
spec text and from what the generator drew, by code that shares nothing with the analyser under
test. If truth.py ever imported flashmap, the suite would be marking its own homework and every
number it produced would be worthless.

Two checks, because either alone can be fooled:

1. the syntax tree of each ground truth module, so a comment about flashmap is fine and an
   import is not, however it is spelled;
2. an actual import in a fresh interpreter, which catches a module that reaches flashmap
   through something else it imports.

The same two checks cover eval/plots.py and eval/labeling/plots.py, which are how a person looks
at a hazard clip without playing it, for the same reason: an inspection tool that shared code
with the analyser would stop being an independent look at the file.

To confirm the guard is live, add `import flashmap` to eval/conformance/truth.py and watch both
go red. Verified Sep 17, 2026: they do. Repeated against eval/labeling/plots.py the same day,
once that file was added to the list, because until then nothing checked it: the runtime check
imported only the conformance modules, so an import reached through labelling code would have
gone unseen.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parents[1]
GROUND_TRUTH_MODULES = [
    EVAL_DIR / "conformance" / "truth.py",
    EVAL_DIR / "conformance" / "spec.py",
    EVAL_DIR / "conformance" / "geometry.py",
    EVAL_DIR / "plots.py",
    # The labelling figures are the only thing two people will ever see of a hazard clip, and
    # they are the evidence the detector is scored against. If this module reached flashmap, the
    # labels would be agreeing with the analyser rather than with the spec.
    EVAL_DIR / "labeling" / "plots.py",
]
FORBIDDEN_ROOT = "flashmap"


def _flashmap_imports(source: str) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == FORBIDDEN_ROOT:
                    found.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == FORBIDDEN_ROOT:
                found.append(f"line {node.lineno}: from {node.module} import ...")
    return found


@pytest.mark.parametrize("path", GROUND_TRUTH_MODULES, ids=lambda p: p.name)
def test_no_flashmap_import_in_the_source(path: Path):
    assert path.exists(), f"{path} is missing"
    offenders = _flashmap_imports(path.read_text())
    assert not offenders, f"{path.name} imports flashmap: {offenders}"


def test_importing_the_ground_truth_does_not_pull_flashmap_in():
    program = (
        "import sys; sys.path.insert(0, %r);"
        "import conformance.truth, conformance.spec, conformance.geometry;"
        "import labeling.plots;"
        "print(any(name == 'flashmap' or name.startswith('flashmap.') for name in sys.modules))"
        % str(EVAL_DIR)
    )
    out = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, timeout=120
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False", "importing the ground truth reached flashmap"
