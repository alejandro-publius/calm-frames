"""Recall against the pooled candidates: what it is, and the one way it can lie.

Every window, detector and title in this file is FABRICATED FOR TEST ONLY. No clip is opened,
no file under results/ is read or written, and none of these numbers describes anything real.

The measurement this guards is the one the README's IRIS caveat was about. With no labels,
each detector is scored against the union of what all the candidate lists proposed. A
detector's own flags are always inside that union, so:

- its coverage is exactly its own windows over the union's windows, never more than 1;
- adding a candidate list can only lower it, or leave it alone. That is the whole reason a
  pool drawn from one detector cannot measure that detector's recall, and the reason the
  number published while EA IRIS was missing was optimistic by an amount nobody could name.

If `score` ever computed a detector against its own flags rather than against the union, every
detector would come out at 1.0 and the caveat would have been replaced by a number that means
nothing. That is the failure this file is here to catch.

To see them fail on purpose: in `score`, change `per_detector.get(detector, set()) & union` to
`per_detector.get(detector, set())` and drop the union terms from the denominator, and both
tests go red. Verified Sep 18, 2026.
"""

from __future__ import annotations

import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

sys.path.insert(0, str(EVAL_DIR / "realclips"))

from pool_recall import score  # noqa: E402

FABRICATED_FOR_TEST_ONLY = True

# Two invented titles. "one" is where the lists mostly agree, "two" is where they do not.
FABRICATED_WINDOWS = {
    "invented_one": {
        "flashmap": {0, 1, 2},
        "ffmpeg_photosensitivity": {1, 2},
        "naive_luma_diff": {2},
        "iris": {2, 7},
    },
    "invented_two": {
        "flashmap": {4},
        "ffmpeg_photosensitivity": {4, 5},
        "naive_luma_diff": set(),
        "iris": {9},
    },
}
FABRICATED_FILES = {
    "invented_one": "HAZARD_invented_one.mp4",
    "invented_two": "HAZARD_invented_two.webm",
}

THREE_LISTS = ("flashmap", "ffmpeg_photosensitivity", "naive_luma_diff")
FOUR_LISTS = (*THREE_LISTS, "iris")


def test_a_detector_is_scored_against_the_union_and_not_against_itself():
    """Break it: score a detector against its own flags, and every rate here becomes 1.0."""
    scored = score(FABRICATED_WINDOWS, FABRICATED_FILES, THREE_LISTS)

    # union over both titles: {0,1,2} and {4,5}, so five windows.
    assert scored["union_windows"] == 5
    assert scored["titles"] == 2

    table = scored["table"]
    assert table["flashmap"]["recall_against_the_union"]["numerator"] == 4
    assert table["flashmap"]["recall_against_the_union"]["denominator"] == 5
    assert table["flashmap"]["recall_against_the_union"]["value"] == 4 / 5
    assert table["naive_luma_diff"]["recall_against_the_union"]["value"] == 1 / 5
    for name in THREE_LISTS:
        value = table[name]["recall_against_the_union"]["value"]
        assert value <= 1.0, f"{name} covered more of the union than the union holds"

    # Windows nobody else proposed: window 0 is flashmap's alone, window 5 is ffmpeg's alone.
    assert table["flashmap"]["windows_only_this_list_proposed"] == 1
    assert table["ffmpeg_photosensitivity"]["windows_only_this_list_proposed"] == 1
    assert table["naive_luma_diff"]["windows_only_this_list_proposed"] == 0


def test_adding_a_candidate_list_can_only_lower_the_others():
    """The caveat, as arithmetic.

    Break it: as above. Scored against itself, a detector's number does not move when another
    list joins, and this goes red on the strict inequality.
    """
    before = score(FABRICATED_WINDOWS, FABRICATED_FILES, THREE_LISTS)["table"]
    after = score(FABRICATED_WINDOWS, FABRICATED_FILES, FOUR_LISTS)["table"]

    for name in THREE_LISTS:
        assert (
            after[name]["recall_against_the_union"]["value"]
            <= before[name]["recall_against_the_union"]["value"]
        ), f"{name} went up when a candidate list joined, which cannot happen"

    # iris proposes window 7 in one title and window 9 in the other, and nobody else does, so
    # the union grows from five windows to seven and flashmap's coverage has to fall.
    assert (
        after["flashmap"]["recall_against_the_union"]["denominator"] == 7
    ), "the union did not grow when a list with windows of its own joined"
    assert after["flashmap"]["recall_against_the_union"]["value"] == 4 / 7
    assert after["iris"]["windows_only_this_list_proposed"] == 2


def test_the_bootstrap_groups_by_title_and_not_by_window():
    """Windows inside one title are not independent, so the resample has to move whole titles.

    Break it: pass each window as its own group, and the group count here stops matching the
    number of titles.
    """
    scored = score(FABRICATED_WINDOWS, FABRICATED_FILES, FOUR_LISTS)
    for name in FOUR_LISTS:
        assert scored["table"][name]["bootstrap_over_titles"]["groups"] == 2
