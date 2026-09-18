# Baselines

Set: the generated conformance suite, the same clips and windows for every detector

the windows every detector saw. ffmpeg's photosensitivity filter has its first second dropped, so window 0 of every clip is missing from its denominator, and leaving it in the others' denominators would compare them on different windows.

| detector | precision | recall | F1 |
|---|---|---|---|
| flashmap (this project) | 0.954 [0.924, 0.972] (290/304) | 0.895 [0.857, 0.924] (290/324) | 0.924 |
| flashmap, half window rule | 0.954 [0.924, 0.972] (290/304) | 0.895 [0.857, 0.924] (290/324) | 0.924 |
| flashmap, flash bounds only (diagnostic, not the hide) | 0.954 [0.924, 0.972] (290/304) | 0.895 [0.857, 0.924] (290/324) | 0.924 |
| naive mean luminance differencing (best threshold on this suite, 4 luma codes) | 0.667 [0.619, 0.711] (262/393) | 0.809 [0.762, 0.848] (262/324) | 0.731 |
| ffmpeg photosensitivity filter (best difference threshold on this suite, 1 codes, first second dropped) | 0.368 [0.336, 0.401] (308/838) | 0.951 [0.921, 0.969] (308/324) | 0.530 |

## Not run

- **EA IRIS**: the pinned image at eval/baselines/iris/ has never built, and building it here would have taken the shared machine for a long time: the shared colima VM had 6 containers from another project running on 4 CPUs and 7.7 GiB. CLAUDE.md forbids touching containers, images or volumes this project did not create, and the build is a vcpkg source build of the whole IRIS dependency tree on two jobs. Skipped rather than fought, as the lane brief asked.
- **Apple VideoFlashingReduction**: it needs Xcode, and xcode-select reports '/Library/Developer/CommandLineTools', which is Command Line Tools only. It is also cut list item 4 in EVAL_PLAN section 6, so it was never part of the committed comparison.

## Operating points

- naive_luma_diff: best F1 at threshold 4 (precision 0.667, recall 0.809, F1 0.731), chosen on the conformance suite
- ffmpeg_photosensitivity: best F1 at threshold 1 (precision 0.368, recall 0.951, F1 0.530), chosen on the conformance suite
