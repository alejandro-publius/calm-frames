"""Theora in Ogg, and the empty packets that used to stop the decoder dead.

Four clips in the screening pool died with `avcodec_send_packet() returned 22`. Ogg Theora
marks a frame that is identical to the one before it with a zero length packet, and libavcodec
answers a packet that has a buffer and no bytes with EINVAL, which is the 22. So an empty
packet is never handed to the decoder now. It keeps its place in the timeline and repeats the
picture in front of it, which is what a player shows for that slice of time.

`fixtures/calm_sweep_theora.ogv` is a 24 frame grey sweep where frames 8 to 12 repeat frame 7,
so 5 of its 24 packets are empty. Nothing in it flashes. How it was built is in
fixtures/README.md.
"""

from __future__ import annotations

import av
import pytest

from flashmap import WCAG, analyze_file
from flashmap.decode import iter_frames, probe

from conftest import FIXTURES

THEORA_CLIP = FIXTURES / "calm_sweep_theora.ogv"

FRAME_COUNT = 24
EMPTY_PACKETS = 5
FRAME_INTERVAL_MS = 100.0


def test_the_fixture_really_carries_empty_packets():
    """Without these the clip proves nothing, so the test suite checks they are still there."""
    with av.open(str(THEORA_CLIP)) as container:
        stream = container.streams.video[0]
        assert stream.codec_context.name == "theora"
        sizes = [packet.size for packet in container.demux(stream) if packet.pts is not None]
    assert len(sizes) == FRAME_COUNT
    assert sum(1 for size in sizes if size == 0) == EMPTY_PACKETS


def test_theora_decodes():
    info = probe(THEORA_CLIP)
    frames = list(iter_frames(THEORA_CLIP, info))
    assert len(frames) == FRAME_COUNT


def test_an_empty_packet_repeats_the_picture_in_front_of_it():
    info = probe(THEORA_CLIP)
    frames = list(iter_frames(THEORA_CLIP, info))
    repeats = [frame for frame in frames if frame.repeats_previous]
    assert len(repeats) == EMPTY_PACKETS
    for frame in repeats:
        previous = frames[frame.index - 1]
        assert frame.rgb is previous.rgb
        assert frame.pts_ms > previous.pts_ms


def test_the_timeline_keeps_its_cadence_across_the_repeats():
    """Dropping the empty packets would leave a hole and make a constant rate file look
    variable, which is what the sidecar and the pipeline's timing check both read."""
    info = probe(THEORA_CLIP)
    stamps = [frame.pts_ms for frame in iter_frames(THEORA_CLIP, info)]
    assert stamps == sorted(stamps)
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    assert gaps == pytest.approx([FRAME_INTERVAL_MS] * (FRAME_COUNT - 1))


def test_theora_analyses():
    result = analyze_file(THEORA_CLIP, WCAG)
    assert result.frame_count == FRAME_COUNT
    assert not result.variable_frame_rate
    assert result.frame_interval_ms["median"] == pytest.approx(FRAME_INTERVAL_MS)
    assert result.passes
