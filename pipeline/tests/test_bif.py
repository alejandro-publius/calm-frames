"""BIF trickplay files, and the rule that every frame comes from a calm moment."""

from __future__ import annotations

import struct

import pytest

from pipeline import PipelineError
from pipeline.bif import (
    BIF_MAGIC,
    HEADER_BYTES,
    BifFrame,
    all_frames_calm,
    plan_bif_frames,
    read_bif,
    write_bif,
)
from pipeline.flashmap_adapter import MapSegment
from pipeline.hideplan import build_cover_intervals, is_calm


def seg(start, end, reason="general"):
    return MapSegment(start_ms=start, end_ms=end, reason=reason)


class TestBifFormat:
    def test_round_trip(self, tmp_path):
        images = [b"\xff\xd8jpeg-one", b"\xff\xd8jpeg-two-longer"]
        path = write_bif(tmp_path / "t.bif", images, timestamps=[0, 10])
        parsed = read_bif(path)
        assert parsed.version == 0
        assert parsed.count == 2
        assert parsed.multiplier_ms == 1000
        assert parsed.timestamps_ms == [0, 10_000]
        assert parsed.sizes == [len(images[0]), len(images[1])]

    def test_the_header_carries_the_magic(self, tmp_path):
        path = write_bif(tmp_path / "t.bif", [b"a"])
        assert path.read_bytes()[:8] == BIF_MAGIC

    def test_the_index_points_at_the_images(self, tmp_path):
        images = [b"first", b"second"]
        path = write_bif(tmp_path / "t.bif", images)
        raw = path.read_bytes()
        first_offset = struct.unpack_from("<I", raw, HEADER_BYTES + 4)[0]
        assert raw[first_offset : first_offset + len(images[0])] == images[0]

    def test_the_last_index_entry_is_the_end_of_the_file(self, tmp_path):
        images = [b"first", b"second"]
        path = write_bif(tmp_path / "t.bif", images)
        raw = path.read_bytes()
        sentinel_at = HEADER_BYTES + 2 * 8
        timestamp, offset = struct.unpack_from("<II", raw, sentinel_at)
        assert timestamp == 0xFFFFFFFF
        assert offset == len(raw)

    def test_a_truncated_file_is_refused(self, tmp_path):
        path = write_bif(tmp_path / "t.bif", [b"first", b"second"])
        raw = path.read_bytes()
        path.write_bytes(raw[:-3])
        with pytest.raises(PipelineError):
            read_bif(path)

    def test_something_that_is_not_a_bif_is_refused(self, tmp_path):
        path = tmp_path / "t.bif"
        path.write_bytes(b"this is not a trickplay file")
        with pytest.raises(PipelineError):
            read_bif(path)

    def test_one_timestamp_per_image_is_required(self, tmp_path):
        with pytest.raises(PipelineError):
            write_bif(tmp_path / "t.bif", [b"a", b"b"], timestamps=[0])


class TestFramesComeFromCalmMoments:
    def test_a_slot_inside_a_covered_span_is_sampled_from_elsewhere(self):
        intervals = build_cover_intervals([seg(9000, 11_000)], guard_band_ms=500)
        frames = plan_bif_frames(intervals, 30_000, interval_ms=10_000, margin_ms=1000)
        slots = [frame.slot_ms for frame in frames]
        assert slots == [0, 10_000, 20_000]
        # The slot at 10 s is inside the flagged span, so the picture comes
        # from the nearest calm moment instead, and the manifest says so.
        inside = frames[1]
        assert inside.snapped
        assert inside.source_ms != inside.slot_ms
        assert is_calm(intervals, inside.source_ms, margin_ms=1000)

    def test_every_planned_frame_is_calm(self):
        intervals = build_cover_intervals(
            [seg(2000, 3000), seg(9000, 11_000), seg(25_000, 26_000)]
        )
        frames = plan_bif_frames(intervals, 30_000, interval_ms=2000, margin_ms=1000)
        assert frames
        assert all_frames_calm(frames, intervals, margin_ms=1000) == []

    def test_a_frame_taken_from_a_flagged_moment_is_caught(self):
        intervals = build_cover_intervals([seg(9000, 11_000)])
        frames = [BifFrame(index=0, slot_ms=0, source_ms=10_000)]
        bad = all_frames_calm(frames, intervals, margin_ms=1000)
        assert [frame.source_ms for frame in bad] == [10_000]

    def test_a_title_flagged_end_to_end_gets_no_trickplay(self):
        intervals = build_cover_intervals([seg(0, 30_000)], guard_band_ms=0)
        with pytest.raises(PipelineError):
            plan_bif_frames(intervals, 30_000, interval_ms=10_000, margin_ms=1000)

    def test_a_zero_length_title_is_refused(self):
        with pytest.raises(PipelineError):
            plan_bif_frames([], 0, interval_ms=10_000)
