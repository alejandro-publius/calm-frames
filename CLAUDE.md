# Calm Frames: rules for every session

**Current phase:** Phase 2 and 3 in progress, Thu Sep 17, 2026. Phases 0 and 1 are done apart from what needs the stick.
**The head-start kits never arrived.** flashmap, calm-timing, evkit and the notes were all written here instead. docs/PLAN.md lists what replaced what. If the kits turn up, treat them as a second opinion and re-record any number taken with our version.
**Repo:** private at github.com/alejandro-publius/calm-frames, main, CI green on ubuntu runners. It goes public during the final checks on Oct 21, because the rules need it public with the licence visible at submission.

Read first, in this order: docs/STATUS.md (done, next, blocked, needs), docs/BUILD_PROMPT.md (the full plan, phases, gates, kill rules, cut list), docs/DECISIONS.md, docs/GATES.md.

## What this is

Calm Frames is our entry for Build, Ship, Shape: Amazon Developer Hackathon (https://amazonappdev2026.devpost.com). Track: Fire TV. Mini challenges: Open Source (primary) and AWS Builder. Deadline Fri Oct 23, 2026, 12:00 PT; we submit Thu Oct 22.

Thesis: a verified safety layer for kids with photosensitive epilepsy, not a video player. Every frame of a title is analyzed before it can play in kid mode, producing a signed flash map. The player hides each flagged flashing segment before it starts while sound and captions continue, then says what was hidden. Household settings can only make it stricter than WCAG. Voice, D-pad and on-screen cards work as one flow and every seek path is safe. Any Vega video app can add it with a small hook, and studios can check content with the open-source analyzer and GitHub Action.

## Hard rules

### Safety (these override everything)
- Nobody watches strobes at full speed. Hazard files carry the `HAZARD_` prefix, live under `media/` (gitignored), never autoplay, and are inspected only as plots (`eval/plots.py`, which must not import flashmap) or slowed, dimmed playback.
- Generated conformance clips are hazardous by design: generate, analyze and delete them in the same job. Never open them.
- Never play real flashing content with the filter off. Compute prevented exposure from the flash map instead.
- Never commit hazardous media. Only `media/LICENSES.csv` and hashes are committed.
- Whoever films flashing footage is not photosensitive and doesn't look at the lights. People in frame give consent.
- Approved wording: "reduces exposure to flashing above published limits in the videos it plays; not a medical device." Never "prevents seizures" or "seizure-proof".

### Truth
- Every published number (README, Devpost text, video) comes from `results/*.json` through `eval/readme_sync.py`, and CI fails on drift. Mark one like this: `<!--n results/file.json:key -->value<!--/n-->`.
- Nothing mocked is shown as real. Label composite personas (Maya), sham maps and estimates.
- Thresholds come only from `docs/SPEC_SOURCES.md`. Never re-derive a threshold from memory. A new number needs the quoted spec text and link in SPEC_SOURCES.md first, and anything that cannot be verified from a primary source is named there and not used.
- Every guard gets a test that has been seen to fail: break the guard on purpose, watch the test go red, restore it. A green new test proves nothing on its own.
- `docs/EVAL_PLAN.md` is committed before any real clip is labeled. Later changes are logged as deviations.
- Re-check any source page before quoting it (impact numbers, licenses, Amazon docs).

### Media and licenses
- Download a file only after opening its source page and confirming the license and credit line. Record URL, license, credit line, SHA-256, duration and resolution in `media/LICENSES.csv`.
- Tears of Steel is CC BY 3.0 only with its credit scroll kept. Blender logos are excluded from the Blender Studio licenses. DVIDS needs a non-endorsement notice. Follow NASA's credit-line guidance. Keep the Hell's Angels (1930) title out of the video. Anything marked "verify" is verified or dropped.

### Engineering guarantees (enforced in code, with tests)
- The verify step blocks publishing. A title can't appear in kid mode until verify passes.
- Fail closed: a missing, stale, unsigned, unparseable or wrong-hash map keeps the picture hidden.
- Every way of moving the playhead goes through one function. Target inside an interval or guard band: cover first, then seek.
- Room settings can only add hides. Red segments always get an opaque cover. Dim mode only for non-red segments at 90% or darker, and verify models it.
- Plan B (pre-covered kid-safe rendition) is always built, whatever GATE 1 says.

### Vega app rules (SDK 0.24, React Native 0.83)
- No `setNativeProps` (throws TypeError on RN 0.83). Drive UI through state. A lint rule enforces this.
- No `[[components.task]]` or `[[components.service]]` in `app/manifest.toml` (can crash at launch on RN 0.83).
- The package ID must not start with `com.amazon` (developer mode won't sideload it).
- Don't try to hide video by lowering the surface view's opacity.
- Playback only through `@amazon-devices/react-native-w3cmedia`; captions in one `KeplerCaptionsView` per process.

### Security and ops
- No secrets in the repo. gitleaks runs in CI and as a pre-commit hook. AWS access from CI only through GitHub OIDC.
- The map-signing private key never enters the repo; the app ships only the public key.
- CDK: `natGateways: 0`, $20 budget alarm, cost tags, `make destroy` leaves nothing billable. No AWS deploy until HUMAN CHECKPOINT D is confirmed.
- Pinned: Vega SDK 0.24.9914, sample tag `v0.24-RN83` (commit ef8e4da), Node 22 (`.nvmrc`), Python 3.12 (`.python-version`, `.venv`).
- The colima Docker VM on this Mac is shared with other projects. Never restart colima or remove containers, images or volumes we didn't create.
- Commit small and often. Once the judged release tag exists, never move it.

### Style
- No em dashes or en dashes anywhere: docs, UI text, code comments, commit messages.
- Don't use the words "genuinely", "honestly" or "straightforward". Plain, warm writing.

## Working mode
- Work on your own. Record each call in docs/DECISIONS.md (date, decision, why, cost) and keep going.
- Stop and ask only at a HUMAN CHECKPOINT or when a KILL rule fires (both listed in docs/BUILD_PROMPT.md).
- Keep docs/STATUS.md current and end every block of work with one status line.
- Friction log from minute one: real entries only (task, steps, expected vs actual, severity, workaround, suggestion), in docs/friction_pending.md. evkit never arrived, so that file is the log.
- Parallel lanes: (1) flashmap and conformance, (2) Vega app, (3) pipeline and CDK, (4) baselines and evaluation, (5) docs, friction log and feedback. A separate verifier agent attacks every claim and number at each milestone before it reaches the README, Devpost text or video.
- Update this file at every phase change.

## Environment quick reference
- Vega: `source ~/vega/env` (already in `.zshrc`), then `vega ...`
- Node: `eval "$(fnm env)" && fnm use`. The app also needs `JAVA_HOME=/opt/homebrew/opt/openjdk@21` for the Shaka build during `npm install`.
- Python: `.venv/bin/python` or `uv run` (the system `python3` is 3.9)
- Full versions: docs/ENVIRONMENT.md

## Measurement runs

- `eval/marker_clip.py` makes the marker clip and its schedule. The clip stays out of git; the schedule and its SHA-256 are committed.
- `eval/vvd_timing_run.py` serves the clip and a run config over HTTP, launches the app and collects what it did. `eval/gate1_rehearsal.py` turns that into the gate analysis.
- A run is started by a config the app fetches at startup, because on OS 1.2 nothing can put a file in another package's data directory from the host.
- Serve the clip as HLS. The player does not start a plain MP4 over HTTP, and the test server has to answer byte ranges.
- The clip needs an audio track, even a silent one, or playback pauses a few seconds in.
- Device logs cannot carry the evidence: the device drops the app's console output under load. Runs post their events to the machine running them.

## Working with the Vega Virtual Device
- Start it detached, or it dies with the shell that started it. `eval/vvd_smoke.py` handles this.
- `vega virtual-device status` says running before the device is usable. Wait for `vega device is-connected` instead.
- `vega device list` crashes with a TypeError. Use `vega device info` and `vega device is-connected`.
- The CLI cannot press remote buttons or take screenshots. `eval/vvd_control.py` does both through QEMU's QMP socket. Screenshots come back black because the app renders on a GPU layer the capture misses, so verify playback from device logs.
- Release builds strip `console.log`. Use the debug package when you need the app's own logs.
- The build rewrites `app/manifest.toml`, adding a `[[needs.module]]` entry per installed `@amazon-devices` package. Removing a feature means removing its dependency too, or the app still declares it needs that module.
