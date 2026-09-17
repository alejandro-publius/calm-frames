# Status

Updated Thu Sep 17, 2026, afternoon PT.

## Done

### Phase 0
- **0.1 Machine check:** macOS 15.1.1 on Apple M1, 16 GB, 1.2 TiB free. Supported by Vega SDK 0.24. HUMAN CHECKPOINT A passed.
- **0.2 Installs:** Vega CLI 1.3.4 and SDK 0.24.9914 (latest), Node 22.23.2 through fnm, Python 3.12.13 venv through uv, JDK 21 (the sample's Shaka build needs Java 21 or newer), watchman, gitleaks 8.30.1. Versions in docs/ENVIRONMENT.md.
- **0.3 Repo:** `~/calm-frames`, local only (no GitHub remote yet).
- **0.5 License:** Apache-2.0 LICENSE and NOTICE.
- **0.8 Name check:** "Calm Frames" is free on GitHub, Devpost and the web. `flashmap` and `calm-frames` are free on PyPI, `use-flash-guard` on npm.
- **Rules check against Devpost:** deadline Oct 23 12:00 PT, judging Nov 9 to 20, winners around Dec 3. Four equally weighted criteria, ties broken by the first one, Tech Implementation. Both AWS credit form links open the same form ($150, closes Oct 21 12:00 PT). A Sep 16 update requires the repo to be public with an open-source license, or private and shared with testing@devpost.com and @AmazonAppDev.

### Phase 1
- **1.2 Day-one fixes, done before anything was built on the sample:** package renamed to `io.github.alejandropublius.calmframes`; both service components, both task components and the live TV sync source removed with their code, mocks and tests (4,644 lines); the five npm dependencies those features needed removed, because `react-native build-kepler` turns every installed `@amazon-devices` package into a `[[needs.module]]` entry; `setNativeProps` banned by lint; personalization and account login flags forced off.
- **1.3 The app plays a Blender title on the Vega Virtual Device**, two days before the Sat Sep 19 target. Cosmos Laundromat over HLS, with the media pipeline reporting playback started and Shaka fetching segments. Recorded in results/vvd_smoke.json, written up in docs/GATES.md including what is still flaky.
- **1.6 (part) Cover schedule:** the guard band, merging, minimum cover length, red handling, playback-rate conversion and seek-target checks that GATE 1 measures, with 30 tests.
- **Tooling:** `eval/vvd_control.py` presses remote buttons and captures the screen through QEMU's QMP socket, since the Vega CLI has neither. `eval/vvd_smoke.py` records a playback run to results/.
- **Guards, each one seen to fail:** 15 day-one assertions (manifest has no task or service components, package id is not under com.amazon, app.json matches the manifest, no module entries for removed features, flags off) and 30 cover-schedule assertions. Breaking each rule on purpose turned the suite red, and one mutation survived the first pass and exposed a real gap, now covered.

## Not started or blocked

- **Layering test screen (1.5) and the GATE 1 harness wiring (1.6):** the schedule logic is in and tested; the on-screen cover, the event logging (currentTime with wall clock on every timeupdate, seeking and seeked, plus getVideoPlaybackQuality) and the dev screen that toggles a cover over a playing title are not built yet. The marker clip itself comes from calm-timing, which is in the missing kits.
- **Back navigation regression test (1.2):** the sample's README lists a black screen with audio-only playback after back navigation. Not written yet.
- **0.4 kits, 0.6 CI, 0.7 friction tooling:** blocked. `day-one-head-start.zip` is not on this Mac, in Google Drive or in claude.ai artifacts.
- **0.9 outreach drafts (due Fri Sep 18):** blocked on `outreach-kit.md`.
- **docs/RUBRIC.md:** blocked on `rubric-amazon.md`.
- **Lane 4, IRIS baseline image:** files committed with verified pins, never built. Paused while the shared colima VM runs another project's DataHub stack. Needs to finish by about Sep 30.
- **GitHub repo:** not created yet, so CI has nowhere to run.

## Friction log
9 real entries in docs/friction_pending.md, waiting for evkit. Five about the SDK installer and docs, four from device work: `vega device list` crashes with a TypeError while a device is running, the virtual device stops with no message, its status says running before the device can be used, and there is no supported way to press a remote button or capture the screen.

## What I need from you
1. **The kits:** `day-one-head-start.zip`, `rubric-amazon.md` and `outreach-kit.md` in `~/calm-frames/headstart/`, or tell me where they are. Four Phase 0 items and the GATE 1 marker clip are waiting on them.
2. **Today's steps:** order the stick, join the hackathon on Devpost, sign in to an Amazon Developer account, request the AWS credits, put the AWS account on the Paid plan with a $20 budget alarm, and check 240 fps filming and TV game mode.
3. **One decision:** may I create the GitHub repo now as private, and make it public later? CI cannot run until it exists.
