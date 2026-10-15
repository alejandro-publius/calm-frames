> The summary is presentation data, not an authentication gate. `validate()`
> checks selected shape and count rules only. It does not bind files or verify
> signatures. `signature_present` means a field exists. Use the strict package
> check plus an approved compiled catalog for playback. Corrected output is in
> results/acadia-integration-2026-10-15/evidence-summary.json.

# The evidence summary, for the app

`pipeline/evidence_summary.py` writes one JSON file per video that the app can
read without parsing an HTML report. It composes records that already exist
(the media ledger row, the analyzer's maps, the local receipt, the packaged
manifest, the plots and the test record) and adds no measurement of its own.
`schema` is `calm-frames-evidence-summary-v1`. The generated example is
[`results/video-reset/acadia/evidence-summary.json`](../../../results/video-reset/acadia/evidence-summary.json).

## The four states, kept apart

| State | Where it lives | What it means |
|---|---|---|
| Actual findings | `findings.actual` (one entry per run and segment) and `findings.distinct_spans` (overlapping segments merged, with the runs that found each) | Spans the analyzer measured over a published limit, with the profile, the room and the window that triggered each. Zero is written as zero. |
| Simulated events | `findings.simulated`, each with `detected: false` | Covers scheduled on purpose, for practice or demonstration, such as Harbor's two practice holds. Never counted as findings. |
| Unsupported or not analyzed | `findings.unsupported_or_not_analyzed` | What no measurement in the summary covers: the audio track, rooms not measured, HDR inputs (refused, not measured), rules not applied. |
| Independent validation pending | `findings.independent_validation`, `pending` or `done` | Nobody outside this repository has checked the findings, the preparation or the playback. Re-analysis by this repository's own analyzer does not count. |

`states` repeats these four definitions inside every file so a reader of the
JSON alone has them. `validate()` refuses a summary that drops a state, that
marks a simulated event as detected, whose counts disagree with its lists, or
that contains "seizure-proof", "prevents seizures", "clinically validated" or
"universal filter".

## The fields

- `source`: the ledger row (file, SHA-256, origin, licence, credit, the date the
  licence was checked, duration, resolution, notes) and, from the first map, the
  container facts (bytes, coded size, frame rate, frame count, first and last
  timestamps, whether the rate varied, the timestamp source) and the colour
  decision. `hazard_prefix` says whether the file carries `HAZARD_`.
- `analysis.runs`: one entry per map: profile, path and SHA-256 of the map,
  whether a signature field is present, the analyzer name and version, and the settings that
  matter (working width and height, working color model and separate profile-specific luminance rules, flash limit and window,
  area limit, every area window with its size, the room if one was set, whether
  the pattern rule applied, what the picture was measured on), then the map's
  summary and its segments.
- `findings`: the four states above, plus `actual_count`, `distinct_spans` and
  `distinct_span_count`. A distinct span carries the widest bounds any run gave
  it, `found_by` (profile, map, room, reason, area), `found_in_runs` (unique map paths), `segment_observations` and
  `breaks_wcag_baseline`, which is true only when a run broke the WCAG
  reference window rather than only a room window.
- `preparation`: `status` is `ready`, `failed`, `not run` or `unknown`; the
  local receipt (path, SHA-256, source hash, title, presets, verification
  outcome, `physical_tv_validated`, and the artifact hashes per preset) and the
  packaged manifest (path, SHA-256, bundle id, the SHA-256 of the public key
  encoded as base64 text (not the raw-key fingerprint), and per title the map and rendition paths, hashes,
  durations, start offsets, guard bands and minimum cover lengths).
- `report`: the verification report and the plots, by path.
- `tests`: the boundary test file and the negative-control record (which break
  was applied, which tests went red, and that the file was restored).
- `limitations`: fixed sentences plus any the run adds. Always present.

## Reading it from the app

Show `distinct_spans` as the findings, with `breaks_wcag_baseline` deciding
whether a span is a WCAG finding or a room-only one. Show `simulated` as
practice. Show `independent_validation` as pending until it is not. Never
derive a single "safe" badge from this file: a `ready` preparation with zero
findings means the pipeline ingested and prepared the video, not that the
video is safe for anyone.

## Making one

```sh
.venv/bin/python -m pipeline.evidence_summary \
    --ledger media/LICENSES.csv --ledger-file HAZARD_example.mp4 \
    --map results/x/example.wcag.json --map results/x/example.broadcast.json \
    --receipt build/x/local-library/local-receipts/<source-sha256>.json \
    --manifest build/x/prepared-library/<bundle-id>/manifest.json \
    --plot results/x/plots/example_luminance_and_area.png \
    --negative-controls results/video-reset/negative-controls.json \
    --test-file flashmap/tests/test_video_reset_boundaries.py \
    --not-analyzed "The audio track." --report results/x/verification-report.json \
    --out results/x/evidence-summary.json
```

For a title with scheduled practice holds, pass `--simulated events.json`
holding a list of `{"kind": "practice hold", "start_ms": ..., "end_ms": ...,
"detected": false}` entries; the file is refused if any says otherwise.
