# Demo video script

Current filming plan, October 2. Target **2:53**, spoken in English. The final
video must be public on YouTube or Vimeo and show the app running on an actual
Fire TV device or the Fire TV/Vega simulator. See the checked requirements in
[RUBRIC.md](RUBRIC.md). No current native take or public video is claimed here.

The story is: a family can follow a scene while the moving picture is hidden,
then a developer can trace a prepared title from verification to the TV shelf.
The camera journey uses our owned, non-flashing Harbor media throughout.

The only product safety claim is: **"Calm Frames reduces exposure to flashing
above published limits in the videos it plays. It is not a medical device."**
This is a prototype. Do not imply seizure prevention or clinical validation.

## Two titles with different purposes

| Title shown in the app | What the video may demonstrate | Required label |
|---|---|---|
| **Harbor story (benign demo)** | Signed still images, countdown, captions, audio and safe seek behavior through scheduled practice holds. It plays the verified pre-covered master with a fixed Extra cautious preparation. | `Benign demo: practice holds, no flashing` |
| **Harbor story (prepared locally)** | Original Harbor picture and audio with neutral story captions, measured by the normal pipeline, exported with all presets, then compiled into the app shelf. No sham detector intervals are added. | `Real local preparation of owned, non-flashing media` |

The prepared import uses the canonical opaque cover plan. It does not currently
carry signed scene images. Its clean source has no detected interval to cover.
Do not describe that title as demonstrating a hidden flashing scene. The benign
demo demonstrates still-image continuity with openly synthetic intervals.

The demo's fixed preparation does not change when household preferences change.
Do not film a hidden-count increase that the current title cannot produce.

## Before filming

- Install a newly checked build and complete first-run household setup. Kid mode,
  title details and the PIN-gated parent area are wired into the app now.
- Check that a camera sees the actual app on the selected display. Historical
  macOS and QEMU captures missed its GPU layer; that observation does not prove
  a phone camera will fail or that a new capture method works. A visible native
  take remains required.
- Name the simulator on screen if using it. Run `vega device info --device <target>`
  beside the app. Avoid `vega device list`, which previously failed.
- Rehearse with [the native smoke runner](../eval/benign_native_smoke.py). Its
  default is read-only; execution needs an explicit target, a checked package
  and, on physical hardware, the documented checkpoint. A fresh software log
  does not establish screen composition or household durability.
- Observe captions, the hold image and sound together before reading a line
  that says they continue. Observe a restart before claiming saved settings
  survived one. If a behavior fails, fix it and recapture; do not dub success
  over a failed or unrelated take.
- Show no flashing source footage. No `HAZARD_` file is opened in a player. The
  app's color-frame records are engineering checks, not screenshots, and never
  substitute for a native app shot. Nobody needs to film flashing footage for
  this cut. Obtain consent from anyone visible, including hands.

## Timed script

These are planned edit timings, not measured results. The continuous Harbor
take is the priority. Do a timed read before recording; trim transitions before
trimming the visible caption and hold sequence. Shot IDs match
[SHOT_MANIFEST.md](SHOT_MANIFEST.md).

| Time | Shots and picture | English voiceover | On-screen text and capture condition |
|---|---|---|---|
| **0:00-0:10** | **S01.** Actual app and targeted device info in the same camera frame. | "This is Calm Frames running on Vega OS. It helps families follow a story when the moving picture needs to be hidden." | Name `Vega Virtual Device` or the actual physical target. Do not call a simulator a television test. |
| **0:10-0:22** | **S02, S03.** Checked shelf, Harbor demo details, Play, then its countdown. | "For a child sensitive to flashing, simply covering the picture can also hide the story. This original, non-flashing animation lets us demonstrate another approach." | Keep the benign-demo label legible. No patient or family outcome is claimed. |
| **0:22-0:47** | **S04.** One unbroken Harbor playback take including the still hold, changing captions and audible gentle tone. | "These are scheduled practice holds. The prepared video holds a calm scene while captions and sound continue. The app tells the viewer what is happening, then returns to the story. The source itself contains no flashing." | Show `English practice captions` selected. The fixed Extra cautious plan and label must match the current app. Narrate continuity only after it is visible and audible in this take. |
| **0:47-0:58** | **S05.** Readable still showing the signed demo schedule and its source binding. | "The hold image and its timing are signed and tied to this exact source. This is a continuity rehearsal, not a test of preventing a seizure." | `Signed sham intervals. No detected flashing in this source.` Do not display a hazard trace as if it came from Harbor. |
| **0:58-1:12** | **S06.** D-pad seek into a practice hold, then pause and resume. | "A seek can land inside a hidden interval. Our guarded seek path requests the cover before moving the playhead, and interruptions keep the opaque fallback available." | Record the real remote interaction. Software ordering is tested; this shot alone does not establish screen-level timing. Add Alexa only if it works on the selected target and is captured. |
| **1:12-1:28** | **S07, S08.** Parent PIN gate, then household preset and room settings. | "Parents choose a preset and room settings behind a PIN. These choices can add protection. The practice title keeps its disclosed preparation, while imported titles select the corresponding prepared rendition." | Conceal PIN digits. Do not imply changing settings modifies the already packaged practice master. |
| **1:28-1:38** | **S09.** Relaunch without clearing data, then revisit the parent gate. | "Here, the selected profile and settings remain after relaunch, and the parent area still asks for the PIN." | Use this line only after the visible restart succeeds. Until then this shot remains pending and no durability claim is published. |
| **1:38-2:00** | **S10, S11, S12.** Real owned-source preparation receipt, export check, then the distinct prepared Harbor title on the actual shelf. | "This second Harbor title goes through normal local preparation. Each preset receives a verified rendition. Export checks the source, signatures and exact output bytes. The package binds those files to its catalog, and the app accepts only those compiled entries." | `Real preparation, no synthetic detector intervals.` Show source and delivered hashes as different fields. Do not suggest the app downloads a mutable catalog or runs a cloud service. |
| **2:00-2:13** | **S13, S14.** Analyzer interface and real local rejection tests or workflow source. | "The analyzer and preparation tools can run outside this app. Changed artifacts are refused. The repository includes a CI workflow, while the local checks remain available without a hosted runner." | Label a deliberate mutation `local negative test`. Do not fabricate a hosted failed check; account-level CI startup failures are not analyzer findings. |
| **2:13-2:26** | **S15.** Readable hook integration and offline consumer check. | "The player guard is also packaged as a reusable hook. An offline consumer check exercises the built package. Independent developer adoption is still something we need to demonstrate." | `Offline integration check; independent adoption not yet observed` |
| **2:26-2:43** | **S16, S17.** Current results and limitations beside the real drift-check output. | "We publish the limits alongside the results. Near-threshold detection remains weaker, native composition needs direct observation, and software timing is not physical-TV timing. Published numbers link back to result files." | Show the current README's weaker results and missing evidence together. Use only source-backed numbers below, with their context. |
| **2:43-2:53** | **S18.** Return to the calm native app and hold the end card. | "Calm Frames reduces exposure to flashing above published limits in the videos it plays. It is not a medical device." | Project name, product claim, and repository/license link. Do not call the repository public until that is true. |

There is no camera meter or claimed zero exposure in this cut. A gentle still
with captions is not zero luminance. Calibrated physical-TV measurements belong
to the separate hardware protocol and may be added only when measured.

## Source-backed figures for optional overlays

Keep these markers intact when editing. These are existing historical records,
not results from the new Harbor native journey. If a figure is omitted from the
cut, keep its worse counterpart or explain the limitation in the same beat.

| Figure | Exact context required if shown |
|---|---|
| <!--n results/screening.json:totals.flagged_segments -->456<!--/n--> flagged segments across <!--n results/screening.json:totals.sources_with_at_least_one_flag -->6<!--/n--> licensed sources | Historical screening corpus, not the Harbor demo or a clinical outcome. |
| <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms | Longest gap between the player's own position reports in the recorded virtual-device run; not a measured cover lead or physical-TV latency. |

Prefer the current README's paired overall and near-limit detection results to
a lone favorable metric. Run `.venv/bin/python eval/readme_sync.py --check`
against the final text and do not invent a number for unobserved screen behavior.

## Final cut and publication gates

- The app is visibly running on an actual Fire TV device or Fire TV/Vega
  simulator. A terminal, unit test or rendered mockup cannot replace that take.
- The benign-demo label is visible during practice holds; prepared import and
  rehearsal footage never impersonate each other.
- English voiceover and captions are readable, native sound is audible through
  the hold, and the final file is strictly shorter than three minutes.
- Film only our app. No Fire TV home-screen tiles, unlicensed music or other
  third-party footage is needed. Original Harbor assets and new story captions
  are owned material; credits are in the benign asset README.
- Run `eval/check_video.sh <final-file> --max-seconds 179` and require exit zero.
  Commit the resulting `results/video_check.json`. A measurement failure blocks
  publication. This gate checks the edited file; it is not medical validation.
- After the authorized public upload, confirm the YouTube or Vimeo link works
  while logged out and add it to `SUBMISSION.md`. No upload or publication has
  happened as part of this script update.

Still needed from a person: a visible device/camera session, direct observations
of the hold/caption composition and restart, consent for anyone in frame, the
voiceover, the final edit and the public video link. The terminal work prepares
and checks those steps; it does not supply their evidence.
