# Claude Code handoff: prepared video evidence slice

Completed historical brief: Claude delivered ec323fc; Codex audited and
integrated only the approved Acadia catalog on app source 0a54252. Read
FINAL_HANDOFF.md for the current build/native result. Do not rerun acquisition,
preparation or key generation from this old brief. The separate follow-up lane
is bounded detector tests and specification review, as assigned by the owner.

## Objective and boundaries

Deliver one honest end-to-end path: choose a prepared video, understand its actual
analysis, and watch the exact prepared rendition. The user explicitly approved a
controlled reset after finding that too much effort had gone into static artwork.
Do not spend this lane on visual polish. Do not claim live analysis, interception
of other TV apps, clinical safety, or detected flashing from simulated intervals.

This file is an executable work brief for a separately opened Claude Code session.
Codex has not controlled a Claude terminal or started this work on Claude's behalf.

## Exact baseline and ownership

Repository: https://github.com/alejandro-publius/calm-frames (private).
Preserved baseline branch: codex/home-comparison-2026-10-15.
Preserved baseline HEAD: ee76cf559a5814183bc005de57512ee08a10fb5a.
Its final app source: 689c484efca088e65e76e0c7efeaf51f210c818e.
The original Claude candidate checkout must remain untouched:
/Users/alexvintera/calm-frames-claude-final-2026-10-14.

Codex owns codex/prepared-video-slice-2026-10-15 in:
/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-review.
Codex owns app/src, app/test, hook/src mirror when app changes require it,
shared typography/spacing/buttons/navigation, the evidence presentation adapter,
this handoff, UI preview and the final native integration build.

Claude owns a NEW independent checkout and branch claude/pipeline-evidence-2026-10-15
based on ee76cf559a5814183bc005de57512ee08a10fb5a. Claude owns pipeline/** and its tests, docs/evidence/video-reset/** and
results/video-reset/**. Run existing flashmap/eval tests without editing their
source; propose cross-boundary fixes for review. Keep all generated assets in
your own workspace outside app/**. Codex alone imports reviewed artifacts into
app/assets/raw/prepared-library. Do not edit any app/** file, hook/src, catalog
imports, package manifests, SDK links, global status docs, keys, or Codex's tree.
Do not overwrite a pre-existing directory or branch with these names. Inspect
status and applicable instructions first; if the proposed directory exists,
choose a new empty directory and report it. Do not reset or stash other work.

Example NEW checkout setup, only after confirming the destination does not exist:

```sh
git clone --no-hardlinks /Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-review /tmp/calm-frames-pipeline-evidence-2026-10-15
git -C /tmp/calm-frames-pipeline-evidence-2026-10-15 switch -c claude/pipeline-evidence-2026-10-15 ee76cf559a5814183bc005de57512ee08a10fb5a
```

The clone's origin initially points at the local checkout. Do not push to that
origin. Report commits for integration, or deliberately set the existing private
GitHub remote before an authorized private branch push. No public PR or release.

## Read first

Read CLAUDE.md, FINAL_HANDOFF.md, docs/SAFETY.md, pipeline/LOCAL_LIBRARY.md,
flashmap/docs/SPEC_SOURCES.md, pipeline/packaged_library.py and the current
catalog. Some high-level README text is stale: the current analyzer DOES contain
an informative broadcast regular-pattern implementation. Code, exact artifacts
and fresh receipts take precedence over dated marketing/status text.

## Current functionality, without embellishment

- Home uses static coastal art. It is not video analysis evidence.
- app/assets/raw/benign-story/harbor.mp4 is a 20-second, 1280x720 H.264 film,
  480 frames, AAC audio and subtitle track. It is animated original artwork.
- harbor.precovered.mp4 is the separate harmless practice rendition. Its two
  intervals are intentionally inserted by eval/benign_story.py, not detections.
  The runtime picture replacements are near 5-9 and 12-16 seconds; audio and
  playhead continue. Never use this as positive detector evidence.
- app/assets/raw/offline/calm_gradient.mp4 is a 12-second playback test.
- The active prepared catalog bundle is
  51b91d7413c50cc020452d4594a493fbf78e6d1ebac40c8066753b76c776d101.
  It has one title, source SHA
  de53dd81f60a44409531ad1ff57ee08fb213d9650b06c92ae1fe88a2cbbb526e,
  with wcag, broadcast and extra-cautious maps containing zero segments.
  The original report hash is
  18802e65a69233e259eeb2bc68056b22fdd8cbd3b5fdec04576a4464bf19d5f9.
  Its 48 checks passed, with outcome "no flagged segments".
- Runtime follows signed precomputed maps and checked prepared MP4s. It does
  not analyze TV frames live. Do not replace this architecture in this slice.
- Python decodes actual timestamps and temporal frames; default analysis width
  is 192 pixels, configurable. Distinguish temporal frame coverage from spatial
  resolution. HDR PQ/HLG is refused. Record unsupported/error cases as failures
  to assess, never passes. Inspect actual format/timestamp edge handling.
- Archived real-clip evaluation lists 16 titles and still has unanswered human
  labels. It is not independent validation. Source videos are not present in the
  inspected media directories. Do not turn archived candidate agreement into
  measured recall or independent expert labels.

## Your work, in order

1. Audit the existing video-to-report-to-rendition path against actual code.
   Establish timestamp handling, luminance/red/area/rolling windows, pattern
   scope, decode refusal, seek/loop boundary limits and input/output lineage.
   Record any unsupported claim or defect before changing code.
2. Use a short, openly licensed ordinary-motion SDR clip with verified source,
   license and attribution, modest download size, and explicit source SHA.
   Codex is researching a candidate; await its source/attribution packet or
   report your candidate before acquiring a different one. Do not fabricate
   real footage, download unknown large media, or show an unanalyzed source.
3. Run actual input analysis, normal preparation, mandatory output verification
   and package checks. Zero findings are a valid result. Report them as zero.
   Source and output analysis by the same engine are separate runs but NOT
   independent validation. Record an independent method only if it really ran.
4. Validate positive detection with the existing headless fixture harness and
   known expected temporal signals, distinct from the ordinary-motion demo.
   Never open, render, embed or record hazardous fixtures. Reuse fixture-managed
   cleanup; do not generate hazardous files outside that harness. Do not add
   hazard thumbnails to the report. Record expected and observed intervals,
   false negatives/positives and boundaries, rather than only "tests passed".
5. Produce a compact machine-readable evidence receipt and plain explanation.
   If no authorized existing signer is available, STOP before package export
   requiring new signatures. Preserve keys/configuration. Deliver the unsigned
   analysis and explicit signing block; do not create/rotate a signer, use demo
   keys, alter trust configuration, or bypass signature verification.
6. Commit focused pipeline/evidence changes in your branch. Return exact commit,
   tests/commands, input/output hashes, report paths and remaining blocks to the
   owner/Codex. Do not merge main or touch the user's running apps.

## Motion-footage candidate supplied by the research lane

Candidate only, NOT a verified ready asset: NPS Acadia B-Roll: Coastal Scenery,
37 seconds. Official page reports NPS Video and Public domain: Full Granting Rights.
Source page: https://npgallery.nps.gov/AssetDetail/6fc09aec-7fc2-47ed-b8cc-e1b10861dd3e
Official 720p MP4 candidate: https://npgallery.nps.gov/GetAsset/6fc09aec-7fc2-47ed-b8cc-e1b10861dd3e/proxyhires
Research reports the 1080p variant as 64.3 MB; the 720p size and actual SDR/color
metadata remain unverified. Claude owns acquisition and probing in its isolated
workspace, with a bounded download, source SHA and retained attribution/license
record. Do not preview it before analysis. Codex will not duplicate this download
or pipeline run. If acquisition, rights, decoding or signing blocks progress,
return the exact blocker and the report produced so far.

## Existing runnable commands and paths

Use the installed Python 3.12 environment, with THIS checkout first on import
paths so an editable package in another checkout does not silently run old code:

```sh
export PYTHONPATH="$PWD/flashmap/src:$PWD"
PY=/Users/alexvintera/calm-frames/.venv/bin/python
"$PY" -m flashmap check app/assets/raw/benign-story/harbor.mp4 --profile wcag --json /tmp/harbor-analysis.json
"$PY" -m flashmap report /tmp/harbor-analysis.json --out /tmp/harbor-report.html --license-csv media/LICENSES.csv
```

The report contains plots, no film frames, and does not play media.
For an approved local source and ALREADY AUTHORIZED existing signer:

```sh
"$PY" -m pipeline.local_library prepare /path/to/input.mp4 --workdir /path/to/separate-workspace --key /existing/private/key.pem --pub /existing/public/key.pub.pem --title "Actual video title"
"$PY" -m pipeline.local_library catalog --workdir /path/to/separate-workspace
"$PY" -m pipeline.packaged_library export --workdir /path/to/separate-workspace --pub /existing/public/key.pub.pem --output /path/to/separate-export
"$PY" -m pipeline.packaged_library check --output /path/to/separate-export --require-reports
```

The path placeholders are NOT credentials or permission to discover secret
values. No source file may overlap the pipeline workspace. Do not copy the
whole workspace to app assets; only the exporter's allowlisted outputs belong.
Do not run eval.prepare_owned_harbor merely for convenience: it creates a new
temporary signer, which is outside this instruction's unchanged-key boundary.
The upload_server is an existing local report UI, not automatic TV ingestion;
starting it is optional and does not replace the preparation/export steps.

Relevant existing tests (select according to changes; no capture scripts):

```sh
"$PY" -m pytest pipeline/tests/test_local_library.py pipeline/tests/test_packaged_library.py pipeline/tests/test_app_playback_recipe.py -q
"$PY" -m pytest flashmap/tests/test_vfr.py flashmap/tests/test_cli.py -q
```

Inspect fixture safety and actual test names before broad detector runs. Reuse
existing focused conformance tests where appropriate. Report exact collected
counts and known exclusions. No purchased analyzer, PEAT install, or external
service account should be introduced by this slice.

## UI/pipeline contract

Keep the version-1 compiled manifest contract. Required fields are already
present: bundleId; sourceSha256; durationMs; per-preset maps {path, sha256, text};
per-preset renditions {path, sha256, durationMs, startOffsetMs, guardBandMs,
minCoverMs, captions}; verification {reportSha256, checkedInputsSha256, outcome}.
The original report stays at reports/<reportSha256>.json and must match its hash.
Do not rewrite fields after signing or invent report success values.

Codex will expose read-only evidence only for an exact compiled title match,
using the existing playback identity predicate. A route-supplied report/key or
unverified map must not become trusted because it is displayed. UI counts come
from the verified maps under current settings, and will distinguish raw findings
from padded/merged hidden intervals. The evidence screen says analysis happened
before playback. It will separately label simulated demo events.

Minimum evidence receipt fields:
source_commit, input {path, sha256, bytes, license, source_url}, analysis
{profile, analysis_dimensions, frame_count, timestamp_range, raw_segments},
verification {report_sha256, checked_inputs_sha256, passed, outcome}, map hashes,
prepared rendition hashes and timing offsets, export bundle id, test commands
and outcomes, independent_validation (explicit status), and known limitations.
Native integration later adds package SHA and observed playback identity/events.
No fabricated clinical assessment or hazard-free promise.

## Acceptance and division of integration

- A selected catalog item, displayed evidence, player route and final packaged
  bytes identify the same prepared rendition and source; tampering is rejected.
- All three preset schedules remain consistent with prepared media and household
  rules. No shortcut around missing maps, wrong hashes, unknown keys or PINs.
- A real ordinary-motion input can complete normal preparation if signing access
  exists. Otherwise deliver exact analysis and the smallest explicit blocker.
- Positive headless tests are labeled synthetic and distinct from demo overlays.
- New evidence is reproducible without AWS, billing, credentials changes or a
  public publication. Existing tests and data remain intact.
- Codex alone integrates assets, builds the final app and runs the authorized
  non-capture native route test. Claude should not compete for the simulator,
  shared SDK workspace, local preview port or another session's app instance.
- UI quality still requires sight/reading-distance review; tests do not prove
  visual quality. Logs do not prove audible continuity or visible captions.

## Hard constraints

No deletion of user work; no main merge; no public publishing; no release tag;
no screenshots, screen/video capture or capture scripts; no hazardous display;
no new billing, AWS deployment or credential/key configuration changes. No
control of another Claude terminal. Do not retry or bypass denied access.
Report access/usage limits promptly. Finish by reporting useful artifacts,
exact evidence and remaining blocks rather than claiming completion by tests.
