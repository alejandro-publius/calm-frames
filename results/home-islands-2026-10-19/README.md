# Island Home layout repair, October 19

**What was wrong.** On the TV, Home's heading, map decorations, cards and Watch
collided. The cause was structural: the map is an SVG with its own fixed
coordinates and the controls were placed by flex margins and a hero pinned to
the bottom of a scroll view, so nothing kept them apart. Rendered from the real
component tree of `c84f95d` (`before-*.png`): the wordmark and the "Choose an
island" heading sat across the sky's shoreline, a wave ran through the featured
title, Watch and Details sat on the sand line, the cards hid half of each
island and cut the lighthouse in two, the island rings overlapped, and the boat
touched the selected card.

**What changed.** `app/src/calmframes/homeIslands.ts` is now the one place that
says where everything on the island Home sits, and the map (`CoastalWorld`),
the boat (`CoastalBoat`) and the controls (`KidHomeScreen`) all read it. The
bands are stacked so every word and control sits on one flat colour: header and
heading on the cream sky, cards standing on their islands in the sea, the boat
in open water on its route, and the featured title, runtime, Watch and Details
on the cream sand. Each island's landmarks (lighthouse, pines, kelp) now stand
on the strips either side of its card instead of under it. The offline notice
takes the empty right half of the sand, and Who is watching takes the row of
cards while it is open, so neither pushes anything. A shelf whose videos are
not all islands keeps the old flowing layout unchanged. Details and loading
keep their own scenery.

**How it is held.** `app/test/calmframes/homeIslands.test.tsx`, 15 tests,
renders Home and reads back the boxes the screen places and every shape the
map draws (paths, ellipses and rects through their transforms, with control
points and half the stroke, so overlap is overstated, never missed). It fails
if any word or control touches a shoreline, a card touches a landmark, islands
or rings meet, the boat touches a card, island, wave or word, or any text
leaves its box or the safe area. Seen to fail, one break at a time and
restored: islands at the old 0.86 scale, the boat at y 600, the lighthouse
back at x 200, the hero at the old top 760, the sky's shoreline at 200, and
the picker's slot at 200 units tall.

**Pictures.** `after-*.png` are browser renders of the exported component trees
(`eval/preview/islands.fixture.tsx` then `eval/preview/render_islands.mjs`),
with the real styles, fonts, images and SVG. Browser flexbox stands in for
Yoga, so these show composition and overlap, **not native pixels**. Nothing
here was run on Vega: this container has no Vega SDK or device. The layout
still needs one install and a look on the virtual device or the stick.

**Test suite.** The full app suite on the pushed tip `c84f95d` had 18 failing
tests in 8 suites (`full-suite-before.log`). The Oct 18 records counted a
bounded subset, which is why none of them reported this. Two of the 18 are
fixed here: the approved-wording guard in `copy.test.ts` had been crashing on
the new `integration/` folder and checking nothing (it now recurses, and a
planted "prevents seizures" in that folder turns it red), and the trace test
had not been told that the controls now hide themselves after five seconds.
The other 16 expect earlier designs (the Harbor home, "Choose a video", the
dark palette) and are listed in `full-suite-after.log`; none is new.

**Not covered.** The Ocean/Forest categorization that is installed on the Mac
was never pushed, so this repair is to the newest pushed Home (`c84f95d`, three
islands under "Choose an island"). Bringing that work in means merging it with
`KidHomeScreen.tsx` here and adding its headings to `homeIslands.ts`, where the
test will measure them.
