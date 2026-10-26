"""Build-only generators keep their established outputs after leaving assets.

Intercept writes and the encoder so these checks never regenerate shipped media.
"""

from __future__ import annotations

import runpy
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]


def test_logo_generator_keeps_output_paths_and_svg_bytes_from_any_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    writes = {}

    def capture_write(path, text):
        writes[path] = text
        return len(text)

    with patch.object(Path, "write_text", capture_write):
        runpy.run_path(str(REPO / "app/tools/brand/make_logo.py"), run_name="__main__")

    expected = {
        REPO / "app/assets/brand" / name
        for name in (
            "calm-frames-mark-bust.svg",
            "calm-frames-mark-head.svg",
            "calm-frames-tile-1280x720.svg",
        )
    }
    assert set(writes) == expected
    assert all(text == path.read_text() for path, text in writes.items())
    assert not list(tmp_path.iterdir())


def test_selection_sound_keeps_encoder_output_in_runtime_assets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("subprocess.run") as encoder:
        runpy.run_path(str(REPO / "app/tools/sound/generate_menu_select.py"), run_name="__main__")

    encoder.assert_called_once()
    args = encoder.call_args.args[0]
    assert args[0] == "ffmpeg"
    assert args[-1] == str(REPO / "app/assets/raw/sound/menu-select.mp3")
    assert args[args.index("-i") + 1] == "pipe:0"
    assert encoder.call_args.kwargs["check"] is True
    assert encoder.call_args.kwargs["input"]
    assert not list(tmp_path.iterdir())
