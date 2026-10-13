# Focused Mac finishing task

Use the following task on the Mac with `~/calm-frames`, the Vega SDK and the
original project artifacts. For the restricted promotional credits described
by Alex, test the noninteractive `claude -p` route with an API key from the
credited organization. Pasting the task into an interactive subscription chat
does not establish that those promotional credits are used.
The cloud session prepared this task but has not started Claude, used API
credits, connected to the Mac or scheduled an unattended reviewer.

## Noninteractive launch on the Mac

The official Claude CLI version 2.1.296 was inspected in the cloud without an
API request. Its help confirms `-p`, `--allowedTools`, `--output-format json`
and `--max-budget-usd`; the budget option works only in print mode. Check the
installed Mac CLI's help too. The account-specific promotion's coverage and
expiry must be checked in Console; they were supplied in the user's pasted
explanation and have not been independently verified in this cloud session.

Create or use an API key in the organization holding the promotional credits.
From the ordinary Mac terminal, the following zsh commands read it without
echoing it or placing the key itself in command history. The key is passed only
to the selected Claude process; the existing interactive login is preserved.

```sh
cd ~/calm-frames
read -s 'calm_claude_key?Anthropic API key from the credited organization: '
printf '\n'
ANTHROPIC_API_KEY="$calm_claude_key" claude -p \
  'Reply API_CONNECTION_OK. Do not use tools or change files.' \
  --allowedTools 'Read,Glob,Grep' --max-budget-usd 1 --output-format json
```

Before the larger task, confirm this request succeeded and check Console usage
and billing attribution in that organization. A successful request alone does
not establish which balance paid for it. If it still reports low credits, stop
and inspect the credited organization, key, promotion coverage and expiry.
Do not keep repeating interactive login or silently use purchased credits.

After the test is accepted and its billing route is confirmed, run:

```sh
ANTHROPIC_API_KEY="$calm_claude_key" claude -p \
  'Safely sync origin/codex/signed-scene-holds-2026-09-29, preserving local work and recordings. Read the latest docs/CLAUDE_FINISH_PROMPT.md and execute its Task section. Finish the existing Mac/Vega build and matching demo, and push each checked milestone.' \
  --allowedTools 'Read,Glob,Grep,Edit,Write,Bash' --max-budget-usd 24
unset calm_claude_key
```

The first test and finishing call have separate limits, totaling US$25 for this
pass. Tool permissions let the local agent run the documented build/capture and
Git workflow. The task below retains the publication and communication limits.
Actual running behavior, billing and Mac permissions remain to be observed.

## Task

Finish the current Calm Frames implementation and its matching simulator demo.
Continue from the shared work. Preserve the cinematic storybook design, open
text layouts, optional motion/sounds and all playback guards. Use the Vega
Virtual Device exclusively. Do not restart the project review or add features.

### Start from the current branch

Inspect local changes and active work before fetching
`codex/signed-scene-holds-2026-09-29`. Preserve and reconcile local work; do not
reset, clean, force-push or overwrite another editor's work. If another agent is
editing the same checkout, arrange one implementation owner before proceeding.
Use the existing checkout; no extra worktree is needed.

The known application/tooling baseline is `cd42004`. Its hosted CI run
[38415127212](https://github.com/alejandro-publius/calm-frames/actions/runs/38415127212)
and Audit run
[38415126573](https://github.com/alejandro-publius/calm-frames/actions/runs/38415126573)
both passed. Later pushes take precedence; inspect their changes and checks.
Read the current [completion checklist](COMPLETION_CHECKLIST.md),
[Mac workflow](MAC_FINISH.md) and [recording plan](VIDEO_SCRIPT.md).
Read other files only as needed for the remaining work.

### Establish the Claude billing route

The user wants to use available Anthropic API credits. API billing is separate
from a Claude subscription; a subscription login alone does not establish use
of those credits. Inspect the installed CLI's version, help and non-secret
authentication status, and verify which configured Anthropic workspace is billed.
Do not print or commit keys, read credential values into a transcript, log out
an existing subscription session, or silently fall back to another billing route.

Start with a ceiling of US$25 for the first API-assisted pass, including any
delegated calls. This is an initial work budget, not an estimate of the cost to
finish. Enforce it with supported CLI or provider controls; a sentence in this
prompt alone is not a spending cap. Verify the installed CLI's budget support
before invoking it, and keep calls sequential under one cumulative allowance.
Run one small read-only task first and confirm its actual model and API usage
without exposing credentials. Save cost metadata locally and report the total.
When launched with the commands above, reuse the completed US$1 connection test
and work within the remaining US$24 call limit. Do not start nested paid CLI
workers whose spending is outside that call's budget.

If credentials or an enforceable limit are unavailable, report that specific
prerequisite and continue work available to the current local agent without
starting paid Claude calls. Credentials belong in the secure local/provider
configuration, never in chat or the repository. Do not use credits simply to
consume the balance. Prefer one implementation owner over repeated review teams.

### Milestone 1: recover evidence and build the current app

Use [MAC_FINISH.md](MAC_FINISH.md) to locate and attach the two exact original
prepared-library verification reports. Search the project's existing build,
pipeline and log directories and known project archives. The cloud review ZIP
and its nested source ZIP were already searched without finding either report.
Do not repeat that search or scan unrelated personal files.

If an original cannot be recovered, inspect the real benign source material and
existing authorized local signing workflow. A separately prepared and verified
new library export can supply new evidence; preserve the old export and receipts.
Never substitute a regenerated report under an old digest or relax the strict
release gate. If required source material or signing access is missing, record
the exact blocker and continue independent preparation.

Build the current aarch64 Debug package with its source/input receipt. Install
it on the existing virtual device without erasing household data. Fix actual
build or acceptance failures and run the relevant checks for those changes.
Preserve the earlier package and recordings as historical evidence.

### Milestone 2: observe the actual viewing experience

Complete the native journeys in the Mac workflow: remote focus and Back,
scrolling, PIN correction, saved settings after restart, compatible titles,
holds, captions, sound and interrupted-playback recovery. Check the current
panorama and open layouts for clipping and TV readability.

Observe the optional artwork motion and selection sounds, their Off defaults,
persistence, accessibility/lifecycle behavior and separation from playback and
the warning chime. Use benign media and a separate test household where needed.
Record what was actually seen and heard. Keep passed, failed and untested
observations distinct; browser previews and software logs do not replace them.

If macOS needs a Screen Recording or other OS permission, identify the exact
user action and continue independent work. Do not bypass the permission.

### Milestone 3: produce the matching submission artifacts

Capture the actual native journey, fill a fresh capture manifest and assemble
the current English demo using [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md). Review the
short Inter subtitles against the spoken narration and preserve the full native
picture. Listen to captions/audio demonstrations and the mixed narration.
Run the finished-video checks under both WCAG and broadcast, including a capture
with motion enabled, and preserve fresh source, package and video hashes.

Build the matching review archive. Update [SUBMISSION_COPY.md](SUBMISSION_COPY.md)
and the checklist only where the new observations support a change. Keep the
practice holds, presentation art, separate AWS pipeline and detector limitations
accurate. A polished video must not imply the untested or unresolved parts work.

Read the [Amazon sample license record](AMAZON_SAMPLE_LICENSE_REVIEW.md) and
look for an authoritative clarification already published upstream. An AI
opinion does not resolve the conflicting notices. If none exists, keep the
prepared question ready; do not send outreach or open a public issue from this
task. The app work can continue while that question remains unresolved.

### Push completed milestones and leave a precise status

Commit and push each checked, coherent milestone to the same shared branch.
Fetch before each push, preserve concurrent changes, and verify the remote SHA
afterward. Update the single completion checklist with artifact paths and exact
remaining blockers so another session can review only the new work.

GitHub CI and Audit already run on pushes. Check the runs for the exact pushed
SHA; a running or cancelled workflow is not a pass. Reuse valid results for
unchanged inputs. Run the required build and acceptance checks, without repeated
full conformance runs or generic audits. Do not push empty status commits solely
to announce polling. Once the final batch is pushed, let its hosted runs finish.

Keep large new review artifacts distinct from the October 10 draft assets.
Use the existing private draft release only after checking it is still private
and draft, preserving earlier artifacts. If upload is unavailable, report the
artifact's path and hash; do not claim it is shared.

Prepare the release and Devpost fields for review. Do not merge main, make the
repository public, publish a final release, send external messages, submit the
entry or redeploy AWS from this task. Those actions retain their separate
review/approval requirements in CLAUDE.md.

End with the pushed commit, the actual native package/demo identities, hosted
check status, locally measured API spend if available, and the exact remaining
steps. Do not claim submission until an actual Devpost confirmation exists.

## Reviewing progress from this chat

This cloud chat can fetch and inspect new pushes while a turn is active. It is
not an unattended background monitor after the turn ends. GitHub's existing
workflows continue checking pushes independently. Ask this chat to check the
latest push for a review of the changed work and remaining checklist items.
