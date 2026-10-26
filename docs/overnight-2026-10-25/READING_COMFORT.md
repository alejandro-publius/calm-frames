# Optional Reading comfort

Original checklist item 20 is **partially completed**. The default-off source
implementation and cloud regressions are complete; native layout, focus,
VoiceView and owner comfort acceptance remain open. It was implemented after
the higher-priority overnight product changes at
`ba39bc76e022d69dd0290487874b3b2eb8225b1a`, in the isolated
`codex/reading-comfort-2026-10-25` worktree. The existing UX branch is preserved.
Application source: `e6ebec43abd6896db9aabac1c80757059b7d8f93`.

## What changes for a parent

Open Parents, unlock privately, and select a kid. The **Reading comfort**
switch appears below the hidden-scenes record. Turning it on enlarges ordinary
help and body text and adds room inside settings rows for that kid's Parents
page. More info follows the kid currently watching and enlarges its existing
body text, including the safety note with equal emphasis. The wording stays
the same. Choosing another kid uses that kid's own preference.

On and Off come from the saved family. A pending write keeps the switch
focusable, blocks a second change and retains the old value. A failed write
uses the existing household storage error and retry route. Retry saves the
pending preference, and Parents requires its PIN again. An adapter that
refuses a save without leaving Parents shows a short retry message instead.
Completing a write requests focus on the switch only if the remote has not
moved away in the meantime.

The name editor, profile panel, locked PIN screen, FirstRun and its disclaimer,
and the approved Parents explainer keep their existing layouts. Home, Watch,
technical details, player controls, captions, global typography and motion
settings do not use this preference. Protection rules, signed media and
playback positions are unchanged. This is a display preference, not a
treatment or a statement about medical safety.

## Storage and rollback

`Profile.readingComfortEnabled` is separate from `HouseholdSettings`, so it
cannot participate in protection-floor calculations. Missing legacy values
and new profiles are off. Only literal `true` enables it; a stored value of
the wrong type is rejected instead of being treated as true. Both profile
normalization and household serialization preserve the explicit boolean.

The existing household storage key and version remain. Loading an old record
normalizes the preference in memory; it does not trigger an automatic write.
The regular result-aware save persists it. No PIN, household or playback data
was accessed by this cloud work; regression tests use fictional records in
memory. IDs, names, the selected kid, other kids, the floor and PIN state remain
unchanged by a preference save.

Rollback uses the separately retained native package and its own verified
receipt. Do not clear app data. Older app code ignores this optional field and
drops it on its next household save, so Reading comfort can return to off after
rollback and upgrade. That preference loss does not require resetting names,
PINs, protection or positions. This cloud change does not produce a new native
package or inherit an earlier package's native acceptance.

## Evidence

The [machine receipt](../../results/overnight-2026-10-25/reading-comfort/receipt.json)
binds the source files, commands and sanitized log hashes. The source-backed
checks exercise legacy loading, true/false roundtrip, profile isolation,
preserved protection, failed saves and retry, real route remount and profile
switching, duplicate presses, focus ownership and unchanged excluded layouts.
The initial tests failed against the previous source. The
[negative controls](../../results/overnight-2026-10-25/reading-comfort/negative-controls.json)
then deliberately broke persistence, routing, save feedback, duplicate-press
protection, focus and text bounds; each relevant regression failed. The source
was restored before acceptance checks.

The normal locked install, typecheck, lint and app test commands retain the
repository's flags and coverage floors. Existing name/PIN, picker, parent
navigation and ten-foot checks also run. Text-bound tests use the repository's
conservative wrapping ruler on the rendered styles; they are estimates, not
native captures or evidence of VoiceView pronunciation.

## Remaining native acceptance

Use the eventual exact-build native package and record its source and package
hash. Keep the existing household and rollback. Enter any real PIN privately
and exclude names, letters and digits from captured logs.

- At both supported sizes, enable and disable the preference for a test kid.
  Inspect wrapping, visible focus, row spacing and D-pad access to all controls.
- Navigate through More info's reading stop, its safety sentence, technical
  details and Back. Confirm the larger help remains reachable and no text is
  clipped. Inspect the unchanged Watch and FirstRun layouts separately.
- Save while focus stays on the switch, then move away during a pending save.
  Confirm focus stays with the intended control and VoiceView speaks its
  actual saved state. Do not manufacture a failure by corrupting household
  storage; cloud tests cover the controlled failure and retry path.
- Switch between kids, return to Parents and relaunch. Confirm each saved
  preference applies only to that kid. Retain the accepted name-editor and
  protection behavior.
- Ask the owner to judge readability and comfort. Source tests cannot close
  this acceptance item or authorize a submitted replacement.

Status: optional source work completed locally; native acceptance pending.
