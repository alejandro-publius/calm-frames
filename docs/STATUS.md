# Status

Updated Tue Sep 29, 2026.

## 0. Where things stand

**AWS-free product workflow improvements pass local tests; the dependency audit holds publication.**
The app reviews the chosen household before opening its checked library, and
each verified title explains its selected preset, room, checked maps and
fallback behavior. Pending, failed or incomplete-profile entries get no ready
viewing plan. These changes are presentation-only and retain the approved
limits wording. Household settings and the PIN remain in memory in this demo.

`pipeline.local_library` wraps existing ingest and verification in one local
preparation command and issues a receipt for complete checked renditions only.
Its verified-only snapshot rechecks recorded bytes, withdraws a failed
re-import, rejects unsafe artifact paths and refuses overlapping imports. It
does not serve source media, connect the Vega shelf or establish physical-TV
readiness. The hook can be locally packed and installed in a clean offline
consumer, with current Vega peer types, TypeScript, Metro and Babel checks.
That check is now included in CI and `make ci`; nothing is published to npm.

Final regression evidence for this follow-up: the app has 840 passing tests
and 57 passing snapshots, with its existing one skipped suite and four skipped
tests unchanged. Strict TypeScript and lint pass; broad lint retains existing
warnings and the changed files have no warnings. The final full Python command
below passes 1,334 tests with no failures or skips; only the two existing slow
tests are deselected. This includes all nine HTTP cases and all 55 local-library
tests. The latter include a real benign ffmpeg/flashmap CLI run preparing all
three presets, not just fabricated wrapper contracts.

```sh
CALM_FRAMES_REQUIRE_NODE=1 .venv/bin/python -m pytest flashmap pipeline eval -q -m 'not slow'
```

Use the pinned Node 22 runtime on PATH. The hook's ten guard tests and actual
offline tarball-consumer check pass. The UI's encoded color-model check passes
WCAG and broadcast for every captured screen and transition. Published-number
drift, integration checksum, SBOM and staged secret checks pass. The earlier
broad Python run found stale README source anchors; correcting them restores
the link regression without relaxing it. Every new UI guard and the local
wrapper/package guard groups have observed assertion-red controls followed by
restored green source. The final-source native Debug build passes for armv7,
aarch64 and x86_64, with manifest and ABI validation. Nothing was installed or
played on a device. These checks are not physical-TV or usability evidence.

The fresh unrestricted dependency audit found a new unaccounted `image-size`
advisory, [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr).
The official patched version is incompatible with the older SDK build-tool
API. No risky override, downgrade or extra exception was applied. These
follow-up changes are committed locally, but their push is held while the
audit gate is red, as Alex requested ready-only pushes. The published branch
and main remain unchanged. This is separate from the GitHub Actions payment
or spending-limit restriction; connecting AWS would resolve neither issue.

**Scene holds are implemented; local regression gates pass and remote CI is blocked.** Each
scheduled hide can show a checked frame from the preceding context, or a flat
neutral image when no eligible frame exists. The inline JPEG and exact source
timestamp join the existing map signature. The safe rendition, HLS and live-cover
model use the same image, with provenance and actual-byte verification before
publication. The runtime selects an image only for a completely contained
scheduled interval, keeps an opaque black backing, preserves image aspect ratio,
and returns to black on seeks, stalls, pauses, backgrounding, invalid maps or
decode failures. Detector thresholds, signed segments and guard timing did not
change. The standalone hook and integration example include the new image prop.

Focused benign-media pipeline tests and app guard tests pass, including altered
assets at unchanged paths, false provenance with a valid signature, an initial
neutral cover, and an unchanged restart. The new guards were deliberately broken
and their tests failed before restoration. Physical-device image, caption and
timing composition remain unmeasured. Nothing has been deployed; main stays
unchanged until the complete required checks pass.

The final broad app suite, TypeScript check and lint passed with Watchman
disabled. The first Python regression run exposed two legacy-only fixture
assumptions and an integration-diff checksum drift; both are fixed. That earlier
Python sweep passed in four serial groups: 1,270 tests passed, 11 deselected,
with no failures, errors or skips. The exclusions are exactly two existing slow
tests and nine upload-server HTTP fixtures that cannot bind a localhost socket
in that restricted environment. The later unrestricted run passed all nine
HTTP cases with no errors in 8.54 seconds. The current full sweep can include
them; the earlier sweep's reproduction commands were:

```sh
cd app
node node_modules/jest/bin/jest.js --ci --watchman=false --runInBand
cd ..
.venv/bin/python -m pytest flashmap -q -m 'not slow' \
    -k 'not TestTheServer and not TestAMeasuredClip'
.venv/bin/python -m pytest pipeline -q -m 'not slow' \
    --ignore=pipeline/tests/test_infra.py --ignore=pipeline/tests/test_infra_ingest.py \
    -k 'not TestTheServer and not TestAMeasuredClip'
.venv/bin/python -m pytest eval -q -m 'not slow' \
    -k 'not TestTheServer and not TestAMeasuredClip'
.venv/bin/python -m pytest pipeline/tests/test_infra.py pipeline/tests/test_infra_ingest.py \
    -q -m 'not slow' \
    -k 'not TestTheServer and not TestAMeasuredClip'
```

Use the pinned Node 22 runtime and `CALM_FRAMES_REQUIRE_NODE=1` for Python. The
ordinary CI suite still includes both HTTP
test classes. The integration patch was regenerated and its checksum remeasured;
the published line counts did not change.

Initial implementation checks: the app suite, TypeScript, lint, in-sandbox Python regression suite,
integration checksum, published-number drift check, changed-code secret scans
and whitespace checks passed. The scene-specific guards also passed independent
review and deliberately failing mutation controls. Existing signed titles must
be re-ingested with their signing key to gain image descriptors; the bundled
calm title and original media pool were not changed.

Pre-push hardening found and fixed repeated
image/black changes during buffering within one covered interval. The runtime
now latches interrupted intervals black for the verified map/title session,
including batched uncertainty/resume events and seeks back into an earlier
interval. Review also reproduced a suspended, uncommitted title render clearing
the original title's latch. Commit-only latch ownership and presentation refs
now fix that case too. The final focused run passed 45 guard/playback tests;
strict TypeScript, targeted lint and three independent isolated runtime
regressions passed. Cached probe, still, BIF and poster artifacts
also now check their recorded output bytes and restore altered previews before
reuse. A fresh property compile exposed a numeric-narrowing error hidden by an
incomplete compiler-cache dependency list; both are fixed, with a regression
for the cache dependency. Strict TypeScript and 241 freshly compiled property
tests pass. None of this is physical-device evidence.

The earlier restricted runner also could not fetch the SBOM generator from PyPI, and
headless Chrome exited before the report-page screenshot. Those checks are
unverified in that run, not passes. The current unrestricted SBOM check passes:
every committed bill matches the generator's output. GitHub CI still needs to
check the proposed tree. The review branch is
`codex/signed-scene-holds-2026-09-29`; publication does not certify remote CI or
authorize deployment.

An earlier native bundle attempt and an outdated broad Jest rerun were stopped while the
runtime changed and host load was excessive. Two existing registry tests timed
out in that interrupted rerun. Neither interrupted command counts as a pass;
the final-source sequential app rerun now passes: 91 suites, 832 tests and 57
snapshots, with the existing one skipped suite and four skipped tests unchanged.
The final-source `build-vega --build-type Debug --max-workers 2
--check-manifest true` also passed, producing aarch64, armv7 and x86_64 packages
with manifest and ABI validation. The build emitted a non-fatal telemetry DNS
warning; no device was installed or media played. Debug packaging is not
physical-TV evidence. The earlier stopped mutation run had reached only
unmutated controls and produced no new canonical report.

The earlier broad Python rerun was also stopped under excessive host load, so
its partial progress is not a final-source pass. The completed serial sweep
above supersedes it. The complete mutation measurement passes, with no
unexpected survivors and every unmodified control green. The two remaining
survivors are the existing documented equivalent checks. Actual measurements
are in `results/mutation.json`, not an inferred score. Review caught `--check`
overwriting its expected report before comparing
it; the fix preserves the baseline, including path aliases, rejects skipped
controls and independently rejects unexpected survivors. All 83 harness
regressions pass, including deliberately failing controls for those guards.
CI retains the actual measurement as a separate artifact, with hidden-file
upload enabled only for that exact report path. None of these local checks
means the full GitHub suite is green. Alex asked to continue in-scope work
without further permission questions. The isolated review branch carries the
proposed tree for CI; main stays unchanged until the complete required checks
pass. The existing main branch's Sep 28 scheduled Audit failed before any
runner started. A Sep 29 retry reproduced the same condition in all four jobs:
`runner_id: 0`, no steps, no runner logs. This is not a dependency finding.
The later unrestricted annotation read confirms GitHub's account-level
restriction: jobs were not started because recent account payments failed or
the spending limit needs increasing. The message does not say which of those
conditions applies. No account setting was changed. An external Actions
startup fix is needed before CI can supply the remaining evidence; connecting
AWS would not fix it.

The exact tested tree is published in
[draft PR #1](https://github.com/alejandro-publius/calm-frames/pull/1). Immediately
after publication, the local branch matched its canonical GitHub commit with a
clean worktree. The new
[CI run](https://github.com/alejandro-publius/calm-frames/actions/runs/36646189829)
and [Audit run](https://github.com/alejandro-publius/calm-frames/actions/runs/36646189802)
reproduced the startup restriction in every job: no assigned runner and no
executed steps. No assertion ran or failed remotely. The complete committed
tree also passed the local secret scan after publication. Main is unchanged;
the draft is not ready to merge until complete remote checks pass.

The Sep 19 work below is the earlier phase history, not a new measurement run.

**The build was red and nobody knew.** The tree was clean, pushed and level with
origin, which is what the last session handed over, and the Vega app job had been
failing on main since that push. One file did it:
`app/test/calmframes/hideLog.test.tsx` went in at zero bytes beside the real tests
for the same change, and jest treats a suite with no tests as a failure. It is
gone, the tests it was meant to hold were already in
`app/test/screens/hideLog.test.tsx`, and the app suite is 90 suites, 786 passed,
4 skipped. The lesson is in CLAUDE.md's new resume section: a clean tree is not a
green build, and the two have to be checked separately. Nothing else was
half-finished, no orphaned job was running, and no partial JSON was in `results/`.

**The pattern rule stopped reading text as stripes, and both ffmpeg baselines
were re-run as one set.** Guideline 2 is about *regular* patterns and the rule
was only testing alternation, so every glyph edge counted as a bar and all nine
display frames of our own report page read as a pattern over 44 to 64 per cent of
the screen. A run of bars now has to have a period before it contributes any
area, measured by autocorrelation, and what that is worth is measured rather than
asserted: 171 rendered pages and gratings, including every type size and
colour pair this product ships, precision
<!--n results/pattern_text_precision.json:published.pattern_text_precision_without_periodicity -->0.2462<!--/n-->
to
<!--n results/pattern_text_precision.json:published.pattern_text_precision -->0.9143<!--/n-->
with recall unchanged at
<!--n results/pattern_text_precision.json:published.pattern_text_recall -->0.9412<!--/n-->.
Eight of the nine frames are clean now and one still is not, for a different
reason that is written down and not tuned away. Separately, ffmpeg 8.1.2 is gone
from this machine, so both ffmpeg based baselines were re-run over every clip on
9.0.1 in one go, a check now fails any results directory holding two tool
versions, and the container's ffmpeg is pinned by exact apt version. That re-run
also closed the item that was holding the sixteen calm clips out of the labelling
pool: it is back to <!--n results/realclips_status.json:segments -->40<!--/n-->
segments over <!--n results/realclips_status.json:titles -->16<!--/n--> titles,
with the unflagged half twice the size it was.

## 1. The head-start kits are still not here, asked for twice

**`day-one-head-start.zip` is not on this machine.** Not at the repo root, not in `~/Downloads`, nowhere within four levels of your home folder, and Spotlight finds nothing by that name. `headstart/` is still the empty directory from day one. Neither `rubric-amazon.md` nor `outreach-kit.md` is here.

They were meant to be the test oracle: the kit's flashmap tests to run against ours, spec-exact WCAG and BT.1702-3 numbers to diff our thresholds against, the clip pool in STRESS_TEST.md and the Vega API sheet. Everything they were meant to bring has been built here instead, listed in docs/PLAN.md.

**If the zip exists, the fastest fix is to tell me the exact path.** If it is gone, nothing is waiting on it. What stands in for it: docs/SPEC_SOURCES.md quotes a primary source for every threshold and names what could not be verified, and the conformance suite computes its ground truth from the spec text in a module that cannot import flashmap.

## 2. What you have to do, in order, with dates

| When | What | Why it needs you |
|---|---|---|
| **Overdue, was Fri Sep 18** | Send the three outreach emails in `docs/outreach/`. | Each needs a recipient and your name. They ask only about wording and flow, and say plainly that nothing we send contains flashing. |
| **When the stick arrives, about Sep 20, so probably tomorrow** | Update it to Vega OS 1.2, turn on developer mode, plug it in by USB, then run `make stick-day`. | The whole measurement chain waits on real hardware. The script prints the developer-mode steps, refuses a wrong OS build, installs, runs the layering test and then the marker run. It took about 6 minutes end to end against the virtual device. |
| **Same session** | Film the layering test, then the 240 fps marker run. | **This is the only thing that can produce a GATE 1 number.** Phone at 240 fps, exposure locked, TV in game mode with motion smoothing off. `make stick-day` prints what to film and where the files go. |
| **Before then** | Confirm your phone films 240 fps and the TV has a game mode. | Assumed, never confirmed. If either is wrong, GATE 1 needs a different plan and it is better to know now. |
| **By Thu Sep 24** | Film the red footage, described below. | Nothing else in the pool covers it. |
| **Any evening, about an hour** | Label the <!--n results/realclips_status.json:segments -->40<!--/n--> blinded segments. You take `eval/labeling/labels_labeller_a.csv` and all of them. Rachel takes `labels_labeller_b.csv` and at least seg000 to seg014. Neither of you talks about a segment until both sheets are saved, and neither opens `pool_key.json`. | The pack is ready and nobody has labelled anything, which is correct: this is the step that turns the detector's output into a measured number instead of its own opinion. `eval/labeling/GUIDE.md` has the commands for afterwards, in order. Kappa and the bootstrap run the moment the sheets are in. **The pool was recut again on Sep 19**, after both ffmpeg based baselines ran over every clip and let the sixteen calm Wikimedia clips in, so the segment ids have moved a second time and are not the ones any earlier version of this page named. It is 40 segments over 16 titles, 28 flagged and 12 unflagged, which is twice the unflagged half it had on Sep 18. Nothing is waiting on this now except the two of you. |
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

**The app.** Countdown card with a D-pad Skip, the cover, the after-card, and a minimum cover length. Fail closed for missing, stale, unsigned, unparseable and wrong-hash maps, with real Ed25519 verification written for Vega, which has no crypto API, checked against RFC 8032 vectors. Seek safety through one function for the seek bar, D-pad, trickplay and Alexa transport commands. VoiceView announcements, a parent area behind a PIN where room settings can only add hides, and a kid home with shield badges. **The app's own UI passes flashmap: 24 screens and transitions, 0 segments, checked in CI.**

**Kid mode is reachable.** The app opens on Calm Frames: the first run sets a PIN, a preset and the room, then the shelf, a title, and the parent area behind that PIN. The shelf hands the player the map it verified, and the player itself now refuses to show a picture without one, so the five sample screens that still navigate to it the old way get a black picture and a card saying the title is not checked. A first run, empty and error states for every screen, and a ten foot pass measured rather than eyeballed: 32 units is the smallest text anywhere, 5.12 to 1 the worst contrast, 96 by 54 units the safe margins on every screen. The virtual device cannot be photographed, so those are measurements off the rendered screens, in `app/build/ui-capture/ten-foot.json`. 671 tests, and every new guard was broken on purpose and seen red before it was trusted.

**flashmap.** WCAG general and red flash, area windows, letterbox handling, real timestamps, chunked analysis, the room rule, signed sidecars, the CLI and the GitHub Action. Theora decoding is fixed with a regression fixture. Over 200 tests, 42 mutations all killed.

**The pipeline.** Ingest, hide plan, kid-safe renditions, trickplay and posters from the safe rendition only, signed maps, and a verify step that blocks publishing and was mutation tested. The CDK app synthesizes with zero NAT gateways and a $20 budget alarm, and refuses to deploy.

**Infrastructure and security.** The ingest container exists: ARM64, base image pinned by digest, every Python package installed from a hash, not root, and an entrypoint that publishes nothing unless verify passed and uploads only an allowlist, so the source master and the cover model video cannot leave the task. `make deploy` is one command that deploys the stack and then pushes the image, and it still refuses. The estimate for running it is about $1.34 a month against the $20 alarm, with its assumptions in docs/DECISIONS.md. docs/SECURITY.md now opens with a threat model and ends with what has never been run. pip-audit is clean; npm audit's 59 packages are the pinned Vega toolchain and each one is accounted for in writing with a review date. Three CycloneDX bills of materials, checked in CI. A map signed by a revoked key is refused by the app, and that test was seen to fail three ways.

**Evaluation.** The conformance suite runs with ground truth computed from the spec text in a module that cannot import flashmap. The real-clip labelling pack is ready: 40 segments, 16 titles, 7 sources, blinded, with plots that show no detector output and blank sheets for two labellers. Nobody has labelled anything, which is correct: that is your step and Rachel's.

**Release.** `make test`, `reproduce`, `synth`, `release`, `stick-day`, `hooks` and `scan` all run. `make release` built six packages, staged three architectures with checksums, printed the release command and stopped without publishing.

**Submission.** README, `docs/SUBMISSION.md`, `docs/FRICTION_LOG.md`, `docs/OPEN_SOURCE_PR.md` and `docs/VIDEO_SCRIPT.md` are written, with every number traced to `results/` and checked by CI.

## 4b. The chaos run, finished

**71 marker crossings under deliberate abuse, none with the picture showing.**
`results/chaos_vvd.json`. 16 passes, all launched, no device lost, 157 rude
actions, machine quiet. The fail-safe cover fired on pause, seeking and waiting as
well as on the intervals, so the uncertain-event path was exercised on a real
player. Written up in docs/GATES.md.

An earlier run of the same harness counted only 3 crossings and is the basis of no
claim: `markers50.mp4` puts its first marker at 4000 ms and a rewind under chaos is
a 10 second seek, so 14 of its 16 passes never reached it. The packed clip, whose
first marker is at 2000 ms, was the whole fix.

Two limits recorded in the file and not fixed: `segments_served` and
`segment_requests_stalled` are both 0, because the clip is fully fetched before the
9 second settle ends, so **there is no evidence here about a starved network**; and
backgrounding never happened, so `background_covers_seen` is 0.

## 4c. The five features, and the honest state of each

All five landed with tests and docs. Two Fable verifier passes attacked them and
found nothing that FAILS, which is written up in `docs/VERIFY_PASS_1.md`. What
they did find is a pattern worth naming: **three of these are built and tested but
not yet reachable in the running app**, for the same reason the hide log was.

| | Feature | Built | Reachable in the app |
|---|---|---|---|
| A | Regular-pattern rule (BT.1702-3 Guideline 2) | Yes, with its own profile flag, conformance clips and a separate verdict | Yes, through the broadcast preset the pipeline already runs |
| B | Family profiles | Yes, four kids, one PIN, picker on the shelf | Partly, see below |
| C | Chime before a hide | Yes, and it now has a sound and is wired into the player | **Never heard on a device** |
| D | Report page and upload page | Yes, self contained, every image checked | Yes, locally. Not deployed and it refuses to be |
| E | Map registry | Yes, signed index, tampering fails closed | **No: nothing calls `lookupMap` yet** |

Four specific gaps, none of them hidden:

- **Per-profile hide logs are empty in the running app.** `KidModeScreen` holds
  `profileLogs` with no setter, so nothing writes to them. The keying and the
  parent view are real and tested; the producer is missing, which is the same
  shared-store problem the household log has.
- **The shelf picker has no lock.** A child can pick another child's profile. The
  household floor is still enforced, so nobody can get below it, but per-kid
  strictness above the floor is advisory rather than protected.
- **Nothing in the app or the hook calls `lookupMap`.** The registry verifies,
  refuses and fails closed exactly as claimed, but the app does not consult it, so
  the feature is available rather than in use.
- **The registry's rollback window is 30 days.** Anyone who can serve both the
  index and the maps can replay a 29 day old index and its maps. That is the
  design's declared bound, not a defect, and it is worth saying in days.

The report page's timeline has three guards now, not one. The cap of five bars
per lane is still there. The bars are also drawn low contrast: the widest step a
lane can hold is 8.47 cd/m2 against the 20 cd/m2 Guideline 1 difference, so no
number of them can form a hazardous pattern even if the cap were lost. And CI
renders the whole page at 1280 px, cuts it into nine display frames and runs the
analyzer over each under the broadcast profile, with a negative control that
proves the check can refuse a striped page.

**Eight of the nine display frames pass now, and one does not.** This block used to
say the page could not pass at all, and that was true of the rule as it then
stood: every glyph edge is a Guideline 1 step, so all nine frames read 16 to 25
stripe pairs over 44 to 64 per cent against a 25 per cent limit. Guideline 2 is
about *regular* patterns though, and counting steps is not a test of regularity.
A run of bars now contributes area only when the signal inside it has a period,
and a line of glyphs does not have one. The one frame that still carries a finding
does it at 0.262, and it is not the glyphs any more: it is the line
rhythm. Body text at a fixed leading is a row of repetitive elements at a
constant spacing, which is one of the things Guideline 2 says a pattern may be
formed by, so a column scan down a paragraph has a period and it is the leading.

**That is left standing rather than tuned away**, and the reason is in
docs/DECISIONS.md. Nothing in the attachment exempts it, "clearly discernible" in
the scope sentence is a judgement no number there supplies, and a detector
loosened until our own page passes is not a detector. The check asserts on the
timeline, on the absence of flash and on the negative control being refused, and
prints the page's own verdict beside them.

**The app's own screens are in front of the pattern rule now and they pass it.**
`app/tools/ui_flashmap.mjs` ran the wcag profile only, which has no pattern rule.
It runs the broadcast profile as well, all 25 screens and transitions pass both,
and a non-zero exit from either fails the job. What that check can and cannot see
is worth knowing: those frames are painted from the colours the app records it
drew, one block per colour, so there is no text in them. It asks whether the
layout of the app's own blocks is a regular pattern. What the rule makes of a
glyph is measured somewhere else, in `results/pattern_text_precision.json`.

**The 0.527 raw precision was never about text, and saying so was a guess.** An
earlier version of this page suggested text was probably part of why the pattern
rule's raw precision is 0.527 against 0.937 settled. It is not: every clip in
that suite is a grating and none of them holds a glyph. The gap is window
alignment, which is what "settled" means. The text question needed its own
measurement and now has one.

### The pattern crop defect, fixed on Sep 18

**It is closed.** A black edge bar is read as a stripe rather than a pillarbox
now, so the full-frame six pair grating that used to pass the broadcast profile
is flagged, and `detect_picture` only ever crops less than it did. The flash side
was checked rather than assumed: 402 flash-design clips through the old and new
detector, picture rectangle changed on none, so the published flash precision and
recall stand. Reproduced here before and after.

The three features that were built but unreachable are wired too: the hide log
has a producer and the parent area shows it, the shelf asks the registry before
falling back to a bundled map, and the chime reaches the platform with our asset.
None of those was ever a job for Alex, and they are off the dated list.

### What that defect was, kept for the record

**A full-frame pattern at the count boundary can escape the rule entirely.** Six
pairs of black to peak white stripes, filling the frame, PASSES the broadcast
profile: exit 0, `pattern_pass` true, and the hide plan and verify never see a
segment. The cause is the picture detector, not the pattern code. It reads the
near-black outermost bar as pillarbox and crops it, so the map records
`pillarbox: true, width 175 of 192`, eleven bars remain, and five pairs is not
"more than five". Seven pairs with a black edge bar is flagged but reports
`stripe_pairs 6`.

Any pattern whose edge bar is near black loses a pair to the crop. That is a
hazard reaching a child, so it is the first thing to fix in phase 8, ahead of
wiring anything up. Both files are named in `docs/VERIFY_PASS_2.md` with the
commands that reproduce it.

**A second thing to tighten while in there.** A pattern segment is covered opaque
today, which is right, but only because `normalise_reason('pattern')` falls
through to `red` on an unknown-reason default in both the pipeline adapter and
`flashMap.ts`. Nothing names patterns. Adding `pattern` to `_GENERAL_WORDS` would
make every pattern dimmable and every test would stay green. It also makes
`has_red` true for a title whose red rule never fired, which is a wrong word in
the record. The opacity of a pattern cover should be a rule that says so.

The rest of the pattern rule holds, checked end to end on the real pipeline: a
pattern gets the identical cover interval a flash gets, `pipeline.verify` passes
with the cover proven drawn, wcag and extra-cautious never report a pattern, and
the smooth-flow exemption failed safe on every ambiguous case put to it and logged
every exemption it did apply.

### One environment change you cannot undo

Building EA IRIS pulled in Homebrew's opencv@4, which upgraded ffmpeg from 8.1.2
to 9.0.1 and relinked it. **ffmpeg 9 removed `-vsync`**, which broke every
labelling plot with "no frames decoded" until `eval/plots.py` and
`eval/labeling/plots.py` moved to `-fps_mode passthrough`. Rolling back is not
available: the 8.1.2 binary no longer starts, because x265 moved under it.

What that costs. The ffmpeg based baseline results in `results/baselines/` were
measured on 8.1.2 and still say so in their own files. **If they are re-run,
re-run them as a set rather than piecemeal**, or the table will mix two versions
of the tool and nothing will say which row came from which.

One finding about IRIS itself, worth knowing before anyone leans on it: it
reports PASS with exit 0 on two Theora files it cannot decode at all, writing an
empty frame-data file. It is recorded in `results/baselines/iris_failures.json`,
and it is the reason no report is written for a clip it could not read.

**Still open, in rough order of what would help most:**

1. **The early covers are not capped.** The p95 lead is 4097 ms and the longest is
   6197.5 ms against a 500 ms guard band. A cover four seconds early is safe and it
   is not the schedule working, it is the cover firing whenever the next position
   report happened to arrive. Capping it would mean delaying the cover on a player
   whose reports can be 5219 ms apart, which trades the thing this app exists for
   against a cosmetic gain, so it has not been done. If it is done, the cap has to
   be measured against the worst report gap, not chosen.
2. **The report page's line rhythm.** One of its nine display frames carries a
   pattern finding at 0.262 against a 0.25 limit, from body text at a fixed
   leading rather than from the glyphs. Section 4c says why it is left
   standing. What would close it for good is a primary source that says a
   paragraph is not a clearly discernible stripe pattern, and Ofcom's guidance
   note is the likeliest one. **Retried on Sep 19 and it is still shut.** A plain
   fetch answered 403, and headless Chrome, which is a real browser engine, got
   the Cloudflare "Just a moment..." interstitial rather than the page. It needs
   a browser somebody is sitting in front of, which is Alex or nobody.
3. **The pattern rule's periodicity numbers come off rendered pictures, not off
   real footage.** `results/pattern_text_precision.json` is 123 pages and
   gratings this repository drew. Nothing has measured what the periodicity test
   does to a film's credits, a brick wall, a picket fence or a striped shirt, and
   those are the cases where a false negative would matter. The screened pool has
   no pattern positive in it at all, so there is nothing to measure it against
   yet.
4. **EA IRIS is not in the pattern conformance loop**, unchanged from Sep 18, and
   the reason is unchanged: putting a second process in the generate, analyse and
   delete loop means keeping thousands of flashing clips alive for it.

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
- **EA IRIS does not run on the conformance suite**, so that table still has ffmpeg and naive and no IRIS. It is built and it has run over the real clip pool; what it is not in is the generate-analyse-delete loop, because putting a second process in that loop means keeping three thousand flashing clips alive for it. The pinned Docker image is still unbuilt and stays that way on this machine: the shared VM has another project's services in it, and a vcpkg OpenCV build there could get their containers killed rather than the compiler.
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
| Segments ready for blind labelling | <!--n results/realclips_status.json:segments -->40<!--/n--> across <!--n results/realclips_status.json:titles -->16<!--/n--> titles | realclips_status.json |
| Titles with a verify verdict | <!--n results/verify_pool.json:analyzed -->30<!--/n--> | verify_pool.json |
| Of those, cover proven drawn | <!--n results/verify_pool.json:cover_proven_drawn -->7<!--/n--> | verify_pool.json |
| Of those, no flagged segments | <!--n results/verify_pool.json:no_flagged_segments -->14<!--/n--> | verify_pool.json |
| Of those, failed | <!--n results/verify_pool.json:failed -->9<!--/n--> | verify_pool.json |
| The four add up to the titles on disk | <!--n results/verify_pool.json:adds_up -->yes<!--/n--> | verify_pool.json |
| Pattern rule precision on text, UI and gratings | <!--n results/pattern_text_precision.json:published.pattern_text_precision -->0.9143<!--/n--> (<!--n results/pattern_text_precision.json:published.pattern_text_precision_lo -->0.7762<!--/n--> to <!--n results/pattern_text_precision.json:published.pattern_text_precision_hi -->0.9704<!--/n-->) | pattern_text_precision.json |
| The same, with the periodicity test off | <!--n results/pattern_text_precision.json:published.pattern_text_precision_without_periodicity -->0.2462<!--/n--> | pattern_text_precision.json |
| Pattern rule recall on the same set | <!--n results/pattern_text_precision.json:published.pattern_text_recall -->0.9412<!--/n--> (<!--n results/pattern_text_precision.json:published.pattern_text_recall_lo -->0.8091<!--/n--> to <!--n results/pattern_text_precision.json:published.pattern_text_recall_hi -->0.9837<!--/n-->) | pattern_text_precision.json |
| The same, with the periodicity test off | <!--n results/pattern_text_precision.json:published.pattern_text_recall_without_periodicity -->0.9412<!--/n--> | pattern_text_precision.json |
| Pictures it was measured on | <!--n results/pattern_text_precision.json:pictures -->171<!--/n-->, <!--n results/pattern_text_precision.json:ground_truth_positive -->34<!--/n--> positive by what was drawn | pattern_text_precision.json |

## 7. Next

**Yours, in order.** The table in section 2 is the full list with dates. The
three that are live right now:

1. **Send the three outreach emails.** They were due Fri Sep 18 and they are the
   only thing on the list nothing else depends on.
2. **Confirm the phone films 240 fps and the TV has a game mode**, before the
   stick arrives, because if either is wrong GATE 1 needs a different plan.
3. **When the stick arrives:** `make stick-day`, then film. That is the gate.
   **One measurement to add to it:** the worst gap between two scheduler ticks.
   The harness re-checks every 50 ms, so logging the longest gap between
   consecutive checks gives the worst pause of the JavaScript thread, and the
   guard band should be set above it rather than at the 500 ms we picked by
   judgement. This is still not instrumented.

**Mine, in order, and none of it is waiting on you.**

1. Instrument the scheduler tick gap, so the stick run measures it the first time
   rather than the second.
2. Put a negative control in `app/tools/ui_flashmap.mjs`. It runs the broadcast
   profile now and the screens pass, and a check that has never been seen to
   refuse anything is not yet evidence.
3. Finish the conformance run, which is still partial and says so.
4. A third mock judge. Both existing passes read clones from before phase 8, so
   neither has seen kid mode wired up, the five features reachable, or the
   pattern rule's precision work.
5. More titles through verify. Only 7 of the 30 with a verdict prove anything
   about covering, and that number only moves with footage that actually flashes.

---

**Status line, Sat Sep 19 late (recovery, then the pattern rule).** Main was red
for a day over a zero byte test file and the clean tree hid it; it is green
again. The pattern rule now requires a period before a run of bars counts, which
took the report page from nine failing display frames to two and put the app's
own screens in front of the rule for the first time. Precision on text and UI
went from 0.246 to 0.914 with recall unchanged, measured on 171 drawn pictures
whose ground truth does not import flashmap. Both ffmpeg baselines were re-run as
one set on 9.0.1, the container's ffmpeg is pinned, a check now refuses a results
directory holding two tool versions, and the labelling pool is back to 40
segments over 16 titles with twice the unflagged half. Eleven mutations killed
across the session. Nothing has touched AWS and nothing has been pushed to the
upstream sample.

Tue Sep 29, 2026: signed scene holds are implemented and verified locally across
the pipeline, player and hook. All nine HTTP fixtures now pass unrestricted, and
native image/caption composition needs a benign-media physical-device check.
The proposed tree is on `codex/signed-scene-holds-2026-09-29`. Main remains
unchanged pending complete CI; no deployment has been made.

Tue Sep 29, 2026, AWS-free follow-up: the local preparation receipt, household
review, title viewing plan and installed hook-consumer check are implemented
and pass the final local app/Python/package checks and native Debug build.
A new unaccounted dependency advisory holds publication. No cloud connection, deployment, npm
publication, durable-settings claim or physical-TV evidence has been added.
