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

## Installed result

One Debug build and one update/install succeeded from source
`999f69cd917e51444502d157a3e1bfb069d85235`. Package SHA-256:
`d8217c60e2857dcd09b1a807fb0a96b1ed68da69eff08675ef4ebe112f787cdd`.
Package path: `build/release/cinematic-review-2026-10-18/calm-frames-cinematic-aarch64-debug.vpkg`.
All 815 app inputs matched before/after build and before installation. The device
copy matches the package hash. Both approved catalogs and all 12 media/map assets
match directly inside the package; new scene timeline/copy strings are included.
The ambient registry remains byte-identical.

Nine native text checks passed on the existing Extra cautious profile:

- Home Watch selected the exact ocean Acadia bundle. Both scheduled intervals
  requested baked ocean, at sampled media positions 7365 and 28143 ms. Natural end
  returned to Home Watch.
- The compact selector reached both titles. Otters opened Details with Watch
  preview focused, played its exact rendition once and returned to Details Watch.
- Manual Back from Otter playback restored Details Watch; Details Back restored
  the selected Otter card. Up returned to the hero actions.
- The app is left on Home with Otters selected and Watch preview focused. The
  text collector is stopped.

Receipts, every native command, filtered CALM traces and selected-media identities
are retained here. Full bounded application logs remain under
`build/cinematic-review-2026-10-18/`. Logged samples are not display latency
measurements. Package media proof retains Acadia's original audio packet/timestamp
continuity and the otter's 106 frames, 4.24 seconds and absent audio stream.

No capture, PIN entry, Parents navigation, household writes or push occurred.
Practice and Parents cancellation were covered by unit tests, not exercised
natively in this pass. Native error/seek/pause injection and screen-reader speech
were not tested here. Logs establish route/guard decisions and installed bytes,
not native pixels, readability, transition appearance or heard audio.

## Owner review

The open app is ready. Use the compact film selector, open Details, play Acadia
through both ocean replacements and listen across them; then select Otters and
confirm the silent short preview. Review the selected-film marker separately from
the remote focus ring. These visual/audio judgments require the owner. No further
installation is needed, and no real product decision blocks this review.

The earlier synced checkpoint 59f2383 and installed source 603f6ce remain in history;
this redesign and its evidence are local only. Evidence commits after 999f69c do
not change the installed app.
