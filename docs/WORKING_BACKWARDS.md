# Working backwards: the picture break

Written Oct 13, 2026 on branch `claude/evidence-and-submission-2026-10-13`,
begun on `60eca59` and rebased onto `e51529c`, the native branch head at handoff. Nothing here comes from customer research: no interviews, surveys or
user tests have taken place. Every customer statement below is a hypothesis.

## 1. The one page

**Who is the viewer?** *Hypothesis H1.* A parent at home with a child who is
photosensitive, watching a title from the Calm Frames library together, remote
in the parent's hand. The child may also hold the remote.

**When does the current experience fail them?** *Hypothesis H2.* Mid-story,
something on screen worries them and Calm Frames has nothing planned for it.
Detection can miss flashing: in the synthetic evaluation, recall near a limit
was <!--n results/conformance_current_report_2026-10-02.json:published.recall_near_limits -->0.469<!--/n-->
against <!--n results/conformance_current_report_2026-10-02.json:published.flashmap_recall -->0.85<!--/n-->
overall. A busy, bright stretch can also sit below every published limit and
still be one this family would rather not watch. Today the product only acts
on parts its map flagged; at any other moment the family is on its own.

**Why are the ordinary options inadequate?**

- **Pause** stops the story for everyone, and Play brings back the same scene.
- **Mute** removes the wrong sense.
- **Looking away** depends on the child noticing in time. The screen keeps
  changing in the room, and the child loses track of the story.
- **Skip** exists only on a flagged part, and seeking forward blindly jumps the
  story by a guessed amount.

**What concrete improvement would make them choose Calm Frames?** *Hypothesis
H3.* One remote press hides the picture while sound and captions carry the
story on. One more press brings the picture back, and it never comes back a
moment before a planned hold. It works on every title in the library, flagged
or not, and it moves no playhead.

**What evidence would disprove the assumption?**

- In the walkthrough in section 5, fewer than four of five adults can say how to
  start and end a break after one demonstration, or most say they would pause.
- Parents tell us story continuity does not matter at that moment: they stop the
  show whatever the app offers.
- On the Vega Virtual Device the Menu key never reaches the app, or focus lands
  on the player controls so that OK does something other than return.
- An accessibility reviewer judges a covered screen with continuing sound to be
  no better than pause for this family.

## 2. Three candidates, checked against what exists

| | 1. Viewer picture break | 2. Compare viewing experiences before starting | 3. Creator path for an owned clip |
|---|---|---|---|
| Already exists? | No. Covers come only from the signed schedule. Pause, Skip on a countdown and the guarded seek are the only viewer actions. | Mostly. The details page draws the hold timeline (`FlashMapStrip.tsx`), explains the household's settings (`ViewingPlan.tsx`), and the labelled Harbor demo is a live preview. | Mostly. `pipeline.local_library prepare` runs analysis, signing and verification in one command; `packaged_library export` and a rebuild put it on the shelf. |
| Customer benefit | Covers the case detection misses, at the moment it matters, without stopping the story. | Small: presets are chosen once by a parent at setup, behind a PIN. | Real for a creator, invisible to the family watching. |
| Differentiation | New behavior; no ordinary player control keeps the story going with the picture hidden. | Repackages information the details page already shows. | A wrapper over a path that already works. |
| Demonstrability | One press on the simulator remote, in under ten seconds of footage. | Static screen. | Terminal output and a rebuild. |
| Effort | Small: two new modules, one card, a flagged hookup in the player. | Medium: touches the details page under active redesign. | Small to medium, mostly documentation. |
| Risk | Must never remove a cover, flash through repeated presses, or steal OK from the player. All three are testable. | Low. | Low; key handling for creators adds support burden. |
| Decision | **Build.** | Reject for now: little added value. | Reject for now: wrong audience for this session. |

A fourth idea was considered and set aside: speaking a short description of the
hidden picture. It needs authored text for every title and cannot be shown
reliably this week.

## 3. Does the Harbor film show the value?

Only partly. Harbor's sound is synthesized water ambience and its captions
describe the picture ("Sunlight follows the ripples"). During a hold, the
captions describe a picture the viewer cannot see, and nothing in the sound
carries a story. The demo proves the cover and captions stay up; it does not
show anyone following a story they would otherwise have lost. Since `d52d657`,
Harbor's captions start Off as optional scene descriptions, so a break on
Harbor carries on with water sound alone unless the viewer turns captions on.

A short separate scene with two or three spoken lines that cross each hold would
show continuity far better. It must be a new benign title with its own signed
artifacts, built through the production path in `eval/benign_story.py`, and a
new shelf entry. That touches the catalog and the native build, so it is a
proposal here, not work done. The voice needs rights checked first. Recording
Alex's own voice is the simplest rights-clear option. Synthetic system voices
need their licence terms read before use, and the existing demo narration,
which uses macOS Samantha, should get the same check.

The picture break needs no new media: it works on both existing Harbor titles.

## 4. Acceptance criteria, written before the code

Automated, in this branch:

1. **One press.** From playback of a verified title, a Menu press puts the cover
   up in the same render. Playback is not paused and no seek is requested.
2. **Caption choice kept.** The break never changes the caption track. Its card
   says captions keep playing only when they are on, and says they are off
   otherwise.
3. **A clear way back.** During a break the card offers a focusable "Back to the
   picture" control. OK or Menu asks for the picture back.
4. **Predictable return.** The picture returns only when the break has lasted at
   least two seconds, the playhead is outside every scheduled hold, and the next
   hold is at least two seconds away. Until then the card says when it will
   come back, and it returns by itself once those hold.
5. **Only adds cover.** For every input sequence, the screen is covered whenever
   the signed schedule alone would cover it. An unverified or blocked title gets
   no break and keeps its existing card.
6. **No flashing by remote.** Over any one second, presses can add at most two
   cover changes to what the schedule makes. With no schedule, there are never
   more than two changes in any one second. The three-flashes rule this stays
   under is quoted in `flashmap/docs/SPEC_SOURCES.md` section 1.
7. **No history.** A break is not written to the exposure history.
8. **Off by default.** With the prototype flag off, the player behaves as
   before, and the existing player suites pass unchanged.

Native, owned by Codex and untested here: the Menu key reaches the app; focus
lands on "Back to the picture"; OK returns without pausing; no frame of picture
shows between the press and the cover in a recording.

Not claimed by any of the above: that viewers understand or prefer the feature.
Section 5 is the protocol for that, and it has not been run.

## 5. A short adult walkthrough, not yet performed

Five adults who have not seen the app, one at a time, on the simulator or a
recording of it. No children, no flashing content, Harbor only. About ten
minutes each.

1. Play the 30 second demonstration in section 8 once, with no explanation.
2. Ask: "If something on screen bothered you during a show, what would you do
   with this remote?" Note whether the Menu press is mentioned.
3. Ask: "What happened to the story while the picture was hidden?"
4. Hand over the remote during Harbor and say only: "Hide the picture, then
   bring it back." Count presses and note any OK press that paused instead.
5. Ask which they would use for a worrying scene: pause, the picture break, or
   neither, and why.

Record answers verbatim with permission and no names. The H3 hypothesis fails
if fewer than four of five complete step 4 unaided or if most choose pause in
step 5. Until this runs, comprehension and preference are unknown.

## 6. What was built

All of it is in the app, behind `PICTURE_BREAK_PROTOTYPE` in
`app/src/calmframes/pictureBreakConfig.ts`, which is `false`. Switched off, the
player behaves as before.

- **`pictureBreak.ts`** holds every rule as pure functions: start, ask for the
  picture back, when a return may happen, the grace after it, and the wording.
- **`usePictureBreak.ts`** feeds those rules the clock, the playhead and the
  remote. Menu starts a break or asks for the picture back; OK asks for it back
  during a break.
- **`PictureBreakCard.tsx`** draws the card above the cover and clear of the
  captions. Its spoken text and its "Back to the picture" button are separate
  accessible elements, and the button takes D-pad focus.
- **`PlayerScreen.tsx`** joins them in five small places: the hook call, the
  cover, the capture frame, the card, and which control owns OK.

How the rules keep the remote safe:

- The screen is covered whenever the signed schedule alone would cover it.
- A break shows the plain cover, never a scene still.
- A break lasts at least two seconds before the picture may return. Hiding is
  never delayed.
- The picture never returns inside a hold or less than two seconds before one,
  because a return there would show the picture briefly and cover it again.
  A request held back is kept, the card says why, and the picture returns by
  itself once it can.
- For one second after a return, OK still belongs to the break. Without this,
  pressing OK twice to get the picture back paused the film on the second press.
  That defect was found while building and is now guarded by tests.

The break never seeks, pauses, changes the caption track or writes exposure
history. It exists only for a guarded title whose map verified.

## 7. Before and after

| Moment | Before | After, with the prototype switched on |
|---|---|---|
| Something unflagged worries the family mid-story | Pause stops the story; Play brings back the same scene. Looking away or muting are the other options. | One Menu press covers the picture. The film keeps playing, and sound and captions carry the story. |
| Coming back | Play resumes exactly where the worrying scene was. | OK brings the picture back where the story has reached, never inside a hold or a moment before one. |
| Pressing several times | Not applicable. | Presses add at most two cover changes in any second, and a second OK cannot pause the film. |
| Steps | Two presses: pause, then play. | Two presses: hide, then return. The count is the same; what changes is that the story keeps going. |

The evidence is automated, from `results/picture_break_2026-10-13.json`. The
full app suite passed
<!--n results/picture_break_2026-10-13.json:checks.full_app_suite.passed -->1354<!--/n-->
tests with
<!--n results/picture_break_2026-10-13.json:checks.full_app_suite.skipped -->4<!--/n-->
skipped. Of these,
<!--n results/picture_break_2026-10-13.json:checks.full_app_suite.existing_tests_passed -->1198<!--/n-->
are the existing tests, the same count the native branch recorded on `e51529c`
before this change. The picture break suites passed
<!--n results/picture_break_2026-10-13.json:checks.picture_break_suites.passed -->156<!--/n-->
tests. Each of eleven deliberate breaks of a rule or a hookup turned tests red,
and each restored file passed again. No native build, recording or viewer
test has happened.

## 8. A 30 second demonstration

Every shot needs fresh native capture with the prototype switched on. A
browser render cannot stand in for any of them. Use the prepared Harbor, which
has no practice holds, so the only cover on screen is the viewer's own. Turn
English captions on from the caption menu before recording, because Harbor's
captions start Off.

Film times come from Harbor's caption file, `app/assets/raw/benign-story/harbor.vtt`.

| Time | Picture | Subtitle |
|---|---|---|
| 0:00 to 0:03 | Prepared Harbor from its start, caption "Evening settles over the water." | Mid-story, something on screen worries you. |
| 0:03 to 0:05 | Menu pressed at about 2.5 seconds of film, labelled on screen; the cover and the Picture break card appear. | One press rests the picture. |
| 0:05 to 0:14 | The covered screen while three captions change, from "A small boat rests in the harbor." to "The lighthouse watches over the bay.", and the water sound continues. | The story keeps going in sound and captions. |
| 0:14 to 0:20 | OK at about 12.5 seconds of film; the picture returns on the lighthouse, later in the story. | One more press brings the picture back. |
| 0:20 to 0:30 | Editorial card. | It never moves the story, and never comes back a moment before a planned hold. A prototype. Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device. |

Harbor has no dialogue, so the captions carry the continuity in this cut
(section 3). A separate recording on the practice demo can show a return held
back: ask for the picture at about 10.6 seconds, and the card says a hidden
part is coming up. That shot is for acceptance, not for the 30 seconds.

## 9. Handoff to the Codex native task

1. **Integrate.** The branch `claude/evidence-and-submission-2026-10-13`
   starts at `e51529c`, the native branch head, and adds `b9a2299` (this
   brief), `06dfeb9` (the implementation) and the evidence commit. If the
   native branch has not moved, it fast-forwards. Only `app/src/screens/PlayerScreen.tsx` is shared with
   existing work; every other file is new.
2. **Rebuild either way.** The merge changes `PlayerScreen.tsx`, so the
   `dba88d5` package and its receipts no longer describe the source, even with
   the prototype switched off.
3. **Check natively with the prototype on**, in a local build only:
   - The remote's Menu key reaches the app. Confirm the key name with
     `inputd-cli --help` before using it in `vega device run-cmd`.
   - The cover and card appear while the film's sound and captions continue.
   - Focus lands on "Back to the picture" with the gold ring.
   - OK brings the picture back after two seconds, with no pause indicator.
   - Two quick OK presses do not pause the film.
   - On the practice demo, a return asked for at about 10.6 seconds waits
     until the second practice hold has ended.
   - VoiceView reads the card and reaches the button separately.
   - Record the time from the Menu press to the cover. Nothing here claims it.
4. **Ship it on only if those pass.** If Menu never reaches the app, keep it off
   and consider a "Picture break" button in the control bar instead.
5. **Owned by Codex and not done here.** The card wording is proposed and lives
   only in `pictureBreakCopy`. Nothing in the interface tells a viewer about
   Menu yet; one line on the details page or the paused screen would. Menu
   still brings up the player controls, as every key does; the controls could
   ignore Menu while the break owns the remote.
6. **A defect in the new Skip focus fix.** `Seekbar.tsx` now takes
   `hasTVPreferredFocus`, but its `React.memo` comparison ignores that prop, so
   the value only changes when the seekbar remounts. A countdown that appears
   while the controls are mounted leaves the seekbar claiming preferred focus,
   and so would a picture break. The reproduction in
   `results/seekbar_focus_repro_2026-10-13/` fails on `e51529c` and passes
   with the one-line patch beside it; the existing playback suites still pass
   with the patch. It is not applied here, because the seekbar is yours.
7. **A test helper caution.** The shared harness's `remote()` calls whichever
   key listener registered last, which after a state change in the player
   screen is that screen's own listener. No existing test uses it. The new
   tests use `pictureBreakKeys.ts`, which delivers each press to every current
   listener at once.

## 10. What is implemented, proposed and untested

- **Implemented, with automated evidence:** the rules, the hook, the card, the
  flagged player hookup, and the tests listed in the receipt.
- **Proposed only:** a dialogue scene for continuity, discoverability copy, a
  control bar entry, Menu handling in the player controls, final card wording.
- **Untested:** Menu delivery on Vega, native focus, press-to-cover latency,
  VoiceView, and whether viewers understand or prefer the break.
