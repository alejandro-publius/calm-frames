# Isolated native Retry test

Preparation only. Do not merge this branch into the product. Production source
51598761dc557f9bf95459f11ec3284ae604d333 and installed app are unchanged.
Base evidence: e9a0e22e25c734938f3b6c7a7eb884414db48786.

## Exact differences

The launcher title is Calm Frames Retry Test; the package/component IDs are
unchanged. PlayerScreen shows a TEST BUILD marker and one explicit Simulate
failure button. It becomes available only on the authenticated continuous McWay
edition after a usable checkpoint and current native playback at ten seconds.
Activation pauses the current decoder and feeds the existing error state. It
never destroys the decoder, fakes a release confirmation, changes the guard,
changes a seek, or invokes Retry automatically. Production Retry and native
release/recovery implementations are unchanged. The trigger is consumed once
per process, including when pause throws. No media or signed data changes.

This tests recovery from a synthetic UI failure with a real decoder retained.
It cannot establish how the SDK emits spontaneous decoder errors. Unit tests
use explicit native doubles and are not native acceptance.

## Native run, only after private PIN/reset work is complete

1. Confirm the user has finished private interaction and capture may resume.
   Preserve the installed production package and its checksum below. Build this
   branch with the existing pinned Node 22/Vega/JDK 21 workflow. Record source
   and package hashes. Do not change signing, media approval or device settings.
2. Installing this harness replaces the same app binary and uses its existing
   local data. It is not an app reset. Start McWay normally and wait at least ten
   seconds. Navigate to Simulate failure and activate it once.
3. Observe the error cover and audio pause. Press Try again once. While Closing
   player is shown, require a real native release confirmation before another
   decoder can start. If release never confirms, retain refusal and Back.
4. After confirmed release, press Try again explicitly. Observe the existing
   recovery picture barrier, native seek confirmation, fresh position sample,
   saved position and caption choice. Verify no stale callback uncovers or
   starts audio after Back/background cancellation. Restart the test process
   for a separate cancellation trial; no automatic repeated failures.
5. Collect only approved app-window/app-audio/app-specific evidence. Record
   observed facts and limitations, including remote reachability of the added
   test button. Restore the production package and confirm its identity.

Rollback package (in sibling calm-frames-combined-review):
`build/release/native-concise-copy-20261023/calm-frames-0.1.0-aarch64-debug.vpkg`
SHA256: `20dcdf34c16619c78d163f5bffba39f2b1adfab84dc6ad9116a01ac09b3d72ea`.

## Separate owner reset, not performed

The installed SDK offers no documented app clear-data command. Its supported
package-scoped command is:

```
vega device run-cmd --device VirtualDevice --command 'vpm uninstall io.github.alejandropublius.calmframes'
```

This is a proposed action only, pending the owner's specific reset confirmation.
After that confirmation, reinstall the rollback package with the existing
`vega device install-app --device VirtualDevice --packagePath <absolute-package-path> --buildType Debug`
flow. The official package manager reference documents package removal, but
not a guarantee that all app data is erased. Verify first-run setup afterward;
if the PIN persists, stop and report rather than deleting storage manually.
No other app or entire simulator reset is part of this operation.

If app-local data is cleared, it loses the local PIN, kid profiles, preferences,
personal extra covers and playback checkpoints. Packaged approved media, source
checkout and submitted project are unaffected. Never read the stored PIN or
remove the production protection gate.

Reference: https://developer.amazon.com/docs/vega/0.22/app-management-com-tools
