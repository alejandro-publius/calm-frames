# Targeted native receipt fixes

Baseline: `773334ab3ddedea925b40ba02ba3707a768cce2c`. Separate worktree and branch; frozen baseline and read-only rollback retained. The completed native receipt is the acceptance input. Claude #7 media work is independent.

## Causes and changes

- Pale openings: the installed stack consumes `animation`, not the removed `animationEnabled` flag. On Kepler the missing option selects the default animated card transition. Use typed `animation: none`; retain route fallback and signed opening gate. Native evidence is required to establish whether this fully removes the observed interval.
- Pause speech: the generic message depended on controls hiding and a polite live-region mutation. Issue one explicit announcement after native controls hide and settle for each observed playing-to-paused transition; remember delivery so showing/hiding controls does not repeat it. Cancel on resume/unmount; no duplicate live region; no speech for initial/restored pause; scene cards keep ownership of their existing announcements. No Dolby change.
- Reading comfort: requested scroll offsets were cached as though native had applied them. Later native focus/scroll completion could overwrite the correction with no reconciliation. Keep only observed offsets and reconcile actual scroll events while the switch still owns focus. No refocus after the user moves away.
- Black pause picture: `useCoverHarness` treats pause as uncertainty and applies the opaque cover. `useFlashGuard` retains it; no signed still is authorized under uncertainty. This explains ordinary pause blackness without asserting a compositor defect. Keep that fail-closed behavior. A focused regression verifies clear-before, covered-pause, clear-after-confirmed-playing.

## Validation

Targeted tests failed on the baseline for navigation option, explicit pause speech and both viewport scroll races. The first repair passed 71 tests across eight focused suites and typecheck. The revised speech scheduling passed all 14 playback UI tests and typecheck. Both normal Debug and Release builds passed their pre/post gates.

Native 1080p Debug retest FAILED initial Reading comfort Off to On: the lower border remains clipped after settling. Movement away passes without focus theft. Observed-offset reconciliation is insufficient; mocked scroll-race tests do not establish a native fix. No further speculative patch is included.

Opening recordings on Debug bcdfda0 at 720p (Forest, Otters, McWay) and Debug 01504e8 at 1080p (McWay) show continuous meaningful opening art and no near-white interval. The earlier bcdfda0 speech change missed the second pause announcement; that prompted the bounded 01504e8 revision.

Unobserved prior checks remain open; no full acceptance rerun. Full numbered checklist closures are not inferred from these subchecks.

Final product source: `01504e8c29547ba6d2be878cd009b9c2f1f74b2d`. Release 1080p McWay opening also passes the observed pale-frame retest. Release installed SHA384 matched the built package.

The revised pause fix FAILED the final Release native retest: two actual pauses were visible, but offline audio transcription contains the first instruction and no second instruction. Progress speech continued. The remaining native delivery cause is unresolved; this is not a reliable speech fix. Human listening acceptance remains open.

Result: observed pale-opening defect closed within recorded cases; Reading comfort clipping and intermittent pause speech remain open. Black pause cover retained by design. No new complete numbered checklist item; ledger stays 7 complete, 11 partial, 2 blocked. Final revision 720p speech and comfort cases remain unobserved. Disposable viewport restored to 720p and VoiceView disabled; main device, baseline and rollback untouched.

Sanitized local receipt: `native-fixes-773334a/receipt.json` in the enclosing Mac task, with exact package hashes and recording provenance. These changes are local and not ready for promotion as a complete repair.

## Reading comfort only continuation

The previous fix reconciled scroll events but kept a mismatched coordinate system: the ScrollView's onLayout height included safe-area padding while the reading group's position was relative to its content. The native receipt shows the enlarged control retained focus but extended below the window. The old tests supplied an unpadded viewport and missed this distinction.

Move the existing safe-area style onto a static enclosing View and give the ScrollView flex: 1. Its onLayout now measures the actual inset viewport used by the row-bound reveal calculation. Preserve all focus/save handlers and existing safety, navigation, speech and media behavior. No delay or polling added. Focused regressions cover first/repeated enlargements against inset viewport bounds at both sizes. Native retest pending.

Reading comfort result on product commit `3512344c1d28b6385c650bb4847f8cff8832e11b`: PASS in isolated Debug at 720p and 1080p. First Off to On, On to Off, repeated toggles, whole switch visibility and retained focus observed. 26 focused tests and typecheck pass; one Debug rebuild with normal gates and installed hash match. No Release or VoiceView-enabled retest in this scope. Clipping subcriterion closed; human comfort and unrelated open checks remain open. Evidence and package hashes: enclosing task `native-comfort-fix/receipt.json`. Test preference returned Off; disposable restored to 720p with VoiceView off.
