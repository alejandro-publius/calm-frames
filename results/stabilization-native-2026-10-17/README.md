# Stabilization native checkpoint, October 17

The owner authorized one install and test. The reviewed source `c2b56d258979b9d7e968944c0780dc7fb1721f9f` built successfully and this worker installed it once. All 764 app inputs match the build receipt, and the strict prepared-media gate passes with all four verification reports and the unchanged approved Acadia bundle. The prior saved source run passed 144 suites, 1,424 tests and 57 snapshots (one suite and four tests skipped); it was not rerun here.

Package: `build/release/stabilization-native-2026-10-17/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `62f4307ce172edaa71510b478e41e6129938e27ca92b4e7416213e55e0d001cf`.

## Why functional checks stopped

Device logs show our successful installation at 04:40:06 UTC, then another successful package installation at 04:41:16 and launch at 04:41:17. This worker made one explicit launch request at 04:41:52, before discovering that conflict. The app was then reported running, but no CALM_TRACE or CALM_TIMING breadcrumbs arrived. The device's transferred package subsequently hashed to `081369b932daf3786b54ad46aaa18e2a5dadcb74ef4865914d9c868a09f9cef1`, which differs from the reviewed build. The other installer and source were not identified. The temporary package hash alone does not identify all installed runtime files; the current runtime identity is unverified.

The installed SDK implementation was inspected: this command pushes the supplied file and calls `vpm install` once, without repacking or launching. The second install and earlier launch were not part of that command.

No remote navigation keys were sent. The app was left open; only this worker's text-log collector was stopped. No additional installation, restart, capture, recording, publication, or source/media/trust change followed. This is an interrupted native checkpoint, not evidence that the app's flows failed.

The logs prove installation events and a running process. They do not prove Home readiness, first visible picture, sound, Pause/resume, visible Skip position, guarded Skip, Back, or Parents/cancel. A `picture-shown` event would describe the readiness gate rather than the first displayed frame. Missing `waiting off` does not establish a stalled native clock.

## Minimum owner steps

1. Coordinate an exclusive simulator window with the other active session and select one exact package. No source rebuild is needed for this reviewed package. Confirm its delivery hash before any route checks.
2. During the agreed check, observe Home -> Details -> Back and Parents -> cancel, then Watch Acadia. Listen through both covers; pause and resume during the first, confirm Skip keeps its visible position/focus, activate Skip during a cover and then Back. Note whether loading and the first visible picture feel responsive. The normal cover intervals are 7.843-12.199 s and 28.613-31.093 s; Extra cautious uses 7.343-12.699 s and 28.113-31.593 s. No recording is needed.

Evidence: [receipt](receipt.json), [device events](device-events.log), [build receipt](build-receipt.json), [build log](build.log), [install result](install.log).

## Read-only follow-up

The device temporary-package hash stayed at `081369b9...` across three reads. It exactly matches `build/release/stabilization-2026-10-17/calm-frames-0.1.0-aarch64-debug.vpkg`. The separate checkpoint build log records source `c2b56d2` and exit 0. Its drive log records the matching 04:41:15 install, 04:41:17 launch, timeout waiting for Home focus and zero remote keys. These identify the competing checkpoint run and its claimed source. They are not a second per-input build receipt or a direct installed-files measurement. All 764 current source inputs still match our reviewed receipt.

No active installer was found. The separate checkpoint text collector is still running (root PID 11597, Node PID 11602), writing `.logs/checkpoint-device.log` from this checkout. Its parent has exited, so its owner session cannot be proved from process linkage. It was left untouched. Our own logger's initial stop left shell descendants; follow-up terminated only its verified process group and confirmed all members exited.

Exclusive simulator use remains unconfirmed, so no recovery install or remote keys were sent. Minimum owner action: pause the separate checkpoint session and confirm no other session will build, install, launch or send keys during the recovery check. Keep the simulator open. Reuse our existing package; do not rebuild merely to repeat these checks.
