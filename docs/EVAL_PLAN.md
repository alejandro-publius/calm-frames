# Evaluation plan

Written Thu Sep 17, 2026, before any real clip has been labeled and before any conformance clip has been generated. That order is the whole point of this file: it fixes what we will measure and how we will decide, while we still have no idea what the answer is.

**No number in this file is a result.** Everything here is a design parameter, a sample size or a decision rule. Every result lives in `results/*.json` and reaches the README only through `evkit.readme_sync`.

**No threshold is written out here.** Flash thresholds come from `flashmap/docs/SPEC_SOURCES.md` and nowhere else, including from memory. Where this plan needs to talk about a threshold it refers to it by name, or as a multiple of it (0.9x, 1.1x), so that changing the quoted spec text changes the design in one place.

Anything in this plan that changes after today goes in **Deviations** at the bottom, with the date and the reason. That includes cuts: if a section is dropped for time, the cut is a deviation.

## 1. Safety rules that bind every run here

These come from docs/SAFETY.md and CLAUDE.md. They are part of the design, not a preface to it.

1. **Generated conformance clips are hazardous by design.** Every clip is generated, analyzed and deleted inside the same job. No clip is ever opened, played, thumbnailed or previewed by a person. Files are written under a scratch directory outside the repo, named with the `HAZARD_` prefix, and removed in a `finally` block. The run asserts at exit that no `HAZARD_` file survives, and fails if one does.
2. **Real flagged content is played only with the filter on, and nobody is watching the screen.** That applies to every take of the screen-level test. The camera records, the people leave or face away.
3. **Prevented exposure is computed from the flash map, never demonstrated.** We never play real flashing content with the filter off to show what would have happened, on any screen, for any purpose, including the video.
4. Real clips are labeled from plots only, never from playback. Plots come from `eval/plots.py`, which does not import flashmap.
5. Whoever films flashing footage is not photosensitive and does not look at the lights. People in frame consent.

## 2. Definitions

**Window.** The unit of analysis is a one second window. A clip of duration D is cut into non-overlapping windows `[k, k+1)` seconds for `k = 0 .. floor(D) - 1`, measured from the first presentation timestamp in the file, not from an assumed frame index. A trailing remainder shorter than one second is dropped (see Exclusions).

**Ground truth positive window.** A window that the ground truth marks as containing flashing that meets the general flash condition or the red flash condition. Source of truth by set: computed from the spec text for the conformance suite (section 3), from human labels for the real clip set (section 4).

**Predicted positive window.** A window that any interval in the detector's output overlaps. Primary rule: any overlap at all counts. Sensitivity check, reported alongside: overlap of at least 50% of the window. Both are computed in the same run, from the same detector output, so neither can be chosen after seeing the other.

**Detector.** Calm Frames means flashmap at the pinned version recorded in the result file. Baselines are in section 5. Each detector is run once per clip and produces intervals in media time; converting intervals to windows is done by one shared function, `eval/metrics.py::windows_from_intervals`, for every detector including ours.

**Event** (screen-level test only) is defined in section 7.

## 3. Metrics

**Primary, for every set and every detector:**

- Precision per one second window: TP / (TP + FP), over windows pooled across clips.
- Recall per one second window: TP / (TP + FN).
- A Wilson score 95% interval on each, without continuity correction, with the denominator being predicted positive windows for precision and ground truth positive windows for recall. Computed by `eval/metrics.py::wilson`, which has a unit test against published worked values.

Wilson treats windows as independent Bernoulli trials. Windows inside one clip are not independent. We keep Wilson as the headline interval on the conformance suite, where each clip is generated independently, and we report the bootstrap interval over titles (section 4) as the headline for the real clip set. Both intervals are reported for both sets, and the result files say which is the headline for which.

**Secondary, reported but never used to make a pass or fail call:**

- Segment level recall: a ground truth flash segment counts as found if any overlapping window is a predicted positive.
- Onset lead, in windows: the first predicted positive window minus the first ground truth positive window of a segment.
- False positive seconds per minute of calm content.

**Error curves.** For the conformance suite, precision and recall are also plotted against each varied parameter one axis at a time (flash rate, luminance step as a multiple of the threshold, area fraction, and so on), so a failure shows up as a region rather than a single number.

**Every reported metric carries its exclusion counts.** A metric without the count of what was excluded from its denominator does not get published.

## 4. Conformance suite (generated clips)

**Size.** About 3,000 clips. The exact count is whatever the committed design emits, and it is recorded in the design manifest and in the result file.

**Clip shape.** Each clip is 6.0 seconds: a 2 s calm lead-in, a 2 s test section, a 2 s calm tail. Every clip therefore contains both positive and negative windows, and the boundaries of the test section are known exactly.

**Ground truth comes from the spec text, not from flashmap.** `eval/conformance/truth.py` computes the expected per-window labels from the intended frame sequence and the conditions quoted in `flashmap/docs/SPEC_SOURCES.md`. It must not import flashmap, directly or transitively, and a test asserts that (same rule as `eval/plots.py`). If truth and flashmap disagree, that is a finding, not a bug to be fixed by making truth agree.

**The design is committed before anything is generated.** `eval/conformance/design.py` writes the full clip manifest, one row per clip with every parameter and the expected ground truth, to `results/conformance_design.json`, with a fixed RNG seed recorded in the file. Generation reads that manifest. Nothing is sampled at generation time.

**Parameters varied:**

| Axis | Levels |
|---|---|
| Flash rate | 1 to 30 Hz, sampled at 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 20, 24, 30 Hz, with extra points on either side of the spec's per-second flash limit |
| Luminance step size | The relative luminance change between the two states, set as a multiple of the general flash threshold: 0.5x, 0.8x, 0.9x, 0.95x, 1.0x, 1.05x, 1.1x, 1.25x, 2.0x |
| Darker-image condition | The darker of the two states set above and below the spec's darker-image boundary, at 0.8x, 0.95x, 1.05x and 1.2x of it |
| Flashing area | 1, 5, 10, 15, 20, 25, 33, 40, 50 and 60% of the picture, with extra points either side of the spec's area limit. Shapes: centered rectangle, off-center rectangle, scattered blocks, thin horizontal band. Area is measured on the picture, not the coded frame, so letterboxed variants are included |
| Red versus near red | Saturated red meeting the spec's chromaticity condition; near red placed just outside it at stated small offsets in the same space; and a non-red control matched on luminance |
| Frame rate | 24, 25, 30, 50 and 60 fps, plus variable frame rate in two patterns (alternating frame durations, and dropped frames), written with real per-frame timestamps |
| Resolution | 854x480, 1280x720, 1920x1080, 3840x2160 |
| Compression | libx264 at CRF 18, 23 and 28, plus one lossless reference encode per parameter cell |
| Color tagging | BT.709 tagged, untagged HD, untagged SD, and a full-range (yuvj) variant |
| Dynamic range | SDR only. HDR and the BT.1702-3 HDR rule are out of scope for this plan (cut list item 1). Adding them later is a deviation |

**Near threshold share.** At least 40% of clips are near threshold, meaning at least one governing quantity sits within 15% of its applicable limit, or, for flash rate, on the grid point immediately above or below the limit. The design script asserts this share and fails if the emitted manifest misses it.

**Encoding fidelity check, automated, nobody looks.** After encoding, the job decodes the clip and compares its per-frame mean relative luminance against the intended waveform. Clips deviating by more than 2% of full scale in any frame are excluded and counted, except on the variable frame rate and compression axes, where the expected deviation is part of the design and the tolerance is set per axis in the design manifest.

**Cross-checks.** A stratified sample of the suite is also scored by IRIS, and agreement plus Cohen's kappa between IRIS and our ground truth are reported. If the TRACE ground-truth generator named in docs/BUILD_PROMPT.md 5.2 turns out to be public, its output is compared on the same sample; if it is not public, the result file says so. Neither cross-check changes our ground truth.

## 5. Real clip set

**Size and source.** About 40 segments, drawn from the screening pool recorded in `results/screening.json` and `media/LICENSES.csv`, from at least 4 sources.

**How segments are chosen.** If candidate segments came only from flashmap's own flags, recall would be unmeasurable. The pool is therefore built from the union of four candidate lists (flashmap, IRIS, the ffmpeg photosensitivity filter, naive luminance differencing), plus a random sample of time from the same titles that no detector flagged:

- about 28 segments sampled from the union, capped so that no single detector is the sole source of more than half of them;
- about 12 segments sampled at random from unflagged time in the same titles;
- each segment a fixed 10 s window, sampling seed committed in `eval/labeling/make_pool.py`.

**Blind pooled review.** Segments get opaque ids, are shuffled with the committed seed, and carry no title, no source and no indication of which detector proposed them. The labeler sees only plots from `eval/plots.py`: per-frame relative luminance for the whole picture and for the largest changing region, the area fraction of that region, and the red chromaticity trace. No detector output is shown. No clip is played.

**Labeling rule.** The labeler marks, per one second window, whether the window shows flashing meeting the general or the red condition, following a written guide (`eval/labeling/GUIDE.md`) that quotes `flashmap/docs/SPEC_SOURCES.md`. Windows that cannot be called from the plot are marked unlabelable, which is an exclusion, not a negative.

**Second labeler and kappa.** A second labeler (Rachel, if she is on the team) independently labels at least 15 of the segments from the same plots and the same guide. We report unweighted Cohen's kappa at the window level and at the segment level, on the labels as first given, before any discussion. Disagreements are then resolved by discussion, and the adjudicated labels are the ones the primary metrics use. If no second labeler is available, kappa is not reported, the plan says so plainly, and that is logged as a deviation.

**Labels are frozen before any comparison.** Label files are committed to git before any comparison script is run. `eval/realclips/report.py` refuses to run if the label files are dirty in the working tree, and it records their hashes in its output.

**Intervals.** Bootstrap over titles, not over windows: 10,000 resamples of the title list with replacement, percentile 95% intervals, seed committed in the script. Wilson intervals are reported too, marked as the optimistic bound.

**Positives per source.** The result file breaks out, per source: number of titles, number of segments, number of ground truth positive windows, and the same for each detector. The README states the mix, including how many positives are self-filmed.

## 6. Baselines

All baselines run on the same clips, the same windows and the same metrics as flashmap, and land in one table.

| Baseline | How it is run | Mapping to windows |
|---|---|---|
| EA IRIS | `make -f eval/baselines/iris/iris.mk iris-run`, pinned image, no network | Per-frame result codes, confirmed against the pinned `example/main.cpp` and recorded in the result file before any comparison. Primary: codes at or above extended failure count as positive. Sensitivity: warnings also count |
| ffmpeg photosensitivity filter | Pinned ffmpeg, parameters recorded in the result file. The first second of output is dropped, because the filter misfires there even on a static gray clip | Reported frames map to their containing window |
| Naive luminance differencing | `eval/baselines/naive.py`, mean frame luma, threshold on the difference between consecutive frames | Frames over threshold map to their containing window |

**Operating points are fixed before the real clip set is touched.** For any baseline with a tunable threshold, the threshold is swept on the conformance suite, the full curve is reported, and the single operating point that maximizes F1 on the conformance suite is then applied unchanged to the real clip set. flashmap's own thresholds come from the spec and are never tuned on either set.

Apple VideoFlashingReduction is not part of the committed comparison (cut list item 4). Adding it is a deviation.

## 7. Ablations

Each ablation is one flag on the same code path, re-run over the same clips against the same committed ground truth, reporting the same primary metrics and intervals. The ablation runner asserts that with every flag at its default the output is byte-identical to the main run.

Detection ablations, one at a time:

- red rule off
- area rule off (any flashing area qualifies)
- darker-image rule off
- sRGB linearization off (metrics computed on gamma-encoded values)

Cover ablations:

- guard band at 0, 100, 250 and 500 ms. Measured in simulation over the committed flash maps and the timing model fitted from the GATE 1 recordings, not by re-filming at every setting. The simulation reuses the same `app/src/calmframes/coverSchedule.ts` logic the app runs, so an ablation cannot drift from the shipped scheduler. Reported as the fraction of intervals fully covered before onset, per guard band. The plan says plainly that this one is simulated.
- dim versus opaque cover. Measured through the verify step: render each cover over the original in linear light and re-run flashmap, reporting how many segments pass under each. Dim stays allowed only for non-red segments at 90% or darker, and red segments always get an opaque cover, so the dim arm is reported over the non-red subset only.

## 8. Screen-level test on the stick

**Scale.** At least 200 events, filmed at 240 fps with exposure locked, TV in game mode with motion smoothing off, calibrated against a luminance step chart. A static gray screen is filmed before each run to check for backlight flicker.

**What counts as an event.** One scheduled cover interval that the app was supposed to have fully in place before a defined moment. Two kinds, both counted toward the 200 and also reported separately:

- **Marker events.** A non-flashing gray-to-white marker step in the marker clip, under a sham flash map that is labeled as a sham everywhere it appears. The cover must be fully on before the marker onset. The clip and its schedule come from `eval/marker_clip.py`, and every result file records the clip's SHA-256, so a set of numbers always names the video it belongs to.
- **Real segment events.** The start of a flagged interval in a real title, played with the filter on and nobody watching the screen.

An occurrence counts as an event only if all of these hold. Otherwise it is excluded and counted:

1. the recording covers it from at least 1 s before the scheduled cover-on to at least 0.5 s after the interval start;
2. the app logged a matching `CALM_TIMING` line naming the same schedule and interval;
3. the ROI calibration for that take passed;
4. the take was not aborted.

**Leaks.** A leak is any recorded frame inside the interval, or inside the marker onset window, where the ROI luminance rises above the covered-state reference by more than the tolerance set by the step-chart calibration for that take. Leaks are reported as a count out of N with a Wilson 95% interval, including the upper bound when the count is zero.

**Cover lead time.** For each event: the time the cover is fully opaque in the recording, minus the time of the marker onset or interval start, mapped through the calibration. Report median, p95 and worst.

**Strata reported separately, not dropped:** events overlapping a buffering or stall line in the device log, events after a seek, and events after a playback rate change. These are the interesting cases, so they are reported rather than excluded.

**Safety.** Filter on for every take. Nobody watches the screen. The exposure the filter prevented is computed from the flash map and never played.

## 9. Exclusion rules, collected

Every exclusion is counted and reported next to the metric it affects.

**Conformance suite**
- the trailing partial window of every clip
- clips that failed to encode
- clips whose decoded luminance deviates from the intended waveform beyond the tolerance for their axis
- clips whose decoded frame timestamps do not match the requested timing pattern, except on the variable frame rate axis where the pattern is the point

**Real clip set**
- titles whose license line in `media/LICENSES.csv` is not confirmed, dropped at screening, before labeling
- windows the labeler marks unlabelable from the plot
- segments where the plot is dominated by a scene cut rather than flashing, marked as such from the plot alone, before any detector output is seen
- no segment is ever excluded after its detector result is known

**Screen-level test**
- takes where the pre-run gray screen shows backlight flicker
- takes where ROI calibration fails
- occurrences failing any of the four event conditions in section 8

## 10. Scripts that produce each number

Nothing reaches the README except through `results/*.json` and `evkit.readme_sync`. Every result file records the git commit, the flashmap version, every seed, and the exclusion counts.

| Number | Script | Output | Exists today |
|---|---|---|---|
| Conformance design and expected truth | `eval/conformance/design.py`, `eval/conformance/truth.py` | `results/conformance_design.json` | No |
| Conformance detector output | `eval/conformance/generate_analyze.py` (generate, analyze, delete in one job) | `results/conformance_raw.jsonl` | No |
| Conformance precision, recall, intervals, error curves | `eval/conformance/report.py` using `eval/metrics.py` | `results/conformance.json` | No |
| Plots for labeling | `eval/plots.py` (must not import flashmap) | plot files under the scratch dir | No |
| Blinded segment pool | `eval/labeling/make_pool.py` | `eval/labeling/pool.json` | No |
| Labels and kappa inputs | committed label files under `eval/labeling/` | `eval/labeling/labels_*.csv` | No |
| Real clip metrics, kappa, bootstrap, per-source positives | `eval/realclips/report.py` | `results/realclips.json` | No |
| Baseline comparison table | `eval/baselines/run_all.py`, plus `eval/baselines/iris/iris.mk` for IRIS | `results/baselines.json` | IRIS make target yes, runner no |
| Ablations | `eval/ablations/run.py` | `results/ablations.json` | No |
| GATE 1 marker clip and its schedule | `eval/marker_clip.py` (our own, because calm-timing is in the missing kits) | `eval/harness_runs/marker_schedule.json` plus the clip's SHA-256 | Yes |
| GATE 1 timing, from the 240 fps recordings | the camera harness: ROI extraction, per-trial analysis, combine | `results/gate1_timing.json` | No. calm-timing was to provide it; if the kit never arrives we write it |
| Screen-level leaks and lead time | the same camera harness over the Oct 8 to 13 recordings | `results/screen_level.json` | No |
| Screening counts per source | `pipeline/` screening run | `results/screening.json` | No |
| App KPIs on the stick | `vega exec perf kpi-visualizer` | `results/kpi.json` | No |
| VVD playback smoke run | `eval/vvd_smoke.py` | `results/vvd_smoke.json` | Yes |
| Every table and figure, offline, from committed results | `make reproduce` | regenerated artifacts | No |

## 11. Rules that keep this honest

- flashmap's thresholds are never tuned on either evaluation set.
- `eval/conformance/truth.py` and `eval/plots.py` never import flashmap, and tests assert it.
- Labels are committed before any comparison script runs, and the comparison records their hashes.
- Both window-overlap rules (any overlap, and at least 50%) are computed in the same run, so neither is picked after the fact.
- A metric is never published without its exclusion count.
- If a number moves after a change to any script here, the change is logged in Deviations with the date and the reason, and the old number stays in git history.

## 12. Deviations

Every change to this plan after Thu Sep 17, 2026 goes here, newest last, with the date, what changed, and why. Empty is the correct state today.

| Date | What changed | Why |
|---|---|---|
| | | |
