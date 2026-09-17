"""Colour handling on real files: tagged, untagged and full range.

The rules under test are in flashmap/docs/SPEC_SOURCES.md sections 6 and 7:

* a tagged stream is decoded with the tag it carries;
* an untagged stream with a picture at or above 720 lines is decoded as BT.709, below that as
  BT.601, and the sidecar says the matrix was inferred;
* a yuvj pixel format is full range whatever the range tag says.
"""

from __future__ import annotations

import numpy as np
import pytest

import clipgen
from flashmap.decode import ColorPolicy, UnsupportedInput, decide_color, iter_frames, probe

TEAL = (12, 190, 150)
CRIMSON = (192, 32, 64)


def _first_pixel(path, info):
    frame = next(iter(iter_frames(path, info)))
    return (frame.rgb[2, 2] * 255.0).round().astype(int).tolist()


# ---- the decision table, unit level ------------------------------------------------------


def test_tagged_stream_uses_its_own_tag():
    decision = decide_color("yuv420p", 480, clipgen.AVCOL_SPC_BT709, clipgen.AVCOL_RANGE_MPEG, 2)
    assert decision.matrix == "bt709"
    assert decision.matrix_source == "stream-tag"


def test_untagged_hd_is_bt709():
    decision = decide_color("yuv420p", 1080, clipgen.AVCOL_SPC_UNSPECIFIED, 0, 2)
    assert (decision.matrix, decision.matrix_source) == ("bt709", "inferred-hd-bt709")


def test_untagged_720_lines_counts_as_hd():
    decision = decide_color("yuv420p", 720, clipgen.AVCOL_SPC_UNSPECIFIED, 0, 2)
    assert decision.matrix == "bt709"


def test_untagged_sd_is_bt601():
    decision = decide_color("yuv420p", 576, clipgen.AVCOL_SPC_UNSPECIFIED, 0, 2)
    assert (decision.matrix, decision.matrix_source) == ("bt601", "inferred-sd-bt601")


def test_the_hd_cutoff_is_configurable_because_it_is_not_a_spec_number():
    policy = ColorPolicy(hd_min_height=480)
    decision = decide_color("yuv420p", 576, clipgen.AVCOL_SPC_UNSPECIFIED, 0, 2, policy)
    assert decision.matrix == "bt709"


def test_yuvj_is_full_range_even_when_the_range_tag_says_limited():
    decision = decide_color("yuvj420p", 480, clipgen.AVCOL_SPC_BT709, clipgen.AVCOL_RANGE_MPEG, 2)
    assert (decision.color_range, decision.range_source) == ("full", "pixel-format-yuvj")


def test_untagged_range_defaults_to_limited_and_admits_it():
    decision = decide_color("yuv420p", 480, clipgen.AVCOL_SPC_BT709, 0, 2)
    assert (decision.color_range, decision.range_source) == ("limited", "default-limited")


@pytest.mark.parametrize("transfer", [16, 18], ids=["pq", "hlg"])
def test_hdr_is_refused_rather_than_measured_with_the_sdr_curve(transfer):
    with pytest.raises(UnsupportedInput, match="SDR only"):
        decide_color("yuv420p", 1080, clipgen.AVCOL_SPC_BT2020_NCL if False else 9, 1, transfer)


# ---- the same rules on real files ---------------------------------------------------------


def test_tagged_clip_round_trips_its_colour(calm_clip):
    frames = [clipgen.solid(64, 48, CRIMSON)] * 4
    path = calm_clip("tagged.mkv", frames, colorspace=clipgen.AVCOL_SPC_BT709)
    info = probe(path, analysis_width=64)
    assert info.color.matrix_source == "stream-tag"
    assert _first_pixel(path, info) == list(CRIMSON)


def test_untagged_sd_clip_is_read_as_bt601(calm_clip):
    """The file was written with the BT.601 matrix and carries no tag. Reading it as BT.601
    gets the colour back. Reading it as BT.709 would not."""
    frames = [clipgen.solid(64, 48, TEAL)] * 4
    path = calm_clip(
        "untagged_sd.mkv",
        frames,
        colorspace=clipgen.AVCOL_SPC_SMPTE170M,
        tag_colorspace=False,
        tag_range=False,
    )
    info = probe(path, analysis_width=64)
    assert info.color.matrix_source == "inferred-sd-bt601"
    assert info.color.range_source == "default-limited"
    recovered = _first_pixel(path, info)
    assert np.allclose(recovered, TEAL, atol=2), recovered


def test_untagged_hd_clip_is_read_as_bt709(calm_clip):
    frames = [clipgen.solid(128, 720, TEAL)] * 3
    path = calm_clip(
        "untagged_hd.mkv",
        frames,
        colorspace=clipgen.AVCOL_SPC_BT709,
        tag_colorspace=False,
        tag_range=False,
    )
    info = probe(path, analysis_width=128)
    assert info.color.matrix_source == "inferred-hd-bt709"
    recovered = _first_pixel(path, info)
    assert np.allclose(recovered, TEAL, atol=2), recovered


def test_reading_an_sd_clip_with_the_hd_matrix_gets_the_colour_wrong():
    """This is the reason the rule matters. Same bytes, wrong matrix, wrong colour."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sd.mkv"
        clipgen.write_clip(
            path,
            [clipgen.solid(64, 48, TEAL)] * 3,
            colorspace=clipgen.AVCOL_SPC_SMPTE170M,
            tag_colorspace=False,
            tag_range=False,
        )
        right = probe(path, analysis_width=64)
        wrong = probe(path, policy=ColorPolicy(hd_min_height=1), analysis_width=64)
        assert wrong.color.matrix == "bt709"
        assert not np.allclose(_first_pixel(path, right), _first_pixel(path, wrong), atol=2)


def test_limited_range_luma_is_normalised_from_16_to_235(calm_clip):
    """The video signal level the broadcast profile measures is 0 at code 16 and 1 at code 235
    for a limited range file. Reading it as 0 to 255 would put every luminance too high."""
    frames = [clipgen.solid(64, 48, (255, 255, 255)), clipgen.solid(64, 48, (0, 0, 0))]
    path = calm_clip(
        "limited.mkv", frames * 2, colorspace=clipgen.AVCOL_SPC_BT709,
        color_range=clipgen.AVCOL_RANGE_MPEG,
    )
    info = probe(path, analysis_width=64)
    assert info.color.color_range == "limited"
    white, black = list(iter_frames(path, info))[:2]
    assert float(white.video_level.mean()) == pytest.approx(1.0, abs=0.01)
    assert float(black.video_level.mean()) == pytest.approx(0.0, abs=0.01)
    # And the raw luma really is the limited range codes, so the test would fail if the
    # normalisation used 0 to 255.
    import av

    with av.open(str(path)) as container:
        frame = next(container.decode(container.streams.video[0]))
        luma = frame.reformat(format="yuv444p").to_ndarray()[0]
    assert 230 <= float(luma.mean()) <= 240, float(luma.mean())


def test_full_range_clip_is_decoded_full_range(calm_clip):
    """A yuvj file holds black at code 0 and white at code 255. Decoding it as limited range
    would stretch it and push the whites past white."""
    frames = [clipgen.solid(64, 48, (255, 255, 255)), clipgen.solid(64, 48, (0, 0, 0))]
    path = calm_clip(
        "fullrange.mkv",
        frames * 2,
        codec="mjpeg",
        pix_fmt="yuvj420p",
        color_range=clipgen.AVCOL_RANGE_JPEG,
    )
    info = probe(path, analysis_width=64)
    assert info.color.color_range == "full"
    assert info.color.range_source == "pixel-format-yuvj"
    white, black = list(iter_frames(path, info))[:2]
    assert float(white.video_level.mean()) > 0.95
    assert float(black.video_level.mean()) < 0.05
