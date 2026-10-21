# Devpost description, draft

Current build note, October 21, 2026: the integrated Ocean/Forest flow and exact
approved moving Acadia replacement were built and installed on the Vega Virtual
Device using existing Node 22, Vega SDK 0.24 and JDK 21. The aarch64 Debug package
SHA256 is 82f04537767853d6fcb3c6cdc3a177342b35dc894ebf32ae2d7beb1e1283d00e.
Native text traces cover all three approved titles, pause/resume, guarded Skip
and Back. Picture/audio acceptance is unverified: app-only framebuffer capture
returned black. No new demo video was recorded.

Draft for the owner, updated October 21, 2026. Intended candidate branch:
`claude/ocean-layout-fix-2026-10-19`. Not submitted. The official overview and rules
were re-read October 21: deadline October 23 at noon Pacific; a publicly visible
YouTube/Vimeo demonstration and judge-accessible repository are required. Final
submission constitutes agreement to the rules. Browser access to the existing
Devpost draft is currently unresolved, so its ownership, current content and
submission status have not been verified. Preserve its existing text when editing.
Measured research numbers below retain their original results-file references;
they are separate from the final integrated-source checks: 1,687 app tests,
77 Node checks and 41 release tests passed, TypeScript passed, and lint reported
zero errors and 108 warnings. Bracketed notes are not submission copy.

## Name and tagline

**Calm Frames.** A calmer way to watch.

Calm Frames checks a video for flashing before it reaches the TV, then covers those scenes
during playback while any sound continues.

## Who it helps

Households where someone is sensitive to flashing light, such as a child with photosensitive
epilepsy, and the parent who chooses what they watch. Flashing is hard to spot before it is on
screen. Calm Frames shows the household, before anyone presses play, which parts of a video
will be covered.

## What it does

### On the TV today

The app runs on the Vega Virtual Device. The integrated Ocean and Forest Home,
shared map loading states and approved three-video library were built, installed
and exercised with bounded native text checks on October 21. Visual and audio
acceptance remain unverified.

- **Three prepared videos on a map.** Home is a static coastal map. "Ocean" names the
  Acadia and Sea otters islands and "Forest" the third. Acadia is a public-domain National
  Park Service clip; Sea otters is a 19.987-second silent NOAA Fisheries excerpt that plays
  once; Forest is a 12-second NPS creek with nature audio that plays once. Each card gives
  its sound and length. Watch and Details sit below the cards, with Watch focused when Home
  opens. Moving to a card chooses it and a boat marks the chosen island; Select on a card
  opens Details with Watch focused.
- **Know before you watch.** Details says, for the household's setting, how many scenes
  will be covered or replaced and for how long, with a still timeline; a video with none
  says "No flagged scenes", which is what the analyzer found, not a safety certificate.
  Source attribution and the audio explanation are in More info.
- **Scenes replaced with protection retained.** During flagged scenes, approved Acadia
  shows moving ocean footage derived from seconds 13 to 19.5 of the same park
  video, slowed for the replacement and baked into its rendition. It keeps
  the source's audio track (that track is silent, so its card says Silent) and an
  independent opaque fallback. Compact player wording and Skip describe the active
  presentation. The approved Sea otters
  excerpt has no flagged intervals and no audio track; the Forest excerpt has no flagged
  intervals and keeps its original nature audio.
- **Skip is a choice.** Skip covers the picture first, moves past the scene, and uncovers
  only after the player confirms the new position. The seek bar uses the same guard.
- **Fails closed.** If a map's signature or a title's identity does not match the app's
  approved catalog, the picture stays hidden.
- **Parents decide.** Presets and profiles are edited behind a PIN; Home's profile button
  only picks who is watching, and settings can only add covers.
- **Plain about its limits.** More info and How it works both say that Calm Frames works
  only with prepared videos in this app, not other apps or live TV, that it can miss
  flashing, and that it is not a medical device. More info adds that this prototype has
  not been medically validated.
- **Back where you started.** Playback returns to its launch screen. A video opened
  from Details returns to Details with Watch focused; one Back restores the selected
  Home card. Playback launched from Home returns to Home.
- **A connected journey.** Startup, household loading, verification, playback opening
  and return share the coastal map, Ocean/Forest motifs and consistent typography.
  Messages reflect actual application state; optional gentle artwork respects reduced motion.

### On the computer today

A local review page on the Mac. It is not a TV screen.

- Choose a short MP4. The page copies it into a private workspace and analyzes every frame
  against WCAG 2.2 and ITU-R BT.1702-3.
- It shows where flashing was flagged, how each cover is padded, and how much each setting
  would cover. It never plays the video.
- Approval prepares, verifies and exports a signed package, and only with an authorized
  signing key.
- After export, the local tool can stage a delivery review, recheck its files or cancel the
  review. Staging records approval status; it does not install a title or enable Watch.

### Reviewed, not approved

The analysis, preparation and packaging steps were first run on the whole of a second public
domain NPS clip, Prairie Creek and Redwood. That proposal verified a package signed with a
newly authorized local key, and tampered copies were refused. Most of the full clip would be
covered; it was never approved for the TV, it is not in the app's catalog, and no promotion
of it is planned for this submission. A separate 12-second excerpt of the same clip, with no
flagged scenes, was later approved under that same key and is the Forest video. A signature
and a verified package show that the files are intact and were checked. They do not
establish medical safety.

## How it works

1. **Analyze once, ahead of time.** flashmap, our open-source Python analyzer, reads every
   frame at a reduced working resolution. It flags general and red flashes against WCAG 2.2
   Success Criterion 2.3.1, with ITU-R BT.1702-3 as a second profile.
2. **Prepare and sign.** The pipeline pads each flagged interval with guard time and renders
   a prepared copy with those sections already covered. It proves the cover is drawn by
   checking the first, middle and last frame of each covered span, up to six spans per
   preset, then signs a flash map (Ed25519) bound to the exact file hashes. Acadia's
   replacement has its own check instead: the copy is rebuilt, must match byte for byte,
   and is analyzed again whole under both profiles.
3. **Approve exactly, check twice.** A reviewed approval file names the exact bundle,
   catalog digest and signing-key fingerprint, and the app compiles only those. Before delivery, the
   build checks packaged file hashes, signed maps and original reports. At playback, the app
   verifies signed maps and matches the route and source metadata to its compiled approved
   catalog.
4. **Cover on time.** The live cover follows a clock re-anchored to media time at every
   player update. Every seek goes through one guarded function, which covers the picture
   before moving whenever the target is in or near a covered scene. A lint rule rejects
   playhead writes anywhere else, apart from named exemptions for the sample's fallbacks
   and two interface sounds.

## What we built

- **A Vega OS app** in React Native for Vega, on Vega SDK 0.24. It started from Amazon's
  vega-video-sample. We kept its playback stack and W3C media player, and built Home,
  Details, the cover layer, the guarded seek, the scene notice, Parents and the approved
  catalog check.
- **flashmap**, the analyzer, with a GitHub Action, a flash map sidecar format and a hook for
  other Vega video apps. All Apache-2.0.
- **A preparation pipeline** that renders covered copies, verifies them and exports a signed
  package.
- **A local review and staging tool** for new videos, described above.
- **Tests seen to fail first.** Our rule is that every guard gets a test that we break on
  purpose before trusting it. Focused passes on October 18: the delivery integration ran
  <!--n results/package-delivery-2026-10-18/receipt.json:python_tests -->55<!--/n--> Python,
  <!--n results/package-delivery-2026-10-18/receipt.json:node_tests -->32<!--/n--> Node and
  <!--n results/package-delivery-2026-10-18/receipt.json:app_tests -->59<!--/n--> app tests,
  and the final wording pass ran
  <!--n results/final-clarity-2026-10-18/verification.json:tests_passed -->43<!--/n--> tests in
  <!--n results/final-clarity-2026-10-18/verification.json:test_suites -->4<!--/n--> suites.
  These are focused suites, not the full suite.

[Owner: the October 19 records for this branch: app suite 1,676 passed, 0 failed, 4 skipped,
on `53a1c51` (`results/home-islands-2026-10-19/full-suite-after.log`); Python 1,880 passed,
0 failed, 9 skipped, with the 2 slow tests deselected, on `d9c9e2f` (`python-suite-d9c9e2f.txt`
in the same folder); mutation gate 68 of 70 killed, the 2 survivors the documented
equivalents, matching `results/mutation.json` (`mutation-check-53a1c51.json`). The same pass
found the full app suite had 18 failing stale tests on `c84f95d` while the October 18 records
counted focused subsets. The app and Python counts are in a log and a text file, not a results
JSON, so neither is marked or published here; add them only once they are.]

[Owner: add one line on the October 9 AWS deployment only if entering AWS Builder. The current
TV app and local workflow do not call AWS.]

## Challenges

- **No frame counter on the virtual device.** On the packaged files the app plays,
  `getVideoPlaybackQuality` failed with code 50001 and stayed at zero while video played.
  The opening now waits for the player's ready state and a moving clock instead. That gate
  is not proof of a visible frame, and we do not claim one from logs.
- **Packaged files did not open by their documented URI.** The player refused
  `file:///pkg/...` and opened `/pkg/...`. We normalize the prefix at the media boundary
  only.
- **Scripting the remote.** The documented `vega exec inputd-cli` looked for a host program
  that is not there, and still exited 0. `vega device run-cmd` reaches the device's own copy.
- **Slow playback on the virtual device, now and then.** In two isolation runs on October 17,
  <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-app.media_span_ms -->6010<!--/n--> ms
  of video took <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-app.wall_span_ms -->15560<!--/n--> ms,
  and <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-simulator.media_span_ms -->5886<!--/n--> ms
  took <!--n results/native-slowdown-isolation-2026-10-17/receipt.json:experiments.fresh-simulator.wall_span_ms -->26435<!--/n--> ms
  even after a simulator restart. A minimal SDK playback app, tested outside this
  repository, slowed the same way, and then both recovered with no code change. A later run
  kept pace,
  <!--n results/compact-scene-control-2026-10-17/native/summary.json:clock_segments.1.media_ms -->20894<!--/n--> ms
  of video in <!--n results/compact-scene-control-2026-10-17/native/summary.json:clock_segments.1.wall_ms -->20899<!--/n--> ms.
  We have not found the cause, and we do not call it fixed.
- **A cover that looked broken.** In our own review, a plain black cover read as a playback
  failure, and a large centered message crowded the picture. The cover now explains itself,
  and the status moved to a small corner notice beside Skip.

## Accomplishments

- **No unchecked step from analysis to the TV.** Only exactly approved packages reach the
  app's catalog, and a mismatch keeps the picture hidden.
- **One guarded path for every seek.** Skip and the seek bar use the same function, which
  covers before it moves into or near a covered scene.
- **Staging that cannot switch anything on.** A delivery review records approval state, but
  it cannot install a title or enable Watch.
- **Native runs that say what they measure.** Logs on the virtual device recorded the
  covers, Skip's cover-then-seek order, pause during a cover and the return to Watch, each on
  the earlier build where it was observed. We label them as logs, not as pictures or sound.
- **A friction log kept from day one**, each entry with steps, expected and actual results, a
  workaround and a suggestion.

## Limitations

Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a
medical device.

- Detection can miss flashing, and this prototype has not been medically validated. The
  analyzer works on a reduced frame, so small details can be averaged away. "No flagged
  scenes" is a finding, not a safety certificate.
- HDR and variable frame rate are outside this intake version. The broadcast profile also
  implements an informative regular-pattern rule; this is not a WCAG finding or clinical
  validation.
- It works only with prepared videos inside Calm Frames, not other apps, streaming services,
  live TV or DRM content.
- Three prepared videos are on Home: Acadia, Sea otters and Forest. A new one needs exact
  approval, its packaged files and reports, a regenerated catalog, and a build, install and
  device check. It also needs room: the prepared library already fills
  <!--n results/forest-activation-2026-10-18/validation-summary.json:prepared_namespace_bytes -->66492442<!--/n-->
  of its <!--n results/forest-activation-2026-10-18/approval.json:unchangedLimitBytes -->67108864<!--/n-->
  byte budget, much of it the same rendition stored once per preset, which the current
  package format cannot share. So no new clip of useful length can be added until the
  owner decides to change the budget, the titles or that format.
- It is a Vega OS app; there is no Fire OS build.
- Every native observation comes from the Vega Virtual Device, never a physical Fire TV.
  Device logs show events, order and focus, not pixels or sound. The latest run recorded in
  the repository, on source `805f855` (October 18), checked all three titles, Acadia replacement requests,
  natural end and Details/Back routes on the earlier coastal map. Earlier source `6f2570d`
  also has pause fallback, protected Skip and control checks. The Ocean and Forest Home
  on the current source has not been built, installed or seen on a device; its pictures
  are browser renders of the component tree, not device captures. The owner's look and
  listen acceptance is still pending.
- Playback on the virtual device sometimes slows, as described above, and the cause is
  unknown.
- The Acadia clip opens on a few seconds of near-black footage. That is in the source video,
  not a cover. Acadia's replacement footage starts at that same opening.

[Owner: look at Acadia's replaced scenes before calling them ocean footage, here or in the
video. The replacement excerpt is source 0 to 6.5 seconds and every replacement starts at its
beginning (`results/baked-ocean-2026-10-18/README.md`), and the October 17 blackdetect pass
found the source near-black from 0 to 4.963 seconds (`results/black-gap-2026-10-17/README.md`).
By those records the Standard and Broadcast replacements (4.356 and 2.48 seconds) come
entirely from that near-black opening, and the Extra cautious ones (5.356 and 3.48 seconds)
all but the last 0.393 seconds of the first. No recorded check has looked at those frames.]

## Product feedback

The form asks five questions about every tool. Full answers for every tool we used, with
commands and output, are in `docs/FEEDBACK.md` and `docs/FRICTION_LOG.md` in the repository.
[Owner: paste the remaining sections from FEEDBACK.md if the form wants every tool here.]

**Vega SDK and Vega CLI** (SDK 0.24.9914, CLI 1.3.4)

- *Used for:* building, installing, launching and log-streaming the app.
- *Worked well:* install, launch and the log stream were reliable enough to script every
  native check.
- *Needs work:* `vega exec inputd-cli button_press KEY_BACK`, the documented form, looks for
  a missing host executable and exits 0, so a script cannot tell it failed. `vega device
  run-cmd --device Simulator --command 'inputd-cli button_press KEY_BACK'` works. `vega device
  list` crashes while other device commands succeed, and `vega virtual-device status`
  reports running before the device accepts commands.
- *Onboarding:* under a day from a working shell to the sample playing video, most of it
  spent finding the right documentation page.
- *Build with it again:* yes. Every rough edge had a workaround.

**Vega Virtual Device** (1.0.67506.0, OS 1.2)

- *Used for:* every native run in this simulator-only entry.
- *Worked well:* a real OS 1.2 image on ARM, so platform behaviour showed up without
  hardware.
- *Needs work:* on October 17 playback slowed sharply and then recovered with no code
  change, in our app and in a minimal SDK playback app tested outside this repository, and
  nothing in the logs explains it; the numbers are above. There is no documented way to
  capture the app's picture to check our own screens.
- *Onboarding:* quick to start. Readiness means polling `vega device is-connected`, not
  trusting `status`.
- *Build with it again:* yes for development, with simulator results labelled as such.

**W3C media player, `@amazon-devices/react-native-w3cmedia`**

- *Used for:* all playback, media events and seeking.
- *Worked well:* it is the standard media element, so web knowledge carries over.
- *Needs work:* in a September 17 HLS timing run `getVideoPlaybackQuality` did report
  frames, but on the packaged MP4 files the app plays now every call fails below JavaScript
  with `MPB Call failed with code: 50001` and reports zero frames. A packaged
  `file:///pkg/...` URI does not open while `/pkg/...` does. The `timeupdate` cadence and
  `currentTime` resolution are not documented.
- *Onboarding:* good through the sample, hard from the API alone.
- *Build with it again:* yes, with a documented timing contract.

**`AmazonAppDev/vega-video-sample`**

- *Used for:* the base of the app and its playback wiring.
- *Worked well:* a complete reference for the surface, captions and media controls.
- *Needs work:* a failed Shaka load is dropped silently, and the README's data-push step
  cannot work on OS 1.2.
- *Onboarding:* fast. Clone, install, build, sideload.
- *Build with it again:* yes.

## Track, mini challenges and Built With

- **Primary track:** Fire TV, on Vega OS.
- **Mini challenges:** [Owner decision. None is required. Open Source needs a separate public
  contribution URL. AWS Builder means describing the October 9 AWS deployment in the
  feedback.]
- **Built With:** Vega OS, Vega SDK, Vega Virtual Device, React Native, TypeScript,
  react-native-w3cmedia, Python, ffmpeg, Ed25519 signing with Python `cryptography`, GitHub
  Actions. [Add AWS CDK and its services only if entering AWS Builder.]

## Links

- Repository: [Owner: URL once public or private access is set up]
- Demo video: [Owner: public YouTube or Vimeo URL]
- Friction log and product feedback: `docs/FRICTION_LOG.md` and `docs/FEEDBACK.md` in the
  repository
