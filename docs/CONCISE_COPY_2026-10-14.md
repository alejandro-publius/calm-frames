# Concise Home and Details copy, 14 October 2026

Source `ed1347ecb9773d38250a7b8bcc14cb2ee8641ab6`, isolated branch `codex/dusk-lantern-integration-2026-10-14`. Bounded copy cleanup requested after the dusk lantern review. No theme, layout-system, media, timing, household or backend change.

Home now reads:

- Harbor
- 20 sec · No picture holds
- Play | Details
- Picture holds on supported videos. Audio continues.
- Try picture holds
- 20 sec · 2 practice holds

Runtime comes from the title. Practice count comes from its existing merged cover schedule. A regression fixture changes both and verifies the text follows them. Help, parental controls, callbacks, preferred focus and return-focus identifiers remain. Accessible action names retain the title or demo context and match the new visible labels.

Details drops scenery narration and the original-short attribution. It retains factual metadata, the undetected-flashing limitation, demo explanation, viewing settings and pre-play notices. Its primary Harbor action also reads Play.

## Evidence

132 focused app tests passed in 7 suites, typecheck and targeted lint passed, 21 design checks passed, and both actual-component export fixtures passed. Updated static captures at 1920x1080 and 1280x720 passed safe-area, lighthouse-clearance and contrast checks. They are labelled static previews, not native captures. [Commands and outcomes](../results/concise-copy-2026-10-14/checks/commands-and-results.txt).

- [Home](../results/concise-copy-2026-10-14/static/calm-frames-concise-home-static.png)
- [Details](../results/concise-copy-2026-10-14/static/calm-frames-concise-details-static.png)
- [Before and after](../results/concise-copy-2026-10-14/static/calm-frames-concise-comparison-static.png)
- [Library IDs](../results/concise-copy-2026-10-14/static/library-files.json)

Fresh aarch64 Debug package, 21,885,386 bytes:
`build/release/concise-copy-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg`.
SHA-256 `58ee2e769323aff98c3970357bd5d0c530910e00d3ef5278cccdf9dd2054de4f`.
[Build receipt](../results/concise-copy-2026-10-14/checks/release-build-receipt.json), [preparation](../results/concise-copy-2026-10-14/checks/PREPARATION.json) and [artifact hashes](../results/concise-copy-2026-10-14/ARTIFACT_MANIFEST.json).

All three original prepared-media reports passed. Catalog SHA-256 remains `02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79`. Prior packages and captures are preserved. This package has not been installed or launched. Native playback, D-pad, VoiceView and combined caption/hold observation remain untested.

## Permission diagnosis and other worker status

The previously recorded Finder app-selection failure was `Computer Use permissions are not granted`. The current thread-history API confirms failed app-selection calls but does not expose their original error detail, so the wording above is taken from the contemporaneous integration receipt. That generic error does not prove an OS permission failure or a user rejection. Separately, the original Terminal app access was recorded as denied by Computer Use safety policy. Neither action was retried or bypassed.

The current [official Computer Use guide](https://learn.chatgpt.com/docs/computer-use) gives the supported setup checks: Plugins > Computer Use for enable/server/skill state, Settings > Computer use for app access, and macOS System Settings > Privacy & Security > Screen Recording and Accessibility for Codex Computer Use. System permissions and app approvals are separate. The user can check those settings; no specific missing toggle is diagnosed, no permission is changed here, and this guide does not authorize bypassing the Terminal policy denial.

Read-only project status during this follow-up found no new documentation-packet branch or worktree. The main, Claude fixes and prior evidence worktrees were clean at 09ee50e, 8ef8a0e and 325b53b respectively. The known Claude process remained present, sleeping, at 0.4% CPU; that does not establish an active or completed packet task. No duplicate packet edits were made.

[Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3).
