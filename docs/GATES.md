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
| Playback started events | 2 |
| Media play calls | 4 |
| Segment fetches during 40 s of play | 8 |
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
