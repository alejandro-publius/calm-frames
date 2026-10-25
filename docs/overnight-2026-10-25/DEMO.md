# Demo tooling and review inputs

Original items 16 and 8 remain partial and human-blocked respectively. The
machine-executable assembly work is ready for actual accepted-build inputs.
The source reviewed is `15ef46c6e23c8ba627492da23b1b147000031aa4`; the approved
[storyboard](../cloud-integration-2026-10-23/demo/STORYBOARD.md) and narration
text are unchanged. No paid API call, image generation, native capture,
publication or submission edit occurred.

## Completed tooling work

The renderer previously accepted a muted ambient passage, and a closing card
cut short while its generated subtitles extended beyond the movie. It also
started the encoder when an input file changed after preflight. Regression
checks reproduced each behavior. The corrected renderer preserves the actual
ambient audio gain and complete closing-credit hold, rechecks the manifest and
capture receipts, and encodes private input snapshots whose bytes match the
declared hashes. Later edits to a source file cannot alter those snapshots.

The output receipt now records the selected native package hash, capture-receipt
hashes, renderer hash, tool versions and selected source intervals. It retains
human acceptance as pending. No receipt contains private input paths.

An actual full-length encode exercised the existing recipe using a static card
that visibly says TEST ONLY and digital silence. It is not app footage, narration
or a product demonstration. The manifest fails normal production preflight.
The isolated output has its own test-only receipt, subtitle labels and filename.
Full decode, frame inspection, subtitle ordering and the repository video gate
passed on those synthetic bytes. This does not validate missing native footage,
the eventual speech mix, app timing or human comfort.

See the [machine receipt](../../results/overnight-2026-10-25/demo/receipt.json)
and [renderer checks](../cloud-integration-2026-10-23/demo/test_render_preflight.py).
The fixture generator is
[render_smoke_test.py](../cloud-integration-2026-10-23/demo/render_smoke_test.py).
The encoded test file stays outside Git and is not included as a presentation asset.

## Actual asset availability

The [inventory](../../results/overnight-2026-10-25/demo/asset-inventory.json)
hashes the available repository media and historical native screenshot references.
The media files are app content, menu sounds, tests and a labelled browser
approximation. None is an actual current-source app-window recording. No native
motion takes, narration audio or finished story illustrations were received in
the shared transfer workspace. Historical screenshots remain useful references;
they cannot substitute for the missing motion footage.

The current [missing-input manifest](../../results/overnight-2026-10-25/demo/missing-inputs.json)
names each shot, its minimum source interval, the unchanged spoken cue windows,
provenance requirements and the two evidence ZIPs mentioned in Claude's handoff.
Those archives' hashes are reported identities, not bytes inspected here. Their
eventual contents must be checked before treating anything as eligible footage.

## The next bounded production step

After the accepted product source and installed package are selected, reconcile
the unchanged script with that exact build. Use a private copy of the historical
timeline and replace every stale source/package field with verified identities.
Provide the actual raw takes and their original hashed capture receipts. Check
frame/audio coverage, selected intervals, licensing and capture scope. Preserve
the real opening and disclose omitted waiting; no looped or stretched footage.

Story illustrations and ElevenLabs narration remain parked. The script, calm
built-in voice selection and budget were previously authorized; overnight work
does not authorize a purchase or generation. Secure API access and the actual
voice ID are still missing. Do not request keys in chat or ask again for the
already granted script/voice preferences. Show any material wording revision
before producing changed narration.

Once actual inputs exist, run the normal preflight, render and exact-file video
gate. Keep source clips, their hashes and the edit ledger. The synthetic tool
test must never be renamed or presented as that product video.

## Morning human review, item 8

Review only the identified installed candidate or a later explicitly selected
build. The last received Mac receipt names code `a672f57` and package SHA-256
`8cc0ffd52fc61df17d8b69b40c31964c5ed0749c578ec1de67e1aedf78173dd8`.
Its binary was not transferred to this cloud worktree.

- Record the package identity before picture, audio, palette, pacing and reading
  comfort observations. Stop any uncomfortable playback; no hazardous sample is
  required for review.
- Decide the onboarding disclaimer layout separately. Native navigation evidence
  does not determine the preferred resting layout.
- After actual narration exists, listen for wording, pronunciation and artifacts.
  Then watch the entire actual cut at natural speed with its mixed audio.
- Check that the delivery player displays the sidecar subtitles. Merely writing
  an SRT does not make captions visible in every player.
- Leave publication and frozen submission changes for a separate owner decision.

No source test, encoded fixture, video gate or general approval to continue
supplies those human observations or medical validation.
