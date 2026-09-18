# Devpost submission, ready to paste

Every field for **Build, Ship, Shape: Amazon Developer Hackathon**, Fire TV track, with the Open Source and AWS Builder mini challenges.

**How to use this file.** Each section below is one Devpost field. Copy the block under the heading. Anything marked **NEEDS ALEX** cannot be filled in by the build and is listed again at the end.

**Re-check before pasting.** The Devpost form's exact field names and character limits should be read off the live form on the day, because this file is written from the build plan rather than from the form. Submit Thursday October 22 2026. The deadline is Friday October 23 at 12:00 PT.

---

## 1. Project name

```
Calm Frames
```

## 2. Tagline

```
A verified safety layer for Fire TV that hides flashing before it starts, for kids with photosensitive epilepsy.
```

Alternates, if the form wants something shorter:

```
Every frame checked before it plays. The picture hides, the sound and captions keep going.
```

```
Fire TV kid mode for photosensitive epilepsy: verified before play, hidden before the flash.
```

## 3. Description

Devpost splits this into headed sections. They are written out separately below so each one can be pasted into its own box.

### Inspiration

About 3 percent of people with epilepsy are photosensitive, and it is more common in children and adolescents. Flashing at roughly 5 to 30 times a second is the most likely trigger. A 2025 Epilepsy Foundation working group told media designers to avoid bright flashing in the 10 to 20 Hz range.

Now picture a twelve year old at a sleepover picking a movie on the living room television, with no adult sitting next to her to screen it first. Nothing on that television knows what is in the next ninety minutes. Other platforms have partial answers: Apple has a Dim Flashing Lights setting, there are desktop filters, and there are research prototypes that detect flashes and overlay them live. What none of them do is check the whole title before it is allowed to play, and then guarantee that every way of jumping into it is safe.

That is the gap Calm Frames fills, and Fire TV is where it belongs, because the television is the screen a child uses without supervision.

### What it does

Calm Frames is a verified safety layer, and it is never a video player.

Every frame of a title is measured before that title can appear in kid mode. The result is an Ed25519 signed flash map, bound to the file's SHA-256, that lists each interval that goes over the WCAG 2.2 general flash or red flash threshold. A verify step blocks publishing: a title whose rendition still contains a violation, whose map is tampered with, whose hash is wrong, or whose poster was taken from a flagged moment, does not reach kid mode at all.

During playback the app hides each flagged segment before it starts. The picture goes, the sound keeps going and the captions keep running above the cover, so the story stays followable. Afterwards the app says what it hid.

It adapts to the household. A parent gives the television diagonal and the seat distance behind a PIN, and picks a preset. The room rule then adds a second area window for that room's ten degree visual field. A household setting can only ever add hides. It cannot make Calm Frames weaker than WCAG.

Voice, D-pad and on-screen cards all run through one seek function. If the target lands inside a flagged interval or its guard band, the picture is covered first and the seek happens second. An Alexa "skip forward" that would drop the playhead into the middle of a flagged scene is as safe as pressing right on the remote.

And any Vega video app can add the same protection with a small hook, while any studio can check its own content before publishing with the open-source analyzer and its GitHub Action.

Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device.

### How we built it

Four pieces.

**flashmap**, an Apache-2.0 Python package, measures video against WCAG 2.2 Success Criterion 2.3.1: both the general flash rule and the red flash rule, with the saturated red test done in the CIE 1976 UCS chromaticity diagram. It slides a one second window to every position for the three-flashes-a-second limit, and slides a ten degree area window for the 25 percent rule, because the specification says "any 10 degree visual field" rather than a fixed grid. It reads real container timestamps, so variable frame rate input comes out right. It detects letterbox and pillarbox so area is measured on the picture rather than on the bars. Chunked analysis gives byte for byte the same map as a whole file run, which is a property test rather than a claim. Every threshold in the code is quoted, with a link, in `flashmap/docs/SPEC_SOURCES.md`, and the three things that could not be verified from a primary source are named there and are not used.

**The pipeline** takes a title through probe, analyze per preset, hide plan, kid-safe rendition, trickplay, posters taken only from the safe rendition, signing, and a catalog entry. It is idempotent and keyed by the source hash. `pipeline/verify.py` is the gate, and it was mutation tested: a violation left in a rendition, a violation under the modelled cover, a tampered map, a wrong hash and a poster from a flagged moment all fail it.

**The Fire TV app** is built on `AmazonAppDev/vega-video-sample` at tag `v0.24-RN83`. Playback stays on `@amazon-devices/react-native-w3cmedia`. The cover is a plain React Native view between the video surface at zIndex 0 and `KeplerCaptionsView` at zIndex 2, driven by state rather than `setNativeProps`, which throws on React Native 0.83.

**The infrastructure** is an AWS CDK stack with zero NAT gateways, a 20 dollar budget alarm, private buckets and a GitHub OIDC role.

The hardest design decision came out of a measurement. The player's own position reports are irregular: in a recorded run the longest gap between two of them was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms while the clip kept playing. A cover that waited for a position report before acting would have been that late. So the scheduler runs on a wall clock re-synced to media time at every report, and anything that makes the playhead uncertain, including a stall, a seek, a pause or the app being backgrounded, hides the picture at once instead of trusting the estimate. Amazon does not document either figure, so we measured them.

### Challenges we ran into

The virtual device has no supported way to press a remote button or capture the screen, so we drive it through QEMU's QMP socket. Key injection works. Screenshots come back black, because the app renders on a GPU layer the capture does not see, so playback evidence comes from device logs rather than pictures. `vega device list` crashes with a TypeError while a device is running, so every script uses `vega device info` and `vega device is-connected` instead. And on OS 1.2 there is no path from the host into another package's data directory, although the sample's README documents one, so a measurement run is started from a button inside the app or from a config the app fetches over HTTP. Every one of those is in the friction log with its exact output, alongside seven more.

The real one is this. We do not have a cover lead time number, and for a while we thought we did. A rehearsal run appeared to show every marker covered in time with a worst lead of 449 ms. It was wrong. The player in that run never got past about a quarter of a second, while the cover scheduler, which runs on a wall clock by design, kept advancing its own estimate and fired every cover on time against that estimate. The analysis agreed with itself. A stricter second script refused to count any of it, which is how it surfaced, and both scripts now require a position report from the player before a lead time is counted. Those numbers were withdrawn from everywhere they appeared, and the retraction is written out in `docs/GATES.md`. Run again on a packed clip under the new rule, the measurement gave 49 usable trials with 48 covered in time, a median lead of 488 ms, and one cover that went on 86 ms after its marker started because the JavaScript thread stalled. We kept that last one in the README rather than rounding it away, because it is the thing that tells us the guard band is not yet known to be wide enough. The real measurement is 50 trials filmed at 240 frames a second against a real Fire TV stick, and it has not happened yet.

### Accomplishments we are proud of

Three.

The first is that nothing here is asserted. Every number in the README, in this text and in the video is written as a marker pointing at a file in `results/`, a script checks that they still match, and CI fails the build if any of them drifts. A number nobody can trace is worse than no number, so rows with no measurement behind them are left empty.

The second is that the failures are in the record, including the one that cost us our best-looking number. We withdrew a timing result that our own analysis had blessed, because a second and stricter script would not count it, and the withdrawal is written out in full rather than quietly deleted. The layering run came back inconclusive because playback did not run in that take, and it is published as inconclusive. Four of twenty screening clips could not be decoded, and that is in the results file. Two titles were refused by verify, which is verify doing its job.

The third is that nobody on this project watched a strobe at full speed to build it. Hazard files are inspected as luminance plots, conformance clips are made and measured and deleted in the same job, and prevented exposure is computed from the flash map rather than demonstrated by playing flashing content with the filter off.

### What we learned

That the safety property is a scheduling problem, not a detection problem. Detecting a flash is arithmetic on pixels and it is testable offline. Being *on the screen before the flash*, through seeks, stalls, rate changes and an app coming back from the background, is where the work is, and it is the part a specification does not help with.

And that a fail-closed default changes what you build. Once a missing, stale, unsigned, unparseable or wrong-hash map means the picture stays hidden, every question about error handling answers itself.

### What is next

Filming the real gates on the stick. Self-filmed red strobe footage, because no free source we found has a saturated red strobe, under the safety rules. The upstream pull request. And the feature request that would help most: a system-wide Fire TV setting for dimming flashing lights, so this protection is not one app's job.

### Built with

```
Vega SDK 0.24 · Vega CLI · React Native 0.83 · TypeScript · @amazon-devices/react-native-w3cmedia · Shaka Player · Kepler Media Controls · KeplerCaptionsView · Kepler UI Components · Kepler File System · Python 3.12 · PyAV / FFmpeg · Ed25519 · pytest · Jest · AWS CDK · Amazon S3 · Amazon DynamoDB · AWS Fargate · AWS Lambda · Amazon CloudFront · Amazon ECR · AWS Budgets · GitHub Actions
```

## 4. Track

```
Fire TV
```

## 5. Mini challenges entered

```
Open Source (primary)
AWS Builder
```

## 6. Repository URL

```
https://github.com/alejandro-publius/calm-frames
```

**NEEDS ALEX:** the repository is private today and goes public during the final checks on October 21, because the rules need it public with the licence visible at submission. Confirm it is public, and that the licence shows in GitHub's About box, before pasting this.

## 7. Video URL

```
NEEDS ALEX
```

**NEEDS ALEX:** film and upload the demo, then paste the link. The script is in [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md), timed and under 3:00. Three checks before pasting: the link works while logged out, the final video file passes `flashmap check` with zero violations and that result is committed, and the on-screen wording is "reduces exposure to flashing above published limits in the videos it plays; not a medical device".

## 8. Testing instructions

```
Calm Frames runs on a Fire TV stick with Vega OS 1.2 in developer mode, and on
the Vega Virtual Device. Everything below is also in the repository README.

WHAT YOU NEED
  Vega SDK 0.24.9914 and Vega CLI 1.3.4
  Node 22 (the repo has a .nvmrc)
  Python 3.12 (the repo has a .python-version)
  JDK 21, for `npm install` only: the Shaka Player build runs in postinstall

SET UP
  source ~/vega/env
  eval "$(fnm env)" && fnm use
  export JAVA_HOME=/opt/homebrew/opt/openjdk@21

RUN IT ON THE VIRTUAL DEVICE
  cd app
  npm install
  npm run build:debug
  cd ..
  python3 eval/vvd_smoke.py --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg

  This starts the virtual device if it is not running, installs and launches the
  app, drives the remote, plays a title, and writes results/vvd_smoke.json.

  Two notes. `vega virtual-device status` says running before the device is
  usable, so wait for `vega device is-connected`. And `vega device list` crashes
  on this SDK, so use `vega device info`.

RUN IT ON A STICK
  cd app && npm install && npm run build:debug
  vega device is-connected
  vega run-app app/build/armv7-debug/calm-frames-app_armv7.vpkg

  Use a debug build. Release builds strip console.log, and the evidence for a
  measurement run is in the log.

PARENT AREA
  The parent area is behind a PIN. Demo PIN: NEEDS ALEX.

CHECK ANY VIDEO YOURSELF, WITHOUT THE APP
  python -m pip install -e 'flashmap[dev]'
  python -m flashmap check YOUR_VIDEO.mp4 --profile wcag

  Exit code 0 means below the WCAG general and red flash thresholds, 1 means
  over them, 2 means flashmap could not tell. Treating 2 as a pass is a hole.

CHECK OUR NUMBERS
  python eval/readme_sync.py --check

  Every number published in the README and in this submission is a marker that
  points at a file in results/. This command fails if any of them has drifted,
  and CI runs it on every push.

SAFETY, PLEASE READ
  Do not open any file under media/ with a HAZARD_ prefix in a player. They
  contain real flashing footage and they are in the repository's ignore list for
  that reason. Inspect them as luminance plots with eval/plots.py instead.
```

**NEEDS ALEX:** the demo PIN. The parent area lands in phase 4. Once it exists, set the PIN here, in the README and in the GitHub Release notes.

---

## 9. Product feedback

Amazon asks five questions about every tool we used. Answered once per tool.

### 9.1 Vega SDK and Vega CLI

**Which tools, and what for.** Vega SDK 0.24.9914 and Vega CLI 1.3.4 for everything: building, installing, launching, log streaming and running the virtual device. The whole app is a Vega app.

**What worked well.** The install is one non-interactive command and it finished in about four minutes. `vega run-app` and `vega device start-log-stream` are reliable and were the backbone of every measurement run we did. The virtual device boots a real OS 1.2 image, which meant we found platform behaviour early rather than on hardware.

**What needs work.** Four things. `vega device list` crashes with `Cannot read properties of undefined (reading 'trim')` while a device is connected, although every other device command works at that same moment. `vega virtual-device status` reports `"running":true` about twenty seconds before the device can actually take a command, so scripts have to poll `vega device is-connected` instead. The same command fails with a non-zero exit before the first start, where "no instance yet" is a normal state. And the virtual device sometimes exits with nothing written to its log, so a scripted run has to check for it before every step. `vega device copy-to --help` also has its source and destination descriptions the wrong way round.

**Onboarding, zero to hello world.** Good once you find the right page, and the right page is hard to find. `https://developer.amazon.com/docs/vega/0.24/` is a 404, and so is `/latest/`. System requirements are split between the install page and the release notes, and the install page says Node 18 while the samples require Node 22. From a working shell to a sample app playing video on the virtual device was under a day, and most of that day was the documentation rather than the tools.

**Would we build with them again.** Yes. The gaps we hit are rough edges in the CLI rather than limits in the platform, and every one of them had a workaround. The missing input and screen capture commands are the only ones that would change our answer if they stayed missing, because an accessibility project has to be able to check its own screens.

### 9.2 Vega Virtual Device

**Which tools, and what for.** The Vega Virtual Device, for all development and for every measurement in this submission that is not on hardware: the smoke test, the cover timing rehearsal and the layering run.

**What worked well.** It is a real OS 1.2 image on ARM, and the app that runs there is the app that runs on the stick. It made it possible to start the whole project before any hardware arrived, which for a two-month build is most of the value.

**What needs work.** There is no supported way to press a remote button or capture the screen. `vega device` has install, launch, logs, shell and port forwarding, and no input or capture. We drive it through QEMU's QMP socket, which is undocumented and could change with any SDK release. Key injection works. `screendump` comes back black, because the app renders through a GPU layer that capture does not see, so we cannot look at our own screens at all and playback evidence has to come from device logs. Playback itself is not steady: of four runs in one afternoon, two played cleanly, one failed with `Category: UNKNOWN, Position: 0.084` on the same HLS stream, and one never started. And the device occasionally exits with nothing in the log.

**Onboarding, zero to hello world.** Quick to start, and confusing to script against, because the readiness signal lies. Add twenty minutes for working out that `status` is not readiness.

**Would we build with them again.** Yes for development. Not for evidence. Every number we take from it is labelled as a virtual device number, and the gates that matter are filmed on a real stick.

### 9.3 vega-video-sample

**Which tools, and what for.** `AmazonAppDev/vega-video-sample` at tag `v0.24-RN83` is the base of our app. We kept its playback stack and its media controls, and replaced the rest.

**What worked well.** It is a complete, working reference for the parts that are hard to guess: how `KeplerVideoSurfaceView`, `KeplerCaptionsView` and the W3C media player fit together, how the caption view handle is passed to the player, and how Kepler Media Controls are given focus. That wiring would have taken a long time to reconstruct from documentation, and having it in one repository under MIT-0 is worth a lot.

**What needs work.** The README documents a workflow that cannot be carried out on OS 1.2: pushing a file into the app's data directory. `/home` is not on the device, and the developer shell runs in its own sandbox, so there is no path from the host. Beyond that, the sample has real behaviour problems that we hit while building on it. Those are the subject of our upstream pull request, and they are described in [`docs/OPEN_SOURCE_PR.md`](OPEN_SOURCE_PR.md).

**Onboarding, zero to hello world.** Fast. Clone, install, build, sideload, and a title plays. The Shaka Player build in `postinstall` needs a JDK, which is not mentioned where you first need it.

**Would we build with them again.** Yes, and we are: the contribution goes back to it.

### 9.4 W3C media player, `@amazon-devices/react-native-w3cmedia`

**Which tools, and what for.** All playback. We read `currentTime`, `playbackRate` and the media events from it, and we draw on top of it. We never replace it.

**What worked well.** It is the standard W3C media element surface, so the knowledge transfers, and `getVideoPlaybackQuality` gave us dropped and total frame counts that we published. `setMediaControlFocus` and the caption view handle are clean integration points.

**What needs work.** The behaviour we had to measure ourselves, because it is not documented. `timeupdate` is irregular: in one recorded run, the median gap was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms, the shortest was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.min -->75<!--/n--> ms and the longest was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms while the clip kept playing. The smallest step `currentTime` reported was <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms. For anything that has to act at a precise media time, those two facts decide the whole design, and both should be in the documentation with a stated guarantee. Separately, a plain MP4 over HTTP does not start where the same content over HLS does, and a stream with no audio track pauses a few seconds in, so a silent audio track has to be added to any test clip.

**Onboarding, zero to hello world.** Good, because the sample does it for you. Hard if you started from the API surface alone, because the surface handle and caption handle lifecycle is not obvious.

**Would we build with them again.** Yes. We would ask for a documented statement about `timeupdate` cadence and `currentTime` resolution first, because an accessibility feature that has to be on screen before a specific frame cannot be built on undocumented timing.

### 9.5 Kepler Media Controls

**Which tools, and what for.** `@amazon-devices/kepler-media-controls`, for system and voice transport. It is where an Alexa "skip forward" arrives, which makes it a safety surface for us rather than a convenience.

**What worked well.** Subclassing `KeplerMediaControlHandler` and overriding only the methods you care about is a good shape, and `setMediaControlFocus` made it one call to wire up.

**What needs work.** For our purposes the important thing is that `handleSeek` can move the playhead without the app's own UI being involved, so an app that has to validate a target position has to funnel every one of these through its own logic. That is the right design, but it deserves to be called out in the documentation, because it is easy to leave a voice path unguarded while the remote path is careful.

**Onboarding, zero to hello world.** Quick, through the sample.

**Would we build with them again.** Yes.

### 9.6 KeplerCaptionsView

**Which tools, and what for.** Captions, and in our case the reason a hidden segment is still followable. It sits above our cover, so the words carry on over a black picture.

**What worked well.** The handle-based lifecycle, `onCaptionViewCreated` and `setCaptionViewHandle`, is clear, and the view composited above our own React Native views exactly as we needed.

**What needs work.** One captions view per process is a real constraint and it should be stated loudly, because an app that adds a second one finds out at runtime. We would also like a documented statement about z-ordering between the captions view, the video surface and ordinary React Native views, since our whole design depends on being able to put a view between them.

**Onboarding, zero to hello world.** Fine through the sample. Not obvious from the API alone.

**Would we build with them again.** Yes.

### 9.7 Kepler UI Components, react-native-kepler and Kepler File System

**Which tools, and what for.** `@amazon-devices/kepler-ui-components` for themed components and the seek bar, `@amazon-devices/react-native-kepler` for TV focus management and the splash screen, `@amazon-devices/kepler-file-system` for reading a run config from the app's data directory.

**What worked well.** `TVFocusGuideView` and the focus model do the hard part of ten-foot navigation. The theme builder is sensible.

**What needs work.** Two platform rules cost us time and neither is loud enough in the documentation. `setNativeProps` throws a TypeError on React Native 0.83, so any UI has to be state-driven, and the error does not say that is why. And the build rewrites `manifest.toml`, adding a `[[needs.module]]` entry for each installed `@amazon-devices` package, so removing a feature means removing its dependency too, or the app still declares it needs a module it does not use. On Kepler File System, the data directory it reads from cannot be written to from the host on OS 1.2, which makes it hard to use for exactly the fixture-loading case it is good for.

**Onboarding, zero to hello world.** Good.

**Would we build with them again.** Yes.

### 9.8 AWS CDK

**Which tools, and what for.** The whole ingest stack in Python CDK: buckets, table, container, trigger, distribution, budget and OIDC role. Unit tested against the synthesized template.

**What worked well.** Testing the synthesized template meant we could be confident about cost and privacy settings without deploying anything, which mattered because we are not allowed to deploy until the account is ready. Asserting on the template is the cheapest safety net we have.

**What needs work.** The default for `ec2.Vpc` is one NAT gateway per availability zone, which is 65 to 100 US dollars a month and would have been the largest line on a hobby project's bill by a wide margin. That default costs beginners real money, and it should either be zero by default or warn at synth time. A budget alarm should also be a one-liner rather than a raw `aws_budgets` construct.

**Onboarding, zero to hello world.** Good if you know CloudFormation, slower if you do not.

**Would we build with them again.** Yes.

### 9.9 GitHub Actions

**Which tools, and what for.** CI for the app, the Python packages, a secret scan and the check that every published number still matches its results file. Also the home of the flashmap Action we publish for other people.

**What worked well.** Composite actions made it easy to ship our flash check as something a studio can drop into a repository in one file.

**What needs work.** Nothing that cost us time on this build.

**Onboarding, zero to hello world.** Fast.

**Would we build with them again.** Yes.

---

## 10. AWS services, and how we used them

The CDK app is in `pipeline/infra/`. It synthesizes and is unit tested.

**NEEDS ALEX: nothing is deployed yet and no AWS credentials have been used.** Deployment waits on the account being on the Paid plan with the budget alarm confirmed.

| Service | How it is used | Why this one |
|---|---|---|
| **Amazon S3** | Two private buckets. `source` takes uploads and is never reachable from the internet. `delivery` holds kid-safe renditions, signed maps, posters and trickplay. | Object storage with a lifecycle rule for the raw uploads, which are the large and short-lived part. |
| **Amazon CloudFront** | Serves the delivery bucket through origin access control, so the bucket itself stays private. Signed URLs when a public key is configured. | The app needs range requests and reasonable latency for HLS. Origin access control means no public bucket. |
| **Amazon DynamoDB** | The title catalog, on demand, keyed by the source file's SHA-256, with the same fields as the local JSON catalog. | On-demand billing suits a workload that is quiet most of the time, and the hash key is the natural identity for a title. |
| **AWS Fargate on Amazon ECS** | The ingest task, ARM64, running the same container as the local pipeline. | No servers to keep alive between titles, and the same image runs locally, so what CI tests is what runs. |
| **Amazon ECR** | Holds that image. | It is where a Fargate task definition reads from. |
| **AWS Lambda** | A small function started by an S3 upload notification, which runs the Fargate task. | The plan rules out Step Functions and EventBridge while the cut list still has items on it, and one small function is the least machinery that does the job. |
| **Amazon VPC** | Public subnets only, `nat_gateways=0`, the task gets a public IP. | The CDK default of a NAT gateway per availability zone would have been the biggest line on the bill. |
| **AWS IAM with GitHub OIDC** | The deploy role that GitHub Actions assumes. | No AWS access key is ever stored in the repository or in GitHub secrets. |
| **AWS Budgets** | A 20 US dollar budget alarm. | A hard stop on a hobby project's spending, set before anything can spend. |
| **Amazon CloudWatch Logs** | Task logs with a retention setting. | Retention means old logs stop costing money on their own. |
| **Cost allocation tags** | On everything in the stack. | So the bill can be read per project. |

Estimated cost: about 5 US dollars in a month where 25 titles are ingested, and under a dollar in a month after that. `make destroy` leaves nothing billable.

**NEEDS ALEX:** request the 150 US dollar AWS credits by October 21 at 12:00 PT, while supplies last. Either form link works, both resolve to the same Google Form.

---

## 11. Open Source mini challenge

### 11.1 Contribution URL

```
NEEDS ALEX
```

**NEEDS ALEX:** the pull request has to be opened by Monday October 12 so that the contribution URL exists. The branch, the title and the body are prepared in [`docs/OPEN_SOURCE_PR.md`](OPEN_SOURCE_PR.md). The pull request has not been opened and the branch has not been pushed anywhere, because opening it needs a fork under your own GitHub account. It does not need to be merged by the deadline.

### 11.2 Project repository URL

```
https://github.com/alejandro-publius/calm-frames
```

The open-source parts of this project are:

| What | Where | Licence |
|---|---|---|
| `flashmap`, the analyzer, CLI and sidecar format | [`flashmap/`](../flashmap/) | Apache-2.0 |
| The flash check GitHub Action | [`flashmap/action.yml`](../flashmap/action.yml) and [`flashmap/examples/flash-check.yml`](../flashmap/examples/flash-check.yml) | Apache-2.0 |
| The flash map sidecar specification, version 1 | [`docs/SIDECAR_SPEC.md`](SIDECAR_SPEC.md) | Apache-2.0 |
| The drop-in hook for other Vega video apps | `app/src/calmframes/useFlashGuard.ts` today. The standalone `hook/` package that ships it is **not built yet** | Apache-2.0 |
| The threshold sources, quoted with links | [`flashmap/docs/SPEC_SOURCES.md`](../flashmap/docs/SPEC_SOURCES.md) | Apache-2.0 |

### 11.3 GitHub username

```
NEEDS ALEX
```

**NEEDS ALEX:** the repository lives under `alejandro-publius`. Confirm which GitHub account should be credited on the contribution and which one forks the upstream repository, because the fork's owner is what appears on the pull request.

### 11.4 What we did, and why it matters

```
We contributed in two directions: a fix upstream, and a reusable tool downstream.

UPSTREAM

A pull request to AmazonAppDev/vega-video-sample, the Fire TV video sample that
most Vega video apps start from, fixing a real playback defect we hit while
building on it, with a test that fails without the fix. Details, including the
root cause and the test, are in docs/OPEN_SOURCE_PR.md in our repository.

Why it matters: every developer who starts from that sample inherits the bug.
A fix there is worth more than a fix in our own fork, because it is the
starting point rather than one app.

DOWNSTREAM

flashmap, an Apache-2.0 Python package that measures video against WCAG 2.2
Success Criterion 2.3.1, both the general flash and the red flash thresholds. It
ships as a library, a CLI, a signed sidecar format and a GitHub Action that fails
a pull request adding an image or video over the thresholds.

Why it matters. There was no way for a studio or an app developer to check
whether the content they are about to publish breaks the flash thresholds, as
part of their normal review, without buying something. flashmap makes it one
file in .github/workflows/. It does the parts that the free tools skip: it
slides the one second window to every position rather than using fixed buckets,
it slides the ten degree area window rather than measuring the whole frame, it
does the saturated red test in CIE 1976 UCS, it measures area on the picture
rather than on the letterbox bars, and it reads real container timestamps so
variable frame rate input comes out right. Every threshold it uses is quoted
with a link in SPEC_SOURCES.md, and the three values that could not be verified
from a primary source are named there and are not used as thresholds.

The sidecar specification is published so that a flash map is portable: a studio
can ship one with a title and any player can honour it.
```

---

## 12. Feature requests

Priority scale: **Critical** means we could not do the right thing without it. **Important** means it cost real time or forced an undocumented workaround. **Nice-to-have** means it would be better.

| # | Priority | Request | Why |
|---|---|---|---|
| 1 | **Critical** | **A system-wide Fire TV "dim flashing lights" setting**, that any app can read and honour, in Accessibility settings next to the existing options. Apple has one. Fire TV does not. | Photosensitivity is a property of the person, not of an app. A child should not have to hope that whichever app they opened happens to have built protection. A system setting turns this from one app's feature into a platform guarantee, and gives every developer a single flag to respect. |
| 2 | **Critical** | **`vega device screenshot` that captures the composited output**, and `vega device key` for remote input. | Today there is no supported way to see what an app drew or to press a button from a script. For an accessibility app this is not a convenience: we have to check our own screens and transitions for flashing, and we cannot. Our workaround goes through QEMU's QMP socket, which is undocumented, only works on the virtual device, and returns black frames for anything drawn on the GPU layer. |
| 3 | **Important** | **Document the `timeupdate` cadence and `currentTime` resolution of the W3C media player, with a stated guarantee.** | We measured a median gap of <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.median -->426<!--/n--> ms and a longest gap of <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms during continuous playback, and a smallest reported step of <!--n results/vvd_timeupdate_stats.json:current_time_precision_ms -->3<!--/n--> ms. Anything that must act at a precise media time, which includes captions, chapter skips, ad insertion and our covers, has to know this. Right now every developer has to measure it themselves and each one gets a different answer. |
| 4 | **Important** | **Fix `vega device list`**, which crashes with `Cannot read properties of undefined (reading 'trim')` while a device is connected and every other device command works. | It is the obvious way to script against a device and it is the first thing a new developer tries. |
| 5 | **Important** | **A way to write into an app's data directory in developer mode**, such as `vega device copy-to --package <id>`. | On OS 1.2 there is no path from the host into another package's sandbox, `/home` is not on the device, and the sample's README documents a workflow that cannot be carried out. Any app that loads a config or a test fixture from its data directory cannot be given one. |
| 6 | **Important** | **A readiness signal for the virtual device**, either by holding `"running"` until it is connectable or by adding a separate field. | `status` flips to running about twenty seconds before the device can take a command, so every script has to poll something else and every developer discovers this the same way. |
| 7 | **Important** | **Document the z-order contract** between `KeplerVideoSurfaceView`, `KeplerCaptionsView` and ordinary React Native views, and state that there is one `KeplerCaptionsView` per process. | Our whole design depends on being able to place a view between the video surface and the captions. It works, and we had to find out by trying it. A second captions view fails at runtime rather than at build time. |
| 8 | **Important** | **Make the `setNativeProps` failure on React Native 0.83 explain itself**, or lint it in the template. | It throws a TypeError that does not say why, and the fix is a design change rather than a patch. |
| 9 | **Nice-to-have** | **One requirements table on the install page**, with host OS, CPU architecture, RAM, disk, the virtual device's memory needs, the Intel end-of-support date, and the Node version the samples need. | Today it is split between the install page and the release notes, and the install page says Node 18 while the samples require Node 22. |
| 10 | **Nice-to-have** | **Redirect `/docs/vega/<version>/` and `/docs/vega/latest/`** to the get-started page instead of returning 404. | These are the links most guides give. |
| 11 | **Nice-to-have** | **`NO_MODIFY_RC=true` for the installer**, and write to one startup file per shell. | It currently appends to `.zshrc`, `.zprofile`, `.bashrc`, `.bash_profile` and `.profile`, so a zsh login shell sources the env file twice, and there is no way to opt out. |
| 12 | **Nice-to-have** | **Quiet progress output when stdout is not a TTY.** | The install log was 2.5 MB of progress frames with the version lines buried in it. |
| 13 | **Nice-to-have** | **Log why the virtual device exited**, and add an exit reason to `vega virtual-device status`. | It stops with nothing written after "Virtual device ready", so a scripted run has to check for it before every step. |
| 14 | **Nice-to-have** | **Swap the `--source` and `--destination` descriptions in `vega device copy-to --help`**, which are currently backwards. | One-line fix, and it contradicts the command's own examples printed just below. |

---

## 13. Friction log

The full log, in Amazon's six fields, is [`docs/FRICTION_LOG.md`](FRICTION_LOG.md). It holds eleven entries: four Medium and seven Low. Each one has the task, the steps with the exact commands, expected versus actual with the exact output, severity, the workaround we used, and a suggestion.

If the Devpost form wants the entries inline rather than a link, paste the body of that file from its "Summary" heading down. Nothing in it needs editing first.

Short version of the eleven, so the list is readable at a glance:

| # | What broke | Severity |
|---|---|---|
| 1 | The installer floods a non-TTY log with progress frames | Low |
| 2 | The installer edits every shell startup file, with no opt-out | Low |
| 3 | The versioned docs root returns 404 | Low |
| 4 | System requirements are split across pages, and the Node versions disagree | Low |
| 5 | `vega virtual-device status` fails before the first start | Low |
| 6 | `vega device list` crashes with a TypeError while a device is connected | Medium |
| 7 | The virtual device stops with no message in the log | Medium |
| 8 | `status` reports running before the device can be used | Low |
| 9 | No supported way to press a remote button or capture the screen | Medium |
| 10 | No way to put a file in an app's data directory on OS 1.2 | Medium |
| 11 | `vega device copy-to` help text has source and destination backwards | Low |

---

## 14. Everything that needs Alex

One list, so nothing is missed on submission day.

| # | What | When |
|---|---|---|
| 1 | **Make the repository public** and confirm the licence shows in GitHub's About box | Final checks, Wed Oct 21 |
| 2 | **Film and upload the video**, then paste the URL into field 7. Check it works while logged out | Before Thu Oct 22 |
| 3 | **Run `flashmap check` on the final video file**, confirm zero violations, and commit the result | Before pasting the video URL |
| 4 | **Open the upstream pull request** from a fork under your own account, and paste the URL into field 11.1 | By Mon Oct 12 |
| 5 | **Confirm the GitHub username** to credit on the Open Source fields | Before Oct 12 |
| 6 | **Set the demo PIN** once the parent area exists, in field 8, in the README and in the Release notes | Phase 4 |
| 7 | **AWS: confirm the Paid plan and the 20 dollar budget alarm** before any deploy, which is HUMAN CHECKPOINT D | Before the first deploy |
| 8 | **Request the 150 dollar AWS credits** | By Oct 21, 12:00 PT |
| 9 | **Confirm the team and entrant details** on the Devpost form: names, eligibility, country of residence | Submission day |
| 10 | **Read the eleven friction entries** and confirm you are happy for them to be published as written | Before submission |
| 11 | **Any outreach reply you want quoted** goes into `docs/VALIDATION.md`, with permission | By Fri Oct 16 |
| 12 | **Press submit** at HUMAN CHECKPOINT G | Thu Oct 22 |
