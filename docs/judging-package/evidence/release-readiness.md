> Historical source excerpt copied from `docs/RELEASE_READINESS.md` at `13551e4`. Local references now point to immutable source or bundled assets. Publication wording describes its original checkpoint, not current status.

# Release readiness: preparation recovery with Playback Proof

October 22, 2026. Branch `codex/recovery-proof-integration-2026-10-22`, code
commit <!--n results/release-validation-2026-10-22/validation.json:tested_commit -->d96c0886227f7dcfc5ae6584132a86b193359215<!--/n-->.
It combines the preparation recovery work (`ce6f6a3`) with Playback Proof
(`318a3fe`) on top of the submitted candidate `bf2f615`. Nothing here is pushed,
merged, uploaded or submitted. Machine-readable results:
[validation.json](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/results/release-validation-2026-10-22/validation.json).
Earlier receipts, such as `results/playback-proof-2026-10-21/` and
`results/preparation-recovery-2026-10-21/`, describe their own commits; every
check below was run again on this one rather than carried over.

**Verdict: ready for a native demo of this build, and for the owner's publication review**

Every automated gate passes on this commit, its package is installed on the
Vega Virtual Device, and the native checks pass after one defect found on the
device was fixed. Nothing is published: pushing this branch, a new public video
and any Devpost change each need the owner's specific approval. Before
recording, the owner should look at the new light menu palette and listen to
the audio, which no check here covers.

## What each claim rests on

| Claim | Evidence | Reproduce |
|---|---|---|
| The whole Python suite passes with nothing skipped | <!--n results/release-validation-2026-10-22/validation.json:python.full.passed -->2049<!--/n--> passed, <!--n results/release-validation-2026-10-22/validation.json:python.full.failed -->0<!--/n--> failed, <!--n results/release-validation-2026-10-22/validation.json:python.full.skipped -->0<!--/n--> skipped, <!--n results/release-validation-2026-10-22/validation.json:python.full.deselected_slow -->2<!--/n--> slow tests deselected as in CI | `python -m pytest -q -m "not slow" flashmap pipeline eval --cov --cov-config=.coveragerc` with boto3, moto and aws-cdk-lib importable |
| The unchanged <!--n results/release-validation-2026-10-22/validation.json:python.full.coverage.floor_percent -->90<!--/n-->% coverage floor in `.coveragerc` holds | <!--n results/release-validation-2026-10-22/validation.json:python.full.coverage.percent -->90.46<!--/n-->% of <!--n results/release-validation-2026-10-22/validation.json:python.full.coverage.statements -->7419<!--/n--> statements; the same in CI's install, where <!--n results/release-validation-2026-10-22/validation.json:python.ci_equivalent.skipped -->6<!--/n--> AWS-dependent tests or modules skip and <!--n results/release-validation-2026-10-22/validation.json:python.ci_equivalent.passed -->1987<!--/n--> pass | Same command with only `flashmap[dev]`, pytest 9.1.1 and matplotlib 3.11.2, as `.github/workflows/ci.yml` installs |
| Python lint and types | ruff, strict mypy on flashmap and mypy on the pipeline all pass | `python -m ruff check .`, `python -m mypy --config-file flashmap/pyproject.toml`, `python -m mypy --config-file pipeline/mypy.ini` |
| Published numbers match their results | <!--n results/release-validation-2026-10-22/validation.json:published_numbers_matched -->550<!--/n--> markers on the code commit, and the check passes again with this report's own markers; plus the style, pin, archive, diff, baseline and conformance rebuild checks | `python eval/readme_sync.py --check` and the other steps of CI's numbers job |
| Interrupted or damaged preparation recovers and never publishes damaged work | <!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.passed -->16<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.scenarios -->16<!--/n--> scenarios, including real SIGKILL restarts and a real analyzer run; <!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.killed -->24<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.mutations -->24<!--/n--> guard mutations caught | `python -m eval.preparation_recovery --out results/preparation-recovery-2026-10-22/evidence.json --mutations` ([how it works](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/docs/PREPARATION_RECOVERY.md)) |
| The mutation gate's guards fail when broken | <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.totals.killed -->68<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.totals.mutations -->70<!--/n--> mutations killed; the <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.totals.survived -->2<!--/n--> survivors are the two documented equivalent mutants; `--check` against the previous report exited <!--n results/release-validation-2026-10-22/validation.json:mutation_gate.check_against_previous_report_exit -->0<!--/n--> | `python eval/mutate_gate.py --check --out <file>`; the regenerated report is [mutation.json](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/results/mutation.json) |
| The app's tests pass above their floors | <!--n results/release-validation-2026-10-22/validation.json:app.jest.tests_passed -->1729<!--/n--> jest tests passed and <!--n results/release-validation-2026-10-22/validation.json:app.jest.tests_skipped -->4<!--/n--> skipped, <!--n results/release-validation-2026-10-22/validation.json:app.jest.snapshots_passed -->57<!--/n--> snapshots; line coverage <!--n results/release-validation-2026-10-22/validation.json:app.jest.coverage_percent.lines -->82.94<!--/n-->% (floor <!--n results/release-validation-2026-10-22/validation.json:app.jest.coverage_floor_percent.lines -->77<!--/n-->%); TypeScript passes; lint <!--n results/release-validation-2026-10-22/validation.json:app.lint.errors -->0<!--/n--> errors | `npm run typecheck`, `npx eslint src test --ext .ts,.tsx`, `npx jest --ci` in `app` |
| The packaged media and Playback Proof records are the approved ones | prepared library <!--n results/release-validation-2026-10-22/validation.json:app.prepared_library.bytes -->129255687<!--/n--> bytes, catalog <!--n results/release-validation-2026-10-22/validation.json:app.prepared_library.catalogSha256 -->02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79<!--/n-->, every report present; the proof records reproduce from the approved catalogs; <!--n results/release-validation-2026-10-22/validation.json:app.node_tool_tests.passed -->60<!--/n--> tool tests | `node tools/check_prepared_library.mjs`, `node tools/playback_proof.mjs --check` and CI's tool tests in `app` |
| The app's own screens do not flash | <!--n results/release-validation-2026-10-22/validation.json:app.ui_flash_screens_and_transitions -->79<!--/n--> screens and transitions pass the WCAG and broadcast profiles, and the negative control still refuses a flash and a grating; <!--n results/release-validation-2026-10-22/validation.json:app.brand_images_checked -->17<!--/n--> shipped images pass | `npm run ui:flashmap`, `node tools/ui_flashmap.mjs --negative-control`, `python eval/brand_assets_check.py` |
| No secret in the tree | gitleaks found no leaks | `gitleaks dir . --config .gitleaks.toml` |
| The package installed is the package built from this commit | SHA-256 <!--n results/release-validation-2026-10-22/validation.json:native.final_build.package_sha256 -->6914d157c76a0478588f63e222525754f1202990481e313b4e72422c93759090<!--/n-->, <!--n results/release-validation-2026-10-22/validation.json:native.final_build.package_bytes -->132592040<!--/n--> bytes; the device's own SHA-384 matches | `make release RELEASE_ARGS="--tag <tag>"`, then `vpm info` on the device |

## On the Vega Virtual Device

All observations are from the final build, driven one remote key at a time and
judged by the app's own trace lines, with app-window-only screenshots; details
and picture hashes are in `validation.json` under `native`.

- Home, Details, More info and Playback proof & details are reached with the
  remote, and the three evidence stages switch in place without playing
  anything.
- Acadia's three stages show its approved extra cautious record: <!--n results/release-validation-2026-10-22/validation.json:native.displayed.acadia.source_findings.wcag -->3<!--/n--> WCAG
  and <!--n results/release-validation-2026-10-22/validation.json:native.displayed.acadia.source_findings.broadcast -->3<!--/n--> broadcast source findings, no output findings, the cover proven
  drawn, <!--n results/release-validation-2026-10-22/validation.json:native.displayed.acadia.frames -->1804<!--/n--> frames, prepared file `<!--n results/release-validation-2026-10-22/validation.json:native.displayed.acadia.prepared_file -->8aa6b3566e32<!--/n-->` and report
  `<!--n results/release-validation-2026-10-22/validation.json:native.displayed.acadia.report -->4043445adbb8<!--/n-->`.
- McWay's report does not record its output analyzer version, and the page says
  "version not recorded in this report" rather than inventing one.
- Every section of the record below the proof takes focus in order and scrolls
  into view, and the bottom Back follows.
- Remote Back restores each opener: the proof button, More info, the Home
  Details button, and Watch after playback.
- McWay played from the approved edition `<!--n results/release-validation-2026-10-22/validation.json:native.displayed.mcway.prepared_file -->795927874818<!--/n-->`: the picture
  appeared at media <!--n results/release-validation-2026-10-22/validation.json:native.mcway_playback.picture_shown_media_ms -->299<!--/n--> ms and playback ended
  <!--n results/release-validation-2026-10-22/validation.json:native.mcway_playback.seconds_from_picture_to_end -->300.8<!--/n--> seconds later on the still frame, with no stall,
  surface loss or error line in between. A frame from a second, shorter run is in
  `results/release-validation-2026-10-22/native/`.
- Of <!--n results/release-validation-2026-10-22/validation.json:native.key_presses.total -->70<!--/n--> remote presses, <!--n results/release-validation-2026-10-22/validation.json:native.key_presses.with_expected_trace -->64<!--/n--> expected a trace line
  and all <!--n results/release-validation-2026-10-22/validation.json:native.key_presses.expected_trace_seen -->64<!--/n--> produced it before the next press. The
  <!--n results/release-validation-2026-10-22/validation.json:native.key_presses.stage_selections_without_trace -->6<!--/n--> stage selections print no trace line and were checked on
  screen, except one made while the screen was locked.

## Found and fixed during this validation

- **The analysis record below the proof could not be reached with the remote.**
  On the first integrated build, one Down from the stage buttons went straight to
  the closing Back. The record's sections are now focus stops
  (`app/src/calmframes/ReadingStop.tsx`); a test fails on any text outside one,
  and the ten foot test holds their rings to the button floors.
- **Python lint failed in CI** on five ruff errors in the architecture renderer,
  present on `bf2f615` too. Fixed by formatting only; the rendered PNG and SVG
  are byte-identical.
- **Two integration fixes had no mutation**: the scene-hold publication check and
  the oversized ledger timestamp. Both are now in the recovery runner's guard
  mutations and both are killed.

## Not established

- Audio was not listened to. The new light menu palette and the reading-stop
  focus look still need the owner's own review.
- <!--n results/release-validation-2026-10-22/validation.json:native.failed_captures -->4<!--/n--> screenshots failed while the Mac screen was locked; those steps rest on
  trace lines, which the device can drop under load.
- The five-minute run was judged from trace lines alone, because the Mac screen
  was locked while it played.
- Sea Otters, Forest and Acadia were not played in this session.
- Recovery evidence comes from one Mac and APFS; no power was cut. See
  [the recovery limits](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/docs/PREPARATION_RECOVERY.md#limitations).
- No hosted CI run exists for this branch, because it is not pushed.
- Approved work directories were not prepared again: with this code, the first
  re-preparation of an old work directory reruns every step and signs new maps.

## Rollback

The package the device held before this validation is the submitted candidate's
app (`60c3bbb`), package SHA-256
`207898aa14d8659760348a716b825fabab83afd8e3b9431f9387202cc10e7163`. A read-only
copy is kept outside the repository with its SHA-256 and SHA-384. Reinstall it
with `vega device install-app --device VirtualDevice --packagePath <that copy>`.
The submitted branch and commit and the public video are untouched.
