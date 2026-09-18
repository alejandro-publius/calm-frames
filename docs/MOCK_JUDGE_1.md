# Mock judge 1

An independent agent judged this repository against `docs/RUBRIC.md` on **Thu Sep 17, 2026**. Its verdict is below, unedited apart from this header.

## How this run was set up

- The judge had **not seen any of the code or documents being written**. It was given the rubric, `README.md`, `docs/SUBMISSION.md` and `docs/VIDEO_SCRIPT.md` as its starting points, and then read the repository on its own.
- It worked in a **fresh `git clone` in a temporary directory**, never in the live checkout, and it was told in as many words that editing the live checkout would be a total failure of its task. It reported at the end that `git status --porcelain` in the clone was empty and that it never touched the live path.
- It was told to judge exactly what was in front of it, as if the submission closed that day, and to give no credit for anything a document only promises.
- It did not fetch anything from the web. The rules it applied are the ones quoted into `docs/RUBRIC.md` from the hackathon's own pages.
- The clone was taken at commit `92cdc0b`.

## Read the scores in context

**Several lanes were still writing documents while this ran, and the snapshot is a build in progress, not a submission.** The deadline is Fri Oct 23, 2026 and this was judged on Sep 17, five weeks early. That matters for how the Stage One result should be read.

**A correction to the verdict below, found by mock judge 2.** Its prose says twice that the submission "misses five hard lines". Its own table marks **seven** lines FAIL: 2, 3, 7, 8, 12, 13 and 16. The table is the part to trust and the prose undercounts. This header originally repeated the wrong number, which is a good illustration of why the second run was worth doing.

Of those seven, four are things scheduled to happen that have not happened yet rather than things done wrong:

- **No demo video** (lines 2 and 3). It is scheduled for Oct 19 to 20 in `docs/STATUS.md`. It was thought to be blocked on the stick when this judge ran; it is not, because the rules allow the Vega simulator.
- **The repository is private** (line 7). It is scheduled to go public on Oct 21, which is a route the rules allow. What the judge is right about is that the other route, staying private, needs `testing@devpost.com` and `@AmazonAppDev` added, and nothing records that happening.
- **No Open Source contribution URL** (line 12). The patches are finished and the pull request is dated Oct 12 in `docs/STATUS.md`.
- **No demo PIN** (part of line 16). It depends on the parent area being reachable.

Line 13, the AWS Builder services table sitting outside the product feedback field, was a real placement error and has since been fixed.

That leaves line 8, and it is the finding that makes this whole exercise worth the time: **kid mode never engages in the app as committed.** That is not a scheduling item. It is a wiring gap in the product, found by someone reading the code with no idea what it was supposed to do, and it is gap 2 in the list below. It has since been fixed, in commit `8a155ff`.

None of this softens the scores. A judge in November will read whatever is in front of them on that day. It is here so that a reader in October can tell which failures were the calendar and which were the build.

## What happened next

`docs/MOCK_JUDGE_2.md` is a second run of the same rubric by a second judge, after the gaps that belonged to this lane were fixed. The gaps that belong to other lanes were reported to them rather than fixed here.

---

## The verdict, as written

Snapshot judged: `judge1-clone`, Thu Sep 17 2026. Fire TV track, plus the Open Source and AWS Builder mini challenges. Rules and scoring instrument taken from `docs/RUBRIC.md` as instructed. I did not fetch anything from the web and I did not build or run the app.

---

## 1. Stage One: PASS or FAIL

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Working app that runs on Fire OS or Vega OS | PASS with a caveat | `app/manifest.toml` declares `io.github.alejandropublius.calmframes` on OS 1.2 and `results/vvd_smoke.json` records a real launch and 40 seconds of play on the Vega Virtual Device, but the kid mode path is not wired (see line 8 and gap 2). |
| 2 | Demo video shows it on a Fire TV device or the Fire TV/Vega simulator | **FAIL** | No video exists anywhere in the repository and `docs/SUBMISSION.md` field 7 reads `NEEDS ALEX`; `docs/VIDEO_SCRIPT.md` is a shot list whose own "What must exist before this can be filmed" table lists four items as not yet available. |
| 3 | Video under three minutes, public on YouTube or Vimeo, in English | **FAIL** | There is no video URL to check; the script targets 2:55 but a target is not a film. |
| 4 | Video carries no third party trademarks and no unlicensed music or footage | CANNOT TELL | The rules for it are written out well in `docs/VIDEO_SCRIPT.md` lines 18 to 24 (no Fire TV home screen, no Blender logo, no Hell's Angels title card), but with no film there is nothing to check them against. |
| 5 | Text description explaining features and functionality | PASS | `docs/SUBMISSION.md` section 3 has Inspiration, What it does, How we built it, Challenges, Accomplishments, What we learned, What is next and Built with, all written out ready to paste. |
| 6 | Repository holds all source, assets and instructions needed to run it | PASS | `app/`, `flashmap/`, `pipeline/`, `hook/`, `eval/` and `results/` are all present, the offline demo title and its signed map are committed at `app/assets/raw/offline/`, and the screening media is deliberately not committed but is reproducible from `media/LICENSES.csv` and `eval/fetch_media.py`. |
| 7 | Public with a detectable licence in the About box, or private and shared with testing@devpost.com and @AmazonAppDev | **FAIL** | `docs/SUBMISSION.md` line 126 says in the submission's own words "the repository is private today and goes public during the final checks on October 21", and nothing anywhere records the two required collaborators being added in the meantime. The `LICENSE` file itself is a clean Apache-2.0 and would be detected once public. |
| 8 | Setup and run instructions clear, and the project shown functioning | **FAIL** | Two problems. The stick instructions do not work as written: `README.md` lines 322 to 328 do `cd app` and then `vega run-app app/build/armv7-debug/...`, which resolves to `app/app/build`, and `docs/SUBMISSION.md` lines 167 to 170 repeat the same error. And "shown functioning" depends on the video, which does not exist. |
| 9 | Product feedback answers all five questions for every tool, API and SDK | PASS | `docs/SUBMISSION.md` sections 9.1 to 9.9 cover nine tools and each one answers all five questions, including an explicit "Yes" on the yes/no question. |
| 10 | Primary track named | PASS | `docs/SUBMISSION.md` section 4 says `Fire TV`. |
| 11 | Mini challenges named | PASS | `docs/SUBMISSION.md` section 5 says `Open Source (primary)` and `AWS Builder`. |
| 12 | Open Source: contribution URL, repository URL, GitHub username, description | **FAIL** | `docs/SUBMISSION.md` 11.1 (contribution URL) and 11.3 (GitHub username) both read `NEEDS ALEX`; `docs/OPEN_SOURCE_PR.md` line 5 states plainly that nothing has been pushed and no pull request has been opened. The patches are ready at `docs/upstream-pr/0001-*.patch` and `0002-*.patch`, which is preparation, not a contribution URL. |
| 13 | AWS Builder: which AWS services and how, inside the Product Feedback answer | **FAIL** | The services table is complete and specific, but it lives in `docs/SUBMISSION.md` section 10, outside the Product Feedback field; section 9.8 is the only AWS entry inside product feedback and it covers CDK alone. Section 10 also carries its own `NEEDS ALEX` saying nothing is deployed and no AWS credentials have been used. |
| 14 | If the project pre-existed, what was significantly updated is described and demoed | PASS | Every commit in the clone is dated 2026-09-17, well inside the Aug 31 to Oct 23 window, and the derivation from `AmazonAppDev/vega-video-sample` at `v0.24-RN83` is named in the README licence table and in `docs/SUBMISSION.md`. `docs/PRIOR_WORK.md` is stale (it still says `app/` is "not added yet") but the requirement itself is met. |
| 15 | Third party SDKs, APIs and data used within their licences | PASS | `media/LICENSES.csv` carries 38 rows with source page, licence, credit line, SHA-256 and the date the licence was checked; `app/LICENSE` keeps the MIT-0 text, `NOTICE` and `LICENSE` cover the original work, and `flashmap/docs/SPEC_SOURCES.md` traces every threshold. |
| 16 | Judges can reach the project free of charge, with credentials if anything is private | **FAIL** | The repository is private, the demo PIN is `NEEDS ALEX` in both `docs/SUBMISSION.md` line 176 and `README.md` line 371, and the stick is not in hand, so there is no route by which a judge could reach anything today. |
| 17 | Everything in English | PASS | Every document I opened is in English. |

### Overall: FAIL

Stage One is pass/fail and this submission misses five hard lines. The decisive one is the Fire TV track's own requirement, which the rubric is right to flag as a video requirement rather than a code requirement: the demo video must show the project running on an actual Fire TV device or the Fire TV/Vega simulator, and there is no video at all. Lines 2, 3 and 8 fall with it. Line 7 falls independently: a private repository with no record of testing@devpost.com or @AmazonAppDev being added fails the requirement that changed on Sep 16, and line 16 falls with that. Line 12 fails because the Open Source mini challenge needs a contribution URL and the pull request has not been opened.

None of these is a quality judgement. The build behind them is one of the more careful ones I have read. But a missing hard requirement is a fail even when everything else is excellent, and five of them are missing.

---

## 2. The four criteria, 1 to 5

**How much I checked.** I verified 38 file and directory paths that the README links to: all 38 exist. I extracted all 59 numeric markers in the README and resolved each one against the JSON file it points at: all 59 match (the handful that look like mismatches are float formatting that the project's own renderer normalises, for example `5219.0` against `5219`). I checked 14 of the line number references in the "Required tech at runtime" table against the files: 8 land on the named symbol and 6 do not.

### Tech Implementation: 3

**What I would write.** The engineering underneath this is deeper than most hackathon entries get: a WCAG 2.2 SC 2.3.1 analyzer with sliding one second and ten degree windows, letterbox detection, a saturated red test in CIE 1976 UCS, Ed25519 sidecars bound to a file hash, a publish gate that was mutation tested, 107 app test files and 39 Python test files, and a six job CI that rebuilds the headline timing summary from its own raw events and fails if the two disagree. The required technology is not name-dropped: the app really imports and calls `VideoPlayer`, `KeplerVideoSurfaceView`, `KeplerCaptionsView`, `setMediaControlFocus` and `announceForAccessibilityWithOptions`, and I found each of those calls. What stops it going higher is that the thing the whole stack exists to do does not run: nothing in `app/src` ever sets `route.params.guarded`, which is the only switch that turns the guard on, so in the app as committed the flash guard never engages for a user.

**Strongest evidence.** `results/gate1_software_vvd.json` ships with `results/gate1_software_vvd_events.json`, the raw event stream it was computed from, and `.github/workflows/ci.yml` runs `eval/verify_gate1_archive.py` on every push to rebuild the summary from those events and fail on disagreement. Very few submissions make their own headline number falsifiable in CI.

**What holds it down.** `app/src/screens/PlayerScreen.tsx:141` reads `route.params.guarded`, and a grep of all of `app/src` finds that param set nowhere: it appears only as an optional type at `app/src/components/navigation/types.tsx:69`. `KidHomeScreen.tsx` and `ParentAreaScreen.tsx` are imported only by `app/test/calmframes/uiCapture.test.tsx` and `app/test/calmframes/screens.test.tsx`. The safety layer is a well tested library sitting beside an app that never calls it.

### Design: 2

**What I would write.** The interaction thinking is excellent on the page: the cover sits between the video surface at zIndex 0 and the captions view at zIndex 2 so the words carry on over a hidden picture; the cover is taken out of the accessibility tree at `CoverLayer.tsx:66` so VoiceView never reads a black rectangle; announcements queue rather than interrupt at `announce.ts:58`; the kid shelf refuses to autoplay a preview; the household rule can only add hides. But a judge cannot see any of it. There is not one image of the product in the repository, the README contains zero image tags, the kid home and parent area are not reachable in the running app, the demo PIN does not exist, and there is no video. On this criterion the submission asks to be believed about an experience it never shows.

**Strongest evidence.** `app/src/calmframes/KidHomeScreen.tsx` lines 1 to 13, which state what the screen deliberately does not do (never lists an unverified title, never autoplays a preview, focus is a ring rather than a colour change or a wobble). That is real ten foot design reasoning.

**What holds it down.** No screenshot, no video, no reachable screen. By the project's own account in friction entry 9 the virtual device returns black frames, so they cannot capture their own screens, yet `app/test/calmframes/uiCapture.test.tsx` already renders every screen to frames for the CI flashmap job. Nothing was committed from it.

### Potential Impact: 3

**What I would write.** The case for the problem is specific, sourced and careful with its own numbers: 3 percent of people with epilepsy rather than 3 percent of people, with the archive capture date named because the live page returned 403. The four things that outlive the deadline are real artifacts rather than intentions: `hook/` is a published package with its own README and a measured integration diff, `flashmap/examples/flash-check.yml` is a drop in Action, and `docs/SIDECAR_SPEC.md` is written for a second implementer. What keeps it at 3 is that nobody outside the project has seen any of it, by the project's own statement, and the one measured number that speaks to whether the analyzer is fit for this purpose is missing from the README.

**Strongest evidence.** `docs/SIDECAR_SPEC.md` plus `flashmap/action.yml`: a format and a CI check that a studio can adopt without ever installing Calm Frames. That is the difference between one app's feature and something other people can use.

**What holds it down.** `docs/VALIDATION.md` says in its first line that nothing has been collected and no parent, clinician, researcher, advocate, studio or app maker has seen it. And `results/conformance.json` records `flashmap_precision` at 0.65 (0.605 to 0.693) with recall 0.895 on 467 of 3000 designed clips. That precision appears in `docs/STATUS.md` and nowhere in the README, which has no conformance row in either its "What has been measured" table or its "Not measured yet" table. A judge who reads only the README does not learn that roughly a third of flagged windows are false positives.

### Quality of the Idea: 4

**What I would write.** This is not a basic streaming UI. Pre-verifying a whole title, signing the result and binding it to the file hash, then having the player refuse anything unsigned, stale or wrong hashed, is a different shape from the live overlay detectors the description itself names as prior art. Routing voice, D-pad, trickplay and the seek bar through one function so that no path can land the playhead inside a flagged interval is precisely the rubric's own example of a creative Fire TV idea. The one thing that keeps it off a 5 is that the submission never says so in the rubric's words.

**Strongest evidence.** `app/src/calmframes/seekSafety.ts:113` `planSeek`, used by `SafeMediaControlHandler.handleSeek` at `:68` and `handleFastForward` at `:89`, neither of which calls `super`. An Alexa "skip forward" and a D-pad press go through the same gate, which is exactly the multi-modal single flow the rules ask for.

**What holds it down.** The words "multi-modal UX" and "family entertainment" appear nowhere in `README.md`, `docs/SUBMISSION.md` or `docs/VIDEO_SCRIPT.md`, even though `docs/RUBRIC.md` line 227 tells the team to use them. Two of the six Fire TV priority categories are theirs by name and the submission never claims either.

---

## 3. The friction log against Amazon's six fields

`docs/FRICTION_LOG.md` holds eleven entries. Columns are the six fields from section 4 of the rubric: task attempted, steps taken, expected versus actual, severity rating, workaround used, actionable suggestion.

| # | Entry | Task | Steps | Expected vs actual | Severity | Workaround | Suggestion |
|---|---|---|---|---|---|---|---|
| 1 | Installer floods a non-TTY log | yes | yes | yes | yes (Low) | yes | yes |
| 2 | Installer edits every shell startup file | yes | yes | yes | yes (Low) | yes | yes |
| 3 | Versioned docs root returns 404 | yes | yes | yes | yes (Low) | yes | yes |
| 4 | System requirements split, Node versions disagree | yes | yes | yes | yes (Low) | yes | yes |
| 5 | `vega virtual-device status` fails before first start | yes | yes | yes | yes (Low) | yes | yes |
| 6 | `vega device list` crashes with a TypeError | yes | yes | yes | yes (Medium) | yes | yes |
| 7 | Virtual device stops with no message | yes | yes | yes | yes (Medium) | yes | yes |
| 8 | `status` reports running before usable | yes | yes | yes | yes (Low) | yes | yes |
| 9 | No remote input and no screen capture | yes | thin | yes | yes (Medium) | yes | yes |
| 10 | No way to write into an app's data directory | yes | yes | yes | yes (Medium) | yes | yes |
| 11 | `copy-to` help text reversed | yes | yes | yes | yes (Low) | yes | yes |

All eleven carry all six fields. Entry 9's steps are the one soft spot: "Read through `vega device --help` and `vega exec vda`" is a description of looking rather than a reproducible sequence, though the field is present.

**Bonus I would recommend: 6 out of 10.**

What earns it. Every entry has all six fields, the exact command and the exact error string are quoted (`Cannot read properties of undefined (reading 'trim')`, `{"running":false,"process_ids":{"qemu":-1}}`, the 39,131 progress lines), the environment is stated once at the top so no entry repeats it, and the summary table at line 13 lets a reviewer read the whole log in thirty seconds. The suggestions are specific and implementable: add `NO_MODIFY_RC=true`, add `vega device key` and `vega device screenshot`, hold `running` until connectable. That is what an internal review team wants.

What holds it below 9 or 10. First, the log covers only the installer, the docs and the CLI. The most valuable platform findings this team made are not in it: the undocumented `timeupdate` cadence and `currentTime` resolution, `setNativeProps` throwing a TypeError on React Native 0.83, the build rewriting `manifest.toml` with a `[[needs.module]]` per installed package, and the one captions view per process rule. All four appear in `docs/SUBMISSION.md` sections 9.4, 9.6 and 9.7 and as feature requests 3, 7 and 8, but a reviewer assessing the friction log alone never sees them. Second, nothing is rated High, which reads as a log that stayed on the surface even though the explanation at line 27 is reasonable. Third, the version count: the log itself says it holds eleven entries and `docs/SUBMISSION.md` line 442 agrees, but nine of the eleven are Low or documentation papercuts.

**What would slow down a reviewer reading at speed.** `docs/friction_pending.md` sits in the same directory and contains the same eleven entries in a different format, with a header saying they are "waiting for evkit" and that the file will be deleted after import. `docs/FRICTION_LOG.md` line 7 points at it and says the lanes still add to it. A reviewer who opens the wrong file reads a working document that announces itself as unfinished. It should not ship.

---

## 4. Ranked gap list

1. **There is no demo video.** Hits Stage One lines 2, 3, 4, 8 and 16, and it is the Fire TV track's one hard requirement. To close it: film the script in `docs/VIDEO_SCRIPT.md`, run `flashmap check` on the cut, upload, paste the URL. Needs a human: a Fire TV stick, a television, a camera, consent from anyone in frame and a voiceover.

2. **Kid mode never engages in the app.** Hits Tech Implementation, Design and Stage One line 1. `app/src/screens/PlayerScreen.tsx:141` reads `route.params.guarded` and nothing in `app/src` ever sets it; `KidHomeScreen.tsx` and `ParentAreaScreen.tsx` are imported only by tests. To close it: add the two screens to `AppStack.tsx` and navigate to the player with the guarded params. Could be done in the repository today, but it is a day of work, not an edit.

3. **The repository is private with no evidence of the required sharing.** Hits Stage One lines 7 and 16. To close it: make it public with the licence visible in the About box, or add testing@devpost.com and @AmazonAppDev now. Needs a human with GitHub access, and it takes a minute.

4. **No cover lead time on any real device.** Hits Tech Implementation. The one figure that exists is software level on the virtual device and stops at the moment the app sets its state. To close it: GATE 1, 50 trials at 240 fps on a stick. Needs a human and hardware that has not arrived.

5. **Open Source mini challenge has no contribution URL and no GitHub username.** Hits Stage One line 12. The two patches are finished at `docs/upstream-pr/`. To close it: fork `AmazonAppDev/vega-video-sample`, push the branch, open the pull request. Needs a human with a GitHub account.

6. **AWS Builder rests on a stack that has never been deployed, and the services table is in the wrong field.** Hits Stage One line 13 and Tech Implementation. `docs/SUBMISSION.md` section 10 carries its own admission that no AWS credentials have been used. Two fixes: move section 10 into the product feedback answer, which is an edit today, and deploy once, which needs a human and an AWS account. `docs/RUBRIC.md` section 5 already names this as the single biggest open question on the entry and says to ask the hackathon manager. That question has not been asked.

7. **No image of the product exists anywhere.** Hits Design hardest, since the rules say judges may judge on text, images and video alone. `README.md` has zero image tags and the only PNGs in the repository are luminance plots and conformance charts. `app/test/calmframes/uiCapture.test.tsx` already renders every screen. Could be done today: commit a handful of those frames and put them in the README.

8. **Six of fourteen line references in the "Required tech at runtime" table are stale.** Hits Tech Implementation, and it is the first thing a judge checks because the README invites them to. `VideoHandler.ts:133` for `new VideoPlayer()` is actually line 147; `:144` for `setMediaControlFocus` is line 158; `:259` for the Shaka attach is line 274; `PlayerScreen.tsx:444` for `KeplerVideoSurfaceView` is line 496; `:461` for `KeplerCaptionsView` is line 513; `:416` for `setCaptionViewHandle` is line 460. Every reference into `app/src/calmframes/` lands exactly, and `docs/OPEN_SOURCE_PR.md` even documents the 14 line shift, so this was known and the README was not updated. Edit today.

9. **The drift checker silently skips 15 of the 59 README markers.** Hits Tech Implementation, because the README claims at line 165 that every number on the page is checked. The regex in `eval/readme_sync.py` uses `(?P<path>[^\s]+)`, which cannot match a JSON path containing a space, so the entire per-source screening table (`per_source.Blender open movies.files` and fourteen more) is invisible to `--check`. All fifteen happen to be correct today, which means CI would not notice if they stopped being correct. Edit today: one character class.

10. **The README and the submission both say the standalone hook package does not exist, and it does.** Hits Tech Implementation and credibility. `README.md` line 387 says "What does not exist yet is the standalone `hook/` package" while line 117 sells that package with measured diff statistics, and `docs/SUBMISSION.md` 11.2 lists it as "not built yet". `hook/` contains a package.json, a README and 20 source files. A judge who notices will wonder which other status lines are stale. Edit today.

11. **flashmap's measured precision of 0.65 is absent from the README.** Hits Potential Impact and Tech Implementation. `results/conformance.json` publishes precision 0.65 (0.605 to 0.693) and recall 0.895 on a partial run, and it is in `docs/STATUS.md` but has no row in either README table, not even the "Not measured yet" one. For a project whose stated rule is that a row with no number is left empty on purpose, a measured number left out entirely is the wrong asymmetry. Edit today.

12. **The software level lead time is published without its spread.** Hits Tech Implementation. `results/gate1_software_vvd.json` records `lead_ms` p95 of 4097 ms and max of 6197.5 ms alongside the median of 488.4 ms, and the README publishes only the median and the worst case. A 4 second p95 means the covers were mostly firing at whenever the next position report arrived rather than at a scheduled moment, which is the same mechanism the README describes in one sentence at line 210 but does not connect to the number. Edit today.

13. **The stick run instructions do not work as written.** Hits Stage One line 8. `README.md` lines 322 to 328 and `docs/SUBMISSION.md` lines 167 to 170 both `cd app` and then pass `app/build/armv7-debug/...`, which is one directory too deep. The README comment also says "armv7 for the stick" on a `build:debug` script that carries no architecture flag. Edit today.

14. **The screening per-source table does not add up.** Hits Tech Implementation. The six rows in `README.md` lines 260 to 265 sum to 15 files while the table above says 20 clips in the pool and 16 analyzed cleanly. `results/screening.json` has a seventh source, `unlabeled`, with 1 file and 0 flags, which the README drops without saying so. A judge who adds the column gets a number that matches nothing. Edit today.

15. **The submission never claims its priority categories or uses the rubric's own creative language.** Hits Quality of the Idea. "Multi-modal UX" and "family entertainment" appear nowhere in the README, the submission or the video script, although `docs/RUBRIC.md` line 227 says to use those words and the one seek function is exactly that example. Edit today.

16. **Nobody outside the project has seen it.** Hits Potential Impact. `docs/VALIDATION.md` says so in its own first line and the three outreach drafts in `docs/outreach/` have not been sent. Needs a human to send three emails and to get consent for any reply that gets quoted.

17. **The friction log leaves the substantive platform findings out.** Hits the up to 10 percent bonus. The `timeupdate` cadence, `setNativeProps` on React Native 0.83, the `manifest.toml` rewrite and the one captions view per process rule are all written up in the product feedback and the feature requests but have no friction entry. Edit today: four new entries, all already evidenced elsewhere in the repository.

18. **`docs/friction_pending.md` ships alongside the real log with the same eleven entries in draft form.** Hits the bonus, by giving a reviewer at speed a chance to read a file that labels itself unfinished. Edit today: delete it or move it out of `docs/`.

19. **`docs/PRIOR_WORK.md` is stale.** Hits Stage One line 14, which is the line a reviewer would check it against. It still says `app/` and `headstart/` are "not added yet" when `app/` is the whole Fire TV application. Edit today.

20. **The demo PIN does not exist.** Hits Stage One line 16. `README.md` line 371 and `docs/SUBMISSION.md` line 176 both say so. Cannot be closed until the parent area is reachable, which is gap 2.

---

## 5. The three things I would fix first

1. **Film the video.** Nothing else on this list can rescue a Stage One that has no video, and the Fire TV track's only hard requirement is a video requirement. If the stick does not arrive, film against the Vega Virtual Device, which the rules explicitly allow.

2. **Wire kid mode into the app, then photograph it.** Set `route.params.guarded` from a real navigation path and put `KidHomeScreen` and `ParentAreaScreen` in the stack. That single change turns the guard from a tested library into a product, unblocks the demo PIN, gives the video its three best shots, and gives the README the images it currently has none of.

3. **Make the repository public with the licence visible, or share it with testing@devpost.com and @AmazonAppDev today.** It takes a minute, it is a hard rule that changed on Sep 16, and leaving it until Oct 21 puts a pass/fail line on a single unrepeatable day.
