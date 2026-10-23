# Claude Code Fable: implement editable kid names

Implement original backlog item 5, PIN/profile/kid-name UX. This is a coding
assignment, not an audit-only assignment. Deliver an actual native Parents
feature in a separate worktree while the cloud integration owner handles CI,
dependency remediation, presentation and the evidence checklist.

## Exact starting point and ownership

Start from `d7da316d2d48c3b66b3cc4874257e98ca5ef943e` on the local review branch
`codex/design-polish-2026-10-23`. This includes the approved Home, Details and
Parents visual pass, separate Acadia/McWay/Sea Otters/Forest islands and the
capitalized Sea Otters card. It descends from frozen canonical
`2cf54e0d168e58daedfde3f15407833d23af4e93`.

The source ZIP supplied with this handoff contains a thin Git bundle requiring
that frozen base. Verify SHA256SUMS and `git bundle verify` before importing.
Follow START_HERE.md to create `claude/profile-names-fable-2026-10-23` and a new
worktree. Never switch, reset, stash or clean an existing checkout. Stop only if
the verified source or a required API is missing; do not substitute an older
branch or reconstruct these changes from descriptions.

Read CLAUDE.md and the current source. This explicit assignment supersedes old
instructions to leave all app work to another session. The cloud thread remains
the integration owner. You own only the following implementation lane:

- `app/src/calmframes/ParentAreaScreen.tsx` and new profile-name UI components.
- Profile-name copy in `app/src/calmframes/copy.ts`.
- `app/src/calmframes/profiles.ts` only if the name contract needs a bounded fix;
  retain existing IDs, limits and protection semantics.
- Relevant profile/Parents tests, plus exact UI surface declarations and generated
  mirrors only when required by your real change. Run the existing sync tool.
- Your concise result under `docs/design-polish-2026-10-23/fable-profile-names/`.

The cloud owner will not edit these files while this assignment is active.
Do not change dependency manifests/locks/SBOMs, pipeline, analyzer, player,
recovery, signing, approved media/catalogs, global theme, Home island geometry,
onboarding, root README, canonical checklist or demo assets. Do not apply the
rejected browser UI or merge the Retry harness. No other agent assignment.

## Demonstrated gap

`ParentAreaScreen.tsx` currently calls `addProfile` with `nextKidName` and
explicitly says there is no keyboard to rename a kid. The data model already
exports `renameProfile` in `profiles.ts`, preserving the ID and other fields;
`MAX_PROFILE_NAME` is 16. Existing profile tests cover truncation and identity.
Complete the user-facing path without replacing the household model.

## Required behavior

1. A parent who has privately unlocked Parents can select a kid and choose
   **Edit name**. Everyone cannot be renamed. The last remaining kid can be
   renamed even though it cannot be removed.
2. Offer compact, native TV input with a clear label, current name, **Save** and
   **Cancel**. Verify the installed Vega input API before using it. If its text
   keyboard is unavailable, implement a bounded D-pad entry control using the
   existing native components. Do not use a browser field or add a dependency.
3. Preserve the approved coastal panel, fonts, focus outline and control sizes.
   All input/actions must be reachable by remote. Back cancels editing and returns
   focus to Edit name before any subsequent Back leaves the page.
4. Trim input; enforce the existing maximum; reject empty/whitespace-only names
   visibly instead of silently changing them to Kid. Handle a duplicate display
   name with a clear validation message so profiles remain distinguishable. Do
   not change unrelated model serialization or silently rename existing records.
5. Save through the existing household persistence path. Preserve profile ID,
   active profile, saved playback position, hide log, per-profile settings and
   household protection floor. Do not change the PIN or weaken its gate.
6. While saving, prevent repeated submissions and expose a concise pending state.
   A write failure must not appear as success, erase typed input, or change which
   profile the draft belongs to. Keep a reachable retry/cancel path consistent
   with the current route's save-error behavior. Inspect that route before
   implementing; a void callback is not proof that persistence succeeded.
7. Cancel leaves the persisted household unchanged. Keep draft text out of logs,
   analytics and committed fixtures. Test with fictional names only.
8. Keep Add a kid's existing creation path working. The new editor must let a
   parent rename its generated name; an additional creation wizard is out of scope.

## Acceptance and deliverables

Implement first, then run focused checks for rename/cancel, validation boundaries,
Back/focus return, pending/failure/retry and preservation of IDs, protection and
progress. Use existing tests for unchanged contracts. Run normal typecheck and
lint with the repository's locked install, Node 22 and npm 10.9.8. Preserve
existing style, mirror and UI declaration checks; do not adjust flags or silence
guards to pass. No expensive detector suites or media regeneration.

Inspect 720p and 1080p layouts where tooling is available. Browser/tree renders
are approximations, never native captures. Native keyboard, D-pad, VoiceView and
human comfort stay pending until observed on this exact source. Do not interfere
with an operator's shared native session or record private PIN entry.

Commit only your owned files locally. Return the full base and commit SHA, file
list, exact commands/results, visible feature screenshots with honest provenance,
and remaining native checks. Export a verified bundle or patch, its size and
SHA-256 for the cloud owner to review. No push, merge, release, live submission
change, generated narration or new video. Do not call the entire release accepted.
