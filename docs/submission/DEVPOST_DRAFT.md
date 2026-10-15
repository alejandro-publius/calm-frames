# Devpost description, draft

Draft of Oct 14, 2026 for the Fire TV track, reconciled Oct 15 against
candidate head `a3368a9e` and package 5 from `4016e8d`. Not submitted.
Every number is a
marker against a file in `results/`, checked by `eval/readme_sync.py`. Replace
the bracketed items before pasting; they are the facts that do not exist yet.

## Project name

Calm Frames

## Tagline

A calmer way to watch

## The problem

A flashing scene can end a family's movie night when a child has photosensitive
epilepsy. The Epilepsy Foundation's photosensitivity page says that "for about
3% of people with epilepsy, exposure to flashing lights at certain intensities or
to certain visual patterns can trigger seizures", and that it "is more common in
children and adolescents" (quoted with its date in the README). Broadcasters have
signal analysis and trained inspectors; a living room has neither. Hiding the
picture is the obvious fix, and it throws away the story: the child loses the
sound, the captions and the context.

## Who it is for

Families where a child has photosensitive epilepsy, with a parent who sets the
app up once and a child who uses the remote. Secondly, studios and app developers
who want to check content before it ships: the analyzer, the GitHub Action, the
sidecar format and the player hook are open source.

## What it does today

Calm Frames is a Vega OS app for Fire TV with a small library compiled into it.
Every title was analyzed frame by frame before it could be chosen, and the
result is a signed flash map bound to the file's hash.

**Picture holds on supported titles.** When a title's map marks a flashing
interval, the player covers the picture before that interval starts and shows a
checked still from just before it, while the sound and the captions keep going.
A card says what is happening. A countdown and a Skip appear before a practice
hold. The ordinary Harbor film has zero holds, because nothing in it goes over
the limits, so it simply plays. The practice version, opened from Details with
"Try picture holds", is the same film with two scheduled holds, so a family can
see the player work.
Those two holds are examples, not detected flashing.

**Parental controls behind a PIN.** Profiles, a viewing preset (Standard,
Broadcast or Extra cautious), the television size and seating distance, a
warning chime before a hold, and two optional interface effects that are off
unless a parent turns them on. Household settings can only make the app
stricter than the published limits, never looser. The record is saved locally
with a salted PIN hash; no PIN digits are stored.

**One guarded seek.** The D-pad, the on-screen controls and the system transport
that Alexa requests arrive on all go through one function. A target inside a
flagged interval is covered first, then sought. A missing, unsigned, stale or
mismatched map keeps the picture hidden.

**How it works, in the app.** Four short lines: who it is for, every video
checked before it plays, the picture holding while the sound continues, and
that detection can miss flashing.

**The screen itself.** An ivory and teal coast with dimensional artwork: a
seated figure on a rock, a lighthouse island, a boat. Home is one heading,
"Calm Frames", with Play and Details; How it works and Parents sit in the header.
Details carries Harbor's length and hold count and the quiet Try picture holds
entry that opens the practice demo. Playback keeps dark controls over the
video. Text is sized for a room and every focused control shows a ring.

## How it is built

- **flashmap**, a Python analyzer that measures video against WCAG 2.2 Success
  Criterion 2.3.1, general and red flash, with a stricter broadcast profile. It
  slides the one second window and the ten degree area window, reads real
  container timestamps, and signs its map with Ed25519. Every threshold is
  quoted with a link in `flashmap/docs/SPEC_SOURCES.md`.
- **A preparation pipeline** that builds a pre-covered rendition, extracts and
  signs the scene stills, and runs a verify step that must pass before a title
  can be published. Verify refuses a map whose signature it cannot check.
- **The Vega app**: React Native 0.83 on Vega SDK 0.24, Amazon's W3C media
  player with Shaka, Vega Media Controls, one KeplerCaptionsView above the cover,
  and the accessibility APIs so VoiceView is told what is about to be hidden.
- **A drop-in hook** (`hook/`) so another Vega video app built on the W3C media
  player can get the same scheduling and guarded seek by handing one hook its
  player and a trusted map.
- **A GitHub Action** that fails a pull request adding an image or video over the
  thresholds.
- **AWS**: a CDK stack (S3, Lambda, Fargate on ECS, DynamoDB, CloudFront,
  Parameter Store with KMS, a budget) deployed once on Oct 9, 2026. A calm test
  clip went through it twice: unsigned, it was analyzed and refused with exit
  code <!--n results/aws_deploy_2026-10-09.json:runs.0.exit_code -->1<!--/n-->;
  signed, it was published as
  <!--n results/aws_deploy_2026-10-09.json:runs.1.published_objects -->16<!--/n-->
  objects and <!--n results/aws_deploy_2026-10-09.json:runs.1.catalog_rows -->1<!--/n-->
  catalog row. The TV app does not call AWS; its library is compiled into the
  package, and the cloud demo key is one the app does not trust.

The project is new: its first commit is dated Sep 17, 2026, inside the
Submission Period.

## Challenges

A live overlay can arrive late. The player's position reports are irregular and
a stalled JavaScript thread delays everything, which is why the pipeline builds
a pre-covered rendition as the first layer and the app covers whenever playback
becomes uncertain. The device also drops the app's own log output under load and
offers no way to capture a frame of what it drew from inside the app. Its logs
record reported app events; confirming the composited picture and sound needs
direct observation or an authorized host side recording.

Detection is the honest limit. On the corrected synthetic conformance run,
overall recall was
<!--n results/conformance_current_report_2026-10-02.json:published.flashmap_recall -->0.85<!--/n-->
but recall on windows near a limit was
<!--n results/conformance_current_report_2026-10-02.json:published.recall_near_limits -->0.469<!--/n-->;
precision was
<!--n results/conformance_current_report_2026-10-02.json:published.flashmap_precision -->0.649<!--/n-->
overall and
<!--n results/conformance_current_report_2026-10-02.json:published.precision_near_limits -->0.573<!--/n-->
near a limit. The worse numbers are published beside the better ones because
they are the ones that bound what the app can promise.

## Accomplishments

- On earlier builds, the complete family journey was observed on the Vega
  Virtual Device: setup
  with a PIN, a wrong PIN rejected and corrected, browsing with the remote,
  both practice holds with changing English captions over continuing sound, the
  prepared Harbor playing through, pause, Skip and Back with visible focus
  (`results/redesign_validation_2026-10-10.json`,
  `results/polish_native_validation.json`,
  `results/native-checkpoint-2026-10-14/receipt.json`).
- The safety guards are tested by breaking them:
  <!--n results/mutation.json:totals.killed -->68<!--/n--> of
  <!--n results/mutation.json:totals.mutations -->70<!--/n--> deliberate mutations
  are caught, and the two survivors are written up as equivalent edits.
- Fail closed was shown on AWS as well as in tests: the unsigned clip was refused.
- A bounded reliability pass on Oct 14 made a failed player setup reach the
  recovery screen at once instead of after a timeout, with the regression
  recorded in `results/core-reliability-2026-10-14.json`.
- The same night a remote-driven session on the Vega Virtual Device, judged
  from the app's own log, found two device-only defects and both are fixed with
  tests: the signed hold still was refused as a data URI and showed black, so
  the practice holds now draw bundled copies checked byte for byte against the
  signed map; and the opening shell waited for a frame counter the device never
  fills, so every playback reached the recovery screen, and it now readies on
  a moving clock. After the fixes the session reported cold launch, browsing,
  Details and return focus, Harbor start to finish with zero holds, pause and
  resume, both practice holds with the still loading, Help, the Settings gate
  and a relaunch (`results/native-acceptance-2026-10-14/receipt.json`).
- Package 5 from `4016e8d`, with the simplified Home and one-voice copy,
  reported eight journeys in a later log-driven session: cold launch, Home
  controls, Details and return focus, ordinary Harbor, the practice page and
  both holds, How it works, the Parents PIN gate and relaunch
  (`results/native-acceptance-5-2026-10-14/receipt.json`). Package 4's
  second pass separately reported pause and resume, the caption control and a
  cover-first remote seek (J10b,
  `results/native-acceptance-4-2026-10-14/second-pass.json`). These are
  software observations; the current candidate's pixels and audio remain
  unobserved.
- Every published number traces to a results file and CI fails on drift.

## Limitations

- Calm Frames reduces exposure to flashing above published limits in the videos
  it plays; it is not a medical device. Detection can miss flashing.
- It works only with content prepared for this player. It does not filter other
  streaming apps or their DRM content, and it makes no claim about Netflix,
  Prime Video or any other service.
- All observations are from the Vega Virtual Device. No physical television
  timing was measured, and no clinical validation or feedback from families or
  clinicians exists yet.
- The current candidate's package 5 (`4016e8d`) was driven on the Vega
  Virtual Device and judged from its own log; nobody has yet looked at its
  pixels or listened to its sound. The parent settings interior, VoiceView and
  the caption menu's contents also remain unchecked. [Replace with the owner's
  receipt before pasting.]
- On the device the practice holds draw bundled copies of their signed stills;
  a prepared title whose still is not bundled would show black during a hold.
- It runs on Vega OS and has only run on the Vega Virtual Device. Fire OS
  devices, which is most Fire TV sticks and Cubes in homes today, cannot
  install it.

## Not shipped, planned

Native visual and audio acceptance and an authorized demo video of the final
design; the upstream pull request to
Amazon's `vega-video-sample`; signed scene stills for arbitrary imports across
preset unions; and asking families and accessibility reviewers whether the flow
and its limits are understandable.

## Built with

Vega SDK 0.24, React Native 0.83, TypeScript, Amazon W3C media player, Vega
Media Controls, KeplerCaptionsView, Kepler UI components, AsyncStorage, Python
3.12, PyAV, FFmpeg, NumPy, Ed25519, pytest, Jest, GitHub Actions, AWS CDK,
Amazon S3, CloudFront, DynamoDB, Fargate on ECS, ECR, Lambda, Systems Manager
Parameter Store.

## Track and mini challenges

Primary track: Fire TV (family entertainment, multi-modal UX). The mini
challenges are optional and do not block this submission: [Open Source: needs
a public contribution URL, such as the prepared fix published in a public fork
or branch under Alex's account; a PR is optional and need not be merged. Two
production patches and a third test patch are ready in `docs/upstream-pr/`; private
patch files alone do not establish the entry] and [AWS Builder: the CDK stack
is deployed and described in `docs/SUBMISSION.md` section 10.2; Alex decides
whether to enter].

## Friction log

Friction log, 44 entries in Amazon's six fields:
<https://github.com/alejandro-publius/calm-frames/blob/main/docs/FRICTION_LOG.md>.
Until the candidate is merged the file is on `claude/final-candidate-2026-10-14`
at the same path. An Amazon organizer answered on the Devpost forum (topic
45430, "Inquiry about submission mechanics", read Oct 14, 2026) that a link
in the description is fine and that saving the log in the same repository is
easier for the judges, so the link goes here and the log stays in the
repository. The same answer says judges' credentials belong at least in the
testing instructions; Calm Frames has no login, and the parent PIN is chosen
on first run, which the testing instructions say.

## Links to fill in

Repository: <https://github.com/alejandro-publius/calm-frames>. Video URL:
[none yet]. Release or "try it out" link: [none yet; do not use a placeholder].
