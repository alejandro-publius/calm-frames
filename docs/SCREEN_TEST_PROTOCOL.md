# Screen test protocol

How to film the screen-level test so the recordings can be measured, and what happens to them
afterwards. This is the 200-event test in `docs/EVAL_PLAN.md` section 8 and HUMAN CHECKPOINT E2
in `docs/GATES.md`, planned for Oct 8 to 13.

The instrument is `eval/meter.py`. It finds the screen in the picture, corrects the camera's
exposure against a step chart filmed on that same screen, and counts WCAG 2.2 SC 2.3.1 general
and red flashes inside the screen region. It is the meter that sits beside the TV in the demo
video and the tool that turns these recordings into `results/screen_level.json`.

**Nothing in here has been done on real hardware yet.** The stick has not arrived, no footage
exists, and the meter has only ever seen simulated recordings (`results/meter_validation.json`).
Expect the first session to find something this page did not think of, and write it down in
`docs/friction_pending.md` when it does.

---

## 1. Safety comes first, and it is not negotiable

- **The filter is on for every take.** No take ever plays flagged content with the filter off.
  The exposure the filter prevented is computed from the flash map, never played.
- **Nobody watches the screen.** The camera records; people leave the room or face away. This
  applies to every take, including the ones that are expected to be dull.
- **Whoever films is not photosensitive** and does not look at the lights. Anyone in shot has
  agreed to be there. `docs/SAFETY.md` applies in full.
- **The recordings are treated as hazard files.** They are footage of a screen that was playing
  flagged content, and a leak is exactly what we are looking for, so a leak is what they might
  contain. They live under `media/`, which is gitignored, and nothing opens them in a player.
  Look at them with `eval/meter.py run --plot`, which draws a graph and never shows a frame.
- **Do not commit a recording.** Only the numbers go in the repository.

---

## 2. What you need

| Thing | Why | State |
|---|---|---|
| A phone that films 240 fps | A camera samples the screen, and a slow one under-reads a fast strobe | **Not confirmed yet.** `docs/STATUS.md` has this on the list to check before the stick arrives |
| A tripod or something solid | The screen region is found once per take and reused. A camera that drifts breaks that | |
| A TV with a game mode | Motion smoothing invents frames that were never sent, and a meter cannot tell an invented frame from a real one | **Not confirmed yet** |
| The Fire TV stick on Vega OS 1.2 | | Waiting on delivery |
| A room you can keep at one light level | A light that changes mid take moves the exposure, and the calibration is only good while the exposure holds still | |

---

## 3. Set the TV up once per session

1. **Game mode on.** This is the one that matters most. It turns off the frame interpolation,
   and on most sets it also turns off the noise reduction and the dynamic contrast.
2. **Motion smoothing off**, by whatever name the maker uses: TruMotion, Motionflow, Auto Motion
   Plus, Action Smoothing.
3. **Picture mode off the dynamic setting.** Dynamic contrast and local dimming both bend the
   relationship between the signal and the light coming off the panel. An affine fit cannot
   follow a bend, so the calibration will refuse the take and tell you so.
4. **No overscan.** Look for "Just scan", "Screen fit", "1:1" or "Full pixel". If the edges of
   the chart are cut off, the patches are not where the meter thinks they are.
5. **Brightness and backlight fixed**, with any ambient light sensor turned off.
6. **Write down what you set**, in the session note. The setting is part of the measurement.

---

## 4. Lock the camera

The single most common way to ruin one of these recordings is to leave the camera on automatic.
Autoexposure follows the strobe, which means the thing being measured changes the instrument.

1. Frame the TV so the whole screen is in view **with some room visible around it**. The meter
   finds the screen by separating it from its surroundings, and with no surroundings it refuses
   and says so.
2. Lock focus on the screen.
3. **Lock exposure.** On iPhone, press and hold until AE/AF LOCK appears. On Android, use the
   pro or manual mode and fix ISO and shutter.
4. **Lock white balance** if the phone lets you.
5. **Turn HDR video off.** The meter is written for standard dynamic range, the same as flashmap.
6. **Set the shutter short if you can choose**, around 1/240 s. A long exposure averages the
   strobe and hides it.
7. Point the camera slightly off the screen's normal so the lens is not looking at its own
   reflection, and check the frame for reflections of lights and windows before you start.
8. **Do not change any of this between the three takes of one run.** The gray take, the chart
   take and the run take are one measurement, and they only fit together while the camera stays
   put.

---

## 5. Every run is three takes and one event file

Film them in this order, without touching the camera in between.

### 5.1 The gray field, and the flicker check

Put a flat mid gray on the screen and film about two seconds.

```
.venv/bin/python eval/meter.py chart --gray --out /tmp/gray.mp4 --seconds 20
```

This take does two jobs:

- **it is where the screen region comes from.** A uniform lit rectangle in a darker room is the
  easiest thing in the world to find, which is why the region is taken from here and reused for
  the other two takes rather than guessed from the run;
- **it is the flicker check.** A still gray screen should be still. If it ripples, something is
  moving that has nothing to do with the content: a backlight being driven with a pulse, a TV
  still doing motion processing, or a lamp in the room on the mains cycle. The meter measures the
  ripple and compares it against the tolerance that take's calibration earned.

A take whose gray field fails the flicker check is excluded, and the exclusion is counted.
`docs/EVAL_PLAN.md` section 9 lists it.

### 5.2 The step chart, for the exposure correction

```
.venv/bin/python eval/meter.py chart --out /tmp/chart.mp4 --seconds 20
```

Show it full screen, film about two seconds, and check on the phone that all ten patches are
visible and that none of the bright ones has gone flat white. The meter fits each colour channel
against the relative luminance the chart was drawn with, so what comes out of it afterwards is
the light the TV actually produced and not the camera's opinion of it.

The calibration refuses a take, loudly, when:

- fewer than four patches survive clipping (the exposure is wrong: re-film it);
- the patches do not get brighter from left to right (the chart is not framed the way it was
  drawn, or the screen region is wrong);
- the worst patch is out by more than 0.05 in relative luminance (the TV or the camera is doing
  something an affine fit cannot follow: check the picture mode).

A refusal is the right outcome in all three cases. It costs two minutes of re-filming and it
saves a number that would have been wrong.

### 5.3 The run itself

Start the recording, start the run, leave the room. Two kinds of run, both counted toward the
200 and both reported separately:

- **Marker events.** The marker clip from `eval/marker_clip.py` under a sham map. The cover has
  to be fully on before the marker step.
- **Real segment events.** A flagged interval in a real title, filter on.

The marker clip carries a reference patch in a corner that the cover leaves uncovered, flipping
between two close grays every 500 ms. That is a clock written on the screen, and it is how a
recording gets tied to media time without trusting either machine's idea of the hour. The patch
step is under the WCAG threshold and covers a small part of the screen, so the clip stays
non-hazardous and anyone can be in the room for a marker run.

### 5.4 The event file

The app posts what it did to the machine running the session, the same way the GATE 1 harness
does, because the device drops console output under load. Save that as the take's event file. An
occurrence with no matching log line is not an event, by `docs/EVAL_PLAN.md` section 8, and the
ingest excludes it and counts the exclusion.

---

## 6. The sham map, for real titles

A real title cannot be asked to flash on cue, and we are not going to make one flash. So for the
events that need a known moment, the title is published with a **sham map**: a flash map that
declares intervals which are not flashing at all, so the app covers a stretch of ordinary
picture.

Rules for a sham, all of them load bearing:

1. **A sham map is labelled a sham everywhere it appears.** In the file, in the take's event
   file, in `results/screen_level.json`, and in any sentence that quotes a number that came from
   one. `CLAUDE.md`: nothing mocked is shown as real.
2. **A sham is signed by the test key, never the release key.** It must not be possible for a
   sham to reach a household build.
3. **A sham never makes the app play something it would otherwise hide.** It only adds hides.
   That is the same rule the room settings live under.
4. **The filter stays on.** A sham changes what is covered, not whether covering happens.
5. **Real flagged intervals are covered as usual in the same take.** They are the real segment
   events. The sham exists to give the marker events a known moment, not to replace them.

The reason a sham is honest here: the thing under test is whether the cover is on the screen
before a known moment, and a cover does not know why it was asked to be there. The content
behind it is not part of the measurement.

---

## 7. File naming

One stem per take, four files:

```
media/screen_level/20261008_marker_t01_gray.mov
media/screen_level/20261008_marker_t01_chart.mov
media/screen_level/20261008_marker_t01_run.mov
media/screen_level/20261008_marker_t01_events.json
```

- `20261008` is the date the take was filmed, as YYYYMMDD.
- `marker` is the session: `marker` for the marker clip under a sham, `title` for a real title.
- `t01` is the take, counting from one within that date and session.
- The kind is one of `gray`, `chart`, `run`, `events`.

`eval/meter_ingest.py` groups files by stem. A take missing any of the four is listed as
incomplete and is not measured. Phones name files things like `IMG_4312.MOV`, so renaming is a
step of the session, not an afterthought: do it before you film the next take, while you still
know which is which.

---

## 8. What `make ingest-recordings` does

```
make ingest-recordings                       # media/screen_level -> results/screen_level.json
make ingest-recordings INGEST_ARGS="--recordings /some/other/dir"
```

It runs `eval/meter_ingest.py`, which for each complete take:

1. finds the screen region in the gray take, and refuses the take if it cannot;
2. runs the flicker check on the gray take, and excludes the take if it fails;
3. fits the exposure correction on the chart take, and excludes the take if the fit is refused;
4. reads the run take once, and gets three things from that one pass: the meter's flash counts,
   the luminance of the picture over time, and the luminance of the reference patch over time;
5. recovers the media clock from the patch flips, anchored to absolute media time by the app's
   own event log;
6. scores each declared interval: whether the recording covers it, whether the app logged it,
   when the cover was fully on, and whether any frame inside it rose above the covered state by
   more than that take's tolerance;
7. writes `results/screen_level.json`: leaks as a count out of N with a Wilson 95% interval,
   cover lead time as median, p95 and worst, and every exclusion counted beside the number it
   affects.

**With no recordings it writes nothing.** It prints what it is looking for and exits non-zero.
An absent file is honest; a file full of zeros would read as a real result in three weeks.

Two kinds of leak come out of this, and they are not the same thing:

- a **cover leak** is a frame inside a declared interval where the screen region is brighter
  than the covered state by more than the tolerance. It is the sensitive one: it fires on any
  light getting through, flashing or not;
- a **flash leak** is a stretch where the meter counted more flashes in a second than the spec
  allows. It is the one that matters for the claim, and it is the number the meter beside the TV
  shows.

Both are reported. Neither is allowed to stand in for the other.

---

## 9. What gets excluded, and what that costs

Every exclusion is counted and reported next to the number it affects, per
`docs/EVAL_PLAN.md` section 9:

- takes where the gray field fails the flicker check;
- takes where the screen region or the calibration is refused;
- occurrences that fail any of the four event conditions in `docs/EVAL_PLAN.md` section 8;
- events with no media clock, because the event file did not say where the recording started.

Events that overlap a buffering line, a seek or a rate change are **not** excluded. They are
reported as their own strata, because they are the interesting ones.

Plan for exclusions when budgeting the session. To end up with 200 events, film more than 200.

---

## 10. What the meter cannot tell you

Say these out loud when the numbers are written up.

- **Colour is not calibrated.** The step chart is neutral gray, so the fit corrects luminance and
  each channel's gain, and it cannot undo the camera's colour matrix. A red flash count from
  camera footage is an indication, not a calibrated measurement. Every report carries that
  warning in `quality.warnings`.
- **A camera is a sampler, and above a certain rate it reads high.** On simulated footage the
  meter read the rate back exactly for every trial up to
  <!--n results/meter_validation.json:published.exact_up_to_hz -->0<!--/n--> Hz. Above that it
  can be out by one. Across
  <!--n results/meter_validation.json:published.exact_rate_total -->0<!--/n--> flashing trials
  the worst it read high was
  <!--n results/meter_validation.json:published.worst_overcount_per_second -->0<!--/n-->
  flash a second and the worst it read low was
  <!--n results/meter_validation.json:published.worst_undercount_per_second -->0<!--/n-->.
  Reading high is the safe direction. Reading low is the one that would matter, and it did not
  happen in those trials.
- **Zero on a covered run is only as strong as the runs behind it.**
  <!--n results/meter_validation.json:published.covered_runs_with_a_leak -->0<!--/n--> of
  <!--n results/meter_validation.json:published.covered_runs -->0<!--/n--> simulated covered
  runs showed a leak, which is an upper bound of
  <!--n results/meter_validation.json:published.covered_leak_upper_95 -->0<!--/n--> at 95% by
  Wilson. That is a wide bound, and it is wide because seven runs is not many. The screen-level
  test is what narrows it.
- **An uncalibrated run is not publishable**, and the report says so in `publishable`. So is a
  run where the camera clipped, because a clipped camera reads bright states low, which can only
  make the meter under-count.
- **The clock from the reference patch gives rate and phase, not absolute media time.** Every
  flip looks like every other one. The absolute part comes from the app's log, and an event whose
  log cannot supply it is excluded rather than guessed.
- **None of this has met real hardware.** Until it has, the GATE 1 harness stays the authority on
  cover lead time, and this page is a plan rather than a record.

---

## 11. The short version, to take into the room

1. TV: game mode, motion smoothing off, no overscan, picture mode not dynamic.
2. Camera: on a tripod, whole screen plus some room in frame, focus and exposure locked, HDR off.
3. Film gray. Film the chart. Check the chart's bright patches are not flat white.
4. Start the recording, start the run, leave the room.
5. Rename the four files to the stem before the next take.
6. `make ingest-recordings`, and read what it refused as carefully as what it counted.
