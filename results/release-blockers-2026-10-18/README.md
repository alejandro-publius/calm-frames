# Release blocker follow-up, October 18

Source commit `23a24c27a78b693ec2213cc5f65558d1796d525b`, based cumulatively on
pushed `a11587e`. Local branch `codex/creator-editions-2026-10-18`; no new push or
install. The running app remains the previously installed `50bc01f` checkpoint.
The other working checkout remains clean at `a11587e`.

## Concrete fixes

| Demonstrated gap | Fix and evidence |
| --- | --- |
| A headless install lacks ignored Shaka/runtime files, discovered only deep in Metro | Read-only `npm run check:native-inputs` names missing files and `npm run setup:player`. Both npm native build hooks and the release helper invoke it. Fresh tracked app assets/reports pass the strict gate; missing runtime fails early. |
| Setup treated any dependency patch failure as already applied | Patches now stop setup on error and use a command-local dependency identity. A real temporary Git fixture succeeds with no global identity and refuses malformed patches. No global Git settings change. |
| Shared/stale Metro state had broken isolated builds | The standard configuration now uses a checkout-local cache and disables Watchman, matching the previously successful isolated native configuration. No shared caches are reset. |
| `npm run clean` deleted the committed dependency lock | The clean command preserves `package-lock.json`; `npm ci` remains reproducible. |
| Duplicate storage keys silently replaced personal additions | Strict JSON parsing rejects ambiguous stored records. The regression failed before the fix. |
| A write could commit then reject its acknowledgment, leaving stale editable state | An uncertain save hides stale edit controls, focuses Retry loading, and reloads actual persisted values before another edit. The regression verifies no duplicate write. |
| Saved millisecond boundaries displayed as whole seconds | Fractional seconds now remain visible, including 1 ms and 999 ms boundaries. |
| Style and attribution checks were red | Existing approval label punctuation is repaired; existing review-source ledger rows receive titles and generated acknowledgments. The exact approval tuple and consumer membership are unchanged. |
| Secret-scan CI falsely flagged 70 build-input digests | Ten exact filename/digest pairs, verified against tracked source, are exempted by whole-line shape. No directory is ignored. Altered values and credential-like fields remain detected by negative tests. The full outgoing preflight corpus, including expanded logs, scans clean with this configuration. |
| Release-package fixtures omitted the now-required approval checker | Temporary fixtures now include the real checker and empty generated registry. Invalid-option tests assert the intended refusal rather than accepting an unrelated missing-module error. |

The existing edition import/idempotence/rollback tests, bridge checksum/fallback
tests, release-only exclusion tests and return-focus tests pass. No new import or
bridge authority was added. No detector thresholds, coverage, media, signer,
consumer membership or household additions were changed.

## Verification and limits

193 focused tests pass: 74 app, 35 pipeline/attribution/setup/security, 49 release
helper and 35 Node tests. TypeScript, focused ESLint, Ruff, style, attribution and
the strict prepared-library gate pass. A separate tracked-source app export passes
TypeScript, 26 Node checks and the strict asset/report check. Dependencies were
reused at their existing versions; this is not a fresh registry install or full
Shaka build. The native preflight correctly reports the seven generated files
missing from that export and succeeds on the prepared development checkout.

No native build/install was done for these edits, to preserve the owner's demo.
A consolidated build/native check of this new source remains engineering follow-up
after review, not a result claimed here. Prior native evidence does not validate
this delta's visible layout or device storage behavior.

## Owner-requested demo

The simulator was stopped when the owner asked to run the demo. Its existing GUI
instance was started once, the installed app launched, and Home Watch pressed once.
Fresh logs confirm approved Acadia playback at 03:57:44 UTC. The collector stopped
and no more keys were sent. No rebuild, reinstall, capture, recording, PIN entry
or household-data mutation occurred. Playback may finish naturally; no loop was
started. This confirms playback events, not the owner's visual/audio acceptance.

## Remaining decisions and verification

- Review this local delta before another private-branch push. Select the final
  judged commit and grant judge access; the repository remains private.
- Complete visual/audio acceptance, including any later consolidated build.
- For personal-cover native rehearsal, privately unlock Parents and establish
  an exact snapshot/restore of existing household additions first. None were read
  or modified here.
- Real authored bridges still need verified wording and an eligible immutable
  base interval. No narration was invented and no new title was approved.
- Recording/publication, footage/notice questions, eligibility and Devpost fields
  remain owner actions. No recording or publication was performed.
- Intermittent simulator slowdown and independent detector validation remain
  documented limits; no fix or medical validation is claimed.
