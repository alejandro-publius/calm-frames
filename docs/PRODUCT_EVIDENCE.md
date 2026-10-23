# What Calm Frames does, and what shows it

October 22, 2026, branch `codex/recovery-proof-integration-2026-10-22`. Four kinds
of claim are kept apart:

- **Implemented**: the code exists at the validated commit `d96c088`.
- **Tested**: an automated test or harness checks it, and that check has been seen
  to fail when the code is broken.
- **Observed**: seen on the Vega Virtual Device's screen, in app-window screenshots
  or recordings, not only in trace lines.
- **Not verified**: nothing here establishes it yet.

Calm Frames reduces exposure to flashing above published limits in the videos it
plays; not a medical device.

## From a video to the TV

1. **Prepare** (`pipeline/local_library.py`, `pipeline/ingest.py`). The source is
   probed and analyzed by flashmap under the WCAG and broadcast profiles, the maps
   are signed with Ed25519, a cover plan is made for each preset, pre-covered
   renditions and HLS are rendered, and verification analyzes the outputs again
   and proves the covers were drawn. Only then is a receipt ready.
2. **Recover** (`pipeline/state.py`, `pipeline/durable.py`). Every step's outputs
   are hashed; a step is reused only when its bytes are unchanged; a killed or
   damaged run rebuilds what it must and never leaves a ready receipt behind.
   [PREPARATION_RECOVERY.md](PREPARATION_RECOVERY.md) explains the design.
3. **Approve and package** (`pipeline/packaged_library.py`,
   `app/config/approved-prepared-libraries.json`, `app/tools/check_prepared_library.mjs`).
   The app is built only with catalogs approved by exact bundle, catalog and
   signer hash, inside a byte budget. Nothing at run time can add a catalog or key.
4. **Play** (`app/src/calmframes`). The app checks signatures and identities
   before playback, covers before any seek into a flagged span, and shows the
   record behind the selected edition on the Playback proof page.

## Evidence by capability

| Capability | Implemented | Tested | Observed | Not verified |
|---|---|---|---|---|
| Preparing a new video | `pipeline.local_library prepare` | Pipeline suite in [RELEASE_READINESS.md](RELEASE_READINESS.md) | An owned 20 s clip imported with the real analyzer, renderer and verifier came out <!--n results/preparation-benchmark-2026-10-22/import-demonstration.json:receipt.status -->ready<!--/n--> in <!--n results/preparation-benchmark-2026-10-22/import-demonstration.json:commands.0.wall_clock_seconds -->114.23<!--/n--> s, outcome "<!--n results/preparation-benchmark-2026-10-22/import-demonstration.json:verification.outcome -->no flagged segments<!--/n-->" ([record](../results/preparation-benchmark-2026-10-22/import-demonstration.json)); terminal only | That title on the TV: the app's gates keep it off, as designed (below) |
| Only approved media reaches the TV | Exact-hash approval registry and build gates | Tool tests in `app/tools` | In an isolated copy of `app/`, the export and a dropped-in bundle were refused on the package budget, and the registry still compiled only its four catalogs | A new catalog going through approval: that needs the owner |
| Recovering an interrupted or damaged preparation | Ledger, atomic writes, locks, bound receipts | <!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.passed -->16<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:recovery.scenarios.scenarios -->16<!--/n--> recovery scenarios and <!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.killed -->24<!--/n--> of <!--n results/release-validation-2026-10-22/validation.json:recovery.guard_mutations.mutations -->24<!--/n--> guard mutations | With the real analyzer on the owned clip: restarts reused <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.steps_reused_on_restart.0 -->19<!--/n--> steps and rebuilt <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.steps_rebuilt_on_restart.0 -->6<!--/n-->; a flipped byte kept the title out of the catalog until a <!--n results/preparation-benchmark-2026-10-22/benchmark.json:integrity_demonstration.repair.seconds -->1.46<!--/n--> s repair; terminal only | A real power cut; shared network drives |
| Playback proof page | `PlaybackProofPanel.tsx`, `playbackProof.ts` | Proof, ten foot and UI flash tests | All three stages for Acadia and McWay, McWay's "version not recorded in this report", and the exact file identities ([screens](../results/native-review-2026-10-22/)) | VoiceView reading; a physical TV |
| Every part of the record reachable by remote | `ReadingStop.tsx` | A test fails on any text outside a reachable stop | Every section of Acadia's and McWay's records, and the closing Back | |
| Back returns focus to the opener | `TitleDetailsScreen.tsx` | Proof navigation test | Proof page to its opener, More info, then Home | |
| Calm ambient playback | Approved McWay edition, guarded player | App suite | <!--n results/replacement-demo-2026-10-22/demo.json:uncut_playback.seconds -->78<!--/n--> s recorded uncut at natural speed; the full five minutes ran to the still frame by trace | Listening: the audio was measured, not heard |
| The app's own screens do not flash | Light menu palette, near-luminance focus | <!--n results/release-validation-2026-10-22/validation.json:app.ui_flash_screens_and_transitions -->79<!--/n--> screens and transitions pass, with a negative control | The palette on every menu page | The owner's view of the palette; a physical TV |

## Measured preparation time

On one Mac (<!--n results/preparation-benchmark-2026-10-22/benchmark.json:machine.cpu -->Apple M1<!--/n-->), for one
<!--n results/preparation-benchmark-2026-10-22/benchmark.json:fixture.seconds -->20<!--/n--> s,
<!--n results/preparation-benchmark-2026-10-22/benchmark.json:fixture.width -->1280<!--/n-->x<!--n results/preparation-benchmark-2026-10-22/benchmark.json:fixture.height -->720<!--/n-->
owned clip, three runs each, with the real analyzer and all three presets:

| Phase | Median seconds | Range |
|---|---|---|
| Cold preparation | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.cold_seconds.median -->93.21<!--/n--> | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.cold_seconds.min -->87.66<!--/n--> to <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.cold_seconds.max -->95.45<!--/n--> |
| Warm rerun, every step reused | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.warm_seconds.median -->0.46<!--/n--> | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.warm_seconds.min -->0.45<!--/n--> to <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.warm_seconds.max -->0.49<!--/n--> |
| Killed mid-write after | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.kill_after_seconds.median -->28.21<!--/n--> | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.kill_after_seconds.min -->27.28<!--/n--> to <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.kill_after_seconds.max -->28.55<!--/n--> |
| Restart after the kill | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.restart_seconds.median -->62.07<!--/n--> | <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.restart_seconds.min -->61.73<!--/n--> to <!--n results/preparation-benchmark-2026-10-22/benchmark.json:summary.restart_seconds.max -->62.95<!--/n--> |

Verification is most of a restart, because it analyzes every output again, so a
kill plus restart costs about as much as a cold run here. What the restart saves
is correctness, not time: finished work is kept and nothing half-written is
trusted. These are measurements of one clip on one machine, not a rate for other
videos. Reproduce with
`python -m eval.preparation_benchmark --samples 3 --out <file> --transcript <file>`;
[the results](../results/preparation-benchmark-2026-10-22/benchmark.json) also hold
every check and the tool versions.

## Not verified anywhere yet

- How the audio sounds: it was measured, and nobody has listened to it.
- The owner's view of the light menu palette, pacing and the reading-stop focus.
- A physical Fire TV, VoiceView and the Home key.
- Hosted CI: this branch has not been pushed, so every result here is local.
- Detection beyond the published evaluation: analyzers can miss flashing.
