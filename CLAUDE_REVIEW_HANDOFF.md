# Claude review handoff: the TV experience pass (app lane)

## Native checkpoint, October 17, 2026 (latest)

The owner said yes to the one checkpoint planned below. Source `c2b56d2` was built once
(Debug, 38 s, prepared-library gate passed before and after), installed once and launched
once on the existing Vega Virtual Device. The installed package's SHA-256 is
`081369b932daf3786b54ad46aaa18e2a5dadcb74ef4865914d9c868a09f9cef1`, the same on the
device as in `build/release/stabilization-2026-10-17/`. One prepared-Acadia walkthrough
ran by remote keys while the device log streamed. No screenshot, capture or recording.
The app is left at Home with Watch focused. Evidence:
[receipt](results/native-checkpoint-2026-10-17/receipt.json) and
[selected events](results/native-checkpoint-2026-10-17/selected-events.log).

What the device log established (device clock, measured from the key's release):

| Phase | Result |
| --- | --- |
| Launch to visible | system metric 583 ms; first screen settled by the first 5 s render sample |
| Home to Details | Details screen 20 ms after Enter, its Watch focused at 37 ms |
| Details Back to Home | Home 24 ms after Back, Details focused at 30 ms |
| Watch to first picture | handler 5 ms, player mounted 79 ms, maps verified 123 ms, first picture 1,204 ms |
| Covers (Extra cautious on this device) | on at media 7.378 s and 28.142 s, off at 12.714 s and 31.611 s, each 29 to 35 ms after its scheduled start; wall time matched media time through both |
| Stalls | none: one 42 ms wait at playback start, and the clock advanced 31.299 s of media in 31.264 s |
| Return to Home | at video end: teardown ok in 303 ms, Home with Watch focused at 329 ms, player unmounted at 728 ms |

Not established, still for the owner: anything visible (layout, focus rings, card text,
the single paused statement, How it works, the three circles), sound during covers, the
remote Back key mid-playback (my driver stopped on a pattern that did not allow the
trailing component-stack suffix this Debug build adds to player warnings; the
end-of-video return exercised the same leavePlayer path), and Profiles and Parents.

Two things to know before the next run:

- **Startup traces did not arrive.** Neither launch emitted JavaScript console lines until
  the first key press, so step 1 below cannot read Home readiness from `CALM_TRACE`; use
  the system launch lines and a Right then Left press instead.
- **Someone else touched the device.** A Calm Frames package install at 04:40:06 (during
  this build) and a forced relaunch at 04:41:52 (35 s after this launch) came from no
  command issued here. The installed bytes are this build's, and the walk window shows
  only this driver's keys, but coordinate simulator use before the owner's own pass.


## Stabilization pass, October 17, 2026 (latest)

**Where.** Worktree `/Users/alexvintera/calm-frames-claude-tv-2026-10-16`, branch
`claude/tv-experience-2026-10-16`. Baseline (reviewed head):
`bfb811f41103526c011454e79e47d210eff1cf66`. Last code commit:
`d444fd0470a9c0659fabfe88a47fae62019eb073`; HEAD is the commit that adds this section.
Tree clean after it. Nothing pushed. The installed simulator app is still source
`3f681a783c792cc046a704ac6ebb9383a8128e9c`; nothing was built, installed, launched,
navigated, captured or recorded, and the detector worktree was not touched.

**Preserved, not reimplemented.** The Acadia-only hero, the covered-sections strip, the
rendition offset and shared title styles, the focus and paused/unavailable copy fixes,
the verification cache and deferred legacy routes (`33cbf29`), the cache and teardown
review (`d788a9d`) and the steady scene card (`bfb811f`).

**Newly fixed, oldest first.**

| Commit | What a viewer gets | Files |
| --- | --- | --- |
| `3427030` | Paused during a countdown or cover, one paused statement instead of the card and a corner banner both saying it, on screen and to a screen reader | `app/src/screens/PlayerScreen.tsx`, `app/test/calmframes/playbackUi.test.tsx` |
| `2825451` | Nothing visible. Debug builds log Watch, the first picture, each cover and each wait with media time, Back and teardown, so one native run yields phase timings from the device log | `PlayerScreen.tsx`, `app/src/screens/KidModeScreen.tsx`, `app/src/calmframes/trace.ts`, hook mirror (`hook/src/engine/trace.ts`, `hook/src/mirror.json`), `app/test/calmframes/playbackTrace.test.tsx` |
| `cce89cf` | Nothing visible. Corrects a source note that said Watch evaluates Shaka on the MP4 path; it does not | `app/src/components/navigation/playerRouteFallback.tsx` |
| `a47eee4` | How it works says it works only with the prepared videos in Calm Frames, not with Netflix, Prime Video, other apps or live TV; the purpose line says "prepared", as Home does | `app/src/calmframes/copy.ts`, `app/test/calmframes/copy.test.ts` |
| `d444fd0` | Nothing visible. Three suites that already failed at `bfb811f` now follow its documented behavior | `app/test/screens/playerWiring.test.tsx`, `app/test/calmframes/tenFoot.test.tsx`, `app/test/components/__snapshots__/Player.test.tsx.snap` |

**Investigated, no change needed.**

- Shaka on Watch: a Metro-style transform of `VideoHandler.ts` and `PlayerScreen.tsx`
  (React Native 0.83 metro-config, `inlineRequires: true`) shows the Shaka module required
  only inside the HLS and DASH branch, and PlayerScreen's type-only import elided. The
  prepared MP4 never evaluates it.
- Startup store read: one small AsyncStorage read of legacy sample state; nothing on the
  Calm Frames path dispatches to that store, so nothing rewrites it during viewing.
- Teardown before a fresh player returns at once when there is no player.
- First signature check on Home: required and pure JavaScript; the cache serves the
  player's second check. Host numbers below.
- The three teal circles in the owner's screenshot: no Calm Frames code draws them. On TV
  the player chrome is Back, the title, a seek bar with one orange thumb and a captions
  button; the 10-second buttons are automotive-only. The Acadia cover is plain black (no
  scene stills in its catalog), and the still burned into the rendition is a sunset
  coast frame. Their origin is unidentified; a system or simulator overlay is possible,
  not shown. The checkpoint below tells them apart.
- Seizure wording: the copy test bans "prevents seizures" even in a negation, so Help
  keeps "Detection can miss flashing." with the approved sentence ("not a medical device").

**Checks on the final source.**

| Check | Result |
| --- | --- |
| Full jest, `--testPathIgnorePatterns='uiCapture\|coastalExport\|controlStudy'` | 144 suites passed, 1 skipped; 1424 tests passed, 4 skipped; 57 snapshots passed |
| Same three suites at `bfb811f`, no changes of mine (throwaway worktree, since removed) | playerWiring, Player snapshot and tenFoot fail (4 tests): baseline regressions, now repaired |
| KidModeScreen | timed out once at 5 s in a loaded parallel run; passes alone and in the final full run; passed at `bfb811f` |
| Typecheck | pass |
| Lint | 0 errors, 101 warnings (unchanged baseline), none in changed files |
| Hook package | `test:package` 10 pass; `check:package` offline install, metro resolution and transform true |
| Style and doc-link guards | pass |
| Mutations | banner shown in every paused state: 2 of 9 red; picture-shown line removed: 1 of 2 red; both restored |
| Not run | `uiCapture`, `coastalExport`, `controlStudy` (banned capture suites) |

The one snapshot update is deliberate and equals `bfb811f`'s card change: live region
none, role text, aria-live off, and an empty stable-layout style slot. Logs:
`.logs/stabilization-*.log` (sha256 prefixes: suite `fade0dba96bac6b5`, mutations
`429f35217406b379`, baseline `5f7697c6a7f99991`).

**Measurements.** Host only, not Vega. `node results/performance-2026-10-17/benchmark.cjs
app`, Node 22.23.2, arm64 Mac, three exact Acadia maps per batch, eleven batches:

| Run | First batch, cold | Warm median |
| --- | ---: | ---: |
| With the JIT, this session | 79.4 ms | 4.24 ms |
| `--jitless`, interpreter only | 121.6 ms | 9.99 ms |

The same script recorded 23.97 ms and 0.91 ms on Oct 17 under a lighter machine load; the
spread is host noise. Interpreter-only puts the cold check at about a tenth of a second
here. Home checks only the maps the preset needs, so this does not account for seconds.
Unmeasured: everything on the device, namely startup, Home to Details, Watch to first
picture, buffering, and Back to Home.

**Native checkpoint: one build, one install, one Acadia walkthrough.** After the owner's
approval, build the Debug package from HEAD (release strips the log lines), install
once, and stream the log with `vega device start-log-stream | grep CALM_TRACE`. No
screenshot or recording.

1. Launch. Home is ready at the first `focus kid-mode-home-watch` line. Read the title, the
   benefit line, Watch focused.
2. Details, then Back: `screen details`, then focus returns to Details on Home.
3. Watch: `playback watch`, `screen player`, `prepared-playback`, then
   `playback picture-shown`. Watch to first picture is the gap between the first and last.
4. Covers. Standard and Broadcast cover 7.843 to 12.199 s and 28.613 to 31.093 s; Extra
   cautious 7.343 to 12.699 s and 28.113 to 31.593 s. The card "Flashing scenes" with Skip
   appears five seconds early. Logs show `playback cover on media=` near each start and
   `cover off` near each end. Listen for sound through each cover.
5. Pause inside a cover: one paused statement on the card, no corner banner; Play resumes.
6. Back: `playback back`, `playback teardown ok` (or `fallback`, then 0.7 s), `screen
   player-left`, focus on Watch.

How to tell a stalled clock from an intentional cover:

- **Intentional cover.** It starts at a scheduled time above, the card says "The picture is
  hidden during flashing. You can skip past this scene.", it ends on its own after about
  4.4 to 5.4 s, and the sound continues. Pressing Up shows the seek bar time advancing.
- **Stalled clock.** A `playback waiting on` line with no `waiting off`. Inside a cover the
  card says "Waiting for playback. You can skip past this scene."; outside a cover a plain
  "Loading" appears after 1 s. The seek bar time does not advance, and no `cover off`
  arrives at its scheduled time. At the opening, "Opening your video..." stays, and after
  15 s "Playback stopped" offers Go back.
- **Circles.** If the three circles appear, press Back once. If they stay on Home or
  outside the app, they are not the app's. Note whether the seek bar time advances.

**Remaining submission blockers.** The native checkpoint above (appearance, focus, sound
through covers, real speed). The owner-run usability sheet, which has no results. The
submission requirements in `docs/submission/`. None of these is verified, so this is not
submission-ready. The detector candidate stays disabled on its branch.


## Installed design review build, October 17, 2026

The owner-approved fixes and design pass are built, installed and open in the existing
Vega Virtual Device. App source: `3f681a783c792cc046a704ac6ebb9383a8128e9c`, branch
`claude/tv-experience-2026-10-16`. Both Details schedules propagate rendition offsets;
Details and the opening share short-title and long-title typography and column width.

Package: `build/release/design-native-2026-10-16/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `b682245fc8cdfcdcdd6dd289c58db72516ad0c4f431f558fd9fe721aaf98920e`.
All 760 app inputs match the build receipt. The strict package gate passes with all
four original verification reports and the unchanged approved Acadia bundle. The hash
of the transferred package on the simulator also matches. One installation succeeded,
followed by one launch request and a positive running-state check for
`io.github.alejandropublius.calmframes.main`.

The original build completed during the Mac connection interruption; no rebuild was
needed. The first simulator start exited before installation, so that install attempt
failed with Device not found. A detached process session started the same simulator
successfully. No device data, preferences or SDK configuration was reset.

Evidence: [native receipt](results/design-native-2026-10-16/receipt.json).
The app is left open. No navigation, playback, screenshot or recording was performed.
Logs establish package delivery and a running process, not visible layout or sound.
The owner still needs to assess Home and Details, title continuity, visible focus through
Profiles / Back / How it works and Parents / cancel, and sound through prepared Acadia
covers. Use the existing usability checklist. No push, publication, merge, detector,
media, signing or trust change occurred.

## Owner-approved review fixes, October 16, 2026

Both review findings are corrected. The watch and technical Details schedules pass
`renditionStartOffsetMs`, including memo refresh when the offset changes. Details and
PlayerOpening share `heroTitleTypography` and a 720-unit title column, retaining the
same short-title and long-title sizes. The hook style mirror is regenerated.

Affected checks: 71 unique tests across eight suites pass after regenerating the mirror
(the initial run correctly caught that it was stale); typecheck passes; lint reports
zero errors and the existing 101 warnings; style and strict prepared-input gates pass.
New checks cover positive and negative offsets at duration boundaries, all three
compiled Acadia presets, both rendered Details strips, offset changes, and rendered
title typography for short and long names. No snapshots were updated.
Logs are in `results/design-native-2026-10-16/`. Native build and installation results
will be recorded separately there. These source checks do not establish native appearance
or audible continuity. Media, maps, trust and the detector remain unchanged.

Written October 16, 2026, for another agent or a person to review before anything is
built. Nothing here was built, installed, launched, navigated, captured or recorded. The
installed demo on the simulator has not changed. This is not submission-ready until the
native checks and the submission requirements are verified.

## The cohesive design pass, latest

Five commits on top of the review fixes, oldest first:

- `917849a` Say what paused and unavailable states do, and nothing they do not
- `4193ccb` Compose Home around one featured video
- `bf49430` Keep the title in place from Details to the opening shell
- `cc319d9` Show the covered sections on Details, from the player's own schedule
- this commit: `DESIGN_ACCEPTANCE.md`, the decisions, the usability sheet, the status
  line and this handoff

`DESIGN_ACCEPTANCE.md` lists every requirement with its files, its automated check and the
before and after in words. In short: the unavailable card says "The picture stays hidden.
Go back to the library." and names the title once; a paused cover says "Paused. The
picture stays hidden. Press Play to continue." and a paused countdown says how long
remains before the flashing; Home with one featured video shows the hero alone with
"Watch prepared videos with flashing scenes covered." and the running time in words, the
rail returning with two or more videos; Details shows "Covered sections" as a still strip
with a text equivalent, built from `buildCoverIntervals` under the household's options,
with limitation lines for an unknown length or an unverified title; Home, Details and the
opening shell start the title at one offset; while How it works is open only its Back asks
for focus; Back on the opening shell is pinned to leave once even if the stall timeout
fires later.

Checks on the final source: full jest 140 suites passed, 1 skipped, 1375 tests passed, 4
skipped, 57 snapshots passed (one updated on purpose, the three unavailable-card wording
lines in `Player.test.tsx`); typecheck pass; lint 0 errors, 101 warnings; style and
doc-link guards pass; the hook mirror is current (no mirrored file changed). Mutations,
each seen red and restored: rail rule reverted (2 of 11), paused line reverted (1 of 5),
clamp removed from the covered-sections schedule (2 of 13). Pins changed on purpose: the
default shelf expects no card under the hero; running times read in words. Not run:
`uiCapture`, `coastalExport`, `controlStudy`. Logs under `.logs/design-pass-*.log` and
`.logs/details-timeline-*.log`.

Unresolved after this pass:

- Everything native: appearance, visible focus, legibility at distance, the title's
  continuity on Watch, audible sound through a cover, and real D-pad behaviour. The list to
  walk is at the end of `DESIGN_ACCEPTANCE.md`.
- The usability sheet (`docs/evidence/usability-checklist-2026-10-16.md`) has five owner-run
  tasks and no results; nobody has performed it.
- The Harbor demo's own card copy (`benignStory.ts`) still names captions, which that title
  ships; left as it is.
- The detector candidate on `claude/detector-concurrency-2026-10-16` stays disabled and its
  limitations stand as documented there, including the red-envelope finding.

The sections below are the earlier handoffs of the day, kept as written.

## Where

- Absolute checkout path: `/Users/alexvintera/calm-frames-claude-tv-2026-10-16`
  (a git worktree of the Codex repository at
  `/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-review`).
- Branch: `claude/tv-experience-2026-10-16`, based on `63a0bcb3547df218a634a0ecca100c3bca05cc4e`
  (`codex/dark-cinema-2026-10-16`, the verified latest app branch, equal to origin at the start).
- HEAD: the commit that updates this file. Run `git -C /Users/alexvintera/calm-frames-claude-tv-2026-10-16 log --oneline 63a0bcb..HEAD`
  to see the sixteen commits; the eleven of the earlier passes are listed below and the
  five of the design pass above.
- Working tree status at the time of writing: clean apart from this file and
  `docs/STATUS.md`, both committed together. `app/node_modules` is an APFS clone of the
  Codex checkout's modules and is ignored; `.logs/` is ignored.
- Not pushed. No branch was pushed anywhere in this pass.

## What changed for the user, and why

1. The app says what it does, from its data. How it works, More info, the first run
   explainer and the viewing plan said flashing scenes are "replaced by a still picture"
   and that "sound and captions continue". The featured Acadia maps carry no scene hold, so
   its three covers are plain black, and its rendition has an audio track and no caption
   track. Those pages now say flashing scenes are covered while the sound continues, and
   More info names captions only for a title that ships them. The sentence about a title's
   own covers is built from its schedule and caption list in `coverLine`.
2. Two quick presses on Watch start the player once (a latch that reopens on the
   navigator's focus event).
3. Back from the profile picker puts focus on the button that opened it.
4. The player's refusal of an altered prepared route has a regression suite naming what a
   person sees: no opening shell, no media load, one unavailable card and one Back, with
   the exact compiled Acadia route as the passing control.
5. An evidence index, an Acadia demo script draft and a usability sheet, for judges and
   for the next pass.

The dark cinema palette, the Acadia imagery, the faces, the shared button, header, surface
and notice components, the focus ring and the one-video rail are unchanged.

## Commits, oldest first

- `f51ae29` Test the player's refusal of an altered prepared route
- `a5c34f4` Latch Watch so two quick presses launch the player once
- `4e221d7` Return focus to the profile button after Back closes the picker
- `e6e7cd2` Say covered, not still picture, and promise captions only where they exist
- `852ce26` Record the Oct 16 TV experience decisions
- `0b106ba` Record the TV experience pass: evidence and receipt
- `fe21fff` Add the evidence index, the Acadia demo script draft and the usability sheet
- `2b6d4b2` Hand off the TV experience pass for review (the reviewed head)
- review fix: Clear the picker's focus request when How it works opens
- review fix: Promise sound, not captions, on the covering and after cards
- this commit: the records and this handoff updated for the review fixes

## Files changed, by feature

- Prepared route refusal suite: `app/test/calmframes/playerRouteRefusal.test.tsx`.
- One launch per Watch press: `app/src/screens/KidModeScreen.tsx`,
  `app/test/screens/repeatedPresses.test.tsx`.
- Focus return after the profile picker: `app/src/calmframes/KidHomeScreen.tsx`,
  `app/test/calmframes/pickerFocusReturn.test.tsx`.
- Words built from the data: `app/src/calmframes/copy.ts`,
  `app/src/calmframes/TitleDetailsScreen.tsx`, `app/src/calmframes/PictureHoldIntroduction.tsx`,
  `app/src/calmframes/ViewingPlan.tsx`, `app/test/calmframes/copy.test.ts`,
  `app/test/calmframes/detailDiscovery.test.tsx`, `app/test/calmframes/screens.test.tsx`.
- Records: `docs/DECISIONS.md`, `docs/evidence/tv-experience-2026-10-16.md`,
  `results/tv-experience-2026-10-16/receipt.json`.
- Review fixes: `app/src/calmframes/KidHomeScreen.tsx` and
  `app/test/calmframes/pickerFocusReturn.test.tsx` (How it works clears the picker's focus
  request; Acadia-only regression); `app/src/calmframes/cards.ts`,
  `app/src/calmframes/usePlaybackPresentation.ts`, `app/test/calmframes/cards.test.tsx`,
  `app/test/calmframes/useFlashGuard.test.tsx`, `hook/src/engine/cards.ts`,
  `hook/src/mirror.json` (sound, not captions, on the covering and after cards; mirror
  regenerated with `node hook/tools/sync.mjs`).
- Judge experience: `docs/evidence/README.md` (the evidence index),
  `docs/submission/DEMO_SCRIPT_ACADIA_2026-10-16.md`,
  `docs/evidence/usability-checklist-2026-10-16.md`, `docs/README.md` (index rows),
  `docs/STATUS.md`, this file.

## Checks run on the final app source, and how to repeat them

From `app/`, under Node 22 (`eval "$(fnm env --shell zsh)" && fnm use 22`):

| Check | Command | Result |
| --- | --- | --- |
| Full jest | `node_modules/.bin/jest --watchman=false --ci --coverage=false --colors=false --maxWorkers=4 --testPathIgnorePatterns='uiCapture\|coastalExport\|controlStudy'` | 135 suites passed, 1 skipped; 1336 tests passed, 4 skipped; 57 text snapshots passed, 0 written, 0 obsolete |
| tenFoot and hookMirror guards | included in the run above | pass |
| Typecheck | `npm run typecheck` | pass |
| Lint | `npx eslint src test --ext .ts,.tsx` | 0 errors, 101 warnings (97 source + 4 test, the Acadia-first baseline), 0 in changed files |
| Style guard | `python eval/style_check.py` from the root | pass |

Excluded on purpose, as in the Acadia-first receipt: `uiCapture`, `coastalExport`,
`controlStudy` (capture and export suites). The Python suites were run in the detector
worktree, not here; the app change does not touch them.

Mutations, each applied, run and reverted (exact edits and counts in the receipt):
refusal removed in `PlayerScreen.tsx` (9 of 10 red); latch never set (2 of 2 red); picker
return control removed (2 of 3 red); captions always promised (2 of 31 red).

After the review fixes, on the final source: focused jest on the 14 affected suites, 253
tests, pass; full jest 135 suites passed, 1 skipped, 1337 tests passed, 4 skipped, 57
snapshots unchanged; typecheck pass; lint 0 errors, 101 warnings; hook package
`npm --prefix hook run test:package` 10 pass and `check:package` offline install, metro
resolution and transform all true; `hookMirror.test.ts` passes after
`node hook/tools/sync.mjs`. Mutation: with the clearing line removed from How it works the
Acadia-only regression failed (1 of 4) and passed again when restored. Logs and digests are
under `review_fixes_2026-10-16` in the receipt.

## What remains experimental or unverified

- Nothing native. No build, install, launch, simulator action, screenshot or recording.
  Visible focus, legibility at distance, audible sound during covers and caption drawing
  all still need the owner's native check after an approved build.
- Audio continuity: headless evidence shows the cover layer never pauses, mutes or changes
  the element's volume and follows the playhead through intervals, buffering, seeking and
  background. That is planned-interval evidence about the app's own layer, not a
  measurement of sound on the simulator or a device.
- The launch latch reopens on the navigator's focus event. If the player route never
  mounts, the latch stays shut until focus returns, which is the same state the existing
  control removal already leaves the shelf in. Worth a native check.
- The covering and after cards no longer name captions. Two places still do, on purpose:
  the unavailable card's announcement in `playerAccess.ts` ("while sound and captions keep
  playing"), left for a separate decision, and the Harbor demo's own card copy in
  `benignStory.ts`, which describes a title that ships captions.
- The usability sheet has not been run with anyone. The demo script is a draft and the
  refusal case can only be shown on the television if a review build carries an
  unavailable title; otherwise it is shown headlessly, and the script says so.

## Asset and trust implications

None. No media, map, key, catalog, signing, trust, parental control, household setting or
cloud resource changed. The Acadia bundle and its approved key are unchanged.

## Confirmation about the installed app and other checkouts

The installed dark cinema demo on the simulator (app source `d67e1da`, see
`FINAL_HANDOFF.md`) was not rebuilt, reinstalled, launched, restarted or navigated. The
simulator was not touched. The Codex checkouts, `~/calm-frames`, the earlier Claude
checkouts and the detector worktree were not edited by this lane.

## Next steps for review, build, installation and device QA

1. Read `docs/evidence/tv-experience-2026-10-16.md` and the receipt; spot-check the four
   mutations by repeating one.
2. Review the three source changes (`copy.ts`, `KidModeScreen.tsx`, `KidHomeScreen.tsx`)
   and decide on the player card wording.
3. With the parent's go-ahead, build once from this branch, install once, and walk the
   Acadia route with the remote: Home, Details, More info, Watch, the first covered part
   (its time comes from the map), pause, seek, resume, Back, the profile picker and Back.
   Listen for sound through the cover. Record the native receipt as before.
4. Only then consider the demo script and the usability sheet.
