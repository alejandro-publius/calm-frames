# Curated friction log draft

**Draft for owner review, not submitted feedback.** These are recorded development issues, not new reproductions. The canonical log remains `docs/FRICTION_LOG.md` at `13551e4`; this package does not edit it. [Local source excerpts](evidence/friction-records.md) retain the relevant observations. The environment recorded for the October native work was Vega SDK 0.24.9914, CLI 1.3.4 and the Vega Virtual Device, with source checkpoints identified where the record provides them. Do not generalize these observations to physical hardware or current SDK versions without a new authorized check.

Reproduction steps below are normalized descriptions for a future maintainer. They were not run in this cloud task. Use a benign, already approved local fixture and a developer device; no credentials, signer changes, hazardous playback or desktop capture is required by this draft.

## F1. Packaged media URI differs from the documented form

- **Task and steps:** On the recorded virtual-device build, pass a bundled MP4 and WebVTT to the native player as `file:///pkg/...`. Compare with the same package-relative path beginning `/pkg/...`.
- **Expected:** The package asset opens using the form described by the file-system documentation.
- **Actual recorded:** The native player treated the URI as a literal filename and failed; the same bytes opened with `/pkg/...`.
- **Severity:** High in that workflow: package playback was blocked.
- **Workaround:** Normalize the prefix only at the native media boundary in `app/src/utils/VideoHandler.ts`; preserve catalog and signed identities.
- **Evidence/status:** Canonical entry 36; implementation in the pinned code map. App workaround exists. No SDK-side resolution is established.
- **Suggestion:** Publish one explicit package-URI contract across file-system and media APIs, or accept both supported forms. Include an MP4 plus caption sample.
- **Useful acceptance check:** The sample opens using the documented URI, or unsupported input produces a documented JavaScript error with the accepted format.

## F2. Authenticated data-URI still renders black natively

- **Task and steps:** On the recorded Debug candidate, open the practice title from Details and correlate `CALM_TRACE still` with `LocalAssetImageLoader` around the scheduled hold.
- **Expected:** The authenticated still renders as it did in the source tests and browser preview.
- **Actual recorded:** The hold card appeared over black and the native log said it could not load the image from a non-local source. A browser render was not evidence of device support.
- **Severity:** High: the intended hold image was absent.
- **Workaround:** Bundle the exact practice stills and substitute only when the authenticated data URI matches. The recorded change is `52138fe`; the implementation is `app/src/calmframes/bundledStills.ts`. Do not generalize the workaround to arbitrary data or expand trust.
- **Evidence/status:** Canonical entry 41 and the existing native acceptance context. App workaround exists; an SDK fix is not recorded.
- **Suggestion:** Document the native `Image` source support matrix, and propagate refusal reasons through JavaScript `onError`. If data URIs are supported, test them in the native sample.
- **Useful acceptance check:** A supported data URI loads, or a specific unsupported-source error reaches the application without requiring device-log inspection.

## F3. Decoded-frame quality counter does not establish readiness on the VVD

- **Task and steps:** Start a benign title on the recorded virtual-device candidate; poll `getVideoPlaybackQuality().totalVideoFrames` while comparing with media state and device trace lines.
- **Expected:** The counter advances as frames decode, or the API explicitly reports that the capability is unavailable.
- **Actual recorded:** The counter remained zero while picture and sound played. Native logs contained error code `50001`; the app's original opening logic eventually showed recovery over ongoing playback.
- **Severity:** High in this implementation: normal playback was misclassified as an opening failure.
- **Workaround:** The recorded `ac5a610` change in `useOpeningFrame.ts` uses readiness and advancing media time when the counter is silent, while giving a reporting counter precedence. This is a fallback, not proof that a frame was physically displayed.
- **Evidence/status:** Canonical entry 42. App workaround is recorded; no platform fix or physical-stick reproduction is claimed.
- **Suggestion:** Expose capability support and documented errors in JavaScript, and distinguish media-clock progress from decoded-frame and displayed-frame evidence.
- **Useful acceptance check:** A VVD sample can distinguish supported statistics, unsupported statistics and actual decode failure without inferring capability from a silent zero.

## F4. Documented remote command fails with a success exit code

- **Task and steps:** The log records `vega exec inputd-cli --help`, then `vega device run-cmd --device Simulator --command 'inputd-cli --help'`, then a device-side `button_press KEY_DOWN`.
- **Expected:** The documented host form reaches the device utility; an unavailable executable produces a failure exit status.
- **Actual recorded:** The host form reported a missing executable and exited successfully. Device-side `run-cmd` worked. The CLI behavior was rechecked on October 14 in the source record.
- **Severity:** Medium: automation could mistake a failed input operation for success.
- **Workaround:** Run the utility inside the selected device and confirm the expected app trace before sending another key.
- **Evidence/status:** Canonical entry 43; `results/native-acceptance-2026-10-14/receipt.json`. No new command was sent here.
- **Suggestion:** Correct the documentation or route the documented command to the device; return nonzero for missing tools and failed input dispatch.
- **Useful acceptance check:** A shell script can reliably distinguish an input sent to the intended device from a missing command or disconnected target.

## F5. Disabling the focused control loses native focus

- **Task and steps:** In the recorded parent-settings workflow, focus a setting and start a deferred save that disables that control.
- **Expected:** Focus remains discoverable on that control or moves predictably to a neighbour.
- **Actual recorded:** Native focus disappeared and the remote had no useful next target.
- **Severity:** Medium in the log: a blocked remote interaction.
- **Workaround:** Keep the control in focus order, expose its disabled accessibility state and block duplicate handlers. See `ParentAreaScreen.tsx`; the deferred-write regression was recorded as failing before the app fix.
- **Evidence/status:** Canonical entry 40. No full screen-reader or physical-device acceptance follows from this fix.
- **Suggestion:** Document focus semantics for disabled and removed controls, and provide a native sample showing asynchronous saves and predictable focus restoration.
- **Useful acceptance check:** Keyboard/remote focus remains visible and the accessibility state remains accurate during and after an asynchronous save.

## F6. Incremental package staging retains removed media

- **Task and steps:** In the recorded October 18 and October 21 workflows, remove or replace a prepared bundle in the source namespace, then run the native incremental package build and compare staged/package membership with source membership.
- **Expected:** Removed source assets are absent from the generated package.
- **Actual recorded:** Staging retained obsolete media. The existing strict package budget gate rejected the package. A successful compile was not a valid-package result.
- **Severity:** Build-blocking in the recorded workflow. This is not a measured startup or analyzer-performance issue.
- **Workaround:** Preserve the stale generated namespace as evidence, clear only that generated namespace and rebuild/repackage from checked sources, then rerun strict package gates. This describes historical authorized recovery, not an instruction to change the current package.
- **Evidence/status:** Canonical dated staging entries. The application gate detected the mismatch; no SDK repair is established.
- **Suggestion:** Reconcile deletions when staging assets, or document a supported narrowly scoped clean command and emit a source-versus-package membership report.
- **Useful acceptance check:** Removing a source fixture removes it from the next incremental package, and package checks still reject any unexplained extra asset.

## Attribution boundaries

Locked Mac screenshots, ScreenCaptureKit/Stage Manager behavior, browser file-URL policy, sandboxed Watchman access and GitHub runner/account problems are not attributed to Amazon in this draft. A native capture API could be a feature request, but those host observations do not prove a Vega defect. Entry 44's noisy image-loader errors are a useful diagnostic observation, not proof of the logger's internal fallback order.
