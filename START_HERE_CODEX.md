**Current cloud continuation, October 25:** source/toolchain `09b3c55603ddff50bb068a585980aa188002479e`, continuing from `64f792b`. [Current record](docs/cloud-followup-2026-10-25/README.md) and [single native handoff](docs/cloud-followup-2026-10-25/NATIVE_VERIFICATION.md) supersede the earlier next-action instructions below. Eight more dependency findings are fixed, leaving five; Audit still fails. Local-import record/worker recovery is fixed. The original checklist remains 6 complete, 12 partial, 2 blocked. No new native acceptance, push or publication.

**Current local continuation:** [native fixes, checks and exact-source handoff](docs/native-fixes-2026-10-25/README.md). Product source is `a6bdb62276dd63603716509e24b2034451b46b44`; the export records the final documentation HEAD. The received 37d10c2 handoff below is historical and unchanged in scope. Its original 5/20 tally precedes the presentation reconciliation; use the [current ledger](docs/cloud-integration-2026-10-23/CHECKPOINT.md) for 6/20.

# Start here: native validation of fbe53bf, handed to cloud Codex

This branch, `codex/native-validation-handoff-2026-10-25`, is the verified source
`fbe53bf9e5ff432dbc28cd68cd8b89e3f5cac93f` plus documentation and fictional-household
evidence from the Mac validation run on 2026-10-25. No product code changed. It is a
handoff for fixing three native defects (D1, D2 and D3 below), not a release approval.
Nothing was merged, no tag was created, the default branch is unchanged, and the
submitted fallback `bf2f615` and `docs/judging-package` are untouched. Further Mac-only
checks wait until the owner is home.

Read next: [the receipt](results/native-validation-fbe53bf-2026-10-25/receipt.json), then
[the canonical checkpoint](docs/cloud-integration-2026-10-23/CHECKPOINT.md), whose 20-item
ledger matches the one below.

## Exact identities

| What | Value |
|---|---|
| Source | `fbe53bf9e5ff432dbc28cd68cd8b89e3f5cac93f` (from the verified overnight bundle, base `15ef46c6e23c8ba627492da23b1b147000031aa4`); this branch adds only `START_HERE_CODEX.md`, `results/native-validation-fbe53bf-2026-10-25/` and ledger notes in `docs/cloud-integration-2026-10-23/CHECKPOINT.md` and `CLAUDE.md` |
| Transfer received | `calm-frames-native-validation-fbe53bf.zip`, sha256 `85e9f65c1f8a9ba47a5fbf2d0f6a0db1bca1d513ead3888295af28eca6546a2a`; all 5 outer and 13 inner sums OK |
| Debug package | 132,667,620 bytes; sha256 `3ce800cf493af7a54aeb0b6a16785f3bb6e9d3d778a9930b257458b2ec4f276d`; sha384 `2b98119e38dd32128827c6e4241722b34aa0ab34101d5dd9526d8abd4b97a17984d9cc645451ddb06c9f692b94426bdf` |
| Release package | 132,101,221 bytes; sha256 `8ce683285c12172dd515a7758313d60572fdd511f7a94c0e66bd22efbf020fea`; sha384 `ace30351afc9ed7ea251b026bec789bd0f14eb2a871b85eae50ec17c032624ebc257bdfb35401248f74703785e5a2557` |
| Builds | Debug exit 0 in 78.07 s, Release exit 0 in 75.14 s, through the handoff's 20-minute wrapper with the normal prebuild gates and package checks; source tree clean before and after; build inputs unchanged |
| Installed, main device (real household, read only) | Debug, installed sha384 `2b98119e...6bdf`, install time Oct 23 03:58:40 GMT kept, updated Oct 25 15:50:11 GMT; household retained; no PIN entered; VoiceView off |
| Installed, disposable device (made-up household, deleted afterwards) | Debug then Release, package scoped; Release installed sha384 `ace30351...2557`, install time kept, updated 18:41:02 GMT |
| Retained rollbacks, verified, not used | a672f57: sha256 `8cc0ffd52fc61df17d8b69b40c31964c5ed0749c578ec1de67e1aedf78173dd8`, sha384 `480fd42d96096bb5a2b2c1a471fb0f498ab284118facd0561bdef19750e56506bded03dd3ec3e00204efced90ef30d59`; 6a87937: sha256 `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d`, sha384 `b268be9946241be7e8efab64737e6672b907dfb2d9558cae6a90acb51349b1b02b63e68a7ea63fe4d259a8db432eb458` |
| Tools | Vega SDK 0.24.9914, Vega CLI 1.3.4, node v22.23.2, npm 10.9.8, Python 3.12.13, OpenJDK 21.0.12.1 (the Homebrew fallback the handoff names) |

Package inventories are read from each package and tied to its own source map: packaged
`index.bundle` sha256 Debug `8e931bf12f075052e48a6b5c8613b2f9dd4ae9e30b991a901e1e060f2341c9e1`
and Release `2ee4a5fc7891fb26315049477d7a9d58107122fd62047302dc8c11ddb33c152f`; each map
is named after that hash and carries it as `x_amazon_bundleId`. Debug ships 89 versioned
module instances, Release 76. Of the residual advisories only `decode-uri-component` 0.2.2
ships, in both packages; Audit still fails and no exception was renewed. Details:
[instances-debug.json](results/native-validation-fbe53bf-2026-10-25/native-results/instances-debug.json),
[instances-release.json](results/native-validation-fbe53bf-2026-10-25/native-results/instances-release.json),
[shipped-versions.json](results/native-validation-fbe53bf-2026-10-25/native-results/shipped-versions.json).

## Owner decision recorded on 2026-10-25

The disclaimer layout is accepted as-is, so #6 is complete. It closes against the navigation
that already passed: the production first run at 1920 by 1080 and 1280 by 720 on `a672f57`
(steps open at top, one Down reaches Next, Up reaches the explainer reading stop, Down returns,
Open library reaches Home). `FirstRunScreen.tsx` is unchanged between `a672f57` and `fbe53bf`,
and the fbe53bf first run at 1920 by 1080 repeated the explainer route:
[at rest](results/native-validation-fbe53bf-2026-10-25/evidence/d07-1080-explainer-at-rest.jpg),
[one Up onto the stop](results/native-validation-fbe53bf-2026-10-25/evidence/d08-1080-explainer-one-up.jpg),
[one Down back](results/native-validation-fbe53bf-2026-10-25/evidence/d09-1080-explainer-down.jpg),
[Open library to Home](results/native-validation-fbe53bf-2026-10-25/evidence/t01-1080-open-library-sheet.jpg).
No layout change is requested. This is not audiovisual or comfort acceptance; #8 stays with
the owner.

## Passing source tests are not native acceptance

Codex recorded these source results at fbe53bf in the transfer's `CHECK_RESULTS.json`: 180 app
suites and 1,900 app tests passed, 2,122 Python tests passed, and the exact-head secret, docs
and whitespace checks passed. They were not rerun on the Mac; the handoff did not ask for it.
The native behavior below was observed on the fbe53bf Debug package on the Vega Virtual Device.

| Area | Source side at fbe53bf | Native on fbe53bf |
|---|---|---|
| Up from Watch on Home | all app suites passed; Jest does not run the platform's spatial D-pad movement, and the closest test (`journeyFlow.test.tsx`, selection stays marked when focus moves from a poster to Watch) covers the other direction | failed: D1 |
| Focus after a Reading comfort save | `readingComfort.test.tsx` passed, including "retains a single focus target" and "does not steal focus if the remote moved away during the save" | failed: D2 |
| Pause announcement once per real pause | `playbackUi.test.tsx` passed: "one pause announcement survives controls hiding and is spoken again only after another pause"; it failed against the old source | failed: D3 |
| Reading comfort state, isolation, wrapping, persistence, VoiceView wording | source and route tests reported passing | observed at both sizes |
| Stricter profile covers and per-kid positions | guard and checkpoint tests reported passing | observed (resume only; retry not reached) |

## D1: Up from Watch changes the selected title

- **Expected.** On Home, Up from Watch returns focus to the card Watch belongs to, and moving
  between Watch and the cards never changes the chosen title by itself.
- **Observed.** Up from Watch lands on whichever middle card is nearest the centered Watch
  button (McWay Falls or Sea Otters). Card focus selects a title, so the check mark, the boat
  and Watch move to that card. Down from Sea Otters or Forest lands on Details, not Watch.
- **Repro.** Home, Acadia chosen, focus on Watch, press Up: McWay is focused and chosen. From
  Forest, Down then Up: Sea Otters is chosen.
- **Seen on.** fbe53bf Debug at 1920 by 1080 and 1280 by 720, and fbe53bf Release at 1280 by 720.
  `KidHomeScreen.tsx` is unchanged since `a672f57`, so this predates fbe53bf.
- **Evidence.** [h01](results/native-validation-fbe53bf-2026-10-25/evidence/h01-1080-up-from-watch.jpg),
  [h02](results/native-validation-fbe53bf-2026-10-25/evidence/h02-1080-acadia.jpg) to
  [h04](results/native-validation-fbe53bf-2026-10-25/evidence/h04-1080-up-again.jpg),
  [h07](results/native-validation-fbe53bf-2026-10-25/evidence/h07-1080-forest-down-up.jpg),
  [e03 at 720](results/native-validation-fbe53bf-2026-10-25/evidence/e03-720-up-from-watch.jpg),
  [r21 on Release](results/native-validation-fbe53bf-2026-10-25/evidence/r21-720-release-mcway-watch.jpg),
  [m11, Down to Details](results/native-validation-fbe53bf-2026-10-25/evidence/m11-1080-forest-down.jpg).
- **Where to look (hypothesis from reading source, not verified natively).** In
  [KidHomeScreen.tsx](app/src/calmframes/KidHomeScreen.tsx) each card's `onFocus` selects its
  title, and nothing routes Up from the Watch row to the selected card, so the platform's
  nearest-element movement decides.
- **Mac check after a fix.** From every card: Down reaches Watch for that card, and Up from Watch
  returns to it with the selection unchanged, at both sizes.

## D2: focus jumps to the page-top Back after a Reading comfort save

- **Expected.** After Select on Reading comfort, focus stays on the switch, the row with its new
  On or Off state is fully in view, and the next Up or Down moves to the neighbouring control.
- **Observed.** The state saves correctly, but the next D-pad press in any direction lands on
  the page-top Back. Turning it On also pushed the focused row mostly below the visible edge
  with its state off screen, and no scroll followed. With VoiceView on at 720, focus moved to the
  top Back about 10 s after the save without a key, and VoiceView read "Parental controls".
- **Repro.** Parents, choose a kid, Down eight times to Reading comfort, Select, then Down.
- **Seen on.** fbe53bf Debug at 1920 by 1080 and 1280 by 720.
- **Evidence.** [p24](results/native-validation-fbe53bf-2026-10-25/evidence/p24-1080-kid-comfort-on.jpg),
  [p25](results/native-validation-fbe53bf-2026-10-25/evidence/p25-1080-kid-comfort-on-still.jpg),
  [p26](results/native-validation-fbe53bf-2026-10-25/evidence/p26-1080-comfort-up.jpg),
  [p30](results/native-validation-fbe53bf-2026-10-25/evidence/p30-1080-after-toggle-down.jpg),
  [e26 at 720](results/native-validation-fbe53bf-2026-10-25/evidence/e26-720-after-off-down.jpg),
  [e28 with VoiceView](results/native-validation-fbe53bf-2026-10-25/evidence/e28-720-after-vv-toggle.jpg),
  [a10 transcript](results/native-validation-fbe53bf-2026-10-25/evidence/a10-720-comfort-toggle-on.transcript.txt).
- **Where to look (hypothesis from reading source, not verified natively).** In
  [ParentAreaScreen.tsx](app/src/calmframes/ParentAreaScreen.tsx) the switch's `onBlur` clears
  `comfortReturnFocus`, which makes the header's `preferredBack` condition true, and
  [CalmPageHeader.tsx](app/src/calmframes/CalmPageHeader.tsx) passes that to the top Back as
  `hasTVPreferredFocus`. The larger text also changes the row's height without a scroll to keep
  it in view.
- **Mac check after a fix.** Off to On and On to Off at both sizes, with and without VoiceView:
  focus and the state stay visible, and Up and Down go to the neighbours.

## D3: the pause announcement is not heard on real pauses

- **Expected.** With VoiceView on, each real pause says "Paused. Press Play to continue." once;
  showing and hiding the controls during the pause adds nothing; the next real pause speaks again.
- **Observed.** VoiceView on, Dolby kept (the owner's device setting): nothing was spoken on any
  of three real pauses across two runs, including while the controls showed and hid. The sentence
  was spoken once while the player was opening after Resume, before any pause. No repeats on
  hide, because nothing was spoken.
- **Repro.** VoiceView on (Back and Menu held), choose Do not disable Dolby if asked. McWay, Watch,
  Resume; once it plays, Play/Pause; wait 10 s; Down and Up to show and hide the controls;
  Play/Pause to resume; Play/Pause again.
- **Seen on.** fbe53bf Debug at 1920 by 1080; not repeated at 720. `a672f57`, whose polite live
  region spoke after the controls hid, did speak on pause (repeatedly), in the acceptance archive.
- **Recorded separately, as the handoff asked.** Resume entry: "McWay Falls. Resume at 1:18,
  button" and "Resume at 1:42, button", then "Back, button". Seek bar: "Current progress is 27%,
  28%" and "34%". In the second run the picture held at 1:42 for about 10 s after Resume, and
  later the app's own Playback slow card with Try again appeared and was read; Try again was not
  pressed.
- **Evidence.** [a01 transcript](results/native-validation-fbe53bf-2026-10-25/evidence/a01-1080-pause-once.transcript.txt),
  [a01 frames](results/native-validation-fbe53bf-2026-10-25/evidence/a01-1080-pause-once-frames.jpg),
  [a03 transcript](results/native-validation-fbe53bf-2026-10-25/evidence/a03-1080-pause-repeat.transcript.txt),
  [a03 frames](results/native-validation-fbe53bf-2026-10-25/evidence/a03-1080-pause-repeat-frames.jpg).
  Frame times and key times are in each `.transcript.json` and in the ledger.
- **Where to look (hypothesis, not verified).** [VideoPlayerUI.tsx](app/src/w3cmedia/mediacontrols/VideoPlayerUI.tsx)
  now calls `announceForAccessibility` when `paused` becomes true and sets the notice's live region
  to none. The effect also runs while the player opens paused, which fits the one sentence heard
  on entry. At a real pause the call happens at once, while the Dolby media session may still be
  active; the system's own dialog says VoiceView may need playback paused or left before it speaks.
- **Mac check after a fix.** Same repro with Dolby kept, at both sizes; count the sentence per
  real pause and confirm nothing is spoken on entry or on hide.

## Unresolved: the pale first frame (#3)

A near-white frame (mean luma 240 of 255) appears only when the player route opens. It was
not seen on still scenes, Open library or cold starts. The recorder writes a frame only on a picture
change, so these durations are lower bounds.

| Transition | Near-white frame |
|---|---|
| Home Watch on McWay (playing) | about 0.07 s |
| Details Watch on McWay with a saved place (resume prompt) | about 0.07 s |
| Sea Otters still scene, Video preview 20 sec | about 0.42 s, then the Opening your video card, then a different coastal shot for about 0.2 s before the otters |
| Forest still scene, Video preview 12 sec | about 0.47 s, then the Opening your video card; one black frame (33 ms) as the preview ended into its still |
| Still scenes, Open library, cold starts at both sizes, Release cold start | none |

The cause is not established. [NATIVE_LIMITS.md](docs/overnight-2026-10-25/NATIVE_LIMITS.md)
already states this limit; do not change cover or decoder timing without new native evidence.
Data: [pale-frame-measurements.json](results/native-validation-fbe53bf-2026-10-25/evidence/pale-frame-measurements.json),
[Sea Otters start frames](results/native-validation-fbe53bf-2026-10-25/evidence/t12-1080-otters-preview-start-frames.jpg),
[Forest start frames](results/native-validation-fbe53bf-2026-10-25/evidence/t14-1080-forest-preview-start-frames.jpg),
[per-frame luma](results/native-validation-fbe53bf-2026-10-25/evidence/t12-1080-otters-preview-luma.csv).

## The original 20-item ledger after this pass

Completed: 5, 6, 9, 15, 18. Partially completed: 1, 2, 3, 4, 7, 10, 11, 12, 13, 14, 16, 19, 20. Blocked: 8, 17.
Newly closed by this pass: #6, on the owner's decision.

| # | Original outcome | Status | Native result and what remains |
|---|---|---|---|
| 1 | Cohesive native Fire TV design | Partially completed | Current native images at both sizes now exist; owner visual acceptance pending; D1 affects focus. |
| 2 | Remove redundant copy, keep safety, accessibility and error instructions | Partially completed | Native copy sweep at both sizes found nothing redundant or missing; error views not reached; stays open while D1 is open. |
| 3 | Calm cold start, loading, first frames, errors, transitions | Partially completed | Cold starts, Open library, Watch, resume and preview transitions recorded; the pale first frame is measured, cause unknown; error views not reached. |
| 4 | Visible Watch and distinct card focus at both sizes | Partially completed | Watch visible and focus ring distinct at both sizes; D1 fails card focus. |
| 5 | PIN, profile panel and kid-name UX | Completed | Retained; not repeated. |
| 6 | Reachable onboarding Next, Back and footer with readable disclaimer | Completed | Owner accepted the layout as-is on 2026-10-25; navigation passed both sizes on a672f57; fbe53bf repeated the route at 1920 by 1080. |
| 7 | Sustained ambient viewing beyond McWay | Partially completed | Sea Otters and Forest are silent still scenes with optional 20 s and 12 s previews; only McWay has a 5-minute edition; no long Forest or Sea Otters edition exists. |
| 8 | Owner audiovisual and comfort review | Blocked | Owner review on the installed fbe53bf Debug package, naming that package. |
| 9 | Native timing evidence or truthful limitations | Completed | Retained. |
| 10 | Recovery keeps floors, per-profile positions and captions | Partially completed | Kid 2 on Extra cautious covers 9 s of Acadia against Kid's 7 s; separate McWay positions kept and ordinary resume worked, carried into Release; error retry and covered moving playback not reached; no caption tracks. |
| 11 | Native readability, D-pad order, VoiceView, reduced motion | Partially completed | D2 and D3 failed; resume-entry and seek bar speech recorded; system reduced motion is unavailable on the virtual device. |
| 12 | Technical depth, dependency remediation, final validation | Partially completed | Exact builds and source-map-bound inventories for both packages; only decode-uri-component 0.2.2 ships; Audit still fails. |
| 13 | Personal-file import and caregiver pre-check | Partially completed | Not part of this pass. |
| 14 | GitHub presentation with actual screenshots and build identity | Partially completed | Current native captures exist here; presentation reconciliation pending. |
| 15 | Devpost and YouTube description drafts | Completed | Retained. |
| 16 | Replacement-demo tooling and assembly | Partially completed | Not part of this pass. |
| 17 | Submission and judge-access requirements | Blocked | Not part of this pass. |
| 18 | Consolidated source, exact SHA, checklist and handoff | Completed | This branch records the exact fbe53bf identities and native results. |
| 19 | Validated release artifacts; publication waits for the owner | Partially completed | Debug and Release built, installed and identified; Release launch, Watch, Back and persistence observed; release gates and publication remain. |
| 20 | Optional per-profile Reading comfort | Partially completed | Per-kid state, isolation, wrapping, scrolling, persistence and VoiceView observed at both sizes; D2 and the owner's comfort judgment remain. |

## Not observed, and Mac checks queued for when the owner is home

- Error views and the playback error Try again route (no fault harness was used).
- Covered intervals during moving playback for the stricter profile; caption restoration (the
  consumer catalog has no caption tracks).
- System reduced motion (`a11y-tv-util settings list` answers "Error obtaining user profile object";
  no settings screen). The app's Gentle artwork motion was left at its default, off; Home stays still.
- D3 at 1280 by 720; Release VoiceView and Parents changes; a physical Fire TV.
- After the fixes: the three Mac checks above, then the owner's picture, sound, palette, pace and
  comfort review on the exact fixed package.

## What is in this branch

[results/native-validation-fbe53bf-2026-10-25/](results/native-validation-fbe53bf-2026-10-25/receipt.json)
holds the receipt, the machine results (`native-results/`), review copies of the cited captures
with transcripts and tables (`evidence/`, provenance in `evidence/MANIFEST.json`) and the full step
ledger (`ledger/steps.jsonl`). Every capture is of the made-up household on the disposable device.
Excluded by rule: the private main-household captures and audio, PIN screens and keypads even with
nothing typed, videos, raw device logs and identifiers, packages and rollbacks, source maps, and
every never-merge or harness branch. The 25 own-commit IDs of the ten never-merge branches are
listed in [never-merge-own-commit-ids.json](results/native-validation-fbe53bf-2026-10-25/native-results/never-merge-own-commit-ids.json);
none is in this branch's history. Text was redacted for the private home directory before it
entered the repository.

## Attach separately (not in git)

- `calm-frames-native-validation-fbe53bf-results.zip`, 111,362,967 bytes, sha256
  `80ebdc08ba24a383265bc93bb3051a9af3a1172dc32e4187bea4e330ef3ce68b`: full-size originals of every
  capture (258), transcripts, the sanitized source maps, the tools and a sanitize manifest with each
  file's original and returned hash. Its `RETURN_RECEIPT.json` predates the owner's #6 decision.
- `calm-frames-acceptance-evidence-a672f57-2026-10-24.zip`, 12,111,203 bytes, sha256
  `bb7c423899d1671746dbb24aac79c26761d4be44c5875e7f9ebe02eba61cee34`.
- `calm-frames-integration-evidence-2026-10-24.zip`, 5,739,813 bytes, sha256
  `ac3b3e92391297ee5cbf10b6714344660a9b20b0ad4ae1d208e2509dfacc0207`.

The complete private receipt (main-household captures, recordings, raw logs, packages and the
read-only rollback) stays on the Mac.

## Hosted CI

This branch push starts no workflow: `ci.yml` and `audit.yml` run on pushes to main, pull
requests, the Monday schedule or manual dispatch. No hosted result is claimed for fbe53bf or this
branch. Local checks on this branch are listed in the commit message.
