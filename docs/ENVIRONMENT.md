# Environment

Recorded Thu Sep 17, 2026. Update this file whenever a tool is added or a version changes.

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
| ffmpeg and ffprobe | 8.1.2 | Encoders include libx264, libx264rgb, libvpx, libvpx-vp9 |
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
  source "/Users/alexvintera/vega/env"
  ```
- It also symlinks `kepler` and `vvman` to `vega` for older scripts (the sample's npm scripts still call `kepler`).
- Telemetry is on by default: https://developer.amazon.com/docs/vega/latest/telemetry.html explains how to opt out.
