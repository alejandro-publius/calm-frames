#!/bin/sh
# Build EA IRIS's example console app (IrisApp) natively on this Mac, with no Docker.
#
#   sh eval/baselines/iris/build-native.sh
#
# The Docker path in Dockerfile is still the reproducible one and is still the right
# thing on a CI runner. It was not used here: the colima VM on this machine is shared
# with another project, and a vcpkg source build of the whole OpenCV tree inside it is
# what pushed it into its memory limit once already. CLAUDE.md says never to restart
# colima and never to touch containers, images or volumes we did not create, so this
# build does not go near it.
#
# What this does instead: the same upstream source at the same pinned commit, built
# against Homebrew's OpenCV 4, ffmpeg, spdlog and nlohmann-json rather than against
# vcpkg's. Those are different builds of the same libraries, so this is a deviation and
# it is recorded in BUILD_INFO.txt beside the binary and in docs/DECISIONS.md. Anything
# measured with it carries the build it came from, in its own report file.
#
# The app and its appsettings.json install outside the repository, because a binary is
# not something this repository commits:
#
#   ~/.cache/calm-frames/iris/IrisApp
#   ~/.cache/calm-frames/iris/appsettings.json
#   ~/.cache/calm-frames/iris/BUILD_INFO.txt
#
# test/ is never checked out and its blobs are never fetched: it holds flashing test
# videos, and docs/SAFETY.md says those do not come near this machine.
set -eu

# Same pins the Dockerfile uses, read out of it so the two cannot drift apart.
HERE=$(cd "$(dirname "$0")" && pwd)
IRIS_COMMIT=$(sed -n 's/^ARG IRIS_COMMIT=//p' "$HERE/Dockerfile")
if [ -z "${IRIS_COMMIT:-}" ]; then
    echo "build-native: no IRIS_COMMIT in $HERE/Dockerfile" >&2
    exit 1
fi

PREFIX=${IRIS_PREFIX:-$HOME/.cache/calm-frames/iris}
WORK=${IRIS_WORK:-$(mktemp -d)}
JOBS=${IRIS_BUILD_JOBS:-4}
BREW=${BREW_PREFIX:-/opt/homebrew}

for tool in git cmake ninja pkg-config; do
    if ! command -v "$tool" > /dev/null 2>&1 && ! [ -x "$BREW/bin/$tool" ]; then
        echo "build-native: $tool is not here. brew install cmake ninja pkgconf" >&2
        exit 1
    fi
done
PATH="$BREW/bin:$PATH"
export PATH

if [ ! -d "$BREW/opt/opencv@4/lib/cmake/opencv4" ]; then
    echo "build-native: no Homebrew opencv@4. brew install opencv@4 spdlog nlohmann-json ffmpeg" >&2
    exit 1
fi

# This Mac's Command Line Tools ship an empty usr/include/c++/v1, and clang stops there
# rather than falling through to the SDK's copy, so every C++ standard header comes back
# "file not found". Pointing at the SDK's libc++ headers is the whole fix. Recorded in
# docs/FRICTION_LOG.md territory rather than papered over: without these two flags the
# build fails on `#include <vector>`.
SDK=$(xcrun --show-sdk-path)
CXX_FLAGS="-nostdinc++ -isystem $SDK/usr/include/c++/v1"

SRC=$WORK/iris-src
BUILD=$WORK/iris-build
rm -rf "$SRC" "$BUILD"
git init -q "$SRC"
git -C "$SRC" remote add origin https://github.com/electronicarts/IRIS.git
git -C "$SRC" fetch -q --depth 1 --filter=blob:none origin "$IRIS_COMMIT"
git -C "$SRC" config core.sparseCheckout true
printf '/*\n!/test/\n' > "$SRC/.git/info/sparse-checkout"
git -C "$SRC" checkout -q --detach FETCH_HEAD
test "$(git -C "$SRC" rev-parse HEAD)" = "$IRIS_COMMIT"
test ! -e "$SRC/test"

# IRIS's CMakeLists does find_package(FFMPEG REQUIRED), which is vcpkg's module, not one
# CMake ships. This stands in for it with the same two variables, over Homebrew's ffmpeg.
mkdir -p "$WORK/cmake-shims"
cat > "$WORK/cmake-shims/FindFFMPEG.cmake" <<'SHIM'
find_package(PkgConfig REQUIRED)
pkg_check_modules(_FFMPEG REQUIRED IMPORTED_TARGET libavformat libavcodec libavutil)
set(FFMPEG_INCLUDE_DIRS ${_FFMPEG_INCLUDE_DIRS})
set(FFMPEG_LIBRARIES PkgConfig::_FFMPEG)
set(FFMPEG_FOUND TRUE)
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(FFMPEG DEFAULT_MSG FFMPEG_LIBRARIES)
SHIM

cmake -S "$SRC" -B "$BUILD" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLE_APP=ON -DBUILD_TESTS=OFF -DEXPORT_IRIS=OFF -DEXPORT_UTILS=OFF \
    -DCMAKE_MODULE_PATH="$WORK/cmake-shims" \
    -DOpenCV_DIR="$BREW/opt/opencv@4/lib/cmake/opencv4" \
    -DCMAKE_PREFIX_PATH="$BREW;$BREW/opt/opencv@4" \
    -DCMAKE_OSX_SYSROOT="$SDK" \
    -DCMAKE_CXX_FLAGS="$CXX_FLAGS"

cmake --build "$BUILD" -j "$JOBS"

mkdir -p "$PREFIX"
install -m 0755 "$BUILD/example/IrisApp" "$PREFIX/IrisApp"
install -m 0644 "$BUILD/example/appsettings.json" "$PREFIX/appsettings.json"
install -m 0644 "$SRC/LICENSE.txt" "$PREFIX/IRIS-LICENSE.txt"
install -m 0644 "$SRC/NOTICE.txt" "$PREFIX/IRIS-NOTICE.txt"

{
    echo "iris_repo=https://github.com/electronicarts/IRIS"
    echo "iris_commit=$IRIS_COMMIT"
    echo "built_by=eval/baselines/iris/build-native.sh"
    echo "built_on=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "machine=$(uname -sm)"
    echo "compiler=$(c++ --version | head -n 1)"
    echo "sdk=$SDK"
    echo "cmake=$(cmake --version | head -n 1)"
    echo "opencv=$("$BREW/opt/opencv@4/bin/opencv_version" 2>/dev/null || echo unknown)"
    echo "ffmpeg_libavformat=$(pkg-config --modversion libavformat)"
    echo "spdlog=$(pkg-config --modversion spdlog 2>/dev/null || echo unknown)"
    echo "dependency_source=Homebrew, not vcpkg. See the note at the top of this script."
    echo "tests_built=no"
    echo "test_videos_fetched=no"
} > "$PREFIX/BUILD_INFO.txt"

echo
echo "IrisApp installed in $PREFIX"
cat "$PREFIX/BUILD_INFO.txt"
if [ -z "${IRIS_WORK:-}" ]; then
    rm -rf "$WORK"
fi
