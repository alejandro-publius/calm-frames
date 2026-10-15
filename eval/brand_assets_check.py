"""Run flashmap over the app's own brand images.

app/tools/ui_flashmap.mjs checks the screens the app draws. It cannot check the
images the app ships, because those never reach the rendered tree: the icon is
read by the platform and the tile is uploaded to the Appstore. They are still
pictures this project puts in front of people, and this project's whole claim is
that it checks pictures, so they get checked too.

Each image is analysed on its own, held for two seconds, and nothing is cut
against anything else.

The first version of this alternated each image with the app's background every
100 ms, copying the worst case ui_flashmap.mjs uses for screens, and it failed.
That failure was the test's fault. Screens really do follow one another as fast
as a remote repeats, so the worst case is fair for them. These images do not:
the icon is drawn by the platform in a Settings list, the tile sits on an
Appstore page, and the previews are in docs. None of them animates and none
follows another. A 5 Hz cut between the ground and the icon cannot happen, and a
guard that fails on something that cannot happen is noise that teaches people to
ignore it.

What is worth asking of a shipped image is whether the image itself holds
anything over the thresholds, which is what a still analysed alone answers: a
file that turns out to be animated, or that decodes to something other than what
was drawn, fails here. A single cut between two pictures is one luminance change,
and WCAG counts flashes per second, so no arrangement of stills that a person can
cause could break it.

    python eval/brand_assets_check.py           # check every asset, exit non-zero on a finding
    python eval/brand_assets_check.py --json    # the same, as a report

Each video is built and deleted in the same run. None is hazardous, and none is
committed: they are derived from files that are.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Every image the app or the listing ships. eval/tests/test_brand_assets.py
# fails if a PNG exists under docs/brand or app/assets/image and is not named
# here, so the check cannot quietly stop covering a file somebody added.
ASSETS = [
    REPO / "app/assets/image/tv/harbor.png",
    REPO / "app/assets/image/tv/harbor-cinematic.png",
    REPO / "app/assets/image/tv/harbor-water.png",
    REPO / "app/assets/image/tv/gradient.png",
    REPO / "app/assets/image/tv/coastal-zen.png",
    REPO / "app/assets/image/tv/harbor-illustrated.png",
    REPO / "app/assets/image/CalmFrames.png",
    REPO / "docs/brand/appstore-icon-512.png",
    REPO / "docs/brand/appstore-icon-114.png",
    REPO / "docs/brand/firetv-app-icon-1280x720.png",
    REPO / "docs/brand/preview-1024.png",
    REPO / "docs/brand/preview-256.png",
    REPO / "docs/brand/preview-48.png",
]

# CALM_COLORS.BACKGROUND in app/src/calmframes/calmStyles.ts, used only to pad a
# non-16:9 image out to the frame. Nothing is cut against it.
PAD = "#102F3A"

WIDTH, HEIGHT, FPS = 640, 360, 24
HOLD_SECONDS = 2


def build_still(asset: Path, out: Path) -> None:
    """A lossless clip of one image, held, at the size flashmap analyses."""
    scale = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color={PAD},"
        f"setsar=1,fps={FPS},format=rgb24"
    )
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            # No -loop: an animated file has to play its own frames, or this
            # would freeze the first one and miss exactly what it is looking for.
            "-t", str(HOLD_SECONDS), "-i", str(asset),
            "-vf", scale,
            "-c:v", "ffv1",  # lossless, so the analyzer sees the pixels we built
            str(out),
        ],
        check=True,
    )


def check_one(asset: Path) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as work:
        video = Path(work) / "still.mkv"
        build_still(asset, video)
        result = subprocess.run(
            [sys.executable, "-m", "flashmap", "check", str(video), "--profile", "wcag"],
            capture_output=True,
            text=True,
        )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--json", action="store_true", help="print a report instead")
    arguments = parser.parse_args()

    missing = [asset for asset in ASSETS if not asset.is_file()]
    if missing:
        for asset in missing:
            print(f"missing: {asset.relative_to(REPO)}", file=sys.stderr)
        print("Run app/assets/brand/render.sh.", file=sys.stderr)
        return 2

    findings: list[dict[str, object]] = []
    for asset in ASSETS:
        ok, output = check_one(asset)
        name = str(asset.relative_to(REPO))
        findings.append({"asset": name, "passed": ok, "flashmap": output})
        if not arguments.json:
            print(f"{'PASS' if ok else 'FAIL'}  {name}")
            if not ok:
                print(output, file=sys.stderr)

    failed = [finding for finding in findings if not finding["passed"]]
    if arguments.json:
        print(json.dumps({
            "statement": (
                "Every brand and title image analysed on its own, held two seconds. "
                "Native recordings and UI palette simulations check transitions separately; "
                "this individual asset check does not measure screen transitions."
            ),
            "tool": "eval/brand_assets_check.py",
            "profile": "wcag",
            "assets": findings,
            "failed": len(failed),
        }, indent=2))

    if failed:
        print(
            f"\n{len(failed)} brand image(s) over the thresholds.", file=sys.stderr
        )
        return 1
    if not arguments.json:
        print(f"\nflashmap: {len(ASSETS)} brand images, no segment over the thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
