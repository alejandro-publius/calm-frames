# Calm Frames canonical product checkpoint

This cloud thread is the sole integration owner. This is unpublished development,
not a replacement submission. The original 20 requested outcomes below supersede
the earlier operational checklist, whose narrower scopes overstated completion.
The Git history retains that older record.

## Exact source and ownership

| Role | Exact source and inclusion |
|---|---|
| Submitted fallback | `bf2f615e6fad0d73442fe2b9acab3067bf311e7e`; existing video and live materials remain unchanged. |
| Frozen integration branch | `codex/integration-owner-2026-10-23`, `2cf54e0d168e58daedfde3f15407833d23af4e93`. Remote identity checked in the [hosted receipt](../../results/design-polish-2026-10-23/cloud-finish/hosted.json). |
| Current review branch | `codex/design-polish-2026-10-23`. Resolve the full final HEAD from the verified transfer manifest and this thread's final checkpoint. It descends from the frozen integration source; no merge is needed to include that work. |
| Included UI work | `41bdeb94ca1c3e8cceabafd821f141587f77c202` adds pending-PIN feedback; `fb7f48031d3ae587c8fba40422566c68a0a1f23f` refines Home, Details and Parents; `edbd4359443454c115c9137861f2e39ec575677c` separates four islands; `d7da316d2d48c3b66b3cc4874257e98ca5ef943e` capitalizes Sea Otters. |
| Included cloud correction | `acf064c` fixes Python lint; `f5ea4fb` fixes legacy shell-quote. `5bf123409d8d863e2dbefd73bc3b2046e264d89e` fixes nested Lodash and Minimatch. [Latest dependency receipt](../../results/design-polish-2026-10-23/dependency-wave2/receipt.json) records exact inputs and checks. |
| Fable implementation lane | Verified source `6cda443c3475bd086e62a0582cce42a6a49a4695` received from the user. Feature `9546c0f` and evidence `6cda443` replayed as `9a2db49` and `f32f2d6`. The [integration review](../design-polish-2026-10-23/FABLE_INTEGRATION.md) records cloud Back/focus corrections and exact checks. Original source preserved on `codex/fable-handoff-6cda443`; no other cloud editor is active. |
| Prior completed handoffs | Claude source through `6360417814d684d41c94789a9e406fc27de53c66` is an ancestor. Combined release checks were replayed as `0371ebaa`, `5ef3b0d1`, `3bcfe542`; judging package `9ad7bb7` was replayed as `a61c83c5`. Its package tree remains identical. [Original-to-integrated map](../CLOUD_RELEASE_CHECKPOINT.md#integrated-inputs). No duplicate import. |
| Explicit exclusions | The separate Retry harness and rejected browser UI remain excluded by the integration record and task boundary. Their referenced full objects are unavailable here, so this is not a new ancestry certificate for those references. New narration, illustrations and replacement video are not included. |

## Hosted checks and remaining release blockers

The latest read of frozen `2cf54e0` shows [CI 40007368463](https://github.com/alejandro-publius/calm-frames/actions/runs/40007368463)
**failed at Python lint**. Vega app, modeled UI checks, secret scan, mutation/property
checks and published-number checks passed. [Audit 40007372605](https://github.com/alejandro-publius/calm-frames/actions/runs/40007372605)
**failed at dependency policy**; its infrastructure, ARM64 image and SBOM jobs passed.
These are results for that exact frozen source, not for the newer local review branch.
No hosted run has validated the local review changes. No run was restarted here.

Pinned Ruff 0.17.0 reproduced the lint defects in the demo preflight tooling.
They are fixed without changing the lint configuration or approved narration.
The dependency continuation replaces the old shell-quote leaf with the already
used fixed 1.11.0 version. See the [dependency decision](DEPENDENCY_DECISION.md)
and [cloud receipt](../../results/design-polish-2026-10-23/cloud-finish/receipt.json).
The next local fix, `5bf1234`, deduplicates old Lodash onto the existing 4.18.1
and moves only Minimatch 3.x onto 3.1.5. Six more advisory IDs are removed,
with no additions. Clean normal checks and unchanged installed build-tool
behavior are recorded in the [latest receipt](../../results/design-polish-2026-10-23/dependency-wave2/receipt.json).
Other dependency findings and expired exception groups remain blockers. The
owner's TOML-only approval through October 30 is not blanket acceptance.

## One 20-item product checklist

These are the user's original items in their original order. Implemented code,
local checks, native observations, publication and acceptance are separate facts.
A partial item can contain completed subparts; it is not a reason to redo them.

| # | Original outcome | Status | Evidence and next action |
|---|---|---|---|
| 1 | Cohesive native design | Partially completed | [Approved broader visual work](../design-polish-2026-10-23/README.md) is implemented through `d7da316`, including separate Acadia and McWay islands. Browser renders are not native acceptance. Next: exact-source D-pad/layout review; no new redesign. |
| 2 | Redundant-copy removal | Partially completed | `2403d8f` and existing Details/still/recovery copy changes are retained; [source ledger](EVIDENCE_RECONCILIATION.md#implemented-work-to-retain). Next: current-build screen sweep, preserving necessary protective/error disclosures. |
| 3 | Loading and transitions | Partially completed | `41bdeb9` adds visible PIN-checking feedback. The reported pale opening frame still has no established cause. Next: benign source-bound native observation before changing any player or cover timing. |
| 4 | Watch and focus visibility | Partially completed | `ae30cc7` contrast fixes, clean normal checks and later coastal refinements are implemented. [Contrast receipt](../../results/cloud-integration-2026-10-23/ui-contrast.json). Next: observe rest/focus/press and selection on this native build. |
| 5 | PIN, profiles and kid names | Partially completed | Editable names are implemented and integrated: letter keys, validation, committed-save feedback, cancel/retry and preserved profile identity. [Integration review and receipt](../design-polish-2026-10-23/FABLE_INTEGRATION.md). Visible Back and preferred-focus conflicts are corrected. Next: native D-pad, VoiceView, focus return and failed-write acceptance. Current entry supports letters and spaces only. |
| 6 | Onboarding footer | Partially completed | [Recorded code/build fix](../../results/native-onboarding-footer-2026-10-23/receipt.json) is retained. Next: isolated first-run native fixture to inspect wrapping/reachability without resetting the real household. |
| 7 | Ambient experience across titles | Partially completed | McWay sustained playback/ending was observed on `3bc658f`. Acadia, Sea Otters and Forest have still defaults and explicit short previews. [Native ledger](EVIDENCE_RECONCILIATION.md#native-and-human-acceptance-ledger). Next: check existing routes on selected native source; equal long moving editions are not delivered. |
| 8 | Human audio and comfort review | Blocked | No final-build owner listening/palette/comfort receipt. Next: owner observations tied to package identity. Script approval and technical measurements do not supply them. |
| 9 | Cover, seek and decoder ordering | Partially completed | [Source and predecessor evidence](EVIDENCE_RECONCILIATION.md#native-and-human-acceptance-ledger) supports scoped behavior. Harness-only Retry is separate; compositor timing is not proved. Next: benign native checks with instrumentation limits recorded. |
| 10 | Profile protection and captions | Partially completed | Profile positions were independently observed on `4b04877`; `5e4da02` rejects stored protection overrides. Shipped consumer titles have [no caption tracks](../../results/native-acceptance-gaps-2026-10-23/catalog-caption-inventory.json). Next: stricter-profile native recovery; do not claim native caption restoration. |
| 11 | Native accessibility | Partially completed | **Implementation:** done on local branch `claude/native-accessibility-2026-10-24`, candidate `3b0174b` (production commits `4d4152c`, `3ede1fa`, `88c1716`, `eeaaf16`, `3b0174b`; [notes](../design-polish-2026-10-23/claude-native-accessibility/README.md); earlier source guards: [evidence ledger](EVIDENCE_RECONCILIATION.md#native-and-human-acceptance-ledger)). **Native acceptance:** partial. VoiceView and D-pad passed at 1920 by 1080 and 1280 by 720 for Home, Details, More info, How it works, the Parents rows, footer and explainer, and the name editor with made-up names; the resume prompt heading and first focus pass. Open: seek bar progress announcements blocked upstream in Kepler UI Components 3.2.2; VoiceView's own Back or bare button at resume prompt entry in 2 of 5 openings; reduced motion not observable on the virtual device; no physical TV or human listening. **Final integration:** not done. Cloud follow-up `226d317` is missing, and #6 `dd1ec6c` is separate. Next: reconcile both, then the owner's listening on the exact integrated package. |
| 12 | Further technical depth and dependency audit | Partially completed | Recovery and decode-completeness work retained. Lint and shell-quote fixes are followed by Lodash/Minimatch remediation in `5bf1234`, with [six advisory IDs removed and clean normal checks](../../results/design-polish-2026-10-23/dependency-wave2/receipt.json). Next: resolve residual findings/expired exceptions and validate the selected exact source in hosted CI. Audit remains blocked; analyzer cache identity stays separate. |
| 13 | Personal import and caregiver pre-check | Partially completed | [Local intake/report utilities](EVIDENCE_RECONCILIATION.md#personal-file-import-and-caregiver-pre-check) exist. They are not a finished native TV import journey and do not authorize arbitrary files for playback. Next: define that later user journey separately; no invented delivery claim. |
| 14 | GitHub presentation | Partially completed | Review README now leads with the photosensitive-epilepsy design purpose, standalone scope and exact evidence boundaries. Historical images remain labelled. Next: current native captures and explicitly authorized publication; default branch is unchanged. |
| 15 | Devpost and YouTube copy | Partially completed | [Private drafts](PRESENTATION_DRAFTS.md) now retain the core purpose and scope limits. Next: reconcile with accepted source before any permitted publication. Live text is frozen. |
| 16 | Manga/native/ElevenLabs demo | Deferred | [Approved script and tooling](demo/README.md) exist. No generated narration, illustrations or finished current-source replacement video are claimed. Next: accepted product freeze, show any material script revision, then production and human review. |
| 17 | Submission and judge requirements | Partially completed | Submitted fallback retained; earlier judging evidence preserved. Current official rules/access are not freshly reverified. Next: authoritative permitted-window/access confirmation before any submission action; no invites or live edits. |
| 18 | Single source of truth | Partially completed | Original numbering retained; Fable source is received, verified and integrated once with the cloud dependency work. One reviewed development branch and transfer manifest identify the source. Next: attach the Mac package hash and acceptance receipt to that exact source. |
| 19 | Publish upgraded artifacts | Blocked | Review branch remains local and unsubmitted. Native/human acceptance and Audit remain open. Next: complete gates and obtain a permitted publication decision; no automatic promotion. |
| 20 | Reading comfort mode | Deferred | Not implemented. Keep last; later bounded text/spacing work requires native wrapping/focus checks. No treatment claim. |

## Mac-only acceptance, without duplicate work

A Mac operator was confirmed available; a completed acceptance receipt has not
arrived here. Use [MAC_ACCEPTANCE.md](MAC_ACCEPTANCE.md) with the exact current
transfer manifest, not the obsolete f9c210b package or an inferred Mac path.
The current export includes Fable and the cloud fixes; use its exact source for the next build. Preserve
private PIN entry, household data, approved media and a verified rollback package.
Report native focus/button appearance, onboarding footer, protection/recovery
ordering, retained title routes, VoiceView/reduced motion and owner listening/
comfort as observed, failed or unobserved. A source test cannot mark them passed.

## External inputs and publication boundary

The source and browser work continues privately after the user-stated October 23
noon Pacific cutoff. No public posting, branch push, main merge or submitted
material change is authorized by this continuation. The old judging guide and
native captures remain historical evidence. This app plays its own prepared
catalog; it does not protect playback in Prime Video, Netflix or other apps.

The owner already approved the existing narration, a calm built-in voice choice
and the budget. Do not ask again. Production remains parked until product
acceptance; the unchanged script must then be reconciled with that exact build.
Secure API access is a later-stage requirement, not a blocker to source work.
