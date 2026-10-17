# Performance investigation, October 17, 2026

Source fixes are tested. Native speed and the reported stuck playback are not yet
validated. The installed app remains source `3f681a7`, package hash
`b682245fc8cdfcdcdd6dd289c58db72516ad0c4f431f558fd9fe721aaf98920e`.
No install, launch, navigation, capture or recording occurred in this investigation.
Base source: `deff7f2a20e56bf82126988b0daffbd9a8a1db41`, isolated app worktree
`/Users/alexvintera/calm-frames-claude-tv-2026-10-16`.

## What the evidence establishes

- Startup eagerly imported the legacy sample drawer and dispatched its playlist
  load, including a filesystem read and Redux updates persisted by the store.
  The drawer is now lazy and that work runs only when its route opens. Stable
  Suspense wrappers also prevent new route component identities on stack renders.
  No startup milliseconds have been measured on Vega.
- Home checks the signed maps; the player checks them again before playback.
  Exact-text/trusted-key authentication now uses a bounded, process-local cache
  (8 entries, each at most 64K characters). Only successful cryptographic checks
  are reused. Parsing, signature metadata/trust, file binding, expiry and map
  structure checks still run each call. Returned map objects are always fresh.
  Large maps are uncached; old entries are evicted; failed signatures are uncached.
- Back waited 700 ms even after successful synchronous media teardown. Success
  now returns immediately. The existing delay remains when teardown returns false
  or no success. Native teardown itself can take up to its existing 1500 ms limit.
- Debug beacons tried an unneeded HTTP collector during ordinary viewing. They
  are now explicit opt-in. These requests were not awaited, so they are not proven
  to have caused a loading wait. Bundled map/MP4 playback does not await a registry
  or BIF network request on the current route. The legacy measurement config's
  network lookup is confined to the legacy Home route, not Calm Frames startup.

## Host measurement, not native loading time

`before.json` and `after.json` record 11 successive batches, each verifying the
three exact compiled Acadia maps with Node 22.23.2 on this arm64 Mac. Batch one is
cold; the other 10 form the warm median (mean of the two middle sorted samples).

| Three-map batch | Before | After |
| --- | ---: | ---: |
| First, cold | 22.96 ms | 23.97 ms |
| Warm median | 13.62 ms | 0.91 ms |

This removes repeated JS work. It does not explain seconds of cold loading, prove
a simulator speedup, or prove that playback was stalled. The cold batch did not
improve. The initial live checkpoint used the upper middle sample (13.64/0.92 ms);
the files here use the conventional median. Reproduce from repository root with
`node results/performance-2026-10-17/benchmark.cjs app` using Node 22. The before
measurement used the unchanged base source; the after used the cache change.

## Screenshot and player state

The supplied Library screenshot `libfile_39104eca3d2c8191b14288aeff769175` was
inspected, without making a new capture. It shows the scheduled-cover card:
"Flashing hidden / Sound continues while this scene is hidden." The app's loading
component is plain stationary "Loading" text. Its cover and card contain no three
connected teal circles. The origin of those circles remains unverified; do not call
them an app spinner or infer that they demonstrate loading.

The screenshot does not identify the title or elapsed time. Acadia is the current
consumer title, but that is an inference about this image. For Acadia, Standard
and Broadcast covers are 7.843-12.199 s and 28.613-31.093 s; Extra cautious covers
are 7.343-12.699 s and 28.113-31.593 s. A cover can remain if media time stalls or
playback pauses inside an interval. Those conditions cannot be distinguished from
one still image. The captured *text log* is retained as `retained-native.log` and
contains media-session queries/renderer counters, not currentTime progression,
route durations or an initialization trace. Absence of these events proves nothing.

The opening still requires a valid guard, native surface and frame/advancing clock
before uncovering. Its 15-second stall recovery and 100 ms readiness poll are
unchanged. The Loading plate's 1000 ms reveal and 500 ms minimum visibility affect
status presentation, not media initialization. Cover-before-ready, guarded seeking,
interval boundaries, media, maps, keys and detector code are unchanged.

## Verification and remaining checkpoint

- 93 tests in 10 suites pass, plus 74 in 7 guard/UI/mirror suites: 167 total.
- One existing textual snapshot passes. No capture/export tests ran.
- Typecheck passes. Lint has zero errors and 101 existing warnings.
- Regressions cover cache tampering/trust/file/expiry/eviction/large input/result
  isolation, opt-in network beacons, immediate successful Back and fallback,
  startup data deferral, retained routes, guarded seek and opening behavior.

Minimum owner step: agree one short checkpoint before replacing the currently
running app. Build the committed source, install/launch once, and record elapsed
startup, Home-to-Details, Watch-to-first-picture and Back independently. Observe
playhead progress across the two Acadia covers and listen for continued audio.
If a cover remains, record whether time advances and whether the player is paused,
buffering or in error. No new screenshot or recording is necessary. Logs alone
cannot establish visible layout, audible continuity or human-perceived latency.
Do not tell the owner all slowness is fixed until this checkpoint is complete.
