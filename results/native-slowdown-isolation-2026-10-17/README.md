# Native slowdown isolation, October 17

The old control-check evidence is finalized in local commit b32c007. This pass reused the installed reviewed c2b56d2 package; all 764 source inputs still match. No application changes, rebuilds, installations, settings changes, captures, recordings or pushes occurred.

| Focused comparison | Result |
| --- | --- |
| New app process, same simulator | 6.010 s media progress in 15.560 s wall, without Pause; Back returns Home |
| Clean simulator restart, unchanged app | Initial 5.096 s media in 5.015 s wall, then slowdown before Pause. Across retained samples: 5.886 s media in 26.435 s wall, including the later deliberate pause |

The old simulator stderr contained five kAudioHardwareBadDeviceError entries and could-not-resume messages. Host inventory showed a valid default MacBook Pro Speakers output at 44100 Hz. One clean simulator restart removed those errors, but did not restore sustained playback. This was a failed repair attempt, not a validated fix. The startup video-sink Invalid configuration errors also appear in the earlier healthy checkpoint, so they cannot by themselves identify the cause.

The fresh-process and fresh-simulator comparisons narrow the cause: residual players from the previous app process and old retained CoreAudio errors are not sufficient explanations. Native audio-position nonadvancement and video-queue buffering still accompany very low media progress. The exact trigger remains unresolved. Guard-clock resynchronization can retract an estimated cover state when the actual media is still earlier than the interval; no physical-frame conclusion is drawn from these logs.

No safe, minimal app-source repair is established yet. Changing protected timing, forcing audio settings, or inserting automatic seeks would hide symptoms without proving recovery. The remaining investigation boundary is the active native media/audio/backend path, ideally compared with an isolated supported SDK playback sample before changing this app's lifecycle. The waiting UI also cannot be considered proof of healthy playback: native waiting events may be absent while progress is very low.

The app is left running at Home with Watch focused. Our collectors were stopped. Visual appearance and audible playback remain unverified.

Evidence: [receipt](receipt.json), [fresh app timing](fresh-app-timing.json), [fresh simulator timing](fresh-simulator-timing.json), [pre-reset CoreAudio errors](coreaudio-before-restart.log), [post-reset stderr](simulator-stderr-after-restart.log). Full filtered text-log paths and hashes are in the receipt.
