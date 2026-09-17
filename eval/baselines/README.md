# Baselines

Phase 2.5. Each baseline runs over the same clips as flashmap so the comparison
table in the README is like for like. None of them is a safety tool and none of
their output is a conformance result.

| Baseline | Where | Make target | State on Sep 17, 2026 |
|---|---|---|---|
| EA IRIS | `iris/` | `iris-build`, `iris-run` | Not built. Blocked on the shared Docker VM, see below. |
| ffmpeg `photosensitivity` | `ffmpeg_photosensitivity/` | `ffmpeg-ps-run`, `ffmpeg-ps-pool`, `ffmpeg-ps-selftest` | Working, selftest green and mutation-checked. |
| Naive mean-luminance differencing | `naive_luma_diff/` | `naive-luma-run`, `naive-luma-pool`, `naive-luma-selftest` | Working, selftest green and mutation-checked in both directions. |
| Apple VideoFlashingReduction | not started | none yet | Deferred, no Xcode on this machine. |

Every makefile here is standalone, so a root Makefile is not needed:

```
make -f eval/baselines/<dir>/<name>.mk <target>
```

## Shared report schema

Each run writes one JSON file per clip under
`results/baselines/<baseline>/<clip stem>.json`:

```
baseline, tool_version, video, sha256, params,
frames_analyzed, flagged_frames, segment_count,
segments[{start_s, end_s, duration_s}], notes
```

`sha256` ties every report to the exact file in `media/LICENSES.csv`.

## IRIS: why it has not been built

The Dockerfile, pins and README in `iris/` are reviewed and ready. The build was
not started on Sep 17 because the colima VM on this Mac is shared with another
project and was running six DataHub containers: 7.7 GiB total, about 2.9 GiB
available, against a 4 GiB floor. vcpkg building OpenCV from source inside that
would have starved the other project's services. The repo rule is that we never
restart colima and never remove containers, images or volumes we did not create,
so the build waits.

Start it when the VM is idle:

```
docker ps            # expect no containers we did not create
colima ssh -- free -m
VCPKG_MAX_CONCURRENCY=2 make -f eval/baselines/iris/iris.mk iris-build
```

It takes hours on two cores. Start it first thing on whatever day it fits.

## Apple VideoFlashingReduction: why it is deferred

`xcode-select -p` returns `/Library/Developer/CommandLineTools`. The Swift
package needs a full Xcode, and the alternative MATLAB version needs MATLAB.
Neither is on this machine, so this baseline is logged and skipped rather than
half-done. If it comes back, its output is a 0 to 100 risk score from whole-frame
average luminance and it is causal, so whatever threshold we compare at has to be
stated next to the number.
