# Coastal islands and selection boat, October 18, 2026

This bounded improvement retains the accepted coastal-world layout, Fraunces
headings, Source Sans 3 controls, card geometry and two current playable titles.

- Acadia has an angular granite headland and lighthouse. Sea Otters has a rounded,
  kelp-lined shore. Forest has pines, rounded rock and a small illustrated waterfall.
- Forest is scenery labelled **Not ready to watch**. It is not a button, title,
  playable route or trusted catalog. Its staged real footage shows a redwood creek,
  not a waterfall; the illustration is a destination motif rather than source footage.
- An original boat follows the selected current destination. Selection, focus and
  Watch update synchronously; the decorative boat never handles input. Existing
  opt-in artwork motion allows one 560ms move. Default, reduced-motion, screen-reader,
  inactive, failed or unknown preference states settle instantly. No household
  preference is changed to demonstrate animation.
- Static shoreline rings and layered shadows add depth without continuous movement.
  The selected island silhouette continues into Details and the static loading view.

Components: CoastalIsland, CoastalBoat, CoastalWorld, KidHomeScreen,
TitleDetailsScreen and PlayerOpening. No player guard or media payload change.
Existing Acadia ocean and NOAA Sea Otters bytes, trust and reports match ab83cf8.

## Verification

See the test logs, mutation regression, preservation record and independent review.
The final bounded app suite, TypeScript, lint, native inputs and strict media gates
run before the source commit. Build/install and native receipts follow that commit.
Controlled tests establish motion cancellation and accessibility fallbacks. Native
text logs establish route, focus, playback identity and event order; they do not
establish pixels, audible quality or the owner having watched. No screenshot,
recording or PIN operation is part of this pass.

## Forest activation boundary

The [concrete media proposal](../forest-candidate-2026-10-18/approval-proposal.json)
requires exact catalog and fresh-package approval. UI work does not authorize that
catalog. The original package namespace and source recordings remain preserved.
No detector threshold, signing key, broad trust, AWS or release change is included.
