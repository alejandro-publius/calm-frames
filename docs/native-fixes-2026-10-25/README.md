> Historical 64f792b pass. For the current source, dependency counts, compatible generated inputs and native queue, use the [cloud continuation](../cloud-followup-2026-10-25/README.md). Counts below describe that prior pass.

# Native defect continuation

Product source: **`a6bdb62276dd63603716509e24b2034451b46b44`** on
`codex/native-defect-fixes-2026-10-25`. Later commits in this pass contain
documentation, checked evidence and the transfer helper only. The external
`SYNC_MANIFEST.json` gives the final full transfer SHA and tree.

Received branch `codex/native-validation-handoff-2026-10-25` was fetched and
matched **`37d10c2db57fc0868499adc133cff7560600d5cc`**. Its product tree matches
`fbe53bf9e5ff432dbc28cd68cd8b89e3f5cac93f`; all 102 supplied review files matched
their recorded hashes. The [received native receipt](../../results/native-validation-fbe53bf-2026-10-25/receipt.json)
remains evidence for fbe53bf, not this new source. Existing worktrees, household
data, media approvals, rollback and submitted `bf2f615` are preserved.

## Implemented changes

| Defect or gap | Local change | Verification and remaining boundary |
|---|---|---|
| D1: Watch Up changes the title; some cards go Down to Details | `256bc67`, `1fc9349`: every card routes Down to Watch; Watch and Details route Up to the selected card using native view handles. | Regression checks verify actual ref/handle wiring and selection changes. Native spatial navigation at both sizes still needs observation. |
| D2: Reading comfort save returns to Back and the enlarged switch leaves the viewport | `0c4ab57`: Back's initial preferred focus is consumed once; saved-switch focus is retained; measured native layout scrolls the focused switch into view without animation. | Save/failure/retry, moving focus during save, and changed geometry at both sizes pass. Native pixels, scroll offset and VoiceView remain pending. |
| D3: pause speech occurs on opening and is absent on real pauses | `401816b`, `1fc9349`, `577f6be`: a persistent polite live region changes after observed playback and a real pause, when controls settle. Initial paused/resume state gets visible guidance without a new pause announcement. | Tests cover startup silence, repeated controls, real pause cycles, covers and resume guidance. Dolby/VoiceView speech is not proved by Jest. |
| Near-white route frame | `8884339`: root and navigation cards paint the existing coastal background before lazy route content mounts. | [Evidence and limits](FIRST_FRAME.md). Removes a concrete app fallback; does not prove the native pale frame is gone or alter media/decoder/cover timing. |
| Vulnerable URI decoder | `74ba643`: fixed 0.5.1 behind a small legacy CommonJS adapter; real consumers and Metro checked. | [Dependency record](DEPENDENCIES.md). Native package inventory still required. |
| Vulnerable UUID implementation in Xcode tooling | `a6bdb62`: scoped 11.1.1 override, preserving the actual v4 consumer. | Short-buffer regression, ID generation and actual project parse/write/reparse pass. Audit remains blocked. |

The initial regressions and the full-suite integration failures are retained
alongside the passing results in [checks](../../results/native-fixes-2026-10-25/checks/).
Tests, coverage thresholds, media budgets, guard ordering and exception dates
were not weakened. The normal locked install uses this checkout's dependencies,
Node 22.23.2 and npm 10.9.8. It is not a shared node_modules symlink.

## Completion and next action

The [original numbered checklist](../cloud-integration-2026-10-23/CHECKPOINT.md)
is authoritative: **6 complete, 12 partial, 2 blocked**. Item **14** closes with
the native gallery, provenance, source-backed architecture and reproducible
setup. Completed **5, 6, 9, 15 and 18** stay closed. D1/D2/D3 have implemented
and source-tested fixes, but their native outcomes remain pending, so their
parent checklist items stay partial.

Next: the single [native verification handoff](NATIVE_VERIFICATION.md), including
new package identity, D-pad, Reading comfort, pause speech and transition
observations. No additional archive is required for this implementation review;
the supplied sanitized evidence was sufficient. Do not upload the 111 MB archive
or private household captures by default.

Audit has 13 distinct advisories and two expired exception groups. Other open
work needs accepted source-bound footage, licensed long ambient editions,
owner audiovisual observations or account/judge-access decisions. The
[demo input register](DEMO_INPUTS.md) prevents reference screenshots from being
mistaken for production footage. Narration and manga remain parked.

All new commits and portable artifacts remain local. No push, hosted CI run,
main merge, submission edit, publication or human acceptance is implied.
