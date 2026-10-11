# Product feedback

Amazon asks five questions about every tool an entry used. This file answers them once per tool, for every tool Calm Frames actually used, and then lists what we would like added, each marked Critical, Important or Nice-to-have.

**The five questions, in the order they appear in each section:**

1. What we used it for
2. What worked well
3. What needs work
4. Onboarding, zero to hello world
5. Would we build with it again

**Two rules this file keeps.** Nothing here is a guess. Every complaint points at something that happened during the build, and the long version of each one, with the exact commands and the exact output, is an entry in [`docs/FRICTION_LOG.md`](FRICTION_LOG.md) or, for AWS, in [`results/aws_deploy_2026-10-09.json`](../results/aws_deploy_2026-10-09.json) and [`pipeline/infra/README.md`](../pipeline/infra/README.md). The AWS sections, 8 to 16, were rewritten after the stack was deployed on Oct 9, 2026, and answer from that night: one deploy, one update and two runs of a short calm test clip. Where one night of use is all there is, the section says so rather than inventing an opinion.

Every measured number in this file is marked and checked against `results/` by CI, so a figure that drifts from what was measured fails the build.

**Environment for everything below unless a section says otherwise:** macOS 15.1.1 (24B91) on Apple M1, 16 GB. Vega CLI 1.3.4, Vega SDK 0.24.9914, Vega <!--n results/vvd_smoke.json:device.build -->OS 1.2 (TV Ship/101520710)<!--/n--> on the Vega Virtual Device, Node 22, React Native 0.83, September 2026, with the native journey observed on Oct 9 and 10, 2026. This submission is simulator-only and uses no physical Fire TV device, which is why nothing below claims anything about hardware. **For the AWS sections:** us-east-1, CDK CLI <!--n results/aws_deploy_2026-10-09.json:cdk.cli_version -->2.1142.0<!--/n--> with aws-cdk-lib <!--n results/aws_deploy_2026-10-09.json:cdk.aws_cdk_lib -->2.270.0<!--/n-->, run from the same Mac on the night of Oct 9, 2026, in Pacific Daylight Time.

## At a glance

| # | Tool | Heaviest complaint | Build with it again |
|---|---|---|---|
| 1 | Vega SDK and Vega CLI | `vega device list` crashes; `inputd-cli` works only through `vega device run-cmd`, not the documented `vega exec` form, and no CLI screenshot command turned up | Yes |
| 2 | Vega Virtual Device | QMP and plain window captures missed the app picture, the composited recording that works is undocumented, and playback is not steady | Yes for development and recorded journeys; not for screen timing |
| 3 | `vega-video-sample` | A failed load is silent; the README documents a workflow OS 1.2 cannot do | Yes, and we are sending a fix back |
| 4 | `react-native-w3cmedia` | `timeupdate` cadence and `currentTime` resolution are undocumented | Yes, with that documented |
| 5 | Vega Media Controls | A voice seek can move the playhead without the app's UI, and that is not called out | Yes |
| 6 | KeplerCaptionsView | The z-order contract is not written down anywhere | Yes |
| 7 | The accessibility APIs | No system signal for photosensitivity, and no in-app capture to check our own screens with | Yes |
| 8 | AWS CDK | A CLI older than the library stops right after synth; four more traps on the first deploy | Yes |
| 9 | AWS Fargate on ECS | With no NAT gateway the task needs a public IP, and nothing documents the cheap and still private pattern | Yes |
| 10 | Amazon S3 | Nothing that cost us time | Yes |
| 11 | Amazon CloudFront | Signed URLs need an RSA key pair managed out of band, so the Oct 9 stack serves without them | Yes |
| 12 | AWS Lambda | The CDK's own helper functions leave log groups behind with no retention | Yes |
| 13 | Amazon DynamoDB | Nothing that cost us time, and one row is not a load test | Yes |
| 14 | Amazon ECR | Nothing that cost us time; its scan found what our own audit could not see | Yes |
| 15 | Systems Manager Parameter Store and KMS | CloudFormation cannot make a SecureString, so the key lives outside the stack | Yes |
| 16 | AWS Budgets | A budget filtered on a new tag cannot fire until the tag is activated, and nothing says so | Yes |
| 17 | Kepler UI Components, react-native-kepler, Kepler File System | The build rewrites `manifest.toml`; the data directory cannot be written from the host | Yes |
| 18 | GitHub Actions | Three days of runs that never started, which cost the pre-publication CI evidence for the scene-hold tree | Yes |

---

## 1. Vega SDK and Vega CLI

**What we used it for.** Everything. Vega SDK 0.24.9914 and Vega CLI 1.3.4 built, installed, launched and log-streamed the app, and ran the virtual device. Calm Frames is a Vega app end to end.

**What worked well.** The install is one non-interactive command and it finished in 4 minutes 18 seconds. `vega run-app`, `vega device install-app` and `vega device start-log-stream` are reliable, and they are the backbone of every measurement run in this submission. The virtual device boots a real OS 1.2 image, so platform behaviour showed up early rather than on hardware. `vega device info` and `vega device is-connected` are dependable enough to script around, which mattered once we found that the obvious command is not.

**What needs work.** Six things, all in the friction log with their output.

- `vega device list` crashes with `Cannot read properties of undefined (reading 'trim')` while a device is connected and every other device command works against that same device at that same moment. It is the obvious way to script against a device and it is the first thing a new developer tries.
- `vega virtual-device status` reports `"running":true` about twenty seconds before the device can take a command, so every script has to poll `vega device is-connected` instead and every developer finds this out the same way.
- The same command exits non-zero before the first start, where "no instance yet" is a normal state, and prints the internal command line with it.
- The virtual device sometimes exits with nothing written to its own log after "Virtual device ready", so a scripted run has to check for the device before every step.
- Earlier work missed the documented `inputd-cli` remote-input route. The Oct 9 documentation review found it written as `vega exec inputd-cli button_press KEY_BACK`; on this CLI that form looks for a host executable that does not exist. The form that works, used on Oct 9 and 10, is `vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'`. No CLI screenshot command was found in the pages reviewed. See section 2 for the capture story.
- `vega device copy-to --help` has its `--source` and `--destination` descriptions the wrong way round, contradicting its own examples printed immediately below.

Two smaller ones, both about the installer: with stdout redirected to a file it writes progress frame by frame, so our install log was 2.5 MB holding 39,131 `Extracted Files: n/39131` lines, and it appends `source ~/vega/env` to every shell startup file it can find, with no way to opt out.

**Onboarding, zero to hello world.** Good once you find the right page, and the right page is hard to find. `https://developer.amazon.com/docs/vega/0.24/` is a 404, and so is `/latest/`. System requirements are split between the install page and the release notes, and the install page says Node 18 while the samples declare Node 22 or later, so following the install page gives you a Node the samples reject. From a working shell to the sample playing video on the virtual device was under a day, and most of that day went on documentation rather than tools.

**Would we build with it again.** Yes. What we hit are rough edges in the CLI rather than limits in the platform, and every one of them had a way around it. Discoverable input and composited capture documentation matter because an accessibility app has to check its own screens.

---

## 2. Vega Virtual Device

**What we used it for.** All development and device measurements in this simulator-only submission: the smoke test, the layering run, the cover timing runs, and on Oct 9 and 10 the whole benign journey, observed on its screen and recorded. It is also where the app was driven from a script, over the QEMU control socket, before `inputd-cli` was reached through `vega device run-cmd`.

**What worked well.** It is a real OS 1.2 image on ARM, and it is the only device used for this submission. It supports development without purchasing hardware; behavior on a physical device is not inferred from it. The recorded smoke run played a Blender title over HLS with <!--n results/vvd_smoke.json:segment_fetches_during_play -->8<!--/n--> segment fetches during <!--n results/vvd_smoke.json:play_seconds -->40<!--/n--> seconds of play, <!--n results/vvd_smoke.json:streaming_errors -->0<!--/n--> streaming errors and <!--n results/vvd_smoke.json:crash_lines -->0<!--/n--> crash lines, at a peak of <!--n results/vvd_smoke.json:peak_pss_kb -->353178<!--/n--> kB. On Oct 9 and 10 it carried the whole benign journey, recorded: onboarding, settings surviving a relaunch, the parent gate, all three catalog titles, both Harbor holds with changing English captions and non-silent audio, and pause, resume and seeks into holds.

**What needs work.** Three things, and the first is the serious one.

- **Capture is undocumented, and the obvious routes miss the picture.** QMP `screendump` returned black and one macOS full-screen grab showed the desktop behind the virtual device. What worked, on Oct 9 and 10, was a ScreenCaptureKit recording of the simulator window, H.264 picture with AAC audio, and even that came back with stale frames after overnight inactivity under Stage Manager until the capture helper activated the Vega window first. The saved takes show both Harbor holds, their changing English captions and non-silent audio, inspected by eye. None of this is in Amazon's documentation, and logs and synthetic UI color frames cannot replace it.
- **Playback is not steady.** Of four runs in one afternoon, two played cleanly, one failed with `Category: UNKNOWN, Position: 0.084` on the same HLS stream, and one never started. A later timing measurement needed 22 app launches to collect <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n--> usable trials. The error carries a category of `UNKNOWN` and a position, and nothing else to act on.
- **The device backgrounds an app nobody is touching**, and a backgrounded app stops playing. A person holding a remote never hits this. A camera rig with nobody pressing anything hits it every time, so our runs press a key the app does not bind, every few seconds, to keep the device awake without touching playback.

**Onboarding, zero to hello world.** Quick to start and confusing to script against, because the readiness signal is not one. Budget time for two discoveries nothing warns you about: that `status` is not readiness, and that the black screenshot you are looking at is black for a reason rather than because the app failed.

**Would we build with it again.** Yes. Label simulator measurements as such, distinguish software events from displayed frames, and inspect the saved recording directly, which is what the Oct 9 and 10 takes are for. Physical camera timing is outside this submission scope.

---

## 3. `AmazonAppDev/vega-video-sample`

**What we used it for.** `vega-video-sample` at tag `v0.24-RN83` is the base of our app. We kept its playback stack, its caption wiring and its media controls, and replaced the rest.

**What worked well.** It is a complete, working reference for the parts that are hard to guess: how `KeplerVideoSurfaceView`, `KeplerCaptionsView` and the W3C media player fit together, how the caption view handle is passed to the player and cleared again, and how media controls are given focus. Reconstructing that wiring from documentation would have taken a long time, and having it in one repository under MIT-0 is worth a great deal. Its test setup is good enough that our upstream fix needed no new mocks: `jest.setup.ts` already mocks `ShakaPlayer`, and the existing `VideoHandler` test already works around `useCallback` inside a class.

**What needs work.** Four things, three of them real defects.

- **A failed Shaka load is dropped in silence.** `ShakaPlayer.load()` is declared `void` and fires `internalLoad()` without returning or awaiting it, so a rejected manifest or segment fetch becomes an unhandled rejection. The caller's `try`/`catch` in `VideoHandler.loadAdaptiveMediaPlayer` can only see a synchronous throw, so `setIsVideoError` is never called, the error view never renders, and the buffering spinner stays up for good. The method's own comment block says it "4. Handles any loading errors". This is the subject of our upstream pull request, with the root cause, the fix, three tests and the mutation results in [`docs/OPEN_SOURCE_PR.md`](OPEN_SOURCE_PR.md).
- **The README documents a workflow OS 1.2 cannot carry out.** It says to push search data with `vega exec vda push KVATestData.json /home/app_user/packages/<package id>/data`. On OS 1.2 `/home` is not on the device, and the developer shell runs inside its own sandbox at `/pkgs/com.amazon.dev.shell`, so there is no path from the host into any app's data directory. We lost time following it before concluding the route does not exist.
- **`npx jest --ci` exits 1 on a clean checkout with every test passing**, because `test/blocks/components/MediaItemShoveler/__snapshots__/MediaItemShoveler.test.tsx.snap` holds two snapshot entries no current test produces, and `--ci` counts an obsolete snapshot as a failure. Two deleted lines fix it. We hit it as a red CI run on a day when nothing was wrong.
- **`postinstall` builds Shaka Player from source and needs a JDK**, which is not said where you first need it. The JDK on this machine was Java 1.8 and x86_64 only, and the build wants a modern one, so `npm install` now runs with `JAVA_HOME` pointed at openjdk 21. Our CI installs with `--ignore-scripts` and skips the build entirely, because the tests mock the player.

One more thing that is a design choice rather than a defect, and worth knowing: the sample picks its player purely from a hand-declared `format` field. `VideoFormat` in `src/types/TitleData.d.ts` admits `'DASH'` while `VideoFileTypes` in `src/data/videos/index.ts` does not, so anything whose `format` is not exactly `"MP4"` goes to Shaka, which cannot parse a raw MP4 as a manifest. That is how we first met the silent failure above.

**Onboarding, zero to hello world.** Fast. Clone, install, build, sideload, and a title plays, with the Shaka build in `postinstall` taking most of the wall-clock time.

**Would we build with it again.** Yes, and we are: the contribution goes back to it. The repository is still on `ef8e4da` from August 6 2026, and the one outside pull request it has merged was a two-line documentation change, so we are not expecting a quick review, and the fix is written to be reviewable in two independent commits for that reason.

---

## 4. The W3C media player, `@amazon-devices/react-native-w3cmedia`

**What we used it for.** All playback. We read `currentTime`, `playbackRate`, `getVideoPlaybackQuality` and the media events from it, and we draw a cover over it. We never replace it and we never reimplement it.

**What worked well.** It is the standard W3C media element surface, so what a web developer knows transfers directly. `getVideoPlaybackQuality` gave us dropped and total frame counts, <!--n results/vvd_timeupdate_stats.json:playback_quality_last.droppedVideoFrames -->0<!--/n--> dropped of <!--n results/vvd_timeupdate_stats.json:playback_quality_last.totalVideoFrames -->1164<!--/n--> in the recorded run, which is exactly what a safety layer needs to know about the pipeline underneath it. `setMediaControlFocus` and the caption view handle are clean integration points.

**What needs work.** Five things.

- **`timeupdate` cadence is not documented, and it is not regular.** In one recorded run the median gap was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms, the shortest <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.min -->75<!--/n--> ms and the longest <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms, while the clip kept playing throughout. A feature that reacts to `timeupdate` would have been five seconds late. Our whole design follows from that number: the cover runs on a wall clock re-anchored to media time at every report, and the price is drift, which reached <!--n results/vvd_timeupdate_stats.json:worst_wall_clock_drift_ms -->2756<!--/n--> ms in that same gap.
- **`currentTime` resolution is not documented either.** The smallest step we saw reported was <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms. Anything that must act at a precise media time needs a stated guarantee for both of these, not a number each developer measures for themselves and gets a different answer to.
- **A plain MP4 over HTTP does not start**, where the same content over HLS does, and nothing says why. Two things had to be true before our marker clip would play at all: package it as HLS, and have the test server answer byte ranges. Python's own `SimpleHTTPRequestHandler` ignores the `Range` header and returns the whole file with a 200, and the player treats that as a broken source with no error anywhere.
- **A stream with no audio track pauses a few seconds in.** We searched the sample for anything that waits on audio and there is nothing, so this comes from below it. Every test clip we generate now carries a silent AAC track.
- **A packaged asset is not opened by its documented URI.** The Kepler file system documentation gives package assets as `file:///pkg/...`, and the native player treated that form as a literal file name and failed to open it; the same bytes opened as `/pkg/...`. We normalize the prefix at the native media boundary only (friction log entry 36). One documented form, accepted by both the file system and the player, would remove a blocking afternoon.

**Onboarding, zero to hello world.** Good, because the sample does it for you. Hard from the API surface alone, because the surface handle and caption handle lifecycle is not obvious and the ordering matters.

**Would we build with it again.** Yes. We would ask for the documented `timeupdate` and `currentTime` statement first, because an accessibility feature that has to be on screen before a specific frame cannot rest on undocumented timing. One more thing we would ask for: something that tells the app how long the JavaScript thread was unavailable. Our own measurement found a cover going on <!--n results/gate1_software_vvd.json:worst_lead_ms -->-86<!--/n--> ms relative to its marker, which is a thread pause of about a third of a second, and we can only see that after the fact.

---

## 5. Vega Media Controls, `@amazon-devices/kepler-media-controls`

**What we used it for.** System and voice transport. This is where an Alexa "skip forward" arrives, which for us makes it a safety surface rather than a convenience: a spoken command can move the playhead into a part of a video we are supposed to be hiding.

**What worked well.** Subclassing `KeplerMediaControlHandler` and overriding only the methods you care about is the right shape, and handing the subclass to `setMediaControlFocus` made it one call to wire up. Our `SafeMediaControlHandler` overrides every transport callback, calls none of `super`, and routes all of them through the same seek function the on-screen controls use, which covers the picture first and only then moves. That was easy to express.

**What needs work.** Two things.

- **The design deserves a warning in the documentation.** `handleSeek` and friends can move the playhead with the app's own UI uninvolved. That is correct behaviour, and it means an app that has to validate a target position must funnel every one of these through its own logic. It is easy to leave the voice path unguarded while the remote path is careful, and nothing tells you.
- **The manifest opt-in is load bearing and easy to lose.** The `IMediaPlaybackServer` extras block with `command_options` and the `AdvancedSeek` feature is what makes these commands reach the app at all. Without it our handler is never called and a spoken "skip forward" goes straight past the guard, with no error and no log line. Since the build rewrites `manifest.toml` on every build (section 17), we have a test that fails if that block goes missing. That test should not have to exist.

**Onboarding, zero to hello world.** Quick, through the sample. Slow from the documentation, because the manifest half and the code half are in different places.

**Would we build with it again.** Yes. For a voice-first television platform this is the right abstraction, and `AdvancedSeek` carrying a position rather than a direction is what lets us check a target before honouring it.

---

## 6. KeplerCaptionsView

**What we used it for.** Captions, and in our case the reason a hidden segment is still followable. It sits above our cover, so the words carry on over a black picture and a child does not lose the story while the flashing part is hidden.

**What worked well.** The handle-based lifecycle, `onCaptionViewCreated` and `setCaptionViewHandle` with `clearCaptionViewHandle` on the way out, is clear and hard to get wrong once you have seen it done. The view composites above ordinary React Native views, which is the fact our whole design rests on: the cover is drawn between the video surface and the captions view.

**What needs work.** Three things, two of them documentation.

- **The z-order contract is not written down.** Video surface at the bottom, our own views in the middle, captions on top. We rely on it completely and we found it by trying it. It should be a stated contract, because if it ever changed, an accessibility layer built on it would fail silently and look like a rendering glitch.
- **One captions view per process should be said loudly.** We designed around it from the start, so we never hit it, and an app that adds a second one finds out at runtime rather than at build time. A note in the API reference costs nothing.
- **A z-index on the caption view itself does nothing.** When a scene hold draws a React Native image over the picture, the native caption view stayed under the image whatever z-index it carried; what works is a retained, non-collapsible React Native host view that carries the stacking style with the caption view inside it (friction log entry 37). The composition rules for native views inside React Native trees would be worth one worked example.

Whether captions stay readable over the cover on screen was checked on Oct 9 and 10, after a fix on our side: captions had been stacking behind the cover image, and once that was corrected the ScreenCaptureKit recordings of the Vega Virtual Device show both scheduled Harbor holds with changing English captions above the held picture, with non-silent audio throughout. The earlier harness verdict in `results/vvd_layering_rehearsal.json` stays <!--n results/vvd_layering_rehearsal.json:layering.verdict -->inconclusive<!--/n-->, because its captures missed the app picture; the recordings, inspected by eye, are the evidence, which is R00 and S04 in [`docs/SHOT_MANIFEST.md`](SHOT_MANIFEST.md). No physical device was used.

**Onboarding, zero to hello world.** Fine through the sample. Not obvious from the API alone.

**Would we build with it again.** Yes.

---

## 7. The accessibility APIs: VoiceView, `AccessibilityInfo` and the accessibility privilege

**What we used it for.** Every card Calm Frames shows is spoken as well as drawn. A countdown before a hidden part, the fact that a part was hidden, and why. We use two mechanisms together: `accessibilityLiveRegion="polite"` on the card itself, so a screen reader watching the tree reads it when it appears, and `AccessibilityInfo.announceForAccessibilityWithOptions(text, { queue: true })` to push the same words without interrupting whatever is already being read. The app declares `com.amazon.devconf.privilege.accessibility` under `[wants]` in the manifest.

**What worked well.** The React Native accessibility surface is there and it behaves the way a React Native developer expects: `accessibilityLabel`, `accessibilityRole`, `accessibilityLiveRegion` and the announcement API all work, so knowledge carries over from mobile. `announceForAccessibilityWithOptions` with `{ queue: true }` is the right primitive for this job. A child hearing "flashing part coming up" cut off halfway is worse than hearing it a beat later, and having queueing available rather than only the interrupting form is what makes the polite version possible.

**What needs work.** Four things, and the first is the feature request that leads this whole submission.

- **There is no system-wide signal for photosensitivity.** A television knows the volume the household likes, the caption style they prefer and whether a screen reader is on. It does not know that the person in front of it must not be shown flashing. So every app has to invent its own protection, and a child's safety depends on which app they happened to open. Apple ships "Dim Flashing Lights" at the system level. Fire TV should too, and it should be readable by any app, in the same way `AccessibilityInfo.isScreenReaderEnabled()` is readable now.
- **Announcements are fire and forget.** `announceForAccessibility` returns nothing and throws nothing. There is no way to ask whether VoiceView is running, whether the announcement was spoken, or whether it was dropped, so an app cannot fall back to something visible when speech is unavailable. Ours is written to never throw and to never block the cover, which is the safe shape, and it is a shape forced by not being able to ask.
- **The privilege is quiet when it is missing.** Without `com.amazon.devconf.privilege.accessibility` in the manifest, no announcement is made and nothing says why. Since the build rewrites `manifest.toml` (section 17), we hold that line in place with a test.
- **There is no documented way to check your own screens.** This is section 2's capture problem seen from the accessibility side. WCAG 2.3.1 applies to an app's own interface, not only to the video it plays, and on Vega today a developer cannot get a frame of what their app drew from inside the app, and the outside routes we tried did not give one either. React Native 0.83 has no `takeSnapshot`, no `@amazon-devices` package offers a view capture, and the QMP screendump we tried returned black. A composited host screen recording does capture the app (section 2), which gives a person evidence to inspect but gives the app no way to check itself. We had to make the app record what it paints, screen by screen, and turn that record into a video our analyzer could read, which is a real answer but it is not a photograph of the screen.

**Onboarding, zero to hello world.** Good if you arrive from React Native. The manifest privilege is the one piece that is not where you expect it, and it is the piece that silently disables everything else.

**Would we build with it again.** Yes. The pieces we needed were there, and the gap is not in the API surface, it is that the platform has no idea a viewer is photosensitive.

---

## 8. AWS CDK

**What we used it for.** The whole ingest stack in Python CDK: two S3 buckets, a DynamoDB table, an ECR repository, an ARM64 Fargate task definition, a Lambda trigger, a CloudFront distribution, a VPC, a budget, log retention, cost tags, and a GitHub OIDC deploy role that is defined and unit tested but was not deployed. The template is asserted on in unit tests, and on Oct 9, 2026 the stack was deployed once, from commit c5724de: <!--n results/aws_deploy_2026-10-09.json:stack.resources_total -->42<!--/n--> resources, created in <!--n results/aws_deploy_2026-10-09.json:stack.create_seconds -->210.9<!--/n--> seconds, then updated in <!--n results/aws_deploy_2026-10-09.json:stack.update_seconds -->39.9<!--/n--> seconds to give the ingest task a signing key.

**What worked well.** Asserting on the synthesized template is still the cheapest safety net on this project. Zero NAT gateways, private buckets and a budget were all known before anything existed, and the deployed stack has the same <!--n results/aws_deploy_2026-10-09.json:stack.nat_gateways -->0<!--/n--> NAT gateways the tests asserted. The IAM approval prompt is the right design. Before the first deploy it printed every IAM and security group change the stack was about to make, <!--n results/aws_deploy_2026-10-09.json:iam_approval.statement_rows -->20<!--/n--> statement rows, <!--n results/aws_deploy_2026-10-09.json:iam_approval.managed_policy_rows -->3<!--/n--> managed policies and <!--n results/aws_deploy_2026-10-09.json:iam_approval.security_group_rows -->1<!--/n--> security group rule, and a person read them before typing `y`. It only asks when it has a terminal to ask on: from a script or an agent's shell the deploy fails instead, because the stack includes security changes. That is the behaviour we want, and it is why both deploys that night were run by Alex in his own terminal. The update touched only what it had to: <!--n results/aws_deploy_2026-10-09.json:stack.update_changed_count -->4<!--/n--> resources, the task definition, the task role's policy, and the starter Lambda and its policy pointed at the new revision. The CloudFront distribution was left alone.

**What needs work.** Six things, the first four from the night of the deploy, Oct 9, 2026.

- **A CLI older than the library fails after synth, not before.** Our CLI was pinned at <!--n results/aws_deploy_2026-10-09.json:cdk.cli_version_pinned_in_repo_at_deploy -->2.1032.0<!--/n-->, beside aws-cdk-lib <!--n results/aws_deploy_2026-10-09.json:cdk.aws_cdk_lib -->2.270.0<!--/n-->, which writes cloud assembly schema <!--n results/aws_deploy_2026-10-09.json:cdk.cloud_assembly_schema -->54<!--/n-->. Our offline `make synth` runs the app without the CLI, so nothing caught the mismatch until the pinned CLI was pointed at the app on the night of the deploy, and it stopped right after synth with:

  > <!--n results/aws_deploy_2026-10-09.json:cdk.pinned_cli_error -->This CDK CLI is not compatible with the CDK library used by your application. Please upgrade the CLI to the latest version. (Cloud assembly schema version mismatch: Maximum schema version supported is 48.x.x, but found 54.0.0. You need at least CLI version 2.1142.0 to read this manifest.)<!--/n-->

  The message is clear and names the fix, which is to its credit. The deploy ran on <!--n results/aws_deploy_2026-10-09.json:cdk.cli_version -->2.1142.0<!--/n-->, named on the command line, which is also the oldest CLI the library declares, <!--n results/aws_deploy_2026-10-09.json:cdk.library_minimum_cli_version -->2.1142.0<!--/n-->. The pin has moved to that version in all three places it is written, and a test fails if they disagree or fall below what the installed library declares. Suggestion: the library knows the oldest CLI it can work with, so say so before synthesizing, not after.
- **The CLI's own region wins over the one you export.** The CLI resolves its region and writes it over any `CDK_DEFAULT_REGION` in the environment. On the deploy machine a fresh terminal resolved us-west-2, so without `AWS_REGION=us-east-1` exported, the bootstrap and the stack would have gone there. Nothing would have failed, which is the problem: it would have worked, somewhere else. Our deploy instructions export `AWS_REGION` now. Suggestion: when `CDK_DEFAULT_REGION` is set and the CLI resolves a different region, say so.
- **Bootstrapping inside the app's directory runs the app.** `cdk bootstrap` inside `pipeline/infra` picks up the app's `cdk.json` and, without an environment on the command line, runs the app to find one, which needs the virtual environment, Node 22 and the stack's context values. From a directory with no `cdk.json`, bootstrap is one command that needs none of that. Suggestion: say that it is about to run the app to find an environment, and that naming one avoids it.
- **The lookup cache holds the account id, and the guide says to commit it.** The VPC's availability zone lookup is cached in `cdk.context.json` under a key that includes the account and region, and the CDK guide's page on context says `cdk.json` and `cdk.context.json` "must be committed to source control along with the rest of your app's source code" (read Oct 9, 2026). That puts the account id in a repository that goes public, so ours is gitignored instead. The same file was written into the checkout minutes before the deploy built the ingest image, and it went into that image's build context; `.dockerignore` now keeps it out. Suggestion: say on that page what the file holds, and how to keep it out of a public repository.
- **The `ec2.Vpc` default is one NAT gateway per availability zone.** For this stack's two zones that would add <!--n results/cost_estimate.json:published.nat_gateways_would_add_usd -->65.7<!--/n--> US dollars a month in hourly charges alone, against an estimate of <!--n results/cost_estimate.json:published.monthly_total_usd -->1.34<!--/n--> for everything else here. On a project with a 20 dollar budget, the default is an accident waiting to happen. It should be zero by default, or synth should say out loud what the default just cost.
- **A budget alarm should be a one-liner.** Setting one means reaching for the raw `aws_budgets.CfnBudget` L1 construct and filling in nested property objects by hand. A budget is the first thing a new builder should be told to add and it is one of the least pleasant things in the library to write.

**Onboarding, zero to hello world.** One night, for a first deploy into an account with no ECS history and no CDK bootstrap in us-east-1: the ECS service-linked role at 00:15 PDT, then the bootstrap, the deploy at 00:21, the image push at 00:26 and the first task run at 00:27. Good if you know CloudFormation, slower if you do not, because the errors are still CloudFormation errors wearing a Python coat. Our account of each step is [`pipeline/infra/README.md`](../pipeline/infra/README.md).

**Would we build with it again.** Yes. Pin the CLI next to the library, export the region, and keep a person at the prompt.

---

## 9. AWS Fargate on Amazon ECS

**What we used it for.** One ingest task per uploaded title: probe the file, run the analyzer per preset, build a hide plan, render a kid-safe rendition, sign the map, and publish nothing verify did not pass. ARM64, <!--n results/aws_deploy_2026-10-09.json:stack.task_cpu_units -->2048<!--/n--> CPU units and <!--n results/aws_deploy_2026-10-09.json:stack.task_memory_mib -->4096<!--/n--> MiB, running the same container image the local pipeline runs, started by a small Lambda from an S3 upload notification. It has run twice, on Oct 9, 2026, on a short calm marker clip.

**What worked well.** The fail closed rule held on AWS. The first run, before the task had a signing key, did the whole analysis in <!--n results/aws_deploy_2026-10-09.json:runs.0.steps_run -->11<!--/n--> steps, failed verify on the missing signature, published <!--n results/aws_deploy_2026-10-09.json:runs.0.published_objects -->0<!--/n--> objects and exited <!--n results/aws_deploy_2026-10-09.json:runs.0.exit_code -->1<!--/n-->, with the reason in its log. The second, with the key, ran <!--n results/aws_deploy_2026-10-09.json:runs.1.steps_run -->12<!--/n--> steps and published its title, in <!--n results/aws_deploy_2026-10-09.json:runs.1.seconds_container_ran -->43.5<!--/n--> seconds of container time, <!--n results/aws_deploy_2026-10-09.json:runs.1.seconds_started_to_stopped -->70.4<!--/n--> from start to stop. Nothing stays running between titles. ARM64 suits work that is ffmpeg and numpy, and the image was built natively on the ARM64 Mac it was written on.

**What needs work.** Two things.

- **No NAT gateway means a public IP.** With `nat_gateways=0` the task runs in a public subnet with a public IP, because otherwise it cannot reach ECR to pull its own image. That is a real trade between cost and network posture, and every tutorial we read either takes the NAT gateway or skips the question. A documented pattern for "cheap, no NAT, still not exposed" would help small builders more than another walkthrough of the expensive default.
- **A first ECS cluster wants its service-linked role first.** ECS had never been used in the account, and a first cluster made by CloudFormation without the ECS service-linked role is reported to fail, which would have rolled back the whole stack, the slow CloudFront distribution included. So we made the role by hand before the bootstrap, at 00:15 PDT, with one `aws iam create-service-linked-role` call. CloudFormation could make it, or say it is missing, before it starts building anything else.

**Onboarding, zero to hello world.** Quick, once the stack exists. It finished at 00:25 PDT, the image was pushed at 00:26, and the first task ran at 00:27, with its log saying what it did.

**Would we build with it again.** Yes. One night and two short runs is all the evidence there is, and both times it did what it was built to do, including refusing.

---

## 10. Amazon S3

**What we used it for.** Two private buckets. `source` takes uploads and is never reachable from the internet; an object under `uploads/` starts one ingest task, and a lifecycle rule ages the raw uploads out, since they are the large and short-lived part. `delivery` holds kid-safe renditions, signed flash maps, posters and trickplay images, and is read only through CloudFront origin access control. After the signed run it held <!--n results/aws_deploy_2026-10-09.json:read_back.delivery_objects -->16<!--/n--> objects for the one title.

**What worked well.** The upload notification to Lambda is the least machinery that could start the pipeline, and it meant we did not need Step Functions or EventBridge for a job that is one step: the second upload landed at 00:34:57 PDT and the starter ran at 00:34:58. Being able to assert "public access is blocked" and "this bucket has a lifecycle rule" against the template is the part we care about most, because for a children's safety product a bucket that is accidentally readable is the worst outcome on the list.

**What needs work.** Nothing that cost us time. The defaults here are sensible: private by default, and block public access on by default in CDK.

**Onboarding, zero to hello world.** Quick. One `aws s3 cp` under `uploads/` was the whole trigger.

**Would we build with it again.** Yes.

---

## 11. Amazon CloudFront

**What we used it for.** Serving the delivery bucket through origin access control, so the bucket itself stays private. The stack adds signed URLs when it is given a public key; the Oct 9 stack was not, so it serves a title to anyone who has its path, and what is there is a kid-safe rendition and a map no TV trusts (section 15). The TV app does not stream from it: its library is compiled into the package.

**What worked well.** `origins.S3BucketOrigin.with_origin_access_control(...)` is one line and it removes the entire class of mistake where a bucket has to be public for a CDN to read it. After the signed run, at 00:36:49 PDT, the title entry, a poster and the HLS master playlist each answered <!--n results/aws_deploy_2026-10-09.json:runs.1.cloudfront_status.title_entry -->200<!--/n-->. A read back at 02:40 got the same, and <!--n results/aws_deploy_2026-10-09.json:read_back.byte_range_status -->206<!--/n--> for a <!--n results/aws_deploy_2026-10-09.json:read_back.byte_range_bytes -->1024<!--/n--> byte range request, which is what HLS playback on a television needs.

**What needs work.** Signed URLs need an RSA 2048 key pair that a hobby project has to create and manage out of band, separate from the Ed25519 key that signs our maps, and the CDK path for it is more fiddly than the rest of the distribution. So the stack treats signing as optional, and the Oct 9 stack went up without it: the delivery bucket is private, and the distribution in front of it is not. Per-viewer signing is written and has never signed a URL.

**Onboarding, zero to hello world.** Quick. The first fetch after the first publish worked without touching the distribution.

**Would we build with it again.** Yes.

---

## 12. AWS Lambda

**What we used it for.** `StartIngest`, a small Python 3.12 function on ARM64, called by the source bucket's upload notification. It reads the bucket and key from the event and makes one `RunTask` call, handing the task the object to read. The CDK adds two functions of its own, for the bucket notification and for emptying the buckets on delete, so the stack lists <!--n results/aws_deploy_2026-10-09.json:stack.resources_by_type.AWS::Lambda::Function -->3<!--/n-->.

**What worked well.** It did its one job both times, one task per upload. Its role may run one task definition in one cluster and pass only that task's two roles, and nothing else. When the update moved the task definition to revision <!--n results/aws_deploy_2026-10-09.json:stack.task_definition_revision -->2<!--/n-->, the CDK repointed the function and its policy in the same change, and the next upload ran the new revision.

**What needs work.** Lambda makes a function's log group on its first run if nothing else has, with no retention, so its logs are kept forever. Our own function's log group is in the stack with a retention. The CDK's two helper functions are not, so they made theirs that way, outside the stack, and `make destroy` will leave both behind. Our teardown deletes them by hand. Suggestion: a retention setting for the log groups Lambda creates on its own.

**Onboarding, zero to hello world.** Quick. The S3 event shape is the one thing to learn, including that the object key arrives URL-encoded.

**Would we build with it again.** Yes.

---

## 13. Amazon DynamoDB

**What we used it for.** The title catalog, on demand, keyed by the source file's SHA-256, with the same fields as the local `catalog.json`. The ingest task writes one row per published title with one `put_item`.

**What worked well.** It held exactly what the publishing rule allows. The refused run wrote <!--n results/aws_deploy_2026-10-09.json:runs.0.catalog_rows -->0<!--/n--> rows and the signed run wrote <!--n results/aws_deploy_2026-10-09.json:runs.1.catalog_rows -->1<!--/n-->, with status <!--n results/aws_deploy_2026-10-09.json:runs.1.catalog_row_status -->verified<!--/n--> and the WCAG preset, and a read back at 03:18 PDT found <!--n results/aws_deploy_2026-10-09.json:read_back.catalog_rows -->1<!--/n--> row. On-demand billing suits a table that is idle almost all the time.

**What needs work.** Nothing that cost us time. One row on one night is not a load test, and we claim nothing about it beyond that it worked.

**Onboarding, zero to hello world.** Quick. The table came with the stack.

**Would we build with it again.** Yes.

---

## 14. Amazon ECR

**What we used it for.** The ingest image. `make deploy` builds it and pushes it to the stack's own repository under two tags, the short commit hash and `latest`, which is the tag the task definition pulls. On Oct 9 that was one image, built from c5724de, <!--n results/aws_deploy_2026-10-09.json:image.size_mb -->279<!--/n--> MB.

**What worked well.** Basic scanning on push finished at 00:26:30 PDT, the same minute the image was pushed, and it saw what our own audit cannot: <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.findings_total -->101<!--/n--> findings, <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.critical -->8<!--/n--> critical and <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.high -->56<!--/n--> high, every one in a Debian package from the base image or the pinned ffmpeg, and none in the Python packages pip-audit covers. Until then nothing had read the image's Debian packages at all.

**What needs work.** Nothing that cost us time in ECR itself. The findings are ours to fix, by rebuilding on a newer base image.

**Onboarding, zero to hello world.** Quick. The repository came with the stack, and a login, a tag and a push put the image there. The one thing to know is the order: the repository does not exist until the stack does, so `make deploy` pushes after deploying, and nothing runs in between because a task only starts on an upload.

**Would we build with it again.** Yes.

---

## 15. Systems Manager Parameter Store and KMS

**What we used it for.** The ingest task's signing key. Without one the task refuses to publish, which the first run showed. So the task was given a throwaway Ed25519 key made for the cloud and for nothing else, kept as the SecureString `/calm-frames/cloud-signing-key` under the account's own `aws/ssm` KMS key. The app does not trust that key, by design, so a map the cloud signs plays on no TV ([`docs/SECURITY.md`](SECURITY.md), "A signing key in the cloud").

**What worked well.** The scoping is exact and was easy to write. The task role may call `ssm:GetParameter` on that one parameter, and `kms:Decrypt` only when the call comes through SSM in us-east-1. Nothing else in the stack has either permission. The signed run read the key when it started and signed with it, and no customer managed KMS key was needed.

**What needs work.** CloudFormation cannot make the parameter. Its `AWS::SSM::Parameter` reference says "Parameters of type `SecureString` are not supported by AWS CloudFormation" (read Oct 9, 2026). So the key went in with one `aws ssm put-parameter` call, outside the stack, and it outlives `make destroy`; our teardown deletes it by hand. For a private key that is arguably the right home, since a template is no place for a secret, but it means the stack's own lifecycle does not cover everything the stack depends on.

**Onboarding, zero to hello world.** Quick. One command stored the key, one context value wired it in, and the update that did it took <!--n results/aws_deploy_2026-10-09.json:stack.update_seconds -->39.9<!--/n--> seconds.

**Would we build with it again.** Yes, for a key the TV does not trust. Not for the release key, which never leaves the machine that holds it.

---

## 16. AWS Budgets

**What we used it for.** A <!--n results/aws_deploy_2026-10-09.json:budget.limit_usd -->20<!--/n--> US dollar monthly budget, made by the stack, with alerts at 50 and 80 percent of actual spend and at 100 percent of forecast, filtered on the cost allocation tag `Project=calm-frames`.

**What worked well.** It is in the same template as everything it watches, so it went up with the stack, and the template tests assert on it.

**What needs work.** The trap, found on Oct 9, 2026: a budget filtered on a user-defined tag counts nothing until that tag is activated as a cost allocation tag in Billing, and a new tag can take up to a day to show up there before it can be activated. At 02:50 PDT, Cost Explorer listed no `Project` tag at all, so that night the budget could not have warned anyone however much was spent. The stack created it without a word about that. Suggestion: warn when a budget filters on a tag that is not active for cost allocation.

**Onboarding, zero to hello world.** One construct to create, then a second step in Billing that cannot be done on day one. Until it is done, the bill is read by hand.

**Would we build with it again.** Yes, and we would put the tag on something on the account's first day, so it can be activated before the first deploy.

---

## 17. Kepler UI Components, `react-native-kepler` and Kepler File System

**What we used it for.** `@amazon-devices/kepler-ui-components` for themed components and the seek bar, `@amazon-devices/react-native-kepler` for ten-foot focus management and the splash screen, `@amazon-devices/kepler-file-system` for reading a measurement run's config out of the app's own data directory.

**What worked well.** `TVFocusGuideView` and the focus model do the hard part of ten-foot navigation, which matters here because a Skip button on a countdown card has to hold focus and has to be reachable in one press. The theme builder is sensible and got out of the way.

**What needs work.** Five things.

- **The build rewrites `manifest.toml` on every build**, adding a `[[needs.module]]` entry for each installed `@amazon-devices` package. So removing a feature means removing its dependency too, or the app goes on declaring it needs a module for a feature it no longer has. It also means anything hand-written in that file lives under a tool that rewrites it, which is why two of our load-bearing blocks have a test that fails if they go missing.
- **`setNativeProps` throws a TypeError on React Native 0.83**, and the error does not say that is why. The fix is a design change to state-driven UI rather than a patch. We banned it with a lint rule on day one, which was preventive rather than a fix, and we would rather the platform explained itself once than that every app learn this the same way.
- **Kepler File System reads a data directory that cannot be written from the host on OS 1.2.** That is exactly the fixture-loading and configuration case it is good for, and there is no path into it: `vega device copy-to` fails with `Permission denied`, `/home` is not on the device, and `vega device run-cmd` runs inside the developer shell's own sandbox. We start runs from a button in the app and fetch the config over HTTP instead.
- **Custom fonts render as the fallback face unless they sit in `assets/fonts`.** Under `assets/raw/fonts` every weight of the bundled Inter faces rendered as the fallback, with no warning; under `assets/fonts` the intended weights appeared (friction log entry 39). The fonts directory and what a fallback render looks like belong in the documentation.
- **Disabling a focused control drops native focus.** Disabling the focused preset, room and chime controls for the length of a save left the remote with nowhere to go. We keep the control in the focus order, report the disabled accessibility state and block its handler instead (friction log entry 40). Moving focus to a neighbour by default would be the platform's answer.

**Onboarding, zero to hello world.** Good.

**Would we build with it again.** Yes.

---

## 18. GitHub Actions

**What we used it for.** Two workflows on `ubuntu-latest`. CI has six jobs: the Vega app (typecheck, lint, jest, the prepared package checks and the hook consumer check), the Python packages, the app's own UI through flashmap, a hardening job with the mutation gate, property tests and the map fuzz corpus, a secret scan, and a check that every published number in every document still matches the file in `results/` it came from. Audit has four more: pip-audit and npm audit, whether the bills of materials are current, the CDK stack and container rules, and an ARM64 build of the ingest image. It is also how we ship the flash check to other people, as a composite action a studio can drop into a repository in one file.

**What worked well.** Composite actions made it cheap to publish our analyzer as something someone else can adopt in one file, which is most of what "open source" means for a tool like this. `actions/setup-node` reading `.nvmrc` and `actions/setup-python` reading `.python-version` keeps CI pinned to the same versions as the laptop with no duplication.

**What needs work.** Two things. First, from Sep 28 to Sep 30 every run on this repository, CI and Audit alike, failed in two or three seconds with no runner assigned and no step executed; GitHub's annotation put it down to a failed account payment or a spending limit rather than code. That is friction entry 35, and it cost the pre-publication CI evidence for the scene-hold tree for those three days. It ended by Oct 5, when the scheduled Audit on main ran real steps, and runners have taken every job since. On dcb27a1, the latest hosted commit, CI passes in all six jobs and Audit fails on npm advisories that have no written exception, bills of materials that have drifted from what the generator writes, and a CDK CLI minimum of 2.1144.0 above the repository's 2.1142.0 pin. Those three are findings on our side, not GitHub's. Since then, in the reviewed local changes, all three bills of materials reproduce byte for byte with the pinned generators, the CDK transitive pins are corrected and the infra tests pass locally; no hosted rerun has happened, so nothing here claims Audit is green, and the advisories are unresolved. Second, for other Vega projects: we found no published way to run the Vega SDK or its virtual device on a hosted runner, and we did not attempt it, since the SDK is a 5.4 GB install and the virtual device is a QEMU guest. So our app job runs `npm install --ignore-scripts` to skip the Shaka build, mocks the player and tests the logic, and everything device-shaped is a local run with its output committed to `results/` and checked in CI from there.

**Onboarding, zero to hello world.** Fast.

**Would we build with it again.** Yes.

---

## Feature requests

**Priority scale.** **Critical** means we could not do the right thing without it. **Important** means it cost real time or forced an undocumented workaround. **Nice-to-have** means it would be better.

| # | Priority | Request | Why |
|---|---|---|---|
| 1 | **Critical** | **A system-wide Fire TV "dim flashing lights" setting**, in Accessibility settings next to the existing options, readable by any app through the accessibility APIs the way `isScreenReaderEnabled` is readable now. | Photosensitivity is a property of the person, not of an app. A child should not have to hope that the app they opened happens to have built protection. A system setting turns this from one app's feature into a platform guarantee and gives every developer a single flag to respect. Apple has one. Fire TV does not. We would delete half of our own settings screen the day this ships, and gladly. |
| 2 | **Critical** | **Document composited simulator capture and make remote automation easy to discover.** | Earlier QMP and macOS capture attempts missed the app picture; a ScreenCaptureKit recording of the simulator window captured picture, captions and sound on Oct 9 and 10, and no Amazon page describes that route. Amazon documents `inputd-cli` for scripted buttons, and on this CLI it works only as `vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'`, not the documented `vega exec` form. A documented recording path and a working documented input command would make accessibility checks reproducible. |
| 3 | **Critical** | **A way to get one frame of what an app drew, from inside the app.** A `takeSnapshot`-style view capture in a Vega module would do it. | Same gap from the other side. React Native 0.83 removed `takeSnapshot` and no `@amazon-devices` package replaces it, so an app cannot check its own rendering at all. Any app with a self-test, a visual regression suite or an accessibility claim about its own UI needs this. |
| 4 | **Important** | **Document the `timeupdate` cadence and `currentTime` resolution of the W3C media player, with a stated guarantee.** | We measured a median gap of <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms and a longest gap of <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms during continuous playback, and a smallest reported step of <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms. Captions, chapter skips, ad insertion and our covers all have to act at a precise media time. Today every developer measures this themselves and each one gets a different answer. |
| 5 | **Important** | **Fix `vega device list`**, which crashes with `Cannot read properties of undefined (reading 'trim')` while a device is connected and every other device command works. | It is the obvious way to script against a device and the first thing a new developer tries. The message gives no clue what to fix. |
| 6 | **Important** | **A way to write into an app's data directory in developer mode**, such as `vega device copy-to --package <id>`. | On OS 1.2 there is no path from the host into another package's sandbox, `/home` is not on the device, and the sample's README documents a workflow that cannot be carried out. Any app that loads a config or a test fixture from its data directory cannot be given one. |
| 7 | **Important** | **Stop the device log dropping an app's output**, or give one level that is never rate limited, or a developer-mode switch that turns suppression off. | A measurement run lost every line the app printed, with the device reporting `Log suppression ended at level [info]. [140] logs were suppressed`. Evidence that a rate limiter can delete is not evidence. We now post run events over HTTP to the machine driving the run, which is a lot of machinery to replace `console.log`. |
| 8 | **Important** | **A readiness signal for the virtual device**, either by holding `"running"` until it is connectable or by adding a separate field. | `status` flips to running about twenty seconds before the device can take a command, so every script has to poll something else, and every developer discovers this the same way. |
| 9 | **Important** | **Document the z-order contract** between `KeplerVideoSurfaceView`, `KeplerCaptionsView` and ordinary React Native views, and state that there is one `KeplerCaptionsView` per process. | Our whole design depends on being able to place a view between the video surface and the captions. It works, and we found out by trying it. A second captions view fails at runtime rather than at build time. |
| 10 | **Important** | **Say in the Media Controls documentation that transport commands bypass the app's own UI**, and show the pattern for validating a target before honouring it. | A spoken "skip forward" arrives at `handleSeek` with nothing on screen involved. It is easy to leave the voice path unguarded while the remote path is careful, and for a safety feature that is the difference between working and not. |
| 11 | **Important** | **Make the `setNativeProps` failure on React Native 0.83 explain itself**, or lint it in the app template. | It throws a TypeError that does not say why, and the fix is a design change rather than a patch. |
| 12 | **Important** | **Report why a playback error happened.** `Category: UNKNOWN, Position: 0.084` is what we got when an HLS stream that had just played failed. | An app cannot decide what to do, or what to tell a viewer, from `UNKNOWN`. For us the fallback is to keep the picture hidden, which is safe and unhelpful. |
| 13 | **Nice-to-have** | **A queued announcement API that reports what it did**, so an app can tell whether speech is available and fall back visually when it is not. | `announceForAccessibility` returns nothing and throws nothing. Our wrapper is written to never fail because there is no way to ask. |
| 14 | **Nice-to-have** | **One requirements table on the install page**, with host OS, CPU architecture, RAM, disk, the virtual device's memory needs, the Intel end-of-support date, and the Node version the samples need. | Today it is split between the install page and the release notes, and the install page says Node 18 while the samples require Node 22. |
| 15 | **Nice-to-have** | **Redirect `/docs/vega/<version>/` and `/docs/vega/latest/`** to the get-started page instead of returning 404. | These are the links most guides give. |
| 16 | **Nice-to-have** | **`NO_MODIFY_RC=true` for the installer**, and write to one startup file per shell. | It appends to `.zshrc`, `.zprofile`, `.bashrc`, `.bash_profile` and `.profile`, so a zsh login shell sources the env file twice, and there is no way to opt out. |
| 17 | **Nice-to-have** | **Quiet progress output when stdout is not a TTY.** | The install log was 2.5 MB of progress frames with the version lines buried in it. |
| 18 | **Nice-to-have** | **Log why the virtual device exited**, and add an exit reason to `vega virtual-device status`. | It stops with nothing written after "Virtual device ready", so a scripted run has to check for it before every step. |
| 19 | **Nice-to-have** | **Swap the `--source` and `--destination` descriptions in `vega device copy-to --help`.** | One-line fix, and it contradicts the command's own examples printed just below. |
| 20 | **Nice-to-have** | **Say in the sample's README that `postinstall` builds Shaka Player and needs a JDK**, and delete the two obsolete snapshot entries that make `jest --ci` exit 1 on a clean checkout. | Both are first-hour experiences for anyone who clones it, and both are a few lines to fix. |
| 21 | **Nice-to-have** | **A published way to build and test a Vega app on a hosted CI runner**, or a plain statement that there is not one and why. | We could not find one, and a 5.4 GB SDK plus a QEMU guest is not something you try speculatively on a runner. Today every Vega project keeps a laptop in the loop for anything device-shaped. |

The first one is the one that matters. The rest of this list is a fortnight of engineering work at Amazon. The first is a policy decision, and it would protect far more children than anything we can ship.
