# Shot manifest

Capture plan for [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md), updated October 2. Shot IDs
remain S01-S18. **No shot below is marked captured.** Existing logs, generated
assets and tests are preparation evidence, not a completed native filming take.
Raw footage belongs under gitignored `media/video/raw/`.

The app now exposes kid mode, title details, playback and the parent area through
normal navigation. The remaining filming dependency is a visible, checked
native build and observed behavior on its display. The current sandbox cannot
establish screen visibility by interpreting a log or a black capture as success.

## Capture routes

| Route | Use | Boundary |
|---|---|---|
| **A. Native camera take** | Camera pointed at the television or monitor showing the actual app. A directly captured native display can be used if its correctness is first verified. | Historical macOS/QEMU captures missed the GPU layer. Confirm the chosen route with a visible current app. Label the simulator when used. |
| **B. Desktop recording** | Terminal, editor and local check output. | This documents tools; it does not prove the app was visible on a device. |
| **C. Static evidence figure** | Readable signed schedule, result table or integration excerpt. | Clearly label sham schedules, historical measurements and local mutation tests. |

The app's color-frame capture path is excluded from the cut. It measures colors
declared by UI components, not the complete rendered screen. It cannot stand in
for a screenshot, caption-composition take or hardware timing measurement.

## Shot inventory

| Shot | Script time | Actual content | Route | Prerequisite and truth check | Capture destination | Status |
|---|---|---|---|---|---|---|
| **S01** | 0:00-0:10 | Actual app beside `vega device info --device <target>` in one frame | A | Explicit connected target and matching checked package. Name the simulator if used. | `media/video/raw/S01_device.mov` | not captured |
| **S02** | 0:10-0:22 | Checked kid shelf, focused Harbor benign-demo card | A | First-run setup completed. No patient or child participation is required. | `media/video/raw/S02_shelf.mov` | not captured |
| **S03** | 0:10-0:22 | Harbor details, Play and the native practice countdown | A | Fixed Extra cautious plan and `Benign demo: practice holds, no flashing` label visible. | `media/video/raw/S03_countdown.mov` | not captured |
| **S04** | 0:22-0:47 | Unbroken Harbor take through scene holds, moving captions and gentle tone | A | Select `English practice captions`; observe composition and audio directly. No meter or physical timing claim. | `media/video/raw/S04_hold_captions.mov` | not captured |
| **S05** | 0:47-0:58 | Signed sham schedule and bound Harbor source identity | C | Derive from packaged benign-story maps. Label synthetic intervals and do not imply actual flashes. | `media/video/raw/S05_signed_practice.png` | not captured |
| **S06** | 0:58-1:12 | Remote seek into a practice hold, pause/resume and opaque fallback | A | Real D-pad interaction on the same demo. Alexa is optional only after verified on that target. | `media/video/raw/S06_seek.mov` | not captured |
| **S07** | 1:12-1:28 | Locked parent area, then successful PIN gate | A | Conceal entered PIN. Opening after failed storage is not success. | `media/video/raw/S07_parent_gate.mov` | not captured |
| **S08** | 1:12-1:28 | Household preset and room controls | A | Do not claim the benign demo's fixed preparation changes with household settings. No staged hidden-count increase. | `media/video/raw/S08_settings.mov` | not captured |
| **S09** | 1:28-1:38 | Relaunch without data reset, same selected profile/settings and locked parent area | A | Directly observe persistence before claiming it. Fresh logs alone do not establish durability. | `media/video/raw/S09_restart.mov` | not captured |
| **S10** | 1:38-2:00 | Owned Harbor normal preparation and ready receipt | B | Use neutral-caption source from `eval.prepare_owned_harbor`; no synthetic detector intervals. Show the actual run, with waiting time clearly edited. | `media/video/raw/S10_prepare.mov` | not captured |
| **S11** | 1:38-2:00 | Python export check and Node exact-byte build gate | B | Show actual commands and distinct source/rendition hashes. No key material in the recording. | `media/video/raw/S11_export.mov` | not captured |
| **S12** | 1:38-2:00 | Distinct `Harbor story (prepared locally)` on shelf and in playback | A | Fresh build containing the checked export. Clean imported source has no detected cover interval and does not carry scene images. | `media/video/raw/S12_prepared_shelf.mov` | not captured |
| **S13** | 2:00-2:13 | Analyzer command or a real artifact-tampering rejection test | B | No hazardous preview. Any deliberate mutation is explicitly labelled a local negative test. | `media/video/raw/S13_local_check.mov` | not captured |
| **S14** | 2:00-2:13 | CI workflow source and local verification output | B | Hosted CI startup is account-blocked; do not show its red status as an analyzer rejection or invent a PR run. | `media/video/raw/S14_workflow.mov` | not captured |
| **S15** | 2:13-2:26 | Hook integration excerpt and offline consumer check | B or C | State that independent adoption has not been observed. Keep text readable without scrolling. | `media/video/raw/S15_hook.mov` | not captured |
| **S16** | 2:26-2:43 | Current results, weaker near-limit performance and unmeasured rows | B | Use current README and committed results. No physical-TV claim inferred from software timing. | `media/video/raw/S16_results.mov` | not captured |
| **S17** | 2:26-2:43 | Actual `eval/readme_sync.py --check` output | B | Run against the same text used in the final cut. Passing drift checks does not independently validate a metric. | `media/video/raw/S17_drift_check.mov` | not captured |
| **S18** | 2:43-2:53 | Calm native app and closing product claim | A | Approved wording and accurate repository visibility. No seizure-prevention claim. | `media/video/raw/S18_close.mov` | not captured |

The two Harbor titles must remain distinct in the edit. The benign demo has
signed scene images and synthetic practice intervals. The normal prepared import
uses the canonical opaque plan, genuine analysis and neutral story captions.
Its clean source cannot demonstrate hiding a detected hazard.

## Rehearsal and evidence checklist

| ID | Check | Command or action | What it proves |
|---|---|---|---|
| **R00** | Display visibility | Observe the app on the selected target and test the intended camera/capture route. | The native app can actually be seen in the planned take. Still pending direct observation. |
| **R01** | Prepared asset delivery | `.venv/bin/python -m pipeline.packaged_library check --output app/assets/raw/prepared-library`, then `cd app && node tools/check_prepared_library.mjs` | The packaged namespace matches its immutable manifests and compiled catalog. It does not prove playback. |
| **R02** | Benign native preflight | `.venv/bin/python -m eval.benign_native_smoke --device <target> --vpkg <matching-debug-package>` | Read-only target, package and benign-fixture checks. Physical targets retain their separate checkpoint. |
| **R03** | Native journey and restart | Add `--execute --restart` to R02 in a permitted device session; operate the visible app as prompted. | Fresh software playback events only. Record image/caption composition and saved-state observations separately. Never reset data to manufacture a pass. |
| **R04** | Owned import reproducibility | `.venv/bin/python -m eval.prepare_owned_harbor --workdir build/video-import-proof --output build/video-import-export` | Actual analysis, verification, captions and immutable export from owned non-flashing media. A temporary signing key is deleted. This isolated rehearsal output does not alter the app catalog. |
| **R05** | UI color checks | `cd app && npm run ui:capture && npm run ui:flashmap` when the tree is quiet | Component color-frame checks. No screen composition, camera exposure or physical timing claim. |
| **R06** | Final video gate | `eval/check_video.sh <final-file> --max-seconds 179` | The finished cut measures within the chosen flash and duration checks. Exit zero is required before upload. |

Use a fresh work directory for R04. The proof signer is temporary, and rerunning
against an old workspace is not a key-rotation workflow. Only a separately
reviewed export into the app assets followed by a new native build changes S12.

## Order of work

1. Keep source, export and native build checks green before recording. Desktop
   shots S10, S11, S13-S17 can be captured without a visible target.
2. Confirm R00. Then film S01-S04 and S06 in one native session, with the benign
   label and external captions visible.
3. Film S07-S09 without clearing application data. If persistence is not
   observed, leave S09 pending and remove the durability line from any draft cut.
4. Film the distinct prepared title for S12, then S18. Keep original audio where
   it demonstrates continuity and avoid covering all of it with narration.
5. Time the English read and final edit. Run R06, preserve its result, and check
   the eventual public link while logged out. Nothing in this manifest publishes
   a video, opens a PR or sends feedback to another person.

No calibrated meter, physical-TV lead time, patient outcome, external adoption
or hosted CI result is required as a substitute for missing native footage.
Each has its own evidence requirement; software tests do not supply it.
