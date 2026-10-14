# Morning handoff: the current Calm Frames candidate

Updated October 14, 2026. This is the operational handoff for this integration.
It supersedes older next-action instructions in STATUS, MAC_FINISH,
COMPLETION_CHECKLIST, CLAUDE_FINISH_PROMPT and earlier demo plans. Historical
receipts remain valid only for their recorded source and package.

## Use this candidate

| Item | Current value |
|---|---|
| Branch | `codex/design-integration-2026-10-14` |
| Runtime source | `cce5f22ccdc07fb5c9022d7ed9d0963b9df98a5b` |
| Checked evidence | `d38793a4bc04d71b8a9ee5c6f7013cce79ae1077` |
| Local checkout | `/Users/alexvintera/Documents/Codex/2026-10-13/task/calm-frames-home` |
| Package | `build/release/design-loading-integrated-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg` |
| Target | aarch64 Debug |
| SHA-256 | `9c7381f7e3033eb5e57cd6b47dca556ca93a969a595612c4314c1b3daf753627` |

The [current receipt](../results/loading-integration-2026-10-14/receipt.json)
and [complete package provenance](../results/loading-integration-2026-10-14/preparation.json)
identify the same source. Documentation-only commits after this source do not
require a rebuild. Earlier package directories are historical and preserved;
do not install an older candidate or the mutable `app/build` output by mistake.

The dedicated Claude loading component from `fa766f3` is integrated with
opening/return/error suppression. No separate loading merge is pending. The
disabled picture-break prototype and unrelated Claude commits remain excluded.
Do not merge that prototype, main, or the shared branch as a finishing step.
Keep work on this integration branch and preserve other worktrees.

## What is checked

- Library-first Harbor design, optional How it works/demo, destination-neutral
  Back copy, caption defaults and seekbar focus propagation have software tests.
- Opening and return shells cancel hidden Loading announcements. In-play stalls
  retain truthful static feedback without scene dimming. Signed stills, Skip,
  error recovery and the verification guard have regression coverage.
- Exact-source full app run: **1254 passed, 4 skipped; 57 snapshots passed**.
  Command: `npm --prefix app test -- --runInBand --coverage=false --watchman=false`.
  [Full log](../results/loading-integration-2026-10-14/loading-corrected-full-app.txt).
- Typecheck passes; focused loading lint has no errors or warnings. The early
  bootstrap file retains one pre-existing `no-void` warning at line 82.
  [Typecheck](../results/loading-integration-2026-10-14/loading-corrected-typecheck.txt),
  [lint limitation](../results/loading-integration-2026-10-14/loading-bootstrap-lint-existing.txt).
- The 21 design checks and packaged-library/identity checks pass. The existing
  36-state solid-surface timeline passes WCAG and broadcast analysis. Its
  timeline does not exercise the new loading plate's timed appearance; that
  plate has separate rendered-tree and timing tests. None of these are native
  pixel or motion proof. [Check scope](../results/loading-integration-2026-10-14/receipt.json).

The current visual review uses these actual React Native host-tree browser
renders, unchanged by the subsequent loading-component integration:
[home](../results/design-integration-review-2026-10-14/home-browser.png),
[How it works](../results/design-integration-review-2026-10-14/how-it-works-browser.png),
[household loading](../results/design-integration-review-2026-10-14/loading-browser.png),
[playback opening](../results/design-integration-review-2026-10-14/opening-browser.png).
They are not Vega screenshots. Prior native captures do not validate this source.

## Two separate access issues

**Mac lock:** Computer Use app inventory reported that the Mac was locked and
automatic unlock failed. The current candidate has not been installed or
launched. The user must manually unlock macOS before native UI validation can
resume. Do not retry automatic unlock, bypass the lock, or operate Terminal UI.

**Forgotten parental PIN:** unlocking macOS does not unlock parental controls.
The existing household PIN was not retrieved, guessed or reset. The app has no
Forgot PIN recovery flow; its local gate is described in
[parentGate.ts](../app/src/calmframes/parentGate.ts). Parent settings and their
persistence remain unverified for this candidate until the user can legitimately
unlock them. Continue the public library/playback checks independently. Do not
ask for the PIN in chat, mine stored data, uninstall, clear data, or create a
replacement household. No recovery feature or reset is authorized here.

## One native session after manual Mac unlock

Use the [machine-readable demo plan](../results/loading-integration-2026-10-14/demo-plan.json)
for the exact preflight/install/launch commands. Verify the package SHA-256
above before installation. Update the existing app once, retaining its data,
and keep the session open. If the simulator is unavailable, record that state
before deciding on a new start; do not repeatedly foreground or relaunch it.

1. Observe home, optional How it works, Back and Try the demo. Capture the
   opening transition, moving Harbor film, scheduled holds, countdown Skip and
   return focus. Use actual D-pad input where available.
2. Watch ordinary Harbor from home, then from More info/details. Observe loading,
   first picture, Back to the retained caller and focus restoration.
3. Pause past six seconds with controls hidden, resume, and select optional
   captions. Capture a hold with controls or caption menu. The shipped cues are
   single-line; the earlier multiline fixture is separate historical evidence,
   not proof for this package. Record that limitation instead of changing VTT.
4. Observe post-opening buffering and recoverable errors if they occur through
   an available non-destructive path. Confirm no competing Loading announcement
   during opening/return or errors. VoiceView has both an explicit announcement
   and a polite live region: verify it says Loading only once and never speaks
   a queued Loading after an error. Signed-hold tests mock guard state, so verify
   actual stall continuity or the appropriate black-cover fallback. Do not claim
   live continuity from those tests or induce failure by altering signed media.
5. Test still/reduced motion and VoiceView only where legitimately accessible.
   A parental PIN or unexpected OS permission blocks that check, not the other
   journey. Report the exact action needed; leave settings/data unchanged.

Native first-frame composition, moving ripple behavior, timing, D-pad behavior,
VoiceView and simultaneous overlay layout are **not verified on this source**.
The SDK frame counter is a readiness signal, not observation of displayed
pixels. If a material native defect requires another launch, finish related
code fixes first and report why before another consolidated run.

## Judging evidence and release blockers

The repository's actual saved criteria are in [RUBRIC.md](RUBRIC.md):
[Fire TV runtime/demo requirements](RUBRIC.md#22-the-runtime-technology-hook-and-why-fire-tv-is-exempt)
and [the four criteria](RUBRIC.md#3-stage-two-the-four-criteria): Tech
Implementation, Design, Potential Impact and Quality of the Idea. This evidence
records a September 17 read and October 1 repository-access recheck. It was not
re-researched in this handoff and must not be presented as a fresh rules check.
[The October 2 assessment](../results/hackathon_review_2026-10-02.json) is explicitly
subjective, not an official score, eligibility decision or prediction of winning.

Independent review accepts `cce5f22` pending native evidence, with no concrete
source blocker. It independently confirmed the 63 focused tests and final
1254 passes, four skips and 57 snapshots. No new loading pixels or timing have
been observed.

Remaining blockers are the current native session and matching recording;
parent-settings observations blocked separately by the forgotten PIN; and later
release review of the
[existing licence question](AMAZON_SAMPLE_LICENSE_REVIEW.md),
[security findings](SECURITY.md), entrant/reviewer access and final demo links.
The rules and external sources need their scheduled pre-submission recheck in
that later approved task. No new research, audit or backend work was done here.

Draft/submission material stays private. Publication, visibility changes,
deployment, merging shared/main and submission are not authorized by this
handoff. A built package or passing suite is not a submitted entry or medical
validation. Preserve the source, package and recording identities in any later
review; do not substitute earlier native evidence.
