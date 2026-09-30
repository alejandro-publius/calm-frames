# Calm Frames: rules for every session

**Current phase:** Phase 10, signed scene holds and AWS-free workflow, Tue Sep 29, 2026. Scene-specific
preceding images now join the signed map, rendition, cover model and live guard.
They never change intervals or thresholds. Focused regressions and the final
broad app suite, final selected Python sweep and complete mutation measurement
pass. The final-source native Debug build passes on all three configured
architectures; remote CI is blocked before runner startup.
The upload-server HTTP fixtures now pass on the unrestricted runner, and
real-device image, caption and timing composition still need benign-media proof.
The follow-up local-library receipt wraps normal ingest and verify, without
serving media or connecting the app shelf. Household review and title plans are
presentation-only; settings and the PIN remain in memory. The hook now has a
clean offline tarball-consumer check using current Vega peers. The final local
app, Python and package tests and native Debug build pass for these changes;
see STATUS section 0.
The earlier `image-size` audit blocker is repaired with a small local legacy
API adapter around exact official parser 2.0.4. The fresh audit and regenerated
SBOM check pass, without a copied parser or widened exception. Existing written
SDK/tooling exceptions remain. All 860 app tests and 1,378 selected Python tests
pass, with existing skips/deselections unchanged. The rebuilt native Debug
packages pass manifest/ABI checks for all three configured architectures.
The read-only hardware preflight checks current package bytes but reports no
connected device. The bundled calm clip cannot test caption/scene-hold layering;
a checked benign fixture, physical-target runner adaptation and real-TV camera
proof remain required. Do not run the QEMU-based timing path on hardware unchanged.
Publish only locally checked changes to the isolated review branch; main still
waits for complete hosted CI, in line with Alex's ready-only push requirement.
Phase 9's pattern-rule precision work remains recorded below. Phases 0 to 2
are done apart from what needs the stick, and all five phase 8 features are in, tested,
documented and reachable in the running app. Phase 9 so far: the regular-pattern rule
requires a period before a run of bars counts, so text is no longer read as stripes; both
ffmpeg baselines were re-run as one set on ffmpeg 9.0.1; the labelling pool is back to 40
segments over 16 titles. docs/STATUS.md section 0 is the short version and section 2 is
Alex's dated list.
**The head-start kits never arrived.** flashmap, calm-timing, evkit and the notes were all written here instead. docs/PLAN.md lists what replaced what. If the kits turn up, treat them as a second opinion and re-record any number taken with our version.
**Repo:** private at github.com/alejandro-publius/calm-frames. Work is on
`codex/signed-scene-holds-2026-09-29`, published as
[draft PR #1](https://github.com/alejandro-publius/calm-frames/pull/1); main remains
unchanged. Both review workflows failed before any runner or step started. The
unrestricted startup annotation identifies failed account payments or a
spending limit, not a code failure; account settings were not changed. The
main commit's inspected push CI passed on Sep 20; the Sep 28 scheduled Audit and Sep 29 retry failed
before any runner or step started. The scene-hold tree must pass GitHub CI before
main is updated. It goes public during the final checks on Oct 21, because the rules
need it public with the licence visible at submission.

Read first, in this order: docs/STATUS.md (done, next, blocked, needs), docs/BUILD_PROMPT.md (the full plan, phases, gates, kill rules, cut list), docs/DECISIONS.md, docs/GATES.md.

## How to resume, from a session with no memory

1. **Read, in this order.** `docs/STATUS.md` section 0 and section 2 first, then this file,
   then `docs/BUILD_PROMPT.md`, `docs/DECISIONS.md` (newest entries are at the bottom),
   `docs/GATES.md`, and `docs/VERIFY_PASS_2.md` if the work touches the pattern rule.
   `git log --oneline -40` after that, because a commit message here carries the reasoning.
2. **Check the tree and the build before touching anything.** `git status`, then
   `gh run list --limit 4`. A clean tree is not the same as a green build: on Sep 18 the tree
   was clean, pushed and up to date with origin while the Vega app job had been red on main
   for a day over a zero byte test file. Read the failing job, do not assume.
3. **Check for jobs that should be running.** `ps aux | grep -E 'ffmpeg|pytest|run.py'`. The
   colima `limactl usernet` process belongs to another project and is always there; leave it.
   Logs from background runs go under `.logs/`, which is gitignored.
4. **Restart commands for the long jobs**, all safe to re-run and all writing to `.logs/`:
   - `make ffmpeg-ps-pool` and `make naive-luma-pool`, about 40 minutes each over the whole
     of `media/`. Afterwards delete any un-prefixed report whose `HAZARD_` twin now exists,
     then `python eval/baseline_versions.py` must pass.
   - `.venv/bin/python eval/pattern_text_precision.py`, about 4 minutes, writes
     `results/pattern_text_precision.json`.
   - `.venv/bin/python eval/report_page_check.py`, about 2 minutes, needs Chrome.
   - `cd app && npm run ui:flashmap`, about 1 minute.
   - `.venv/bin/python eval/labeling/make_pool.py` then `eval/labeling/plots.py`, about a
     minute. **Never once labelling has started**: a segment id is a position in a shuffled
     list. `make_pool` refuses while any sheet has an answer in it.
5. **Before any number reaches a document:** `python eval/readme_sync.py` to rewrite, then
   `--check`. The drift checker cannot see prose, so re-read the sentences around a number
   that moved.
6. **Before pushing:** `make ci`, or at least `make test-app` and
   `.venv/bin/python -m pytest flashmap pipeline eval -q -m "not slow"`.

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
- **The drift checker cannot catch the right number being left out.** Every published
  number traces to `results/` and passes `eval/readme_sync.py --check`, and that guards
  against a number going stale. It does nothing about which number was chosen. Four
  times now the one published was the friendlier one: the blended recall instead of the
  near-limits recall, the median cover lead instead of the spread, the well-behaved
  timing run instead of the under-load one, and "21 titles verified" instead of the 7
  that cover anything. So when a number has a worse sibling, publish both, or say in
  the same sentence why the worse one is not the honest measure. This matters most in
  the Devpost text and the video script, where no marker check runs at all.

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
- Friction log from minute one: real entries only (task, steps, expected vs actual, severity, workaround, suggestion), in docs/FRICTION_LOG.md. There is no second file: the scratch pad that used to sit beside it shipped by mistake and is gone.
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
