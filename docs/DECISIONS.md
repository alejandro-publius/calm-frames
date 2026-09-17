# Decisions

Each entry: date, decision, why, what it costs. Newest at the bottom.

## 2026-09-17: Build on the M1 MacBook
- **Decision:** Develop on this Mac (macOS 15.1.1, Apple M1, 16 GB). No Ubuntu SSD.
- **Why:** Vega SDK 0.24 supports macOS on Apple silicon, so HUMAN CHECKPOINT A passes and no kill rule applies. Apple silicon support continues after Dec 15, 2026, when Intel support ends.
- **Cost:** None. The install docs list KVM only as an Ubuntu requirement.

## 2026-09-17: Keep the name "Calm Frames"
- **Decision:** Keep the name.
- **Why:** No GitHub repository matches "calm frames" or "calmframes". Web and Devpost searches show no project or Appstore app with that name (only unrelated "Calm ..." meditation and fireplace apps). `flashmap`, `calm-frames` and `calmtiming` are free on PyPI, and `use-flash-guard` and `@calm-frames/flash-guard` are free on npm (checked Sep 17). GitHub has other repos named `flashmap` (Rust hashmap, ChromiumOS fmap), which is fine for a package name but worth a distinct PyPI description.
- **Cost:** None.

## 2026-09-17: Vega SDK 0.24.9914 through the official installer, run non-interactively
- **Decision:** Install Vega CLI 1.3.4 and SDK 0.24.9914 with `NONINTERACTIVE=true bash get_vvm.sh`, from a downloaded copy that was read first (SHA-256 in docs/ENVIRONMENT.md). Shell rc files were backed up first.
- **Why:** 0.24.9914 is the latest on the main channel (released Aug 10, 2026) and matches the build prompt's SDK 0.24 pin. Reading the script before running it matters because the documented method pipes curl into bash. Non-interactive mode skips the VS Code extension prompt.
- **Cost:** 5.4 GB in `~/vega`. The installer appended `source ~/vega/env` to `~/.zshrc` and `~/.zprofile`. Telemetry is on by default (opt-out documented).

## 2026-09-17: Node 22 LTS through fnm and `.nvmrc`
- **Decision:** Pin Node 22 (22.23.2 today) for the repo instead of the system Node 26.0.0.
- **Why:** The sample declares `engines.node >= 22` and was last released Aug 6, 2026. Node 22 is the oldest version it accepts, so it's the most likely to match what Amazon tested. Node 22 is in maintenance LTS through April 2027, past judging. CI can read the same `.nvmrc` through `actions/setup-node`.
- **Cost:** One more tool (fnm), and every shell has to run `fnm use`. If the Shaka build or Metro fails on 22, try Node 24 and log it here.

## 2026-09-17: Python 3.12 in a uv venv
- **Decision:** `.python-version` = 3.12, venv at `.venv` (Python 3.12.13).
- **Why:** The prompt needs Python 3.11 or newer, and the system `python3` is 3.9.13. 3.12 has the widest wheel coverage for the scientific and video packages we're likely to need. Revisit when the kits' `requires-python` values are known.
- **Cost:** Commands run as `.venv/bin/python -m ...` or `uv run`, not bare `python3`.

## 2026-09-17: App base is vega-video-sample at tag v0.24-RN83
- **Decision:** Copy `AmazonAppDev/vega-video-sample` at tag `v0.24-RN83` (commit `ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`) into `app/`, keeping its MIT-0 license and notices. Use a plain copy, not a submodule.
- **Why:** That tag is the React Native 0.83 release for SDK 0.24 (the repo also has `v0.24-RN72`). A plain copy keeps everything judges need in one repo. The repo has merged an outside contributor's pull request (#7, Jul 6, 2026), so the upstream pull request in Phase 7.3 can come from a separate GitHub fork.
- **Cost:** Upstream changes have to be pulled in by hand. The copy is not done yet (next step in Phase 1.2).

## 2026-09-17: Leave the shared colima VM alone
- **Decision:** Don't restart or resize colima (2 CPUs, 4 GiB) for the IRIS build. Build IRIS with limited parallelism instead.
- **Why:** Other projects on this Mac use the same Docker VM. Restarting it could interrupt their work.
- **Cost:** The IRIS image (vcpkg builds OpenCV from source) takes longer to build. If it runs out of memory, ask before resizing the VM.

## 2026-09-17: Either AWS credit form link works
- **Decision:** No change needed to the credit request step.
- **Why:** The Official Rules link `https://forms.gle/5hyhr1u6x3fuV2aW7` and the Resources page link `https://forms.gle/GaHFxSbBQNG9Kti6A` (the one in the build prompt) both resolve to the same Google Form, "AWS Credit Request Form | Amazon Developer Hackathon", which was open on Sep 17. The rules say entrants may request $150 in credits by Oct 21 at 12:00 PT, while supplies last.
- **Cost:** None.
