# Integration status, October 23, 2026

One Claude cloud session owns integration on this branch. Other sessions should
stay idle here; their own worktrees and edits are untouched.

## Where the work is

| What | Where |
|---|---|
| Integration branch | `claude/eager-goldberg-1s5eb4`, fast forwarded from the verified handoff `6193182` (`codex/claude-handoff-2026-10-23`), no force push, `main` not merged |
| Product baseline | the handoff branch, production source `bd55e47` plus evidence through `6193182` |
| Not a baseline | `main` (`7110893`, September 20) is far behind the product |
| Submitted fallback | `bf2f615` on `claude/ocean-layout-fix-2026-10-19`, untouched |
| Kept apart | Retry harness `84faeed` (never merge), rejected browser redesign `76223f9` (excluded) |
| Code at | `12125b2970342b5376b0bc7964383e547b407376`; commits after it change documentation only |

## Included on this branch

| Commit | What and why |
|---|---|
| `bde35e9` | Remote focus stays whole while a profile choice saves. The October 23 polish let Watch and the active chip both ask for focus, and closed the picker into a disabled button during the save. Tests seen to fail first. |
| `3a6ca92` | A README line link moved by the teardown fixes, and four relative links in a copied handoff note. |
| `2403d8f` | How it works shows the approved safety sentence (it said "cannot guarantee seizure prevention"); the main button reads Watch for every title, as How it works instructs; one ellipsis character for loading and saving. |
| `9f8c612` | Paired island cards keep the 32 unit text floor (their second line was 26). The ten foot test now draws the real island map. |
| `5e4da02` | A saved position edited on the device to carry settings loads without them. |
| `12125b2` | decode.py may differ from the conformance record: every one of the 3000 measured clips decoded every frame it wrote, so its new completeness check could not have moved a row. A test enforces that from the record. |
| Documentation | README status lines, this file, the Mac checklist, DECISIONS, STATUS, START_HERE and the [results receipt](../../results/integration-2026-10-23/receipt.json) |

## CI

The run on the handoff commit, [39910746898](https://github.com/alejandro-publius/calm-frames/actions/runs/39910746898), had two red jobs:

| Job | Failure | Cause | Resolution |
|---|---|---|---|
| Vega app | `pickerFocusReturn.test.tsx` | Two controls asked for focus with the picker open | Source fix, `bde35e9` |
| Vega app | `householdRestart.test.tsx` | Picker closed into a disabled button during the save | Source fix, `bde35e9` |
| Python | `test_doc_line_links` | README anchor moved | `3a6ca92` |
| Python | `test_doc_links` | Copied note kept old relative paths | `3a6ca92` |
| Python | `test_measured_sources_unchanged` | `flashmap/src/flashmap/decode.py` gained the decode completeness check (`eff3ca4`) after the published conformance numbers were measured | Allowance with its reason enforced from the record, `12125b2` |

The mutation gate, secret scan, number drift checks and the app's own flash check
passed on that run.

Hosted CI runs on this branch through
[draft PR #2](https://github.com/alejandro-publius/calm-frames/pull/2), which exists
only to start CI: never merge it. This session's GitHub app gets HTTP 403 when it
asks to dispatch, cancel or re-run a workflow, so each run here starts from a push,
and a new push cancels the run before it. On `d95e9df`,
[run 39994434980](https://github.com/alejandro-publius/calm-frames/actions/runs/39994434980)
passed the Vega app, the app's own flash check, the mutation gate, the secret scan
and the published numbers jobs. Its Python job stalled in the runner's `apt-get install ffmpeg`
before any test ran (the same step took about 20 seconds in the other jobs), so
the next push replaced that run. The latest run on PR #2 is the one that counts.
The same commands CI runs were also run in the cloud session on the code commit;
the [results receipt](../../results/integration-2026-10-23/receipt.json) has the
counts.

The separate Audit workflow fails on this branch, on the handoff commit and on
the submitted commit alike: the reviewed exceptions in
`scripts/audit_exceptions.toml` were due for review on October 21, and new
advisories for `launch-editor` and `toml` arrived since. Renewing exceptions is
the owner's review, so the file is unchanged here; PR #2 has the details.

## Verified here, and not

Verified in the cloud session, on the code commit above: the app's Jest suite,
TypeScript and lint, the app's own flash check, the Python suites CI runs, the
style and number drift checks, and the record-based reason decode.py cannot move a
published conformance row. One Python test fails only because this container runs
as root, so `chmod 0` does not stop a read; it passes as an unprivileged user and
on CI. A fresh conformance run here was stopped after 890 of 3000 clips and is not
evidence; [DECISIONS.md](../DECISIONS.md) says what it showed.

Not verified here, because this session has no Vega simulator or device: remote
focus on screen, audio, cover and seek ordering, uninterrupted playback, comfort.
Those are the [Mac checklist](MAC_ACCEPTANCE_CHECKLIST.md). Nothing in this file
claims them.

## Deferred, with the reason

- **Analyzer identity in the preparation cache key.** Confirmed absent: the
  analyze step is keyed by a manual `decode_evidence_revision`, not by the
  analyzer's version or source. Adding it changes every analyze fingerprint, so
  the next ingest of an approved work directory would issue new signed maps. That
  needs the owner's approval and is not a submission-day change.
- **Visual proposals from the design critique**, each a look change that wants an
  owner's eye on the simulator first: a visible resting fill on the primary button
  (today 1.03:1 against the page), a lighter resting card edge so the focus ring
  is a 3:1 change instead of 1.19:1, an error colour apart from the focus brick,
  the profile panel sized to its chips, four PIN slots that fill as digits arrive,
  one name for the Details, More info and Technical details path, grouping
  Parental controls, one illustration style on parent screens, and choosable kid
  names in place of Kid and Kid 2.

## Next

1. Read the latest CI run on draft PR #2 and check that its head is the branch tip.
   If a job stalls before its tests start, cancel and re-run it from the Mac
   (`gh run cancel <run id>`, then `gh run rerun <run id> --failed`); this
   session cannot.
2. Build and install from the branch tip and work through the
   [Mac checklist](MAC_ACCEPTANCE_CHECKLIST.md). Keep the PIN, profiles and the
   rollback packages it lists.
3. The owner decides, before 12:00 PT, whether to replace the demo video and update
   the Devpost entry. Nothing here publishes either. The deadline, October 23 at
   12:00 PT (19:00 UTC), was confirmed from two public listings; the official rules
   page did not resolve from the cloud session, so read it once more before submitting.
4. If this branch becomes the one judges should use, change the README's clone
   command, which still names the submitted branch.
