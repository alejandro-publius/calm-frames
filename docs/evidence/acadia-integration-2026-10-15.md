# Acadia integration review, October 15

Update: the owner approved the exact scope below at 21:19 UTC. The restricted
catalog integration is implemented; see FINAL_HANDOFF.md for build and native
status. The following offscreen audit describes the pre-approval checkpoint.

The candidate was audited without displaying source footage or playing any
Acadia rendition. It is staged at `build/acadia-audit-staging`, outside app
assets. Claude's `ec323fcf38ccb493082100bbf06ea79b0cfb1c53` was imported as
`f46e238`; its source workspace was not changed. The installed app remains the
prepared-video UI package recorded in FINAL_HANDOFF.md.

## Exact approval scope (approved at 21:19 UTC)

Permit the existing public key with raw-key SHA-256
`98e4c9564d4ef219cc743a0e06372192b9aef573c4ce956987d5bfe255a11407`
only for compiled Acadia bundle
`4bab8d81f779d7cf0eac3f5e2fe5372e88e95088fb068680818b28865dc6ad13`.
The catalog bytes are SHA-256
`ad74eb70199adc8597d1f7bcdba57fa1c0b805987e2f8a11f240fba4c036dd4c`.
The base64-text hash in Claude's handoff names a different encoding of the
same public key; use the raw-key fingerprint above for this decision.

The intended change is a separate compiled Acadia catalog, its six prepared
media/map files and original report, exact catalog matching in
`app/src/calmframes/packagedLibrary.ts`, and shelf/evidence tests. Retain the
existing Harbor catalog, key, files and practice demo. Do not replace the
global key or accept arbitrary bundles signed by the Acadia key. No private
key, generation, household setting, cloud deployment or publication is part
of this approval. Claude's preparation script generated a temporary key;
Codex did not run that script, access a private key, or activate its trust.

## What the offscreen checks establish

- Source bytes match `2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28`
  at 4,049,669 bytes. The source was hashed only.
- Strict package check with `--require-reports` passes. It verifies the
  artifact hashes, map signatures under the candidate's public key, complete
  report and manifest consistency. This local check does not grant app trust.
- A fresh copy passed unchanged; six altered copies were refused: rendition
  byte, map byte, swapped rendition, edited manifest hash, edited embedded
  map text, and missing report. The text mutation is caught by canonical
  catalog validation; this case alone is not a cryptographic mutation test.
- The preparation workspace digest matches `checkedInputsSha256`, binding
  the exact still used for the full-frame audit. The script decoded every
  frame at full size as numeric arrays, with no image exports. Every planned
  covered frame was compared with that still at the existing 30 dB floor,
  using RGB whole-frame PSNR. This is similarity, not pixel equality.
- WCAG and broadcast each cover 326 of 1,804 decoded frames, with worst RGB
  PSNR 41.743 dB. Extra cautious covers 422 frames, worst 42.088 dB. Adjacent
  frame timestamps and scores are recorded for each interval. An initial
  black-frame assumption was rejected: these renditions use a source-derived
  still, so the corrected check compares that exact hash-bound still.

Receipts are under `results/acadia-integration-2026-10-15`. Reproduce the
numeric frame audit with the repository Python environment and:

```sh
PYTHONPATH="$PWD/flashmap/src:$PWD" python scripts/audit_prepared_cover_frames.py \
  --root build/acadia-audit-staging \
  --preparation /Users/alexvintera/calm-frames-claude-video-2026-10-15/build/video-reset/local-library \
  --out results/acadia-integration-2026-10-15/all-covered-frames.json
```

## Corrections to the reporting contract

The first merged finding has seven segment observations across four unique
map files. Across all five map files there are ten segment observations and
two merged time spans. These are not independent detector confirmations.
`found_in_runs` now counts unique map paths, and `segment_observations` keeps
the other count. A broadcast baseline flag cannot become a WCAG baseline flag.

Standalone WCAG uses a 64x36 area window, relative-luminance delta 0.1 and
dark image below 0.8. Broadcast uses the 192x108 whole picture, BT.1886 delta
20 nits and dark below 160 nits at an assumed 200-nit peak, plus its informative
pattern rule. Pipeline maps add a 22x22 window for 85 inches at 4 feet.
The first broadcast pipeline span ends at 9906 ms; WCAG ends at 9864 ms.
The merged cover intervals do not change.

The summary now preserves profile-specific luminance, pattern, exception and
transition settings. `signature_present` only reports field presence.
`validate()` remains presentation consistency checking, not authentication.
The UI must derive its trusted facts from verified maps and exact compiled
catalog metadata, never a summary boolean. The original summary is retained
as historical evidence; the corrected summary is in the integration receipts.

The area boundary test adds 24 pixels above a quarter, not one. A separate
max-coverage unit check adds one. Loop-seam display behavior is unverified.
No one should watch the original hazardous source for this integration.

## Selection sound

The existing optional local cue is `app/assets/raw/sound/menu-select.mp3`,
an original CC0 sine-wave asset with SHA-256
`38e2663df732562de2876fe40d3fd64f2fc9aa3ac52d745b956a88e5af2c7ab0`.
It has an 8 ms attack, 105 ms synthesized content and 144 ms encoded duration.
The player volume is 0.22; no system volume changes. Selection sounds remains
off by default and follows the saved setting. No download or account needed.

The existing controller drops overlapping, rapid and late cues and stops for
playback, blur, background or VoiceView. The new observer suppresses repeated
confirmation while Select/Enter remains held, including beyond the 220 ms
cooldown. It does not handle or change navigation actions. Source tests cover
focus-only silence, held-key suppression, settings and playback cancellation.
Audible quality and the new guard's native event ordering remain unverified.

## Source validation

37 focused Python tests, 55 package tests, and the app gate of 131 suites,
1,302 tests and 57 snapshots passed. Four app tests remain skipped and three
capture suites were excluded. Typecheck passed. Lint has zero errors and 101
existing warnings. Ruff, style and the 664-number documentation check passed.
The focused sound suites passed 46 tests. See the integration receipt for log
hashes. No new app package or native run is claimed for this checkpoint.

## Remaining work

Obtain the exact public-key scope approval above before adding Acadia to app
assets or trust. Then compose the isolated catalogs, bind the findings to the
selected rendition, rebuild once and run authorized non-capture native checks.
Do not claim the candidate has been tested natively. Audio, caption appearance,
seek behavior, replay seam and TV display cannot be established by these logs.
Same-analyzer rechecks are not independent detector validation. The approved
claim remains: reduces exposure to flashing above published limits in the
videos it plays; not a medical device.
