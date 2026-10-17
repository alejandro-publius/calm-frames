# Finish pass, October 17, 2026

Completed on `claude/tv-experience-2026-10-16`. Installed app source: `ed75fca6d52d5be52fedcd94e19a7eff387abd27`, based on compact-control evidence `7f0567f`. Native evidence commit: `1b13895918c97c1cae386e3ce70af9d9b92f1d1b`.

Package: `build/release/finish-pass-2026-10-17/calm-frames-finish-aarch64-debug.vpkg`.
SHA-256: `d8a253c5e49bccd7a3995165c7d7be3a2205aad680345f3019ba1ac13937a54e`.
The successful build was reused after all 726 tracked app-input hashes matched. One installation was verified against the device copy; no rebuild or reinstall during reconnections. The app is running at Home with Watch focused. Text-log collectors are stopped.

| Before | After |
| --- | --- |
| Native playback could crawl while the UI reported no wait. | Read-only media-clock observation says Playback slow after sustained low progress; it does not guess a network cause or change protection. |
| Loading could remain beside a paused state; repeated MP4 clock events dismissed waiting. | Pause owns status immediately, and MP4 waiting clears on actual forward progress outside pause/seeking. |
| Loading had both explicit speech and a live region. | One explicit announcement per revealed episode, including later episodes with the same words. |
| Ended video waited 2.3 seconds, and any remote key could cancel returning. | End immediately invokes the same idempotent teardown as Back; the existing 700 ms fallback remains if native teardown does not confirm success. |
| Home and Help used prepared-video jargon; Details repeated its cover explanation. | Short shared plain-language copy keeps app-only scope, detection limits and credits. Approved imagery, typography, controls and compact scene layout remain. |

The new status compares actual media progress with the requested playback rate: six seconds below 50% enters slow, three seconds at 80% or better clears it. Pause, seek, rate changes, errors, ended state, clock reversals and long host scheduling gaps reset observation. This is presentation only. Guard schedules, trust/signing, media files and detector thresholds are unchanged. The unresolved simulator/SDK slowdown is not claimed repaired.

217 focused tests across 15 suites, one existing snapshot, TypeScript, changed-file lint and diff whitespace checks pass. Tests cover historical slow/normal traces, genuine loading versus pause/slow, observer cleanup, guarded Skip preservation, end teardown/fallback, copy, focus and layout. Independent review found one accessibility issue, fixed and regression-tested, with no remaining blocking findings. Evidence: `results/finish-pass-2026-10-17/`.

## Verified native outcome

- Home to Details and More info, then Back to each opener: passed.
- Help and Back: passed. The first driver expected an optional demo button; the current catalog correctly focuses Back. The driver was corrected without app changes.
- Parents cancellation using hardware Back and the on-screen Back: passed, restoring Parents focus without PIN entry.
- Pause/resume during the first cover: passed, retaining Skip focus and protection.
- Skip during the second cover: passed; cover requested before playhead write, seek confirmed while covered, then cover released outside the interval.
- Natural end: native ended to Home Watch focus in 361 ms, including 335 ms to completed teardown. The old 2.3-second presentation wait is gone.
- Manual Back: Home Watch focus in 356 ms.

After resume and before Skip, media advanced 20.574 s in 20.577 s of device wall time. No slow-status activation occurred. Opening and seek waiting transitions were logged. This does not prove the intermittent slowdown is cured or establish the appearance of a sustained slow/loading state.

Connection interruptions delayed verification. On the final continuation the simulator was already running but the app was not; the existing production component was launched once. Old collector PID 91713 and final collector PID 98424 were stopped only after identity verification. No cause of the app's earlier stop is inferred. Host and guest clocks differ, so all durations compare timestamps within the same device clock.

## Remaining owner step and limits

Review the already-open Home, then Watch, for actual visual comfort, focus appearance and sound. Native pixels, audio quality and VoiceView speech were not captured or judged. Slow/loading state behavior is covered by the focused tests and historical trace replay; a sustained native instance was not forced. The earlier simulator/SDK slowdown's cause remains unresolved. There is no remaining implementation or connection blocker for this bounded pass.

No screenshots, screen/audio/video recording, capture/export suites, push, publication, credentials/system changes or detector work. The three reserved Opus submission files and concurrent work are untouched. Full receipts and compressed text logs: [results/finish-pass-2026-10-17](results/finish-pass-2026-10-17/README.md).
