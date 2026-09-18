# Status

Updated Thu Sep 17, 2026, late evening PT.

## 1. The head-start kits are still not here, asked for twice

**`day-one-head-start.zip` is not on this machine.** Not at the repo root, not in `~/Downloads` (which holds no zip at all now), nowhere within four levels of your home folder, and Spotlight finds nothing by that name. `headstart/` is still the empty directory from day one. Neither `rubric-amazon.md` nor `outreach-kit.md` is here either.

They were meant to be the test oracle: the kit's flashmap tests to run against ours, the spec-exact WCAG and BT.1702-3 numbers to diff our thresholds against, the clip pool in STRESS_TEST.md and the Vega API sheet. Without them there is no independent implementation to check ours against. What we have instead: docs/SPEC_SOURCES.md quotes primary sources for every threshold and names what could not be verified, and the conformance suite computes its ground truth from the spec text in a module that cannot import flashmap.

**If the zip exists somewhere, the fastest fix is to tell me the exact path.** If it is gone, nothing is waiting on it.

Rather than wait, everything they were meant to bring was built here:

| Missing kit | What replaced it |
|---|---|
| flashmap | `flashmap/`, written from scratch, 200 tests, every threshold quoted in docs/SPEC_SOURCES.md |
| calm-timing | `eval/marker_clip.py`, `eval/vvd_timing_run.py`, `eval/gate1_rehearsal.py` |
| evkit.readme_sync | `eval/readme_sync.py`, which CI runs on every push |
| evkit.friction | `docs/friction_pending.md`, 11 entries |
| calm-vega-notes | Measured on the device instead, and written into docs/GATES.md and CLAUDE.md |
| rubric-amazon.md | The rules read from Devpost and recorded below |
| outreach-kit.md | `docs/outreach/`, three drafts ready for Friday |

Treat the kits as a second opinion if they turn up, and re-record any number taken with our version.

## 2. The repo

Private at **github.com/alejandro-publius/calm-frames**, branch `main`, **CI green** on ubuntu-latest: the Vega app, the Python packages, a secret scan, and a check that every published number still matches the file in `results/` it came from. Nothing runs on macOS runners. It goes public during the final checks on Oct 21.

## 3. Where each lane stands

### Lane A, the cover and GATE 1
- The marker clip and its schedule are made by `eval/marker_clip.py`: 20 markers, one gentle gray to white step each. Measured after generation: 20 rising edges, zero offset from the schedule, 0.333 transitions per second against WCAG's three. The clip stays out of git; the schedule and its hash are committed.
- The cover scheduler runs on a wall clock re-synced to media time, knows about playback rate and pauses, and hides the picture at once on seeking, buffering, stalling, pausing and backgrounding. 81 tests across the Calm Frames modules.
- **The GATE 1 analysis is rehearsed end to end** on the virtual device: all 20 markers covered in time, worst lead 449 ms, median 471 ms, Wilson interval 0.839 to 1.0. `results/gate1_rehearsal_vvd.json`.
- Measured about the player, which Amazon does not document: `timeupdate` is irregular, and in the recorded run it went quiet for over five seconds while the clip played on. `results/vvd_timeupdate_stats.json`. This is the argument for scheduling ahead rather than reacting.
- The layering test ran and is **inconclusive**: the cover toggled 8 times on schedule and nothing crashed, but playback did not run in that take, so it says nothing about sound continuing. Recorded that way in `results/vvd_layering_rehearsal.json`.

### Lane B, flashmap v1
Built from scratch. WCAG general and red flash on sliding one second windows, sliding ten degree area windows, letterbox and pillarbox with the area measured on the picture, real container timestamps, robustness to burned in subtitles, chunked analysis with the property test that chunked equals whole file, the room rule that can only add hides, Ed25519 signed sidecars, the CLI, docs/SIDECAR_SPEC.md, and the GitHub Action with a fixture. **200 tests, 42 mutations written and all 42 killed.** A transition bug surfaced and was fixed: the state machine could not reverse, so a pixel that dipped before rising stayed stuck.

Checked independently before it was committed: it passes our calm marker clip, flags a 7.5 Hz alternation as a general flash over the full area, flags a red alternation as both general and red, and exits 1 on a failing file, which is what the Action depends on.

### Lane C, screening day
Media pool downloaded with the licence checked before each download and recorded in `media/LICENSES.csv`: Blender open movies, NASA SVS and ISS time-lapses, DVIDS, Wikimedia, two 1930 public domain films. Three sources were skipped rather than guessed, with the reason recorded. `eval/plots.py` renders a hazard file as plots so nobody has to open one, and it does not import flashmap. The ffmpeg photosensitivity and naive luminance baselines run. **EA IRIS is not built**: its Dockerfile is pinned and reviewed, but the shared colima VM has another project's services in it and a vcpkg build of OpenCV there could have the kernel kill their containers instead of the compiler.

**GATE 2's target is already met, eight days early.** `results/screening.json`: <!--n results/screening.json:totals.flagged_segments -->432<!--/n--> flagged segments across <!--n results/screening.json:totals.sources_with_at_least_one_flag -->5<!--/n--> sources, against a target of 15 segments from 4 sources. 20 clips, <!--n results/screening.json:clips_analyzed_ok -->16<!--/n--> analyzed cleanly and <!--n results/screening.json:clips_failed -->4<!--/n--> that flashmap could not decode.

**The self-filmed gap has a name: red.** Every one of the 432 segments fired the general rule and not one fired the red rule. The pool has no saturated red strobe and no sustained regular strobe, and no free third-party footage was found that covers it. So the clips you film should be exactly that: red emergency-vehicle lights or red stage lighting, and a steady strobe. Everything in docs/SAFETY.md applies: whoever films is not photosensitive and does not look at the lights.

**Two real bugs came out of the screening run**, both logged for lane B: flashmap cannot decode Theora `.ogv` (4 clips, `avcodec_send_packet` returned 22), and re-encoding shifts the picture rectangle it detects, which lifts area fractions and is what blocked a title in the pipeline.

### Lane D, the pipeline

**4 titles verified end to end, not yet 5.** Six were ingested; two were refused by verify, which is verify doing its job. One was blocked because re-encoding shifts the picture rectangle flashmap detects, which lifts every area fraction and pushes spans just over the 25 percent line, and one because the title is flagged end to end and has no calm moment to take a cover still from. Two more titles were still ingesting when this was written.

`pipeline/ingest.py` runs end to end, idempotent and keyed by the source hash, through probe, analyze per preset, hide plan, kid safe rendition, trickplay and posters from the safe rendition only, signed map and catalog entry. `pipeline/verify.py` blocks publishing and was mutation tested: a violation left in a rendition, a violation under the modelled cover, a tampered map, a wrong hash, a poster from a flagged moment all fail it. The CDK app synthesizes and is unit tested, never deployed: **zero NAT gateways, a 20 dollar budget alarm**, private buckets, a GitHub OIDC role. Estimated cost about 5 dollars in a month where 25 titles are ingested, under a dollar after. **185 tests.**

### Lane E, docs and people
`docs/outreach/` holds the three emails for Friday, each asking only for feedback on wording and flow and saying plainly that nothing we send contains flashing. `docs/EVAL_PLAN.md` is committed before any real clip is labelled, which is the point of committing it.

## 4. The numbers so far

All from `results/`, all checked by CI:

| What | Value | Source |
|---|---|---|
| Markers covered in time, rehearsal | 20 of 20 | gate1_rehearsal_vvd.json |
| Worst lead time, rehearsal | 449 ms | gate1_rehearsal_vvd.json |
| Guard band | 500 ms | gate1_rehearsal_vvd.json |
| App tests | 415 | jest |
| flashmap tests | 200, 42 of 42 mutations killed | pytest |
| Pipeline tests | 185 | pytest |
| Flagged segments found | 432 across 5 sources | screening.json |
| Clips flashmap could not decode | 4 of 20 | screening.json |
| Titles verified end to end | 4 | pipeline catalog |
| Friction log entries | 11 | docs/friction_pending.md |

## 5. What I need from you

1. **The kits**, if they still exist. Everything they blocked has been built around, so this is no longer urgent, but the real calm-timing would be a useful second opinion on the marker clip.
2. **The stick.** Assumed ordered, arriving about Sep 20. Everything that needs a screen is queued behind it: the layering test's real questions, GATE 1 itself, and the KPI run.
3. **Two pending checks from Wednesday**, which I have assumed rather than confirmed: that your phone films 240 fps, and that the TV has a game mode with motion smoothing off.
4. **AWS is untouched**, as instructed. The stack synthesizes and is tested; nothing is deployed and no credentials were used. When the account is on the Paid plan with the budget alarm, say so and it can go up.
5. **Screen recording permission**, only if you want a screen-recorded rehearsal on the virtual device. macOS exposes no capture device to ffmpeg without it. Worth knowing: even with permission, the virtual device's window is not captured, so this may be a dead end. It does not affect GATE 1, which films a TV with a phone.

## 6. Next

1. Fix the two flashmap bugs the screening found: Theora decode, and keeping the picture rectangle across a re-encode.
2. Get a fifth title through verify, by giving flashmap a way to keep the picture rectangle across a re-encode, or by generating a neutral cover still for a title with no calm moment.
3. Build the IRIS image when the shared Docker VM is free.
4. Phase 4: kid mode, the parent area behind a PIN, seek safety across voice, D-pad and cards, and the drop-in hook.
5. When the stick arrives: OS 1.2, developer mode, the layering test, then GATE 1 for real.
