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

## 2026-09-17 late: what this stack costs a month, as an estimate

- **Decision:** Publish a monthly cost estimate of about $<!--n results/cost_estimate.json:published.monthly_total_usd -->1.34<!--/n--> in us-east-1, against the $<!--n results/cost_estimate.json:published.budget_alarm_usd -->20<!--/n--> budget alarm, and say plainly that it is an estimate rather than a bill.
- **Why:** Anyone reading an infrastructure lane's work wants to know what it would cost before they let it run. The arithmetic is in `scripts/cost_estimate.py` and the numbers in `results/cost_estimate.json`, so it can be argued with rather than believed.

  The assumptions: 20 titles a month, 10 minutes each, one preset in the cloud, an ARM Fargate task of 2 vCPU and 4 GB taking 15 minutes per title, 0.8 GB of published artifacts per title, source masters expiring after 30 days, and about 20 GB of viewing a month.

  The lines: Fargate $<!--n results/cost_estimate.json:published.fargate_usd -->0.4<!--/n-->, S3 storage $<!--n results/cost_estimate.json:published.storage_usd -->0.83<!--/n-->, and small change for ECR and requests. CloudFront is nothing because 20 GB is inside its always free 1 TB a month. DynamoDB at 20 writes a month is nothing. Lambda and CloudWatch Logs are not in the table at all, because at this volume they round to zero whatever the rate is.

  Every unit price was read from the AWS pricing pages on Sep 17, 2026 and each one carries its page in the JSON. Fargate ARM is $0.032380 per vCPU hour and $0.003560 per GB hour; S3 Standard is $0.023 per GB month; DynamoDB on demand is $0.625 per million writes; ECR is $0.10 per GB month; CloudFront gives 1 TB out and 10 million requests a month free.
- **Cost:** The estimate has one soft input and it is the biggest one: nobody has measured how long the ingest task takes per title, because the container has never processed a video. So the file carries a sensitivity block. At twice the task time the total is $<!--n results/cost_estimate.json:published.task_time_double_usd -->1.73<!--/n-->; at four times, $<!--n results/cost_estimate.json:published.task_time_quadruple_usd -->2.52<!--/n-->. The shape of the bill does not change, because compute is not what dominates it at this size.

  What would change the shape: a NAT gateway per zone, which the CDK creates by default and this stack sets to zero, would add $<!--n results/cost_estimate.json:published.nat_gateways_would_add_usd -->65.7<!--/n--> a month on its own, before any data. That is the line the whole network design exists to avoid, and it is more than three times the budget alarm.

## 2026-09-17 late: stop building the container on this Mac

- **Decision:** Do not build the ingest image in the shared colima VM again. Build it on a GitHub Actions runner instead, in the new `image` job in `.github/workflows/audit.yml`, with QEMU for ARM64.
- **Why:** The build was started with a 768 MB memory cap and two of four CPUs, on a VM with about 1.4 GB free and no swap. Eight minutes in, with apt unpacking ffmpeg's dependencies, the other project's `datahub-gms` container was killed with exit 137, which is the out of memory killer. The build was stopped and their container was started again; it came back healthy. The memory cap did not prevent this, because the page cache a build fills is not charged to the build's cgroup.

  This is the risk the Sep 17 IRIS entry described, arriving from a smaller build than the one that entry was about.
- **Cost:** The container build is not verified end to end on this machine. What did get verified before it was stopped: the pinned base image digest resolves and pulls, the platform is arm64, and the apt step reaches unpacking Debian's ffmpeg packages. What is not verified: the pip install from hashes, the flashmap install, the entrypoint running inside the image. That answer now comes from CI, on a runner where a build cannot hurt anybody else.

## 2026-09-17 late: anchor the AWS status lock, and test both locks

- **Decision:** Change the guard's pattern from `AWS Paid plan:[[:space:]]*confirmed` to the same thing anchored at the start of a line, and add `pipeline/tests/test_aws_guard.py`.
- **Why:** The row in docs/STATUS.md that tells the operator to add that line contains the line, in backticks. An unanchored grep matched it, so the document lock had been open since the day it was written and only `CHECKPOINT_D` was holding. Nothing was deployed and no AWS call was ever made, but that was one typo away rather than by design. The anchored pattern is stricter, not looser: a document that talks about the line is no longer a document that says it.
- **Cost:** The operator has to put the line at the start of a line of its own, which the refusal text now says. Sixteen tests, run against a copy of the real script in a temporary directory so the real STATUS.md is never touched, and every one of them with the credential files pointed at /dev/null because this machine has an AWS CLI and credentials on it.

## 2026-09-17 late: moto and boto3 in the development venv

- **Decision:** Add `moto==5.2.3` and `boto3==1.43.97` to `.venv`, and install them in CI's new infra job.
- **Why:** The ingest container's rules are worth testing end to end, and moto is a real S3, DynamoDB and SSM in the test process, so the test drives the actual boto3 calls rather than a mock of them. boto3 is a container dependency anyway and is already in the hash pinned requirements.
- **Cost:** Two more packages in a venv other lanes share, both additive. The same job also installs `aws-cdk-lib`, which CI never had, so `pipeline/tests/test_infra.py` has been skipping itself there since it was written.

## 2026-09-17, night: the real clip set and the credits

- **Decision:** Rescreen the four Theora titles with a merge, rather than running
  the whole pool again.
  **Why:** the whole pool run was already going when this lane picked the work
  up. It ran for two hours and fourteen minutes and wrote nothing: it was killed
  near the end with its output still in the buffer, so there was no log either.
  Four titles take six minutes. `eval/screen.py --only` now screens the named
  titles, replaces their rows and leaves every other row as the run that made it
  wrote it, recording the re-run in a `rescreens` block so a merged file never
  reads as one sweep.
  **Cost:** a merge path and four tests, each seen to fail. Per clip lines are
  flushed now, so the next long run leaves something to read.

- **Decision:** A title joins the labelling pool only when every candidate list
  has analysed it, not when any one of them has.
  **Why:** the pool's negative half is time no detector flagged. Sixteen calm
  clips arrived after the two ffmpeg based baselines had run, so a rescreen was
  about to put their time into that half with only flashmap having looked at it,
  which would have handed flashmap free false positives on windows nobody
  measured.
  **Cost:** those sixteen titles are out of the pool until the baselines run on
  them. The skip reason names which lists never ran, per title.

- **Decision:** Generate NOTICE and the app's credits screen from
  media/LICENSES.csv, rather than keeping two lists by hand.
  **Why:** the conditions that are not the licence text are the ones that get
  lost: the Blender logo exclusion, the Tears of Steel credit scroll, the DVIDS
  non-endorsement notice, the NASA credit line, share alike. Two hand-kept lists
  drift, and the one that drifts is the one nobody is reading.
  **Cost:** `eval/attribution.py --check` in the test suite, and a small table of
  eight titles whose names no page gives us. A row that is neither a Commons file
  nor in that table fails rather than being named after its file.

- **Decision:** Write the credits screen but do not wire it into navigation.
  **Why:** the screens around it belong to another lane and were being edited at
  the time. The screen is complete, tested, and its frame is in the app's own
  flashmap run, which passes with it in.
  **Cost:** nothing navigates there yet, so a CC BY clip is credited in NOTICE
  and not yet anywhere a person watching can see. The file says so at the top
  and gives the one line that wires it.

- **Decision:** The mutation gate mutates a copy of the tree, never the working
  tree.
  **Why:** flashmap runs as a subprocess of a long ingest on this machine and the
  app's jest suite runs in another session, so an edit to the real tree, even for
  thirty seconds, could hand somebody else a wrong answer. It also means no
  restore step can destroy unstaged work, which is why there is no `git checkout`
  anywhere in `eval/mutate_gate.py`.
  **Cost:** flashmap is installed into the virtual environment as an editable
  package, so `import flashmap` reaches the original source whatever the working
  directory is. Every mutation runs a canary that resolves the module the way the
  test runner will and looks for the mutated text in it, and a mutation whose
  canary fails is recorded as survived rather than killed.

- **Decision:** The mutation gate's canary writes its values into the test file
  rather than reading them from the environment.
  **Why:** the first version read `process.env`, and the second mutation's canary
  was handed the first mutation's needle. jest had cached the transformed canary
  with the environment values baked in, because the file itself had not changed.
  A harness that reads its own inputs out of a cache can say anything.
  **Cost:** the canary file is rewritten per mutation, which is a few
  milliseconds and makes the cache key move with it.

- **Decision:** A mutation the gate calls equivalent still counts as a survivor
  in the kill rate.
  **Why:** the unsigned check in flashMap.ts is guarded three times over, so
  removing the first guard changes the diagnostic detail and nothing else. It
  would be easy to exclude that from the denominator and publish a higher number.
  Rounding a number up for a good reason is still rounding it up.
  **Cost:** the published kill rate is lower than it could be made to look, and
  `results/mutation.json` carries the reason next to the mutant so a reader can
  check the claim.

- **Decision:** The scheduler property tests drive the app's TypeScript through a
  node process rather than a Python model of it.
  **Why:** hypothesis is Python and the scheduler that GATE 1 measures is
  TypeScript. A Python reimplementation would agree with itself and prove
  nothing, which is the same mistake as measuring a scheduler against its own
  clock.
  **Cost:** `make properties` needs node and the app's tsc. Without them the
  tests skip and say why, and the CI job that owns them sets
  `CALM_FRAMES_REQUIRE_NODE=1` so a skip there is a failure.

- **Decision:** `flashmap verify` now checks the segment list.
  **Why:** the fuzz corpus found that a correctly signed map whose segments ended
  before they started, or were written as strings, or were not a list at all,
  verified cleanly. The app's reader and the pipeline's loader both refuse those
  maps, so the tool a studio runs on its own work was the only one calling them
  fine, and a studio has no second check behind them.
  **Cost:** a map with a segment that makes no sense now fails verify. Nothing in
  the pool produces one, and the guard has two mutations in the gate.

- **Decision:** The playback fuzzing run reports what it could not do rather than
  leaving it out.
  **Why:** the run cannot change playbackRate, because nothing a remote can press
  changes it and the app does not change it itself, and it cannot force the app
  into the background, because the only key that reaches the device shell is the
  one the keepalive uses to stop the device backgrounding the app by itself. A
  chaos run that quietly dropped both would read as covering more than it does.
  **Cost:** `results/chaos_vvd.json` names both, and rate changes are exercised
  against the real scheduler in `eval/property_scheduler_test.py` instead.

## 2026-09-18: the recovery pass, three findings

- **Decision:** `waiting` now stops the media clock, beside `pause`, `ended` and
  `stalled`, in `app/src/calmframes/useCoverHarness.ts`.
  **Why:** `waiting` is the event a player fires when it runs out of data, and it
  is the common one. `stalled` only arrives after the fetch has been quiet for
  seconds, and some players never send it. The clock therefore kept running
  through every buffer, and the estimate came out the far side ahead of the
  playhead by the length of the buffer. Measured on the real hook: a four second
  buffer left the clock 4,000 ms ahead. The picture was covered throughout,
  because `waiting` was already an uncertain event, so this is not a hole in the
  cover. It is a hole in every number taken off that clock, which is the drift
  and the cover lead that GATE 1 reports.
  **Cost:** one line in the event handler, mirrored into `hook/`. The new test in
  `app/test/calmframes/coverHarness.test.tsx` was seen red at 4,000 ms against a
  1,000 ms baseline before the fix and green after.

- **Decision:** the property harness no longer invents a position report during a
  stall, in `eval/property_scheduler_runner.mjs`.
  **Why:** `test_the_estimate_matches_the_player_when_nothing_drifts` was failing
  on main, out by 75 ms against a 25 ms bound. The counterexample was a seek that
  lands inside a stall. The harness answered that seek with `setRunning(true)` and
  a synthetic timeupdate, which contradicts the rule written twelve lines below it
  in the same file: a stalled player fires no timeupdate. A seek does carry the
  new position, so the clock still learns it, but the player stays stalled. With
  that corrected the estimate error is 0.00 ms across every case probed, not
  merely under the bound, which is what the test's own docstring always claimed.
  **Cost:** the harness models one more thing about real players. Nothing in the
  app changed for this one.

- **Decision:** the README says the `unlabeled` row is our own marker clips.
  **Why:** the pool count moved from 36 to 38 when the sweep finished, and both
  new files are marker clips the timing harness plays against itself. Left alone,
  "38 clips in the pool" reads as 38 pieces of screened footage. It is 35.
  **Cost:** one sentence, and the headline number stays 38 because that is what
  the results file counts.

## 2026-09-17 late: a pass that proves nothing gets a name of its own

- **Decision:** a title verify passes with no flagged segment is recorded as
  **`no flagged segments`**, spelled exactly that way, in `pipeline/verify.py` as
  `OUTCOME_NO_FLAGGED_SEGMENTS`. The other three outcomes are `cover proven
  drawn`, `cover not proven` and `failed`. They live on `VerifyReport.outcome`,
  in the written report, in the catalog entry under `notes.verify_outcome`, and
  in the four counts in `results/verify_pool.json`.
  **Why:** `cover_actually_drawn` sat behind `if sampled and still.exists()`, so
  a title with nothing to hide never ran it and still collected 38 passing
  checks, reading exactly like a title whose cover had been measured on its
  rendition. 14 of the 21 verified titles were in that state and the single word
  "verified" covered both. Finding nothing over the thresholds is a real result
  and for cloud and sunset footage it is the right one. It is not evidence that
  any cover works.
  **Cost:** one more check per preset, `cover_proof:{preset}`, and a fourth
  outcome kept for reports written before that check existed. The count of those
  is 0 today and it is published rather than folded into a neighbour.

- **Decision:** the new outcome does not become the catalog `status`. `status`
  stays `verified` or `failed` and `notes.verify_outcome` carries which kind of
  pass it was.
  **Why:** `CatalogEntry.kid_mode_visible` in `pipeline/catalog.py` is
  `verified and status == STATUS_VERIFIED`, so a fourth status value would drop
  all 14 calm titles out of `kid_mode_titles` and out of the shelf. A title with
  no flagged segment is safe to play: hiding it would be a worse answer than
  publishing it, and the problem was never that those titles play, it was that
  they were counted as proof. `pipeline/catalog.py` belongs to another lane this
  session, so the split was made where this lane owns the code.
  **Cost:** two fields to read instead of one. If the catalog lane ever wants the
  outcome in `status`, `kid_mode_visible` has to learn the new value in the same
  commit.

- **Decision:** the counts are published from `results/verify_pool.json`, written
  by `python -m pipeline.verify --workdir <dir> --pool-summary <path>`.
  **Why:** the README said the pipeline catalog was local state and had no file
  in `results/`, so no title count could be published at all and the only one in
  circulation, "21 titles verified", was hand typed in docs/STATUS.md. The four
  counts add up by construction and `adds_up` fails if a title falls out of every
  one of them or an outcome is added and left unpublished.
  **Cost:** the file is a digest of a work directory that is not in the
  repository, the same arrangement as `results/realclips_status.json`. It is
  regenerated by the one command above, and the title directories that have no
  verdict are listed by name and count rather than left out.

## 2026-09-18: family profiles, and what stops one of them being weaker

- **Decision:** a profile is never the settings that run. `effectiveSettings`
  in `app/src/calmframes/profiles.ts` takes the stricter of the household floor
  and the kid's own choice on every axis, and the guard is handed that.
  **Why:** four kids means four chances to leave one gentler than the house
  rule, and the obvious shape, where a profile replaces the household setting,
  makes that the default rather than the accident. Taking the stricter of the
  two means the worst a profile can do is agree with the floor. Under the floor
  sits WCAG itself, because every preset keeps the WCAG map and
  `coverOptionsFor` already floors the guard band and the minimum cover at the
  WCAG defaults, so there is no arrangement of four profiles that hides less
  than WCAG asks.
  **Cost:** a kid cannot be gentler than the house, which is the point, but it
  also means a parent lowering one kid sees nothing change until they lower the
  floor. The parent area says so in that case rather than leaving them to
  wonder, in `describeFloorEffect`. The strictness order is written down rather
  than derived, so a new preset has to say where it sits, and
  `profiles.test.ts` checks that claim against what the presets actually do:
  anything ranked stricter has to keep the gentler one's maps and hold a guard
  band and a minimum cover at least as long.

- **Decision:** one PIN for the household, not one per profile, and the profile
  picker on the shelf is not a lock.
  **Why:** the thing behind the PIN is the same settings whichever kid is
  watching, so a PIN per kid would be four locks protecting one room, and four
  chances to leave one unset. A kid switching to another kid's profile can only
  ever change which shelf they see, never what is hidden, because every profile
  is floored the same way. The parent area asks once and stays open while a
  parent moves between kids.
  **Cost:** nothing stops an older child watching under a younger one's
  profile. That gets them more hidden, not less, so it fails safe.

- **Decision:** hide logs are kept per profile, keyed by profile id.
  **Why:** the parent area's record is the only evidence a household gets that
  the thing they set up is doing anything, and a single list mixing four kids
  cannot answer the question a parent actually asks, which is what happened to
  this one. Keying by id rather than by name keeps a kid their record through a
  rename.
  **Cost:** the player still cannot post into it. Carrying a hide back from the
  player screen to kid mode needs a store the two screens share, which is not
  built, so every profile's log is empty in the running app and the parent area
  says nothing has been hidden for that kid rather than inventing entries. The
  shape is right and tested, and the one thing missing is the store.

- **Decision:** a profile is named from a fixed list rather than typed.
  **Why:** naming a kid needs a text field, and a text field on a television
  needs an on-screen keyboard that this app does not have. The model renames
  and the parent area does not, so profiles are Kid, Kid 2 and so on until
  there is a keyboard.
  **Cost:** four profiles called Kid read worse than four names. `renameProfile`
  is there and tested, so the screen is the only piece missing.

## 2026-09-18: the map registry, and why signing it is not enough on its own

- **Decision:** the index of published maps is signed, **and** every entry is
  checked against the map it points at, **and** the map has to be the one the
  entry named, by its Ed25519 signature. `pipeline/registry.py` builds it,
  `app/src/calmframes/mapRegistry.ts` reads it, docs/SIDECAR_SPEC.md holds the
  format.
  **Why:** the threat is somebody serving a modified index. Ask what they can do
  with only one of the two halves in place and the answer is different each
  time. With the index signed and the entries not rechecked, an attacker who can
  serve the maps as well as the index, which is the ordinary case because both
  come off the same origin, swaps a validly signed older map of the same file,
  one with fewer segments, in at the URL the index names. The index is untouched
  and still verifies, and the picture comes back. With the entries rechecked and
  the index unsigned, they write their own index instead: point a file at no map
  at all, or at an older map they kept, and every check we run passes because
  each map is a real map. So both, plus the entry carrying the map's signature,
  which is what ties one to the other. The one attack neither closes is replaying
  yesterday's set whole, so the index has a staleness bound of its own, thirty
  days, shorter than a map's ninety because it is rebuilt on every publish.
  **Cost:** one more fetch and one more signature check before a title can play,
  both off the frame path, and a published set now has a file that has to be
  rebuilt whenever a map is added.

- **Decision:** the builder refuses to index a map it cannot verify against the
  public key it was given, and refuses two maps claiming the same file and
  profile, and either refusal stops the whole build.
  **Why:** an index entry is a claim that a checked map exists. An index built
  from maps nobody checked is that claim made at scale, and a build that quietly
  skipped the maps it could not read would publish a shelf with holes in it that
  nobody would see. Failing the build is loud, and nothing is written.
  **Cost:** one unreadable map in a directory blocks the index for all of them,
  which is the direction we want to fail in.

- **Decision:** the index's own date is the newest date of the maps it indexes,
  not the clock, and paths in it are relative to the index.
  **Why:** the file has to be reproducible, so a mirror can be compared rather
  than trusted. With the clock in it, two builds of the same directory differ,
  and there is nothing left to compare. Ed25519 signatures are deterministic, so
  with the timestamp and the paths pinned the bytes are too.
  **Cost:** an index of maps that never change never changes its date either,
  which is right, and an empty set has no date to take, so that one case has to
  be given one.

- **Decision:** the lookup is not in the hook package yet.
  **Why:** `hook/src/engine/*` is generated from `app/src/calmframes` by
  `hook/tools/sync.mjs` and a test enforces it byte for byte. Adding the file to
  that mirror means editing the sync script's list and running it, which belongs
  to whoever owns the mirror, not to this lane.
  **Cost:** an app that installs `@calm-frames/flash-guard` today gets the guard
  and not the registry lookup. The change is two lines and a sync run.

## 2026-09-18: a chime before the hide, and what counts as the hide that follows it

- **Decision:** a soft chime sounds 2,000 ms of media time before the cover
  goes on, on by default, with one switch for the household in the parent area.
  **Why:** the cover arriving unannounced is the thing about this app that
  startles people, and the countdown card only helps somebody who is looking at
  the screen. Two seconds is fixed by the two numbers either side of it: the
  countdown card appears at three seconds, so a chime earlier than that would
  sound before there was anything on screen to explain it, and the guard band
  is 500 ms, so anything under about a second would land inside the widened
  interval rather than ahead of it. One switch rather than one per kid, because
  it is about the room rather than about who is watching, and a chime that is
  on for one child and off for another is a chime nobody learns to read.
  **Cost:** one more thing that can be wrong in the dark. It is the reason the
  property below exists.

- **Decision:** what "a cover following it" means when the playhead is seeked
  away between the chime and the cover. The cue is discharged by the next time
  the picture goes dark, whatever raised it: the interval the chime announced,
  or the fail safe cover that any seek raises before it moves the playhead. It
  does not have to be the announced interval's own cover.
  **Why:** every way of moving the playhead in this app covers first.
  `seekSafety.ts` covers before it seeks into an interval, and
  `useCoverHarness.ts` has `seeking` in its uncertain set, so the cover goes on
  at the start of every seek wherever it lands and is held until playback is
  confirmed outside an interval. So a person who hears the chime and then seeks
  still gets chime, then dark, which is what the chime promised. Insisting on
  the announced interval would make the app worse in both directions: after the
  seek it would either chime again over a cover that is already on, which is a
  warning after the event, or mark the cue broken and stay silent at the next
  interval.
  **Cost:** the property leans on the seek funnel covering first. That is not
  assumed here: `app/test/calmframes/chimeCue.test.tsx` scripts the seek the
  way the funnel really answers one, and the funnel's own guard has three
  mutations in the gate already. If the funnel ever stopped covering first,
  this property would be discharged by a cover that did not happen, so the two
  belong together.

- **Decision:** the cue counts its own broken promises in `unmatched`, rather
  than throwing.
  **Why:** the property is "a chime never sounds without a cover following it",
  and a property needs to be measurable to be worth claiming. `unmatched` is
  the number of times a chime sounded and the playhead then ran past the part
  it announced with the picture never going dark. It is zero, and the test
  drives a timeline that does leave a cue unmatched, so the zero elsewhere is a
  measurement rather than a constant.
  **Cost:** the counter is dead weight in the running app. It is what makes the
  mutation gate able to tell a kept promise from a broken one.

- **Decision:** the sound itself is a port, and the default is silence.
  **Why:** there is no chime asset in the package, and the one audio path Vega
  offers is the same w3cmedia player the title is already using, which is one
  per process. Writing device audio code that cannot be run here and might
  break the single player rule would be worse than an honest gap. Everything
  that decides whether a chime is due is real, tested and mutation checked.
  **Cost:** nothing is audible yet. Two things are missing and both are outside
  this lane: a short sound in `app/assets`, with its licence line, and one call
  to `useChimeCue` in `app/src/screens/PlayerScreen.tsx` beside the existing
  `useFlashGuard` call, with `chimeEnabled` carried through the guarded route
  parameters in `app/src/components/navigation/types.tsx`.

## 2026-09-17, Feature D: the report page

- **Decision:** the report is one HTML file with every picture inlined as a
  PNG data URI, and no SVG.
  **Why:** self contained had to mean a file somebody can mail. Inline SVG
  would also have been self contained, but the pictures have to be run through
  flashmap, and flashmap measures pixels. Drawing an SVG for the page and
  rasterising a twin of it for the check would mean the bytes that were
  measured were not the bytes that shipped, which is the kind of gap this
  project keeps finding in other people's work. A PNG is measured exactly as
  it is read.
  **Cost:** a PNG writer had to be written, because flashmap's three
  dependencies do not include an imaging library and adding one to an analyzer
  studios install for one job is a poor trade for thirty lines of format.
  `flashmap/src/flashmap/pngout.py` writes the plainest truecolour PNG there
  is.

- **Decision:** no text and no tick marks inside any picture. The labels and
  the time axis are HTML around them.
  **Why:** three reasons that all point the same way. Text in a raster is not
  readable by a screen reader and does not scale. Hairlines for ticks are the
  beginning of the pattern the drawing is trying not to be. And a picture made
  only of solid blocks is one whose colours can be asserted, which is how
  `test_a_lane_holds_no_colour_but_the_palette` can say no frame of the film
  ever leaked in.

- **Decision:** a lane draws at most five bars, and when a title has more
  spans than that the closest neighbours are joined until five are left.
  **Why:** the cap is not ours. It is the regular pattern criterion in the
  broadcast profile, from ITU-R BT.1702-3 Attachment 1 to Annex 1, already
  quoted in docs/SPEC_SOURCES.md section 8: more than five light and dark
  pairs. Five bars is at most five pairs, so a lane cannot reach the
  criterion whatever its area, and no number had to be invented or
  re-derived. The first version collapsed everything over the cap into one
  bar from the first span to the last, which was safe and useless: Big Buck
  Bunny has fifty three spans between 19 s and 590 s of a ten minute film, and
  it drew one bar across almost the whole lane. Joining the closest pairs
  instead keeps the bars where the flashes are.
  **Cost:** a bar now covers calm time as well as flagged time. Every lane
  that was drawn coarser than the numbers prints a line saying so, and the
  tables underneath carry every span to the millisecond.

- **Decision:** every picture in the report is checked under both the wcag and
  the broadcast profile, with a negative control for each.
  **Why:** eval/brand_assets_check.py learned not to invent a worst case that
  cannot happen, and that lesson holds here: a lane is a static PNG in a
  static page, it never follows another picture, so it is analysed alone and
  held for two seconds and nothing is cut against anything. But a still cannot
  flash, so the WCAG profile passes any drawing this module could make. It was
  checked: a full frame of forty stripe pairs passes `--profile wcag` and
  fails `--profile broadcast`. Checking only against wcag would have been a
  check that cannot fail.
  **Cost:** two negative controls to maintain instead of one, and a note in
  the test file saying where the picture check stops. The padded still the
  check builds puts a lane in about a fourteenth of the frame, which is under
  the pattern rule's area limit, so the image check is not what keeps the
  timeline safe. The block cap is, and its tests are the ones that go red when
  it comes off.

- **Decision:** a preset whose maps were not all supplied is reported as a
  lower bound, by name, and never as a measured figure.
  **Why:** the Broadcast and Extra cautious presets union the wcag and
  broadcast maps. Given only a wcag map, the honest answer is "at least this
  much", and the row says which map is missing.
  **Cost:** a report made from one map has two rows that are floors rather
  than figures. `python -m pipeline.upload_server` always analyses both, so
  the page a judge uses has neither.

- **Decision:** the upload page checks the two AWS locks itself rather than
  calling scripts/aws_guard.sh.
  **Why:** the shell guard's only actions are deploy, destroy, diff and an ECR
  push. There is no way to ask it a question without picking one of those, and
  a server that has to run a real CDK action to find out whether it is allowed
  to is not a lock. So the check is a second copy.
  **Cost:** a second copy of a lock is a second chance to make the mistake
  that had one of these open for a day, where an unanchored match read the row
  in docs/STATUS.md that describes the line as the line itself.
  pipeline/tests/test_upload_server.py holds the two together: it pulls
  STATUS_PATTERN out of the shell script and runs the same five strings
  through grep and through this module, and fails if they disagree.

- **Decision:** the uploaded clip is deleted before the response is written,
  not after.
  **Why:** it was written the other way first and the test caught it as a
  race: a caller holding the report could still find the clip on disk. An
  uploaded clip may well be a hazard file, which is the reason somebody
  uploads it.
  **Cost:** none. The report is built in memory either way.

## 2026-09-18: the regular pattern rule, and the judgement that had to fail safe

- **Decision:** the smooth flow exemption in ITU-R BT.1702-3 Attachment 1 to Annex 1
  is applied only when the flow is unambiguous, an uncertain motion class takes
  the 25% area rather than the 40% one, and every exemption that is applied is
  written into the map as its own interval in `pattern_exemptions`.
  **Why:** the attachment's two area limits turn on a motion class, and its
  exemption turns one off entirely. Of the four calls the detector can make,
  three cost a few covered seconds when they are wrong and one hides a hazard
  from a child. So the exemption needs a full history of frame to frame
  comparisons, all one way, none still, none ambiguous, none under the match
  floor, and anything short of that is `uncertain`. Uncertain never reaches the
  exemption and never gets the wider area. An exemption is never a silence: it
  is an interval in the map with the stripe count and the area that were let
  through, so a reviewer sees it.
  **Cost:** measured, not guessed. On the pattern conformance suite, of 40 clips
  drawn flowing smoothly one way, which the attachment exempts outright, 15 were
  exempted and 25 were hidden. The fine ones drift less than a pixel of the
  analysis grid per frame, or far enough to alias, and neither is a flow this
  detector will swear to. A pattern between the two area limits is also hidden
  for the first few frames while the history fills: 23 windows across the suite.
  Both are in `results/conformance_pattern.json` under
  `where_the_false_positives_are` and `smooth_flow_exemption`.

- **Decision:** a pattern segment is its own kind. It sits in the map's
  `segments` array beside the flash segments, in time order, carrying
  `reason: "pattern"`, none of a flash segment's fields, and
  `is_a_wcag_finding: false`. `summary` carries `flash_pass` and `pattern_pass`
  separately.
  **Why:** WCAG 2.2 SC 2.3.1 does not cover regular patterns at all, so a
  pattern hide must never move a WCAG verdict, and Attachment 1 is informative
  and says its criteria are what some administrations use, so the source has to
  travel with the finding. Putting it in the same array is what lets a player,
  the pipeline adapter and verify consume it with no change at all: an unknown
  reason already falls through to the strictest handling.
  **Cost:** `summary.pass` for the broadcast profile now includes the pattern
  rule, so a title with a big regular pattern fails that profile where it passed
  before. `flash_pass` is the field to read for the WCAG story.

- **Decision:** the stripe count gate lives in exactly one place,
  `PatternTracker.min_bars`, and the limit check downstream is a plain area
  comparison.
  **Why:** it was in two, and neither could be tested. Dropping `min_bars` by a
  pair left every test green, because the downstream comparison went on holding
  the line, and loosening the downstream comparison left every test green
  because `min_bars` did. Two guards that cover for each other are one guard
  nobody can break on purpose.
  **Cost:** the reader has to know that a scanline under the gate contributes no
  pixels, so a picture with too few stripes has an area of zero. There is a test
  for that, `test_a_picture_under_the_stripe_gate_has_no_pattern_area_at_all`.

- **Decision:** `detect_picture` crops a bar only when the opposite edge has one
  too and there is no dark line inside the picture.
  **Why:** the verifier found a whole frame black to peak white six pair grating
  passing the broadcast profile. Its outermost bar is dark, black sits under
  `max_bar_luminance` on every sampled frame, and the detector cropped that bar
  as a pillarbox. Eleven bars were left, which is five pairs, which is not more
  than five.
  **Cost:** both checks only ever crop less, which raises the stripe count and
  lowers every area fraction, so it is the cautious direction for the flash
  rules and their published precision and recall. That had to be checked rather
  than assumed: the whole spine of the committed flash design plus 250 cross
  product rows, 402 clips, went through the old detector and the new one on the
  frames the generator drew, and the picture rectangle changed on none of them.

## 2026-09-18: the hide log producer, and a module-level store rather than a context

- **Decision:** the player writes one entry per cover into a module-level
  store, `app/src/calmframes/hideLogStore.ts`, and the kid mode route reads it
  through `useSyncExternalStore`. Not a context, not Redux, not the navigation
  parameters.
  **Why:** the guard has always reported every cover through `onHide` and the
  parent area has always been able to draw a log. Nothing joined them, so a
  household read "Nothing has been hidden yet" however much had been hidden,
  which is the one thing in the parent area that could quietly say the app was
  doing nothing. The join has to outlive the player, because the player is torn
  down on the way back to the shelf, so it cannot be either screen's state. Of
  the three ways to make it outlive them: a context has to be provided above
  both routes, which means editing the navigator that the five sample screens
  share; the sample's Redux store is the sample's, and a slice there would put
  what a child watched inside the app's general state; a module lives as long
  as the JavaScript context and is reachable from the guard's callback, which
  is not a component. The writer being a callback rather than a component is
  what decided it.
  **Cost:** a module-level store is global, so a test that writes has to reset
  it, and `resetHideLogs` exists for that. It is memory, so it empties when the
  app is killed, the same as the PIN and the room setting, and that is written
  down in docs/STATUS.md rather than hidden. Writing it to /data is a separate
  job.

- **Decision:** the stored entry carries the profile, the preset and the end of
  the cover, on top of what the engine's `HideLogEntry` already carries.
  **Why:** the engine's entry is mirrored into the hook package and knows about
  a title and a position, not about this app's families. Whose sitting it was
  and which rule set the schedule was built under are the app's facts, so they
  are added in the app's store as `HouseholdHideEntry`. The preset is recorded
  as it was at the time of the cover, so a household that tightens the setting
  later still reads the old lines truthfully.
  **Cost:** two shapes for one thing. The parent area still prints the engine's
  wording, so the profile shows only as which kid's log the line is in and the
  preset shows nowhere yet. It is in the record and not on the screen, which is
  worth saying rather than implying it is displayed.

- **Decision:** a cover the player cannot attribute is recorded under
  `unattributed` rather than dropped or filed under the active kid.
  **Why:** kid mode always names the profile in the guarded parameters. Anything
  else reaching a guarded player did not come through the shelf, and a cover it
  caused still happened. Filing it under whoever was last chosen would put one
  kid's sitting in another kid's record, and dropping it would make the log
  quietly incomplete. It appears under Everyone and in no kid's own log.
  **Cost:** a household can see a line in the everyone view that is in nobody's
  own view, which reads as odd until you know why.

## 2026-09-18: the registry is asked first, and what a missing entry does that a tampered one does not

- **Decision:** the catalog goes through `app/src/calmframes/mapSource.ts`
  before it reaches `checkTitle`. For every title and every profile the preset
  asks for, `lookupMap` is asked first, by the file's SHA-256, and only then
  does the bundled or catalog map get a look in.
  **Why:** the registry has been right since it was written and nothing called
  it, so it was a feature the app had rather than one it used. Of the three
  sources a map can come from, the index is the only one that can say a map has
  been replaced since the catalog was written, so it is the one to ask first.
  Everything it hands back still goes through `verifyFlashMap` on the shelf and
  again in the player, so a map reached through the index is held to every rule
  a map is held to.
  **Cost:** a title now waits on a network answer before it can be listed, and
  while it waits it is pending rather than verified, which means the shelf is
  empty for as long as the index takes. Listing it on the strength of the
  bundled map and refusing it a moment later would leave it playable in
  between, so the wait is the safe direction. Nothing sets `registryUrl` yet,
  because no index has been published: the pipeline builds one and nothing has
  been deployed, so the shipping default is still the bundled map and the
  lookup runs only where a URL is configured. That is one prop, and until it is
  set the registry is wired rather than in use.

- **Decision:** a missing entry falls through to the map the app already holds.
  A tampered one does not, and takes the title off the shelf.
  **Why:** they are different facts. An index that verified and lists no map
  for this file, or no index at all, is the normal state of a file nobody has
  published and is also what a device in flight mode sees. Blocking there would
  break the bundled title, which is the whole offline story, and the fallback
  is a signed map bound to the same file hash and read by the same reader, so
  nothing is being trusted that was not already. With no such map either, the
  title is pending, kid mode never lists a pending title and the player refuses
  it, so the picture stays hidden exactly as a missing map has always left it.
  An index that did not check out is a different thing: unsigned, signed by a
  key we do not hold, edited after signing, stale past the thirty day bound,
  pointing outside itself, or naming a map other than the one that came back.
  That is somebody serving us something, and the answer is to stop rather than
  to keep playing off a different map. The two cases are one list,
  `FALL_THROUGH_REFUSALS`, with exactly two entries, so there is one place to
  read which is which.
  **Cost:** a denial of service. Whoever can serve a broken index can stop a
  title playing even though a perfectly good bundled map is sitting there. That
  is the direction to fail in, and it is worth saying out loud rather than
  discovering on a judge's device.

- **Decision:** the resolver hands on the exact bytes the lookup verified,
  through a fetch that reads each URL once and keeps what it read.
  **Why:** `lookupMap` returns a parsed map, not its text, and the guard needs
  text. Fetching the map again to get the text would be a second answer to the
  same question, from a server free to give a different one. The same read-once
  fetch means the index is read once for a whole catalog rather than once per
  title and per profile.
  **Cost:** one small wrapper that has to stay honest. It also has a branch
  that cannot be reached without something replacing the reader underneath, and
  that branch blocks rather than falls through.

- **Decision:** which source served each map is logged as one `console.info`
  line and one beacon, not shown on a screen.
  **Why:** a reader has to be able to tell registry from bundled from catalog
  when a title behaves oddly, and the app has no existing timing event kind for
  this. `logTimingEvent` takes a fixed union of kinds and adding one would edit
  a file the hook package mirrors.
  **Cost:** release builds strip console logging, so on a release build the
  beacon is the only copy and it needs the harness listening. The source is
  also returned in `ResolvedMaps.sources` for anything that wants to draw it.

- **Decision:** the wiring is in the shelf and in a new app-only module, not in
  `useFlashGuard`.
  **Why:** `useFlashGuard` is one of the twenty files `hook/tools/sync.mjs`
  mirrors into the published package, and `hookMirror.test.ts` compares them
  byte for byte, so editing the engine turns the suite red until the sync
  script is run, and this lane does not run it. The shelf is also where the
  catalog is resolved and where docs/STATUS.md section 4c said the call
  belonged. The engine stays what it says it is: a guard that knows nothing
  about this app's catalog.
  **Cost:** an app that installs the hook package gets the guard without the
  registry lookup. `lookupMap` is in the package and callable, so a host app
  can do what the shelf does, and this is a seam rather than a wall.

## 2026-09-18: The picker's answer comes off the chip, so choosing moves nothing

- **Decision:** the chosen profile is named in a sentence under the row, not in
  brackets on the chip. The chip carries the name and nothing else.
  **Why:** the chosen chip used to read "Robin (watching)", so it was wider
  than it had been a moment earlier and every chip after it slid along the row.
  A row of controls moving sideways when a child presses one is motion, and kid
  mode has none. The component's own header already claimed nothing moves when
  focus moves, which was true and beside the point: it was choosing that moved
  things, not focusing. Reserving the space on every chip was the other way out
  and it cannot be done here without a magic width, because react-test-renderer
  does no layout and a width nothing can measure is a width no test can hold.
  Off the chip the geometry is fixed by construction, and the guard is on the
  cause rather than the effect: every chip draws the same text whoever is
  chosen. Put the word back and that test goes red, which it was seen to do.
  **Cost:** one more line of vertical space on the shelf, and the answer is a
  short read away from the chip rather than on it. The chip still carries the
  state for a screen reader, in its label and in `accessibilityState.checked`.

- **Decision:** the row is a radio group and says so, and its title is a header.
  **Why:** five controls where exactly one is true is a radio group whether or
  not it is built from radio buttons. Without the role a screen reader read the
  row as five unrelated buttons with no question attached to them. The chips
  also carried `selected` alone, and `checked` is what a radio carries.
  **Cost:** the preset, television and seat rows in the parent area now carry
  `checked` too, for consistency on one screen. `FirstRunScreen.tsx` has three
  more radio groups still on `selected` alone. That file belongs to another
  lane and is left for whoever holds it.

## 2026-09-18: The record says whose it is, where it stops, and what day it is

- **Decision:** every section in the parent area names whose it is, not only
  the record. "How strict for Sam", "The room for Sam", "What was hidden for
  Sam", and "for Everyone" when the household floor is the one open.
  **Why:** the picker scrolls off the top of a television screen quickly. Below
  it, "How strict" looked the same whether it was about to change the floor
  under every kid or one kid's own setting, and those are not the same thing.
  The record already said the name, so the screen was half doing this already.
  A household that has never made a profile reads exactly what it read before,
  and there is a test on that so the bare case cannot quietly acquire a name.
  **Cost:** three headings are longer. On a 1728 unit line at 44 units they fit.

- **Decision:** the summary says where the list stops, and the lines are
  grouped under the day they happened on.
  **Why:** two things the record was not saying. It drew twenty lines, kept two
  hundred, and printed "43 parts" above twenty lines with nothing to explain
  the difference. And a line says the time and nothing else, so "19:30 hid 4
  seconds" could be tonight or last Tuesday. This is the only evidence a
  household ever gets that the thing they set up is working, so it is the last
  place to let a number and the thing under it disagree. The day names are
  spelled out in `copy.ts` rather than taken from the platform, because a date
  that changes with the locale data on the machine is a date no test can hold.
  **Cost:** `describeHideEntry` still prints a bare time, because `hideLog.ts`
  belongs to another lane. The day is above the lines rather than on them,
  which is where a person writing the list by hand would put it anyway.

- **Decision:** the record is body text on the ground, and the totals with it.
  **Why:** the lines were the smallest and dimmest thing on the screen, in the
  same style as the asides beside them. That put the proof below the notes
  about it. They are cream at 36 units now, 7.60 to 1 on teal, and the asides
  stay dim so the two are still told apart. No palette token changed.
  **Cost:** a long record is taller. It was already a scroll.

- **Decision:** a new kid is named apart from the start: Kid, then Kid 2.
  **Why:** "Add a kid" passed an empty name, `cleanName` turned it into "Kid",
  and a second press gave a household two chips reading Kid with no way to tell
  them apart and no keyboard in the parent area to rename either.
  **Cost:** none. `MAX_PROFILE_NAME` is 16 and "Kid 4" is five.

## 2026-09-18: Recommendation on the profile picker having no lock

Not a decision. This is a product call and it belongs to whoever owns the
safety wording, so it is written down rather than taken.

- **What is true today:** any child can press any chip on the shelf. The
  household floor still applies underneath, and WCAG sits under that, so no
  switch can take anybody below either. Per-kid strictness above the floor is
  advisory and a child can shed it by pressing the other kid's name.
- **What that actually costs:** two things, and the second is the worse one.
  A six year old set to Extra cautious who presses the twelve year old's chip
  gets the twelve year old's setting, which the parent chose for a different
  child. And the hide log follows the active profile, so the evening lands in
  the wrong kid's record. A parent reading "nothing has been hidden for Ava
  yet" when Ava watched as Ben is being told something untrue by the one screen
  that exists to tell them the truth, and nothing on it hints that it happened.
- **Recommendation:** do not put the parent PIN on the picker. Extend the rule
  the app already states twice instead. The room can only add hides. A profile
  can only add hides. So a choice a child can make alone can only add hides:
  switching to a profile at least as strict as the one running is free, and
  switching to a laxer one asks for the PIN. `PRESET_STRICTNESS` and
  `roomFieldFraction` already rank the two profiles and are already tested, so
  the comparison is one that exists rather than a new judgement.
- **Why that and not a lock on the whole picker:** a PIN in front of "who is
  watching" takes a grown up to answer a question a child asked, on the one
  screen in this app built for the child. Most switches are sideways or upward
  and would never see the gate. A household where every kid sits at the floor
  would never see it at all.
- **What it costs:** an older sibling cannot get their own shelf back without
  a grown up once a younger one has switched to theirs. That is the direction
  to fail in, and it should be said in words on screen when it happens rather
  than left as a chip that does not respond.
- **Worth doing whichever way this goes:** the hide log store already records
  `profileId` and `profileName` on every entry. The parent area does not yet
  show when the shelf was switched, so a parent cannot see the switch that made
  their record misleading. That is a smaller fix than any lock.

## 2026-09-18: Two findings from this review that were left alone

- **The television and seat chips carry "chosen" as a fill and nothing else.**
  Their accessibility labels say the word, so a screen reader is fine, but a
  person on the sofa has only the colour. That is the same defect the profile
  picker had and it wants the same answer. It is on a different surface from
  the two this pass was asked to review, so it is recorded rather than fixed.
- **Removing a kid has no confirmation.** `Remove Robin` sits one press from
  the picker and takes a profile and its settings with it. A confirmation is
  new behaviour and a new state to record in `ALL_UI_FRAMES`, so it is named
  here for whoever picks it up.
- **One edit outside this lane.** `ProfilePicker` gained a required prop, so
  `KidHomeScreen.tsx` had to pass it. That call site is the only change in the
  file: three lines, no behaviour of its own.

## 2026-09-18: a timeline bar that cannot be a bar, and the page a reader sees

- **Decision:** the report's flash timeline keeps its cap of five bars a lane and
  is now also drawn under the luminance difference that makes a light and dark
  pair at all. The three colours a lane may hold are the app's own COVER for the
  track, SURFACE for a general block and BACKGROUND for a red one. Through
  `color.bt1886_nits`, the curve the broadcast profile measures with, they are
  0.00, 4.45 and 8.47 cd/m2, so the widest step a lane can hold is 8.47 cd/m2
  against the 20 cd/m2 Guideline 1 flash difference that BT.1702-3 Attachment 1
  reuses for its bar to bar condition. That is 11.53 cd/m2 of headroom, and a
  lane spends 42% of the difference. The saffron fill it replaces sat at
  82.20 cd/m2 on a 4.45 cd/m2 ground, a step of 77.75 cd/m2, which is nearly
  four flash differences.
  **Why:** the cap was doing all the work, and it is one number away from being
  wrong: at six blocks a lane can show six pairs, which is the first count the
  attachment can fail. The two limits now fail in different directions, so
  neither has to be right on its own. A bar that cannot reach the bar to bar
  difference is not counted as a bar at any count, at any width and at any area.
  That is asked of `pattern.scan_bars` itself in `TestNoStepInALaneCanBeABar`,
  on a hand built lane of two hundred blocks that `plan_blocks` would never
  draw, and the same scan over a lane sized stripe pattern counts 60 bars, so
  the test is not one that cannot fail.
  **Cost:** contrast, measured rather than felt. Against the track a red block
  is 2.27:1 and a general block 1.75:1, where the saffron fill was 5.81:1 on the
  old lane ground. The ceiling is low by construction: the brightest grey that
  still stays under the flash difference above black is 19.66 cd/m2, which is
  3.39:1, so nothing drawn under this rule can be bright. One alternative was
  measured and not taken: a single fill of SURFACE_FOCUSED at 14.42 cd/m2 is
  3.00:1, which is the 3:1 non-text floor the app's palette is built to, but it
  spends 72% of the difference instead of 42% and leaves the two kinds of block
  nothing but their height to tell them apart. The report's own line is that the
  picture is a picture and the table is the truth, and the table carries every
  span to the millisecond, so the headroom was worth more than the extra three
  quarters of a contrast point. The kinds are told apart by shape before colour
  and the key shows each fill sitting on a piece of track.

- **Decision:** no block reaches the top or bottom edge of its lane, and the
  lane's outline on the page is drawn in a lane colour rather than the page's
  border colour.
  **Why:** both were found by running the new page check, not by thinking about
  it. A red block is drawn in the page's own ground colour, and on a worst case
  page forty spans joined into five wide blocks that ran to the lane's edges, so
  the lane read as the page with a few black notches cut in it. And the lane's
  1 px `var(--border)` outline is 55.18 cd/m2 around a 0.00 cd/m2 track, a step
  of 55 cd/m2: the check counted three bars in every lane on the page and it was
  right to.
  **Cost:** the lane's edge on the page is a dim line now rather than a bright
  one, and one more pixel of each block is track.

- **Decision:** `eval/report_page_check.py` renders the whole report page in
  headless Chrome at 1280 px wide, cuts it into 1280x720 display frames, holds
  each for two seconds and runs the analyzer over it under the `broadcast`
  profile, which is the one that carries the regular pattern rule. It runs in
  the ui-flashmap CI job beside eval/brand_assets_check.py, and it carries its
  own negative control: the same page with a twelve pair stripe pattern in place
  of each lane, which it refuses.
  **Why:** the lanes were checked one picture at a time, padded into an analysis
  frame where a lane is about a fourteenth of the picture, and the test file
  said out loud that the picture check therefore does not cover the stripe
  hazard. A reader does not see a padded lane. A reader sees the page, with the
  lanes at the size the layout gives them and the text around them, and that is
  what a hazard would arrive in.
  **Cost:** about 70 seconds of CI on the ubuntu runner, three browser renders
  and eighteen analyzer runs, and a dependency on Chrome being on the runner.
  The GitHub ubuntu image ships Google Chrome and the script also takes
  Chromium, a `CALM_FRAMES_CHROME` path, or an exit code 2 saying it found
  neither.

- **Decision:** the page's own pattern verdict is printed on every run and is not
  what the check asserts on. What it asserts is the timeline: the pattern rule's
  own bar scanner has to find nothing at all inside a lane, at the size the page
  draws it.
  **Why:** the report page fails the regular pattern rule, and the cause is its
  text. Cream on teal is 160.77 cd/m2 against 8.47 cd/m2, so every glyph edge is
  a Guideline 1 step and a line of text crossed by a scan line is a row of them.
  Nine display frames out of nine hold a pattern finding at 16 to 25 pairs over
  44% to 64% of the frame, against a 25% area limit, and analysing more finely
  sharpens it rather than rescuing it: the same nine frames at analysis widths
  384, 640 and 1280 give 37 to 77, 71 to 152 and 82 to 176 pairs, over as much
  as 93% of the frame. That is not something the
  report can design away: readable text needs 4.5:1, and at an SDR peak of
  200 cd/m2 no pair of colours at that ratio has its difference under 20 cd/m2
  or its darker state above 160 cd/m2, so any page a person can read holds those
  steps at every glyph. BT.1702-3 asks for the guidelines where patterns are
  "clearly discernible" and a paragraph is not a discernible stripe pattern, but
  the attachment puts no number on that and flashmap does not invent one.
  **Cost:** this is the first time anything in this repo has put text in front of
  the pattern rule. app/tools/ui_flashmap.mjs runs `--profile wcag`, which has no
  pattern rule, so the app's own screens have never been asked. The same finding
  is waiting there and in any film with credits or subtitles, and the number the
  pattern rule reports on such a title is a false positive nobody has counted
  yet. The check prints the page's numbers every run so that a change in them is
  visible in the log, and the second half of its negative control is that the
  striped page has to measure more pattern area on the whole page than the real
  one does, which keeps the analyzer run from becoming decoration.

## 2026-09-18: The three findings the design pass left behind, picked up

The 2026-09-18 review recorded three defects on surfaces outside its scope and
left them. These are them, fixed the way it fixed the equivalents rather than a
second way.

- **Decision:** the television and seat chips say which one is chosen, in a
  sentence under the row, and both rows now carry a visible name.
  **Why:** the chips carried chosen as a fill colour and nothing else. Their
  screen reader labels already said the word, so the only reader told nothing
  was the one looking at the screen, on a television, from a sofa. This is the
  same defect the profile picker had, so it gets the picker's answer: the word
  goes under the row, not on the chosen chip, because a word on one chip makes
  that chip wider than it was a moment earlier and slides every chip after it
  along the row, and kid mode has no motion. The sentence is the chip's own
  label plus the state word, "55 inch is chosen", so nobody translates one into
  the other. The two rows got names because two unlabelled rows of numbers
  under one heading left a person working out which was inches and which feet.
  **Cost:** two lines on the parent area's room section and two on the first
  run's room step, and two more headings. Both screens were already scrolls.
  No palette token changed.

- **Decision:** `FirstRunScreen.tsx`'s three lists are labelled radio groups and
  carry `checked` beside `selected`.
  **Why:** the picker's entry above says this file was left for whoever held
  it. Without the role a screen reader read three questions as thirteen loose
  buttons, and `selected` alone is not what a radio carries. The parent area's
  copies of the same two rows got the role at the same time, so the two screens
  a parent meets these chips on read the same way.
  **Cost:** one wrapper view per list. `radiogroup` is not in `FOCUSABLE_ROLES`,
  so the ten foot pass does not measure the wrappers as controls.

- **Decision:** removing a kid asks first, as a `StatusNotice` with two buttons
  in it, in the place the buttons were.
  **Why:** one press took a kid's preset, their room and their record of what
  was hidden, and none of it comes back. The button sits beside the picker a
  parent uses to switch between kids, which is the worst place on the screen
  for a one press delete. It is not a dialog: CLAUDE.md rules out anything that
  blocks events on Vega, there is no browser here for a modal, and `Alert`
  would be a second style of asking on a screen that already has one. The
  wording follows the `design:ux-copy` shape for a destructive confirmation.
  It names the kid rather than saying "are you sure", says what goes and what
  does not, says it cannot be undone, and puts the action in both buttons
  rather than OK and Cancel. Keep is first and takes focus, so a parent who
  pressed Remove by mistake is one press from undoing it rather than one press
  from finishing it. The question is held by profile id rather than as a flag,
  because the picker stays live above it and a question asked about Sam must
  not be answerable about Robin.
  **Cost:** two presses to remove a kid instead of one. A new state,
  `PARENT_REMOVE_KID_FRAME`, which is in `ALL_UI_FRAMES`, in the capture walk
  and in the ten foot pass. It paints no new colour, so the flash run is
  unchanged at 25 screens and transitions.

- **Decision:** the question's tone is `calm`, not `blocked`.
  **Why:** `blocked` means the picture stays hidden and will not play, which is
  not what is happening, and widening that word for one use would make the
  other three notices harder to read. So colour carries none of this and the
  words carry all of it, which is the rule this whole pass exists to enforce.
  **Cost:** the question's border is the same blue as every other calm notice.
  It is still a notice block standing where a row of buttons was, which is not
  a change anybody misses.

- **Every new guard was seen to fail.** The chosen line off the television row
  (`Unable to find an element with testID: parent-area-tv-chosen`), the word
  put back on the chosen chip, the radiogroup role off the room row, `checked`
  dropped back to `selected` alone, Remove removing on the first press
  (`Expected number of calls: 0, Received number of calls: 1`), the question
  held as a flag rather than an id, the seat plural dropped, and the new frame
  taken out of `ALL_UI_FRAMES`. The real failure text is quoted beside each
  test.

## 2026-09-18: EA IRIS is built, on the host and not in the Docker VM

- **Decision:** build EA IRIS's example app natively on this Mac with
  `eval/baselines/iris/build-native.sh`, against Homebrew's OpenCV 4, ffmpeg,
  spdlog and nlohmann-json, and leave the pinned Docker image unbuilt.
- **Why:** the image is a vcpkg source build of the whole OpenCV tree, and the
  colima VM it would run in is shared with another project. A lane building an
  image in that VM on Sep 17 pushed it into its memory limit and got that
  project's `datahub-gms` container killed; its kafka and opensearch containers
  were still sitting at exit 137 the next morning. CLAUDE.md says never restart
  colima and never touch containers, images or volumes we did not create, and
  repeating the exact workload that caused the incident is not a risk worth an
  hour of build time. The native build is the same upstream commit, read out of
  the Dockerfile so the two cannot drift, with tests off and `test/` still left
  out of the checkout. It takes about two minutes.
- **Cost:** the dependencies are different builds of the same libraries.
  Upstream pins OpenCV and ffmpeg through vcpkg at a fixed baseline; this links
  against Homebrew's OpenCV 4.14 and ffmpeg 9. Decoding is where that could
  show, because a different ffmpeg can hand IRIS a different frame. Every report
  file carries the commit, the compiler, the OpenCV version and the libavformat
  version that produced it, so no number from this build is ever read as a
  number from upstream's. If the image is ever built on a CI runner, the pool
  should be re-run through it and the two compared rather than assumed equal.

## 2026-09-18: IRIS joins the pool as a candidate list, at its own fail line

- **Decision:** a frame joins IRIS's candidate list when its luminance or red
  frame result is an extended fail or a flash fail, or its pattern result is a
  fail. IRIS's "pass with warning", which is flashing between 2 and 3 Hz that
  IRIS passes, is recorded as `warning_frames` and `warning_segments` and is not
  a flag.
- **Why:** the candidate list should be what IRIS says is a hazard, not
  everything IRIS noticed, or the comparison is between our threshold and their
  curiosity. Keeping the warnings in the same file means "IRIS flagged nothing
  here" can still be told apart from "IRIS saw nothing here", and those are not
  the same finding.
- **Cost:** a window IRIS warned about and nobody else proposed is not in the
  union, so it will not be labelled. `--include-warnings` moves the line and the
  report records which side it was on.

## 2026-09-18: a clip IRIS cannot decode keeps its title out of the pool

- **Decision:** when IrisApp writes a frame data file with no frames in it, or
  stamps every frame with the same timestamp, `eval/baselines/iris/run.py`
  records a failure and writes no report for that clip. No report means no IRIS
  candidate list, which means `make_pool` keeps the title out.
- **Why:** on two Theora clips IrisApp logs "Video analysis started", "Elapsed
  time: 0 ms", writes a header-only CSV and reports the video as **Pass**. On
  four more it reads the container's frame rate as 0 and gives every frame the
  same timestamp, so its own one second transition window has nothing to measure
  against. A tool that passes what it never looked at is the one failure mode a
  candidate list must not inherit, and a report saying IRIS found nothing would
  be indistinguishable from one saying it never looked. The alternative, giving
  those clips a time base from `r_frame_rate` afterwards, puts real looking
  timestamps on an analysis that never had them.
- **Cost:** the pool shrank from 40 segments across 15 titles to 34 across 9.
  The three ISS night passes dropped out, and they were carrying half the
  unflagged half of the pool, so the negative half went from 12 windows to 6.
  That is the guard doing what it was built to do and it is still a real loss.
  `make ffmpeg-ps-pool` and `make naive-luma-pool` over the 16 calm clips would
  more than replace it, and this lane did not run them because its brief was the
  IRIS candidate list and nothing else.

## 2026-09-18: ffmpeg went from 8.1.2 to 9.0.1 on this machine, and two tools had to change

- **Decision:** keep ffmpeg 9 and change `-vsync 0` to `-fps_mode passthrough`
  in `eval/plots.py` and `eval/labeling/plots.py`.
- **Why:** not a decision anybody planned. Installing Homebrew's `opencv@4` for
  the IRIS build pulled ffmpeg 9.0.1 in and relinked it, and ffmpeg 9 removed the
  `-vsync` spelling outright. It exits with "Unrecognized option 'vsync'" before
  it opens the file, which reads downstream as a clip with no frames in it rather
  than as a bad command line, so every labelling plot failed to render with "no
  frames decoded". Rolling back is not cheap either: the 8.1.2 binary in the
  Cellar no longer starts, because x265 was upgraded underneath it. `fps_mode`
  has been in ffmpeg since 5.0 and means exactly what `-vsync 0` meant, so the
  two tools now work on both.
- **Cost:** every baseline result already in `results/baselines/` was measured
  with ffmpeg 8.1.2 and records that in its own `tool_version`, while the machine
  now has 9.0.1. Re-running either ffmpeg based baseline will produce numbers
  from a different decoder, and they should be re-run as a set rather than one
  clip at a time. The `photosensitivity` filter is still present in ffmpeg 9.

## 2026-09-19: the container's ffmpeg is pinned, this Mac's cannot be, and a check stops a table mixing them

- **Decision:** pin the ingest container's ffmpeg to the exact Debian apt version
  behind an `ARG`, record all three ffmpegs this project uses in
  docs/ENVIRONMENT.md, and add `eval/baseline_versions.py`, which fails when one
  baseline results directory holds reports from two tool versions. It runs in the
  numbers job.
- **Why:** the 8.1.2 to 9.0.1 upgrade the entry above describes was not asked
  for, and nothing in the repository would have noticed a second one. The
  container was installing the bare package name, so its decoder could change
  under a rebuild with no commit; it is Debian bookworm's 5.1.9, which is neither
  the Mac's nor a CI runner's, and docs/ENVIRONMENT.md never said so. Separately,
  every baseline report already stamped the build it ran under and nothing read
  those stamps, so a piecemeal re-run would have produced a table with rows from
  two tools and nothing saying which was which.
- **Cost:** Debian drops a superseded version from the mirror when it ships a
  security update, so the pin will one day fail the build instead of drifting.
  That is the intended failure and the comment beside it says what to do. The Mac
  cannot be pinned the same way: Homebrew has no supported downgrade for a
  formula another formula depends on, and this machine is shared. What stands in
  for a pin there is the record and the check.

## 2026-09-19: a run of bars has to repeat before it counts as a pattern

- **Decision:** add a periodicity test to the regular pattern rule. A scanline's
  run of bars contributes area only when the signal inside it has a period: its
  unbiased autocorrelation, searched from two samples to a third of the run, has
  a local maximum reaching `min_autocorrelation_peak`. The area thresholds then
  apply to the periodic region only.
- **Why:** Guideline 2 is about *regular* patterns and `scan_bars` was not
  testing regularity, only alternation. Cream on teal is 160.77 against
  8.47 cd/m2, so every glyph edge clears the Guideline 1 difference and a scan
  line through a paragraph counts dozens of bars at no spacing in particular.
  All nine display frames of our own report page read as a pattern over 44 to 64
  per cent of the screen, which is not a hazard and is not something a readable
  page can design away: at an SDR peak of 200 cd/m2 no pair of colours at 4.5:1
  has a difference under 20 cd/m2 with the darker state above 160.
- **The threshold was chosen by a rule fixed before the numbers were read:** the
  largest peak at which recall does not fall. That rule matters more than the
  value. A number picked because it makes our own page pass is not a
  measurement, and this is exactly the shape of mistake docs/STATUS.md already
  records four times, where the friendlier of two siblings got published.
- **What it is worth, measured:** `results/pattern_text_precision.json`, 123
  rendered pictures with ground truth from what was drawn. Precision 0.381 with
  the test off, 0.821 (0.673 to 0.910) at 0.85. Recall 0.941 (0.809 to 0.984),
  unchanged across the whole sweep from 0 to 0.85 and falling above it. **The
  entry below supersedes these numbers**: the suite grew to 171 pictures and the
  detector gained the spacing half of the test, and the sweep was re-run.
- **Cost, and it is not zero.** Body text at a fixed leading is a row of
  repetitive elements at a constant spacing, which Guideline 2 says a pattern may
  be formed by, so a column scan through a paragraph still has a period and it is
  the leading. Two of the report page's nine frames still carry a finding, at
  0.259 and 0.289 against a 0.25 limit, one frame at 0.262 after the entry below.
  That is left standing. Loosening the
  detector until our own page passes would be the same mistake in the other
  direction, and the page's verdict is printed rather than asserted on.
- **Second cost:** three more tuning numbers in the sidecar, and one of them,
  `min_cycles_for_period`, is load bearing in a way that is easy to get wrong. It
  must stay well under the spec's pair count. A twelve bar grating filling the
  picture spans five and a half periods, not six, because the run is measured
  from the first counted boundary to the last plus half a bar at each end, so a
  search that re-applied the pair count could not find the period of the first
  count the attachment can fail. That was a live false negative during this
  session and two existing tests caught it within minutes.

## 2026-09-20: the ITC/Ofcom guidance note, read at last, and a spacing test the count needs

- **Decision:** read the ITC Guidance Note from an Internet Archive capture,
  quote it in flashmap/docs/SPEC_SOURCES.md section 8.4, and add the second half
  of the periodicity test: the period the autocorrelation finds has to agree with
  the spacing of the boundaries that were counted, to within `spacing_tolerance`,
  at a whole multiple up to `MAX_HARMONIC`.
- **Why the source:** it is the document BT.1702-3's attachment reads like, and
  section 8.3 had been carrying a guess about how the two differ. ofcom.org.uk is
  still shut to every method tried, including headless Chrome, which gets the
  Cloudflare challenge page. The Internet Archive serves the file; SHA-256 and the
  exact capture URL are in 8.4.
- **What it settled:** every number matches BT.1702-3 Attachment 1 exactly, so
  nothing in the profile changed. The 8.3 guess was right and is no longer a
  guess: Ofcom makes the contrast condition its own clause applying in addition to
  the area condition, and the two read the same way. And it gives no periodicity
  measure, no spatial frequency, no stripe width, no pattern duration, no field of
  view and no contrast ratio, which is the negative result it was wanted for: the
  tuning constants stay tuning.
- **Why the spacing test:** the note counts "light-dark pairs of clearly
  discernible stripes". The count is a count of boundaries, so the boundaries have
  to be the thing that repeats, and a strong autocorrelation peak on its own does
  not say that. A motif of twelve irregular bars repeated eight times has a clean
  peak at the motif length and 96 counted boundaries at no regular spacing at all.
- **What it cost, and what it bought.** The suite grew to 171 pictures, adding
  every type size and colour pair this product actually ships, at both the app's
  scale and the report page's. Precision at the pre-registered 0.85 went from
  0.821 to 0.914 (0.776 to 0.970) and recall stayed at 0.941 (0.809 to 0.984).
  **Not one of the 94 pages of text is called a pattern now.** The report page is
  down from two failing display frames to one, at 0.262 against a 0.25 limit, and
  that one is recorded rather than tuned away, which is the instruction and is
  also the right call. The app's 25 screens pass.
- **The pre-registered 0.85 was not moved**, and it has now survived two changes
  to the suite. Recall is still flat from 0 through 0.85 and still drops above it.
- **One mistake, caught by measuring rather than by review.** The spacing test
  first compared the lag against `2 * bar_width` and nothing else. Lags are whole
  samples and a real bar width is not, so a grating at 2.23 samples a bar has a
  period of 4.45 that no integer lag sits on, and the strongest lag is the second
  harmonic. That version dropped five real gratings, every one horizontal, the
  worst a 32 pair grating over 80 per cent of the screen, and recall fell from
  0.941 to 0.794 before it was found. Whole multiples up to three are allowed now,
  and both directions of that ceiling are mutation tested.
- **One thing found in Appendix I that changes nothing and should be known.** The
  note's voltage to luminance table disagrees with the BT.1886 curve flashmap uses,
  by up to 8.8 cd/m2 in the middle of the range. For the darker-bar condition ours
  is stricter; for the 20 cd/m2 difference condition ours is the more permissive in
  the dark half, reading a step the table calls 20 as 15.7 from a darker level of
  100 mV. BT.1886 is what the recommendation in force asks for and Appendix I
  describes itself as a typical CRT relationship, so nothing was changed. The table
  and the arithmetic are in SPEC_SOURCES 8.4.

## 2026-10-26: separate public description from source and acceptance

Replace the mixed September/October landing page and placeholder submission draft
with a bounded prototype description and pinned public source navigation. Retain
engineering results and dated records, marking their historical scope. The newer
local repairs are not public and Debug observations are not Release acceptance.
This isolated documentation branch changes no product code or gates; review and
merge into main is still needed to update the default landing page. Cost: no
product rebuild, media preparation, native test or external submission change.

The feedback follow-up reuses the structurally complete numbered records in the
public October handoff and marks the older main copies historical. A concise
reconciliation normalizes dated notes without inventing experiences, identifies
owner confirmation and unread-form limits, and records that public clone-to-build
access still needs a separate check. The existing video's description identifies
an older branch; its private-access note is stale and was not edited.
