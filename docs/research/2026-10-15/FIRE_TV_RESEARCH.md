# Calm Frames: Fire TV resource review and bounded improvement plan

Reviewed: 15 October 2026. Scope: the Fire TV section of the [hackathon resources page](https://amazonappdev2026.devpost.com/resources), its most relevant sample repositories, and linked Amazon documentation. This is research, not an implementation or device-test report. No SDK, package, MCP server, or agent skill was installed or run.

## Recommendation

Keep the existing Vega React Native prepared-video approach. Spend the remaining work on evidence that the distinctive experience works: a clear picture-hold sequence with uninterrupted audio, predictable remote navigation, a dependable parent-settings gate, and a legible coastal presentation. Do not replace the app with a sample, migrate frameworks, add a backend, or add adaptive streaming merely because a reference includes those features.

The order of value is:

1. Prove the existing complete flow on Vega simulator or Fire TV and prepare a manual demo plan. Recording requires the owner's separate approval; automatic capture is currently prohibited.
2. Close playback lifecycle and focus-restoration failures that would interrupt that demonstration.
3. Validate the parent PIN route and accessible remote controls.
4. Optimize existing coastal assets and measure obvious performance problems.
5. Use Builder Tools selectively if setup is already straightforward; it is optional tooling, not a submission feature.

These are engineering judgments for this project, not Amazon requirements. They assume the described app already has prepared content, picture holds, continuing audio, remote UX, a parent PIN, and coastal artwork. This review did not inspect Calm Frames source code or establish whether any particular defect exists.

## 1. Preserve the prepared-video pipeline

**Source findings.** Amazon distinguishes direct URL playback of flat MP4/MP3 files from MSE-based adaptive HLS/DASH playback. The latter requires a JavaScript player such as Shaka. The native media controller must be initialized; rendering and controller lifecycle are separate concerns. [Playback modes](https://developer.amazon.com/docs/vega/0.24/media-player-select-playback), [W3C media overview](https://developer.amazon.com/docs/vega/0.24/media-player).

**Application to Calm Frames.** If the holds are already encoded into the prepared video, leave that single-file mechanism intact. It naturally avoids running independent picture and audio clocks. Do not add an audio-only player or attempt runtime frame extraction just to make the demo more sophisticated. If an existing hold is implemented as an image overlay, verify that changing the visible picture does not pause, recreate, or seek the underlying player. This is a proposed test, not evidence that Vega provides a freeze-frame API; no such API was established by this review.

**Acceptance tests.** Play across a hold boundary; listen for silence, clicks, repeated words, or time jumps. Pause during a hold, wait, then resume. Seek into, across, and out of a hold if seeking is already supported. Replay after completion. Repeatedly enter and leave the player. Establish that there is one coherent playback position and that “picture held” and “playback paused” are visibly different states where both exist.

**Stop criterion.** One complete prepared clip passes those cases on the intended runtime, with no new media engine or content-processing feature required. Any unimplemented behavior should be omitted from the demo claims.

## 2. Use the video sample as a lifecycle reference

**Source findings.** [vega-video-sample](https://github.com/AmazonAppDev/vega-video-sample) demonstrates custom controls, prebuffering, focus, and error handling. Its [VideoHandler.ts](https://github.com/AmazonAppDev/vega-video-sample/blob/main/src/utils/VideoHandler.ts) separates initialization and teardown, removes listeners, and releases the player. The sample also contains IAP, live-TV, and launcher integrations that Calm Frames does not need.

Amazon's [media-app requirements](https://developer.amazon.com/docs/vega/0.24/media-player-requirements) say to release unused media resources on backgrounding and preserve playback context for resumption. These are Appstore-oriented requirements; completing a hackathon demo is not equivalent to passing certification. The [media setup guide](https://developer.amazon.com/docs/vega/0.24/media-player-setup) documents package/Babel configuration and media, audio, and caption manifest declarations.

**Application.** Compare the existing player only against resource ownership and teardown: initialize once per active lifecycle, avoid duplicate event subscriptions, cancel outstanding work on exit, and prevent stale callbacks from resuming a player the user already left. Treat “audio continues while the picture is held” as an in-player behavior; it does not automatically justify playing audio after Home or app exit.

Verify Home/background/foreground, Back from playback, failed media loading, and replay. A failed load should show a readable explanation with a remote-reachable Back or Retry action instead of a permanent spinner. Audit the current manifest against the app's pinned SDK; do not paste every sample permission or replace its versions wholesale. The setup and requirements pages contain different generations of service declarations.

**Stop criterion.** No overlapping audio, orphan player, stuck loading screen, or lost resume context in the exercised cases. Keep a known-good package while any lifecycle fix is tested.

## 3. Make remote focus deterministic

**Source findings.** The [TV interfaces focus guide](https://github.com/AmazonAppDev/vega-tv-interfaces-sample/blob/main/src/services/focusGuide/README.md) favors autofocus containers and reserves directional overrides for exceptional layouts. [TVFocusGuideView](https://www.developer.amazon.com/docs/vega-api/0.24/tvfocusguideview) supports remembering a focused child, destination targets, and directional traps. The [focus-management guide](https://developer.amazon.com/docs/vega/0.24/focus-management) warns about focus loss after unmounting the focused control, hidden views, and returning to a screen.

**Application.** Test Library → Player → Back → same selected item; Settings → PIN → Cancel → initiating control; wrong PIN → retry; correct PIN → intended settings. Check that every screen starts with visible focus and that fading/hiding player controls leaves no invisible focus target. A PIN dialog may contain focus while open, but needs a reachable cancel/back route. Avoid rebuilding navigation for a small app.

For controls that exist, map Select to the focused action and Play/Pause consistently. Do not copy the multi-TV sample's ten-second seek binding if Calm Frames intentionally uses a different minimal interaction model. The goal is consistent, discoverable controls, not parity with every streaming app.

**Important Back caveat.** [BackHandler](https://www.developer.amazon.com/docs/react-native-vega/0.72/backhandler) listeners run in reverse registration order; returning true consumes the event. An open React Native Modal suppresses BackHandler events. If the PIN uses Modal, test its supported close callback rather than assuming a global Back listener receives the key. Remove subscriptions when their owner unmounts.

**Stop criterion.** Every intended control is reachable with D-pad/Select/Back, including rapid repeated input, and dismissing an overlay restores focus without requiring a recovery key press.

## 4. Parent PIN and accessibility: strengthen the existing promise

**Source findings.** Vega's [React Native accessibility guide](https://developer.amazon.com/docs/react-native-vega/0.72/accessibility) supports labels, roles, states, and hints; its current guidance prefers aria-* equivalents where provided. Decorative backgrounds should not generate redundant spoken descriptions. [Assistive technologies](https://www.developer.amazon.com/docs/vega/0.24/assistive-technologies-vega) describes VoiceView and remote navigation. The [sample accessibility service](https://github.com/AmazonAppDev/vega-tv-interfaces-sample/blob/main/src/services/a11y/README.md) provides reusable navigation-hint patterns and screen-reader-state handling.

**Application.** Keep the PIN description precise: an in-app parent-settings gate, unless stronger protection has actually been implemented and tested. It should not be marketed as OS parental controls, an identity check, or a tamper-proof security boundary. Test wrong PIN, incomplete entry, delete, cancel, successful entry, repeated presses, and reopening the gate. Ensure cancel never opens settings, entry is masked, and the app does not log the PIN. Use normal owner/judge setup; do not add a default PIN or include household PIN values in judge instructions.

Test the core flow with VoiceView: content selection, playback, picture-hold status, and PIN cancel/unlock. Label icon-only controls by action; expose selected/disabled state; avoid announcing a progress timer continuously. Do not make every scenic image a focus stop. Add information to the UI only when it helps someone act.

**Stop criterion.** The core flow works remotely with and without VoiceView; the PIN route does not accidentally unlock; the claims match the actual gate. No account system or expanded parental-control service is needed.

## 5. Coastal artwork: improve clarity without adding motion

**Source findings.** Amazon's [performance best practices](https://developer.amazon.com/docs/vega/0.24/best_practices) say Vega's native Image implementation already has caching. They recommend appropriately sized assets, lightweight focus handlers, listener cleanup, and avoiding redundant overdraw. The [sports sample](https://github.com/AmazonAppDev/vega-sports-app) separates palette, focus colors, gradients, and component tokens.

**Application.** Keep the existing coastal artwork and visual identity. Use a consistent text scrim and a high-contrast focus treatment that remains visible over sea, sand, and sky. Use thumbnail-sized versions in a gallery and reserve large assets for the player/hero. Avoid importing another image-cache library solely for caching, animated waves in navigation, full-screen blurred layers, or parallax. A calm interface benefits from limited movement and stable controls.

Check asset rights and retain attribution/license records. Code samples being open source does not establish rights to every image, audio recording, font, or video bundled into a new project. Record the provenance of Calm Frames assets independently.

**Stop criterion.** Text and focus are readable on every existing artwork treatment, no unnecessary image decoding or conspicuous navigation stutter is observed, and every demo asset has a documented permission basis.

## 6. Measure selectively, and distinguish simulator from hardware

**Source findings.** [Measure App KPIs](https://developer.amazon.com/docs/vega/0.24/measure-app-kpis) provides guidelines including cool-start TTFF below 1.5 seconds, warm-start TTFF below 0.5 seconds, foreground PSS below 400 MiB, background PSS below 150 MiB, and video fluidity above 99%. These are reference targets, not measured Calm Frames results. Missing KPIs or -1 values are not passes. Its fully drawn marker must reflect actual interactivity.

The [video sample build instructions](https://github.com/AmazonAppDev/vega-video-sample#build-and-run-the-app) distinguish armv7 device packages from aarch64 Mac Virtual Device packages and x86_64 Virtual Device packages. The available project context identifies a Calm Frames aarch64-debug package; that alone does not establish a hardware run, performance result, or even a successfully completed simulator test.

**Application.** First confirm the package launches and completes the core demo on the intended runtime. Record package architecture, build mode, SDK version, commit, target, test date, and actual results. If hardware/tooling is available, measure launch, enter/exit player, and repeated navigation; investigate regressions rather than optimizing every component. Keep simulator results labeled as simulator results. Do not use a phone/browser recording as proof of Fire TV execution.

**Stop criterion.** Preserve a reproducible package and an honest verification record. If physical hardware is unavailable, complete the permitted simulator demonstration and disclose the hardware-testing limitation rather than starting a port or making unsupported performance claims.

## 7. Amazon Devices Builder Tools: exact setup guidance, not an installation request

**Source findings.** The resources page's old Vega MCP link redirects to [Builder Tools setup](https://developer.amazon.com/docs/adbt/get-started). Builder Tools is separate from the Vega SDK. Documented prerequisites are Node 18+ and Vega SDK 0.22+ for Vega workflows. The documented commands are:

```sh
npx -y @amazon-devices/amazon-devices-buildertools-mcp@latest init-context
npx -y @amazon-devices/amazon-devices-buildertools-mcp@latest check-status
```

The interactive setup selects the host and context destination. Prefer reviewing merge/save choices over force-overwriting project guidance. Verify actual tool availability afterward, including documentation search/read, Perfetto analysis, hot-function analysis, and crash symbolication. Amazon discloses that documentation search queries reach Amazon services and anonymous usage telemetry is collected; the tool is not wholly offline. [Setup and privacy](https://developer.amazon.com/docs/adbt/get-started).

**Useful supported capabilities.** [Capabilities](https://developer.amazon.com/docs/adbt/capabilities) covers Vega performance, manifest checks, focus, accessibility, playback, crash analysis, and build/run. Use those to review the existing app. Do not invoke app-porting, RN-upgrade, IAP, live-TV, Matter Casting, or backend integration for this submission merely because they are available.

Suggested bounded prompts after an authorized setup:

- Review this existing Vega player for resource leaks and background/resume correctness. Keep prepared MP4 playback and existing UI. Report evidence before proposing edits.
- Audit the Library, Player, and parent PIN paths for focus loss, hidden focusable controls, and Back behavior. Keep the current navigation architecture.
- Check the current manifest and package versions against the SDK already used by this project. Do not upgrade frameworks.
- Explain the captured startup or playback trace. Separate measured results from hypotheses.

**Setup cautions.** The [troubleshooting guide](https://developer.amazon.com/docs/adbt/troubleshooting) names setup/build-and-run/media-player skills, notes globally installed skills, and documents Node v26 SQLite binding failure with Node v24 as a workaround. Do not change the app's known-good Node version merely to follow a different sample's prerequisites. The npm README and registry endpoint could not be fetched in this review. Search and opened setup-page versions also differed about host options; do not assume a particular Codex flag without checking the installed command's help and supported configuration. No setup was verified here.

**Credentials and package-registry safety.** If setup or dependency resolution requires registry authentication, the account owner should use the official supported login flow. Never paste registry tokens, .npmrc authentication contents, cookies, or credentials into chat, GitHub, a friction log, or a screenshot. An authentication failure is not a reason to bypass access controls or copy credentials between machines. The [official porting troubleshooting page](https://www.developer.amazon.com/docs/adbt/port-fire-os-app-to-vega) discusses expired registry credentials; this review does not authorize its commands or recommend a migration. Preserve the lockfile and identify the actual package/version error before changing dependencies.

**Stop criterion.** Setup is useful only once the intended host can enumerate the server tools and complete one relevant read-only diagnostic. If configuration, authentication, or compatibility becomes a detour, continue with the documented SDK workflow and direct source review. The submission does not depend on claiming MCP usage.

## 8. Documentation discrepancies worth checking, not invented project friction

- The focus overview mentions FocusManager.setFocus, while the [0.72 Focus Manager API](https://developer.amazon.com/docs/react-native-vega/0.72/focus-manager) documents focus. Check the installed API/types before using either name.
- The audio-only example on the playback-mode page instantiates AudioPlayer without importing it. Use the API reference and pinned package types rather than copying that snippet blindly.
- Media setup and general requirements list some legacy/new service names differently. Validate against the current project SDK and actual APIs used.
- Older `/latest` media URLs returned redirect shells in this review; explicit `/0.24/` pages were readable. A failed research fetch does not prove the documentation is unavailable in a browser.
- The [SDK installer guide](https://developer.amazon.com/docs/vega/0.24/install-vega-sdk) is useful for version/status verification; broad upgrade/clean-install instructions should not be applied reflexively to a working submission.

These are observed documentation issues or review limitations. Only report them as project friction if someone actually attempts the relevant task and records the steps, result, workaround, and impact. Do not claim a failed build or runtime incident that did not occur.

## 9. Narrow submission reminder

The [official rules](https://amazonappdev2026.devpost.com/rules) require a working Fire OS/Vega app shown on a Fire TV device or Fire TV/Vega simulator. The deadline is 23 October 2026 at 12:00 pm PDT, equivalent to 19:00 UTC. Aim for a public YouTube/Vimeo demo under three minutes, usable code/assets/run instructions, and accurate product feedback. Family entertainment is a priority category. Public repository licensing, private-repository judge access, participant eligibility, and any mini-challenge claims require their own final rules check. This research does not submit, share, license, or change access to the project.

**Suggested demo shape, not a rule:** briefly show the viewer/parent need, launch the actual app, select coastal content with the remote, visibly demonstrate picture holds with continuing sound, show pause/resume and the parent gate, and close on the exact tested scope. Avoid claims of clinical benefit, content safety guarantees, or platform security that have not been substantiated.

## Link coverage and deliberate exclusions

“Reviewed” means relevant content was read in this research. It does not mean every file, linked page, or video was inspected. GitHub main branches and documentation can change; record exact commits when reusing code. “Skimmed” means the landing page/README was used to decide fit.

| Resource | Coverage | Decision for Calm Frames |
| --- | --- | --- |
| [Hackathon resources](https://amazonappdev2026.devpost.com/resources) | Reviewed Fire TV and shared-tool sections | Starting map; not an exhaustive review of every track or promotional link |
| [Builder Tools setup](https://developer.amazon.com/docs/adbt/get-started) | Reviewed, including prerequisites/privacy/verification | Optional targeted diagnostic aid |
| [Builder Tools capabilities](https://developer.amazon.com/docs/adbt/capabilities) | Reviewed | Focus, media lifecycle, manifest, performance, accessibility only |
| [Builder Tools troubleshooting](https://developer.amazon.com/docs/adbt/troubleshooting) | Reviewed relevant setup sections | Use only for an actual matching failure |
| [npm package README](https://www.npmjs.com/package/@amazon-devices/amazon-devices-buildertools-mcp) | Fetch blocked/tool error | Full skill inventory and installed version not verified |
| [vega-video-sample](https://github.com/AmazonAppDev/vega-video-sample) | Reviewed README and VideoHandler | Highest-value lifecycle/control reference; do not transplant app |
| [vega-tv-interfaces-sample](https://github.com/AmazonAppDev/vega-tv-interfaces-sample) | Reviewed README, focus and accessibility service docs | Highest-value remote/focus reference |
| [multi-TV app sample](https://github.com/AmazonAppDev/react-native-multi-tv-app-sample) | Reviewed architecture and remote-control sections | Learn separation of platform adapters; do not adopt monorepo/Expo |
| [multi-TV Hello World](https://github.com/AmazonAppDev/react-native-multi-tv-helloworld) | Skimmed README | Initial scaffolding; low value for an existing app |
| [React Native Fire TV Hello World](https://github.com/AmazonAppDev/hello-world-fire-tv-react-native) | Skimmed README | Android/Expo setup does not replace Vega setup |
| [native Fire TV Hello World](https://github.com/AmazonAppDev/hello-world-fire-tv) | Skimmed README | Kotlin/Compose route outside current scope |
| [vega-audio-sample](https://github.com/AmazonAppDev/vega-audio-sample) | Skimmed playback/focus/state sections | Useful only if diagnosing existing audio behavior; no second audio engine |
| [vega-sports-app](https://github.com/AmazonAppDev/vega-sports-app) | Skimmed theme/catalog sections | Palette/token idea only; no dynamic catalog/backend |
| [Callstack TV ebook](https://www.callstack.com/ebooks/the-ultimate-guide-to-react-native-tv-development) | Landing page skimmed; full ebook not read | General companion, lower priority than matching Vega docs |
| Fire TV documentation landing link on resources | Fetch error; explicit Vega pages succeeded | Used relevant media/focus/accessibility/performance pages instead |
| [Vega forum](https://community.amazondeveloper.com/c/vega/6) and [Fire Devices forum](https://community.amazondeveloper.com/c/fire-apps/17) | Category pages opened; threads not investigated | Appropriate for a concrete unresolved issue, not evidence by themselves |
| [W3C API reference](https://developer.amazon.com/docs/vega-api/0.24/README.amazon-devices_react-native-w3cmedia) | Reviewed relevant controller/surface sections | API concepts checked; no runtime frame-capture promise established |
| [Performance best practices](https://developer.amazon.com/docs/vega/0.24/best_practices) and [KPI guide](https://developer.amazon.com/docs/vega/0.24/measure-app-kpis) | Reviewed relevant sections | Small measured fixes, honest target-vs-result distinction |
| [Improve HLS performance](https://developer.amazon.com/docs/vega/0.24/media-player-improve-hls-performance) | Opened/skimmed | Not relevant unless existing content actually uses HLS |
| [Official rules](https://amazonappdev2026.devpost.com/rules) | Relevant deadline/demo/repository sections reviewed | Separate final submission audit still required |
| Alexa+, Bee, Ring, AWS, open-source mini-challenge links; newsletters/social/video channels | Outside this technical review | Do not add integrations solely for another category |

## Final bounded completion checklist

- [ ] Record the exact working commit, package, SDK, build architecture/mode, and test target.
- [ ] Capture the real target-runtime demo of the existing complete experience.
- [ ] Pass the hold/audio, pause/resume, replay, exit/re-enter, background, and error-path tests that apply.
- [ ] Pass focus restoration, rapid remote input, hidden controls, PIN cancel/retry/unlock, and VoiceView checks.
- [ ] Preserve asset permissions and keep secrets out of all public materials.
- [ ] Clearly label untested hardware/performance behavior and unsupported features.
- [ ] Stop adding features once the core path is reproducible and submission evidence is complete.

The completion outcome is a credible, reproducible Calm Frames demo with documented limits, not a larger app or a checklist of newly installed tools.
