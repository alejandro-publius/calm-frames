# Baselines

Phase 2.5. Each baseline runs over the same clips as flashmap so the comparison
table in the README is like for like. None of them is a safety tool and none of
their output is a conformance result.

| Baseline | Where | Make target | State on Sep 18, 2026 |
|---|---|---|---|
| EA IRIS | `iris/` | `iris-native-build`, `iris-run`, `iris-pool`, `iris-selftest` | Working. Built natively rather than in Docker, see below. Selftest green and mutation-checked in both directions. |
| ffmpeg `photosensitivity` | `ffmpeg_photosensitivity/` | `ffmpeg-ps-run`, `ffmpeg-ps-pool`, `ffmpeg-ps-selftest` | Working, selftest green and mutation-checked. |
| Naive mean-luminance differencing | `naive_luma_diff/` | `naive-luma-run`, `naive-luma-pool`, `naive-luma-selftest` | Working, selftest green and mutation-checked in both directions. |
| Apple VideoFlashingReduction | not started | none yet | Deferred, no Xcode on this machine. |

Three of these are also the candidate lists the real clip pool is the union of, with flashmap as the fourth. A pool drawn from one detector cannot measure that detector's recall, which is why the list matters more than the table.

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

A baseline may add fields of its own after those, and IRIS does: `build` (the commit and
libraries the binary came from), `warning_frames`, and the `iris_*` fields copied out of
IRIS's own `result.json`. Nothing reads them as part of the schema; they are there so a
report says which tool, at which version, produced it.

## IRIS: why it was built without Docker

The Dockerfile in `iris/` still describes the reproducible build and is still the right
thing on a CI runner. It has never been run here.

On Sep 17 the shared colima VM was running another project's DataHub stack, and a lane
building an image in it pushed the VM into its memory limit and got that project's
`datahub-gms` container killed. Two of that stack's containers were still sitting at
exit 137 the next morning. The repo rule is that we never restart colima and never
remove containers, images or volumes we did not create, and a vcpkg source build of the
whole OpenCV tree is exactly the workload that caused the first incident. So the Docker
build was not attempted, then or now.

`eval/baselines/iris/build-native.sh` builds the same upstream commit on the host
instead, against Homebrew's OpenCV 4, ffmpeg, spdlog and nlohmann-json, in about two
minutes:

```
make iris-native-build
make iris-pool
```

The dependencies are different builds of the same libraries, which is a real deviation
and not a detail: every report file records the commit, the compiler, the OpenCV version
and the libavformat version that produced it, and `eval/baselines/iris/README.md` says
what that costs.

## Apple VideoFlashingReduction: why it is deferred

`xcode-select -p` returns `/Library/Developer/CommandLineTools`. The Swift
package needs a full Xcode, and the alternative MATLAB version needs MATLAB.
Neither is on this machine, so this baseline is logged and skipped rather than
half-done. If it comes back, its output is a 0 to 100 risk score from whole-frame
average luminance and it is causal, so whatever threshold we compare at has to be
stated next to the number.
