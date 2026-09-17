# Test fixtures

Only files that do not flash live here.

- `calm_sweep.mp4` is 40 frames of 64 by 48, a slow brightness sweep, H.264 in MP4, tagged
  BT.709 limited range. It is under 3 KB. It is the file the GitHub Action test uses as the
  "this pull request is fine" case, and the CLI test uses as the passing case.

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
