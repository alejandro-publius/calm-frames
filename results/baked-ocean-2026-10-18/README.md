# Real ocean baked replacements: implemented, unapproved

This supersedes the no-motion-path finding in the previous ambient inspection.
The new path uses one prepared video stream. It does not depend on a second native
surface, runtime mute, runtime looping, Harbor or a browser effect.

## Deliverables

`pipeline/ambient.py` provides an unsigned local preparation command. It derives
exact coverage from the existing app recipe and source-bound maps, validates an
audio-free real-ocean excerpt under WCAG and broadcast at 85 inches / 4 feet,
replaces source pixels over a solid backing for each complete interval, maps only
original audio, and checks the entire resulting rendition with both profiles.
Each interval starts at the beginning of the ocean excerpt; it does not loop.
A clip too short for a whole interval is rejected. Failed checks produce diagnostic
receipts and never produce activation metadata. Existing directories are refused.

All 1,804 original video presentation timestamps, video duration and all 1,765
compressed audio packets (including timestamps and durations) match in every
candidate. Video duration is exactly 1693879/45000 seconds. The candidates preserve
source audio; the replacement input has no audio. These are data checks, not an
assertion that someone heard the sound or inspected the picture.

The local MP4s are under `build/ambient-ocean-2026-10-18/` in this checkout:

- `standard-1/candidate.mp4`: 7,088,050 bytes, Standard.
- `broadcast-1/candidate.mp4`: same media bytes, independently bound Broadcast metadata.
- `extra-cautious-1/candidate.mp4`: 6,842,701 bytes.
- `otter-short/otter-short-unapproved.mp4`: 1,809,740 bytes, described below.

`identity-audit.json` has exact paths, SHA-256 media identities and SHA-512 metadata
identities. Candidate analysis reports and draft metadata are retained beside this
README; large media stays local in build/. No candidate was signed, exported to the
active app namespace, approved, opened, installed or pushed.

## Ocean provenance and unchanged timing

The existing NPS public-domain Acadia source supplies the ocean excerpt from source
0 to 6.5 seconds. `media/LICENSES.csv` retains its provenance and original hash:
https://npgallery.nps.gov/AssetDetail/6fc09aec-7fc2-47ed-b8cc-e1b10861dd3e
Credit: NPS Video, Acadia National Park. No NPS endorsement is implied.
The source file remains unchanged in the separate Claude video checkout; it was
read only. No new footage acquisition, fabrication or signer access occurred.

Standard/Broadcast replace 7.843-12.199 and 28.613-31.093 seconds.
Extra cautious replaces 7.343-12.699 and 28.113-31.593 seconds.
The original map bytes, detector, guard bands and interval recipe are unchanged.
All replacement inputs and complete outputs had zero reported segments in both
room-aware analyses. Cuts into and out of the ocean are included in the full-output
analysis. This is evidence from the existing software, not independent or medical
validation. Native appearance and audio still require owner review.

## Runtime integrity and fallback

The current opaque UI would hide baked ocean frames. The narrow new capability is
`app/src/calmframes/bakedAmbient.ts`, called by PlayerScreen, with an EMPTY compiled
registry in `approvedBakedAmbient.ts`. Current production behavior therefore stays
unchanged. A route, upload or household record cannot activate this feature.

A future reviewed entry requires an exact SHA-512 of the metadata bytes, exact
source/rendition/ambient hashes, duration, zero offset, preset, both source-map
hashes, complete interval equality, preserved timing/audio assertions and both
output-analysis hashes. Strict JSON rejects duplicates and unknown fields; checked
records are frozen and tracked by provenance in memory. An accepted compiled
prepared route and successfully verified guard maps are also required.

Only stable ordinary scheduled playback within a matching base interval may reveal
baked pixels. Seeking/uncertainty (scheduledCover false), loading, slow progress,
pause, opening, return, end, errors, unknown storage and any personal addition keep
the opaque layer. Conservative treatment of any personal addition is intentional:
the first version does not distinguish its overlap from baked base intervals.
The guard remains covered, keeps its schedule, log, label, Skip target and seek
funnel; only the redundant visual layer can be omitted over verified baked pixels.
No fade, transparency or cover delay was added.

## Exact approval proposal and remaining activation work

The proposed content is ONLY the three Acadia candidates in `identity-audit.json`,
using the existing source-map signer fingerprint already approved for Acadia.
No new signer is needed for those unchanged signed maps. The new rendition bytes
are not covered by the old exact-bundle/catalog approval.

Review proposal: accept the exact media SHA-256 and per-preset metadata SHA-512
pairs in `identity-audit.json` as the proposed replacement recipe for Acadia. This
would authorize preparing the replacement catalog for final review, not granting
blanket signer trust or adding other media. Otter is excluded from this proposal.

A final activation approval must name the NEW bundle ID, catalog SHA-256 and the
existing public-key fingerprint, plus these metadata identities. Those catalog
values do not exist yet and must not be invented or borrowed from the old bundle.
The current strict exporter/report gate proves still-image covers; it does not yet
accept this separate unsigned ambient receipt. Its verification/export schema must
be extended to bind the new recipe and its full evidence, with negative tests,
before generating that exact catalog. Do not forge legacy still-cover checks,
reuse the old verification report, or activate merely by populating the registry.
This is the remaining engineering boundary, not an asset or platform choice.

After the export gate and exact approval, use the reserved single native build /
install to check playback, fallback/seek/Skip and Home/Details/Back from text logs.
An owner must assess actual picture transitions and original sound. No Parents
access, household edits, screenshot or recording is part of that validation.
Installed source remains `50bc01f`; the earlier release fixes remain on this branch.

## Otter: a bounded lower-coverage result

The earlier USFWS excerpt was covered for all 12.012 seconds. The earlier CC0
16-second grooming excerpt was covered for 14.440 seconds in Standard/Broadcast
and 15.440 seconds in Extra cautious. Neither was a shipped selection.

The already downloaded CC0 Uusijani grooming source has an Extra cautious gap at
81.000-84.720 seconds. Taking 81.250-84.470 adds 250 ms of separation at both ends
and yields a 3.22-second excerpt. Re-analysis of the actual encoded excerpt found
zero segments in WCAG and broadcast with the unchanged 85-inch / 4-foot room.
Source and excerpt have no audio. `otter-short/receipt.json` retains its exact
identity and source URL. It is a short content candidate, not an ambient option,
not a restored long video, and not signed or catalog-approved. No looping was
assessed; a loop would require separate seam validation.

## Reproduce without activation

Run `python -m pipeline.ambient --help` in the project venv. Supply the original
source, the local audio-free ocean excerpt, both exact source maps, preset,
new output directory and attribution. The CLI has no signing, trust, export,
install or approval option. The three `metadata.draft.json` files are review
inputs, never runtime imports.

## Focused validation

79 app tests passed across metadata refusal, playback card/focus, buffering,
seek safety and the guard. 18 pipeline tests passed, including the existing app
playback recipe. New tests check every covered synthetic frame and both adjacent
boundary frames, exact audio/PTS, wrong source identity, short replacement input,
replacement/output analysis refusal, input mutation, no overwrite and no approval
metadata on failure. TypeScript, focused ESLint, Ruff and repository style passed.
The configured redacted secret scan found no leaks in 163.44 KB of changed source
and evidence. No tests opened a player, captured a screen or used a device.
