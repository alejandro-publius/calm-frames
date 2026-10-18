# Ocean replacement ready for exact approval

The local export is complete and reproducible. It is not approved, active,
installed or pushed. The installed app still corresponds to `50bc01f`.
No new signer or private key was used. The existing signed source maps are unchanged.

## Exact proposal

- Bundle: `d1abd36aa0cf3ba51d6e66c186c9a1c1deb9cf04b027919dd67a465722015e46`
- Catalog SHA-256: `6b590929ffd622454803caf87354a653190dcb89afa12e906bbaaedfe0e9012d`
- Existing signer: `98e4c9564d4ef219cc743a0e06372192b9aef573c4ce956987d5bfe255a11407`
- Report SHA-256: `45c6f62f741bbc133d01a0d80b3d4da13d9f2dff0e49d045796592eda0071493`

The exact files are in `build/ambient-export-2026-10-18/prepared-library` in this
checkout. `approval-proposal.json`, `catalog.json` and `verification-report.json`
retain the reviewable identity and proof. The report is generated from independent
reproduction of all three candidates, not from a manually asserted success flag.

One owner approval is required by the delegated scope: approve this exact Acadia
ocean replacement catalog under the existing signer and its single native Debug
build/install. This approval covers generated ambient metadata bound to the same
checked report. It does not approve another title, signer, release or publication.

After approval, stage the new immutable bundle and report alongside existing
assets, replace only the old Acadia entry in the exact approval registry, and run
`node tools/approved_prepared_libraries.mjs --write` followed by
`node tools/approved_baked_ambient.mjs --write` from app/. Record the actual owner
approval reference. Run the normal build gates, then one native build/install.
Do not add a duplicate Acadia title entry or overwrite other generations.

## What the checks establish

- Python and Node strict catalog checks both pass; 21,208,489 bytes, one title.
- All three independent reproductions match the proposed MP4 bytes exactly.
- Every original video timestamp (1,804) and compressed audio packet (1,765),
  including timing, matches. Exact video duration is 1693879/45000 seconds.
- Full outputs and the silent ocean input pass unchanged WCAG and broadcast
  analysis at 85 inches / 4 feet. No threshold, source map or coverage timing changed.
- Changed media, map and report bytes are rejected; restoring them passes.
- 82 Python, 58 Node and 85 focused app tests pass. These include semantic report
  tampering, duplicate keys, timing/audio claims, signer mismatch, metadata generation,
  household additions, loading, seeks and the conservative guard.
- TypeScript, focused ESLint, Ruff and the read-only native input/prebuild gate pass.
  The compiled ambient registry remains empty until approval.

The exact prior Acadia household record is read as well as the new rendition's
record. Both must load successfully; additions are combined without writing or
migrating either record. Invalid records or more than 32 combined additions block
playback. Any household addition retains the opaque cover. This continuity is
limited to the unchanged source, maps, duration and timeline proven by the exact
Acadia replacement. No actual household records or PIN were accessed.

These checks establish bytes, timing, recipe execution and software decisions.
They do not establish native rendering, audible playback quality or owner visual
acceptance. After the single installation, inspect only authorized public-flow
logs and leave Home. The owner still needs to watch the ocean replacements and
listen to transitions. No capture, recording, Parents navigation or native action
was performed in this pass.

## Bounded otter result

The same existing CC0 source yields a checked 4.22-second excerpt, from 80.750 to
84.970 seconds. Both unchanged analysis profiles report zero segments. It remains
an unapproved short preview, without audio, and is excluded from this approval.
No further search, full-title claim, signing, looping claim or install was made.
Its receipt and analysis are in `otter-longer/`.
