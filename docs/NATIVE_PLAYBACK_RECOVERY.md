# Native playback recovery

Isolated feature branch: `codex/native-playback-recovery-2026-10-22`.
Critical-review fixes: `codex/native-recovery-reviewed-2026-10-22`.
Base: `13551e45bd853c392489dbecce7158a04036f615`.
The fetched release candidate `5771bdeae9c58c257b2e785f64f2fd06c08089ff`
has identical `app`, `hook`, `pipeline` and `flashmap` trees to this base.
The feature is not merged into that candidate or published.

## What changes for a viewer

Previously, leaving a prepared video lost its position; playback errors offered
Back only. Approved prepared titles now remember the actual reported position,
caption choice and paused intent per household profile and exact media edition.
Opening one again offers **Resume at m:ss** and **Start over**, using the existing
coastal Fire TV appearance. No decoder starts while this choice is displayed.

Resume reconstructs the player, verifies the current protection configuration,
and sends the saved position through the existing guarded seek function. It holds
an opaque recovery view until both native `seeked` and fresh `timeupdate` report
the settled target. A paused checkpoint stays paused. A missing confirmation
fails closed after 12 seconds; this timeout never authorizes uncovering.

Playback errors and sustained buffering offer explicit **Try again** only when a
usable checkpoint exists. Retry requires confirmed teardown before constructing
another player. Back, backgrounding and teardown cancel stale callbacks. There
is no automatic retry or background autoplay. Completion clears the checkpoint
and retains the existing stationary ending.

## Boundaries

- Recovery applies to accepted packaged prepared routes with a profile. Previews,
  static scenes and the measurement harness keep their existing behavior.
- Checkpoints never authorize playback or restore protection settings. Current
  route evidence and current household settings remain authoritative.
- Missing, corrupt, expired or edition-mismatched history takes the ordinary
  playback path. An optional read gets at most one second before that fallback.
- Local storage retains at most 24 records for 30 days. Position writes use
  reported media time, normally at two-second intervals and on pause/exit.
  Persistence is best effort; power loss or storage failure can lose progress.
  Slow writes coalesce the latest pending sample; teardown pauses cannot replace
  the viewer's saved playback intent.
- Caption tracks match language and label, never a previous native track ID.
  A missing track uses the existing title default.
- The hook mirror contains only the shared seek-source and transport gating
  changes. Detector, media, pipeline, signing and dependencies are unchanged.

## Verified in cloud

Targeted checkpoint, recovery state machine, real React player integration,
ordinary opening, seek safety and hook-mirror tests pass. Native media, SDK
widgets and guard verdicts in UI tests are explicit test doubles. App TypeScript
and scoped ESLint checks pass. These checks do not establish native playback,
pixel ordering, audio behavior or safety efficacy.

The critical review reproduced and fixed a late play resolution releasing an
invalidated seek, a slow write dropping paused intent, native detach exceptions
breaking Back, and audio continuing after a recovered surface was lost. Focused
regressions failed on those behaviors before the fixes. A synchronous memory
close also prevents teardown pause events from replacing coalesced exit samples.

## Required Mac / Vega acceptance

Use a separate feature checkout and package; keep the current release package
and original submission available. This feature changes app code and needs its
own native build. Do not relabel an older package or receipt as feature evidence.

1. Open an already approved prepared ambient title, select captions, play to a
   distinct position, pause/Back, then reopen. Verify remote focus, spoken labels,
   Resume position, caption restoration, paused intent and Start over. Repeat
   across profiles and app restart; corrupt/mismatched history must still open.
2. Verify native `seeked`, `timeupdate`, `seeking`, `readyState` and reported
   position during Resume, including a paused seek. `VideoHandler.ts` already
   notes unreliable MP4 seek events. If required events are absent, expect a
   covered error and Back; do not weaken the guard merely to make Resume pass.
3. Verify the opaque view is actually above the native video during recovery,
   seek, surface loss and cancellation. `onLayout` proves layout only, not
   compositor presentation. This remains an unresolved native acceptance gate.
4. With benign approved media, exercise an error/stall, explicit retry, repeated
   error, unconfirmed teardown, Back and background during recovery. Require
   one active decoder, no stale audio/playback, no automatic retry and a usable
   Back action. Foregrounding must not resume automatically.
5. Verify current protection settings and Playback Proof still apply after
   recovery; captions/audio continue as intended through existing covers, and
   normal completion retains the ending still and clears resume history.

No native result is claimed here. Do not promote the feature until these checks
support it. Preserve the Fire TV visual identity; the rejected browser redesign
is unrelated and must not be imported with this feature.
