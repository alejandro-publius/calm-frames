# Native name-editor receipt reviewed

Fable's evidence ZIP is received and readable. Its source and lockfile match
the preserved Mac snapshot `6a87937f9f185ac0760d6f8331184e34b876d92c`.
The installed-device log reports the same SHA-384 as the package recorded by
the Mac operator. The [transfer verification](../../results/design-polish-2026-10-23/native-names-acceptance/transfer-verification.json)
records file hashes, source checks, package identity and the limits below.

This closes the receipt-transfer and source-reconciliation work in item 18.
It advances native portions of items 5 and 11; it does not close every
acceptance criterion or validate later cloud commits.

## Exact evidence

| Record | Identity |
|---|---|
| Received ZIP | `calm-frames-names-acceptance-6a87937-evidence.zip` |
| ZIP SHA-256, computed here | `7398282249be7ac2d87fdacfa9494185dc41ae5fd2f738b205db5010d7e6a463` |
| Checked code underlying the Mac source | `0102622c1985ef0f7927d7fc434a15a9d2c2e278`; app inputs match `6a87937` |
| Native package SHA-256, recorded on Mac | `623615034f69586886d57a8b6f582a814d74cce6f58f21cdf4ebba5f3fd8259d` |
| Native package SHA-384, matching the supplied installed-device log | `b268be9946241be7e8efab64737e6672b907dfb2d9558cae6a90acb51349b1b02b63e68a7ea63fe4d259a8db432eb458` |
| Rollback SHA-256, recorded on Mac | `e3458d5a59e6d68cd96b50e1ebe4784c1bdfbcbcadca3b1a8b6ba4c3f7b9b3c5` |

All checksum-index entries match the actual received files. The native binary
and rollback binary are absent, so their hashes were not recomputed in cloud.
The original larger archive is also absent. Its reported hash does not mean
that its bytes were read here. The original receipt is preserved unchanged;
this review qualifies its scope separately.

## What the native record supports

The operator recorded
<!--n results/design-polish-2026-10-23/native-names-acceptance/receipt-review.json:operator_counts.passed -->21<!--/n-->
passed checks, with
<!--n results/design-polish-2026-10-23/native-names-acceptance/receipt-review.json:operator_counts.unobserved -->2<!--/n-->
unobserved checks and an owner comfort review still pending. Those counts
describe the received checklist, not the original 20 project outcomes.
The [per-check review](../../results/design-polish-2026-10-23/native-names-acceptance/receipt-review.json)
keeps every recorded status and states the supported scope.

- Parents remained behind the PIN. Selecting a kid exposed Edit name; the
  household-wide choice did not. The letter grid opened with the current name
  and first-key focus.
- Remote-driven key travel, word capitalization, Shift, Space, Delete, blank
  refusal and the length limit were observed. Entry remains letters and spaces.
- Save persisted the rename through explicit app termination and relaunch.
  Cancel, device Back, header Back and the Parents footer cancelled editing
  before leaving Parents. Focus returned to Edit name. The
  [trace summary](../../results/design-polish-2026-10-23/native-names-acceptance/trace-corroboration.json)
  corroborates relevant control transitions, without exporting private key events.
- Two profiles retained distinct saved places through the rename. The
  temporary test name was restored. This is position isolation, not proof of
  different protection presets or caption restoration.

Two recorded passes need narrower wording. **Still routes:** Acadia's still
scene opened; Sea Otters and Forest reached Details only. **Duplicate names:**
the household label was rejected, but a sibling kid's name was not entered.
Keep those as partial native observations; source tests cover additional cases.

## What remains open

| Item | Remaining evidence |
|---|---|
| 5 | Native failed-write/retry remains unobserved. Use only a controlled isolated fixture; do not damage household storage. Sibling-name rejection was not exercised natively. |
| 11 | VoiceView announcements remain unobserved. The log contains a missing AccessibilityManager diagnostic, which does not prove the feature is absent on every Vega device. Reduced-motion acceptance is also outside this pass. |
| 8 | Owner picture, audio, palette and reading-comfort observations remain pending. |
| 7 | Sea Otters and Forest still playback were not opened in this pass; no new sustained moving editions are supplied. |
| 6 | The Parents footer was traversed. That does not validate the isolated first-run onboarding footer. |
| 9-10 | Profile position isolation does not establish differential protection restoration or exhaustive compositor/decoder ordering. |
| 1, 4, 14-15 | The manifest indexes native captures, but their image bytes were excluded. Independent visual inspection and a current native presentation gallery still need the existing cropped images, not a new capture run. |
| 12 and later build selection | Ajv/Zod, logger and private-input trace follow-ups are outside the installed `6a87937` snapshot. The selected combined source needs its own build identity and appropriate checks. Audit findings and expired exceptions remain open. |

## Privacy and receipt corrections

The evidence notes disclose PIN-key focus traces in the original device log.
That supersedes the original README's broader assertion that no PIN digits
were recorded. The received log matches the declared redacted hash and contains
no lines matching the disclosed PIN-focus pattern. The original log is absent,
so the claim that all other lines remained unchanged cannot be independently
reconstructed here. Raw logs, household values and private Mac paths are kept
out of this committed review.

Cloud fix `07db296137ec3ba50afff15097053061709fda27` suppresses private name/PIN
key focus traces. It is locally checked and is not installed by this receipt.
Release silence comes from the existing `__DEV__` guard; Babel retains
`console.warn`, so console stripping is not the explanation.

The final redacted log's line count agrees with the manifest's removal
arithmetic. The earlier receipt has a different pre-redaction count. Capture
hash references agree with the manifest; an extra baseline image pair is
outside the ledger's snap events. These metadata differences are recorded in
the review and do not require repeating the native checks.

No attached script was executed. No build, simulator action, push, merge,
publication, media generation or change to the submitted fallback occurred.
