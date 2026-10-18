# Independent coastal-world review

Reviewed the working diff on `codex/coastal-world-2026-10-18`, including the follow-up theme and geometry fixes. No implementation changes, device commands, screenshots, recordings, builds or household changes were made by this reviewer.

## Final status

**No remaining blocker found in this scoped code review.** The final contrast fix is present at `app/src/calmframes/CoastalWorld.tsx:6`: `TEXT_DIM` now matches `TEXT #193F3E`. Home's runtime at `KidHomeScreen.tsx:309` therefore measures **4.8517:1** against the actual SVG water `#6FB4B1`, above the project's 4.5:1 floor (`calmStyles.ts:90–98`). The prior P2 finding is closed. This is a standard sRGB calculation, not a screenshot measurement.

The generic verified-poster fallback is also restored at `KidHomeScreen.tsx:280`: entries without built-in art use `shelfPoster(entry)` when available; built-in destinations retain their prepared stills. This observation does not certify the final test run.

## Findings resolved by inspected code

- `ProfilePicker.tsx:83,144–184` selects a coherent context-specific palette for title, chosen line, chips and their focused/selected states. The pale-on-pale world picker issue is resolved.
- `CalmButton.tsx:127,167,177` passes `WORLD.FOCUS_RING` to world primary controls. The terracotta ring against peach measures 3.4561:1, above the project's 3:1 non-text floor.
- `KidHomeScreen.tsx:224–225` applies the world to every nonempty, non-introduction shelf, including the demo-only fallback. Dark world text no longer appears on the dark fallback background.
- `TitleDetailsScreen.tsx:184,215` sets a 1080-unit minimum content height and adds 40 units of reading inset. `PlayerOpening.tsx:35` uses the same inset. `CoastalWorld.tsx:30` now places the 900-by-700 panel at x90/y200. Text begins at x136, with roughly 42 units inside the stroke. Opening's eyebrow at y220 and both title baselines fit the panel; the shared title starts at y274.

## Layout and remote route

At the fixed 1920-by-1080 design size, the two Home destination cards fit approximately x276..676 and x1244..1644, y356..666. The sea-otter title measures approximately 750 units in the packaged 80-unit Fraunces face and fits the 780-unit Details column. The right Details still does not overlap the left copy. These are source/metric checks, not native rendered observations.

Native direction checks must use Up from Watch to the destination cards and Down to the actions. The prior cinematic script used the opposite vertical order. Also exercise Home → Details → Watch → Back, Details → practice → Back, and Parents → cancel with the selected destination retained and focus returned to Parents. Focus IDs alone do not establish the spatial route.

## Protection and asynchronous state

- No diff found in the current ocean Acadia payload, `useFlashGuard`, `bakedAmbient` or `approvedBakedAmbient`.
- The removed pre-ocean Acadia catalog remains metadata only for authenticating existing household additions. It is absent from the active libraries/key route. Recommend the planned explicit old-playback-route rejection regression in addition to the exact consumer-list assertion.
- Parent-owned selection state addresses selection loss across Parents/cancel.
- VideoHandler's generation checks cancel setup when teardown wins the first setup microtask or asynchronous initialization.
- Surface-generation/handle checks and late BIF cleanup address stale setup and surface loss. The loading fallback is a static vector world, with the protective cover independently retained.

## Evidence limits

This reviewer did not rerun tests. Final regression tests were running during the closing review; earlier saved failed runs are superseded only by the parent's final recorded results. Parent must record the final successful test/type/lint results after the fixes. Native appearance, readable focus and surface recovery still require the single authorized native build/check pass; no such verification is claimed here.


## Late lifecycle and trace addendum — source 6f2570d

Read-only recheck of the committed source found no additional blocker.

- `PlayerScreen.tsx:689–698` ignores creation callbacks for the already-current identical surface handle. This makes duplicate notifications idempotent: they cannot increment the presentation generation, reset the decoded-frame baseline, or restart surface setup. A genuine destruction clears the stored handle, so recreation with that same handle still proceeds. The stale-destruction check remains intact.
- `playerOpening.test.tsx:19–20` repeats the current handle after the opening has cleared and asserts the opening stays absent. The adjacent surface-loss test still covers replacement handles, stale destruction, and a new frame before reopening the picture. This is meaningful regression coverage for the reported repeated-callback loop.
- `VideoPlayerUI.tsx:98,109` adds dependency-scoped paused/playing and controls shown/hidden traces only. `calmframes/trace.ts` suppresses them outside debug builds and when tests disable tracing. They do not alter playback, focus, controls timing or guards and contain no personal data. The paused/playing trace describes UI state, including the initial prop value; it does not by itself prove frame presentation, uninterrupted playback or audio output. Likewise, controls shown/hidden is state evidence, not a visual rendering measurement. Absence of a log proves nothing.
- Inspected saved logs: `bounded-tests.log` reports 426 tests in 32 suites passed; `safety-household-tests.log` reports 108 tests in six suites passed; `attribution-tests.log` reports 11 tests passed. The bounded log also records Jest's open-handle warning. The earlier `regression-tests.log` retains the failed OOM attempt; do not cite it as the passing result. This reviewer read these logs and did not rerun the tests.

The build was in progress during this addendum. No new build, installation, native visual/audio result or device action is certified by this review.
