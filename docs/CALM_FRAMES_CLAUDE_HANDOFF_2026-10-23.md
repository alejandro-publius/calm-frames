# Calm Frames: Claude Code handoff and remaining-work backlog

Prepared October 23, 2026, from the Mac checkout and recorded evidence. This is a continuation guide, not a new release certificate or blanket permission to publish. The product review was inspection only: no app changes, builds or simulator actions were performed. The user subsequently requested a private GitHub handoff. A separate documentation branch preserves the complete production ancestry; a separate harness branch preserves the test build. See the publication receipt alongside this document for actual remote verification and CI state.

## 1. What we are building and what matters now

Calm Frames is a native Fire TV/Vega application for deliberate, sustained viewing of prepared nature scenes. The viewer browses an original coastal world with Ocean and Forest, chooses a title, and explicitly starts watching. The flagship McWay Falls scene runs for approximately five continuous minutes at natural speed, then holds its final frame until Back. Older Acadia, Sea Otters and Forest titles have stationary defaults and separate short previews. Do not turn those previews into an automatically advancing reel.

The application is paired with a real offline analysis and preparation pipeline. It analyzes licensed source footage, prepares preset renditions, verifies actual output bytes, binds maps and reports to exact editions, and makes approved content available to the player. The player verifies its route and map, applies protective covers and guarded seeks, and refuses unresolved playback. PIN-protected household controls and separate profiles remain part of the product.

The user rejected earlier fast cuts and short scenes because they caused nausea. Sustained ambient viewing is the product goal; a still image is a useful fallback, not a substitute for every requested moving scene. Neither analyzer passes nor protective playback constitutes medical certification, a guarantee of comfort, or proof that every hazard was detected.

The user wants the project's engineering discipline to rival Tideline and Blackbox/DataHub: demonstrable correctness, recovery, integrity, evidence and a coherent experience. This does not mean adding services, agents, tests or architecture for their own sake. Preparation recovery and Playback Proof already exist. Improve the actual product and finish its release gates before inventing more scope.

## 2. Canonical state: verify before touching anything

Use these abbreviations throughout this document:

- `TASK=/Users/alexvintera/Documents/Codex/2026-10-20/task`
- `REPO=$TASK/calm-frames-combined-review`
- `ARTIFACTS=$TASK/mac-readiness-2026-10-21/release-validation-2026-10-22`
- `TOOLS=$TASK/design-tools-runtime-2026-10-23`

These are explanatory paths, not instructions to overwrite shell system variables.

| Item | Verified state at handoff |
|---|---|
| Canonical current checkout | `/Users/alexvintera/Documents/Codex/2026-10-20/task/calm-frames-combined-review` |
| Branch | `review/combined-validation-eff3ca4` |
| Clean evidence HEAD | `69eae5fb1553fdf315960a48d495952bfa2fd7d0` |
| Installed production source, according to latest native receipt | `bd55e470b895aa9e8b7ef8a843f0a742fce3611b` |
| App identity | `io.github.alejandropublius.calmframes`, launch component `.main`; aarch64 Debug Vega package |
| Current package | `$REPO/build/release/native-coastal-polish-20261023/calm-frames-0.1.0-aarch64-debug.vpkg` |
| Current package bytes / SHA-256, freshly rehashed | `132597849` / `4d229b6fd9c2a1ab61aa22eb996a673243da367db66035cb7f640bf70214e8a7` |
| Device package SHA-384 matched in native receipt | `d83f66440a782a481b027d4d6d052c9cef3fd0c9a73efef22cb07f21fd4f5889053b8890ad35a69e22d8d3aa4405977e` |
| Prepared namespace, freshly summed | 56 regular files, `129255687` bytes; limit `134217728` bytes (128 MiB); `4962041` bytes remaining |
| Package versus media budget | The VPKG size is not the namespace size. Do not substitute one budget calculation for the other. |
| Last recorded app state | Static Home, Kid active, Kid and Kid 2 retained. Not a fresh foreground observation during this documentation task. |

The Git status was clean when checked. HEAD includes evidence after the production source commit; do not claim the evidence-only HEAD was itself the compiled source. Re-read status before starting because the user or another session can change it.

### Rollbacks: preserve both

Nearest production rollback, rehashed this turn:

- `$REPO/build/release/native-onboarding-footer-20261023/calm-frames-0.1.0-aarch64-debug.vpkg`
- Source `4b04877f60101b33fc2e93e1e56413bcd165b051`
- 132,597,309 bytes; SHA-256 `2bfac62fe2bd992186dd5d948a18b47dc5392f5e003c1cc49280be2476963101`.

Original submitted-era fallback, rehashed this turn:

- `$ARTIFACTS/rollback/calm-frames-60c3bbb-aarch64-debug.vpkg`
- 132,557,605 bytes; SHA-256 `207898aa14d8659760348a716b825fabab83afd8e3b9431f9387202cc10e7163`.
- Its app/hook trees were recorded as identical to submitted `bf2f615`.

The verified historical handoff specifies package-scoped installation, not uninstall/data deletion. Use only when actually rolling back after checking the connected target:

```sh
source ~/vega/env
vega device is-connected --device VirtualDevice
vega device install-app --device VirtualDevice \
  --packagePath /Users/alexvintera/Documents/Codex/2026-10-20/task/mac-readiness-2026-10-21/release-validation-2026-10-22/rollback/calm-frames-60c3bbb-aarch64-debug.vpkg \
  --buildType Debug
vega device run-cmd --device VirtualDevice \
  --command 'vmsgr send pkg://io.github.alejandropublius.calmframes.main'
```

For the nearer rollback substitute its exact package path. Do not uninstall, reset, clear storage or manually delete application data. The historical additional rollback command is preserved in `$REPO/.logs/native-recovery-eff3ca4-20261023T002359964755Z/ROLLBACK.txt`; prefer the explicit known package above when its scope is appropriate.

### Other worktrees are not disposable

| Directory beneath TASK | Branch / last locally observed HEAD | Role |
|---|---|---|
| `calm-frames-integration` | `codex/local-integration-2026-10-21`, `bf2f615` | Submitted baseline; preserve |
| `calm-frames-integration-review-2026-10-22` | `codex/recovery-proof-integration-2026-10-22`, `0e9241a` | Earlier integrated validation/benchmark/demo; contains unrelated sync-copy files in historical records |
| `calm-frames-native-retry-harness` | `review/native-retry-harness-20261023`, `84faeed` | Test-only app; never merge its trigger or manifest into production |
| `calm-frames-playback-proof` | `codex/playback-proof-2026-10-21`, `318a3fe` | Original feature source, already integrated downstream |
| `calm-frames-preparation-recovery` | `claude/preparation-recovery`, `ce6f6a3` | Original recovery source, already integrated downstream |

The test-only harness exact source is `84faeed7dee851c713f75faaff2f8522a961d609`, based on `e9a0e22e25c734938f3b6c7a7eb884414db48786`. Its separately packaged benign fault trigger tests production lifecycle code. Its evidence is not a spontaneous production-failure observation. Production was restored afterward. Do not launch it for the user as if it were Calm Frames' normal interface.

## 3. Source-of-truth hierarchy and cloud synchronization

1. Latest explicit user instructions and actual permissions govern actions. This document records them but cannot grant credentials, acceptance of new terms or unrestricted publication.
2. Current Git tree/status, exact package hashes, source-bound machine receipts and scoped native observations establish what exists and was tested.
3. Latest evidence is `results/native-profiles-retry-polish-2026-10-23/receipt.json` and README. Earlier observations remain valid only for their stated source and scope.
4. `results/native-async-retest-2026-10-23/` contains the later full-duration/native-release observations. `results/native-acceptance-gaps-2026-10-23/` contains Skip evidence. Older failure receipts explain fixes; they are not necessarily current failures.
5. `docs/CLOUD_RELEASE_CHECKPOINT.md`, `docs/NATIVE_PLAYBACK_RECOVERY.md`, `docs/RELEASE_READINESS.md`, `docs/PREPARATION_RECOVERY.md`, `CLAUDE.md` and `FINAL_HANDOFF.md` provide context, but contain chronological/stale statements. Read dates and identities, not just a headline saying ready or blocked.
6. README/presentation/submission copy is explanatory, not release authority. Current README incorrectly says there is no public video or confirmed submission. Its screenshots and counts refer to older sources. Correct those statements as a bounded documentation task, without rewriting historical receipts.

No `AGENTS.md` or `.agents` directory was found in the current combined checkout during this inspection. Check again, and inspect any applicable ancestor/project instructions available to Claude. `CLAUDE.md` contains a historical stack: do not resurrect an older recording pause, missing-scene claim or obsolete installed SHA over later scoped approvals/evidence.

### Portable native continuation archive

- Local file: `$TASK/calm-frames-native-polish-69eae5f.zip`
- Library ID: `libfile_278617dfcdc48191ace2de1fa6256a11`, version 0 as recorded at creation.
- Rehashed size: `14770148` bytes.
- SHA-256: `691299745b49469ff6175b709a46fe8a24c7728e90d1c3b94cb8a489d9a2a162`.
- Contains cumulative production history from `eff3ca4fa88712f6426ccb8398b782f63ba422c2` through `69eae5f`, plus a separate test-only harness bundle. Read its instructions and verify prerequisites before import. Do not apply both a cumulative bundle and overlapping older patches.

Known cloud history: the older private branch `codex/cloud-release-candidate-2026-10-22` is recorded at `5771bdeae9c58c257b2e785f64f2fd06c08089ff`; the Mac remote-tracking ref still has that SHA. A live authenticated repository read and git ls-remote verified that older ref and that the repository is private; no existing remote branch was changed. The combined candidate `eff3ca4` added reviewed native recovery and decoder/cache integrity work on that release base. Subsequent Mac source/evidence through `69eae5f` is newer. The new handoff branch is `codex/claude-handoff-2026-10-23`, and the separate harness branch is `codex/native-retry-harness-2026-10-23`. Check `docs/handoff-2026-10-23/publication-receipt.json` for the verified pushed SHAs. GitHub availability does not prove Astra has fetched/imported the branch. Earlier Library transfers and messaging routes sometimes failed; an ID in a message is not proof of consumer-readable bytes.

Existing Astra task is `01a16276-925a-703d-998c-1039baf72012`, titled “Set up calm-frames.” Its original judging package is `9ad7bb7a2efd0a3b95f84fcefbeaca19d3eabcf2`. The cloud checkpoint records its byte-identical import as `a61c83c`. The Mac combined checkout already contains `docs/judging-package`; do not recreate that package or claim its older snapshot describes the latest UI. The combined release-check series supersedes old standalone `63122a1` and `32cf1f7`; do not cherry-pick them again.

Rejected browser redesign `76223f99cf8543ffe1e75d54c9873b56a0c23318` must stay excluded.

## 4. Implemented architecture and code map

All paths in this section are relative to REPO.

```text
Licensed source and attribution
  -> pipeline.local_library / ingest
  -> flashmap analysis + signed maps + preset render/scene holds
  -> byte-bound verification and crash-safe publication
  -> packaged/ambient export + compiled approved registry
  -> native catalog / route / signed-map verification
  -> explicit viewer choice and profile/edition checkpoint
  -> guarded player with opaque cover, seek confirmation, decoder ownership
  -> five-minute scene -> final still until Back

Recorded reports -> compiled Playback Proof -> read-only explanation UI
                  (never authority to play or remove a cover)
```

| Responsibility | Actual paths |
|---|---|
| Application/navigation and native playback | `app/src/App.tsx`, `app/src/screens/PlayerScreen.tsx`, `app/src/utils/VideoHandler.ts` |
| Home, title, profile and household UI | `app/src/calmframes/KidHomeScreen.tsx`, `TitleDetailsScreen.tsx`, `ProfilePicker.tsx`, `ParentAreaScreen.tsx`, `FirstRunScreen.tsx` |
| Coastal visual language and opening | `app/src/calmframes/calmStyles.ts`, `homeIslands.ts`, `CoastalAppearance.ts`, `PlayerOpening.tsx`, `TitleArtwork.tsx`, `AmbientScene.tsx` |
| Profile/settings persistence | `app/src/calmframes/profiles.ts`, `household.ts`, `householdStorage.ts` |
| Authenticated prepared catalog | `app/src/calmframes/packagedLibrary.ts`, `approvedPreparedCatalogs.ts`, `flashMap.ts`, `titleStatus.ts`, `bakedAmbient.ts` |
| Scheduled coverage and guarded transport | `app/src/calmframes/useFlashGuard.ts`, `coverSchedule.ts`, `seekSafety.ts`, `SafeMediaControlHandler.ts`, `mediaClock.ts` |
| Recovery and saved-position binding | `app/src/calmframes/playbackRecovery.ts`, `playbackCheckpoint.ts`, `playbackCheckpointStorage.ts`, `usePlaybackPresentation.ts`; player/VideoHandler own decoder lifecycle |
| Explainable evidence | `app/src/calmframes/PlaybackProofPanel.tsx`, `playbackProof.ts`, `approvedPlaybackProof.ts`; generator/check `app/tools/playback_proof.mjs`; offline `pipeline/evidence_summary.py` |
| Exact continuous-scene ending | `app/src/calmframes/continuousScene.ts`, player, `AmbientScene.tsx`, `app/assets/image/tv/mcway-final-frame.png` |
| Analyzer and preparation | `flashmap/`, `pipeline/ingest.py`, `render.py`, `verify.py`, `sceneholds.py`, `flashmap_adapter.py`, `hashing.py` |
| Recovery/integrity and publication | `pipeline/state.py`, `durable.py`, `catalog.py`, `local_library.py`, `packaged_library.py`, `ambient.py`, `ambient_export.py` |
| Local import/delivery, not the main product UI | `pipeline/local_intake.py`, `upload_server.py`, `package_delivery.py`, `edition_delivery.py` |
| Build/release contracts | `app/tools/check_native_inputs.mjs`, `check_prepared_library.mjs`, `approved_baked_ambient.mjs`, `scripts/release.sh`, `.github/workflows/ci.yml` |
| Guard hook mirror and evaluation | `hook/`, `eval/preparation_recovery.py`, `eval/preparation_benchmark.py`, `eval/mutate_gate.py`, `eval/check_video.py`, `eval/readme_sync.py` |

The app uses Vega's media implementation, not a browser video element for final native acceptance. It does not intercept Prime Video or arbitrary streams. Local preparation pages are developer/caregiver utilities, not a replacement for the native product.

### Important implemented invariants

- Cached preparation outputs are byte-checked, including HLS artifacts. Downstream identities depend on output hashes. Records are invalidated before work, and state/catalog/receipts use durable replacement. Per-title locking prevents concurrent ingest. Damaged cached output is withdrawn before reuse and cannot be published as ready.
- A verification verdict and ready receipt bind the exact checked bytes, including scene holds. Approved media must not be regenerated just to exercise recovery: legacy ledgers can trigger full re-preparation and new map timestamps/signatures.
- Playback Proof is explanatory only. Missing, malformed, substituted or mismatched records must not display a success result and cannot authorize playback.
- Checkpoints bind profile and exact edition; they do not restore weaker protection settings. The current household configuration and verified route remain authoritative. No player should prebuffer while the user is choosing Resume versus Start over.
- Recovery waits for opaque-view readiness, a guarded seek, settled `seeked` and fresh `timeupdate` at the target. React layout acknowledgment is not proof that a compositor frame was presented.
- Teardown completion is an ownership barrier. Timeout or delayed release does not permit another decoder. Late/stale callbacks must not revive canceled playback. Back/background/ending all retain this barrier. Do not merely increase a timeout or remove a cover to make a demo pass.
- Completion clears the checkpoint and presents the exact final still; there is no auto-repeat or auto-exit.

McWay identity is explicitly in `continuousScene.ts`: source SHA-256 `c9d5d21786c1beaf075dbc05373cf74184050a5f9b52765d5ef25d2a9cc65cb2`, rendition `795927874818f98c03cff64b6cd1b1e60db4544f7ddd0962f0d1d6340f39ebf2`, 8,991 frames at 30000/1001 fps, duration 299999.7 ms. Do not generalize its final-frame rule to unrelated routes.

## 5. Completed work: do not redo it as a new feature

| Completed work | Evidence and limits |
|---|---|
| Approved long ambient McWay edition; 128 MiB budget | Prepared namespace/provenance checks pass. Existing maps/signers/media unchanged by recent native fixes. Actual namespace sum rechecked for this handoff. |
| Preparation crash recovery and cache integrity | `docs/PREPARATION_RECOVERY.md`, `results/preparation-recovery-2026-10-22/`, benchmark receipts. Historical integrated validation: 16/16 scenarios and 24/24 guard mutations. Not a physical power-loss test. |
| Owned-clip benchmark | `results/preparation-benchmark-2026-10-22/benchmark.json`: 34/34 recorded checks; three samples, one Mac/owned clip; median cold 93.21 s, warm 0.46 s, restart 62.07 s. Not general throughput or new measurements of the latest source. |
| Playback Proof UI | Integrated; remote reading stops fixed at `d96c088`. Current `playbackProof.ts` validates compiled record digest and exact route/report/preset identity. Do not implement it twice. |
| Build/receipt failure reporting | Combined release-check commits are already imported. Locked dependency-install failure and evidence-write failure cannot be reported as success. |
| Native transport and teardown fixes | `f237a73`, `cfa6610`, `beb7ee0`, `e0f2ee7`, `3bc658f`: current paused-state use, Retry focus/OK ownership, awaited native deinitialization across exits, stable decoder ownership and paused presentation reconciliation. |
| Full five-minute native run | `results/native-async-retest-2026-10-23/receipt.json`, source `3bc658f`: natural-speed completion, no slow event in that run, final hold observed about 39.6 s after end, explicit Back, next Watch fresh. Slowness did not recur, but changed host load prevents a single-cause guarantee. |
| Resume/Back/background observations | Same receipt: paused recovered state, first explicit Play, Back release about 0.236 s, background release about 0.323 s. App audio signal measured; no human listening claimed. |
| Approved preview Skip | `results/native-acceptance-gaps-2026-10-23/`: requested cover before seek write, seeking/seeked reported covered, uncovered after confirmation outside interval. Sampled pictures do not prove atomic compositor ordering. |
| Onboarding viewport correction | `4b04877`, `FirstRunScreen.tsx`, `firstRun.test.tsx`: scrollable body and nonshrinking footer; redundant selection copy removed. Structural tests/build passed. First-run native footer was not revisited after setup because user data was preserved. |
| Second profile and isolated history | Latest receipt: Kid saved McWay at 0:57; Kid 2 had no inherited Resume and saved 0:24; Kid still offered 0:57 after switching back. Profiles/PIN retained. No deliberately different protection setting was created. |
| Native benign explicit Retry | Separate harness `84faeed`: covered failure and Try again reached; first Try again returned to ready error, second reached recovery and native clock 2:03-2:10; later Play resumed at 2:15. Back left playback; final six seconds of retained Back recording measured silence. Capture gaps and no useful app-scoped callback logs prevent exhaustive ordering proof. |
| Final coastal polish | `bd55e47`: active profile radio receives focus, choice closes picker and restores header focus; duplicate watching/settings/selected sentences removed; McWay synopsis shortened. Native chooser/Details/Back observed. |

### Test results must keep their source identity

- Latest polish: **94 focused Jest tests**, TypeScript, scoped ESLint (zero errors/warnings), native build pass. Latest receipt is authoritative for this scope.
- `3bc658f` native-retake source: **1,796 passed / four skipped**, 171 suites, 57 snapshots; TypeScript/scoped lint pass.
- Older `d96c088` integrated validation: Python **2,049 passed, zero skipped**, two slow tests deselected, coverage **90.46%** against unchanged 90% floor. CI-equivalent optional-dependency environment: **1,987 passed / six AWS-related skips**, same coverage. App **1,729 passed / four skipped**. These are historical evidence, not fresh full-suite results for `bd55e47`.
- Harness focused tests/build are separate; do not add their count to production totals or imply full production coverage from the harness.
- Hosted CI on the final local source is not established. Do not count local execution as a hosted green check.

### Remaining native evidence limitations

The latest requested 40-second recording contains only 14.573333 seconds; another requested 30-second recording contains 22.404626 seconds. A still capture was entirely black. Package-filtered diagnostics yielded no useful callback events in that pass, and broad device logs were not substituted. Earlier paused capture had only three video frames despite longer audio. These are instrumentation limitations, not evidence that a hidden unsafe frame was or was not shown.

McWay has no caption track: caption restoration is non-applicable to that title. Do not introduce unapproved captioned/hazardous content merely to tick a test box. Physical Fire TV and full VoiceView acceptance remain unclaimed. The finite release decision must explicitly address the remaining cover/release evidence gap, not keep repeating inconclusive captures indefinitely.

## 6. Non-negotiable design direction

Native Fire TV only. Preserve the original coastal, museum-like calm identity, shared map geometry and restrained palette. The existing font provenance names Fraunces and Source Sans 3 in `app/assets/fonts/FONT_PROVENANCE.json`; `calmStyles.ts` exposes aliases `CalmDisplaySemibold`, `CalmSansRegular`, `CalmSansSemibold`. Preserve the established font assets/aliases and their licenses.

User's exact direction:

> Cut taglines, helper text and secondary labels. If a screen needs them to make sense, fix the layout.

> Make the best decision that will elevate all three: the user experience (UX), developer experience (DX), and agent experience (AX) always, without breaking anything.

AX here means agent experience; accessibility is independently required, not renamed away. Preserve essential errors, safety disclosures, consent, accessible names, selected state and concise playback state. Do not remove a useful state label because all text is supposedly bad.

Use ten-foot readability, obvious D-pad focus, predictable focus return, visible footer controls, clear primary actions and calm loading/empty/error states. No rapid cuts, aggressive zoom, flashing, unnecessary animation or loading sounds. Respect reduced motion. Do not import a SaaS dashboard, generative landing-page aesthetic, browser UI or decorative complexity. Do not apply every installed design skill simultaneously.

## 7. Installed skills and actual runtime status

Local Codex skill root: `/Users/alexvintera/.codex/skills/`. Discovery in Codex does **not** prove discovery in Claude Code or availability in any cloud executor. Claude should inspect its own supported skill inventory and use a verified readable skill only through its allowed workflow. Do not restore Trash, reinstall duplicates, invent connectors or invoke code merely because a SKILL.md mentions it.

| Skill(s), directory under that root | Source/revision and adaptation | Actual status |
|---|---|---|
| `accessibility-review`, `design-critique`, `design-system`, `design-handoff`, `ux-copy`, `user-research`, `research-synthesis` | `https://github.com/anthropics/knowledge-work-plugins`, `design/skills/<name>`. Initial install did not retain a full source revision; do not invent one. Exact local skill hashes are in the native evidence `skills-inventory.json`. `../../CONNECTORS.md` references made local/self-contained; local notes describe the adapter. Do not assume connector runtime is installed. | Seven portable text skills present. Use critique, copy and accessibility selectively for native work. Verify upstream license for any redistribution; this handoff does not claim a missing license record. |
| `frontend-design` | `anthropics/claude-plugins-public`, `plugins/frontend-design/skills/frontend-design`; license file included. Original install revision not retained; exact local hash in inventory. | Installed text skill; avoid overriding the user's established visual direction. |
| `cowork-plugin-management` | Already in `/Users/alexvintera/.codex/plugins/cache/claude-cowork/cowork-plugin-management/0.2.2`; no duplicate install. | Cowork-specific runtime/output assumptions are not magically portable. |
| `design-taste-frontend` | `Leonxlnx/taste-skill` at `6010f91a9935f1c167dfc500fb1a475681892e6b`, subtree `skills/taste-skill`; MIT and local scope/provenance note. | Executable Node/browser scripts installed by specific approval. Exact approved lint smoke test passed exit 0, `{"files":1,"findings":[]}`. Browser inspector **not tested**. Node 22+ and Chrome requirements are present. No asset-generation/network scripts run. |
| `image-to-code` | Maintainer's moved repository `Leonxlnx/imagegen-skills` at `beb16b0d0f4dae9a6f5cb04ea41e97b93a54ab8e`; MIT; local scope note. | Text only; no script/hook. Website/image-generation workflow is not a mandate to redesign native Fire TV or generate unnecessary assets. |
| `awesome-design-md` | `VoltAgent/awesome-design-md` at `3b605329240ce735b510037cca322f1831fdd7f8`; MIT. 84 unchanged DESIGN.md references, local index and explicitly attributed original local wrapper. | Reference collection, not an upstream runtime plugin. |
| `playwright-cli` | Microsoft skill docs pinned `b1a5903c5b633b8c9f843ad7b629c2a78437040c`; Apache-2.0. Local adapter now points at separately installed runtime, preserving supported user-browser routes. | Official `@playwright/cli@0.1.22` actually installed and tested; see below. |
| `adhd` | `UditAkhourii/adhd` at `7b91ce601ed951c1a9658c63f6f9550d2486525b`; MIT; opt-in Codex tool-name adapter, source specification and license. | Text only; no `adhd-agent` CLI, no fan-out executed. Expensive ideation is inappropriate for a known bounded fix; invoke only when specifically requested. |
| `web-design-guidelines` | Original `vercel-labs/agent-skills` at `063bee94c3f4df8453406c830b0a7df0f2860278`; publisher README explicitly states MIT and installation instructions. Offline guideline reference pinned `434b7f91364665f2f733b310ec54809bf8f37937` from MIT `web-interface-guidelines`. Original wrapper retained with documented local Codex/offline adapter. | Installed; earlier licensing hold resolved. No scripts/dependencies. HTML/ARIA rules need native interpretation. |

Authoritative local installation records:

- `$TASK/design-skills-text-2026-10-23/installed-inventory.json` records the initial five-skill installation and file hashes; it predates the later Playwright runtime adapter and Vercel addition.
- `$TASK/design-skills-text-2026-10-23/web-design-guidelines-install.json` records the Vercel addition.
- `$TOOLS/operational-status.json` is the current three-tool operational receipt; `smoke/taste-lint-result.json` records the approved Taste retry.
- Each installed skill's `LOCAL_INSTALL.md`, where present, describes origin/adaptations. Initial frontend-design has no such local note; do not invent one.

### Tool runtime, isolation and permissions

Microsoft's official package is **`@playwright/cli`**, not deprecated `playwright-cli`. Installed executable:

`/Users/alexvintera/Documents/Codex/2026-10-20/task/design-tools-runtime-2026-10-23/node_modules/.bin/playwright-cli`

Version 0.1.22 depends on pinned `playwright` and `playwright-core` `1.64.0-alpha-1790635538000`. Exact official tarballs were checked against registry SHA-512 integrity and installed offline with lifecycle scripts disabled after an npm metadata fetch stalled. Package/lock/download receipts are in TOOLS. No app dependencies or global PATH were changed.

Smoke test used existing Node 26.0.0 and Chrome 155.0.8059.85, a new isolated headless browser, `chromiumSandbox: true`, loopback-only fixture, and no user profile. The fixture's button changed Ready to Confirmed. Before/after YAML snapshots are in `smoke/output/`; browser and server were closed. This is actual tooling operation, not native app evidence. No new browser was needed.

**Do not use Node 26 to build Calm Frames.** The app pins Node 22 in `.nvmrc`; Python is pinned 3.12 in `.python-version`; native build uses existing Vega SDK and JDK 21. Inspect the existing pinned runtime path from local build receipts/environment rather than installing another runtime or assuming the default shell Node is correct.

Taste's linter ran once after explicit permission resolved an earlier approval denial. That approval was for this synthetic fixture only, with no browser/network. Do not extrapolate permission to arbitrary third-party execution. The pinned browser launcher includes `--enable-unsafe-swiftshader`; browser inspector execution was not attempted or approved by the lint test. Do not weaken browser protections or route around the session's supported browser tools. If a concrete next test needs approval, name its exact command, input, output and access scope together.

## 8. Submission, public artifacts and account context

Baseline destinations from established project history:

- Devpost project: https://devpost.com/software/calm-frames
- Existing entry/draft identity: `1187358`.
- Current baseline public demo: https://www.youtube.com/watch?v=6lAP1FH16vc
- Existing private GitHub repository: https://github.com/alejandro-publius/calm-frames
- Submitted baseline `bf2f615`, branch `claude/ocean-layout-fix-2026-10-19`, remains protected.

These are baseline project records, not a fresh signed-in submission receipt. The public Devpost page could not be read through the web tool during this handoff; no authenticated status check or mutation was made. Do not turn stale repository statements into proof of non-submission, and do not assert a new submission occurred.

The official deadline page was rechecked October 23: **October 23, 2026, noon PDT = 19:00 UTC**. Recheck immediately on taking over; do not update frozen materials after the allowed window. Fire TV requires a working Fire OS/Vega demo and developer account/docs; the FAQ permits a simulator. AWS is an optional mini-challenge, not a reason to provision gratuitous infrastructure. The prior requirements review did not require Appstore publication; recheck current official wording before asserting more. Sources: [Official Rules](https://amazonappdev2026.devpost.com/rules), [FAQ](https://amazonappdev2026.devpost.com/details/faqs).

Account evidence is inconsistent across old documents: an old checklist says identity verified based on an owner statement; a later signed-in review reported an existing Amazon developer account with verification failed. Treat current verification status as unresolved until checked through the owner's supported session. SDK installation is not proof of account verification. Do not create accounts, change identity information, accept new terms or buy services to hide this gap. Existing AWS endpoint 403 is not proof of working cloud integration; infrastructure source alone does not establish mini-challenge eligibility.

The user already stated this is a **solo** build, significant learning, yes to AI career value, legal age, eligible jurisdiction, not an employee, and agreement to the rules in response to the concrete eligibility request. Do not ask those personal facts again without a new discrepancy. These statements are not blanket acceptance of unknown later agreements or authority for arbitrary external messages.

Judge-access history: six explicitly approved accounts were `devposttesting`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar`. Latest coordination reported five accepted, `knmeiss` pending; older local documents list different/pending names. **Recheck the current official list and actual invitations before acting**, without duplicate invitations or widening access. Prior approval disclosed personal-private-repo read/write collaborator access. Never claim all judges have access from an invitation alone. No access reads or changes were performed for this handoff.

### Existing replacement demo: available, but stale relative to new UI/lifecycle code

`$ARTIFACTS/calm-frames-replacement-demo.mp4`

- Rehashed: 49,643,080 bytes; SHA-256 `dde2ba357cf769c42eda519591aaf235e06fd487eb61f1d1d59548f4d703df92`.
- Recorded 169.21 seconds (2:49), under three minutes; contains 78 seconds of uncut native playback and a Playback Proof walkthrough.
- Source/demo evidence describes older `d96c088`, not the latest `bd55e47` recovery/profile/onboarding work.
- Sidecars: `calm-frames-replacement-demo.srt`, `calm-frames-replacement-demo-description.txt`, `calm-frames-replacement-demo-EDIT_NOTES.txt`, `calm-frames-replacement-demo.video_check.json` in the same directory.
- Audio listening clip: `$ARTIFACTS/native-review-2/audio-check-mcway-20s.mp4`.
- Palette/focus screenshots: `$ARTIFACTS/native-review-2/screens/`; newer production screenshots in `results/native-profiles-retry-polish-2026-10-23/`.

The older demo's video gate/full-decode/frame-matching checks are recorded; they do not establish human comfort or automatically cover a new edit. Keep the baseline public video unchanged until a verified replacement is approved for publication. Metadata must say what is actually shown; do not claim pause/resume, fault recovery or native acceptance that the footage does not demonstrate. Credits must include MoneySavingVideos/McWay CC BY 3.0 and the exact adaptation; supporting NPS/NOAA/Forest and font notices remain in `media/LICENSES.csv`, `NOTICE`, `app/LICENSE-THIRD-PARTY`, `app/assets/fonts/` and presentation credits. Do not relicense media as project code.

## 9. Bounded remaining-work backlog

This enumerates known work, not every imaginable feature. **Verified gap** means evidence or behavior is demonstrably missing; **proposal** means useful work to consider, not a newly discovered defect; **blocked** names a real dependency. P0 gates govern promoting the newer candidate, not a claim that the existing submitted fallback must be destroyed. Stop optional scope when it threatens a coherent deliverable before the deadline.

### P0 :  promotion/release gates

1. **Freeze and reconcile exact candidate identities.** Status: verified divergence. Purpose: stop cloud/local/source/package confusion. Location: section 2, native receipt, cloud checkpoint, cumulative ZIP. Dependencies: fetch the verified GitHub handoff branch, or use the consumer-readable archive and verified bundle prerequisites. Acceptance: isolated cloud/worktree import reaches the intended source/evidence identities, exact diff reviewed, no duplicate series, harness/rejected browser commit excluded. Risk/rollback: use new review refs, preserve all original refs and submitted branch. User-only: authenticated access may need user presence; do not claim consumer import from IDs alone. The current private handoff push is explicitly authorized; future promotion scope remains separate.

2. **Run a final source-scoped regression pass once, after intended changes are frozen.** Status: verified evidence gap for the latest production aggregate. Location: app package scripts, `.github/workflows/ci.yml`, current receipts. Dependencies: Node 22/Python 3.12/existing dependencies and no concurrent writer. Acceptance: applicable full app/type/lint/tool checks and Python/integrity checks pass or have explicit justified scope; record SHA, skips, warnings and commands. Reuse valid unchanged evidence, do not sum overlapping counts or rerun long benchmarks for vanity. Risk/rollback: no auto-fix broad churn; preserve failed logs and fix only actual regressions. User-only: none unless access/install boundary is encountered.

3. **Close hosted CI policy/access gap.** Status: blocked/unverified. Prior Astra report: `api.github.com` absent from cloud environment allowlist. Location: workflows and cloud task/environment UI. Dependencies: exact candidate publication scope and allowed network access. Acceptance: terminal CI/Audit results for the exact intended commit, or an explicit release decision retaining the gap. Risk/rollback: no alternate credential/dispatch route around a restriction, no network/security change without applicable action-time approval. User-only: may need the actual environment settings approval; identify the precise control, not a vague permission request.

4. **Close the native cover/decoder-ordering evidence gap.** Status: verified missing evidence, not proof of an exposed frame. Location: `useFlashGuard.ts`, `playbackRecovery.ts`, `VideoHandler.ts`, latest native receipt and separate harness. Dependencies: stable simulator ownership, benign approved fixture and reliable scoped capture/diagnostics. Acceptance: correlate cover presentation, seek request/confirmation, confirmed decoder release and new decoder creation; no stale frame/audio or automatic retry. If platform cannot expose sufficient ordering, record that precise limit and obtain a bounded release decision rather than fabricate success. Risk/rollback: never weaken cover/timeout/ownership rules, never use hazardous raw playback; restore exact production package after any separate harness. User-only: unlock or scoped capture permission only when actually required; no PIN capture.

5. **Owner listening, comfort and visual acceptance.** Status: pending human review. Purpose: address the user's actual nausea/pacing complaint. Location: installed app, 20-second audio clip, final hold, latest nonsecret screenshots and eventual revised demo. Dependencies: coherent candidate and calm playback. Acceptance: user explicitly reports audio level/quality, comfort/pacing and palette/focus acceptance or actionable objections. Technical signal measurement is not listening. Risk/rollback: stop uncomfortable motion promptly; stationary Home remains available. User-only: yes; one bundled short review, no repeated vague approval or forced hazardous viewing.

6. **Validate the final package and reproducible build identity.** Status: latest Debug package and namespace verified; final promoted-source package acceptance pending if source changes. Location: pre/postbuild gates, release script, source-bound package receipt. Dependencies: frozen source, Node 22, Vega/JDK 21. Acceptance: native inputs/provenance/approval registry/Playback Proof checks pass, actual package and prepared namespace under applicable limits, device hash matches package, rollback retained. Current namespace is already within limit; do not optimize/re-encode unnecessarily. Risk/rollback: preserve signed media and edition identity, no trust expansion; nearest verified package rollback. User-only: only new media/signing/access scope, not routine unchanged checks.

7. **Reconcile current documentation and engineering claims.** Status: verified stale copy. Location: README, CLAUDE chronology, `docs/RELEASE_READINESS.md`, presentation architecture, judging-package addendum, submission drafts. Dependencies: tasks 1-6 evidence. Acceptance: public baseline links, latest SHA, local versus hosted results, current implemented features and remaining limits agree; older receipts remain historical. Preserve judging package's older source identity rather than silently relabeling its visuals. Risk/rollback: documentation-only coherent commit, no live edits implied. User-only: none for local corrections; later publication has its own boundary.

8. **Prepare an accurate revised under-three-minute native demo.** Status: older replacement exists; showing latest work is a proposal dependent on final scope. Location: ARTIFACTS sidecars, `docs/submission/REPLACEMENT_DEMO_RUN_OF_SHOW.md`, video checker. Dependencies: validated installed build and owner audiovisual feedback. Acceptance: real app-only footage, sustained uncut ambient section, concise proof/recovery only if actually shown, calm edit, truthful time cuts, credits/captions, decode/gate receipt for exact final hash; no test-harness UI presented as production. Risk/rollback: preserve both existing final files and public baseline; no microphone/webcam/desktop/private screens. User-only: human listen/watch and any new capture/publication scope beyond retained approval.

9. **Verify deadline, entry/account and judge-access requirements.** Status: time-sensitive external facts partly unresolved. Location: official rules/FAQ, current Devpost entry, Amazon account and private repo access. Dependencies: signed-in supported routes and user availability if authentication requires it. Acceptance: current entry status/receipt, eligible Fire TV track, truthful account status, all required judge access actually effective, no invented AWS claim; exact deadline/editability confirmed. Risk/rollback: no account recreation, access widening, duplicate invites, paid services or editing frozen materials. User-only: identity/authentication issues and new attestations that cannot be inferred; prior solo/survey facts remain answered.

10. **Promote only the verified candidate with scoped authorization.** Status: private GitHub handoff publication is covered by the later explicit user request; replacement video/live submission promotion is not performed for the newest native candidate. Location: private GitHub branch, owner YouTube channel, existing Devpost entry. Dependencies: preceding gates and final publication scope. Acceptance: normal non-force push of reviewed SHA, matching CI links, playable authorized video if replaced, correct repo/setup/media links, and confirmed saved/submitted receipt as applicable. Preserve baseline `bf2f615` and `6lAP1FH16vc`. Risk/rollback: new branch/video first; no visibility changes, new accounts, undisclosed agreements, arbitrary communications or automatic replacement. User-only: exact unresolved action approvals and legal action-time boundaries, not re-asking already answered facts.

### P1 :  meaningful product, UX and technical uplift after the gates are bounded

11. **Observe onboarding footer without resetting the household.** Status: structural fix complete; native first-run view unobserved after final install. Location: `FirstRunScreen.tsx`, `firstRun.test.tsx`. Purpose: verify the clipped Next/Back complaint is actually resolved at supported TV sizes. Dependencies: a permitted isolated first-run fixture/profile flow, not deletion of current data. Acceptance: all steps and footer reachable by D-pad, no clipping, essential text legible. Risk/rollback: test-only entry separate from production, no PIN capture. User-only: private PIN step if encountered; no further reset is authorized.

12. **Check profile-dependent protection, distinct from position isolation.** Status: positions passed; deliberately different stricter preset not observed. Location: profiles/household, picker, route acceptance tests. Dependencies: owner-controlled protected setting change or approved isolated test data. Acceptance: current stricter floor wins after switching/recovery, no weaker persisted setting restored, profile histories stay isolated. Risk/rollback: preserve/default protections and restore any test setting via ordinary controls. User-only: enter PIN privately and approve any real household setting change; never ask for the PIN.

13. **Scope caption restoration accurately.** Status: non-applicable to McWay; unit coverage exists. Location: checkpoint/recovery code and tests. Purpose: avoid a misleading universal claim. Dependencies: an existing eligible captioned title or separately approved benign test fixture. Acceptance: restore by language/label, missing-track fallback, no old native-track-ID reliance; if unavailable, document narrower consumer support. Risk/rollback: no new shipped media or signed-map edits merely to test. User-only: only new fixture/edition authorization if needed.

14. **One native accessibility and remote-focus pass.** Status: partial evidence; VoiceView/full device audit unverified. Location: Home/Details/Parents/FirstRun/ProfilePicker/Playback Proof; installed critique/a11y/copy skills. Acceptance: ten-foot readability, contrast, focus not clipped/hidden, logical order, meaningful selected/disabled/error announcements, Back restores opener, reduced motion respected. Fix only observed or source-proven issues. Risk/rollback: small UI commits; preserve safety semantics and established typography. User-only: device availability/subjective readability; PIN screens stay private.

15. **Check loading, empty and failure-state consistency.** Status: bounded review proposal, not a claim these screens are broken. Location: opening/presentation/household loading and catalog error components. Acceptance: truthful state, clear retry/back action, no false percentages/artificial delays, no extra explanatory paragraphs, no rapid luminance changes. Risk/rollback: do not alter timing-critical cover logic for visual polish; unit state/focus tests plus relevant native observation. User-only: none unless new visual acceptance is needed.

16. **Evaluate the observed pale opening transition.** Status: historically observed, comfort consequence unassessed. Location: native Skip receipt and older demo edit notes, player opening/surface handoff. Acceptance: determine source of the brief light frame with benign evidence; if a real transition defect, correct actual surface/backdrop ordering and show it resolved without hiding it in an edit. Risk/rollback: no weakened cover or analyzer threshold. User-only: comfort feedback, not exposure to repeated uncomfortable trials.

17. **Validate legacy title routes without reintroducing a rushed reel.** Status: recent pass concentrated on McWay/Acadia; Sea Otters/Forest not comprehensively re-observed on latest source. Location: approved catalog, static scene/preview route and title controls. Acceptance: still defaults remain sustained, preview only explicit, Back/focus consistent, no auto-advance; existing titles preserved. Risk/rollback: unchanged prepared bytes; restore production package on regression. User-only: optional subjective review, not new content approval for unchanged titles.

18. **Create a bounded runtime performance baseline.** Status: improvement proposal prompted by historical slowdown; later run passed. Location: `mediaClock.ts`, VideoHandler, scoped timing receipts. Acceptance: fresh and resumed benign playback measured against wall clock under recorded host load; report dropped-frame API limitations, memory and teardown durations without claiming causation from correlation. Risk/rollback: no production debug flood/whole-device logs, no indefinite soak. User-only: stable unlocked Mac window; no new purchases.

19. **Address analyzer-version cache invalidation if still absent.** Status: documented limitation requiring current-code confirmation, not an assumed active defect. Location: `docs/PREPARATION_RECOVERY.md`, ingest/state/adapter fingerprints. Purpose: keep analysis evidence tied to analyzer implementation. Acceptance: changing the analyzer identity invalidates only appropriate cached stages in synthetic test workdirs, with deterministic regression and migration notes. Risk/rollback: can trigger new maps/signatures; never run against approved media workdirs without explicit approval. User-only: separate authorization before any real approved-edition re-preparation.

20. **Make crash-recovery evidence easier to reproduce.** Status: proposal; core recovery already implemented. Location: recovery/benchmark runner, local-library docs. Acceptance: one documented bounded command with prerequisites, output ownership, failure semantics and known limitations; reuse existing 16-scenario/mutation coverage rather than duplicate it. Risk/rollback: synthetic fixtures/test keys only, no production signer access or destructive process matching. User-only: none for existing isolated tests; do not generate or rotate production credentials.

21. **Improve caregiver onboarding/recovery design without bypassing PIN.** Status: known UX gap: forgotten PIN has no verified supported non-destructive recovery in prior review. Purpose: make recovery understandable without silently weakening parental protection. Location: first-run/household/PIN documentation and source. Acceptance: first confirm current supported behavior; propose owner-controlled recovery with explicit data-loss/security semantics before implementation. Risk/rollback: high enough to separate from release polish; no backdoor, guessing, stored-secret reads or undocumented clear-data shortcut. User-only: design/security decision before credential-changing behavior.

22. **Physical target coverage.** Status: unverified, not a hackathon hardware requirement. Purpose: distinguish simulator success from real-device behavior. Location: native acceptance matrix/release docs. Dependencies: available supported Fire TV/Vega hardware and authorization. Acceptance: exact device/OS/package matrix with focus, audio, cover/recovery and ending evidence; do not claim Android/Fire OS support from Vega tests. Risk/rollback: package-scoped install with preserved data/rollback; no procurement or security changes implied. User-only: device access if available; otherwise clearly defer.

23. **Finish a clean reviewer and agent entrypoint.** Status: proposal with verified stale entrypoint text. Location: README, CLAUDE.md, docs/judging-package addendum, architecture sources, exact commands. Acceptance: a new human/agent can identify canonical branch, build prerequisites, data boundaries, verified evidence and next task without rereading chat; no contradictory mutable counts or cloud-local path assumptions. Risk/rollback: documentation-only, preserve historical receipts and package ownership. User-only: none for local work.

24. **Keep proof visible without drowning the viewer in it.** Status: design-review proposal; Playback Proof already implemented. Location: `PlaybackProofPanel.tsx`, `TitleDetailsScreen.tsx`, evidence schema. Acceptance: Watch remains primary, technical evidence stays secondary/reachable, unknown values never appear successful, focus/Back retain context. Risk/rollback: never let explanatory UI affect trust gates; no extra helper paragraphs. User-only: optional review of the resulting hierarchy.

### P2 :  optional after release; not prerequisites for finishing

25. **Expand the sustained ambient catalog.** Proposal. Use licensed, provenance-tracked fixed-camera scenes with suitable long uninterrupted spans, natural speed and deliberate ending; no visible loop seams. Location: media ledger and standard preparation/export path. Dependencies: exact source/edition approval, budget and both actual-output analyzers. Acceptance: approved reproducible bytes/audio/timing/credits and comfortable owner review. Risk/rollback: stage separately, retain all approved titles. User-only: new media/signing/budget approval where needed.

26. **Broaden recovery stress testing only for a demonstrated risk.** Proposal. Location: existing mutation/property/interrupt suites. Acceptance: a concrete uncovered fault scenario is reproduced and its regression catches the broken guard. Risk/rollback: isolated synthetic dirs/process groups, no power cuts to the user's Mac or shared storage tests without permission. User-only: only hardware/filesystem experiments outside normal scope.

27. **Optional cloud/AWS delivery.** Proposal, not required to prove this native product. Location: `pipeline/infra/` and local delivery abstractions. Dependencies: a real user need, security/cost plan and explicit provisioning approval. Acceptance: documented working integration and bounded costs, no checkbox-only claim from a 403 or source files. Risk/rollback: no resources/accounts/credentials now. User-only: yes for provisioning/cost/access.

28. **Public SDK/open-source contribution packaging.** Proposal. Location: hook/analyzer package docs and license inventory. Acceptance: real separable contribution with reproducible consumer setup, accurate license/attribution and maintenance scope. Risk/rollback: private repo stays private unless separately approved; don't expose approved/private artifacts accidentally. User-only: exact public destination/access authorization.

29. **Broader research and sensory preferences.** Proposal. Use existing user-research/research-synthesis skills only with an actual study brief. Acceptance: informed, respectful feedback with clear limits and actionable results; no medical efficacy claims or fabricated participants. Risk/rollback: no unsolicited recruitment/messages or collection of sensitive health data. User-only: study/communications/privacy authorization.

30. **Extended design exploration.** Proposal only after functional closure. Use design-system/awesome-design-md/ADHD selectively; no blanket application of web taste rules to TV. Acceptance: measurable improvement in navigation/readability or maintenance, preserving the original identity. Risk/rollback: separate experimental worktree; no replacement before user review and validation. User-only: explicit invocation for expensive ADHD exploration or major visual-direction change.

## 10. Operating rules for Claude

- Start read-only: current branch/HEAD/status, worktree inventory, latest receipt, package hashes, active owned jobs and applicable instructions. Do not print environment secrets or scan denied session/private files.
- Preserve the existing PIN, Kid and Kid 2, settings/history and all unrelated sync-copy files. The prior disposable-data reset was explicitly approved and completed; it is not standing reset permission. The user set a new PIN privately. Never ask them to tell you it, inspect stored secrets, brute force, bypass the gate or capture its entry.
- Ordinary source/shell engineering is separate from computer-use. Computer-use access to `com.apple.Terminal` and `com.openai.codex` was explicitly denied; do not work around those denials through alternate UI automation. Respect your own session's supported tool policies.
- Prior approved capture scope is only the Calm Frames simulator window, app audio and app-specific diagnostics. No microphone, webcam, desktop, unrelated windows/logs or PIN screen. Pause immediately for private input; do not treat a generic keep-going as permission to capture secrets.
- Verify current simulator/session ownership. Old session IDs are historical and may be dead; do not blindly poll/restart/reinstall. A retained foreground SDK launch session previously helped avoid emulator exits. No ongoing capture/test was started for this documentation task.
- Keep one owner per worktree. Inspect concurrent work before editing; use a separate worktree for experiments. Do not contact or launch another Claude/Codex worker unless the user asks/authorizes coordination. No duplicate long suites or conflicting simulator navigation.
- No destructive Git reset/clean, force pushes, branch replacement, removal of sync copies, wholesale rewrite, secret exports, new credentials, signer expansion or unreviewed media activation.
- Preserve build gates, source/audio/timing identity and signed maps. Test failure is a problem to explain/fix, not suppress. Do not regenerate approved workdirs just to refresh old ledgers or satisfy a count.
- Keep commits small and coherent: source fix, focused evidence, then documentation tied to exact SHA. Do not commit raw private logs, PIN content, credentials, helper caches, new runtime node_modules or large external videos by accident.
- Finish the core experience. Do not expand scope while a genuine P0 blocker is recoverable. When blocked, state exact action/target/reason, what completed, and whether denied/pending/uncertain; continue independent work. Check uncertain outcomes before retry and never bypass a denial.

## 11. Minimal first-session plan

1. Read this handoff, current `CLAUDE.md`/cloud checkpoint and latest native receipt. Confirm clean `69eae5f` or explain every newer change. Inspect your own skill discovery; do not reinstall this inventory blindly.
2. Confirm deadline/editability and select a finite release scope. Preserve baseline/public artifacts. State the genuine remaining P0 gates once, with source/evidence identities.
3. Compare actual test coverage to the final diff. Run only necessary focused checks first; reserve one aggregate source pass for the frozen candidate. Do not rebuild unchanged app inputs just to show activity.
4. Choose the highest-impact available task: trustworthy native ordering evidence if the platform can provide it, otherwise current-source documentation/claim reconciliation and cloud transfer. Use benign fixtures and maintain the decoder/cover invariants.
5. Bundle the short owner actions: listen/watch/palette feedback; any required account/auth/network approval; publication decision for exact commit/video/entry when concrete. Do not re-ask solo/learning/eligibility facts already answered.
6. Produce a coherent checkpoint with source SHA, exact package/media/video hashes, tests actually run, native observations, limitations, rollback and next action. Stop optional work before it threatens the deliverable.

### Definition of done

A specified native Fire TV candidate provides deliberate long ambient viewing, usable pause/resume/Back and ending behavior, authenticated prepared content, fail-closed recovery and understandable household controls. Required source/package/native checks have source-bound evidence; unresolved platform and human-review limits are explicit and accepted through the appropriate decision. Documentation/demo/reviewer setup describe that same candidate. If publication is requested and authorized, remote SHA, hosted results, public playable video and actual saved/submitted receipt are verified: not merely planned. Submitted fallback and rollback remain available. Tool/plugin installation alone never establishes product readiness.

### User-only actions still potentially needed

- Listen and watch once for comfort/audio/palette; no tool can infer this from signal measurements or blanket approval.
- Unlock the Mac or enter the existing PIN privately if the ordinary protected flow requires it. No new PIN/reset is needed merely to continue development.
- Resolve any current Amazon identity/account issue through the owner account; confirm current judge access if a supported route requires authentication.
- Approve a precise environment network control, new agreement, new media/signing action or publication destination only when outside retained authorization.
- Taste browser inspection is not covered by the completed synthetic lint approval; request its concrete bounded scope only if actually needed. It is not necessary for native acceptance.

## 12. Short prompt to paste into Claude Code

> Read `/Users/alexvintera/Documents/Codex/2026-10-20/task/CALM_FRAMES_CLAUDE_HANDOFF_2026-10-23.md` completely, then inspect the current checkout and latest receipts before editing. Continue Calm Frames from the verified native candidate, preserving the submitted fallback, PIN/profiles, approved media and original coastal Fire TV design. Use the installed design skills selectively through your supported tools; do not reinstall them or mistake browser checks for native evidence. Start with a concise factual checkpoint and the highest-impact remaining P0 task you can safely complete. Do not expand scope, reset data, bypass denied access, publish, or contact other agents from this handoff alone. Keep exact source/test/artifact identities and leave a resumable checkpoint. Ask only for concrete user-only decisions that are still required.


## 13. Private GitHub continuation entrypoint

The user explicitly requested all relevant project work pushed to the existing private repository. The new branch preserves production source/evidence through `69eae5f` and adds documentation only. Original worktrees, submitted branch and installed app remain untouched.

- Handoff branch: https://github.com/alejandro-publius/calm-frames/tree/codex/claude-handoff-2026-10-23
- Start here: https://github.com/alejandro-publius/calm-frames/blob/codex/claude-handoff-2026-10-23/docs/CALM_FRAMES_CLAUDE_HANDOFF_2026-10-23.md
- Separate test harness: https://github.com/alejandro-publius/calm-frames/tree/codex/native-retry-harness-2026-10-23
- Reviewed inclusion/exclusion ledger and source-branch accounting: `docs/handoff-2026-10-23/artifact-manifest.json`.
- Tool origins/file hashes: `docs/handoff-2026-10-23/skill-installation-inventory.json`, `web-guidelines-installation.json` and `tool-runtime-status.json`; no third-party tool trees are vendored.
- Remote verification and CI receipt: `docs/handoff-2026-10-23/publication-receipt.json`. Do not infer CI success from dispatch acceptance.

For cloud Claude: fetch the handoff branch into a new worktree after preserving current edits, read the start-here document and receipt, then reconcile source-bound evidence. GitHub includes source, approved already-tracked media, scoped committed screenshots and receipts. Packages, large raw recordings and local tooling remain outside Git by design; the manifest says exactly where they live. Do not call those artifacts uploaded to GitHub.

### Verified private publication checkpoint

The atomic private push succeeded. An independent `git ls-remote` check matched production handoff payload `3a240927e54c3f4b443853ffa6a4bed896839bb4`, harness `84faeed7dee851c713f75faaff2f8522a961d609`, and the preserved historical Playback Proof branch `318a3fe8dcba07474d08af0609cb1168e1b37f41` at `codex/playback-proof-archive-2026-10-23`. The submitted branch remains `bf2f615e6fad0d73442fe2b9acab3067bf311e7e`. This publication receipt is a documentation-only descendant of that payload; use the branch tip for the final documentation. No product code was changed. CI is a distinct pending check, not implied by the push. Cloud agents must still fetch and verify the branch themselves.

CI was successfully dispatched from this Mac for documentation head `a4651a6062aa0662fab4559a86201620962b27bd`: https://github.com/alejandro-publius/calm-frames/actions/runs/39910572282 . Its secret scan passed. The first documentation style check found 11 punctuation/wording violations introduced by this handoff; those are corrected in the subsequent documentation-only commit and the exact local style checker passes. A new CI run for the corrected head is separate and must reach a terminal state before claiming CI acceptance. This does not resolve any separate cloud-executor allowlist policy.
