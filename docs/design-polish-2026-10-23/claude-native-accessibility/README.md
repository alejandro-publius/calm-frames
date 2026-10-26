# Native accessibility, original item 11

Base `6a87937`, branch `claude/native-accessibility-2026-10-24`. Local only:
nothing here is pushed, merged or published, and nothing here is integrated
into the product yet (see Integration below).

| Commit | Pass | Kind |
|---|---|---|
| `4d4152c` | 1 | Production fix: announcements, Details heading and hint, reading stops |
| `3ede1fa` | 1 | Production fix found on the device: the How it works ring was cut off |
| `0eab3c4` | 1 | Notes |
| `88c1716` | 2 | Production fix: Parents footer row, row states first, name field reachable, resume heading |
| `eeaaf16` | 2 | Production fix: Resume takes first focus alone on the resume prompt |
| `3b0174b` | 2 | Production fix found on the device: How Calm Frames works in Parents was never read |
| this commit | 2 | These notes |

The integration candidate is `3b0174b`. Two harness branches add a made-up
household and a seek bar study for checks on the device, and must never be
merged: `claude/native-accessibility-harness-2026-10-24-never-merge` (`5e48655`,
on `88c1716`) and `claude/native-accessibility-harness-v2-2026-10-24-never-merge`
(`4553ee3`, on `3b0174b`).

## How the app was heard

VoiceView on the Vega Virtual Device was switched on by holding Back and Menu
for three seconds through `inputd-cli`, as Amazon's React Native for Vega 0.83
accessibility page describes. It speaks the control that has focus and the
headings of a page as it appears. Text that cannot take focus is never spoken.

The device log does not carry what VoiceView says, so every flow was recorded
from the app window with its audio and transcribed on the Mac with a local
Whisper model. The recordings stay private; the transcripts are evidence.
When the system offered to disable Dolby so VoiceView could speak during
playback, Do not disable Dolby was chosen, so no system setting changed.

In the second pass, Parents and the name editor were heard in the harness: the
production Parents screen over a made-up household (Robin and Sam) kept in
memory, with the debug focus trace switched off. No real profile, name or PIN
was used for them.

## First pass, before and after, at 1920 by 1080

| Where | Before, `6a87937` | After, `3ede1fa` |
|---|---|---|
| Home card, McWay Falls | "McWay Falls, Ocean middle dot 5 minutes, button, not selected, selected" | "McWay Falls, 5 minutes, button, selected" |
| Home card, Sea Otters (drawn as Still scene) | "Sea Otters, Ocean wildlife middle dot 20 seconds, button, not selected" | "Sea Otters, Still scene, button, selected" |
| Home profile button (drawn as Kid) | "Choose who is watching, button" | "Kid is watching. Choose who is watching, button" |
| Details | "Watch: Sea Otters in Alaska, button" and nothing else | "Acadia. Watch: Acadia, button. Scenes replaced. Two scenes, seven seconds." |
| More info | headings, then Down skipped to Playback proof | Down lands on the text: "... not a medical device." |
| How it works | "How it works. Back, button. Check playback, button." | Down lands on the explanation, read to "... not a medical device." |
| Parents record | the heading only | "No scenes hidden yet." |
| Parents, Extra picture covers | "Extra picture covers, button" for every title | "Extra picture covers: Acadia, button" and so on |

What changed: the profile button says who is watching; a card says the line
drawn on it through `spoken()` in `copy.ts`; only the chosen card states
selected; the Details title is a heading and Watch carries the covered strip as
its hint; How it works, the More info safety text and the Parents record sit in
flush `ReadingStop`s the remote lands on, without moving at rest; Extra picture
covers names its title; and How it works gives its ring room inside its
scroller.

## Second pass: the five gaps

| Gap | Before | After, heard on the device | Status |
|---|---|---|---|
| 1. Parents footer | Right from Credits and licences, the last button, jumped several screens up to the 6 ft chip | Right from Credits and Left from Back stay put, Down stays, Up leaves the row; 1920 by 1080 and 1280 by 720 | Fixed |
| 2. Preset and switch rows | Each row read its description first and its state last | "Standard, chosen, radio button, checked", then the description; "Gentle artwork motion, off, switch, not selected", then its note | Fixed |
| 3. Name editor value | The name being typed could not take focus and was never read | Up from the keys lands on the field: "Sam. 3 of 16 characters"; each change is announced: "S. 1 of 16 characters", "Type a name. 0 of 16 characters", "Jo. 2 of 16 characters" | Fixed, checked with made-up names only |
| 4. Resume prompt | The title was not a heading, and Back took focus for a few milliseconds while the saved place loaded, heard as "Back, button" or a bare "button" | The video's name is a heading ("McWay Falls"), and Resume alone takes first focus: focus traces show Back in none of 6 openings, against 3 of 4 before | Partly fixed (below) |
| 5. Seek bar | "Current progress is N percent" every percent while a video plays | Unchanged | Blocked upstream (below) |

Found and fixed in the second pass: How Calm Frames works, at the foot of
Parents, was plain text the remote could not reach, so VoiceView never read it
or its approved sentence. It is now a flush reading stop. It is read in full at
both sizes with its whole ring, and the footer is still reached below it: Down
from the stop lands on Credits and licences, and Up from the footer comes back
to the stop.

How the fixes work:

- `FocusRow.tsx` wraps the footer in Kepler's `TVFocusGuideView` with Left and
  Right trapped. Jest's global mock of `TVFocusGuideView` renders nothing, so
  `jest.setup.ts` mocks `FocusRow` as a plain view, and `focusRow.test.tsx`
  checks the real row's traps against a recording guide.
- Presets and switches put the name, the chosen or on state and the role in the
  label, and the description in the hint, which VoiceView reads after a pause.
- The name field is a flush reading stop with a polite live region whose label
  is the draft and its length, so the keys do not move and each change is said.
  The label reaches VoiceView only; nothing writes the name to a log.
- The resume prompt's title has the header role, and Back no longer asks for
  first focus while the saved place loads. Recovery state, its transitions, the
  protection guards and playback authorization are unchanged.

### Resume prompt: what remains

Across 5 recorded openings of the fixed prompt (4 at 1920 by 1080, 1 at 1280
by 720), VoiceView read the heading in 4 and Resume in all 5. In one opening at
1280 by 720 it also said "Back, button" as the window appeared, and in one at
1920 by 1080 a bare "button" after Resume. The focus traces show no Back focus
in any of them, so these come from VoiceView's own reading as the window
appears, not from app focus. They are reported, not claimed fixed.

### Seek bar: the upstream limitation

The player's `app/src/components/Seekbar.tsx` wraps the SeekBar of Kepler UI
Components 3.2.2 (`@amazon-devices/kepler-ui-components`):

- `dist/src/components/SeekBar/SeekBar.js` line 616: the focusable `Pressable`
  gets no accessibility props, and line 617 passes the remaining props to
  `Slider`.
- `dist/src/components/SeekBar/Slider/Slider.js` line 57: `Slider` takes a
  fixed list of props and drops the rest, so a label, role or value given to
  the seek bar never arrives.
- `Slider` draws `ProgressBarWithSegments` or `ProgressBarWithoutSegments`,
  and both draw a view with `accessibilityRole="progressbar"` and the value
  "Current progress is, N percent." (`ProgressBar/ProgressBarWithSegments.js`
  lines 49 to 51, `ProgressBar/ProgressBarLight.js` lines 20 to 24), which
  VoiceView says again each time the value changes.

The harness tried four app-level arrangements with VoiceView on: the bar as
shipped; a named adjustable wrapper with its value every second; the same with
the value only on focus and after a seek; and the bar hidden from VoiceView
with a spoken line after a seek. In all four VoiceView kept saying "current
progress is N percent" every percent, and hiding the bar left it nothing to
land on. No supported app-level change stops it without patching or replacing
the kit's seek bar, which this item does not do. Integration request: a kit
release whose SeekBar passes accessibility props to its focusable element and
lets the app set or quiet the progress value.

## Reduced motion

The boat, the artwork entrance and the Harbor opening move only when the
household opted in, the app is active, reduced motion reports off and no
screen reader is running; anything unknown keeps them still. Their existing
tests cover reduced and unknown settings. No change was needed. On the device
it was not observed: the virtual device has no settings screen, and
`a11y-tv-util settings` answers "Error obtaining user profile object".

## Privacy

- The owner's PIN was not entered in the second pass. The first pass entered
  it four times with each press withheld from the record.
- The harness's made-up PIN was entered five times. Each time VoiceView was
  first confirmed off by ear, and no recorder, stream or log filter was
  running. A device log reader was, as the next point explains.
- A finding, disclosed: `vega device start-log-stream` reads the device log
  through a separate adaptor process (`vda ... loggingctl log -f`). That process
  outlives the stream when the stream is stopped. The check before a private
  entry looked for the stream, its filter and the recorder, but not for that
  reader. A reader left over from an earlier stream was confirmed running
  during the last made-up PIN entry. Earlier streams were stopped the same
  way, so readers were probably running during three earlier made-up entries
  as well; those can no longer be checked. Each reader's output pipe had no
  reader of its own, so nothing was written anywhere, no log file changed
  after its stream stopped, and the harness's focus trace is off. The check now covers the reader and refuses a
  private entry while any stream, reader, filter or recorder runs. Stopping a
  stream now ends its reader too. A test shows the old check letting a decoy
  reader and a decoy recorder through, and the new one refusing both.
- Only made-up names were typed (Sam, Jo, Samg). The harness logs hold no
  focus trace and no letter or keypad line.

## Packages and rollback

| Package | sha256 | Device sha384 |
|---|---|---|
| Rollback, `6a87937` | `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d` | `b268be99...` |
| `4d4152c` | `15f68f9810e21873ffbaddecface19a18de7a910ec925fbf99fe2d6f618c3f81` | `5e64a1b4...` |
| `3ede1fa` | `b4272a5f872afbc21b7296563c02ea03efee278dccdf3ca6ebb8b40703c8aad5` | `f28c9a96...` |
| `88c1716` | `eb00d6cda82e8a6c2ce42f43d0c958a5b7f512a70cd6943559a25db06f50bd7b` | `db345c97...` |
| `eeaaf16` | `b6550574423f8a63181d2258ac8b99e252e625e1bc1814707f5848e4a4f683d7` | `5de99634...` |
| `3b0174b`, candidate | `e0da8c73168e1a91f298f265e9632b0150b799485f7eeddd66f39f30787d8478` | `072c7916...` |
| Harness `5e48655`, never merge | `f6300da367045e1c740477d39f66a0eff340f552dd847b3e734b942483b47416` | `ea33633d...` |
| Harness `4553ee3`, never merge | `3b39ef5f87a61fba3f98004f0a9ba2e6a6ea4556aaaedd6ef52626c2328ef4f2` | `1b7c65be...` |

Each install was package scoped. The rollback package was installed last; the
device reports `b268be99`, Home is ordinary at 1920 by 1080, and VoiceView is
off (heard "VoiceView exiting", then silence on the D-pad). Nothing was
uninstalled, no storage was cleared, the PIN is unchanged, no setting was
chosen, and Dolby was left on.

Saved positions: the first pass moved McWay Falls' saved place from 0:36 to
0:55; its notes said "a few seconds", which this corrects. The second pass
opened the resume prompt about a dozen times and left each time with Back
without choosing, so the saved place stays at 0:55.

## Checks

- On `3b0174b`: `tsc --noEmit` exit 0; `npm run lint` 0 errors, with 104
  warnings, none in a changed file; `eval/style_check.py` exit 0.
- The full app suite on `3b0174b`: 175 suites passed and 1 skipped; 1868 tests
  passed and 4 skipped.
- `nativeAccessibility.test.tsx` holds the fixes in 27 tests;
  `focusRow.test.tsx` holds the row's traps; `nativePlaybackRecovery.test.tsx`
  adds the heading and first-focus tests.
- Deliberate breakages: 15 in the first pass and 10 in the second (M16 to
  M25), each seen to turn a test red.

## Integration

- The cloud follow-up `226d317` and its privacy changes are not in this
  repository, not on GitHub (no commit found) and not on this Mac. It is a
  missing integration input.
- Likely overlap: this branch changes `ProfileNameEditor.tsx` (the field in a
  reading stop with a live region), `ReadingStop.tsx` (two optional
  accessibility props) and `ParentAreaScreen.tsx` (labels, hints, the footer
  row and the explainer stop). It does not touch `trace.ts`,
  `CalmTouchable.tsx` or `PinKeypad.tsx`. A privacy change to name logging
  would most likely meet this branch in `ProfileNameEditor.tsx`.
- Item 6's onboarding fix `dd1ec6c` and its exports are separate and untouched.
- The harness branches stay out of production.

## Not covered

- Down from the Parents explainer to the footer at 1280 by 720 (heard at 1920
  by 1080; the explainer itself was heard at both sizes).
- The profile chooser and the player at 1280 by 720.
- Parents in the real household on the second pass builds; it was heard in the
  harness, which renders the same screen code.
- Reduced motion on the device, VoiceView during playback with Dolby on, a
  physical Fire TV and any human listening.

Nothing here signs off medical safety, human comfort or the 20 items.
