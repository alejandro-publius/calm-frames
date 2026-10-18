# Cinematic viewing flow

Local review branch: `codex/cinematic-review-2026-10-18`, from synced `59f2383`.
The owner authorized this redesign and one consolidated build/install, without
capture or publication. Source media, detector code, signing trust and protective
logic remain unchanged; `preserved-inputs.json` records the checked paths.

## Revised screens

Home keeps the existing edge-to-edge licensed coast and gives the picture more
space. A compact film selector replaces large poster blocks. Inactive entries
have no panel; the selected film keeps a marker and selected accessibility state
when remote focus moves to Watch. Focus still selects without autoplay, and Enter
still opens Details. Runtime, silence and once-through wording remain truthful.
There is no persistent explanatory paragraph on Home.

Home, Details and opening share title typography, reading width and primary action
geometry. Otters keeps the same decorative coastal setting through Details and
opening, including the lazy route fallback. This scenery is decorative, not an
otter thumbnail or a playback cover. Details leads with title, runtime, short
synopsis and Watch/More info, followed by the compact scene summary and timeline.
More info retains explanations, attribution, practice and technical records.

The existing guarded player seekbar gains a thin read-only scene rail using the
same geometry/colors as Details. It uses verified guard intervals, which already
include rendition offset and household additions, with native duration and
playhead in the same milliseconds. It introduces no focus target or seek handler;
its memoized views update when verification data changes. Controls retain their
existing show/hide behavior. Captions and compact Skip keep their reserved bands.

The large duplicate scheduled-cover message is removed. Opaque fallback coverage
remains intact, and the compact scene control retains Skip and paused/loading
status. The control says `Scene replaced` only when the exact verified baked ocean
presentation is actually visible; other covers retain `Scene hidden`. The scene
itself, source audio, intervals and all fallback eligibility rules are unchanged.

## Checks before the build

271 tests in 25 suites pass, including selection, return focus, practice, Parents
cancellation, typography/geometry, opacity, cover eligibility, caption plumbing,
scene markers and guarded seeking. One existing Jest snapshot also passes.
TypeScript and focused ESLint pass; four existing CoverLayer warnings remain.
Native input and strict prepared-package gates pass. Independent review found two
presentation issues, corrected before build; see `review.md`.

`initial-tests.log` retains four expected old-presentation assertion failures.
The tests now assert absence of the removed copy while still checking opacity,
Skip and focus. A new live-state timeline test exposed the existing seekbar memo
comparison missing the new interval input; the comparator is fixed and the test
passes, including removal of marks when verification is lost.

## Native review

One build/install follows this source checkpoint. Build, install and native text
receipts are authoritative once present. No screenshot or recording is used.
Tests and source/asset contrast calculations do not establish native pixels,
readability, transition appearance or heard audio. Those remain owner review.

Owner review after installation: use the compact film selector, open Details,
play Acadia through both ocean replacements and listen across them; then select
Otters and confirm the silent short preview and return behavior. The app will be
left on Home. No push or publication is part of this pass.
