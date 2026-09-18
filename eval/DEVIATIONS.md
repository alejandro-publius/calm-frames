# Deviations from docs/EVAL_PLAN.md

The plan says every change to it after Thu Sep 17, 2026 is logged with the date, what changed
and why. This is that log for the evaluation lane. **These rows still need copying into
EVAL_PLAN section 12 by whoever owns docs/**, which this lane does not: it was asked to stay
inside `eval/` and `results/`. Nothing here is a result.

| Date | What changed | Why |
|---|---|---|
| 2026-09-17 | Conformance clips are 3.0 s (1 s calm lead-in, 2 s test section) instead of the planned 6.0 s (2 s calm, 2 s test, 2 s calm). | Three thousand six second clips do not fit in one session on a machine shared with a Docker VM and a virtual device. Two seconds of test section is the least that lets a four flash per second clip finish four flashes, so the test section is unchanged and only the calm padding is shorter. |
| 2026-09-17 | The trailing calm section is gone, so the suite does not measure how far a hide runs past the end of the flashing. | Same reason. flashmap's trailing one second window means a hide always continues about a second after the flashing stops; with no trailing calm section that cost is invisible here. The leading cost is still measured, because the calm lead-in is still there. This is the one thing the shorter clip gives up and it should be measured on the real clip set. |
| 2026-09-17 | The per axis encoding fidelity tolerance lives in `eval/conformance/report.py`, not in the design manifest. | The plan puts it in the manifest. The manifest was already written and every clip id is a hash of its row, so adding a field would have renamed all three thousand clips in the middle of a run. The tolerance is 2% of full scale as the plan says, 4% for clips at the highest quantiser, both named in the report and applied offline so they can be changed without regenerating anything. |
| 2026-09-17 | Ground truth counts flashes in a **half open** one second period, `[s, s + 1000)`. | The spec does not say whether the period is open or closed. The closed reading counts a flash at both ends and so calls a clean 3 Hz square wave four flashes in a second. flashmap's trailing window is closed. The difference is measurable at exactly the flash limit and the conformance report names it rather than smoothing it over. |
| 2026-09-17 | A third window rule, "flash bounds only", is reported beside the two the plan fixes. | It is a diagnostic, not a decision rule: it scores the tight flash bounds flashmap records in the map rather than the interval it hides, which separates "did it find the flashing" from "how much did it hide around it". It is labelled as a diagnostic everywhere it appears and no pass or fail call uses it. |
| 2026-09-17 | EA IRIS did not run, so the IRIS cross-check of the ground truth in plan section 4 did not happen. | The pinned image has never built, and the shared colima VM was busy with another project's stack. The lane brief said to skip it rather than fight it. What was on the machine at the time is recorded, with the probe that read it, under `environment_when_written` in `results/baselines.json`, so the numbers are not restated here. |
| 2026-09-17 | Apple VideoFlashingReduction did not run. | It needs Xcode; this machine has Command Line Tools only. It was already cut list item 4, so this changes nothing about the committed comparison. |
| 2026-09-17 | The conformance run reported on is a sample of the committed design, not all of it. | At the measured rate on a machine under load from three other lanes, three thousand clips take about four hours. The run order is the whole spine first and then the cross product shuffled with the committed seed, so a partial run holds every one axis at a time sweep plus a random sample of everything else. The exact count is in `results/conformance.json` under `sample`, and `make conformance-full` finishes the rest and rebuilds the tables. |
| 2026-09-17 | The guard band ablation reports across a grid of assumed cover latencies rather than one measured latency. | `results/gate1_timing.json` does not exist yet. A single number here would look measured and would not be. When the GATE 1 recordings land, the same script takes the measured latency and the assumption grid comes out. |
| 2026-09-17 | The labelling plots come from a new `eval/labeling/plots.py` rather than from `eval/plots.py` directly. | The plan asks the labeller to see four series: whole picture luminance, the luminance of the largest changing region, that region's area fraction, and the red chromaticity trace. `eval/plots.py` draws the first and third and has no way to blind a figure or to start part way into a file, and it is the sanctioned inspection tool for other lanes, so it was left alone. The new module imports its probing and timestamp helpers, keeps the same rule about never importing flashmap (the same test covers both), and adds the two panels and the blinding. |
| 2026-09-17 | A root `Makefile` was created for `make reproduce`, and then replaced by the release lane's own. | `make reproduce` has to work from the repository root. The root makefile this lane wrote was superseded within the hour by a fuller one from another lane, which includes `eval/reproduce.mk` and takes the `reproduce` recipe from it. `eval/reproduce.mk` is written to that convention: it owns the recipe, the root file adds its own half as a prerequisite, and every target still runs standalone with `make -f eval/reproduce.mk`. |

## Incidents

**2026-09-17, two hazard clips outlived their job for about a minute.** The conformance run was
stopped with SIGTERM to restart it with more workers. Python's default SIGTERM handler tears a
process down without running `finally` blocks, so two clips in flight were left in the scratch
directory. They were deleted as soon as the next command looked, they were never opened, and
they were outside the repository the whole time.

Three changes came out of it, each in `eval/conformance/generate_analyze.py`:

1. workers turn SIGTERM into `SystemExit`, so the `finally` that deletes the clip runs;
2. the parent sweeps the scratch directory at startup as well as at exit, so a leftover from an
   earlier crash cannot survive into a new run;
3. leaving the worker pool by any route other than a clean finish now cancels the queue. The
   first attempt at the fix did not, and `shutdown(wait=True)` kept feeding the workers the
   rest of the 3000 clip queue while nobody was reading the answers: the job looked stopped,
   the rows stopped appearing, and it carried on making strobes. That is the more dangerous of
   the two bugs.

Verified afterwards by stopping a real run with SIGTERM and watching the directory empty, and
by `eval/tests/test_hazard_clips_are_never_kept.py`, which fails if the deletion or the sweep is
taken out.
