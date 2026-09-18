# Status

Updated Thu Sep 17, 2026, late evening PT.

## 0. Where the recovery pass left things

The tree is clean and pushed, and the two suites the CI command runs are green
here: 973 Python tests and 671 app tests. Three things were making CI red and all
three are fixed. The python job never installed matplotlib, so
`eval/tests/test_labeling_plots.py` failed to import and took the whole job down
at collection, which is worse than one red test because it hid the other two
behind it. Under that, a scheduler property was failing for real. And the new
hardening job was red until a full mutation report existed, which it now does. The screening sweep and the ingest chain that were still going have
finished; the re-verify gave <!--n results/verify_pool.json:analyzed -->30<!--/n-->
titles a verdict, which is **<!--n results/verify_pool.json:cover_proven_drawn -->7<!--/n-->
with the cover proven drawn, <!--n results/verify_pool.json:no_flagged_segments -->14<!--/n-->
with no flagged segment at all and <!--n results/verify_pool.json:failed -->9<!--/n-->
failed**. Every title that passed has a row in `media/LICENSES.csv`.

Two defects came out of the recovery rather than out of a plan, and both are the
kind that a green suite was hiding. The media clock kept running through every
buffer, because `waiting` was missing from the list of events that stop it while
`stalled` and `pause` were on it; a four second buffer left the estimate 4,000 ms
ahead of the playhead. The picture stayed covered throughout, so this was never a
hole in the cover, but every number taken off that clock, which is the drift and
the cover lead GATE 1 reports, was wrong by the length of the buffer. Separately
the property harness was answering a seek that lands inside a stall with a
position report a stalled player never sends, which is what the 75 ms failure
was. Both are fixed, both were seen red first, and the estimate error across
every case probed is now 0.00 ms rather than merely inside its bound. The full
mutation gate ran for the first time and then again after the fixes: 57
mutations, 55 killed, and the 2 that live are both declared equivalent with
their reasoning in the file. The third survivor of the first run was a real gap
in the property tests and is closed.

## 1. The head-start kits are still not here, asked for twice

**`day-one-head-start.zip` is not on this machine.** Not at the repo root, not in `~/Downloads`, nowhere within four levels of your home folder, and Spotlight finds nothing by that name. `headstart/` is still the empty directory from day one. Neither `rubric-amazon.md` nor `outreach-kit.md` is here.

They were meant to be the test oracle: the kit's flashmap tests to run against ours, spec-exact WCAG and BT.1702-3 numbers to diff our thresholds against, the clip pool in STRESS_TEST.md and the Vega API sheet. Everything they were meant to bring has been built here instead, listed in docs/PLAN.md.

**If the zip exists, the fastest fix is to tell me the exact path.** If it is gone, nothing is waiting on it. What stands in for it: docs/SPEC_SOURCES.md quotes a primary source for every threshold and names what could not be verified, and the conformance suite computes its ground truth from the spec text in a module that cannot import flashmap.

## 2. What you have to do, in order, with dates

| When | What | Why it needs you |
|---|---|---|
| **Fri Sep 18** | Send the three outreach emails in `docs/outreach/`. | Each needs a recipient and your name. They ask only about wording and flow, and say plainly that nothing we send contains flashing. |
| **When the stick arrives, about Sep 20** | Update it to Vega OS 1.2, turn on developer mode, plug it in by USB, then run `make stick-day`. | The whole measurement chain waits on real hardware. The script prints the developer-mode steps, refuses a wrong OS build, installs, runs the layering test and then the marker run. It took about 6 minutes end to end against the virtual device. |
| **Same session** | Film the layering test, then the 240 fps marker run. | **This is the only thing that can produce a GATE 1 number.** Phone at 240 fps, exposure locked, TV in game mode with motion smoothing off. `make stick-day` prints what to film and where the files go. |
| **Before then** | Confirm your phone films 240 fps and the TV has a game mode. | Assumed, never confirmed. If either is wrong, GATE 1 needs a different plan and it is better to know now. |
| **By Thu Sep 24** | Film the red footage, described below. | Nothing else in the pool covers it. |
| **Any evening, about an hour** | Label the 40 blinded segments. You take `eval/labeling/labels_labeller_a.csv` and all 40. Rachel takes `labels_labeller_b.csv` and at least seg000 to seg014. Neither of you talks about a segment until both sheets are saved, and neither opens `pool_key.json`. | The pack is ready and nobody has labelled anything, which is correct: this is the step that turns the detector's output into a measured number instead of its own opinion. `eval/labeling/GUIDE.md` has the commands for afterwards, in order. Kappa and the bootstrap run the moment the sheets are in. |
| **Before any deploy** | Put AWS on the Paid plan, set the $20 budget alarm, then add that line to this file. It has to start a line of its own: no bullet, no table cell, no backticks. The exact wording is in the refusal `make deploy` prints. | `make deploy` refuses until that line exists and `CHECKPOINT_D=confirmed` is set. Seventeen tests now cover both locks, run against a copy of the script so this file is never touched. Nothing has touched AWS. |
| **By Mon Oct 12** | Open the upstream pull request from a fork under your account. | The fix, the test and the PR text are ready in `docs/OPEN_SOURCE_PR.md`. It cannot be opened from here: it needs a fork you own. |
| **Oct 19 to 20** | Film the video from `docs/VIDEO_SCRIPT.md`, timed to 2:55. | |
| **Wed Oct 21** | Make the repo public, then run the final checks. | The rules need it public with the licence visible at submission. |
| **Thu Oct 22** | Press submit. `docs/SUBMISSION.md` has every field, with the ones needing you marked. | |

### The red footage, specifically

Every flagged segment in the screened pool fired the general rule. **Not one fired the red rule**, across 456 flagged segments. The pool has no saturated red strobe and no sustained regular strobe, and no free third-party footage was found that covers it.

Five clips, listed with their rates in `results/screening.json` under `self_filmed_needed`, all still needed. The rates are multiples of the analyser's own per second limit, read from the wcag profile rather than typed in:

| Clip | Rate | Length | What it is |
|---|---|---|---|
| `red_emergency_lightbar` | 6 a second | 30 s | A red emergency vehicle light bar filling most of the frame, head on after dark or against a dark wall. The red has to be the lamp, not a red wash on something pale. |
| `red_stage_wash` | 4 a second | 30 s | A red stage or party light washing the whole frame, chased on and off, close enough that red fills the picture. The red positive near the limit. |
| `red_below_the_limit` | 2 a second | 20 s | The same rig as above, flashing slowly, nothing else changed. **The red negative control**: without it a red flag only says the picture was red. |
| `white_strobe_steady` | 10 a second | 30 s | A white strobe on a plain wall, one steady rate for the whole take. Nothing in the pool holds a rate for more than a second or two. |
| `strobe_small_area` | 10 a second | 20 s | The same strobe as a small lamp in a wide shot, flashing part about a tenth of the picture. The area rule negative. |

Filming notes: 60 fps if the camera has it, shutter and exposure locked because a rolling shutter can record a rate that was not in the room, no auto exposure, one take each, no grading, and write the rate actually set into `media/LICENSES.csv`. **docs/SAFETY.md applies in full: whoever films is not photosensitive and does not look at the lights.**

## 3. A number was published and withdrawn

An earlier status said the GATE 1 rehearsal covered 20 of 20 markers in time, worst lead 449 ms. **It was wrong and it is gone.** The run never played: the player reported positions up to 0.26 s and no further, while the cover scheduler, which runs on a wall clock by design, advanced its own estimate and fired every cover on time against it. The analysis compared two views of the same clock and found perfect agreement.

It surfaced because a second, stricter script needed a position report from the player before counting anything, and returned zero usable trials. Both scripts now refuse to count a marker the player never reached, and a third rule was added after that: a trial where playback stalled between the cover and the marker is recorded and excluded, because the cover being held for forty seconds says nothing about whether the schedule fires early enough. The full retraction is in docs/GATES.md.

**The re-run worked, and it found something.** On a packed clip across 22 app launches: 49 usable trials, 48 covered in time, median lead 488 ms against a 500 ms guard band. One cover went on 86 ms **after** its marker started. The scheduler re-anchors on every position report and re-checks every 50 ms, so that is the JavaScript thread being unavailable for about a third of a second, not a scheduling error. It means the guard band has to be wider than the worst pause of that thread and nobody has measured that pause on hardware. This is still software-level and stays labelled that way.

**A second wrong number was caught before it was written down.** Rebuilding that summary from its own events by splitting the passes on each `harness-start` gave 54 trials and a 13.3 s lead, because two passes opened with a batch the previous app instance posted late. The right split is the per-pass event counts the summary records. `eval/verify_gate1_archive.py` now does that rebuild in CI and was checked by breaking it five ways.

## 4. Where each lane stands

**The app.** Countdown card with a D-pad Skip, the cover, the after-card, and a minimum cover length. Fail closed for missing, stale, unsigned, unparseable and wrong-hash maps, with real Ed25519 verification written for Vega, which has no crypto API, checked against RFC 8032 vectors. Seek safety through one function for the seek bar, D-pad, trickplay and Alexa transport commands. VoiceView announcements, a parent area behind a PIN where room settings can only add hides, and a kid home with shield badges. **The app's own UI passes flashmap: 20 screens and transitions, 0 segments, checked in CI.**

**Kid mode is reachable.** The app opens on Calm Frames: the first run sets a PIN, a preset and the room, then the shelf, a title, and the parent area behind that PIN. The shelf hands the player the map it verified, and the player itself now refuses to show a picture without one, so the five sample screens that still navigate to it the old way get a black picture and a card saying the title is not checked. A first run, empty and error states for every screen, and a ten foot pass measured rather than eyeballed: 32 units is the smallest text anywhere, 5.12 to 1 the worst contrast, 96 by 54 units the safe margins on every screen. The virtual device cannot be photographed, so those are measurements off the rendered screens, in `app/build/ui-capture/ten-foot.json`. 671 tests, and every new guard was broken on purpose and seen red before it was trusted.

**flashmap.** WCAG general and red flash, area windows, letterbox handling, real timestamps, chunked analysis, the room rule, signed sidecars, the CLI and the GitHub Action. Theora decoding is fixed with a regression fixture. Over 200 tests, 42 mutations all killed.

**The pipeline.** Ingest, hide plan, kid-safe renditions, trickplay and posters from the safe rendition only, signed maps, and a verify step that blocks publishing and was mutation tested. The CDK app synthesizes with zero NAT gateways and a $20 budget alarm, and refuses to deploy.

**Infrastructure and security.** The ingest container exists: ARM64, base image pinned by digest, every Python package installed from a hash, not root, and an entrypoint that publishes nothing unless verify passed and uploads only an allowlist, so the source master and the cover model video cannot leave the task. `make deploy` is one command that deploys the stack and then pushes the image, and it still refuses. The estimate for running it is about $1.34 a month against the $20 alarm, with its assumptions in docs/DECISIONS.md. docs/SECURITY.md now opens with a threat model and ends with what has never been run. pip-audit is clean; npm audit's 59 packages are the pinned Vega toolchain and each one is accounted for in writing with a review date. Three CycloneDX bills of materials, checked in CI. A map signed by a revoked key is refused by the app, and that test was seen to fail three ways.

**Evaluation.** The conformance suite runs with ground truth computed from the spec text in a module that cannot import flashmap. The real-clip labelling pack is ready: 40 segments, 16 titles, 7 sources, blinded, with plots that show no detector output and blank sheets for two labellers. Nobody has labelled anything, which is correct: that is your step and Rachel's.

**Release.** `make test`, `reproduce`, `synth`, `release`, `stick-day`, `hooks` and `scan` all run. `make release` built six packages, staged three architectures with checksums, printed the release command and stopped without publishing.

**Submission.** README, `docs/SUBMISSION.md`, `docs/FRICTION_LOG.md`, `docs/OPEN_SOURCE_PR.md` and `docs/VIDEO_SCRIPT.md` are written, with every number traced to `results/` and checked by CI.

## 4b. Running right now, and what is still open

**A chaos re-run is in flight** and will write `results/chaos_vvd.json` when it
finishes, in about twenty minutes from 22:30 PT. The committed run is honest but
thin: 16 passes, 157 rude actions, every pause, seek and stall met by the
fail-safe cover, but only **3 marker crossings**, because `markers50.mp4` puts its
first marker at 4000 ms and a rewind under chaos is a 10 second seek, so 14 of 16
passes never got the playhead that far. The re-run uses `markers_packed.mp4`,
whose first marker is at 2000 ms, and should give 20 to 30 crossings in the same
time. **Nothing quotes the 3 crossing run and nothing should.** If the re-run
comes back thin too, say so and leave the claim unmade.

Two limits of that harness are recorded in the file and are not fixed: no segment
request ever stalled, because the whole clip is fetched before the 9 second settle
ends, so the network chaos reached a player that had already buffered everything;
and backgrounding never happened, so `background_covers_seen` is 0.

**Still open, in rough order of what would help most:**

1. **The early covers are not capped.** The p95 lead is 4097 ms and the longest is
   6197.5 ms against a 500 ms guard band. A cover four seconds early is safe and it
   is not the schedule working, it is the cover firing whenever the next position
   report happened to arrive. Capping it would mean delaying the cover on a player
   whose reports can be 5219 ms apart, which trades the thing this app exists for
   against a cosmetic gain, so it has not been done. If it is done, the cap has to
   be measured against the worst report gap, not chosen.
2. **Fixed, Sep 17 late.** `pipeline/verify.py` used to skip its own cover check
   when a title had no flagged segment, so
   <!--n results/verify_pool.json:no_flagged_segments -->14<!--/n--> titles
   collected 38 passing checks without covering anything and read like the
   <!--n results/verify_pool.json:cover_proven_drawn -->7<!--/n--> whose cover
   was measured. Those titles now carry the outcome `no flagged segments`, and a
   preset with intervals cannot pass unless the drawn check ran for it and
   passed. The counts are in `results/verify_pool.json`.
3. **EA IRIS is still not a candidate list**, so the recall estimate is optimistic
   by an unknown amount, and the 16 calm clips are screened but not in the
   labelling pool because only flashmap has looked at them.

## 5. What is not done

- **No cover lead time on real hardware**, and none is possible until the stick arrives. There is now a software-level figure in `results/gate1_software_vvd.json`, and the strict reading is the one to quote: **48 of the 55 trials started covered in time, 0.873**, Wilson 95% 0.760 to 0.937. Six of the seven that did not were dropped for producing no usable evidence and one cover went on 86 ms late, because the JavaScript thread paused for about a third of a second. Counting only the 49 trials that could be measured gives 48 of 49, 0.980, which is the friendlier number and is why both are published. Median lead 488 ms. It is labelled as software-level: it cannot see the React commit, the compositor, scan-out or the panel, so it is an upper bound on how well the real thing can do, never a prediction of it.
- **Only <!--n results/verify_pool.json:cover_proven_drawn -->7<!--/n--> titles
  prove anything about covering.** Of the
  <!--n results/verify_pool.json:analyzed -->30<!--/n--> titles with a verdict,
  <!--n results/verify_pool.json:no_flagged_segments -->14<!--/n--> have
  `covered_ms = 0` and no flagged segment at all: the analyzer looked and found
  nothing over the thresholds, which for gentle cloud and sunset footage is the
  right answer and is not evidence that anything was covered. They now carry the
  outcome `no flagged segments` rather than the same word as the seven, and a
  preset with intervals can no longer pass on a cover check that never ran. The
  seven that exercise the whole path, detect then plan then cover then prove the
  cover drew, are fireworks_rieti, lightning_blackout, lightning_240fps,
  illumination_flares, jezioro_cisie, irminger_waves and dvids_fireworks_safety.
  **Never publish the total on its own.** Adding more calm footage raises it
  without adding evidence. The remaining
  <!--n results/verify_pool.json:failed -->9<!--/n--> failed and cannot play, and
  <!--n results/verify_pool.json:not_analyzed.pending -->1<!--/n--> title and
  <!--n results/verify_pool.json:not_analyzed.no_entry_json -->3<!--/n-->
  directories have no verdict at all, so they are in none of the four counts.
- **EA IRIS is not built**, so the baselines table has ffmpeg and naive but no IRIS. The shared Docker VM has another project's services in it, and a vcpkg OpenCV build there could get their containers killed rather than the compiler.
- **The conformance run is partial**, and `results/conformance.json` says so in its own statement field rather than implying a full 3,000-clip run.
- **The demo PIN does not exist yet**, so the release notes say so.
- **Nothing in the app has been opened on a device since kid mode was wired up.** Every screen, the first run, the play path and the player's refusal are checked in the app's own test suite, and none of it has been seen on the virtual device or the stick. The bundled clip's URI is `file:///pkg/assets/raw/offline/calm_gradient.mp4`, which is where the Kepler file system README says package assets land, and that has never been played.
- **The PIN and the room setting live in memory**, so the first run comes back on every launch. Writing them to `/data` is a small job and a separate one.
- **The hide log has no way back from the player**, so the parent area says nothing has been hidden rather than inventing entries. It needs a store the player screen and the kid mode route share.

## 6. The numbers

Every one comes from `results/`, and CI fails if a document drifts from them.

| What | Value | Source |
|---|---|---|
| flashmap precision, partial conformance run | <!--n results/conformance.json:published.flashmap_precision -->0.65<!--/n--> (<!--n results/conformance.json:published.flashmap_precision_lo -->0.605<!--/n--> to <!--n results/conformance.json:published.flashmap_precision_hi -->0.693<!--/n-->) | conformance.json |
| flashmap recall, same run | <!--n results/conformance.json:published.flashmap_recall -->0.895<!--/n--> | conformance.json |
| Clips measured, of 3000 designed | <!--n results/conformance.json:published.clips_kept -->467<!--/n--> | conformance.json |
| Flagged segments in the pool | <!--n results/screening.json:totals.flagged_segments -->456<!--/n--> across <!--n results/screening.json:totals.sources_with_at_least_one_flag -->6<!--/n--> sources | screening.json |
| Red-rule segments found | none | screening.json |
| Longest gap between player position reports | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms | vvd_timeupdate_stats.json |
| Segments ready for blind labelling | <!--n results/realclips_status.json:segments -->40<!--/n--> across <!--n results/realclips_status.json:titles -->15<!--/n--> titles | realclips_status.json |
| Titles with a verify verdict | <!--n results/verify_pool.json:analyzed -->30<!--/n--> | verify_pool.json |
| Of those, cover proven drawn | <!--n results/verify_pool.json:cover_proven_drawn -->7<!--/n--> | verify_pool.json |
| Of those, no flagged segments | <!--n results/verify_pool.json:no_flagged_segments -->14<!--/n--> | verify_pool.json |
| Of those, failed | <!--n results/verify_pool.json:failed -->9<!--/n--> | verify_pool.json |
| The four add up to the titles on disk | <!--n results/verify_pool.json:adds_up -->yes<!--/n--> | verify_pool.json |

## 7. Next

1. Send the emails tomorrow.
2. When the stick arrives: `make stick-day`, then film. That is the gate. **Add one measurement to it:** the worst gap between two scheduler ticks. The harness re-checks every 50 ms, so logging the longest gap between consecutive checks gives the worst pause of the JavaScript thread, and the guard band should be set above it rather than at the 500 ms we picked by judgement. This is not instrumented yet.
3. Meanwhile: more titles through verify, IRIS when the Docker VM frees up, and finish the conformance run.

---

**Status line, Thu Sep 17 late (infrastructure and security lane).** Everything
for one `make deploy` is ready and still refuses to run. Found and fixed one
lock that had been open since it was written: the guard's grep matched the row
in this file that tells you to add the line. The container build was stopped
part way because it helped push the shared Docker VM into its memory limit and
killed another project's container, which was restarted; the build is verified
on a CI runner from now on. Nothing has touched AWS.
