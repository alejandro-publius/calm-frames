# Evidence reconciliation for the October 23 integration

Reviewed source: `6360417814d684d41c94789a9e406fc27de53c66`, on the isolated `codex/integration-owner-2026-10-23` branch. This is a source and recorded-evidence review, not a new native run. The [machine receipt](../../results/cloud-integration-2026-10-23/evidence-review.json) records tree comparisons, screenshot checksums and boundaries. The [latest integration status](../handoff-2026-10-23/INTEGRATION_STATUS.md) supersedes older source-status paragraphs in the historical handoff.

## Identities that must stay separate

| Identity | Meaning and evidence |
|---|---|
| `6360417814d684d41c94789a9e406fc27de53c66` | Fetched PR #2 head at review start. Relative to code commit `12125b2970342b5376b0bc7964383e547b407376`, only README, start instructions, documentation and the integration receipt changed. Application, hook, pipeline and analyzer trees match that code commit. |
| `12125b2970342b5376b0bc7964383e547b407376` | Code identity for the [recorded cloud regression pass](../../results/integration-2026-10-23/receipt.json). That receipt contains passed, skipped and root-only failed results separately. Its historical hosted-dispatch blocker is superseded by actual current GitHub run metadata, not by these local results. |
| `bd55e470b895aa9e8b7ef8a843f0a742fce3611b` | Latest installed production source named by the [native profile/polish receipt](../../results/native-profiles-retry-polish-2026-10-23/receipt.json). The current candidate includes later source changes; those screenshots do not prove the current candidate was installed. |
| `4b04877f60101b33fc2e93e1e56413bcd165b051` | Production source used for the profile-isolation observation in that receipt. The onboarding footer fix was built and installed, but the first-run footer itself was not re-observed. |
| `3bc658f0491b02b92fa22bc454a40887ecbf23ae` | Source for the [full McWay run, ending hold, paused recovery, Back and background observations](../../results/native-async-retest-2026-10-23/receipt.json). It is not a new native observation of `6360417`. |
| `84faeed7dee851c713f75faaff2f8522a961d609` | Separate benign Retry harness. Its trigger/manifest must never enter production. Harness observations are labelled below, not converted into spontaneous production-failure evidence. |
| `bf2f615e6fad0d73442fe2b9acab3067bf311e7e` | Submitted fallback. Keep its branch, package and public demo intact. The older judging guide remains an earlier snapshot, not a current-UI certificate. |

The Retry harness and rejected browser UI `76223f99cf8543ffe1e75d54c9873b56a0c23318` are absent from the reviewed candidate ancestry. This review changed no app, tests, media, maps, keys, household data, shared branch or simulator state.

## Implemented work to retain

| Area | Source and recorded checks | Current evidence boundary |
|---|---|---|
| Profile-picker focus | `bde35e9`: [KidHomeScreen](../../app/src/calmframes/KidHomeScreen.tsx) stops competing preferred-focus requests while the picker is open, keeps it open while saving, then returns focus to the header button. [Picker focus tests](../../app/test/calmframes/pickerFocusReturn.test.tsx) and [household restart tests](../../app/test/screens/householdRestart.test.tsx) cover the failure paths. | Implemented and included in the recorded cloud pass. Native screenshots at `bd55e47` precede this follow-up fix; current-source D-pad/save/focus acceptance remains a Mac check. |
| Watch labels and concise copy | `2403d8f`: [KidHomeScreen](../../app/src/calmframes/KidHomeScreen.tsx) gives approved consumer scenes the Watch action; [PictureHoldIntroduction](../../app/src/calmframes/PictureHoldIntroduction.tsx) carries the approved protective-behavior disclosure. Earlier copy removal is already included. | Do not repeat the copy cleanup or remove essential error, safety and accessible labels. Current-source native wrapping remains unobserved here. |
| Minimum title-card text | `9f8c612`: paired island title and qualifier styles use the established text floor in [KidHomeScreen](../../app/src/calmframes/KidHomeScreen.tsx). [Ten-foot tests](../../app/test/calmframes/tenFoot.test.tsx) render the real island map. | Structural/rendered-tree measurements establish the guard; they do not establish readability on a physical TV or native focus clipping. |
| Protection-restoration rejection | `5e4da02` adds a regression for a stored checkpoint carrying altered settings and intervals. [Checkpoint validation](../../app/src/calmframes/playbackCheckpoint.ts) constructs an explicit allowed-field object. [Checkpoint tests](../../app/test/calmframes/playbackCheckpoint.test.ts) verify no preset/settings fields survive and edition/profile mismatches are refused. | This confirms the existing boundary; it is not a native observation of deliberately different profile protection settings. Current household and verified route remain authoritative. |
| Decode completeness provenance | `12125b2` narrows the measured-source allowance using the stored conformance record. The [integration status](../handoff-2026-10-23/INTEGRATION_STATUS.md) records why the completeness check could not move those recorded rows. | No new conformance measurement was made in this review. The earlier interrupted conformance run is not acceptance evidence. |

## Native and human acceptance ledger

| Capability | Status now | Exact remaining check or limit |
|---|---|---|
| Separate profile positions | **Observed on predecessor source and through rename on `6a87937`.** The [profile receipt](../../results/native-profiles-retry-polish-2026-10-23/receipt.json) and [received name-editor review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md) record distinct saved positions. | Retain the completed observation. Position isolation does not prove different protection presets; do not reset the household or request a PIN in chat. |
| Name editing, persistence and focus return | **Mac operator observed on `6a87937`.** [Verified source/package mapping and per-check scope](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md) cover editing, Save through relaunch, Cancel/Back and return to Edit name. | Native failed-write/retry and VoiceView remain unobserved. Duplicate refusal covered the household label only. The newer cloud privacy patch is outside this native package. |
| Stricter per-profile protection | **Automated boundary implemented; differential native observation missing.** | With owner-controlled private PIN entry and ordinary protected controls, compare a stricter profile before and after Resume, then restore the test setting. Position isolation alone does not prove this behavior. |
| McWay sustained playback and ending | **Observed on `3bc658f`.** Its receipt records a full-duration run, final still remaining until explicit Back, completion clearing Resume and the next Watch starting fresh. | Source-bound prior evidence, not universal performance or a fresh candidate run. Native frame counters were unavailable; measured clock progress is not every rendered frame. |
| Sustained viewing beyond McWay | **Stationary defaults implemented; native coverage remains scoped.** The `6a87937` pass opened Acadia's still scene. Sea Otters and Forest reached Details only. | Observe the two unopened still scenes when native access is available. Do not describe short previews as five-minute moving scenes or prepare new footage just to expand the catalog. |
| Explicit Retry | **Bounded harness observation.** The [latest receipt](../../results/native-profiles-retry-polish-2026-10-23/receipt.json) describes covered failure; the first Try again returned to ready error, the next reached recovery and playback. Production was restored. | This is a benign injected-failure test on the separate harness. Capture gaps and missing useful app-scoped callback logs prevent exhaustive compositor/decoder-ordering proof. Never merge or present the harness as production. |
| Cover before seek | **Bounded predecessor evidence.** [Skip receipt](../../results/native-acceptance-gaps-2026-10-23/receipt.json) records a cover request before the playhead write, covered seeking/seeked events and uncover after confirmation. [Recovery tests](../../app/test/calmframes/playbackRecovery.test.ts) require seek confirmation and fresh timeupdate before play. | Request order and sampled frames do not prove an opaque frame reached the compositor before every seek or decoder event. Keep the native instrumentation limit explicit. |
| Decoder release and Back/background | **Source guards and scoped predecessor observations.** [Async retest receipt](../../results/native-async-retest-2026-10-23/receipt.json), [VideoHandler](../../app/src/utils/VideoHandler.ts) and [native playback tests](../../app/test/calmframes/nativePlaybackRecovery.test.tsx) cover release and recovery paths. | Do not infer exhaustive current-candidate native callback ordering from mocked events or an absence of visible errors. Do not weaken covers, timeouts or ownership barriers for a demo. |
| Caption restoration | **Implemented with simulated-native tests; non-applicable to the shipped consumer catalog.** [Caption inventory](../../results/native-acceptance-gaps-2026-10-23/catalog-caption-inventory.json) records no caption tracks in Acadia, McWay, Forest or Sea Otters. [Native playback tests](../../app/test/calmframes/nativePlaybackRecovery.test.tsx) restore language/label onto a changed native track ID. | Do not claim observed native caption restoration or add new media merely for the checklist. A separately approved eligible captioned fixture would be needed for that native observation. |
| Onboarding footer | **Source fix/build/install recorded; native layout unobserved.** [Footer receipt](../../results/native-onboarding-footer-2026-10-23/receipt.json), [FirstRunScreen](../../app/src/calmframes/FirstRunScreen.tsx), [first-run tests](../../app/test/calmframes/firstRun.test.tsx). | Use an authorized isolated first-run fixture that preserves the real household. Check supported sizes, footer visibility, wrapping and D-pad reachability without recording PIN entry. |
| Accessibility and reduced motion | **Name-grid D-pad and focus return observed on `6a87937`; full acceptance remains open.** [Artwork motion tests](../../app/test/calmframes/artworkMotion.test.tsx) cover reduced or unknown settings. | VoiceView was unobserved, with a missing AccessibilityManager diagnostic in the supplied log. This does not establish universal platform absence. Native screen-reader/reduced-motion checks and independent inspection of the existing captures remain open. |
| Light opening transition | **Reported observation; cause and comfort effect unresolved.** | Inspect benign, source-bound native evidence before changing surface timing. Keep presentation and protection logic separate; no repeated exposure to an uncomfortable transition to make a demonstration. |
| Human audiovisual acceptance | **Missing.** Latest native receipts explicitly retain this limitation. | Owner listening, palette/pacing/comfort and full-video acceptance cannot be inferred from audio measurements, technical gates or general approval to continue. |

## Personal-file import and caregiver pre-check

The source implements two local utilities, separate from the native Fire TV interface:

- [pipeline/upload_server.py](../../pipeline/upload_server.py) accepts a clip for analysis and a report. It has no playback page or file-serving route, and binds to loopback by default. This is a pre-check/report workflow, not TV playback authorization or medical screening.
- [pipeline/local_intake.py](../../pipeline/local_intake.py) implements bounded file intake, analysis, review and prepared-package export. An authorized signer is required for preparation; it reports that analysis-complete content is not playable on TV when the signer is absent. It never serves original/prepared video through its HTTP routes.
- [pipeline/package_delivery.py](../../pipeline/package_delivery.py) and [edition_delivery.py](../../pipeline/edition_delivery.py) stage/recheck immutable packages against exact approvals. Their review states do not mean installed or watchable. TV membership still depends on compiled approval data, checked build and installation.

The [local intake evidence](../../results/local-intake-2026-10-17/receipt.json) is historical execution evidence for that utility. Its old handoff's signing-blocked paragraph was superseded for specifically approved content by later work; do not repeat it as a current global blocker. Likewise, the older [package delivery handoff](../PACKAGE_DELIVERY_HANDOFF.md) describes an earlier catalog and budget. Current source and compiled approvals govern those values. No new personal file reaching the current TV app was demonstrated in this review, and no on-device arbitrary-file picker is implemented by these utilities.

## Deferred analyzer identity change

[pipeline/ingest.py](../../pipeline/ingest.py) keys analysis with source/preset/room/signing inputs and `decode_evidence_revision: 1`; it does not include the analyzer's own version or source identity. [PREPARATION_RECOVERY.md](../PREPARATION_RECOVERY.md) records this limitation. A cache-key migration can invalidate approved workdirs, regenerate maps and create new timestamps/signatures. Keep it a separate deferred change with synthetic-workdir checks and explicit approval before any real approved-edition preparation. No cache invalidation or media preparation occurred here.

## Rollback and external-artifact boundary

These are hashes recorded in supplied repository receipts, not cloud rehashes of available packages:

| Package role | Recorded source | Recorded SHA-256 |
|---|---|---|
| Received Mac names acceptance, Debug | `6a87937` | `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d` |
| Rollback retained for that pass, Debug demo | `2cf54e0` | `e3458d5a59e6d68cd96b50e1ebe4784c1bdfbcbcadca3b1a8b6ba4c3f7b9b3c5` |
| Earlier coastal production | `bd55e47` | `4d229b6fd9c2a1ab61aa22eb996a673243da367db66035cb7f640bf70214e8a7` |
| Earlier footer rollback | `4b04877` | `2bfac62fe2bd992186dd5d948a18b47dc5392f5e003c1cc49280be2476963101` |
| Submitted-era rollback | App/hook trees recorded equivalent to `bf2f615` | `207898aa14d8659760348a716b825fabab83afd8e3b9431f9387202cc10e7163` |

The earlier package locations and package-scoped restoration procedure are in
the [Mac acceptance checklist](../handoff-2026-10-23/MAC_ACCEPTANCE_CHECKLIST.md).
The [received names review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md)
records the newer package and retained rollback separately. Native binaries,
raw logs and the older replacement MP4 are excluded from Git. The newly received
ZIP supplies capture hashes but no image bytes; older committed native images
remain predecessor captures. A recorded path or hash does not establish receipt
of the corresponding binary or image.

The existing replacement-demo receipt describes source `d96c088` and is stale for the newer profile/recovery UI. Keep public submitted materials unchanged unless an exact validated replacement is explicitly selected and authorized within the permitted window. No claim in this ledger certifies release, medical safety, hosted CI success, judge access or current competition rules.
