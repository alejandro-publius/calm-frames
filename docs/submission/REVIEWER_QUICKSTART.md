# Reviewer quickstart

For a judge with a Mac, a terminal and about thirty minutes. Written Oct 14,
2026 from the repository's own scripts and documents. **None of the commands
below were executed while writing this file.** Where a command has been run by
an earlier session, the receipt that records it is named; everything else is
marked unverified.

The working integration baseline is `codex/core-reliability-2026-10-14` at
`cfddc4adb8bcdd17a861e6489f5fb50693c282d3`, a candidate; the final judged
release is still to be selected ([OPEN_DECISIONS.md](OPEN_DECISIONS.md)). Use
the branch or tag named in the submission form.

## 1. What you need

| Tool | Version | Why |
|---|---|---|
| Vega SDK and CLI | SDK 0.24.9914, CLI 1.3.4 | Build, virtual device, install and launch |
| Node | 22 (`.nvmrc`) | The app |
| Python | 3.12 (`.python-version`) | flashmap, the pipeline and the checks |
| JDK | 21 | The Shaka Player build during `npm install` only |
| ffmpeg and ffprobe | 9.0.1 (6.1.1 also passes the suite) | Pipeline and measurements |

Apple Silicon Mac: the packages are built for `aarch64`. Full versions are in
[../ENVIRONMENT.md](../ENVIRONMENT.md).

```sh
source ~/vega/env                        # Vega CLI and SDK on PATH
eval "$(fnm env)" && fnm use             # Node 22
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e "./flashmap[dev]"
```

Unverified in this session; the same lines are in the README and
[../SUBMISSION.md](../SUBMISSION.md) section 9.

## 2. Check the repository without a device (about ten minutes)

From the repository root. These are the commands CI runs
([README.md](../../README.md), "Run the checks").

```sh
cd app && npm ci --ignore-scripts && npm run typecheck && npm run lint && npx jest --ci --colors=false && cd ..
.venv/bin/python -m pytest flashmap pipeline eval -q -m "not slow"
.venv/bin/python eval/readme_sync.py --check     # every published number against results/
.venv/bin/python eval/style_check.py             # no dashes, none of the three banned words
```

`npm ci --ignore-scripts` skips the Shaka build, which the tests mock; a device
package needs the full `npm install` with the JDK. Unverified here. On the candidate, the bounded reliability pass recorded 88 tests passing
across 8 suites with typecheck and focused lint
([`results/core-reliability-2026-10-14.json`](../../results/core-reliability-2026-10-14.json)),
and the release helper's 39 tests passing
([`results/release-pin-license-review-2026-10-14.json`](../../results/release-pin-license-review-2026-10-14.json)).
The last full app suite in the repository ran on Oct 14 on `00905510`
([`results/native-checkpoint-2026-10-14/receipt.json`](../../results/native-checkpoint-2026-10-14/receipt.json):
<!--n results/native-checkpoint-2026-10-14/receipt.json:checks.full_jest.passed -->1198<!--/n--> passed,
<!--n results/native-checkpoint-2026-10-14/receipt.json:checks.full_jest.skipped -->4<!--/n--> skipped).
The hosted `Vega app` job that failed on Oct 13 ran on the shared PR branch head
`4c9996d`; it predates this candidate and does not describe it. The candidate
has no hosted run because it has no pull request.

## 3. Build, install and launch on the Vega Virtual Device

```sh
cd app
npm install                                  # runs the Shaka build; needs JAVA_HOME
cd ..
bash scripts/release.sh --arch aarch64 --build-type Debug --tag reviewer-$(date +%Y%m%d)
```

`scripts/release.sh` builds the one architecture, checks the prepared library
and package identity, and writes `build/release/<tag>/` with the package,
`SHA256SUMS`, `PREPARATION.json` and `NOTES.md`. It never publishes. It needs a
Python 3.12 on `RELEASE_PYTHON` or at `.venv/bin/python`. The older route is
`npm run build:debug -- --target aarch64` inside `app`. Unverified here; the
Oct 14 receipts record the exact `release.sh` line that produced their packages.
Since `cfddc4a` the helper no longer reads `DEMO_PIN` and never writes a supplied
PIN into `NOTES.md`; `--pin` is kept as a deprecated option whose value is unused
(`results/release-pin-license-review-2026-10-14.json`). A package built from
`cfddc4a` exists as build output outside git in the reliability worktree,
`build/release/core-reliability-cfddc4a-2026-10-14/`, SHA-256
`e315e16d19172a5aadc1bfa8a9364bcf9205d51870ec610b92eb01ea9d2841dd`, with its 723
recorded source inputs verified and `native_validation_performed: false`.

```sh
nohup vega virtual-device start > /tmp/calm-frames-vvd.log 2>&1 < /dev/null &
vega device is-connected --device Simulator      # wait for this, not for "status"
vega device info --device Simulator
vega device install-app --device Simulator --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
vega device launch-app --device Simulator --appName io.github.alejandropublius.calmframes.main
```

Start the virtual device only if it is stopped; it must be started detached.
Avoid `vega device list`, which crashes on this SDK. The install and launch
lines are the ones the Oct 13 and Oct 14 sessions ran
([`results/polish_native_validation.json`](../../results/polish_native_validation.json),
[`results/native-observation-2026-10-14/receipt.json`](../../results/native-observation-2026-10-14/receipt.json)).

Remote buttons from the host, if the simulator window is inconvenient:

```sh
vega device run-cmd --device Simulator --command 'inputd-cli button_press KEY_DOWN'
```

Keys seen to work in the receipts: `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`,
`KEY_ENTER`, `KEY_BACK`, `KEY_PLAYPAUSE`.

An optional software preflight drives the benign journey and writes a log:

```sh
.venv/bin/python -m eval.benign_native_smoke --device Simulator \
    --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
```

Logs do not prove what was on screen; look at the simulator.

## 4. The demo sequence (about ten minutes)

1. **First run.** The app asks for a household PIN. Choose any four digits and
   confirm them; there is no preset PIN in the package and it is never stored in
   plain text. Pick a profile, a viewing preset and the room.
2. **Home.** Move focus with the D-pad across Play, Details, Try picture holds,
   Parental controls and How it works. The line under Harbor reads "20 sec ·
   No picture holds".
3. **Try picture holds.** Select it, read "20 sec · 2 practice holds" on the
   details page, then Play. Watch the countdown and Skip, then the first hold:
   the picture holds a still, the "Holding a calm scene" card appears, captions
   change and the sound continues. The second hold follows. These are scheduled
   examples, not detected flashing.
4. **Transport.** Pause and resume; seek back into a hold and watch the cover
   appear before the picture moves; press Back and see focus return to the tile.
5. **Harbor.** Play the ordinary title: the same film with zero holds.
6. **Parental controls.** Enter a wrong PIN and see it rejected with the tries
   remaining, correct it with Delete, enter the right one. Change the preset or
   the room, relaunch the app and see the choice kept. Practice holds never
   enter the exposure history, so an empty history after the demo is correct.

Steps 1 to 3, 5 and the PIN gate of step 6 were observed on Oct 13 and 14 on
earlier builds; the settings interior and the restart were last observed on the
Oct 10 build. The seek into a hold has only test coverage. Re-verify everything
on the final package.

## 5. The analyzer, the Action and the hook, without the app

```sh
python -m flashmap check VIDEO.mp4 --profile wcag        # 0 under, 1 over, 2 could not tell
python -m flashmap keygen --out team_key
python -m flashmap analyze VIDEO.mp4 --profile wcag --out MAP.json --key team_key.pem
python -m flashmap verify MAP.json VIDEO.mp4 --pub team_key.pub.pem
python -m flashmap report VIDEO.mp4 --out report.html    # never shows a frame of the film
```

Treating exit code 2 as a pass is a hole. The GitHub Action is
`flashmap/examples/flash-check.yml`; copy it into `.github/workflows/`. The hook
installs from a local tarball (`npm pack ./hook`, then `npm install` the tarball
in a Vega app); [`hook/README.md`](../../hook/README.md) has the lines and the
peer list. The sidecar format is [../SIDECAR_SPEC.md](../SIDECAR_SPEC.md).
Unverified here.

A full local preparation of a calm clip, ending in a package that includes it:

```sh
python -m pipeline.local_library prepare CALM.mp4 --workdir build/local-library \
    --key team_key.pem --pub team_key.pub.pem --title 'Our calm video' \
    --presets wcag,broadcast,extra-cautious
python -m pipeline.packaged_library export --workdir build/local-library \
    --output app/assets/raw/prepared-library --pub team_key.pub.pem
```

Use a benign clip. Never open a file with the `HAZARD_` prefix in a player.

## 6. AWS, offline

```sh
pip install -r pipeline/infra/requirements.txt
make synth            # synthesizes the CDK stack; no credentials, no account touched
```

Deploying is behind two locks and a human checkpoint and is not part of a
review. The Oct 9 deployment record, with every account identifier left out,
is [`results/aws_deploy_2026-10-09.json`](../../results/aws_deploy_2026-10-09.json).

## 7. Configuration names

No value here is a secret, and no secret is needed to review the app.

| Name | Where it is read | Meaning |
|---|---|---|
| `JAVA_HOME` | `npm install` in `app` | JDK 21 for the Shaka build |
| `RELEASE_PYTHON` | `scripts/release.sh` | Python used by the release preparer; defaults to `.venv/bin/python` |
| `DEMO_PIN` | formerly `scripts/release.sh` | No longer read since `cfddc4a`; `--pin` remains as a deprecated option whose value is unused, so no PIN reaches a reviewer document |
| `CHECKPOINT_D` | `Makefile`, `pipeline/upload_server.py` | Must read `confirmed` before anything can reach AWS |
| `AWS_REGION`, `CDK_DEFAULT_ACCOUNT`, `CDK_DEFAULT_REGION` | CDK deploy only | Not needed for `make synth` |
| `CALM_FRAMES_CHROME` | `eval/report_page_check.py` | A Chrome binary for the report page check |
| `CALM_FRAMES_REQUIRE_NODE` | `Makefile` | Makes a target fail instead of skip when Node is missing |

The map-signing private key never enters the repository; the app ships only
the public key, and the key for the Harbor demo is its own.

## 8. Safety while reviewing

Files under `media/` with the `HAZARD_` prefix contain real flashing footage
and are excluded from git. Do not open one in a player; inspect with
`eval/plots.py`. Generated conformance clips are hazardous by design and are
deleted by the job that makes them. The bundled Harbor media contains no flashing.
