# Editable kid names

Implemented October 23, 2026 by Claude Code (Fable) in the separate worktree
`calm-frames-fable-profile-names`, on the local branch
`claude/profile-names-fable-2026-10-23`. Nothing was pushed, merged, installed
or published. The frozen canonical branch, the installed package and the
submitted fallback are untouched. This is a development candidate for the
cloud integration owner to review.

## Exact source

| Role | Identity |
|---|---|
| Frozen canonical base | `2cf54e0d168e58daedfde3f15407833d23af4e93` |
| Starting point, from the verified bundle | `d7da316d2d48c3b66b3cc4874257e98ca5ef943e` on `codex/design-polish-2026-10-23` |
| Feature and tests | `9546c0f530e2bd99966c1836f2b9ae0246fb3dec` |
| Notes and previews | the commit that adds this folder |

The transfer ZIP's SHA-256 matched the brief, `shasum -a 256 -c SHA256SUMS`
passed on its members, and `git bundle verify` passed against the base in the
existing repository. The worktree's `git status` was empty at the start.

## What a parent sees

Inside unlocked Parents, choosing a kid in the Whose settings picker shows
**Edit name** beside Add a kid and Remove. Everyone has no Edit name. The
last remaining kid has Edit name and no Remove.

Pressing Edit name puts the editor where the picker and the buttons were, so
one name is being typed and nothing else in the group can move under it. The
rest of the page stays below. The editor has:

- a heading, New name for Sam, and a field showing the name so far with
  `3 of 16 characters` at its right edge;
- three rows of letter keys, then Shift, Space and Delete, built the same way
  as the PIN keypad: quiet cards, the saffron ring and lifted fill on the key
  with focus, the ring's width reserved on every key. Focus opens on A;
- Save name and Cancel.

Case takes care of itself: the first letter of each word is a capital and the
rest are small. Shift turns the next letter the other way once, and every key
shows the case it will type. One space is allowed between words, none at the
start and none twice in a row. At 16 characters the letter keys stop and the
field says `A name can be up to 16 characters.` in the count's place.

Save refuses, in words in that same place, a blank (`Type a name before
saving.`), a name another chip already carries in any case, and the word
Everyone (`Robin is already in this household. Choose a different name.`).
Saving an unchanged name closes the editor without a write. A kid may keep
their own name in a different case.

While the write is in flight the Save button reads `Saving the name…`, and
every key and button stays in the focus order and ignores presses. The editor
closes only when the household write reports true. Focus then returns to
Edit name, and the picker chip reads the new name.

If the write reports false, the draft stays, and a notice (`Name not saved
yet`) offers Try again, which takes focus, and Cancel. Cancel and the
remote's Back both discard the draft, write nothing, and return focus to Edit
name. Back does nothing while a write is in flight, because the write cannot
be taken back. A second Back is the route's to answer, as before.

Add a kid is unchanged: the new kid is still Kid or Kid 2, and the editor
renames that kid.

## Input method, and what was verified

The brief asked for the installed Vega input API to be verified before use.
The locked install's `@amazon-devices/react-native-kepler` ships
`TextInput` with a Kepler native component and two Kepler-only props,
`auxOptions` ("additional context to a TV-based keyboard") and
`keyboardUiMode` (`half-screen`, `full-screen`). So the API is installed and
documents an on-screen keyboard.

Nobody on this project has observed that keyboard on the Vega Virtual Device:
the repository's own comments and decisions say the parent area has no
keyboard, and no capture or log shows one. This assignment forbids installing
a package, so the keyboard could not be observed here either. The PIN keypad,
built from the same key component, has been pressed on that device many
times. The editor therefore uses letter keys, which is the path known to
work, and the component's header says so. A `TextInput` beside the keys is a
small later change once the keyboard has been seen. No browser field and no
dependency were added.

## How the save reports its result

`ParentAreaScreen` gained `onRenameProfile?: (family: Family) =>
Promise<boolean>`. Edit name is offered only when it is given, because the
existing `onFamilyChange` returns nothing and an editor that closed on a void
return would be reporting a save it never saw.

`KidModeScreen.setFamily` now returns the household write's own answer: the
`Promise<boolean>` from `useSavedHousehold.write`, or `false` when the record
is not ready. Its other callers ignore the value. The screen passes
`onRenameProfile={setFamily}`. No other route behavior changed.

The route's existing save-error path is unchanged and was inspected first.
When a household write throws, the hook marks the record as failed and
`KidModeScreen` replaces Parents with the storage screen, whose Try again
re-writes the pending record. For a rename, that pending record is the
renamed household, so the typed name is the retry, and Parents comes back
behind the PIN as it does for every failed write. The route test writes this
down. The in-editor Try again and Cancel cover a write the hook refuses
without throwing, which returns false and leaves Parents on screen.

## Preservation

`renameProfile` maps by id and copies every other field. The tests assert
that the family passed to the save equals the original with exactly one
name changed: same ids, same per-kid settings, same active kid, same floor,
same chime and interface flags. Hide logs and playback checkpoints are keyed
by profile id in stores outside the family record, so a rename cannot reach
them; the route test records a hide for the kid before the rename and reads
it back after. Nothing about the PIN changed.

## Files

Owned implementation lane only. No dependency, lock, SBOM, pipeline,
analyzer, player, recovery, signing, media, catalog, theme, Home island,
onboarding, root README, checklist or demo file was touched, and no mirrored
engine file changed, so `hook/tools/sync.mjs` had nothing to do.

| File | Change |
|---|---|
| `app/src/calmframes/ProfileNameEditor.tsx` | New. The keys, the field, Save and Cancel, the refusal words, the failure notice. |
| `app/src/calmframes/ParentAreaScreen.tsx` | Edit name button, editor in place of the picker, result-aware save, Back handling, focus return, the edit-name frame. |
| `app/src/calmframes/profiles.ts` | `nameProblem`, `namesTakenFor`, `profileNameProblem`. `renameProfile` and its limits are unchanged. |
| `app/src/calmframes/copy.ts` | The editor's words and the `NAME_SAVE_FAILED` notice. |
| `app/src/calmframes/uiFrames.ts` | `PARENT_EDIT_NAME_FRAME`, declared and listed in `ALL_UI_FRAMES`. |
| `app/src/screens/KidModeScreen.tsx` | `setFamily` returns the write's result; `onRenameProfile` passed to Parents. |
| `app/test/calmframes/profileNames.test.tsx` | New. 21 tests: the button, typing, refusals, saving, pending, failure, Back, Cancel, Add a kid. |
| `app/test/screens/profileNameSave.test.tsx` | New. 2 tests through the route with a memory disk: the committed write and the failed write's retry. |
| `app/test/calmframes/profiles.test.ts` | 5 tests for the name checks and for what `renameProfile` leaves alone. |
| `app/test/calmframes/copy.test.ts` | The new words join the dash and notice checks. |
| `app/test/calmframes/uiCapture.test.tsx` | The edit-name frame is compared with the rendered tree, listed, and walked. |
| `app/test/calmframes/tenFoot.test.tsx` | The editor is a measured case: text size, text contrast, every key's focus ring. |
| `docs/design-polish-2026-10-23/fable-profile-names/` | These notes, the checks, the mutation record, the preview fixture and renderer, and the renders. |

## Checks and results

Run with the repository's locked install, Node 22.23.2 and npm 10.9.8, with
no flags changed and no guard silenced. Exact commands and outputs are in
[checks.json](checks.json).

- `npm run typecheck`: clean.
- `npm run lint`: 0 errors. The 104 pre-existing warnings are in files this
  change did not touch; the touched files lint clean with `--max-warnings 0`.
- Focused suites, `npx jest --coverage=false`: profileNames 21 passed,
  profileNameSave 2 passed, profiles, copy, uiCapture, tenFoot,
  parentNavigation, hardwareBack, profilePicker, hookMirror and
  householdRestart all passed.
- Full `npx jest` with coverage and its thresholds: see checks.json for the
  final run on the committed source.
- `python3 eval/style_check.py`: no dashes and none of the three words.
- Mutations, in [mutations.json](mutations.json): ten guards broken on
  purpose, one at a time, and all ten caught by a red test. The pending guard
  in the save handler stayed green on its first run, because the editor's own
  saving gate stops a second press after a re-render, so a test was added for
  two presses in one frame and the mutation was run again and caught.

## Previews

[preview/1080](preview/1080) and [preview/720](preview/720) hold renders of
seven states: the kid selected with Edit name focused, the editor open, typing
with Shift held, a refused duplicate, a save in flight, a failed save with Try
again focused, and the renamed picker with focus back on Edit name. States
that scroll have a second render scrolled to the editor.

These are browser approximations of exported React Native host trees, drawn
by Chromium with the app's own fonts and styles through the existing
`eval/preview/render_harbor.py`. They are not Vega captures and not evidence
of native layout or focus. The 720p set is the 1080p tree drawn at two
thirds, where the device rounds each unit on its own. The fixture and script
are in [preview](preview); the fixture is copied into `app/test/calmframes`
to run and removed afterwards, and it uses an in-memory household with a
fixture PIN. Robin, Sam and Ash are fixtures.

[preview/bounds.json](preview/bounds.json) records the watched controls'
boxes. At both sizes every watched control sits inside the horizontal 5%
safe area, and Save sits inside the first viewport's safe area while the
editor is open, typing, refusing or saving. The failed-save state's Try again
is below the first viewport; it holds preferred focus, so the page scrolls to
it on a device, and the scrolled render shows it.

## What still needs a device

- Remote travel through the keys, the field's live region, Shift's spoken
  state and VoiceView wording, on the exact source.
- Focus returning to Edit name after Save, Cancel and Back, and the header's
  Back staying quiet while it does.
- Whether the Kepler on-screen keyboard appears at all, which decides whether
  a `TextInput` should join the keys.
- The failed-save path on a device: the storage screen, its Try again, and
  Parents returning behind the PIN.
- Human reading comfort of the key grid and the field at ten feet.

## Limits

- Letters and spaces only. No digits, punctuation or accents. Names the
  model allows but the keys cannot type are left as they are.
- A rename that fails because storage threw follows the route to the storage
  screen, so the editor is not on screen for that retry; the draft survives
  as the pending write.
- No docs/DECISIONS.md or docs/STATUS.md entry was written, because those
  files are outside the owned lane. The reasoning is here instead.
