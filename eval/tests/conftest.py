"""Put `eval/` on the import path so these tests can import metrics and conformance.*.

`eval/` is not an installed package. It is a directory of scripts that the repository runs in
place, so the tests reach their modules the same way the scripts do.
"""

from __future__ import annotations

import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))
