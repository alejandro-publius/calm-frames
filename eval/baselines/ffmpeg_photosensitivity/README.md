# ffmpeg photosensitivity baseline

Uses ffmpeg's built-in `photosensitivity` video filter as a detector.

The filter is a mitigator, not a reporter: it quietly rewrites frames it thinks
are unsafe and prints nothing. So `run.py` runs it against an unfiltered copy of
the same decode and records where the two differ.

```
[0:v]split=2[o][s]; [s]photosensitivity[p]; [o][p]blend=difference,signalstats
```

`YMAX` of that difference is 0 exactly on the frames the filter passed through
untouched.

## Run it

```
make -f eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk ffmpeg-ps-run VIDEO=media/clip.mp4
make -f eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk ffmpeg-ps-pool
make -f eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk ffmpeg-ps-selftest
make -f eval/baselines/ffmpeg_photosensitivity/ffmpeg_ps.mk ffmpeg-ps-version
```

One JSON report per clip lands in `results/baselines/ffmpeg_photosensitivity/`.

## The first second

The brief says to drop the filter's first second of output because it misfires
even on a static gray clip. `run.py` drops it (`DEFAULT_WARMUP_S = 1.0`), because
dropping it is the conservative choice and keeps our numbers comparable with
whatever produced that note. The report carries both
`frames_dropped_as_warmup` and `warmup_would_have_flagged`, so the cost of the
drop is always visible.

**On this machine the misfire did not reproduce.** ffmpeg 8.1.2, Sep 17 2026, a
6 s 25 fps static mid-gray clip: 150 frames in, 150 frames out, difference YMAX 0
on every frame including the first second. Either the behavior is build
dependent or it was fixed upstream. `ffmpeg-ps-selftest` re-runs exactly that
measurement and fails if a build ever does misfire, so nobody has to take this
paragraph on trust.

## Version

Pinned by measurement rather than by image, for now: the local ffmpeg build
string goes into every report's `tool_version`. `FFPS_IMAGE` in the makefile
names the image for the containerized path, which is not the default because the
colima VM on this Mac is shared with another project and was busy.

## What it cannot do

No area rule, no color, no red-flash rule, no room rule, no signed output. It
keys on whole-frame change. That is the point of a baseline.

Nothing here is a conformance result or a safety claim.
