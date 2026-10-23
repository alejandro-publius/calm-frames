# Playback integration prototype

This kit makes Calm Frames' coverage decisions reusable inside a player that the
integrator controls. It is source code with tested contracts, not a Prime Video
extension or an installed runtime overlay. The installed three-island demo remains
source `805f855`; its Acadia ocean replacement is baked into the approved rendition.
The four files in `app/src/calmframes/integration/` have no production imports.

## What each part does

| File | Responsibility |
| --- | --- |
| `verifiedCoverage.ts` | Accept an exact existing packaged edition, verify its signed maps with the current household settings, and issue an immutable in-memory token. |
| `coverageController.ts` | Turn that token and a current playback sample into cover, restore or unavailable, plus the next media-time boundary. No player or UI dependency. |
| `vegaCoverageAdapter.ts` | Observe a Vega player, invalidate uncertain timelines, wait for host acknowledgment before transport, reject stale operations and remove listeners/timers on detach. |
| `VegaIntegrationControls.ts` | Funnel remote and standard Alexa media commands through that adapter. Refuse unsupported speed, repeat and title-switch commands. |

The factory calls the existing `packagedLibrary.publicKeyFor/evidenceFor`,
`checkTitle`, `coverOptionsFor` and `buildCoverIntervals`. It does not reimplement
signature verification, register a new signer or accept a caller's arbitrary
catalog. It snapshots caller metadata and rechecks map freshness on each decision.
A new external publisher would need its own reviewed, exact catalog admission
boundary before this can support its editions. This example deliberately does not
provide an arbitrary-key shortcut.

The source hash binds the signed analysis. The rendition hash, URI, bundle edition,
preset, offset and duration bind playback. Package gates hash the files; the
runtime factory does **not** hash loaded video bytes. The loader must ensure the
loaded file is the verified asset. A URI alone cannot establish that for a mutable
network resource. Only the existing local package path is supported here.

## Host contract and order

1. Obtain an exact `CatalogTitle` from `packagedLibrary` and call
   `verifyPackagedCoverage(title, settings, Date.now())`. Null means unavailable.
2. Create `VegaIntegrationControls` with a getter that initially returns null.
   Await `player.setMediaControlFocus(componentInstance, controls)` **before**
   `player.initialize()`, as the Vega API requires. If registration rejects, stop
   setup and keep the cover; never fall back to the default handler.
3. After successful initialization, call `attachVegaCoverage(player, token, host)`
   and bind the adapter getter. Keep the cover visible while setting the asset URI
   and loading. Attach must precede playback. Initial player state must be paused,
   `loop=false`, `playbackRate=1`; loop/rate mismatches fail closed on evaluation.
4. Supply `host.identity()` from the active loader's immutable asset record,
   not by returning the token regardless of what the player loaded. The adapter
   additionally checks the player's URI and exact duration.
5. Supply `host.onDecision` to render an approved opaque cover for both `cover`
   and `unavailable`; restore only for `restore`. The renderer owns any approved
   still/ocean asset, caption layering and accessibility notice. This kit does not
   select a replacement image or alter audio/captions.
6. Supply `host.presentCover()` that resolves only when that opaque cover has
   actually been presented. A React state setter, `requestAnimationFrame` callback
   or resolved promise is **not** that acknowledgment. The current app has no
   demonstrated native compositor acknowledgment; until the host supplies one,
   this adapter is a prototype and must not protect an unprepared hazardous source.
7. Supply `host.seek(targetMs)` through the host's one guarded seek implementation.
   It must resolve only when its own movement operation settles. All UI, remote,
   standard Alexa and resume commands must use adapter methods. Do not call raw
   `play`, `fastSeek`, playhead writes or sample seek helpers elsewhere.
8. After loading/seeking/buffering recovery, capture the adapter generation and
   bind it to the host's **current** load/seek operation. Once the host confirms
   the actual settled media position and matching edition, call
   `synchronize(capturedGeneration)`. Never read a fresh generation inside an old
   asynchronous callback, and never treat `timeupdate`, `playing` or `seeked`
   alone as this proof. Synchronization refuses pending transport operations.
9. Forward lifecycle changes with `setForeground`; background pauses and covers,
   foreground stays covered pending a new confirmation. Call `discontinuity`
   before ads, period changes, clock remaps or loader changes. This prototype
   does not support those timelines: detach and refuse playback until an exact
   supported edition is verified.
10. On replacement/unmount, detach before changing the media source, clear the
    controls getter and remove the host's own lifecycle subscriptions. The host
    owns player deinitialization. Queued adapter commands cannot start after detach. Already-dispatched native
    operations cannot be canceled by removing listeners: use a new player for a
    new title, or await every outstanding host/native operation before reusing it.
    Transport calls are serialized; a second operation is refused while one is pending. Rejected cover/play/seek operations latch unavailable; create a new
    session after resolving the cause rather than clearing a boolean.

A paused sample inside an interval stays covered. Buffering, seeking, background
and unknown timeline states stay covered. Timers can request a cover ahead of a
boundary but cannot reveal the picture. A missing sample hides after 250 ms and
requires renewed synchronization. This is conservative prototype behavior, not a
measured device deadline. JavaScript timers can be late; frequent `timeupdate`
events do not guarantee frame accuracy. A host scheduler and presentation proof
are needed before an unprepared-source deployment. Timing validation on physical
hardware is a future deployment prerequisite, not an extra completion task for
this Vega Virtual Device submission.

## Audited command paths

The installed `@amazon-devices/react-native-w3cmedia` and
`@amazon-devices/kepler-media-controls` declarations compile with this adapter.
The existing app's `SafeMediaControlHandler` funnels explicit seeks, start-over,
skips, rewind and fast-forward through `requestSeek`. Its play/toggle and speed
callbacks delegate to SDK defaults. The SDK's repeat implementation writes
`loop`, despite its misleading no-op comment. Next/Previous reject without moving.
The new isolated handler overrides all those transport commands; it does not
inherit repeat/rate behavior.

The production app's `Seekbar` also resumes immediately after its seek callback,
and `VideoHandler` logs a media-control registration failure then continues.
Those paths are not the new kit's paths. The existing seek engine requests a React
cover before moving but does not await compositor presentation; its release logic
does not bind every sample to a seek generation. These are integration limits,
not evidence that the installed prepared clips displayed an uncovered frame.
The production path, approved media, signed trust and baked replacement registry
are unchanged by this kit. Native repeat/resume/voice behavior was not exercised
again for this isolated source addition.

## Platform boundaries

[Vega's W3C player](https://developer.amazon.com/docs/vega/0.24/media-player)
exposes a React Native controller/surface model with W3C media events.
[Media Controls](https://developer.amazon.com/docs/vega/0.24/media-player-media-control)
provides remote and standard Alexa command routing for a cooperating app. This
example targets that installed API, not Android Media3.

No public Prime Video player-extension API was found in the reviewed materials,
and Prime Video support has not been demonstrated. The documented
[Fire TV Integration SDK](https://developer.amazon.com/docs/fire-tv/get-started-with-firetv-integration-sdk.html)
and [Content Personalization](https://developer.amazon.com/docs/fire-tv/introduction-content-personalization.html)
concern catalog/entitlement integration, watch activity and recommendations. These
are not documented frame-interception hooks into another provider's player.

A real partner integration would need control of its own playback stack and a
signed analysis for each exact edit/edition. DRM secure surfaces may prevent the
required cover composition. Adaptive variants must retain a verified timeline;
ads, discontinuities and alternate edits need their own mapping and admission.
Captions must remain usable above the appropriate surface and cannot silently
be described as preserved without testing the actual renderer. None of these
requirements can be solved by runtime LLM decisions. A future Fire OS adapter
could use Kotlin/Media3 with the same decision contract; no port or C++ rewrite
is included here.

## Validation and tooling

Run from `app/`, using the existing Node 22 dependencies:

```sh
npx jest --watchman=false --runInBand --coverage=false test/calmframes/playbackIntegration.test.ts
npm run typecheck
npx eslint src/calmframes/integration test/calmframes/playbackIntegration.test.ts
```

Tests cover signed identity/staleness, boundaries, pause, seek in/out, acknowledgment
ordering, overlapping operations, detached title switches, buffering, background,
rejected operations, partial subscription failure and remote command refusal.
They use real signed packaged metadata and a controlled player. They are not
native rendered-frame or audio checks. See the [evidence record](../../results/playback-integration-2026-10-18/README.md).

[Amazon Devices Builder Tools setup](https://developer.amazon.com/docs/adbt/get-started)
was reviewed, alongside the official [hackathon resources](https://amazonappdev2026.devpost.com/resources).
No ADBT MCP tools are exposed in this session, no `adbt` executable was found, and
no builder-tools package was found in the checked npm/global install locations.
Nothing was installed or reconfigured. Existing native text logs were summarized
for player-entry-to-readiness and end-to-return latency; they do not measure cold
start, actual time to first displayed frame, CPU, memory or performance percentiles.
No device restart, new capture, profiling recording or native kit install occurred.
