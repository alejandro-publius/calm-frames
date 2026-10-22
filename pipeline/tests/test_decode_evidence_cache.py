"""Old analysis must not bypass the complete-decode evidence check."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.ingest import IngestOptions, _Steps, ingest_title

from .conftest import needs_ffmpeg


@needs_ffmpeg
def test_legacy_analysis_is_rechecked_once_before_planning(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[2] / "flashmap/tests/fixtures/calm_sweep.mp4"
    calls = []

    class Analyzer:
        def analyze(self, source, **kwargs):
            calls.append(source)
            path = kwargs["out_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}")
            return SimpleNamespace(violation_count=0, is_signed=False)

    class StopBeforePlan(Exception):
        pass

    original_run = _Steps.run
    legacy = True

    def run_until_plan(self, name, payload, outputs, work, **kwargs):
        if name.startswith("plan:"):
            raise StopBeforePlan
        if legacy and name.startswith("analyze:"):
            payload = {k: v for k, v in payload.items() if k != "decode_evidence_revision"}
        return original_run(self, name, payload, outputs, work, **kwargs)

    monkeypatch.setattr(_Steps, "run", run_until_plan)
    options = IngestOptions(presets=["wcag"])

    def prepare():
        with pytest.raises(StopBeforePlan):
            ingest_title(source, tmp_path, options, adapter=Analyzer())

    prepare()  # Seed an authentic legacy ledger, without rendering or signing.
    assert len(calls) == 1
    legacy = False
    prepare()
    assert len(calls) == 2  # The old map cannot skip the stricter analyzer.
    prepare()
    assert len(calls) == 2  # Current evidence remains resumable.
