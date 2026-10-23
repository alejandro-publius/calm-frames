# Native asynchronous release handoff

Local source tests pass. Native acceptance is pending; do not call this release-ready.

The installed production source is e0f2ee747851f5a47fba8d0605c186e55873e414. e744d49 adds only test updates to await asynchronous confirmation. The production tree is identical. The exact package and installed hash match are recorded in receipt.json. Source and evidence remain local; nothing was pushed or merged.

Retry, Back and completion now use the SDK asynchronous teardown completion. A process-wide ownership barrier prevents a subsequent player from initializing while any release is pending or uncertain. The UI stays covered while closing, permits Back, and offers explicit Retry only after confirmation. Late callbacks after exit cannot restart playback. The prior synchronous timeout is not treated as success or simply increased.

A stable VideoHandler owner also replaces repeated construction with hook-memoized methods bound to the first instance. This makes generation cancellation and listener ownership refer to the same instance. Tests cover delayed completion, rejection, duplicate release, multiple native owners, refusal after timeout, explicit Retry, Back/background/unmount and stable ownership.

The final full app run passed 1,795 tests, four skipped, and 57 snapshots. TypeScript and scoped ESLint passed. A prior full run exposed six tests assuming synchronous cleanup; they were changed to await actual completion while retaining navigation, cover and teardown assertions. No checks were suppressed.

The Mac reconnected, but its screen locked before visual testing. One approved simulator-window screenshot timed out and wrote no frame. Native capture and UI interaction are paused until unlock; no lock/security settings were changed. The simulator was confirmed stopped and relaunched once in owned session 79214. Inspect it before any restart. Scoped logs were stopped; no recording is active.

Unlock is the immediate user action. Then verify the actual foreground app, collect a bounded app-only capture plus scoped timing/resource deltas, and compare fresh playback and recovered playback. Verify asynchronous Retry, explicit restart, Back and background cancellation. Do not assume the earlier slowness was caused by resource pressure: compressed memory/load snapshots are only context. Preserve the rollback and all prior captures. Profile/caption restoration and human audiovisual acceptance remain open. No PIN bypass, new media, signing changes or publication.
