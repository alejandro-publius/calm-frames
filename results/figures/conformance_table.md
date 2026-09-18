# Conformance suite

Sample: 467 clips measured and kept, of 3000 clips in the committed design. 8 were measured and excluded. The run order is the whole spine (152 rows that walk one axis at a time) followed by the cross product shuffled with the committed seed, so a partial run is a random sample of the cross product with every sweep complete. Every number in this file is from that sample and from nothing else.

- clips designed: 3000
- clips measured: 475
- clips kept after exclusions: 467
- one second windows kept: 1401
- ground truth positive windows: 324
- complete run: no, this is a partial run

Exclusions: decoded luminance off the intended waveform (8)

## Over every window

| detector | precision (Wilson 95%) | recall (Wilson 95%) | F1 |
|---|---|---|---|
| flashmap (this project) | 0.650 [0.605, 0.693] (290/446) | 0.895 [0.857, 0.924] (290/324) | 0.753 |
| flashmap, half window rule | 0.681 [0.635, 0.723] (290/426) | 0.895 [0.857, 0.924] (290/324) | 0.773 |
| flashmap, flash bounds only (diagnostic, not the hide) | 0.954 [0.924, 0.972] (290/304) | 0.895 [0.857, 0.924] (290/324) | 0.924 |

## Over the windows every detector saw

ffmpeg's filter has its first second dropped, so window 0 of every clip is missing from its denominator. This table puts every detector on the windows that are left.

| detector | precision (Wilson 95%) | recall (Wilson 95%) | F1 |
|---|---|---|---|
| flashmap (this project) | 0.954 [0.924, 0.972] (290/304) | 0.895 [0.857, 0.924] (290/324) | 0.924 |
| flashmap, half window rule | 0.954 [0.924, 0.972] (290/304) | 0.895 [0.857, 0.924] (290/324) | 0.924 |
| flashmap, flash bounds only (diagnostic, not the hide) | 0.954 [0.924, 0.972] (290/304) | 0.895 [0.857, 0.924] (290/324) | 0.924 |
| naive mean luminance differencing (best threshold on this suite, 4 luma codes) | 0.667 [0.619, 0.711] (262/393) | 0.809 [0.762, 0.848] (262/324) | 0.731 |
| ffmpeg photosensitivity filter (best difference threshold on this suite, 1 codes, first second dropped) | 0.368 [0.336, 0.401] (308/838) | 0.951 [0.921, 0.969] (308/324) | 0.530 |

## Secondary

- clip level (does the clip fail at all): precision 0.954 [0.908, 0.978] (145/152), recall 0.895 [0.838, 0.933] (145/162)
- segment recall: 0.895 [0.838, 0.933] (145/162)
- false positive seconds per minute of calm: 8.69 over 1077 calm windows
- onset lead: median -1 window(s), 100% of found segments hidden before the flashing started (n=145)

## Known disagreements

- **one_second_period_boundary**: The ground truth counts flashes in a half open one second period and flashmap counts them in a closed trailing one. On a clean square wave at exactly the flash limit the closed reading finds one more flash than the half open one. Look at the flash_rate_hz error curve at 3 Hz to see what it costs. Neither reading is written in the spec.
- **leading_hide**: flashmap hides the whole failing one second period, which starts before the flashing does. Under the any overlap rule that shows up as false positive windows in the calm lead-in. It is the direction a safety layer should err in, and it is counted here rather than excused: see onset_lead_windows.
