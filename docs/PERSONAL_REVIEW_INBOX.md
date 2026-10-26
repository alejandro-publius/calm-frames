# Native caregiver review attempt: not accepted

The bounded item-13 attempt did not pass native report selection and is not
part of main. Its source is preserved on
[codex/personal-review-inbox-2026-10-26](https://github.com/alejandro-publius/calm-frames/tree/001921e76709a30d0b00ee6b951f3ae9aad612ef).
Do not follow that branch as a working TV import guide.

The existing caregiver-computer intake produced a report from a self-created
steady-color silent fixture. SDK transfer to a separate fictional validation app
succeeded. The original media was not played or transferred to the TV. Preparation
stopped at `signing_blocked`, with no signer supplied or trust change.

The Debug screen opened through unlocked Parents. Its first failure was a
structured directory `IsADirectoryError`. A precise compatibility correction
passed its focused regression, but the native retest still refused the report.
No successful native selection, summary or delivery acceptance was observed.

Review then found that installed `kepler-file-system` 0.0.7 declares
`Metadata.mode` as `OpenMode` (values 0 through 5). The adapter and its passing
mocks instead assumed POSIX file-type bits. Removing the refusal would not
establish link/privacy protection. The feature therefore stays off main.
A supported way to validate file/link types is required before continuing this
particular scratch-inbox design; another build without that diagnosis is not
a useful next step.

The [receipt](../results/personal-review-inbox-2026-10-26.json) preserves the
exact source, fixture and Debug package identities. Its 28 passing focused tests,
typecheck, lint and build gates are source-bound engineering evidence, with the
mock limitation recorded. They are not native acceptance.

Original item 13 remains partial: arbitrary native TV file selection is not
implemented, and exact-edition activation still requires existing authorized
signing authority, approval, verification and a checked build/install. The
caregiver-computer intake remains available as documented in its
[existing guide](overnight-2026-10-25/personal-import/README.md). No new playable
title, signer, protection floor, package budget or security policy is introduced.

## Single SDK-contract correction retest

Source `3a8a3600adeec7aa90486e6e8fb7f73f2c5a8415` replaces the POSIX assumption
with the installed native `file_system.idl` FileType enum (FILE 5, DIRECTORY 2,
SYMLINK 4) and uses the component-owned scratch mount directly. This removes the
custom inbox-directory alias and directory-error workaround. The targeted
regression fails against the former adapter; 35 focused tests, typecheck, lint
and normal Debug build gates pass afterward.

The one corrected native retest still shows no selectable report. Its exact
visible response is recorded in the receipt. The per-file JavaScript bridge
metadata/error payload was not captured; native IDL values alone do not prove
what that bridge returns. No vendor defect, successful link refusal or successful
selection is inferred. This branch remains outside main, and another build
without the missing bridge observation is deferred.
