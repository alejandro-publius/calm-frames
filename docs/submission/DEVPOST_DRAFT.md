# Devpost description, draft

Draft of Oct 14, 2026 for the Fire TV track. Not submitted. Every number is a
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
the limits, so it simply plays. The practice version, "Try picture holds", is
the same film with two scheduled holds, so a family can see the player work.
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

**How it works, in the app.** A short page in plain words: supported titles
only, and detection can miss flashing.

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
offers no way to capture a frame of what it drew, so native evidence is a host
side screen recording of the composited window, not a log line.

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

- The complete family journey was observed on the Vega Virtual Device: setup
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
- The current interface design has been built but not yet observed on the
  device; the observations above are of earlier builds of the same app.
  [Replace with the final build's receipt before pasting.]

## Not shipped, planned

A native run and demo video of the final design; the upstream pull request to
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

Primary track: Fire TV (family entertainment, multi-modal UX). Mini challenges:
[Open Source: contribution URL needed] and [AWS Builder: owner decision].

## Links to fill in

Repository: <https://github.com/alejandro-publius/calm-frames>. Video URL:
[none yet]. Release or "try it out" link: [none yet; do not use a placeholder].
