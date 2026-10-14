# Approved dusk coast integration — 14 October 2026

Integrated the approved palette into `codex/control-depth-integration-2026-10-14`. Runtime source: **`e05216284b2e3e85e8a73275432568c512c7317c`**, following approved study `e97e0da` and prior integrated candidate `95f7411`. The study branch remains preserved.

Ink/slate/ivory/coral now carry Home, Details, Settings, Help, startup, player opening/loading/error/controls, caption menu and PIN/setup surfaces. Gold is reserved for focus, including the native seekbar's focused indicator. Noninteractive metadata uses supporting text; pending status uses pale slate-blue, errors use the distinct warm error tone, and disabled PIN labels use the shared muted text. Selected controls retain a checkmark/pale edge; focus retains the gold outline and existing secondary cue. The full palette and typography reference is synchronized with the source in [design tokens](design/tokens.json).

Original Harbor/zen artwork, logo files, Fraunces/Source Sans 3, film, cover/guard logic, timing, storage, geometry and interactions are unchanged. Protective black covers and video/error backdrops remain black. The design-page check now explicitly protects the original logo palette independently of UI tokens; it does not recolor the artwork to satisfy token parity.

## Review artifacts

- [Home, Details, Settings and Help](../results/dusk-coast-integration-2026-10-14/comparisons/library-and-help.png)
- [Startup, player opening, PIN and setup](../results/dusk-coast-integration-2026-10-14/comparisons/startup-and-setup.png)
- [Player, pause, simultaneous hold/caption menu/cue and recovery](../results/dusk-coast-integration-2026-10-14/comparisons/player-and-captions.png)
- [Loading and shared control states](../results/dusk-coast-integration-2026-10-14/comparisons/loading-and-control-states.png)
- Full captures: [1080p](../results/dusk-coast-integration-2026-10-14/1080/index.html) · [720p](../results/dusk-coast-integration-2026-10-14/720/index.html)

All four review sheets were saved to Library; [exact attachment IDs](../results/dusk-coast-integration-2026-10-14/checks/library-attachments.json). Matched sheets compare prior source `867d449` (left) with final source `e052162` (right), at identical 1920 × 1080 states. These are **static component renders in Chromium**. Native video, captions and seekbar are explicit substitutes. Loading is a final-state capture rather than a before/after pair. A composition-only text-stacking correction was made after the build; app inputs remain exactly `e052162`.

## Checks

- 178 focused app tests covered 13 suites; two old color/inventory expectations were corrected and their 25-test subset reran successfully. The remaining 153 tests already passed. One existing snapshot passed.
- Twelve full-flow fixture exports passed, plus eight palette/control tests. Both resolutions produced 48 states / 95 captures; help/PIN safe bounds and hold/menu/multiline-cue separation assertions passed.
- Typecheck passed. Targeted ESLint: zero errors, one existing `no-void` warning in `HarborOpening.tsx:84`; final changed-test/inventory lint passed.
- Design-page/token/font/contrast/artwork-preservation checks: **21 passed**.
- Modeled solid-color UI transition check: **36 screens/transitions passed WCAG and broadcast profiles**. This is a model check, not native motion or gradient pixel proof.
- Visually inspected all four representative sheets, the final control states and the 720p simultaneous hold/menu/multiline cue. No conflicting old teal UI hex tokens remained in the inspected app UI paths; teal artwork/ripples are intentionally preserved.
- Material text minima: primary **4.63:1**, secondary **5.72:1**, selected **4.94:1**, disabled **5.36:1** (truncated); gold/ink separator **9.36:1**. All exceed the applicable 4.5 text / 3 focus floors. Gold directly against coral alone is not claimed to meet 3:1.

## Exact package

Built aarch64 Debug at `2026-10-14T17:51:07Z` using the existing Node 22 / Vega / JDK 21 toolchain, reused generated Shaka outputs and local watchman shim. No dependencies added.

Local package: `build/release/dusk-coast-integrated-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg` — **21,881,599 bytes**.

SHA-256: **`d31ddafca960363ee76afaa4f2cf6eb28563cb144ea6aa0a6a9145e4fd365f2a`**.

[Preparation](../results/dusk-coast-integration-2026-10-14/checks/PREPARATION.json) and [build receipt](../results/dusk-coast-integration-2026-10-14/checks/release-build-receipt.json) bind it to committed source `e052162`. Packaged library exact-byte checks passed: one title, three bundles, all three original verification reports. Catalog SHA-256 remains `02f76715d81d263deb556433cb3ddb914ea9c1d8820f9f8054719dda71b88b79`.

Commands and outcomes are retained in [checks](../results/dusk-coast-integration-2026-10-14/checks/commands-and-results.txt); all evidence hashes are in [ARTIFACT_SHA256SUMS](../results/dusk-coast-integration-2026-10-14/ARTIFACT_SHA256SUMS).

## Native boundary

**Pending:** installation and native observation of this package. The existing simulator was previously connected, but Computer Use returned **“Computer Use permissions are not granted.”** No new permission evidence was provided, so no denied action was retried or bypassed. Actual moving playback, native fonts/gradients, D-pad and VoiceView remain unverified. The user must grant the Mac's Computer Use access and unlock it if needed before a consolidated native session. Household PIN entry, if required, must be legitimate user entry; no PIN was read, guessed or reset.

[Native task](codex://threads/01a138bb-a422-7746-9293-caf676f250f3). No installation, data reset, deployment, publication or merge occurred. Previous packages, recordings, other workers and shared/main branches were preserved.
