# Whole-flow design candidate, 14 October 2026

Implemented in the isolated `codex/whole-flow-design-2026-10-14` worktree, from integrated baseline `cce5f22ccdc07fb5c9022d7ed9d0963b9df98a5b`, following the user's replacement of the previously accepted home design. Final runtime source: **`28904a0690d736a0b97eb80b04943c5d49f8117b`**. The shared remote branch remains `4c9996d70dcc3327663679845f7c888648297d59` (rechecked before push).

The candidate uses shared stationary page chrome, control geometry and pressed feedback across home, details, optional help/demo, startup/loading/return, PIN/setup/settings, recovery and playback. Home has one dominant Harbor action. Demo and playback-check access remain in optional help. Selection marks remain distinct from focus. Loading is status, not a disabled pretend button. The player menu uses the same surfaces/type and closes when the active track is selected again. Original zen/Harbor artwork, the 20-second film, signed media/maps, guard timing and household storage code are unchanged.

## Review now

- [Whole-flow overview, 1080p](../results/whole-flow-2026-10-14/1080/overview.png) · [720p](../results/whole-flow-2026-10-14/720/overview.png)
- [Connected review index](../results/whole-flow-2026-10-14/index.html), with 46 states and 94 captures per resolution, including all scrollable sections and unavailable-title variants.
- [Hold + controls + two-line cue](../results/whole-flow-2026-10-14/1080/03-hold-controls.png) · [Hold + caption menu + two-line cue](../results/whole-flow-2026-10-14/1080/03-hold-caption-menu.png)
- [Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3)

These are actual React Native component host trees rendered in headless Chromium. Native video, native cue rendering and native seekbar use explicit substitutes. They establish browser composition, not moving native playback or native input. The capture checks assert separation of hold/menu/cue/control zones and safe bounds for the help action and setup/parent keypads at 1080p and 720p. Setup and PIN captures use ephemeral fixtures only.

## Validation

| Check | Result |
|---|---|
| Full app suite on `d7ba95c` | 122 suites; 1,256 tests; 57 snapshots passed; four existing skipped tests |
| Final startup change | 39 focused startup, capture and full-flow tests passed |
| Final TypeScript / ESLint | Pass; lint has zero errors and four existing warnings |
| Browser exports | 12 fixture runs passed; both resolution capture assertions passed |
| UI transition model | 36 modeled screens/transitions passed WCAG and broadcast checks; not native pixel evidence |
| Prepared library/package | Exact catalog bytes and all three original reports passed |
| Scope/secret checks | No asset, timing-engine or household-storage diff; staged secret scan and whitespace checks passed |

Checks cover reachable help/demo/check routes, returned focus, disabled save actions, stationary readable pressed/focused controls, optional captions, active-track menu dismissal, pause/resume after six-second control hiding, Skip, and recoverable errors. Native D-pad/VoiceView are **untested on this candidate**. [Check summaries and package identity](../results/whole-flow-2026-10-14/checks/).

Commands used from the isolated worktree:

```sh
npm --prefix app test -- --runInBand --coverage=false --watchman=false
npm --prefix app run typecheck
npm --prefix app run lint
python3 eval/preview/export_flow.py
/tmp/calm-home-preview-venv/bin/python eval/preview/render_flow.py --browser /Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell --height 1080
# Same render command with --height 720.
PY=/Users/alexvintera/calm-frames/.venv/bin/python node app/tools/ui_flashmap.mjs
source /Users/alexvintera/vega/env
export PATH="$PWD/.logs/whole-flow-2026-10-14/build-bin:/Users/alexvintera/.local/share/fnm/node-versions/v22.23.2/installation/bin:$PATH"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
RELEASE_PYTHON=/Users/alexvintera/calm-frames/.venv/bin/python bash scripts/release.sh --arch aarch64 --build-type Debug --tag whole-flow-design-final-2026-10-14
```

The existing toolchain and generated Shaka outputs were reused; the local watchman shim avoids interference with shared workers. Full local logs are in `.logs/whole-flow-2026-10-14/`. The earlier package and first visual pass remain preserved separately.

## Package and native blocker

Built successfully at 13:47 UTC with committed app inputs. Local package: `build/release/whole-flow-design-final-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg` (**21,581,423 bytes**).

SHA-256: `0826bda9cc11b37a4794ba3782e99fd57d45f065d93491ec7c03c508ad0a2366`.

[Preparation record](../results/whole-flow-2026-10-14/checks/PREPARATION.json) and [build receipt](../results/whole-flow-2026-10-14/checks/release-build-receipt.json) bind the package to the exact source and app-input hashes. No installation, launch, publication or merge occurred.

**Pending:** install and observe this package in the existing Vega Virtual Device. Its VM process remains present, but the Mac is locked and native UI work was explicitly paused after automatic unlock failed. No retry was made. The user must manually unlock the Mac before native checks resume. Parental native checks require legitimate user PIN entry; the PIN was not retrieved, guessed or reset. Existing worktrees, active workers, recordings, packages and household data were left intact.
