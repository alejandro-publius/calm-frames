# Native accessibility, original item 11

Base `6a87937`, branch `claude/native-accessibility-2026-10-24`. Local only:
nothing here is pushed, merged or published.

| Commit | Kind |
|---|---|
| `4d4152c` | Production fix: announcements, Details heading and hint, reading stops |
| `3ede1fa` | Production fix found on the device: the How it works ring was cut off |
| this commit | These notes |

There is no harness. The production Debug build was installed and heard.

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

## Before and after, at 1920 by 1080

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

The profile chooser, Back from playback, the name editor's keys and the
focus return after the chooser and the editor were already right and are
unchanged.

## What changed

- The profile button says who is watching.
- A card says the line drawn on it, through `spoken()` in `copy.ts`, which
  turns the separator into a pause and short units into words.
- Only the chosen card states selected. Focus selects a card one render after
  VoiceView reads its state, so a stated false was heard as "not selected,
  selected".
- The Details title is a heading, and Watch carries the covered strip as its
  hint. The strip and the hint use one summary, so they cannot disagree.
- How it works, the safety text on More info and the Parents hidden scenes
  record sit in flush `ReadingStop`s. The remote lands on them, so VoiceView
  reads them. A flush stop takes its ring's room from its margins, so the text
  does not move at rest; the How it works text area was pixel identical
  before and after.
- Extra picture covers names its title.
- How it works gives its ring room inside its scroller. On `4d4152c` the
  scroller's edge cut the left side of the ring off.

Copy, colours, layout, playback, covers, recovery, PIN and storage are unchanged.

## Found, not fixed

- Right from Credits and licences, the last Parents footer button, sends focus
  several screens up to the 6 ft seat chip. A focus guide would hold it, but
  the jest mock of `TVFocusGuideView` renders nothing, so the fix also needs a
  test setup change. Integration request.
- Parents preset rows and interface switches read their description before
  their state, so a quick move cuts the state off. Moving the description to
  the hint would put the state first.
- The player seek bar says "current progress is N%" for every percent while a
  video plays and the bar has focus. The Kepler UI Components seek bar drops
  the accessibility props it is given. Dependency; integration request.
- The resume prompt's title is not a heading, and one bare "button" was heard
  as it opened. That screen is recovery code, outside this pass.
- The name editor's draft cannot take focus, so the name being typed is never
  read. Typing feedback was not checked, because no name was typed.

## Reduced motion

The boat, the artwork entrance and the Harbor opening move only when the
household opted in, the app is active, reduced motion reports off and no
screen reader is running; anything unknown keeps them still. Their existing
tests cover reduced and unknown settings. No change was needed. On the device
it was not observed: the virtual device has no settings screen, and
`a11y-tv-util settings` answers "Error obtaining user profile object".

## Packages and rollback

| Package | sha256 | Device sha384 |
|---|---|---|
| Rollback, `6a87937` | `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d` | `b268be99...` |
| `4d4152c` | `15f68f9810e21873ffbaddecface19a18de7a910ec925fbf99fe2d6f618c3f81` | `5e64a1b4...` |
| `3ede1fa` | `b4272a5f872afbc21b7296563c02ea03efee278dccdf3ca6ebb8b40703c8aad5` | `f28c9a96...` |

Each install was package scoped. The rollback package was installed last; the
device reports `b268be99`, VoiceView is off and Home is silent on D-pad
presses. Nothing was uninstalled, no storage was cleared, the PIN is unchanged
and no setting was chosen. Resuming McWay Falls moved its saved place a few
seconds.

## Checks

- `tsc -p tsconfig.json --noEmit` and `eslint --max-warnings 0` on every
  changed file pass, and so does `eval/style_check.py`.
- The full app suite passes: 174 suites, 1860 tests, 4 skipped.
- `app/test/calmframes/nativeAccessibility.test.tsx` holds each fix in 22
  tests. Fifteen deliberate breakages each turned a test red at an assertion.

## Not covered

- 1280 by 720 was heard for Home and How it works only.
- Parents and More info were heard on `4d4152c`; `ParentAreaScreen.tsx` is
  identical in `3ede1fa`, and More info was heard again on it.
- VoiceView during playback with Dolby on, reduced motion on the device, a
  physical Fire TV and any human listening.

Nothing here signs off medical safety, human comfort or the 20 items.
