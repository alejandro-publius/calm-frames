# Finish the polished simulator demo on the Mac

Design baseline: `54dab0b`, plus the shared fixes through `9afacc0`. This handoff
uses the accompanying updated build, capture and review tools. Sync those changes too. Use the current
[completion checklist](COMPLETION_CHECKLIST.md) if later work changes this state.
These Mac commands were checked against repository scripts and earlier receipts;
they have not been executed in the cloud session.

The latest artwork and TV layouts are pushed. The saved native package and demo
still show the earlier design. Finish by rebuilding, observing and recording the
current source on the existing Vega Virtual Device. Include the latest focus and
screen-reader fixes in that check. No physical stick is needed.

## 1. Reconcile the existing checkout

Use the existing Mac checkout and review branch. Preserve local work, recordings,
household data and the separate AWS worktree. From the repository root:

```sh
git status --short
git branch --show-current
git fetch origin
git log --oneline --left-right HEAD...origin/codex/signed-scene-holds-2026-09-29
```

If the tree is clean, this is the review branch and it can advance without a
merge, run:

```sh
git merge --ff-only origin/codex/signed-scene-holds-2026-09-29
```

If local changes or commits exist, inspect and preserve them before reconciling.
Do not reset, clean, replace the checkout or force-push. Commit and push checked
batches to this same branch as work progresses. Do not merge into `main`.

## 2. Activate the known tools and build

```sh
source ~/vega/env
eval "$(fnm env)"
fnm use
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
node --version
"$JAVA_HOME/bin/java" -version
vega sdk list-installed
.venv/bin/python --version
```

Expected toolchain: Node 22, JDK 21, Python 3.12 and Vega SDK 0.24.9914.
Use the existing working installation. If app dependencies need restoration,
run `npm ci` inside `app` with this JDK active. Its postinstall builds Shaka;
`--ignore-scripts` alone is insufficient for a native package. Inspect tracked
changes afterward. Do not use the package's destructive `clean` script.

The final preparation gate now requires the original verification reports for
all retained library generations. Older catalogs preserve their report hashes,
but this cloud checkout does not contain the matching originals. Normal delivery
checks list missing reports; release preparation refuses to proceed without them.
Attach the originals on the Mac before building, using their actual paths:

```sh
.venv/bin/python -m pipeline.packaged_library check --output app/assets/raw/prepared-library
.venv/bin/python -m pipeline.packaged_library attach-reports \
  --output app/assets/raw/prepared-library \
  --report /path/to/first/original/verify/report.json \
  --report /path/to/second/original/verify/report.json
.venv/bin/python -m pipeline.packaged_library check \
  --output app/assets/raw/prepared-library --require-reports
```

The attachment command accepts only exact report hashes already referenced by
the library and checks source, presets, passing checks and outcome. It keeps the
catalog, signed maps, captions and video bytes unchanged. Future exports carry
the original reports automatically. A regenerated report is new evidence and
cannot replace an original under its old hash. If an original is unavailable,
record that blocker; preserve existing evidence while planning a new verified
export. Do not bypass the strict gate.

Inspect report contents before committing: originals can contain local paths and
analyzer output. Do not redact a file while retaining its old digest. Run the
repository's secret scan on the exact staged changes.

Run the current checks and build the Apple Silicon Debug package:

```sh
cd app
npm run typecheck
npm test -- --runInBand --coverage=false
node tools/check_prepared_library.mjs --require-reports
cd ..
bash scripts/release.sh --arch aarch64 --build-type Debug --tag review-polish-mac
```

The local release preparer builds only the selected architecture and checks its
package identity, native runtime and exact prepared-library bytes. It saves a
build receipt at `app/build/aarch64-debug/release-build-receipt.json` and a local
`build/release/<tag>/` directory with hashes and `PREPARATION.json`. It does not
publish or claim simulator validation. Commit any reviewed SDK-generated app
changes before the native capture session, then recheck the package with its
build receipt using `--skip-build` and a new tag. This makes its source commit
reproducible. Choose a new tag if an output exists; preserve previous artifacts.

The underlying build is `npm exec -- react-native build-kepler --build-type Debug
--target aarch64` inside `app`. The older `npm run build:debug` postbuild hook
checks all three architectures. The preparer uses explicit checks for the chosen
target instead. To recheck its prepared-library bytes directly:

```sh
cd app
node tools/check_prepared_library.mjs --packages Debug --arch aarch64 --require-reports
cd ..
```

Inspect any generated `app/manifest.toml` changes against the pre-build tree.
When reusing a package later, `release.sh --skip-build` requires a matching
`--receipt` with package and complete app-input hashes. A file merely existing
is not proof that it matches the current source.

## 3. Install and observe the current package

Start the virtual device only if it is stopped. Start it detached:

```sh
nohup vega virtual-device start > /tmp/calm-frames-vvd.log 2>&1 < /dev/null &
```

Wait for an actual connection, then use the explicit simulator target:

```sh
vega device is-connected --device Simulator
vega device info --device Simulator
vega device install-app --device Simulator --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
vega device launch-app --device Simulator --appName io.github.alejandropublius.calmframes.main
.venv/bin/python -m eval.benign_native_smoke --device Simulator \
  --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
```

After the read-only preflight passes, run it again with `--execute --restart`.
Operate the visible app during both capture periods. The runner creates a new
timestamped log directory and preserves household data. A successful software
receipt alone does not establish visible composition or usable focus.

Use the visible remote or the verified device command:

```sh
vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'
```

Record fresh observations for these journeys:

1. Reach every library action with the D-pad; check focus, Back and return focus.
   Switch profiles and confirm focus remains visible while the choice is saved.
   Repeated presses during that save must not write another choice.
2. Scroll the entire details, setup, parental controls and settings pages.
3. Check incorrect PIN, Delete correction, successful unlock and relocking.
4. Check fresh setup only in a preserved or separate test household; never erase
   existing user data to reach onboarding. Record any untested setup path.
5. Change presets, room settings and chime; restart and verify persistence.
6. Play every offered compatible title; verify the stricter presets keep Harbor.
7. Play both labelled Harbor practice holds with audible tone and English captions.
8. Check caption Off, pause/resume, guarded seeks, Skip, loading Back and replay.
9. Observe the interruption fallback and confirm practice holds do not add history.
10. With the screen reader enabled, reach notice actions separately from their
    announcements and hear every displayed credit and licence condition. Use a
    separate test profile for removal confirmation; preserve existing household data.

Use only the bundled benign media. Practice holds are synthetic examples;
simulator observations do not measure physical screen timing. A UI or logic fix
requires a new package and affected native observations before final recording.

## 4. Capture, assemble and bind the evidence

Use `eval/record_vega_window.m`, the existing macOS ScreenCaptureKit recorder,
and its earlier local build procedure. It accepts an output path and seconds;
zero seconds saves a PNG. Capture the composited Vega window and native audio.
Keep Vega foregrounded and avoid taking screenshots during video capture.
macOS Screen Recording permission, if absent, needs the user's OS interaction;
continue independent preparation while that is unavailable.

Save new captures to a fresh local directory. Preserve the earlier recordings,
package, demo and receipts. Reuse the sequence in [SHOT_MANIFEST.md](SHOT_MANIFEST.md)
and [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md), replacing the actual app shots with the
polished build and updating claims to match the new observations.

The assembler now requires an explicit capture manifest. Generate its template:

```sh
.venv/bin/python eval/assemble_demo.py --write-template .logs/polish-capture-plan.json
```

Fill `capture_source_commit` with the exact full commit used for the captures,
`capture_package.path` and `sha256` with the installed package, and each shot's
`source`, `sha256`, `kind`, timings and narration. Relative inputs start at the
repository root. The editorial status card is an explicit image input too.
Review every narration claim against the fresh observations. Keep actual stills,
editorial cards and synthetic narration labelled. Preserve earlier outputs.

```sh
.venv/bin/python eval/assemble_demo.py --manifest .logs/polish-capture-plan.json \
  --output-dir build/submission-polish --result results/polish_demo_manifest.json --dry-run
.venv/bin/python eval/assemble_demo.py --manifest .logs/polish-capture-plan.json \
  --output-dir build/submission-polish --result results/polish_demo_manifest.json
bash eval/check_video.sh build/submission-polish/Calm-Frames-demo-English.mp4 \
  --max-seconds 179 --out results/polish_video_check.json
bash eval/check_video.sh build/submission-polish/Calm-Frames-demo-English.mp4 \
  --profile broadcast --max-seconds 179 --out results/polish_video_check_broadcast.json
```

The preflight checks the supplied hashes and media before Mac assembly.
Check audio for clipping and intelligibility, captions for readability, and
the entire finished edit for stale frames or accidental desktop/account details.
Record the exact final source commit and fresh package/video hashes:

```sh
git rev-parse HEAD
shasum -a 256 app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
shasum -a 256 build/submission-polish/Calm-Frames-demo-English.mp4
.venv/bin/python eval/readme_sync.py --check
```

Create `results/polish_native_validation.json` with `source_commit`,
`package: {path, sha256, target}`, the complete `app_source_files` inventory from
the build receipt, fresh observations and selected `capture_files`/`evidence_logs`
entries containing `path` and `sha256`. Mark installed and observed behavior only
after those actions occur. Keep real household PINs out of logs and receipts.

Rebuild the review archive from the new native and demo receipts:

```sh
.venv/bin/python eval/package_redesign_review.py \
  --native-receipt results/polish_native_validation.json \
  --demo-manifest results/polish_demo_manifest.json \
  --output build/calm-frames-polish-review.zip \
  --receipt results/polish_review_bundle.json
```

Verify the ZIP CRC and payload hashes. The bundler requires matching app trees
and package identities and refuses existing outputs. Update the checklist and
shot manifest accurately. Do not relabel the earlier receipt as evidence for
this build or replace published artifacts during preparation.

## 5. Keep the remaining release work explicit

Read the latest security audit before finalizing its wording. The checkpoint
now has a passing dependency gate with two documented exception groups due for
review on October 21. Findings remain, including saved AWS cost-tag/image
findings. Keep that distinction explicit and do not weaken the checks.
[AMAZON_SAMPLE_LICENSE_REVIEW.md](AMAZON_SAMPLE_LICENSE_REVIEW.md) records the
license conflict that remains open before public source release.

The Amazon Developer account is already identity-verified. Remaining entrant
form values, public author identity, reviewer/video links, upstream contribution
and final publication/submission are separate tasks. Do not invent credentials,
send outreach, change billing, deploy AWS, publish or submit from this handoff.

## Copy and paste into the agent on the Mac

> Continue Calm Frames from docs/MAC_FINISH.md and the current completion checklist.
> Reconcile the existing review branch with the pushed cloud work while preserving
> local edits, captures, household data and the AWS worktree. Use only the Vega
> Virtual Device. Rebuild the latest polished source for Apple Silicon aarch64
> Debug after attaching the original verification reports and passing the strict
> evidence gate, validate the exact prepared package, install it, exercise the native
> journeys, fix observed issues and record a fresh English demo under 179 seconds.
> Refresh capture provenance, package/video hashes, gates and the review bundle;
> preserve the earlier evidence. Commit and push small checked batches to the
> existing review branch. Routine inspection, builds, fixes, simulator operation
> and local recording are authorized; do not ask me to reconfirm each step.
> If using Claude CLI workers, first verify existing Max subscription auth and
> one small successful task. Do not switch to API-key billing or change accounts.
> If Claude is unavailable, continue the independent work and report the limitation.
> Keep unresolved security and license findings explicit. No physical stick,
> outreach, AWS spending, public publication, visibility change or submission.
> Stop only for an actual missing prerequisite that prevents the next useful work,
> and tell me exactly what is blocked and what you already completed.
