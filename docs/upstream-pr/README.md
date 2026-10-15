# Shaka load-promise coverage proposal

Prepared October 15, 2026 from upstream `ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`
and the two patches in this directory. This is a test proposal, not an executed
test result. No app source or patch has been changed.

## The gap to close

The six focused tests last passed on October 10. They exercise
`VideoHandler`, while upstream `jest.setup.ts` replaces `ShakaPlayer` with
`jest.fn()`. The October 2 negative control documented in
[OPEN_SOURCE_PR.md](../OPEN_SOURCE_PR.md) reverted only the wrapper patch and
still passed all six tests. That is historical measured evidence, not a test
run performed for this review.
Upstream's Jest configuration also excludes the wrapper directory from coverage.
A passing coverage percentage therefore cannot establish this contract.

Both patches are needed on current upstream: catching `Promise.resolve(undefined)`
does not catch the promise that an unchanged wrapper drops internally.

## Smallest useful addition

Add one wrapper-focused test file, for example
`test/w3cmedia/ShakaPlayer.test.ts`, in a throwaway upstream checkout with both
patches applied. Keep the real wrapper and its real `internalLoad` method.

- Load the real class with `jest.requireActual` so the setup-file mock cannot
  turn the test into a test of a mock.
- Mock only the compiled Shaka engine and the six imported polyfill modules.
  Each polyfill needs a no-op `install`; importing the wrapper otherwise
  installs browser/native polyfills as a side effect.
- The engine stub must provide the members the real `load` uses:
  `polyfill.installAll`, `net.NetworkingEngine.unregisterScheme`,
  `registerScheme`, `PluginPriority.APPLICATION`, `net.HttpFetchPlugin`
  (`isSupported` and `parse`), `config.AutoShowText.ALWAYS`, and a
  `Player` constructor.
- That fake player needs `getNetworkingEngine`, `configure`, `load` and
  `setTextTrackVisibility`. Its networking engine needs the four
  clear/register request/response filter methods. Use a deferred promise for
  the fake player's `load`.
- Use a minimal content object with a manifest URI, codec fields and
  `drm_scheme: ''`; this avoids unrelated DRM configuration. Native parsing
  is already disabled by the wrapper's static flags.
- The compiled engine is generated and its directory is ignored by Jest.
  Resolve its import to a test-only stub, using a virtual Jest mock if the
  existing resolver accepts it. Verify that resolution before relying on the
  test; do not execute the generated engine or change production module paths
  merely to make the assertion pass.

Two paths are enough:

1. Rejection: the real `load(content, false)` returns a thenable. Attach its
   rejection assertion before rejecting the engine's deferred load. The returned
   promise rejects with the same error, the engine received `content.uri`,
   and `setTextTrackVisibility` was not called.
2. Fulfillment: while the engine's load is pending, text-track visibility has
   not been changed. Resolve it, await the wrapper's result, and assert that
   `setTextTrackVisibility(true)` ran. No network or device is involved.

Prove the first patch is covered by temporarily restoring only its old
`void` signature and dropped-return body in the throwaway checkout. The
wrapper contract test must fail because no promise is returned. Use the
fulfillment case for this negative control, or explicitly consume the rejected
internal promise, so the intentional mutation does not leave an unhandled
rejection behind. Restore the patch and see the test pass again.

## Strengthen the existing teardown test without expanding scope

The current test manually sets `mockPlayer.current = null`. Replace that
simulation with the real `destroyMediaPlayerSync()` call:

- Select HLS in the existing fixture so teardown takes the adaptive branch.
- Give the video mock its existing `pause` and `deinitializeSync` stubs.
- Stub `removeEventListeners` as the existing destruction test does. Make
  the Shaka mock's `unload` call the deferred load's rejection function and
  return normally; it must not throw synchronously. The rejection handler
  runs after the synchronous teardown has nulled the ref.
- Call teardown, then flush the promise queue. Assert that `unload` ran,
  the player ref is null and `setIsVideoError` was not called.

This checks the actual nulling order on which the guard relies. Keep the
existing async-error and synchronous-throw cases. Removing the caller catch
or only its teardown guard must still make the corresponding tests fail.

## Verification record to produce

Record the upstream SHA, Node/Jest versions, exact test commands and exit
codes. Run the focused files first, then lint, formatting and the broader
suite/typecheck against the same dependency installation before and after the
patch. Do not use `npm run build` for a read-only check: upstream's script
runs `lint:fix`. Report unchanged baseline failures separately.

Keep the October 10 six-pass result and October 14 clean-apply result dated.
Update the PR text only after new tests actually run. A completed test proposal
does not authorize a fork, push, issue, pull request or public release.
