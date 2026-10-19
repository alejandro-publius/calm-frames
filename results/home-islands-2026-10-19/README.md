# Ocean and Forest Home, Details, and the checks behind them, October 19

All of this was done in a cloud session from the pushed tip `c84f95d`. Nothing
here was built, installed or seen on Vega: the session has no Vega SDK, device
or virtual device. The Mac's installed source `2b78587` and its uncommitted
navigation work were never pushed, so they are not in this branch.

## What visibly changed

**Home.** The map and the controls had no shared coordinates, so the heading,
shorelines, waves, cards, boat and Watch collided (`before-home-*.png`).
`app/src/calmframes/homeIslands.ts` now places all of them, and every word and
control sits on one flat colour:

- **Ocean** is named once over Acadia and Sea Otters, **Forest** once over
  Forest, on the cream sky. The islands sit in that order: Acadia, Sea Otters,
  Forest.
- Each card stands on its own island; the lighthouse, kelp and pines stand
  beside the card instead of under it. The islands and their rings never meet.
- Every card has the same two lines: a short name, then sound and length
  (`Silent · 38 sec`, `Silent · 20 sec`, `Nature audio · 12 sec`). The Acadia
  rendition's audio track measures -91 dB throughout, so it is called silent.
- The chosen title is no longer repeated under the cards. The sand holds Watch
  and Details, and Watch announces what it plays ("Watch: Sea otters in
  Alaska"). A shelf with one video and no card keeps its title and runtime.
- The boat waits in open water on its route. The offline notice takes the
  empty half of the sand, and Who is watching takes the card row while open,
  so neither moves the map.

**Details and the opening screen.** Back sat on the shoreline because the old
sky curve's control points ran up to y -30, and the photograph covered the
island's lighthouse and trees (`before-details-coastal.png`). Both now read
the same module: the sky's shoreline stays below Back, the 560 by 315
photograph stands on its island with the landmarks beside and below it, and the
opening screen shows the whole island in the same place.

Help, More info and the parent area were rendered too and showed no overlap.

## How it is held

`app/test/calmframes/homeIslands.test.tsx`, 24 tests, renders Home, Details and
the opening and reads back the boxes the screens place and every SVG shape the
map draws, through its transforms, with control points and half the stroke, so
overlap is overstated and never missed. Seen to fail, one break at a time and
restored each time: islands at 0.86 scale; the boat at y 600; the lighthouse at
x 200; the hero at 760; the sky's shoreline at 200; the picker slot at 200
units; the chosen title shown under the cards; Forest between the Ocean
islands; a card line back to "20 seconds"; an environment renamed; the old
Details photograph; the old Details sky curve.

## Pictures

`after-*.png` are Chromium renders of the exported component trees
(`eval/preview/islands.fixture.tsx`, then `eval/preview/render_islands.mjs`)
with the real styles, fonts, images and SVG. Browser flexbox stands in for
Yoga: this shows composition and overlap, **not native pixels**.

## Checks that were not running

- **The full app suite** had 18 failing tests on `c84f95d`
  (`full-suite-before.log`); the Oct 18 records counted a bounded subset. It is
  163 suites, 1,676 passed, 0 failed now (`full-suite-after.log`), with the
  coverage floors met. The stale tests expected the Harbor home, the dark
  palette and older copy; each was changed to check what the screen does now.
- **The approved-wording guard** (never "prevents seizures") had been crashing
  on the new `integration/` folder and checking nothing. It recurses now and
  turns red on a planted phrase.
- **The trust-gate tests** for approved catalogs copied only the first approved
  manifest, so all nine died in setup after the Sea Otters and Forest
  approvals and none of the seven substitution attacks was checked. The
  fixture copies every manifest now; 51 tool tests pass.
- **The app's own UI flash check** declared Home and Details in the old dark
  palette. The declarations now match what the screens paint, and flashmap
  passes all 37 screens and transitions under both the wcag and broadcast
  profiles; the negative control still refuses the flashing sequence.

- **A real delivery bug.** `pipeline/edition_delivery.py` copies a fixed list
  of checker tools into the proposed checkout, and `check_prepared_library.mjs`
  had gained an import that was not on it, so every edition delivery was
  refused before it was checked. The list now includes `ambient_report.mjs`;
  the delivery and release gate tests run again.
- **More stale checks**, each now checking what ships: the delivery fixtures
  named Acadia's retired bundle; the design page and `tokens.json` described a
  palette three revisions old (regenerated from the code, every listed pair
  still clears its floor, the lowest a focus ring at 5.99 to 1); the brand
  image check never looked at the three card photographs (added, all pass
  flashmap); seven README line links had drifted; the tampered-map mutation
  targeted code that had moved (retargeted at the same fault, killed again,
  committed report unchanged); pipeline mypy had five typing errors; ruff was
  linting the evidence scripts under `results/`, which are now excluded; and
  the flashmap report page used the Oct 14 palette (moved to the app's: the
  widest step inside a lane falls from 5.63 to 3.25 cd/m2, and the page check
  still finds no flash, no bar boundary and no pattern in its 6 frames).

## Still open

- **The package budget is spent.** The prepared library is 66,492,442 bytes of
  its 67,108,864 byte (64 MiB) budget, about 602 KB left, so the import workflow
  cannot add a real clip of any useful length. Options for the owner: raise the
  budget, remove a title, or store identical renditions once (Sea Otters ships
  three identical 9.7 MB files), which changes the signed package format and
  needs approval. `test_changed_generated_module_is_restored_on_final_failure`
  fails for this reason and is left failing on purpose.
- **The pattern rule's text precision** (published as 0.9143) was measured
  on a corpus whose colours are hard coded from the Oct 10 palette in
  `eval/pattern_text_frames.py`, so "every colour pair this product ships" no
  longer describes the shipped palettes. Re-running it on today's colours
  would publish a new number, which is the owner's call.

- Install this branch and look at it on the virtual device or the stick.
- Merge the Mac's unpushed work, or decide to drop it in favour of this branch.
- The official rule pages could not be re-read from this session: the network
  policy blocks devpost.com.
