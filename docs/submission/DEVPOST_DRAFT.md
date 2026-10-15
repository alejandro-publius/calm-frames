# Devpost description, draft

Updated October 15, 2026 for private branch
`codex/prepared-video-slice-2026-10-15`, app source `21f0ea6`. Not submitted.
The exact package and per-check limits are in [the handoff](../../FINAL_HANDOFF.md).
Review the live form's field names and limits before pasting. Final release,
licensing, reviewer access and publication remain owner decisions.

## Project name and tagline

Calm Frames. A calmer way to watch.

## The problem and audience

Families affected by photosensitive epilepsy need understandable choices
about the video they play. Calm Frames explores a narrow approach: analyze
supported videos in advance, prepare covered versions, and explain the result
before playback. Parents control the household settings; children use a TV
remote to choose from the verified library.

## What it does today

The Vega OS app includes Harbor and an owner-approved Acadia coastal clip.
Harbor has no detector findings. Acadia's analysis separates two distinct
detected periods from the longer picture-cover times for the selected preset.
Its record identifies the original source, prepared rendition, maps and
preparation report. Playback uses the prepared file, not the original source.
The coastal illustration is decorative and is labelled as such.

Each compiled catalog has its own exact trust scope. Source and rendition
hashes, signed maps and retained reports bind the selected title to the files
that play. A missing or mismatched record blocks playback. Acadia approval is
limited to its exact bundle and existing public key; it does not authorize
other videos signed with that key.

Harbor's separate Try the demo flow schedules two simulated picture pauses.
It teaches the mechanism without claiming those pauses were detected in
Harbor. Back returns one level at a time. Cancelling the Parents PIN gate
returns focus to Parents.

The TV transport uses a seek bar. Left and Right choose a position and Select
confirms it through the guarded seek path. An automotive-only Forward button
is not part of this TV interface. A follow-up fixed background Home/Details
controls remaining focusable behind playback. Source and native results are
recorded separately in the current receipt.

Household presets, room settings and profiles are protected by the parent's
PIN. Optional selection sounds and artwork motion are off by default. The
existing quiet local sound is retained, with held Select/Enter repeats
suppressed. No household preference was changed for the latest checks.

The interface retains Fraunces headings, Source Sans 3 controls, ivory and
teal reading areas, terracotta accents and dimensional coastal art. Analysis
comes before playback so the result and its limits can be understood first.

## How it is built

The Python analyzer measures supported SDR video against its documented WCAG
and broadcast profiles. The pipeline prepares renditions and maps, verifies
the package and retains an evidence report. The React Native app runs on Vega
OS, verifies its compiled catalog and uses a shared guarded seek function.
The reusable analyzer, Action, sidecar format and hook are licensed project
components; the repository is currently private, so no public contribution
URL is claimed here.

An AWS CDK pipeline was deployed on October 9. Its historical record includes
an unsigned input being refused and a signed input being published. October
15 offline infrastructure and ingest checks passed. The current TV app plays
its compiled library and does not call AWS. Live deployment, security findings,
budget coverage and billing have not been reverified in this pass.

## What the evidence establishes

- The current app suite passes <!--n results/transport-focus-2026-10-15/receipt.json:tests.appPassed -->1313<!--/n--> tests and <!--n results/transport-focus-2026-10-15/receipt.json:tests.snapshots -->57<!--/n--> snapshots across <!--n results/transport-focus-2026-10-15/receipt.json:tests.appSuites -->131<!--/n--> suites.
  Typecheck, package checks and lint pass, with existing lint warnings retained.
- Native logs identify the selected files and report playback, cover events
  and focus requests. The current receipt gives each journey's outcome.
- All seven earlier cover-positive source files remain locally and match the
  historical ledger hashes. A fresh headless Irminger waves check reproduced
  the historical findings; numeric comparisons checked every covered frame
  in its three retained renditions. This adds no video or trust to the app.
- Claude's detector test/specification review is integrated as tests/docs only;
  the <!--n results/detector-review/integration.json:tests.passed -->22<!--/n--> focused boundary tests pass. No production detector or media changed.
  This is not independent detector or clinical validation.

## Limits and what remains

Calm Frames reduces exposure to flashing above published limits in the videos
it plays; not a medical device. Detection can miss flashing. It does not filter
other apps, arbitrary streaming services or DRM content.

The analyzer works on a reduced analysis frame; small source features can be
averaged away. The broadcast profile assumes a display luminance model. HDR,
certain exceptions and loop-seam analysis remain unsupported. Engineering
tests and matching covered frames do not establish medical effectiveness.

Current native checks are simulator text-log observations. They do not prove
visible focus, compositor timing, sound, captions, VoiceView or physical-TV
behavior. Owner visual/audio acceptance and an authorized current demo video
remain open, as do release selection, licensing and reviewer access.

## Track and supporting material

Primary track: Fire TV, using Vega OS. Open Source and AWS Builder are optional
mini challenges. For Open Source, choose an eligible public contribution URL
only after publication approval; a PR is not mandatory. AWS Builder uses the
dated deployment record and must not imply fresh live verification.

[Product feedback](../FEEDBACK.md) and the [friction log](../FRICTION_LOG.md)
retain their evidence and dates. The owner must approve their publication.
See [the readiness matrix](CHECKLIST.md), [open decisions](OPEN_DECISIONS.md)
and [demo draft](DEMO_SCRIPT.md) before submission.
