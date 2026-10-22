# Release checklist: replacement candidate, October 22

For the integrated branch `codex/recovery-proof-integration-2026-10-22`, built from
`d96c088`. The submitted candidate `bf2f615`, its installed package (kept for
rollback) and the public video stay the fallback until the owner approves the
publication bundle at the end. Nothing below has been pushed, uploaded or
submitted.

## Source and build

- [x] Code validated at `d96c088`; later commits add the benchmark tool and
  documentation only ([RELEASE_READINESS.md](../RELEASE_READINESS.md)).
- [x] Package SHA-256
  <!--n results/release-validation-2026-10-22/validation.json:native.final_build.package_sha256 -->6914d157c76a0478588f63e222525754f1202990481e313b4e72422c93759090<!--/n-->,
  installed on the Vega Virtual Device and confirmed by the device's own hash.
- [x] Approved media, signed maps, keys and trust settings unchanged since `bf2f615`.
- [ ] Hosted CI: not run, because the branch is not pushed. Local results are not
  hosted results.

## Automated gates (local)

- [x] Python: <!--n results/release-validation-2026-10-22/validation.json:python.full.passed -->2049<!--/n--> passed, nothing
  skipped; coverage <!--n results/release-validation-2026-10-22/validation.json:python.full.coverage.percent -->90.46<!--/n-->% against the unchanged floor.
- [x] App: <!--n results/release-validation-2026-10-22/validation.json:app.jest.tests_passed -->1729<!--/n--> jest tests passed; TypeScript,
  lint, tool tests, hook package and the UI flash check with its negative control.
- [x] Mutation gate: <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.totals.killed -->68<!--/n--> of
  <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.totals.mutations -->70<!--/n--> killed; the two survivors are documented equivalents.
- [x] Recovery scenarios and guard mutations, and the benchmark's
  <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.checks_passed -->34<!--/n--> of
  <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.checks -->34<!--/n--> checks.
- [x] After the benchmark tool was added: ruff, the style check and the eval test
  lane passed again. The full suites were not repeated, because no app or
  pipeline code changed after `d96c088`.

## Native review on the virtual device

- [x] Palette, all three Playback proof stages for Acadia and McWay, every section
  of the record, Back and focus, and unknown report versions, seen on screen in
  two sessions ([second session](../../results/native-review-2026-10-22/native-review.json)).
- [x] The five-minute McWay scene ran to its still frame (trace), and 78 seconds
  of it were recorded uncut (picture).
- [ ] Owner: listen to `native-review-2/audio-check-mcway-20s.mp4` and the demo's
  audio. It measures <!--n results/native-review-2026-10-22/native-review.json:audio_check.integrated_lufs -->-27.3<!--/n--> LUFS
  as captured; nobody has listened to it.
- [ ] Owner: look at the light menu palette and the reading-stop focus on the
  device or in the screenshots.

## Replacement demo

- [x] `calm-frames-replacement-demo.mp4`, SHA-256
  <!--n results/replacement-demo-2026-10-22/demo.json:sha256 -->dde2ba357cf769c42eda519591aaf235e06fd487eb61f1d1d59548f4d703df92<!--/n-->,
  <!--n results/replacement-demo-2026-10-22/demo.json:seconds -->169.21<!--/n--> s, under three minutes.
- [x] Video gate <!--n results/replacement-demo-2026-10-22/demo.json:video_gate.verdict -->pass<!--/n-->; full decode clean;
  <!--n results/replacement-demo-2026-10-22/demo.json:uncut_playback.seconds -->78<!--/n--> s of native playback uncut and
  frame-matched to the capture; audio <!--n results/replacement-demo-2026-10-22/demo.json:audio.integrated_lufs -->-18.8<!--/n--> LUFS,
  true peak <!--n results/replacement-demo-2026-10-22/demo.json:audio.true_peak_dbfs -->-3.6<!--/n--> dBFS.
- [x] Labels on screen for the app-window capture, the shortened pauses, and the
  terminal cards rendered from saved logs; credits on screen and in
  [the upload description](../../results/replacement-demo-2026-10-22/upload-description.txt);
  <!--n results/replacement-demo-2026-10-22/demo.json:captions -->10<!--/n--> captions in the sidecar.
- [ ] Owner: watch it once at normal speed before approving the upload.

## Rollback

Reinstall the fallback package, a read-only copy kept outside the repository with
its SHA-256 and SHA-384:
`vega device install-app --device VirtualDevice --packagePath <rollback copy of calm-frames-60c3bbb-aarch64-debug.vpkg>`.
The submitted branch, commit and video need no rollback; they were not changed.

## Publication approval bundle (nothing done; each item needs the owner's yes)

1. **GitHub, private repository `alejandro-publius/calm-frames`.** Push the local
   branch `codex/recovery-proof-integration-2026-10-22` as a new remote branch at its
   final commit, with no force and no merge. `claude/ocean-layout-fix-2026-10-19`,
   `bf2f615` and `main` stay as they are. Then run the CI and Audit workflows on that
   branch by hand to get hosted results.
2. **YouTube, the Patagonia Bear channel.** Upload `calm-frames-replacement-demo.mp4`
   as a new video with the title and description in the upload description file and
   the captions file, at the same visibility and audience settings as the current
   demo. The current public video, `6lAP1FH16vc`, stays up unchanged.
3. **Devpost, the existing Calm Frames entry (1187358).** Before the edit cutoff,
   October 23 at noon Pacific, replace the video link with the new one and point
   the repository link at the pushed branch; everything else in the entry stays.
   If hosted CI fails on the branch, keep the repository link on the submitted
   branch and change only the video.
