# Demo video script

**Target length: 2:55.** Judges do not have to watch past 3:00, so everything that matters is in the first 60 seconds and nothing lands after 2:55.

**The one sentence, on screen and in the voiceover, and never anything else:** "Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device." Never "prevents seizures". Never "seizure-proof".

---

## Before filming: read this

### Safety, which overrides the shot list

1. **Nothing that flashes appears in this video, not for a single frame.** Where a flash has to be shown, it is a luminance trace on a chart, never the footage. This applies to the raw material too: nobody opens a `HAZARD_` file to find a shot.
2. **Whoever films any flashing footage is not photosensitive and does not look at the lights.** Everyone in frame has given consent.
3. The final cut is measured before it is uploaded: `python -m flashmap check final_video.mp4 --profile wcag` has to return 0, and that result is committed. This is a hard gate, not a nice-to-have.

### Rights and credits

- Film **only inside our own app**. The Fire TV home screen shows other companies' app tiles, so it never appears.
- Cut every Blender logo. They are excluded from the Blender Studio licences.
- Mute or credit any film music.
- If Tears of Steel appears, its credit scroll stays.
- The Hell's Angels (1930) title card stays out of the video entirely.
- DVIDS material carries its non-endorsement notice. NASA material follows NASA's credit-line guidance.

### What must exist before this can be filmed

| Needed | Where it stands |
|---|---|
| The Fire TV stick on Vega OS 1.2, developer mode, connected | Waiting on the stick |
| Kid mode, the countdown card, the parent area behind a PIN | Phase 4 |
| The camera-fed meter beside the television | Phase 5, the camera harness |
| At least one verified title with a real flagged segment in it | The pipeline produces these; pick one with a clean calm moment |
| The drop-in hook, so there is a diff to show | Phase 4 |
| A pull request in a scratch repository that the Action fails | Can be made any time from `flashmap/examples/flash-check.yml` |

### Numbers on screen

Every number that appears comes from `results/` and matches the README. There are only three in this cut, and each one is marked in this file, so `python eval/readme_sync.py --check` covers them too.

**There is no screen-level cover lead time**, and none appears in this video. The one run that claimed one was withdrawn. The software-level figure that exists now is not said out loud either, because a viewer cannot be expected to hold the difference in their head. The voiceover says what is measured and what is not, and does not imply a timing figure we do not have.

---

## The script

Times are cumulative. Voiceover is the left column read aloud. On-screen text is what is burned in.

### 0:00 to 0:12, the real thing, running

| | |
|---|---|
| **Picture** | One continuous shot, no cut. A Fire TV stick in the back of a television, the app's own home screen on the panel, and a laptop terminal beside it in the same frame. In the terminal, type and run `vega device list`. Then, in the same shot, `vega device info`. |
| **Voiceover** | "This is a Fire TV stick, running our app, on a real television." |
| **On screen** | Nothing burned in. Let the terminal be the caption. |
| **Note** | `vega device list` crashes with a TypeError on SDK 0.24 while a virtual device is running. On the stick it may work. **If it prints the device, use it and cut `vega device info`.** If it crashes, leave the crash in frame for about a second and let `vega device info` answer instead. Do not re-take until it prints something it did not print. The crash is friction log entry 6, and a judge seeing it is a point in our favour, not against. |

### 0:12 to 0:26, who this is for

| | |
|---|---|
| **Picture** | Close on the television. The app's kid mode row, a child's hand on the remote. Nobody's face. |
| **Voiceover** | "Maya is twelve. She has photosensitive epilepsy. Tonight she is at a sleepover, choosing a film, and no adult is going to watch it first to check what is in it." |
| **On screen** | `Maya is a composite persona. Not a real person.` Hold it for the whole beat, bottom left, plain text. |
| **Note** | The persona label is not optional and it is not small print. It stays legible on a phone screen. |

### 0:26 to 0:40, the countdown card

| | |
|---|---|
| **Picture** | Maya presses play. The countdown card appears on the television: the app saying, ahead of time, that a flagged segment is coming and what it will do. |
| **Voiceover** | "Every frame of this film was checked before it could appear here. When a flagged part is coming, the app says so first." |
| **On screen** | Nothing. The card is the text. |

### 0:40 to 1:00, the calm hold, and the meter at zero

**This is the shot the whole video exists for. Film it more than once and keep the best take.**

| | |
|---|---|
| **Picture** | One unbroken shot, no cut, of three things in the same frame: the television with the picture covered and captions still running across it; a small meter beside the television, fed by the camera looking at the panel, reading 0; and, composited in a corner, the luminance trace for those same seconds with the flagged span marked. The sound is audible throughout. |
| **Voiceover** | "The picture is hidden. The sound keeps going, the captions keep going, and the meter beside the television, which is reading the panel itself, stays at zero. What it is hiding is this." (beat, trace fills the corner) "A trace, not the footage. Nobody has to look at the flashes to know they were there." |
| **On screen** | `Luminance trace. The flashing itself is never shown.` |
| **Note** | The meter has to be visibly live: let it move before and after the covered span so it is obviously not a still image. If the camera harness is not ready, this shot cannot be faked and the video waits. |

### 1:00 to 1:14, the seek that would have landed inside it

| | |
|---|---|
| **Picture** | Same take if possible. Maya says an Alexa skip-forward command that would put the playhead inside the flagged part. The picture stays covered. The meter stays at 0. |
| **Voiceover** | "Voice, remote and on-screen cards all go through one seek path. A skip that would land inside a flagged part is covered before it lands." |
| **On screen** | `Voice · D-pad · cards: one seek path` |
| **Note** | This is the strongest single second in the video, because it is the failure mode a reviewer would expect. Get it clean. |

### 1:14 to 1:32, her dad set this up

| | |
|---|---|
| **Picture** | Cut to the parent area. PIN entry, then the household settings: the preset, the television diagonal, the seat distance. Change the room size and show the number of hidden segments for this title go **up**. |
| **Voiceover** | "Her dad set this up behind a PIN: how strict, how big the television is, how far away she sits. A household setting can add hides. It cannot take any away, and it cannot go below the published thresholds." |
| **On screen** | `Household settings can only make it stricter.` |
| **Note** | Showing the count go up rather than down is the whole point of the shot. If the demo title's count does not move, pick one where it does. |

### 1:32 to 1:44, three ways in, one flow

| | |
|---|---|
| **Picture** | Quick, unhurried: a card press, a D-pad seek, a voice command. Same title, same protection, no reload between them. |
| **Voiceover** | "Cards, the remote and voice are the same flow, and every one of them is safe." |

### 1:44 to 2:04, verified before it can play

| | |
|---|---|
| **Picture** | Cut to a terminal. A title going through the pipeline. Then a second title hitting `verify` and being **refused**, with the reason printed. Then the kid mode row, where the refused title is not present. |
| **Voiceover** | "None of this happens live. A title is measured end to end, and the result is a signed map tied to that exact file. A verify step blocks publishing, so a title that fails it never reaches kid mode at all." |
| **On screen** | `Fail closed: a missing, stale, unsigned or wrong-hash map keeps the picture hidden.` |
| **Note** | Use a title that verify really refuses. There are real ones. Do not stage a refusal. |

### 2:04 to 2:22, the analyzer, and the Action failing a pull request

| | |
|---|---|
| **Picture** | Split or quick cut. Left: `python -m flashmap check` on a file, exiting 1. Right: a GitHub pull request that adds a flashing asset, with our Action's check **red** and its summary open. |
| **Voiceover** | "The analyzer is open source and it runs on its own. Any studio can drop one file into their repository and have a pull request fail when it adds flashing above the thresholds." |
| **On screen** | <!--n results/screening.json:totals.flagged_segments -->432<!--/n--> `flagged segments across` <!--n results/screening.json:totals.sources_with_at_least_one_flag -->5<!--/n--> `licensed sources` |
| **Note** | The Action's summary must not render a thumbnail of the offending asset. Check the job summary before filming it. |

### 2:22 to 2:36, any Vega app can add it

| | |
|---|---|
| **Picture** | The hook diff on screen for four seconds. Small enough to read in one look. |
| **Voiceover** | "And any Vega video app can add the same protection with a hook this size." |

### 2:36 to 2:48, the measurement we do not have

| | |
|---|---|
| **Picture** | The terminal, showing `python eval/readme_sync.py --check` passing, then `docs/GATES.md` open on the retraction. |
| **Voiceover** | "Every number we publish points at a file, and a check fails the build if one drifts. We had a timing result that looked good. The run behind it never played, so we withdrew it and wrote down why. We do not have a lead time number yet, and we are not going to publish one until we have filmed it." |
| **On screen** | `Longest gap between the player's own position reports:` <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> `ms. Virtual device.` |
| **Note** | This beat is worth the twelve seconds. A project that catches its own bad number and says so is more trustworthy on the rest, not less. |

### 2:48 to 2:55, close

| | |
|---|---|
| **Picture** | Back to the television, calm, playing. Hold. |
| **Voiceover** | "Calm Frames. It reduces exposure to flashing above published limits in the videos it plays. It is not a medical device." |
| **On screen** | `Calm Frames` (line break) `Reduces exposure to flashing above published limits in the videos it plays.` (line break) `Not a medical device.` (line break) `github.com/alejandro-publius/calm-frames · Apache-2.0` |

---

## After filming, before uploading

- [ ] `python -m flashmap check <final file> --profile wcag` returns 0, and the result is committed
- [ ] No Fire TV home screen, no other companies' app tiles
- [ ] No Blender logo anywhere
- [ ] Tears of Steel credit scroll kept, if it appears
- [ ] No Hell's Angels title card
- [ ] Music muted or credited
- [ ] Maya labelled as a composite persona, legible on a phone
- [ ] Every number on screen matches the README, and `python eval/readme_sync.py --check` passes
- [ ] The words "prevents seizures" and "seizure-proof" appear nowhere, spoken or written
- [ ] Under 3:00
- [ ] The link works while logged out

## What needs Alex

1. **The stick, a television in game mode with motion smoothing off, and a phone that films at 240 fps.** Two of those were assumed rather than confirmed.
2. **Consent** from anyone in frame, including hands.
3. **Filming the flashing source material**, under the rules at the top: not photosensitive, does not look at the lights.
4. **The voiceover.** Read it slowly. The script is written for about 150 words a minute and it has room.
5. **Upload and paste the link** into `docs/SUBMISSION.md` field 7, then check it while logged out.
