# Read a caregiver review on the TV

The implemented Parents inbox selects staged reports from the existing caregiver-computer intake.
Fixed native selection acceptance is still pending in the receipt.
This is a read-only report inbox, not a system file picker or video importer.
Original media is neither transferred nor played by this flow. A report never
adds a library title, signer or playback permission.

## Prepare and transfer a report

1. Use the [local caregiver page](overnight-2026-10-25/personal-import/README.md)
   on your computer. Select a non-DRM video you own or have permission to process,
   confirm processing permission, analyze it, then choose **Save caregiver review
   (JSON)**. Keep its generated `calm-frames-review-<job-id>.json` name.
2. Start the installed TV app. In Developer Mode, use the SDK's documented
   [component scratch transfer](https://developer.amazon.com/docs/vega/0.24/developer-mode#file-operations).
   Target your intended device explicitly. Create only this report directory:

   ```sh
   vega exec vda -s <device-serial> shell -t component-id io.github.alejandropublius.calmframes.main 'mkdir -p /scratch/calm-frames-reviews'
   vega device copy-to --device <device-serial> --source path/to/calm-frames-review-<job-id>.json --destination /tmp/scratch/io.github.alejandropublius.calmframes/calm-frames-reviews/calm-frames-review-<job-id>.json
   ```

   Use an exact destination filename, not only a trailing directory. Do not copy
   original media, keys or household files. Scratch is a development transfer
   area, not durable installed content or an end-user sharing service.
3. Open **Parents**, unlock normally, then choose **Personal file reviews**.
   Refresh, select a report and read its file identity and reported plans.
   Back returns to the list and then to the exact Parents opener.

Product limits are eight report files and a bounded report size, enforced
in [caregiverReviewInbox.ts](../app/src/calmframes/caregiverReviewInbox.ts).
Non-report names, links, oversized or malformed reports, absent processing
permission and playback-authorization claims are refused. A damaged report is
isolated from intact ones. Selection rechecks the staged bytes. The app does not
independently rehash the original video or authenticate the report's author;
those limitations are visible beside the report.

## Exact boundary

The installed [file-system API](https://developer.amazon.com/docs/vega-api/0.24/interfaces.KeplerFileSystem.amazon-devices_kepler-file-system)
provides sandbox file operations, not a documented system picker. This addition
supplies native report selection and viewing using the existing report format.
Arbitrary TV video selection remains unimplemented. Do not describe the inbox
as direct personal-video playback or production file import.

Preparation and activation still require an existing authorized signer, exact
edition approval, verified export and a checked app build/installation. No new
signer or trust root was introduced. The current generated-input check correctly
stops at signing_blocked when no signer is configured. Rights/DRM refusal,
protection floors and compiled membership remain unchanged.

The [receipt](../results/personal-review-inbox-2026-10-26.json) records
<!--n results/personal-review-inbox-2026-10-26.json:focused_tests.passed -->28<!--/n-->
focused tests, typecheck, targeted lint, a normal Debug build and exact fixture
identities. The validation package has a separate application identity and
fictional data; it does not replace the existing app household. Native UI
observations are recorded separately in that receipt. No Release, medical,
comfort or whole-item-13 acceptance is inferred.

## SDK directory compatibility

The native run rejected directory metadata with the structured response
`[com.amazon.kepler.file_system.IsADirectoryError]: `. The correction recognizes
only that precise response with noFollow still true; other metadata failures,
resolved link types, file limits and report refusals retain their guards. Its
regression fails before the correction and passes afterward. Temporary diagnostic
UI and API probes are removed. Source merge readiness does not close original
item 13 or imply final native acceptance.
