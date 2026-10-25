#!/bin/zsh
# Render the brand SVGs to the PNG sizes Amazon asks for.
#
#     ./render.sh
#
# Sizes, and where each one is required, are in docs/brand/README.md. Nothing
# here invents a size: every one is quoted from a primary Amazon page there.
#
# Why headless Chrome. This Mac has no rsvg-convert, no cairosvg and no
# inkscape, and the two Python routes both need a native cairo. Chrome is
# already installed, renders SVG the same way the browsers everyone checks
# these files in do, and needs nothing added to the machine. The SVG is wrapped
# in a margin free page so the output is exactly the size asked for, and
# --force-device-scale-factor=1 stops a retina display doubling it.
#
# The tile is flattened onto its own teal rather than left with an alpha
# channel, because the Fire TV App Icon is specified as PNG with no
# transparency. The icons keep their alpha: the mark is a rounded square and
# the corners have to be see through.
set -e
CALM_BRAND_TOOLS="$(cd "$(dirname "$0")" && pwd)"
cd "$CALM_BRAND_TOOLS/../../assets/brand"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
QT_RENDERER=""
if command -v pkg-config >/dev/null && pkg-config --exists Qt6Svg; then
  mkdir -p ../../../build/brand
  QT_RENDERER="$(cd ../../../build/brand && pwd)/render-svg"
  c++ -std=c++17 -fPIC -isystem "$(xcrun --show-sdk-path)/usr/include/c++/v1" \
    "$CALM_BRAND_TOOLS/render_qt.cpp" $(pkg-config --cflags --libs Qt6Svg) -o "$QT_RENDERER"
elif [ ! -x "$CHROME" ]; then
  echo "Google Chrome is not at $CHROME. Install it, or render the SVGs some other way." >&2
  exit 2
fi

BRAND="$(pwd)"
DOCS="$BRAND/../../../docs/brand"
IMAGE="$BRAND/../image"
mkdir -p "$DOCS" "$IMAGE"

render() {  # render SVG WIDTH HEIGHT OUT
  local svg="$1" w="$2" h="$3" out="$4"
  if [ -n "$QT_RENDERER" ]; then
    QT_QPA_PLATFORM=offscreen "$QT_RENDERER" "$BRAND/$svg" "$w" "$h" "$out"
    echo "  $(basename "$out")  ${w}x${h} (Qt SVG)"
    return
  fi
  local tmp
  tmp="$(mktemp -d)"
  cat > "$tmp/page.html" <<HTML
<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:transparent;}
img{display:block;width:${w}px;height:${h}px;}</style>
<img src="file://$BRAND/$svg">
HTML
  "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --default-background-color=00000000 --force-device-scale-factor=1 \
    --virtual-time-budget=2000 \
    --window-size="${w},${h}" --screenshot="$out" "file://$tmp/page.html" \
    >/dev/null 2>&1
  rm -rf "$tmp"
  echo "  $(basename "$out")  ${w}x${h}"
}

BUST=calm-frames-mark-bust.svg
HEAD=calm-frames-mark-head.svg
TILE=calm-frames-tile-1280x720.svg

echo "manifest icon (assets/image, 512x512, under 1 MB):"
render "$BUST" 512 512 "$IMAGE/CalmFrames.png"

echo "Appstore listing:"
render "$BUST" 512 512 "$DOCS/appstore-icon-512.png"
render "$BUST" 114 114 "$DOCS/appstore-icon-114.png"
render "$TILE" 1280 720 "$DOCS/firetv-app-icon-1280x720.png"

echo "previews:"
render "$BUST" 1024 1024 "$DOCS/preview-1024.png"
render "$BUST" 256 256 "$DOCS/preview-256.png"
# Under 96 px the bust loses the face to the robe, so the small sizes use the
# head mark, which is the same person drawn larger in the same frame.
render "$HEAD" 48 48 "$DOCS/preview-48.png"

echo "done"
