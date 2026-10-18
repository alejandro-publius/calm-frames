# Demo run of show: about 90 seconds

The canonical demo script. Plan only, updated on October 17, 2026, in the evening, Pacific
time, for installed source `9cc57ca`. Nothing has been recorded, captured or rehearsed for
it. Older scripts in this repository point here.

Two things are unresolved, and both can stop a take:

- **Visual and audio acceptance.** The owner has not yet looked at and listened to the
  installed build. Its native record says `native_visual_audio_acceptance: false`
  ([final clarity](../../results/final-clarity-2026-10-18/native-results.json)).
- **Native playback stability.** Playback on the Vega Virtual Device has slowed badly and
  then recovered with no code change. Later runs were healthy. The cause is unknown, so a
  slow take is possible on any day.

## Before anyone presses record

1. **The owner accepts the build by eye and ear.** Home with Watch beside Details, the
   Details bar, the explanation screens, the corner notice, the cover panel near 7.3 s and
   28.1 s, and the sound continuing through both covers. Until then, every line below about
   what is seen or heard is unconfirmed.
2. **The organizers answer the footage question.** The FAQ asks entrants to check
   third-party footage with them. Ask at Office Hours #2, Monday, October 19, 9:00 am PT, or
   in the forum. Acadia is a public domain National Park Service clip.
3. **The owner authorizes the recording.** This page authorizes nothing.
4. **The installed package is still the one described.** Source `9cc57ca`, package
   SHA-256 `8f3636ec8bcc2a1c2d5ac80e26f7b3024c0b0ff9003bbdb1341569c51adecbfd`
   ([install record](../../results/final-clarity-2026-10-18/README.md)). After any rebuild,
   re-run the native checks and update this page.
5. **The household preset is Extra cautious.** The times below assume it. Do not change
   household settings to record.
6. **The Mac is unlocked and the simulator window is visible.** Host activity is a
   candidate confound for the slowdown, not a proven cause.
7. **The screen is clean.** No other apps, notifications, tabs, file paths or logos.
8. **Sound is captured from the device.** Mix the narration so the clip's own sound stays
   audible during the covers.
9. **The review page in shot 7 is a version the owner accepted.** Confirm it shows no
   frames, thumbnails or personal paths. Do not press Approve or Stage on camera.

## Rules while recording

- Only the prepared Acadia copy plays, inside the app. Never show the original file or any
  unprepared footage.
- No diagnostics in the journey: no terminal, logs, Technical details page or overlays.
- Shots 1 to 6 are one continuous take. If it must be cut, cut only on Home, never during
  playback.
- If "Loading" or "Playback slow" appears outside the opening and the Skip seek, stop and
  retake later. Never speed up, trim or re-time a slow stretch.
- If a cover does not appear where this page expects it, stop. Do not publish that take.

## Evidence by build

Each observation belongs to the build it was made on. All are device text logs, which show
routes, focus and player events, not pixels or sound.

| Build | What its native check logged | Record |
| --- | --- | --- |
| `9cc57ca`, installed | More info and How it works routes, Parents cancel, return to Home Watch. No media played. | [final clarity](../../results/final-clarity-2026-10-18/native-results.json) |
| `6125459` | Home, Details, Watch on the exact approved Acadia, the picture-shown gate, Back to Details, Home Watch, natural end to Home Watch. | [delivery integration](../../results/delivery-integration-2026-10-18/native-resume-results.json) |
| `3fab999`, October 17 | Both covers with the corner notice, pause and resume during a cover, guarded Skip, natural end and manual Back. | [cover record](../../results/black-gap-2026-10-17/receipt.json) |

The player, cover and guarded seek source files are unchanged since `3fab999`, but its
cover and Skip checks were not repeated on later builds.

## Shots

Times assume healthy playback, with Watch pressed at 0:25 and the clip starting about a
second later. The Extra cautious covers run from 7.343 s to 12.699 s and from 28.113 s to
31.593 s of the clip ([cover record](../../results/black-gap-2026-10-17/README.md)).

### 1. Home, 0:00 to 0:12

- **Purpose.** Say who it is for and show the app running on Vega OS.
- **Action.** The Vega Virtual Device fills the frame on Home, with Watch focused. Hold.
  Lower third: "Calm Frames on Vega OS, recorded in the Vega Virtual Device."
- **Narration.** "Some children are sensitive to flashing light, and a flashing scene
  arrives without warning. Calm Frames, on Vega OS, checks a video before it reaches the TV."
- **Evidence.** The installed build ended its check on Home with Watch focused. Its look
  awaits the owner.

### 2. Details, 0:12 to 0:25

- **Purpose.** Show that the household knows what will be covered before anything plays.
- **Action.** Right to Details, Select. Hold on the covered sections bar for about six
  seconds. Back returns to Home with Details focused. Left to Watch.
- **Narration.** "Details shows which parts this household's setting will cover, before
  anything plays, and that the sound continues. The clip is public domain, from the National
  Park Service."
- **Evidence.** On `6125459`, Details opened with Watch focused, and Details Back restored
  Home Details before Left selected Home Watch. The bar is drawn from the same schedule the
  player follows ([design record](../../DESIGN_ACCEPTANCE.md#details-section)).

### 3. Watch and the first cover, 0:25 to 0:39

- **Purpose.** Show real playback and a covered scene.
- **Action.** Select Watch. The opening screen, then the clip, which starts near-black for
  its first five seconds. "Scene ahead" appears in the lower-left corner. At about 0:33 the
  cover panel appears: "This scene is covered. You can wait or choose Skip." The notice reads
  "Scene hidden". Do nothing until the cover lifts at about 0:39.
- **Narration.** At Watch: "Watch opens a prepared copy, after checking its signed map. The
  clip itself starts dark." When the cover appears: "Here the analysis flagged flashing,
  so the picture is covered. The sound keeps playing."
- **Evidence.** On `6125459`, Watch started the exact approved Acadia and logged the
  picture-shown gate, which is a readiness gate, not proof of a visible frame. The covers
  and the corner notice were logged on `3fab999`. The dark start is in the encoded clip,
  measured from 0 to 4.963 s.

### 4. Between covers, 0:39 to 0:54

- **Purpose.** Say how the covers are made, while normal footage plays.
- **Action.** Let it play. "Scene ahead" appears again at about 0:49.
- **Narration.** "Before a video is added, a computer checks every frame against the WCAG
  2.2 flash limits. The TV checks the signed result again." At about 0:49: "The corner
  notice says another scene is ahead."
- **Evidence.** The analyzer and its profiles are described in
  [flashmap's README](../../flashmap/README.md). At playback the app verifies signed maps
  and matches the route and source metadata to its compiled approved catalog
  ([architecture facts](../ARCHITECTURE_FACTS.md)).

### 5. Second cover and Skip, 0:54 to 0:58

- **Purpose.** Show guarded Skip.
- **Action.** Wait for "Scene hidden", about 0:54. Skip is focused. Press Select once. The
  clip jumps past the scene and the cover lifts.
- **Narration.** "Skip is a choice. It covers first, then jumps past the scene."
- **Evidence.** On `3fab999`, Skip requested the cover before writing the playhead, and
  released it only after the seek landed outside the interval. Not repeated since.

### 6. The end, 0:58 to 1:03

- **Purpose.** Show that the journey ends where it started.
- **Action.** The clip plays its last six seconds and returns to Home, with Watch focused.
- **Narration.** "When it ends, the remote is back on Watch."
- **Evidence.** On `6125459` the natural end returned to Home Watch. On `3fab999` it took
  <!--n results/black-gap-2026-10-17/receipt.json:natural_end_to_home_ms -->339.652<!--/n--> ms.

### 7. Optional: the review page on the Mac, 1:03 to 1:18

- **Purpose.** Show the working local analysis and review flow, kept apart from the TV.
  Drop this shot and the video runs about 75 seconds.
- **Action.** Cut to the Mac. The loopback review page shows the finished report for
  Prairie Creek and Redwood, a public domain NPS clip used as a review example: flagged
  intervals, padded covers and covered time per setting. No video plays. Lower third: "On
  the Mac: local review tool. Not the TV."
- **Narration.** "New videos start on the computer. This page shows what each setting would
  cover, without playing the video. Staging a review does not put a title on the TV. This
  example was never approved for it."
- **Evidence.** [The intake handoff](../LOCAL_INTAKE_HANDOFF.md),
  [the delivery integration](../DELIVERY_INTEGRATION_FINAL.md) and
  [the earlier Prairie proposal](../NEW_VIDEO_TRUST_PROPOSAL.md). Prairie is frozen outside
  the TV's consumer list.

### 8. Close, 1:18 to 1:32

- **Purpose.** State the limits in the approved words.
- **Action.** Back to Home on the TV. End card: "Video: National Park Service, Acadia
  National Park. Public domain. No NPS endorsement is implied." If shot 7 is used, add
  "Review example: Prairie Creek and Redwood, NPS, G Litten. No endorsement implied."
- **Narration.** "Calm Frames reduces exposure to flashing above published limits in the
  videos it plays; not a medical device. It has not been medically validated, and works only
  with prepared videos inside the app."
- **Evidence.** The first sentence is the project's approved wording. The installed source's
  More info and How it works carry the same limits.

## Left out, and why

- **Pause during a cover.** Logged on `3fab999`, left out for time.
- **Parents and the PIN.** No PIN is entered on camera.
- **A refused video.** Refusals are proven in tests, not staged on the device. Do not fake
  one.
- **Prairie on the TV.** It was never approved and is not in the app's catalog.
- **Staging on camera.** Staging changes review state only, and showing it invites the
  wrong reading that it installs a title.
