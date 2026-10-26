# Caregiver review stays usable when one import record is damaged

The change at `4dea0cedeff562d59898d5f39cf3066d9151fa66` fixes two demonstrated
local-import defects. It does not change native playback, household data,
permissions, signatures, trust or the 60-second import limit.

Previously, an incomplete or malformed `job.json` could prevent startup or the
entire job list from loading, including a second intact review. The store now
shows that one entry as **Unreadable import** and keeps its files. It exposes
no review, approval, retry or delivery action from the damaged metadata. The
caregiver can explicitly remove that local copy and select the original again.
Removal stays within its validated job directory; it does not remove the
caregiver's original file.

If the record becomes unreadable while an owned worker is still active, the
UI keeps work active and offers Cancel first. A new upload or approval stays
blocked until that owned worker stops. The application never guesses a saved
review or rewrites the damaged record to appear valid.

The real HTTP check also exposed a small publication race: a worker could save
its completed review just before exiting. The page then offered approval while
the ownership gate still refused a second job. The page now shows the finishing
state until the worker has actually exited and been reaped. Ownership checks
remain in force; a saved result alone does not release them.

## Reproduction and checks

Use fictional temporary imports only, never a household's real files. Create
one intact review and one job whose metadata is truncated, missing or has an
invalid title/status/time. Restart the store and request `/jobs`: both entries
must remain visible, the intact report must work and the damaged record must
not authorize preparation. Explicit removal deletes only that damaged import.
Repeat with an owned child still running: Cancel must stop it before removal.

The [regression tests](../../pipeline/tests/test_intake_corrupt_record.py) and
[real HTTP regression](../../pipeline/tests/test_local_intake_http.py) cover
preservation, restart, safe refusal, worker ownership and the publication race.
The focused intake/delivery run passed 116 tests. Ruff and normal pipeline mypy
pass. The before-fix failures and final results are retained in
[checks](../../results/cloud-followup-2026-10-25/checks/).

A subsequent corrupted-timestamp case demonstrated that a JSON integer too
large for the finite-time check could still interrupt startup. It now becomes
the same unreadable placeholder. The targeted intake/HTTP rerun passes 54 tests;
this is an overlapping subset, not 54 additional independent outcomes.

The real local page was rendered in Chromium at 1100 by 850 and 390 by 844.
Keyboard Enter reached the explicit removal confirmation; focus is visible,
the narrow page has no horizontal overflow, and the run produced no page errors
or external requests with reduced motion emulated. Both images were inspected.
These are browser captures of the caregiver tool with fictional data, not
native Fire TV screenshots or VoiceView acceptance.

- [Desktop browser capture](../../results/cloud-followup-2026-10-25/browser/desktop.png)
- [Narrow browser capture](../../results/cloud-followup-2026-10-25/browser/narrow.png)
- [Browser checks](../../results/cloud-followup-2026-10-25/browser/checks.json)

Item 13 remains partial: verified local analysis and caregiver pre-check are
available, but direct TV file selection and a separately approved personal
edition are not supplied by this fix.
