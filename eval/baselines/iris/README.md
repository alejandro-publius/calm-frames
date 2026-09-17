# EA IRIS baseline

Builds `IrisApp`, the example command-line app from [EA IRIS](https://github.com/electronicarts/IRIS) (BSD-3-Clause), in Docker, so Calm Frames can be compared with IRIS on the same clips.

**Status, Sep 17, 2026: this image has not completed a build yet.** The first attempt stopped early, and the build is paused while the shared Docker VM runs another project's services. See docs/DECISIONS.md.

## Pins (checked Sep 17, 2026)

| What | Value |
|---|---|
| IRIS | commit `d96978ac1107f3463b77f69a9c1b1ec5d45291a0` (Jan 14, 2025, "Update main (#7)"), the newest commit on `main` |
| vcpkg | commit `d320630b28aeb59b24424eb2a7ef3905314107a1`, the `vcpkgGitCommitId` in IRIS's `.github/workflows/c-cpp.yml` |
| Port versions | IRIS's `vcpkg.json` builtin-baseline `0affe8710a4a5b26328e909fe1ad7146df39d108` |
| Base image | `ubuntu:22.04@sha256:829f6df217bcbae2b371026e81711d1a787c61b2967ad09d015063663ebafbf7` (multi-arch index) |
| Compile jobs | 2 by default (`IRIS_BUILD_JOBS`) |

IRIS depends on `opencv` with the `ffmpeg` and `contrib` features, plus `gtest`, `nlohmann-json`, `spdlog` and `giflib`. vcpkg builds all of it from source, which takes hours on 2 cores.

## How the image is built

- It follows upstream: CMake preset `linux-release` with `-DBUILD_EXAMPLE_APP=ON`, Ninja, and vcpkg in manifest mode. Tests are not built (`-DBUILD_TESTS=OFF`).
- Dependencies install in four cached steps (`vcpkg-stage.sh`). Each step is a larger subset of the same dependency tree at the same versions, and the last one is upstream's `vcpkg.json` unchanged. If a step fails, the next build resumes from the last finished step.
- IRIS's `test/` folder is never checked out and its files are never downloaded, because it holds flashing test videos (see docs/SAFETY.md).
- The runtime stage holds only `IrisApp`, its `appsettings.json`, license files, and the Ubuntu packages that own the shared libraries it loads (`collect-runtime.sh` finds them with `ldd` and `dpkg -S`). Build provenance goes to `/opt/iris/share/BUILD_INFO.txt`.

## Usage

From the repo root:

```
make -f eval/baselines/iris/iris.mk iris-build
make -f eval/baselines/iris/iris.mk iris-run VIDEO=path/to/clip.mp4 OUT=path/to/results
```

`iris-run` runs with no network access and mounts the video's folder read-only.

Flags, read from `example/main.cpp` at the pinned commit:

| Flag | Meaning |
|---|---|
| `-v <file>` | Analyze this video. Without `-v`, IrisApp analyzes every file in `./TestVideos`. |
| `-j true` or `-j 1` | Also write JSON results |
| `-p true`, `1`, `false` or `0` | Turn pattern detection on or off, overriding `appsettings.json` |
| `-r true`, `1`, `false` or `0` | Turn frame resizing on or off |
| `-a <number>` | Set the safe-area proportion |

IrisApp returns exit code 0 even when analysis fails, so `iris-run` checks that result files were written instead of trusting the exit code.

Still to confirm with the first smoke test on a non-flashing clip: the output layout (`Results/<video>/framedata.csv`, plus `result.json` with `-j 1`) and the per-frame result codes (0 pass, 1 warning, 2 extended failure, 3 failure).

## Deviations from upstream

- Tests are not built, and `test/` is excluded from the checkout (safety).
- Dependencies are installed in staged steps before CMake configure instead of only during configure. The versions and features are the same, so the installed packages are the same.
