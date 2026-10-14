# Final handoff: the integration candidate

Written Oct 14, 2026 (evening, Pacific). This is the state of the candidate
Claude prepared after Codex handed over the approved coastal interface. It is
local and committed; nothing is pushed, merged, published, recorded or
submitted, and the app has not been installed or run on any device by this work.

## 1. Branch, commit and package

| What | Value |
|---|---|
| Branch | `claude/final-candidate-2026-10-14`, worktree `/Users/alexvintera/calm-frames-claude-final-2026-10-14` |
| Package source commit | `93cf80028529992cedc4439cb29a59d6ff024188` (`93cf800`), the last commit that changes an app input; the documentation commits after it change no app input |
| Package | `build/release/final-candidate-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg`, aarch64 Debug, 28,664,945 bytes (build output outside git, in the worktree above) |
| Package SHA-256 | `d53444ab70f38d24fb4cb1c468ebe78e0ed24cc6932c45235e50dd174fb2a25a` |
| Receipt | `build/release/final-candidate-2026-10-14/PREPARATION.json`: 728 recorded app inputs with hashes, inputs committed, prepared library checked with all 3 original reports present, catalog SHA-256 `02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79`, native validation false, published false. `SHA256SUMS` and `NOTES.md` sit beside it |
| Receipt recheck | After the documentation commit `668f941`, `scripts/release.sh --skip-build --receipt app/build/aarch64-debug/release-build-receipt.json --tag final-candidate-recheck-2026-10-14` passed at that head: 728 inputs still match and the copied package hashes `d53444ab…` again (`build/release/final-candidate-recheck-2026-10-14/`) |
| Build route | `source ~/vega/env`, fnm Node 22 and the watchman fallback shim on `PATH`, `JAVA_HOME=/opt/homebrew/opt/openjdk@21`, `DEMO_PIN` unset, then `RELEASE_PYTHON=/Users/alexvintera/calm-frames/.venv/bin/python bash scripts/release.sh --arch aarch64 --build-type Debug --tag final-candidate-2026-10-14`. Built once; the helper printed its publication command and it was not run |
| Lineage | `cfddc4a` (reliability: immediate player setup recovery, PIN kept out of reviewer notes) → `b22d275` (Codex: approved coastal interface) → `fbcbe20`, `5065314`, `cf53d39` (the submission packet and the illustrated harbor ledger, cherry-picked) → `58bd1a7` (coastal artwork ledgered, credits regenerated) → `53ab01b` (hook mirror) → `93cf800` (coastal menus held to the ten foot floors) |
| Previews | Static component export of this candidate: <http://127.0.0.1:4174/> (served from `build/coastal-preview` in the worktree; regenerate with `.venv/bin/python eval/preview/coastal_preview.py` after `npx jest test/calmframes/coastalExport.test.tsx`). Codex's separate water study, read-only: <http://127.0.0.1:4175/>. Both are browser approximations of rendered component trees, not the device |

The package is a Zstandard compressed tar. Its listing holds `assets/image/tv/coastal-zen.png` with its provenance file, `harbor-illustrated.png`, the bundled fonts, the prepared library with its catalog, and the JavaScript bundle, which carries the regenerated credits titles for both pictures.

Codex's own package of the coastal commit (`a6ecd33e…`, 728 inputs, built from `b22d275`) is preserved in the coastal worktree and superseded by the one above, which carries the credits list, the pressed state fix and the retry button move.

## 2. What changed, and the checks

**Integrated, from the approved design (`b22d275`, Codex):** the ivory coast on
every menu screen with the dimensional coastal artwork (`coastal-zen.png`), the
expressive Harbor title, the tactile Play button with its glyph, the quiet
Details action, the compact Try picture holds entry, Help and Settings in the
header, and dark playback controls kept through `CoastalAppearance`.

**Fixed on top (`93cf800`):**
- A pressed coastal primary switched to the light surface fill while keeping
  its ivory label; it now keeps its ink fill, so the label stays legible.
- The storage error screen's Try again button sat inside the notice panel,
  where its terracotta focus ring measured 2.89 to 1; it now sits on the page,
  where the ring clears 3 to 1.
- The decorative play glyph is drawn at the 32 unit text floor instead of 30.
- The declared frame inventory (`uiFrames.ts`) moves the menus to the coastal
  palette and names the ink fill a focused primary paints; every player frame
  stays dark. The ten foot pass accepts each palette's own ring colours with
  its contrast floors unchanged, and seven tests that named the dark palette
  for menu screens now name the coastal one.
- The hook package mirrors the coastal control files (`53ab01b`).
- The coastal artwork has a ledger row, and NOTICE and the credits screen are
  regenerated from the ledger (`58bd1a7`). The earlier `harbor-illustrated.png`
  row (`cf53d39`) records it as a pixel-identical render of our own
  `app/assets/brand/tv/harbor.svg`. Neither row asserts ownership or a CC0
  dedication; the coastal row says exactly what its provenance file says.
- `docs/design/README.md` documents the coastal palette and the switch.

**Checks on `93cf800`, all passed:** the full app suite (130 suites, 1295
tests passed, 4 skipped, 57 snapshots; log in `.logs/final/jest-full2.log`,
outside git), `npm run typecheck`, ESLint on the changed files with nothing
reported, the hook package tests, the offline packed consumer check and the
five mirror tests, the eleven attribution tests, the 21 design page tests, the
repository style check and the published number check, and the gitleaks hook
at every commit. Before the fixes, the same suite on the coastal commit had 40
failures in eight suites (`.logs/final/jest-full.log`).

**Not done, on purpose:** no hosted CI run (the branch has no pull request;
CI runs on `main` pushes and pull requests), no native install, launch,
capture or recording, no AWS, no push.

**Ambient motion:** Codex's water study is a browser Canvas that distorts a
masked patch of open water pixel by pixel. The native stack has no canvas and
no supported path to that effect without new rendering code or a looping
video behind the menus, which would have to be released before story playback
and checked on the device for layering, focus and reduced motion. The release
default stays the approved still artwork; the study stays separate and
unmerged. The existing opt-in ripples and reduced motion behaviour are unchanged.

## 3. Native acceptance checklist (owner step, Vega Virtual Device only)

Install the package above with the commands in
`docs/submission/REVIEWER_QUICKSTART.md` section 3. Expected outcomes:

1. **First run** asks for a four digit PIN, a profile, a preset and the room;
   finishing lands on Home. No preset PIN exists.
2. **Home** shows the coastal artwork full bleed, "Harbor" with "20 sec · No
   picture holds", Play (with a triangle glyph, not a box) and Details, the
   line "Picture holds on supported videos. Audio continues.", and the Try
   picture holds entry with "20 sec · 2 practice holds". Header: Help and
   Settings. Text reads from the couch; nothing sits inside the safe margins.
3. **Focus** is visible on every control: deep teal ring on quiet and
   secondary controls, terracotta ring with ink fill on a focused Play, and
   the label stays legible while OK is held down.
4. **Details** opens with Play focused; Back returns to Home with focus on the
   control that opened it.
5. **Try picture holds** plays the 20 second film with a countdown and Skip
   before each of the two practice holds; during a hold the picture is a calm
   still with the "Holding a calm scene" card, sound continues, English
   captions change. Dark controls over the video; pause and resume work;
   controls hide after six seconds and the paused state stays readable.
6. **Harbor** plays through with zero holds and captions.
7. **Settings** opens the PIN gate; a wrong PIN is refused with tries
   remaining, Delete corrects, the right PIN opens profiles, preset, TV size,
   distance, chime, motion and sounds; a changed preset survives a relaunch.
8. **Loading failure and retry:** a title that cannot load reaches the recovery
   screen at once, Try again is focused on the page, and Back returns Home.
9. **Help** opens the plain language page and Back returns to the header.
10. **VoiceView**, if available, announces controls by their accessible names
    (Help: How it works; Settings: Parental controls; Play: Harbor).

Record what was seen, what failed and what could not be reached, with the
package hash, in a new `results/` receipt. Do not reset household data.

## 4. Remaining owner actions, by submission impact

1. Run the native acceptance above and decide whether `93cf800` (or a later
   head with only documentation on top) becomes the judged release; then merge
   to `main` and cut the tag that never moves.
2. Authorize and make the recording from `docs/submission/DEMO_SCRIPT.md`,
   assemble and check it, upload to YouTube or Vimeo, and check the link while
   logged out.
3. Choose reviewer access: public repository with the licence visible in About
   (after the merge, the audit exception dates, private vulnerability
   reporting and item 5), or private with `testing@devpost.com` and the six
   Amazon reviewers invited at submission. Fill in the About box either way.
4. Confirm eligibility (age of majority, no Sponsor or Administrator
   affiliation), the contact email and the Devpost registration.
5. Settle the licence items: the Amazon sample's conflicting notices (still
   unresolved; clarification unsent), the CC0 confirmation for the generated
   Harbor artwork, and the position on the generated coastal artwork, which the
   ledger records without any ownership claim.
6. Optional, not blocking: the Open Source contribution URL (fork and upstream
   pull request, or the repository's own packages once public) and the AWS
   Builder entry with the inactive cost allocation tag.
7. Approve the friction log and product feedback for publication as written.

## 5. Where the submission text lives

- Description to paste: `docs/submission/DEVPOST_DRAFT.md`.
- Narration and shot plan (2:40): `docs/submission/DEMO_SCRIPT.md`.
- Requirements against the repository: `docs/submission/CHECKLIST.md`.
- Judge setup, run and demo steps: `docs/submission/REVIEWER_QUICKSTART.md`.
- Decisions and blockers: `docs/submission/OPEN_DECISIONS.md`.
- The longer field by field draft: `docs/SUBMISSION.md`; product feedback
  `docs/FEEDBACK.md`; friction log `docs/FRICTION_LOG.md`.

## 6. Reviewer access, licensing and eligibility, unresolved

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

## 7. Finished work and optional improvements

**Finished:** the approved design integrated and held to the repository's
floors; the credits and ledger current; the hook mirror current; one package
built from a committed source with its receipt; the submission packet updated
to this candidate; this handoff.

**Optional, not started:** ambient water motion on the device; a native
double ring for the focused primary that would clear every surface with a wide
margin; the Open Source and AWS Builder entries; the picture break and
buffering prototypes on their own branches; a changelog section for the judged
tag, which is written when the tag exists.
