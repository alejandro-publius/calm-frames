"""Static, non-flashing swatches must be encoded using their declared matrix/range.

These tests never display pixels. Both generated states are identical, and each
temporary file is deleted by its job. The truth generator stays independent of
flashmap: neither this decoder nor the renderer imports the detector.
"""

from pathlib import Path
import tempfile

import av
from av.video.reformatter import VideoReformatter
import numpy as np
import pytest

from conformance.render import decode_mean_luminance, render_clip
from conformance.spec import load_spec


def round_trip(tagging, height, color, matrix, color_range):
    clip = {
        "width": 32, "height": height, "duration_ms": 100,
        "fps": 20, "timing": "cfr", "flash_start_ms": 1000,
        "flash_hz": 0, "seed": 0, "shape": "center_rect",
        "area_fraction": 1, "background_rgb": color,
        "state_a_rgb": color, "state_b_rgb": color,
        "color_tagging": tagging, "crf": None,
    }
    with tempfile.TemporaryDirectory(prefix="calm-static-color-test-") as scratch:
        path = Path(scratch) / "constant_swatch.mp4"
        try:
            render_clip(clip, path)
            with av.open(str(path)) as container:
                stream = container.streams.video[0]
                tags = (stream.codec_context.colorspace, stream.codec_context.color_range)
                frame = next(container.decode(stream))
                rgb = VideoReformatter().reformat(
                    frame, format="rgb24", src_colorspace=matrix,
                    src_color_range=color_range, dst_color_range="JPEG",
                ).to_ndarray()
            _, means = decode_mean_luminance(path, load_spec(), work_width=32)
            return rgb[height // 2, 16].astype(int), tags, means
        finally:
            path.unlink(missing_ok=True)


@pytest.mark.parametrize("tagging,height,matrix", [
    ("bt709", 32, "ITU709"),
    ("bt601", 32, "ITU601"),
    ("untagged_sd", 32, "ITU601"),
    ("untagged_hd", 720, "ITU709"),
    # Frozen cross-design names are not a reliable indicator of actual height.
    ("untagged_hd", 32, "ITU601"),
    ("untagged_sd", 720, "ITU709"),
])
def test_encoded_chroma_matches_the_tag_or_documented_height_convention(tagging, height, matrix):
    intended = [255, 58, 58]
    decoded, tags, _ = round_trip(tagging, height, intended, matrix, "MPEG")
    assert np.max(np.abs(decoded - intended)) <= 3, (intended, decoded.tolist())
    if tagging.startswith("untagged"):
        assert tags[0] == 2, "untagged cases must retain unspecified matrix tags"
    else:
        assert tags[0] == (1 if tagging == "bt709" else 6)


@pytest.mark.parametrize("intended", [[0, 0, 0], [255, 255, 255], [255, 58, 58]])
def test_full_range_pixels_match_full_range_metadata(intended):
    decoded, tags, _ = round_trip("full_range", 32, intended, "ITU709", "JPEG")
    assert np.max(np.abs(decoded - intended)) <= 3, (intended, decoded.tolist())
    assert tags == (1, 2)


@pytest.mark.parametrize("tagging,height,matrix,color_range,intended", [
    ("bt709", 32, "ITU709", "MPEG", [255, 58, 58]),
    ("untagged_hd", 720, "ITU709", "MPEG", [255, 58, 58]),
    ("untagged_sd", 720, "ITU709", "MPEG", [255, 58, 58]),
    ("full_range", 32, "ITU709", "JPEG", [255, 255, 255]),
])
def test_fidelity_decode_uses_declared_or_inferred_matrix_and_range(
    tagging, height, matrix, color_range, intended,
):
    _, _, means = round_trip(tagging, height, intended, matrix, color_range)
    spec = load_spec()
    expected = float(spec.relative_luminance(spec.srgb_to_linear(np.array(intended) / 255)))
    # libswscale rounds differently per platform. On x86_64 it puts the white swatch's
    # chroma one code low, so it decodes to a mean of 0.99558, while Apple silicon
    # returns 1.0. A wrong matrix or range moves these means by 0.02 or more, so allow
    # up to the luminance change of moving every channel one 8-bit code (0.0089 at
    # white), and never less than the 0.004 used before. The 1e-12 only absorbs
    # floating-point noise, so a decode exactly one code off on every channel passes.
    one_code = max(
        abs(spec.luminance_of_srgb8(np.clip(np.add(intended, step), 0, 255)) - expected)
        for step in (-1, 1)
    )
    tolerance = max(0.004, one_code)
    assert means and max(abs(mean - expected) for mean in means) <= tolerance + 1e-12
