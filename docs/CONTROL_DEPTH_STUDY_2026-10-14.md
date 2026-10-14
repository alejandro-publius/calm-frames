# Control depth study — 14 October 2026

Review candidate, not approval or a rollout. Source **04e5638d92ecd3017eef99d299cbdb480de8f0bd**, isolated branch `codex/control-depth-study-2026-10-14`, based on `e49f712b7a0d74b3fbc41a4a0c90e232fa559bdc`. The `ControlSurfaceStudy` context is false by default and is enabled only in the capture fixture. Current production surfaces, package, layout and behavior remain unchanged.

## Inspect the implemented study

- [Review index](../results/control-depth-study-2026-10-14/index.html)
- [1080p control states](../results/control-depth-study-2026-10-14/1080/controls.png) · [720p](../results/control-depth-study-2026-10-14/720/controls.png)
- [1080p selected-row states](../results/control-depth-study-2026-10-14/1080/selected-rows.png) · [720p](../results/control-depth-study-2026-10-14/720/selected-rows.png)
- [1080p home pair](../results/control-depth-study-2026-10-14/1080/home-default-pair.png) · [720p](../results/control-depth-study-2026-10-14/720/home-default-pair.png)
- [1080p home](../results/control-depth-study-2026-10-14/1080/home-default.png) · [720p](../results/control-depth-study-2026-10-14/720/home-default.png)
- [1080p settings group](../results/control-depth-study-2026-10-14/1080/settings-group-closeup.png) · [720p](../results/control-depth-study-2026-10-14/720/settings-group-closeup.png)

Both resolution indexes also contain separate primary, secondary, tertiary and keypad close-ups and focused-home captures. The first keypad key is isolated from the actual rendered `PinKeypad`; selected rows are extracted from the actual `ParentAreaScreen`. No controls are redrawn in the renderer. Focus/press states are exercised with React Native Testing Library before host-tree export. This is browser composition evidence, not a live browser application, native input or native pixel evidence.

## Installed rendering support

Inspected installed packages and their bindings; [versions, file paths and SHA-256s](../results/control-depth-study-2026-10-14/checks/render-support.json):

| Mechanism | Evidence and use |
|---|---|
| Native gradient | `@amazon-devices/react-linear-gradient` **2.0.9000000001+2.6.2** documents Kepler support for colors, start/end, locations and angles. `index.kepler.tsx` registers `NativeLinearGradient`, processes alpha colors and forwards props. The study uses this existing native component for tonal shading. |
| Borders, clipping, alpha | `@amazon-devices/react-native-kepler` **4.0.1+rn0.83.0** explicitly accepts Kepler in `ViewNativeComponent.js`, registering rounded/per-edge borders, overflow, pointer events and offscreen-alpha-compositing capability. Its style attributes register opacity and color processing. The study uses clipped, rounded View layers and alpha colors. |
| Native shadows | Style attributes expose elevation, shadowColor/Offset/Opacity/Radius and boxShadow processing. That alone does not verify the installed device renderer's visual output. None is used: depth comes from two contained dark layers, a 2-unit contour, a fine top highlight and native gradient. No CSS blur/filter, external shadow or browser-only effect is added. |

The browser renderer translates those same host properties and gradient stops to HTML/CSS. Yoga layout, clipping, alpha blending and native paint still require a simulator observation; no native rendering parity is claimed.

## Treatment and checks

Primary is warm cream with deep teal text; secondary is translucent dark teal with a subtle contour. Compact quiet navigation and explicit tertiary controls remain text at rest. Focus uses the existing six-unit amber ring, a dark separator and underline. Selection retains its green edge and explicit checkmark independently of focus. Press reverses tonal shading and settles the surface edge without moving the text or target. Disabled surfaces flatten without fading the label.

All paint stays inside the existing target via an absolutely positioned, clipped layer. Target dimensions, padding and focus geometry are unchanged. Decorative layers ignore input and are hidden from accessibility. No animation is introduced, so reduced-motion behavior is unchanged. No signed-overlay, guard, media, storage or navigation code changes were made.

- **18 focused tests passed** across five suites, plus the 720p export test. Coverage includes unchanged default surfaces, activation, disabled actions/keypad focusability, fixed geometry, focus/press/release and existing home/parent routes.
- Typecheck passed. Focused lint: **zero errors and zero warnings**.
- Both resolution captures and bounds checks passed. Selected and focused states are separately visible in the settings group.
- Gradient-extreme contrast, including alpha over a worst-case white backdrop: primary **9.13:1**, pressed primary **7.45:1**, muted secondary text **4.56:1**, selected **4.91:1**, disabled **7.06:1**. Focus ring is **6.53:1** against its dark separator. [Measurements](../results/control-depth-study-2026-10-14/checks/contrast.json).

Commands (existing Node 22 and dependencies; no install or new toolchain):

```sh
npm --prefix app test -- --runInBand --coverage=false --watchman=false --testPathPattern='(controlSurface|homeIntroduction|wholeFlowDesign|controlStudy|parentNavigation).test'
CONTROL_STUDY_HEIGHT=720 npm --prefix app test -- --runInBand --coverage=false --watchman=false --testPathPattern=controlStudy.test
npm --prefix app run typecheck
app/node_modules/.bin/eslint app/src/calmframes/CalmControlSurface.tsx app/src/calmframes/CalmButton.tsx app/src/calmframes/CalmTouchable.tsx app/src/calmframes/PinKeypad.tsx app/test/calmframes/controlSurface.test.tsx app/test/calmframes/controlStudy.test.tsx
/tmp/calm-home-preview-venv/bin/python eval/preview/render_control_study.py --browser /Users/alexvintera/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell
```

[Check logs and source/host-tree provenance](../results/control-depth-study-2026-10-14/checks/). The previous Debug package remains byte-identical: `d43f7060ca5468239cbca3e55ac46093db50de71fba158a161f8ec90d6b06208`. No new native package or installed study is claimed.

**Pending:** parent visual review before broader activation, then one native simulator validation session after the user unlocks the Mac. Native UI remains explicitly paused; no unlock attempt, Terminal UI automation, stored PIN access or household change occurred. Settings captures use a fresh in-memory fixture only. [Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3).
