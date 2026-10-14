# Dusk lantern integration and build, 14 October 2026

Isolated branch `codex/dusk-lantern-integration-2026-10-14` in `calm-frames-dusk-final` pins Claude's completed handoff `6a6212c7fc3b0327a1491554e7a9a7f1067e2066`. Its app design is `3fc2720`; snapshot updates are `dcca82c`. The worktree was independently confirmed clean and tracking the pushed handoff at 20:48 UTC. No worker files or terminals were modified.

The candidate already includes the integrated dusk palette, Fraunces/Source Sans 3, original zen and harbor, Harbor loading fallback and Watch/Details/poster return-focus fixes. Dusk lantern adds the optional demo entry and its return focus. Supported-title limitations, mandatory household setup, stored household data and the zero-hold Harbor story are preserved. No app-source change was needed during this integration pass.

## Checked build

Source: **6a6212c7fc3b0327a1491554e7a9a7f1067e2066**. App inputs were committed at build time. Existing toolchain and locally cloned dependencies/generated runtime were reused.

Package: `build/release/dusk-lantern-integration-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg`, **21,886,935 bytes**.

SHA-256: **48cbad6d97e912e7ee091ffabd15bb035966fa4952a55754b36406cb4dc51198**.

The supplied Claude package was preserved and independently hashed as `4f576e54c724d780bde5645fb617b6747014f57b4a13bae5c33f4093a0d25cd8`, built from `3fc2720`. Its receipt differed from the final handoff only in six subsequently updated test snapshots. A fresh isolated build avoids claiming complete source-inventory equivalence for that older package.

[Build receipt](../results/dusk-lantern-integration-2026-10-14/checks/release-build-receipt.json) and [preparation record](../results/dusk-lantern-integration-2026-10-14/checks/PREPARATION.json) contain the complete input and package hashes. All three original prepared-media reports passed; catalog SHA-256 remains `02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79`.

## Checks and snapshots

187 focused tests passed across 12 suites, including the design, route focus, mandatory setup, household restart, prepared library and benign-demo checks. Typecheck, focused lint and 21 design-token checks passed. Two component-export fixtures passed. These are bounded integration checks; no new full-suite pass is claimed. [Commands and outcomes](../results/dusk-lantern-integration-2026-10-14/checks/commands-and-results.txt).

Home and Details were freshly rendered from this candidate at 1920x1080 and 1280x720. Existing safe-area, lighthouse-clearance and contrast checks passed. The comparison is matched against the preceding `f95a366` immersive study. Library attachments explicitly say **Static component preview | Not a native simulator capture**.

- [Home](../results/dusk-lantern-integration-2026-10-14/static/calm-frames-dusk-lantern-home-static.png)
- [Details](../results/dusk-lantern-integration-2026-10-14/static/calm-frames-dusk-lantern-details-static.png)
- [Before and after](../results/dusk-lantern-integration-2026-10-14/static/calm-frames-dusk-lantern-comparison-static.png)
- [Verified Library IDs](../results/dusk-lantern-integration-2026-10-14/static/library-files.json)
- [Capture hashes](../results/dusk-lantern-integration-2026-10-14/ARTIFACT_MANIFEST.json)

## Pending boundaries

Claude separately owns the reported hook mirror/package dependency fix and repository prose-style violations. Those files were not modified here. This receipt will be supplemented after that commit is delivered and checked.

Native observation remains blocked by the earlier Computer Use permission failure. No new permission evidence was provided, and no denied action was retried or bypassed. Claude also reported Simulator Device not found; that was not independently re-probed here. This package has not been installed or launched. Actual moving playback, hidden controls, simultaneous hold/caption-menu/multiline cue, D-pad, VoiceView and recovery remain unverified for this candidate.

[Installation and demonstration outline](DUSK_LANTERN_INSTALL_DEMO_OUTLINE.md) prepares one coherent native session after legitimate access is available. No PIN was read or reset. No submission, demo assembly, publication, deployment or shared/main merge occurred.

[Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3).
