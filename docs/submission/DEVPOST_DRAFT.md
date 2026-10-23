# Calm Frames submission copy

Updated October 21, 2026 for app source `110ba6e`. The exact build and test receipt
is [here](../../results/mcway-activation-2026-10-21/verification.json). This local
copy supersedes the old short-preview draft. Devpost draft 1187358 already contains
Calm Frames, but this latest wording has not yet been pasted into the live form.
Do not submit until native review, public demo and required personal answers are complete.

## Name and pitch

Calm Frames

A calmer way to watch on Vega: quiet nature scenes, family controls, and prepared
video checked against signed flash-analysis maps.

## Inspiration

A nature app should give a scene time to breathe. Early feedback exposed a gap:
short clips and changing scenes felt rushed. Calm Frames now includes a continuous
five-minute fixed-camera view of McWay Falls at natural speed. After it finishes,
the picture stays on its final frame until the viewer chooses Back. Earlier short
clips remain available through a stationary-first presentation with optional previews.

## What it does

A coastal map connects Ocean and Forest, title details, loading, playback and
return. Nothing plays automatically from Home. Watch is an explicit action;
pause/resume and Back keep control with the viewer. Parent settings and profiles
sit behind a PIN, and the interface respects reduced motion.

The app plays only prepared videos whose exact catalog membership and signed
flash maps match. The offline pipeline analyzes the source, prepares three preset
renditions, checks the delivered files and exports an authenticated bundle. During
flagged intervals the player retains an independent cover and guards seeks before
moving the playhead. “No flagged scenes” reports an analyzer finding, not a safety
certificate. Calm Frames does not intercept other apps or live TV and is not a
medical device. It has not been medically validated and cannot guarantee comfort
or detect every hazard.

## How we built it

The TV app uses React Native for Vega, TypeScript and the Amazon video sample's
W3C media stack. A Python pipeline uses ffmpeg for preparation and Ed25519 for
signed maps. The compiled approval registry identifies an exact bundle, catalog
hash and existing signer. Build checks verify the packaged bytes and reports;
the app checks route identity again before playback. No signing secret is needed
to build or run the already prepared catalog, and none is included in the repository.

The new McWay edition preserves five minutes at natural speed with no inserted
cuts or repeated loops. Its original nature audio fades over the last three seconds.
All three presets passed normal authenticated preparation and strict export checks.
The prepared namespace contains 129,255,687 bytes under the approved 128 MiB budget,
with Acadia, Sea otters and Forest retained.

## Challenges and results

The original short-preview experience did not meet the intended ambient use.
We changed the experience and media, rather than treating analyzer passes as
proof of comfort. Exact file identity also mattered: the authenticated runtime
is 299.9997 seconds, so the final-frame presentation checks that exact duration.

The integrated source passed 1,698 app tests (four skipped), TypeScript, lint with
zero errors and 108 warnings, and 94 Node checks. The aarch64 Debug package built
successfully with ABI and packaged-media validation. These checks establish code
and package behavior, not what a person sees or hears. This new edition has not
yet been installed or accepted through native picture/audio review; that remains
a prerequisite to recording the submission demo. Earlier simulator logs must not
be presented as acceptance of this build. No physical Fire TV validation is claimed.

## Product feedback grounded in observed development

- **Vega SDK/CLI:** existing SDK 0.24.9914 and Node 22 built the exact aarch64 Debug
  candidate. ABI checks and package validation are useful. Readiness should mean
  `vega device is-connected --device VirtualDevice`; process status alone is not
  enough. Clearer CLI examples for the VirtualDevice name and remote input would
  reduce setup friction. The repository records failures of `vega device list` and
  the host-side `inputd-cli` route on the existing SDK.
- **Virtual Device:** it provides an OS target without physical hardware. Earlier
  sessions recorded intermittent media-clock slowdown, including a minimal control
  outside this app, without a confirmed cause. Better playback and capture diagnostics
  would help. No claim is made that the current edition's native playback has passed.
- **W3C media:** media events and guarded seeks fit the playback model. Earlier
  packaged-MP4 runs found `getVideoPlaybackQuality` failed with code 50001 and the
  `/pkg/` path worked where `file:///pkg/` did not. A documented packaged-file URI
  and timing contract would make integration more predictable.
- **Amazon video sample:** provided the surface, captions and media-control wiring.
  Clearer failed-load reporting and versioned setup instructions would help.
- **AI assistance:** Codex/ChatGPT and Claude assisted development, investigation,
  editing and tests. The TV app does not call a generative-AI service at runtime.
  Personal learning and career-value survey answers are still for the submitter.

These are implementation observations. Do not invent an onboarding duration,
career benefit, learning rating or new personal recommendation.

## Credits and links

McWay footage and final-frame still: MoneySavingVideos, “♥♥ Relaxing 3 Hour Video
of a Waterfall on an Ocean Beach at Sunset,” CC BY 3.0.
Source: https://commons.wikimedia.org/wiki/File:%E2%99%A5%E2%99%A5_Relaxing_3_Hour_Video_of_a_Waterfall_on_an_Ocean_Beach_at_Sunset.webm
License: https://creativecommons.org/licenses/by/3.0/
Changes: first five-minute excerpt, 720p downsampling, H.264/AAC encoding,
three-second final audio fade and extracted final-frame still. No endorsement implied.
Acadia: NPS Video; Sea otters: NOAA Fisheries; Forest: NPS: G Litten. See NOTICE.

Repository for judges: https://github.com/alejandro-publius/calm-frames/tree/claude/ocean-layout-fix-2026-10-19
The repository remains private with the authorized judge access. No new public
code release or Open Source mini-challenge entry is claimed. Primary track: Fire TV
on Vega OS. Current app/local workflow does not call AWS. Public demo URL is pending;
never insert an older demo as if it showed this build.
