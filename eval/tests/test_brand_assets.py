"""The brand image check covers every image, and it can actually fail.

Two things have to be true of eval/brand_assets_check.py for it to be worth
running. It has to look at every image that ships, and it has to notice a bad
one. A check that quietly stopped covering a file, or that passed everything
put in front of it, would read exactly like a check that works.

The second test generates a deliberately flashing file. docs/SAFETY.md applies:
it is 320 by 180, it lives in a temporary directory, it is analysed and deleted
inside this test, and nothing ever opens it in a player.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brand_assets_check import ASSETS, REPO, check_one  # noqa: E402

SEARCHED = [REPO / "docs/brand", REPO / "app/assets/image"]


def test_every_shipped_image_is_in_the_list():
    on_disk = {
        path.resolve()
        for folder in SEARCHED
        if folder.is_dir()
        for path in folder.rglob("*.png")
    }
    listed = {asset.resolve() for asset in ASSETS}

    missed = sorted(path.relative_to(REPO).as_posix() for path in on_disk - listed)
    assert not missed, (
        "these images ship and the flashmap check never looks at them: "
        f"{missed}. Add them to ASSETS in eval/brand_assets_check.py."
    )

    gone = sorted(path.relative_to(REPO).as_posix() for path in listed - on_disk)
    assert not gone, f"ASSETS names files that are not there: {gone}"


def test_the_check_says_no_to_something_that_really_flashes():
    """The negative control.

    Without this the passing run above says nothing: it could mean the images
    are calm, or it could mean the check cannot tell. This builds a full frame
    black to white alternation at 10 Hz, which is five flashes a second against
    a limit of three, and asserts the check refuses it.
    """
    if not subprocess.run(
        ["ffmpeg", "-version"], capture_output=True
    ).returncode == 0:
        pytest.skip("ffmpeg is not on this machine")

    with tempfile.TemporaryDirectory() as work:
        flashing = Path(work) / "HAZARD_negative_control.apng"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=320x180:r=20:d=2",
                # Frame number drives the luminance, so it swings between
                # 16 and 235 every two frames at 20 fps: a 10 Hz alternation.
                "-vf",
                "geq=lum='if(eq(mod(floor(N/2),2),0),16,235)':cb=128:cr=128",
                "-plays", "0",
                str(flashing),
            ],
            check=True,
        )
        assert flashing.is_file()

        passed, output = check_one(flashing)

    assert not passed, (
        "the brand check passed a file alternating black and white five times a "
        "second, so it would pass anything"
    )
    assert "over the thresholds" in output
