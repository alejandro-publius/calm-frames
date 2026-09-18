# Test fixtures

Only files that do not flash live here.

- `calm_sweep.mp4` is 40 frames of 64 by 48, a slow brightness sweep, H.264 in MP4, tagged
  BT.709 limited range. It is under 3 KB. It is the file the GitHub Action test uses as the
  "this pull request is fine" case, and the CLI test uses as the passing case.
- `calm_sweep_theora.ogv` is 24 frames of 64 by 48, the same kind of slow sweep, Theora in Ogg,
  10 frames per second. Frames 8 to 12 repeat frame 7 exactly and frames 20 to 23 repeat frame
  19, so 9 of its 24 packets are zero length. It is 4.2 KB. It is the regression clip for the
  bug that stopped four clips in the screening pool: an empty packet handed to libavcodec makes
  `avcodec_send_packet()` return EINVAL, reported as "returned 22". `test_theora.py` uses it.
  The run at the end also leaves the file's last decodable frame at 1.9 s of a 2.4 s duration,
  which is the shape `pipeline/tests/test_stills.py` needs, so the same clip is copied there.

Anything that flashes is hazardous and is generated into a temporary directory by the
`hazard_clip` fixture in `../conftest.py`, measured, and deleted in the same test. Nothing that
flashes is ever written into this folder or committed.

To rebuild `calm_sweep.mp4`:

```python
import numpy as np, clipgen
frames = [clipgen.solid(64, 48, (v, v, v)) for v in
          [int(60 + 40 * np.sin(i / 12.0)) for i in range(40)]]
clipgen.write_clip("calm_sweep.mp4", frames, fps=20, codec="libx264", pix_fmt="yuv420p")
```

To rebuild `calm_sweep_theora.ogv`, two steps are needed.

1. libtheora encodes the frames. Neither the ffmpeg on this machine nor the one PyAV links
   against is built with it, so the clip was made with the static ffmpeg inside the
   `imageio-ffmpeg` wheel, which does have `libtheora`. Any ffmpeg built with libtheora works.
2. ffmpeg's libtheora wrapper answers a repeated frame by returning no packet at all and
   counting the repeat in the Ogg granule position, so the file it writes has a hole in its
   timeline where the repeats should be. The packets are read back and re-muxed with an
   explicit zero length packet at every timestamp the encoder skipped. That is the shape
   ffmpeg2theora writes, and the shape the four clips in the screening pool have.

```python
import subprocess, av, numpy as np
from pathlib import Path

FFMPEG = "path/to/an/ffmpeg/built/with/libtheora"
work = Path("_theora_build"); work.mkdir(exist_ok=True)

REPEATS = ((8, 12), (20, 23))
values = []
for i in range(24):
    run = next((r for r in REPEATS if r[0] <= i <= r[1]), None)
    values.append(values[run[0] - 1] if run else int(60 + 40 * np.sin(i / 6.0)))
for index, value in enumerate(values):
    frame = np.full((48, 64, 3), value, dtype=np.uint8)
    frame[:, :, 0] = min(255, value + 10)
    av.VideoFrame.from_ndarray(frame, format="rgb24").to_image().save(work / f"f{index:03d}.png")

subprocess.run([FFMPEG, "-y", "-framerate", "10", "-i", str(work / "f%03d.png"),
                "-c:v", "libtheora", "-q:v", "8", str(work / "encoded.ogv")], check=True)

src = av.open(str(work / "encoded.ogv"))
src_stream = src.streams.video[0]
out = av.open("calm_sweep_theora.ogv", "w", format="ogg")
out_stream = out.add_stream_from_template(src_stream, opaque=True)
previous = None
for packet in [p for p in src.demux(src_stream) if p.pts is not None]:
    if previous is not None:
        for missing in range(previous + 1, packet.pts):
            repeat = av.Packet(0)
            repeat.stream, repeat.pts, repeat.dts = out_stream, missing, missing
            repeat.time_base, repeat.duration = packet.time_base, 1
            out.mux(repeat)
    packet.stream = out_stream
    out.mux(packet)
    previous = packet.pts
# A run of repeats at the end of the file gets counted in the granule position and written as
# no packet at all, so the encoder's file is short. Put those back too.
for missing in range(previous + 1, 24):
    repeat = av.Packet(0)
    repeat.stream, repeat.pts, repeat.dts = out_stream, missing, missing
    repeat.time_base, repeat.duration = packet.time_base, 1
    out.mux(repeat)
out.close()
```
