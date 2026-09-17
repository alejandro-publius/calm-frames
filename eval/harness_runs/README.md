# Measurement runs

Each file here starts one measurement run. Push one to a device and launch the
app, and it goes straight into that run, so a take can be started in front of a
camera without navigating menus.

```
PKG=io.github.alejandropublius.calmframes
vega device copy-to eval/harness_runs/layering.json /home/app_user/packages/$PKG/data/calm-frames-harness.json
vega run-app app/build/armv7-debug/calm-frames-app_armv7.vpkg     # stick
vega run-app app/build/aarch64-debug/calm-frames-app_aarch64.vpkg # virtual device
```

Use a debug package. Release builds strip `console.log`, and the run's evidence
is in the log:

```
vega device start-log-stream | grep CALM_TIMING
```

To get the normal app back:

```
vega device run-cmd --command "rm /home/app_user/packages/$PKG/data/calm-frames-harness.json"
```

## The runs

| File | What it is | What it is for |
|---|---|---|
| `layering.json` | Phase 1.5 layering test. A full-screen cover toggles every 5 seconds over a playing title. | Answers whether the cover really hides the hardware video layer, whether captions stay readable above it, and whether audio keeps going. Film the screen, with captions turned on in the player. |
| `timing-placeholder.json` | The GATE 1 harness shape, on a placeholder schedule. | Exercises the scheduler, the cover and the logging. **It cannot produce a GATE 1 number**, because the title it plays has no markers at these times. Replace the segments with the schedule calm-timing emits for the marker clip, then it is a real GATE 1 run. |

## What the log holds

Every line is one JSON object after the `CALM_TIMING` prefix:

- `harness-start` and `harness-stop`, with the mode, the number of intervals and the schedule label;
- every media event (`timeupdate`, `seeking`, `seeked`, `waiting`, `stalled`, `pause`, `playing`, `ratechange`, `ended`, `error`) with media time, wall-clock time, playback rate and, on timeupdate, the frame counters if the player exposes them;
- `cover-on` and `cover-off`, with the media time and the reason.

Pairing media time with wall-clock time on every line is what lets a 240 fps
recording be lined up against what the app believed it was doing. How often
`timeupdate` fires on Vega, and how precise `currentTime` is, are not
documented, which is exactly why the harness records both rather than assuming.

## Safety

Both runs play a non-flashing title. Never point a measurement run at flashing
content with the cover off. See docs/SAFETY.md.
