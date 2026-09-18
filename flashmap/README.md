# flashmap

Measure video and animated images against the WCAG 2.2 general and red flash thresholds, and
write a signed map of the parts that go over.

flashmap reduces exposure to flashing above published limits in the videos it measures. It is
not a medical device and it does not prevent seizures.

Apache-2.0. Part of [Calm Frames](../README.md), and usable on its own.

## What it does

- **WCAG 2.2 Success Criterion 2.3.1**, both the general flash rule and the red flash rule,
  with the saturated red test done in the CIE 1976 UCS chromaticity diagram.
- **Sliding one-second windows** for the three-flashes-a-second limit, and **sliding area
  windows** for the 25% of a 10 degree visual field rule. The window is slid to every position,
  because the spec says "any 10 degree visual field".
- **ITU-R BT.1702-3** as a second profile, standard dynamic range only.
- **Real frame timestamps** from the container. There is no assumed frame rate anywhere.
  Variable frame rate input comes out right.
- **Letterbox and pillarbox detection**, so the area is measured on the picture. Every map says
  so and carries the bar geometry it removed, in the file's own coded pixels, so a re-encode
  can be measured on the same rectangle rather than on one detected in the re-encode.
- **Ogg Theora empty packets** kept in the timeline. A frame identical to the one before it is
  written as a zero length packet, libavcodec refuses one outright, and the picture a player
  shows for that packet's time is the one in front of it.
- **The room rule**: a household gives its TV diagonal and seat distance, and flashmap adds the
  10 degree field for that room as a second area window. A room setting can only add hides.
- **Correct colour handling**: a tagged stream uses its tag, an untagged HD stream is decoded
  as BT.709 and an untagged SD stream as BT.601, and a `yuvj` pixel format is full range. Every
  guess is recorded in the map.
- **Chunked analysis** with overlap, which gives byte for byte the same map as a whole file run.
- **Ed25519 signed sidecars** bound to the file's SHA-256.
- **A GitHub Action** that fails a pull request adding an image or video over the thresholds.

## Where the numbers come from

[`docs/SPEC_SOURCES.md`](docs/SPEC_SOURCES.md) holds the exact quoted text and a link for every
threshold in the code, and names the three things that could not be verified from a primary
source. Nothing in this package may use a number that is not on that page.

The map format is [`docs/SIDECAR_SPEC.md`](../docs/SIDECAR_SPEC.md), version 1.

## Install

```sh
python -m pip install flashmap
```

From this checkout, with the tests:

```sh
python -m pip install -e 'flashmap[dev]'
```

Needs Python 3.12 or newer. PyAV brings its own FFmpeg, so there is nothing else to install.

## Use

```sh
# make a signing key. The private key never goes in a repository.
python -m flashmap keygen --out team_key

# analyse a file and write a signed map next to it
python -m flashmap analyze VIDEO --profile wcag --out MAP.json \
    --diag 55 --distance-ft 8 --key team_key.pem

# the broadcast profile, with an assumed peak white
python -m flashmap analyze VIDEO --profile broadcast --out MAP.json --peak-nits 200

# measure a re-encode on the picture rectangle out of the original's map, rather than on one
# detected in the re-encode. Re-encoding nudges the outermost rows, and one row read as a
# letterbox bar shrinks the rectangle and lifts every area fraction measured against it.
python -m flashmap analyze RENDITION.mp4 --profile wcag --out CHECK.json \
    --picture-from SOURCE_MAP.json

# check a map is real, is for this file, and was signed by a key you hold
python -m flashmap verify MAP.json VIDEO --pub team_key.pub.pem

# pass or fail one or more files
python -m flashmap check VIDEO [VIDEO ...] --profile wcag
```

Exit codes: `0` below the thresholds or verified, `1` over the thresholds or failed to verify,
`2` flashmap could not tell. A caller that treats `2` as a pass has a hole in it.

From Python:

```python
from flashmap import WCAG, RoomSetting, analyze_file, build_map, sign_map

result = analyze_file("clip.mp4", WCAG, room=RoomSetting(tv_diagonal_in=55, seat_distance_in=96))
print(result.passes, result.hidden_ms)
document = build_map(result)
```

## The GitHub Action

Copy [`examples/flash-check.yml`](examples/flash-check.yml) into
`.github/workflows/flash-check.yml`. Every pull request that adds or changes an image or video
gets checked, and the job summary says which file broke which rule and where the area was
measured.

```yaml
- uses: calm-frames/calm-frames/flashmap@v1
  with:
    profile: wcag
```

The checkout needs history, so use `fetch-depth: 0`. Without a base commit the action checks
every tracked file instead, which is the right thing on a scheduled run.

## Safety while working on this

- A clip that flashes is hazardous. Generate it, measure it, delete it in the same job. Never
  open one in a player.
- Generated media never goes in git. The only media file in this package is
  `tests/fixtures/calm_sweep.mp4`, which does not flash.
- The suite's `hazard_clip` fixture is the only way it makes a flashing file, and it deletes
  the file when the test ends, pass or fail.

## Tests

```sh
python -m pytest flashmap/tests                 # everything, about 13 seconds
python -m pytest flashmap/tests -m 'not slow'   # what CI runs on a busy runner
```

A green test proves nothing on its own, so every guard in flashmap has been broken on purpose
and watched go red:

```sh
python flashmap/tools/mutate.py
```

That edits one line of the source at a time, runs only the tests meant to catch that edit,
expects them to fail, puts the file back and checks the tree is byte for byte what it was. It
clears every `__pycache__` first, because a mutation that keeps the file the same length can
otherwise be hidden by a cached `.pyc`.

## What it does not do

- **No HDR.** HLG and PQ tagged files are refused rather than measured with the SDR curve.
- **No pattern rule.** BT.1702-3 Guideline 2, regular patterns, is not implemented.
- **No fine balanced pattern exception.** WCAG would excuse white noise and small
  checkerboards. flashmap reports them, which is the strict direction.
- **No risk score.** Neither spec defines one, so flashmap does not invent one.

Every one of these is repeated inside each map, under `profile.rules_not_implemented` and
`profile.exceptions_not_implemented`, so a reader never has to come back here to find out.
