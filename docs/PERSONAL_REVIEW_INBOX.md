# Read a caregiver report on the TV

The Parents inbox selects reports exported by the existing caregiver-computer
intake. It does not select or import raw videos, add a playable title, recheck
the original file on the TV or grant signing/playback permission.

## Transfer and read

1. Use the [caregiver-computer page](overnight-2026-10-25/personal-import/README.md)
   to select a non-DRM file you own or have permission to process. Confirm
   processing permission, analyze it, then save the caregiver review JSON.
   Keep its generated `calm-frames-review-<job-id>.json` filename.
2. Start the installed app on your intended development device. Use the SDK's
   [component scratch transfer](https://developer.amazon.com/docs/vega/0.24/developer-mode#file-operations)
   with the exact destination filename:

   ```sh
   vega device copy-to --device <device-serial> --source path/to/calm-frames-review-<job-id>.json --destination /tmp/scratch/io.github.alejandropublius.calmframes/calm-frames-review-<job-id>.json
   ```

   Use the component-owned scratch root directly. Do not create an intermediate
   inbox directory or link. Transfer only the exported report, never household
   files, keys or original media. Scratch is a development transfer area, not
   durable installed content or an end-user sharing service. The current inbox
   allows at most eight staged entries and bounds each report before reading.
3. Open **Parents**, unlock normally, then choose **Personal file reviews**.
   Refresh and choose the report to read its original-file identity and reported
   plans. Back returns to the selected report, then the Parents opener.

Reports must retain the existing schema, confirmed processing permission,
non-playable status and absence of TV playback authorization. Unknown names,
links, directories, oversized and malformed reports are refused. One refused
entry does not prevent an intact report from appearing. Selection rereads the
current report and refuses changed bytes.

## Scope and trust

The TV does not independently rehash the original media or authenticate the
report's author. A displayed report is not medical safety, comfort, rights or
seizure-prevention validation. Existing rights/DRM refusal, protection floors,
signed media and compiled membership remain unchanged.

Arbitrary native TV video selection remains unimplemented. Exact-edition
preparation/activation still requires existing authorized signing authority,
approval, verification and a checked build/install. The generated fixture
correctly stops at `signing_blocked` without a signer. Original item 13 stays
partial; report readback alone does not finish the personal-video journey.

## SDK correction and evidence

The installed JavaScript declaration annotates `Metadata.mode` as an open mode.
Read-only debugger observation of the actual 0.24.9914 / file-system 0.0.7 bridge
instead returned `entryType: "5"` for the owned regular report, `"4"` for its
symlink, no `mode`, and `IsADirectoryError` for the directory. The sanitized
[bridge observation](../results/personal-review-bridge-metadata-2026-10-26.json)
records these values. The adapter accepts only the regular native file type;
it does not infer file type from open modes or POSIX bits.

The [receipt](../results/personal-review-inbox-2026-10-26.json) separates earlier
failed attempts, the successful native debugger-connected list/readback and
final packaged validation. The focused regressions fail against the preceding
adapter and summary-offset behavior. Those dated Debug observations do not
establish Release or VoiceView acceptance. Raw captures remain outside the repository; only sanitized evidence
identities are published.


## Release navigation correction, October 26

The canonical Release exposed a summary-opening defect: native focus scrolling
hid the header Back. A keyed-scroll attempt also failed and remains unpublished.
Navigation now sits outside the report scroller and requests the supported
native host focus after its measured layout. First and repeated summary opening,
D-pad reading of essential limitations, visible Back activation, malformed-report
refusal and both return-focus targets passed on the isolated 720p Release device.
See the [exact package and native receipt](../results/report-summary-release-2026-10-26.json).
This bounded pass does not establish 1080p, VoiceView, owner comfort, new-edition
activation or full Release acceptance. Original item 13 remains partial.
