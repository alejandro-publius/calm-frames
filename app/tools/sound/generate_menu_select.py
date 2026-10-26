#!/usr/bin/env python3
"""Generate the original Calm Frames selection cue from sine waves only."""

import math
from pathlib import Path
import struct
import subprocess


def main() -> None:
    sample_rate = 48000
    duration = 0.105
    samples = bytearray()
    for index in range(round(sample_rate * duration)):
        time = index / sample_rate
        attack = min(time / 0.008, 1.0)
        release = min((duration - time) / 0.025, 1.0)
        envelope = math.sin(attack * math.pi / 2) ** 2 * release ** 2
        envelope *= math.exp(-time * 35)
        tone = math.sin(2 * math.pi * 560 * time)
        tone += 0.13 * math.sin(2 * math.pi * 1120 * time)
        samples.extend(struct.pack('<h', round(32767 * 0.12 * envelope * tone)))

    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 's16le', '-ar', str(sample_rate), '-ac', '1', '-i', 'pipe:0',
        '-map_metadata', '-1', '-fflags', '+bitexact', '-flags:a', '+bitexact',
        '-c:a', 'libmp3lame', '-b:a', '128k',
        str(Path(__file__).resolve().parents[2] / 'assets' / 'raw' / 'sound' / 'menu-select.mp3'),
    ], input=samples, check=True)


if __name__ == '__main__':
    main()
