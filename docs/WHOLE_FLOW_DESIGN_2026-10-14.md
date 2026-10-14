# Whole-flow design candidate — 14 October 2026

Implemented in the isolated `codex/whole-flow-design-2026-10-14` worktree, from integrated baseline `cce5f22ccdc07fb5c9022d7ed9d0963b9df98a5b`, following the user's replacement of the previously accepted home design. Final runtime source: **`e49f712b7a0d74b3fbc41a4a0c90e232fa559bdc`**. The shared remote branch remains `4c9996d70dcc3327663679845f7c888648297d59` (rechecked before push).

The candidate uses shared stationary page chrome, control geometry and pressed feedback across home, details, optional help/demo, startup/loading/return, PIN/setup/settings, recovery and playback. Home has one dominant Harbor action. Demo and playback-check access remain in optional help. Selection marks remain distinct from focus. Loading is status, not a disabled pretend button. The player menu uses the same surfaces/type and closes when the active track is selected again. Original zen/Harbor artwork, the 20-second film, signed media/maps, guard timing and household storage code are unchanged.

## Home refinement

The final small pass replaces the existing benefit and explanation with “Watch with fewer flashes.” and “Supported titles use a still picture during marked scenes while sound continues.” The secondary action is “Details”. Parental controls is transparent text at rest with its existing 88-unit target, cream text, focus fill/ring and underline. Alignment and artwork are unchanged. The focus measurement helper now correctly reports a transparent resting border as 1:1 instead of trying to parse it as an opaque color.

[720p home](../results/whole-flow-2026-10-14/720/01-home.png) · [720p parent focus](../results/whole-flow-2026-10-14/720/01-home-parent-focused.png) · [1080p home](../results/whole-flow-2026-10-14/1080/01-home.png) · [1080p parent focus](../results/whole-flow-2026-10-14/1080/01-home-parent-focused.png).

The explanation occupies two lines at both resolutions. The parental label has no shadow; every sampled artwork pixel beneath the label passes 4.5:1 (minimum 6.74:1 at 1080p, 6.84:1 at 720p). Focused text is 7.83:1 and the focus ring against its fill is 4.61:1. [Layout measurements](../results/whole-flow-2026-10-14/checks/home-refinement-layout.json) and [pixel contrast measurements](../results/whole-flow-2026-10-14/checks/home-refinement-contrast.json) include the corresponding background samples. These are browser measurements, not native accessibility certification.

Only home, home parental focus and the optional help view sharing that link were recaptured for this pass. Their overviews/contact sheets were refreshed; the other prior captures remain unchanged. The reviewer retracted the missing-Back concern after reopening the checksum-matched 720p image. No opening navigation code or capture was changed for that concern.

## Review now

- [Whole-flow overview, 1080p](../results/whole-flow-2026-10-14/1080/overview.png) · [720p](../results/whole-flow-2026-10-14/720/overview.png)
- [Connected review index](../results/whole-flow-2026-10-14/index.html), with 47 states and 95 captures per resolution, including all scrollable sections and unavailable-title variants.
- [Hold + controls + two-line cue](../results/whole-flow-2026-10-14/1080/03-hold-controls.png) · [Hold + caption menu + two-line cue](../results/whole-flow-2026-10-14/1080/03-hold-caption-menu.png)
- [Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3)

These are actual React Native component host trees rendered in headless Chromium. Native video, native cue rendering and native seekbar use explicit substitutes. They establish browser composition, not moving native playback or native input. The capture checks assert separation of hold/menu/cue/control zones and safe bounds for the help action and setup/parent keypads at 1080p and 720p. Setup and PIN captures use ephemeral fixtures only.

## Validation

| Check | Result |
|---|---|
| Full app suite on `d7ba95c` | 122 suites; 1,256 tests; 57 snapshots passed; four existing skipped tests |
| Prior startup change | 39 focused startup, capture and full-flow tests passed |
| Final home refinement | 100 tests across six focused suites passed; home/details action, parental rest/focus/activation, room-scale checks and UI captures |
| Final TypeScript / ESLint | Pass; lint has zero errors, 97 existing source warnings and four existing test warnings (unchanged from the prior full log) |
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
# Same render command with --height 720 for the prior full-flow capture.
# Final targeted home update:
npm --prefix app test -- --runInBand --coverage=false --watchman=false --testPathPattern='(homeIntroduction|shelf|uiCapture|wholeFlowDesign|KidModeScreen|tenFoot).test'
/tmp/calm-home-preview-venv/bin/python eval/preview/render_home_refinement.py --browser /Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell
/Users/alexvintera/calm-frames/.venv/bin/python eval/preview/measure_home_contrast.py
PY=/Users/alexvintera/calm-frames/.venv/bin/python node app/tools/ui_flashmap.mjs
source /Users/alexvintera/vega/env
export PATH="$PWD/.logs/whole-flow-2026-10-14/build-bin:/Users/alexvintera/.local/share/fnm/node-versions/v22.23.2/installation/bin:$PATH"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
RELEASE_PYTHON=/Users/alexvintera/calm-frames/.venv/bin/python bash scripts/release.sh --arch aarch64 --build-type Debug --tag whole-flow-home-corrections-2026-10-14
```

The existing toolchain and generated Shaka outputs were reused; the local watchman shim avoids interference with shared workers. Full local logs are in `.logs/whole-flow-2026-10-14/` and `.logs/home-refinement-2026-10-14/`. The earlier package and first visual pass remain preserved separately. This receipt corrects the prior lint summary, which counted only the four test warnings and omitted 97 existing source warnings.

## Package and native blocker

Built successfully with committed app inputs; exact build identity is recorded below. Local package: `build/release/whole-flow-home-corrections-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg` (**21,581,924 bytes**).

SHA-256: `d43f7060ca5468239cbca3e55ac46093db50de71fba158a161f8ec90d6b06208`.

[Preparation record](../results/whole-flow-2026-10-14/checks/PREPARATION.json) and [build receipt](../results/whole-flow-2026-10-14/checks/release-build-receipt.json) bind the package to the exact source and app-input hashes. No installation, launch, publication or merge occurred.

**Pending:** install and observe this package in the existing Vega Virtual Device. Its VM process remains present, but the Mac is locked and native UI work was explicitly paused after automatic unlock failed. No retry was made. The user must manually unlock the Mac before native checks resume. Parental native checks require legitimate user PIN entry; the PIN was not retrieved, guessed or reset. Existing worktrees, active workers, recordings, packages and household data were left intact.
