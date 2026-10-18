#!/usr/bin/env bash
# Dependency patches need a local committer identity, not the reviewer's Git settings.
# A patch failure must stop setup; it must never be treated as an already-patched player.
set -eu
cd "$(dirname "$0")/shaka-player"
git -c user.name='Calm Frames dependency build' \
    -c user.email='dependency-build@invalid.example' \
    am --3way shaka-rel/shaka-patch/*.patch
