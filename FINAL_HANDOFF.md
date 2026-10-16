# Final handoff: the integration candidate

## Dark cinema review build, October 16, 2026

Continuation at 06:09 UTC: the owner authorized an uninterrupted check window.
The simulator had stopped, so the existing device was started once and the
installed app launched without rebuilding or reinstalling. Home/Watch appeared
in logs, but external touch input immediately opened Details and playback before
the driver sent any navigation key. The driver stopped again. No new route pass
is claimed. Last observed focus was `player-seekbar`; the app was not forced
Home while another session was interacting. All 750 build inputs still match.
The receipt retains this second interruption. Coordinate all simulator users,
including other agents, before another check window.


The approved dark-cinema direction is implemented and installed on the separate
private branch `codex/dark-cinema-2026-10-16`. App source is
`d67e1daf6fab07126c7720e49772eeccf09887ee`. The prior branch remains at
`1509c1bc1270b6156e18c6b5f18af3ff835ce416`.

Home now gives the video title first priority, with a quiet brand, full-screen
coastal imagery, bright Watch, subdued Details and a horizontal rail of the
two actual videos. Card focus selects the title without playback. Details,
opening/return and player controls share the same dark palette. The
[design record](docs/evidence/dark-cinema-2026-10-16.md) explains hierarchy,
focus routes, assets and the still-image fallback. Water-only seamless motion
is outstanding; decorative moving lines were removed.

Package: `build/release/dark-cinema-2026-10-16/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `b5e62325e8270a0bc845ad09ca3fb68e1b4e03d257bbc3ece77947a5084e2467`.
All 750 recorded app inputs match. Source checks pass 132 suites, 1,318 tests,
57 textual snapshots, typecheck and lint (zero errors, 101 warnings).
No capture/export suites were run. Media, maps, trust and household settings
are unchanged. No release, public publication, main merge or AWS action occurred.

The [native receipt](results/dark-cinema-2026-10-16/receipt.json) records one
installation and passing launch/Harbor Watch/Back observations. The driver
paused after touch input outside its own remote-key sequence opened Acadia.
This is an interrupted check, not evidence of a product navigation failure.
The remaining native routes need a short exclusive simulator window. No agent
tool used touch injection, and no screenshot or recording was taken. The app
is left available for owner review, with no further automated navigation.

Minimum owner steps: review Home, move Down and Left/Right through Harbor and
Acadia, open Details and Watch, then use Back. Judge the title hierarchy,
visible focus, legibility and playback transition; listen to audio and inspect
captions if used. Allow a short untouched simulator window to finish the
remaining remote-only checks. Logs alone cannot supply visual acceptance.

## Current Watch-first build with Back repair, October 15, 2026

The corrected viewing app and nested Back repair are installed and running at
Home with Watch focused. Build source is `fcef3bb48a3dc2381b3b321f05864c8344581a3a`;
latest app change is `9afdbe5bf72170787deb5cc0d82e3aa565a87812`.
Package: `build/release/watch-back-repair-2026-10-15/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `fb77e4ca69c8d29543a336dd58e17b7b6775d617399ad9c20edb664c26f7ba8c`.
All 747 recorded app inputs match. The [repair receipt](results/watch-back-repair-2026-10-15/receipt.json)
records eight passing targeted native observations, including the exact hardware
Back route: demo > More info > Details > Home, with focus on each opening control.
Technical details Back, Watch focus and Harbor/demo playback returns also pass.
The source gate passes 131 suites, 1,314 tests and 57 snapshots; typecheck and
lint pass with 101 existing warnings. No source changed after the build.

Home leads with Watch and secondary Details. Harbor Details is only Back,
Harbor, 20 sec, Watch and More info. Acadia adds a short coastal description.
The report card, zero-findings copy and empty timeline are gone. Analysis is
under More info > Technical details; the simulated demo is secondary. Exact
before/after and remaining text are in [the copy record](docs/evidence/watch-first-2026-10-15.md).

The extra build was authorized after a native check found a nested Back defect;
the parent clarified that the earlier single-build wording was efficiency
guidance. The failing checkpoint below is preserved as history, now resolved.
No media, trust, detector, settings, PIN or volume changes. No capture was used.
Logs prove events and requested focus, not visible quality or audible continuity.
Minimum owner step: review the running Home and Details with the remote. No
further engineering or access blocker remains for this correction.


## Historical first Watch-first build, October 15, 2026

The new viewing copy is installed from `8d1bb787bb8b54b9023bee6f75baa2aac432940e`.
Home now leads with Watch. Harbor Details contains only Back, Harbor, 20 sec,
Watch and More info. Acadia adds a short content description. Reports and profile
jargon are under More info > Technical details; the simulated demo is secondary.
The zero-findings card and empty timeline are removed. Artwork, fonts, media,
trust and detection behavior are preserved. Exact before/after strings and all
remaining viewing text are in [the copy record](docs/evidence/watch-first-2026-10-15.md).

Installed package: `build/release/watch-first-2026-10-15/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `874d91690c4ae6893be9e0c2f075503c29c0c7aa394aaaa34a19f948e6b36409`.

The single requested build exposed a nested hardware Back defect after returning
from the simulated demo: Back skipped More info and returned to Home. It is
reproduced in native logs and a regression test. Source fix `9afdbe5bf72170787deb5cc0d82e3aa565a87812`
lets Details own its nested Back stack and passes the complete app suite. This
fix is newer than the installed package and needs one additional authorized
build/install. Do not claim the fixed route was tested natively. No further
redesign or architecture work is needed. See the [receipt](results/watch-first-2026-10-15/receipt.json)
for the exact native outcomes and source/build distinction. The installed
app is left running at Home with Watch focused. Harbor/Acadia playback returns,
Technical details, Help and both Parents cancellations passed by logs. The demo
Back defect remains in that installed build; use the visible Back button there
until the small tested repair is installed.


## Historical background-focus completion, October 15, 2026

App source `21f0ea60332b83efe960eb7cf799139ec2d82ae9` fixes background focus
while preserving the exact approved Acadia integration. The private working
branch remains `codex/prepared-video-slice-2026-10-15`.
Package: `build/release/transport-focus-2026-10-15/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `a39566ba190b21cbfc5523e902a37bbe00801c189c3d55c891177343d3b36507`.
The [current receipt](results/transport-focus-2026-10-15/receipt.json) records
one rebuild and installation for this fix. The app remains running at Home,
with How it works focused. No app source changed after the build.

The old Forward-button check targeted an automotive-only control. TV uses
a seek bar. Separately, Home and Details left native controls focusable behind
playback. Two regression cases reproduced that defect before the fix. The
inactive route now removes its controls while retaining its state for Back.
The current gate passes 131 suites, 1,313 tests and 57 snapshots; typecheck
and lint pass, with 101 existing warnings. The full suite includes the copy
and optional-sound regressions. Sound preference, cue asset and volume remain
unchanged; audible quality is not claimed.

All 16 current native observations pass by logs, with no blocked or
inconclusive journey. They cover core Home/Details and Parents cancellation,
Harbor to end, simulated practice and Back, Acadia identity and both cover
intervals, Help, and the corrected TV seek-bar route. After pause, Up/Down
reported no background route focus. Right then Select requested cover before
writing 12,123 ms, inside the first Extra cautious interval. Back restored
Acadia Details then its Home card. Logs do not prove visible focus or paint
ordering. The prior remote Fast Forward evidence remains dated to `0a54252`.

[Earlier positive-video recovery](docs/evidence/earlier-positive-2026-10-15.md)
reconciles the Sept 17 ledger with retained local files. All seven cover-positive
source hashes match. The Irminger case freshly reproduces its WCAG findings;
every covered decoded frame in its three retained renditions passes the numeric
still comparison. No download, new trust, media integration or private key was
needed. No independent detector or medical validation follows from this.
Claude's `3af32e4` test/spec review is now integrated as tests/docs only;
all 22 focused tests pass. The [integration receipt](results/detector-review/integration.json)
confirms unchanged detector, app inputs, maps, trust and installed package.

The [submission packet](docs/submission/README.md), readiness matrix, Devpost
draft, reviewer steps and demo script now describe this actual candidate.
AWS remains dated deployment/offline evidence; live state is unverified.
Open Source remains optional and a PR is not mandatory. Recording, publication,
reviewer invitations, main merge, release tags and AWS changes remain undone.

### Minimum owner actions

1. In the running app, review Acadia analysis, prepared playback, visible focus
   and Back. Check sound/captions and VoiceView if used. Only open prepared
   media, never the original hazardous source. Physical-TV acceptance remains open.
2. Optionally enable Selection sounds using your own existing Parents PIN,
   then listen. The agent has not changed household settings or volume.
3. Settle the Amazon sample/Shaka permission scope and artwork dedication,
   entrant/contact/registration details, and choose the judged source/package.
4. Choose and authorize reviewer access. Separately authorize demo recording,
   final video review and public upload; the script is ready, nothing is recorded.
5. If entering the optional AWS mini challenge, verify current bill, budget/tag,
   deployed digest and findings through authorized live access. If entering
   Open Source, select and authorize an eligible public contribution URL.

The remaining gaps are human acceptance, independent detector/physical-TV and
loop-seam validation, licensing/access/release choices and any live AWS review.
They are not hidden behind an all-green submission claim. Historical checkpoints
below retain their original evidence and are superseded by this section.

## Historical approved Acadia integration, October 15, 2026

App source: `0a542522642cf42d32bacf8dd41aa0f97aca62ff` on private working
branch `codex/prepared-video-slice-2026-10-15`. The owner approved the exact
Acadia bundle and public key at 21:19 UTC. Separate Harbor and Acadia catalogs
select a key only after an exact route match. Harbor stays the featured Home
title; Acadia is an additional card. Its analysis shows two distinct detected
periods, separate covered times and the settings from verified maps. The
coastal artwork is explicitly decorative, not a frame from the video.

Package: `build/release/acadia-integrated-2026-10-15/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `cad71bade96e135b6b741fec87f3fc5ee02d7d294a3be2ee61fa477169faa9a1`.
Built once from committed inputs, installed once, and left running at Home
with How it works focused. No app source changed after this build.
The [current receipt](results/acadia-native-2026-10-15/receipt.json) binds the
package, approval, source tests and native evidence. The source gate passed
131 suites, 1,310 tests and 57 snapshots; typecheck, strict delivery and the
offline hook consumer passed. Lint has zero errors and 101 existing warnings.

The initial native run reports 12 passing observations and one blocked check.
It covers Home and Details, Parents cancellation by hardware Back and button
Back, Harbor to end, both simulated practice holds and Back one level at a
time. Acadia played to the end using the exact approved source, rendition,
three maps, report and checked-input digest. Both Extra cautious cover
intervals were reported. A continuation adds four passing observations:
remote Fast Forward into each cover interval, Acadia Back navigation and
How it works return. For seek targets 12,320 and 29,832 ms, logs place the
cover request before the playhead write. This establishes JavaScript request
ordering, not compositor paint timing.

**Remaining native gap:** after pausing, the driver could not reach the
on-screen Forward button. It saw underlying Details focus IDs instead.
Remote Fast Forward worked, but does not validate that on-screen control.
The original blocked result remains in the receipt. This needs a focused
follow-up before claiming all transport controls work.

No capture was used. Collected logs contain zero touch-injection events.
Logs establish emitted events and requested focus, not rendered appearance,
actual focus rings, audio, captions or VoiceView. The offline catalog label
"cover proven drawn" is preparation evidence, not a native pixel observation.
Only the existing Extra cautious preset was exercised natively. Independent
detector validation, physical TV acceptance and the replay seam remain open.

### Minimum owner steps

1. In the running app, open the additional Acadia card, read its analysis,
   then select Play. Review text size, hierarchy and visible focus. Only the
   prepared rendition is available; do not open the original hazardous source.
2. If desired, use your existing Parents PIN to enable Selection sounds and
   listen for the quiet cue. The agent did not enter a PIN, change the saved
   preference or volume, or claim audible verification. The original local
   cue is retained and held Select/Enter repeats are suppressed.
3. Report any visible, audio, caption or VoiceView issue. The known on-screen
   Forward focus gap is engineering follow-up, not something the owner must
   diagnose. No further trust approval is needed for this exact bundle.

Claude's separate detector test/specification lane remains separate. No
production detector or prepared artifact was regenerated. The original
Claude checkouts, SDK app symlink, Harbor media, key and practice demo remain
unchanged. Earlier checkpoints below are historical, not current installed
state. The older browser comparison is retained for design learning; it is
not a preview of this prepared-video UI.

## Historical Acadia audit before approval, October 15, 2026

[Integration review](docs/evidence/acadia-integration-2026-10-15.md) records
Claude's imported artifacts, corrected reporting, offscreen frame checks and
the exact public-key approval that was required at that checkpoint. Acadia was
staged outside app assets and not yet playable. Harbor trust was unchanged.
A small held-key guard was added to the existing optional selection cue; the
saved sound setting remains unchanged. At that checkpoint these changes had not been
built or installed. The top section records the later approved integration.

## Prepared video UI reset, October 15, 2026

Latest app source: `4ba895946aabf322ed03ba7d52debbed6f5611ad` on
`codex/prepared-video-slice-2026-10-15`, based on preserved `ee76cf5`.
Home now identifies the actual selected video and initially focuses View analysis.
The analysis result appears before Play; its record separates source, rendition
and preparation report and explicitly explains pre-analysis and its limits.
Demo events are labeled simulated. A mismatched prepared file record offers
Back but no Play. Shared fonts, spacing, controls and coastal art are retained.

[Claude handoff](CLAUDE_CODE_HANDOFF.md) defines separate ownership. Claude owns
pipeline/** and tests plus docs/evidence/video-reset/** and results/video-reset/**
in a separate checkout. Codex owns app/** and final integration. No Claude session
has been confirmed started. The NPS Acadia clip is only a candidate; no new media,
key, catalog import or pipeline change was made by this UI lane.

Package: `build/release/prepared-video-slice-2026-10-15/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `74f6c2790a0407490094e834e9a2bb3129978be210d60cbe4a7166964ea926e5`.
[Current receipt](results/prepared-video-ui-2026-10-15/receipt.json) separates source,
build and native checks. The source gate passed 131 suites, 1,300 tests and 57
snapshots; lint has zero errors and 101 existing warnings. All three retained
preparation reports are present and pass the package report check.
Nine native checks reported observed-pass, including exact playback lineage.
The log contains an unassigned touch down/up near Help, so the session is not
an isolated remote-only validation. The app was left running; no replay or
capture was attempted. Pixels, sound, captions and VoiceView remain unverified.

This package plays the existing prepared Harbor with zero detected segments.
Its source-to-report-to-rendition lineage is recorded from the compiled catalog
and archived report; a fresh source import and independent detector validation
remain pipeline work. No visual or audio quality claim follows from the tests.
The older browser composition comparison is not a preview of this reset.

## Final Mac layout and copy, October 15, 2026

Both requested passes are implemented on private working branch
`codex/home-comparison-2026-10-15`. Final app source: `689c484efca088e65e76e0c7efeaf51f210c818e`.
A, the left reading area, groups the heading and Play in one scan. Home, Details,
How it works and the locked Parents gate share the ivory reading treatment;
Fraunces, Source Sans 3 and the existing dimensional coastal art remain.
B is retained as a runnable comparison, and the prior app remains at `b6b134c`.

The [copy review](docs/design/PLAIN_LANGUAGE_REVIEW.md) covers all interface
surfaces. “So the picture never holds” is now “The video plays normally.”
“Try picture holds” is “Try the demo.” Demo pauses and real hidden scenes are
named separately. Detection limits, PIN rules, distinct playback errors and
the approved safety clause remain. Home gained no extra explanatory text.

Final package: `build/release/home-reading-a-plain-copy-2026-10-15/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256: `8163aee15b6062a085b79c225994ed199b85ae3c253be1dc978c4d668c72595f`.
The [final receipt](results/plain-language-2026-10-15/receipt.json) records build,
tests and native status separately. Its preparation record binds 736 inputs to
committed source. All seven final-package native journeys passed by logs:
Home launch; Details and return; Parents hardware Back and button Back after
Details; Harbor to end; both demo pauses and the three Back steps; help return.
The app is left running. No native visual or audio claim is made.
Typecheck, 130 app suites, 1,292 tests, 57 snapshots, ten hook package tests and
the offline hook consumer pass. Four existing tests are skipped and three
capture/export suites excluded. Lint has zero errors, 97 existing source warnings
and four test warnings. The earlier four-warning summary is corrected.

Open <http://127.0.0.1:4186/docs/design/home-comparison/> or
[the HTML](docs/design/home-comparison/index.html). Start in grayscale, then
switch color on. If needed, run `python3 -m http.server 4186 --bind 127.0.0.1`
from `/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-review`.
The browser is a route simulation; it does not play media or collect a PIN.

Owner's minimum steps: inspect text wrapping and focus from the usual TV seat;
listen through Harbor and the demo and inspect captions; enter the existing PIN
personally to check settings. Test VoiceView if available. Logs cannot do these.
Resolve sample notice scope and artwork permissions before distribution. No
capture, public publication, main merge, release tag, AWS cost or credential
change occurred. The original Claude checkout and SDK app link were preserved.

## Earlier Mac layout-only checkpoint, October 15, 2026

This layout-only checkpoint is superseded above. Working branch: `codex/home-comparison-2026-10-15`.
Implemented app source: `69df28c8215920ae5a1cc8e82a3124d4a68d65b3`, based on
`b6b134c` and retaining the `0e434dc` Parents return-focus fix. The owner delegated
the final layout decision and immediate implementation after the comparison was
prepared. A, the left reading area, was chosen because its heading and Play form
a short, clear scan. Home, Details, How it works and the locked Parents gate now
share that reading treatment; routes and playback behavior are unchanged.

Both compositions remain runnable at
<http://127.0.0.1:4186/docs/design/home-comparison/> or by opening
[the local HTML](docs/design/home-comparison/index.html). Start in grayscale,
then switch to the approved colors. The study uses the same coastal image,
Fraunces and Source Sans 3. B remains a browser proposal. The prior native
design is preserved at `b6b134c`; no reset of an existing checkout was used.

The final package is
`build/release/home-reading-a-2026-10-15/calm-frames-0.1.0-aarch64-debug.vpkg`
in `/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-review`.
SHA-256: `a09eff79ad8466a1ae8d5da81383458b0bf70a6a176b84e98e6faa820500922a`.
Its [preparation receipt](results/home-review-2026-10-15/selected-preparation.json)
binds 736 inputs to the committed source. It is build evidence, not runtime evidence.
The [Mac review receipt](results/home-review-2026-10-15/receipt.json) is the source
of truth for the separate native observations and remaining checks.

The app gate passed 130 suites, 1,292 tests and 57 snapshots. Four pre-existing
tests remain skipped; the three capture/export suites were excluded. Typecheck
passed and lint reported zero errors with 97 source and four test warnings, on Node 22.23.2.
Browser DOM checks passed both route simulations, local fonts, color switching
and large-view frame bounds without screenshots. Native logs can establish
reported focus IDs, route transitions, media events and still-load callbacks.
They cannot establish pixels, readable focus rings, sound continuity, caption
appearance, VoiceView or the PIN-protected settings interior.

Minimum owner steps: inspect the final app by sight and sound, check captions
and visible focus, and enter the existing PIN personally to inspect settings.
No further layout choice blocks implementation. Before distribution, resolve
the sample-license notice scope and artwork permissions; notices were kept.
Recording, reviewer access, public contribution, submission and release selection
remain separate owner actions. No capture, main merge, release tag, AWS deployment,
cost or credential change was performed. Private working-branch delivery is authorized.

The official Open Source mini-challenge rule allows a public fork or branch
contribution without opening or merging a PR. Private patch files alone do not
qualify. The packet now reflects that distinction; nothing was published upstream.

The sections below are dated history and do not replace this checkpoint.


## Cloud continuation, October 15, 2026

Current private working branch: `codex/cloud-finish-2026-10-15`.
Application source: `0e434dc7c89b7fb2dc19a9ca5d4593e5effa6c19`, based on
candidate `a3368a9e` plus the 13-file documentation reconciliation `85dedefd`.
The older package and device sections below remain historical evidence.

The PIN-gate cancel focus defect is fixed in source: both button Back and
remote Back now return focus only to Parents, including after visiting Details.
The regression failed twice on the old behavior and passes with the fix.
The final app gate passed 130 suites, 1,292 tests and 57 snapshots; four existing
tests remain skipped and the three capture/export suites were excluded.
Typecheck and lint passed. Checks used the supplied Node 24, not pinned Node 22.
Exact commands and limits: [cloud finish receipt](results/cloud-finish-2026-10-15.json).

The upstream wrapper/teardown tests now execute with eight passes and three
expected-failing negative controls. Both original patches remain required;
a third patch adds the tests. The broader upstream baseline and patched run
both exit 1 for the same two obsolete snapshots. The duplicate-issue recheck
was blocked by GitHub API `Forbidden`. See [upstream evidence](docs/upstream-pr/README.md).

Offline AWS checks passed: 100 tests, synthesis and image context. Live billing,
tags, credits, deployed image digest and findings are blocked by absent AWS
access. The [bounded owner checklist](docs/research/cloud-aws-check-2026-10-15.md)
keeps the historical inactive tag, inconclusive zero-dollar reading and
8 critical/56 high image findings unresolved. The TV still uses its packaged
library, not the cloud demo signer.

No Vega CLI/SDK is available here. No Mac was accessed, no native package was
rebuilt, and no screenshot or recording was made. Package 5 does not contain
this focus fix; rebuild from the new source and repeat acceptance before
claiming it does. Pixels, audio, parent-settings interior, VoiceView and
caption-menu contents remain unobserved. No main merge, release tag, upstream
publication, reviewer invitation or submission occurred.


Written Oct 14, 2026, night (Pacific), after remote-driven acceptance sessions
on the Vega Virtual Device, and reconciled Oct 15 against candidate head
`a3368a9e4dbfde52153d586d97d8c6da5ab5c8fd` and package 5 from `4016e8d`.
The candidate is committed and pushed to
`origin/claude/final-candidate-2026-10-14` (no main merge, no pull request,
no visibility change); nothing from this candidate is published, recorded or
submitted. Packages 3, 4 and 5 were installed and driven on the simulator
without any screenshot, video or capture. This reconciliation reads the saved
receipts; it does not add a native run.

## 1. Branch, commit and package

| What | Value |
|---|---|
| Branch | `claude/final-candidate-2026-10-14`, worktree `/Users/alexvintera/calm-frames-claude-final-2026-10-14` |
| Package source commit | `4016e8dac8f675a4eb1e1613fd9dc7cf63d06e58` (`4016e8d`), the last commit that changes an app input: the one-voice copy on every screen, on top of `819de40` (the simplified Home, the practice entry on Details, the bordered icon); the commits after it are renders and this documentation |
| Package | `build/release/final-candidate-5-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg`, aarch64 Debug, 28,733,262 bytes (build output outside git, in the worktree above) |
| Package SHA-256 | `a226b39fc855cd7cf5eb4136b9ba890f92e6e6518ca764a6862cf9990870dc13` |
| Receipt | `build/release/final-candidate-5-2026-10-14/PREPARATION.json`: 736 recorded app inputs with hashes, inputs committed, prepared library checked with all 3 original reports present, catalog SHA-256 `02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79`; `SHA256SUMS` and `NOTES.md` beside it. The helper writes `native_validation_performed: false`; the sessions in section 3 are the validation |
| Tested on the device | This exact package, installed over the existing household with `vega device install-app`; no uninstall, no data reset, no PIN entered. Receipt: [`results/native-acceptance-5-2026-10-14/receipt.json`](results/native-acceptance-5-2026-10-14/receipt.json). Package 4's two sessions: [`results/native-acceptance-4-2026-10-14/receipt.json`](results/native-acceptance-4-2026-10-14/receipt.json) and [`second-pass.json`](results/native-acceptance-4-2026-10-14/second-pass.json); package 3's: [`results/native-acceptance-2026-10-14/receipt.json`](results/native-acceptance-2026-10-14/receipt.json) |
| Source comparison | The GitHub comparison from package 5's source `4016e8d` to candidate head `a3368a9e` changes documentation, browser renders and their receipt, and the package 5 acceptance receipt; no `app/` file changes. This is a source comparison, not a fresh hash check of the local package or its 736 recorded inputs. Package 4 remains earlier evidence from `819de40` |
| Earlier build route (package 3) | `source ~/vega/env`, fnm Node 22 and the watchman fallback shim on `PATH`, `JAVA_HOME=/opt/homebrew/opt/openjdk@21`, `DEMO_PIN` unset, then `RELEASE_PYTHON=/Users/alexvintera/calm-frames/.venv/bin/python bash scripts/release.sh --arch aarch64 --build-type Debug --tag final-candidate-3-2026-10-14`. The helper printed its publication command and it was not run |
| Earlier packages, preserved | `final-candidate-4-2026-10-14` from `819de40` (`471770fb…`, driven twice on the device), `final-candidate-3-2026-10-14` from `ac5a610` (`4d36c177…`, driven once), `final-candidate-2026-10-14` from `93cf800` (`d53444ab…`) and `final-candidate-2-2026-10-14` from `52138fe`; Codex's `approved-coastal-b22d275-2026-10-14` in the coastal worktree |
| Lineage | `cfddc4a` (reliability) → `b22d275` (Codex: approved coastal interface) → the submission packet and the illustrated harbor ledger → `58bd1a7` (coastal artwork ledgered, credits regenerated) → `53ab01b` (hook mirror) → `93cf800` (coastal menus held to the ten foot floors) → `204f185` (debug breadcrumbs) → `487e5e5` (Back one level at a time in setup, the picker and the removal question) → `52138fe` (bundled copies of the practice stills) → `69390ed` (README opens on the coast) → `ac5a610` (opening readies on a moving clock) → `d7e13be` (documented checks runnable from a fresh checkout) → the judge-path fixes and this documentation → `819de40` (the simplified Home, the practice entry on Details, the bordered icon and tile) → `111ff12` (friction log 41 to 43, renders) → this documentation → `4016e8d` (one voice for the words) → this documentation |
| Earlier local previews (recorded at `819de40`) | Static component export: <http://127.0.0.1:4176/> (served from `build/coastal-preview` in this worktree, pid in `.logs/final/preview-4176.pid`; regenerate with `cd app && npx jest --ci --watchman=false --coverage=false test/calmframes/coastalExport.test.tsx && cd .. && .venv/bin/python eval/preview/coastal_preview.py`). <http://127.0.0.1:4174/> is Codex's older export served from its own directory and <http://127.0.0.1:4175/> its water study; both left running. Browser previews, not device captures |

## 2. What changed, and the checks

**One voice for the words (`4016e8d`, later on Oct 14):** Alex found the
wording incohesive and padded. A picture hold is now the mechanism on every
screen: the cards ("Picture hold coming up", "Holding the picture", "Held the
picture for 4 seconds"), the timeline key, the parent area's record ("Picture
holds", "3 holds, 12 seconds in all"), the room and profile rules, the chime
row, the presets and the first run explainer; "the picture stays hidden" is
the one phrase for a video that may not play; "video" is the word for content.
Buttons say what they open: How it works and Parents in the Home header, Back,
Play demo, Before you watch. Details says the check's result once in the hero
("20 sec · No flashing found", "Checked frame by frame. No flashing found, so
the picture never holds.") and Before you watch carries only the limit of
detection, the timeline, the settings and the approved sentence; How it works
is four lines beginning with who the app is for. The full app suite passes
on it (133 suites, 1310 tests), typecheck and lint are clean, the hook mirror
is re-synced, and the browser renders are regenerated from it. The label
table is in `docs/design/COPY_GUIDE.md`.

**Simplified at Alex's request (`819de40`, late Oct 14):** Home is one heading,
"Calm Frames", at 120 units on one line (measured: 755 units wide in the
display face, clear of the island; 184 would run under the lighthouse), with
Play and Details under it and How it works and Parents in the header, and
nothing else: the smaller wordmark, the "20 sec · No picture holds" line, the
explanation sentence, the Try picture holds card and the notice about titles
held back are gone from Home. Play still speaks "Play: Harbor" and Details
"Details: Harbor". Details keeps the title at 184 with its facts and offers
the practice demo beside Play as a quiet Try picture holds entry that opens
the demo's own page; Back returns one level at a time, to the page that
opened it with focus on that entry, then to Home with focus on Details. The
launcher icon and the Fire TV tile carry the warm-sand inset border Alex
asked for. The browser renders were regenerated from this commit, then refreshed from
`4016e8d` for the one-voice copy.

**Integrated from the approved design (`b22d275`, Codex):** the ivory coast on
every menu screen with the dimensional coastal artwork, the expressive Harbor
title, the tactile Play button, the quiet Details action, the compact Try
picture holds entry, Help and Settings in the header (since renamed How it works and Parents), and dark playback
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

**Checks on `819de40`:** typecheck; ESLint on the changed files; the 18 Jest
suites that touch Home, Details, the route, return focus, hardware Back, the
ten foot pass, the frame inventory and the export (242 tests); ruff; the style
check; the published number check; the design page, brand asset, attribution,
measured-source and doc link tests; the brand flash check on all thirteen
images; the full app suite, recorded below in this section's last paragraph.

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

**The full app suite on `819de40`,** in this worktree after the Home patch:
133 suites passed and 1 skipped, 1310 tests passed and 4 skipped.

**The local equivalent of the hosted gate, late Oct 14,** on the candidate
with the documentation on top: the Python suites (`pytest flashmap pipeline
eval -m "not slow"`: 1801 passed, 2 deselected), ruff over the repository,
the pin check (51 pinned, 0 loose), the conformance report rebuilt byte for
byte, the hook package tests and the packed consumer check, the standalone
eval tests (957 passed), the committed-tree secret scan (clean after the
`unknown-key.png` allowlist, `f47ecd9`), the style check, the published number
check and the document link test. Not run locally: strict mypy, which the
local environment lacks; the hosted Python job runs it.

## 3. Native acceptance, as observed

Method: the Debug package's own breadcrumbs and media events, read from
`vega device start-log-stream` while a driver pressed remote keys through the
device's `inputd-cli`. No pixels were seen and no audio was heard; "pass" means
the app reported the journey happening. Details and the open items are in the
receipts.

### Package 5 (`4016e8d`, one voice for the words), later on Oct 14

Receipt: `results/native-acceptance-5-2026-10-14/receipt.json`, the same
driver and the same running device as package 4's sessions; the focus ids it
steers by did not change with the words.

| Journey | Result | What the app reported |
|---|---|---|
| J1 cold launch reaches Home with Play focused | observed-pass | first screen=[] first focus=['kid-mode-home-watch'] now screen=None focus=kid-mode-home-watch running=True touch events injected on the device after launch=0 |
| J2 remote reaches Home controls and nothing removed takes focus | observed-pass | focus ids seen=['kid-mode-home-choose-profile', 'kid-mode-home-learn', 'kid-mode-home-more-info', 'kid-mode-home-parent-area', 'kid-mode-home-watch'] unexpected=[] removed seen=[] |
| J3 Details opens on Play, Try picture holds sits beside it, Back restores focus to Details | observed-pass | reached=True screen=details focus=kid-mode-details-play right of Play=kid-mode-details-practice after Back screen=home focus=kid-mode-home-more-info |
| J4 Home to Play: ordinary Harbor plays to the end with zero holds | observed-pass | playing=True ended=True interval covers=0 recovery screen=False after Back screen=player-left', focus=kid-mode-home-watch |
| J5 Details to practice: the demo page, both holds with the calm still, Back one level at a time | observed-pass (the driver said observed-partial; see below) | reached practice entry=True demo page screen=details focus=kid-mode-details-play covers=['cover-on media=5034 interval 5000-9000', 'cover-on media=12007 interval 12000-16000'] stills=['still loaded', 'still loaded', 'still loaded', 'still loaded'] recovery=False Back1=("player-left',", 'kid-mode-details-practice') Back2=('home', 'kid-mode-home-more-info') Back3=('home', 'kid-mode-home-more-info') |
| J6 Help opens and Back returns to Help | observed-pass | reached Help=True focus in Help=picture-hold-start after Back screen=home focus=kid-mode-home-learn |
| J7 Settings opens its PIN gate and Back returns to Home | observed-pass | reached Settings=True screen=parent focus=kid-mode-parent-key-1 after Back screen=home focus=kid-mode-home-more-info; interior blocked: needs the household PIN |
| J8 relaunch lands on the saved Home, no setup | observed-pass | screen=home focus=kid-mode-home-watch running=True touches in session=0 |

Where a verdict reads "the driver said": the cold launch wanted the "screen
home" breadcrumb as well as the focus breadcrumb, and the device's log limiter
dropped the screen line (friction log entry 12); the first focus after launch
was Play on Home with the app running, which is what the first session judged
by. Pause and resume, the remote seek and the caption control were observed on
package 4 (its second pass); they were not repeated in package 5's receipt.
Those earlier observations do not establish package 5's pixels or audio.

### 3a. Package 4 (`819de40`, the simplified Home), late Oct 14

Receipt: `results/native-acceptance-4-2026-10-14/receipt.json`. The virtual
device had frozen earlier in the evening (no log lines and no disk writes for
hours while its status said running) and was stopped and started again; its
user data persisted, so the household and the installed app were kept. A
first attempt at this session saw a touch injected on the device five seconds
after the cold launch, on the Details control; the driver sends only remote
keys, so that touch came from the simulator window on the Mac. The attempt
was discarded and the run below saw no touch.

| Journey | Result | What the app reported |
|---|---|---|
| J1 cold launch reaches Home with Play focused | observed-pass | first screen=['home'] first focus=['kid-mode-home-watch'] now screen=home focus=kid-mode-home-watch running=True touch events injected on the device after launch=0 |
| J2 remote reaches Home controls and nothing removed takes focus | observed-pass | focus ids seen=['kid-mode-home-choose-profile', 'kid-mode-home-learn', 'kid-mode-home-more-info', 'kid-mode-home-parent-area', 'kid-mode-home-watch'] unexpected=[] removed seen=[] |
| J3 Details opens on Play, Try picture holds sits beside it, Back restores focus to Details | observed-pass | reached=True screen=details focus=kid-mode-details-play right of Play=kid-mode-details-practice after Back screen=home focus=kid-mode-home-more-info |
| J4 Home to Play: ordinary Harbor plays to the end with zero holds | observed-pass | playing=True ended=True interval covers=0 recovery screen=False after Back screen=player-left', focus=kid-mode-home-watch |
| J5 Details to practice: the demo page, both holds with the calm still, Back one level at a time | observed-pass (the driver said observed-partial; see below) | reached practice entry=True demo page screen=details focus=kid-mode-details-play covers=['cover-on media=5022 interval 5000-9000', 'cover-on media=12028 interval 12000-16000'] stills=['still loaded', 'still loaded', 'still loaded', 'still loaded'] recovery=False Back1=("player-left',", 'kid-mode-details-practice') Back2=('home', 'kid-mode-home-more-info') Back3=('home', 'kid-mode-home-more-info') |
| J6 Help opens and Back returns to Help | observed-pass | reached Help=True focus in Help=picture-hold-start after Back screen=home focus=kid-mode-home-learn |
| J7 Settings opens its PIN gate and Back returns to Home | observed-pass | reached Settings=True screen=parent focus=kid-mode-parent-key-1 after Back screen=home focus=kid-mode-home-more-info; interior blocked: needs the household PIN |
| J8 relaunch lands on the saved Home, no setup | observed-pass | screen=home focus=kid-mode-home-watch running=True touches in session=0 |

The practice journey is read as a pass against the log: when the film ended
at 19999 ms the player left on its own and the demo page came back with Play
focused; the driver's first Back then landed on Harbor's Details with focus on
Try picture holds and its second on Home with focus on Details, which is the
designed route. The driver had budgeted one more Back to leave the player and
reported partial. The ordinary Harbor journey ended the same way, onto Home
with focus on Play. Not observed in that first pass: pause and resume, seeking by remote and
the caption control, which the second pass below covers; still unobserved on
any package: the caption menu's contents, the parent settings interior
(household PIN), pixels, audio and VoiceView.

### 3a, second pass: pause and resume, the remote seek, the caption control

Receipt: `results/native-acceptance-4-2026-10-14/second-pass.json`, the same
package and the same running device.

| Journey | Result | What the app reported |
|---|---|---|
| J9 pause, resume and Back from playback | observed-pass | playing=True pause=True resume=True left=True screen=player-left', focus=kid-mode-home-watch |
| J10 seek back into a hold by remote (Left, then Select on the seek bar) | observed-partial | second hold ended=True seek events=[] covers after seek=['cover-on media=19999 pause'] pauses=['pause media=19999'] plays=[] order=['ended@19999', 'cover-on@19999 pause', 'pause@19999'] screen now=player', focus=kid-mode-details-back |
| J11 caption control reached by remote during playback | observed-pass (the driver said observed-partial; see below) | focus after two Down=video-player-caption-btn caption lines=['2aa2e18 local0.info io.github.alejandropublius.calmframes[12167]: 546981343520 INFO com.amazon.keplerscript: [KeplerScript-JavaScript] render KeplerCaptionsView', '2aa2e18 local0.info io.github.alejandropublius.calmframes[12167]: 546981343520 INFO com.amazon.keplerscript: [KeplerScript-JavaScript] render KeplerCaptionsView', '2aa2e18 local0.info io.gith... |
| J12 app still on Home at the end | observed-pass | screen=player-left', focus=kid-mode-home-watch touches in session=0 |
| J10b seek back into the first hold by remote (Down, Left, Select) | observed-pass | hold 2 seen=True hold 2 ended=True seek events=['seeking@6788', 'seeked@6812'] covers after Left/Select=['cover-on@17502 pause'] order=['cover-on@17502 pause', 'pause@17502', 'seeking@6788', 'playing@6788', 'seeked@6812', 'waiting@6812', 'playing@6967', 'cover-off@9050 clear'] screen now=player', focus=calm-card-skip |
| J12b app on Home at the end | observed-pass | screen=home focus=kid-mode-home-more-info touches in session=0 |

The first seek attempt (J10) began its slide after the second hold ended at
16 s and its Select arrived after the 20 s film had ended, so nothing was
requested; it was too late, not refused. The retry (J10b) brought the controls
up with Down during the second hold, slid back with Left after it (the slide
pauses, and the player covered the picture at 17.5 s for that pause), and
confirmed with Select: the seek went to 6.8 s, inside the first hold, with the
cover already on, playback resumed under the cover, and the cover cleared at
9.05 s when the hold ended. That is the cover-first seek the tests promise,
seen by remote. J11 is read as a pass for what it checked: two Down presses
during playback put focus on the caption button and Select was accepted; the
menu's contents are not visible from the log.

### 3b. Package 3 (`ac5a610`), the first Oct 14 session

Receipt: `results/native-acceptance-2026-10-14/receipt.json`. The Home of that
package still carried the practice card, which is why its journeys name it.

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
(household PIN); VoiceView; any physical television. **The loader error,
explained:** the package 4 session shows one `LocalAssetImageLoader: Cannot
load image from non local source:` line a few milliseconds before every
packaged image reports loading: the scene on Home and on Details, the two
pictures of the opening shell, and each bundled still at the holds. Every one
of those images then loads. The device's loader evidently tries a non-local
source first for a packaged asset and logs the miss; it is noise, not a
defect, and friction log entry 44 records it. The data URI case (entry 41) is
different: those never loaded.

## 4. Native acceptance checklist for the owner (eyes and ears)

Install the package in section 1 with the commands in
[`docs/submission/REVIEWER_QUICKSTART.md`](docs/submission/REVIEWER_QUICKSTART.md)
section 3 and confirm by looking and listening:

1. Home: the coastal artwork fills the screen; one heading, "Calm Frames",
   Play with a triangle and Details under it; How it works and Parents in the header;
   no title line, explanation, demo card or notice; text readable from the
   couch; focus rings visible on every control, terracotta on a focused Play.
   The launcher tile shows the bust mark with its thin sand border.
2. Details: "Harbor" with "20 sec · No flashing found", Play, and Try picture
   holds beside it. Try picture holds opens the demo's page ("20 sec · 2
   practice holds"); Play there: the countdown and Skip, then at each hold the
   calm still (not black) with the "Holding the picture" card, captions
   changing, sound continuing without a gap. Back returns to the demo's page,
   then to Harbor's Details with focus on Try picture holds, then Home.
3. Harbor: plays through, sound audible, no hold, no error screen.
4. Playback controls: dark and readable over the video; pause shows a readable
   paused state after the controls hide; Back returns to the launching screen.
5. Parents: Alex enters the existing household PIN himself. Check that a wrong
   PIN is refused with tries remaining, Delete corrects, the right PIN opens
   presets, room, chime, motion and sounds, and a changed preset survives a
   relaunch. Check Back from the PIN gate too: package 5 reported Home with
   Details focused, not Parents, so return focus to the opening control remains
   an owner check.
6. How it works reads correctly in four short lines; the home scene's reading
   edge fades the artwork behind the text.
7. VoiceView, if available, names controls by their accessible names.

Record what was seen and heard in a new `results/` receipt with the package
hash. Do not reset household data.

## 5. Remaining owner actions, by submission impact

1. Run the checklist in section 4 and decide whether package 5 from `4016e8d`,
   with its candidate documentation, becomes the judged release. Choose the
   exact commit or release reference judges will use. Merging to `main` and
   cutting a tag are release choices, not stated hackathon requirements.
   The branch is on origin already; opening a draft pull request from
   `claude/final-candidate-2026-10-14` would run the hosted CI and Audit
   workflows. If authorized, this command opens it with the handoff as its body:

   ```sh
   gh pr create --draft --base main --head claude/final-candidate-2026-10-14 \
     --title "Calm Frames: the coastal interface, the simplified Home and the Oct 14 device fixes" \
     --body-file FINAL_HANDOFF.md
   ```

   Draft PR #1 from the shared branch stays as it is; this candidate contains
   everything that branch holds.
2. Authorize and make the recording from
   [`docs/submission/DEMO_SCRIPT.md`](docs/submission/DEMO_SCRIPT.md), assemble
   and check it, upload to YouTube or Vimeo, and check the link logged out.
3. Choose reviewer access: public (licence visible in About, audit exception
   dates, private vulnerability reporting, item 5) or private with
   `testing@devpost.com` and the six Amazon reviewers invited at submission.
   Fill in the About box either way.
4. Confirm eligibility, the contact email and the Devpost registration.
5. Settle the licence items: the Amazon sample's conflicting notices (still
   unresolved; clarification unsent), the CC0 confirmation for the generated
   Harbor artwork, and the position on the generated coastal artwork, which the
   ledger records without any ownership claim.
6. Optional: the Open Source entry needs a public qualifying contribution URL,
   such as the prepared change in a public fork or branch under your account;
   opening or merging a PR is not required (`docs/upstream-pr/`, steps in
   `docs/OPEN_SOURCE_PR.md`); the private repository on its own does not
   establish it. The AWS Builder entry is possible with the deployed stack
   (`docs/SUBMISSION.md` section 10.2). The cost allocation tag was recorded
   inactive on Oct 9; its current state and billing coverage are unverified; the overview also says building with Kiro Crew qualifies on its
   own, which this project did not use.
7. Approve the friction log (44 entries) and product feedback for publication
   as written. An Amazon organizer confirmed on the Devpost forum that a link
   in the description is enough and that keeping the log in the repository is
   easiest for judges; the description draft carries that link.

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
repository is private today and GitHub detects Apache License 2.0. The
candidate branch is on origin; the CI and Audit workflows trigger on pull
requests, so no hosted run exists for it until a pull request is opened. The
local equivalent of the CI gate was run on the candidate late on Oct 14 (the
app suite, the Python suites, ruff, the hook package, the pin check, the
conformance rebuild and the committed-tree secret scan; strict mypy was not
run in that late local gate, as section 2 records); the scan had reported
four false findings since Oct 13, hashes of renders named `unknown-key.png`,
which is why the hosted CI run on the shared branch was red, and a narrow
allowlist now excuses exactly that line shape. Unresolved:
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
from a fresh checkout; the Home simplified as Alex asked, the practice demo
reached from Details, the icon and tile bordered; a package built from the
committed source with its receipt and driven on the device; friction log
entries 41 to 43; the candidate branch on origin; the submission packet and
this handoff.

**Optional, not started:** the caption button for a title without tracks
opens a menu that lists only Off (it is announced as "Captions unavailable");
a bundled-still path for prepared titles beyond the practice demo; visual
confirmation of the cover-first remote seek (observed by log on package 4);
the gradient loader message; the Open Source
and AWS Builder entries; a changelog section for the judged tag, written when
the tag exists.
