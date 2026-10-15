# Final handoff: the integration candidate

Written Oct 14, 2026, night (Pacific), after a remote-driven acceptance session
on the Vega Virtual Device. The candidate is local and committed; nothing is
pushed, merged, published, recorded or submitted. The app was installed and
driven on the simulator by this work, without any screenshot, video or capture.

## 1. Branch, commit and package

| What | Value |
|---|---|
| Branch | `claude/final-candidate-2026-10-14`, worktree `/Users/alexvintera/calm-frames-claude-final-2026-10-14` |
| Package source commit | `ac5a610e63deeaeca672d34da43279a1394ca65a` (`ac5a610`), the last commit that changes an app input; every commit after it is documentation, Python packages, checks or results |
| Package | `build/release/final-candidate-3-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg`, aarch64 Debug, 28,716,350 bytes (build output outside git, in the worktree above) |
| Package SHA-256 | `4d36c177c000eb6470ac39acef7e02bdfb72300697f4142e65522d3d3315a6c5` |
| Receipt | `build/release/final-candidate-3-2026-10-14/PREPARATION.json`: 736 recorded app inputs with hashes, inputs committed, prepared library checked with all 3 original reports present, catalog SHA-256 `02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79`, published false. `SHA256SUMS` and `NOTES.md` sit beside it |
| Tested on the device | This exact package, installed over the existing household with `vega device install-app`; no uninstall, no data reset, no PIN entered. Receipt: [`results/native-acceptance-2026-10-14/receipt.json`](results/native-acceptance-2026-10-14/receipt.json) |
| Build route | `source ~/vega/env`, fnm Node 22 and the watchman fallback shim on `PATH`, `JAVA_HOME=/opt/homebrew/opt/openjdk@21`, `DEMO_PIN` unset, then `RELEASE_PYTHON=/Users/alexvintera/calm-frames/.venv/bin/python bash scripts/release.sh --arch aarch64 --build-type Debug --tag final-candidate-3-2026-10-14`. The helper printed its publication command and it was not run |
| Earlier packages, preserved | `final-candidate-2026-10-14` from `93cf800` (`d53444ab…`) and `final-candidate-2-2026-10-14` from `52138fe`; Codex's `approved-coastal-b22d275-2026-10-14` in the coastal worktree |
| Lineage | `cfddc4a` (reliability) → `b22d275` (Codex: approved coastal interface) → the submission packet and the illustrated harbor ledger → `58bd1a7` (coastal artwork ledgered, credits regenerated) → `53ab01b` (hook mirror) → `93cf800` (coastal menus held to the ten foot floors) → `204f185` (debug breadcrumbs) → `487e5e5` (Back one level at a time in setup, the picker and the removal question) → `52138fe` (bundled copies of the practice stills) → `69390ed` (README opens on the coast) → `ac5a610` (opening readies on a moving clock) → `d7e13be` (documented checks runnable from a fresh checkout) → the judge-path fixes and this documentation |
| Previews | Static component export: <http://127.0.0.1:4174/> (served from `build/coastal-preview` in the worktree; regenerate with `.venv/bin/python eval/preview/coastal_preview.py` after `npx jest test/calmframes/coastalExport.test.tsx`). Codex's separate water study, read-only: <http://127.0.0.1:4175/>. Labelled browser renders of Home and Details: `results/coastal-renders-2026-10-14/` |

## 2. What changed, and the checks

**Integrated from the approved design (`b22d275`, Codex):** the ivory coast on
every menu screen with the dimensional coastal artwork, the expressive Harbor
title, the tactile Play button, the quiet Details action, the compact Try
picture holds entry, Help and Settings in the header, and dark playback
controls kept through `CoastalAppearance`.

**Fixed, each with a test that failed first:**
- A pressed coastal primary switched to the light surface fill while keeping
  its ivory label; it keeps its ink fill (`93cf800`).
- The storage error screen's Try again ring measured 2.89 to 1 inside its
  panel; the button sits on the page, where the ring clears 3 to 1 (`93cf800`).
- The play glyph was drawn under the 32 unit text floor (`93cf800`).
- Hardware Back fell through to the shelf and left the app from the profile
  picker, from every setup step and from the remove-a-kid question; each now
  closes one level (`487e5e5`, navigation worker).
- On the device every practice hold showed black: the loader refuses the data
  URI the signed map carries. The two stills ship as bundled copies, swapped in
  only on an exact match of the authenticated data URI, hash-checked against
  the signed map by a test (`52138fe`). The device session logged the still
  loading at both holds.
- On the device every playback ended on the recovery screen about fourteen
  seconds in: the opening shell waited for a frame counter the device's player
  never fills. A moving clock while playing now readies it; a counter that
  reports only dropped frames still waits, and a stalled clock still reaches
  recovery (`ac5a610`). The device session saw no recovery screen.
- The flashmap report page carried a palette no longer in the app; the brand
  asset flash check skipped the two newest pictures; ruff refused the study
  renderers. All three pass now, with the measured conformance scripts left
  byte for byte as recorded (the judge-path commit).

**Also added:** Debug-only breadcrumbs (`CALM_TRACE screen|focus|still|image`)
so a device session without capture can be judged from the log (`204f185`,
`ac5a610`); the README opens on the coast with labelled browser renders
(`69390ed`); the documented checks run from a fresh checkout, with the one
Python package the docs omitted and four drifted line links fixed (`d7e13be`).

**Checks.** On `ac5a610` from a fresh checkout with nothing copied (the judge
path): `npm ci --ignore-scripts`, typecheck, lint with 0 errors, and the full
app suite, 133 suites and 1309 tests passed; the analyzer's one-minute path
and the report page as written. On this worktree: typecheck, ESLint on changed
files, the hook package tests, the packed consumer check and the mirror tests,
the attribution tests, the brand asset tests, the design page tests, the
measured-source hash test, ruff over the repository, the style check and the
published number check, and the gitleaks hook at every commit. The full Python suite (`pytest flashmap pipeline eval -m "not slow"`) after the judge-path fixes: 1800 passed, 2 deselected, and one test that pins the report page's lane luminance figures, which the palette change moved from 5.59 and 2.52 to 5.63 and 0.93 cd/m2; the pins and the comment beside the constants now record those figures and the suite passes. mypy over flashmap (strict) and the pipeline was clean in the judge's fresh venv. No hosted CI run exists for the branch (no pull request).

**Ambient motion:** Codex's water study is a browser canvas effect with no
clean native path; the still artwork stays the release default and the study
stays separate.

## 3. Native acceptance, as observed

Method: the Debug package's own breadcrumbs and media events, read from
`vega device start-log-stream` while a driver pressed remote keys through the
device's `inputd-cli`. No pixels were seen and no audio was heard; "pass" means
the app reported the journey happening. Details and the open items are in the
receipt.

| Journey | Result | What the app reported |
|---|---|---|
| Cold launch | observed-pass | Running, Home with focus on Play |
| Remote reaches Home controls | observed-pass | Focus visited the profile chooser, Help, Play, Details and the practice entry |
| Home to Details and Back | observed-pass | Details with Play focused; Back returned to Home with focus on Details |
| Ordinary Harbor | observed-pass | playing, ended at 19999 ms, zero holds, no recovery screen, returned to Home with focus on Play |
| Pause, resume, Back from playback | observed-pass | pause, playing again, player left, focus on Play |
| Practice demo, two holds | observed-pass | cover on at 5000 to 9000 and 12000 to 16000, the still loaded at both, media clock through both holds, ended, back to Details and Home |
| Seek by remote inside the demo | observed-partial | No seeking event after the presses; a pause event followed, so the keys reached the player. Covered by tests and by the Oct 10 on-device receipt |
| Help | observed-pass | Help opened with its first control focused; Back returned Home with focus on Help |
| Settings PIN gate | observed-pass | The gate opened with key 1 focused; Back returned Home. Interior not entered: no PIN |
| Relaunch without clearing data | observed-pass | Home again, no first run, focus on Play |
| Back on the Home root | observed | Exits to the launcher, the platform's convention; left alone |

**Not observed:** the artwork, fonts, focus rings, caption text and the hold
still as pixels; audio; the caption menu; the parent settings interior
(household PIN); VoiceView; any physical television. **Open observation:** one
image loader error is logged at every mount of the home scene while both
pictures in it report loading; the remaining candidate is the scene's gradient
view, and no visible defect is established.

## 4. Native acceptance checklist for the owner (eyes and ears)

Install the package in section 1 with the commands in
[`docs/submission/REVIEWER_QUICKSTART.md`](docs/submission/REVIEWER_QUICKSTART.md)
section 3 and confirm by looking and listening:

1. Home: the coastal artwork fills the screen; "Harbor", "20 sec · No picture
   holds", Play with a triangle, Details, the picture-holds line, the Try
   picture holds entry; Help and Settings in the header; text readable from
   the couch; focus rings visible on every control, terracotta on a focused Play.
2. Try picture holds: the countdown and Skip, then at each hold the calm still
   (not black) with the "Holding a calm scene" card, captions changing, sound
   continuing without a gap.
3. Harbor: plays through, sound audible, no hold, no error screen.
4. Playback controls: dark and readable over the video; pause shows a readable
   paused state after the controls hide; Back returns to the launching screen.
5. Settings: a wrong PIN refused with tries remaining, Delete corrects, the
   right PIN opens presets, room, chime, motion and sounds; a changed preset
   survives a relaunch.
6. Help reads correctly; the home scene's reading edge fades the artwork
   behind the text (the open observation above).
7. VoiceView, if available, names controls by their accessible names.

Record what was seen and heard in a new `results/` receipt with the package
hash. Do not reset household data.

## 5. Remaining owner actions, by submission impact

1. Run the checklist in section 4 and decide whether `ac5a610`, with the
   documentation on top, becomes the judged release; then merge to `main` and
   cut the tag that never moves.
2. Authorize and make the recording from
   [`docs/submission/DEMO_SCRIPT.md`](docs/submission/DEMO_SCRIPT.md), assemble
   and check it, upload to YouTube or Vimeo, and check the link logged out.
3. Choose reviewer access: public (merge, licence visible in About, audit
   exception dates, private vulnerability reporting, item 5) or private with
   `testing@devpost.com` and the six Amazon reviewers invited at submission.
   Fill in the About box either way.
4. Confirm eligibility, the contact email and the Devpost registration.
5. Settle the licence items: the Amazon sample's conflicting notices (still
   unresolved; clarification unsent), the CC0 confirmation for the generated
   Harbor artwork, and the position on the generated coastal artwork, which the
   ledger records without any ownership claim.
6. Optional: the Open Source contribution URL and the AWS Builder entry with
   the inactive cost allocation tag.
7. Approve the friction log and product feedback for publication as written.

## 6. Where the submission text lives

- Description to paste: `docs/submission/DEVPOST_DRAFT.md`.
- Narration and shot plan (2:40): `docs/submission/DEMO_SCRIPT.md`.
- Requirements against the repository: `docs/submission/CHECKLIST.md`.
- Judge setup, run and demo steps: `docs/submission/REVIEWER_QUICKSTART.md`.
- Decisions and blockers: `docs/submission/OPEN_DECISIONS.md`.
- The longer field by field draft: `docs/SUBMISSION.md`; product feedback
  `docs/FEEDBACK.md`; friction log `docs/FRICTION_LOG.md`.

## 7. Reviewer access, licensing and eligibility, unresolved

The rules allow a public repository with an open source licence visible in
About, or a private one shared with `testing@devpost.com`, `chris-trag`,
`knmeiss`, `giolaq`, `anishamalde`, `mosesroth` and `emersonsklar`. The
repository is private today and GitHub detects Apache License 2.0. Unresolved:
the Amazon sample notices (`docs/AMAZON_SAMPLE_LICENSE_REVIEW.md`,
`results/release-pin-license-review-2026-10-14.json`), the dedications and
positions on the generated artwork, and the entrant's eligibility and contact
details (`docs/SUBMISSION.md` section 15).

**Supported devices.** The package targets Vega OS, Amazon's newer non-Android
TV platform, and has only ever run on the Vega Virtual Device. Fire OS devices,
which is most Fire TV sticks and Cubes in homes today, cannot install it. Press
coverage of Amazon's September 30, 2025 announcement names the Fire TV Stick
4K Select as the first Vega OS device; this project has not run on it, and the
current device list should be read from Amazon's documentation before it is
stated on the form.

## 8. Finished work and optional improvements

**Finished:** the approved design integrated and held to the repository's
floors; two device defects found and fixed with tests; three Back traps fixed;
the credits, ledger and hook mirror current; the documented checks runnable
from a fresh checkout; one package built from a committed source with its
receipt and driven on the device; the submission packet and this handoff.

**Optional, not started:** the caption button for a title without tracks
opens a menu that lists only Off (it is announced as "Captions unavailable");
a bundled-still path for prepared titles beyond the practice demo; seeking by
remote re-observed on the device; the gradient loader message; the Open Source
and AWS Builder entries; a changelog section for the judged tag, written when
the tag exists.
