# Devpost submission, ready to paste

Every field for **Build, Ship, Shape: Amazon Developer Hackathon**, Fire TV track, with the Open Source and AWS Builder mini challenges.

**How to use this file.** Each numbered section below is one Devpost field. Copy the block under the heading. Anything marked **NEEDS ALEX** cannot be filled in by the build, and section 16 lists every one of them again with a date.

**Re-check before pasting.** The Devpost form's exact field names and character limits should be read off the live form on the day, because this file is written from the build plan rather than from the form.

**The dates.**

| When | What |
|---|---|
| Mon Oct 12 | The upstream pull request is open, so the contribution URL exists |
| Mon Oct 19 to Tue Oct 20 | Film the video from [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md) |
| Wed Oct 21 | Make the repository public, run the final checks, tag the judged release |
| Wed Oct 21, 12:00 PT | Last moment to request the 150 US dollar AWS credits |
| **Thu Oct 22** | **Press submit** |
| Fri Oct 23, 12:00 PT | The deadline. We are a day early on purpose |

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

Now picture Maya. She is twelve, she has photosensitive epilepsy, and tonight she is at a sleepover picking a film on somebody else's living room television, with no adult sitting next to her to screen it first. Nothing on that television knows what is in the next ninety minutes. (Maya is a composite persona, not a real person. She is labelled as one on screen in our demo video too.)

Other platforms have partial answers: Apple has a Dim Flashing Lights setting, there are desktop filters, and there are research prototypes that detect flashes and overlay them live. What none of them do is check the whole title before it is allowed to play, and then guarantee that every way of jumping into it is safe.

That is the gap Calm Frames fills, and Fire TV is where it belongs, because the television is the screen a child uses without supervision.

### What it does

Calm Frames is a verified safety layer, and it is never a video player.

Every frame of a title is measured before that title can appear in kid mode. The result is an Ed25519 signed flash map, bound to the file's SHA-256, that lists each interval that goes over the WCAG 2.2 general flash or red flash threshold. A verify step blocks publishing: a title whose rendition still contains a violation, whose map is tampered with, whose hash is wrong, or whose poster was taken from a flagged moment, does not reach kid mode at all.

During playback the app hides each flagged segment before it starts. The picture goes, the sound keeps going and the captions keep running above the cover, so the story stays followable. Afterwards the app says what it hid.

It adapts to the household. A parent gives the television diagonal and the seat distance behind a PIN, and picks a preset. The room rule then adds a second area window for that room's ten degree visual field. A household setting can only ever add hides. It cannot make Calm Frames weaker than WCAG.

Voice, D-pad and on-screen cards all run through one seek function. If the target lands inside a flagged interval or its guard band, the picture is covered first and the seek happens second. An Alexa "skip forward" that would drop the playhead into the middle of a flagged scene is as safe as pressing right on the remote.

And any Vega video app can add the same protection with a small hook, while any studio can check its own content before publishing with the open-source analyzer and its GitHub Action.

Two of the Fire TV track's six priority categories are this project by name. It is **family entertainment**, because the whole thing exists so a child can pick a title on the family television without a parent having to preview it first. And it is **multi-modal UX**, because voice, D-pad and on-screen cards are not three ways into the same app: they are three inputs to one seek function that covers the picture before it moves the playhead. A spoken "skip forward" and a press of the remote go through the same gate, and neither can land inside a flagged interval. That is multi-modal UX combining voice, D-pad and visual in a single flow, and the single flow is the part that stops working if you build it three times.

Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device.

### How we built it

Four pieces.

**flashmap**, an Apache-2.0 Python package, measures video against WCAG 2.2 Success Criterion 2.3.1: both the general flash rule and the red flash rule, with the saturated red test done in the CIE 1976 UCS chromaticity diagram. It slides a one second window to every position for the three-flashes-a-second limit, and slides a ten degree area window for the 25 percent rule, because the specification says "any 10 degree visual field" rather than a fixed grid. It reads real container timestamps, so variable frame rate input comes out right. It detects letterbox and pillarbox so area is measured on the picture rather than on the bars. Chunked analysis gives byte for byte the same map as a whole file run, which is a property test rather than a claim. Every threshold in the code is quoted, with a link, in `flashmap/docs/SPEC_SOURCES.md`, and the three things that could not be verified from a primary source are named there and are not used.

**The pipeline** takes a title through probe, analyze per preset, hide plan, kid-safe rendition, trickplay, posters taken only from the safe rendition, signing, and a catalog entry. It is idempotent and keyed by the source hash. `pipeline/verify.py` is the gate, and it was mutation tested: a violation left in a rendition, a violation under the modelled cover, a tampered map, a wrong hash and a poster from a flagged moment all fail it.

**The Fire TV app** is built on `AmazonAppDev/vega-video-sample` at tag `v0.24-RN83`. Playback stays on `@amazon-devices/react-native-w3cmedia`. The cover is a plain React Native view between the video surface at zIndex 0 and `KeplerCaptionsView` at zIndex 2, driven by state rather than `setNativeProps`, which throws on React Native 0.83.

**The infrastructure** is an AWS CDK stack with zero NAT gateways, a 20 dollar budget alarm, private buckets and a GitHub OIDC role.

The hardest design decision came out of a measurement. The player's own position reports are irregular: in a recorded run the longest gap between two of them was <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms while the clip kept playing. A cover that waited for a position report before acting would have been that late. So the scheduler runs on a wall clock re-synced to media time at every report, and anything that makes the playhead uncertain, including a stall, a seek, a pause or the app being backgrounded, hides the picture at once instead of trusting the estimate. Amazon does not document either figure, so we measured them.

### Challenges we ran into

The virtual device has no supported way to press a remote button or capture the screen, so we drive it through QEMU's QMP socket. Key injection works. Screenshots come back black, because the app renders on a GPU layer the capture does not see, so playback evidence comes from device logs rather than pictures. `vega device list` crashes with a TypeError while a device is running, so every script uses `vega device info` and `vega device is-connected` instead. And on OS 1.2 there is no path from the host into another package's data directory, although the sample's README documents one, so a measurement run is started from a button inside the app or from a config the app fetches over HTTP. Every one of those is in the friction log with its exact output, alongside twenty-six more.

The real one is this. We do not have a cover lead time number, and for a while we thought we did. A rehearsal run appeared to show every marker covered in time with a worst lead of 449 ms. It was wrong. The player in that run never got past about a quarter of a second, while the cover scheduler, which runs on a wall clock by design, kept advancing its own estimate and fired every cover on time against that estimate. The analysis agreed with itself. A stricter second script refused to count any of it, which is how it surfaced, and both scripts now require a position report from the player before a lead time is counted. Those numbers were withdrawn from everywhere they appeared, and the retraction is written out in `docs/GATES.md`. Run again on a packed clip under the new rule, the measurement gave <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n--> usable trials with <!--n results/gate1_software_vvd.json:in_time -->48<!--/n--> covered in time, a median lead of <!--n results/gate1_software_vvd.json:lead_ms.median -->488.4<!--/n--> ms, and one cover that went on 86 ms after its marker started because the JavaScript thread stalled. We kept that last one in the README rather than rounding it away, because it is the thing that tells us the guard band is not yet known to be wide enough. The real measurement is 50 trials filmed at 240 frames a second against a real Fire TV stick, and it has not happened yet.

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
Vega SDK 0.24 · Vega CLI · React Native 0.83 · TypeScript · @amazon-devices/react-native-w3cmedia · Shaka Player · Kepler Media Controls · KeplerCaptionsView · Kepler UI Components · Kepler File System · react-native-kepler · AccessibilityInfo / VoiceView · Python 3.12 · PyAV / FFmpeg · NumPy · Ed25519 · pytest · Jest · AWS CDK · Amazon S3 · Amazon DynamoDB · AWS Fargate · AWS Lambda · Amazon CloudFront · Amazon ECR · AWS Budgets · AWS IAM with GitHub OIDC · Amazon CloudWatch Logs · GitHub Actions
```

## 4. Track

```
Fire TV
```

**Priority categories: family entertainment, and multi-modal UX.** The rules list six for Fire TV and two of them are this project by name. If the form has a box for them, tick both. If it does not, the sentence is already in the description above, under "What it does".

## 5. Mini challenges entered

```
Open Source (primary)
AWS Builder
```

A project can win at most one track prize and one mini challenge prize. Open Source is the one to lead with: the analyzer, the Action, the sidecar specification and the hook are all published under Apache-2.0, and the upstream fix goes back to the sample every Vega video app starts from.

**Open Source is solid. AWS Builder is not certain, and section 11 says exactly why.** The short version: the rules ask for a project that "incorporates AWS services ... with documented integrations", and our stack synthesizes, is unit tested and has never been deployed. Nobody here can tell from the rules text whether that counts. Entering both is still right, because entering costs nothing and the answer might be yes. Claiming it as won is not.

## 6. Repository URL

```
https://github.com/alejandro-publius/calm-frames
```

**NEEDS ALEX:** the repository is private today and goes public during the final checks on **Wednesday October 21**, because the rules need it public with the licence visible at submission. Confirm it is public, and that Apache-2.0 shows in GitHub's About box, before pasting this.

## 7. Video URL

```
NEEDS ALEX
```

**NEEDS ALEX:** film it **Monday October 19 to Tuesday October 20**, upload it, then paste the link. The script is in [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md), timed to 2:53 with a shot list, and the capture plan for each shot is in [`docs/SHOT_MANIFEST.md`](SHOT_MANIFEST.md).

Three checks before pasting:

1. `eval/check_video.sh <final file>` exits 0, and `results/video_check.json` is committed. It runs flashmap over the finished cut and refuses anything over three minutes. Exit 2 means flashmap could not tell, and that is a failure too.
2. The link works while logged out, on YouTube or Vimeo, in English.
3. The on-screen and spoken wording is "reduces exposure to flashing above published limits in the videos it plays; not a medical device". Never "prevents seizures", never "seizure-proof".

## 8. Required technologies

**First, what the rules actually ask of a Fire TV entry.** Alexa+, Bee and Ring entries have to demonstrate their track's required technology at runtime, imported and called. Fire TV is the exception. Quoted from the rules page, Submission Requirements, and copied into [`docs/RUBRIC.md`](RUBRIC.md) section 2.2:

> Fire TV: Any framework or language is acceptable (React Native, Android/Kotlin/Java, web technologies, etc.). The requirement is that the project runs on Fire OS or Vega OS. The demo video must show the project running on an actual Fire TV device or the Fire TV/Vega simulator.

So the hard Stage One line for our track is a video line, not a code line, and it is field 7 rather than this one. The table below goes past what the rules ask. It is here because it helps Technical Implementation and because an automated review can follow it, not because it is required.

Every row links a file and a symbol in the repository, and the README carries the same table with line numbers: [Required tech at runtime](../README.md#required-tech-at-runtime).

| Required technology | Package | Where it is called | What it does here |
|---|---|---|---|
| **W3C media player** | `@amazon-devices/react-native-w3cmedia` | `app/src/utils/VideoHandler.ts`, `new VideoPlayer()`, with Shaka attached | All playback. Calm Frames never replaces it and never lowers its opacity. It reads `currentTime`, `playbackRate` and the media events, and covers on top. |
| **W3C media player, video surface** | `@amazon-devices/react-native-w3cmedia` | `app/src/screens/PlayerScreen.tsx`, `KeplerVideoSurfaceView` | The hardware video layer at zIndex 0. The cover sits above it, which is what keeps the sound running while the picture is hidden. |
| **Vega Media Controls** | `@amazon-devices/kepler-media-controls` | `setMediaControlFocus` in `app/src/utils/VideoHandler.ts`; the safe handler is `app/src/calmframes/SafeMediaControlHandler.ts` | System and voice transport, and the path an Alexa "skip forward" arrives on. None of the handlers call `super`. Each one goes through `planSeek` in `app/src/calmframes/seekSafety.ts`. |
| **KeplerCaptionsView** | `@amazon-devices/react-native-w3cmedia` | `app/src/screens/PlayerScreen.tsx`, with `setCaptionViewHandle` | Captions at zIndex 2, above the cover. One captions view per process. This is why a hidden segment is still followable. |
| **Accessibility APIs** | `react-native` `AccessibilityInfo`, plus the `com.amazon.devconf.privilege.accessibility` privilege in `app/manifest.toml` | `app/src/calmframes/announce.ts`, with `accessibilityLiveRegion` and `accessibilityRole` on the card | VoiceView is told what is about to be hidden, in a queue rather than by interrupting. The cover itself is taken out of the accessibility tree, so VoiceView never reads a black rectangle. |
| **Kepler UI Components and `react-native-kepler`** | `@amazon-devices/kepler-ui-components`, `@amazon-devices/react-native-kepler` | Throughout `app/src/calmframes/` | Ten-foot focus management through `TVFocusGuideView`, the themed components and the seek bar. |
| **Kepler File System** | `@amazon-devices/kepler-file-system` | `app/src/calmframes/harnessConfig.ts` | Reading a measurement run config from the app's data directory. |

The whole guard is one hook, `app/src/calmframes/useFlashGuard.ts`. Give it a player and where the map is, and it verifies the map, builds the schedule, drives the cover, decides the card, announces it and hands back the one seek function every control has to use. It knows nothing about Calm Frames screens, navigation or storage, which is what makes it the thing another Vega app can drop in.

## 9. Testing instructions

```
Calm Frames runs on a Fire TV stick with Vega OS 1.2 in developer mode, and on
the Vega Virtual Device. Everything below is also in the repository README.

THE FASTEST PATH: INSTALL THE RELEASE
  Download the package for your device from the GitHub Release, check it
  against SHA256SUMS, and sideload it:

    vega device is-connected
    vega run-app calm-frames-<version>-armv7.vpkg

  calm-frames-<version>-armv7.vpkg    Fire TV Stick
  calm-frames-<version>-aarch64.vpkg  64 bit Fire TV devices, and the
                                      aarch64 virtual device
  calm-frames-<version>-x86_64.vpkg   the x86 virtual device

  These are release builds for Vega OS 1.2. Release builds strip console.log,
  so use a debug build if you want the app's own logs.

  Release: NEEDS ALEX
  SHA256SUMS: in the same release

BUILD IT YOURSELF INSTEAD

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
  vega device is-connected            # not "vega device list", which crashes
  vega run-app build/armv7-debug/calm-frames-app_armv7.vpkg

  Use a debug build. Release builds strip console.log, and the evidence for a
  measurement run is in the log.

PARENT AREA
  The parent area is behind a four digit PIN, set on the device by whoever sets
  the app up. The PIN itself is never stored: what is stored is a salted,
  iterated hash of it.

  Demo PIN: NEEDS ALEX

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

RUN THE WHOLE THING
  make test         the app's jest suite, flashmap and pipeline pytest
  make reproduce    rebuild every table and figure from committed results
  make synth        the CDK stack, offline, with no AWS account touched

SAFETY, PLEASE READ
  Do not open any file under media/ with a HAZARD_ prefix in a player. They
  contain real flashing footage and they are in the repository's ignore list for
  that reason. Inspect them as luminance plots with eval/plots.py instead.
```

**NEEDS ALEX, two things in this block.**

1. **The demo PIN.** Set it once, then put the same four digits in three places: the block above, the README's "The parent area and the demo PIN" section, and the GitHub Release notes. `make release RELEASE_ARGS="--pin 1234"` puts it in the notes. The README says today that it is not set, and it must not carry a made-up one.
2. **The release links.** The release does not exist yet, because the judged tag can never move once it is created and that is a person's decision. `make release` builds all three packages, writes `SHA256SUMS` and `NOTES.md` into `build/release/<tag>/`, prints the `gh release create` line and stops. Once it is published, the links are:

   ```
   https://github.com/alejandro-publius/calm-frames/releases/tag/<tag>
   https://github.com/alejandro-publius/calm-frames/releases/download/<tag>/calm-frames-<version>-armv7.vpkg
   https://github.com/alejandro-publius/calm-frames/releases/download/<tag>/calm-frames-<version>-aarch64.vpkg
   https://github.com/alejandro-publius/calm-frames/releases/download/<tag>/calm-frames-<version>-x86_64.vpkg
   https://github.com/alejandro-publius/calm-frames/releases/download/<tag>/SHA256SUMS
   ```

   `<version>` comes from `app/manifest.toml` and `<tag>` defaults to `v<version>`. Paste the real ones here once the tag exists, and install from the release on a real stick before telling anyone about it. [`docs/RELEASE.md`](RELEASE.md) has the full steps.

---

## 10. Product feedback

### 10.1 The five questions, once per tool

Amazon asks five questions about every tool an entry used. **The answers live in [`docs/FEEDBACK.md`](FEEDBACK.md)**, which covers thirteen tools: the Vega SDK and CLI, the Vega Virtual Device, `vega-video-sample`, the W3C media player, Vega Media Controls, KeplerCaptionsView, the accessibility APIs, AWS CDK, AWS Fargate on ECS, Amazon S3, Amazon CloudFront, the Kepler UI and file system packages, and GitHub Actions.

That file is the one to paste from, and it is deliberately the only copy, so this document cannot drift away from it. If the form wants the answers inline, paste `docs/FEEDBACK.md` from its "1. Vega SDK and Vega CLI" heading down to the "Feature requests" heading. Nothing in it needs editing first.

Two things a reader should know about it, which it says itself:

- Every complaint points at something that happened during the build, and the long version with exact commands and exact output is a numbered entry in [`docs/FRICTION_LOG.md`](FRICTION_LOG.md).
- Fargate, S3 and CloudFront say in their first line that nothing is deployed and no AWS credential has been used, and they answer as far as a synthesized template and a unit test can. Their onboarding question is answered "not answerable yet" rather than made up.

The heaviest complaint, in one line each, is in that file's "At a glance" table.

### 10.2 Which AWS services we used, and how

**This block belongs in the Product Feedback answer, not in a field of its own.** The rules put the AWS Builder requirement inside this field: the Stage One checklist line reads "AWS Builder: which AWS services were used and how, inside the Product Feedback answer". So paste `docs/FEEDBACK.md` first, then paste this table at the end of the same box. Section 11 is the reasoning about whether we qualify at all, and it is not a substitute for having the table here.

Section 11.1 is the sentence that has to be read before the table: the stack synthesizes and is unit tested, and **nothing has ever been deployed and no AWS credential has ever been used.** Read every row as "how it is used in the stack as written and tested", not as "how it behaved in production".

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

**Cost.** Estimated at about 5 US dollars in a month where 25 titles are ingested, and under a dollar in a month after that. This is an estimate from the stack's shape, not a bill anybody has received. `make destroy` leaves nothing billable.

**What we would tell another builder.** The `ec2.Vpc` default is one NAT gateway per availability zone, which is 65 to 100 US dollars a month and would have been the largest line on this project's bill by a wide margin. Asserting on the synthesized template, before deploying anything, is the cheapest safety net available, and it is what let us be confident about cost and privacy settings with no account attached. Both of those are written up properly in [`docs/FEEDBACK.md`](FEEDBACK.md) section 8.

---

## 11. AWS Builder mini challenge

### 11.1 What exists, stated plainly before anything else

The AWS work in this project is **an AWS CDK application in [`pipeline/infra/`](../pipeline/infra/) that synthesizes to a CloudFormation template and is unit tested against that template.** That is the whole of it, and here is what that does and does not mean:

- the stack is written, and `make synth` builds the template offline with no account attached;
- the template is asserted on in unit tests, which is how we know about the zero NAT gateways, the private buckets, the budget alarm and the OIDC role;
- **nothing has ever been deployed. No AWS credential has been used. No AWS API has been called by this project at any time.** `make deploy` refuses to run until HUMAN CHECKPOINT D is confirmed, and that lock was tested;
- so no number in this section is a bill, a metric or a log line. The cost figure further down is an estimate from the stack's shape and is labelled as one.

### 11.2 Whether this qualifies is an open question, and it is Alex's to settle

The rules page, Project Requirements, says:

> AWS Builder (Mini Challenge): Any primary track project that incorporates AWS services (i.e. Amazon Bedrock, AgentCore, Strands SDK, Kiro Crew, SageMaker, etc.) with documented integrations.

Neither the rules page nor the overview page defines "incorporates", and neither says whether a deployment is required. A synthesized, unit tested, undeployed stack is documented and integrated in the sense that the code exists and is tested, and it is not integrated in the sense that nothing has ever run. **We cannot tell from the rules text which reading applies, so this document does not claim the mini challenge.** It describes what exists and lets a judge decide.

Three routes settle it, and they are Alex's calls, not the build's:

1. **Ask the hackathon manager.** One question, and the answer is authoritative in a way that our reading never will be. This is the cheapest route and it should go first.
2. **Deploy once.** Put the account on the Paid plan, set the 20 dollar budget alarm, confirm HUMAN CHECKPOINT D, run `make deploy`, ingest one title, and the doubt is gone. `make destroy` leaves nothing billable afterwards.
3. **Kiro Crew.** The rules say it qualifies on its own: "Kiro Crew qualifies on its own as a development tool used during the hackathon[,] a submission does not need to also call a runtime AWS service". **We have not used Kiro Crew and nothing in this submission may imply that we have.** It is listed because it is a route that exists, not because it is a route we have taken.

Route 1 then route 2 is the order that costs least. Doing nothing is also a choice: we enter the mini challenge, describe the stack as it is, and a judge decides.

### 11.3 Which AWS services, and how

**The table is in [section 10.2](#102-which-aws-services-we-used-and-how), because that is the field the rules name.** It is one copy on purpose, so the two cannot drift. Eleven services and settings: S3, CloudFront, DynamoDB, Fargate on ECS, ECR, Lambda, VPC with zero NAT gateways, IAM with GitHub OIDC, Budgets, CloudWatch Logs, and cost allocation tags on everything.

**NEEDS ALEX:** request the 150 US dollar AWS credits by **Wednesday October 21 at 12:00 PT**, while supplies last. Either form link works, both resolve to the same Google Form.

---

## 12. Open Source mini challenge

### 12.1 Contribution URL

```
NEEDS ALEX
```

**NEEDS ALEX:** the pull request has to be opened by **Monday October 12** so that this URL exists. The branch, the title and the body are prepared in [`docs/OPEN_SOURCE_PR.md`](OPEN_SOURCE_PR.md), which Lane G owns. It has not been opened and the branch has not been pushed anywhere, because opening it needs a fork under your own GitHub account. It does not need to be merged by the deadline, only opened.

### 12.2 Project repository URL

```
https://github.com/alejandro-publius/calm-frames
```

The open-source parts of this project are:

| What | Where | Licence |
|---|---|---|
| `flashmap`, the analyzer, CLI and sidecar format | [`flashmap/`](../flashmap/) | Apache-2.0 |
| The flash check GitHub Action | [`flashmap/action.yml`](../flashmap/action.yml) and [`flashmap/examples/flash-check.yml`](../flashmap/examples/flash-check.yml) | Apache-2.0 |
| The flash map sidecar specification, version 1 | [`docs/SIDECAR_SPEC.md`](SIDECAR_SPEC.md) | Apache-2.0 |
| The drop-in hook for other Vega video apps | [`hook/`](../hook/), mirrored from `app/src/calmframes/` with a diff in [`docs/INTEGRATION_DIFF.md`](INTEGRATION_DIFF.md) | Apache-2.0 |
| The threshold sources, quoted with links | [`flashmap/docs/SPEC_SOURCES.md`](../flashmap/docs/SPEC_SOURCES.md) | Apache-2.0 |

### 12.3 GitHub username

```
NEEDS ALEX
```

**NEEDS ALEX:** the repository lives under `alejandro-publius`. Confirm which GitHub account should be credited on the contribution and which one forks the upstream repository, because the fork's owner is what appears on the pull request. Both answers are needed before Oct 12.

### 12.4 What we did, and why it matters

```
We contributed in two directions: a fix upstream, and a reusable tool
downstream.

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
ships as a library, a CLI, a signed sidecar format and a GitHub Action that
fails a pull request adding an image or video over the thresholds.

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
can ship one with a title and any player can honour it. The hook package ships
the playback side, so a Vega video app can get the same protection by giving one
hook a player and a map URL.
```

---

## 13. Feature requests

**The full list is in [`docs/FEEDBACK.md`](FEEDBACK.md) under "Feature requests"**: twenty-one requests, each marked Critical, Important or Nice-to-have, each tied to something that happened during the build. Paste that table.

The scale, so the priorities read correctly: **Critical** means we could not do the right thing without it. **Important** means it cost real time or forced an undocumented workaround. **Nice-to-have** means it would be better.

The three Critical ones, because they are the argument:

1. **A system-wide Fire TV "dim flashing lights" setting**, in Accessibility settings, readable by any app the way `isScreenReaderEnabled` is readable now. Photosensitivity is a property of the person, not of an app. A child should not have to hope that the app they opened happens to have built protection. We would delete half of our own settings screen the day this ships.
2. **`vega device screenshot` that captures the composited output**, and `vega device key` for remote input. WCAG 2.3.1 applies to an app's own interface, and today a developer cannot look at it.
3. **A way to get one frame of what an app drew, from inside the app.** The same gap from the other side: React Native 0.83 removed `takeSnapshot` and no `@amazon-devices` package replaces it.

Requests 2 and 3 are the pair that stopped us seeing our own screens, which is why an accessibility entry is raising them as Critical rather than as a convenience.

### Request 1 has a shipped precedent, and it is worth quoting rather than asserting

This is not a thing nobody has tried. Apple's Media Accessibility framework documents it, and its developer pages say:

> The Dim Flashing Lights setting allows the system to calculate, mitigate, and inform people about flashing lights in a piece of media.

> Dim Flashing Lights is a setting that allows a person to indicate that they want to avoid bright, frequent flashes of light on their Apple device. When a person turns on this setting, the device automatically dims video content when the system detects flashing or strobing effects.

A person turns it on at Settings, Accessibility, Motion. An app can read whether it is on, can register for a notification when it changes, and Apple ships `MAFlashingLightsProcessor`, described in the same documentation as "A class that processes a framebuffer object to detect and dim sequences of flashing lights". So **the setting, the read API, the change notification and the processing class all exist and are documented for app developers**. That is the precedent, and it is the shape request 1 asks for.

Sources, and how they were read, because the pages do not serve their text as HTML:

- <https://developer.apple.com/documentation/mediaaccessibility/flashing-lights>
- <https://developer.apple.com/documentation/mediaaccessibility/responding-to-changes-in-the-flashing-lights-setting>

Both render their text in the browser, so fetching the HTML returns the navigation and nothing else. The quoted sentences come from the documentation content those pages load, at `developer.apple.com/tutorials/data/documentation/mediaaccessibility/flashing-lights.json` and the matching path for the second page, both fetched on Sep 17, 2026. **Nothing about Apple's implementation is claimed beyond what those two pages say.**

**We have not found an equivalent on Fire TV.** That is a statement about what we looked for and did not find, not a proof that nothing exists, and it is the first thing the request should be checked against by somebody inside the Fire TV team.

And two differences, because the precedent is not the same product. Apple's detection runs on the device, in real time, on the frames as they are drawn. Calm Frames analyses the whole title ahead of time, signs the result, and the player acts on a schedule rather than on what it has just seen, which is what lets it cover a flash **before** its first frame rather than dimming after one starts. Apple's approach needs no cooperation from the app; ours needs a signed map, so it only ever protects content somebody measured. The two are complementary, and a system setting would make ours unnecessary for anyone who turned it on, which is the point.

---

## 14. Friction log

**The full log, in Amazon's six fields, is [`docs/FRICTION_LOG.md`](FRICTION_LOG.md)**, which Lane G owns. It holds **thirty entries: four High, thirteen Medium and thirteen Low.** Each one has the task, the steps with the exact commands, expected versus actual with the exact output, severity, the workaround we used, and a suggestion.

If the Devpost form wants the entries inline rather than a link, paste the body of that file from its "Summary" heading down. Nothing in it needs editing first.

The four High entries, so the list reads in the right order:

| # | What broke |
|---|---|
| 12 | The device drops the app's own log output under load, so evidence a rate limiter can delete is not evidence |
| 14 | No way to get a frame of what the app drew, from inside the app or from outside it |
| 15 | No crypto API on the platform, so Ed25519 signature checking had to be written by hand |
| 22 | Playback on the virtual device is not steady, and the error says `UNKNOWN` |

**NEEDS ALEX:** read the thirty entries and confirm you are happy for them to be published as written. They name real defects in Amazon's tools, in plain words, with the exact output. That is what the log is for, and it is still your name on the submission.

---

## 15. Team and entrant details

**NEEDS ALEX, all of it.** Nothing in this section can be filled in by the build.

| Field | Answer |
|---|---|
| Entrant name or team name | NEEDS ALEX |
| Team members, if any | NEEDS ALEX |
| Country of residence | NEEDS ALEX |
| Eligibility confirmation | NEEDS ALEX |
| Contact email | NEEDS ALEX |
| Amazon developer account | NEEDS ALEX |

Anything quoted from outreach goes in [`docs/VALIDATION.md`](VALIDATION.md), with permission, by **Friday October 16**.

---

## 16. Everything that needs Alex

One list, in date order, so nothing is missed on submission day.

| # | What | When | Field it unblocks |
|---|---|---|---|
| 0 | **Settle the AWS Builder question.** Ask the hackathon manager whether a synthesized, unit tested, undeployed CDK stack counts as "incorporating AWS services". If the answer is no or nobody answers, decide between deploying once and dropping the mini challenge. Kiro Crew is a third route we have not taken and must not imply we have | **As early as possible.** Route 2 needs the paid plan first, so a late yes is worth less than an early one | 5, 11 |
| 0b | **Settle whether a camera can see the Vega Virtual Device window.** Two minutes with a phone. It decides whether the video can be filmed without the stick, and the rules allow the simulator, so this is the Stage One line | **The moment the virtual device is free** | 7 |
| 1 | **Confirm the GitHub username** to credit on the Open Source fields, and which account forks the upstream repository | Before Mon Oct 12 | 12.3 |
| 2 | **Open the upstream pull request** from a fork under your own account, and paste the URL | By Mon Oct 12 | 12.1 |
| 3 | **Set the demo PIN** once, then put it in the testing instructions, the README and the Release notes | Before the release is built | 9 |
| 4 | **AWS: confirm the Paid plan and the 20 dollar budget alarm**, which is HUMAN CHECKPOINT D | Before any deploy, and it is the gate on route 2 of item 0 | 11 |
| 5 | **Any outreach reply you want quoted** goes into `docs/VALIDATION.md`, with permission | By Fri Oct 16 | 15 |
| 6 | **Film the video** from `docs/VIDEO_SCRIPT.md`, with the shot manifest beside it | **Mon Oct 19 to Tue Oct 20** | 7 |
| 7 | **Run `eval/check_video.sh` on the final file**, confirm exit 0, and commit `results/video_check.json` | Before pasting the video URL | 7 |
| 8 | **Upload the video** and check the link works while logged out | Before Thu Oct 22 | 7 |
| 9 | **Read the thirty friction entries** and confirm you are happy for them to be published as written | Before submission | 14 |
| 10 | **Request the 150 dollar AWS credits** | By **Wed Oct 21, 12:00 PT** | 11 |
| 11 | **Make the repository public** and confirm Apache-2.0 shows in GitHub's About box | **Wed Oct 21**, during the final checks | 6 |
| 12 | **Publish the release** and paste the `.vpkg` links and the tag into the testing instructions | **Wed Oct 21**, after the final checks | 9 |
| 13 | **Confirm the team and entrant details**: name, team, eligibility, country of residence, contact email | Submission day | 15 |
| 14 | **Press submit** at HUMAN CHECKPOINT G | **Thu Oct 22** | all |

The deadline is **Friday October 23 at 12:00 PT**. We submit a day early on purpose, so that a form problem on the day is a problem with a day left in it rather than a problem with an hour.
