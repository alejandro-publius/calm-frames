# The documents

Every file and folder in `docs/`, in two groups. **For readers** is what the
project is, how it keeps people safe, and how to judge it or build on it.
**Project records** are the working documents kept for the record: the status
log, the decisions, the gates, the prompts the coding agents were given, the
reviews and the bills of materials.

If you are new here, read the [repository README](../README.md) first, then
[SAFETY.md](SAFETY.md) before you run anything. For what is true today, the
canonical submission lists are
[submission/FINAL_REQUIREMENTS_CHECKLIST.md](submission/FINAL_REQUIREMENTS_CHECKLIST.md)
and [submission/DEMO_RUN_OF_SHOW.md](submission/DEMO_RUN_OF_SHOW.md), and
[STATUS.md](STATUS.md) section 2 is the dated engineering list.

**Why the working records are public.** The project's rule is that the
reasoning behind every call stays in the repository: each decision with its
date, why and what it cost, each gate with its evidence, and the prompts the
agents worked from. So the agent prompts, the logs and the reviews are kept
rather than tidied away. They record how the work was done, not what the
product is, and an older record keeps the words it had on its date, so read
the date before relying on it.

## For readers

### Safety and trust

| File | What is in it |
|---|---|
| [SAFETY.md](SAFETY.md) | The safety rules for anyone working here (hazard files, conformance clips, filming, never playing flashing content unfiltered), how the repository enforces them, and the approved wording. Read it before running anything. |
| [SECURITY.md](SECURITY.md) | The secrets the project has and where they live, the threat model, rotating and revoking the signing key, secret scanning, every dependency exception, AWS, what has never been run, and how to report a problem. |
| [SPEC_SOURCES.md](SPEC_SOURCES.md) | A pointer to [`flashmap/docs/SPEC_SOURCES.md`](../flashmap/docs/SPEC_SOURCES.md), the only place a threshold may come from, with the quoted spec text and links. |
| [SIDECAR_SPEC.md](SIDECAR_SPEC.md) | The flash map format, version 1: the signed JSON contract between flashmap and everything that reads it, and the signed registry of maps. |
| [AMAZON_SAMPLE_LICENSE_REVIEW.md](AMAZON_SAMPLE_LICENSE_REVIEW.md) | What was checked on Oct 10 about the proprietary notice inside Amazon's MIT-0 video sample, and the clarification request that has not been sent yet. |

### Evaluation and evidence

| File | What is in it |
|---|---|
| [evidence/README.md](evidence/README.md) | The evidence index: who the product is for, what is and is not supported, the architecture in one paragraph, the checks that have run with their commands, the detector baseline and candidate, provenance and licences, the exact revision and what is installed, and the four kinds of evidence kept apart. |
| [evidence/usability-checklist-2026-10-16.md](evidence/usability-checklist-2026-10-16.md) | The sheet for a few people trying the Acadia journey with ordinary footage. Not run yet; no participants or results in it. |
| [EVAL_PLAN.md](EVAL_PLAN.md) | The evaluation plan, committed on Sep 17 before any real clip was labelled, with every later change logged as a deviation at the bottom. |
| [VALIDATION.md](VALIDATION.md) | Outreach, and what anyone outside the project has said about it. Nothing has been collected yet, and the page says so. |
| [SCREEN_TEST_PROTOCOL.md](SCREEN_TEST_PROTOCOL.md) | How to film and measure the screen-level test on a physical TV. Never run: physical hardware has been outside this submission's scope since Oct 9. |

The measured results themselves are in `results/`, and the conformance write-up
is [`eval/EVAL_RESULTS.md`](../eval/EVAL_RESULTS.md).

### Judging and the submission

| File | What is in it |
|---|---|
| [RUBRIC.md](RUBRIC.md) | The hackathon's dates, Stage One, the four criteria, the mini challenges and the form, quoted from its own pages rather than remembered. |
| [SUBMISSION.md](SUBMISSION.md) | The older field-by-field Devpost draft, superseded for the description by [submission/DEVPOST_DRAFT.md](submission/DEVPOST_DRAFT.md). Section 15 still holds the entrant details marked NEEDS ALEX. |
| [SUBMISSION_COPY.md](SUBMISSION_COPY.md) | The shorter October 15 project story, superseded by [submission/DEVPOST_DRAFT.md](submission/DEVPOST_DRAFT.md) and kept as a record. |
| [../FINAL_HANDOFF.md](../FINAL_HANDOFF.md) | The handoff for the final candidate: branch, package hash and receipt, what changed and which checks passed, the native acceptance checklist and the owner's remaining actions. |
| [submission/README.md](submission/README.md) | The submission packet index: the canonical checklist, description, demo script, quickstart and open decisions, with superseded drafts marked. |
| [submission/FINAL_REQUIREMENTS_CHECKLIST.md](submission/FINAL_REQUIREMENTS_CHECKLIST.md) | The canonical checklist: every mandatory rule, read live on October 17, mapped to evidence and marked done, missing or unverified. |
| [submission/DEMO_RUN_OF_SHOW.md](submission/DEMO_RUN_OF_SHOW.md) | The canonical demo script, about 90 seconds, with each shot's purpose, narration, action and evidence. Not recorded. |
| [submission/CHECKLIST.md](submission/CHECKLIST.md) | The October 15 readiness matrix, superseded by the canonical checklist and kept as a record. |
| [submission/DEVPOST_DRAFT.md](submission/DEVPOST_DRAFT.md) | The project description to paste once the pending rows close. |
| [submission/DEMO_SCRIPT.md](submission/DEMO_SCRIPT.md) | The October 15 plan of 2:40, superseded by the canonical demo script and kept as a record. |
| [submission/DEMO_SCRIPT_ACADIA_2026-10-16.md](submission/DEMO_SCRIPT_ACADIA_2026-10-16.md) | The October 16 Acadia draft, superseded by the canonical demo script and kept as a record. |
| [submission/REVIEWER_QUICKSTART.md](submission/REVIEWER_QUICKSTART.md) | Setup, run and demo steps for a judge, with unexecuted commands marked. |
| [submission/OPEN_DECISIONS.md](submission/OPEN_DECISIONS.md) | What is pending and what only Alex can decide, mandatory first. |
| [CLAUDE_FINISH_PROMPT.md](CLAUDE_FINISH_PROMPT.md) | A bounded Mac finishing task for Claude Code or a local Codex session, with API billing verification and milestone pushes. |
| [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) | The October 13 recording plan, superseded by [submission/DEMO_RUN_OF_SHOW.md](submission/DEMO_RUN_OF_SHOW.md) and kept as a record. |
| [SHOT_MANIFEST.md](SHOT_MANIFEST.md) | The shots in the Oct 10 recording of the earlier native build, with their source hashes, and what has to be captured again. |
| [FEEDBACK.md](FEEDBACK.md) | Amazon's five product feedback questions, answered once for every tool the project used, and the feature requests. |
| [FRICTION_LOG.md](FRICTION_LOG.md) | Developer friction in Amazon's six fields, every entry traceable to a commit, a log or a results file. |
| [OPEN_SOURCE_PR.md](OPEN_SOURCE_PR.md) | The upstream contribution to Amazon's vega-video-sample: what the two patches fix, how they were tested, and the steps still to take. |

### Building on it

| File | What is in it |
|---|---|
| [INTEGRATION_DIFF.md](INTEGRATION_DIFF.md) | The whole change that adds the flash guard hook to a clean vega-video-sample checkout, generated by a script rather than written by hand. |
| [ENVIRONMENT.md](ENVIRONMENT.md) | The build machine and every pinned tool version, the three ffmpegs, and the Python setup for a fresh reviewer checkout. |
| [PREPARATION_RECOVERY.md](PREPARATION_RECOVERY.md) | What can interrupt or damage title preparation, how the ledger, publication and receipts recover from it, and the one command that reproduces the evidence. |
| [RELEASE_READINESS.md](RELEASE_READINESS.md) | The integrated recovery and Playback Proof branch: each claim with its evidence and the command that reproduces it, what the virtual device showed, what was fixed during validation, what is not established, and the rollback. |
| [PRODUCT_EVIDENCE.md](PRODUCT_EVIDENCE.md) | From a video to the TV in four steps, and for each capability whether it is implemented, tested, observed on the device or not verified, with measured preparation times. |
| [RELEASE.md](RELEASE.md) | How to prepare the simulator package and the flashmap PyPI release. No final release has been published. |

### Design and brand

| Path | What is in it |
|---|---|
| [design/README.md](design/README.md) | The design page, the one to read first: identity, palette, contrast, type, spacing, focus, motion, sound and copy, copied from `calmStyles.ts` and held to it by `eval/tests/test_design_page.py`. |
| [design/](design/) | The rest of the TV design record: its brief, copy guide, tokens, reviews and renders, listed below. |
| [design/POLISH_REVIEW.md](design/POLISH_REVIEW.md) | The visual refinement of the native screens, with the before and after renders in `design/polish/`. |
| [design/SEAMLESS_REVIEW.md](design/SEAMLESS_REVIEW.md) | The Oct 11 review of the viewing experience and the public design reference it studied, with renders in `design/seamless/`. |
| [design/NATIVE_IMPLEMENTATION.md](design/NATIVE_IMPLEMENTATION.md) | How the approved TV design went into the native app, and which changes since have not been built or seen on Vega. |
| [design/IMPLEMENTATION_BRIEF.md](design/IMPLEMENTATION_BRIEF.md) | The Oct 10 visual direction for the TV app: type, composition and remote control clarity. |
| [design/COPY_GUIDE.md](design/COPY_GUIDE.md) | The voice and wording rules for interface copy. |
| [design/tokens.json](design/tokens.json) | Design tokens for the TV canvas. The palette the app draws is defined in `app/src/calmframes/calmStyles.ts`, and the file's own status line says how the two relate. |
| `design/assets/` | The Inter variable font the design references use, with its OFL licence beside it. |
| `design/polish/`, `design/seamless/` | Browser renders of the app's own React Native tree. Review aids, not Vega screenshots; the two reviews say how they were made. |
| [brand/](brand/README.md) | The Calm Frames mark and the brand line, how the icon files are made, and the app store and Fire TV icons and previews. |

## Project records

| Path | What is in it |
|---|---|
| [STATUS.md](STATUS.md) | Where things stand. Section 0 is the dated history, newest first; section 2 is the dated list of what remains. |
| [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) | The October 13 to 15 completion checklist, kept as a record. The submission checklist is [submission/FINAL_REQUIREMENTS_CHECKLIST.md](submission/FINAL_REQUIREMENTS_CHECKLIST.md). |
| [MAC_FINISH.md](MAC_FINISH.md) | The handoff for the Mac: rebuild, observe and record the current source on the Vega Virtual Device. |
| [DECISIONS.md](DECISIONS.md) | Every call made, with its date, why and what it cost. Newest at the bottom. |
| [GATES.md](GATES.md) | Every gate, human checkpoint and kill rule, with the date and the evidence for each result. |
| [PLAN.md](PLAN.md) | The short version of the plan with where each phase stood, kept as it was under a dated Oct 11 banner. |
| [PRIOR_WORK.md](PRIOR_WORK.md) | Everything reused from before the submission period, as the rules require, with its origin, date and licence. |
| [BUILD_PROMPT.md](BUILD_PROMPT.md) | Agent prompt: the full build prompt the coding agent worked from, with the phases, gates, kill rules and cut list. |
| [CONTINUATION_PROMPT.md](CONTINUATION_PROMPT.md) | Agent prompt: the reusable prompt for a long improvement session, within that session's own budget. |
| [HACKATHON_REVIEW.md](HACKATHON_REVIEW.md) | A subjective assessment against the rules on Oct 2. Not an official score. |
| [MOCK_JUDGE_1.md](MOCK_JUDGE_1.md), [MOCK_JUDGE_2.md](MOCK_JUDGE_2.md) | Two independent agents judging a fresh clone against RUBRIC.md on Sep 17, their verdicts kept as given, apart from their headers and one marked word in judge 2. |
| [MOCK_JUDGE_3.md](MOCK_JUDGE_3.md) | Four independent agents, one per rubric lens, judging a fresh clone on Oct 11, and what was fixed afterwards. |
| [DUSK_LANTERN_2026-10-14.md](DUSK_LANTERN_2026-10-14.md) | The finished Home and Details composition of Oct 14: what a family sees, the supported-content scope, matched before and after renders, build and install steps, and credits. |
| [VERIFY_PASS_1.md](VERIFY_PASS_1.md) | The verifier lane's Sep 17 read of family profiles and the map registry. |
| [VERIFY_PASS_2.md](VERIFY_PASS_2.md) | The verifier lane's Sep 17 read of pattern segments through the hide plan and verify. |
| [SBOM.app.cdx.json](SBOM.app.cdx.json), [SBOM.cdk.cdx.json](SBOM.cdk.cdx.json), [SBOM.ingest.cdx.json](SBOM.ingest.cdx.json) | CycloneDX bills of materials for the Vega app, the CDK stack and the ingest container. `make sbom` writes them and the Audit workflow fails when one is stale. |
| [outreach/](outreach/README.md) | Drafts for Alex to send or post: three emails asking for feedback on wording, a Discord check-in and questions for the organizers. Nothing has been sent. |
| `upstream-pr/` | The two patch files for vega-video-sample that OPEN_SOURCE_PR.md describes, still carrying placeholder author details. |

## Outside docs/

| Path | What is in it |
|---|---|
| [CLAUDE.md](../CLAUDE.md) | The rules every working session follows, and where things stand at the top. |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Setup, the checks, the rules in short, adding a title, and reporting a security problem. |
| [CHANGELOG.md](../CHANGELOG.md) | What changed, by date, on main and on the review branch. |
| [WRITEUP.md](../WRITEUP.md) | The one-page account of why the system is built the way it is, and its limits. |
| [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | How people here treat each other, and how to report a problem. |
| [`flashmap/README.md`](../flashmap/README.md) | The analyzer on its own: install, the CLI and the GitHub Action. |
| [`hook/README.md`](../hook/README.md) | The flash guard hook for a Vega video app. |
| [`pipeline/LOCAL_LIBRARY.md`](../pipeline/LOCAL_LIBRARY.md) | Preparing a checked local library and packaging it into the app. |
| [`pipeline/infra/README.md`](../pipeline/infra/README.md) | The CDK stack: the Oct 9 deploy, what it taught, and how to take it down. |
| [`media/LICENSES.csv`](../media/LICENSES.csv) | The licence ledger: source, licence, credit line, hash, duration and resolution for every clip. |
