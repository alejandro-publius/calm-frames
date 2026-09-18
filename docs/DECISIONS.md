# Decisions

Each entry: date, decision, why, what it costs. Newest at the bottom.

## 2026-09-17: Build on the M1 MacBook
- **Decision:** Develop on this Mac (macOS 15.1.1, Apple M1, 16 GB). No Ubuntu SSD.
- **Why:** Vega SDK 0.24 supports macOS on Apple silicon, so HUMAN CHECKPOINT A passes and no kill rule applies. Apple silicon support continues after Dec 15, 2026, when Intel support ends.
- **Cost:** None. The install docs list KVM only as an Ubuntu requirement.

## 2026-09-17: Keep the name "Calm Frames"
- **Decision:** Keep the name.
- **Why:** No GitHub repository matches "calm frames" or "calmframes". Web and Devpost searches show no project or Appstore app with that name (only unrelated "Calm ..." meditation and fireplace apps). `flashmap`, `calm-frames` and `calmtiming` are free on PyPI, and `use-flash-guard` and `@calm-frames/flash-guard` are free on npm (checked Sep 17). GitHub has other repos named `flashmap` (Rust hashmap, ChromiumOS fmap), which is fine for a package name but worth a distinct PyPI description.
- **Cost:** None.

## 2026-09-17: Vega SDK 0.24.9914 through the official installer, run non-interactively
- **Decision:** Install Vega CLI 1.3.4 and SDK 0.24.9914 with `NONINTERACTIVE=true bash get_vvm.sh`, from a downloaded copy that was read first (SHA-256 in docs/ENVIRONMENT.md). Shell rc files were backed up first.
- **Why:** 0.24.9914 is the latest on the main channel (released Aug 10, 2026) and matches the build prompt's SDK 0.24 pin. Reading the script before running it matters because the documented method pipes curl into bash. Non-interactive mode skips the VS Code extension prompt.
- **Cost:** 5.4 GB in `~/vega`. The installer appended `source ~/vega/env` to `~/.zshrc` and `~/.zprofile`. Telemetry is on by default (opt-out documented).

## 2026-09-17: Node 22 LTS through fnm and `.nvmrc`
- **Decision:** Pin Node 22 (22.23.2 today) for the repo instead of the system Node 26.0.0.
- **Why:** The sample declares `engines.node >= 22` and was last released Aug 6, 2026. Node 22 is the oldest version it accepts, so it's the most likely to match what Amazon tested. Node 22 is in maintenance LTS through April 2027, past judging. CI can read the same `.nvmrc` through `actions/setup-node`.
- **Cost:** One more tool (fnm), and every shell has to run `fnm use`. If the Shaka build or Metro fails on 22, try Node 24 and log it here.

## 2026-09-17: Python 3.12 in a uv venv
- **Decision:** `.python-version` = 3.12, venv at `.venv` (Python 3.12.13).
- **Why:** The prompt needs Python 3.11 or newer, and the system `python3` is 3.9.13. 3.12 has the widest wheel coverage for the scientific and video packages we're likely to need. Revisit when the kits' `requires-python` values are known.
- **Cost:** Commands run as `.venv/bin/python -m ...` or `uv run`, not bare `python3`.

## 2026-09-17: App base is vega-video-sample at tag v0.24-RN83
- **Decision:** Copy `AmazonAppDev/vega-video-sample` at tag `v0.24-RN83` (commit `ef8e4da89b22ef7973d0d41beedfa2b42f7bb272`) into `app/`, keeping its MIT-0 license and notices. Use a plain copy, not a submodule.
- **Why:** That tag is the React Native 0.83 release for SDK 0.24 (the repo also has `v0.24-RN72`). A plain copy keeps everything judges need in one repo. The repo has merged an outside contributor's pull request (#7, Jul 6, 2026), so the upstream pull request in Phase 7.3 can come from a separate GitHub fork.
- **Cost:** Upstream changes have to be pulled in by hand. Done: commit cf8b752 holds the untouched copy, so later commits show exactly what Calm Frames changes.

## 2026-09-17: Leave the shared colima VM alone
- **Decision:** Don't restart or resize colima (2 CPUs, 4 GiB) for the IRIS build. Build IRIS with limited parallelism instead.
- **Why:** Other projects on this Mac use the same Docker VM. Restarting it could interrupt their work.
- **Cost:** The IRIS image (vcpkg builds OpenCV from source) takes longer to build. If it runs out of memory, ask before resizing the VM.

## 2026-09-17: Pause the IRIS image build; don't compete with the shared VM
- **Decision:** Commit the IRIS Dockerfile, scripts, Make snippet and README, but don't restart the build in the shared colima VM while another project's services run there. Build it when that VM is idle, or on a GitHub Actions runner once the repo is on GitHub.
- **Why:** The first build attempt (started about 09:38 PT) ended when the lane 4 agent stalled and was stopped, before any dependency step finished. By then the VM had been resized to 4 CPUs and 8 GiB and was running a DataHub quickstart stack (started about 09:24 PT) using 4.7 of 7.9 GB, with 3.2 GB available and no swap. vcpkg compiles OpenCV with the contrib and ffmpeg features from source, and running out of memory there could make the kernel kill the other project's containers instead of the compiler.
- **Cost:** IRIS isn't building on day one as the prompt asked. Screening day (GATE 2, Fri Sep 25) runs IRIS only once it builds, but the Sep 24 to Oct 2 goal needs IRIS, ffmpeg and naive baselines running in Docker, so the image has to finish by about Sep 30. The ffmpeg and naive baselines don't depend on it.

## 2026-09-17: Either AWS credit form link works
- **Decision:** No change needed to the credit request step.
- **Why:** The Official Rules link `https://forms.gle/5hyhr1u6x3fuV2aW7` and the Resources page link `https://forms.gle/GaHFxSbBQNG9Kti6A` (the one in the build prompt) both resolve to the same Google Form, "AWS Credit Request Form | Amazon Developer Hackathon", which was open on Sep 17. The rules say entrants may request $150 in credits by Oct 21 at 12:00 PT, while supplies last.
- **Cost:** None.

## 2026-09-17: Keep the sample's personalization code, switch it off by flag
- **Decision:** Remove the personalization and account login service components and every dependency the removed features needed, but keep the personalization client calls that remain in the sample's screens, with `isContentPersonalizationEnabled` and `isAccountLoginEnabled` returning false.
- **Why:** Every one of those call sites is already behind a feature flag, so forcing the flags off stops them running, and the guard test proves the flags are off. Ripping the calls out of five screens now would be churn in code that Phase 4 replaces with kid mode anyway.
- **Cost:** Two dependencies stay (`kepler-content-personalization` and `kepler-epg-provider`, which the personalization mocks need), so the manifest still declares those modules. Both go when Phase 4 replaces the sample UI.

## 2026-09-17: Drive the virtual device through QEMU's QMP socket
- **Decision:** Press remote buttons and capture the screen with `eval/vvd_control.py`, which talks to the QMP socket the virtual device exposes.
- **Why:** The Vega CLI has no input or screenshot command, and we need both: to drive playback in a smoke test now, and in Phase 4.5 to record every screen and transition and check them with flashmap.
- **Cost:** It is not a documented interface, so it could change between SDK versions. Screenshots come back black because the app renders on a GPU layer the capture does not see, so playback evidence comes from device logs until that is solved. It only applies to the virtual device, never the stick.

## 2026-09-17 late: the shell that was left running was ingest, not IRIS
- **Decision:** Record what it did and let it finish.
- **Why:** The job still running at handover was `pipeline.ingest` over the two 1930 public domain films, started 23:44 UTC. EA IRIS was never started at all: the shared colima VM had another project's DataHub stack in it with about 2.9 GB free against a 4 GB floor, checked twice an hour apart, so building OpenCV there could have had the kernel kill their containers instead of the compiler.
- **Cost:** IRIS is still not built, so the baselines table has ffmpeg and naive but no IRIS. The first 1930 film failed verify with "the cover schedule over the original video left 1 violation" under the broadcast preset, which is verify doing its job on a title that flickers almost end to end.

## 2026-09-17 late: the head-start kits are still not here, asked for twice
- **Decision:** Carry on without them, and say so as the first line of docs/STATUS.md.
- **Why:** `day-one-head-start.zip` is not at the repo root, not in `~/Downloads` (which now holds no zip at all), nowhere within four levels of the home directory, and Spotlight finds nothing by that name. `headstart/` is still the empty directory created on day one. The kits were meant to be the test oracle for flashmap's thresholds, the source of the spec-exact WCAG and BT.1702-3 numbers, the clip pool in STRESS_TEST.md and the Vega API sheet.
- **Cost:** No independent oracle. Our thresholds stand on docs/SPEC_SOURCES.md, which quotes primary sources and names what could not be verified. The conformance suite computes its ground truth from the spec text in a module that cannot import flashmap, which is the closest thing to an independent check we can build ourselves. If the kits ever arrive, diff the thresholds first and re-record any number taken with our version.

## 2026-09-17 late: stop trying to record the virtual device's screen
- **Decision:** Drop screen capture of the virtual device. Measure software-level lead time instead, in results/gate1_software_vvd.json, labelled as software-level and never quoted as a gate number.
- **Why:** Two independent blocks. macOS exposes no screen capture device to ffmpeg without the Screen Recording permission, and the window is not captured anyway: a full screen grab while the virtual device was frontmost returned the desktop behind it, and QEMU's own screendump returns black, because the app draws on a GPU layer neither path sees. Chasing it further would spend time on a dead end.
- **Cost:** Nothing measured on the virtual device can speak for the screen. The software number is an upper bound on how well the real thing can do, because the React commit, the compositor, scan-out and the panel all add delay that this measurement cannot see. GATE 1 stays what it always was: 50 trials filmed at 240 fps on a real stick.

## 2026-09-17, night: the carry-over fixes

- **Decision:** The player subtracts `rendition_start_offset_ms` inside
  `buildCoverIntervals`, rather than anywhere else.
  **Why:** it is the one place every caller already goes through, so a screen
  that forgot to apply the offset is not possible. The safety property is
  stated as lead time and not as coverage, because with an offset smaller than
  the guard band the cover still lands before the picture, just with less room
  than the band promised, and the band has to absorb the scheduler as well.
  **Cost:** one option on a pure function, plus a fail closed path in
  useFlashGuard when the offset is further out than verify would publish.

- **Decision:** Re-verify the eight titles blocked on
  `rendition_matches_source` instead of ingesting eight more.
  **Why:** those eight failed on the picture rectangle and start offset bar
  that was fixed today. They already have maps and renditions on disk, so
  verify alone decides them. Ingesting new titles to reach twenty while eight
  correct ones sat blocked by a fixed bug would have been the wrong count.
  **Cost:** minutes per title with `--no-rerender`, against roughly an hour
  each to ingest a new one.

- **Decision:** Report cover lead in media time alongside wall clock.
  **Why:** the two come apart when playback runs slower than real time, which
  the virtual device does constantly. The cover goes on at the right place in
  the clip and then waits a long time in wall clock for the playhead to reach
  the marker. That is what put the p95 at 4097 ms, not the scheduler being
  early, and reporting only wall clock would have made a slow machine look
  like a design fault.
  **Cost:** one more field per trial, and a reason recorded for any cover that
  goes on earlier in the clip than the guard band asked for.

- **Decision:** Report dropped trials two ways, strict and usable, and quote
  the strict one if only one is quoted.
  **Why:** a trial that could not be measured is not a trial that passed. The
  usable fraction on its own flatters, because the runs that went wrong are
  exactly the ones that drop out.
  **Cost:** two fractions and two intervals in the results file.

- **Decision:** Instrument the gap between runs of the scheduler's own tick.
  **Why:** the cover that went on 86 ms late was blamed on the JavaScript
  thread being away, and nothing measured that directly. The guard band has to
  be wider than the worst such pause, so the pause has to be a number.
  **Cost:** one ref and one log line per gap past twice the tick.

- **Decision:** Do not cap how early a cover may go on. Report the reason for
  every cover that starts earlier in the clip than the guard band asked for,
  and leave the cover itself alone.
  **Why:** the brief asked for a cap so that the p95 lead stays under 1.5
  seconds unless a stall or a seek forced it. Looking at where the long leads
  actually come from, a cap would either do nothing or make the app less safe.
  There are only three ways a cover starts earlier than one guard band ahead.

  The first is interval merging. Two flagged segments close together merge
  into one cover so the picture does not flicker clear for a fraction of a
  second between them. Capping that would uncover between two segments that
  nearly touch, which is the exact thing the merge exists to prevent, and the
  picture would flash clear over flashing content.

  The second is a hold the harness takes when the playhead stops being
  trustworthy, after a seek, a stall, a pause or the app going to the
  background. Those are the cases the brief already exempts.

  The third is not an early cover at all. It is playback running slower than
  real time, which the virtual device does constantly. The cover goes on at
  the right place in the clip and then waits in wall clock for the playhead to
  reach the marker. That is what put the p95 at 4097 ms. Nothing about the
  schedule is early there, and a cap keyed on wall clock would start
  uncovering flashing content on any slow device, which is the worst possible
  place to save time.

  So the fix for the number is to measure it in media time, where it is
  bounded by the guard band by construction, and to name the reason whenever
  it is not. That is what landed.
  **Cost:** the p95 of the wall clock lead stays large on the virtual device
  and is reported as such, with the media time lead beside it. If the media
  time p95 ever exceeds the guard band for a reason that is not a merge or a
  hold, that is a real defect and the reason field will say so.

## 2026-09-17: Measure the ten foot pass instead of looking at it
- **Decision:** Every claim about how the app reads across a room is a number
  taken off the rendered screen: type size, the contrast of each line against
  the colour actually painted behind it, the focus ring against both of its
  neighbours, and the safe margins. `app/src/calmframes/uiContrast.ts` does the
  reading, `app/test/calmframes/tenFoot.test.tsx` applies the floors to every
  screen and every state, and the numbers land in
  `app/build/ui-capture/ten-foot.json`.
- **Why:** the virtual device cannot be photographed. The app draws on a GPU
  layer that macOS screen capture and QEMU's screendump both miss, so there is
  no screenshot to judge and no way for anyone else to check a judgement. A
  measurement can be checked, and a floor can be enforced on every screen
  including the ones nobody opens.
- **Cost:** the floors are written out twice, once in calmStyles.ts and once in
  the test. That is deliberate: the first version compared each screen against
  the same constant the screens are built from, so narrowing the safe margin
  moved both and the test stayed green. A guard that cannot fail is not a
  guard. The duplication is what makes it fail.

## 2026-09-17: The type floor is 32 units at 1080p, and the safe margins are 96 by 54
- **Decision:** Raise the smallest text from 28 units to 32, and keep every
  screen 96 units from the side of the picture and 54 from the top and bottom.
- **Why:** on a 55 inch screen one unit at 1080p is about 0.025 inches, so a 32
  unit line is about 20 arcminutes of cap height from a sofa 8 feet away, which
  is inside the comfortable range for sustained reading rather than at its
  edge. 28 units came out at about 18 arcminutes. The margins are five per cent
  of each edge, the convention television interfaces have used for decades,
  because sets still overscan by different amounts.
- **Cost:** the poster grid fits four across instead of five, and every screen
  holds slightly less. Both are the right trade for a child and a tired parent
  reading from a sofa.

## 2026-09-17: The player decides whether it may show a picture, not the caller
- **Decision:** `app/src/calmframes/playerAccess.ts` gives three answers and
  the player asks on every render: the guard is running, a measurement harness
  is running, or the picture stays hidden with a card saying why. Guarded
  parameters carrying no map are not guarded parameters.
- **Why:** the player came from the Vega sample, where anything in the catalog
  plays on request, and five screens still navigate to it that way. Fixing the
  call sites is a promise about call sites; any new screen, deep link or
  leftover sample screen would have played whatever it was handed. The whole
  project is the claim that nothing plays unchecked, so the refusal belongs in
  the one place every path goes through.
- **Cost:** the sample's own titles now show a "Not checked yet" card and a
  black picture, which is correct for this app and surprising for anyone
  expecting the sample. Measurement runs are exempt, because a harness run
  plays a marker clip at a camera with nobody watching.

## 2026-09-17, night: the camera meter

- **Decision:** The meter counts flashes with its own code and never imports
  flashmap.
  **Why:** the meter exists to find out whether the thing flashmap protects
  stayed covered on a real screen. Counting with flashmap's own tracker would
  make a pattern flashmap cannot see invisible to both, and the check would
  then agree with the thing it is checking for the worst possible reason.
  Thresholds still come from the one quoted spec file, through
  eval/conformance/spec.py, which lives under the same rule.
  **Cost:** a second implementation of the same two state machines, and a real
  risk that the two drift apart. Two guards: one reads the syntax tree of every
  meter module, the other imports them in a fresh interpreter and checks
  flashmap never arrived.

- **Decision:** A run of transitions in the same direction counts once when the
  meter pairs them into flashes.
  **Why:** a camera whose shutter is open while the screen changes records the
  middle of the change, so one edge on the TV arrives as two steps at the
  camera. Pairing both turned a 6 Hz strobe into 12 flashes a second, which the
  validation caught on its first run. WCAG measures between adjacent peaks and
  valleys, and a run in one direction is one journey between them, so
  collapsing it is the closer reading as well as the working one. It can only
  ever remove a duplicate, never an opposing pair, so it cannot hide a flash.
  **Cost:** the meter and flashmap now read a multi step edge differently.
  flashmap never meets one, because a file changes on a frame boundary, so
  nothing needs to change there today. Worth a look for footage that was itself
  filmed off a screen.

- **Decision:** The screen region comes from the gray field take, and the
  region finder uses the bounding box of the lit pixels.
  **Why:** the first version kept the rows and columns that were mostly lit. On
  a step chart, which is black at one end, it handed back the white half of the
  chart and called it the TV, and the calibration then read patches that were
  not there. A bounding box copes with a screen that is only partly lit, and a
  uniform gray field is the easiest thing in the world to find, so the protocol
  films one first and the other two takes reuse the region.
  **Cost:** a third recording per take, about two seconds of filming. The gray
  field was already needed for the flicker check, so it earns its place twice.

- **Decision:** An uncalibrated run, or one where the camera clipped, is marked
  not publishable rather than refused.
  **Why:** the meter beside the TV in the demo video has to run without a step
  chart on the night, and a reading in a video is not a published number. A
  clipped camera reads bright states low, so it can only under-count, which is
  the dangerous direction. Marking the report and saying why keeps both uses
  honest.
  **Cost:** a `publishable` field that anything writing a number has to check.
  Two tests, both seen to fail.

- **Decision:** Mutate the meter's guards in the working tree rather than in
  eval/mutate_gate.py.
  **Why:** the gate landed in another lane while this was being written, and
  the meter's files are new and imported by nothing else, so the blast radius
  was one lane's own code for about two minutes per mutation. Fifteen guards
  were broken, fourteen went red for the right reason, and the fifteenth
  survived: the ceiling on how much of the frame a screen may fill was measured
  after the bezel inset came off, which put it permanently out of reach. That
  is fixed and it now has a test of its own.
  **Cost:** these mutations are recorded in the test file's docstring rather
  than in results/mutation.json. Moving them into the gate is a job for whoever
  owns it, and the list is written out ready to move.
