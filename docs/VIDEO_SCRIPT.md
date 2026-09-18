# Demo video script

**Target length: 2:53.** Judges do not have to watch past 3:00, so everything that matters is in the first 60 seconds and nothing lands after 2:53. That leaves seven seconds of headroom for a slow read.

**The one sentence, on screen and in the voiceover, and never anything else:** "Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device." Never "prevents seizures". Never "seizure-proof".

**How this file is laid out.** The timing table first, so the whole shape is visible in one look. Then the rules that override the shot list. Then the script beat by beat, where each beat names the shots it needs. Then the shot list itself, numbered `S01` to `S18`. [`docs/SHOT_MANIFEST.md`](SHOT_MANIFEST.md) carries the same numbers and says how each shot is captured and what it waits on.

---

## Timing at a glance

Read at about 130 words a minute, which is slower than the 150 the script is budgeted for. The word counts are the voiceover only.

| # | Beat | In | Out | Length | Words | Shots |
|---|---|---|---|---|---|---|
| 1 | The stick, running, on a real television | 0:00 | 0:10 | 10 s | 13 | S01 |
| 2 | Who this is for | 0:10 | 0:22 | 12 s | 31 | S02 |
| 3 | The countdown card | 0:22 | 0:34 | 12 s | 29 | S03 |
| 4 | The calm hold, the meter at zero, the trace | 0:34 | 0:58 | 24 s | 51 | S04, S05 |
| 5 | The Alexa skip that lands inside it | 0:58 | 1:12 | 14 s | 29 | S06 |
| 6 | Her dad set this up | 1:12 | 1:28 | 16 s | 39 | S07, S08 |
| 7 | Three ways in, one flow | 1:28 | 1:38 | 10 s | 17 | S09 |
| 8 | Verified before it can play | 1:38 | 1:56 | 18 s | 41 | S10, S11, S12 |
| 9 | The analyzer, and the Action failing a pull request | 1:56 | 2:14 | 18 s | 35 | S13, S14 |
| 10 | Any Vega app can add it | 2:14 | 2:26 | 12 s | 25 | S15 |
| 11 | The results table, including the empty rows | 2:26 | 2:44 | 18 s | 45 | S16, S17 |
| 12 | Close | 2:44 | 2:53 | 9 s | 21 | S18 |
| | **Total** | | | **2:53** | **376** | |

376 words over 173 seconds is 130 a minute. If a beat runs long in the read, the slack is in beats 7 and 12, in that order. Beat 4 is the one beat that must never be trimmed.

Beat 1 has two voiceover lines, one for the stick and one for the virtual device. They are both 13 words, so the timing is the same whichever device the video is shot on.

**Everything the first 60 seconds has to contain, and where it is:** the countdown card (beat 3, 0:22), the calm hold with captions and sound still going (beat 4, 0:34), the camera meter reading zero (beat 4, 0:34), and the luminance trace of what was hidden (beat 4, from about 0:48). The last of them is on screen at 0:58, with two seconds to spare.

---

## The device the video shows: the hardest Stage One line

This is the one Stage One requirement that no amount of code satisfies, so it gets its own section.

The rules exempt Fire TV from the runtime technology hook that Alexa+, Bee and Ring have. What they ask instead is about this video. Quoted from the rules page, Submission Requirements, and copied into [`docs/RUBRIC.md`](RUBRIC.md) section 2.2:

> Fire TV: Any framework or language is acceptable (React Native, Android/Kotlin/Java, web technologies, etc.). The requirement is that the project runs on Fire OS or Vega OS. The demo video must show the project running on an actual Fire TV device or the Fire TV/Vega simulator.

**The simulator counts.** So this video does not hang on the stick arriving. Every shot that has to show the app running can be filmed against the Vega Virtual Device, and the stick is an upgrade rather than a dependency.

### The constraint that shapes every app shot

The virtual device's screen cannot be captured on this machine. macOS screen grabs and QEMU's `screendump` both come back black, because the app draws on a GPU layer that neither capture sees. There is no workaround and none is coming before the deadline. So there is no route that turns the virtual device into a clean screen recording, and every shot of the app on the virtual device has to be **a camera pointed at the monitor the virtual device window is on**, exactly the way the stick shots are a camera pointed at a television.

The app's own capture path, `app/src/calmframes/uiCapture.ts`, is the other thing that exists, and it is not a second route for these shots. It records the colours the app paints, screen by screen. It is a frame record, not a picture of a screen, and it never appears in this video. It is how the screens get checked before anyone films them. [`docs/SHOT_MANIFEST.md`](SHOT_MANIFEST.md) says this twice, because cutting one of those renders into the video would be showing something mocked as real.

### The open question, which has to be settled before this plan is trusted

**Nobody has yet pointed a camera at the virtual device window and confirmed the app is visible in it.** The capture APIs miss the GPU layer. Whether a human eye and a camera see the app on that monitor is a different question, and it has not been checked. If the window is visible, the plan below works. If it is black to a camera as well, then every app shot waits on the stick after all, and that changes the schedule rather than the script.

It takes two minutes to settle: put the app on the virtual device, point a phone at the monitor, and look. **Do it the moment the virtual device is free**, because everything below depends on the answer, and finding out on Oct 19 would be the worst possible time.

### Which device each shot uses

| | On the stick, if it is here | On the virtual device, if it is not |
|---|---|---|
| **S01**, the opening | The stick in the back of a television, `vega device info` beside it | The virtual device window on a monitor, `vega device info` beside it, naming the device it prints |
| **S02, S03, S07, S08, S09, S12, S18**, the app screens | Camera on the television | Camera on the monitor |
| **S04, S06**, the calm hold and the Alexa skip | Camera on the television, with the meter reading the panel | Camera on the monitor, with the meter reading the monitor. See the note below |
| **S05, S10, S11, S13, S14, S15, S16, S17** | Captured from this machine. The device makes no difference | Same |

**If the video is shot on the virtual device, say so on screen.** One plain line, `Vega Virtual Device`, in the corner of the first app shot. The rules allow the simulator, so there is nothing to hide, and a viewer who works out for themselves that it is not a television trusts everything else less.

**The meter, in S04 and S06, is the one place the two plans are not equal.** The meter is calibrated by filming a step chart shown on the same screen with the same camera, and a calibration only holds for the surface it was filmed on. On a television that is one step. On the virtual device window it is an open question whether a chart shown by another application on that monitor calibrates the same surface the app draws through, because the whole reason capture fails is that the app draws through a different path. Two ways out, in order of preference: film S04 and S06 on the stick, or have the app show the step chart itself so the chart and the cover come off the same layer. The second is a question for the app lane, not something to decide with a camera in hand. **If neither is possible, the meter in those shots is labelled uncalibrated on screen, and the beat still works, because a meter that moves before and after a covered span and sits at zero through it is an argument even without a calibrated scale.**

---

## Before filming: read this

### Safety, which overrides the shot list

1. **Nothing that flashes appears in this video, not for a single frame.** Where a flash has to be shown, it is a luminance trace on a chart, never the footage. This applies to the raw material too: nobody opens a `HAZARD_` file to find a shot. The only thing that ever sees those pixels is a decoder.
2. **Whoever films any flashing footage is not photosensitive and does not look at the lights.** Everyone in frame has given consent, including hands.
3. The final cut is measured before it is uploaded:

       eval/check_video.sh final_video.mp4

   It runs flashmap over the file, refuses anything over three minutes, and writes `results/video_check.json`. Exit 0 or the video does not go up. Exit 2 means flashmap could not tell, and that is a failure too. Commit the record next to the link. This is a hard gate, not a nice-to-have.

### Rights and credits

- Film **only inside our own app**. The Fire TV home screen shows other companies' app tiles, so it never appears.
- Cut every Blender logo. They are excluded from the Blender Studio licences.
- Mute or credit any film music.
- If Tears of Steel appears, its credit scroll stays.
- The Hell's Angels (1930) title card stays out of the video entirely.
- DVIDS material carries its non-endorsement notice. NASA material follows NASA's credit-line guidance.

### One deviation from the build plan, on purpose

The VIDEO RULES in `docs/BUILD_PROMPT.md` say to open with a terminal where `vega device list` shows the stick connected. **That command is not in this script and must not be filmed.** It crashes with `Cannot read properties of undefined (reading 'trim')` while a device is connected, which is friction log entry 6 and feature request 4. `vega device info` answers the same question and works, so it is the one that appears. The crash is worth reporting and it is reported in writing, where a reader can see the exact output. It is not worth a viewer's first ten seconds.

### What must exist before this can be filmed

| Needed | Where it stands |
|---|---|
| A device the app runs on: the stick on Vega OS 1.2 in developer mode, **or** the Vega Virtual Device | The virtual device works today. The stick is an upgrade |
| A camera view of that device's screen | Confirmed for a television. **Not yet confirmed for the virtual device window**, see the section above |
| **Kid mode reachable in the app, not only in tests** | **Blocked.** `app/src/screens/PlayerScreen.tsx` reads `route.params.guarded` and nothing in `app/src` sets it, and `KidHomeScreen` and `ParentAreaScreen` are imported only by tests. So the guard never engages for a user in the app as committed. Found by mock judge 1, written up in [`docs/MOCK_JUDGE_1.md`](MOCK_JUDGE_1.md). **Nine of the ten camera shots cannot be filmed until the app lane wires this up.** It is the single biggest thing standing between this script and a video |
| The countdown card, the cover, the parent area behind a PIN | Built and tested. Not yet reachable from the app, see the row above |
| The camera-fed meter beside the screen | `eval/meter.py` is built. It needs a calibration filmed on the same screen, which is part of stick day |
| At least one verified title with a real flagged segment in it | The pipeline produces these. Pick one with a clean calm moment either side of the flagged span |
| The drop-in hook, so there is a diff to show | [`docs/INTEGRATION_DIFF.md`](INTEGRATION_DIFF.md) |
| A pull request in a scratch repository that the Action fails | Can be made any time from `flashmap/examples/flash-check.yml` |

### Numbers on screen

Every number that appears comes from `results/` and matches the README. There are only two in this cut, both marked in this file, so `python eval/readme_sync.py --check` covers them.

**There is no screen-level cover lead time**, and none appears in this video. The one run that claimed one was withdrawn. The software-level figure that exists now is not said out loud either, because a viewer cannot be expected to hold the difference in their head. The voiceover says what is measured and what is not, and does not imply a timing figure we do not have.

---

## The script

Times are cumulative. Voiceover is the middle column read aloud. On-screen text is what is burned in.

### Beat 1. 0:00 to 0:10, the real thing, running

| | |
|---|---|
| **Shots** | S01 |
| **Picture** | One continuous shot, no cut. The device running the app and a terminal beside it in the same frame. On the stick: the stick in the back of a television, the app's own home screen on the panel. On the virtual device: the device window on a monitor with the app's home screen in it. Either way, in the terminal, type and run `vega device info`. Let its output sit for a beat. |
| **Voiceover, on the stick** | "This is a Fire TV stick, running our app, on a real television." |
| **Voiceover, on the virtual device** | "This is our app, running on Vega OS, on the Vega Virtual Device." |
| **On screen** | Nothing burned in on the stick. On the virtual device, `Vega Virtual Device` in a corner, held through this shot and the next. |
| **Note** | Ten seconds is enough for one command to be typed and answer. Do not add a second command. If the shell is slow, type the command before the take starts and press return on the first frame. `vega device info` prints the device it is talking to, so the shot proves which one this is without the voiceover having to insist. |

### Beat 2. 0:10 to 0:22, who this is for

| | |
|---|---|
| **Shots** | S02 |
| **Picture** | Close on the television. The app's kid mode row, a child's hand on the remote. Nobody's face. |
| **Voiceover** | "Maya is twelve. She has photosensitive epilepsy. Tonight she is at a sleepover, picking a film, and no adult is going to watch it first to check what is in it." |
| **On screen** | `Maya is a composite persona. Not a real person.` Bottom left, plain text, held for the whole beat. |
| **Note** | The persona label is not optional and it is not small print. It stays legible on a phone screen: white on a dark plate, at least a twentieth of the frame height. Maya is also named as a composite persona in the Devpost description, so the label and the text agree. |

### Beat 3. 0:22 to 0:34, the countdown card

| | |
|---|---|
| **Shots** | S03 |
| **Picture** | Maya presses play. The countdown card appears on the television: the app saying, ahead of time, that a flagged part is coming and what it is about to do about it. |
| **Voiceover** | "Every frame of this film was checked before it could appear here. When a flagged part is coming, the app says so first, and says what it will do." |
| **On screen** | Nothing. The card is the text. |
| **Note** | Let the card's own countdown run. Cutting away before it reaches zero throws away the one thing the shot is for. |

### Beat 4. 0:34 to 0:58, the calm hold, the meter at zero, and the trace

**This is the shot the whole video exists for. Film it more than once and keep the best take.**

| | |
|---|---|
| **Shots** | S04, with S05 composited into a corner from about 0:48 |
| **Picture** | One unbroken shot, no cut, of three things in the same frame: the television with the picture covered and the captions still running across it; a small meter beside the television, fed by the camera looking at the panel, reading 0; and, from about 0:48, the luminance trace for those same seconds composited into a corner with the flagged span marked. The sound is audible throughout. |
| **Voiceover** | "The picture is hidden. The sound keeps going, the captions keep going, and the meter beside the television, which is reading the panel itself, stays at zero. What it is hiding is this." (beat, the trace fills the corner) "A luminance trace, not the footage. Nobody has to look at the flashes to know they were there." |
| **On screen** | `Luminance trace. The flashing itself is never shown.` next to the trace, for as long as the trace is up. |
| **Note** | The meter has to be visibly live: let it move before and after the covered span so it is obviously not a still image. Pick a title where the captions carry real dialogue through the covered seconds, because captions reading over a black picture is the argument. If the camera meter is not calibrated, this shot cannot be faked and the video waits. |

### Beat 5. 0:58 to 1:12, the seek that would have landed inside it

| | |
|---|---|
| **Shots** | S06 |
| **Picture** | Same take if possible. Maya says an Alexa skip-forward command that would put the playhead inside the flagged part. The picture stays covered. The meter stays at 0. |
| **Voiceover** | "Maya asks Alexa to skip forward, and it lands inside a flagged part. Voice, the remote and the cards all go through one seek path: cover first, seek second." |
| **On screen** | `Voice, D-pad and cards: one seek path` |
| **Note** | This is the strongest single second in the video, because it is the failure mode a reviewer would expect to find. Get it clean. Work out the target time before the take so the skip really does land inside the flagged span, and say so on screen only if the take makes it obvious. |

### Beat 6. 1:12 to 1:28, her dad set this up

| | |
|---|---|
| **Shots** | S07, S08 |
| **Picture** | Cut to the parent area. PIN entry, then the household settings: the preset, the television diagonal, the seat distance. Change the room size and show the number of hidden segments for this title go **up**. |
| **Voiceover** | "Her dad set this up behind a PIN: how strict, how big the television is, how far away she sits. A household setting can add hides. It cannot take any away, and it cannot go below the published thresholds." |
| **On screen** | `Household settings can only make it stricter.` |
| **Note** | Showing the count go up rather than down is the whole point of the shot. If the demo title's count does not move, pick one where it does, and find that out before the day rather than on it. Do not film the real demo PIN being typed if that PIN ships in the release notes: cover the keypad or use a throwaway PIN for the take. |

### Beat 7. 1:28 to 1:38, three ways in, one flow

| | |
|---|---|
| **Shots** | S09 |
| **Picture** | Quick, unhurried: a card press, a D-pad seek, a voice command. Same title, same protection, no reload between them. |
| **Voiceover** | "Cards, the remote and voice are one flow, on the same title, with no reload between them." |
| **On screen** | Nothing. |
| **Note** | This beat is the first place to take time from if the read runs long. Two of the three inputs still make the point. |

### Beat 8. 1:38 to 1:56, verified before it can play

| | |
|---|---|
| **Shots** | S10, S11, S12 |
| **Picture** | Cut to a terminal. A title going through the pipeline. Then a second title hitting `verify` and being **refused**, with the reason printed. Then the kid mode row, where the refused title is not present. |
| **Voiceover** | "None of this happens live. A title is measured end to end, and the result is a signed map tied to that exact file. A verify step blocks publishing, so a title that fails it never reaches kid mode at all." |
| **On screen** | `Fail closed: a missing, stale, unsigned or wrong-hash map keeps the picture hidden.` |
| **Note** | Use a title that verify really refuses. There are real ones. Do not stage a refusal. |

### Beat 9. 1:56 to 2:14, the analyzer, and the Action failing a pull request

| | |
|---|---|
| **Shots** | S13, S14 |
| **Picture** | Split screen or a quick cut. Left: `python -m flashmap check` on a file, exiting 1, with the segment list printed. Right: a GitHub pull request that adds a flashing asset, with our Action's check **red** and its job summary open. |
| **Voiceover** | "The analyzer is open source and it runs on its own. Any studio can drop one file into their repository, and a pull request that adds flashing above the thresholds fails before anyone merges it." |
| **On screen** | <!--n results/screening.json:totals.flagged_segments -->456<!--/n--> `flagged segments across` <!--n results/screening.json:totals.sources_with_at_least_one_flag -->6<!--/n--> `licensed sources` |
| **Note** | The Action's summary must not render a thumbnail of the offending asset, and the pull request's Files tab must not be opened, because GitHub previews images there. Check the job summary before filming it. Leave the red cross on screen for the last four seconds of the beat. |

### Beat 10. 2:14 to 2:26, any Vega app can add it

| | |
|---|---|
| **Shots** | S15 |
| **Picture** | The hook diff on screen, still, for the whole beat. Large enough to read in one look, small enough to fit without scrolling. |
| **Voiceover** | "And any Vega video app can add the same protection with a hook this size. One hook, one cover, and every seek path already safe." |
| **On screen** | Nothing burned in. The diff is the text. |
| **Note** | Do not scroll the diff. A still frame a viewer can read beats a scroll they cannot. If it will not fit, show the part that adds the hook and the part that routes seeks through it, and drop the imports. |

### Beat 11. 2:26 to 2:44, the results table, including the empty rows

| | |
|---|---|
| **Shots** | S16, S17 |
| **Picture** | The README's results tables on screen, scrolled slowly to the "Not measured yet" table so the empty rows are visible and readable. Then the terminal, with `python eval/readme_sync.py --check` passing. |
| **Voiceover** | "Every number we publish points at a file, and a check fails the build if one drifts. The empty rows are measurements we have not made yet. We had a timing result that looked good. The run behind it never played, so we withdrew it." |
| **On screen** | `Longest gap between the player's own position reports:` <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> `ms. Virtual device.` |
| **Note** | Hold long enough on the "Not measured yet" table that a viewer can read two of its rows. This beat is worth the eighteen seconds. A project that catches its own bad number and says so is more trustworthy on the rest, not less. |

### Beat 12. 2:44 to 2:53, close

| | |
|---|---|
| **Shots** | S18 |
| **Picture** | Back to the television, calm, playing. Hold. |
| **Voiceover** | "Calm Frames. It reduces exposure to flashing above published limits in the videos it plays. It is not a medical device." |
| **On screen** | `Calm Frames` (line break) `Reduces exposure to flashing above published limits in the videos it plays.` (line break) `Not a medical device.` (line break) `github.com/alejandro-publius/calm-frames . Apache-2.0` |

---

## The shot list

Eighteen shots. The capture plan for each one, and what it waits on, is [`docs/SHOT_MANIFEST.md`](SHOT_MANIFEST.md).

| Shot | Beat | What is in frame | Filmed or captured |
|---|---|---|---|
| **S01** | 1 | The device running the app, and a terminal in the same frame running `vega device info` | Camera on the screen, either device |
| **S02** | 2 | Close on the screen: the kid mode row, a child's hand on the remote, no faces | Camera on the screen, either device |
| **S03** | 3 | The countdown card, its own countdown running to zero | Camera on the screen, either device |
| **S04** | 4 | One unbroken frame: the covered picture with captions running, the meter beside the screen reading 0, sound audible | Camera on the screen, with the meter live. Prefer the stick |
| **S05** | 4 | The luminance trace for those same seconds, flagged span marked, composited into a corner of S04 | Generated from the flash map. No device |
| **S06** | 5 | The Alexa skip landing inside the flagged part, picture still covered, meter still 0 | Camera on the screen, with the meter live. Prefer the stick |
| **S07** | 6 | The parent area PIN entry | Camera on the screen, either device |
| **S08** | 6 | The household settings, and the hidden-segment count going up when the room changes | Camera on the screen, either device |
| **S09** | 7 | A card press, a D-pad seek and a voice command, same title, no reload | Camera on the screen, either device |
| **S10** | 8 | A terminal, a title going through the pipeline | Terminal recording. No device |
| **S11** | 8 | A terminal, `verify` refusing a second title with the reason printed | Terminal recording. No device |
| **S12** | 8 | The kid mode row with the refused title absent | Camera on the screen, either device |
| **S13** | 9 | A terminal, `python -m flashmap check` exiting 1 with its segment list | Terminal recording. No device |
| **S14** | 9 | A browser, a pull request adding a flashing asset, our Action red, its job summary open | Browser recording. No device |
| **S15** | 10 | The hook diff, still, readable in one look | Screen recording. No device |
| **S16** | 11 | The README results tables, scrolled to "Not measured yet" | Screen recording. No device |
| **S17** | 11 | A terminal, `python eval/readme_sync.py --check` passing | Terminal recording. No device |
| **S18** | 12 | The screen, calm, playing, with the end card over it | Camera on the screen, either device |

Ten of the eighteen are a camera pointed at whichever screen the app is running on. Eight are captured from this machine and need no device at all, except S14, which needs a scratch repository first.

None of the ten is a screen recording, on either device. A television cannot be screen recorded, and the virtual device's screen comes back black because the app draws on a layer the capture misses. Nothing in this video is a screenshot of the virtual device, and nothing in it is a render from the app's own capture path.

---

## After filming, before uploading

- [ ] **The app is shown running on a real Fire TV device or on the Vega Virtual Device**, and if it is the virtual device, it is named on screen. This is the Stage One line
- [ ] `eval/check_video.sh <final file>` exits 0, and `results/video_check.json` is committed
- [ ] No Fire TV home screen, no other companies' app tiles
- [ ] No Blender logo anywhere
- [ ] Tears of Steel credit scroll kept, if it appears
- [ ] No Hell's Angels title card
- [ ] Music muted or credited
- [ ] Maya labelled as a composite persona, legible on a phone
- [ ] `vega device list` appears nowhere
- [ ] Every number on screen matches the README, and `python eval/readme_sync.py --check` passes
- [ ] The words "prevents seizures" and "seizure-proof" appear nowhere, spoken or written
- [ ] Under 3:00, which `eval/check_video.sh` also checks
- [ ] Public on YouTube or Vimeo, in English, and the link works while logged out

## What needs Alex

1. **Settle whether a camera can see the virtual device window.** Two minutes with a phone, the moment the device is free. If it can, this video can be filmed without the stick and the Stage One line is met either way. If it cannot, every app shot waits on hardware. Nothing else in this file matters as much.
2. **The stick, a television in game mode with motion smoothing off, and a phone that films at 240 fps.** The stick is now an upgrade rather than a dependency, but the 240 fps phone is still the only way to get a GATE 1 number, and it was assumed rather than confirmed.
3. **Consent** from anyone in frame, including hands.
4. **Filming the flashing source material**, under the rules at the top: not photosensitive, does not look at the lights.
5. **The camera meter calibration**, which is a step chart shown on the same screen and filmed by the same phone. `eval/meter.py chart` writes the chart and `eval/meter.py calibrate` fits it. On a television this is one step. On the virtual device window it is the open question in the section above.
6. **The voiceover.** Read it slowly. The script is budgeted at 150 words a minute and written to 130, so there is room.
7. **Upload and paste the link** into `docs/SUBMISSION.md` field 7, then check it while logged out.
