# Evidence index

One page for a judge or a reviewer: what Calm Frames is for, what it does and
does not do, how it is built, which checks have run, and where each kind of
evidence stops. Everything below links to a committed record. Where a record
is a receipt, its numbers were written by the command it names.

Read with the [documents index](../README.md), [SAFETY.md](../SAFETY.md) and
the [submission packet](../submission/README.md).

## Who it is for and the problem

Families with a child who is photosensitive, and anyone who wants to put a
chosen video on the television without watching for flashing themselves.
Flashing above the published limits in WCAG 2.2 and ITU-R BT.1702-3 is what
the analyser looks for. The product covers those moments in a prepared video
while the sound continues, and says so on screen.

Calm Frames reduces exposure to flashing above published limits in the videos
it plays; not a medical device. It is not clinically validated and it does not
prevent seizures.

## What is supported, and what is not

Supported:

- Fire TV through Amazon's Vega SDK 0.24, built and checked on the Vega
  Virtual Device. The app plays only the prepared videos compiled into it.
- The featured video is Acadia, a National Park Service public domain clip,
  prepared by the pipeline into three renditions (Standard, Broadcast, Extra
  cautious) with signed maps.
- A general flash cover and a red flash cover, from maps produced before the
  video was added. Covers are plain black for Acadia; a signed scene still is
  drawn only when a map carries one.
- A D-pad remote: Watch, Details, More info, Technical details, Parents,
  Back, pause, seek. Every seek goes through one guarded function.

Not supported, on purpose:

- Netflix, Prime Video, other apps, live television, HDMI inputs or any
  arbitrary stream. The analyser never runs on the television.
- HDR sources. The decoder refuses PQ and HLG.
- Any claim that a video is safe. The approved sentence is the only safety
  wording the app uses, and the detector can miss flashing.

## How it is built, in one paragraph

A video is analysed offline by `flashmap` (Python, in `flashmap/`), frame by
frame at a working width, against the WCAG and broadcast rules in
[SPEC_SOURCES.md](../../flashmap/docs/SPEC_SOURCES.md). The result is a flash
map, signed with Ed25519. The pipeline (`pipeline/`) prepares a rendition per
preset, verifies that every covered frame is covered, and compiles the
catalog, maps, renditions and the public key into the app. The app
(`app/`, React Native for Vega) lists only titles whose maps verify against
the exact source hash and the compiled key, and the player checks the maps
again before it opens a file, covers each interval before it starts, and keeps
the picture hidden if anything about the route or the map is wrong. The audit
of that chain, step by step, is in
[tv-experience-2026-10-16.md](tv-experience-2026-10-16.md).

## Checks that have run, with the commands

| Check | Record | How to reproduce |
| --- | --- | --- |
| App unit and screen tests, typecheck, lint on the current source | [tv-experience receipt](../../results/tv-experience-2026-10-16/receipt.json) | commands in the receipt, run from `app/` |
| Acadia as the only main choice, Harbor retained as fixtures | [acadia-first receipt](../../results/acadia-first-2026-10-16/receipt.json) | commands in the receipt |
| Prepared library integrity (catalog bytes, bundle, reports present) | same receipt, `prepared_library` | `node app/tools/check_prepared_library.mjs` |
| Detector concurrent-area review, production rule characterised | [detector-area-review-2026-10-16.md](detector-area-review-2026-10-16.md) | `PYTHONPATH="$PWD/flashmap/src:$PWD" python -m pytest eval/tests/test_concurrent_area_review.py -q` |
| Detector candidate against baseline, fixtures and real footage | `docs/evidence/detector-concurrency-2026-10-16.md` on the branch `claude/detector-concurrency-2026-10-16` | commands in that document and its receipt |
| Conformance numbers published in the README | [conformance record](../../results/conformance_current_full_2026-10-02.json) | `python eval/readme_sync.py --check` and `eval/tests/test_measured_sources_unchanged.py` |
| Earlier positive real videos, recovered by hash and re-run | [earlier-positive-2026-10-15.md](earlier-positive-2026-10-15.md) | command in that document |

The detector review and the detector candidate live on a separate branch so
the app source and the detector experiment stay reviewable apart. Neither
changes a signed map or a shipped rendition.

## Detector baseline and candidate, and what is unresolved

The production rule can combine flashes from different moments inside one
second into one area. The review reproduced it and the design proposed a
duration-aware refinement. A candidate now exists, opt-in, beside the
production rule, with the production files byte for byte unchanged. On the
written schedules it suppresses the separated-burst counterexample and keeps
every overlap control; on the real footage available locally its baseline
replay matches the production analyser everywhere, the lightning positives are
unchanged, and the otter clips lose a small fraction of their covered time.
The exact numbers, the semantics it assumes, and the questions still open
(the red rule's end bound, moving regions, same-direction re-confirmations)
are in the candidate's own evidence record on its branch. It is not a
production change and no map was regenerated.

## Real video provenance and licences

| Video | Source | Licence | Where recorded |
| --- | --- | --- | --- |
| Acadia coastal scenery | National Park Service, NPGallery asset 6fc09aec-7fc2-47ed-b8cc-e1b10861dd3e | Public domain, no NPS endorsement implied | [acadia-integration-2026-10-15.md](acadia-integration-2026-10-15.md), `NOTICE` |
| Harbor (demo and prepared film) | Original artwork made for this project | Project licence | `app/assets/raw/benign-story/README.md` |
| Otter candidates | USFWS Pacific Southwest (public domain); Uusijani, Wikimedia Commons (CC0 1.0) | As stated | [otter-candidate-2026-10-16.md](otter-candidate-2026-10-16.md), [otter-grooming-candidate-2026-10-16.md](otter-grooming-candidate-2026-10-16.md); not integrated |
| Evaluation pool | 35 sources with URL, licence, credit line and hash | Per row | `media/LICENSES.csv`; the files themselves are not in the repository |

## The source revision and what is installed

- App source for review: branch `claude/tv-experience-2026-10-16`, based on
  `63a0bcb` (`codex/dark-cinema-2026-10-16`). See
  [CLAUDE_REVIEW_HANDOFF.md](../../CLAUDE_REVIEW_HANDOFF.md) for the exact head.
- Detector candidate: branch `claude/detector-concurrency-2026-10-16`, based
  on `5e5e88c` (`codex/detector-area-review-2026-10-16`).
- Installed on the simulator: the dark cinema build from app source `d67e1da`,
  package `build/release/dark-cinema-2026-10-16/calm-frames-0.1.0-aarch64-debug.vpkg`,
  per [FINAL_HANDOFF.md](../../FINAL_HANDOFF.md). It predates the Acadia-first
  change and everything on the two branches above. Nothing in this pass built,
  installed, launched or captured it.

## Four kinds of evidence, kept apart

| Kind | What it establishes | Where |
| --- | --- | --- |
| Synthetic fixtures | Rules and boundaries on numbers and tiny generated clips: pairing, thresholds, windows, chunking, the candidate's overlap logic. Generated hazardous clips are made, analysed and deleted in the same test. | `flashmap/tests/`, `eval/tests/` |
| Real video processing | What the analyser and the pipeline produce on real files: maps, renditions, verification reports, the baseline and candidate comparison. Headless; no file is displayed. | `results/`, `docs/evidence/` |
| Simulator | What the app did on the Vega Virtual Device, from its logs: routes, focus requests, media events, cover requests. Logs do not show pixels, visible focus, paint order or audible sound. | receipts named `native` in `results/`, [FINAL_HANDOFF.md](../../FINAL_HANDOFF.md) |
| Physical device | None. No physical Fire TV, stick or television has run this build. [SCREEN_TEST_PROTOCOL.md](../SCREEN_TEST_PROTOCOL.md) describes the test that has not been run. | nowhere yet |

A result in one row is never written up as a result in another.
