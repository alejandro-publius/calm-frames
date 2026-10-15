# Calm Frames: submission, judging, and scope research

Verified against official hackathon pages on **15 October 2026**. This report is research and a proposed checklist, not a completed submission or a permission change. The existing project is understood to be a **private GitHub repository**. No account, repository-access, visibility, or submission changes were made.

## Recommendation

Keep **Fire TV / Vega** as the primary entry. Put remaining effort into proving the prepared-video experience on Vega, usable parent controls, reproducible setup, a concise demo, and evidence-backed developer feedback. Treat Alexa+, Bee, and Ring as future directions unless a genuinely working integration already exists. Consider a mini-challenge only when its qualifying work is real and documented; don't retrofit claims to collect categories.

The product positioning should be precise: a prepared-media viewing experience that holds selected frames while audio continues, with parent control over the experience. Avoid implying that it transforms every streaming service, bypasses protected media, or provides clinically proven benefits.

## Verified requirements and dates

| Topic | Current verified fact | Implication for this project |
|---|---|---|
| Deadline | **23 October 2026, 12:00 noon PDT**, equivalent to **19:00 UTC**. [Submission tips](https://amazonappdev2026.devpost.com/updates/46538-strong-submission-tips) | Aim to finish submission before the final day. |
| Build window and judging | Build window: August 31, 10:15 a.m. PT through the deadline. Existing projects need significant in-window updates, explained and demonstrated. Judging: November 9–20; winners expected around December 3. [Rules](https://amazonappdev2026.devpost.com/rules) | Preserve a before/after record and commit evidence. |
| Fire TV proof | Fire TV/Vega simulators qualify; physical hardware is unnecessary. [FAQ](https://amazonappdev2026.devpost.com/details/faqs) | Desktop-browser footage alone is insufficient proof of the intended Vega experience. |
| Primary fit | Family entertainment is a prioritized Fire TV category. [Resources](https://amazonappdev2026.devpost.com/resources) | Lead with the family use case and the distinctive playback behavior. |
| Judging | Four equally weighted criteria, scored 1–5: technical implementation, design, potential impact, and idea quality. [Organizer update](https://amazonappdev2026.devpost.com/updates/46456-got-an-idea) | These are published criteria, not predicted scores for Calm Frames. |
| Availability | Judges need unrestricted, free evaluation access through judging's end; they may rely entirely on submitted media and text. [Rules](https://amazonappdev2026.devpost.com/rules) | Make the demo self-contained and the repository reproducible. |
| AWS credits | Promotional codes were exhausted October 7. [Resources](https://amazonappdev2026.devpost.com/resources) | Do not plan around the FAQ's older credit-request instructions. |

Eligibility, ownership, licensed dependencies/media, and team-representative authority still need the owner's review. Submitting accepts the official rules. [Rules](https://amazonappdev2026.devpost.com/rules)

## Private repository route

Keep the repository private. The organizer's explicit collaborator list is:

- Amazon: `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar`
- Devpost: `testing@devpost.com`

Add the individual accounts, not the `AmazonAppDev` organization. Organizer guidance says invitations must be accepted and expire after seven days; invite near submission and check acceptance/expiry. Both Amazon and Devpost need access. [Manager clarification](https://amazonappdev2026.devpost.com/forum_topics/45264-private-repo-path-amazonappdev-is-an-organization-so-it-cannot-be-added-as-a-collaborator)

The FAQ omits `chris-trag` from its abbreviated Amazon list, while the rules and manager clarification include it. Use the fuller list above. GitHub specifically is required; a GitLab link is insufficient. [FAQ](https://amazonappdev2026.devpost.com/details/faqs), [organizer update](https://amazonappdev2026.devpost.com/updates/46456-got-an-idea)

**Proposed action, requiring owner authorization:** share this named repository with those named reviewers using the least access supported by the repository type. This report does not grant that access. A public-repository licensing route exists, but changing visibility is unnecessary for this private submission.

## Track and mini-challenge decision matrix

| Option | Qualification / useful resource | Judgment for Calm Frames |
|---|---|---|
| **Fire TV** | A functioning Fire OS/Vega app; [official track guidance](https://amazonappdev2026.devpost.com/updates/46202-let-s-get-you-building). | **Keep.** Strongest existing architecture match. Demonstrate intentional held-frame behavior, uninterrupted audio, remote navigation, and parent settings. |
| **Alexa+** | Self-hosted MCP/Agent Skill or a simulated experience; gated Alexa+ developer tools cannot be obtained by hackathon participants. [FAQ](https://amazonappdev2026.devpost.com/details/faqs) The linked [MCP Apps resource](https://apps.extensions.modelcontextprotocol.io/api/) concerns interactive chat UIs; the [transport spec](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) covers Streamable HTTP. | **Defer.** Voice-based parent setup could eventually be useful, but introduces a second interaction surface and demonstration burden. Merely using an MCP coding assistant is not an Alexa+ product integration. |
| **Bee** | Actual Bee-device or Apple-Watch Bee data must power the demo. [Track guidance](https://amazonappdev2026.devpost.com/updates/46202-let-s-get-you-building) [Bee docs](https://docs.bee.computer/) expose conversation/context access through CLI, MCP, and skills. | **Defer.** Ambient family-context capture is outside the prepared-media core and creates unnecessary privacy questions. Do not collect family conversations just to add a track. |
| **Ring** | Ring API/SDK/simulator/device integration; physical hardware is optional. [Track guidance](https://amazonappdev2026.devpost.com/updates/46202-let-s-get-you-building) The [API reference](https://developer.amazon.com/docs/ring/api-documentation.html) adds account linking, credentials, and event handling. | **Defer.** Doorbell-aware playback is an adjacent feature, but does little to prove the central benefit before this deadline. |
| **AWS Builder** | Documented AWS integration; **Kiro Crew development use alone can qualify**, without a separate runtime AWS call. [Overview](https://amazonappdev2026.devpost.com/?ref_medium=homepage-recommended-hackathons) | **Conditional.** Enter if authentic qualifying work already exists. Identify exact service/tool, code or workflow evidence, and its role. Generic AI-assisted coding or use of Amazon's device MCP is not evidence of Kiro Crew use. Avoid adding a backend only for a checkbox. |
| **Open Source** | Additional new licensed open-source project or public-repository contribution made during the window; branch/fork/PR allowed, merge unnecessary. Supply contribution URL, repo URL, GitHub username, and explanation. [Overview](https://amazonappdev2026.devpost.com/?ref_medium=homepage-recommended-hackathons) | **Conditional.** A small, independently reusable timing/test utility or real upstream fix could fit. The private main repository alone does not establish this qualification. Do not publish existing code or change licenses without authorization and a rights review. |

A project can win at most one primary-track prize and one mini-challenge prize. [Rules](https://amazonappdev2026.devpost.com/rules)

## Friction log: valuable, evidence-first

The optional bonus is discretionary: Amazon's internal Stage 1 review recommends **up to 10%** for friction entries, and the Stage 2 panel applies the recommendation to the final score. Required entry content: attempted task, reproduction steps, expected/actual outcome, severity, workaround, and actionable suggestion. [Rules](https://amazonappdev2026.devpost.com/rules)

**Delivery is clarified:** a link in the submission description is acceptable; Emerson Sklar recommends keeping the log in the project repository for easier judging. This clarification does not require a separate upload or a public repository. [Submission-mechanics discussion](https://amazonappdev2026.devpost.com/forum_topics/45430-inquiry-about-submission-mechanics)

### Proposed file structure

Put a reviewable `docs/friction-log.md` in the private repository and link directly to it from the submission. Link it from the README as well. For each entry, use:

- ID and short factual title
- Product/component and exact SDK/tool version
- Date, environment, target device/simulator, app commit
- Goal and minimal reproduction
- Expected behavior, with the relevant documentation link if applicable
- Actual behavior, with a sanitized log/screenshot reference
- Severity and effect on this project's work
- Workaround attempted and whether it actually worked
- Specific improvement requested
- Current state: reproduced, resolved, or unresolved

The added version/evidence/state fields are recommendations for making the feedback credible, not additional organizer requirements.

### Candidate investigation topics, not established complaints

The following come from project-history summaries and have **not been independently reproduced in this research**. Verify them against the repository, command output, and original documentation before inclusion:

| Candidate | Evidence needed | Safe framing |
|---|---|---|
| Frame-capture denial | Exact API, target, version, error, relevant restriction, and why capture was attempted. | Identify whether the restriction belongs to Vega/media protection or to the assistant/tool environment. A safety/permission denial outside Amazon's product is not an Amazon SDK defect. Do not bypass it. |
| Browser water-effect experiment | Original goal, browser recording, measured outcome, and target-runtime status. | Record that the browser result failed to establish the intended effect. Do not claim the native Vega result is broken if it was never tested. |
| SDK/build-architecture confusion | Commands, architecture values, SDK version, exact error, and documentation pages followed. | Describe the reproducible mismatch and the clarification that would have helped. Distinguish setup error from a confirmed SDK issue. |
| Proprietary headers versus `LICENSE.TXT` | File paths and commit IDs, exact notices, and an existing upstream discussion if any. | Ask for clearer guidance on permitted reuse/distribution. Avoid declaring the code unlawful or treating a license change as a technical fix. |

Include only the strongest verified entries. One precise, actionable issue is better than several speculative complaints. Do not invent severity, reproduce private logs verbatim, or include secrets or personal data.

## Judge-facing narrative and evidence recommendations

The organizer warns that a basic video player is an obvious entry and encourages more distinctive TV interactions. [Idea guidance](https://amazonappdev2026.devpost.com/updates/46456-got-an-idea) The opportunity is therefore to make the **specific behavior and parent experience** unmistakable.

| Published criterion | Evidence I recommend showing |
|---|---|
| Technical implementation | The actual Vega build and a repeatable test demonstrating selected frames remain visible while the audio clock progresses. Exercise seeking, pause/resume, navigation away/back, and end-of-media. Clearly separate prepared assets from runtime processing. |
| Design | A complete remote-only journey: choose media, start viewing, reach parent controls, change the permitted setting, return to viewing, and recover focus predictably. |
| Potential impact | One precise household scenario and the observed inconvenience it addresses. If no user research exists, state that the value proposition is a hypothesis; don't invent testimonials, medical evidence, or adoption metrics. |
| Quality of idea | Explain why intentional temporal control is different from a conventional player or simply pausing everything. Make audio continuity audible in the demo. |

### Suggested 2:45 demo outline

1. **0:00–0:20:** Who it is for and the concrete viewing problem.
2. **0:20–0:35:** Identify the actual Vega simulator/device and launch the app.
3. **0:35–1:25:** Show a rights-cleared clip, the held-frame behavior, continuing audio, and the transition back. Explain that media is prepared if that is the implementation.
4. **1:25–2:00:** Navigate parent controls with the remote and demonstrate their real effect.
5. **2:00–2:25:** Show one edge-case recovery and a compact implementation explanation.
6. **2:25–2:45:** What changed during the hackathon, current limitations, and the next validation step.

This timing and storyboard are recommendations, not a prescribed organizer template.

## Final submission checklist

### Required deliverables

- [ ] Working project description; all source, necessary assets, and run instructions in GitHub.
- [ ] Public YouTube/Vimeo demo, under three minutes, showing the intended runtime.
- [ ] Track and mini-challenge selections; relevant mini-challenge evidence.
- [ ] In-window changes described if the project predates the event.

These deliverables are listed in the [official overview](https://amazonappdev2026.devpost.com/?ref_medium=homepage-recommended-hackathons).

- [ ] For every tool/API/SDK used: purpose, successes, problems, onboarding experience, and whether/why it would be used again. Describe AWS usage here if claiming that mini-challenge.
- [ ] Make Vega visible in the description, Built With section, and video; remove committed API keys and other secrets.

These items follow the [organizer's submission advice](https://amazonappdev2026.devpost.com/updates/46538-strong-submission-tips).

- [ ] English materials or English translations; verify media/dependency rights.
- [ ] Review eligibility and submission terms; retain evaluator access until judging ends.

See the [official rules](https://amazonappdev2026.devpost.com/rules).

### Project-specific verification before clicking Submit

- [ ] A fresh checkout builds and launches with the documented versions and architecture.
- [ ] The committed app, packaged build, written description, and recorded demo describe the same behavior.
- [ ] No browser-only experiment is presented as a verified Vega feature.
- [ ] The demo audibly establishes continuous audio during held frames.
- [ ] Remote focus, parent settings, back navigation, seeking, pause/resume, and end-of-playback have been checked on Vega.
- [ ] Prepared test media is included or deterministically obtainable, with provenance and permitted use documented.
- [ ] Private reviewer access is authorized, granted, and checked using the named route above.
- [ ] The friction log contains evidence-backed entries and has a direct submission link.
- [ ] All submitted links open in a clean session or with the judge access supplied.
- [ ] Save the submitted revision/commit identifier and submission confirmation for later comparison.

## Remaining questions worth resolving

1. Has a final Vega build actually demonstrated the claimed frame-hold/audio behavior, or is the current evidence still limited to browser experiments?
2. Which significant features were completed inside the build window?
3. Does authentic AWS/Kiro Crew usage or a separate public contribution already exist?
4. Are reviewer sharing, final video publication, and the Devpost submission authorized and ready?

If an organizer answer is needed, the next listed office hour is **October 19, 9:00–10:00 a.m. PT / 16:00–17:00 UTC**. [Office-hours announcement](https://amazonappdev2026.devpost.com/updates/46771-office-hours-schedule)

## Link coverage inventory

Status meanings: **Reviewed** = relevant content read; **Skimmed** = selected sections inspected for scope; **Not needed** = intentionally excluded from this pass; **Recovered** = first fetch failed but alternate official URL worked. This is not a claim that every linked document or repository file was reviewed.

| Resource | Status | Scope / result |
|---|---|---|
| [Resources](https://amazonappdev2026.devpost.com/resources) | Reviewed | Track links, mini-challenges, exhausted-credit notice. |
| [Rules](https://amazonappdev2026.devpost.com/rules) | Reviewed | Requirements, judging, access, timeline, mini-challenges, friction bonus. |
| [FAQ](https://amazonappdev2026.devpost.com/details/faqs) | Reviewed | Simulator allowance, private repository guidance, Alexa+ gating, Bee hardware, media. |
| [Overview](https://amazonappdev2026.devpost.com/?ref_medium=homepage-recommended-hackathons) | Recovered; reviewed | Bare root fetch returned an internal error; official query-linked version opened. |
| [Updates](https://amazonappdev2026.devpost.com/updates) | Reviewed | Followed the submission-tips, idea, build-start, and office-hours articles. |
| [Submission mechanics](https://amazonappdev2026.devpost.com/forum_topics/45430-inquiry-about-submission-mechanics) | Reviewed | Direct friction-log location clarification. |
| [Private-repository clarification](https://amazonappdev2026.devpost.com/forum_topics/45264-private-repo-path-amazonappdev-is-an-organization-so-it-cannot-be-added-as-a-collaborator) | Reviewed | Named reviewer accounts and invitation expiry. |
| [MCP Apps / Build with Agent Skills](https://apps.extensions.modelcontextprotocol.io/api/) | Reviewed | Linked resource is MCP Apps with Agent Skills scaffolding guidance. |
| [Streamable HTTP specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | Reviewed | Transport and security sections; relevant only if adding an MCP product surface. |
| [Bee docs](https://docs.bee.computer/) | Reviewed | Context-data access and prerequisites. |
| [Bee CLI](https://github.com/bee-computer/bee-cli), [Bee Skill](https://github.com/bee-computer/bee-skill) | Skimmed | README prerequisites and capabilities; no installation or authentication. |
| [Ring developer portal/getting started](https://developer.amazon.com/docs/ring/get-started.html) | Skimmed | App lifecycle and credentials; no account setup. |
| [Ring API](https://developer.amazon.com/docs/ring/api-documentation.html) | Skimmed | Authentication and account-linking burden. Resources page's “Get started with Ring” and “Ring API reference” resolve to this API document. |
| [Ring UX design guide](https://developer.amazon.com/docs/ring/ux-design-guide.html) | Skimmed | Data-privacy/deletion sections. |
| [Ring Hello World](https://github.com/AmazonAppDev/ring-api-helloworld) | Skimmed | Repository landing/README surface; no implementation audit. |
| [AWS Builder Center](https://builder.aws.com/), [Learn](https://builder.aws.com/learn) | Reviewed landing pages | Learning/service-discovery hubs; no account or paid-service setup. |
| Fire TV sample repositories, device MCP, Vega technical docs | Not needed in this pass | Covered by the parallel Fire TV technical review. |
| Ring Appstore gallery/community, broad Amazon forum, social/video/newsletter links | Not needed | No bearing on immediate submission compliance; no subscriptions or posts. |
| Hacktoberfest | Not needed | Separate program; no assumption that hackathon work qualifies there. |

No unresolved fetch block prevents the findings above. The signed-in Devpost form and actual private repository reviewer permissions were not inspected in this public-source research.
