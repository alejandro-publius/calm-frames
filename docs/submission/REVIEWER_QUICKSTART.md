# Reviewer quickstart

For a judge with a Mac, a terminal and about thirty minutes. Written Oct 14,
2026 from the repository's own scripts and documents. On the evening of Oct 14
sections 1, 2 and 5 were run as written on a fresh checkout of this branch with
nothing copied from another checkout: the Node checks (`npm ci` 44 s, typecheck
6 s, lint 9 s with no errors, the full Jest suite 35 s, all passing), the
analyzer path in section 5 (install 12 s, `check` 17 s printing PASS, `report`
10 s), and the Python checks (the pytest line 5 minutes 17 seconds, the
number and style checks under a second, both mypy configurations clean). At
that run two Python tests failed for code reasons on this branch and `make
lint-py` reported ruff findings in `eval/preview` and `scripts`; they were
reported to the integration owner and are not setup problems. The later fixes
and local gate are recorded in [FINAL_HANDOFF.md](../../FINAL_HANDOFF.md)
section 2; the failures above describe that earlier fresh-checkout run.
Section 3 (the
device build and install) and section 4 (the demo) were not run from this
file; the receipts they name record where they were run.

Updated October 18, 2026 for installed source `6f2570d` on the coastal-world
working branch. The private GitHub handoff targets `codex/creator-editions-2026-10-18`.
[Current build and native evidence](../../results/sea-otters-flow-2026-10-18/README.md).
The fresh-checkout timings above remain historical; no new clean-room install is claimed.

## Current candidate, October 18

The installed app source is `6f2570da4165acc752882a0c04ffe996cd072880`.
The private handoff branch includes that source plus documentation and evidence;
use the final remote commit in the handoff receipt. The installed package and
current test scope are recorded in [the coastal-world evidence](../../results/sea-otters-flow-2026-10-18/README.md).
No clean-room rerun of the historical timings above is claimed.

After repository access is granted, start with the explicit working branch:

```sh
git clone --single-branch --branch codex/creator-editions-2026-10-18 https://github.com/alejandro-publius/calm-frames.git
cd calm-frames
git rev-parse HEAD
```

Use the reviewed commit from the handoff, not the repository's older default branch.
No account, key, preset PIN or signing credentials are required to run the existing
prepared Acadia catalog. A fresh install asks the reviewer to choose a private PIN.

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

Run on a fresh checkout of this branch on Oct 14 (evening): the venv took
seconds, the analyzer install two seconds with warm caches, and the extra
package is the one CI adds; without it the pytest line below stops at
collection. The same lines are in the README and
[../ENVIRONMENT.md](../ENVIRONMENT.md).

## 2. Check the repository without a device (about ten minutes)

From the repository root. These are the commands CI runs
([README.md](../../README.md), "Run the checks").

```sh
cd app && npm ci --ignore-scripts && npm run typecheck && npm run lint && npx jest --watchman=false --ci --colors=false --testPathIgnorePatterns="uiCapture|coastalExport|controlStudy" && cd ..
.venv/bin/python -m pytest flashmap pipeline eval -q -m "not slow"
.venv/bin/python eval/readme_sync.py --check     # every published number against results/
.venv/bin/python eval/style_check.py             # no dashes, none of the three banned words
```

`npm ci --ignore-scripts` skips the Shaka build, which the tests mock; a device
package needs the player setup below with the JDK. The latest installed source
passed 534 focused app tests across 38 suites and 11 attribution tests, plus
TypeScript, lint with zero errors, native-input and media delivery checks.
[The validation summary](../../results/sea-otters-flow-2026-10-18/validation-summary.json)
records the exact scope. An initial unrestricted Jest run exhausted its heap;
a duplicate surface callback was then fixed and the final bounded suites passed.
This is not a current full-suite pass. The older figures that follow are dated. On the October 14 candidate, the bounded reliability pass recorded 88 tests passing
across 8 suites with typecheck and focused lint
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
`4c9996d`; it predates this candidate and does not describe it. The candidate
has no hosted run because it has no pull request.

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
The current built package is
`build/release/sea-otters-flow-2026-10-18/calm-frames-coastal-world-aarch64-debug.vpkg`,
SHA-256 `8311d90bc34db2efaae77a8a5eda144d7d45cc3989035558860c1b4604e3e63b`, from
source `6f2570d`. See its [build and install record](../../results/sea-otters-flow-2026-10-18/README.md).
It is already installed on the owner's simulator; do not reinstall it merely
for owner acceptance. The commands below are for a separately authorized
reviewer installation. Preserve concurrent checkouts and the SDK app link.

```sh
nohup vega virtual-device start > /tmp/calm-frames-vvd.log 2>&1 < /dev/null &
vega device is-connected --device VirtualDevice      # wait for this, not for "status"
vega device info --device VirtualDevice
vega device install-app --device VirtualDevice --packagePath app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
vega device run-cmd --device VirtualDevice --command 'vmsgr send pkg://io.github.alejandropublius.calmframes.main'
```

Start the virtual device only if it is stopped; it must be started detached.
Avoid `vega device list`, which crashes on this SDK. The install and launch
lines are the ones the Oct 13 and Oct 14 sessions ran
([`results/polish_native_validation.json`](../../results/polish_native_validation.json),
[`results/native-observation-2026-10-14/receipt.json`](../../results/native-observation-2026-10-14/receipt.json)).

Remote buttons from the host, if the simulator window is inconvenient:

```sh
vega device run-cmd --device VirtualDevice --command 'inputd-cli button_press KEY_DOWN'
```

Keys seen to work in the receipts: `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`,
`KEY_ENTER`, `KEY_BACK`, `KEY_PLAYPAUSE`.

An optional software preflight drives the benign journey and writes a log:

```sh
.venv/bin/python -m eval.benign_native_smoke --device VirtualDevice \
    --vpkg app/build/aarch64-debug/calm-frames-app_aarch64.vpkg
```

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

Use [DEMO_RUN_OF_SHOW.md](DEMO_RUN_OF_SHOW.md) and the
[exact owner keys](../../results/sea-otters-flow-2026-10-18/OWNER_WALKTHROUGH.md).
Preserve an existing household; no PIN entry or reset is part of this walkthrough.

From Home with Acadia selected and Watch focused:

1. **Up, Right, Select** opens Sea Otters Details with Watch focused.
2. **Select** starts the exact NOAA Fisheries ocean excerpt: 19.987 seconds, silent,
   plays once. End/Back returns to Details Watch; Back returns to the selected destination.
3. **Left, Down, Left** reaches Home Acadia Watch. Select plays approved Acadia.
   Under the current extra-cautious profile the two replacement intervals are
   7.343 to 12.699 seconds and 28.113 to 31.593 seconds. The rendition has approved
   baked ocean replacements and retained original audio, plus an independent opaque fallback.
4. **Play/Pause** toggles playback; **Down** reveals hidden controls. Select on focused
   Skip requests protection before seeking. End/Back restores the launching screen.
5. Details shows covered sections; More info contains source credits and limits.
   Parents cancellation restores focus to Parents without entering a PIN.

Current native text logs cover these core behaviors on `6f2570d`. They do not certify
pixels, audio, VoiceView or physical Fire TV behavior. Loading/error recovery is
controlled-test evidence. The legacy WCAG-only playback check is unavailable under
extra-cautious; do not change settings to expose it. No screenshot or recording is authorized.

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
was written for the October 14 interface and was not rechecked against the
installed build.

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
