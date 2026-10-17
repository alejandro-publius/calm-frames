# Finish pass, October 17, 2026

Source changes are complete on `claude/tv-experience-2026-10-16`, based on `7f0567f`. Native build/install follows; final source and package identity will be recorded here after that checkpoint.

| Before | After |
| --- | --- |
| Native playback could crawl while the UI reported no wait. | Read-only media-clock observation says Playback slow after sustained low progress; it does not guess a network cause or change protection. |
| Loading could remain beside a paused state; repeated MP4 clock events dismissed waiting. | Pause owns status immediately, and MP4 waiting clears on actual forward progress outside pause/seeking. |
| Loading had both explicit speech and a live region. | One explicit announcement per revealed episode, including later episodes with the same words. |
| Ended video waited 2.3 seconds, and any remote key could cancel returning. | End immediately invokes the same idempotent teardown as Back; the existing 700 ms fallback remains if native teardown does not confirm success. |
| Home and Help used prepared-video jargon; Details repeated its cover explanation. | Short shared plain-language copy keeps app-only scope, detection limits and credits. Approved imagery, typography, controls and compact scene layout remain. |

The new status compares actual media progress with the requested playback rate: six seconds below 50% enters slow, three seconds at 80% or better clears it. Pause, seek, rate changes, errors, ended state, clock reversals and long host scheduling gaps reset observation. This is presentation only. Guard schedules, trust/signing, media files and detector thresholds are unchanged. The unresolved simulator/SDK slowdown is not claimed repaired.

217 focused tests across 15 suites, one existing snapshot, TypeScript, changed-file lint and diff whitespace checks pass. Tests cover historical slow/normal traces, genuine loading versus pause/slow, observer cleanup, guarded Skip preservation, end teardown/fallback, copy, focus and layout. Independent review found one accessibility issue, fixed and regression-tested, with no remaining blocking findings. Evidence: `results/finish-pass-2026-10-17/`.

The simulator was found closed before native work. It will be started once using its existing configuration. No screenshots, recording, capture suites, pushes, publication, credentials/settings changes or detector work. The three Opus submission files are reserved and untouched. Owner visual/audio approval remains pending.
