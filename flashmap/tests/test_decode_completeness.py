"""Partial copies must not turn missing video evidence into a passing map.

The fixture is the repository's synthetic, non-flashing brightness sweep.
Real licensed-footage diagnostics are recorded separately from these regressions.
"""
import subprocess
from pathlib import Path

import av
import pytest

from flashmap.cli import EXIT_ERROR, main
from flashmap.decode import iter_frames, probe

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("fraction", [0.5, 0.75])
def test_packet_boundary_truncation_cannot_write_a_successful_map(tmp_path, fraction):
    complete = tmp_path / "complete.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(FIXTURES / "calm_sweep.mp4"),
                    "-c", "copy", "-movflags", "+faststart", str(complete)], check=True)
    with av.open(str(complete)) as container:
        packets = [packet for packet in container.demux(video=0) if packet.size]
    cutoff = packets[int(len(packets) * fraction)].pos
    broken = tmp_path / "incomplete.mp4"
    broken.write_bytes(complete.read_bytes()[:cutoff])
    out = tmp_path / "map.json"
    assert main(["analyze", str(broken), "--out", str(out), "--quiet"]) == EXIT_ERROR
    assert not out.exists()


@pytest.mark.parametrize("name, count, declared", [
    ("calm_sweep.mp4", 40, 40), ("calm_sweep_theora.ogv", 24, 0),
])
def test_complete_video_and_unknown_frame_count_keep_all_frames(name, count, declared):
    path = FIXTURES / name
    with av.open(str(path)) as container:
        assert container.streams.video[0].frames == declared
    assert len(list(iter_frames(path, probe(path)))) == count
