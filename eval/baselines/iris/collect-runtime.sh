#!/bin/sh
# Collect what the Dockerfile's runtime stage needs from the build stage:
#   /opt/iris/share/ldd.txt               shared libraries IrisApp loads
#   /opt/iris/share/runtime-packages.txt  Ubuntu packages that own them
#   /opt/iris/share/BUILD_INFO.txt        pins and tool versions
#   /opt/iris/share/vcpkg-packages.txt    vcpkg packages linked into IrisApp's build
#   /opt/iris/share/licenses/<port>/      copyright files of those vcpkg packages
set -eu

: "${IRIS_COMMIT:?}" "${VCPKG_COMMIT:?}" "${UBUNTU_IMAGE:?}" "${VCPKG_ROOT:?}"

bin=/opt/iris/bin/IrisApp
share=/opt/iris/share
src=/src/iris
install_root=$src/bin/build/linux-release/vcpkg_installed

ldd "$bin" > "$share/ldd.txt"
if grep -q 'not found' "$share/ldd.txt"; then
    cat "$share/ldd.txt" >&2
    echo "collect-runtime: IrisApp has unresolved shared libraries" >&2
    exit 1
fi

# dpkg records some libraries under /lib and others under /usr/lib (merged
# /usr), so try the path ldd prints, its resolved target, and both prefixes.
libs=$(awk '$2 == "=>" && $3 ~ /^\// { print $3 } $1 ~ /^\// { print $1 }' "$share/ldd.txt" | sort -u)
packages=""
for lib in $libs; do
    pkg=""
    for path in "$lib" "$(readlink -f "$lib")"; do
        for candidate in "$path" "/usr$path" "${path#/usr}"; do
            pkg=$(dpkg -S "$candidate" 2>/dev/null | grep -v '^diversion' | head -n 1 | cut -d: -f1)
            if [ -n "$pkg" ]; then
                break 2
            fi
        done
    done
    if [ -z "$pkg" ]; then
        echo "collect-runtime: no Ubuntu package owns $lib" >&2
        exit 1
    fi
    packages="$packages $pkg"
done
printf '%s\n' $packages | sort -u > "$share/runtime-packages.txt"
echo "== runtime packages:"
cat "$share/runtime-packages.txt"

cmake_bin=$("$VCPKG_ROOT/vcpkg" fetch cmake --x-stderr-status 2>/dev/null | tail -n 1)
baseline=$(sed -n 's/.*"builtin-baseline": *"\([0-9a-f]\{40\}\)".*/\1/p' "$src/vcpkg.json")
{
    echo "iris_repo=https://github.com/electronicarts/IRIS"
    echo "iris_commit=$IRIS_COMMIT"
    echo "base_image=$UBUNTU_IMAGE"
    echo "vcpkg_commit=$VCPKG_COMMIT"
    echo "vcpkg_builtin_baseline=$baseline"
    echo "vcpkg_tool=$("$VCPKG_ROOT/vcpkg" version | head -n 1)"
    echo "cmake=$("$cmake_bin" --version | head -n 1)"
    echo "compiler=$(g++ --version | head -n 1)"
    echo "machine=$(uname -m)"
} > "$share/BUILD_INFO.txt"
echo "== build info:"
cat "$share/BUILD_INFO.txt"

"$VCPKG_ROOT/vcpkg" list --x-install-root="$install_root" > "$share/vcpkg-packages.txt"

for copyright in "$install_root"/*-linux/share/*/copyright; do
    port=$(basename "$(dirname "$copyright")")
    install -D -m 0644 "$copyright" "$share/licenses/$port/copyright"
done
