# Calm Frames completion checklist

Updated October 11, 2026. Solo entry, identity-verified Amazon Developer account.
Deadline October 23 at noon Pacific. Vega Virtual Device exclusively.

## Current design polish

The latest cloud work refines the library, title artwork, secondary navigation,
setup, parental controls and viewing settings. It changes app inputs beyond the
native package below. The current source has not been built, installed or
verified on the Vega Virtual Device in this cloud session.

Review: [design/POLISH_REVIEW.md](design/POLISH_REVIEW.md).
Cloud evidence: [`design_polish_2026-10-10.json`](../results/design_polish_2026-10-10.json).
Native validation and refreshed demo assets remain open below.

The latest interaction pass keeps profile choices in the remote focus order
while saving, separates notice actions from spoken announcements and includes
all displayed licence conditions in spoken credits. These changes preserve the
approved visual design; they still need native focus and screen-reader checks.

## Earlier native tested build

The earlier approved native design was implemented, reviewed and installed.
Its simulator demo and review assets are preserved as evidence of that build;
they do not contain the current cloud polish.
App source: `73fbbeddf6c259b3cb4286f770ff6c2a55a63564`.
Branch: `codex/signed-scene-holds-2026-09-29`.
Installed package: `app/build/aarch64-debug/calm-frames-app_aarch64.vpkg`,
aarch64 Debug for this Apple Silicon Mac. SHA-256:
`9dbffc3addeb023d2d14893a85a065d67ddef658485a375182e7a2f79f98e726`.
Receipt: `results/redesign_validation_2026-10-10.json`.
Documentation and audit work through `8271b38` preserved these app inputs.
The subsequent design polish changes them and requires a new native receipt.

## Completed implementation and checks for the earlier build

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

## Earlier native journey and evidence scope

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

## Run the earlier simulator demo

```sh
source ~/vega/env
vega virtual-device start
vega device is-connected --device Simulator
vega device install-app --device Simulator --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
vega device launch-app --device Simulator --appName io.github.alejandropublius.calmframes.main
```

If Vega is already running, omit the start command. Existing household data is
preserved. Fresh installs choose their own PIN. The synthetic local validation
household uses a PIN that is not in the repository; there is no built-in package PIN.
Choose the first shelf card, Harbor: Scene hold demo, and select Watch demo.
The hero Watch now action plays the separately prepared Harbor title.
Use the visible remote or:

```sh
vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'
```

Do not infer native composition from the CLI smoke log alone. The observed
captures and native receipt provide that evidence.

## Earlier submission preparation

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
- [x] Pushed the completed implementation to the existing GitHub branch and
  uploaded all nine review assets as a private draft release. GitHub asset
  digests match local hashes. See `results/github_push_2026-10-10.json` and
  [the draft release](https://github.com/alejandro-publius/calm-frames/releases/tag/untagged-5e898f46d87868df8dd6).
- [x] Devpost draft: `docs/SUBMISSION.md`; product feedback: `docs/FEEDBACK.md`;
  friction: `docs/FRICTION_LOG.md`; brand assets: `docs/brand/`.
- [x] Qualifying Open Source candidate patches and instructions prepared in
  `docs/OPEN_SOURCE_PR.md` and `docs/upstream-pr/`; six focused tests pass.
- [x] Saved AWS evidence inspected: `results/aws_deploy_2026-10-09.json`.
  Signed cloud publication worked in that record. The app uses its compiled
  local catalog and does not consume the cloud output. No new cloud costs.

## Cloud continuation

The cloud checkout received the finished `d451a90` source and reran the current
app and Python checks. Environment-specific failures passed after scoped child
process permission, refreshed Python pins and isolated Moto configuration.
New dependency-scanner regression tests also pass. Exact full-run and rerun
counts are separate in `results/cloud_continuation_2026-10-10.json`.

That handoff preserved the approved native package inputs through `8271b38`.
The later design polish requires a fresh Mac build and native checks. Direct
cloud verification of the earlier private release assets awaits
the saved GitHub API network setting; Git source synchronization works.

## Current release-preparation tools

- [x] Synced the shared source through `9afacc0` and pushed the simulator-focused
  preparation tools as `52ecf14`; the GitHub branch hash matched.
- [x] App and Python suites, final preparation guards, TypeScript, SBOM comparison,
  style and staged secret checks pass. Exact runs and limits are in
  [`finish_preparation_2026-10-11.json`](../results/finish_preparation_2026-10-11.json).
- [x] Prepared [MAC_FINISH.md](MAC_FINISH.md) with current build, native verification,
  recording and evidence-bundle commands. The commands still require a Mac run.
- [x] Added exact original report attachments under the prepared library's
  `reports/` directory. Future exports carry them automatically; existing exports
  accept matching originals without changing catalog, maps, captions or video.
  Release preparation requires reports for every retained generation.

## Still open

- [ ] Rebuild and install the current polished source on the Mac's Vega Virtual
  Device. Check D-pad focus and return navigation, full-page scrolling, PIN
  setup and correction, saved settings, title playback, holds, audio and captions.
  The Oct 11 tree also changes two runtime dependencies (`xmldom` is an alias
  of `@xmldom/xmldom` 0.8.15, `lodash` is 4.18.1) and the Harbor shelf copy, so
  the same rebuild covers them; if the Vega build or playback rejects the
  parser alias, the one line in `app/package.json` reverts.
- [ ] Re-render the narration before any upload: the recorded cut still says
  the earlier 2:10 sentence, and `docs/VIDEO_SCRIPT.md` now carries the approved
  one. Follow [MAC_FINISH.md](MAC_FINISH.md) to supply the assembler with fresh
  capture and package hashes, then run both finished-video checks before
  preparing replacement assets.
- [ ] Capture the polished native screens and playback, refresh the English
  demo and its source manifest, and rerun the finished video checks. Rebuild
  the review bundle and package hashes before replacing draft release assets.
- [x] Dependency Audit was repaired on Oct 11: `xmldom` replaced, `lodash`
  moved, and every remaining finding sorted into two groups by whether the
  package is in the device bundle (`results/bundle_packages_2026-10-11.json`).
  The hosted Audit run on the Oct 11 push is green in all four jobs and CI in
  all six (`results/github_push_2026-10-11.json`). Both groups are due for
  review on Oct 21, when the dates move past judging. Saved AWS evidence also has inactive Project cost tagging
  and container security findings.
- [ ] Attach the original verification reports for both prepared-library
  generations. Neither original is present in this cloud checkout. The normal
  delivery check lists their exact hashes, and the strict release gate refuses
  to proceed until both are present and checked. Use the attachment commands in
  [MAC_FINISH.md](MAC_FINISH.md) on the Mac where they were generated; do not
  substitute a new report under an old hash.
- [ ] Send the Amazon sample licence clarification in
  [`AMAZON_SAMPLE_LICENSE_REVIEW.md`](AMAZON_SAMPLE_LICENSE_REVIEW.md) by Oct 13.
  NOTICE and the README now carry the caveat either way.
- [ ] Resolve the conflicting Amazon license notices in the tracked Shaka player
  wrapper and source files inside its integration archive before public source
  release. See [`AMAZON_SAMPLE_LICENSE_REVIEW.md`](AMAZON_SAMPLE_LICENSE_REVIEW.md)
  for verified upstream evidence and an unsent clarification request.
- [ ] Entrant name, country, eligibility and contact email need the entrant's
  values. Upstream patch metadata needs the chosen public author identity.
- [ ] Public video/release/reviewer-access links and upstream PR URL remain
  unpublished. Code and private draft artifacts are on GitHub. No merge,
  visibility change, final release publication or Devpost submission performed.

Simulator, recording and Claude authentication worked in the earlier Mac session.
The current polish still needs its own Mac build and simulator validation;
cloud checks cannot supply that evidence. Publication and unresolved security
items also remain open. No physical device or hardware timing work is required.
