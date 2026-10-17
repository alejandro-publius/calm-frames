# Compact scene control, October 17, 2026

Source checkpoint: 125 tests across nine focused suites pass; TypeScript, changed-file lint and diff whitespace checks pass. Native build and installation follow in a separate receipt.

## What changed and why

The scheduled scene message and Skip now share a fixed 520 by 104 group in the lower-left safe corner (96 from the left, 54 from the bottom in 1080 units). A 152 by at least 88 Skip target keeps one six-unit focus outline. Its decorative inner outline is disabled locally. The scene label uses 36-unit text; optional status uses 32. The short, quiet group leaves the picture as the main content while keeping the action visible.

The label reads Scene ahead before actual cover, Scene hidden while covered. Paused and Loading appear only for those states. Practice uses Practice ahead or Practice cover. The group, action instance and focus route stay fixed through those changes. Full guidance remains available to accessibility speech. Checking, refusal and player errors retain their existing messages. Full-screen cover, guard boundaries, seek handling, signing, map eligibility and prepared media are unchanged.

The geometry test helper now handles fixed-width rows, rejecting flexible or overflowing rows. The caption test now includes both the native view and retained host bottom offsets; previously it measured the inner view's zero offset as if it were screen-relative. This does not move captions. The compact group spans y922 to1026; the conservative caption band spans y600 to840. These are rendered-tree measurements, not native visual proof.

## Verification scope

Nine suites: playbackCardSequence, playbackUi, seekbarFocusTransition, bufferingOpening, cards, useFlashGuard, tenFoot, playerWiring and uiLayout. Tests cover truthful labels, stable action geometry/focus, pause/loading behavior, no extra focus skin, caption clearance and existing guarded seeking. No capture test, screenshot, recording or computer-use action was used.

Earlier native playback recovery preceded this change. The original 48 kHz diagnostic passed twice on October 17 and the unchanged production app then passed pause/resume, Skip and Back. Resampling was not demonstrated to repair the earlier slowdown; its cause remains unknown. Those observations are preserved in the separate local calm-native-diag/evidence/followup report. This UI change is not a playback-performance fix.

Owner review still must establish actual native appearance, reading comfort, focus visibility and audio/VoiceView quality. The unknown teal linked orbs from the supplied image were not identified or modified. The three submission files reserved for Opus are untouched.
