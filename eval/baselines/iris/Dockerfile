# IRIS baseline image for Calm Frames.
#
# Builds IrisApp, the example console application of EA IRIS
# (https://github.com/electronicarts/IRIS, BSD-3-Clause), at a pinned commit
# the way upstream builds it: CMake preset "linux-release", Ninja, and vcpkg in
# manifest mode with upstream's builtin-baseline. The runtime stage holds only
# IrisApp, its config file, license texts and the shared libraries it loads.
#
# Uses no BuildKit-only features, so the legacy builder works. Builds are
# native: build on an arm64 host for linux/arm64 and on an amd64 host for
# linux/amd64. See README.md for pins, usage and deviations from upstream.

# Ubuntu 22.04 LTS, pinned by the digest of its multi-arch index (it includes
# linux/amd64 and linux/arm64). 22.04 is the Linux image that vcpkg's own CI
# used at both pinned vcpkg commits below.
ARG UBUNTU_IMAGE=ubuntu:22.04@sha256:829f6df217bcbae2b371026e81711d1a787c61b2967ad09d015063663ebafbf7
# IRIS main at 2025-01-14 ("Update main (#7)"), the newest upstream commit.
ARG IRIS_COMMIT=d96978ac1107f3463b77f69a9c1b1ec5d45291a0
# vcpkg checkout that upstream's CI uses (vcpkgGitCommitId in
# .github/workflows/c-cpp.yml). Port versions come from the builtin-baseline
# in upstream's vcpkg.json, not from this commit.
ARG VCPKG_COMMIT=d320630b28aeb59b24424eb2a7ef3905314107a1
# Parallel compile jobs. Changing it invalidates every cached build layer.
ARG BUILD_JOBS=2

FROM ${UBUNTU_IMAGE} AS build

ENV DEBIAN_FRONTEND=noninteractive

# Build prerequisites, taken from vcpkg's bootstrap script and Linux CI image
# (scripts/azure-pipelines/linux/provision-image.sh at VCPKG_COMMIT), the apt
# step in upstream's CI, and the system requirements that ports in this
# dependency tree state (gtk3, at-spi2-core, libepoxy, libxcrypt, libsystemd,
# ffmpeg). cmake here is 3.22 and only bootstraps the vcpkg tool on arm64.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        autoconf autoconf-archive automake autopoint bison build-essential \
        ca-certificates cmake curl file flex gettext git gperf libltdl-dev \
        libtool libtool-bin m4 nasm ninja-build patch perl pkg-config \
        python-is-python3 python3 python3-jinja2 python3-packaging python3-pip \
        python3-setuptools python3-venv tar unzip xz-utils zip \
        libegl1-mesa-dev libgl1-mesa-dev libgles2-mesa-dev libx11-dev \
        libxcomposite-dev libxcursor-dev libxdamage-dev libxext-dev \
        libxfixes-dev libxi-dev libxinerama-dev libxrandr-dev libxrender-dev \
        libxtst-dev \
 && rm -rf /var/lib/apt/lists/*

ARG BUILD_JOBS
ENV VCPKG_ROOT=/opt/vcpkg \
    VCPKG_DISABLE_METRICS=1 \
    VCPKG_BINARY_SOURCES=clear \
    VCPKG_MAX_CONCURRENCY=${BUILD_JOBS} \
    CMAKE_BUILD_PARALLEL_LEVEL=${BUILD_JOBS}

# vcpkg with its full history up to VCPKG_COMMIT, because manifest mode reads
# the builtin-baseline and old port versions out of git. On arm64 the bootstrap
# script builds the vcpkg tool from source (tarball checked against the SHA-512
# pinned at VCPKG_COMMIT); on amd64 it downloads the pinned prebuilt binary.
ARG VCPKG_COMMIT
RUN git init -q "$VCPKG_ROOT" \
 && git -C "$VCPKG_ROOT" remote add origin https://github.com/microsoft/vcpkg.git \
 && git -C "$VCPKG_ROOT" fetch -q --no-tags origin "$VCPKG_COMMIT" \
 && git -C "$VCPKG_ROOT" checkout -q --detach FETCH_HEAD \
 && test "$(git -C "$VCPKG_ROOT" rev-parse HEAD)" = "$VCPKG_COMMIT" \
 && "$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics \
 && rm -rf "$VCPKG_ROOT/buildtrees" "$VCPKG_ROOT/downloads"

# IRIS source at IRIS_COMMIT. test/ is left out of the checkout and its blobs
# are never fetched: it holds flashing test videos, and tests are not built.
ARG IRIS_COMMIT
RUN git init -q /src/iris \
 && cd /src/iris \
 && git remote add origin https://github.com/electronicarts/IRIS.git \
 && git fetch -q --depth 1 --filter=blob:none origin "$IRIS_COMMIT" \
 && git config core.sparseCheckout true \
 && printf '/*\n!/test/\n' > .git/info/sparse-checkout \
 && git checkout -q --detach FETCH_HEAD \
 && test "$(git rev-parse HEAD)" = "$IRIS_COMMIT" \
 && test ! -e test

# Dependencies, in vcpkg manifest mode with upstream's builtin-baseline, into
# the install root that the linux-release preset uses. The first three steps
# are checkpoints: each installs a growing subset of the same dependency tree
# (same versions and features, so the same package ABIs). The last step
# installs upstream's vcpkg.json unchanged. If a step fails, a rebuild resumes
# from the last finished step instead of restarting the multi-hour install.
COPY vcpkg-stage.sh /usr/local/bin/vcpkg-stage.sh
RUN sh /usr/local/bin/vcpkg-stage.sh gtk3-stack gtk3
RUN sh /usr/local/bin/vcpkg-stage.sh codecs-dnn gtk3 ffmpeg protobuf flatbuffers
RUN sh /usr/local/bin/vcpkg-stage.sh contrib-deps gtk3 ffmpeg protobuf flatbuffers hdf5 tesseract
RUN sh /usr/local/bin/vcpkg-stage.sh upstream-manifest

# IrisApp via upstream's preset. CMakePresets.json uses schema version 6, which
# needs CMake 3.25 or newer, so configure and build use the CMake that vcpkg
# pins at VCPKG_COMMIT (3.30.1). The vcpkg toolchain still runs its manifest
# install during configure; it finds everything installed.
RUN cd /src/iris \
 && CMAKE="$("$VCPKG_ROOT/vcpkg" fetch cmake --x-stderr-status | tail -n 1)" \
 && "$CMAKE" --version \
 && "$CMAKE" --preset linux-release -DBUILD_EXAMPLE_APP=ON -DBUILD_TESTS=OFF \
 && "$CMAKE" --build --preset linux-release \
 && install -D -m 0755 bin/build/linux-release/example/IrisApp /opt/iris/bin/IrisApp \
 && install -D -m 0644 bin/build/linux-release/example/appsettings.json /opt/iris/share/appsettings.json \
 && cp LICENSE.txt NOTICE.txt /opt/iris/share/

# Runtime package list, build provenance and third-party license files.
ARG UBUNTU_IMAGE
COPY collect-runtime.sh /usr/local/bin/collect-runtime.sh
RUN sh /usr/local/bin/collect-runtime.sh

FROM ${UBUNTU_IMAGE} AS runtime
ARG UBUNTU_IMAGE
ARG IRIS_COMMIT
LABEL org.opencontainers.image.title="calm-frames-iris" \
      org.opencontainers.image.description="EA IRIS example CLI (IrisApp) built at a pinned commit" \
      org.opencontainers.image.source="https://github.com/electronicarts/IRIS" \
      org.opencontainers.image.revision="${IRIS_COMMIT}" \
      org.opencontainers.image.licenses="BSD-3-Clause" \
      org.opencontainers.image.base.name="${UBUNTU_IMAGE}"

COPY --from=build /opt/iris /opt/iris

# Install the Ubuntu packages that own IrisApp's shared libraries, check that
# every library resolves, and prepare the working directory. IrisApp reads
# appsettings.json from, and writes logs/ and Results/ into, its working
# directory.
RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update \
 && xargs -r -a /opt/iris/share/runtime-packages.txt apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && ldd /opt/iris/bin/IrisApp > /tmp/ldd.txt \
 && if grep -q 'not found' /tmp/ldd.txt; then cat /tmp/ldd.txt; exit 1; fi \
 && rm /tmp/ldd.txt \
 && mkdir -p /in /work/Results /work/logs \
 && cp /opt/iris/share/appsettings.json /work/appsettings.json \
 && chmod 1777 /in /work/Results /work/logs

WORKDIR /work
ENTRYPOINT ["/opt/iris/bin/IrisApp"]
