# Bounded final clarity pass, October 18, 2026

This pass follows the completed delivery integration at `6125459` / documentation
`be94cde`. It closes one wording gap and records submission corrections. Feature scope
remains frozen.

## Changed

The existing How it works explanation, reachable from Home, and Details → More info
now say:

> Calm Frames works only with prepared videos in this app, not other apps or live TV.

> Detection can miss flashing. This prototype has not been medically validated.

The approved safety sentence immediately following remains unchanged. The change reuses
existing text blocks and shared copy; Home gets no warning panel or new controls.
It changes no layout tokens, playback behavior, catalog, assets, detector, trust or settings.
An existing copy test was updated for the clarified scope and shared house-style checks.

Prepared on isolated branch `codex/final-clarity-2026-10-18`, source `5ba252b`, then integrated
onto `claude/tv-experience-2026-10-16` as **`9cc57ca04077611c9bf535ce5083b23c83c7bb4a`**.

## Already done; no change needed

- `App.tsx` renders `HarborOpening` while the store initializes; the initial lazy Home
  route uses the same component. Both actual callers omit `onFinish`, so the component
  renders its static scene/header/status branch without animation or an artificial timer.
- `HouseholdStorageScreen` renders a static matching scene and “Opening Calm Frames” /
  “Loading your settings.” Errors show a blocked state with Retry. Neither is blank.
- The consumer player lazy route uses `PlayerOpening`, matching its following opening
  screen. This is separate from the native video cover and readiness guards, which remain
  untouched. The hidden/inactive Home subtree intentionally removes controls to prevent
  focus escaping behind playback; it is not a blank startup bug.
- There is no new shimmer, grain, pulse, focus scaling, fabricated title row or startup
  delay. These React fallbacks do not establish or repair OS/native blank frames. Acadia's
  encoded dark opening is still content, not a placeholder bug.
- Home already exposes How it works, and Details exposes More info; both return focus to
  their opener. “Not other apps or live TV” was already present; “prepared” and the explicit
  lack of medical validation are the limited additions.

## Submission handoff

[SUBMISSION_RECONCILIATION.md](SUBMISSION_RECONCILIATION.md) lists exact corrections for
Claude's three reserved drafts. Main corrections: current installed identity; the generated
approved catalog replacing the old Home filter; completed staging/recheck/cancel versus
Prairie's frozen proposal; build-time file hashes versus runtime map/route verification;
and existing informative broadcast pattern analysis versus a blanket “unsupported” claim.
Historical test/native figures must stay attributed to their actual runs. No legal/rules
research, publication or edits to the reserved files occurred.

## Verification and limits

43 focused tests across four suites pass, including copy, explanation navigation and
existing startup rendering. TypeScript, focused ESLint and diff whitespace checks pass.
The first Jest invocation could not access Watchman's state under the sandbox; the completed
run disabled Watchman and used a workspace-local cache. No dependency or global setup changed.

One Debug build and one install were performed for this pass. All 730 app inputs match;
only the four expected source/test files differ from `6125459`. The report-required built
package check passes for the retained four bundles and original reports. Consumer membership
remains Acadia only.

Package: `build/release/final-clarity-2026-10-18/calm-frames-clarity-aarch64-debug.vpkg`

SHA-256: `8f3636ec8bcc2a1c2d5ac80e26f7b3024c0b0ff9003bbdb1341569c51adecbfd`

See [the exact native result and receipts](../results/final-clarity-2026-10-18/README.md).
Native text logs establish navigation/focus events, not wording legibility, pixels or audio.
Playback observations remain the separately dated `6125459` integration smoke; this wording
pass does not repeat playback or claim to fix intermittent simulator slowdown.

## Smallest owner steps

1. Read the two explanation screens on the installed app and complete the existing
   visual/audio acceptance. Text logs cannot approve their layout or sound.
2. Have the submission owner apply the separate reconciliation, then finish footage/demo,
   reviewer access and the actual form decisions. No new title or feature is required.

No screenshots, recordings, original-video playback, push, external publication or
security/cloud changes occurred. The reserved draft files were preserved. Stop feature work.
