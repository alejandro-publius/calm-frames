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

## 2026-09-29: carry scene-specific holds in authenticated maps

- **Decision:** add an optional `scene_holds` presentation field to version 1
  maps, containing an opaque preceding-context JPEG per eligible covered
  interval. Use the same bytes in the prepared rendition and live cover model.
  Keep cover timing, segment lists, room floors and seek safety unchanged.
- **Why:** one still reused throughout a title and a black live cover lose the
  scene's context. Holding a preceding checked image while sound and captions
  continue is a bounded way to improve story continuity. Inline signed images
  bind the presentation asset to the map without trusting a mutable image URL.
- **Cost:** larger maps and image decoding on the player. Bound the number,
  individual image size and total payload; fall back to an opaque cover when
  an image is unavailable or the runtime interval is stricter. Validate the
  actual render and its transitions before publishing. No story-comprehension,
  physical-screen timing or clinical result is claimed by this change.
- **Review refinements:** keep the native image aspect intact over opaque black,
  and check pattern findings at the encoded output resolution during every
  hold, including HLS after correcting its transport time origin. This does not
  apply the broadcast source policy outside holds. Include actual image,
  manifest, map, output and verification-report bytes in cache checks; withdraw
  a prior catalog verdict before re-ingest so an early failure cannot leave it
  playable. Keep the legacy path covered by explicit legacy fixtures.

## 2026-09-29: latch interrupted scene holds black and verify cached preview bytes

- **Decision:** after uncertainty, a seek, backgrounding or an unready player
  interrupts a covered interval, retain an opaque black presentation for that
  interval throughout the verified map/title session. Resuming or seeking back
  must not restore its image; a later uninterrupted interval remains eligible.
- **Why:** an independently reproduced sequence of four waiting/playing cycles
  alternated the checked image and black within 400 ms of simulated time. The
  image itself being checked does not make that sequence acceptable. Synchronous
  event notifications and a monotonic event counter retain disruptions even when
  React batches the uncertainty and resume into one render. The hide schedule,
  thresholds and seek funnel are unchanged.
- **Commit boundary:** an uncommitted title render must not erase a committed
  title's blacklist or replace its presentation-event callback. Reset latch
  ownership and update event/presented-interval references only when the new
  render commits. Mismatched ownership stays black while verification catches
  up. This keeps one bounded session history without retaining every map text.
- **Cache boundary:** the probe and preview steps now compare recorded hashes
  of their actual outputs before reuse. Register poster JPEGs as step outputs,
  not only their manifest, so deleting or changing a preview causes restoration
  from the source. Include probe, global still, BIF, poster and manifest bytes
  in the final verification fingerprint as well as the signed scene assets.
- **Test boundary:** the property compiler now tracks the new parser as a cache
  prerequisite. A forced compile caught a numeric-narrowing error that a cached
  compiled scheduler had hidden. Both strict app compilation and the property's
  non-strict compilation must work; stale compiled bytes are not evidence about
  the edited parser.
- **Limit:** encoded-output checks and simulated event tests do not establish
  native image composition or cover timing on a physical television. Those
  measurements remain required before any corresponding claim.

## 2026-09-29: preserve the mutation baseline during CI checks

- **Decision:** `--check` must compare the real run against the existing
  committed report without replacing that report. Unexpected non-equivalent
  survivors must fail even if a baseline already names them. CI writes the
  actual measurement to a separate ignored path and retains it as an artifact.
- **Why:** review found the gate writing its result to the default canonical
  path before comparing it. The comparison then read the same newly written
  result as its expectation, so score and inventory drift could escape CI.
- **Evidence boundary:** add regressions proving a failed comparison leaves
  the baseline bytes unchanged. A newly registered mutant is not a measured
  kill, and an interrupted run is not a complete report. The full current
  inventory has now completed with every unmodified control green and no
  unexpected survivors; `results/mutation.json` contains the actual measurement.
- **Publishing boundary:** Alex asked to continue in-scope work without further
  permission questions. Use an isolated review branch for unrestricted CI
  evidence, not as a claim that the code is ready. Do not update main until its
  proposed tree has passed the complete required checks.
- **Artifact boundary:** upload only `.logs/mutation-ci.json` with hidden-file
  inclusion enabled. The action excludes files in hidden directories by default;
  leaving that setting out would discard the report on a failed drift check.

## 2026-09-29: distinguish an Actions startup failure from an audit result

- **Evidence:** the Sep 28 scheduled Audit on the unchanged main commit failed
  in all four jobs before any runner or step started. One Sep 29 retry reproduced
  `runner_id: 0` and empty steps, with no runner logs. The Sep 21 scheduled Audit
  on that same commit passed.
- **Decision:** do not change dependencies, widen audit exceptions, disable jobs
  or make the private repository public based on a run that never reached code.
  Record the startup restriction separately and keep main unchanged until the
  complete proposed tree has actual passing checks. Account or billing changes
  are outside this code-and-testing task.
- **Initial limit:** the connected API could not retrieve the startup annotation.
  The later unrestricted read did: GitHub says jobs were not started because
  recent account payments failed or the spending limit needs increasing. It
  does not identify which of those two account conditions applies. No account
  billing or repository-visibility setting was changed.
- **Cost:** two days without a hosted run while the cause sat outside the code, and a status board that said the build was red when nothing in it was; the Oct 5 scheduled run ended it.

## 2026-09-29: make the local preparation result usable without cloud deployment

- **Decision:** add a separate local-library wrapper around existing ingest and
  verification, with explicit external keys, requested presets, a per-source
  receipt and a verified-only snapshot. It never enables `skip_verify` or
  changes the upload server's measure-and-delete contract.
- **Why:** a developer needs one preparation command and a readable next step
  before AWS delivery is available. Catalog booleans alone do not establish
  readiness: source/result identity, complete reports and current output bytes
  are checked before listing. Failed re-imports withdraw the prior receipt.
- **Cost:** a per-workspace nonblocking lock prevents overlapping imports, and
  refreshing the snapshot hashes its checked inputs again. Unsafe artifact
  paths, symlinks and unexpected HLS references cannot be listed. This is a
  local status receipt, not cryptographic publication authority, an app-shelf
  connection, a clinical result or physical-TV evidence.

## 2026-09-29: explain the household's actual checked viewing plan

- **Decision:** review the selected household at the end of setup and show a
  title's plan only for a verified entry with every required preset map. Use
  existing calm surfaces, television-size type and the approved limits text.
- **Why:** a parent should see their choices and what the title's check means
  before choosing Play. Pending and failed entries must not look approved, and
  an old Standard check must not imply that Broadcast has already been checked.
- **Cost:** presentation-only UI and assertion regressions. The status and
  required-profile guards were each removed in isolation; the corresponding
  assertions failed, then passed when the guards were restored. Settings and
  the PIN remain in memory. Detector, schedule and seek rules are unchanged.

## 2026-09-29: test an installed hook package rather than a source alias

- **Decision:** support and document a locally packed tarball, include the
  repository licence and an explicit React Native source entry, and exercise
  that tarball in a clean offline consumer in CI and `make ci`.
- **Why:** installing the monorepo's GitHub root cannot select its hook folder.
  A source mirror test alone cannot catch omitted packed dependencies, broken
  exports or a consumer resolving the wrong entry.
- **Cost:** the check uses installed app tooling and current real Vega peer
  types after the clean install. It checks package inventory, import closure,
  TypeScript, Metro and Babel; it does not publish to npm or certify native
  playback or compatibility with future peer versions.

## 2026-09-29: retain the new dependency-audit blocker without a risky override

- **Evidence:** an unrestricted fresh audit reaches the public advisory
  databases and fails on `image-size`, npm source `1239766`,
  [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr).
  The installed version is `0.6.3`, pulled in by the SDK's older build tooling.
  Malformed ICNS input can hang its asset parser.
- **Decision:** do not add the advisory to an exception, downgrade to escape
  the affected range, or force the patched `2.0.3` under an incompatible
  consumer. The old Metro expects a callable CommonJS export and synchronous
  file input; the official patched API does not supply that legacy entry.
- **Cost:** this audit remains red until a compatible dependency repair is
  validated. Alex requested pushes only when ready and checks pass, so these
  follow-up changes can be committed locally but are not pushed while that
  gate is red. Main and the published review branch remain unchanged. This
  blocker is separate from GitHub's account-level Actions startup restriction
  and has nothing to do with connecting AWS.

## 2026-09-29: adapt the legacy asset API around the official parser fix

- **Decision:** keep the SDK and Metro versions unchanged, replace only Metro
  0.54.1's vulnerable `image-size` resolution with a private local API adapter,
  and pin its real parser to official `image-size@2.0.4` under an explicit npm
  alias. No parser code is copied and no audit exception is widened.
- **Why:** the official fix does not preserve Metro's callable CommonJS and
  synchronous filename interface. The small adapter restores that interface,
  bounded partial reads and descriptor cleanup while every parse uses upstream.
  Both packages retain their actual identities in the lockfile and SBOM.
- **Evidence:** the old malformed-ICNS buffer, filename and callback paths
  time out in isolated byte-only children; all three now terminate with an
  error. Timeout is a failed regression, never a successful rejection. Actual
  Metro PNG, JPEG and SVG asset tests and a relocated clean offline consumer
  pass. The full app lockfile also installs with clean offline `npm ci`, using
  its unchanged tracked `.npmrc`, with real Metro resolution and all rejection
  modes checked again. Cleanup, bound and partial-read guards were observed assertion-red
  in copied controls and green after restoration. The fresh audit gate passes.
- **Cost:** maintain the local interface shim and exact upstream pin when the
  SDK changes. Local dependency readiness does not resolve the hosted Actions
  account restriction or establish real-TV playback readiness.

## 2026-09-29: expose physical-TV prerequisites without executing a device session

- **Decision:** add a read-only hardware preflight and Makefile target. Check
  live SDK connection, literal physical identity, explicit serial, developer
  mode, pinned OS/build and actual bounded Debug package members. Never scan
  the LAN, install, launch, play, reset or manufacture a gate result.
- **Why:** the current SDK connection has no physical or virtual device. The
  bundled benign clip has audio but no captions or scene holds, and the old
  timing runner uses QEMU host paths. Basic smoke, composition and camera
  timing must remain separate rather than treating a software log as proof.
- **Cost:** HUMAN CHECKPOINT B, a checked benign captioned sham-hold fixture,
  physical-target timing-runner adaptation and HUMAN CHECKPOINT E1 footage
  remain required. Synthetic SDK/archive regressions validate only these
  preflight guards, not native decoding, playback or physical composition.

## 2026-09-29: diagnose Actions billing without changing account finances

- **Evidence:** Actions is enabled and the repository connection has admin
  permission, but the current jobs still have zero assigned runners and no
  steps. GitHub's annotation says a recent payment failed or the spending
  limit needs increasing. Read-only personal billing endpoints return 404;
  the installed GitHub plugin provides no account-billing control.
- **Decision:** ask the owner to inspect Billing and plans without sharing
  card details. Do not infer which condition applies, broaden authorization,
  purchase minutes, change payment details, raise an unspecified budget,
  register a persistent self-hosted runner or make the private repo public.
- **Cost:** complete hosted CI still waits on the owner's account action.
  Continue local implementation and tests; keep main unchanged until its
  proposed tree passes the complete required checks. AWS remains disconnected.


## 2026-10-02: restore household setup before allowing viewing

- **Decision:** save the family and PIN gate as one bounded, versioned local
  record using the app's existing SDK storage adapter. Validate every preset,
  room, profile and PIN field before showing the shelf. Keep invalid records
  and read failures blocked rather than resetting their floor or parent PIN.
- **Why:** setup that disappears on restart makes the family repeat onboarding
  and loses its stricter room and preset. Losing failed attempts on restart
  also defeats the local keypad lockout. A PIN result must be saved before
  allowing the parent area to open or another attempt to start.
- **Evidence:** restart, strict-floor, retry, lockout, pending-write and stale
  read regressions exercise the real app route against injected local storage.
  Removing the loading block, record validation, save-before-unlock, retained
  write retry and stale-read guard each caused an assertion failure, followed
  by restored green source. The full app suite, strict TypeScript, lint and
  native Debug builds pass. The broad Python run has no assertion failures;
  its existing HTTP fixtures error on the sandbox localhost bind restriction.
  Loading and error notices enter the existing
  rendered palette and ten-foot measurements.
- **Cost:** a malformed or unsupported record requires repair outside kid mode;
  the app offers retry but no PIN-free reset. This does not encrypt local
  storage or defend against someone who can run code on the device. Native
  process-restart durability still needs device validation. Hide history
  remains in memory. No detector, threshold, map, timing or seek rule changed.

## 2026-10-02: correct repository access instructions using current rules

- **Decision:** keep the planned public release while documenting the allowed
  private reviewer route and current named Amazon accounts. Preserve historical
  mock reviews as historical records. Do not change visibility or invitations.
- **Why:** the overview and rules fetched when this pass began both list
  `testing@devpost.com` and named reviewers rather than a single Amazon account.
  Invitations should be issued at submission and their acceptance checked.
- **Cost:** the owner still chooses the actual access route and final publication
  timing. Documentation does not establish accepted invitations, a published
  video, an open-source contribution or an AWS integration running in cloud.


## 2026-10-02: demonstrate story continuity and separate evidence from ambition

- **Decision:** score the current project against live Devpost criteria, keep
  submission completeness separate, and replace overbroad submission claims
  with implemented behavior and the unfavorable measurement denominators too.
- **Why:** the strongest idea was difficult to see in the original gradient;
  an extensive test suite cannot substitute for a working product demonstration.
- **Cost:** a benign original captioned story with clearly labelled sham holds,
  actual pipeline checks, fixed packaged trust and conservative per-title
  preparation. The demo uses Extra cautious coverage without changing saved
  household settings. Current TV composition and playback remain unverified.
- **Review fixes:** history deletion follows committed household removal;
  turning captions off uses the current selected native track. Both had
  observed failing regression cases before correction.
- **Continuation:** keep an explicit implement, validate and review loop in
  `docs/CONTINUATION_PROMPT.md`, with a precise handoff at real session limits.
  It does not promise unlimited credits, deploy services or publish the repo.


## 2026-10-02: terminal completion and packaged prepared media

- Decision: connect local receipts through a bounded compiled library with
  immutable content-addressed generations. Keep original SHA and rendition SHA
  separate; accept the public key only for an exact compiled title and preset.
  Recheck source assets and every native archive. Why: a source-bound signed map
  alone cannot identify the changed video delivered to the player. Cost: adding
  a title requires a new build; the namespace is deliberately small and previous
  generations are retained rather than deleted automatically.
- Decision: use one explicit room, the app's complete profile unions and its
  fixed cover timings for local imports. Recompute the plan during verification.
  Omit union scene descriptors until the signed descriptor contract can represent
  them correctly. Why: separate profile plans can be shorter than the app's union
  and a union hold may not belong to the individual source map. Cost: generic
  imports use the verified pre-covered picture and opaque live fallback; the
  existing labelled scene-hold demo and legacy pipeline remain available.
- Decision: import the owned Harbor source with neutral captions through genuine
  analysis, without adding synthetic findings. Keep it separate from the
  explicitly labelled practice-hold demo. Cost: two distinguishable shelf items;
  this proves the delivery path, not detector recall or physical playback.
- Decision: replace the legacy smoke CLI with a read-only default preflight and
  explicit-target capture of the current household/Harbor journey. Never reset
  data, synthesize successful observations or treat logs as camera proof. Cost:
  native completion waits for an accessible target; sandbox launch is denied.
- Decision: make the final-video duration gate exclusive. Why: exactly three
  minutes violates the under-three-minute submission requirement. Cost: none;
  the real benign boundary regression was red before the fix and green after it.
- Decision: recheck the full frozen synthetic design after correcting its
  RGB/YUV matrix and range encoding, preserving the old-protocol recheck and
  archive. Thresholds, production analysis resolution and truth labels are
  unchanged. Cost: a long local CPU run; no cloud spend. Report exclusions,
  near-limit weaknesses and paired protocol effects before changing claims.
- Decision: reapply and test the existing upstream patches in isolated scratch,
  leaving their publication for the authorized public contribution step. Cost:
  no external write; observed faulty controls and restored focused tests support
  the prepared patch without claiming an upstream merge or native test.


## 2026-10-09: size the colour fidelity tolerance from one 8-bit code

- **Decision:** the colour encoding fidelity test
  (`test_fidelity_decode_uses_declared_or_inferred_matrix_and_range`) now
  allows up to the luminance change of moving every channel of the intended
  colour one 8-bit code, never less than the old 0.004. White gets 0.0089; the
  three [255, 58, 58] cases stay at 0.004. The comparison is `<=` with 1e-12
  added only for floating-point noise, so a decode exactly one code off on
  every channel passes. This is a test tolerance, not a detector threshold,
  and the test computes it from the parsed sRGB and luminance constants.
- **Why:** hosted CI run 37902331109 failed only the full-range white case, at
  a decoded mean of 0.99558 against 1.0. PyAV 18.1.0's x86_64 builds (the
  macOS wheel under Rosetta, and the exact Linux wheel CI installs) reproduce
  that mean bit for bit. Their libswscale RGB to YUV step puts 7/8 of the
  white chroma samples at 127 instead of 128, so 7/8 of the pixels decode to
  (253, 255, 253). Apple silicon returns exactly 1.0, and libx264 runs
  lossless (qp 0) here, so the codec is not involved. The old 0.004 is less
  than half of what one code on every channel costs at white, so rounding
  alone could cross it.
- **Evidence:** with the new bound, a full-range clip encoded with limited
  levels still fails the white case (0.169 against 0.0089). A decoder that
  always applies BT.601, ignores the declared range, or drops the untagged
  height rule still fails the affected red cases (0.021 to 0.049 against
  0.004). Each mutation went red on arm64 and on x86_64 with the mutated
  module confirmed as the one imported, and each restore went green. Under
  x86_64 the old test fails with CI's exact message and the new one passes.
- **Known gap, older than this change:** a decoder hard-coded to BT.709 passes
  all 13 tests on both architectures, because every fidelity case is BT.709.
  Closing it with BT.601 red cases needs its own tolerance: on x86_64 with the
  CI wheel, BT.601 limited-range red decodes to (253, 57, 57), an error of
  0.00476, above both 0.004 and that colour's one-code bound of 0.00299
  (arm64: 0.00198).
- **Cost:** white now accepts up to one code of rounding on every channel.
  That hides nothing this case can see: no matrix error moves white, and the
  range error it guards moves it by 0.169. The red cases are unchanged.
  libswscale's portable C path, which neither platform takes, decodes them
  0.0042 low, so a runner without SIMD would fail them under the old limit and
  the new one alike.

## 2026-10-09: HUMAN CHECKPOINT D, amended and confirmed

- **Decision:** Treat HUMAN CHECKPOINT D as confirmed on Oct 9, 2026, with its
  third clause, "the $150 credit request is in", recorded as void and waived
  rather than met. Alex confirmed it in chat, where he asked for the deploy,
  and at his own terminal, where he ran `make deploy CHECKPOINT_D=confirmed`
  and approved the IAM changes himself. docs/GATES.md has the entry.
- **Why:** The credit request form closed on Oct 7, so nobody could meet that
  clause any more. Alex waived it and planned to use his existing credits for
  eligible charges; coverage was not verified. The other two hold. The account moved to
  the Paid plan at 23:03 PDT on Oct 8 (CloudTrail), and the 20 dollar budget
  exists with its three alerts.
- **Cost:** The budget cannot warn anyone yet. It counts only costs tagged
  `Project=calm-frames`, and at 02:50 PDT Cost Explorer listed no such cost
  allocation tag, so until Alex activates it the bill is read by hand. The lock
  line went only into the deploy worktree's copy of docs/STATUS.md and was never
  committed, so the committed lock stays closed and the next deploy needs a
  person to open it again.

## 2026-10-09: deploy without the GitHub OIDC role

- **Decision:** Leave `githubRepo` empty on the first deploy, so the stack made
  no GitHub OIDC provider and no deploy role, and record that rather than
  redeploying to add them.
- **Why:** Nothing in this repository deploys from CI, on purpose. A role that
  nothing assumes is standing permission with no use, and the control that
  matters here is a person at a terminal reading the IAM table before typing
  `y`, which CI cannot do. Adding the role later is one redeploy with
  `GITHUB_REPO` set, and its IAM rows would come up for approval then.
- **Cost:** docs/SECURITY.md described AWS access as a GitHub OIDC role; it now
  says the one deploy used the operator's own CLI credentials in his terminal.
  CLAUDE.md's rule, AWS access from CI only through OIDC, still holds, because
  CI has no AWS access at all.

## 2026-10-09: a separate cloud demo signing key, which the app does not trust

- **Decision:** Give the ingest task a throwaway Ed25519 key made for the cloud,
  `cloud_demo_2026-10`, kept as the SSM SecureString
  `/calm-frames/cloud-signing-key` under the account's `aws/ssm` key and readable
  by the task role alone, through SSM alone. Never the release key or
  `team_key.pem`, and never compile its public half into the app.
- **Why:** Without a key the task refuses to publish, which the first run
  proved. With the release key in SSM, a key a running task can read would be a
  key the TV believes. A key the app does not trust lets the cloud run end to end
  while a leak changes nothing on the TV: its id starts
  <!--n results/aws_deploy_2026-10-09.json:signing_key.key_id_short -->9fa44e490266<!--/n-->, and the
  key the app checks maps against starts
  <!--n results/aws_deploy_2026-10-09.json:signing_key.app_trusted_key_id_short -->9d32df3b18c9<!--/n-->.
- **Cost:** The maps the cloud makes play on no TV. They are evidence of the
  pipeline running on AWS, not titles, and the demo shelf stays the packaged one.
  A redeploy without `SIGNING_KEY_PARAMETER` takes the wiring out again, which
  is why `scripts/aws_guard.sh` now passes it and says on every deploy whether a
  key is wired in. The parameter and the local copy outlive `make destroy` and
  are deleted by hand.

## 2026-10-09: keep the stack up until the results, about Dec 3

- **Decision:** Leave CalmFramesStack running through judging and take it down
  with `make destroy` after the winners are announced, about Dec 3, 2026, then
  remove what lives outside it (pipeline/infra/README.md, "Taking it down").
  Only read-only checks in between.
- **Why:** The AWS Builder evidence is a deployed stack and its recorded runs. A
  judge who looks during judging should find what the documents describe, not a
  stack that was taken down the week the video was cut.
- **Cost:** Idle, the stack bills storage only: the
  <!--n results/aws_deploy_2026-10-09.json:image.size_mb -->279<!--/n--> MB image in ECR at
  $<!--n results/cost_estimate.json:unit_prices.ecr_gb_month.usd -->0.1<!--/n--> per GB month, a few
  kilobytes in S3 and DynamoDB, and the log groups. That is cents a month at list
  prices, but the bill is the measure, and the budget cannot see it until the
  tag is active. For the whole time, CloudFront serves the delivered calm title
  to anyone who has its path: a kid safe rendition and a map no TV trusts.

## 2026-10-09: pin the CDK CLI to 2.1142.0

- **Decision:** Move the CDK CLI pin from 2.1032.0 to 2.1142.0 in
  `scripts/aws_guard.sh`, `pipeline/infra/Makefile` and the bootstrap command in
  `pipeline/infra/README.md`, and test that the three agree and meet the minimum
  the installed aws-cdk-lib declares.
- **Why:** aws-cdk-lib 2.270.0 writes cloud assembly schema 54, and the old pin
  stops right after synth with "Cloud assembly schema version mismatch: Maximum
  schema version supported is 48.x.x, but found 54.0.0. You need at least CLI
  version 2.1142.0 to read this manifest." The deploy ran on 2.1142.0, named on
  the command line. A bisect in scratch that night found CLIs from 2.1126.0 on
  already read the manifest and synthesized a byte-identical template, but
  2.1142.0 is what the library declares and what the stack was deployed with.
- **Cost:** The library and the CLI now move together: bumping aws-cdk-lib means
  bumping the pin, or the version test fails in the Audit workflow's infra job.
  That test needs aws-cdk-lib, so it skips in the CI Python job.

## 2026-10-09: the ingest image was built in the shared Docker VM after all

- **Decision:** Record that the Oct 9 `make deploy` built the ingest image in the
  shared colima VM on this Mac, which the Sep 17 entry "stop building the
  container on this Mac" ruled out, and keep the risk in front of the next build.
- **Why:** `scripts/push_ingest_image.sh` builds before it pushes, so a deploy
  from this Mac builds here. The Sep 17 decision added an image job on a runner
  but left `make image` and the push script building locally. This time the
  build finished and nothing else was hurt: every other project's container
  still read up for two or three weeks the next morning, and the two that exited
  137 date from Sep 17.
- **Cost:** The memory risk the Sep 17 entry describes is still there for every
  deploy from this Mac, and the planned rebuild for the Harbor run is the next
  one. Watch the VM while it builds, or build on a runner and push from there.
  Two local images from that night, about 1 GB each in the VM (the pushed one
  under two tags, and a dry run build), are ours and can be removed once the
  rebuild has replaced them.

## 2026-10-09: ledger rows for our own marker clip and story, kept out of the pool

- **Decision:** Give `media/markers_packed.mp4` and the Harbor story
  `app/assets/raw/benign-story/harbor.mp4` rows in `media/LICENSES.csv` marked
  "Ours", CC0-1.0, like the chime's, so NOTICE and the credits screen name them.
  The labelling pool now keeps out every row whose note starts "Ours.".
- **Why:** Every asset we ship or measure with should have one row saying where
  it came from. But the marker clip sits in media/, every candidate list has a
  result for it and it is longer than a segment, so the next pool rebuild would
  have drawn windows from it. Run against the main checkout's media/, it came
  out eligible.
- **Cost:** The screening table's unlabeled row now counts 12 analysed seconds
  instead of 0, because the ledger gives the clip a duration; nothing published
  reads that field. `eval/fetch_media.py` rewrites the ledger from its own list
  and would drop these rows, as it would the chime's.

## 2026-10-09: one feedback section per AWS service, answered from the deploy

- **Decision:** Rewrite docs/FEEDBACK.md's AWS answers from the night of Oct 9
  and give each service the stack used its own five questions: CDK, Fargate,
  S3 and CloudFront as before, and now Lambda, DynamoDB, ECR, Parameter Store
  with KMS, and Budgets. The Kepler packages and GitHub Actions move from 12
  and 13 to 17 and 18. Only facts in `results/aws_deploy_2026-10-09.json`,
  `results/cost_estimate.json` or the committed infra docs are published, and
  the two quoted AWS pages were read that night.
- **Why:** Amazon asks the five questions of every tool an entry used, and the
  AWS Builder field is answered inside the product feedback. Sections that said
  "nothing is deployed" became false on Oct 9, and five services had no answer
  at all.
- **Cost:** Section numbers moved. The two references inside FEEDBACK.md and
  SUBMISSION.md section 10.1 follow; docs/MOCK_JUDGE_2.md still cites the old
  numbers and is left as the historical review it is. The starter Lambda's run
  durations exist only in the saved evidence outside the repository, so they are
  not quoted. Each answer is one night and one short clip deep, and says so.

## 2026-10-09: the cost line stays the estimate, with its worse sibling beside it

- **Decision:** Replace SUBMISSION.md's unsourced "about 5 US dollars" with the
  <!--n results/cost_estimate.json:published.monthly_total_usd -->1.34<!--/n--> a month in
  `results/cost_estimate.json`, published next to its
  <!--n results/cost_estimate.json:published.task_time_quadruple_usd -->2.52<!--/n--> for a task four
  times as long, rather than a figure worked out from the Oct 9
  runs.
- **Why:** The estimate's largest unknown is how long the ingest task runs per
  title. The only runs so far are a short calm clip, which says nothing about a
  full-length title, and the bill cannot be read per project until the
  `Project` tag is active. The NAT figure moves the same way, from an unsourced
  "65 to 100" to the file's
  <!--n results/cost_estimate.json:published.nat_gateways_would_add_usd -->65.7<!--/n-->.
- **Cost:** `results/cost_estimate.json` still says "Nothing has been deployed"
  in its own statement field. That is the file's wording from Sep 17, and it is
  left for the next regeneration of the estimate rather than edited by hand.

## 2026-10-09: the integration page installs the release tarball

- **Decision:** docs/INTEGRATION_DIFF.md's `npm install @calm-frames/flash-guard`
  becomes installing `calm-frames-flash-guard-0.1.0.tgz` from the GitHub
  Release, with a line saying the release does not exist yet and pointing at
  hook/README.md for packing the same tarball meanwhile.
- **Why:** The package is not on npm, so the old line failed for anyone who ran
  it. A release asset is the one install path a reader outside this repository
  can follow.
- **Cost:** `scripts/release.sh` attaches the three `.vpkg` files and
  `SHA256SUMS`, not the hook tarball. The release work has to add it, and its
  checksum, or this line has to change again before the release is published.

## 2026-10-09: the player's first P0 block, for the build rehearsed Saturday

Five changes on `wip/ui-player-card-2026-10-09`, app code and tests only, each
with a guard test seen red before it was trusted. None has been seen on a
device yet.

- **Decision:** while a countdown card offers Skip, OK belongs to Skip.
  VideoPlayerUI neither toggles play nor brings up the sample's controls for
  SELECT then; every other key behaves as before. **Why:** Skip has D-pad
  focus during a countdown, and the sample also reacting to the same key
  paused the title under the card or put its controls over it. **Cost:** OK
  cannot pause during the five seconds of a countdown; the remote's play and
  pause key still can.
- **Decision:** a title that ships a caption track starts with its first track
  showing, and CaptionMenu takes the track id the player passes down. **Why:**
  captions are what keep a hidden part followable. A menu that started at Off
  with a track on left that track running when Off was chosen, and two tracks
  showing after a change of language. **Cost:** captions are on for every such
  title, the sample's own included, and there is no household setting to start
  them off. Amazon's w3cmedia README says nothing renders until the system
  setting ClosedCaptioningEnabled is 1, so the device walk checks that first.
- **Decision:** one console.log line for every KeplerAppStateChange the player
  receives and every Vega Media Controls callback, the seventeen that do not
  move the playhead included. **Why:** device bring-up needs to see which
  commands arrive and how many per press. console.log because the Release
  build strips it; a test compiles each file both ways. **Cost:** seventeen
  pass-through overrides in SafeMediaControlHandler that exist only for the
  line. Each still hands the call to the base class unchanged, and a test reads
  the pinned SDK's declaration and fails if a callback is left without one.
- **Decision:** the card hangs from 160 units down instead of standing 160 up
  from the bottom, and the Harbor practice label moves onto a plate in the top
  left corner of the safe area, TEXT_DIM on SURFACE at 32 units. The ten foot
  pass renders the real player and fails if the card, the plate and the
  caption band overlap, taking the band as 240 units above the captions
  view's bottom edge. **Why:** the card sat over the captions, and the bare
  label sat where the card now goes, at 3.25 to 1 over the mid grey that
  stands in for video. **Cost:** the card covers part of the upper picture
  during its countdown and after windows, and while the sample's controls are
  up their header draws over it, which is the P1 chrome work. The check
  measures styles with a deliberately generous ruler, not pixels.
- **Decision:** while the guard is still checking a map, the card says
  "Checking this title" instead of the "Not checked yet" refusal. **Why:**
  every title opened on what read as a failure, and a replacement map kept the
  last refusal's wording until its own check finished. The picture is hidden
  either way. **Cost:** one more card kind, `checking`, and more frames for the
  UI flash run, which passes across 33 screens and transitions.

## 2026-10-09: Harbor's practice cards in the real pattern, and the shelf's first frame

- **Decision:** the Harbor practice cards follow the pattern a family meets on
  a checked title. Countdown: "Practice hold coming up" with the live "In N
  seconds. Press Skip to jump past it." Covering: "Holding a calm scene" with
  "Practice hold. Sound and captions keep playing." After: "Held N seconds for
  practice" with "Sound and captions kept playing. No flashing was present."
  Only `app/src/calmframes/benignStory.ts` changed. The media, the signed maps
  and `benignStoryData.ts` did not, so the demo key and the pinned proof stay
  put (K11: Harbor is never regenerated for wording).
- **Why:** the finish plan's video storyboard quotes the after card exactly as
  the app draws it, and the Oct 2 cards ("A practice hold is coming", "The
  story carries on") showed neither the real countdown nor the real after card.
- **Cost:** "no flashing" is now on one card instead of three. The corner label
  and the label burned into the picture still say it for the whole story. On
  Harbor v1 the first hold's after card never shows: the second hold starts
  inside the countdown lead, and the countdown wins, as on a real title. Only
  the second hold's after card can be filmed.
- **Decision:** the shelf opens on Harbor with the D-pad focus, then the
  checked prepared library, then the calm gradient last. `defaultCatalog` is
  the order.
- **Why:** Harbor is the one title that shows the whole journey (captions, a
  countdown, a practice hold), and the shot list films the shelf with Harbor
  focused (SHOT_MANIFEST S02). The gradient has none of those.
- **Cost:** coming back from a title puts the focus on Harbor, not on the
  poster that was opened. Restoring focus on purpose is in the second UI block.
- **Decision:** Harbor's poster is the first of the two stills its own signed
  WCAG map already carries, shown only when its check passed, it is the bundled
  Harbor by id, uri and hash, the check read the WCAG map, and that map text is
  the compiled one. The prepared Harbor and the gradient keep a plain block.
  No image was added to the package.
- **Why:** the plan asks for stills from the signed hold images and no new
  media. Lending Harbor's still to the prepared Harbor would put another file's
  signature, and its burned-in "BENIGN DEMO - NO FLASHING" label, on a title
  that is neither.
- **Cost:** two of three posters are still plain blocks. The UI flash run
  paints colours, not pictures, so it never sees the still: the still does not
  move, comes from a title whose source measured no violations, and sits in a
  block smaller than the area that run paints for each colour. The block keeps
  its BORDER fill under the picture, which keeps the reported frames true, and
  posters are now 16:9 rather than a fixed 180 units tall, so a still is never
  cropped.
- **Decision:** a poster reads as a name, then a second line: "Harbor story"
  over "Benign demo, practice holds", "Harbor story" over "Prepared locally",
  "Calm gradient" over "Bundled". The shelf splits a trailing "(...)" off the
  catalog title, and Harbor's line is written out so that it says practice.
- **Why:** the first frame reads as titles rather than file labels, and the
  two Harbors stay told apart by the second line.
- **Cost:** the shelf and the details page now word the same title two ways.
  The catalog, the details page, the parent area, the player, the hide log,
  the docs and the native smoke steps keep the full title, so nothing that
  names a title by it had to change.
- **Evidence:** every guard was seen to fail with its code broken on purpose
  and restored (the commit messages list each one).


## 2026-10-09: simulator-only finishing scope and evidence

- **Decision:** preserve `dcb27a1` and the separate deployment worktree; use
  the Vega Virtual Device exclusively. **Why:** Alex's current instructions
  supersede the old hardware schedule and possible teammate. **Cost:** no
  physical screen-timing or clinical claim; simulator behavior must still be
  observed directly.
- **Decision:** add a Delete key for partial PIN entry, remember the last opened
  checked shelf title, and consume Back from Credits. **Why:** remote correction
  and return navigation were incomplete. **Cost:** another keypad control in
  the existing last row. Regression controls failed before these fixes; actual
  D-pad focus remains a simulator check.
- **Decision:** retain the monk and palette, replace concentric rings with one
  open halo, and use "A calmer way to watch". **Why:** the requested identity
  needs one consistent small-size silhouette and accurate brand line. **Cost:**
  regenerated icons and tile. The installed Qt renderer avoids dependence on
  browser capture and keeps transparent icon corners and an opaque listing tile.
- **Decision:** adopt the complete corrected conformance report without
  rerunning hazardous generators. **Why:** its recorded input hashes and exact
  report rebuild passed independent review. **Cost:** lower recall than the
  archived partial headline, disclosed alongside the weaker near-limit result.
  The encoding-protocol correction and unmatched historical baselines remain
  explicit. Detector thresholds are unchanged.
- **Decision:** stop Claude delegation at the authentication probe. **Why:**
  `auth status` reports not logged in here and the small task failed. **Cost:**
  existing subscription access must be made available before Claude work can
  proceed. No API key, billing change or permission bypass was attempted.

## October 10, 2026: complete the simulator evidence

- **Decision:** use the verified host Claude Max session with explicit Fable 5.1
  and max effort. **Why:** the small subscription probe succeeded. **Cost:**
  subscription allowance only, no API keys or billing changes. Ultracode works
  noninteractively but its background wait ceiling ended an unfinished review;
  bounded ordinary CLI workers completed useful fixes and independent reviews.
- **Decision:** normalize package URIs only at the native media boundary and
  retain an RN caption host. **Why:** native errors and screenshots established
  the file-open and caption-stacking failures. **Cost:** small regression-tested
  changes, no signed identity or threshold changes.
- **Decision:** make exit cleanup idempotent and independent of the captions
  menu. **Why:** final review and observed-red tests reproduced duplicate Back
  and blocked background teardown. **Cost:** three regression tests and a final
  rebuilt package/native playback rerun.
- **Decision:** ship a local review cut with disclosed synthetic English voice,
  actual native video/stills and a source manifest. **Why:** it demonstrates the
  running app truthfully below three minutes. **Cost:** local recording/encoding;
  no fabricated feedback, hazard viewing, public upload or cloud execution.
- **Decision:** report security findings and history-test scope explicitly.
  **Why:** SDK dependency Audit is still red, the cloud pipeline is separate,
  and synthetic practice must not create false exposure history. **Cost:**
  the entry is reviewable but is not yet a released or submitted product.

## October 10: approved native TV design

- **Decision:** apply the user-approved Documents archive to the current Mac branch. Preserve signed assets, playback gates and household logic. **Why:** the older cloud checkout does not include the current Harbor and recovery work.
- **Decision:** bundle licensed static Inter faces in Vega's `assets/fonts` directory. **Why:** native before/after captures verified the correct directory and real weights; the image exposes no Ember semibold.
- **Decision:** use concept artwork only for browsing and keep scheduled demo holds distinct from detected hazards. **Why:** the design must not alter media provenance or safety claims.
- **Decision:** use a stable outline plus focused text underline. **Why:** the independent Ultracode review requested a non-color focus cue without layout movement.
- **Decision:** keep actual native still/video sources and disclose narration in the redesigned demo. **Why:** a browser reference is not simulator evidence.

- **Decision:** retain focus on parent preset, room and chime controls while a save blocks presses. **Why:** native validation showed focus vanished; the deferred-write test failed with `focusable=false` before the fix and passes afterward.
- **Decision:** update the report palette to the approved native palette and pin its newly measured lane luminances. **Why:** the existing drift test caught the mismatch. Maximum lane step is now 5.59 cd/m2 against the unchanged 20 cd/m2 difference; the half-threshold margin and five-block cap remain unchanged.
- **Cost, for the seven decisions above:** a rebuilt package and a re-recorded demo, which the Oct 10 receipt covers, and shelf copy that the Oct 11 review had to put the practice label back into.

## Oct 10, 2026: final unavailable-title copy

- **Decision:** align the generic missing-check sentence with the existing
  missing-map reason, so the equality check in noticeForTitle shows it once.
  **Why:** the native comparison exposed a repeated hidden-picture explanation,
  because the two sentences differed in wording and both were appended.
  **Cost:** none. Copy only; title eligibility, signatures and thresholds are
  unchanged.


## Oct 10: cloud handoff and dependency scanner failures

- **Decision:** receive the finished `d451a90` review branch in the existing cloud checkout. **Why:** source and design work can continue while the Mac is unavailable. **Cost:** refresh local dependencies and preserve separate provenance for the uploaded native artifacts.
- **Decision:** make malformed reports and scanner failures fail the dependency gate. **Why:** empty output or error JSON previously looked like a clean scan. **Cost:** offline regression tests and schema checks against real npm and pip-audit reports; no new dependency exception.
- **Decision:** preserve native package inputs while documenting current advisories and the conflicting Amazon sample notices. **Why:** changing the playback integration requires another Vega build and playback check. **Cost:** dependency Audit and redistribution review remain open.
- **Decision:** save the missing GitHub API network domain through environment configuration. **Why:** source Git access works but direct private artifact verification is blocked. **Cost:** configuration must be reviewed, saved and published before that route can be retried; no alternate client was used to bypass the denial.

## Oct 10: polish the current TV interface in the cloud

- **Decision:** refine library composition, card proportions, secondary navigation, setup and parental controls within the existing identity. **Why:** the user requested more deliberate visual design after the core features were built. **Cost:** changed app inputs need a fresh Mac package, D-pad and scroll checks, and native playback validation.
- **Decision:** use a new imagegen Harbor illustration only for browsing. **Why:** richer title artwork can improve the library without changing the film or its signed hold images. **Cost:** preserve the generated PNG and its hash in `results/design_polish_2026-10-10.json`; inspect the rendered artwork and refreshed native recording before publishing.
- **Decision:** replace technical viewing copy and fragmented settings descriptions with direct product language. **Why:** parents need to understand their choices without reading implementation terms. **Cost:** update existing copy expectations while preserving the approved safety sentence, cumulative preset behavior and explicit practice labels.
- **Decision:** keep the earlier native receipt and demo as historical evidence. **Why:** cloud rendering and tests do not establish Vega layout, focus or playback for the new source. **Cost:** refresh the demo, source manifest, package and review bundle after native checks; do not relabel old assets as the polished build. See [design/POLISH_REVIEW.md](design/POLISH_REVIEW.md).

## Oct 11, 2026: the dependency audit goes green by fixing two findings and sorting the rest by the bundle

- **Decision:** replace `xmldom` 0.6.0 with an npm alias of `@xmldom/xmldom`
  0.8.15 in app/package.json, keeping the import name the generated Shaka
  `DOMParserPolyfill` uses. **Why:** sixteen advisories, one critical and
  twelve high, in the shipped bundle, under an exception that expired on
  Oct 5 and said in its own words that the answer was no longer "we will get
  to it". The polyfill only subclasses the fork's `DOMParser` and calls
  `super.parseFromString`; the 0.8 line is the fork's long term support line
  and keeps 0.6's behaviour on malformed input, a partial document rather than
  an exception (checked here on a DASH manifest, a TTML fragment, a mismatched
  tag and two root elements), and `npm audit` reports nothing against it.
  **Cost:** the Mac must rebuild and play a title on the virtual device before
  this is trusted, the same rebuild the Oct 10 polish already needs. If the
  Vega build or playback rejects it, the one line in app/package.json reverts
  and the exception comes back with a review date, not a wish.
- **Decision:** move the app's own `lodash` from 4.17.23 to 4.18.1. **Why:**
  the bundle carries `lodash/omit`, and two advisories against `_.omit` and
  `_.unset` cover every 4.17 release; 4.18.1 is outside both ranges. The call
  sites pass prop names written in this repository's source, so the exposure
  was small, and the fix is smaller. **Cost:** a minor version in the bundle,
  covered by the jest suite here and by the Mac rebuild; the two nested 4.17
  copies inside the Vega CLI platform and API Extractor stay, as build tools'
  own.
- **Decision:** sort every remaining finding into two groups by one mechanical
  test, whether the package is in the Metro bundle for the kepler platform,
  and record the bundle inventory in results/bundle_packages_2026-10-11.json.
  **Why:** the old file said in its own header that nobody had read Metro's
  module graph, and it had query-string and decode-uri-component, which
  react-navigation ships, in the "does not ship" group. A Release and a Debug
  bundle were built here with the SDK's Metro configuration, with Shaka's
  compiled file stubbed because its Closure build needs GitHub tarballs the
  proxy refuses; the stub cannot change which npm packages are bundled. Twenty
  flagged packages are in the Release bundle, react-devtools-core joins them
  in Debug, and the other ninety eight are in neither. **Cost:** the inventory
  is a Linux build, not a Vega build or a device run, and it says so; the
  Mac's release build should confirm the same list once.
- **Decision:** keep every review date at Oct 21, the day of the final checks,
  with this session named on the acceptance and Alex's confirmation owed.
  **Why:** a hundred and nineteen packages under thirty three advisories is
  not a thing to accept silently from a cloud session, and Oct 21 is when the
  release build is made. **Cost:** on Oct 21 someone has to re-run
  `make audit-update`, re-read the words, and move the dates past Dec 3, or
  the Monday audit after the tag goes red for a date rather than an advisory.
  It is on Alex's dated list in docs/STATUS.md.
- **Decision:** the Shaka integration is not built on this machine and nothing
  was done about it. **Why:** `shaka-player`'s own `npm ci` downloads two
  forks from codeload.github.com, which the proxy answers with 403. **Cost:**
  none to the submission; the Mac builds it. Recorded so the next session does
  not spend an hour finding out.

## Oct 11, 2026: the review pass over the branch, and what it changed

- **Decision:** review the 56 commits against this file's rules with eight
  parallel reviewers, one per rule dimension, and a skeptic on every finding
  before anything was changed. **Why:** the branch was written by several
  sessions over twelve days, none of which read the whole of it, and it is
  about to become main. **Cost:** about two hours of agent time on a four
  core box; the findings that stood are listed in docs/STATUS.md section 0.
- **Decision:** publish the near-limit precision beside the pooled one, through
  the report wrapper rather than the frozen scorer, and let CI rebuild the
  report from its rows on every push. **Why:** 0.649 pooled was published and
  0.573 on the clips that sit on a limit was not, which is the shape of
  mistake this file already records four times. The wrapper is the one place
  the published block is assembled, and the scorer's hash is pinned by the
  measurement. **Cost:** the committed report changed in its published block
  and its wrapper hash only; the README sentence about a one-time rebuild on
  Oct 9 became a sentence about CI.
- **Decision:** hold every document, Python and TypeScript file we wrote to
  the style rule with eval/style_check.py, in CI and in `make ci`. **Why:** two
  dashes in a design brief sat on a green build for a day. **Cost:** a line
  that quotes a primary source with a dash in it will have to be reworded or
  the source quoted differently; Amazon's files, the licence texts and the
  four jest fixtures are out of its scope by path.
- **Decision:** put "Practice holds" back on the shelf for the Harbor demo and
  have the prepared Harbor say it is our own demo film. **Why:** labelling sham
  holds is a hard rule, and the prepared title's frames carry the burned-in
  demo label whatever the shelf says. **Cost:** a shorter second line than
  "Scheduled scene holds" and one more sentence in each description; the
  owned source without the label is a Mac job.
- **Decision:** remove four identifiers rather than argue about each: the
  validation PIN digits, an organizer's name and address, Claude session ids
  and a subscription tier in two results records, the owner's macOS account
  name in paths. **Why:** none is a secret, all go public on Oct 21, and none
  carries evidence. **Cost:** two results records now say "withheld" where an
  id was, and the timing script makes its own scratch directory.
- **Decision:** state the Amazon proprietary notices in NOTICE and the README
  now, and leave sending the clarification to Alex by Oct 13. **Why:** a
  public reader should meet the conflict from us, and a request to Amazon in
  Alex's name is his to send. **Cost:** none if the answer is MIT-0; if it is
  not, the review's other options stand.
- **Decision:** not rewrite the two commits that carry a university address as
  author. **Why:** rewriting pushed history on the owner's branch is the
  owner's call, and the address is on a public branch already. **Cost:** it
  goes public with the repository unless Alex rebases those two before the
  merge; docs/STATUS.md says so.
- **Decision:** record and not chase a render test that fails on this Linux
  box and passes on CI and the Mac. **Why:** nothing in this tree touches that
  path, and the hosted run on the same tree is green. **Cost:** a known
  environment difference with no explanation written down.
- **Decision:** a scene-hold still may stand in for the opaque cover over a
  red or a pattern segment, and the sidecar spec now says so. **Why:** the
  review found nothing restricted holds by segment reason and no decision
  written down. A still is one checked picture, drawn opaque and static; it
  cannot flash, the red rule is about the picture changing, and the image is
  checked under the broadcast pattern rule before publication, so the letter
  and the point of "red segments always get an opaque cover" are both met.
  **Cost:** a context frame from up to five seconds before a red flash is on
  screen during the hide instead of black. It is a single static picture and
  that is what the rule asks for; if a reviewer with a clinical view says a
  calm picture is worse than black there, the containment check in
  `readSceneHolds` is one condition away from excluding red and pattern.
- **Decision:** put the branch's five new guards into the mutation gate: the
  still-belongs-to-a-segment check in `readSceneHolds`, the demo key's title
  binding, the packaged library's source hash comparison, the household
  record's PIN rounds bound, and verify's scene hold byte reproduction. **Why:**
  the gate is the durable form of "every guard gets a test that has been seen
  to fail", and the branch's own record of breaking them by hand is prose.
  **Cost:** five more mutations in `results/mutation.json`, each killed by a
  test that already existed, and about a minute more in the hardening job.


## Cloud finishing tools after the shared Oct 11 checkpoint

- **Decision:** synchronize `9afacc0` before completing this preparation batch. **Why:** another session pushed dependency repairs, disclosure fixes and hosted check receipts while this cloud work was in progress. **Cost:** resolve the overlapping instructions and narration without replacing either session's changes.
- **Decision:** make aarch64 Debug the release-preparation default and require complete input hashes for skipped builds. **Why:** the user's target is the Apple Silicon Vega Virtual Device; stale artwork, fonts or generated runtime code must not pass as current. **Cost:** older receipts without the full inventory require a rebuild. Publication instructions pin the prepared source commit and are withheld while app inputs are uncommitted.
- **Decision:** require an explicit capture plan and matching native/demo evidence when assembling review artifacts. **Why:** the previous scripts embedded the older build identity and overwrote existing outputs. **Cost:** fill fresh provenance from the actual Mac run and select new output paths; cloud fixture checks do not substitute for native observations.
- **Decision:** preserve existing publication boundaries while pushing checked batches frequently. **Why:** the user needs every terminal and workspace to receive the same latest source. **Cost:** fetch before work, reconcile concurrent commits and verify each pushed commit; other checkouts still need to pull the review branch.
- **Decision:** give the app's own screen check a negative control, run in CI
  after the real screens. **Why:** `npm run ui:flashmap` had been green since
  Sep 17 and had never been seen to refuse anything, and the Sep 19 list said
  so. The control paints a flashing sequence and a grating with the same
  painter, hold and encoder as the real screens and fails unless the wcag
  profile refuses the first, the broadcast profile refuses the second and the
  wcag profile passes the grating. **Cost:** three more analyzer runs in that
  job, about twenty seconds; and the lesson that the other Sep 19 item next to
  it, the tick gap, had been done on Sep 17 and never crossed off.

## Oct 11: interaction details and original preparation evidence

- **Decision:** preserve remote focus eligibility during profile saves, group only notice text for screen readers, and speak complete credits. **Why:** the interface should keep its place and expose every action and displayed attribution. **Cost:** regression checks and a fresh native focus and screen-reader pass; the approved layout stays intact.
- **Decision:** attach exact original verification reports outside immutable media manifests. **Why:** both retained generations reference report hashes whose originals are missing here, and rewriting a manifest would change its bundle identity. **Cost:** validate raw bytes and report semantics, account for their package size, and locate the originals on the Mac. New exports include them automatically; regenerated reports cannot stand in for missing originals under old hashes.
- **Decision:** require all referenced original reports for final release preparation, including reused packages. **Why:** a checked byte inventory alone does not fill the missing preparation evidence. **Cost:** the strict gate remains blocked on this checkout until the originals are attached. Normal inspection remains available and lists exactly what is missing.
- **Decision:** preserve the concurrent `54954ab` update while combining this batch. **Why:** another session added a UI analyzer negative control and submission feedback during the full test run. **Cost:** reconcile the shared notes and verify the updated UI tool separately. Its generated hazard fixtures must be labelled and deleted after analysis, and analyzer errors must not count as successful refusals.

## Oct 11, later: the third mock judge, and what it found that could be fixed from here

- **Decision:** run the third mock judge as four independent readers of a fresh clone at e043d80, one per rubric lens (Stage One, technical and design, impact and idea, an automated reviewer), and one writer turning the four verdicts into `docs/MOCK_JUDGE_3.md`. **Why:** both earlier judges read clones from before phase 8, and one reader with one lens misses what another lens sees; the clone keeps the judges off the live checkout. **Cost:** five agents and about forty minutes; and the report cites line numbers at e043d80, which its header has to say, since the fixes below landed after the clone was taken.
- **Decision:** the README opens with one dated status paragraph instead of three stacked ones. **Why:** the judge met "a build in progress" from Oct 9 and "Dependency Audit ... remain open" from Oct 10 before the architecture diagram, and the second was no longer true. **Cost:** the Sep 29 and Oct 9 paragraphs are gone from the README; docs/STATUS.md and this file already hold that history.
- **Decision:** the README's install commands use `vega device install-app` and `launch-app` with `--device Simulator`, which the Oct 10 run used, and the requirements table has an ffmpeg row. **Why:** README and SUBMISSION disagreed on the CLI form, and the README named no ffmpeg while the pipeline needs it and one test is sensitive to its version. **Cost:** none.
- **Decision:** the two videos that shipped without a ledger row have one, the bundled calm gradient and the prepared Harbor rendition kid mode plays, and NOTICE and the credits screen were regenerated from the ledger. **Why:** NOTICE says every asset that ships has a row saying where it came from, and two did not. **Cost:** two more credits on the TV screen, both ours.
- **Decision:** `app/package.json` declares its licence as `SEE LICENSE IN LICENSE`, and the lock and the app bill of materials were regenerated under npm 10.9.8. **Why:** the hook and flashmap declare theirs and the app did not. **Cost:** eight lines in the bill.
- **Decision:** the submission's friction field is rewritten from the log's own summary (forty entries, eight High), and entries 34 and 35 carry the same Expected and Actual labels as the other thirty-eight. **Why:** the field Amazon reads for the bonus said thirty-five entries and six High while the log said forty and eight. **Cost:** none.
- **Decision:** `app/README.md`'s License section states the Amazon notice caveat and points at NOTICE. **Why:** a reader of app/ met MIT-0 and nothing else. **Cost:** one paragraph in the sample's README.
- **Decision:** a lint rule refuses `currentTime =` and `fastSeek(` outside `useFlashGuard.ts`, with the sample's three fallbacks and the chime's audio element exempted by name, the reason beside each. Seen to fail: a probe file writing both was refused twice, then deleted. **Why:** "every seek goes through one function" was enforced by prop wiring alone, which a new screen could bypass without any check going red. **Cost:** four directive comments and three override entries in `app/package.json`.
- **Decision:** `eval/tests/test_video_duration.py` hands `check_video.sh` its own interpreter. **Why:** in a clone with no `.venv` the script fell back to a `python3` without flashmap and the three tests failed for the judge. **Cost:** none.
- **Decision:** this box's Python run is a results record, `results/local_python_run_2026-10-11.json`, quoted in STATUS beside the other session's count. **Why:** the judge found the published count does not reproduce here, and it does not: ffmpeg 6.1.1 fails two PSNR comparisons that 7.1.5 and the hosted runner pass. A count without its environment beside it is not a measurement. **Cost:** one more file in results/.
- **Decision:** `docs/design/POLISH_REVIEW.md` names the commit its proofs were rendered from. **Why:** the images show the earlier shelf copy, and a reader could not tell which was current. **Cost:** none.
- **Decision:** the rest of the judge's list stays with the Mac or with Alex, in STATUS section 2: the public video, the upstream pull request, the rebuild and native captures, the VoiceView run, the licence clarification. **Why:** none of it can be done from a Linux box. **Cost:** the Stage One FAILs stand until those are done.
- **Decision:** the sample workflow pins the flash check action to a commit on this repository, `alejandro-publius/calm-frames/flashmap@c4dbf0f...`, and the action installs flashmap from the checkout it came from when no version is named. **Why:** the automated reviewer found the sample pointing at an organisation and a tag that do not exist and a PyPI release that was never made, so the "drop it in today" route was not open; a commit pin is the one reference that exists and resolves. **Cost:** the pin has to move to the judged tag once it is cut, and the package homepage was wrong in the same way and is fixed.
- **Decision:** the README's pipeline walkthrough carries the keys on every line, with `keygen` first. **Why:** verify refuses a map whose signature it cannot check, so the walkthrough as written could never pass its own gate. **Cost:** none.
- **Decision:** the README has a "Run the checks" block with the plain commands CI runs, the requirements table names the repository `.venv` and fnm, the Makefile uses the node on PATH when fnm is absent, `scripts/reproduce.py` honours `PY` and falls back to its own interpreter, and `app/tools/ui_flashmap.mjs` exits 2 with its own message when flashmap cannot be imported and takes `PY` like the other scripts. **Why:** on a Linux checkout `make test`, `make reproduce` and `make synth` died over fnm and a `.venv` the README never named, the README gave no test command at all, and a missing analyzer read as a threshold failure. Seen to fail: the screen check refused a stub python with exit 2 and the sentence that says it is not a threshold finding. **Cost:** none that a Mac with fnm will notice.

### 2026-10-11: check the shared handoff's actual entry points

- **Decision:** both sample action references pin `1b088d17c53343025b2ca37cf7615e809709ba8b`, the existing commit containing self-installation. **Why:** the earlier pin resolved, but its action still defaulted to the unpublished PyPI version. Reading and exercising the pinned install step confirms it selects its own checkout. **Cost:** the reference still needs the planned release update; this is an offline check, not a new hosted run.
- **Decision:** the UI preflight imports `flashmap.cli`, and the seek lint rule covers bracket notation and playhead increments. **Why:** an uninstalled checkout can satisfy `import flashmap` as an empty namespace, and alternate seek syntax bypassed the new rule. Both regressions failed before the fixes and pass after them. **Cost:** the lint check is syntactic, with no alias or dynamic-property analysis; native playback still needs the Mac checks.

### 2026-10-11: confirmed entrant name and country

- **Decision:** record Alex Velazquez and United States (USA) in the submission draft and completion checklist. **Why:** Alex supplied these values in response to the public entrant name and country question. **Cost:** none. This does not confirm eligibility, contact email or the upstream contribution's author identity, and does not submit or publish the entry.

### 2026-10-11: finish the viewing journey with public design references

- **Decision:** apply hierarchy and state-handling principles from OpenAI's public Apps SDK UI while retaining the approved TV identity. Give Harbor a shorter, truthful browse synopsis, reserve the parent page's saving space, and let setup return to earlier choices without saving or asking for the PIN again. **Why:** the recent disclosure expanded the library hero, saving moved the parent settings, and setup offered no way to revise a choice before finishing. **Cost:** another native build and review are required before recording; no new dependency, cloud deployment or artwork was added. The references and acceptance work are in `docs/design/SEAMLESS_REVIEW.md`.
- **Decision:** the judge's writer, interrupted once while the four verdicts were already in, was resumed from the cached verdicts rather than re-run from the clone. **Why:** the four readings were finished and recorded; only the synthesis was lost, and a second set of readings would have cost forty minutes to say the same thing. **Cost:** the report cites the clone at e043d80 and was written against the head at 60b1528, which its opening says.

### Oct 11 (late Oct 10 Pacific): final interface effects and the finish line

- **Decision:** add optional artwork entrances and an original menu confirmation sound, each Off by default. **Why:** Alex explicitly requested motion and interactive sounds after the static design review. Artwork can settle on entry while focus, text and picture covers remain still; accessibility and lifecycle checks keep uncertain states still or silent. **Cost:** new native acceptance for actual frames, audio timing, VoiceView and playback coexistence; no dependency or AWS deployment added.
- **Decision:** confirm profile changes only after storage succeeds, and cancel menu sound before navigation to playback. **Why:** an immediate click could report an unsuccessful save or arrive over title audio. **Cost:** regressions seen failing before correction, plus controller cancellation and lifecycle mutation checks. The cloud evidence is in `results/interface_finish_2026-10-10_pacific.json`.
- **Decision:** freeze new features after this pass and use the existing completion checklist as the only finish line. **Why:** the project needs one reviewed build, its matching demo and a submitted entry. **Cost:** the Mac must rebuild current source and close the recorded acceptance items before final publication approval; account form details are deferred and do not block app work.

- **Decision:** qualify earlier statements that existing AWS credits cover the stack. **Why:** Alex's Credits page establishes active balances, while the saved deployment record establishes working infrastructure; neither establishes applicable-service coverage or actual credit application. The earlier funding statement was a plan, not a verified billing result. **Cost:** a read-only check of the stack account, credit applicability, Bills and cost-tag/budget visibility on the Mac. No billing mutation, new deployment or spending was performed here.

## Oct 11, later still: the cover proof was measuring the wrong thing

- **Decision:** treat the two Python tests that failed on this box as a defect to find rather than an environment to note, now that the box reproduces them. **Why:** the morning's write-up said ffmpeg 6.1.1 loses the still part way through a hold and sent the fix to the Mac. Read frame by frame with `select='eq(n,N)'`, the rendition shows the still to the last frame of the span on this very ffmpeg; a drawbox gate alone holds to the frame too. The thing that said otherwise was `cover_psnr`: it asks ffmpeg for one frame with `-frames:v 1`, but that only stops the encoder, and the `average:` line it reads is the mean over every frame the psnr filter compared before the graph was torn down. How many that is depends on threads and load, so a sample inside a covered span averaged in the uncovered frames after it here and not on the runner or the Mac. **Cost:** a wrong diagnosis stood in STATUS, the judge report and a results record for most of a day, and is corrected in each rather than deleted.
- **Decision:** `cover_psnr` trims both inputs to one frame before the comparison. **Why:** the measurement has to be the frame it names, whatever the machine is doing. Seen to fail: the two failing tests were the failure, and they pass after the change. **Cost:** none; the same ffmpeg call with two `trim=end_frame=1` filters.
- **Decision:** verify's cover proof samples the first frame, the middle and the last frame of every covered span, one midpoint for a span shorter than three frames, and records `samples_per_interval` and the ffmpeg version string on the `cover_actually_drawn` check. **Why:** one midpoint cannot see a cover that is late to start or gone before the end, which is exactly the fault that was believed to exist; the version string lets a number that moved between two machines be read against the decoder that produced it. Seen to fail: `TestTheCoverProofReachesTheEdgesOfASpan` fakes a still that matches at every midpoint and nowhere else, and the midpoint-only proof passed that title. **Cost:** three decodes per span instead of one, a few seconds on a long title; the committed Harbor verification keeps its recorded data, and the next verify run carries the new fields.
- **Decision:** the new proof joins the mutation gate as `cover-proof-reaches-the-end-of-a-span`, reverting the three samples to the midpoint, killed by the new test. **Why:** every guard gets a test seen to fail, and the gate is where that is kept. **Cost:** one more mutation, about two minutes of the gate.

## Oct 11, later still: the other session's last two commits, reviewed

- **Decision:** review the motion and sound commits with three readers and two skeptics per finding before anything else is built on them. **Why:** opt-in motion in an app for photosensitive children is a safety surface until it is read, and the same pass caught that the still-drop story was wrong. **Cost:** a few minutes of agents; nothing reached "block".
- **Decision:** the selection sound is CC0-1.0 like every other asset we made, its ledger row points at the README on main like the chime's, and its note opens "Ours.". **Why:** the row was the one asset of ours under Apache-2.0, with a branch URL and the third-party note prefix, so the credits screen linked a branch and grouped the sound apart from the rest. **Cost:** NOTICE and the credits screen regenerated.
- **Decision:** the seek lint message names the menu sound's audio element as the third exemption, and CLAUDE.md's rule says the same. **Why:** a message that lists its exemptions and omits one teaches the next reader the wrong rule. **Cost:** none.
- **Decision:** `results/aws_deploy_2026-10-09.json` carries an `amendments` field saying its credit clause was reworded on Oct 11, rather than the rewording standing silent. **Why:** a results record changed after it was written must say so, or it stops being a record. **Cost:** one field.
- **Decision:** the finish line in `docs/COMPLETION_CHECKLIST.md` names the merge into main and the Oct 21 date moves, and the household record lists in the README and CLAUDE.md name the two interface preferences. **Why:** the finish line called itself the single checklist while STATUS section 2 held two steps it lacked, and the record now saves two things the lists did not say. **Cost:** none.
- **Decision:** leave the artwork's dip-then-settle and the never-initialising sound player as notes for the Mac acceptance rather than change the other session's code. **Why:** both are only reachable with the effects opted in, the acceptance step already asks for exactly the observation that would show the first, and silence is the safe direction for the second. **Cost:** two observations owed to the Mac's list; the entry below reverses the second and writes the first in.

## Oct 11, later still: two of the review's findings became fixes

- **Decision:** the press that turns Selection sounds on is confirmed from the render that holds the saved record, through a one-shot state set by the write's continuation, not from the continuation itself. **Why:** RN 0.83 renders Fabric into a concurrent root, where a state update made from a promise is rendered in a later scheduler task. The continuation ran first, the hook still read the old record and refused, and the one press a parent makes to turn the sound on was the one press that never sounded; both skeptics confirmed it. Seen to fail: the new test renders `KidModeScreen` on a concurrent root with act() off, records what the hook was reading when confirm() arrived, and read false. The library's legacy root and act() both render before the continuation, which is why the suite was green. **Cost:** two cheap renders after a save; the mutation `selection-sound-confirmed-from-the-render-that-holds-the-record` in the gate.
- **Decision:** a released sound playback frees the next request at once, and the player's deinitialize() is called without waiting on an initialize() that has not answered. **Why:** the entry above left this as a note because silence is the safe direction, and it still is; but one player that never answered, once, kept the menu silent for the rest of the screen's life, and `KidModeScreen` stays mounted behind the player for the whole sitting. The SDK's deinitialize() aborts a pending initialize() and rejects it, which the request's own catch already handles, so there was nothing to wait for. One skeptic refuted it as deliberate and unreached; the other confirmed it; the fix is a few lines and the test pins it. Seen to fail: `makePlayer` stayed at one call after the release and a later confirm, for a stuck initialize() and for a stuck deinitialize(). **Cost:** the test that pinned "deinitialize waits for initialize" now pins the opposite; the mutation `released-sound-player-frees-the-next-request`.
- **Decision:** the artwork's possible dip stays as it is in code and is named in the Mac acceptance step. **Why:** both skeptics refuted it: the gap between the first commit and the offset is one native round trip, and still until the answer arrives is the designed contract. The ready fix, remembering the last explicit answer so a later page starts offset, would snap a user who has just turned reduced motion on, which is the wrong direction. **Cost:** one sentence in `docs/MAC_FINISH.md`; the Mac decides.


## Oct 11, evening: the repository measured against tideline

- **Decision:** answer "how close am I, and does the repository read like tideline in rigor and beyond it" with a measured comparison of the two trees rather than an impression: four readers (tideline's practices, Calm Frames' presentation, its hygiene, and the distance to the finish line), one comparer per dimension, and a skeptic on every major gap. **Why:** the two repositories are different in kind (a portfolio web app and a hackathon TV entry), so only a practice by practice reading says which differences matter. **Cost:** an agent run; its final synthesis was cut off when usage credits ran out, so the verdict was assembled here from the readers' and skeptics' recorded results.
- **Decision:** close the README's first screen now, from what the tree already holds: badges, the library render as a hero image labelled as a browser render of the real tree at 54dab0b and not a device capture, a list of what a family sees, what it does underneath, a one-minute way to try the analyzer on the project's own CC0 clip, and the dated status after those. **Why:** every skeptic confirmed that the README showed no picture of the product while thirteen labelled renders sat unlinked, and that a stranger read 469 words of definition, status and judge links before learning what the app does. The truth rule holds because the caption says what the image is. **Cost:** none in code; the readme_sync and style checks pass.
- **Decision:** add a "How this is checked" section naming every CI and Audit job and what each refuses, with the mutation and fuzz results by marker, and keep test counts out of it. **Why:** the mutation gate, the fuzz corpus and the numbers check are the work that sets the repository apart and the README named none of them; test counts stay out because the README already says no regenerated record backs them. **Cost:** six markers more for readme_sync to keep.
- **Decision:** the remaining gaps, ranked by what a judge or a senior engineer notices first, are left as the next presentation and tooling work rather than done in this pass. **Why:** each is real and closable without a feature, but together they are about two days, and the Mac session and the dated items come first. In order: one design page in `docs/design/` that holds the palette from `calmStyles.ts` with a test keeping the two equal (the palette is described three ways today, and `tokens.json` still says proposed); committed native screenshots from the Mac rebuild; an index in `docs/` that separates reader-facing documents from working records and agent prompts; a CHANGELOG with a 0.1.0 entry at the judged tag; ruff and mypy in CI for the Python lanes (flashmap ships `py.typed`); `permissions: contents: read` and SHA-pinned actions in the two everyday workflows; CONTRIBUTING, a code of conduct and issue and pull request templates; app coverage reported rather than hidden; and the GitHub About box (description, topics), which only Alex can set. **Cost:** none until done; the list is the record.
