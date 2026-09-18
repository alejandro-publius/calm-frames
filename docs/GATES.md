# Gates, checkpoints and kill rules

Every gate result and every kill rule that fires is logged here with the date and evidence.

## Status board

| Item | Due | Status |
|---|---|---|
| HUMAN CHECKPOINT A: supported machine | Thu Sep 17 (kill if none by Sat Sep 19) | **Passed** Sep 17: macOS 15.1.1 on Apple M1 |
| HUMAN CHECKPOINT F: outreach emails drafted and sent | Fri Sep 18 | Blocked: `docs/outreach-kit.md` not provided yet |
| VVD plays the renamed sample | Sat Sep 19 | **Done Sep 17**, two days early. Evidence in results/vvd_smoke.json |
| HUMAN CHECKPOINT B: stick on Vega OS 1.2, developer mode, USB | Mon Sep 21 (SDK 0.23 fallback after) | Waiting on the stick |
| Layering test (1.5) | When the stick is ready | **Harness built and tested.** Waiting on the stick. Steps below. |
| GATE 1: overlay timing, 48 of 50 covered 150 ms early (HUMAN CHECKPOINT E1) | Wed Sep 23 (Fri Sep 25 latest) | **Harness built and tested.** Waiting on the stick and on the calm-timing marker clip. |
| HUMAN CHECKPOINT C: self-filmed flashing footage | Thu Sep 24 | Waiting |
| GATE 2: 15 real flagged segments from 4 sources | Fri Sep 25 | Not started |
| HUMAN CHECKPOINT D: AWS Paid plan, $20 alarm, credits requested | Before the first deploy | Waiting |
| GATE 3: end to end on the stick | Fri Oct 2 | Not started |
| Upstream pull request opened | Mon Oct 12 | Not started |
| HUMAN CHECKPOINT E2: 200 screen-level events | Oct 8 to 13 | Not started |
| Outreach validation in docs/VALIDATION.md | Fri Oct 16 | Not started |
| Feature freeze | Sun Oct 18 | |
| Final checks | Wed Oct 21 | |
| HUMAN CHECKPOINT G: submit | Thu Oct 22 | |

## Log

### 2026-09-17: HUMAN CHECKPOINT A passed
Detected macOS 15.1.1 (24B91) on an Apple M1 (arm64) with 16 GB memory and 1.2 TiB free disk. Vega SDK 0.24 supports macOS on Apple silicon. Vega CLI 1.3.4 and SDK 0.24.9914 installed cleanly the same morning. Details in docs/ENVIRONMENT.md.

### 2026-09-17: the stripped app plays a Blender title on the Vega Virtual Device
Target was Sat Sep 19, reached Wed Sep 17. Recorded by `python3 eval/vvd_smoke.py`, which writes results/vvd_smoke.json.

| What | Value |
|---|---|
| Package | `io.github.alejandropublius.calmframes`, debug build for aarch64 |
| Device | OS 1.2 (TV Ship/101520710), aarch64, virtual |
| Title | Cosmos Laundromat, a Blender open movie, over HLS from the Amazon reference assets CDN |
| Playback started events | <!--n results/vvd_smoke.json:playback_started_events -->2<!--/n--> |
| Media play calls | 4 |
| Segment fetches during 40 s of play | <!--n results/vvd_smoke.json:segment_fetches_during_play -->8<!--/n--> |
| Streaming errors | 0 |
| Crash lines | 0 |
| Peak memory | 353 MB (the phase 4.10 target is under 400 MiB in the foreground, on the stick, not here) |

How it was driven: the Vega CLI has no command for pressing remote buttons, so `eval/vvd_control.py` sends key events through QEMU's QMP socket. From the home screen the sequence is down, down, select to open a title, then select to play.

Honest notes on this milestone:
- Playback is not reliable yet on the virtual device. Of four runs today: two played cleanly, one reached the player screen and then failed with `Category: UNKNOWN, Position: 0.084` on the same HLS stream, and one never started playback because the select press did not land on the play button (the smoke test now watches the log and presses again, up to three times). Worth watching once the stick arrives, since the stick is what the gates actually measure.
- Screenshots through QMP come back black, because the app renders through a GPU layer the capture does not see. Playback evidence therefore comes from device logs, not from pictures. Phase 4.5 needs a way to check our own screens for flashing, so this has to be solved before then.
- The sample's own catalog is what played here. Calm Frames has no catalog of its own until phase 3.

### 2026-09-17: the layering test and the GATE 1 harness are built

Both runs exist in the app and are covered by tests. What is still missing for GATE 1 is the marker clip, which comes from calm-timing in the kits.

**How to start a run on the stick**

The app has two buttons at the bottom of the Settings screen, "Layering test" and "Timing harness". Open Settings from the permanent drawer on the left, scroll to the bottom and press select. I could not confirm that menu path myself, because the virtual device renders on a GPU layer that screenshots come back black from, and driving the menus blind did not land on the buttons. With the stick in front of you and the screen visible this is a few button presses.

A run can also be started without menus, by putting `calm-frames-harness.json` in the app's data directory, which is how a take gets started in front of a camera without navigating. The files are in `eval/harness_runs/` with instructions. One caution: on OS 1.2 `vega device copy-to` cannot write into another package's sandbox (it fails with "Permission denied", and the path the sample README gives, `/home/app_user/packages/<id>/data`, does not exist), so that route needs another way to place the file. The Settings buttons work regardless.

Use a debug package. Release builds strip `console.log`.

**What the layering test shows (phase 1.5)**

A full-screen cover toggles every 5 seconds over a playing title. Turn captions on in the player first. Pass: the picture is fully hidden every time, captions stay visible above the cover, audio never stops, no crash. Film it, and record the result here.

**What the timing harness does (GATE 1)**

It drives the cover from a schedule with a 500 ms guard band, leaving the reference patch uncovered, and writes one `CALM_TIMING` line per event:

```
vega device start-log-stream | grep CALM_TIMING
```

Each line pairs media time with wall-clock time, so a 240 fps recording can be lined up against what the app believed it was doing. The cover runs on a wall clock re-synced to media time at every timeupdate, rather than reacting to timeupdate, which is what lets it be on before the marker.

**Not a GATE 1 run yet.** The committed schedule is a placeholder: twenty one-second hides six seconds apart, over a title that has no markers at those times. It exercises the scheduler, the cover and the logging, and it cannot produce a number. Every run says which schedule it used in its `harness-start` line, and the placeholder calls itself `placeholder-not-a-gate-1-run`. Replace the segments with the schedule calm-timing emits for the marker clip and it becomes a real run.

**A bug the tests caught before any filming**

The first version restarted its run clock on every re-render, so the cover turned on and then straight back off. It would have wasted a filming session. The schedule is now read through a ref, the run clock survives re-renders, and putting the bug back turns the suite red.

### 2026-09-17, evening: a retracted number, and what it taught us

**An earlier version of this entry said the GATE 1 rehearsal covered 20 of 20 markers in time, with a worst lead of 449 ms. That number was wrong and it is withdrawn.**

What happened. The run it came from never played. The player reported positions between 0.17 s and <!--n results/gate1_rehearsal_vvd.json:furthest_position_the_player_reported_ms -->259<!--/n--> ms and got no further. Meanwhile the cover scheduler, which runs on a wall clock by design, kept advancing its own estimate of where the playhead was and fired all 20 covers on time against that estimate. The analysis then compared those covers against the schedule and found perfect agreement, because both sides were the same clock. It was arithmetic wearing the clothes of a measurement.

It was caught by writing a stricter second script. `eval/gate1_software.py` needs a position report from the player on both sides of a marker before it will place that marker in wall-clock time, and it returned zero usable trials out of 150 across three passes. That disagreement with a script reporting a perfect score is what exposed the problem.

`eval/gate1_rehearsal.py` now refuses the same way: a lead time is counted only when the player actually reached that part of the clip. Re-run against the same events, it reports <!--n results/gate1_rehearsal_vvd.json:markers_counted -->0<!--/n--> counted and <!--n results/gate1_rehearsal_vvd.json:markers_not_counted -->20<!--/n--> not counted, with the reason on each one.

**So there was no lead time number from that run, and the twenty markers in it all failed the rule.** Getting one needed playback that actually ran, which the virtual device would not manage on the original clip.

### The re-run, same evening

The clip was packed so the markers come sooner, and the measurement ran again across 22 app launches. That worked: results/gate1_software_vvd.json records <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n--> counted trials, <!--n results/gate1_software_vvd.json:in_time -->48<!--/n--> of them covered in time, a median lead of <!--n results/gate1_software_vvd.json:lead_ms.median -->488.4<!--/n--> ms against a <!--n results/gate1_software_vvd.json:guard_band_ms -->500<!--/n--> ms guard band, and <!--n results/gate1_software_vvd.json:trials_dropped_no_timeupdate -->4<!--/n--> dropped for want of a position report plus <!--n results/gate1_software_vvd.json:trials_dropped_playback_stalled -->2<!--/n--> dropped for stalling mid-trial. This is software-level and stays labelled that way.

**One cover was late, and that is the useful part.** The worst lead is <!--n results/gate1_software_vvd.json:worst_lead_ms -->-86<!--/n--> ms, meaning the cover went on after the marker had already started. Every other pass fired at the first position report past the guard band, about 6.5 s in. In that one the report at 6.744 s was skipped and the cover fired at 7.079 s. The scheduler re-anchors to media time on every report and re-checks every 50 ms, so a 335 ms gap is the JavaScript thread being unavailable, not a scheduling error. The conclusion is that the guard band has to be wider than the worst pause of that thread, and no one has measured that pause on hardware. GATE 1 now has to report it.

**A second near miss, caught before it was published.** The first attempt to rebuild this summary from its own event archive got 54 trials rather than 49, including a lead of 13.3 s, because the passes were split on each `harness-start` event. Two passes had opened with a batch the previous app instance posted late, so that split put two launches in one pass and interpolated a media position across them. The right split is the per-pass event counts the summary already records. Nothing about the wrong answer looked wrong. `eval/verify_gate1_archive.py` now does the rebuild in CI and fails on any disagreement, and it was checked by breaking it five ways.

GATE 1 on the stick does not depend on any of this, because a stick plays video properly and a camera watches the screen.

The lesson is worth keeping: a scheduler measured against its own clock will always look perfect. Any timing number has to be anchored to something the player or the screen reported, not to what the app believed.

What the same run measured about the player, in results/vvd_timeupdate_stats.json. Neither figure is documented by Amazon, which is why the scheduler runs on a wall clock re-synced to media time rather than reacting to timeupdate:

| What | Value |
|---|---|
| timeupdate events in the run | <!--n results/vvd_timeupdate_stats.json:timeupdate.count -->10<!--/n--> |
| Gap between them, median | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms |
| Gap between them, shortest | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.min -->75<!--/n--> ms |
| Gap between them, longest | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms |
| Smallest step currentTime reported | <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms |
| Worst gap between the app's estimate and the player | <!--n results/vvd_timeupdate_stats.json:worst_wall_clock_drift_ms -->2756<!--/n--> ms |

Read that carefully, because it is the argument for the design. In this run the player went quiet for over five seconds between position reports while the clip kept playing. A cover that waited for timeupdate would have been that late. The wall-clock scheduler kept covering through the gap, and the drift figure is the price: with no position report for five seconds, the estimate had run nearly three seconds away from the player by the time one arrived. That is why anything which makes the playhead uncertain, including a stall, hides the picture at once rather than trusting the estimate.

The cadence is not stable on this device. The same clip played smoothly earlier in the evening and choppily here, so treat these as virtual device numbers only. The stick is what GATE 1 measures.

## 2026-09-17, night: what the late cover actually was

The run on Sep 17 left one cover going on 86 ms after its marker, and the
guess written down at the time was that the JavaScript thread had been
unavailable for about a third of a second. That was a guess. Nothing measured
the thread.

The scheduler now records the gap between two runs of its own tick. It asks
every 50 ms whether the cover should be on, so a gap far past that is the
thread being away rather than the schedule being wrong.

The first run with that instrument is not a characterization of anything, and
it is kept at `results/under_load/` rather than in `results/` for that reason.
The machine was carrying a load average of 218 at the time, from eight working
agents, two ingest jobs and four verify jobs, on top of the virtual device
itself. Under that:

- the worst gap between two scheduler ticks was 72.8 seconds;
- seven passes out of ten could not start the app at all;
- nine trials came back where fifty were asked for;
- the worst cover landed 426 ms late in media time, against 86 ms on the
  quiet machine.

**That last line is the useful one.** The lateness scales with how starved the
thread is. A quiet machine gave one cover 86 ms late; a machine at load 218
gave one 426 ms late and lost most of its runs entirely. That is the
relationship the thread explanation predicts, and it is the first direct
evidence for it rather than an inference from a gap in the timestamps.

Two things follow, and the second matters more.

**The 86 ms cover was a host artifact, not a design fault.** The schedule fires
correctly and the thread was not there to run it. Nothing in `coverSchedule.ts`
or `mediaClock.ts` accounts for it.

**A Fire TV stick can be a loaded machine too.** A stick doing a background
download, an app update, or simply running a heavier title has less headroom
than this Mac does when it is quiet. So "it was only host load" is not a reason
to stop worrying. It is a reason to find out what the worst tick gap is on the
real device under realistic conditions, and to set the guard band above it.
That measurement is now part of stick day.

The citable software level result is still the quiet-machine run in
`results/gate1_software_vvd.json`, which predates the instrument and so has no
tick gap in it. A clean re-run with the instrument, on an idle machine, is
still owed and is listed in docs/STATUS.md.
