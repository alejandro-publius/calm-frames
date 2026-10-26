# Product feedback

> **Historical September feedback record.** The [coverage reconciliation](FEEDBACK_RECONCILIATION.md) points to newer public records and identifies what needs owner confirmation. This file is not a record of answers submitted to Devpost. Later AWS deployment and native capture evidence supersede the old claims that neither existed.

Amazon asks five questions about every tool an entry used. This file answers them once per tool, for every tool Calm Frames actually used, and then lists what we would like added, each marked Critical, Important or Nice-to-have.

**The five questions, in the order they appear in each section:**

1. What we used it for
2. What worked well
3. What needs work
4. Onboarding, zero to hello world
5. Would we build with it again

**Two rules this file keeps.** Nothing here is a guess. Every complaint points at something that happened during the build, and the long version of each one, with the exact commands and the exact output, is an entry in [`docs/FRICTION_LOG.md`](FRICTION_LOG.md). Where a tool has not been run yet, the section says so in the first line rather than inventing an opinion: that applies to Fargate, S3 and CloudFront, which exist here as a synthesized CloudFormation template and unit tests, with nothing deployed and no AWS credential used.

Every measured number in this file is marked and checked against `results/` by CI, so a figure that drifts from what was measured fails the build.

**Environment for everything below unless a section says otherwise:** macOS 15.1.1 (24B91) on Apple M1, 16 GB. Vega CLI 1.3.4, Vega SDK 0.24.9914, Vega <!--n results/vvd_smoke.json:device.build -->OS 1.2 (TV Ship/101520710)<!--/n--> on the Vega Virtual Device, Node 22, React Native 0.83, September 2026. No physical Fire TV stick yet, which is why nothing below claims anything about hardware.

## At a glance

| # | Tool | Heaviest complaint | Build with it again |
|---|---|---|---|
| 1 | Vega SDK and Vega CLI | `vega device list` crashes; no input or capture commands | Yes |
| 2 | Vega Virtual Device | The screen cannot be captured at all, and playback is not steady | Yes for development, no for evidence |
| 3 | `vega-video-sample` | A failed load is silent; the README documents a workflow OS 1.2 cannot do | Yes, and we are sending a fix back |
| 4 | `react-native-w3cmedia` | `timeupdate` cadence and `currentTime` resolution are undocumented | Yes, with that documented |
| 5 | Vega Media Controls | A voice seek can move the playhead without the app's UI, and that is not called out | Yes |
| 6 | KeplerCaptionsView | The z-order contract is not written down anywhere | Yes |
| 7 | The accessibility APIs | No system signal for photosensitivity, and no capture to check our own screens with | Yes |
| 8 | AWS CDK | The `ec2.Vpc` default is a NAT gateway per availability zone | Yes |
| 9 | AWS Fargate on ECS | Nothing deployed yet, so this is a design-stage answer | Expect so |
| 10 | Amazon S3 | Nothing deployed yet | Yes |
| 11 | Amazon CloudFront | Nothing deployed yet; signed URLs need a key we do not have | Yes |
| 12 | Kepler UI Components, react-native-kepler, Kepler File System | The build rewrites `manifest.toml`; the data directory cannot be written from the host | Yes |
| 13 | GitHub Actions | Nothing that cost us time | Yes |

---

## 1. Vega SDK and Vega CLI

**What we used it for.** Everything. Vega SDK 0.24.9914 and Vega CLI 1.3.4 built, installed, launched and log-streamed the app, and ran the virtual device. Calm Frames is a Vega app end to end.

**What worked well.** The install is one non-interactive command and it finished in 4 minutes 18 seconds. `vega run-app`, `vega device install-app` and `vega device start-log-stream` are reliable, and they are the backbone of every measurement run in this submission. The virtual device boots a real OS 1.2 image, so platform behaviour showed up early rather than on hardware. `vega device info` and `vega device is-connected` are dependable enough to script around, which mattered once we found that the obvious command is not.

**What needs work.** Six things, all in the friction log with their output.

- `vega device list` crashes with `Cannot read properties of undefined (reading 'trim')` while a device is connected and every other device command works against that same device at that same moment. It is the obvious way to script against a device and it is the first thing a new developer tries.
- `vega virtual-device status` reports `"running":true` about twenty seconds before the device can take a command, so every script has to poll `vega device is-connected` instead and every developer finds this out the same way.
- The same command exits non-zero before the first start, where "no instance yet" is a normal state, and prints the internal command line with it.
- The virtual device sometimes exits with nothing written to its own log after "Virtual device ready", so a scripted run has to check for the device before every step.
- There is no `vega device key` and no `vega device screenshot`. See section 2; for an accessibility project this is the one that hurt.
- `vega device copy-to --help` has its `--source` and `--destination` descriptions the wrong way round, contradicting its own examples printed immediately below.

Two smaller ones, both about the installer: with stdout redirected to a file it writes progress frame by frame, so our install log was 2.5 MB holding 39,131 `Extracted Files: n/39131` lines, and it appends `source ~/vega/env` to every shell startup file it can find, with no way to opt out.

**Onboarding, zero to hello world.** Good once you find the right page, and the right page is hard to find. `https://developer.amazon.com/docs/vega/0.24/` is a 404, and so is `/latest/`. System requirements are split between the install page and the release notes, and the install page says Node 18 while the samples declare Node 22 or later, so following the install page gives you a Node the samples reject. From a working shell to the sample playing video on the virtual device was under a day, and most of that day went on documentation rather than tools.

**Would we build with it again.** Yes. What we hit are rough edges in the CLI rather than limits in the platform, and every one of them had a way around it. The missing input and capture commands are the only ones that would change the answer if they stayed missing, because an accessibility app has to be able to check its own screens.

---

## 2. Vega Virtual Device

**What we used it for.** All development, and every measurement in this submission that is not on hardware: the smoke test, the layering run and the cover timing runs. It is also where the app was driven from a script, over the QEMU control socket, because the CLI cannot press buttons.

**What worked well.** It is a real OS 1.2 image on ARM, and the app that runs there is the app that will run on the stick. It let the whole project start before any hardware arrived, which on a two-month build is most of its value. The recorded smoke run played a Blender title over HLS with <!--n results/vvd_smoke.json:segment_fetches_during_play -->8<!--/n--> segment fetches during <!--n results/vvd_smoke.json:play_seconds -->40<!--/n--> seconds of play, <!--n results/vvd_smoke.json:streaming_errors -->0<!--/n--> streaming errors and <!--n results/vvd_smoke.json:crash_lines -->0<!--/n--> crash lines, at a peak of <!--n results/vvd_smoke.json:peak_pss_kb -->353178<!--/n--> kB.

**What needs work.** Three things, and the first is the serious one.

- **The screen cannot be captured, by any route we could find.** `vega device` has no screenshot command. The device is QEMU, so we went to its QMP socket: key injection works, and `screendump` returns black, because the app draws on a GPU layer the capture does not see. Capturing the window from macOS does not work either: a full screen grab with the virtual device frontmost returned the desktop behind it. So we cannot look at our own screens at all, and every piece of playback evidence has to be reconstructed from device logs. For an app whose whole purpose is to keep flashing off a screen, not being able to see the screen is the single worst thing in this list.
- **Playback is not steady.** Of four runs in one afternoon, two played cleanly, one failed with `Category: UNKNOWN, Position: 0.084` on the same HLS stream, and one never started. A later timing measurement needed 22 app launches to collect <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n--> usable trials. The error carries a category of `UNKNOWN` and a position, and nothing else to act on.
- **The device backgrounds an app nobody is touching**, and a backgrounded app stops playing. A person holding a remote never hits this. A camera rig with nobody pressing anything hits it every time, so our runs press a key the app does not bind, every few seconds, to keep the device awake without touching playback.

**Onboarding, zero to hello world.** Quick to start and confusing to script against, because the readiness signal is not one. Budget time for two discoveries nothing warns you about: that `status` is not readiness, and that the black screenshot you are looking at is black for a reason rather than because the app failed.

**Would we build with it again.** Yes for development. No for evidence. Every number we take from it is labelled a virtual device number, and the gates that matter are filmed at 240 fps against a real stick.

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

**What needs work.** Four things.

- **`timeupdate` cadence is not documented, and it is not regular.** In one recorded run the median gap was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms, the shortest <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.min -->75<!--/n--> ms and the longest <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms, while the clip kept playing throughout. A feature that reacts to `timeupdate` would have been five seconds late. Our whole design follows from that number: the cover runs on a wall clock re-anchored to media time at every report, and the price is drift, which reached <!--n results/vvd_timeupdate_stats.json:worst_wall_clock_drift_ms -->2756<!--/n--> ms in that same gap.
- **`currentTime` resolution is not documented either.** The smallest step we saw reported was <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms. Anything that must act at a precise media time needs a stated guarantee for both of these, not a number each developer measures for themselves and gets a different answer to.
- **A plain MP4 over HTTP does not start**, where the same content over HLS does, and nothing says why. Two things had to be true before our marker clip would play at all: package it as HLS, and have the test server answer byte ranges. Python's own `SimpleHTTPRequestHandler` ignores the `Range` header and returns the whole file with a 200, and the player treats that as a broken source with no error anywhere.
- **A stream with no audio track pauses a few seconds in.** We searched the sample for anything that waits on audio and there is nothing, so this comes from below it. Every test clip we generate now carries a silent AAC track.

**Onboarding, zero to hello world.** Good, because the sample does it for you. Hard from the API surface alone, because the surface handle and caption handle lifecycle is not obvious and the ordering matters.

**Would we build with it again.** Yes. We would ask for the documented `timeupdate` and `currentTime` statement first, because an accessibility feature that has to be on screen before a specific frame cannot rest on undocumented timing. One more thing we would ask for: something that tells the app how long the JavaScript thread was unavailable. Our own measurement found a cover going on <!--n results/gate1_software_vvd.json:worst_lead_ms -->-86<!--/n--> ms relative to its marker, which is a thread pause of about a third of a second, and we can only see that after the fact.

---

## 5. Vega Media Controls, `@amazon-devices/kepler-media-controls`

**What we used it for.** System and voice transport. This is where an Alexa "skip forward" arrives, which for us makes it a safety surface rather than a convenience: a spoken command can move the playhead into a part of a video we are supposed to be hiding.

**What worked well.** Subclassing `KeplerMediaControlHandler` and overriding only the methods you care about is the right shape, and handing the subclass to `setMediaControlFocus` made it one call to wire up. Our `SafeMediaControlHandler` overrides every transport callback, calls none of `super`, and routes all of them through the same seek function the on-screen controls use, which covers the picture first and only then moves. That was easy to express.

**What needs work.** Two things.

- **The design deserves a warning in the documentation.** `handleSeek` and friends can move the playhead with the app's own UI uninvolved. That is correct behaviour, and it means an app that has to validate a target position must funnel every one of these through its own logic. It is easy to leave the voice path unguarded while the remote path is careful, and nothing tells you.
- **The manifest opt-in is load bearing and easy to lose.** The `IMediaPlaybackServer` extras block with `command_options` and the `AdvancedSeek` feature is what makes these commands reach the app at all. Without it our handler is never called and a spoken "skip forward" goes straight past the guard, with no error and no log line. Since the build rewrites `manifest.toml` on every build (section 12), we have a test that fails if that block goes missing. That test should not have to exist.

**Onboarding, zero to hello world.** Quick, through the sample. Slow from the documentation, because the manifest half and the code half are in different places.

**Would we build with it again.** Yes. For a voice-first television platform this is the right abstraction, and `AdvancedSeek` carrying a position rather than a direction is what lets us check a target before honouring it.

---

## 6. KeplerCaptionsView

**What we used it for.** Captions, and in our case the reason a hidden segment is still followable. It sits above our cover, so the words carry on over a black picture and a child does not lose the story while the flashing part is hidden.

**What worked well.** The handle-based lifecycle, `onCaptionViewCreated` and `setCaptionViewHandle` with `clearCaptionViewHandle` on the way out, is clear and hard to get wrong once you have seen it done. The view composites above ordinary React Native views, which is the fact our whole design rests on: the cover is drawn between the video surface and the captions view.

**What needs work.** Two things, both documentation.

- **The z-order contract is not written down.** Video surface at the bottom, our own views in the middle, captions on top. We rely on it completely and we found it by trying it. It should be a stated contract, because if it ever changed, an accessibility layer built on it would fail silently and look like a rendering glitch.
- **One captions view per process should be said loudly.** We designed around it from the start, so we never hit it, and an app that adds a second one finds out at runtime rather than at build time. A note in the API reference costs nothing.

One thing we could not check yet, and will not pretend we did: whether captions stay readable over the cover on a real screen. The layering test exists and the harness runs, but the virtual device cannot be photographed, so the verdict in `results/vvd_layering_rehearsal.json` is <!--n results/vvd_layering_rehearsal.json:layering.verdict -->inconclusive<!--/n-->. That is a question for the stick and a pair of eyes.

**Onboarding, zero to hello world.** Fine through the sample. Not obvious from the API alone.

**Would we build with it again.** Yes.

---

## 7. The accessibility APIs: VoiceView, `AccessibilityInfo` and the accessibility privilege

**What we used it for.** Every card Calm Frames shows is spoken as well as drawn. A countdown before a hidden part, the fact that a part was hidden, and why. We use two mechanisms together: `accessibilityLiveRegion="polite"` on the card itself, so a screen reader watching the tree reads it when it appears, and `AccessibilityInfo.announceForAccessibilityWithOptions(text, { queue: true })` to push the same words without interrupting whatever is already being read. The app declares `com.amazon.devconf.privilege.accessibility` under `[wants]` in the manifest.

**What worked well.** The React Native accessibility surface is there and it behaves the way a React Native developer expects: `accessibilityLabel`, `accessibilityRole`, `accessibilityLiveRegion` and the announcement API all work, so knowledge carries over from mobile. `announceForAccessibilityWithOptions` with `{ queue: true }` is the right primitive for this job. A child hearing "flashing part coming up" cut off halfway is worse than hearing it a beat later, and having queueing available rather than only the interrupting form is what makes the polite version possible.

**What needs work.** Four things, and the first is the feature request that leads this whole submission.

- **There is no system-wide signal for photosensitivity.** A television knows the volume the household likes, the caption style they prefer and whether a screen reader is on. It does not know that the person in front of it must not be shown flashing. So every app has to invent its own protection, and a child's safety depends on which app they happened to open. Apple ships "Dim Flashing Lights" at the system level. Fire TV should too, and it should be readable by any app, in the same way `AccessibilityInfo.isScreenReaderEnabled()` is readable now.
- **Announcements are fire and forget.** `announceForAccessibility` returns nothing and throws nothing. There is no way to ask whether VoiceView is running, whether the announcement was spoken, or whether it was dropped, so an app cannot fall back to something visible when speech is unavailable. Ours is written to never throw and to never block the cover, which is the safe shape, and it is a shape forced by not being able to ask.
- **The privilege is quiet when it is missing.** Without `com.amazon.devconf.privilege.accessibility` in the manifest, no announcement is made and nothing says why. Since the build rewrites `manifest.toml` (section 12), we hold that line in place with a test.
- **There is no way to check your own screens.** This is section 2's capture problem seen from the accessibility side. WCAG 2.3.1 applies to an app's own interface, not only to the video it plays, and on Vega today a developer cannot get a single frame of what their app drew, from inside the app or outside it. React Native 0.83 has no `takeSnapshot`, no `@amazon-devices` package offers a view capture, and the platform's own capture returns black. We had to make the app record what it paints, screen by screen, and turn that record into a video our analyzer could read, which is a real answer but it is not a photograph of the screen.

**Onboarding, zero to hello world.** Good if you arrive from React Native. The manifest privilege is the one piece that is not where you expect it, and it is the piece that silently disables everything else.

**Would we build with it again.** Yes. The pieces we needed were there, and the gap is not in the API surface, it is that the platform has no idea a viewer is photosensitive.

---

## 8. AWS CDK

**What we used it for.** The whole ingest stack in Python CDK: two S3 buckets, a DynamoDB table, an ECR repository, an ARM64 Fargate task definition, a Lambda trigger, a CloudFront distribution, a VPC, a budget alarm, log retention, cost tags and a GitHub OIDC deploy role. It synthesizes and is unit tested against the synthesized template.

**What worked well.** Asserting on the synthesized template is the cheapest safety net on this project. It let us be confident about the two things that would quietly cost money or leak data, zero NAT gateways and a budget that tells someone, without deploying anything, which matters because we are not allowed to deploy until the account is ready. Being able to test infrastructure the same way we test code, in the same CI job, is the part we would keep.

**What needs work.** Two things.

- **The `ec2.Vpc` default is one NAT gateway per availability zone**, which is roughly 65 to 100 US dollars a month and would have been the largest line on a hobby project's bill by a wide margin. On a project with a 20 dollar budget alarm, the default is an accident waiting to happen. It should be zero by default, or synth should say out loud what the default just cost.
- **A budget alarm should be a one-liner.** Setting one means reaching for the raw `aws_budgets.CfnBudget` L1 construct and filling in nested property objects by hand. A budget is the first thing a new builder should be told to add and it is one of the least pleasant things in the library to write.

**Onboarding, zero to hello world.** Good if you know CloudFormation, slower if you do not, because the errors are still CloudFormation errors wearing a Python coat.

**Would we build with it again.** Yes.

---

## 9. AWS Fargate on Amazon ECS

**Nothing is deployed and no AWS credential has been used, so this is a design-stage answer.** The task definition synthesizes and is unit tested. The image has not been built or run. We will not write an operational opinion we have not earned.

**What we used it for.** One ingest task per uploaded title: probe the file, run the analyzer per preset, build a hide plan, render a kid-safe rendition, sign the map, and refuse to publish anything verify did not pass. ARM64, running the same container image the local pipeline runs, started by a small Lambda from an S3 upload notification.

**What worked well, as far as we can tell without running it.** The shape fits the workload. Ingest is bursty and quiet in between, and there is nothing to keep alive between titles. Pinning the task to ARM64 costs about 20 percent less than x86 for work that is ffmpeg and numpy, both of which have good aarch64 builds, and it matches the machine this was written on, so the image that gets tested is the image that gets pushed. Writing the task definition in CDK and asserting on it meant the CPU, the memory, the log group and the retention could be reviewed before anything existed.

**What needs work.** With `nat_gateways=0` the task runs in a public subnet with a public IP, because otherwise it cannot reach ECR to pull its own image. That is a real trade between cost and network posture, and every tutorial we read either takes the NAT gateway or skips the question. A documented pattern for "cheap, no NAT, still not exposed" would help small builders more than another walkthrough of the expensive default.

**Onboarding, zero to hello world.** Not answerable yet.

**Would we build with it again.** Expect so, and we will say for certain after the first deploy.

---

## 10. Amazon S3

**Nothing is deployed.** Both buckets exist as synthesized CloudFormation and as assertions in a unit test.

**What we used it for.** Two private buckets. `source` takes uploads and is never reachable from the internet; a lifecycle rule ages the raw uploads out, since they are the large and short-lived part. `delivery` holds kid-safe renditions, signed flash maps, posters and trickplay images, and is read only through CloudFront origin access control.

**What worked well.** The upload notification to Lambda is the least machinery that could start the pipeline, and it meant we did not need Step Functions or EventBridge for a job that is one step. Being able to assert "public access is blocked" and "this bucket has a lifecycle rule" against the template is the part we care about most, because for a children's safety product a bucket that is accidentally readable is the worst outcome on the list.

**What needs work.** Nothing that cost us time at design stage. The defaults here are sensible: private by default, and block public access on by default in CDK.

**Onboarding, zero to hello world.** Not answerable yet, and we would expect it to be quick.

**Would we build with it again.** Yes.

---

## 11. Amazon CloudFront

**Nothing is deployed.** The distribution exists as synthesized CloudFormation and as assertions in a unit test.

**What we used it for.** Serving the delivery bucket through origin access control, so the bucket itself stays private, with signed URLs when a public key is configured. The app needs range requests and reasonable latency for HLS playback on a television.

**What worked well.** `origins.S3BucketOrigin.with_origin_access_control(...)` is one line and it removes the entire class of mistake where a bucket has to be public for a CDN to read it. That is the right default and it is easy to get right.

**What needs work.** Signed URLs need a key pair that a hobby project has to create and manage out of band, and the CDK path for it is more fiddly than the rest of the distribution. Our stack therefore treats signing as optional and works without it, which is the honest state: today the delivery content is private to the bucket and served through the distribution, and per-viewer signing is written but not exercised.

**Onboarding, zero to hello world.** Not answerable yet.

**Would we build with it again.** Yes.

---

## 12. Kepler UI Components, `react-native-kepler` and Kepler File System

**What we used it for.** `@amazon-devices/kepler-ui-components` for themed components and the seek bar, `@amazon-devices/react-native-kepler` for ten-foot focus management and the splash screen, `@amazon-devices/kepler-file-system` for reading a measurement run's config out of the app's own data directory.

**What worked well.** `TVFocusGuideView` and the focus model do the hard part of ten-foot navigation, which matters here because a Skip button on a countdown card has to hold focus and has to be reachable in one press. The theme builder is sensible and got out of the way.

**What needs work.** Three things.

- **The build rewrites `manifest.toml` on every build**, adding a `[[needs.module]]` entry for each installed `@amazon-devices` package. So removing a feature means removing its dependency too, or the app goes on declaring it needs a module for a feature it no longer has. It also means anything hand-written in that file lives under a tool that rewrites it, which is why two of our load-bearing blocks have a test that fails if they go missing.
- **`setNativeProps` throws a TypeError on React Native 0.83**, and the error does not say that is why. The fix is a design change to state-driven UI rather than a patch. We banned it with a lint rule on day one, which was preventive rather than a fix, and we would rather the platform explained itself once than that every app learn this the same way.
- **Kepler File System reads a data directory that cannot be written from the host on OS 1.2.** That is exactly the fixture-loading and configuration case it is good for, and there is no path into it: `vega device copy-to` fails with `Permission denied`, `/home` is not on the device, and `vega device run-cmd` runs inside the developer shell's own sandbox. We start runs from a button in the app and fetch the config over HTTP instead.

**Onboarding, zero to hello world.** Good.

**Would we build with it again.** Yes.

---

## 13. GitHub Actions

**What we used it for.** Four jobs on `ubuntu-latest`: the Vega app (typecheck, lint, jest), the Python packages, a secret scan, and a check that every published number in every document still matches the file in `results/` it came from. It is also how we ship the flash check to other people, as a composite action a studio can drop into a repository in one file.

**What worked well.** Composite actions made it cheap to publish our analyzer as something someone else can adopt in one file, which is most of what "open source" means for a tool like this. `actions/setup-node` reading `.nvmrc` and `actions/setup-python` reading `.python-version` keeps CI pinned to the same versions as the laptop with no duplication.

**What needs work.** Nothing that cost us time. One thing worth saying for other Vega projects: we found no published way to run the Vega SDK or its virtual device on a hosted runner, and we did not attempt it, since the SDK is a 5.4 GB install and the virtual device is a QEMU guest. So our app job runs `npm install --ignore-scripts` to skip the Shaka build, mocks the player and tests the logic, and everything device-shaped is a local run with its output committed to `results/` and checked in CI from there.

**Onboarding, zero to hello world.** Fast.

**Would we build with it again.** Yes.

---

## Feature requests

**Priority scale.** **Critical** means we could not do the right thing without it. **Important** means it cost real time or forced an undocumented workaround. **Nice-to-have** means it would be better.

| # | Priority | Request | Why |
|---|---|---|---|
| 1 | **Critical** | **A system-wide Fire TV "dim flashing lights" setting**, in Accessibility settings next to the existing options, readable by any app through the accessibility APIs the way `isScreenReaderEnabled` is readable now. | Photosensitivity is a property of the person, not of an app. A child should not have to hope that the app they opened happens to have built protection. A system setting turns this from one app's feature into a platform guarantee and gives every developer a single flag to respect. Apple has one. Fire TV does not. We would delete half of our own settings screen the day this ships, and gladly. |
| 2 | **Critical** | **`vega device screenshot` that captures the composited output**, and `vega device key` for remote input. | There is no supported way to see what an app drew or to press a button from a script. For an accessibility app this is not a convenience: WCAG 2.3.1 applies to our own interface and we cannot look at it. Our workaround goes through QEMU's QMP socket, which is undocumented, virtual-device only, and returns black for anything drawn on the GPU layer. |
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

---

## For Lane H: what this changes in other documents

This file and the friction log grew past what other documents say about them. None of these files belong to this lane, so here is the list rather than the edit.

| File and line | What it says now | What is true |
|---|---|---|
| `docs/SUBMISSION.md` section 9 | Product feedback for nine tools, written inline | Thirteen tools are answered here, including the accessibility APIs, Fargate, S3 and CloudFront, which section 9 did not cover. Section 9 can either absorb this file or link to it |
| `docs/SUBMISSION.md` section 12 | Fourteen feature requests | Twenty-one here, in the same priority scale. The three Critical ones are the system setting and the two capture gaps |
| `docs/SUBMISSION.md` section 13 | "eleven entries: four Medium and seven Low" | Thirty-three entries: five High, thirteen Medium, fifteen Low. Twenty-eight are on Amazon's surface and five are the wider toolchain |
| `docs/SUBMISSION.md` line 77 | "alongside seven more" | Alongside thirty more |
| `docs/SUBMISSION.md` section 14, item 10 | "Read the eleven friction entries" | Read the thirty-three |
| `docs/SUBMISSION.md` section 11.4 | The upstream half says two tests | Three tests now, and both guards were seen to fail |
| `docs/PLAN.md` lines 62 to 63 | Nine tools, fourteen requests, eleven entries | As above |
| `docs/VIDEO_SCRIPT.md` line 60 | Calls the `vega device list` crash "feature request 4" | It is request 4 in `docs/SUBMISSION.md` section 12 and request 5 in this file. If section 12 adopts this list, that line needs the new number, or better, the name instead of a number |

Two things that did not change. Friction entries 1 to 11 keep their numbers, so `README.md` line 332 pointing at entries 6 and 8 is still right, and `docs/VIDEO_SCRIPT.md` pointing at entry 6 is still right.
