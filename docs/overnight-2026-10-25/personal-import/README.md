# Personal-file caregiver review

Original checklist item **13** now has a working local file-to-review flow with explicit processing permission, refusal of recognized encrypted MP4 metadata, and a portable report tied to the analyzed file. This extends the existing intake and preparation workflow. It does not add a native TV file picker or authorize a new title for playback.

Implementation: `ba9a60a8ccafd1d7358ac1ab22aea85055c1e40d`, with the existing delivery fixture updated in validated source `5e079494cacdffcc982928637c0210eabb0a5c14`, based on `15ef46c6e23c8ba627492da23b1b147000031aa4`. The [receipt](../../../results/overnight-2026-10-25/personal-import/checks.json) records source and artifact hashes, check commands and limits.

## Use the local caregiver page

From this checkout, use the repository's Python environment and installed FFmpeg. Keep the intake directory outside Git and outside a publicly served folder. Replace the example path with a private directory on the same computer:

```sh
PYTHONPATH=flashmap/src:. python -m pipeline.local_intake serve --root "$HOME/CalmFramesLocalReview" --port 8766
```

1. Open `http://127.0.0.1:8766` in a browser on that computer.
2. Read the supported format and size limits shown on the page. Select a non-DRM file you own or have permission to process, enter a title, and confirm that permission.
3. Choose **Analyze the full video**. The page shows processing stages and a cancellation action. The original is never played by this page.
4. Inspect the completed interruption plans and analysis identity. Choose **Save caregiver review (JSON)** to keep the exact file hash, analysis, acknowledgement and limitations together.
5. Reopen the same local server and intake directory to resume review later. **Remove local import** deletes this tool's copy and generated files after confirmation; it leaves the selected original unchanged.

An existing authorized signer is still required for preparation. Without it, preparation remains blocked and the caregiver report remains available. The report does not add a title to the TV library. The existing separately approved edition delivery, checked build and installation steps still apply.

## What changed

- Uploads require an explicit processing-permission acknowledgement before the tool copies the file. This is a user statement, not a legal-rights verification. Older retained jobs do not receive an invented acknowledgement.
- The bounded MP4 metadata inspection refuses recognized encrypted sample entries, protection boxes and encryption sample groups before analysis. It never decrypts a file or contacts a license service. Recognition of these declarations is not universal DRM detection or proof of ownership.
- Report export rechecks the exact source file, complete review and analysis-map hashes. Missing, incomplete or changed evidence prevents export. The download contains no source path and states that TV playback is not authorized.
- A recovered local connection now clears the stale connection-lost notice and updates the import list. Keyboard focus, download errors and the narrow layout were checked in a real browser.

## Evidence and scope

The focused intake, worker, package and edition-delivery suites passed <!--n results/overnight-2026-10-25/personal-import/checks.json:tests.passed -->129<!--/n--> tests. The evidence includes actual HTTP requests, worker processing and report download for generated steady-color, silent media. It verifies refusal without acknowledgement, refusal of a foreign origin, source-tamper detection, persistence after server restart, missing-signer blocking, no original-media HTTP route, and rejection of a generated encrypted MP4 before analyzer output.

New permission, complete-review, hash-binding and protection-metadata guards were deliberately disabled in isolated temporary edits; their targeted tests failed, then passed after restoration. The normal pipeline mypy configuration, Ruff, repository style check and whitespace check passed. These are local source checks, not hosted CI or native acceptance.

[Browser checks](../../../results/overnight-2026-10-25/personal-import/browser-checks.json) cover keyboard access to the report action, visible focus, measured body/button/focus contrast, narrow and desktop overflow, reduced-motion preference, reconnection, report identity, and absence of external requests or browser errors. The [desktop](../../../results/overnight-2026-10-25/personal-import/desktop.png) and [narrow](../../../results/overnight-2026-10-25/personal-import/narrow.png) images show the local caregiver browser page with a generated fixture. They are not Fire TV screenshots. The [sample report](../../../results/overnight-2026-10-25/personal-import/caregiver-review.json) describes that generated fixture, not approved program content.

The repeatable [browser check](browser-check.cjs) requires Playwright, Chromium, an already analyzed fictional job, and its generated fixture. It neither plays media nor installs a package. The HTTP test generates its own harmless input and temporary workspace, so no personal-file attachment is needed to reproduce the machine checks.

## Remaining boundaries

- Direct personal-file selection on Fire TV has not been implemented or claimed. The working selection and pre-check flow is local to the caregiver's computer.
- Streaming-app downloads and DRM removal are unsupported. The user must establish permission; this software cannot grant or verify it.
- A passed analysis does not establish medical safety, seizure prevention, comfort or human acceptance. No media was watched or heard during this validation.
- Authorizing a signer, approving an exact edition, building and installing that edition remain separate from saving a review. No new key, catalog entry, trust root, app asset, or playback authorization was added in this change.
- Native D-pad/VoiceView checks and the owner's audiovisual review remain outside this cloud evidence. Original item 13 remains partial wherever its acceptance requires direct native import or approved TV delivery.
