# The ingest container: one upload in, one checked title out.
#
# It runs the same code as the local pipeline, so a title built on AWS is built
# the same way as a title built on a laptop. Build it from the repository root,
# because the build context is the repository root filtered by .dockerignore:
#
#   make image            build it for ARM64 and print what is inside
#   make image-smoke      run it with no AWS at all and read its refusal
#   make image-context    list every file the build would send
#
# Three choices worth knowing about:
#
#   ARM64. Fargate charges about 20 percent less for ARM than for x86 and the
#   work here is ffmpeg and numpy, both of which have good aarch64 builds. It
#   matches the machine this was written on, so the image that gets tested is
#   the image that gets pushed.
#
#   The base image is pinned by digest, not by tag. A tag moves. The digest is
#   the multi-architecture index for python:3.12.13-slim-bookworm, so this same
#   line builds on an x86 machine as well and still gets a reviewed image.
#
#   Hashes for every Python package. pip runs with --require-hashes, so a
#   package that has been replaced upstream fails the build instead of shipping.
#
FROM python:3.12.13-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2

LABEL org.opencontainers.image.title="calm-frames-ingest" \
      org.opencontainers.image.description="Analyze one uploaded video and publish only what verify passed" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.source="https://github.com/alejandro-publius/calm-frames"

# ffmpeg carries the decoders, the x264 encoder and ffprobe. No recommends, so
# this does not drag in a desktop stack. The apt lists go afterwards: they are
# the largest thing in the layer and nothing at run time reads them.
#
# Pinned by exact apt version, not by the bare package name. The bare name was
# what this line used to say, and it meant the decoder inside the image could
# change under a rebuild without anything in the repository changing. It is not
# the same ffmpeg as the one on the machine this was written on, which is 9.0.1
# from Homebrew, and docs/ENVIRONMENT.md says so under "The three ffmpegs".
#
# When Debian ships a security update it bumps the deb12uN suffix and drops the
# superseded version from the mirror, so one day this build will stop with
# "Version '...' for 'ffmpeg' was not found". That is the pin working. Read the
# current version off https://packages.debian.org/bookworm/ffmpeg, change the
# ARG, and record the change in docs/ENVIRONMENT.md.
ARG FFMPEG_APT_VERSION=7:5.1.9-0+deb12u1
RUN apt-get update \
    && apt-get install -y --no-install-recommends "ffmpeg=${FFMPEG_APT_VERSION}" \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -version | head -1 \
    && ffmpeg -hide_banner -filters | grep -q photosensitivity

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/opt/calmframes

WORKDIR /opt/calmframes

COPY pipeline/infra/ingest/requirements.txt /tmp/requirements.txt
RUN python -m pip install --require-hashes --no-deps -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# flashmap comes from this repository, not from PyPI, so the analyzer in the
# image is the analyzer in the commit. --no-deps because everything it needs is
# already installed above, from hashes.
COPY flashmap /opt/calmframes/flashmap
RUN python -m pip install --no-deps /opt/calmframes/flashmap

# The pipeline is a plain package on PYTHONPATH. The entrypoint is copied to a
# path of its own rather than run as pipeline.infra.ingest.entrypoint, because
# pipeline/infra is a directory of scripts on sys.path, not an importable
# subpackage, and the CDK app and its tests both rely on that.
COPY pipeline /opt/calmframes/pipeline
COPY pipeline/infra/ingest/entrypoint.py /opt/calmframes/ingest_entrypoint.py

# A task that only ever reads one upload and writes artifacts has no reason to
# be root. /work is the only writable place it needs.
RUN useradd --create-home --uid 10001 calm \
    && mkdir -p /work \
    && chown calm:calm /work
USER 10001
WORKDIR /work

ENTRYPOINT ["python", "/opt/calmframes/ingest_entrypoint.py"]
