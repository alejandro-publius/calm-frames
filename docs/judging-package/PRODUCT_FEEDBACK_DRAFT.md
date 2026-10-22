# Product feedback draft for Vega tooling

Not sent. These suggestions derive from the [recorded friction draft](FRICTION_LOG_DRAFT.md), not new SDK experiments. Priority is a project recommendation, not a claim about Amazon's roadmap or all developers.

This is a **supplement for the Vega issues selected here**, not a replacement for the full per-tool inventory in [the pinned product-feedback record](https://github.com/alejandro-publius/calm-frames/blob/13551e45bd853c392489dbecce7158a04036f615/docs/FEEDBACK.md). That record also covers AWS and other tools; their deployment, account and benchmark details are outside this package. The five prompts below follow that historical record. Current submission wording still needs the live rules check described in [the source register](PRIMARY_SOURCES.md).

## Five-question update for the selected tools

### Vega SDK and CLI

1. **What we used it for:** Build, package, install and log the native app; send remote input to the selected virtual device. The release record supplies the installed source and package identity.
2. **What worked well:** The recorded install and device-side input route enabled the native walkthrough. Exact package checks exposed stale generated media before it was treated as a valid release.
3. **What needs work:** Make input-command failure observable to shell automation (F4), and reconcile deleted assets during incremental staging (F6). The package refusal is an application gate doing its job, not evidence that the SDK diagnosed the mismatch itself.
4. **Onboarding:** Provide one checked example from connected target to installed sample, remote input and device log. State the supported generated-assets-only cleanup path. No new onboarding duration was measured here.
5. **Would we build with it again:** Proposed answer: yes for this prototype, retaining explicit device-response and package-membership checks. This recommendation follows the recorded workarounds; it is not a new SDK evaluation or an owner endorsement of current releases.

### Vega Virtual Device

1. **What we used it for:** Observe the native journey, proof pages and remote reading stops on the recorded build.
2. **What worked well:** Existing captures and trace observations made native behavior inspectable without a physical Fire TV. They remain labelled with their source builds and observation limits.
3. **What needs work:** Clarify which media statistics the virtual device supports and which observations require physical hardware (F3). No conclusion about a host capture failure's platform root cause follows from a locked Mac or a black capture.
4. **Onboarding:** Show a bounded benign sample with supported diagnostics and a clear distinction between virtual-device and physical-screen evidence. This package measured no new setup time.
5. **Would we build with it again:** Proposed answer: yes for development and native workflow review; its observations do not establish physical-screen timing, audio acceptance or a full hardware review.

### react-native-w3cmedia

1. **What we used it for:** Play the packaged approved edition and supply media state to the app's opening and guarded-playback logic.
2. **What worked well:** The recorded native runs show packaged playback after the URI-boundary workaround. The source has one guarded seek path and explicit opening/recovery handling.
3. **What needs work:** Align packaged URI forms with file-system documentation (F1); expose unsupported playback-quality statistics explicitly (F3). Advancing media time must not be described as a physically displayed frame.
4. **Onboarding:** Add a packaged MP4/WebVTT sample alongside streaming examples, with supported-statistic detection and JavaScript error reporting.
5. **Would we build with it again:** Proposed answer: yes with those capability boundaries documented and native observations kept separate from source tests. The draft does not claim a fix in a newer SDK.

### React Native for Vega image and focus APIs

1. **What we used it for:** Present authenticated hold stills, focusable settings and the remote-readable evidence record.
2. **What worked well:** Exact bundled-still substitution and retained-focus controls provided bounded app workarounds. The upgraded record was reached with remote reading stops in the saved native review.
3. **What needs work:** Document image-source support and surface load failures in JavaScript (F2); specify focus behavior when the focused control becomes disabled (F5).
4. **Onboarding:** Include native examples for supported image sources and asynchronous saves. State where native behavior differs from browser previews, and show accessible busy/disabled states without losing the user's place.
5. **Would we build with it again:** Proposed answer: yes, with native acceptance alongside component tests. Complete VoiceView and physical-device acceptance remain open.

## Prioritized suggestions

| Proposal | Developer and user benefit | Recorded basis | Suggested bounded improvement and acceptance |
|---|---|---|---|
| **Priority 1: one native asset contract** | Developers can predict which media/image sources work; viewers encounter fewer unexplained black states. | F1 packaged URI; F2 data-URI still; canonical entry 44's ambiguous image-loader errors. | Publish a per-API support table for package paths, URI forms and data URIs. Add native sample fixtures. Surface actionable `onError` reasons and reserve error logs for terminal failure. A successful fallback must not look indistinguishable from a failed load. |
| **Priority 1: explicit playback-stat capability** | Apps can implement opening/recovery behavior without confusing unsupported statistics with failed playback. | F3, `useOpeningFrame.ts`, error `50001` in historical logs. | Return a capability indicator or documented JavaScript error for unsupported statistics; document what each signal proves. Include VVD and physical-device coverage in the sample matrix. Do not treat media-clock progress as displayed-frame proof. |
| **Priority 1: predictable incremental asset membership** | Smaller, auditable packages and fewer failed release attempts after removing a large asset. | F6 and strict package-gate refusals. | Reconcile deleted source files, or provide a documented generated-assets-only clean path. Report unexpected retained files before packaging. Test add, replace and delete cases. Preserve application-level verification gates. |
| **Priority 2: truthful command exit status** | Automation can stop on a failed input rather than advance a false acceptance script. | F4, documented versus working `inputd-cli` forms. | Align CLI docs and routing; return nonzero for missing tools or targets. Add an example that confirms target identity and expected app response. |
| **Priority 2: focus and accessibility lifecycle examples** | Remote users retain their place during asynchronous saves, and developers can represent busy/disabled states consistently. | F5 and the recorded app workaround. | Show retained focus, announced state and restoration after save; document native differences from web previews. Validate the sample on a device and with VoiceView before claiming accessibility acceptance. |

## Feedback payload to accompany each issue

Send the historical environment, the exact task and minimal reproduction, the expected and observed result, the workaround and a redacted evidence link. State whether an issue is reproduced on current SDK versions; this package has not done that recheck. Never attach private paths, credentials, account identifiers, signing keys or original hazardous media.

The useful ask is a reproducible contract or diagnostic improvement. This draft does not ask Amazon to certify the app medically, endorse the project, award a judging bonus or adopt every workaround as platform policy.
