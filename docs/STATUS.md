# Status

Updated Thu Sep 17, 2026, late evening PT.

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
| **Before any deploy** | Put AWS on the Paid plan, set the $20 budget alarm, then add the line `AWS Paid plan: confirmed` to this file. | `make deploy` refuses until that line exists and `CHECKPOINT_D=confirmed` is set. Both locks were tested. Nothing has touched AWS. |
| **By Mon Oct 12** | Open the upstream pull request from a fork under your account. | The fix, the test and the PR text are ready in `docs/OPEN_SOURCE_PR.md`. It cannot be opened from here: it needs a fork you own. |
| **Oct 19 to 20** | Film the video from `docs/VIDEO_SCRIPT.md`, timed to 2:55. | |
| **Wed Oct 21** | Make the repo public, then run the final checks. | The rules need it public with the licence visible at submission. |
| **Thu Oct 22** | Press submit. `docs/SUBMISSION.md` has every field, with the ones needing you marked. | |

### The red footage, specifically

Every flagged segment in the screened pool fired the general rule. **Not one fired the red rule.** The pool has no saturated red strobe and no sustained regular strobe, and no free third-party footage was found that covers it. So the clips to film are red emergency-vehicle lights, red stage lighting, and a steady strobe. docs/SAFETY.md applies in full: whoever films is not photosensitive and does not look at the lights.

## 3. A number was published and withdrawn

An earlier status said the GATE 1 rehearsal covered 20 of 20 markers in time, worst lead 449 ms. **It was wrong and it is gone.** The run never played: the player reported positions up to 0.26 s and no further, while the cover scheduler, which runs on a wall clock by design, advanced its own estimate and fired every cover on time against it. The analysis compared two views of the same clock and found perfect agreement.

It surfaced because a second, stricter script needed a position report from the player before counting anything, and returned zero usable trials. Both scripts now refuse to count a marker the player never reached, and a third rule was added after that: a trial where playback stalled between the cover and the marker is recorded and excluded, because the cover being held for forty seconds says nothing about whether the schedule fires early enough. The full retraction is in docs/GATES.md.

## 4. Where each lane stands

**The app.** Countdown card with a D-pad Skip, the cover, the after-card, and a minimum cover length. Fail closed for missing, stale, unsigned, unparseable and wrong-hash maps, with real Ed25519 verification written for Vega, which has no crypto API, checked against RFC 8032 vectors. Seek safety through one function for the seek bar, D-pad, trickplay and Alexa transport commands. VoiceView announcements, a parent area behind a PIN where room settings can only add hides, and a kid home with shield badges. **The app's own UI passes flashmap: 9 screens, 0 segments, checked in CI.** 563 tests, 15 mutations all seen red.

**flashmap.** WCAG general and red flash, area windows, letterbox handling, real timestamps, chunked analysis, the room rule, signed sidecars, the CLI and the GitHub Action. Theora decoding is fixed with a regression fixture. Over 200 tests, 42 mutations all killed.

**The pipeline.** Ingest, hide plan, kid-safe renditions, trickplay and posters from the safe rendition only, signed maps, and a verify step that blocks publishing and was mutation tested. The CDK app synthesizes with zero NAT gateways and a $20 budget alarm, and refuses to deploy.

**Evaluation.** The conformance suite runs with ground truth computed from the spec text in a module that cannot import flashmap. The real-clip labelling pack is ready: 40 segments, 16 titles, 7 sources, blinded, with plots that show no detector output and blank sheets for two labellers. Nobody has labelled anything, which is correct: that is your step and Rachel's.

**Release.** `make test`, `reproduce`, `synth`, `release`, `stick-day`, `hooks` and `scan` all run. `make release` built six packages, staged three architectures with checksums, printed the release command and stopped without publishing.

**Submission.** README, `docs/SUBMISSION.md`, `docs/FRICTION_LOG.md`, `docs/OPEN_SOURCE_PR.md` and `docs/VIDEO_SCRIPT.md` are written, with every number traced to `results/` and checked by CI.

## 5. What is not done

- **No cover lead time on real hardware**, and none is possible until the stick arrives. There is now a software-level figure in `results/gate1_software_vvd.json`: 49 trials, 48 covered in time, median lead 488 ms, and one cover that went on 86 ms late because the JavaScript thread paused for about a third of a second. It is labelled as software-level: it cannot see the React commit, the compositor, scan-out or the panel, so it is an upper bound on how well the real thing can do, never a prediction of it.
- **Fewer than 20 titles pass verify.** Verify refuses titles for real reasons, which is the point of it.
- **EA IRIS is not built**, so the baselines table has ffmpeg and naive but no IRIS. The shared Docker VM has another project's services in it, and a vcpkg OpenCV build there could get their containers killed rather than the compiler.
- **The conformance run is partial**, and `results/conformance.json` says so in its own statement field rather than implying a full 3,000-clip run.
- **The demo PIN does not exist yet**, so the release notes say so.

## 6. The numbers

Every one comes from `results/`, and CI fails if a document drifts from them.

| What | Value | Source |
|---|---|---|
| flashmap precision, partial conformance run | <!--n results/conformance.json:published.flashmap_precision -->0.65<!--/n--> (<!--n results/conformance.json:published.flashmap_precision_lo -->0.605<!--/n--> to <!--n results/conformance.json:published.flashmap_precision_hi -->0.693<!--/n-->) | conformance.json |
| flashmap recall, same run | <!--n results/conformance.json:published.flashmap_recall -->0.895<!--/n--> | conformance.json |
| Clips measured, of 3000 designed | <!--n results/conformance.json:published.clips_kept -->467<!--/n--> | conformance.json |
| Flagged segments in the pool | <!--n results/screening.json:totals.flagged_segments -->432<!--/n--> across <!--n results/screening.json:totals.sources_with_at_least_one_flag -->5<!--/n--> sources | screening.json |
| Red-rule segments found | none | screening.json |
| Longest gap between player position reports | <!--n results/vvd_timeupdate_stats.json:timeupdate.interval_ms.max -->5219<!--/n--> ms | vvd_timeupdate_stats.json |
| Segments ready for blind labelling | <!--n results/realclips_status.json:segments -->40<!--/n--> across <!--n results/realclips_status.json:titles -->16<!--/n--> titles | realclips_status.json |

## 7. Next

1. Send the emails tomorrow.
2. When the stick arrives: `make stick-day`, then film. That is the gate.
3. Meanwhile: more titles through verify, IRIS when the Docker VM frees up, and finish the conformance run.
