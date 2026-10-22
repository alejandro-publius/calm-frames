# Replacement demo run of show

Prepared October 22, 2026 for the integrated build, not the submitted one. The
submitted candidate `bf2f615`, its installed package and the public video stay
the fallback until a replacement is recorded, reviewed and accepted by the
owner. Do not overwrite or re-upload the submitted video file. This page is a
plan, not a recording receipt.

**Build to record.** Source
<!--n results/release-validation-2026-10-22/validation.json:native.final_build.source -->d96c0886227f7dcfc5ae6584132a86b193359215<!--/n-->,
aarch64 Debug package SHA-256
<!--n results/release-validation-2026-10-22/validation.json:native.final_build.package_sha256 -->6914d157c76a0478588f63e222525754f1202990481e313b4e72422c93759090<!--/n-->.
Its checks are in [the release readiness report](../RELEASE_READINESS.md).
Confirm with `vega device run-cmd --device VirtualDevice --command 'vpm info
io.github.alejandropublius.calmframes'` that the installed SHA-384 is
<!--n results/release-validation-2026-10-22/validation.json:native.final_build.installed.sha384 -->4b815f37537e69a2949b55a0d44ff57d0a7b198fdbcba63fc24475a80b28879db94c6ead3f20fad4d25d94f455d59f2c<!--/n-->
before the take. Record only after the owner has reviewed the new light menu
palette on this build.

## Rules for the take

- App-only capture of the Vega Virtual Device window, with app audio. No
  microphone, webcam, desktop or other window. The owner unlocks the Mac;
  never work around a locked screen.
- Natural speed throughout. No speed changes, montage, flashing transitions,
  added music or stock voice. Move focus about one press every two seconds.
- Do not pause during playback: the virtual device records a black picture
  while paused.
- Play only the approved prepared titles. Never play test fixtures or anything
  from the recovery runner; its clips are generated, analysed and deleted in a
  temporary directory.
- Words on screen use the approved line: Calm Frames reduces exposure to
  flashing above published limits in the videos it plays; not a medical
  device. No comfort, seizure or clinical claim.

## One quiet take, about 2 minutes 40 seconds

| Time | Picture and action | Optional static caption |
|---|---|---|
| 0:00 to 0:10 | Home at rest: Ocean and Forest, nothing playing. | Calm Frames, prepared nature scenes on Vega |
| 0:10 to 0:20 | Select McWay Falls and open Details. Let it settle. | Five minutes at natural speed, then a still frame |
| 0:20 to 1:30 | Press Watch once. Leave 70 seconds of the scene uninterrupted. | None while it plays |
| 1:30 to 1:35 | Back once. Focus returns to Watch. | |
| 1:35 to 2:00 | Back to Home, select Acadia, open Details, then More info and Playback proof & details. | The record behind the selected edition |
| 2:00 to 2:20 | Step through 1 Source, 2 Prepared and 3 Selection, about four seconds each. | Source measured, prepared file checked, identities matched |
| 2:20 to 2:30 | Press Down through the analysis record: the record, the detected and covered periods, the WCAG analysis. | Every section is reachable with the remote |
| 2:30 to 2:40 | Back three times to Home. Hold a static end card with the credits below. | Credits |

The proof pages show measured findings and file identities; they do not play
the original video, and nothing on them authorizes playback. Acadia's page is
used because its report proves that the replacement picture was drawn. McWay's
page says what its report does not record ("version not recorded in this
report") and is a good alternative if time allows.

## What the recovery work contributes

Preparation recovery runs in the offline pipeline, not on the TV, so it is not
filmed. If the video mentions it, use a static card with numbers from
[the recovery evidence](../../results/preparation-recovery-2026-10-22/evidence.json):
<!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.passed -->16<!--/n--> of
<!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.scenarios -->16<!--/n-->
interruption and corruption scenarios recovered as expected, including real
SIGKILL restarts, and
<!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.killed -->24<!--/n--> of
<!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.mutations -->24<!--/n-->
deliberately broken guards were caught. Say "in our tests on one Mac", not more.

## Credits for the description and the end card

McWay Falls footage: MoneySavingVideos, "♥♥ Relaxing 3 Hour Video of a
Waterfall on an Ocean Beach at Sunset", CC BY 3.0
(https://creativecommons.org/licenses/by/3.0/), from Wikimedia Commons. Changes:
first five-minute excerpt, downsampled to 720p, H.264/AAC encoding, three-second
fade of the source audio at the end, extracted final-frame still. No endorsement
implied.

Acadia footage: NPS Video, Acadia National Park, public domain. No NPS
endorsement is implied. Other visible title art: NOAA Fisheries; NPS: G Litten.
No agency endorsement implied. Full credits: repository NOTICE and the app's
credits screen.

## Before publishing anything

Check the recording frame by frame for black frames and unrelated content, run
`eval/check_video.sh` on it, and keep it under 180 seconds. Publishing the new
video, changing Devpost or pushing this branch each needs the owner's specific
approval; none is given by this plan.
