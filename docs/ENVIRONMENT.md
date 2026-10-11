# Environment

Recorded Thu Sep 17, 2026. Updated Sat Sep 19, 2026 for ffmpeg. Update this file
whenever a tool is added or a version changes.

## Machine

| Item | Value |
|---|---|
| OS | macOS 15.1.1 (build 24B91) |
| CPU | Apple M1, arm64 (Rosetta 2 installed) |
| Memory | 16 GB total, about 51% free at check time |
| Free disk | 1.2 TiB |
| /dev/kvm | Not applicable (macOS) |
| Vega SDK support | Supported. SDK 0.24 runs on macOS with Apple silicon. |

## Pinned toolchain for this repo

| Tool | Version | How it is pinned or activated |
|---|---|---|
| Vega CLI | 1.3.4 | Installed by the official installer to `~/vega/bin` |
| Vega SDK | 0.24.9914 (released Aug 10, 2026, latest on the main channel) | `vega sdk list-installed`; install again with `vega sdk install 0.24.9914` |
| Vega Virtual Device | Bundled with SDK 0.24.9914 at `~/vega/sdk/vega-sdk/main/0.24.9914/vvd` | `vega virtual-device start` |
| Node.js | 22.23.2 (npm 10.9.8) | `.nvmrc` = 22, through fnm 1.39.0: `eval "$(fnm env)" && fnm use` |
| Python | 3.12.13 | `.python-version` = 3.12, venv at `.venv` made with uv 0.11.28 |
| watchman | 2026.07.27.00 | Homebrew |
| gitleaks | 8.30.1 | Homebrew |

The system `python3` on PATH is 3.9.13 and too old. Run Python through `.venv/bin/python` or `uv run`. The system Node on PATH is 26.0.0, newer than the sample supports (`engines.node >= 22`), so use fnm.

## Other tools found

| Tool | Version | Notes |
|---|---|---|
| git | 2.39.5 (Apple Git-154) | |
| gh | 2.92.0 | Signed in as alejandro-publius |
| ffmpeg and ffprobe | 9.0.1 (Homebrew `9.0.1_1`, arm64) | Was 8.1.2 until Sep 18, 2026. Encoders include libx264, libx264rgb, libvpx, libvpx-vp9. See "The three ffmpegs" below before quoting a number that came out of one. |
| Docker | client 29.7.2, engine 29.5.2 | Engine runs in colima 0.10.3 (aarch64 VM, 2 CPUs, 4 GiB). The VM is shared with other projects: do not restart colima or remove containers without checking first. |
| jq | 1.6 (Apple build) | |
| uv | 0.11.28 | Covers what pipx would do |
| AWS CLI | 2.36.44 | Credentials configured locally, region us-west-2. CI will use GitHub OIDC only. |
| Homebrew | 7.0.1 | |
| Swift | 6.0.3 (Command Line Tools) | Full Xcode is not installed; only needed for the Apple baseline (cut list item 4) |
| Java | 1.8 (x86_64 only) | The Shaka Player build in `app/shaka-setup` may need a newer JDK; check during `npm install` |
| Visual Studio Code | 1.125.1 | Vega Studio extension not installed (optional) |

Not installed yet: AWS CDK (will be pinned in `pipeline/infra/package.json`), cmake and ninja (only needed inside the IRIS container).

## Vega install notes

- Installer: `https://sdk-installer.vega.labcollab.net/get_vvm.sh`, SHA-256 `0e5386581e5cf518202687213dd26d1b35e70242d1bd190cdea7096a99476ae0` on Sep 17. It was read before running.
- Command used: `NONINTERACTIVE=true bash get_vvm.sh` (skips the VS Code extension prompt). Took 4 min 18 s. `~/vega` is 5.4 GB afterward.
- The installer appended this block to `~/.zshrc` and `~/.zprofile`:
  ```
  #Vega CLI
  source "$HOME/vega/env"
  ```
- It also symlinks `kepler` and `vvman` to `vega` for older scripts (the sample's npm scripts still call `kepler`).
- Telemetry is on by default: https://developer.amazon.com/docs/vega/latest/telemetry.html explains how to opt out.

## The three ffmpegs

There is no single ffmpeg in this project, and that is worth saying plainly
before anyone reads two numbers as if one tool produced both.

| Where | Version | What runs on it |
|---|---|---|
| This Mac, on PATH | 9.0.1 (Homebrew) | Every baseline in `results/baselines/`, the labelling plots, the marker clips, the conformance generate-analyse-delete loop, both selftests |
| The ingest container | 5.1.9 (Debian bookworm, apt `7:5.1.9-0+deb12u1`) | The pipeline when it runs on Fargate. Pinned in `pipeline/infra/ingest/Dockerfile` |
| CI runners | whatever `apt-get install ffmpeg` gives ubuntu-latest that day | The CI jobs that need a decoder. Nothing published comes off a CI ffmpeg |

They are three different decoders and three different filter graphs. A number
measured on one is not a number measured on another, which is why every baseline
report carries its own `tool_version` string and why `eval/baseline_versions.py`
refuses a results directory that holds more than one.

### The 8.1.2 to 9.0.1 upgrade, and why there is no way back

Building EA IRIS on Sep 18, 2026 pulled in Homebrew's `opencv@4`, which upgraded
ffmpeg from 8.1.2 to 9.0.1 and relinked it. Nobody asked for that upgrade.

Rolling back is not available. The 8.1.2 binary is still on disk and no longer
starts, because x265 moved under it.

What it broke, and what fixed it: **ffmpeg 9 removed `-vsync`**. It exits with
"Unrecognized option 'vsync'" before it opens the file, so every labelling plot
came back as "no frames decoded". `eval/plots.py` and `eval/labeling/plots.py`
now pass `-fps_mode passthrough`, which means the same thing and has been in
ffmpeg since 5.0, so it works on all three of the above.

What it cost: the ffmpeg baseline rows in `results/baselines/` were measured on
8.1.2. They are being re-run on 9.0.1 as one set rather than piecemeal, because
a table with some rows from each version is a table nobody can read.

### Pinning, and what a pin here can and cannot do

The container is pinned exactly, by apt version, so a rebuild cannot quietly
pick up a different decoder. Debian bumps the `deb12uN` suffix for security
updates and drops the superseded version from the mirror, so that pin will one
day fail the build rather than drift. That is the intended failure: read the new
version, change the one `ARG` line, and note the change here.

The Mac cannot be pinned the same way. Homebrew has no supported downgrade path
for a formula another formula depends on, and this is a shared machine. What
stands in for a pin is the record: every baseline report stamps the build string
it ran under, and the one-version check fails if a directory ever holds two.

## Python setup for a fresh reviewer checkout

From the repository root with uv installed:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e "./flashmap[dev]"
```

This installs the analyzer and the dependencies used by the benign package
preflight. `eval/readme_sync.py --check` uses the standard library. The broader
infra suite additionally uses `pipeline/infra/requirements.txt`; do not confuse
that with a requirement to deploy AWS to run the simulator.
