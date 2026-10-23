# Item 5: editable kid names integrated

Fable's finished name editor is integrated with the existing cloud dependency
and visual work on `codex/design-polish-2026-10-23`. Implementation and cloud
review are complete. Fable's native evidence for `6a87937` is received and
reconciled in the [native receipt review](NATIVE_NAMES_REVIEW.md). The recorded
package identity matches the installed-device log and local source inputs.
Native failed-write/retry, VoiceView and owner comfort remain pending.
This is unpublished work; the frozen integration and submitted fallback remain unchanged.

## Follow-up after Fable's native recap

The [owner-pasted recap](../../results/design-polish-2026-10-23/private-input-trace/fable-reported-status.json)
reports completed checks and a saved rollback package. It also identified
letter-key identifiers in debug focus logs. Source review reproduced that
issue and the same path for PIN digits. Code `07db296` on the isolated cloud
follow-up suppresses those private-input traces while retaining labels,
focus feedback, callbacks and ordinary navigation diagnostics.
The [privacy receipt](../../results/design-polish-2026-10-23/private-input-trace/receipt.json)
records the failing reproduction, focused passing checks and normal typecheck/
lint. Layout, player, media and signing stay unchanged. No new native build is
claimed, and Fable's `6a87937` snapshot remains intact.

The smaller evidence ZIP now verifies against its checksum index. Native
editing, persistence through relaunch, Cancel/Back, focus return and position
isolation are recorded. Still-route and duplicate-name passes are narrower
than their labels; the review states the actual scope. Next: only the remaining
native gaps and owner picture/audio/comfort review. Do not repeat completed
work or claim the newer cloud follow-up was installed.

## Exact source and transfer

| Role | Commit |
|---|---|
| Fable starting source and bundle prerequisite | `d7da316d2d48c3b66b3cc4874257e98ca5ef943e` |
| Original feature | `9546c0f530e2bd99966c1836f2b9ae0246fb3dec` |
| Original notes and export head | `6cda443c3475bd086e62a0582cce42a6a49a4695` |
| Feature replay on the cloud review branch | `9a2db495aace369959b975c5f2a2082ff6878051` |
| Notes replay | `f32f2d659e5dd30154d5b7ff43e715d6fa5759ad` |
| Reviewed code, including cloud corrections | `0102622c1985ef0f7927d7fc434a15a9d2c2e278` |

The final export manifest names the later documentation/evidence HEAD. Its app
source is the checked code above. The original Fable commits remain on
`codex/fable-handoff-6cda443` and in a separate review worktree.

The received ZIP's SHA-256 is
`c77452f4c7dc6ef74af2728e6a40ab5a37038f0460a2f7797e23d1a0746bcb29`.
The [transfer receipt](../../results/design-polish-2026-10-23/fable-integration/transfer-verification.json)
records actual bytes, member checksums, full commits and source-file hashes.
Bundle verification passed. The supplied binary patch reconstructs Fable's
exact source tree and matches the user's reported checksum. The bundle's
prerequisite is d7da316; the older frozen commit in its manifest is context.

## Delivered behavior and review corrections

Inside unlocked Parents, a selected kid has **Edit name**. A remote letter grid
offers automatic capitalization, Shift, Space, Delete, Save and Cancel. Blank
and duplicate names are refused. Everyone has no editor. A successful save
changes the name while retaining profile identity, settings and saved positions.
Letters and spaces are the current input scope; accents, digits and punctuation
cannot be entered. Existing names are retained.

Cloud review found that the visible Back buttons bypassed editor cancellation
and that multiple controls requested preferred focus. The corrections make
header/footer Back cancel the editor first, block leaving during a pending save,
and reserve preferred focus for the active editor or retry control. Tests cover
Save and Back arriving in the same frame. They failed against the imported
behavior before the corrections.

The route test now pauses its memory-storage write, verifies the pending state,
then releases and awaits that write. This removes deadline-sensitive polling
exposed by the full coverage run without relaxing coverage or production gates.
The preview renderer also passes the required Python lint and blocks external
HTTP requests. No player, media, signing or dependency input changed in this
integration cycle.

## Cloud evidence

The [check receipt](../../results/design-polish-2026-10-23/fable-integration/receipt.json)
and adjacent logs identify commands, source hashes, earlier failures and limits.

- The normal app suite passed with existing coverage thresholds:
  <!--n results/design-polish-2026-10-23/fable-integration/receipt.json:app_result.passed -->1838<!--/n-->
  passed and
  <!--n results/design-polish-2026-10-23/fable-integration/receipt.json:app_result.skipped -->4<!--/n-->
  skipped. Tests exercise persisted rename, profile isolation, refusal/retry,
  Back, pending-save behavior, declared frames and contrast/focus guards.
- Normal typecheck and lint passed. Existing warnings remain recorded.
- The dependency compatibility guards and pinned Python lint passed.
- The UI color model passed WCAG and broadcast profiles; its flashing and
  grating negative controls behaved as required. This model does not establish
  native rendering, medical safety or human comfort.
- The prior clean locked installation is reused with byte-identical dependency
  inputs. No symlink installation or adjusted TypeScript flags were used.
  [Dependency evidence](../../results/design-polish-2026-10-23/dependency-wave2/receipt.json)
  remains separate. Audit acceptance is still blocked; no exception was renewed.
- The imported commits and cloud code changes passed pinned secret scanning.
  No hosted run or native build is claimed for this source.

## Current browser previews

These are browser approximations of the actual React Native host trees, using
fictional profiles and existing fonts. They are not Vega captures. The normal
editor's Save is visible; the failure state's Retry is visible after browser
scrolling. The received native pass records normal-grid D-pad travel. The native
failed-write route and its automatic scrolling remain unobserved.

| State | 720p | 1080p |
|---|---|---|
| Editor open | [Image](../../results/design-polish-2026-10-23/fable-integration/preview/720/02-editor-open.png) | [Image](../../results/design-polish-2026-10-23/fable-integration/preview/1080/02-editor-open.png) |
| Failed write, scrolled to Retry | [Image](../../results/design-polish-2026-10-23/fable-integration/preview/720/06-editor-failed-scrolled.png) | [Image](../../results/design-polish-2026-10-23/fable-integration/preview/1080/06-editor-failed-scrolled.png) |

## One Mac handoff

This describes the original transfer now covered by the received receipt.
Use [NATIVE_NAMES_REVIEW.md](NATIVE_NAMES_REVIEW.md) to retain completed
observations and identify the remaining gaps; do not import or replay it again.

The cumulative export's `START_HERE.md`, exact HEAD and
[Mac acceptance checklist](../cloud-integration-2026-10-23/MAC_ACCEPTANCE.md)
describe the original isolated import. Fable and the earlier cloud dependency
fixes were already included; do not reapply either patch or overwrite the checkout.

Retain the completed key-travel, save/persistence and focus-return observations.
Remaining name-editor checks are VoiceView, controlled failure/retry and the
sibling-name refusal case. Owner reading comfort and the other footer,
recovery/protection and ambient-title gaps remain separate. Use fictional data
for controlled failure fixtures and enter any real PIN privately. Do not damage
household storage to provoke a failure.

The repository's storage-error route retains the pending renamed record and
returns Parents behind the PIN after retry; source tests prove that route,
not its native appearance. The native platform keyboard was not observed and
is not used by this implementation.

Item 5 remains partially completed because native failure/retry and the
scope-qualified cases remain open. Owner comfort and selection of the final
combined source are separate gates. Item 12 still has
dependency and hosted-check blockers. Item 18's source and receipt reconciliation
is complete; the Mac package identity is recorded in the native review. The
[original numbered checklist](../cloud-integration-2026-10-23/CHECKPOINT.md)
retains all other pending work. Narration, manga and publication stay parked.
