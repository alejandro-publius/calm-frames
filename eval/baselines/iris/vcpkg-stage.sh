#!/bin/sh
# Install IRIS's vcpkg dependencies in manifest mode, into the install root
# that IRIS's "linux-release" CMake preset uses (the vcpkg toolchain's default,
# <binaryDir>/vcpkg_installed). Runs inside the Dockerfile's build stage.
#
#   vcpkg-stage.sh <label>             install upstream's vcpkg.json unchanged
#   vcpkg-stage.sh <label> <port>...   install a manifest listing only these
#                                      ports, with upstream's builtin-baseline
#
# vcpkg's manifest mode is incremental: packages already in the install root
# with a matching ABI are kept, so each call builds only what is new. If the
# install fails, the newest vcpkg build logs are printed so that the docker
# build log shows the cause.
set -eu

label=$1
shift
src=/src/iris
install_root=$src/bin/build/linux-release/vcpkg_installed

# Same triplet the vcpkg CMake toolchain picks for a native Linux build.
case "$(uname -m)" in
    x86_64) triplet=x64-linux ;;
    aarch64 | arm64) triplet=arm64-linux ;;
    *)
        echo "vcpkg-stage: unsupported architecture $(uname -m)" >&2
        exit 1
        ;;
esac

if [ "$#" -gt 0 ]; then
    baseline=$(sed -n 's/.*"builtin-baseline": *"\([0-9a-f]\{40\}\)".*/\1/p' "$src/vcpkg.json")
    if [ -z "$baseline" ]; then
        echo "vcpkg-stage: no builtin-baseline found in $src/vcpkg.json" >&2
        exit 1
    fi
    deps=""
    for port in "$@"; do
        deps="$deps${deps:+, }\"$port\""
    done
    manifest_dir=$(mktemp -d)
    printf '{"name": "iris-deps-%s", "version-string": "0", "dependencies": [%s], "builtin-baseline": "%s"}\n' \
        "$label" "$deps" "$baseline" > "$manifest_dir/vcpkg.json"
else
    manifest_dir=$src
fi

echo "== vcpkg-stage $label: triplet $triplet, jobs ${VCPKG_MAX_CONCURRENCY:-default}, manifest:"
cat "$manifest_dir/vcpkg.json"
started=$(date +%s)

if ! "$VCPKG_ROOT/vcpkg" install \
        --triplet "$triplet" \
        --x-wait-for-lock \
        --x-manifest-root="$manifest_dir" \
        --x-install-root="$install_root" \
        --clean-after-build; then
    echo "== vcpkg-stage $label: FAILED after $(( $(date +%s) - started )) s. Newest build logs:" >&2
    find "$VCPKG_ROOT/buildtrees" -type f -name '*.log' -exec ls -t {} + 2>/dev/null | head -n 6 |
        while read -r log; do
            echo "---- $log" >&2
            tail -n 80 "$log" >&2
        done
    exit 1
fi

if [ "$manifest_dir" != "$src" ]; then
    rm -rf "$manifest_dir"
fi
echo "== vcpkg-stage $label: done in $(( $(date +%s) - started )) s"
