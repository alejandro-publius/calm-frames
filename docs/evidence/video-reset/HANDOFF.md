> Integration review: see ../acadia-integration-2026-10-15.md for corrected
> evidence, trust scope and current blockers. This is Claude's historical
> handoff, with factual and review-safety corrections applied during integration.

# Video reset, pipeline lane: handoff to Codex

Written Oct 15, 2026 on branch `claude/video-reset-2026-10-15`, a worktree at
`/Users/alexvintera/calm-frames-claude-video-2026-10-15` created from the
preserved head `ee76cf559a5814183bc005de57512ee08a10fb5a`
(`codex/home-comparison-2026-10-15`, app source `689c484`). Nothing under
`app/**` was touched. The commit is the branch head; `git log -1` names it.

## 1. What was done

One real-motion, public-domain video went through the existing analyzer,
preparation and package export path, with every step's hash recorded; the
detector gained fifteen boundary tests with four negative controls; and a
machine-readable evidence summary now exists with one generated example.

**The clip.** National Park Service, NPGallery asset
`6fc09aec-7fc2-47ed-b8cc-e1b10861dd3e`, "Acadia B-Roll: Coastal Scenery",
"a series of clips of waves crashing against rocky shores and coastal views".
The page lists its constraints as "Public domain: Full Granting Rights" and
credits "NPS Video"; no NPS endorsement is implied. The 720p proxy
(`.../GetAsset/<id>/proxyhires`, served as `<id>HiResProxy.mp4`) was retrieved
at 2026-10-15T20:38:16Z: 4,049,669 bytes, SHA-256
`2fecba5664992fc6aa321c10fed6f735394a0cce4af6349bd59ef28a6f397f28`, H.264 High
1280x720 yuv420p, BT.709 tagged, limited range, 48000/1001 frames a second,
1804 frames, 37.642 s, AAC stereo. The page lists the original at 67.4 MB; the
proxy is what was analyzed. The ledger row is in `media/LICENSES.csv`; the file
is `media/HAZARD_nps_acadia_coastal_broll_720p.mp4`, outside git.

**The findings are real, and they are why the file carries `HAZARD_`.**

| Run | Settings | Result |
|---|---|---|
| `flashmap check`, WCAG profile, no room | 192 px working width, trailing 1 s window, area over a quarter of the 10 degree window | 1 general flash span, 9302 to 11532 ms, 10 flashes in its worst second, 0.511 of the window |
| `flashmap check`, broadcast profile, no room | 192x108 whole-picture window; BT.1886 delta 20 nits, dark below 160 nits at an assumed 200-nit peak; informative pattern rule | 0 spans |
| pipeline preparation, every preset, 85 inch at 4 feet | the pipeline's fixed strictest room adds a 22 by 22 px room window | 3 spans per preset: 8343 to 9864 (broadcast ends at 9906), 9135 to 11699 and 29113 to 30593 ms; the WCAG map marks only the middle one as breaking its baseline window |

Merged, that is two distinct spans: 8343 to 11699 ms (seven segment observations
across four map files; breaks the WCAG baseline) and 29113 to 30593 ms
(room window only). Nobody has looked at either span, on purpose: the source
is read only by the analyzer and the plot tool. Nothing was simulated; no
threshold was changed. The plots are in `results/video-reset/acadia/plots/`.

**The preparation.** `pipeline.local_library.prepare_local_title` with a
temporary Ed25519 key that was deleted with its directory (the public half is
`results/video-reset/acadia/acadia-import.pub.pem`), then
`pipeline.packaged_library.export_packaged_library` and `check_packaged_library`:

| Step | Result |
|---|---|
| Receipt | `ready`, presets wcag, broadcast, extra-cautious; verification `passed`, outcome "cover proven drawn", checked inputs `cd7f9504…`, report `0c9f243d…` |
| Cover plans | wcag and broadcast: 7843 to 12199 and 28613 to 31093 ms (guard 500 ms, minimum 400 ms); extra cautious: 7343 to 12699 and 28113 to 31593 ms (guard 1000 ms, minimum 800 ms) |
| Bundle | `4bab8d81f779d7cf0eac3f5e2fe5372e88e95088fb068680818b28865dc6ad13`, one title, six files, every hash matches the manifest; `check` and `check --require-reports` both `ready` |
| Renditions | wcag and broadcast `9baa7a90148bdda7…` (byte for byte the same file, same plan); extra cautious `00a214650090bdab…`; all 1280x720 at 48000/1001, 37.621 s, audio copied |
| Signed maps | wcag `709dbd76…`, broadcast `d95fc4aa…`, extra cautious `c6bcb945…` |
| Public key | SHA-256 of the base64 text `68fef375357ae81f…` |

Where everything is, in the worktree (build output, outside git):
`build/video-reset/prepared-library/` holds the bundle directory, `catalog.json`
(26,430 bytes, `ad74eb70…`), `catalog.ts` (30,194 bytes, `cffa3f09…`) and
`reports/`; `build/video-reset/local-library/` holds the receipt and the work
tree. Committed copies for review: `results/video-reset/acadia/` (the two
standalone maps, `pipeline-maps/`, `local-receipt.json`,
`prepared-manifest.json`, `verification-report.json`, the public key, the plots
and `evidence-summary.json`), `results/video-reset/negative-controls.json` and
`results/video-reset/tamper-check.json`.

**Tamper check** (`results/video-reset/tamper-check.json`): on a copy of the
bundle, the untouched copy is accepted; one byte flipped in a rendition, one
byte flipped in a signed map, a rendition swapped for another preset's, an
edited manifest hash and an edited map text are each refused. The plain check
accepts a bundle whose verification report attachment is missing, as its own
documentation says; the strict gate (`--require-reports`, what
`scripts/release.sh` runs) refuses it. Fail-closed behaviour was not changed.

## 2. Changed files

- `flashmap/tests/test_video_reset_boundaries.py`: fifteen tests fed as numbers,
  not files: the inclusive one-second window (four flashes exactly one second
  apart fail, one millisecond wider passes, a gap does not carry old flashes
  forward, the hidden interval starts a second before the fourth flash), a
  repeated timestamp counted once, a backwards timestamp dropped, the
  48000/1001 cadence read as constant and timed to the microsecond, flashes
  counted by timestamp at that cadence, flashing over exactly a quarter of the
  reference window passes and 24 pixels more fails; a separate `max_coverage`
  unit check adds exactly one pixel above a quarter, a frame of NaN neither crashing nor counting, and an audio-only, an
  empty and a noise file refused by `probe`.
- `pipeline/evidence_summary.py` and `pipeline/tests/test_evidence_summary.py`:
  the evidence contract and nine tests; `docs/evidence/video-reset/EVIDENCE_SUMMARY.md`
  describes it.
- `media/LICENSES.csv`: the clip's row; `eval/attribution.py`: its title in
  `TITLES`; `NOTICE`: regenerated by that script. The script also regenerates
  `app/src/calmframes/credits.ts` (eight added lines); that file is under
  `app/**` and was restored untouched, so one attribution test stays red on
  this branch until Codex runs the script (section 5).
- `results/video-reset/**`: the evidence named above.

## 3. Reproduction, verified in this checkout

```sh
export PYTHONPATH="$PWD:$PWD/flashmap/src"
PY=/Users/alexvintera/calm-frames/.venv/bin/python
$PY -m flashmap check media/HAZARD_nps_acadia_coastal_broll_720p.mp4 --profile wcag --json /tmp/acadia.wcag.json
$PY -m flashmap check media/HAZARD_nps_acadia_coastal_broll_720p.mp4 --profile broadcast --json /tmp/acadia.broadcast.json
$PY eval/plots.py media/HAZARD_nps_acadia_coastal_broll_720p.mp4 -o /tmp/acadia-plots
$PY -m pytest flashmap/tests/test_video_reset_boundaries.py pipeline/tests/test_evidence_summary.py -q
$PY -m pipeline.packaged_library check --output build/video-reset/prepared-library --require-reports
```

The preparation itself is `.logs/video-reset/prepare_acadia.py` in the worktree
(it mirrors `eval/prepare_owned_harbor.py`: a temporary key, `prepare_local_title`,
`export_packaged_library`, `check_packaged_library`); it takes about six
minutes and reads the source from `media/`.

## 4. Tests and negative controls

`flashmap/tests/test_video_reset_boundaries.py`: 15 passed. Each of four
deliberate breaks of `flashmap/src/flashmap/analyze.py` was applied alone, the
file run, and the file restored (`git diff` empty) before the next:

| Break | Tests that went red |
|---|---|
| more than three becomes three or more (`counts >=`) | 5 |
| more than a quarter becomes a quarter or more (`value >=`) | 1 |
| the flash exactly one second earlier is dropped from the window (`<=` in the pop) | 3 |
| a repeated presentation timestamp is counted (`<` in the skip) | 1 |

Details, including the test names, are in `results/video-reset/negative-controls.json`.
The synthetic frames are solid grey arrays with exact timestamps; they
exercise counting, timing, area and input refusal, not codecs, camera noise or
colour transforms, which the existing suites cover with generated clips. A
test that watches a line is not evidence of clinical protection. Loop boundaries remain unverified. Chunk equivalence tests and reuse of a
static map do not establish the displayed last-to-first transition during replay.

The analyzer and pipeline suites (`pytest flashmap pipeline -m "not slow"`)
were run once before this handoff: 867 passed, 2 deselected, in 3 minutes 30.
`eval/tests/test_attribution.py`: 10 passed, 1 failed, the one that compares
the committed `credits.ts` with the generator's output (see section 2). ruff
and the repository style check pass on the changed files. Strict mypy is not
installed in this environment; hosted CI runs it.

## 5. What Codex integrates, and the native checks still required

1. Only after explicit approval of this exact bundle and public key, copy the bundle directory `build/video-reset/prepared-library/4bab8d81…`
   and `catalog.json` / `catalog.ts` into the app's prepared-library location
   and catalog import, the way `eval/prepare_owned_harbor.py` outputs are wired
   today. The maps are signed by a new key, so the app must accept its public
   key for exactly this bundle (`packagedLibrary.publicKeyFor`); the public PEM
   is beside the results. Do not merge this bundle into the Harbor bundle;
   they have different keys.
2. Give the title its shelf entry (title, artwork, hold count from the map) and
   its credit line on the credits screen from the ledger row: "NPS Video,
   Acadia National Park. No NPS endorsement is implied." The attribution
   generator already has its TITLES entry and NOTICE is regenerated; run
   `.venv/bin/python eval/attribution.py` once in your checkout to regenerate
   `app/src/calmframes/credits.ts` (eight lines), which clears the one red
   attribution test.
3. Read `results/video-reset/acadia/evidence-summary.json` for the Details page:
   `findings.distinct_spans` are the findings (two; one breaks the WCAG
   baseline), `findings.simulated` is empty, `independent_validation` is
   `pending`. Do not show a green badge.
4. Native checks, in this order: install the package with the bundle, play
   the wcag rendition and confirm the two covered spans (7.8 to 12.2 s and
   28.6 to 31.1 s) hold the picture with audio continuing; seek into each span
   and confirm the cover is on before the picture moves; play the extra
   cautious rendition and confirm its wider spans; confirm the title's page
   reads the summary's findings and states; confirm the Harbor demo still
   plays unchanged. Nothing here has run on the device yet.

## 6. Independent validation and owner decisions still needed

- Do not ask anyone to watch the original hazardous source. Use numeric,
  offscreen evidence for this audit. A descriptive scene label is not a
  requirement for accepting or rejecting the measured findings.
- The owner decides whether to ship this title and its credit, and whether
  the broadcast rendition, identical to the wcag one, should be listed twice.
- Independent validation of the detector against anything outside this
  repository remains pending; this summary does not claim it.
