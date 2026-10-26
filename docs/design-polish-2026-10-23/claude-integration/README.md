# Local integration candidate, October 24, 2026

Branch `claude/integration-2026-10-24`, local only: nothing here is pushed,
merged into main, published or submitted. The integration source was
`d7ff886`. The acceptance pass below added three item 6 commits, so the
candidate source is now `a672f57`. The commits adding these notes change
documentation only.

## Inputs, each verified before use

| Input | Exact source | How it was checked |
|---|---|---|
| Base | `6a87937f9f185ac0760d6f8331184e34b876d92c` | present in this repository |
| Cloud dependency and privacy follow-up | `226d317a2a9eb22c2b16770ec0db15de5be4952e`, from `calm-frames-followup-226d317.zip` (237,073 bytes, sha256 `bb152edf8a81c1fec7a4a6b933584569acbbc2be73b683a71d164cdc547b7e04`) | the transfer receipt matched the ZIP's size and hash, the head, the base and the bundle and patch hashes; every member matched its SHA256SUMS; the bundle verified here and needs only `6a87937`; its seven commits and tree `c1f2a9b` match the manifest; imported as `codex/mac-followup-226d317` |
| Item 6 production fix | `dd1ec6c37f5d5ed86138bc38867d0b16b245a9b8` | named as the production fix in the item 6 export manifest; cherry-picked alone as `161c2f5`, because its parent is a fixture commit and a merge would have brought the fixture in |
| Item 11 | `claude/native-accessibility-2026-10-24` at `a800fb4` | merged as `a0c8816`, so production commits `4d4152c`, `3ede1fa`, `88c1716`, `eeaaf16`, `3b0174b` and notes `0eab3c4`, `a800fb4` keep their SHAs and cannot be applied twice; none was already in `226d317` |

Never brought in: the item 11 harness branches (`5e48655`, `4553ee3`), the item 6
fixture, test and harness commits (`6f5aa66`, `444ca91`, `c812685`, `78e8a2c`,
`b9cd627`), any made-up household or PIN constant, and any temporary entry
wiring. `app/index.js` is byte for byte the base's.

## Commits after `226d317`

| Commit | What |
|---|---|
| `161c2f5` | Item 6: each first run step opens at the top of its own scroller (from `dd1ec6c`) |
| `a0c8816` | Merge of item 11 |
| `738381d` | One test holding the merged name editor's announcement and its private trace together |
| `d7ff886` | The hook package mirror brought up to the cloud's private trace change |
| this commit | These notes and the ledger rows below |

## How the overlaps were resolved

- `ProfileNameEditor.tsx` merged without a conflict and keeps both sides. The
  letter keys keep the cloud's `traceFocus={false}`, and the draft field stays
  item 11's flush reading stop with its polite live region. Its trace id,
  `profile-name-field`, holds nothing typed. `nameEditorIntegration.test.tsx`
  holds both. Four breakages each turned it red at an assertion: tracing the
  letter keys again, dropping the live region, a fixed announcement, and a
  trace that carries what VoiceView says.
- `CHECKPOINT.md`: rows 10 and 12 are the cloud's, and row 11 joins both sides.
- The cloud changed `CalmTouchable.tsx` and a comment in `trace.ts` without
  syncing their copies in `hook/src/engine`, so `hookMirror.test.ts` fails on
  `226d317` itself. `d7ff886` is exactly what `node hook/tools/sync.mjs`
  writes. No item 6 or item 11 file is mirrored.

## Checks on `d7ff886`

- `npm ci --ignore-scripts` and `setup:player` with the cloud's lock (sha256
  `e1ca817d...2398`, as its manifest records). Node 22.23.2, npm 10.9.8.
- Typecheck passes. Lint has 0 errors; its 104 warnings are not in a changed
  file. The style check passes.
- CI's prepared-asset and tooling step passes all 87 Node tests, including the
  cloud's dependency and logger tests.
- The full app suite passes: 177 suites passed and 1 skipped; 1875 tests passed
  and 4 skipped. The first full run, before `d7ff886`, failed only
  `hookMirror.test.ts`.
- `make test-hook-package` passes. `make pins` finds nothing loose.
- `make sbom-check` passes. `make audit` finds 21 npm advisories, none
  critical, and none in Python. Advisory 1243074 (`body-parser`, high) appeared
  after the cloud's scan of the same lock and has no exception. The two older
  exception groups expired on October 21. `make audit-check` fails on those
  three. They are recorded here, not re-dated.

## On the device

Vega Virtual Device, 1920 by 1080, each package installed package scoped.

| Package | Bytes | sha256 | sha384 |
|---|---|---|---|
| Candidate `d7ff886` | 132,679,215 | `e21eaf5f561f36573cf22d65930dd63bf1cdf7de4160f1397dd0a009bd6408f5` | `0dee4edc...9f66` |
| Harness A `937c27e`, never merge: the item 11 harness with the focus trace on | 130,748,953 | `f24d7149ea9e6ef5bc59e5f3f4971f879b43f194e7f76b606d60e4d56dd3602d` | `41ac7436...0e87` |
| Harness B `ec68707`, never merge: the item 6 fixture | 130,706,023 | `237a61b96576e37ea165e22a2fdfeab4f4af0d9763e69a0059c5786179f699b7` | `437b3aed...37c5` |
| Rollback, production build of `6a87937` | 132,661,830 | `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d` | `b268be99...b458` |

- The candidate opens on the ordinary Home. With VoiceView on it says "Details:
  Acadia, button. Watch: Acadia, button. McWay Falls, 5 minutes, button,
  selected", as item 11 left it.
- Private trace, harness A, made-up household, debug trace on, a log stream
  whose filter counts but never writes a line naming a key: focus moved over
  six PIN keys with no key pressed, then over letter keys with one made-up
  letter typed. 0 key focus traces. Ordinary controls were traced: the menu
  buttons, Back, the profile chips, Add a kid, Edit name and the name field.
  No kept line names the made-up name.
- The merged name editor, harness A, VoiceView on: the field says the made-up
  draft with "4 of 16 characters", Down reads a letter key, Up returns to the
  field, and Back closes the editor without saving.
- Item 6 recheck, harness B, on the integrated code: the preset step opens at
  its top with Next; after Extra cautious the first Down only scrolls the list's
  padding and the second reaches Next; the room step opens at its top with its
  safety line; Next is reachable; the explainer opens at its top with Your
  household in full and Open library focused; the remote's Back walks one step
  and the room step opens at its top. The approved disclaimer still starts
  below the explainer's edge.
- Restored: the rollback package, ordinary Home, VoiceView off and silent.

The owner's PIN was not entered. The made-up PINs went in with every press
withheld, VoiceView off and no stream, log reader, filter or recorder running.
No playback was started, so no saved place changed. The earlier correction
stands: item 11's first pass moved McWay Falls from 0:36 to 0:55.

## Item 6 coverage

Observed in its own pass, on its fixture at `6a87937` with harness `b9cd627`:
footers visible and reachable at 1920 by 1080 and 1280 by 720, Back walking one
step, the longest choices, and the fix itself at both sizes. Rechecked here at
1920 by 1080 on the integrated code. Still needed on the integrated build: the
production first run on a fresh household, which this session cannot reach
without resetting the real one, and 1280 by 720. Still open from item 6: the
disclaimer below the explainer's edge, one extra Down on the preset step, and
the device turning its display off after idle time. The fixture's own control
test, which expected the keypad to be traced when nothing turns it off, now
fails on the never-merge harness because the cloud fix removed that trace.
The acceptance pass below takes up each of these.

## Acceptance pass on the candidate

After `d7ff886` the owner asked for the remaining checks that need no human:
items 5, 6, 11 and 12. Item 6 produced three production commits, so the
candidate is now `a672f57`. The full app suite passes on it: 178 suites passed
and 1 skipped; 1878 tests passed and 4 skipped. Typecheck passes and lint has
no error. Each new item 6 guard was broken on purpose and seen to fail.

| Commit | What |
|---|---|
| `917e78f` | Item 6: nothing to scroll below the last preset; the explainer's lines in a reading stop |
| `4de7bd0` | Item 6: FocusArea, so Up from the buttons reaches that stop |
| `a672f57` | Item 6: the explainer's content ends where the stop's ring does |
| this commit | These notes and ledger rows 5, 6, 8, 11, 12 and 18 |

### Where it was checked

- The main virtual device at 1280 by 720, with never-merge harnesses: the item
  6 fixture on `d7ff886` code (`ec68707`) for the pictures of the defects, then
  on `917e78f` (`50b5231`) and `4de7bd0` (`089ec6f`); and the item 11 harness
  on `4de7bd0` code with a made-up household (`19ba55d`), whose first name save
  is refused on purpose. `a672f57` changes only the explainer's bottom padding
  and its test, so those results carry to it. The profile chooser was opened on
  the real household with the candidate at `4de7bd0`, read only.
- A disposable virtual device: its own instance, booted fresh from the SDK's
  base images with the SDK's own tool, used at 1920 by 1080 and 1280 by 720 and
  deleted afterwards. The candidate's own package ran its production first run
  there on a new made-up household: `4de7bd0` first, then the exact `a672f57`
  package at both sizes after a reinstall. It also played McWay Falls and sat
  idle there. The real device's instance was stopped and untouched while it
  ran.

### Item 5, names, made-up household, 1280 by 720, VoiceView on

- Renaming Robin to Sam, a sibling's name, is refused where the counter was:
  "Sam. Sam is already in this household. Choose a different name." The old
  name stays.
- A refused save says "Name not saved yet. This TV couldn't write the change
  down. Try again, or cancel to keep the old name." with focus on Try again,
  and the draft and the old name stay. Try again saves it: the chip and the
  Remove button take the new name, the kid keeps its place, and focus returns
  to Edit name.

### Item 6, first run

- Before, on `d7ff886` code at 1280 by 720: with Extra cautious focused, the
  first Down only scrolled the list. The explainer opened with the approved
  sentence below its edge, and Up from Open library left no visible focus.
- One Down from Extra cautious now reaches Next: in the fixture at 1280 by 720
  and in the production first run at both sizes.
- The explainer took three commits. The reading stop alone was never reached,
  because its frame runs below the visible edge beside the buttons. FocusArea
  lets Up reach it. Then a dead Down from the stop, 2 units of padding, went in
  `a672f57`. At both sizes in the production first run, Up from Open library
  now lands on a whole ring with the approved sentence in view, and one Down
  returns to Open library. With VoiceView on, one Up reads every line, the
  approved sentence and the reading note (heard in the fixture at 1280 by 720).
- Every step opens at its top, the room's safety line first, and Open library
  reaches Home on the new household. The production first run on a fresh
  household is now observed at both sizes.
- At rest the approved sentence still starts below the explainer's edge: the
  step holds more text than one screen. It is one Up away, behind a visible
  ring. Making it visible at rest needs a layout change, which is the owner's
  decision, so the item stays partial.
- The display turning off after idle time is the device, not the app. The
  candidate sat on its Home on the disposable device at 1280 by 720 with no key
  pressed. At 20 minutes the power daemon turned the display off, and the
  lifecycle manager closed every app on it in one call, Calm Frames and the
  system launcher alike. This virtual device has no screensaver. Calm Frames
  was answering a routine media request half a second before. The lifecycle
  manager logs its exit as "after crash", 89 ms after its own kill named it,
  but the device's crash history stayed empty before and after. The window
  keeps its last frame while the display sleeps, so only the log shows the
  change. One Home press woke the device to its launcher, and Calm Frames
  relaunched on its Home with the same made-up household and no error. Not
  observed: idle during playback longer than 20 minutes, and a physical TV's
  own timeout.

### Item 11, 1280 by 720

- Parents, made-up household: Down from the last covers button reads the
  explainer stop in full, then "Credits and licences, button"; Left says
  "Back, button"; Right at the end stays.
- Profile chooser on the real household with the candidate at `4de7bd0`,
  opened and closed without choosing: "Who is watching? Kid, watching, radio
  button, checked", "Kid 2, radio button, not checked", and Back returns to
  "Kid is watching. Choose who is watching, button".
- Player controls on the disposable device, VoiceView on and Dolby kept as on
  the real device: Down shows the title, Back, the seek bar and the captions
  button, and Up reaches Back. VoiceView is silent while the video plays, as
  the system's Dolby dialog says it will be. It reads "McWay Falls. Resume at
  1:32, button" at the resume prompt, then "Back, button" and the seek bar's
  percentages as playback starts (the upstream limitation). Paused, it says
  "Paused. Press Play to continue.", and says it again each time the controls
  hide after a key press: the notice is drawn only while paused with the
  controls hidden, as a polite live region (`VideoPlayerUI.tsx`). The seek bar
  says nothing when focused (upstream). Recorded, not changed: the player UI
  was outside this pass.

### Item 12, what the candidate package carries

- `inventory.py` in the receipt reads the package without installing it: 31
  required and 2 optional native modules in the packaged manifest, one native
  library (`lib/aarch64/com.amazon.keplerscript.carousel.so`), and 83 npm
  packages in the Debug bundle's module table (658 files). The same for
  `d7ff886` and `a672f57`.
- Of the audit's 45 flagged packages, 42 sit where their exception group says.
  `@amazon-devices/react-navigation__native` and
  `@amazon-devices/security-manager-lib` are grouped as shipping but are not in
  this Debug bundle, which a Release bundle never exceeds; their native modules
  are still declared. `body-parser` (advisory 1243074, high) is not in the
  bundle either and has no exception. No exception was added, renewed or
  re-dated.
- The packaged manifest declares content personalization and EPG modules that
  no remaining component uses, because the build adds one per installed
  `@amazon-devices` package, and the package carries four build scripts among
  its assets (`make_logo.py`, `render.sh`, `render_qt.cpp`,
  `generate_menu_select.py`). Recorded, not changed.

### Packages

| Package | Bytes | sha256 |
|---|---|---|
| Candidate `a672f57` | 132,683,992 | `8cc0ffd52fc61df17d8b69b40c31964c5ed0749c578ec1de67e1aedf78173dd8` |
| Harness `19ba55d`, never merge | 130,748,986 | `10bc4fba7a0dbb5ba45ab2ee9fa2f72f3f7a274f2d760d677f2b900822f9ac17` |
| Harness `089ec6f`, never merge | 130,707,765 | `1b465aac12aa894bc83d18e280ed8f027e5b178e6f0edb5df1b72f539f497ac6` |
| Harness `50b5231`, never merge | 130,709,072 | `121c10e027dc23903fd3ce5130360c5aebdb94de06bf219c5981e40ff25e4325` |

The candidate's sha384 is
`480fd42d96096bb5a2b2c1a471fb0f498ab284118facd0561bdef19750e56506bded03dd3ec3e00204efced90ef30d59`.
Harness `0f182f9` was built and never installed.

### The main device, ready for the owner's review

- Back at its default size, with VoiceView off: a recording while focus moved
  twice on Home held no speech (mean -57.8 dB, against about -36.5 dB with
  VoiceView on).
- `a672f57` is installed package scoped over `4de7bd0`, keeping the household.
  The device reports the file's sha384, its first install time is unchanged,
  and it opens on the ordinary Home with the real household.
- The rollback package, the production build of `6a87937` (sha256
  `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d`), is kept
  read only. Calm Native Diagnostic, from an earlier pass, is still on the
  launcher.

The owner's PIN was not entered. Made-up PINs went in with every press
withheld, VoiceView off and nothing capturing. Nothing played on the real
household, so its saved places are as they were.

## What stays open

- Item 6: at rest the approved sentence starts below the explainer's edge, one
  Up away behind a visible ring. Making it visible at rest is the owner's
  layout decision.
- Item 11 stays partial: the seek bar's progress announcements (blocked
  upstream in Kepler UI Components 3.2.2); VoiceView's own Back or bare button
  as the resume prompt opens; reduced motion, which this virtual device cannot
  show; the paused notice repeating each time the controls hide (recorded, not
  changed); and a physical TV.
- Item 12: hosted CI on this exact source, the residual Audit findings and the
  exception decisions stay with the integration owner. Nothing was renewed or
  re-dated.
- Owner listening, palette, comfort and full-video review stay pending, on the
  installed `a672f57`.
- Nothing here signs off medical safety, human comfort or the 20 items.
