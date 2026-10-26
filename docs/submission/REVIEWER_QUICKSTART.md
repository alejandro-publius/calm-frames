# Reviewer quickstart

Use the public **main** branch. It contains the consolidated native prototype and
reviewed fixes; the old private-branch instructions are superseded. The historical
[2:31 demonstration](https://www.youtube.com/watch?v=6lAP1FH16vc) shows an earlier
build, not current main. No accepted public downloadable release is provided.

Calm Frames explores within-app prepared-media playback for people with
photosensitive epilepsy and their caregivers. It is not a medical device or
clinically validated, cannot guarantee seizure prevention, and does not intercept
other apps or arbitrary streams.

## Source and toolchain

```sh
git clone --branch main https://github.com/alejandro-publius/calm-frames.git
cd calm-frames
git rev-parse HEAD
```

Record the full SHA with any build or recording. Source `b91a1f2c059b680b53b4e3fd1a9866147a9e5f01`
produced the existing local aarch64 Release candidate; its app tree is
`107bbfe311d77de44b319bf3a13db77723aa0901`, unchanged on documentation main
`800f14d8b094e2582819a7a83caa9ad8c74dc529`. Those identities are provenance,
not a download or a promise that a fresh build has identical package bytes.

| Tool | Recorded native build environment |
|---|---|
| Vega SDK / CLI | 0.24.9914 / 1.3.4, installed and configured through Amazon |
| Node / npm | 22.23.2 / 10.9.8 |
| JDK | 21 |
| Python | 3.12 for pipeline/checks |
| ffmpeg / ffprobe | Available for media analysis; native catalog review needs no new analysis or signing key |

A fresh public-clone-to-native-build has not been certified. Use this checkout's
lockfiles and normal gates. The existing prepared catalog needs no private
signing key, cloud account or shared PIN. A new household chooses its own PIN;
never include it in logs or recordings.

## Build and install on an isolated device

With Node 22 selected and the licensed Vega SDK/JDK environment configured:

```sh
cd app
npm ci --ignore-scripts
npm run setup:player
npm run check:native-inputs
npm run build:debug
```

These are reproduction instructions, not a new test pass. The build checks
approved editions, original verification reports, package identity and budget.
If a required input is missing, stop and resolve it; do not skip its gate.
[Release preparation](../RELEASE.md) describes the complete inventory rules.

Choose an expendable virtual device with fictional household data using the SDK
device panel. Verify its identifier before installing; do not overwrite an
existing household. Replace the placeholder below with that identifier. The
shown package is the Apple Silicon aarch64 Debug output; use the corresponding
architecture output on another supported host.

```sh
REVIEW_DEVICE='YOUR_DISPOSABLE_DEVICE_ID'
vega device install-app --device "$REVIEW_DEVICE" \
  --packagePath build/aarch64-debug/calm-frames-app_aarch64.vpkg
vega device launch-app --device "$REVIEW_DEVICE" \
  --appName io.github.alejandropublius.calmframes.main
```

## What to review

Home opens without automatically playing. Select McWay Falls and choose Watch.
Its prepared edition provides five minutes at natural speed, then holds its
final picture until Back. Acadia, Sea Otters and Forest have stationary defaults
and separately selected short previews. The acquired Australian woodland is not
an activated title. Returning to the same profile and edition offers Resume or
Start over when a checkpoint exists.

Use More info for protection/edition details and Parents for per-profile settings.
Reading comfort enlarges specified help text and spacing; it is not treatment.
The [caregiver computer workflow](../overnight-2026-10-25/personal-import/README.md)
handles raw-file selection/analysis. The [TV report inbox](../PERSONAL_REVIEW_INBOX.md)
reads reports; it does not grant trusted playback approval or import arbitrary
movies into Watch. New exact-edition activation still needs existing signing
and explicit approval. Do not create a new trust root to review the bundled app.

## Evidence and release boundary

The [original checklist](../cloud-integration-2026-10-23/CHECKPOINT.md) separates
completed outcomes from unresolved criteria. The current local Release was
built and source-bound native observations exist; Debug success alone is not
Release acceptance. Pale-opening repair, Reading comfort, error/retry and
navigation records retain their stated sources and limits.

Audit still reports four advisories/nine high dependency nodes and two expired
review groups. Reliable actual-pause VoiceView speech remains unresolved.
Flagged-interval recovery and supported-caption native observations are not
complete, and the consumer catalog has no caption tracks. The edited replacement
demo is unfinished. There is no physical-device timing, medical or universal
comfort claim. The [native limitations](../overnight-2026-10-25/NATIVE_LIMITS.md)
are retained.

The repository and its [Apache 2.0 license](../../LICENSE) are public. Reviewer
access is already provisioned; no access expansion is needed for these
instructions. The closed Devpost form prevents confirming saved track,
mini-challenge, feedback and pending-team answers. Repository drafts and public
tags do not establish what was submitted. [Submission status](../SUBMISSION.md)
keeps those boundaries separate from source/build access.
