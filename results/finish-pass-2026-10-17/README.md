# Finish-pass evidence

Installed source: `ed75fca6d52d5be52fedcd94e19a7eff387abd27`. The successful October 17 build was reused after 726 tracked app-input hashes matched. One package installation, no rebuild or reinstall on subsequent connection recovery. Package SHA-256: `d8a253c5e49bccd7a3995165c7d7be3a2205aad680345f3019ba1ac13937a54e`.

See [receipt.json](receipt.json), [native/summary.json](native/summary.json), [independent review](independent-review.md) and the root FINISH_PASS_HANDOFF.md.

Native logs verify Home/Details/More info Back focus; Help Back; Parents cancellation by hardware and on-screen Back; pause/resume while covered; cover-before-write and covered seek confirmation for Skip; natural end return; and manual Back. Native ended to Home Watch focus was 361 ms, including 335 ms to teardown completion. The former 2.3-second presentation wait is absent. Manual Back to Home Watch was 356 ms.

After resume and before Skip, media advanced 20.574 s in 20.577 s of device wall time. The slow status did not activate. This does not establish that the intermittent native slowdown is cured. Opening and seek waiting transitions were logged, but sustained loading/slow feedback and actual visual/audio/VoiceView quality remain outside this non-capture verification.

The app remains running at Home with Watch focused. Both old and final collectors were stopped after exact command identity checks. The first Help-driver failure was an incorrect expectation of an optional demo button; the corrected driver passed against the current catalog without changing app behavior. Disconnections interrupted earlier attempts; each completed final check was saved immediately. Host and guest wall clocks differ, so durations use the device clock consistently and device timestamps are not asserted as true UTC.

The compressed device log is text, not a screen/audio/video recording. No captures, publication, push, settings changes or reserved submission-file edits occurred.
