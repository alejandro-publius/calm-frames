# Ablations

150 clips, 0 errors. Default arm compared against the main run on 150 clips, 0 mismatched.

| arm | precision | recall | change in precision | change in recall |
|---|---|---|---|---|
| default | 0.672 [0.587, 0.746] (88/131) | 0.898 [0.822, 0.944] (88/98) | 0.000 | 0.000 |
| red_rule_off | 0.674 [0.574, 0.760] (64/95) | 0.653 [0.555, 0.740] (64/98) | 0.002 | -0.245 |
| area_rule_off | 0.508 [0.435, 0.581] (90/177) | 0.918 [0.847, 0.958] (90/98) | -0.163 | 0.020 |
| darker_image_rule_off | 0.657 [0.573, 0.732] (88/134) | 0.898 [0.822, 0.944] (88/98) | -0.015 | 0.000 |
| srgb_linearization_off | 0.661 [0.575, 0.738] (84/127) | 0.857 [0.774, 0.913] (84/98) | -0.010 | -0.041 |

## Guard band (simulated, not measured on a device)

results/gate1_timing.json does not exist yet, so there is no measured cover latency to put here. Read the rows as: at this guard band, the cover is in place in time as long as the player takes no longer than this to put it up.

| guard band (ms) | latency 0 ms | latency 33 ms | latency 66 ms | latency 100 ms | latency 200 ms |
|---|---|---|---|---|---|
| 0 | 1.000 (144/144) | 0.979 (141/144) | 0.979 (141/144) | 0.979 (141/144) | 0.979 (141/144) |
| 100 | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) | 0.979 (141/144) |
| 250 | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) |
| 500 | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) | 1.000 (144/144) |

## Cover: dim against opaque

dimming multiplies all three channels by the same factor, which leaves the chromaticity where it was, and the red rule reads chromaticity. So a dim cover cannot clear a red flash, whatever the luminance does. The red rows here are the measurement of that, not an argument for it.

| segments | uncovered still flagged | dim still flagged | opaque still flagged |
|---|---|---|---|
| all (60) | 60 | 27 | 0 |
| red (30) | 30 | 27 | 0 |
| non red (30) | 30 | 0 | 0 |
