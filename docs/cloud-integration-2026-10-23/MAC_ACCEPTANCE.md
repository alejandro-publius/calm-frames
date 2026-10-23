# Exact-build Mac acceptance handoff

The canonical branch is `codex/integration-owner-2026-10-23`. This document and
the export's `START_HERE.txt`, `SYNC_MANIFEST.json`, `SHA256SUMS` and transfer
receipt form one handoff. The manifest records the exact full source HEAD,
required base, commits and changed-file hashes. Use that immutable HEAD, not
whatever a moving branch later contains. The ZIP contains source and evidence;
it contains no newly built native package, household data or generated media.

This cloud thread remains the sole integration owner. A Mac operator executes
the checks and returns receipts here. No separate Claude editing assignment is
needed. Before using an external checkout, obtain any active editor's saved
checkpoint and stop acknowledgement. Preserve uncommitted work and all existing
worktrees. No acknowledgement from an inaccessible editor is implied.

## Verify and open a separate worktree

1. Verify the downloaded ZIP's size and SHA-256 against the transfer receipt.
   Extract it to a new directory and run `shasum -a 256 -c SHA256SUMS` there.
2. Follow the export's exact bundle verification and new-ref/worktree commands.
   The required base is `6360417814d684d41c94789a9e406fc27de53c66`. The import
   was tested in a base-only repository; the receipt records that verification.
   Stop if the chosen review ref or directory already exists. Do not reset,
   stash, switch or clean an existing checkout.
3. Confirm the new worktree's full `git rev-parse HEAD` equals the manifest.
   Check its `git status --porcelain` is empty. Compare the exact-SHA hosted
   receipts linked by this thread. A passed upstream run is not acceptance of
   this build; pending or failed checks stay pending or failed.

## Build once using the existing Mac tooling

Use the installed supported Vega SDK, Node 22 and existing JDK/player-build
setup. The cloud clean install uses Node 22.23.2 and npm 10.9.8; those exact
versions also reproduce the committed SBOM. Do not change signing configuration,
approved maps, media or household data to make a build pass.

In the new worktree, perform the repository's existing locked install, player
setup and release preparation, using a distinct tag containing the short HEAD.
The historical [Mac procedure](../handoff-2026-10-23/MAC_ACCEPTANCE_CHECKLIST.md#3-build-and-install-package-scoped)
documents the commands and required local tools. Resolve actual local paths;
Mac paths in old handoffs are not available in the cloud. Do not copy the old
branch checkout or old CI-cancellation instructions from that document.

Before installing, record source HEAD, lock hash, SDK/tool versions, build tag,
package bytes and SHA-256. Verify a rollback package is readable and has the
recorded hash below. Use a package-scoped install on the existing VirtualDevice;
no uninstall, cleared storage, first-run reset or new PIN. Record the installed
package identity as well as the source identity. A failed gate is a result to
report, not permission to bypass checks.

## Native and human checks still required

| Check | Required observation and limit |
|---|---|
| Primary action and card edges | Inspect Watch at rest, focused and pressed, selected versus focused cards, text over actual artwork and unchanged geometry. Source contrast arithmetic does not establish native appearance. |
| Remote focus and profile saving | D-pad navigation, active-profile focus, save completion and Back return; preserve existing profiles and positions. Enter a PIN privately with capture paused. |
| Onboarding footer | Check wrapping and reachable controls only with an isolated first-run fixture that preserves the household. Otherwise record unobserved. |
| Recovery and protection ordering | Use only approved benign/practice routes. Record cover, seek, playback and recovery events with exact source/package identity. Keep compositor/decoder ordering unproved where instrumentation cannot establish it. Do not merge or present the Retry harness as production. |
| Existing ambient titles | Confirm the approved Acadia, otter and Forest still/default and explicitly selected preview routes. Observe sustained McWay playback, final hold and Back on this build; earlier native receipts remain earlier observations. |
| Accessibility | Observe remote focus, VoiceView where available and reduced-motion behavior. A source test is not a native accessibility pass. |
| Human review | Owner listening, pace/comfort, palette and final video review are separate explicit observations. Do not infer them from logs, screenshots, a script approval or technical media evidence. |

Return one receipt with full source and package hashes, each check's observed,
failed or unobserved status, evidence paths/hashes, and exact limitations. Never
include a PIN, household record or private account screen. Stop a failing route
without exposing anyone to unprotected flashing content. Do not introduce new
media or reset preferences to complete the list.

## Package-scoped rollback

These identities were recorded in prior Mac evidence. Their files were not
received or rehashed here. Verify local bytes before using them; if a hash does
not match, stop and identify the missing rollback input.

| Prior source/scope | Recorded package SHA-256 |
|---|---|
| `bd55e47`, nearest recorded production install | `4d229b6fd9c2a1ab61aa22eb996a673243da367db66035cb7f640bf70214e8a7` |
| `4b04877`, earlier footer/profile evidence | `2bfac62fe2bd992186dd5d948a18b47dc5392f5e003c1cc49280be2476963101` |
| Submitted-era rollback | `207898aa14d8659760348a716b825fabab83afd8e3b9431f9387202cc10e7163` |

Restore only by the existing package-scoped install procedure; never uninstall
or erase storage. Verify restored package identity and the ordinary Home route.
Restoring a binary does not authorize changing household data, signed content,
the submitted fallback, repository main or the live submission.

## Acceptance boundary

Cloud source validation is complete only as recorded in the product receipt;
terminal CI and Audit must name this exact HEAD. Product acceptance additionally
requires the unresolved dependency decision and applicable native/human checks.
Until then, this is an unsubmitted development candidate. Manga, ElevenLabs and
new demo production remain parked. Preserve the user-stated October 23
19:00 UTC cutoff: do not edit frozen submitted materials afterward. No automatic
promotion follows from finishing a Mac check.
