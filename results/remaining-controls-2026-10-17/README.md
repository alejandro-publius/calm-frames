# Remaining native controls, October 17

All four requested controls were exercised on the existing installed c2b56d2 app. The owner had closed the simulator; it was reopened, then the app launched once. No rebuild, installation, capture, recording or push occurred. Claude was not operated.

| Check | Result |
| --- | --- |
| Parents -> cancel | Pass by focus logs for both remote Back and the Cancel button; no PIN entered |
| Pause/resume during cover | Native pause and playing events both retain covered=true, then the cover clears. Smooth playback is not a pass: the media clock slows severely afterward |
| Activate Skip | Enter on Skip calls the guarded engine; cover requested before the 12.799 s playhead write; seeked and confirmed-outside release observed. Seeking took about 7.26 s |
| Manual Back during playback | Returns Home Watch in both runs. First uses teardown fallback, 2.257 s to Home. Second succeeds synchronously, 0.884 s to Home |

Skip was triggered after the first cover-on event in the fresh run, but a subsequent media resync had cleared that schedule cover before the Enter event. The guard re-covered before writing. This proves Skip activation and guarded seek ordering, not continuous coverage from the original schedule event or physical pixel ordering.

## Actual unresolved problem

Run 1 advances 17.426 seconds of media in 122.089 seconds of wall time, including a deliberate 3.382-second pause. The fresh run without Pause also slows before Skip (one sample advances 21 ms in 1003 ms). Pause is therefore not established as the cause. Native logs repeatedly report zero audio-position advance and video-queue buffering. The JavaScript layer reports playbackRate=1 and no new waiting event in the first run. These samples establish a slowdown, rather than inferring one from missing logs.

No minimal app-source correction is justified yet: the native playback/audio pipeline is the investigation boundary, and changing protected cover timing or inventing a seek/audio recovery would mask the problem. No app code or guards were changed. The supported controls return to Home, but the playback journey must not be called stable. Next work should isolate the native low-progress/audio-sink behavior and truthful waiting state, using this receipt rather than repeating all navigation checks.

The app was left running at Home with Watch focused. The end-of-video 2.3-second delay was left unchanged; these Back tests happen before ended and do not exercise that delay. Visual focus, message appearance and audible sound remain unobserved.

Evidence: [receipt](receipt.json), [remote dispatches](actions.jsonl), [focus and guard traces](selected-events.log), [unique timing events](timing-events.json), [native warning excerpts](native-media-warning-excerpts.log). Original driver timeouts are retained alongside the successful follow-up observations.
