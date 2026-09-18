# Shot manifest

Every shot [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md) needs, how it is captured, and what it waits on. Shot numbers `S01` to `S18` are the same in both files.

The point of this file is to get everything that does not need hardware captured before the stick arrives, so that on filming day, Oct 19 to 20, the only thing left is pointing a camera at a television.

**Nothing in this file has been captured yet.** The Status column says so for every row, and it is updated as each one lands.

---

## 1. The capture problem, stated once

The Vega Virtual Device's screen cannot be captured on this machine. macOS screen grabs and QEMU's `screendump` both come back black, because the app draws on a GPU layer that neither capture sees. This is written up in `docs/ENVIRONMENT.md`, in `app/src/calmframes/uiCapture.ts`, in friction log entry 9 and in feature request 2. There is no workaround and none is coming before the deadline.

So there is no route that turns the virtual device into a picture. Anything that has to show the app on a screen is filmed off a real panel, and that waits on the stick. Everything else is captured from this machine.

## 2. The four routes

| Route | What it is | Waits on |
|---|---|---|
| **A. Camera on the panel** | A phone or camera pointed at a television with the stick in it. The only way to show the app running. | The stick, a television, and the meter calibration for S04 and S06 |
| **B. The app's own capture path** | `app/src/calmframes/uiCapture.ts`. The app reports the colours it paints, screen by screen and transition by transition. **Not a photograph.** It never appears in the cut | Nothing for the offline leg. The Vega Virtual Device for the on-device leg |
| **C. Desktop capture** | A screen recording of a terminal, a browser or an editor on this machine | Nothing |
| **D. Generated from results** | A figure drawn from a committed results file or a signed flash map | Nothing |

### What route B is for, and what it is not for

Route B exists so that every screen the video needs can be checked before anyone films it: that it is the right screen, that it paints the colours it is supposed to, and that the transition between two of them does not itself flash. That is the whole job.

It is **not** a screenshot and it must never be cut into the video or into a still. What it produces is a list of painted colours per screen, which `app/tools/ui_flashmap.mjs` turns into blocks of colour so flashmap can measure the transitions. A viewer shown one of those would reasonably think they were looking at the app. They would not be. That is the "nothing mocked is shown as real" rule, and route B is the most tempting way to break it.

Route B has two legs:

- **Offline leg.** `npm run ui:capture` in `app/` renders every screen in `ALL_UI_FRAMES` (`app/src/calmframes/uiFrames.ts`) with the real components and writes `app/build/ui-capture/ui-frames.json`. No device is involved, so this can run any time the tree is quiet. It answers "does this screen exist and paint what it says it paints".
- **On-device leg.** The app running on the virtual device posts its own timeline back to the machine that started it, through `postUiCapture`. This is the one that proves the real app on the real OS visited those states in that order. **It needs the virtual device, which is busy.** Do not start, stop or use the device until the main session says it is free.

## 3. The manifest

`Route` is from the table above. `Waits on` is what stops it being captured today.

| Shot | Beat | What | Route | Waits on | Where it comes from | Lands in | Status |
|---|---|---|---|---|---|---|---|
| **S01** | 1 | The stick in the television, the app's home screen on the panel, a terminal running `vega device info` in the same frame | A + C in one frame | Stick | Camera. The terminal is in shot, not composited | `media/video/raw/S01_*.mov` | not captured |
| **S02** | 2 | Close on the kid mode row, a hand on the remote, no faces | A | Stick, consent | Camera | `media/video/raw/S02_*.mov` | not captured |
| **S03** | 3 | The countdown card, its own countdown running to zero | A | Stick, a verified title with a flagged span | Camera | `media/video/raw/S03_*.mov` | not captured |
| **S04** | 4 | The covered picture with captions running, the meter beside the television at 0, sound audible, one unbroken take | A | Stick, meter calibration | Camera, with `eval/meter.py run` live on a second screen inside the frame | `media/video/raw/S04_*.mov` | not captured |
| **S05** | 4 | The luminance trace for the same seconds, flagged span marked | D | Nothing | `eval/plots.py` over the demo title, with the flagged span drawn from its signed map | `results/plots/demo_title_trace.png` | not captured |
| **S06** | 5 | The Alexa skip landing inside the flagged part, still covered, meter still 0 | A | Stick, meter calibration | Camera, same rig as S04 | `media/video/raw/S06_*.mov` | not captured |
| **S07** | 6 | The parent area PIN entry | A | Stick | Camera. Use a throwaway PIN for the take, not the one in the release notes | `media/video/raw/S07_*.mov` | not captured |
| **S08** | 6 | Household settings, and the hidden count going up when the room changes | A | Stick, a title whose count actually moves | Camera | `media/video/raw/S08_*.mov` | not captured |
| **S09** | 7 | A card press, a D-pad seek and a voice command, same title, no reload | A | Stick | Camera | `media/video/raw/S09_*.mov` | not captured |
| **S10** | 8 | A title going through the pipeline | C | Nothing | Terminal recording of the real pipeline run | `media/video/raw/S10_pipeline.mov` | not captured |
| **S11** | 8 | `verify` refusing a second title, reason printed | C | Nothing | Terminal recording. Use a title verify really refuses | `media/video/raw/S11_verify_refuses.mov` | not captured |
| **S12** | 8 | The kid mode row with the refused title absent | A | Stick | Camera | `media/video/raw/S12_*.mov` | not captured |
| **S13** | 9 | `python -m flashmap check` exiting 1 with its segment list | C | Nothing | Terminal recording | `media/video/raw/S13_flashmap_check.mov` | not captured |
| **S14** | 9 | A pull request adding a flashing asset, our Action red, job summary open | C | A scratch repository with the workflow in it | Browser recording | `media/video/raw/S14_action_red.mov` | not captured |
| **S15** | 10 | The hook diff, still, readable in one look | C | Nothing | Screen capture of `docs/INTEGRATION_DIFF.md` or the diff itself in an editor | `media/video/raw/S15_hook_diff.png` | not captured |
| **S16** | 11 | The README results tables, scrolled to "Not measured yet" | C | Nothing | Screen recording of the rendered README | `media/video/raw/S16_results_tables.mov` | not captured |
| **S17** | 11 | `python eval/readme_sync.py --check` passing | C | Nothing | Terminal recording | `media/video/raw/S17_readme_sync.mov` | not captured |
| **S18** | 12 | The television, calm, playing, end card over it | A | Stick | Camera | `media/video/raw/S18_*.mov` | not captured |

**Ten shots wait on the stick. Eight do not.** The eight are S05, S10, S11, S13, S14, S15, S16 and S17, all on route C or D. S14 needs a scratch repository set up first. The other seven are ready to capture as soon as a lane has time.

`media/` is gitignored, so raw footage and the cut never enter the repository. `results/plots/` is tracked, so S05 is committed along with everything else that gets published.

## 4. The rehearsal captures, which are not shots

These do not appear in the video. They are how every screen is checked before a camera is pointed at it, so that filming day finds no surprises.

| # | What | Route | Waits on | Command |
|---|---|---|---|---|
| **R01** | Every screen in `ALL_UI_FRAMES` renders, and paints the colours it declares | B, offline leg | Nothing, but the tree has to be quiet: this writes `app/build/ui-capture/` and another lane's jest run would clash | `cd app && npm run ui:capture` |
| **R02** | No screen or transition in that list breaks the flash thresholds | B, offline leg | R01 | `cd app && npm run ui:flashmap` |
| **R03** | The real app on the real OS visits those states in that order | B, on-device leg | **The virtual device, which is busy.** Ask the main session first | A device session with a capture sink, the same way the timing log is posted |
| **R04** | The meter reads zero over a covered span and non-zero either side | A, rehearsed | Stick, meter calibration | `eval/meter.py chart`, film it, `eval/meter.py calibrate`, then `eval/meter.py run` |

The screens the video actually needs, by their names in `ALL_UI_FRAMES`:

| Shot | Screen name |
|---|---|
| S02, S12 | `kid-home`, `kid-home-focused` |
| S03 | `player-clear-countdown` |
| S04, S06 | `player-covered-covering`, then `player-clear-after` on the tail |
| S07 | `parent-area-locked` |
| S08 | `parent-area-open` |
| S09 | `title-details`, plus the player states above |

R01 covers all of them in one run. Anything in that list that does not render, or renders the wrong thing, is a problem to find now rather than with a camera in hand.

## 5. Order of work

**Now, needs nothing.** S05, S10, S11, S13, S15, S16, S17, and R01 and R02 when the tree is quiet.

**Now, needs one setup step.** S14: a scratch repository with `flashmap/examples/flash-check.yml` in it and a pull request that adds a flashing asset. Check the job summary renders no thumbnail of the asset before recording, and do not open the pull request's Files tab on camera, because GitHub previews images there.

**When the virtual device is free.** R03. Ask the main session first. Nothing in the video depends on it, so it is a confidence check rather than a blocker.

**Stick day, about Sep 20.** R04, the meter calibration. Without it the meter in S04 and S06 is uncalibrated and those two shots do not stand up.

**Filming day, Oct 19 to 20.** The ten camera shots, in this order so the rig moves as little as possible: S01, then S02, S03, S04, S06 as one continuous session with the meter in frame, then S07, S08, S09, S12, then S18 last while the television is already calm.

## 6. Hard rules for this lane

- **Never cut a route B render into the video, or into a still, or into the README.** It is a block of colour, not the app. Label it as a frame record wherever it appears in a document.
- **Never open a `HAZARD_` file in a player** to find a shot. S05 is a trace drawn by a decoder, and that is the only way any of that material is looked at.
- **Never present a black virtual-device screen grab as the app.** The capture is black because the capture is broken, and a viewer cannot tell the difference between that and a cover working.
- **Film only inside our own app.** The Fire TV home screen shows other companies' app tiles.
- **`vega device list` appears in no shot.** It crashes. `vega device info` is the command in S01.
