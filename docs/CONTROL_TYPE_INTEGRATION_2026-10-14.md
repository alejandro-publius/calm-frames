# Calm Frames typography and controls — 14 October 2026

The isolated candidate uses Fraunces for display and section headings, Source Sans 3 for functional text and numerals, a warm cream primary action, and contoured teal secondary controls. Focus stays gold with an underline; selection retains its checkmark. Disabled saving rows retain their selected state with muted readable text. No scenery, film, guard timing or household storage changes.

## Before and after

- [Overview](../results/control-depth-integration-2026-10-14/comparison/calm-frames-before-after.png)
- [Home](../results/control-depth-integration-2026-10-14/comparison/home-before-after.png)
- [Details](../results/control-depth-integration-2026-10-14/comparison/details-before-after.png)
- [Settings](../results/control-depth-integration-2026-10-14/comparison/settings-before-after.png)
- [Full-size comparison index](../results/control-depth-integration-2026-10-14/comparison/index.html)

Matched 1920 × 1080 viewport, state, scenery and content. These are **static React Native component host trees rendered in Chromium**, not native screenshots. Font metrics naturally change wrapping. Before source: `e49f712b7a0d74b3fbc41a4a0c90e232fa559bdc`, with saved evidence from `b3bc111bbcded8f9512028c1b2a2c2d9aba35bab`. After source: `867d4493159b172bcbacce56a1fc7b863439d8f1`. [Comparison manifest](../results/control-depth-integration-2026-10-14/comparison/comparison-manifest.json) records input hashes. Four comparison images were successfully uploaded to ChatGPT Library; IDs are in [Library references](../results/control-depth-integration-2026-10-14/checks/library-attachments.json).

## Sources and scope

[Fraunces](https://github.com/undercasetype/Fraunces) and [Source Sans 3](https://github.com/adobe-fonts/source-sans) came from their official OFL repositories. Static fonts have unique internal family names matching filenames; licenses, upstream commit IDs, hashes and Fraunces axes are in [font provenance](../app/assets/fonts/FONT_PROVENANCE.json). Functional digits have equal widths without requiring a native font-feature switch. Native caption preferences are unchanged.

Mobbin's [public homepage](https://mobbin.com/) was readable. Its [discovery page](https://mobbin.com/discover) exposed login/join prompts but no inspectable app flow in this tool session. No authenticated reference screen was examined, and **no pattern is attributed to Mobbin**. The delivered comparison does not depend on inventing a reference or copying an asset.

## Validation and package

- Eight focused suites / 80 tests passed. Final control-surface regression rerun: 5 tests passed.
- Typecheck passed; targeted ESLint passed with no warnings.
- Twelve fixture exports passed. At each of 1080p and 720p, 47 states produced 94 captures; hold/menu/multiline-cue separation and keypad/help safe bounds passed the renderer assertions.
- Visually reviewed the matched overview, 720p hold + caption menu + multiline cue, and selected/focused/pressed/disabled settings rows. Browser layout only; native captions, video and seekbar remain explicit substitutes.
- aarch64 Debug build completed at `2026-10-14T17:28:18Z`. Exact catalog and all three original verification reports passed. All three new TTFs and both licenses are present at `assets/fonts` in the package.

Package: `build/release/controls-type-integrated-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg` (21,880,526 bytes).

SHA-256: `ced6cecd2fb9c5d1294bb316a412559c048bec0ee04143ad3cf42cc5f76ad257`.

[Preparation](../results/control-depth-integration-2026-10-14/checks/PREPARATION.json) and [build receipt](../results/control-depth-integration-2026-10-14/checks/release-build-receipt.json) bind the package to source `867d449`. An initial build failed because this fresh worktree lacked the ignored generated polyfills; the existing polyfills from the previous successful worktree were copied unchanged and the build then passed. No source media change was needed.

Commands used:

```sh
npm --prefix app test -- --runInBand --coverage=false --watchman=false '(controlSurface|controlStudy|homeIntroduction|wholeFlowDesign|parentNavigation|playbackUi|KidModeScreen|tenFoot).test'
npm --prefix app test -- --runInBand --coverage=false --watchman=false controlSurface.test
npm --prefix app run typecheck
npm exec --prefix app -- eslint app/src/App.tsx app/src/calmframes/CalmButton.tsx app/src/calmframes/CalmControlSurface.tsx app/src/calmframes/CalmTouchable.tsx app/src/calmframes/ParentAreaScreen.tsx app/src/calmframes/PinKeypad.tsx app/src/calmframes/calmStyles.ts
python3 eval/preview/export_flow.py
/tmp/calm-home-preview-venv/bin/python eval/preview/render_flow.py --browser /Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell --height 1080 --output results/control-depth-integration-2026-10-14
# Same command with --height 720; control study rendered separately.
/tmp/calm-home-preview-venv/bin/python eval/preview/compose_type_comparison.py
source /Users/alexvintera/vega/env
export PATH="$PWD/.logs/integration/build-bin:/Users/alexvintera/.local/share/fnm/node-versions/v22.23.2/installation/bin:$PATH"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
RELEASE_PYTHON=/Users/alexvintera/calm-frames/.venv/bin/python bash scripts/release.sh --arch aarch64 --build-type Debug --tag controls-type-integrated-2026-10-14
```

## Pending native access and coordination

The existing Vega simulator process was present and `vega device is-connected --device Simulator` reported connected. Computer Use could not select the Vega process as an app; a Finder selection then returned **“Computer Use permissions are not granted.”** No screenshot or unlock confirmation followed. Native installation and visual/input validation are pending, not passed: actual motion, glyph rendering, D-pad, VoiceView, focus/Back, and simultaneous hold/caption controls need one consolidated session after the user grants the Mac's Computer Use access and unlocks it if needed. Legitimate household unlock must be entered by the user; no PIN was retrieved or reset.

Desktop Commander can read this workspace but reported **“No active sessions.”** Its `interact_with_process` capability accepts a PID returned by its own `start_process`; it does not document attaching to the already-running Claude terminal. No prompt was sent, no new paid process was started, and no alternate route around the earlier Terminal restriction was attempted.

Branch: `codex/control-depth-integration-2026-10-14`. [Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3). Existing packages, workers, recordings, household data and shared PR branch were preserved. No install, launch, publication, deployment or merge was performed.
