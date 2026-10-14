# Submission readiness checklist

Prepared Oct 14, 2026 on `claude/submission-packet-2026-10-14` and reconciled
later that day to the working integration baseline
`codex/core-reliability-2026-10-14` at `cfddc4adb8bcdd17a861e6489f5fb50693c282d3`,
which is a candidate, not the final judged release. Nothing in this packet is
submitted, published, uploaded or recorded, and recording is not yet authorized.

Statuses. **Verified** means the evidence named in the row was read in this
session. **Missing** means the artifact does not exist yet. **Pending** means
the work is planned and not finished: final visual approval, native validation,
final release selection, reviewer access and the video are all pending.
**Owner decision** means only Alex can settle it. A row is never marked verified from a plan, a
statement of intent or an earlier build's evidence standing in for the current one.

## The packet

| File | What it is |
|---|---|
| [CHECKLIST.md](CHECKLIST.md) | This file: the official requirements against the repository |
| [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md) | The project description, ready to paste once the open rows close |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | A 2:40 narration and shot plan for the native video |
| [REVIEWER_QUICKSTART.md](REVIEWER_QUICKSTART.md) | Setup, run and demo steps for a judge |
| [OPEN_DECISIONS.md](OPEN_DECISIONS.md) | The blockers and decisions, by submission impact |

The field-by-field draft with the longer history stays in
[../SUBMISSION.md](../SUBMISSION.md). [README.md](README.md) in this folder still
describes the Oct 13 ZIP and was not changed.

## Mandatory blockers and optional work

**Mandatory for the submission, all pending:**

- Final visual approval of the single 2D composition with dimensional artwork,
  then applying it; the native walkthrough and the video wait for it.
- Native validation of the final build on the Vega Virtual Device (row 4).
- Final release selection: the candidate `cfddc4a` is the working baseline,
  not the judged release (row 10).
- Reviewer access to the repository, public or private (row 11).
- The demonstration video; recording is not yet authorized (rows 6, 12, 13).
- The entrant details and licence items only Alex can settle (rows 1, 8, 23).

**Optional, does not block the submission:** the Open Source mini challenge
(row 18) and the AWS Builder mini challenge (row 17).

## Sources

- **Official rules:** <https://amazonappdev2026.devpost.com/rules>, read in full on
  Oct 14, 2026. The server answers plain fetches with HTTP 403, so the page was
  loaded in a headless browser and its text saved. Quotations below replace the
  page's dash characters with words, because this repository's style check
  refuses dashes; nothing else in a quotation is changed.
- **Not readable here:** the overview page (<https://amazonappdev2026.devpost.com/>)
  answered 403 to every attempt, and the live "Enter a Submission" form needs a
  Devpost login. Track descriptions come from the rules page. Field names and
  character limits on the form remain unchecked.
- **Repository state:** `gh repo view`, `gh pr view 1`, `gh run list` and the
  receipts under `results/`, all read on Oct 14.

## Dates and time zone (rules, section 1)

| What | When |
|---|---|
| Submission Period | Mon Aug 31, 2026, 10:15 am Pacific Time, to **Fri Oct 23, 2026, 12:00 pm Pacific Time**. The page header reads "Deadline: Oct 23, 2026 @ 12:00pm PDT" |
| Judging Period | Mon Nov 9, 2026, 12:00 pm PT, to Fri Nov 20, 2026, 12:00 pm PT |
| Winners announced | On or around Thu Dec 3, 2026, 12:00 pm PT |
| Project's own target | Submit Thu Oct 22, a day early on purpose ([../SUBMISSION.md](../SUBMISSION.md)) |
| Early eligibility check (Oct 16) and office hours (Oct 19) | Recorded in [../SUBMISSION.md](../SUBMISSION.md) from hackathon announcements; not re-read in this session |

After the Submission Period ends no change to a submission is allowed, except
removals the Sponsor permits (rules, section 5).

## Tracks and mini challenges

| Entry | Rule text (rules, Project Requirements) | Fit | Status |
|---|---|---|---|
| **Fire TV, primary track** | "Eligible projects for this category have to launch a demo-ready app that works on Fire OS or Vega OS. Priority categories: AI-enhanced viewing, sports, fitness, family entertainment, multi-modal UX, and computer vision." | A Vega OS app; family entertainment and multi-modal UX are the two priority categories it fits | **Verified** as the chosen track ([../SUBMISSION.md](../SUBMISSION.md) section 4). The demo-ready app requirement is open; see rows 4 and 6 below |
| **Open Source, mini challenge** | "Create a new, additional open-source project or contribute to an existing public repository during the hackathon window, alongside a primary track submission. Contributions can be a new repo (with open-source license), a branch, a fork, or a pull request. PRs do not need to be merged; share your forked version if unmerged. Required: contribution URL, project repository URL, GitHub username, and a description of what you did, how it works, and why it matters." | Candidate contributions: the prepared upstream fix for `AmazonAppDev/vega-video-sample` ([../OPEN_SOURCE_PR.md](../OPEN_SOURCE_PR.md)), and the repository's own Apache-2.0 packages (flashmap, the Action, the sidecar specification, the hook) | **Owner decision.** No fork or pull request exists and the repository is private, so there is no contribution URL today |
| **AWS Builder, mini challenge** | "Any primary track project that incorporates AWS services (i.e. Amazon Bedrock, AgentCore, Strands SDK, Kiro Crew, SageMaker, etc.) with documented integrations." The rules add that Kiro Crew qualifies on its own as a development tool; it was not used here | A CDK stack deployed once on Oct 9, 2026, with the integration documented in [../SUBMISSION.md](../SUBMISSION.md) sections 10.2 and 11 and [../FEEDBACK.md](../FEEDBACK.md) sections 8 to 16. The TV app does not call AWS | **Owner decision** whether to enter. The documented integration exists ([`results/aws_deploy_2026-10-09.json`](../../results/aws_deploy_2026-10-09.json)) |

Prize limits (rules, section 8): a project can win one track prize and one mini
challenge prize. Fire TV first place is 25,000 US dollars cash and 15,000 in AWS
credits; each mini challenge is 5,000 cash and 5,000 in credits.

## Requirements

| # | Requirement, from the rules | Status | Evidence, or what is missing |
|---|---|---|---|
| 1 | **Eligibility** (section 3): individuals at the age of majority where they reside; not a resident of a place where participation is prohibited; not an employee, agent or household member of the Sponsor or Administrator; not a judge | **Owner decision** | [../SUBMISSION.md](../SUBMISSION.md) section 15 records the entrant as Alex Velazquez, United States, solo. Eligibility confirmation and contact email are marked NEEDS ALEX there |
| 2 | **Register on Devpost** by clicking "Join Hackathon" (section 4) | **Owner decision** | No record of a Devpost registration in the repository |
| 3 | **Fire TV developer account** (section 4, How To Enter) | **Verified by owner statement** | [../SUBMISSION.md](../SUBMISSION.md) section 15: created and identity-verified, as confirmed by Alex on Oct 9. Not independently inspectable here |
| 4 | **Demo-ready app on Fire OS or Vega OS** (Project Requirements, Fire TV) | **Verified for earlier builds; Pending for the candidate** | Installed and observed on the Vega Virtual Device: source `73fbbed` on Oct 9 and 10 ([`results/redesign_validation_2026-10-10.json`](../../results/redesign_validation_2026-10-10.json)), source `06190c7` on Oct 13 ([`results/polish_native_validation.json`](../../results/polish_native_validation.json)), sources `dba88d5` and `00905510` on Oct 14 ([`results/native-observation-2026-10-14/receipt.json`](../../results/native-observation-2026-10-14/receipt.json), [`results/native-checkpoint-2026-10-14/receipt.json`](../../results/native-checkpoint-2026-10-14/receipt.json)). The Oct 14 source `af192ac` has two built packages, neither installed or launched ([`results/concise-copy-2026-10-14/ARTIFACT_MANIFEST.json`](../../results/concise-copy-2026-10-14/ARTIFACT_MANIFEST.json), `native_validation_performed: false`). The candidate `cfddc4a` has an aarch64 Debug package built from it with its 723 recorded source inputs verified and `native_validation_performed: false`, as build output outside git in the reliability worktree (`build/release/core-reliability-cfddc4a-2026-10-14/PREPARATION.json`, package SHA-256 `e315e16d19172a5aadc1bfa8a9364bcf9205d51870ec610b92eb01ea9d2841dd`); it has not been installed or run |
| 5 | **Clear setup and run instructions in the repository** (Functionality) | **Verified present; execution on a clean machine unverified** | [README.md](../../README.md) "Install and run" and "Run the checks", [../MAC_FINISH.md](../MAC_FINISH.md), [REVIEWER_QUICKSTART.md](REVIEWER_QUICKSTART.md). No clean-checkout run was performed in this session |
| 6 | **The project shown functioning in the demonstration video** (Functionality, Platforms) | **Missing, pending** | No video of the candidate, and recording is not yet authorized. An earlier English cut of the Oct 10 build (`73fbbed`) exists locally at `build/submission-redesign/Calm-Frames-demo-English.mp4`, <!--n results/redesign_video_check.json:duration_s -->156.021<!--/n--> seconds, never uploaded ([../SUBMISSION.md](../SUBMISSION.md) section 7). [DEMO_SCRIPT.md](DEMO_SCRIPT.md) is the plan |
| 7 | **New or significantly updated after Aug 31, 2026**, with the update explained (New & Existing) | **Verified** | First commit `387c173` on Sep 17, 2026 (`git log --reverse`), inside the Submission Period. [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md) says so |
| 8 | **Third-party SDKs, APIs and data used under their terms** (Third Party Integrations) | **Owner decision** | The Amazon sample's root licence is MIT-0 while its player wrapper and Shaka archive carry a proprietary notice; the clarification request in [../AMAZON_SAMPLE_LICENSE_REVIEW.md](../AMAZON_SAMPLE_LICENSE_REVIEW.md) is unsent. Fonts, media and generated artwork are in the release and licence lane another agent owns; the ledger is [`media/LICENSES.csv`](../../media/LICENSES.csv). `app/assets/image/tv/harbor-illustrated.png` is ledgered in this packet's reconciliation commit as a pixel-identical render of our own `app/assets/brand/tv/harbor.svg`. The Amazon sample notices remain explicitly unresolved: [`results/release-pin-license-review-2026-10-14.json`](../../results/release-pin-license-review-2026-10-14.json) classifies them as an unresolved scope of permission, not a resolved attribution |
| 9 | **Text description of features and functionality** (Submission Requirements) | **Verified draft; not pasted** | [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md), with the longer [../SUBMISSION.md](../SUBMISSION.md) and [../SUBMISSION_COPY.md](../SUBMISSION_COPY.md) |
| 10 | **GitHub repository URL with all source, assets and instructions** (Submission Requirements) | **Verified present; Owner decision on the judged code line** | <https://github.com/alejandro-publius/calm-frames>. Hazardous media under `media/` is excluded by design; only hashes and licence rows are committed, and the README says so. `main` is at `7110893` and has not moved since Sep 20; draft PR #1 from `codex/signed-scene-holds-2026-09-29` (`4c9996d`) is open and mergeable; the working integration baseline `codex/core-reliability-2026-10-14` at `cfddc4a` descends from both and is a candidate only. Final release selection is pending ([OPEN_DECISIONS.md](OPEN_DECISIONS.md)) |
| 11 | **Repository public with an open source licence visible in About, or private and shared** with `testing@devpost.com` and `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth`, `emersonsklar` (Submission Requirements; Sept 16 update "Hackathon submission requirements: Code repository") | **Pending, owner decision** | Today the repository is private (`gh repo view`: `PRIVATE`). GitHub already detects `Apache License 2.0` from the root `LICENSE`. The About description, website and topics are empty. The collaborator list was not read. The project's plan is to go public on Oct 21 after merging to `main` |
| 12 | **Fire TV: any framework; the project runs on Fire OS or Vega OS; the video shows it on an actual Fire TV device or the Fire TV/Vega simulator** (Submission Requirements) | **Verified for the platform; video pending** | React Native 0.83 on Vega SDK 0.24.9914, package `io.github.alejandropublius.calmframes`, installed on the Vega Virtual Device in the receipts of row 4. The video is row 6 |
| 13 | **Demonstration video**: under three minutes, footage on the device it was built for, public on YouTube or Vimeo, link on the form, no third-party trademarks or copyrighted music or material without permission | **Missing, pending; recording not yet authorized** | [DEMO_SCRIPT.md](DEMO_SCRIPT.md) targets 2:40. The project's own gate refuses a file of 179 seconds or longer and runs the flash check on the finished file (`eval/check_video.sh`). Narration in the earlier cut was synthetic macOS speech, disclosed on screen |
| 14 | **Product Feedback for each tool, API or SDK used**: which and for what; what worked well; what needs work; onboarding; build with it again and why | **Verified draft; not pasted** | [../FEEDBACK.md](../FEEDBACK.md): eighteen tools, each section answering the five questions, with an "At a glance" table |
| 15 | **Identify the primary track** | **Verified** | Fire TV ([../SUBMISSION.md](../SUBMISSION.md) section 4) |
| 16 | **Identify the mini challenges** | **Owner decision** | Open Source and AWS Builder are drafted; see the tracks table |
| 17 | **AWS Builder: describe which AWS services were used and how, inside the Product Feedback answer** | **Verified draft** | [../SUBMISSION.md](../SUBMISSION.md) section 10.2 table, built from [`results/aws_deploy_2026-10-09.json`](../../results/aws_deploy_2026-10-09.json): <!--n results/aws_deploy_2026-10-09.json:stack.resources_total -->42<!--/n--> resources, <!--n results/aws_deploy_2026-10-09.json:stack.nat_gateways -->0<!--/n--> NAT gateways, one refused unsigned run and one signed publication. The `Project` cost allocation tag was inactive on Oct 9 |
| 18 | **Open Source: contribution URL, project repository URL, GitHub username, description** | **Missing** | No fork or pull request has been opened ([../OPEN_SOURCE_PR.md](../OPEN_SOURCE_PR.md)); the GitHub username to credit is marked NEEDS ALEX; the description is drafted in [../SUBMISSION.md](../SUBMISSION.md) section 12.4 |
| 19 | **Optional feature requests** with priority ratings | **Verified draft** | [../FEEDBACK.md](../FEEDBACK.md), "Feature requests", each marked Critical, Important or Nice-to-have |
| 20 | **Optional friction log entries** in the six fields; up to a ten percent bonus at Stage One | **Verified draft; publication needs owner approval** | [../FRICTION_LOG.md](../FRICTION_LOG.md): task, steps, expected versus actual, severity, workaround, suggestion, with the evidence table at the end. Alex has not yet confirmed publishing it as written ([../SUBMISSION.md](../SUBMISSION.md) section 14) |
| 21 | **Testing**: accessible to judges through the repository and the video; credentials if private; free of charge until the Judging Period ends | **Owner decision** (access route, row 11) | The app needs no login. The parent area uses a PIN the installer chooses on first run; there is no preset PIN in the package ([README.md](../../README.md), "The parent area and the demo PIN") |
| 22 | **English** materials | **Verified** | All documents, captions and the earlier narration are in English |
| 23 | **Original work, solely owned, no infringement; open source used under its licences** (Submission ownership, Intellectual Property) | **Owner decision** | Same items as row 8, plus the CC0 dedication of the generated Harbor artwork that the completion checklist asks Alex to confirm on Oct 21 |
| 24 | **Judging** (section 6): Stage One pass or fail on viability; Stage Two four equally weighted criteria, Tech Implementation, Design, Potential Impact, Quality of the Idea; friction log bonus | Informational | The description and video are written to those four headings |

## Repository checks that bear on the above

| Check | State on Oct 14 | Evidence |
|---|---|---|
| Hosted CI on the shared PR branch | **Red.** On `4c9996d` (Oct 13) the `Vega app` job failed; `Python packages`, `Secret scan`, `Mutation gate, property tests and the map fuzz corpus`, `The app's own UI passes flashmap` and `Published numbers match results` passed, and Audit passed in every job | `gh run list`, `gh run view`. That run is of the shared PR branch head only; it predates the candidate `cfddc4a` and describes nothing about it |
| Hosted CI on the candidate | **None.** CI runs on pushes to `main`, on pull requests and by hand; `codex/core-reliability-2026-10-14` has no pull request, so the candidate has no hosted run. Its own bounded checks are in [`results/core-reliability-2026-10-14.json`](../../results/core-reliability-2026-10-14.json) and [`results/release-pin-license-review-2026-10-14.json`](../../results/release-pin-license-review-2026-10-14.json) | `.github/workflows/ci.yml` |
| Final visual approval | **Pending.** The single 2D composition with dimensional artwork is to be approved and applied before the final device walkthrough | Alex's direction of Oct 14 |
| Earlier green heads | Oct 11 heads green in every job, recorded in `results/github_push_2026-10-11*.json` | [../STATUS.md](../STATUS.md) section 0 |
| GitHub draft release | One private draft, "Calm Frames approved redesign review, October 10, 2026", tag `review-redesign-2026-10-10`, holding the Oct 10 build's assets | `gh release list` |
| Gallery image | Proposed: `docs/brand/firetv-app-icon-1280x720.png` | [../SUBMISSION.md](../SUBMISSION.md) section 7a; form size limits unread |

## Not checked in this session

The live form, the repository's collaborator list, a clean-machine run of the
instructions, the overview page, and any Devpost registration or account state.
