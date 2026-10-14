# Working backwards: the picture break

Written Oct 13, 2026 on branch `claude/evidence-and-submission-2026-10-13`, from
`60eca59`. Nothing here comes from customer research: no interviews, surveys or
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
show anyone following a story they would otherwise have lost.

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
