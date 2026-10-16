# Design acceptance: the final cohesive pass, October 16, 2026

Branch `claude/tv-experience-2026-10-16`, worktree
`/Users/alexvintera/calm-frames-claude-tv-2026-10-16`. Everything here is source and
headless checks. Nothing was built, installed, launched, driven, captured or recorded, and
the installed demo on the simulator is older than this source. The experimental detector
candidate stays disabled on its own branch; no threshold, map, media, signing or trust
setting changed.

## Requirements, what changed, how it was checked

| Requirement | What changed | Files | Automated check |
| --- | --- | --- | --- |
| Review fix: unavailable announcement must not promise sound or captions | The unavailable card now says "The picture stays hidden. Go back to the library." and its announcement says the title once | `app/src/calmframes/playerAccess.ts`, `app/test/calmframes/playbackCopy.test.ts`, `app/test/components/__snapshots__/Player.test.tsx.snap` (three wording lines, deliberate) | `playbackCopy.test.ts`, `Player.test.tsx` |
| Review fix: paused playback must not claim sound continues | Covering card while paused: "Paused. The picture stays hidden. Press Play to continue." Countdown while paused: "Paused, N seconds before the flashing. Press Play to continue, or Skip to jump past it." Announcements match | `app/src/calmframes/usePlaybackPresentation.ts` | `playbackCopy.test.ts` (seen red with the old line restored), `playbackUi.test.tsx` |
| Home: one deliberate composition for one featured video | Title, running time in words, one benefit line, Watch, Details; the "Choose a video" rail is gone when the hero already shows the only video; a rail returns with two or more videos; a lone title without hero art keeps its poster | `app/src/calmframes/KidHomeScreen.tsx`, `app/src/calmframes/copy.ts` | `homeComposition.test.tsx` (seen red with the rail rule reverted), `KidModeScreen.test.tsx` (one pin changed: the default shelf expects no card), `cinemaSelection.test.tsx`, `screens.test.tsx`, `returnFocus.test.tsx` |
| Benefit wording | "Watch prepared videos with flashing scenes covered." | `copy.ts` (`HOME_BENEFIT_LINE`) | `homeComposition.test.tsx`, `copy.test.ts` house style |
| Running time in natural language | "37 seconds" on Home and Details through one helper | `copy.ts` (`runtimeLabel`), `KidHomeScreen.tsx`, `TitleDetailsScreen.tsx` | `homeComposition.test.tsx`, Details pins |
| Consistent title placement across Home, Details, opening | All three heroes start at `CALM_FLOW.HERO_TOP`; the opening shell subtracts its eyebrow's line and margin so the title does not move on Watch | `KidHomeScreen.tsx`, `PlayerOpening.tsx` | `openingAlignment.test.tsx`, `tenFoot.test.tsx` |
| Exactly one preferred-focus request per screen | While How it works is open, only its Back asks; the profile button and Parents never ask alongside it; a poster that left the rail hands its request to Watch | `KidHomeScreen.tsx` | `homeComposition.test.tsx` focus sweep, `pickerFocusReturn.test.tsx` |
| Loading cancellation | Back on the opening shell leaves once; a stall timeout firing afterwards shows no recovery screen and leaves no second time | existing `PlayerScreen.tsx` behaviour, now pinned | `playerOpening.test.tsx` |
| Details: covered sections explained visually | See the Details section below | `coveredSections.ts`, `CoveredSectionsStrip.tsx`, `TitleDetailsScreen.tsx`, `FlashMapStrip.tsx` | `coveredSections.test.ts` (13, seen red with the clamp removed), `coveredSectionsStrip.test.tsx` (6), `detailDiscovery`, `shelf`, `duskLantern`, `returnFocus`, `tenFoot` |
| Interface sound | No change needed: confirm sounds stay opt-in, one per press, none on focus, none on Watch | `useInterfaceSound.tsx`, `interfaceSound.ts` | `interfaceSound.test.tsx` |
| Usability checklist for the owner | Five tasks with a per-task table, no participants or results | `docs/evidence/usability-checklist-2026-10-16.md` | none (a document) |

## Before and after, in words

**Home, one featured video.** Before: wordmark, profile button, How it works, Parents in
the header; a hero with "Acadia", "38 sec", Watch and Details; under it a "Choose a video"
heading and a single Acadia card repeating the hero. After: the same header; the hero
with "Acadia", "38 seconds", "Watch prepared videos with flashing scenes covered.", Watch
(primary, focused) and Details (quiet); nothing under it. With two prepared videos the
heading and the cards come back as before.

**Details, watch page.** Before: "Acadia", "38 sec", the description, Watch and More
info. After: "Acadia", "38 seconds", the description, a "Covered sections" line with a
still bar marking the parts the player will cover under the household's preset, the
covered total against the full length, then Watch and More info. Details of the block
are in the Details section below.

**Opening shell.** Before: the title sat lower than on Details. After: it sits at the
same height, under the "Calm Frames" eyebrow.

**Player, paused on a covered part.** Before: "Paused. Sound resumes when you press
Play." After: "Paused. The picture stays hidden. Press Play to continue."

**Player, nothing to check.** Before: "This video is unavailable. The picture stays
hidden while sound and captions keep playing.", announced with the title twice. After:
"The picture stays hidden. Go back to the library.", announced once under the title.

## Details section

- **Data.** `coveredSections(entry, settings)` in `app/src/calmframes/coveredSections.ts`
  returns one of four results: `unavailable` (the title has not verified or carries no
  segment list), `no-duration` (the running time is unknown, so nothing can be clamped or
  drawn), `none` (verified, with a running time, nothing to cover) and `ready` (the merged,
  clamped sections, their total and a sentence). The sections are exactly
  `buildCoverIntervals(entry.segments, { ...coverOptionsFor(benignStorySettings(entry.title, settings)), durationMs })`,
  the schedule the player follows, guard bands included; the total is of the merged
  sections, so an overlap is never counted twice. Nothing reads raw detector numbers.
- **Drawing.** `CoveredSectionsStrip.tsx`: the heading "Covered sections", a still 28 unit
  track with marks from the technical page's `stripMarks` arithmetic (ordinary covers in
  the pending colour, red flash covers in the failed colour), and the sentence. The block is
  `accessible` with the sentence as its label, takes no focus, answers no press and cannot
  seek. In the three states with nothing to draw only the sentence appears. It is named
  Strip because this Mac's file system cannot tell `CoveredSections.tsx` from
  `coveredSections.ts`.
- **Words.** Ready: "2 covered sections, 7 seconds of 38 seconds. The sound continues."
  (the demo says "2 simulated pauses, 8 seconds of 20 seconds. The sound continues.").
  None: "No sections of this video are covered." Unknown length: "The length of this video
  is unknown, so the covered sections cannot be drawn." Unavailable: "Covered sections are
  not available for this video." The sound is promised because playback continues through
  a cover; captions are not, because the schedule says nothing about tracks.
- **Where.** On the Details watch page, inside the hero copy after the description and
  before Watch and More info, for any playable title. `tenFoot.test.tsx` still passes with
  the block present, so Watch has not moved below its measured place.
- **Tests.** Boundaries (a section starting at 0, one ending exactly at the running time),
  overlaps merged before the total, a section beyond the running time clamped, unknown
  length, no sections, an unverified title, and equality with `buildCoverIntervals`.
  Mutation: with the clamp removed from the schedule call, two tests went red (ends of
  37500 and 40500 where 37000 was expected); restored and green.
- **Also on Details.** The running time reads "20 seconds" (and "Simulated demo · 20
  seconds"); the demo entry's label reads "20 seconds, 2 picture pauses"; the technical
  page's strip says "The sound continues when the picture changes." and its spoken key
  ends "The sound continues."

## Automated verification on the final source

| Check | Result |
| --- | --- |
| Full jest (`--testPathIgnorePatterns='uiCapture\|coastalExport\|controlStudy'`) | 140 suites passed, 1 skipped; 1375 tests passed, 4 skipped; 57 snapshots passed |
| Snapshot changes | one, `Player.test.tsx`: the three unavailable-card wording lines; deliberate |
| Typecheck | pass |
| Lint | 0 errors, 101 warnings (the existing baseline) |
| Style guard, doc-link guard | pass |
| Hook mirror | `node hook/tools/sync.mjs` produced no change; no mirrored file was edited |
| Mutations | rail rule reverted: 2 of 11 red; paused line reverted: 1 of 5 red; clamp removed: 2 of 13 red; How it works no longer clearing the picker request (earlier today): 1 of 4 red. All restored |
| Not run | `uiCapture`, `coastalExport`, `controlStudy` (capture and export suites, banned in this session) |

Pins changed on purpose: the default shelf expects no card under the hero
(`KidModeScreen.test.tsx`); running times read in words ("20 sec" to "20 seconds",
"20 sec · 2 picture pauses" to "20 seconds, 2 picture pauses") in `returnFocus`, `shelf`,
`detailDiscovery` and `duskLantern`.

## Remaining native visual checks

Headless tests establish what the screens render and what the route refuses. They do not
establish native appearance, visible focus, legibility at distance, audible sound through
a cover, caption drawing or real D-pad behaviour. After an approved build and install:

1. Home: the hero reads in one glance from the sofa; Watch is plainly the primary
   control; the benefit line fits on one line at 1080p; nothing sits under the hero.
2. Details: the covered sections bar and line are legible; Watch has not moved below the
   fold; Back returns to Home with Watch focused.
3. Watch: the title does not jump between Details and the opening shell; the first
   covered part shows the card and the sound continues; pause shows the paused line.
4. Profiles, Back, How it works; Parents, cancel: one visible focus each time.
5. Sound: no sound on focus moves; one confirm sound per press where the household
   turned it on; none on Watch.

Run the usability checklist only after those pass.
