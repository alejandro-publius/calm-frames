#!/usr/bin/env bash
#
# Build the three release packages and get everything ready for a GitHub
# Release, then stop.
#
#   make release                 build, then print what would be attached
#   make release RELEASE_ARGS="--skip-build"
#   make release RELEASE_ARGS="--tag v0.2.0 --pin 4821"
#
# This never publishes. It prints the exact gh command it would run and exits.
# Publishing is a person's decision: the judged release tag can never move once
# it exists, so nothing automatic should be able to create it.
#
# Building the app is the app lane's work. This only calls their build script.
# If the build fails, read the error, say so, and do not edit app source.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHES="armv7 aarch64 x86_64"
SKIP_BUILD=0
TAG=""
DEMO_PIN="${DEMO_PIN:-}"

usage() {
  # The comment block at the top of this file is the help text, so the two can
  # never drift apart. It ends at the first line that is not a comment.
  sed -n '2,/^[^#]/p' "$0" | sed 's/^# \{0,1\}//' | sed '$d'
  exit 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    --skip-build) SKIP_BUILD=1 ;;
    --tag) shift; TAG="${1:-}" ;;
    --pin) shift; DEMO_PIN="${1:-}" ;;
    -h|--help) usage ;;
    *) echo "release: unknown argument '$1'" >&2; exit 2 ;;
  esac
  shift
done

VERSION="$(sed -n 's/^version = "\(.*\)".*/\1/p' "$REPO/app/manifest.toml" | head -1)"
PKG_ID="$(sed -n 's/^id = "\(io\.[^"]*\)".*/\1/p' "$REPO/app/manifest.toml" | head -1)"
OS_VERSIONS="$(sed -n 's/.*"\(1\.[0-9]*\)".*/\1/p' "$REPO/app/build/aarch64-release/vpkg-info.json" 2>/dev/null | head -1)"
[ -n "$VERSION" ] || VERSION="0.0.0"
[ -n "$TAG" ] || TAG="v$VERSION"
[ -n "$OS_VERSIONS" ] || OS_VERSIONS="1.2"

OUT="$REPO/build/release/$TAG"

echo "Calm Frames release, $TAG"
echo "  package id: $PKG_ID"
echo "  app version: $VERSION"
echo

# ------------------------------------------------------------------ build

if [ "$SKIP_BUILD" = "1" ]; then
  echo "Skipping the build. Using whatever is already in app/build."
else
  echo "Building all three architectures. This takes a few minutes."
  echo "Command: npm run build:app, with Node 22 from fnm and JDK 21 for Shaka."
  set +e
  ( cd "$REPO/app" \
      && source ~/vega/env \
      && eval "$(fnm env --shell bash)" \
      && fnm use 22 \
      && export JAVA_HOME=/opt/homebrew/opt/openjdk@21 \
      && export PATH="$JAVA_HOME/bin:$PATH" \
      && npm run build:app )
  build_status=$?
  set -e
  if [ "$build_status" -ne 0 ]; then
    cat >&2 <<BROKEN

The app build failed (exit $build_status).

The app lane owns app/. Do not patch their files to get a release out: read the
error above, tell them what broke, and rerun this once they have landed a fix.

To assemble the release from the packages already in app/build:
  make release RELEASE_ARGS="--skip-build"
BROKEN
    exit "$build_status"
  fi
fi

# ---------------------------------------------------------------- collect

rm -rf "$OUT"
mkdir -p "$OUT"

missing=0
for arch in $ARCHES; do
  src="$REPO/app/build/${arch}-release/calm-frames-app_${arch}.vpkg"
  if [ ! -f "$src" ]; then
    echo "missing: $src" >&2
    missing=1
    continue
  fi
  cp "$src" "$OUT/calm-frames-${VERSION}-${arch}.vpkg"
done

if [ "$missing" -ne 0 ]; then
  echo "" >&2
  echo "Not every architecture built. Run without --skip-build, or fix the build." >&2
  exit 1
fi

# A package older than the source it came from is the classic way to ship last
# week's code. Say so rather than letting it through quietly.
newest_source="$(find "$REPO/app/src" -type f -newer "$REPO/app/build/aarch64-release/calm-frames-app_aarch64.vpkg" 2>/dev/null | head -1)"
if [ -n "$newest_source" ]; then
  echo "warning: app source is newer than the packages, for example:" >&2
  echo "  $newest_source" >&2
  echo "  rerun without --skip-build before publishing anything." >&2
  echo
fi

( cd "$OUT" && shasum -a 256 ./*.vpkg > SHA256SUMS )

# ------------------------------------------------------------------ notes

if [ -n "$DEMO_PIN" ]; then
  pin_block="The demo PIN is \`$DEMO_PIN\`. It opens the parent area, where the preset, the
room settings and the log of what was hidden live. Kid mode itself needs no PIN.

It is four digits on a device anyone can pick up, and the parent area can only
make the filter stricter, never weaker. Treat it as a lock on a drawer, not on a
door."
else
  pin_block="**No PIN is published here, because the app does not ship with one.** The parent
area is locked with a four digit PIN that a person sets on the device the first
time they open it (app/src/calmframes/parentGate.ts: with nothing set it says
\"No PIN is set yet\"). Only the salted hash is stored, so nobody can read the PIN
back off a device either.

Set the demo PIN on the demo stick, then build the notes with it:

    make release RELEASE_ARGS=\"--pin 1234\"

This file will not invent one, and a PIN in a public release should be one you
do not use anywhere else."
fi

cat > "$OUT/NOTES.md" <<NOTES
# Calm Frames $TAG

A verified safety layer for kids with photosensitive epilepsy. Every frame of a
title is analyzed before it can play in kid mode, and the player hides each
flagged flashing segment before it starts while sound and captions carry on.

Not a medical device. It reduces exposure to flashing above published limits in
the videos it plays.

## What is attached

| File | For |
|---|---|
| calm-frames-$VERSION-armv7.vpkg | Fire TV Stick |
| calm-frames-$VERSION-aarch64.vpkg | 64 bit Fire TV devices and the Vega Virtual Device |
| calm-frames-$VERSION-x86_64.vpkg | the x86 virtual device |
| SHA256SUMS | checksums for all three |

These are release builds for Vega OS $OS_VERSIONS. Release builds strip
\`console.log\`, so use a debug build from \`app/build/<arch>-debug/\` when you
need the app's own logs for a measurement run.

## Install it

You need the Vega SDK CLI and a device in developer mode. \`make stick-day\`
prints the developer mode steps and walks the whole first session.

    source ~/vega/env
    vega devmode login
    vega devmode enable-device --code <the 6 digit code on the TV>
    vega device is-connected
    vega run-app calm-frames-$VERSION-armv7.vpkg

Notes that save an hour:

- the package id is \`$PKG_ID\`. Developer mode will not sideload a package whose
  id starts with com.amazon, which is why this app is not called that.
- \`vega device list\` is in Amazon's documentation but crashes with a TypeError
  on Vega CLI 1.3.4. Use \`vega device info\` and \`vega device is-connected\`.
- the device has to be on Vega OS $OS_VERSIONS. On anything older, fall back to
  SDK 0.23.

## The PIN

$pin_block

## Verify what you installed

    shasum -a 256 -c SHA256SUMS

## Licence

Apache 2.0. See LICENSE and NOTICE in the repository.
NOTES

# ------------------------------------------------------- what would happen

echo "Ready in $OUT"
echo
echo "Would attach:"
for file in "$OUT"/*.vpkg "$OUT/SHA256SUMS"; do
  size="$(du -h "$file" | cut -f1 | tr -d '[:space:]')"
  echo "  $(basename "$file")  ($size)"
done
echo
echo "Release notes: $OUT/NOTES.md"
if [ -z "$DEMO_PIN" ]; then
  echo "  no PIN in the notes: the app ships without one and a person sets it on"
  echo "  the device. Pass --pin once the demo stick has one."
fi
echo
echo "The command this would run, and does not:"
echo
echo "  gh release create $TAG \\"
for file in "$OUT"/*.vpkg "$OUT/SHA256SUMS"; do
  echo "    \"$file\" \\"
done
echo "    --repo alejandro-publius/calm-frames \\"
echo "    --title \"Calm Frames $TAG\" \\"
echo "    --notes-file \"$OUT/NOTES.md\""
echo
echo "Nothing was published. No GitHub API call was made."
echo "Publishing is a person's step: once the judged release tag exists it can"
echo "never move, so read NOTES.md first and run the command yourself."
