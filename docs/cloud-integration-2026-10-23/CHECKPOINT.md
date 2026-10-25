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
| Mac acceptance snapshot | `codex/design-polish-2026-10-23`, `6a87937f9f185ac0760d6f8331184e34b876d92c`. The [received native receipt review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md) ties this source to recorded package SHA-256 `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d` and matching installed-device SHA-384. Preserve this immutable snapshot. |
| Isolated cloud follow-up | `codex/dependency-followup-2026-10-23`. Code `121270e802df1f150f09a4216319f1af1f1fd67b` updates Ajv/Zod; `2f187d1723f65c7a09fe566a1e13aea91bdbcbb4` fixes the legacy logger. Code `07db296137ec3ba50afff15097053061709fda27` suppresses private name/PIN key focus traces, preserving layout and interaction. These changes are not in the Mac snapshot or published; [dependency receipt](../../results/design-polish-2026-10-23/dependency-wave4/receipt.json), [privacy receipt](../../results/design-polish-2026-10-23/private-input-trace/receipt.json). |
| Included UI work | `41bdeb94ca1c3e8cceabafd821f141587f77c202` adds pending-PIN feedback; `fb7f48031d3ae587c8fba40422566c68a0a1f23f` refines Home, Details and Parents; `edbd4359443454c115c9137861f2e39ec575677c` separates four islands; `d7da316d2d48c3b66b3cc4874257e98ca5ef943e` capitalizes Sea Otters. |
| Included cloud correction | `acf064c` fixes Python lint; `f5ea4fb` fixes legacy shell-quote. `5bf123409d8d863e2dbefd73bc3b2046e264d89e` fixes nested Lodash and Minimatch. [Mac-snapshot dependency receipt](../../results/design-polish-2026-10-23/dependency-wave2/receipt.json) records exact inputs and checks. |
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

The separate follow-up fixes Ajv 8 and Zod 4 without changing their consumers.
Fresh matching scans remove two advisory IDs, from 23 to 21, with no additions;
the fresh baseline includes a Zod finding absent from the prior scan. The
[follow-up receipt](../../results/design-polish-2026-10-23/dependency-wave3/receipt.json)
records clean normal checks and reproduced SBOMs. The remaining findings and
expired exceptions still block Audit. Fable's Mac target remains `6a87937`.

The next bounded fix scopes legacy logkitty to its patched 0.7.1 version while
retaining both CLI versions. Fresh matching scans remove the critical
GHSA-v8v8-6859-qxm4, from 21 to 20 unique advisory IDs, with none added. There
are no critical entries in that app-lock scan. The [logger receipt](../../results/design-polish-2026-10-23/dependency-wave4/receipt.json)
records reproduction of the old host-shell interpolation, compatible CLI
behavior, clean normal checks and SBOM reproduction. Audit still has remaining
findings and expired exceptions; zero critical app-lock entries is not release
acceptance or a complete native inventory.

Fable's smaller evidence ZIP is now received and verified. The source export,
lockfile and recorded installed-package identity agree with `6a87937`; all
listed file checksums pass. The [native review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md)
records name editing, persistence, focus return and position isolation as Mac
operator observations, with relevant trace corroboration. Screenshots are
indexed but were excluded from the ZIP. Still-route coverage and duplicate-name
coverage are narrower than their recorded passed labels. Failed-write retry,
VoiceView and owner comfort remain open. Do not repeat already observed checks
or infer that every native criterion has passed.

Cloud code `07db296` fixes the concrete privacy issue Fable identified and the
same issue in PIN keys. Debug key focus no longer discloses letter/digit IDs;
ordinary navigation diagnostics remain. [Focused regressions](../../results/design-polish-2026-10-23/private-input-trace/receipt.json)
reproduce the old behavior and verify key actions, labels, focus feedback and
name persistence afterward. Normal typecheck/lint pass. This is a local code
fix, not an updated installed Mac package or new native acceptance.

## One 20-item product checklist

These are the user's original items in their original order. Implemented code,
local checks, native observations, publication and acceptance are separate facts.
A partial item can contain completed subparts; it is not a reason to redo them.

| # | Original outcome | Status | Evidence and next action |
|---|---|---|---|
| 1 | Cohesive native design | Partially completed | [Approved broader visual work](../design-polish-2026-10-23/README.md) is implemented through `d7da316`. Home/Details routes were traversed by the Mac operator on `6a87937`; [review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md). Next: receive the existing cropped native images for independent layout inspection and collect owner comfort; no new redesign. |
| 2 | Redundant-copy removal | Partially completed | `2403d8f` and existing Details/still/recovery copy changes are retained; [source ledger](EVIDENCE_RECONCILIATION.md#implemented-work-to-retain). Next: current-build screen sweep, preserving necessary protective/error disclosures. |
| 3 | Loading and transitions | Partially completed | `41bdeb9` adds visible PIN-checking feedback. The reported pale opening frame still has no established cause. Next: benign source-bound native observation before changing any player or cover timing. |
| 4 | Watch and focus visibility | Partially completed | Contrast and coastal refinements retained. Mac operator observed name-grid focus and return after Save/Cancel/Back on `6a87937`, corroborated by control traces. [Review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md). Next: inspect existing native images for rest/focus/press appearance; traces do not establish pixels. |
| 5 | PIN, profiles and kid names | Partially completed | Native editing, limit/blank refusal, save persistence through relaunch, Cancel/Back and position isolation are recorded on verified `6a87937`; [review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md). Duplicate refusal covered the household label only. Next: controlled native failed-write/retry, sibling-name coverage and eventual combined-build privacy check. Local `07db296` suppresses name/PIN key traces. Do not repeat the completed functional name pass. |
| 6 | Onboarding footer | Partially completed | [Recorded code/build fix](../../results/native-onboarding-footer-2026-10-23/receipt.json) is retained. Next: isolated first-run native fixture to inspect wrapping/reachability without resetting the real household. |
| 7 | Ambient experience across titles | Partially completed | McWay sustained playback/ending remains observed on `3bc658f`. The `6a87937` pass traversed McWay playback and Acadia still playback; Sea Otters and Forest reached Details only. [Native ledger](EVIDENCE_RECONCILIATION.md#native-and-human-acceptance-ledger). Next: the two unopened still scenes; no equivalent long moving editions are delivered for those titles. |
| 8 | Human audio and comfort review | Blocked | No final-build owner listening/palette/comfort receipt. Next: owner observations tied to package identity. Script approval and technical measurements do not supply them. |
| 9 | Cover, seek and decoder ordering | Partially completed | [Source and predecessor evidence](EVIDENCE_RECONCILIATION.md#native-and-human-acceptance-ledger) supports scoped behavior. Harness-only Retry is separate; compositor timing is not proved. Next: benign native checks with instrumentation limits recorded. |
| 10 | Profile protection and captions | Partially completed | Position isolation was observed on `4b04877` and through rename on `6a87937`; `5e4da02` rejects stored protection overrides. Shipped consumer titles have [no caption tracks](../../results/native-acceptance-gaps-2026-10-23/catalog-caption-inventory.json). Next: differential stricter-profile native recovery; positions do not prove protection or caption restoration. |
| 11 | Native accessibility | Partially completed | **Implementation:** done on `claude/native-accessibility-2026-10-24`, production commits `4d4152c`, `3ede1fa`, `88c1716`, `eeaaf16`, `3b0174b` ([notes](../design-polish-2026-10-23/claude-native-accessibility/README.md); earlier source guards: [evidence ledger](EVIDENCE_RECONCILIATION.md#native-and-human-acceptance-ledger)). Native name-grid D-pad travel and focus return were recorded on `6a87937`. **Native acceptance:** partial. VoiceView and D-pad passed on `3b0174b` at 1920 by 1080 and 1280 by 720 for Home, Details, More info, How it works, the Parents rows, footer and explainer, and the name editor with made-up names; the resume prompt heading and first focus pass. Open: seek bar progress announcements blocked upstream in Kepler UI Components 3.2.2; VoiceView's own Back or bare button at resume prompt entry in 2 of 5 openings; reduced motion not observable on this virtual device (that diagnostic does not prove other setups lack it); no physical TV or human listening. **Final integration:** under way on `claude/integration-2026-10-24` with cloud `226d317` and #6 `dd1ec6c`; not yet verified. |
| 12 | Further technical depth and dependency audit | Partially completed | Prior fixes retained. Isolated `121270e` fixes Ajv/Zod; `2f187d1` also removes the critical legacy logger advisory with [clean normal checks and reproduced SBOMs](../../results/design-polish-2026-10-23/dependency-wave4/receipt.json). The latest app-lock scan retains 20 unique IDs and no critical entries. Next: review residual findings and exact native inventory, then select and validate the combined source in hosted CI. Audit stays blocked; no exception renewal or analyzer-cache change. |
| 13 | Personal import and caregiver pre-check | Partially completed | [Local intake/report utilities](EVIDENCE_RECONCILIATION.md#personal-file-import-and-caregiver-pre-check) exist. They are not a finished native TV import journey and do not authorize arbitrary files for playback. Next: define that later user journey separately; no invented delivery claim. |
| 14 | GitHub presentation | Partially completed | Private README now includes editable kid names with source evidence and input/native limits, alongside the core purpose and standalone scope. Historical images remain labelled. Next: current native captures and explicitly authorized publication; default branch is unchanged. |
| 15 | Devpost and YouTube copy | Partially completed | [Private drafts](PRESENTATION_DRAFTS.md) now include the name-editor journey and code-grounded architecture without changing the approved narration. Next: reconcile with accepted source before any permitted publication. Live text is frozen. |
| 16 | Manga/native/ElevenLabs demo | Deferred | [Approved script and tooling](demo/README.md) exist. No generated narration, illustrations or finished current-source replacement video are claimed. Next: accepted product freeze, show any material script revision, then production and human review. |
| 17 | Submission and judge requirements | Partially completed | Submitted fallback and historical judging evidence retained. A fresh rules-page request was [blocked by the cloud proxy with HTTP 403](../../results/design-polish-2026-10-23/dependency-wave3/official-rules-access.json). Next: accessible official rules and authoritative permitted-window/access confirmation; no inferred deadline, invitations or live edits. |
| 18 | Single source of truth | Completed | Fable source and native receipt are received and reconciled once. [Verified source/package mapping and scope](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md) separate the immutable Mac build, later cloud code and submitted fallback. Original numbering and the one-owner checkpoint are current. Next maintenance: attach later combined-build results to their own source. |
| 19 | Publish upgraded artifacts | Blocked | Review branch remains local and unsubmitted. Native/human acceptance and Audit remain open. Next: complete gates and obtain a permitted publication decision; no automatic promotion. |
| 20 | Reading comfort mode | Deferred | Not implemented. Keep last; later bounded text/spacing work requires native wrapping/focus checks. No treatment claim. |

## Mac-only acceptance, without duplicate work

Fable's native receipt is received and its scope reconciled. Use the
[per-check review](../design-polish-2026-10-23/NATIVE_NAMES_REVIEW.md) to retain
completed observations and identify gaps. Use [MAC_ACCEPTANCE.md](MAC_ACCEPTANCE.md)
for those remaining observations, not the obsolete f9c210b package or an inferred Mac path.
The current export is the reported Mac snapshot, without the later isolated
dependency and privacy follow-ups. Keep its receipt tied to `6a87937`; any
combined follow-up build needs its own source/package identity. Preserve private
PIN entry, household data, approved media and a verified rollback package.
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
