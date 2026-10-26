# Honest playback states and a steadier remote, October 16, 2026

Status: source change only, on `claude/tv-experience-2026-10-16`, based on
`63a0bcb` (`codex/dark-cinema-2026-10-16`). The running app was not rebuilt,
installed, launched, restarted, navigated, captured or recorded in this pass.
No media, map, key, trust setting, catalog, threshold, parental control or
cloud resource changed.

## What changed for the person holding the remote

- **The app says what it does, from the data.** How it works, More info, the
  first run explainer and the viewing plan said flashing scenes are "replaced
  by a still picture" and that "sound and captions continue". The featured
  Acadia maps carry no scene hold, so its three covers are plain black, and
  its rendition has an audio track and no caption track. Those pages now say
  flashing scenes are covered while the sound continues, and More info names
  captions only for a title that ships them. The line about a title's own
  covers is built from its schedule and caption list, so it cannot drift from
  the data again.
- **Two quick presses on Watch start the player once.** The route latches on
  the first launch and opens again on the navigator's focus event, the same
  event that restores the controls on return.
- **Back from the profile picker puts focus on the button that opened it**,
  by the rule How it works already used; the header panel dismissed last
  takes focus.
- **An altered prepared route now has a regression suite** naming what a
  person sees: no opening shell, no media load, one unavailable card with a
  way back, and the route leaves once.

Nothing visual was restarted. The dark cinema palette, the Acadia imagery,
the faces, the shared button, header and surface components, the focus ring
and the one-video rail Codex shipped on Oct 16 are unchanged.

## Priority C audit: what decides what the viewer sees

The chain, as the code runs it, from a catalog entry to the cover and card:

1. **Catalog entry.** `defaultCatalog` in `app/src/screens/KidModeScreen.tsx`
   lists the compiled prepared library filtered to the approved Acadia source
   hash, plus the gradient playback check. `packagedLibrary` (`packagedLibrary.ts`)
   parses the compiled catalog with structural checks, and the Acadia
   catalog is accepted only when its bytes, bundle id and public key are the
   approved ones (`createApprovedAcadiaLibrary`).
2. **Shelf.** `useMapSources` (no registry is configured, so the catalog's own
   maps are used) then `checkTitle` (`titleStatus.ts`) verifies every map the
   preset asks for with the Ed25519 reader against the title's source hash,
   the key returned only on an exact identity match, and the household room.
   `kidModeTitles` lists verified titles only. Details shows a Watch control
   only when `noticeForTitle` is null and `evidenceFor` finds the exact
   compiled title; otherwise it shows the notice and one Back.
3. **Launch.** `play` builds `titleDataFor` and `guardedParamsFor` from the
   same checked entry the shelf listed and navigates with both.
4. **Player gate.** `PlayerScreen` asks `packagedLibrary.acceptsRoute` for any
   prepared title: exact uri, source hash, duration, rendition hash, offset,
   map texts, caption list, MP4 format, title id, no map URLs, and settings.
   A refused route gets no guard parameters, so `playbackAccess` answers
   `unguarded`: the cover stays on, the card is the unavailable card with
   "Go back to the library", and `preBufferVideo` is never called, so no
   file, original or otherwise, is opened. An accepted route hands the guard
   the key for that exact match only (`publicKeyForRoute`).
5. **Guard.** `useFlashGuard` verifies the maps again, builds the schedule,
   and reports `status` as loading, verified or blocked. `covered` is true
   unless the status is verified, the player is ready, the schedule says the
   playhead is outside every interval, and no seek is holding. A scene still
   is offered only on verified status with a signed hold for the current
   interval and no uncertainty.
6. **Shell, error and buffering.** The opening shell shows only while the
   route is guarded, not blocked and not failed, and is swapped on frame
   evidence or the media clock advancing (`useOpeningFrame`); fifteen seconds
   without either is a playback error. A player error keeps the cover on,
   removes the card and shows the recovery screen with one Back. The loading
   plate appears only after a second of waiting and never covers or uncovers
   anything.

Where a cosmetic value, rather than verified state, drove what the user saw:

- **More info's cover sentence** said a still picture replaces the scene and
  that captions continue, whatever the maps and the rendition carried. Fixed:
  `coverLine` in `copy.ts` reads the schedule length and the caption list.
- **How it works, the first run explainer and the viewing plan** carried the
  same still-picture promise as fixed text. Fixed to "covered".
- **The player card** (`cards.ts`, mirrored into the hook package) said
  "Sound and captions continue while this scene is hidden" for every title,
  including Acadia, which has no captions. Fixed on review: the covering card,
  its paused variant and the after card now say the sound continues, the
  announcements say the same, and the mirror was regenerated with the sync
  tool. The unavailable card's line in `playerAccess.ts` still names captions
  and is noted below.
- `showHomeOpening` is a route flag that only chooses the opening shell. It
  never affects the cover. The player's title line comes from the route and
  is shown even over a refused route's unavailable card; identity is checked
  by `acceptsRoute`, not by the title text.

Checked by existing headless tests, unchanged: a missing, tampered, stale,
wrong-file or over-offset map keeps the picture hidden with a reason
(`useFlashGuard.test.tsx`); seeking into an interval or its guard band covers
first (`seekSafety.test.ts`, including spoken and transport seeks); pause keeps
the card and the cover (`playbackUi.test.tsx`); Back and background leave once
(`playerWiring.test.tsx`); leaving during initialization attaches nothing
(`VideoHandler.test.ts`); the household record failing to load or save keeps
the library closed (`householdRestart.test.tsx`); a player error paints above
the retained cover with one focused Back (`playbackUi.test.tsx`).

Added in this pass: `playerRouteRefusal.test.tsx` (nine refused routes plus the
control), `repeatedPresses.test.tsx`, `pickerFocusReturn.test.tsx`, and the
captions and wording checks in `copy.test.ts` and `detailDiscovery.test.tsx`.

On review, two more fixes: How it works clears the picker's standing focus
request, so on the Acadia-only shelf the sequence Profiles, Back, How it works
leaves exactly one control asking for focus, the explanation's Back button
(regression in `pickerFocusReturn.test.tsx`, seen red with the clearing line
removed). And the cards no longer promise captions (above). Still naming
captions, on purpose and noted: the unavailable card's announcement in
`playerAccess.ts` ("while sound and captions keep playing") and the Harbor
demo's own card copy in `benignStory.ts`, which describes a title that ships
captions.

## Audio continuity: what is and is not established

Headless: the cover is a view drawn above the video surface and below the
captions view (`CoverLayer.tsx`); the schedule driver listens to media events
and never calls pause, mute or volume on the element (`useCoverHarness.ts`);
`coverHarness.test.tsx` shows the cover following the playhead through
intervals, buffering, seeking and background. This is planned-interval
evidence about the app's own layer. The prepared output verification
("cover proven drawn" in the compiled catalog) is the pipeline's check on the
rendition's pictures. Neither is a measurement of audible sound on the
simulator or a device, and no such measurement was taken in this pass. The
Oct 15 and 16 receipts already record that audio still needs a native check.

## Exact copy, before and after

| Where | Before | After |
| --- | --- | --- |
| How it works, line 1 | Calm Frames replaces flashing scenes with a still picture. Sound and captions continue. | Watch selected videos with flashing scenes covered while the sound continues. |
| How it works, line 2 | Videos are checked before they are added. This only works with videos in Calm Frames, not other apps or live TV. | When a video has captions, the captions continue too. Every video is checked before it is added. |
| How it works, line 3 | (none) | This only works with videos in Calm Frames, not other apps or live TV. |
| More info, title's own covers | A still picture replaces brief parts of this video. Sound and captions continue. | Brief parts of this video are covered. The sound continues. (plus "Captions continue too." only when the title ships captions; "One brief part" for a single cover) |
| More info, purpose | Calm Frames replaces flashing scenes with a still picture while sound and captions continue. It only works with videos in this app. | Watch selected videos with flashing scenes covered while the sound continues. It only works with videos in this app. |
| First run explainer, line 2 | Flashing scenes are replaced by a still picture. Sound and captions continue. | Flashing scenes are covered while the sound continues. Captions continue when a video has them. |
| Viewing plan (Technical details) | Flashing scenes are replaced by a still picture while sound and captions continue. A larger TV or a closer seat can hide more of the video, never less. | Flashing scenes are covered while the sound continues, and captions continue when a video has them. A larger TV or a closer seat can hide more of the video, never less. |

The explainer stays inside its reading budget (`copy.test.ts`). No line uses
"safe", "guaranteed", "nothing flagged", "test cases validated" or "the
picture never holds", and the house style test now reads the new lines.

## States, per screen

| Screen | Loading | Empty | Error or unavailable | Success |
| --- | --- | --- | --- | --- |
| Home | household record loading: "Opening Calm Frames" over the still scene (`HouseholdStorageScreen`) | "Nothing to watch yet" notice, Parents focused | record failed: notice and one focused Try again; service unreachable: banner above what still verifies | hero with Watch focused, Details, rail |
| Details | none (synchronous from the checked entry) | n/a | notice with the reason, one focused Back, no Watch | hero with Watch focused, More info |
| Opening and return shell | "Opening your video..." with one Back | n/a | replaced by the recovery screen on error or by the player on a blocked map | swapped for the player on frame evidence |
| Player | checking card while the map is read; loading plate after a second of waiting | n/a | unavailable card with Go back, or recovery screen with one focused Go back; cover stays on in both | cover off between intervals; countdown, cover and after cards |

Layouts reserve their space: the Home hero and the Details hero keep fixed
minimum heights, the opening shell is a fixed composition, and the loading
plate never changes layout. No artificial delay was added.

## Remote, focus, motion and sound

Watch is the one primary control on Home and on Details. Every actionable
control keeps a ring of the same width at rest and on focus, with the fill
changing alongside the ring and the label underlined; `tenFoot.test.tsx`
measures this on every screen. Focus returns to the pressed control after
Details, playback, Parents, How it works and now the profile picker
(`returnFocus.test.tsx`, `pickerFocusReturn.test.tsx`). Nothing on these
screens responds to hover. The Home scene is a still; the one optional
artwork entrance checks the system reduced motion setting before it moves
(`CalmArtworkMotion.tsx`); the loading plate has no animation. Selection
sounds remain an opt-in household setting, stay silent under a screen reader
or in the background, play at most once per held key and no more than once
every 220 ms (`useInterfaceSound.tsx`, `interfaceSound.ts`); no change was
needed.

## Verification boundary

See [the receipt](../../results/tv-experience-2026-10-16/receipt.json) for
the commands, counts and log digests. Source tests establish what the screens
render and what the route refuses; they do not establish native appearance,
visible focus, audible sound or caption drawing. No build, installation,
launch, simulator action, screenshot or recording was performed. The installed
demo described in `FINAL_HANDOFF.md` is older than this source and was not
touched.
