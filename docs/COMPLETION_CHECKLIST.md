# Calm Frames completion checklist

Updated October 10, 2026. Solo entry, identity-verified Amazon Developer account.
Deadline October 23 at noon Pacific. Vega Virtual Device exclusively.

## Exact tested build

Approved native design implemented, reviewed and installed. Simulator demo and
submission materials are complete locally; publication and security items remain
open below.
App source: `73fbbeddf6c259b3cb4286f770ff6c2a55a63564`.
Branch: `codex/signed-scene-holds-2026-09-29`.
Installed package: `app/build/aarch64-debug/calm-frames-app_aarch64.vpkg`,
aarch64 Debug for this Apple Silicon Mac. SHA-256:
`9dbffc3addeb023d2d14893a85a065d67ddef658485a375182e7a2f79f98e726`.
Receipt: `results/redesign_validation_2026-10-10.json`.
Later documentation commits do not change these app inputs.

## Completed implementation and checks

- [x] Preserved Claude's Harbor work, original recordings and separate AWS worktree.
- [x] Applied approved IMPLEMENTATION_BRIEF.md and COPY_GUIDE.md from Documents.
  Teal, cream, saffron, peaceful monk/open halo and "A calmer way to watch";
  licensed native Inter, title art, library, details, onboarding and parental controls.
- [x] Reviewed all user-visible "Parental controls" wording. Pending titles say
  "Needs check" without implying analysis is running.
- [x] Fixed native focus disappearing during settings saves. Deferred-write
  regression failed before the fix and passed after it. Focus uses both outline
  and underline; save handlers block repeated writes without removing focus.
- [x] Resolved prior load/caption URI, catalog, PIN correction, stale error-card
  and exit cleanup findings. Reviewed final diffs and affected native reruns.
- [x] App suite: <!--n results/redesign_validation_2026-10-10.json:checks.app_tests_passed -->1066<!--/n-->
  passed, <!--n results/redesign_validation_2026-10-10.json:checks.snapshots_passed -->57<!--/n-->
  snapshots; four existing skips. TypeScript passes; scoped lint has zero errors,
  89 warnings. The full suite used cba1a29; the final one-sentence copy fix
  passed 85 affected tests and TypeScript. No verification or specification
  thresholds were weakened.
- [x] Full Python suite: <!--n results/redesign_validation_2026-10-10.json:checks.python_passed -->1584<!--/n-->
  passed, two slow cases deselected. All nine formerly localhost-blocked tests pass.
- [x] All 36 UI screens/transitions and nine brand/title images pass WCAG and
  broadcast checks. Production icons are 512 and 114 pixels; listing tile is
  1280 x 720. Actual small icon and native layouts inspected.
- [x] Claude subscription authentication and one small task verified before work.
  Actual model `claude-fable-5-1`, firstParty Max subscription. Explicit
  `--effort max` accepted; provider telemetry does not independently echo effort.
  Ultracode noninteractive review completed with a per-call wait ceiling.
  No API keys, billing switch or permission bypass. See
  `results/claude_redesign_2026-10-10.json`.
- [x] Prior local SBOM/CDK fixes reproduce; 100 relevant infra tests pass.
  Dependency advisories are still open and have not been waived.

## Native journey and evidence scope

| Journey | Observation |
|---|---|
| Cold launch | Final package launches the saved Kid library |
| Onboarding | Combined redesign build: mismatch rejected, Delete corrected a partial entry, PIN/preset/room setup completed; later changes only focus/copy |
| PIN | Remote keypad, incorrect entry, Delete and correct unlock exercised; Credits Back relocks |
| Presets/catalog | Standard offers all three titles; Broadcast and Extra cautious exclude incompatible gradient. All three titles played under Standard; prepared Harbor also played under stricter presets |
| Restart | Kid, Extra cautious household floor, 55-inch TV, 10-foot household distance and chime Off survive relaunch. Kid's effective distance remains its stricter 8 feet |
| Harbor practice | Both scheduled synthetic holds, changing English captions and recorded audio; examples are explicitly not detected flashing |
| Transport | Forward/back, pause/resume, countdown Skip and interrupted-hold opaque fallback observed; no physical timing measurement |
| History | Empty history after practice is correct. Positive real-cover attribution is integration-tested only; history is not durable across restart |
| Recovery | Back during loading returns to focused Watch demo, then replay succeeds. Earlier native load-error evidence retained; final fault handling also regression-tested, not newly fault-injected |
| Remote | Profile disclosure, PIN/Delete, preset/room/chime rows, full details plan, Credits and return focus exercised |

## Run the simulator demo

```sh
source ~/vega/env
vega virtual-device start
vega device is-connected --device Simulator
vega device install-app --device Simulator --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
vega device launch-app --device Simulator --appName io.github.alejandropublius.calmframes.main
```

If Vega is already running, omit the start command. Existing household data is
preserved. Fresh installs choose their own PIN. The synthetic local validation
household uses 4444; it is not a built-in package PIN or user credential.
Choose the first shelf card, Harbor: Scene hold demo, and select Watch demo.
The hero Watch now action plays the separately prepared Harbor title.
Use the visible remote or:

```sh
vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'
```

Do not infer native composition from the CLI smoke log alone. The observed
captures and native receipt provide that evidence.

## Submission preparation

- [x] Refreshed English demo: `build/submission-redesign/Calm-Frames-demo-English.mp4`,
  companion SRT, exact script and shot manifest. Actual cba1a29 app captures;
  final copy-only build relationship is explicit in `docs/SHOT_MANIFEST.md`.
- [x] Finished video passes WCAG and broadcast at
  <!--n results/redesign_video_check.json:duration_s -->156.021<!--/n--> seconds.
  Audio peak is below clipping. Checks: `results/redesign_video_check*.json`.
- [x] Review archive: `build/calm-frames-redesign-review-2026-10-10.zip`.
  ZIP CRC and payload hashes verified; source, package, video, branding, docs
  and selected native evidence included. Bundle receipt:
  `results/redesign_review_bundle_2026-10-10.json`.
- [x] Devpost draft: `docs/SUBMISSION.md`; product feedback: `docs/FEEDBACK.md`;
  friction: `docs/FRICTION_LOG.md`; brand assets: `docs/brand/`.
- [x] Qualifying Open Source candidate patches and instructions prepared in
  `docs/OPEN_SOURCE_PR.md` and `docs/upstream-pr/`; six focused tests pass.
- [x] Saved AWS evidence inspected: `results/aws_deploy_2026-10-09.json`.
  Signed cloud publication worked in that record. The app uses its compiled
  local catalog and does not consume the cloud output. No new cloud costs.

## Still open

- [ ] Dependency Audit remains failed: unresolved SDK/transitive advisories and
  an expired exception. No exceptions widened. Local SBOM/CDK fixes have no
  hosted rerun. Saved AWS evidence also has inactive Project cost tagging and
  container security findings.
- [ ] Confirm redistribution terms for the generated Amazon DOMParser polyfill
  before public source release; the specific header issue is in `docs/SECURITY.md`.
- [ ] Entrant name, country, eligibility and contact email need the entrant's
  values. Upstream patch metadata needs the chosen public author identity.
- [ ] Public video/release/reviewer-access links and upstream PR URL remain
  unpublished. No push, merge, visibility change or Devpost submission performed.

There is no simulator, localhost-test, recording or Claude authentication blocker.
Publication and the unresolved security items remain distinct from local demo
completion. No physical device or hardware timing work is required.
