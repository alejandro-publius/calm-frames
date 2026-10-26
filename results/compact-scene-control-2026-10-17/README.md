# Compact scene control, October 17, 2026

Completed: 125 tests across nine focused suites pass; TypeScript, changed-file lint and diff whitespace checks pass. Source `e4e7d8618cfeded9d21830111c0bc734e911484c` built and installed once on the Vega Virtual Device. See [receipt.json](receipt.json) and [native/summary.json](native/summary.json).

## What changed and why

The scheduled scene message and Skip now share a fixed 520 by 104 group in the lower-left safe corner (96 from the left, 54 from the bottom in 1080 units). A 152 by at least 88 Skip target keeps one six-unit focus outline. Its decorative inner outline is disabled locally. The scene label uses 36-unit text; optional status uses 32. The short, quiet group leaves the picture as the main content while keeping the action visible.

The label reads Scene ahead before actual cover, Scene hidden while covered. Paused and Loading appear only for those states. Practice uses Practice ahead or Practice cover. The group, action instance and focus route stay fixed through those changes. Full guidance remains available to accessibility speech. Checking, refusal and player errors retain their existing messages. Full-screen cover, guard boundaries, seek handling, signing, map eligibility and prepared media are unchanged.

The geometry test helper now handles fixed-width rows, rejecting flexible or overflowing rows. The caption test now includes both the native view and retained host bottom offsets; previously it measured the inner view's zero offset as if it were screen-relative. This does not move captions. The compact group spans y922 to 1026; the conservative caption band spans y600 to 840. These are rendered-tree measurements, not native visual proof.

## Verification scope

Nine suites: playbackCardSequence, playbackUi, seekbarFocusTransition, bufferingOpening, cards, useFlashGuard, tenFoot, playerWiring and uiLayout. Tests cover truthful labels, stable action geometry/focus, pause/loading behavior, no extra focus skin, caption clearance and existing guarded seeking. No capture test, screenshot, recording or computer-use action was used.

Earlier native playback recovery preceded this change. The original 48 kHz diagnostic passed twice on October 17 and the unchanged production app then passed pause/resume, Skip and Back. Resampling was not demonstrated to repair the earlier slowdown; its cause remains unknown. Those observations are preserved in the separate local calm-native-diag/evidence/followup report. This UI change is not a playback-performance fix.

Owner review still must establish actual native appearance, reading comfort, focus visibility and audio/VoiceView quality. The unknown teal linked orbs from the supplied image were not identified or modified. The three submission files reserved for Opus are untouched.

## Installed native result and owner steps

The aarch64 Debug package is `build/release/compact-scene-control-2026-10-17/calm-frames-compact-aarch64-debug.vpkg`, SHA-256 `0b4718ad798ffea6e7b92597aacefc02fb9db190705cb597be7b81b8ef1414ef`. The transferred device copy matched before launch and after checks. All 724 tracked app inputs remained unchanged through the build and checks. Prepared-library gates passed before and after building: four bundles and four verification reports, with the approved Acadia bundle unchanged.

Native text logs show Pause and resume while covered with Skip focus retained; cover release after the first interval; Skip focused during the second cover and cover requested before playhead write; seeked while covered, followed by cover release; Back and teardown, then Home Watch focused in 404 ms (teardown 363 ms). After resume and before Skip, media advanced 20.894 s in 20.899 s wall time. This one run did not reproduce the earlier sustained slowdown; it is not a claim that this UI change repaired it.

The same app process was used for a brief second playback to leave the review state visible. At 07:15:05.822 UTC it paused at media 8.016 s, covered, with Skip focused. The text collector is stopped and the app stays open. The retained device log is compressed text, not a recording. Native copy and geometry were not visually inspected; source tests plus package identity establish implementation, while logs establish the control route and media events.

Alex: review the already-open paused control for readable text, placement and a single clear outline. Press Play/Pause to resume and listen, or press Select on Skip to move past the scene; Back returns Home. No rebuild or setup is needed. Parents cancellation and practice were not repeated in this focused native pass. The three Opus submission files remain untouched. Nothing was pushed.
