# Reviewer quickstart

Current source, October 21, 2026: use private branch
`claude/ocean-layout-fix-2026-10-19`, not the older default branch. The approved
McWay edition provides five continuous minutes at natural speed and then an
indefinite final-frame hold. It does not loop or automatically exit. Acadia,
Sea otters and Forest remain available as still scenes with optional short previews.

Authenticated preparation and strict delivery passed for all three McWay presets.
See [the exact receipt](../../results/mcway-activation-2026-10-21/verification.json).
The later local ending fix `60c3bbb` is built and installed. Its exact package,
checks and native screenshots are in the [current presentation record](../presentation/README.md).
The ending fix is an ancestor of this presentation revision. Confirm the
current candidate branch head with `git rev-parse HEAD` after cloning. Final edited-demo/audio acceptance and
publication remain open. The installed ending fix is included in the candidate
branch; no new native review is implied by later documentation commits.
Historical test timings and device receipts below describe their stated earlier
commits and are not acceptance of the current edition.

After repository access is granted, start with the explicit working branch:

```sh
git clone --single-branch --branch claude/ocean-layout-fix-2026-10-19 https://github.com/alejandro-publius/calm-frames.git
cd calm-frames
git rev-parse HEAD
```

`git rev-parse HEAD` identifies the exact candidate you checked out. Use this branch, not the repository's older default branch.
No account, key, preset PIN or signing credentials are required to run the
existing prepared catalog (McWay Falls, Acadia, Sea otters, Forest). A fresh install asks
the reviewer to choose a private PIN.

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
uv pip install --python .venv/bin/python matplotlib==3.11.2   # the evaluation tests draw plots
```

Run on a fresh checkout of the October 14 candidate (evening): the venv took
seconds, the analyzer install two seconds with warm caches, and the extra
package is the one CI adds; without it the pytest line below stops at
collection. The same lines are in the README and
[../ENVIRONMENT.md](../ENVIRONMENT.md).

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
package needs the player setup below with the JDK. On this branch the full app
suite passed on `53a1c51`: 163 suites, 1,676 tests passed, 0 failed, 4 skipped,
with the coverage floors met
([log](../../results/home-islands-2026-10-19/full-suite-after.log)). The same
suite had 18 failing tests on `c84f95d`
([log](../../results/home-islands-2026-10-19/full-suite-before.log)). The later
full-source baseline and bounded ending-fix checks are recorded in
[the current presentation evidence](../presentation/README.md); the October 19
figures here are historical. The Python line above, with `-m "not slow"`, passed on
`d9c9e2f`: 1,880 passed, 0 failed, 9 skipped, 2 slow tests deselected
([log](../../results/home-islands-2026-10-19/python-suite-d9c9e2f.txt)). These are recorded
results, not a new run of these instructions. The October 18 record for
`805f855` counted a bounded 499 app tests in 38 suites and 11 attribution tests
([validation summary](../../results/forest-activation-2026-10-18/validation-summary.json)),
not the full suite. The older figures that follow are dated. On the October 14
candidate, the bounded reliability pass recorded 88 tests passing across 8
suites with typecheck and focused lint
([`results/core-reliability-2026-10-14.json`](../../results/core-reliability-2026-10-14.json)),
and the release helper's 39 tests passing
([`results/release-pin-license-review-2026-10-14.json`](../../results/release-pin-license-review-2026-10-14.json)).
An earlier full app suite ran on Oct 14 on `00905510`
([`results/native-checkpoint-2026-10-14/receipt.json`](../../results/native-checkpoint-2026-10-14/receipt.json):
<!--n results/native-checkpoint-2026-10-14/receipt.json:checks.full_jest.passed -->1198<!--/n--> passed,
<!--n results/native-checkpoint-2026-10-14/receipt.json:checks.full_jest.skipped -->4<!--/n--> skipped).
The handoff records the later full app suite on package 5's source `4016e8d`:
133 suites and 1310 tests passed, with typecheck and lint clean. That is a
recorded result, not a new run of these instructions.
The hosted `Vega app` job that failed on Oct 13 ran on the shared PR branch head
`4c9996d`; it predates this branch and does not describe it. This branch has
no hosted run: CI runs on pushes to `main` and on pull requests, and the branch
had no pull request when the GitHub API was asked on October 19.

## 3. Build, install and launch on the Vega Virtual Device

```sh
cd app
npm ci --ignore-scripts                      # exact dependency lock
npm run setup:player                         # Vega environment + JDK 21; generates ignored runtime
npm run check:native-inputs                  # fail early with repair instructions
cd ..
bash scripts/release.sh --arch aarch64 --build-type Debug --tag reviewer-$(date +%Y%m%d)
```

The setup and preflight scripts are present in this handoff. The player setup
builds Shaka and copies its generated runtime and polyfills. `npm ci --ignore-scripts`
alone is sufficient for headless checks but cannot build a native package.
Do not copy another checkout's `node_modules` or reset shared Watchman caches.
Metro uses a checkout-specific cache and does not depend on Watchman.

`scripts/release.sh` builds one architecture, checks the library and package,
and writes a local package, hashes and preparation receipt. It never publishes.
Use Python 3.12 through `RELEASE_PYTHON` or `.venv/bin/python`. Do not pass a PIN.
The current local package and installation are recorded in the linked
presentation evidence. Preserve an existing household and do not reset its PIN.
The following commands are for a reviewer installation, not an instruction to
repeat the already completed local installation.

```sh
nohup vega virtual-device start > /tmp/calm-frames-vvd.log 2>&1 < /dev/null &
vega device is-connected --device VirtualDevice      # wait for this, not for "status"
vega device info --device VirtualDevice
vega device install-app --device VirtualDevice --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg --buildType Debug
vega device run-cmd --device VirtualDevice --command 'vmsgr send pkg://io.github.alejandropublius.calmframes.main'
```

Start the virtual device only if it is stopped; it must be started detached.
Avoid `vega device list`, which crashes on this SDK. The install and launch
lines are what the October 18 native script ran
([`native_walkthrough.py`](../../results/forest-activation-2026-10-18/native_walkthrough.py)).
The October 14 session used `--device Simulator` and `vega device launch-app
--appName io.github.alejandropublius.calmframes.main`
([`results/native-observation-2026-10-14/receipt.json`](../../results/native-observation-2026-10-14/receipt.json)),
historical CLI syntax, not the current commands above.

Remote buttons from the host, if the simulator window is inconvenient:

```sh
vega device run-cmd --device VirtualDevice --command 'inputd-cli button_press KEY_DOWN'
```

Keys seen to work in the receipts: `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`,
`KEY_ENTER`, `KEY_BACK`, `KEY_PLAYPAUSE`.

An optional read-only preflight checks the connected device and the package and
prints a plan; it presses no keys and installs nothing:

```sh
.venv/bin/python -m eval.benign_native_smoke --device VirtualDevice \
    --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
```

Do not add `--execute` for this walkthrough: that installs the package and
counts only playback of the Harbor demo, which the current Home does not list.

Logs do not prove what was on screen; look at the simulator. A Debug package
also prints breadcrumbs you can follow from the host while you drive the app:

```sh
vega device start-log-stream --device VirtualDevice | grep --line-buffered -E 'CALM_TRACE|CALM_TIMING'
```

`CALM_TRACE screen|focus|still|image` lines say which view is up, which control
has focus and whether artwork and the hold still loaded; `CALM_TIMING` lines
are the player's media events. The device prints each app line twice and drops
some under load, so a missing line proves nothing.

## 4. The current demo sequence

Use [DEMO_RUN_OF_SHOW.md](DEMO_RUN_OF_SHOW.md) for the current calm recording plan.
Preserve the existing household and never use blind repeated Back presses. Home
retains Ocean/Forest and all approved titles. McWay is an additional coastal card;
select it explicitly and choose Watch. It plays five minutes at natural speed,
then holds its final frame until Back. Existing Acadia, Sea otters and Forest
start as still scenes and expose short previews only through a separate action.

Before recording, independently verify a complete five-minute run, final audio
fade and still hold, pause/resume and Back on the exact installed build. The prior native session observed the full run, pause/resume, Back and corrected
ending picture; screenshots and limits are linked above. Final edited-demo and
subjective audio acceptance remain open. No physical-TV acceptance is claimed. Do not
show the diagnostic app or replay the rejected short-preview walkthrough.

## 4a. A browser preview, without a device

```sh
cd app && npx jest --ci --watchman=false --coverage=false test/calmframes/coastalExport.test.tsx && cd ..
.venv/bin/python eval/preview/coastal_preview.py
.venv/bin/python -m http.server 4174 --bind 127.0.0.1 --directory build/coastal-preview
```

Then open <http://127.0.0.1:4174/>. It is an HTML export of the rendered
component trees with CSS approximations: Home links to Details, the practice
entry, How it works and Parents, and keyboard focus cycles. Play, PIN keys and unmapped
actions only show a notice. It does not run the native handlers, media,
persistence, PIN checks, D-pad spatial navigation or VoiceView. This section
was written for the October 14 interface. Its fixture is the regression shelf,
which adds the locally prepared Harbor story and the practice demo to the three
titles, so its Home is the flowing "Choose an island" shelf, not the current
Ocean and Forest map. The
current Home, Details and opening screens are in the committed
[October 19 renders](../../results/home-islands-2026-10-19/README.md),
Chromium renders of the component trees, not device pictures;
`eval/preview/render_islands.mjs` says in its header how they were made.

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

The local intake, review and staging page runs on loopback. Its serve command
and input limits are in [the intake handoff](../LOCAL_INTAKE_HANDOFF.md), and
staging is in [the delivery integration record](../DELIVERY_INTEGRATION_FINAL.md).
Staging records approval status; it does not install a title or enable Watch.

## 6. AWS, offline

```sh
uv pip install --python .venv/bin/python -r pipeline/infra/requirements.txt
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
| `CALM_FRAMES_REQUIRE_NODE` | `eval/property_runner.py`, set by `make properties` and `eval/mutate_gate.py` | Makes a test fail instead of skip when Node is missing |

The map-signing private key never enters the repository; the app ships only
the public key, and the key for the Harbor demo is its own.

## 8. Safety while reviewing

Files under `media/` with the `HAZARD_` prefix contain real flashing footage
and are excluded from git. Do not open one in a player; inspect with
`eval/plots.py`. Generated conformance clips are hazardous by design and are
deleted by the job that makes them. The bundled Harbor media contains no flashing.
