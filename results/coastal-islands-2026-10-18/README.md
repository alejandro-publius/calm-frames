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
438 bounded app tests in 33 suites and 11 attribution tests pass, along with
TypeScript, lint with zero errors, native inputs and strict media gates. One build
and install succeeded from `1d142852beb4a0c0b5068d9f50864c2394554107`. All 821 inputs
matched; package SHA-256 is `af2fcb0f8982773b044ec625fa1f7a3c50c34de33ae64bed9b5d829a6aba0712`.
Both exact current videos played to natural end, with both Acadia ocean requests.
Details/Back and destination selection completed; app rests Home, Acadia Watch.
The initial log collector missed the launch focus event. Fresh text logging and
one direction key established current focus; the continuation completed without
another install or launch. All collectors stopped. No PIN operation was performed.
Controlled tests establish motion cancellation and accessibility fallbacks. Native
text logs establish route, focus, playback identity and event order; they do not
establish pixels, audible quality or the owner having watched. No screenshot,
recording or PIN operation is part of this pass.

## Forest activation boundary

The [concrete media proposal](../forest-candidate-2026-10-18/approval-proposal.json)
requires exact catalog and fresh-package approval. UI work does not authorize that
catalog. The original package namespace and source recordings remain preserved.
No detector threshold, signing key, broad trust, AWS or release change is included.

## Open the current demo

The updated app is left open in the existing Vega Virtual Device. From Home,
Acadia Watch: Up, Right, Select opens Sea Otters Details; Select starts it.
Back from playback returns Details; Back returns the selected island. Left,
Down, Left restores Home Acadia Watch. Use the simulator remote; no reinstall
is needed. Forest cannot receive focus or start playback.

The boat supports gentle movement through the existing artwork-motion opt-in.
That preference was not changed during native checks. The enabled/reduced branches
are controlled-test evidence, not a claim of native animation or VoiceView acceptance.

Final independent consistency review corrected historical pause/Skip attribution and
removed pixel-observation wording from the summary. Raw script receipts retain
narration; only corresponding focus and playback log events establish behavior.
