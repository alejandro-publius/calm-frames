# Calm Frames: latest-design and submission handoff

Prepared 2026-10-15 UTC at the owner's request. This document records work to perform; it does not assert that unverified features or local changes are already complete.

## Status update: 2026-10-15 05:35 UTC

The missing app changes described below have now been pushed. The current verified application branch is [claude/final-candidate-2026-10-14](https://github.com/alejandro-publius/calm-frames/tree/claude/final-candidate-2026-10-14), head `a3368a9e4dbfde52153d586d97d8c6da5ab5c8fd`. It includes the approved coastal lineage, Home simplification, practice access through Details, bordered launcher art, and newer copy.

Current package 5 app source: `4016e8dac8f675a4eb1e1613fd9dc7cf63d06e58`. Local package: `build/release/final-candidate-5-2026-10-14/calm-frames-0.1.0-aarch64-debug.vpkg`; 28,733,262 bytes; SHA-256 `a226b39fc855cd7cf5eb4136b9ba890f92e6e6518ca764a6862cf9990870dc13`. The [committed receipt](https://github.com/alejandro-publius/calm-frames/blob/a3368a9e4dbfde52153d586d97d8c6da5ab5c8fd/results/native-acceptance-5-2026-10-14/receipt.json) records eight simulator journeys judged from app logs. This is partial native evidence: pixels, audible continuity, the parent-settings interior and VoiceView remain unobserved. The practice-navigation verdict was reviewed manually after the driver returned partial. The package is local output, not a GitHub-hosted binary.

The following audit and sync instructions are historical context from before that push. Recheck remote refs and inspect the current candidate before changing anything. Do not repeat completed work. The research branch remains documentation-only, based on older source. One remaining-actions paragraph in the candidate's FINAL_HANDOFF still names older `819de40`; use package 5 and source `4016e8d` for current acceptance. No main merge, candidate PR, hosted CI, public video or final submission has been established by this update.

## Read this before pulling or replacing any code

The research branch is documentation-only and is based on an older, verified remote reliability commit. It is **not** the latest integrated application. Do not replace your current local working tree with this branch, reset to it, or assume `main` is current.

GitHub audit at approximately 03:46 UTC found `codex/core-reliability-2026-10-14` at `cfddc4adb8bcdd17a861e6489f5fb50693c282d3`. The approved coastal branch and the newer local integration refs below were not found remotely. Recheck before syncing because another agent may have pushed since this audit.

Known local evidence, not a claim about the current working tree:
- Approved coastal work: `codex/approved-coastal-2026-10-14`, reported commit `b22d27581d23a595878485be747ff279f543f903`.
- Coastal worktree: `/Users/alexvintera/Documents/Codex/2026-10-13/task/calm-frames-coastal`.
- Later Claude integration was observed at abbreviated source ref `93cf800`, with attribution patch integrated as `cf53d39`. Resolve these locally; do not invent full SHAs.
- That later package was 28,664,945 bytes, SHA-256 `d53444ab70f38d24fb4cb1c468ebe78e0ed24cc6932c45235e50dd174fb2a25a`; 728 recorded build inputs matched at the earlier inspection. Subsequent edits require a new build and new evidence.
- Native end-to-end acceptance of the latest candidate has not been independently verified.

## Owner's latest visual direction

Use the approved coastal artwork, ivory background, deep teal typography, restrained terracotta accents, and tactile controls. Preserve the zen character. This is a normal 2D interface using dimensional illustration, not a full 3D application. No new themes, animation experiments, subscriptions, or redesign detours are needed for release.

Apply this focused home-screen cleanup if it is not already present:
1. Replace the large `Harbor` heading with `Calm Frames`; remove the smaller duplicate brand label above it. Fit the heading without overlapping artwork.
2. Remove `Picture holds on supported videos. Audio continues.` from Home.
3. Remove the full `Try picture holds` Home card, thumbnail, and `20 sec · 2 practice holds` subtitle. Retain the practice experience behind Details so the distinguishing feature remains discoverable and testable.
4. Remove the bottom unavailable-title notice, including its `Open Parental controls` wording. Keep parental controls reachable through Settings and preserve all protections.
5. Move `20 sec · No picture holds` into Details. Preserve Harbor as the underlying content title and preserve its actual behavior.
6. Rebalance whitespace without introducing new filler copy, cards, or badges. Keep Play, Details, and discreet Settings access.
7. Fix the remote focus graph after removing controls, including initial focus and return focus.

Earlier requested launcher artwork change: a subtle warm-sand `#E5D9BA` inset border, approximately 1% of tile height, around the existing teal mascot launcher tile. Preserve the original asset and existing rounded corners. This is an artwork border, not a replacement for the OS-controlled launcher focus indicator. Verify which asset is actually used before editing. This change has not been verified as implemented.

## Safe local-to-GitHub synchronization

The owner explicitly requested pushing the latest project work to the existing GitHub repository so Claude can use it. Preserve the private repository's visibility and do not merge or force-push main.

1. Wait for any current code-writing task to finish. Inspect repository identity, origin, branch, `git status`, local worktrees, recent commits and branch ancestry. Locate the current integrated candidate; do not pick an older branch merely because its name appears here.
2. Fetch remote refs without resetting, pulling over a dirty tree, discarding changes, or overwriting another agent's work. Confirm origin is the intended `alejandro-publius/calm-frames` repository.
3. Inspect unpublished commits and untracked files. Separate app source, required artwork, provenance, tests and submission docs from build outputs, logs, recordings, credentials, environment files, dependencies and unrelated projects. Never use a blind `git add .`.
4. Secret-scan the exact proposed tracked changes. Do not print secret values. Keep API keys, tokens, PINs and personal data out of commits. If a secret has already entered history, stop that push and report the issue without exposing it.
5. Preserve unfinished work. Make a normal, descriptive commit for reviewed changes when appropriate, on an explicit working/release-candidate branch. Use small integrations only where ancestry or diffs show a missing required patch; avoid duplicating cherry-picks.
6. Run focused checks against the actual changed code and build the selected target. Do not block backing up clean reviewed source solely on unavailable hardware, but label untested native behavior honestly.
7. Push the explicit working branch normally. No force push, main merge, tag, visibility change, GitHub Release, or external publication.
8. Verify the remote branch resolves to the exact local commit SHA. Report the branch, full SHA, comparison URL, included changes, excluded local changes, tests and remaining blockers. If push credentials or access are missing, report the exact blocker; do not create tokens or change access settings.
9. Read the two accompanying research documents. Copy or cherry-pick only their documentation changes into the current integrated branch if useful; do not merge an older codebase over the latest candidate.

The remote audit also found stale root handoff documents: `CLAUDE.md` and `COMPLETION_CHECKLIST.md` still lead with October 13, and `docs/CLAUDE_FINISH_PROMPT.md` directs work toward an older signed-scene-holds branch. Reconcile these against the actual current local candidate before obeying their branch instructions. Read the accompanying GitHub audit for verified paths and ancestry. Do not treat a filename such as FINAL_HANDOFF as proof that all tests or synchronization succeeded.

## Three implementation priorities

### 1. Playback reliability
Trace actual initialization, loading, playing, pausing, seeking, marked hold intervals, completion, failure, retry, navigation away and cleanup. Verify late callbacks do not update exited screens or start audio after exit. Preserve continuous audio only during supported marked holds, not after leaving playback. Ordinary Harbor has zero holds; the practice clip has two. Do not imply arbitrary Netflix/Prime/unsupported videos are processed, or make medical-safety guarantees.

### 2. Remote usability and accessible UI
Every reachable control needs a clear focus state, predictable directional movement, an accessible label and working Back behavior. Validate return focus, modal focus, parent PIN flows, long strings, and artwork/text separation. Keep honest explanations in Details or Help instead of cluttering Home. Do not bypass parent protections or reset device/app data to make a demonstration easier.

### 3. Final integration and submission evidence
Identify the actual SDK, build architecture and target. The known aarch64 package is not evidence of testing on a physical Fire TV Stick. Run the current integrated candidate through launch, setup, Home, Play, pause/resume, seek, captions where supported, both practice holds, completion/replay, Back, Details and parental controls. Record pass/fail/blocked in text with the package SHA and target. Browser/component previews and unit tests cannot substitute for this native acceptance pass.

For real failures, implement a minimal fix and rerun the affected flow. Avoid repeatedly running the full suite without a code change or specific diagnostic reason. Finish with a package built from the actual final candidate, source SHA, checksum, reproduction steps, and a remaining-blockers list. Update existing submission docs rather than creating conflicting claims.

## Constraints and stopping conditions

- No screen/video recording or screenshot-capture scripts: the owner revoked this permission. Prepare a manual demo shot list/script; do not capture it automatically.
- No purchases, new paid services, public submissions, repo visibility changes, credential configuration, permission expansion, or contacting organizers on the owner's behalf.
- Do not reinstall or rewrite the project around a sample app. Use the official samples as narrowly targeted references.
- Preserve original assets and attribution notices; unresolved source-license issues must remain explicit until resolved.
- Do not report completion based only on tests or a build. If native execution is blocked, report the exact blocker and finish independent documentation/sync work.
- Stop when the requested cleanup, safe synchronization, targeted fixes and evidence packet are complete, or when a specific user action is genuinely required. Do not invent extra work to consume credits.

## Final response expected from Claude

1. Updated remote branch and full commit SHA, verified against the local candidate.
2. User-visible changes actually implemented.
3. Test results separated into unit/build/browser/native evidence.
4. Exact target, package path and SHA-256 for the final build.
5. Remaining submission blockers and the single next action for each.
6. Where to open/run the updated app, clearly identifying native app versus browser preview.

## Read the research packet

- `FIRE_TV_RESEARCH.md`: official device tooling, sample patterns, lifecycle, focus, accessibility, performance and coverage limits.
- `SUBMISSION_RESEARCH.md`: verified requirements, private-reviewer route, mini-challenge conditions, friction feedback and checklist.
- `GITHUB_AUDIT.md`: observed remote refs, missing local changes, and stale guidance.

The owner's October 15 handoff prompt in chat includes the most recent full execution request. The core-first order is native functionality, evidence-backed friction feedback, then an optional reusable Open Source contribution if feasible. Draft any public contribution privately and request approval before publishing or licensing. Check real Kiro Crew usage before claiming AWS Builder qualification. Do not add an AWS backend simply for eligibility.

Friction feedback may earn a discretionary bonus up to 10%; verify and document genuine task/steps/expected-versus-actual/severity/workaround/actionable suggestion. A source-doc inconsistency is not proof the app experienced a bug. No automatic recording or screenshot capture is authorized.
