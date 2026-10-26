"""Build digests must not hide a credential elsewhere, even inside the same manifest."""
import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GITLEAKS = shutil.which("gitleaks")


@pytest.mark.skipif(not GITLEAKS, reason="gitleaks is checked by the separate security job")
@pytest.mark.parametrize("field,known_digest,expected", [
    ("app/src/calmframes/PinKeypad.tsx", True, 0),
    ("app/src/calmframes/PinKeypad.tsx", False, 1),
    ("api_key", False, 1),
])
def test_digest_exception_requires_exact_field_and_verified_value(tmp_path, field, known_digest, expected):
    import json

    target = tmp_path / "results/test/app-inputs.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    # Synthetic detector bait only, derived locally and never a real credential.
    value = hashlib.sha256(b"calm-frames generated secret-scan negative fixture").hexdigest()
    if known_digest:
        value = hashlib.sha256((REPO / field).read_bytes()).hexdigest()
    target.write_text(json.dumps({field: value}, indent=2) + "\n")
    result = subprocess.run([GITLEAKS, "dir", str(tmp_path), "--config", str(REPO / ".gitleaks.toml"),
                             "--redact", "--no-banner"], capture_output=True, text=True, check=False)
    assert result.returncode == expected, "unexpected scanner result (values intentionally omitted)"


@pytest.mark.skipif(not GITLEAKS, reason="gitleaks is checked by the separate security job")
@pytest.mark.parametrize("name", ["official-source-access.json", "source-access.json"])
@pytest.mark.parametrize("mutation", ["none", "digest", "field"])
def test_report_digest_allowlist_requires_exact_report_and_bytes(tmp_path, name, mutation):
    import json

    source = REPO / "results/cloud-completion-2026-10-25" / name
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if mutation == "digest":
        digest = hashlib.sha256(b"synthetic secret scanner bait").hexdigest()
    field = "api_key" if mutation == "field" else name
    (tmp_path / "manifest.json").write_text(json.dumps({field: digest}, indent=2) + "\n")
    result = subprocess.run([GITLEAKS, "dir", str(tmp_path), "--config", str(REPO / ".gitleaks.toml"),
                             "--redact", "--no-banner"], capture_output=True, text=True, check=False)
    assert result.returncode == (0 if mutation == "none" else 1), "unexpected scanner result (values omitted)"
