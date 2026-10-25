# Player pause announcement

Original item 11, checked source `6570662e4cbda2379ef537acb3cd75ac8847ab63`,
based on Claude's verified handoff `15ef46c6e23c8ba627492da23b1b147000031aa4`.

Claude's [native acceptance notes](../design-polish-2026-10-23/claude-integration/README.md#acceptance-pass-on-the-candidate)
record VoiceView repeating "Paused. Press Play to continue." each time the
controls hide. The source explains that behavior: the paused notice is mounted
only with controls hidden, and every mount creates a polite live region.

The [player UI](../../app/src/w3cmedia/mediacontrols/VideoPlayerUI.tsx) now sends
that announcement when the paused state begins. Showing or hiding controls
does not repeat it. Play followed by another Pause announces the new pause.
The visible notice stays accessible for manual reading; its live-region speech
is disabled. Cover and countdown cards retain their own pause guidance.

The [evidence receipt](../../results/overnight-2026-10-25/app-ux/receipt.json)
records a clean locked install with Node 22.23.2 and npm 10.9.8, normal
typecheck and lint, and
<!--n results/overnight-2026-10-25/app-ux/receipt.json:tests.passed -->52<!--/n-->
passing focused tests. Lint retains existing warnings; changed files add none.
The regressions use the actual player UI with simulated native media and SDK
widgets. They verify repeated control visibility changes, a later second pause,
scene-card ownership, retained visual status, captions and recovery overlays.
Seek position, paused state and cover ownership remain unchanged.

The new regression fails against the original source. Two deliberate breakages
also fail: restoring the banner's polite live region, and suppressing the second
pause as a duplicate announcement. The checked source was restored after each.
No hook mirror changed because the player UI is outside the mirrored engine.

This completes the machine-executable correction for that recorded issue.
Native VoiceView listening on the resulting combined build remains pending.
It does not close item 11's SDK seekbar, intermittent resume-prompt entry or
reduced-motion observation gaps. No native build, hosted check, human comfort
acceptance or media generation is claimed.

The source review also inspected the startup/loading shell, household failure
UI and current copy/focus paths for items 1 to 4. The reported pale opening frame
still has no established source cause. Existing loading, focus and protection
behavior was retained instead of changing its timing speculatively. Item 5's
completed name editor and item 6's navigation fixes remain intact; the owner's
disclaimer-layout decision is still separate.
