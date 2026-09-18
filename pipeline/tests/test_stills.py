"""Taking one frame out of a file, including the files that make that hard.

A container can run on past its last coded frame. Ogg Theora does it as a matter of course: a
frame identical to the one before it is written as an empty packet, so a file whose tail is
all repeats has a last decodable frame well before the end of its duration. Seeking into that
tail gives nothing back, and the still, poster and trickplay steps all seek. That stopped four
clips in the pool from being ingested at all once their Theora decode was fixed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline import PipelineError, ffmpegtool
from pipeline.flashmap_adapter import tail_to_hold_ms
from pipeline.probe import probe_video
from pipeline.render import (
    extract_jpeg,
    extract_still,
    make_neutral_still,
    render_safe_master,
    still_is_flat,
)

from .clips import make_calm_clip
from .conftest import needs_ffmpeg

pytestmark = needs_ffmpeg

THEORA_CLIP = Path(__file__).parent / "fixtures" / "calm_sweep_theora.ogv"

# The clip runs to 2.4 s. Its last decodable frame is at 1.9 s, because everything from 2.0 s
# on is an empty packet repeating it.
DURATION_S = 2.4
LAST_FRAME_S = 1.9


def _duration_s(path: Path) -> float:
    return float(
        ffmpegtool.run_ffprobe(
            ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]
        ).stdout.strip()
    )


def test_the_fixture_really_outlives_its_last_frame():
    """Without that gap this clip proves nothing, so the suite checks it is still there."""
    assert _duration_s(THEORA_CLIP) == pytest.approx(DURATION_S, abs=0.05)
    frames = ffmpegtool.run_ffprobe(
        [
            "-v", "error", "-select_streams", "v:0",
            "-show_entries", "frame=pts_time", "-of", "csv=p=0", str(THEORA_CLIP),
        ]
    ).stdout.split()
    assert float(frames[-1]) == pytest.approx(LAST_FRAME_S, abs=0.05)


def test_a_still_past_the_last_frame_falls_back_to_the_last_frame(tmp_path):
    out = tmp_path / "still.png"
    extract_still(THEORA_CLIP, time_s=2.0, out_path=out, width=64, height=48)
    assert out.exists() and out.stat().st_size > 0


def test_a_poster_past_the_last_frame_falls_back_to_the_last_frame(tmp_path):
    out = tmp_path / "poster.jpg"
    extract_jpeg(THEORA_CLIP, time_s=2.0, out_path=out, width=64, height=48)
    assert out.exists() and out.stat().st_size > 0


def test_a_still_inside_the_frames_is_still_taken_normally(tmp_path):
    out = tmp_path / "early.png"
    result = extract_still(THEORA_CLIP, time_s=0.3, out_path=out, width=64, height=48)
    assert out.exists()
    # The ordinary path seeks before the input. The fallback does not.
    assert "-ss" in result.cmd


class TestTheNeutralCoverCard:
    """The card a title gets when it flashes end to end and has no frame that may be shown.

    "Neutral" has to be something verify measures, not something the pipeline claims, because
    on a title like that every frame of the film is flagged.
    """

    def test_the_card_is_one_flat_colour(self, tmp_path):
        out = tmp_path / "card.png"
        make_neutral_still(out, width=64, height=48)
        flat, detail = still_is_flat(out)
        assert flat, detail
        assert detail["spreads"] == {"Y": 0.0, "U": 0.0, "V": 0.0}

    def test_a_frame_of_a_film_is_not_one_flat_colour(self, tmp_path):
        """What the check is really asking is whether the cover shows any picture at all.

        The Theora fixture is no use here: every one of its frames is a single colour by
        construction, which is the same answer a card gives and the right answer for it.
        """
        clip = make_calm_clip(tmp_path / "clip.mp4", seconds=2.0)
        out = tmp_path / "frame.png"
        extract_still(clip, time_s=1.0, out_path=out, width=64, height=48)
        flat, detail = still_is_flat(out)
        assert not flat, detail

    def test_statistics_that_did_not_come_back_are_not_proof_of_anything(
        self, tmp_path, monkeypatch
    ):
        """Fail closed. An absent number must never read as zero spread.

        Treating a missing statistic as zero would make every gap in ffmpeg's output look
        like proof that the picture is flat, which is the one thing this check exists to
        establish.
        """
        card = tmp_path / "card.png"
        make_neutral_still(card, width=64, height=48)

        def half_an_answer(args, **kwargs):
            return ffmpegtool.ToolResult(
                cmd=["ffmpeg"], returncode=0, stdout="",
                stderr="lavfi.signalstats.YMIN=50\nlavfi.signalstats.YMAX=50\n",
            )

        monkeypatch.setattr("pipeline.render.ffmpegtool.run_ffmpeg", half_an_answer)
        with pytest.raises(PipelineError) as caught:
            still_is_flat(card)
        assert "UMIN" in str(caught.value)


class TestHoldingTheLastPicture:
    """A rendition of a file that ends on repeated frames has to end where the title does.

    ffmpeg drops the empty packets that carry those repeats, so without the hold the
    rendition is short by the length of the run, and verify refuses it for not having the
    source's frame timing.
    """

    def _map(self, tmp_path, **source):
        base = {
            "sha256": "ab" * 32,
            "last_pts_ms": 2300.0,
            "last_coded_pts_ms": 1900.0,
        }
        base.update(source)
        path = tmp_path / "map.json"
        path.write_text(json.dumps({"version": 1, "source": base, "segments": []}))
        return path

    def test_the_gap_is_the_run_of_repeats_at_the_end(self, tmp_path):
        assert tail_to_hold_ms(self._map(tmp_path)) == pytest.approx(400.0)

    def test_a_file_that_ends_on_a_picture_is_not_padded(self, tmp_path):
        assert tail_to_hold_ms(self._map(tmp_path, last_coded_pts_ms=2300.0)) == 0.0

    def test_a_map_that_does_not_say_is_not_padded(self, tmp_path):
        """Nothing is padded on a guess."""
        assert tail_to_hold_ms(self._map(tmp_path, last_coded_pts_ms=None)) == 0.0
        assert tail_to_hold_ms(tmp_path / "missing.json") == 0.0

    def test_the_rendition_of_a_clip_that_ends_on_repeats_keeps_its_length(self, tmp_path):
        still = tmp_path / "still.png"
        make_neutral_still(still, width=64, height=48)
        probe = probe_video(THEORA_CLIP)
        out = tmp_path / "safe.mp4"
        render_safe_master(
            THEORA_CLIP,
            intervals=[],
            still_path=still,
            out_path=out,
            probe=probe,
            x264_preset="ultrafast",
            pad_tail_ms=400.0,
        )
        held = float(
            ffmpegtool.run_ffprobe(
                ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)]
            ).stdout.strip()
        )
        assert held == pytest.approx(DURATION_S, abs=0.1)

    def test_without_the_hold_the_rendition_comes_out_short(self, tmp_path):
        still = tmp_path / "still.png"
        make_neutral_still(still, width=64, height=48)
        out = tmp_path / "short.mp4"
        render_safe_master(
            THEORA_CLIP,
            intervals=[],
            still_path=still,
            out_path=out,
            probe=probe_video(THEORA_CLIP),
            x264_preset="ultrafast",
        )
        short = float(
            ffmpegtool.run_ffprobe(
                ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)]
            ).stdout.strip()
        )
        assert short < DURATION_S - 0.3
