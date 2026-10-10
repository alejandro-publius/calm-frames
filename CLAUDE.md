# Calm Frames: rules for every session

**Active scope, Oct 9 finishing session.** Alex is entering solo and has an
identity-verified Amazon Developer account. Use only the Vega Virtual Device.
Physical sticks, camera timing, TV rehearsal and hardware gates are outside
this submission's completion criteria. Preserve their historical measurements
and limitations without treating them as pending work for Alex. The brand line
is "A calmer way to watch". The current checklist is
`docs/COMPLETION_CHECKLIST.md`; it supersedes older next-action lists below.
Do not publish, submit, change repository visibility or incur additional cloud
costs before the reviewable work is complete and Alex approves those actions.
Claude CLI workers require verified existing subscription authentication and
one successful small task first; no API keys or permission bypasses.

**Current phase:** Phase 10, signed scene holds, durable household setup and a
benign captioned demo and checked packaged library, Fri Oct 2, 2026, with the
state brought up to Fri Oct 9 at the end of this section. The current default shelf includes the
original gradient and Harbor story. Harbor uses clearly labelled sham holds,
original non-flashing media, a verified pre-covered master, signed context
images and external captions. Its fixed per-title Extra cautious preparation
matches the displayed plan without changing saved household preferences.
A separate demo key is accepted only for the exact packaged title identity.
The read-only hardware preflight pins its reviewed proof and checks package
members before reporting that caption/hold fixtures are available.

Household state persists in a validated local record. Failed reads/writes block
the library; retries retain the intended change; the parent area unlocks after
saving the PIN gate. Profile history clears only after committed removal, and
caption Off now disables the selected native track. Hide history itself remains
in memory. Native storage durability and image/caption composition were observed on the
Vega Virtual Device on Oct 9 and 10; see the current receipt. Software checks and packaged fixture availability are not
physical-TV proof. Do not run the QEMU timing path on a physical target unchanged.

The latest project assessment is in `docs/HACKATHON_REVIEW.md`; it distinguishes
subjective quality from incomplete submission evidence. The reusable autonomous
work prompt is `docs/CONTINUATION_PROMPT.md`. Follow its current STATUS handoff,
complete the native benign journey next. Checked local receipts now export a
bounded immutable library into the app build. The app selects the exact preset
rendition and accepts its compiled key only for full title membership. The local
wrapper uses the app's map unions/timing; generic imports use opaque live fallback,
while the separate labelled Harbor demo retains signed scene holds. Adding a
prepared title requires rebuilding the package. No remote service was added.
The hook has an offline tarball-consumer check, not independent adoption proof.
See STATUS section 0 for final local checks and limitations; older counts and
runs below it are historical.

**Current finishing checkpoint, Oct 10.** Follow `docs/COMPLETION_CHECKLIST.md`.
The full native benign journey, saved settings, three presets, catalog playback,
remote transport, captions through both holds and native recording are observed.
The final English demo is prepared locally. Full app and Python suites pass;
all formerly blocked localhost tests and the failed UI invocation are resolved.
Claude Fable 5.1 with explicit max effort completed bounded subscription workers.
SBOM/CDK fixes reproduce locally; dependency Audit remains failed and hosted
rerun is pending. No physical timing claim, cloud consumption by the app,
publication or submission is implied. Exact provenance lives in the native receipt.

AWS deployment remains the saved Oct 9 evidence in
`results/aws_deploy_2026-10-09.json`. The app consumes its compiled local
catalog and does not trust or consume the cloud catalog. Preserve the separate
deploy worktree and its checkpoint line. A new deployment still requires
approval and the signing-key parameter; this finishing task does not authorize
additional cloud costs. Budget tag activation and image findings remain open.

**The head-start kits never arrived.** flashmap, calm-timing, evkit and the notes were all written here instead. docs/PLAN.md lists what replaced what. If the kits turn up, treat them as a second opinion and re-record any number taken with our version.
**Repo:** private at github.com/alejandro-publius/calm-frames. Work is on
`codex/signed-scene-holds-2026-09-29`, published as
[draft PR #1](https://github.com/alejandro-publius/calm-frames/pull/1), whose head
on Oct 9 is eb59c69; main remains unchanged. Runs from Sep 28 to Sep 30 stopped
before any runner started, which GitHub's annotation put down to failed account
payments or a spending limit, not a code failure. That ended by Oct 5, when
the scheduled Audit on main ran real steps, and runners have taken every job
since. On eb59c69 CI is green in all six jobs and Audit is red in two of four:
npm advisories with no written exception, and SBOM drift. The scene-hold tree
must pass Audit as well before main is updated. The chosen plan is to make it public during the final checks on Oct 21
with the licence visible. Current rules also allow private reviewer access;
see the rechecked requirements in docs/SUBMISSION.md.

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
- CDK: `natGateways: 0`, $20 budget alarm, cost tags, `make destroy` does not remove the bootstrap resources or manually created signing parameter; inspect the saved deployment record for remaining resources. No AWS deploy until HUMAN CHECKPOINT D is confirmed.
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
- Remote buttons: Amazon's Vega 0.24 docs describe `inputd-cli`, built into Fire TV devices and the Vega Virtual Device and run from the host as `vega exec inputd-cli button_press KEY_BACK`. The full command set needs developer mode; on the virtual device that is `vsm developer-mode enable` inside `vega exec device shell -d VirtualDevice`. Read at developer.amazon.com/docs/vega/0.24/inputdcli.html on Oct 9, 2026. On this CLI, `vega device run-cmd --device Simulator --command 'inputd-cli --help'` works; the documented `vega exec inputd-cli` route instead looks for a missing host executable. Until it has been, `eval/vvd_control.py` presses keys through QEMU's QMP socket.
- Screenshots: no CLI command for them has turned up in the docs read so far. `eval/vvd_control.py` takes one through QMP, and it comes back black because the app renders on a GPU layer the capture misses, so verify playback from device logs.
- Release builds strip `console.log`. Use the debug package when you need the app's own logs.
- The build rewrites `app/manifest.toml`, adding a `[[needs.module]]` entry per installed `@amazon-devices` package. Removing a feature means removing its dependency too, or the app still declares it needs that module.
