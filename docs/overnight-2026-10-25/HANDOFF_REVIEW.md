# Handoff evidence and privacy review

Reviewed source: `15ef46c6e23c8ba627492da23b1b147000031aa4`.
Its candidate application code is `a672f57d333dc0e3fada51b3175ca1711d1f9397`.
The supplied `START_HERE_CODEX.md` was read as evidence. Its statements that
nothing was pushed are historical: the user explicitly corrected them and the
integration owner fetched the named GitHub branch at the expected full SHA.
This review makes no publication or native acceptance decision.

## The committed logs

The reported
<!--n results/overnight-2026-10-25/handoff-review/log-privacy-review.json:count -->68<!--/n-->
logs are the changed `.log` files from `d7da316` through this handoff. They were
already in the ancestry of cloud `226d317`; Claude's later integration commits
add no `.log` file. They are cloud test/tool output, not the missing native
device evidence archives.

The [file-by-file privacy record](../../results/overnight-2026-10-25/handoff-review/log-privacy-review.json)
identifies each file by SHA-256 and covers
<!--n results/overnight-2026-10-25/handoff-review/log-privacy-review.json:file_bytes -->986362<!--/n-->
bytes and
<!--n results/overnight-2026-10-25/handoff-review/log-privacy-review.json:line_count -->21142<!--/n-->
lines. Pinned Gitleaks 8.30.1 reports no findings in that exact set. Targeted
review covered account home paths, credential assignments and headers, private
keys, PIN/name focus traces and serialized household patterns.

The flagged candidates have explicit provenance:

- The email-shaped value is the public dependency-maintainer contact printed
  by npm's deprecated-package warning. It is not an owner's account detail.
- `private-input-trace/privacy-before.log` is the failing Jest reproduction.
  Its command is recorded in the adjacent receipt, and the corresponding
  [test source](../../app/test/calmframes/privateInputTrace.test.tsx) exercises
  every keypad key and a fictional name. These are synthetic regression traces,
  not a household PIN or name captured on a device.

No demonstrated private household or credential disclosure was found in this
scope. The logs remain byte-for-byte unchanged; removing the synthetic failing
output would discard useful regression evidence. This is a bounded privacy
review, not a guarantee against every unknown data representation. No raw native
log or household record was added to Git.

## Never-merge checks

The [exclusion record](../../results/overnight-2026-10-25/handoff-review/harness-exclusion-review.json)
compares the full supplied SHAs against the complete, non-shallow candidate
ancestry. Every supplied head from the ten never-merge branches and every
separately named fixture commit is absent. The original item 6 production fix
`dd1ec6c` is also absent; its accepted standalone cherry-pick `161c2f5` is present.
No harness bundle or branch was fetched or merged during this review.

The supplied table reports
<!--n results/overnight-2026-10-25/handoff-review/harness-exclusion-review.json:reported_total_branch_own_commits -->25<!--/n-->
branch-own commits but does not enumerate their full IDs. Their branch objects
are absent locally. Thus this review independently excludes the named heads and
fixture IDs; it cannot re-prove exclusion of every unnamed intermediate commit.
A plain inventory of those full IDs, grouped by head and base, resolves that
proof gap without importing a harness bundle.

`app/index.js` is byte-identical to `6a87937`, and the production initial route
remains `Screens.KID_MODE_SCREEN`. The integration diff adds no onboarding or
accessibility fixture entry wiring. The attachment's broader wording that
`app/src` has no harness symbol is inaccurate: historical measurement helpers
and `SceneBridgeFixture.tsx` already exist in submitted `bf2f615` and are unchanged
from `6a87937`. Their presence is not a newly merged acceptance harness.

## Items 5 and 6 retain their actual scope

The [acceptance review](../../results/overnight-2026-10-25/handoff-review/acceptance-review.json)
maps the committed operator observations to the source and recorded package.

- **Item 5 remains completed on the operator record.** The later Mac pass
  reports sibling-name refusal and controlled failed-save/retry with fictional
  profiles and VoiceView. Those observations use a separate harness over
  `4de7bd0`; only onboarding layout and its test change between that production
  source and `a672f57`. Earlier persistence, cancellation, focus and position
  observations remain retained. This review does not claim to have inspected
  the missing native recordings or to have run another device pass.
- **Item 6 remains partial.** The committed record describes production
  first-run navigation at both supported sizes on a disposable fresh device.
  The disclaimer remains below the initial viewport and reachable by one Up.
  Its layout acceptance belongs to the owner. The recorded idle event is a
  device power/lifecycle timeout with an empty crash history and clean relaunch,
  not a demonstrated app crash.
- **The native inventory is Debug evidence only.** The committed notes assert
  that the Release bundle never exceeds it, but no corresponding Release bytes
  or inventory were supplied. No Release inclusion, exclusion or superset claim
  is adopted by this review.

## Exact missing inputs

These files are not present in the received attachments or shared workspace.
Their identities below come from the attached handoff and have not been
recomputed from local archive bytes:

| Input | Reported identity | Needed for |
|---|---|---|
| `calm-frames-acceptance-evidence-a672f57-2026-10-24.zip` | SHA-256 `bb7c423899d1671746dbb24aac79c26761d4be44c5875e7f9ebe02eba61cee34` | Current candidate native images/recordings, diagnostics and module-inventory inspection. |
| `calm-frames-integration-evidence-2026-10-24.zip` | SHA-256 `ac3b3e92391297ee5cbf10b6714344660a9b20b0ad4ae1d208e2509dfacc0207` | Earlier `d7ff886` native integration and private-trace corroboration. |
| Plain never-merge commit inventory | Full own-commit IDs for the ten named branches, grouped by their heads and bases | Independent exclusion of the unnamed intermediate harness commits. |

The native binary and rollback binary are also absent. Their package identities
remain recorded Mac evidence, not cloud rehashes. These inputs block independent
native artifact review; they do not block other local source work. No new Mac
build or repeated native pass is needed just to transfer the existing evidence.
