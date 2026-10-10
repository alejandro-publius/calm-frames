# Calm Frames completion checklist

Updated October 10, 2026. Solo entry; identity-verified Amazon Developer account.
Deadline October 23 at noon Pacific. Vega Virtual Device exclusively.

## Tested source and runnable build

Preserved base: `dcb27a1506c7e2e3c58186681c8f5b5dc808d331`.
Final source commit: `cffdf7b786ed0eceac147ad82ef613d7ed16135a`. Implementation committed locally.
Branch: `codex/signed-scene-holds-2026-09-29`.
The native receipt binds the exact app input hashes, final package and source commit:
`results/native_validation_2026-10-10.json`.

Package: `app/build/aarch64-debug/calm-frames-app_aarch64.vpkg`.
Architecture: aarch64 for this Apple silicon Mac. Package SHA-256:
`df238b9a64a7019ea103159bf00354f9451985672ad0c776936f60ad16c3a5df`.
The final package is installed and runnable in the visible simulator.
Earlier observation packages remain identified separately in the receipt.

## Completed

- [x] Preserved Claude's latest Harbor/AWS work and the separate deploy worktree.
- [x] Verified Claude Max subscription authentication and a small task before delegation.
  Explicit `claude-fable-5-1[1m]` with `--effort max` was accepted; actual result
  model is `claude-fable-5-1`, provider firstParty. Telemetry does not separately
  echo effort. No API keys or billing changes. Ultracode Workflow launched real
  workers but hit its noninteractive background wait ceiling; bounded ordinary
  CLI implementation and reviews completed. Receipt: `results/claude_subscription_2026-10-09.json`.
- [x] Resolved native local video/caption/chime URI failures, the Metro catalog
  collision, PIN Delete clipping, Set a PIN completion, save-button focus,
  shelf/details focus restoration, Credits Back, stale error cards and caption stacking.
- [x] Independent final review found duplicate exit navigation and background
  cleanup intercepted by the captions menu. Both regressions were observed red,
  fixed and rerun. Rapid native Back now returns once to focused Play.
- [x] Full app suite: <!--n results/native_validation_2026-10-10.json:checks.app_tests_passed -->1063<!--/n-->
  passed, <!--n results/native_validation_2026-10-10.json:checks.snapshots_passed -->57<!--/n-->
  snapshots; four existing skipped tests and one skipped suite. TypeScript passes.
  Lint: zero errors, 100 existing warnings.
- [x] Full Python suite: <!--n results/native_validation_2026-10-10.json:checks.python_passed -->1584<!--/n-->
  passed, two slow cases deselected. All nine formerly localhost-blocked cases pass.
- [x] Failed UI invocation resolved with `--watchman=false`; all 33 screens and
  transitions pass WCAG and broadcast checks. No thresholds weakened.
- [x] Monk/open halo, teal/cream/saffron identity and "A calmer way to watch"
  finished. 512 px and 114 px icons and 1280 x 720 tile produced and inspected.
  Seven brand images pass both image checks; small-size readability reviewed.
- [x] All three SBOMs reproduce byte for byte. CDK transitive/schema pins corrected;
  100 relevant infra tests pass. Full corrected conformance report independently
  reproduced, including weaker near-limit recall and protocol limitations.
- [x] Native picture and audio recording works through ScreenCaptureKit.
  Final English demo, subtitles, provenance manifest, script and shot list prepared.
- [x] Devpost draft, run instructions, feedback, friction log and upstream patches prepared.
  Current upstream main and eleven issues/PRs rechecked; no duplicate, six focused tests pass.

## Native acceptance

Full journey observations used the prior final package recorded in the receipt.
The last package changes only player exit cleanup; cold launch, saved shelf,
rapid Back, restored focus and both captioned Harbor holds were rerun on it.

| Journey | Verified result and scope |
|---|---|
| Cold launch | First-run setup observed; final rebuild launches to saved Kid shelf |
| Onboarding | PIN creation, mismatched confirmation, Delete correction, presets and room steps |
| Persistence | Kid profile, room 55 inch/8 ft, Broadcast preset and chime off survive restart |
| Parent gate | Wrong PIN remains locked; correct PIN opens; Credits Back and relaunch relock |
| Catalog | All three titles play under compatible Standard; prepared Harbor plays under Broadcast and Extra cautious; gradient excluded by stricter requirements |
| Practice | Both scheduled synthetic holds visible with changing English captions and recorded non-silent audio |
| Seeking | Native forward/backward, pause/resume and first countdown Skip observed; interrupted holds use opaque fallback |
| History | Native empty Kid history after practice is correct; practice is deliberately excluded. Positive cover attribution is integration-tested only; history is in memory |
| Recovery | Native load error observed, stale card fixed, Back and successful replay verified. Altered/unchecked title rejection is regression-tested |
| Remote | PIN, presets, profile, room, chime, catalog, Play, Back and Credits exercised with visible focus; title and Play focus restored |
| Recording | Actual composited H.264/AAC window capture; both holds and captions inspected. No physical screen timing or medical proof |

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
Open the first Harbor title, read its labelled practice plan and choose Play.
Use the visible remote or:

```sh
vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'
```

Do not infer native composition from the CLI smoke log alone. The observed
captures and native receipt provide that evidence.

## Reviewable submission material

- Review bundle: `build/calm-frames-review-2026-10-10.zip` (package, source archive,
  demo, branding, docs, receipts and native evidence).
- Video: `build/submission/Calm-Frames-demo-English.mp4`; companion SRT beside it.
  English synthetic narration, actual simulator clips/stills and editorial cards.
  Duration/WCAG check: `results/video_check.json`; broadcast also passes in
  `results/video_check_broadcast.json`.
- Source/shot provenance: `results/demo_manifest_2026-10-10.json`;
  `docs/VIDEO_SCRIPT.md`, `docs/SHOT_MANIFEST.md`.
- Draft: `docs/SUBMISSION.md`; feedback: `docs/FEEDBACK.md`;
  friction: `docs/FRICTION_LOG.md`; branding: `docs/brand/`.
- Open Source: `docs/OPEN_SOURCE_PR.md`, `docs/upstream-pr/`,
  `results/upstream_review_2026-10-10.json`.
- AWS: saved `results/aws_deploy_2026-10-09.json`. Signed publication worked in
  that record; the app uses its compiled local library, not cloud output.

## Still open

- [ ] Dependency Audit remains failed: unresolved SDK/transitive advisories and
  an expired exception. No exceptions widened. The latest hosted CI passed on
  the base commit; local SBOM/CDK fixes have no hosted rerun yet.
- [ ] Saved AWS evidence reports inactive Project cost allocation tagging and
  container findings. No new cloud run, remediation or costs were incurred.
- [ ] Public video/release/reviewer-access links and the upstream PR URL do not
  exist yet. No push, merge, publication, visibility change or submission performed.
- [ ] Entrant name, country, eligibility and contact email need the entrant's
  own values. Upstream patch author metadata still needs the chosen public identity.

There is no simulator, localhost-test, recording or Claude authentication blocker.
The remaining security and publication items prevent calling this a released,
fully submitted entry. No physical device or hardware timing work is required.
