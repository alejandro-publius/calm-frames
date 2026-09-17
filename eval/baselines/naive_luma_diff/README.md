# Naive mean-luminance differencing baseline

The floor of the comparison, and the simplest thing anyone would try first: one
number per frame (mean luma from ffmpeg's `signalstats` YAVG), flag a frame when
that number moves more than a fixed amount since the previous frame, merge
neighbours into segments.

## Run it

```
make -f eval/baselines/naive_luma_diff/naive_luma.mk naive-luma-run VIDEO=media/clip.mp4
make -f eval/baselines/naive_luma_diff/naive_luma.mk naive-luma-pool
make -f eval/baselines/naive_luma_diff/naive_luma.mk naive-luma-selftest
```

One JSON report per clip lands in `results/baselines/naive_luma_diff/`.

## What it cannot do, by construction

- **Area.** A strobe filling 2% of the picture moves the frame mean about as much
  as a gentle wash over the whole picture. WCAG's flash rules are about a
  proportion of the visual field, and this baseline has no idea what that is.
- **Color.** The red-flash rule keys on saturated red, which mean luma discards.
- **Rate.** No sliding window, so three flashes in one second and three flashes in
  ten seconds look the same frame by frame.
- **Linear light.** Mean luma is read off the gamma-encoded Y plane, so the same
  swing counts equally in the dark end and the bright end.
- **Cuts.** A hard cut between a dark shot and a bright one trips it every time.

That list is why the baseline is here: it is the shape of the gap that flashmap
has to fill.

## Thresholds

`--threshold` defaults to 20 8-bit luma codes. It is a baseline knob, chosen so
the two selftest clips come out right, and it is **not** a spec number. Numbers
that mean something live in `flashmap/docs/SPEC_SOURCES.md`.

## Selftest

`naive-luma-selftest` builds two clips where the right answer needs no spec:

- a 6 s static mid-gray clip, which must produce zero segments;
- a 6 s 10 Hz full-field black/white clip, which must produce at least one.

The flashing clip is generated, analyzed and deleted inside that one target and
is never opened in a player.

Both directions of the check were mutation-tested on Sep 17, 2026: setting
`DEFAULT_THRESHOLD = 0.0` makes it fail with "flagged a clip where nothing
happens", and `DEFAULT_THRESHOLD = 250.0` makes it fail with "missed a 10 Hz
full-field flash". Note that the target ignores `NL_ARGS` on purpose, so mutate
the source, not the command line, when you want to re-confirm this.

Nothing here is a conformance result or a safety claim.
