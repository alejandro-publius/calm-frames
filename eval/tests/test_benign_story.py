"""The demonstration may add practice hides only to a measured-clean source."""
from types import SimpleNamespace

import pytest

from eval.benign_story import DemonstrationAnalyzer
from pipeline.flashmap_adapter import FlashmapAdapter


@pytest.mark.parametrize("clean,generator", [(False, "flashmap"), (True, "fake")])
def test_refuses_unmeasured_or_flagged_demo_before_signing(tmp_path, monkeypatch, clean, generator):
    source = tmp_path / "source.mp4"
    measured = SimpleNamespace(is_clean=clean, raw={"generator": {"name": generator}})
    monkeypatch.setattr(FlashmapAdapter, "analyze", lambda *_args, **_kwargs: measured)
    adapter = DemonstrationAnalyzer(source, tmp_path / "unused.pem", tmp_path / "evidence")
    with pytest.raises(ValueError, match="must measure clean"):
        adapter.analyze(source, profile="wcag", out_path=tmp_path / "map.json")
    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "map.json").exists()


def test_uses_real_cli_despite_fake_analyzer_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("CALM_FRAMES_FLASHMAP_CMD", "some-fake-analyzer")
    adapter = DemonstrationAnalyzer(tmp_path / "source", tmp_path / "key", tmp_path / "proof")
    assert adapter.command[-2:] == ["-m", "flashmap"]
