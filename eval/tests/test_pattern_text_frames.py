"""The pictures the pattern rule's text and UI precision is measured on.

This is the ground truth, so what it claims to have drawn has to be what is in the pixels.
Every guard was broken on purpose and seen red; the mutation is named in each docstring.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "eval") not in sys.path:
    sys.path.insert(0, str(REPO / "eval"))

from pattern_text_frames import HEIGHT, TEAL, WIDTH, frames, grating, text_page  # noqa: E402


def test_the_ground_truth_does_not_import_flashmap():
    """A ground truth that shares code with the thing it grades is not a ground truth.

    Read off the syntax tree rather than by importing, so a lazy import inside a function
    is caught too. Seen to fail by adding `import flashmap` to the module.
    """
    source = (REPO / "eval" / "pattern_text_frames.py").read_text()
    tree = ast.parse(source)
    named = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            named.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            named.append(node.module)
    assert not [name for name in named if name.split(".")[0] == "flashmap"], named


@pytest.mark.parametrize("orientation", ["vertical", "horizontal", "diagonal"])
@pytest.mark.parametrize("area", [0.30, 0.50, 0.80])
def test_a_grating_covers_the_area_it_says_it_does(orientation, area):
    """The label is the drawn area, so the drawn area has to be right.

    It was not, for the diagonal family: a square of side sqrt(a) * min(w, h) covers
    a * h / w of a 16:9 picture, which is 0.56 of what it claimed, and every diagonal row of
    the suite was mislabelled by that factor until the detector disagreed with the label.

    Seen to fail by putting min(WIDTH, HEIGHT) back: the diagonal cases go red at 0.28
    against 0.50.
    """
    picture = grating(12, area, orientation)
    ground = np.array(TEAL)
    drawn = float((np.abs(picture.astype(int) - ground).sum(axis=2) > 10).mean())
    assert drawn == pytest.approx(area, abs=0.02)


def test_a_page_of_text_draws_no_stripe_block():
    """The whole negative arm rests on this: a text page has nothing striped drawn into it."""
    for frame in frames():
        if frame.kind in ("text", "ui"):
            assert frame.drawn_pairs == 0
            assert frame.drawn_area == 0.0


def test_every_picture_is_one_display_and_they_are_all_different():
    """A suite that draws the same picture twice counts one case as two.

    Seen to fail by returning the same lambda for every colour pair, which is what a missing
    default argument in the loop would do.
    """
    seen: dict[bytes, str] = {}
    identifiers: set[str] = set()
    for frame in frames():
        picture = frame.draw()
        assert picture.shape == (HEIGHT, WIDTH, 3), frame.clip_id
        assert frame.clip_id not in identifiers, f"two frames called {frame.clip_id}"
        identifiers.add(frame.clip_id)
        key = picture.tobytes()
        assert key not in seen, f"{frame.clip_id} draws the same picture as {seen.get(key)}"
        seen[key] = frame.clip_id


def test_the_set_holds_both_arms_and_the_hard_negatives():
    kinds = {}
    for frame in frames():
        kinds.setdefault(frame.kind, 0)
        kinds[frame.kind] += 1
    assert kinds["text"] >= 30, "the precision arm has to be big enough to have an interval"
    assert kinds["ui"] >= 8
    assert kinds["grating"] >= 30
    assert kinds["mixed"] >= 4
    identifiers = {frame.clip_id for frame in frames()}
    assert any("table-" in name for name in identifiers), (
        "a monospaced table is the most regular thing a page of text can be and it has to "
        "be in here"
    )
    assert any("under-count-" in name for name in identifiers), (
        "a grating with too few pairs is the count gate's own negative"
    )


def test_a_text_page_really_has_high_contrast_edges_in_it():
    """If the text were low contrast this suite would prove nothing: the rule would never
    have looked at it. Seen to fail by drawing the text in the ground colour."""
    page = text_page(26, 1.55, 1, TEAL, (243, 232, 211))
    ground = np.array(TEAL)
    inked = float((np.abs(page.astype(int) - ground).sum(axis=2) > 60).mean())
    assert 0.01 < inked < 0.40, f"{inked} of the page is ink, which is not a page of text"
