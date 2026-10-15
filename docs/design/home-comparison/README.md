# Home composition review - October 15

Open `index.html` in a browser, or use the running local preview:
<http://127.0.0.1:4186/docs/design/home-comparison/>.

If the local server has stopped, run from the repository root:

```sh
python3 -m http.server 4186 --bind 127.0.0.1
```

No package installation, network assets or build step is needed for this preview.
The fonts and coastal image are the existing licensed/provenance-tracked app assets,
referenced by relative paths. Keep this directory inside the repository when copying it.
The owner delegated implementation on October 15. Composition A was selected for its
shorter title-to-action scan and implemented in the app. B remains a comparison;
the pre-change app is preserved at `b6b134c`. Preview controls never change app settings.

## The two compositions

| | A - Left reading area | B - Lower action band |
|---|---|---|
| First emphasis | Heading and dark Play button together | Coastal scene, then the lower action band |
| Grouping | Heading above Play and Details at the left | Heading at lower left, Play and Details at lower right |
| Separation | Horizontal ivory fade behind the text | Vertical ivory fade into an opaque lower band |
| Tradeoff | Faster scan from name to action; covers more left scenery | More open scenery; a longer scan from name to action |
| Home remote route | Play ↔ Details; Up to How it works, Right to Parents; Down to last Home action | Play ↔ Details; Up from Play to How it works, Up from Details to Parents; Down to the corresponding action |

Both use the same Home words, unedited dimensional coastal art, Fraunces headings,
Source Sans 3 controls and existing palette values: ivory `#F5EBDD`, teal `#193B3C`,
terracotta focus `#C16C45`. Grayscale is the initial review mode. It tests whether
size, spacing and dark/light contrast establish the hierarchy before color helps.
Use the large views to assess reading distance; the small comparison is for structure.

The browser route simulation is deliberately labelled. It plays no media, collects
no PIN and does not implement the native focus engine. Arrow keys move focus; Enter
activates; Escape goes Back; normal Tab navigation lets you leave the study.

## Return paths to compare

Both compositions preserve the intended route:

1. Home / Details → Harbor Details / Play → Try the demo → Practice Details / Play demo.
2. Play demo → simulated practice; Back → Practice Details / Play demo.
3. Back again → Harbor Details / Try the demo; Back again → Home / Details.
4. Home / Parents → PIN gate; Cancel or Back → Home / Parents, including after Details.
5. Home / Play → simulated Harbor; Back → Home / Play. Playing from Details returns there.

The latest app already contains the Parents return fix (`0e434dc`). This study proposes
only Home composition; its secondary pages explain routes, not new secondary designs.

## Evidence and your part

[Preview checks](../../../results/home-review-2026-10-15/preview-checks.json) record
headless DOM checks for both route models, arrows, font loading, color switching and
large-view bounds. No screenshots or screen recording were made. These tests do not
establish appearance, ten-foot readability, screen reader behavior or native navigation.
[The Mac receipt](../../../results/home-review-2026-10-15/receipt.json) separately
records the rebuilt current default and its native log observations.

Your design review: compare grayscale, then color and give feedback on the selected A.
No further layout decision is needed to complete this implementation. Your native acceptance: look at the current rebuilt app,
listen through Harbor and both demo pauses, check visible focus and captions,
and enter the existing household PIN yourself to test the parent settings interior.
Do not reset the household. VoiceView needs a separate owner check if available.

Before distribution, resolve the sample-license notice scope and artwork permissions.
These remain owner decisions; this pass neither removes notices nor contacts third parties.


## Implemented scope and reversion

App commit `69df28c` implements A: Home moves its existing heading/action group
to the left middle, the continuous ivory edge replaces the small lower fade,
and Details adopts Home's title scale. How it works gets a wider reading edge,
scrollable copy and one shorter practice sentence. The locked Parents gate adds
the same scene and an opaque keypad surface. Focus IDs and all route handlers are
unchanged. No new artwork, media, dependency, PIN handling or playback behavior.

For a review or reversion, compare app source at `b6b134c` and `69df28c`. Revert
only the implementation commit on a new working branch if requested; do not
reset another session's checkout. The baseline and selected packages have
separate receipts in the Mac evidence directory.
