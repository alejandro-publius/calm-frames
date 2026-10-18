# Moving ocean cover and missing otter selection: local inspection

Inspected source: `80c7377` on `codex/creator-editions-2026-10-18`.
The owner requested a moving ocean cover and asked where the otter selection was.
This superseded the proposed static dark treatment before any edit or build.
No application code was changed during this inspection. No device interaction,
Parents access, household write, capture, recording, trust change or push occurred.
The consolidated native build/install remains pending; its one-install allowance
has not been consumed. Installed source remains `50bc01f` from the prior receipt.

## What exists

- `app/src/calmframes/HomeHarborScene.tsx` renders fixed PNG artwork, not video.
  FINAL_HANDOFF.md's historical Ambient motion entry explicitly kept the separate
  browser canvas water study out of the native app. That study is not an existing
  native moving cover that can simply be re-enabled.
- `app/assets/raw/benign-story/harbor.mp4` and `harbor.precovered.mp4` exist and their
  current hashes match `verification.json`. They are 20-second generated illustrated
  Harbor films, with camera motion, scene cuts, captions and synthesized water audio.
  Their README records Apache-2.0 provenance. They are not real ocean ambient footage.
  The prepared version includes practice holds. Repurposing this as a looping cover
  would be new behavior, not restoring a lost setting.
- Acadia is the only entry in `app/config/approved-prepared-libraries.json`.
  It is public-domain NPS coastal content with prepared covered intervals; it is not
  a separate uninterrupted ambient replacement loop. No catalog entry was changed.
- The two otter candidates remain in isolated staging under
  `/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-review/build/`.
  Original and selected derivative hashes were re-read and match their receipts.
  They were proposed content titles, not ambient choices or shipped selections.

## Exact otter blockers

1. `otter-candidate-2026-10-16/candidate/UNREVIEWED_otters_06-18_muted_720p.mp4`
   is a 12.012-second USFWS public-domain excerpt. Existing analysis and guard bands
   cover its full duration in all presets. Its prepared outputs show a neutral card,
   not moving otters. The separate experimental bundle is not app-approved.
   See `docs/evidence/otter-candidate-2026-10-16.md` and its linked receipts.
2. `otter-grooming-candidate-2026-10-16/candidate/UNREVIEWED_grooming_30-46_muted.mp4`
   is a 16-second Uusijani CC0 excerpt. Existing plans cover 14.440 seconds in
   Standard/Broadcast and 15.440 seconds in Extra cautious. It was intentionally
   stopped before signing, preparation or catalog registration. Original and excerpt
   have no audio. See `docs/evidence/otter-grooming-candidate-2026-10-16.md`.

These are software-policy findings, not medical judgments about nature footage.
Neither can be restored as an existing watchable selection within the instruction
not to approve new keys/catalog entries or relax protection.

## Native motion and audio boundary

The installed `@amazon-devices/react-native-w3cmedia` README documents explicit
surface creation/attachment/clear lifecycle (lines 39-81, 146-191) and lists
`loop`, `volume` and `muted` as unsupported HTMLMediaElement features (lines 341-354).
Therefore setting `muted=true` and `loop=true` on a second player is not sufficient.
The existing Harbor audio cannot be assumed to stay silent alongside source audio.
The current application uses one source video surface, an opaque RN cover at zIndex 1,
caption layer at zIndex 2 and controls at zIndex 3. CoverLayer has no video path.
No local evidence establishes two concurrent native video surfaces' stacking,
resource behavior or source-audio continuity. This is an unverified implementation
path, not a claim that the platform categorically forbids it.

A moving replacement needs an identified licensed and validated audio-free loop,
explicit lifecycle/loop handling, an opaque backing retained independently of
ambient readiness/failure, and native compositor and source-audio verification.
Coverage must remain immediate for every existing interval, seek and uncertain
state. Text logs can establish lifecycle/state, not actual pixel occlusion or sound.
No footage was fabricated, extracted, displayed or promoted during this inspection.

## Independent pending-release review

The outgoing two-commit range `a11587e..80c7377` passed the configured, redacted
Gitleaks scan (2 commits, approximately 57.8 KB; no findings). The native-input
checker reports ready with no missing files or syntax problems. This is input
readiness only, not an SDK build or native acceptance result.

Review confirmed the tracked package lock has no outgoing changes; the clean
command no longer deletes it. Personal-cover display preserves integer millisecond
values; an uncertain write clears the editable record and requires a storage reload,
including the lost-acknowledgment case covered by the prior tests. Patch application
now uses command-local identity and fails on malformed patches. Prior 193 focused
checks are recorded in `results/release-blockers-2026-10-18`; they were not rerun or
represented as new native tests here. Further consolidated validation remains open.

## Minimum next decision

Identify whether the owner means the illustrated Harbor film or an external real
Ocean ambient clip. No existing suitable approved moving-ocean cover was found in
the inspected application and recorded design work. If real footage is intended,
its exact local asset/provenance and replacement-loop validation are needed before
implementation. Do not build the superseded static design or invent an otter item.
