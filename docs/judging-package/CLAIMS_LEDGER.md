# Claims ledger

Every important claim is scoped to a source, build or observation. Counts below are imported release evidence, not new benchmarks or cloud reruns. This ledger does not upgrade historical evidence into current deployment or clinical claims. The full original release JSON is identified by its source SHA-256 in the [selected fields](evidence/release-selected.json). [Machine-readable ledger](claims.json).

## C01. Approved product wording and scope

**Statement:** Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device.

**Version:** `d96c088`.

**Evidence:** [GUIDE.md](GUIDE.md); [ARCHITECTURE.md](ARCHITECTURE.md); [evidence/spec-sources.md](evidence/spec-sources.md).

**Boundary:** Threshold-based technical aim, not proof of medical safety or personal comfort.

## C02. Submitted baseline preserved

**Statement:** Submitted candidate bf2f615; native source 60c3bbb has identical app and hook trees.

**Version:** `bf2f615 / 60c3bbb`.

**Evidence:** [evidence/release-selected.json](evidence/release-selected.json): bases.submitted_candidate, native.fallback_source.

**Boundary:** Tree equality checked with Git in this task; no submitted artifact or live submission was changed.

## C03. Upgrade identity

**Statement:** Validated source d96c088; integration evidence commit 13551e45bd853c392489dbecce7158a04036f615.

**Version:** `d96c088 / 13551e4`.

**Evidence:** [evidence/release-selected.json](evidence/release-selected.json): tested_commit, evidence_commit, bases.

**Boundary:** A historical local validation receipt, not hosted CI success or a new cloud run.

## C04. Python results

**Statement:** <!--n results/release-validation-2026-10-22/validation.json:python.full.passed -->2049<!--/n--> passed, <!--n results/release-validation-2026-10-22/validation.json:python.full.failed -->0<!--/n--> failed, <!--n results/release-validation-2026-10-22/validation.json:python.full.skipped -->0<!--/n--> skipped, <!--n results/release-validation-2026-10-22/validation.json:python.full.deselected_slow -->2<!--/n--> slow tests deselected.

**Version:** `d96c088`.

**Evidence:** [evidence/release-selected.json](evidence/release-selected.json): python.full.

**Boundary:** Recorded full local run with optional test dependencies installed. Other configurations must retain their different counts.

## C05. App results

**Statement:** <!--n results/release-validation-2026-10-22/validation.json:app.jest.tests_passed -->1729<!--/n--> passed, <!--n results/release-validation-2026-10-22/validation.json:app.jest.tests_skipped -->4<!--/n--> skipped, <!--n results/release-validation-2026-10-22/validation.json:app.jest.tests_failed -->0<!--/n--> failed.

**Version:** `d96c088`.

**Evidence:** [evidence/release-selected.json](evidence/release-selected.json): app.jest.

**Boundary:** Recorded Jest results; not a native, audio, clinical or usability outcome.

## C06. Recovery scenarios and guard mutations

**Statement:** <!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.passed -->16<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.scenarios -->16<!--/n--> scenarios passed; <!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.killed -->24<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.mutations -->24<!--/n--> recovery guard mutations killed.

**Version:** `d96c088`.

**Evidence:** [evidence/release-selected.json](evidence/release-selected.json): recovery.scenarios, recovery.guard_mutations; [evidence/preparation-recovery.md](evidence/preparation-recovery.md).

**Boundary:** One Mac/APFS, mostly fake analyzer, one real-analyzer scenario; no power cut. Not a detector-accuracy or performance benchmark.

## C07. General mutation gate

**Statement:** <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.totals.killed -->68<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.totals.mutations -->70<!--/n--> mutations killed; two documented equivalent survivors.

**Version:** `d96c088`.

**Evidence:** [evidence/release-selected.json](evidence/release-selected.json): mutation_gate.totals; [evidence/release-readiness.md](evidence/release-readiness.md).

**Boundary:** Do not say all 70 were killed. Recovery mutations are a separate set.

## C08. Native images are authentic

**Statement:** Home/Details/ending depict 60c3bbb; four integration crops depict d96c088.

**Version:** `60c3bbb / d96c088`.

**Evidence:** [assets.json](assets.json); [evidence/release-selected.json](evidence/release-selected.json): native.committed_crops; [evidence/capture-history.md](evidence/capture-history.md).

**Boundary:** Reused unchanged, no new native capture. Architecture is documentation. validation/*.png are web-guide renders.

## C09. Playback evidence boundary

**Statement:** The included McWay playback still came from a shorter separate run; the full-duration observation used trace lines.

**Version:** `d96c088`.

**Evidence:** [evidence/release-readiness.md](evidence/release-readiness.md): On the Vega Virtual Device / Not established.

**Boundary:** The Mac was locked during the full run; audio was not listened to; no picture-timing or full-duration video proof follows from the still.

## C10. Proof-page semantics

**Statement:** Source, Prepared and Selection separate measurements, output checks and selected identity.

**Version:** `d96c088`.

**Evidence:** [evidence/code-excerpts.md](evidence/code-excerpts.md): PlaybackProofPanel.tsx; [assets/f04-proof-selection.png](assets/f04-proof-selection.png).

**Boundary:** Read-only explanation, not runtime rescanning or authority to trust a new title.

## C11. Build-time versus runtime identity

**Statement:** Media bytes are checked at build time; selection binds to expected route/map identities.

**Version:** `d96c088`.

**Evidence:** [ARCHITECTURE.md](ARCHITECTURE.md); [evidence/code-excerpts.md](evidence/code-excerpts.md): packagedLibrary.ts; [assets/f04-proof-selection.png](assets/f04-proof-selection.png).

**Boundary:** Do not imply the info page rehashes or reanalyzes all playback bytes.

## C12. Missing analyzer version

**Statement:** McWay report lacks its output analyzer version and the UI says so.

**Version:** `d96c088`.

**Evidence:** [assets/f12-mcway-proof-prepared.png](assets/f12-mcway-proof-prepared.png); [evidence/release-readiness.md](evidence/release-readiness.md).

**Boundary:** Do not infer a version from another report. No flagged output segments does not demonstrate an activated protective cover.

## C13. Remote reading improvement

**Statement:** Reading sections are focus stops and the validation records reaching the analysis record and returning with Back.

**Version:** `d96c088`.

**Evidence:** [evidence/code-excerpts.md](evidence/code-excerpts.md): ReadingStop.tsx; [assets/f07-reading-wcag.png](assets/f07-reading-wcag.png); [evidence/release-readiness.md](evidence/release-readiness.md).

**Boundary:** No full VoiceView or physical Fire TV acceptance is established. Total key counts include an earlier build, so this package does not promote them as final-build counts.

## C14. Need and intended impact

**Statement:** Published flashing guidance and photosensitivity context motivate an inspectable prepared-library workflow.

**Version:** `Primary-source context`.

**Evidence:** [PRIMARY_SOURCES.md](PRIMARY_SOURCES.md): P2/P3; [evidence/spec-sources.md](evidence/spec-sources.md); [evidence/outreach-status.md](evidence/outreach-status.md).

**Boundary:** No fresh source-page verification, interviews, adoption, market sizing, medical outcome or comfort measurement.

## C15. Differentiation

**Statement:** This implementation combines preparation, exact-edition checks, guarded playback and a readable proof record.

**Version:** `d96c088`.

**Evidence:** [ARCHITECTURE.md](ARCHITECTURE.md); [evidence/code-excerpts.md](evidence/code-excerpts.md).

**Boundary:** Describes this project, not a first/only claim or assertion about competitor limitations.

## C16. Official criteria

**Statement:** Recorded criteria: Tech Implementation, Design, Potential Impact, Quality of the Idea.

**Version:** `Dated official-rules record`.

**Evidence:** [RUBRIC_MATRIX.md](RUBRIC_MATRIX.md); [evidence/recorded-rules.md](evidence/recorded-rules.md); [evidence/source-access.json](evidence/source-access.json).

**Boundary:** Live Devpost fetch blocked. Current wording/weights/eligibility unverified; no score or bonus guaranteed.

## C17. SDK friction

**Statement:** F1-F6 summarize historical package-URI, image-source, frame-statistic, CLI, focus and staging observations.

**Version:** `Recorded issue checkpoints; fixes 52138fe / ac5a610 where stated`.

**Evidence:** [FRICTION_LOG_DRAFT.md](FRICTION_LOG_DRAFT.md); [evidence/friction-records.md](evidence/friction-records.md).

**Boundary:** No new repro or current SDK resolution claim. Mac lock state, ScreenCaptureKit, browser policy and unrelated runner issues are excluded from Amazon defect attribution.

## C18. Unavailable work

**Statement:** Claude newer benchmarks and the replacement video are not part of this evidence snapshot.

**Version:** `Package scope`.

**Evidence:** [HANDOFF.md](HANDOFF.md); [DEMO_EVIDENCE_BRIEF.md](DEMO_EVIDENCE_BRIEF.md); [evidence/release-readiness.md](evidence/release-readiness.md).

**Boundary:** Label newer results unavailable. Planned work is not implemented or measured by this package.

## C19. Offline guide and accessibility

**Statement:** Bundled runtime has no remote fetch or autoplay; keyboard, focus, contrast, reduced motion and responsive behavior are checked on the browser guide.

**Version:** `This package only`.

**Evidence:** [validation/checks.json](validation/checks.json); [validation/desktop.png](validation/desktop.png); [validation/narrow.png](validation/narrow.png).

**Boundary:** Checks cover the static guide, not native application accessibility or full WCAG conformance. Managed browser file-URL policy required HTTP for cloud rendering.

## Excluded statements

No claim of seizure prevention, medical safety, universal comfort, guaranteed score, hosted CI success, external user validation, competitor deficiency, new benchmark result or completed replacement video is permitted by this evidence. No private account details or signing material are needed to support the retained claims.
