# EA IRIS baseline

Runs `IrisApp`, the example command-line app from [EA IRIS](https://github.com/electronicarts/IRIS) (BSD-3-Clause), over the same clips as flashmap, so Calm Frames can be compared with a published photosensitivity analyser instead of trusted on its own. IRIS is also the fourth candidate list the real clip pool is the union of, which is the part that changes a number rather than a table: see `eval/labeling/make_pool.py`.

**Status, Sep 18, 2026: built and run over every clip in the pool.** It was built natively on this Mac, not in Docker. `results/baselines/iris/` holds one report per clip.

## How it was built, and why not in Docker

The Dockerfile here is still the reproducible path and is still the right thing on a CI runner. It was not used. The colima VM on this machine is shared with another project, a vcpkg source build of the whole OpenCV tree inside it had already pushed that VM into its memory limit once and got another project's container killed, and CLAUDE.md says never to restart colima and never to touch containers, images or volumes we did not create. So the build went nowhere near it.

`build-native.sh` builds the same upstream commit, with tests off and `test/` still left out of the checkout, against Homebrew's OpenCV 4, ffmpeg, spdlog and nlohmann-json:

```
make iris-native-build
```

It installs outside the repository, because a binary is not something this repository commits:

```
~/.cache/calm-frames/iris/IrisApp
~/.cache/calm-frames/iris/appsettings.json
~/.cache/calm-frames/iris/BUILD_INFO.txt
```

It takes about two minutes on four cores, against the hours the vcpkg build needs.

**What that costs, stated plainly.** Upstream pins its dependencies through vcpkg at a fixed baseline; this build links against whatever Homebrew has. Same source, same settings, different builds of OpenCV and ffmpeg. Decoding is where that could show: a different ffmpeg can hand IRIS a different frame, and OpenCV 4.14 is not the 4.8 the vcpkg baseline pins. So a number from this build is a number from this build, and every report file carries `build` with the commit, the compiler, the OpenCV version and the libavformat version in it. `docs/DECISIONS.md` carries the decision. If the Docker image is ever built on a runner, re-run the pool through it and compare rather than assuming the two agree.

## Pins (checked Sep 17, 2026)

| What | Value |
|---|---|
| IRIS | commit `d96978ac1107f3463b77f69a9c1b1ec5d45291a0` (Jan 14, 2025, "Update main (#7)"), the newest commit on `main` |
| vcpkg (Docker path only) | commit `d320630b28aeb59b24424eb2a7ef3905314107a1`, the `vcpkgGitCommitId` in IRIS's `.github/workflows/c-cpp.yml` |
| Port versions (Docker path only) | IRIS's `vcpkg.json` builtin-baseline `0affe8710a4a5b26328e909fe1ad7146df39d108` |
| Base image (Docker path only) | `ubuntu:22.04@sha256:829f6df217bcbae2b371026e81711d1a787c61b2967ad09d015063663ebafbf7` |
| Native build | Homebrew opencv@4, ffmpeg, spdlog, nlohmann-json, recorded per run in `BUILD_INFO.txt` |

`build-native.sh` reads the IRIS commit out of the Dockerfile, so the two paths cannot drift on to different source.

## Nothing is ever played

IRIS decodes frames and measures them. Its one `cv::imshow` call is inside
`#ifdef DEBUG_PATTERN_DETECTION` in `src/PatternDetection.cpp`, and neither build defines it, so no window is drawn for any clip. `test/` is never checked out and its blobs are never fetched, because it holds flashing test videos. docs/SAFETY.md applies.

## Usage

```
make iris-pool                                  every clip in media/
make iris-run VIDEO=media/HAZARD_clip.webm      one clip
make iris-selftest                              does the flagging work, both ways
```

`run.py` writes one report per clip into `results/baselines/iris/`, in the shared schema of `eval/baselines/README.md`.

Flags, read from `example/main.cpp` at the pinned commit:

| Flag | Meaning |
|---|---|
| `-v <file>` | Analyze this video. Without `-v`, IrisApp analyzes every file in `./TestVideos`. |
| `-j true` or `-j 1` | Also write JSON results |
| `-p true`, `1`, `false` or `0` | Turn pattern detection on or off, overriding `appsettings.json` |
| `-r true`, `1`, `false` or `0` | Turn frame resizing on or off |
| `-a <number>` | Set the safe-area proportion |

IrisApp returns exit code 0 even when analysis fails, so `run.py` checks that a non-empty `framedata.csv` was written instead of trusting the exit code.

## Two things this build of IRIS gets wrong, both found by running it

**A file it cannot decode comes back PASS.** On two of the Theora `.ogv` clips in this pool, IrisApp logs "Video analysis started", "Video analysis ended", "Elapsed time: 0 ms", writes a `framedata.csv` with nothing but a header, writes a `result.json` saying `"OverallResult": "Pass"`, and exits 0. Nothing in its output says it never saw a frame. That is the one failure mode a candidate list must not inherit, so `run.py` treats a frame data file with no frames in it as a failure, writes no report for that clip, and records it in `results/baselines/iris_failures.json`. No report means no candidate list, which means `eval/labeling/make_pool.py` keeps the title out of the pool, which is the answer that is true. A report saying IRIS found nothing would be indistinguishable from one saying it never looked.

**A negative first timestamp is written malformed.** `msToTimeSpan` in `include/iris/FrameData.h` pads the seconds field with a leading zero whenever it is under ten, and does not exclude negative seconds, so a frame whose presentation time is before zero is written as `00:00:0-0.001000`. Four clips here have one. `run.py` strips that leading zero rather than losing the title over it.

Neither is a criticism of IRIS's analysis, which is not what these are. They are what happens at the edges of somebody else's example app, and both were found by running it over real files rather than by reading it.

## What counts as a flag

`framedata.csv` carries `LuminanceFrameResult` and `RedFrameResult` per frame, each one of 0 pass, 1 pass with warning, 2 extended fail, 3 flash fail, and `PatternFrameResult`, 0 pass or 1 fail. A frame is flagged when a flash result is 2 or more, or the pattern result is 1.

IRIS's "pass with warning" is flashing between 2 and 3 Hz, which IRIS passes. Those frames are counted in `warning_frames` and are not segments, so the candidate list is what IRIS failed rather than everything it noticed. `--include-warnings` moves that line and `params.include_warnings` records where it was.

Pattern detection is off, which is upstream's default in `config/appsettings.json`. Our own regular-pattern rule is a separate thing and is measured separately; turning IRIS's on would compare two pattern rules under a flash heading.

A flagged frame covers the frame it is, so its interval is `[t, t + one frame)`. Without the frame duration a single flagged frame would be a zero length interval, and the shared window mapping in `eval/metrics.py` drops an interval whose end is not after its start, which would lose it in silence.

## The selftest, and that it has been seen to fail

`make iris-selftest` generates a static mid-gray clip and a 10 Hz full-field black to white clip, analyses both and deletes both in the same job, and fails if the gray one produces a segment or the flashing one does not. Both directions were broken on purpose on Sep 18, 2026: `FLASH_FAIL_FROM = 0` makes it fail with "flagged a clip where nothing happens", `FLASH_FAIL_FROM = 4` with "missed a 10 Hz full-field flash". A green selftest on its own would prove nothing.

## Deviations from upstream

- Tests are not built, and `test/` is excluded from the checkout (safety).
- The native build links against Homebrew's dependencies rather than vcpkg's, as above.
- IRIS's CMakeLists calls `find_package(FFMPEG REQUIRED)`, which is vcpkg's module and not one CMake ships. `build-native.sh` writes a four line stand-in over Homebrew's ffmpeg with the same two output variables.
- This Mac's Command Line Tools ship an empty `usr/include/c++/v1`, and clang stops there instead of falling through to the SDK copy, so every C++ standard header comes back "file not found". The build passes `-nostdinc++ -isystem $(xcrun --show-sdk-path)/usr/include/c++/v1`. Nothing about IRIS; it would bite any C++ build on this machine.
- The Docker path additionally installs dependencies in staged steps before CMake configure instead of only during configure. The versions and features are the same, so the installed packages are the same.
