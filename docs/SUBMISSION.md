# Devpost submission draft

Every field for **Build, Ship, Shape: Amazon Developer Hackathon**, Fire TV track, with the Open Source and AWS Builder mini challenges.

**Status, October 10.** Solo entry; validation and demo use the Vega Virtual Device exclusively. The Amazon Developer account is created and identity-verified. This draft is not ready to submit. The earlier native simulator journey and English video are recorded and checked locally. The current cloud design polish changes app inputs and still needs a Mac build, native checks and refreshed demo assets. The judged release,
reviewer access and public contribution URL still have no URL. Section 3 was
rewritten against the current implementation; recheck the remaining fields and
replace every **NEEDS ALEX** before submission. Current completion and remaining blockers are in
[COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md).

**Earlier native evidence.** The October 10 receipt, [`results/redesign_validation_2026-10-10.json`](../results/redesign_validation_2026-10-10.json), binds native app source `73fbbed` to its installed aarch64 Debug package and identifies earlier observations separately. PIN mismatch/Delete, all offered presets and compatible catalog titles, saved settings, remote focus, Harbor holds with captions/audio, transport fallback and recovery were exercised. The final restart of that build preserves Kid, Extra cautious, a 55-inch TV, a 10-foot household distance and chime Off; Kid's effective distance remains its stricter 8 feet. Positive real-cover history is integration-tested only. Its English demo is `build/submission-redesign/Calm-Frames-demo-English.mp4`, with disclosed actual captures and synthetic narration. These records remain evidence of that earlier build.

**Current design scope.** The cloud polish adds generated Harbor presentation art, taller library cards, quieter secondary navigation, and refined setup, parental controls and viewing settings. It has not been packaged, installed or verified on Vega here. See [design/POLISH_REVIEW.md](design/POLISH_REVIEW.md) and [`results/design_polish_2026-10-10.json`](../results/design_polish_2026-10-10.json). Rebuild on the Mac and check D-pad navigation, scrolling, saved settings and playback before refreshing the native recording, demo and draft assets. The Harbor illustration is not a film frame or signed hold image.

The corrected conformance report below retains its weaker near-limit result. Saved AWS publication worked, but the app consumes its compiled local catalog. Hosted CI passed on pushed checkpoint 402c167. At that checkpoint Audit passed SBOM, stack and container jobs and failed dependency audit only. All nine earlier review assets are uploaded in a private draft release; see results/github_push_2026-10-10.json. Main and public submission links are unchanged. The dependency audit was repaired on Oct 11 (`xmldom` replaced by its maintained fork, `lodash` moved, every remaining finding sorted by whether it is in the device bundle), and the hosted Audit run on the Oct 11 push came back <!--n results/github_push_2026-10-11.json:published.audit_conclusion -->success<!--/n--> in all four jobs, with CI <!--n results/github_push_2026-10-11.json:published.ci_conclusion -->success<!--/n--> in all six (`results/github_push_2026-10-11.json`). The conflicting Amazon sample notices in [AMAZON_SAMPLE_LICENSE_REVIEW.md](AMAZON_SAMPLE_LICENSE_REVIEW.md) remain open before public release, with the caveat now stated in NOTICE and the README.

**How to use this file.** Each numbered section below corresponds to a planned
Devpost field. Final field names still need checking in the live form.

**Re-check before pasting.** The Devpost form's exact field names and character limits should be read off the live form on the day, because this file is written from the build plan rather than from the form.

**The dates.**

| When | What |
|---|---|
| Done, Oct 9 to 10 | Earlier native simulator takes recorded. Exact clips used in that cut are listed in `results/redesign_demo_manifest_2026-10-10.json` |
| Pending, before upload | Rebuild and validate the cloud polish on the Mac, then refresh native recordings, the English demo and review assets to match |
| Mon Oct 12 | The upstream pull request is open, so the contribution URL exists |
| Fri Oct 16, 12:00 PT | Devpost's early eligibility check. Entries submitted by then are checked, and Devpost says what needs fixing. Optional, and only worth it with a near-complete entry, video link included. The takes exist; this row is reachable only if the final English edit is uploaded before then, otherwise drop it |
| Mon Oct 19, 9 to 10 AM PT | Office Hours #2 with the Amazon team. Optional; register through the link in the Devpost update |
| Before Thu Oct 22 | Upload the completed checked English demo and verify its public link |
| Wed Oct 21 | Make the repository public, run the final checks, tag the judged release |
| **Thu Oct 22** | **Press submit** |
| Fri Oct 23, 12:00 PT | The deadline. We are a day early on purpose |

The two new rows come from the hackathon's announcements as the Oct 9 plan
recorded them. Devpost answers automated requests with HTTP 403, so confirm both
in a browser before relying on them. The AWS credit request that used to be on
this list is gone: the form closed on Oct 7, 2026 (section 11.3).

---

## 1. Project name

```
Calm Frames
```

## 2. Tagline

```
A calmer way to watch
```

A Fire TV accessibility prototype that checks prepared videos and keeps the story going through every scheduled hide.

## 3. Description

Use these headings in the project description. Confirm the live form's layout
before pasting them.

### Inspiration

A flashing scene can interrupt a family's shared viewing experience. Hiding the
picture also removes the visual context that makes a story understandable. I
wanted to explore both problems together: check a title before playback, then
preserve its sound, captions and a calm image when a scene needs covering.

The intended audience is families where a child has photosensitive epilepsy.
The Epilepsy Foundation's page on photosensitivity says that "for about 3% of
people with epilepsy, exposure to flashing lights at certain intensities or to
certain visual patterns can trigger seizures", and that it "is more common in
children and adolescents". Its expert panel's consensus in *Epilepsia* (online
Nov 24, 2025, in the February 2026 issue) says "signal analysis or trained human
inspectors can identify provocative visual patterns". Broadcasters have both; a
living room has neither. Calm Frames is the signal analysis, run before a title
can be chosen, with the result signed and carried to the player. It reduces
exposure to flashing above published limits in the videos it plays; it is not a
medical device. The README's "Who it is for" section quotes both sources with
their dates and says what they are not: they are why the problem is real, not
where the thresholds come from.

Maya, a child used in the early design narrative, is a composite persona. I have
not yet collected feedback from families or clinicians, and I do not claim
clinical validation.

### What it does

Calm Frames is a Fire TV accessibility prototype for family entertainment and
multi-modal UX, with an offline video analyzer, a checked rendition pipeline and
a Vega player. The pipeline analyzes a source
against published flash limits, signs the resulting map and binds it to the
source's SHA-256. Its verification step must pass before publishing the prepared
title. Kid mode is designed to play a pre-covered rendition, with a live cover
as an additional layer.

Scene holds preserve a still from the preceding context during a hidden
interval. The pipeline checks these images and binds their identities to the
signed map. Missing images, decode failures or uncertain playback fall back to
an opaque cover. Captions and audio continue while the image is held: on the
Vega Virtual Device, both scheduled Harbor holds showed changing English captions
above the held picture, with non-silent audio recorded throughout. Physical
television behavior is not claimed.

Parents set room dimensions, profiles and a minimum preset behind a PIN. Those
settings persist locally, and storage errors block the library until resolved.
Stricter household choices can add hides but cannot relax the standard floor.
Voice transport, the D-pad and on-screen seek controls share the same guarded
seek path. The D-pad and on-screen paths were observed on the Vega Virtual
Device; the voice path is exercised by tests only, because the virtual device
has no Alexa to deliver a spoken seek.

There are also developer adoption paths: an analyzer and GitHub Action for
content preparation, a documented sidecar format, and a locally installable
Vega hook package. The hook has an offline consumer build check and a measured
integration patch for Amazon's sample player. Use by an independently maintained
app has not yet been demonstrated.

Calm Frames reduces exposure to flashing above published limits in the videos
it plays. It is not a medical device. It works only with content prepared for
this player; it does not cover other streaming apps or their DRM content.

### How I built it

The Python analyzer measures frames and their timestamps, produces per-preset
maps and signs them with Ed25519. The preparation pipeline builds the covered
rendition, posters and context images, then verifies its artifacts. The native
app uses Amazon's W3C media player, Media Controls, captions view and React
Native for Vega. A shared scheduler and seek function coordinate the cover.

The strongest design choice came from an observed failure: irregular player
position reports and a stalled JavaScript thread can make a live overlay late.
That is why the pipeline builds a pre-covered rendition, and why the app covers
when playback becomes uncertain. A verified signature ties the schedule to a
trusted signing key and the named source; it does not prove that the detector
found every hazard.

Checked local receipts can now export a bounded library into the app package.
The catalog binds each preset's prepared video, captions and maps to their exact
bytes, and the player refuses substituted delivery paths. Adding a title means
rebuilding the package. Arbitrary imports use the pre-covered picture with an
opaque live fallback; union scene images remain unfinished. The AWS CDK stack
has template tests and was deployed once, on Oct 9, 2026. A calm test clip went
through it twice that night: unsigned, it was analyzed and refused; signed, it
was published to S3, DynamoDB and CloudFront (section 11). The TV app does not
call AWS: its library is compiled into the package.

### Challenges I ran into

Our simulator timing record contains <!--n results/gate1_software_vvd.json:in_time -->48<!--/n-->
on-time trials out of <!--n results/gate1_software_vvd.json:trials_attempted -->55<!--/n-->
attempts. Six attempts produced no usable evidence, and one was late. Restricting
the denominator to the <!--n results/gate1_software_vvd.json:trials_counted -->49<!--/n-->
measurable trials would conceal the failed attempts. These are software events,
not camera measurements of a television. Physical screen timing is outside the simulator-only submission scope and is not claimed.

Detector evaluation also has material limits. The complete corrected synthetic conformance
run kept <!--n results/conformance_current_report_2026-10-02.json:published.clips_kept -->2999<!--/n--> of
<!--n results/conformance_current_report_2026-10-02.json:published.clips_designed -->3000<!--/n--> designed
clips. Overall recall was <!--n results/conformance_current_report_2026-10-02.json:published.flashmap_recall -->0.85<!--/n-->
over <!--n results/conformance_current_report_2026-10-02.json:published.flashmap_recall_denominator -->1268<!--/n-->
positive windows. Recall on positive windows near a limit was
<!--n results/conformance_current_report_2026-10-02.json:published.recall_near_limits -->0.469<!--/n-->
over <!--n results/conformance_current_report_2026-10-02.json:published.recall_near_limits_positive_windows -->358<!--/n-->
positive windows, and precision there was
<!--n results/conformance_current_report_2026-10-02.json:published.precision_near_limits -->0.573<!--/n--> over
<!--n results/conformance_current_report_2026-10-02.json:published.precision_near_limits_denominator -->293<!--/n--> flagged windows, against
<!--n results/conformance_current_report_2026-10-02.json:published.flashmap_precision -->0.649<!--/n--> pooled.
I publish the worse numbers beside the pooled ones because the worse ones limit the reliability claims we can make.
CI rebuilds the report from the saved rows on every push and fails if a byte differs. A matrix/range encoding correction changed the evaluation protocol, not detector thresholds or truth labels. Historical baseline comparisons were not rerun. Unit tests, signatures and benign demonstrations do not establish clinical safety or real-video ground truth.

### Accomplishments

The pipeline can reject a changed map or invalid rendition before publication.
All transport paths share a guarded seek. Context images use the same signed
descriptors in rendering and the live cover. Household state survives a restart
in integration tests, including PIN lockouts and stricter settings, and on the
Vega Virtual Device the saved profile, room size and distance, Broadcast preset
and chime setting survived a relaunch.

These behaviors have regression tests and deliberately broken controls. Native
Debug packages build for the configured architectures. Screen behavior, caption
composition and restart persistence were observed and recorded on the Vega
Virtual Device on Oct 9 and 10. Harbor's practice holds are kept out of the
exposure history on purpose, so an empty Kid history after a practice run is
the expected result; attribution of real covers to a profile is covered by
integration tests, not by a native run on hazardous source. Published
measurements point to versioned result files; inconclusive and failed
measurements remain visible alongside successful ones.

### What I learned

Detection, prepared-media integrity and screen delivery are separate problems.
A signature cannot correct a missed flash, and a passing software scheduler test
cannot establish when pixels reached a television. Keeping those boundaries
visible has made both the implementation and its claims more precise.

### What is next

Publish the checked English simulator demo after resolving submission fields.
The cut shows labelled practice intervals, captions and recorded sound. Extend the checked
packaged library to preserve signed scene images across preset unions. Ask
families and accessibility reviewers whether the flow and its limitations are
understandable, and record only feedback actually received.

### Built with

```
Vega SDK 0.24, React Native 0.83, TypeScript, Amazon W3C media player, Vega Media Controls, KeplerCaptionsView, Kepler UI and file system packages, AsyncStorage, Python 3.12, PyAV, FFmpeg, NumPy, Ed25519, pytest, Jest, GitHub Actions, AWS CDK, Amazon S3, Amazon CloudFront, Amazon DynamoDB, AWS Fargate on Amazon ECS, Amazon ECR, AWS Lambda, AWS Systems Manager Parameter Store
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

A project can win at most one track prize and one mini challenge prize. Open Source is the one to lead with: the analyzer, the Action, the sidecar specification and the hook are licensed under Apache-2.0 in the current private repository. The intended upstream fix is prepared but has not been opened publicly.

**Open Source remains incomplete.** It needs a qualifying public contribution and its URL; our private main repository alone does not establish that. **AWS Builder now has a deployed stack**: it went up on Oct 9, 2026 and ran a calm test clip twice (section 11). Whether a pipeline that prepares titles, rather than one the TV streams from, is what the judges want is theirs to decide, and section 11.2 says so. Describe only the work actually delivered when selecting mini challenges.

## 6. Repository URL

```
https://github.com/alejandro-publius/calm-frames
```

**NEEDS ALEX:** the current plan is to make the repository public during the
final checks on **Wednesday October 21**. Confirm Apache-2.0 is visible in
GitHub's About box before pasting this. Making it public is our chosen plan,
not the only route the rules permit. The rules rechecked on **October 1** also
allow a private repository shared with `testing@devpost.com` and Amazon's named
reviewers: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth` and
`emersonsklar`. If using that route, send invitations at submission and check
acceptance before the invitations expire after seven days. No permissions or
visibility have been changed by this documentation update.

## 7. Video URL

```
NEEDS ALEX
```

**Earlier local video is preserved:** `build/submission-redesign/Calm-Frames-demo-English.mp4`.
It is <!--n results/redesign_video_check.json:duration_s -->156.021<!--/n--> seconds,
in English with disclosed macOS Samantha synthetic narration, actual simulator
footage/stills and editorial cards. Its recorded duration/WCAG check passes.
The exact script is [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md); all shot sources
and hashes are in `results/redesign_demo_manifest_2026-10-10.json`. The current
cloud polish requires a Mac build, native validation and refreshed captures
before a matching demo can be published. Update its script, source manifest and
finished-file checks, then upload and verify the public URL while logged out.

Three checks before pasting:

1. `eval/check_video.sh <final file> --max-seconds 179` exits 0, and `results/redesign_video_check.json` is committed. It runs flashmap over the finished cut and, with that flag, refuses any file of 179 seconds or longer, which is the same gate the script and shot manifest require. Exit 2 means flashmap could not tell, and that is a failure too.
2. The link works while logged out, on YouTube or Vimeo, in English.
3. Any exposure-reduction claim must carry its limits. The on-screen plan uses "reduces exposure to flashing above published limits in the videos it plays; not a medical device". The English narration says detection can miss flashing and this is not a medical device. No seizure-prevention claim.

## 7a. Thumbnail, gallery image and "try it out" link

Devpost forms usually ask for a thumbnail or gallery image and offer a "try it out" link field. Neither had an assigned asset before Oct 9.

| Field | Proposed answer | State |
|---|---|---|
| Thumbnail or gallery image | [`docs/brand/firetv-app-icon-1280x720.png`](brand/firetv-app-icon-1280x720.png), the 1280 x 720 opaque Fire TV tile: the mark beside the wordmark and the line "A calmer way to watch". The approved design version passed the brand asset flash checks on Oct 10 ([`docs/brand/README.md`](brand/README.md)) | Proposed. Confirm the live form's accepted size and format on the day, and read the actual PNG before uploading |
| "Try it out" link | The judged release page, section 9, once it exists | **NEEDS ALEX.** No release has been published, so there is no link yet. Do not use a placeholder URL |

## 8. Required technologies

**First, what the rules actually ask of a Fire TV entry.** Alexa+, Bee and Ring entries have to demonstrate their track's required technology at runtime, imported and called. Fire TV is the exception. Quoted from the rules page, Submission Requirements, and copied into [`docs/RUBRIC.md`](RUBRIC.md) section 2.2:

> Fire TV: Any framework or language is acceptable (React Native, Android/Kotlin/Java, web technologies, etc.). The requirement is that the project runs on Fire OS or Vega OS. The demo video must show the project running on an actual Fire TV device or the Fire TV/Vega simulator.

So the hard Stage One line for our track is a video line, not a code line, and it is field 7 rather than this one. The table below goes past what the rules ask. It is here because it helps Technical Implementation and because an automated review can follow it, not because it is required.

Every row links a file and a symbol in the repository, and the README carries the five playback-path rows of this table with line numbers: [Required tech at runtime](../README.md#required-tech-at-runtime).

| Required technology | Package | Where it is called | What it does here |
|---|---|---|---|
| **W3C media player** | `@amazon-devices/react-native-w3cmedia` | `app/src/utils/VideoHandler.ts`, `new VideoPlayer()`, with Shaka attached | All playback. Calm Frames never replaces it and never lowers its opacity. It reads `currentTime`, `playbackRate` and the media events, and covers on top. |
| **W3C media player, video surface** | `@amazon-devices/react-native-w3cmedia` | `app/src/screens/PlayerScreen.tsx`, `KeplerVideoSurfaceView` | The hardware video layer at zIndex 0. The cover sits above it, which is what keeps the sound running while the picture is hidden. |
| **Vega Media Controls** | `@amazon-devices/kepler-media-controls` | `setMediaControlFocus` in `app/src/utils/VideoHandler.ts`; the safe handler is `app/src/calmframes/SafeMediaControlHandler.ts` | System and voice transport, and the path an Alexa "skip forward" arrives on. None of the handlers call `super`. Each one goes through `planSeek` in `app/src/calmframes/seekSafety.ts`. |
| **KeplerCaptionsView** | `@amazon-devices/react-native-w3cmedia` | `app/src/screens/PlayerScreen.tsx`, with `setCaptionViewHandle` | Captions at zIndex 2, above the cover. One captions view per process. This is why a hidden segment is still followable. |
| **Accessibility APIs** | `react-native` `AccessibilityInfo`, plus the `com.amazon.devconf.privilege.accessibility` privilege in `app/manifest.toml` | `app/src/calmframes/announce.ts`, with `accessibilityLiveRegion` and `accessibilityRole` on the card | VoiceView is told what is about to be hidden, in a queue rather than by interrupting. The cover itself is taken out of the accessibility tree, so VoiceView never reads a black rectangle. |
| **Kepler UI Components and `react-native-kepler`** | `@amazon-devices/kepler-ui-components`, `@amazon-devices/react-native-kepler` | Throughout `app/src/calmframes/` | Ten-foot focus management through `TVFocusGuideView`, the themed components and the seek bar. |
| **Kepler File System** | `@amazon-devices/kepler-file-system` | `app/src/calmframes/harnessConfig.ts` | Looks in the app's own data directory for a measurement run config at startup. On OS 1.2 the host cannot write a file there, so when none is found a debug build fetches the config over HTTP instead; a release build never asks the network. |

The whole guard is one hook, `app/src/calmframes/useFlashGuard.ts`. Give it a player and where the map is, and it verifies the map, builds the schedule, drives the cover, decides the card, announces it and hands back the one seek function every control has to use. It knows nothing about Calm Frames screens, navigation or storage, which is what makes it the thing another Vega app can drop in.

## 9. Testing instructions

```
Calm Frames is meant to be reviewed on the Vega Virtual Device. The earlier approved-design Debug
package from source 73fbbed was installed there on Oct 10. Its visible journey was observed and
recorded, with intermediate and final observations distinguished in
results/redesign_validation_2026-10-10.json.
The subsequent cloud design polish has not been built or installed on Vega.
Repeat native navigation, scrolling, settings, playback and recording checks
on the rebuilt package before presenting it as the reviewed release.
On the Apple Silicon development Mac, use the aarch64 package. This package
is not for an Intel Mac. The install/launch commands below are the ones used
for the native checks.

REVIEWABLE PACKAGE
  The judged release and SHA256SUMS have not been published yet.
  Release URL: pending approval and publication; do not use a placeholder URL.

BUILD AND RUN ON THE SIMULATOR
  Vega SDK 0.24.9914, Vega CLI 1.3.4, Node 22, Python 3.12 and JDK 21.
  From the repository root:

  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -e "./flashmap[dev]"
  source ~/vega/env
  eval "$(fnm env)" && fnm use
  export JAVA_HOME=/opt/homebrew/opt/openjdk@21
  cd app
  npm install
  npm run build:debug -- --target aarch64
  cd ..
  nohup vega virtual-device start > /tmp/calm-frames-vvd.log 2>&1 < /dev/null &
  vega device is-connected --device Simulator
  vega device info --device Simulator
  vega device install-app --device Simulator --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
  vega device launch-app --device Simulator --appName io.github.alejandropublius.calmframes.main

  Start only if stopped; wait for is-connected before installing.
  Debug builds retain app logs. Avoid vega device list on this SDK.

  .venv/bin/python -m eval.benign_native_smoke --device Simulator \
      --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg

  This is read-only preflight. After it succeeds, repeat with --execute
  --restart. Use the visible remote to complete setup, open Harbor: Scene hold demo, choose Watch demo, and play, pause and seek.
  English captions are included; the separate hero Watch now plays prepared Harbor.
  Buttons can also be sent from the host. This is the form that works on
  this CLI; the documented vega exec form looks for a missing host executable:

  vega device run-cmd --device Simulator \
      --command 'inputd-cli button_press KEY_DOWN'

  After relaunch without clearing data, check saved settings and the PIN gate.
  Observe the actual picture, captions and sound. Logs alone do not prove them.
  Harbor's practice holds are labelled practice and are kept out of the Kid
  exposure history on purpose, so an empty history after a practice run is
  the expected result, not a defect.
  A physical Fire TV stick and hardware timing recording are not required.

PARENTAL CONTROLS
  Parental controls are behind a four digit PIN, set during first-run setup.
  Family settings, the salted iterated PIN hash and lockouts are stored
  locally. Plaintext PIN digits are not saved. Storage errors block the
  library until resolved. On the Vega Virtual Device the saved profile, room,
  preset and chime setting survived a relaunch, and parental controls locked
  again after Credits Back.

  Fresh install: choose and confirm your own PIN in onboarding.
  Existing simulator: use its owner-provided PIN; the package has no preset PIN.

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
  The targets look for the repository .venv and use fnm when it is there;
  the plain commands they wrap are in the README under "Run the checks".

SAFETY, PLEASE READ
  Do not open any file under media/ with a HAZARD_ prefix in a player. They
  contain real flashing footage and they are in the repository's ignore list for
  that reason. Inspect them as luminance plots with eval/plots.py instead.
```

**Before publication:**

1. **First-run instructions.** Reviewers choose their own PIN on a fresh simulator. A package never transfers the current simulator's household record. If access to an already configured simulator is offered, provide its actual demonstration PIN separately.
2. **The release links.** The release does not exist yet, because the judged tag can never move once it is created and that is a person's decision. `make release` prepares an aarch64 Debug simulator package by default, writes `SHA256SUMS`, `PREPARATION.json` and `NOTES.md` into a new `build/release/<tag>/`, prints the `gh release create` line and stops. Other targets or Release builds must be selected explicitly. Once it is published, the links are:

   ```
   https://github.com/alejandro-publius/calm-frames/releases/tag/<tag>
   https://github.com/alejandro-publius/calm-frames/releases/download/<tag>/calm-frames-<version>-aarch64-debug.vpkg
   https://github.com/alejandro-publius/calm-frames/releases/download/<tag>/SHA256SUMS
   ```

   `<version>` comes from `app/manifest.toml` and `<tag>` defaults to `v<version>`. Paste the real ones here once the tag exists, and install the aarch64 release on the Vega Virtual Device before claiming that release was validated. [`docs/RELEASE.md`](RELEASE.md) has the full steps.

---

## 10. Product feedback

### 10.1 The five questions, once per tool

Amazon asks five questions about every tool an entry used. **The answers live in [`docs/FEEDBACK.md`](FEEDBACK.md)**, which covers eighteen tools: the Vega SDK and CLI, the Vega Virtual Device, `vega-video-sample`, the W3C media player, Vega Media Controls, KeplerCaptionsView, the accessibility APIs, AWS CDK, AWS Fargate on ECS, Amazon S3, Amazon CloudFront, AWS Lambda, Amazon DynamoDB, Amazon ECR, Systems Manager Parameter Store with KMS, AWS Budgets, the Kepler UI and file system packages, and GitHub Actions.

That file is the one to paste from, and it is deliberately the only copy, so this document cannot drift away from it. If the form wants the answers inline, paste `docs/FEEDBACK.md` from its "1. Vega SDK and Vega CLI" heading down to the "Feature requests" heading. Its "At a glance" table and sections 1, 2, 6, 7 and 18 were corrected on Oct 9 to match the body and the simulator-only scope, and again on Oct 10 against the native observations in `results/redesign_validation_2026-10-10.json`; re-read it once more on the day before pasting.

Two things a reader should know about it, which it says itself:

- Every complaint points at something that happened during the build, and the long version with exact commands and exact output is a numbered entry in [`docs/FRICTION_LOG.md`](FRICTION_LOG.md).
- The AWS sections answer from the night of Oct 9, 2026: one deploy, one update and two runs of a calm test clip. Each says where one night of use is all there is, rather than writing an operational opinion it has not earned.

The heaviest complaint, in one line each, is in that file's "At a glance" table.

### 10.2 Which AWS services we used, and how

**This block belongs in the Product Feedback answer, not in a field of its own.** The rules put the AWS Builder requirement inside this field: the Stage One checklist line reads "AWS Builder: which AWS services were used and how, inside the Product Feedback answer". So paste `docs/FEEDBACK.md` first, then paste this table at the end of the same box. Section 11 is the reasoning about whether we qualify at all, and it is not a substitute for having the table here.

**What ran, and when.** The stack was deployed once, on Oct 9, 2026, after Alex
confirmed HUMAN CHECKPOINT D. He ran `make deploy` in his own terminal, from a
detached worktree at commit c5724de, and approved the IAM changes at the CDK
prompt himself. `CalmFramesStack` in us-east-1 was created between 00:21 and
00:25 PDT, updated at 00:33 to give the ingest task a signing key, and stands at
<!--n results/aws_deploy_2026-10-09.json:stack_status -->UPDATE_COMPLETE<!--/n--> with
<!--n results/aws_deploy_2026-10-09.json:stack.resources_total -->42<!--/n--> resources and
<!--n results/aws_deploy_2026-10-09.json:stack.nat_gateways -->0<!--/n--> NAT gateways. A calm
marker clip, never a `HAZARD_` file, went through it twice. Unsigned, at 00:27,
the task ran <!--n results/aws_deploy_2026-10-09.json:runs.0.steps_run -->11<!--/n--> steps,
failed verify on the missing signature and published
<!--n results/aws_deploy_2026-10-09.json:runs.0.published_objects -->0<!--/n--> objects. Signed
with a cloud demo key, at 00:35, it ran
<!--n results/aws_deploy_2026-10-09.json:runs.1.steps_run -->12<!--/n--> steps, published
<!--n results/aws_deploy_2026-10-09.json:runs.1.published_objects -->16<!--/n--> objects and
wrote <!--n results/aws_deploy_2026-10-09.json:runs.1.catalog_rows -->1<!--/n--> catalog row,
and CloudFront served the title entry, a poster and the HLS master playlist. The
record is [`results/aws_deploy_2026-10-09.json`](../results/aws_deploy_2026-10-09.json),
written from read-only calls, with every account id, bucket name, domain, ARN
and repository URI left out.

Read each row as "how it is built, and what it did on Oct 9", and nothing more:
one night, one short calm clip, no real title and no load. **The TV app does not
call AWS.** Its library is compiled into the package, and the cloud demo key is
one the app does not trust, so a map made in the cloud plays on no TV
([`docs/SECURITY.md`](SECURITY.md), "A signing key in the cloud"). AWS is where a
title is prepared, not where it is watched.

| Service | How it is used | Why this one |
|---|---|---|
| **Amazon S3** | Two private buckets. `source` takes uploads and is never reachable from the internet; an upload under `uploads/` starts the pipeline. `delivery` holds kid-safe renditions, signed maps, posters and trickplay: <!--n results/aws_deploy_2026-10-09.json:read_back.delivery_objects -->16<!--/n--> objects after the signed run. | Object storage with a lifecycle rule for the raw uploads, which are the large and short-lived part. |
| **Amazon CloudFront** | Serves the delivery bucket through origin access control, so the bucket itself stays private. Signed URLs when a public key is configured; the Oct 9 stack has none, so it serves a title to anyone who has its path. A byte range request came back <!--n results/aws_deploy_2026-10-09.json:read_back.byte_range_status -->206<!--/n-->. | The app needs range requests and reasonable latency for HLS. Origin access control means no public bucket. |
| **Amazon DynamoDB** | The title catalog, on demand, keyed by the source file's SHA-256, with the same fields as the local JSON catalog. The refused run wrote no row and the signed run wrote one. | On-demand billing suits a workload that is quiet most of the time, and the hash key is the natural identity for a title. |
| **AWS Fargate on Amazon ECS** | The ingest task, ARM64, <!--n results/aws_deploy_2026-10-09.json:stack.task_cpu_units -->2048<!--/n--> CPU units and <!--n results/aws_deploy_2026-10-09.json:stack.task_memory_mib -->4096<!--/n--> MiB, running the same container as the local pipeline. | No servers to keep alive between titles, and the same image runs locally, so what CI tests is what runs. |
| **Amazon ECR** | Holds that image, <!--n results/aws_deploy_2026-10-09.json:image.size_mb -->279<!--/n--> MB, with ECR's basic scan on push. That scan reported <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.findings_total -->101<!--/n--> findings, <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.critical -->8<!--/n--> critical and <!--n results/aws_deploy_2026-10-09.json:image.scan_on_push.high -->56<!--/n--> high, all in Debian packages from the base image or the pinned ffmpeg, none in the Python packages. They are open: the image has not been rebuilt since. | It is where a Fargate task definition reads from, and its scan saw what our own audit does not cover. |
| **AWS Lambda** | A small function started by an S3 upload notification, which runs the Fargate task. | The plan rules out Step Functions and EventBridge while the cut list still has items on it, and one small function is the least machinery that does the job. |
| **AWS Systems Manager Parameter Store, with AWS KMS** | Holds the cloud demo signing key as a SecureString under the account's own `aws/ssm` key. The task role may read that one parameter, and decrypt it only through SSM. | The task gets a key without one in the image or its environment, and it is never a key the TV trusts. |
| **Amazon VPC** | Public subnets only, `nat_gateways=0`, the task gets a public IP. | The CDK default of a NAT gateway per availability zone would have been the biggest line on the bill. |
| **AWS IAM with GitHub OIDC** | **Defined and unit tested, not deployed.** The stack can make a deploy role for GitHub Actions to assume. The Oct 9 deploy left `githubRepo` empty, so neither the OIDC provider nor the role exists and no workflow can reach the account. The deploy ran from Alex's terminal with his own credentials. | No AWS access key is ever stored in the repository or in GitHub secrets. |
| **AWS Budgets** | A <!--n results/aws_deploy_2026-10-09.json:budget.limit_usd -->20<!--/n--> US dollar monthly budget with alerts at 50 and 80 percent of actual spend and 100 percent of forecast, counting costs tagged `Project=calm-frames`. That tag was not yet active for cost allocation on Oct 9, so the budget cannot alert anyone until it is. | A warning on a hobby project's spending, made in the same deploy as everything it watches. It is a warning, not a brake. |
| **Amazon CloudWatch Logs** | Task logs, kept <!--n results/aws_deploy_2026-10-09.json:stack.stack_log_group_retention_days -->14<!--/n--> days. Both runs' logs are there. | Retention means old logs stop costing money on their own. |
| **Cost allocation tags** | On everything in the stack, and on the CDK bootstrap and the SSM parameter. | So the bill can be read per project, once the tag is active. |

**Cost.** Estimated at <!--n results/cost_estimate.json:published.monthly_total_usd -->1.34<!--/n--> US
dollars a month for <!--n results/cost_estimate.json:assumptions.titles_per_month -->20<!--/n-->
titles of <!--n results/cost_estimate.json:assumptions.minutes_per_title -->10<!--/n--> minutes
each, from list prices read on Sep 17, 2026, and
<!--n results/cost_estimate.json:published.task_time_quadruple_usd -->2.52<!--/n--> if every ingest
task ran four times as long as the
<!--n results/cost_estimate.json:assumptions.task_minutes_per_title -->15<!--/n--> minutes
assumed. That task time is the estimate's largest unknown, and the Oct 9 runs do
not settle it, because a short calm clip says nothing about a full-length title.
It is an estimate, not a bill. The bill is the measure, and the budget above
cannot see it until the tag is active. The stack stays up until the results,
about Dec 3. `make destroy` then removes the stack, and the few pieces that live
outside it are removed by hand, as
[`pipeline/infra/README.md`](../pipeline/infra/README.md) lists under "Taking it down".

**What we would tell another builder.** Two things from before the deploy, and
four from the night itself. The `ec2.Vpc` default is one NAT gateway per
availability zone: two of them would add
<!--n results/cost_estimate.json:published.nat_gateways_would_add_usd -->65.7<!--/n--> US dollars a
month in hourly charges alone, far more than everything else in this stack put
together. Asserting on the synthesized template, before deploying anything, is
the cheapest safety net available. Then, on Oct 9: the CDK CLI has to be at least
the version the library declares, or it stops right after synth; export
`AWS_REGION`, because the CLI resolves its own region over `CDK_DEFAULT_REGION`;
bootstrap from a directory with no `cdk.json` in it; and deploy from a terminal,
because the IAM approval prompt needs one. All of it is written up in
[`docs/FEEDBACK.md`](FEEDBACK.md) sections 8 to 16.

---

## 11. AWS Builder mini challenge

### 11.1 What exists, stated plainly before anything else

The AWS work in this project is **an AWS CDK application in [`pipeline/infra/`](../pipeline/infra/), unit tested against its synthesized template and deployed once, on Oct 9, 2026.** Here is what that does and does not mean, with every number read from [`results/aws_deploy_2026-10-09.json`](../results/aws_deploy_2026-10-09.json):

- **The stack runs.** `CalmFramesStack`, in us-east-1, was created between 00:21 and 00:25 PDT from commit c5724de and updated at 00:33 to wire in a cloud signing key. At 02:50 it read <!--n results/aws_deploy_2026-10-09.json:stack_status -->UPDATE_COMPLETE<!--/n-->, with <!--n results/aws_deploy_2026-10-09.json:stack.resources_total -->42<!--/n--> resources, <!--n results/aws_deploy_2026-10-09.json:stack.nat_gateways -->0<!--/n--> NAT gateways and <!--n results/aws_deploy_2026-10-09.json:stack.outputs_total -->5<!--/n--> outputs.
- **A person deployed it, with the checkpoint confirmed first.** Alex confirmed HUMAN CHECKPOINT D, ran `make deploy` in his own terminal and approved the IAM changes at the CDK prompt: <!--n results/aws_deploy_2026-10-09.json:iam_approval.statement_rows -->20<!--/n--> statement rows, <!--n results/aws_deploy_2026-10-09.json:iam_approval.managed_policy_rows -->3<!--/n--> managed policies and <!--n results/aws_deploy_2026-10-09.json:iam_approval.security_group_rows -->1<!--/n--> security group rule. The checkpoint's credit request clause is void, because the form closed on Oct 7, and he waived it ([`docs/GATES.md`](GATES.md)).
- **It ran twice, on a calm marker clip, never a `HAZARD_` file.** Unsigned, at 00:27 PDT, the task analyzed the clip and refused to publish it, exit <!--n results/aws_deploy_2026-10-09.json:runs.0.exit_code -->1<!--/n-->: the fail closed rule, on AWS. Signed with a cloud demo key, at 00:35, it published <!--n results/aws_deploy_2026-10-09.json:runs.1.published_objects -->16<!--/n--> objects and <!--n results/aws_deploy_2026-10-09.json:runs.1.catalog_rows -->1<!--/n--> catalog row <!--n results/aws_deploy_2026-10-09.json:runs.1.seconds_upload_to_published -->66.5<!--/n--> seconds after the upload, and CloudFront served the HLS master playlist with HTTP <!--n results/aws_deploy_2026-10-09.json:runs.1.cloudfront_status.hls_master_playlist -->200<!--/n-->. The signed map had <!--n results/aws_deploy_2026-10-09.json:runs.1.flagged_segments -->0<!--/n--> flagged segments, so AWS has not yet produced a cover on any title, and a short calm clip measures neither a real title's time nor its cost.
- **The TV does not use it.** The cloud demo key is not one the app trusts, by design, so a map made in the cloud plays on no TV. The app's library is compiled into its package. AWS is where a title is prepared, not where it is watched.
- **Not deployed, on purpose:** the GitHub OIDC provider and deploy role, which are defined and unit tested, and CloudFront signed URLs.
- **The budget cannot warn anyone yet.** The <!--n results/aws_deploy_2026-10-09.json:budget.limit_usd -->20<!--/n--> US dollar budget counts costs tagged `Project=calm-frames`, and that tag was not active for cost allocation on Oct 9.
- **Nothing in the repository names the account.** The record was written from read-only calls with every account id, bucket name, domain, ARN and repository URI left out. [`docs/GATES.md`](GATES.md), [`docs/SECURITY.md`](SECURITY.md) and [`pipeline/infra/README.md`](../pipeline/infra/README.md) tell the same night in more detail.

**NEEDS ALEX:** activate `Project` as a cost allocation tag (Billing and Cost Management, Cost allocation tags, User-defined), so the budget can see the bill. [`pipeline/infra/README.md`](../pipeline/infra/README.md) has the steps.

### 11.2 Whether this qualifies, now that it is deployed

The rules page, Project Requirements, says:

> AWS Builder (Mini Challenge): Any primary track project that incorporates AWS services (i.e. Amazon Bedrock, AgentCore, Strands SDK, Kiro Crew, SageMaker, etc.) with documented integrations.

Neither the rules page nor the overview page defines "incorporates". Until Oct 9 the open question was whether a synthesized, unit tested, undeployed stack counts. That question is gone: the stack is deployed and has run. What a judge may still weigh is where AWS sits. It prepares titles: an upload becomes a checked, signed rendition, a catalog row and a CloudFront path. It is not in the playback path, because the TV plays a library compiled into its package. We say that plainly and let the judges decide, rather than claiming the prize for ourselves.

**Kiro Crew is a route we have not taken.** The rules say it qualifies on its own: "Kiro Crew qualifies on its own as a development tool used during the hackathon[,] a submission does not need to also call a runtime AWS service". **We have not used Kiro Crew and nothing in this submission may imply that we have.**

### 11.3 Which AWS services, and how

**The table is in [section 10.2](#102-which-aws-services-we-used-and-how), because that is the field the rules name.** It is one copy on purpose, so the two cannot drift. Twelve services and settings: S3, CloudFront, DynamoDB, Fargate on ECS, ECR, Lambda, Systems Manager Parameter Store with KMS, VPC with zero NAT gateways, IAM with a GitHub OIDC role that is defined but not deployed, Budgets, CloudWatch Logs, and cost allocation tags on everything.

**No credit request.** Requesting the 150 US dollar AWS credits is no longer a step: the form closed on Oct 7, 2026. Alex plans to use his existing AWS credits, but applicable-service coverage and actual billing application have not been verified; HUMAN CHECKPOINT D records the waived request ([`docs/GATES.md`](GATES.md), [`docs/DECISIONS.md`](DECISIONS.md)).

---

## 12. Open Source mini challenge

### 12.1 Contribution URL

```
NEEDS ALEX
```

**NEEDS ALEX:** the pull request has to be opened by **Monday October 12** so that this URL exists. The branch, the title and the body are prepared in [`docs/OPEN_SOURCE_PR.md`](OPEN_SOURCE_PR.md). It has not been opened and the branch has not been pushed anywhere, because opening it needs a fork under your own GitHub account. It does not need to be merged by the deadline, only opened.

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

A pull request to AmazonAppDev/vega-video-sample, Amazon's reference video app
for Vega, fixing a real playback defect we hit while building on it, with three
tests, two of which fail without the fix. Details, including the root cause and
the tests, are in docs/OPEN_SOURCE_PR.md in our repository.

Why it matters: every developer who starts from that sample inherits the bug.
A fix there is worth more than a fix in our own fork, because it is a starting
point rather than one app.

DOWNSTREAM

flashmap, an Apache-2.0 Python package that measures video against WCAG 2.2
Success Criterion 2.3.1, both the general flash and the red flash thresholds. It
ships as a library, a CLI, a signed sidecar format and a GitHub Action that
fails a pull request adding an image or video over the thresholds.

Why it matters. flashmap offers an open-source check that a studio or app developer can add to normal review with a file in .github/workflows/. Its implementation
slides the one second window to every position rather than using fixed buckets,
it slides the ten degree area window rather than measuring the whole frame, it
does the saturated red test in CIE 1976 UCS, it measures area on the picture
rather than on the letterbox bars, and it reads real container timestamps so
variable frame rate input comes out right. Every threshold it uses is quoted
with a link in SPEC_SOURCES.md, and the three values that could not be verified
from a primary source are named there and are not used as thresholds.

The sidecar specification is included in the repository so that a flash map can be portable: a studio
can ship one with a title and any player can honour it. The hook package ships
the playback side, so a Vega video app built on Amazon's W3C media player can get
the same scheduling and guarded-seek behavior by giving one hook a player and a trusted map. Integration still requires verification of content identity, keys and native composition.
```

---

## 13. Feature requests

**The full list is in [`docs/FEEDBACK.md`](FEEDBACK.md) under "Feature requests"**: twenty-one requests, each marked Critical, Important or Nice-to-have, each tied to something that happened during the build. Paste that table.

The scale, so the priorities read correctly: **Critical** means we could not do the right thing without it. **Important** means it cost real time or forced an undocumented workaround. **Nice-to-have** means it would be better.

The three Critical ones, because they are the argument:

1. **A system-wide Fire TV "dim flashing lights" setting**, in Accessibility settings, readable by any app the way `isScreenReaderEnabled` is readable now. Photosensitivity is a property of the person, not of an app. A child should not have to hope that the app they opened happens to have built protection. We would delete half of our own settings screen the day this ships.
2. **Document composited simulator capture and make remote automation easy to discover.** Historical QMP and macOS captures missed the app picture. A ScreenCaptureKit recording of the simulator window captured picture, captions and sound on Oct 9 and 10, and no Amazon page describes that route. Amazon's documented `inputd-cli` works from the host only as `vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'`; the documented `vega exec inputd-cli` form looks for a host executable that is not there.
3. **A way to get one frame of what an app drew, from inside the app.** The same gap from the other side: React Native 0.83 removed `takeSnapshot` and no `@amazon-devices` package replaces it.

Requests 2 and 3 come from actual capture failures during development. A host-side composited recording now works, so request 2 is about documentation and discoverability; request 3 remains open, because an app still cannot capture its own frame.

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

And two differences, because the precedent is not the same product. Apple's detection runs on the device, in real time, on the frames as they are drawn. Calm Frames analyses the whole title ahead of time, signs the result, and the player acts on a schedule rather than on what it has just seen, which lets preparation place a cover before a flagged interval. A live overlay alone has missed deadlines in simulator measurements, so this is not a guarantee about delivered screen timing. Apple's approach needs no cooperation from the app; ours needs a signed map, so it only ever protects content somebody measured. The two are complementary, and a system setting would make ours unnecessary for anyone who turned it on, which is the point.

---

## 14. Friction log

**The full log, in Amazon's six fields, is [`docs/FRICTION_LOG.md`](FRICTION_LOG.md).** Its table holds **forty entries: eight High, fifteen Medium and seventeen Low**. Each one has the task, the steps with the exact commands, expected and actual with the exact output, severity, the workaround we used, and a suggestion. Entries 1 to 28 and 36 to 40 are on Amazon's surface, 29 to 33 are the wider toolchain, and 34 and 35 are restricted local automation and GitHub Actions startup, not Amazon issues; the log says so in its own summary.

If the Devpost form wants the entries inline rather than a link, paste the body of that file from its "Summary" heading down. Nothing in it needs editing first.

The eight High entries, so the list reads in the right order:

| # | What broke |
|---|---|
| 12 | The device drops the app's own log output under load, so evidence a rate limiter can delete is not evidence |
| 14 | No way to get a frame of what the app drew, from inside the app or from outside it |
| 15 | No crypto API on the platform, so Ed25519 signature checking had to be written by hand |
| 22 | Playback on the virtual device is not steady, and the error says `UNKNOWN` |
| 26 | The player's `timeupdate` cadence and `currentTime` resolution are undocumented, and the reports are not regular |
| 35 | Every GitHub Actions Audit job failed before a runner or a step started, Sep 28 to 30. Not an Amazon issue. Hosted runners have run real steps since Oct 5, and the Audit workflow has been green in all four jobs since the Oct 11 push (`results/github_push_2026-10-11.json`) |
| 36 | A packaged `file:///pkg/...` URI is not opened by the native player |
| 37 | The native caption view cannot be stacked above a React Native image by z-index |

**NEEDS ALEX:** read the friction log and confirm you are happy for them to be published as written. They name real defects in Amazon's tools, in plain words, with the exact output. That is what the log is for, and it is still your name on the submission.

---

## 15. Team and entrant details

The confirmed entrant details are recorded below. Personal eligibility and contact details still require Alex.

| Field | Answer |
|---|---|
| Entrant name or team name | Alex Velazquez |
| Team members, if any | Solo entrant; no additional team members |
| Country of residence | United States (USA) |
| Eligibility confirmation | NEEDS ALEX |
| Contact email | NEEDS ALEX |
| Amazon developer account | Created and identity-verified, as confirmed by Alex |

Anything quoted from outreach goes in [`docs/VALIDATION.md`](VALIDATION.md), with permission, by **Friday October 16**.

---

## 16. Completion and approval checklist

Preparation, local tests and capture can proceed autonomously. Alex is needed for missing personal details and final approval to publish, submit, change visibility or incur additional cloud costs. October 12 and October 22 are planning targets; the hard deadline is October 23 at noon Pacific.

| # | What | When | Field it unblocks |
|---|---|---|---|
| 0 | **Done Oct 9: the AWS Builder question.** The stack is deployed and has run twice (section 11), so whether an undeployed stack counts no longer arises. Kiro Crew is a route we have not taken and must not imply we have | Done | 5, 11 |
| 0b | **Done Oct 9 to 10: simulator screen recording.** ScreenCaptureKit recorded the simulator window with picture and audio; the saved takes show both Harbor holds, their English captions and non-silent sound, and the record is `results/redesign_validation_2026-10-10.json` | Done | 7 |
| 0d | **Validate and record the cloud design polish.** Rebuild on the Mac, check native D-pad focus, scrolling, saved settings and playback, then refresh the demo, manifest, package hashes and review bundle to match | Before video or release publication | 7, 9 |
| 0c | **Activate `Project` as a cost allocation tag**, so the 20 dollar budget can see the bill. Until then it cannot warn anyone (section 11.1) | **Now.** A new tag can take up to a day to appear for activation | 11 |
| 1 | **Confirm the GitHub username** to credit on the Open Source fields, and which account forks the upstream repository | Before Mon Oct 12 | 12.3 |
| 2 | **Open the upstream pull request** from a fork under your own account, and paste the URL | By Mon Oct 12 | 12.1 |
| 3 | **Done Oct 9: first-run PIN instructions verified** on the simulator, including a mismatched confirmation and a Delete correction; no preset PIN is embedded in the package | Done | 9 |
| 4 | **Done Oct 9: HUMAN CHECKPOINT D.** The Paid plan and the 20 dollar budget are in place, and the credit clause is void because the form closed on Oct 7 | Done | 11 |
| 5 | **Any outreach reply you want quoted** goes into `docs/VALIDATION.md`, with permission | By Fri Oct 16 | 15 |
| 6 | **Done for the earlier build: English demo edited.** Actual simulator footage, labelled still captures, synthetic English narration, subtitles and source manifest. Refresh for the current polish under item 0d | Earlier build complete | 7 |
| 7 | **Done for the earlier build: finished-file check.** Duration below three minutes and WCAG check pass; receipt in `results/redesign_video_check.json`. Rerun on the refreshed cut | Earlier build complete | 7 |
| 8 | **Upload the video** and check the link works while logged out | Before Thu Oct 22 | 7 |
| 9 | **Read the forty friction entries** and confirm you are happy for them to be published as written | Before submission | 14 |
| 9b | **Merge PR #1 into main.** The hosted Audit and CI runs on the Oct 11 push (ba819dc) are green in every job, recorded in `results/github_push_2026-10-11.json`. A public repository shows main by default, and main does not yet hold the scene-hold work, so the merge has to land before item 10 and the judged tag is cut from main after it | Before **Wed Oct 21** | 6, 9 |
| 9c | **Send the three outreach emails** in `docs/outreach/`, overdue since Sep 18; `docs/VALIDATION.md` still says not yet | Now | 15 |
| 9d | **Send the Amazon sample licence clarification** in `docs/AMAZON_SAMPLE_LICENSE_REVIEW.md`, as an upstream issue or to the hackathon's Amazon contacts, and record where and when | By **Tue Oct 13** | 6 |
| 9e | **Review `scripts/audit_exceptions.toml`** at the final checks: re-run `make audit-update`, re-read both groups, move both `review_by` dates past Dec 3, and confirm the CC0 dedication of the Harbor artwork in `media/LICENSES.csv` | **Wed Oct 21** | 6 |
| 10 | **Make the repository public** and confirm Apache-2.0 shows in GitHub's About box | **Wed Oct 21**, during the final checks | 6 |
| 11 | **Publish the release** and paste the `.vpkg` links and the tag into the testing instructions | **Wed Oct 21**, after the final checks | 9 |
| 12 | **Confirm remaining entrant details**: eligibility and contact email; entrant name, country of residence and solo status are confirmed. Confirm the gallery image and "try it out" link on the live form (section 7a) | Submission day | 7a, 15 |
| 13 | **Press submit** at HUMAN CHECKPOINT G | **Thu Oct 22** | all |

Requesting the 150 dollar AWS credits used to be on this list. It is gone: the form closed on Oct 7, 2026, and Alex plans to use his existing credits. Their coverage of this stack and application to billed usage remain unverified.

The deadline is **Friday October 23 at 12:00 PT**. We submit a day early on purpose, so that a form problem on the day is a problem with a day left in it rather than a problem with an hour.
