# Mock judge 2

A second independent agent judged this repository against `docs/RUBRIC.md` on **Thu Sep 17, 2026**, after the gaps from `docs/MOCK_JUDGE_1.md` that belonged to this lane had been fixed. Its verdict is below, unedited apart from this header and one word. In two places the judge used a word this repository's style rule avoids, and both now read "writes it up [in full]", with the substitution marked in square brackets. Nothing else was altered.

## How this run was set up

- A different agent from judge 1, which had **not seen any of the code or documents being written** and had not seen judge 1's verdict while forming its own.
- It worked in a **fresh `git clone` in a temporary directory**, never in the live checkout, under the same hard rule as judge 1.
- It was told to judge exactly what was in front of it, as if the submission closed that day, and to give no credit for anything a document only promises.
- **It was told not to open `docs/MOCK_JUDGE_1.md` until sections 1 to 5 of its own verdict were written**, so that the second read would be independent. Section 6 is what it said after reading it.
- It did not fetch anything from the web.
- The clone was taken at commit `c740cd6`.

## What the clone did not contain

Two things landed after the clone was taken, so the verdict does not see them and should be read with that in mind.

1. **Kid mode is now reachable.** Commit `8a155ff`, "Kid mode is reachable, and the player refuses anything unchecked", landed while this judge was reading. That is the single finding both judges made independently and ranked second, and it is the reason Stage One line 1 is marked FAIL below. It has been wired since.
2. **The recall split this judge asked for is now published.** Its gap 6, `recall_near_limits = 0.575`, is the most important thing either judge found in this lane's own writing, and it is in the README's conformance table and prose as of commit `d6e8ad7`.

## Both judges undercounted their own tables

Judge 2 noticed that judge 1's prose said "five hard lines" over a table with seven FAIL rows, and it was right. Its own verdict below then does the same thing: the prose under the table says "Six lines fail outright and a seventh cannot be told", and its table marks **seven** FAIL, on lines 1, 2, 3, 7, 8, 12 and 16. The report it handed back said seven. The tables are the part to trust in both files, and the verdict text below is left exactly as written.

## The part worth reading twice

Judge 2 found an overstatement that this lane wrote while trying to be careful. The impact section published the blended recall of <!--n results/conformance.json:published.flashmap_recall -->0.895<!--/n--> and glossed it as about one positive window in ten missed. The same results file holds the split: recall is <!--n results/conformance.json:published.recall_away_from_limits -->1<!--/n--> away from a limit, and <!--n results/conformance.json:published.recall_near_limits -->0.575<!--/n--> on the <!--n results/conformance.json:published.recall_near_limits_clips -->178<!--/n--> clips that sit on one. A safety tool lives at the limit. Publishing the friendlier number, in the paragraph whose entire job was to say what the numbers mean for a child, was the wrong number in the wrong place, and no rule in this repository would have caught it, because every number was traceable and the marker check was green.

That is the lesson from running this twice: the drift checker guards against numbers that have gone stale, not against the right number being left out.

---

## The verdict, as written

Judged against `docs/RUBRIC.md` on the snapshot of Thu Sep 17, 2026, as if the
submission closed today. I did not write any of this project. I read the four
required documents first, then explored the clone, then checked a sample of the
README's claims against the files it points at. I reached every score and every
gap below before opening `docs/MOCK_JUDGE_1.md`.

---

## 1. Stage One: PASS or FAIL

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | A working, demo-ready app that runs on Fire OS or Vega OS | **FAIL** | `results/vvd_smoke.json` records the package `io.github.alejandropublius.calmframes` installing, launching and playing 40 seconds on Vega OS 1.2 with 0 crash lines, but the Calm Frames feature set is unreachable: `app/src/screens/PlayerScreen.tsx:141` reads `route.params.guarded` and no `navigation.navigate` call anywhere in `app/src` sets it, and `KidHomeScreen`, `ParentAreaScreen`, `FirstRunScreen`, `TitleDetailsScreen` and `CreditsScreen` are imported only from files under `app/test/`. What runs on Vega OS is `vega-video-sample` plus a measurement harness. |
| 2 | The demo video shows it running on a Fire TV device or the Fire TV/Vega simulator | **FAIL** | `docs/SUBMISSION.md` field 7 is `NEEDS ALEX`, and every one of the eighteen rows in `docs/SHOT_MANIFEST.md` ends in "not captured". This is the line `docs/RUBRIC.md` section 2.2 calls the hard Stage One requirement for this track. |
| 3 | Video under three minutes, public on YouTube or Vimeo, in English | **FAIL** | There is no video. `docs/VIDEO_SCRIPT.md` targets 2:53 and `eval/check_video.sh` exists to enforce the limit, but there is no file for it to measure and `results/video_check.json` is absent from `results/`. |
| 4 | No third party trademarks, no unlicensed music or footage | **CANNOT TELL** | No video exists to inspect. The rules list in `docs/VIDEO_SCRIPT.md` under "Rights and credits" is thorough (no Fire TV home screen, no Blender logos, Tears of Steel credit scroll kept, no Hell's Angels title card). |
| 5 | A text description explaining features and functionality | **PASS** | `docs/SUBMISSION.md` section 3 has Inspiration, What it does, How we built it, Challenges, Accomplishments, What we learned, What is next and Built with, all written to paste. |
| 6 | The repository holds all source, assets and instructions needed to run it | **PASS** | `app/`, `flashmap/`, `pipeline/`, `hook/`, `eval/` and `results/` are all present, with install and run blocks in the README for the virtual device, a stick, the analyzer, the Action and the pipeline. Two defects sit inside this line and are ranked below: `docs/VIDEO_SCRIPT.md:109` says "`eval/meter.py` is built" and no such file exists, and `docs/SUBMISSION.md:235` gives a stick path one directory too deep. |
| 7 | Public with a detectable licence, or private and shared with testing@devpost.com and @AmazonAppDev | **FAIL** | `docs/SUBMISSION.md` section 6 says "the repository is private today and goes public during the final checks on **Wednesday October 21**", and `CLAUDE.md` line 5 repeats it. Nothing in the repository records sharing with testing@devpost.com or @AmazonAppDev. Apache-2.0 sits at `LICENSE` and would be detected on the day it goes public, but today the line is not met either way. |
| 8 | Setup and run instructions clear, and the project shown functioning | **FAIL** | The instructions are clear. "Shown functioning" is not met: there is no video, there is not one image of the product anywhere in the repository, and the feature being described cannot be reached in the build (see line 1). |
| 9 | Product feedback answers all five questions, for every tool used | **PASS** | `docs/FEEDBACK.md` covers thirteen tools, each with "What we used it for", "What worked well", "What needs work", "Onboarding, zero to hello world" and "Would we build with it again" carrying an explicit Yes. |
| 10 | The primary track is named | **PASS** | `docs/SUBMISSION.md` section 4: `Fire TV`. |
| 11 | The mini challenges entered are named | **PASS** | `docs/SUBMISSION.md` section 5: `Open Source (primary)` and `AWS Builder`. |
| 12 | Open Source: contribution URL, repository URL, GitHub username, description | **FAIL** | Two of the four are empty. Section 12.1 contribution URL is `NEEDS ALEX` and section 12.3 GitHub username is `NEEDS ALEX`. `docs/OPEN_SOURCE_PR.md` states "Nothing has been pushed and no pull request has been opened". |
| 13 | AWS Builder: which AWS services and how, inside the product feedback answer | **PASS** | `docs/SUBMISSION.md` section 11.3 is an eleven row service table, and `docs/FEEDBACK.md` sections 8 to 11 answer the five questions for CDK, Fargate, S3 and CloudFront. The entry declines to claim the mini challenge qualifies, which is a separate matter from the field being answered. |
| 14 | If the project pre-existed, what was significantly updated is described and demonstrated | **PASS** | `git log --reverse` shows the first commit at 2026-09-17 09:15 PT, inside the submission period, so the clause does not bind. The derivation from `AmazonAppDev/vega-video-sample` at tag `v0.24-RN83` is named in the README licence table and in `docs/OPEN_SOURCE_PR.md`. |
| 15 | Third party SDKs, APIs and data used within their licences | **PASS** | `media/LICENSES.csv` carries 38 rows with source page URL, licence, credit line, SHA-256, duration, resolution and the date the licence was checked. `LICENSE` (Apache-2.0), `NOTICE`, `app/LICENSE` (MIT-0) and `app/LICENSE-THIRD-PARTY` are all present. |
| 16 | Judges can reach the project free of charge, with credentials if anything is private | **FAIL** | The repository is private. `docs/SUBMISSION.md` section 9 carries "Release: NEEDS ALEX" and "Demo PIN: NEEDS ALEX". A judge today has no repository, no package to sideload, no PIN and no video. |
| 17 | Everything is in English | **PASS** | Every document, script comment and submission field is English. The `es.json` and `fr.json` files under `app/src/translations/` are inherited from the sample and are not submission content. |

### Overall: **FAIL**

Six lines fail outright and a seventh cannot be told. The one that settles it on its
own is line 2. The rubric quotes the rules saying a Fire TV entry's demo video "must
show the project running on an actual Fire TV device or the Fire TV/Vega simulator",
and `docs/VIDEO_SCRIPT.md` correctly calls that "the one Stage One requirement that no
amount of code satisfies". No video exists, and none can be filmed, because nine of the
ten camera shots are shots of a kid mode that has no entry point in the application.

Stage One is pass or fail, and a missing hard requirement is a fail however good the
rest is. The rest is often very good, which is section 2.

---

## 2. The four criteria, scored 1 to 5

### How I checked the claims

I ran four passes over the README and the submission text rather than taking them
on trust.

| Check | Count | Held |
|---|---|---|
| File and line references in "Required tech at runtime" (does line N of that file contain the named symbol) | 17 | 17 |
| Numeric markers across `README.md`, `docs/SUBMISSION.md` and `docs/VIDEO_SCRIPT.md` resolved against the JSON in `results/` | 74 | 74 |
| Relative links in the four main documents | 96 | 96 |
| Narrative claims spot-checked against the repository | 8 | 5 |
| **Total** | **195** | **192** |

The three narrative claims that did not hold:

1. `docs/VIDEO_SCRIPT.md:109` says "`eval/meter.py` is built". There is no `meter.py`
   anywhere in the repository. `docs/SHOT_MANIFEST.md` lines 52 and 84 build shot S04,
   which the script calls "the shot the whole video exists for", on `eval/meter.py run`
   and `eval/meter.py calibrate`.
2. `README.md:137` says the system-wide setting "is request 1 in `docs/SUBMISSION.md`,
   alongside thirteen others found while building". `docs/SUBMISSION.md` section 13 does
   not hold the list; it points at `docs/FEEDBACK.md`, which has twenty-one requests, not
   fourteen. `docs/FEEDBACK.md` flags this exact drift in its own "For Lane H" table and
   the README has not caught up.
3. `docs/SUBMISSION.md:235` tells a judge to run `vega run-app
   app/build/armv7-debug/...` in a block whose previous line is `cd app && npm install &&
   npm run build:debug`, so the path is one directory too deep. `README.md:366` has the
   same command written correctly. A recent commit fixed the README copy and left the
   copy in the pasted testing instructions behind.

Everything else I tested held, including the integration diff counts (`per_file` in
`results/integration_diff.json` sums to the 32 added, 2 replaced, 4 files and 23 busiest
that the README quotes), the claim that `results/conformance.json` calls its own run
partial (it does, at `sample.statement`), and the friction log pointers at entries 6 and 8.

The rules say judges are not required to test anything, so I also read the submission
the way a reader who never opens a terminal would. That reader has no video, no image,
and 50 KB of README.

---

### Tech Implementation: **3**

The engineering under this is real and the evidence discipline around it is the best
thing in the submission. It is held back by one fact that no amount of testing gets
around: the safety layer has never run as a product, on any device, for any person.
`useFlashGuard` is wired into `PlayerScreen.tsx`, but `guarding` is `Boolean(route.params.guarded)`
and nothing sets `guarded`, so every timing number in the README came from
`useCoverHarness`, a different hook driven from a config file that `HomeScreen.tsx`
fetches. The two hooks share `coverSchedule.ts` and `mediaClock.ts`, so the arithmetic
is the same code, but the guard's own loop, its map verification and its card logic
have never been timed on anything.

**Strongest evidence:** the `numbers` job in `.github/workflows/ci.yml` runs
`eval/readme_sync.py --check`, `eval/verify_gate1_archive.py` and
`eval/integration_diff_stats.py --check` on every push, and all three hold on this
snapshot. 74 of 74 published numbers match their JSON and 17 of 17 file-and-line
references land on the named symbol. That is a level of self-checking most submissions
do not attempt.

**What most holds it down:** beyond the unreachable kid mode, the README publishes the
kindest of three timing runs. `results/gate1_software_vvd.json` (49 trials, 48 in time,
worst lead -86 ms) is in the README. `results/under_load/gate1_software_vvd_load218.json`
(9 trials, 8 in time, worst lead -454.6 ms, worst scheduler tick gap 72,755 ms) and
`results/stick_day/gate1.json` (50 markers, 2 counted, 43 not counted) are not, and
neither path is named anywhere in `README.md` or `docs/SUBMISSION.md`. The README then
says "nothing yet measures what that worst pause is on real hardware", which is true as
written and leaves a README-only reader believing the pause is unquantified when the
repository has measured it at 72.8 seconds on the virtual device. `docs/GATES.md`
writes the under-load run up in full and is one click from the README's "Where else to
look" table, so this is under-surfacing rather than concealment, but it sits directly
under the project's loudest claim about itself.

### Design: **2**

The interaction model is thought through with more care than the device usually gets.
One seek function for voice, D-pad and cards (`planSeek` at `app/src/calmframes/seekSafety.ts:113`),
transport handlers that deliberately do not call `super` so an Alexa command cannot
bypass the gate, VoiceView announcements queued rather than interrupting
(`announce.ts:58`), the cover taken out of the accessibility tree (`CoverLayer.tsx:66`)
so focus never lands on a black rectangle, and captions at zIndex 2 above the cover so
a hidden segment stays followable. The app's own screens are rendered and run through
flashmap in CI, which is a level of self-consistency I have not seen in a hackathon
entry before.

None of it is a product experience yet, and none of it can be seen.

**Strongest evidence:** the `ui-flashmap` job in CI renders every screen, turns it into
a lossless video and runs the same analyzer over it, so the accessibility app is held to
its own standard. That is a design argument made in code.

**What most holds it down:** there is not one picture of this product anywhere. I
searched for `![` in `README.md` and `docs/SUBMISSION.md` and found zero image
embeds, and every `.png` in the repository is a conformance error curve or a luminance
plot. Combined with no video and no reachable kid mode, a judge finishes this submission
without ever having seen a single screen of it. The rules explicitly allow judging "based
solely on the text description, images, and video", and two of those three are empty.

### Potential Impact: **3**

The section headed "Who it is for, and how it leaves this hackathon" is the best written
part of the README and the part I checked hardest, because it is the case for this
criterion.

**The two outside citations.** Both are handled with more care than I expected.

- The Epilepsy Foundation figure is quoted exactly and then corrected in the README's own
  voice: "It is about 3% **of people who have epilepsy**, not 3% of people." The README
  goes on to quote the Foundation's own caution that "The likelihood of such conditions
  combining to trigger a seizure is small" and calls it "the Epilepsy Foundation's own
  caution and it belongs here as much as the rest". A submission that quotes the sentence
  which shrinks its own market is not overselling.
- The *Epilepsia* consensus paper is cited with sixteen authors, volume, issue, pages, DOI
  and PMID, and the README states plainly that **only the abstract has been read** and
  that "Nothing in this project cites the body of that paper, and no threshold comes from
  it."
- The paragraph headed "What these sources are not" does the work that most submissions
  skip: it says the sources are why the problem is real and not where the thresholds come
  from, points every threshold at `flashmap/docs/SPEC_SOURCES.md`, states that the paper's
  10 to 20 Hz range and stripe guidance "are not implemented and are not claimed", and
  ends "Neither source says that hiding flagged segments prevents a seizure, and neither
  do we."

**How each source was read is disclosed candidly, and unusually so.** The Epilepsy
Foundation page returns 403 to automated requests, so the quotes come from an Internet
Archive capture dated Aug 16, 2026, and the README says so and adds "Quoting an archived
capture is quoting what the page said on a date, not what it says today." The Wiley DOI
403s, so the record was confirmed against Crossref and PubMed. The Apple pages render
their text in the browser, so the quotes come from the documentation JSON endpoint. All
three are named with the date each was fetched. I could not fetch the web to confirm the
wording, but the disclosure is precise enough that a judge knows exactly what to re-check
and where. The repository itself flags the residual risk: "Open the live URL in a browser
and confirm these three sentences before the submission goes in," which has not happened.

**Strongest evidence:** the four things said to outlive the deadline are artefacts, not
plans. `hook/` is a package tree with 26 files and its own README. `flashmap/action.yml`
and `flashmap/examples/flash-check.yml` are a working Action with documented exit codes.
`docs/SIDECAR_SPEC.md` is a versioned format with a section on what a map does not say.
`docs/INTEGRATION_DIFF.md` is a real diff whose counts reconcile against
`results/integration_diff.json` and are recounted in CI.

**What most holds it down:** there is no route to an audience. The words "Appstore" and
"App Store" do not appear in `README.md` or `docs/SUBMISSION.md` at all, and the rubric's
own examples for this criterion are "Fire TV Appstore, Ring Appstore". `docs/VALIDATION.md`
says in its first line that no parent, clinician, researcher, advocate, studio or app
maker outside the project has seen it. Behind that sits a measurement the README does not
publish: `results/conformance.json` records `recall_near_limits = 0.575` over the 178
clips that sit on a limit, against the 0.895 the README prints. The README's plain-language
gloss, "about one positive window in ten is missed", is right for the blended figure and
wrong for the region a safety tool lives in, where it is closer to four in ten. The file
that says this, `eval/EVAL_RESULTS.md`, is linked from nowhere in `README.md` or `docs/`.

### Quality of the Idea: **4**

This is the strongest of the four and it would be the reason to shortlist the entry if
Stage One let it through. The rubric names a creative Fire TV idea as "multi-modal UX
combining voice + D-pad + visual in a single flow", and this is that, with the code to
show for it rather than the phrase. Verify-before-play with an Ed25519 signature bound to
the file's SHA-256, a fail-closed default where `covered` starts true, and a household
rule that can only ever add hides and never remove them, are three ideas that a copy of
an existing product would not have arrived at. So is the decision to schedule the cover
on a wall clock rather than react to position reports, which came out of a measurement
(`timeupdate.interval_ms.max` of 5219 ms) rather than a preference.

**Strongest evidence:** `SafeMediaControlHandler` extends the Kepler handler and none of
its methods call `super`, routing system and voice transport through the same `planSeek`
the on-screen controls use. That is the single design decision that makes the multi-modal
claim true rather than decorative, and it is four lines of the README away from being the
first thing a judge reads.

**What most holds it down:** the idea is described far more than it is demonstrated. With
no video and no image, every creative claim has to be taken from prose. The household and
room-rule half of the idea, which is the part that makes it adaptive rather than static,
has never been operated by a person on any device.

---

## 3. The friction log against Amazon's six fields

All thirty entries in `docs/FRICTION_LOG.md` carry all six fields. I checked by parsing
the file for the seven bold sub-headings (Task, Steps, Expected, Actual, Severity,
Workaround, Suggestion) in each `## N.` section. Not one entry is missing one.

| # | Task | Steps | Expected vs actual | Severity | Workaround | Suggestion |
|---|---|---|---|---|---|---|
| 1 Installer floods non-TTY logs | yes | yes | yes | Low | yes | yes |
| 2 Installer edits every shell rc file | yes | yes | yes | Low | yes | yes |
| 3 Versioned docs root 404s | yes | yes | yes | Low | yes | yes |
| 4 System requirements split and inconsistent | yes | yes | yes | Low | yes | yes |
| 5 `virtual-device status` fails before first start | yes | yes | yes | Low | yes | yes |
| 6 `vega device list` crashes with a TypeError | yes | yes | yes | Medium | yes | yes |
| 7 Virtual device stops with nothing in the log | yes | yes | yes | Medium | yes | yes |
| 8 `status` says running before the device is usable | yes | yes | yes | Low | yes | yes |
| 9 No supported key injection or screen capture | yes | yes | yes | Medium | yes | yes |
| 10 No path into an app's data directory on OS 1.2 | yes | yes | yes | Medium | yes | yes |
| 11 `copy-to` help text reversed | yes | yes | yes | Low | yes | yes |
| 12 Device drops the app's log output under load | yes | yes | yes | High | yes | yes |
| 13 Release builds strip `console.log` | yes | yes | yes | Low | yes | yes |
| 14 No frame of what the app drew, inside or out | yes | yes | yes | High | yes | yes |
| 15 No crypto API, Ed25519 written by hand | yes | yes | yes | High | yes | yes |
| 16 Build rewrites `manifest.toml` every build | yes | yes | yes | Medium | yes | yes |
| 17 Plain MP4 over HTTP never starts, never errors | yes | yes | yes | Medium | yes | yes |
| 18 A 200 instead of a 206 fails in silence | yes | yes | yes | Medium | yes | yes |
| 19 Video-only stream pauses a few seconds in | yes | yes | yes | Medium | yes | yes |
| 20 Media element absent at mount, no readiness signal | yes | yes | yes | Medium | yes | yes |
| 21 Device backgrounds an untouched app, playback stops | yes | yes | yes | Medium | yes | yes |
| 22 Playback not steady, error says `UNKNOWN` | yes | yes | yes | High | yes | yes |
| 23 `postinstall` builds Shaka from source, needs a JDK | yes | yes | yes | Low | yes | yes |
| 24 `jest --ci` exits 1 on a clean sample checkout | yes | yes | yes | Low | yes | yes |
| 25 Dependency tree buries a secret scan in 208 findings | yes | yes | yes | Low | yes | yes |
| 26 Ogg Theora duplicate-frame packets kill the decoder | yes | yes | yes | Medium | yes | yes |
| 27 Theora decodes wider than the declared size | yes | yes | yes | Low | yes | yes |
| 28 Re-encoding moves the picture rectangle | yes | yes | yes | Medium | yes | yes |
| 29 A re-encode renumbers the first timestamp | yes | yes | yes | Medium | yes | yes |
| 30 ffmpeg photosensitivity filter misfires on its first second | yes | yes | yes | Low | yes | yes |

The summary table's own counts check out: four High (12, 14, 15, 22), thirteen Medium,
thirteen Low, thirty in total.

**Bonus I would recommend: 8 of the available 10 percent.**

Why that high. Every entry carries exact commands and exact output rather than a
recollection, and several quote the literal string a reviewer could search their own
telemetry for, such as `Log suppression ended at level [info]. [140] logs were suppressed`
in entry 12 and `Cannot read properties of undefined (reading 'trim')` in entry 6. The
workarounds are code in the repository, not resignation: entry 9 points at
`eval/vvd_control.py` driving QEMU's QMP socket, entry 12 points at `eval/vvd_timing_run.py`
replacing the device log with an HTTP event sink, entry 22 points at
`eval/verify_gate1_archive.py`. The suggestions are specific engineering asks a team could
turn into tickets, down to entry 11 asking for two help-text strings to be swapped and
entry 25 asking for a `.gitleaksignore` in the sample. The preamble is candid about which
entries are Amazon's surface (1 to 25) and which are the wider toolchain (26 to 30), and
about which entries are platform absences designed around rather than failures watched
happening.

Why not 10. Three things a downselect reviewer reading at speed would hold against it.
The five toolchain entries are ffmpeg and PyAV rather than Amazon's product, so a reviewer
counting entries that inform Amazon gets 25 and not the 30 the file advertises. Entries 9,
14 and 15 are absent features rather than defects, which the file says, but a fast reader
scoring "what broke" may discount them. And a couple of entries are close neighbours of
each other (5 and 8 are both `vega virtual-device status`; 9 and 14 are both the capture
gap from two sides), which reads as a larger count than the distinct problem list.

**What would slow a reviewer reading at speed.** The file is 664 lines and 47 KB. The
summary table is in entry order rather than severity order, so a reviewer who wants the
four High entries has to scan the Severity column of a thirty-row table. Severity does not
appear in the `## N.` headings, so inside the body you have to read down to find it.
`docs/friction_pending.md` is still committed next to the final log, and a reviewer who
opens the working notes by mistake gets a different and rougher document. And the entry
numbering has drifted against other documents: `docs/VIDEO_SCRIPT.md:99` calls the
`vega device list` crash "feature request 4" while `docs/FEEDBACK.md` numbers the same
request 5, a mismatch `docs/FEEDBACK.md` flags about itself and nobody has reconciled.

---

## 4. Ranked gap list

Worst first. "Repo today" means someone could close it by editing files in this
checkout. "Needs a human" means hardware, an account, a camera or a decision.

1. **No demo video exists.** Stage One lines 2, 3 and 8, and Design. `docs/SUBMISSION.md`
   field 7 is `NEEDS ALEX` and all eighteen shots in `docs/SHOT_MANIFEST.md` are "not
   captured". To close: film and upload. **Needs a human**, and it is blocked by gap 2.

2. **Kid mode has no entry point in the application.** Stage One lines 1 and 8, Design,
   Tech Implementation. `PlayerScreen.tsx:141` reads `route.params.guarded` and nothing in
   `app/src` sets it; `KidHomeScreen`, `ParentAreaScreen`, `FirstRunScreen`,
   `TitleDetailsScreen` and `CreditsScreen` are imported only by tests. Nine of the ten
   camera shots are shots of screens no user can reach. To close: register the screens in
   `app/src/components/navigation/AppStack.tsx` and pass a `guarded` param from wherever a
   verified title is opened. **Repo today** for the wiring, then a device run to confirm it.

3. **The repository is private and not shared with the judges.** Stage One lines 7 and 16.
   `docs/SUBMISSION.md` section 6 dates the change to Oct 21. To close: make it public with
   Apache-2.0 visible in the About box, or share it with testing@devpost.com and
   @AmazonAppDev. **Needs a human**, and it is one setting.

4. **Two of the four Open Source fields are empty.** Stage One line 12. Contribution URL
   and GitHub username are both `NEEDS ALEX`; `docs/OPEN_SOURCE_PR.md` says nothing has been
   pushed. The patch itself is finished and verified against upstream `main` at
   `ef8e4da`. To close: fork, push, open the PR, paste two strings. **Needs a human**,
   because the fork must be under a real account.

5. **Not one image of the product exists.** Design, Potential Impact. Zero image embeds in
   `README.md` and `docs/SUBMISSION.md`, and no screenshot committed anywhere. The rules
   permit judging on "text description, images, and video" and two of the three are empty.
   To close: put labelled stills in the README. The app's own `uiCapture` path can render
   the screens, and `docs/VIDEO_SCRIPT.md` rightly forbids passing a render off as a
   photograph in the video, so any still needs a label saying what it is. **Repo today**
   for a labelled render, **needs a human** for a real photograph.

6. **The near-threshold recall of 0.575 is not in the README, and the file that reports it
   is linked from nowhere.** Tech Implementation, Potential Impact. `results/conformance.json`
   holds `recall_near_limits = 0.575` over the 178 clips that sit on a limit, against the
   0.895 the README publishes. `eval/EVAL_RESULTS.md` explains it well and no document
   links to it. To close: add the split to the README's conformance table and link
   `eval/EVAL_RESULTS.md` from "Where else to look". **Repo today.**

7. **The under-load timing run is absent from the README.** Tech Implementation.
   `results/under_load/gate1_software_vvd_load218.json` records a worst lead of -454.6 ms
   and a worst scheduler tick gap of 72,755 ms, and `docs/GATES.md` writes it up [in full],
   but `README.md` says "nothing yet measures what that worst pause is on real hardware"
   and prints only the -86 ms figure. To close: one row and two sentences in the README's
   cover-timing section. **Repo today.**

8. **The AWS Builder question is unresolved and nothing is deployed.** The mini challenge
   itself, not a Stage One line. `docs/SUBMISSION.md` section 11.2 is right that the rules
   do not define "incorporates", and the entry is right not to claim it. To close: ask the
   hackathon manager, or deploy once behind the budget alarm. **Needs a human.** Worth
   noting separately: the rubric lists "agentic architecture with Claude/Kiro for
   development workflow" as a creative AWS Builder answer, and this project was built that
   way (`CLAUDE.md`, `docs/BUILD_PROMPT.md`) without the submission ever saying so.

9. **The demo PIN and the release do not exist.** Stage One line 16. `docs/SUBMISSION.md`
   section 9 has "Release: NEEDS ALEX" and "Demo PIN: NEEDS ALEX". The README says the PIN
   is not set and will not carry a made-up one, which is the right call and still leaves a
   judge with nothing to install. **Needs a human.**

10. **`eval/meter.py` is claimed as built and does not exist.** Stage One line 6, Tech
    Implementation. `docs/VIDEO_SCRIPT.md:109` says it is built; `docs/SHOT_MANIFEST.md`
    builds shot S04 on three of its subcommands. This is the tool behind "the shot the
    whole video exists for". To close: write it, or mark it as not built. **Repo today.**

11. **The README's feature-request pointer is stale in both the count and the location.**
    Tech Implementation, credibility. `README.md:137` says "request 1 in
    `docs/SUBMISSION.md`, alongside thirteen others"; the list is in `docs/FEEDBACK.md` and
    has twenty-one. `docs/FEEDBACK.md` flags this drift in its own table. **Repo today.**

12. **The pasted stick command in the testing instructions has the wrong path.** Stage One
    line 8. `docs/SUBMISSION.md:235` says `vega run-app app/build/armv7-debug/...` after a
    line that already did `cd app`. `README.md:366` is correct. This is the field a judge
    copies from. **Repo today.**

13. **Internal documents contradict the shipped ones.** Credibility at speed. `docs/PLAN.md`
    still describes "nine tools, fourteen feature requests, eleven entries";
    `eval/screen.py`'s docstring still says "FLASHMAP IS NOT READY YET (Sep 17, 2026).
    flashmap/ is an empty directory" above a populated `flashmap/`; `docs/BUILD_PROMPT.md`
    opens by telling the reader to unzip a head-start kit that `docs/STATUS.md` says never
    arrived. All three ship in the repository a judge browses. **Repo today.**

14. **Nobody outside the project has seen it.** Potential Impact. `docs/VALIDATION.md` says
    so in its first line and is right to. It costs the impact case its only possible outside
    corroboration. **Needs a human**, and `docs/STATUS.md` dates the three outreach emails
    to Sep 18.

15. **The headline statistic is quoted from an archived capture, not the live page.**
    Potential Impact. The README discloses this and instructs a check against the live URL
    that has not been done. **Needs a human**, and it is two minutes in a browser.

16. **`hook/README.md` tells a reader to `npm install @calm-frames/flash-guard`.** Potential
    Impact, Tech Implementation. The package is not published; `docs/DECISIONS.md` records
    only that the name was free on npm as of Sep 17. The most reusable artefact in the
    submission has an install line that does not work. **Repo today**, by saying how to use
    it from source until it is published.

17. **A date inconsistency between the README and the Devpost text.** Potential Impact.
    `README.md:105` says the consensus was published "in *Epilepsia* in February 2026";
    `docs/SUBMISSION.md:50` says "A 2025 Epilepsy Foundation working group". Both are
    defensible from the same record, and a judge reading both sees a mismatch. **Repo today.**

---

## 5. The three things I would fix first

1. **Wire kid mode into the navigation stack.** Register `KidHomeScreen` and
   `ParentAreaScreen` in `AppStack.tsx` and pass a `guarded` param from the title that
   opens the player. Nothing else in this submission moves until this does: it unblocks
   nine of the ten camera shots, it is what turns line 1 of Stage One from arguable into
   settled, and it is the difference between a safety layer that exists in Jest and one
   that exists on a television.

2. **Film and upload the video.** It is the hard Stage One line for this track, the
   project's own documents say so, and the script is already timed to 2:53 with an
   eighteen-shot manifest. The rules allow the Vega simulator, so it does not wait on the
   stick. The two-minute check that `docs/VIDEO_SCRIPT.md` asks for first, whether a camera
   can see the virtual device window at all, should happen before anything else is planned
   around it.

3. **Make the repository public with the licence visible, and open the upstream pull
   request.** One GitHub setting and one fork. Together they clear Stage One lines 7, 12
   and most of 16, and they cost less than anything else on the list.

---

## 6. Where I differ from judge 1

*Written after sections 1 to 5, having now read `docs/MOCK_JUDGE_1.md`. Judge 1 ran on
commit `92cdc0b`; this clone is at `c740cd6`, so a number of its findings have been acted
on in between.*

### The scores came out identical

Judge 1: Tech Implementation 3, Design 2, Potential Impact 3, Quality of the Idea 4, Stage
One FAIL. Mine are the same four numbers and the same overall verdict, reached without
seeing theirs. We even picked the same strongest evidence for Quality of the Idea, which is
`planSeek` at `seekSafety.ts:113` reached from `SafeMediaControlHandler` handlers that do
not call `super`. Two independent reads landing on the same four numbers is worth more than
either read on its own, and I would tell the team to treat 3/2/3/4 as the real answer.

We also both fail Stage One on the video, both fail line 7 on the private repository with
no record of the two required collaborators, both fail line 12 on the two empty Open Source
fields, and both fail line 16 because there is no route by which a judge could reach
anything today.

### Where we differ on the Stage One table

Two lines, and they cancel out in the count. We each fail seven of seventeen.

- **Line 1, the working app.** Judge 1 marked it "PASS with a caveat". I mark it FAIL. The
  rule text in `docs/RUBRIC.md` section 2.1 says a Fire TV entry has to "launch a
  demo-ready app", and an app whose entire demonstrable feature set has no entry point in
  its own navigation is not demo-ready. Judge 1 then puts the same fact in its caveat and
  in its gap 2, so we agree on the finding and differ only on where to record it. I think
  the failure belongs on the line.
- **Line 13, AWS Builder inside the product feedback.** Judge 1 marked it FAIL, because the
  eleven-row service table sat in `docs/SUBMISSION.md` section 10, outside the product
  feedback field, and only CDK was answered inside it. That has since been partly fixed:
  `docs/FEEDBACK.md` now answers the five questions for CDK, Fargate, S3 and CloudFront,
  and the product feedback field points at that file. I mark it PASS on that basis. Judge
  1's harder reading is still defensible, because seven of the eleven services, including
  DynamoDB, Lambda, VPC, IAM and Budgets, appear only in the AWS Builder field and never
  inside the product feedback answer. If a reviewer reads the field literally, judge 1 is
  right and I am too generous.

One small thing about judge 1's own write-up: its table carries seven FAIL rows (2, 3, 7,
8, 12, 13, 16) while its prose twice says "five hard lines". The table is the part to trust.

### What has been fixed since judge 1, and it is a lot

Eight of judge 1's twenty gaps have been closed in the intervening commits.

- **Gap 8, six of fourteen stale line references.** Fixed. Commit 5829ca2 ("Seven stale
  line references in the README, and a test so they stay right") corrected them and added a
  test. I independently checked all 17 references in the current table and all 17 land on
  the named symbol.
- **Gap 9, the drift checker silently skipping fifteen markers.** Fixed. The regex in
  `eval/readme_sync.py:40` is now `(?P<path>[^\n]+?)`, which matches a JSON path containing
  a space. My own extractor resolved all 74 markers, including
  `per_source.Blender open movies.files`, and all 74 matched.
- **Gap 10, the README saying the `hook/` package does not exist while selling it.** Fixed.
  `README.md:426` now says the standalone package "exists too, with its own README and the
  integration diff above".
- **Gap 11, precision 0.65 absent from the README.** Fixed, and generously. There is now a
  whole conformance section with precision, recall, confidence intervals and a
  plain-language reading of both, and it says in its own text that the number "was missing
  from this page until a mock judge asked for it".
- **Gap 14, the screening per-source table not adding up.** Fixed. The table now has seven
  rows, the `unlabeled` row is present, the files column sums to 16, and a sentence explains
  why the row is there rather than dropped.
- **Gap 15, never claiming the priority categories.** Fixed. `README.md:87` now names
  **family entertainment** and **multi-modal UX** in bold and explains why each applies.
- **Gap 17, the friction log leaving substantive platform findings out.** Mostly fixed. The
  log went from eleven entries to thirty, with four rated High, and the `manifest.toml`
  rewrite is now entry 16. Two of judge 1's four named findings still have no friction
  entry: `setNativeProps` throwing on React Native 0.83, and the one-captions-view-per-
  process rule. Both are feature requests 9 and 11 in `docs/FEEDBACK.md` and neither is a
  numbered friction entry, so a reviewer assessing the log alone still does not see them.
- **The video plan no longer waits on hardware.** Not one of judge 1's numbered gaps, but
  it follows from its gap 1. Commit 9621b2c correctly reads the rule that the Vega
  simulator satisfies the device requirement, so the video is no longer blocked on a stick.

Judge 1's headline finding, the unreachable kid mode, has been documented rather than
fixed. `docs/SHOT_MANIFEST.md:21` and `docs/VIDEO_SCRIPT.md:107` now name it in plain words
and count the nine blocked shots. Writing the hole down is the right first move and it is
not the fix.

### Where a fix introduced a new problem

One, and it is the kind that a second pass exists to catch. Judge 1's gap 13 said the stick
command was wrong in both `README.md` and `docs/SUBMISSION.md`. The most recent commit in
this clone is "The stick command pointed one directory too deep", and it corrected the
README and left `docs/SUBMISSION.md:235` wrong. The fix landed on the document a judge
reads and not on the field a judge pastes, which is the wrong way round, and it turned a
consistent error into an inconsistency between two documents that are supposed to agree.

### What judge 1 found that I missed

**Gap 12, the lead time published without its spread.** This is still open and I did not
find it. `results/gate1_software_vvd.json` records `lead_ms` with p95 of 4097 ms and max of
6197.5 ms beside the median of 488.4 ms, and the README publishes only the median and the
worst case. Judge 1's reading of what that spread means is right: a 4 second p95 says most
covers fired whenever the next position report happened to arrive rather than at a
scheduled moment, which is a material qualification of the scheduling claim. Judge 1 is
right, this should be gap 7 or 8 on my list, and I would put it there.

**Gap 19, `docs/PRIOR_WORK.md` is stale.** Also still open. It still says `app/` is "not
added yet" when `app/` is the entire Fire TV application, and `headstart/` likewise. It is
the document a reviewer would check Stage One line 14 against. I had folded this kind of
thing into my gap 13 as a category rather than naming this file, and judge 1 naming it is
better.

### What I found that judge 1 did not

Some of this is the calendar rather than the judging: `results/under_load/` did not exist at
judge 1's commit.

- **Near-threshold recall of 0.575.** `results/conformance.json` records
  `recall_near_limits = 0.575` over the 178 clips that sit on a limit, against the 0.895 the
  README now publishes, and `eval/EVAL_RESULTS.md` is the only document that says so and is
  linked from nowhere. Judge 1 asked for the conformance numbers and got them; what came
  back was the blended pair, and the split that matters most for a safety tool stayed out.
  This is the finding I would most want the team to act on, because it is the same asymmetry
  judge 1 named in its gap 11 reappearing one level down.
- **The under-load timing run.** `results/under_load/gate1_software_vvd_load218.json`:
  worst lead -454.6 ms, worst scheduler tick gap 72,755 ms, 8 of 9 trials in time.
  `docs/GATES.md` writes it up [in full] and the README still says "nothing yet measures
  what that worst pause is on real hardware".
- **`eval/meter.py` is claimed as built and does not exist**, and shot S04, which the script
  calls the shot the whole video exists for, is planned on three of its subcommands.
- **`README.md:137` is stale on the feature requests**, saying "request 1 in
  `docs/SUBMISSION.md`, alongside thirteen others" when the list lives in
  `docs/FEEDBACK.md` and has twenty-one. `docs/FEEDBACK.md` flags this drift about itself.
- **`hook/README.md` tells a reader to `npm install @calm-frames/flash-guard`**, which is
  not published anywhere.
- **`eval/screen.py`'s docstring still says "FLASHMAP IS NOT READY YET ... flashmap/ is an
  empty directory"** above a fully populated `flashmap/`.
- **A date inconsistency between the README and the Devpost text** on the Epilepsia paper,
  February 2026 in one and "A 2025 Epilepsy Foundation working group" in the other.

### Where I am softer than judge 1

The friction log bonus. Judge 1 recommended 6 of 10 against an eleven-entry log with
nothing rated High and no platform findings in it. I recommend 8 of 10, and that is not a
disagreement about standards: the log judge 1 read no longer exists. It is now thirty
entries, four of them High, with the platform material judge 1 asked for largely folded in.
Applying judge 1's own reasoning to the current file gives a higher number, and I think 8
is where it lands. We agree completely on `docs/friction_pending.md`: it still ships next
to the real log, judge 1 said it should not, and it still should not.

### My overall read

Tech Implementation 3, Design 2, Potential Impact 3, Quality of the Idea 4, Stage One FAIL
on seven of seventeen lines. Two independent judges agreeing on all four scores says the
instrument is working and the gaps are real. The difference between this and a shortlisted
entry is not more engineering, because the engineering is already better than the
submission that wraps it. It is one navigation wiring change, a camera, and a repository
setting.
