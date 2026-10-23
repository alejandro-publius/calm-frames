# Recorded demo shot manifest

This is the October 10 recording of the earlier native build. The later cloud
polish and dependency changes require new native captures. Follow
[MAC_FINISH.md](MAC_FINISH.md) for the current manifest and bundle workflow.
The canonical plan for the next recording is
[submission/DEMO_RUN_OF_SHOW.md](submission/DEMO_RUN_OF_SHOW.md).

`results/redesign_demo_manifest_2026-10-10.json` records source hashes,
source offsets, output durations, narration and edits. These are completed
captures. All demo captures used app source `cba1a29` and package SHA-256
`12f757db105ed2aa15d19017963ec63748917e2c4141e0026120390b3be6ecd1`.
The subsequent final app change only removes a duplicated unavailable-title
sentence on a screen not included in the demo. That screen was recaptured
separately after reinstall; the demo does not claim to be captured on that build.

| Shot | Output start | Source offset | Source | Type |
|---|---|---|---|---|
| 1 | 0:00 | 0 s | `docs/brand/firetv-app-icon-1280x720.png` | Editorial card |
| 2 | 0:06 | 0 s | `.logs/redesign-final-library.png` | Actual simulator still |
| 3 | 0:16 | 0 s | `.logs/redesign-final-details.png` | Actual simulator still |
| 4 | 0:28 | 2 s | `.logs/redesign-final-harbor.mp4` | Actual simulator video with recorded audio |
| 5 | 0:54 | 2 s | `.logs/redesign-final-transport.mp4` | Actual simulator video with recorded audio |
| 6 | 1:16 | 0 s | `.logs/redesign-final-pin.png` | Actual simulator still |
| 7 | 1:25 | 0 s | `.logs/redesign-final-parent.png` | Actual simulator still |
| 8 | 1:37 | 0 s | `.logs/redesign-final-history.png` | Actual simulator still |
| 9 | 1:49 | 2 s | `.logs/redesign-final-prepared.mp4` | Actual simulator video with recorded audio |
| 10 | 2:10 | 0 s | `build/submission-redesign/status-card.png` | Editorial card |
| 11 | 2:30 | 0 s | `docs/brand/firetv-app-icon-1280x720.png` | Editorial card |

## Observation scope

The continuous practice take shows both scheduled holds and captions. The
transport take shows remote seeks/pause/resume and opaque fallback. Prepared
Harbor plays a checked local rendition with no synthetic detector intervals.
PIN and settings shots are disclosed stills; correction/restart were separately
observed. No action is fabricated in the edit.

ScreenCaptureKit captures the composited window and audio. It activates Vega
because background Stage Manager thumbnails can return stale GPU frames.
No screenshots were taken during these recordings. Sparse unchanged frames
are encoded at constant frame rate; this is not a timing measurement.

Native evidence and final-package relationship:
`results/redesign_validation_2026-10-10.json`. The review bundle preserves used
sources. Publication and logged-out viewing verification remain pending.
