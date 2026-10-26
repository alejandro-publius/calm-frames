# Targeted native receipt fixes

Baseline: `773334ab3ddedea925b40ba02ba3707a768cce2c`. Separate worktree and branch; frozen baseline and read-only rollback retained. The completed native receipt is the acceptance input. Claude #7 media work is independent.

## Causes and changes

- Pale openings: the installed stack consumes `animation`, not the removed `animationEnabled` flag. On Kepler the missing option selects the default animated card transition. Use typed `animation: none`; retain route fallback and signed opening gate. Native evidence is required to establish whether this fully removes the observed interval.
- Pause speech: the generic message depended on controls hiding and a polite live-region mutation. Issue one explicit delayed announcement for each observed playing-to-paused transition. Cancel on resume/unmount; no duplicate live region; no speech for initial/restored pause; scene cards keep ownership of their existing announcements. No Dolby change.
- Reading comfort: requested scroll offsets were cached as though native had applied them. Later native focus/scroll completion could overwrite the correction with no reconciliation. Keep only observed offsets and reconcile actual scroll events while the switch still owns focus. No refocus after the user moves away.
- Black pause picture: `useCoverHarness` treats pause as uncertainty and applies the opaque cover. `useFlashGuard` retains it; no signed still is authorized under uncertainty. This explains ordinary pause blackness without asserting a compositor defect. Keep that fail-closed behavior. A focused regression verifies clear-before, covered-pause, clear-after-confirmed-playing.

## Validation

Targeted tests failed on the baseline for navigation option, explicit pause speech and both viewport scroll races. Native observations and package identity will be appended after the targeted retest. Unobserved prior checks remain open; no full acceptance rerun.
