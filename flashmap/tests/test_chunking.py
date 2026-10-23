"""Chunked analysis with overlap.

The analyser is a stream. Feeding it a file in pieces, with any amount of overlap between the
pieces, has to give exactly the answer that feeding it whole gives. The overlap is real: those
frames are pushed twice, and the analyser drops the repeats by timestamp.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import clipgen
from flashmap import WCAG, analyze_file
from flashmap import color as color_math
from flashmap.analyze import StreamingAnalyzer, _chunked, build_area_windows
from flashmap.decode import iter_frames, probe
from flashmap.picture import detect_picture

W, H = 64, 48
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def _mixed_frames():
    """Calm, a strobe, calm, a smaller strobe. Enough shape to catch a boundary mistake."""
    calm = [clipgen.solid(W, H, GRAY)] * 10
    strobe = clipgen.alternating(24, clipgen.solid(W, H, BLACK), clipgen.solid(W, H, WHITE))
    band_off = clipgen.solid(W, H, GRAY)
    band_on = clipgen.patch(band_off, WHITE, top=0.3, left=0.0, height=8 / H, width=1.0)
    small = clipgen.alternating(16, band_off, band_on)
    return calm + strobe + calm + small


@pytest.fixture(scope="module")
def mixed_clip(tmp_path_factory):
    path = tmp_path_factory.mktemp("chunk") / "HAZARD_mixed.mkv"
    clipgen.write_clip(path, _mixed_frames(), fps=20)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def decoded(mixed_clip):
    info = probe(mixed_clip)
    frames = list(iter_frames(mixed_clip, info))
    samples = [
        color_math.relative_luminance(color_math.srgb_to_linear(frame.rgb)) for frame in frames
    ]
    picture = detect_picture(samples)
    return frames, picture


def _run(frames, picture, chunk_size, overlap):
    analyzer = StreamingAnalyzer(WCAG, picture, build_area_windows(WCAG, picture, None))
    if chunk_size is None:
        analyzer.push(frames)
    else:
        for batch in _chunked(iter(frames), chunk_size, overlap):
            analyzer.push(batch)
    return [segment.as_dict() for segment in analyzer.segments()]


def test_the_clip_under_test_really_does_flash(decoded):
    frames, picture = decoded
    assert _run(frames, picture, None, 0), "a test that compares nothing proves nothing"


@pytest.mark.parametrize(
    ("chunk_size", "overlap"), [(1, 0), (3, 0), (7, 3), (10, 9), (25, 5), (1000, 0)]
)
def test_chunked_equals_whole_file(decoded, chunk_size, overlap):
    frames, picture = decoded
    assert _run(frames, picture, chunk_size, overlap) == _run(frames, picture, None, 0)


@pytest.mark.slow
@given(
    chunk_size=st.integers(min_value=1, max_value=40),
    overlap_ratio=st.floats(min_value=0.0, max_value=0.95),
)
@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_chunked_equals_whole_file_for_any_chunking(decoded, chunk_size, overlap_ratio):
    frames, picture = decoded
    overlap = min(chunk_size - 1, int(chunk_size * overlap_ratio))
    assert _run(frames, picture, chunk_size, overlap) == _run(frames, picture, None, 0)


def test_overlap_really_does_resend_frames():
    batches = list(_chunked(iter(range(10)), chunk_frames=4, overlap=2))  # type: ignore[arg-type]
    assert batches == [[0, 1, 2, 3], [2, 3, 4, 5, 6, 7], [6, 7, 8, 9]]


def test_overlap_must_be_smaller_than_the_chunk():
    with pytest.raises(ValueError):
        list(_chunked(iter([1, 2, 3]), chunk_frames=2, overlap=2))  # type: ignore[arg-type]


def test_chunking_through_the_public_entry_point_matches(mixed_clip):
    whole = analyze_file(mixed_clip, WCAG)
    chunked = analyze_file(mixed_clip, WCAG, chunk_frames=9, chunk_overlap=4)
    assert [segment.as_dict() for segment in chunked.segments] == [
        segment.as_dict() for segment in whole.segments
    ]
    assert chunked.frame_count == whole.frame_count
