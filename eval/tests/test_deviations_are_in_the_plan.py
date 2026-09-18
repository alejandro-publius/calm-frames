"""Guard: every deviation the evaluation lane logged is also in the plan.

docs/EVAL_PLAN.md says its own section 12 is where changes to the plan live. The evaluation lane
wrote them in eval/DEVIATIONS.md while it worked, because it was asked to stay inside eval/ and
results/, and they were copied across on Sep 17, 2026. Two files saying the same thing drift
apart the moment nobody checks, and a deviation that is only in the lane's log is a change to
the plan that the plan does not admit to.

So: the dated rows of eval/DEVIATIONS.md and the dated rows of section 12 have to be the same
rows, in the same order.

To confirm the guard is live, add a row to one file and not the other, and watch this go red.
Verified Sep 17, 2026: it does.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEVIATIONS = REPO / "eval" / "DEVIATIONS.md"
PLAN = REPO / "docs" / "EVAL_PLAN.md"


def dated_rows(text: str) -> list[str]:
    """Every table row that starts with a date, stripped of trailing whitespace."""
    return [line.rstrip() for line in text.splitlines() if line.startswith("| 20")]


def section_12(text: str) -> str:
    start = text.index("## 12. Deviations")
    return text[start:]


def test_the_two_files_hold_the_same_deviations():
    lane_log = dated_rows(DEVIATIONS.read_text())
    plan = dated_rows(section_12(PLAN.read_text()))

    assert lane_log, "eval/DEVIATIONS.md has no dated rows"
    only_in_lane_log = [row for row in lane_log if row not in plan]
    only_in_plan = [row for row in plan if row not in lane_log]
    assert not only_in_lane_log, (
        "these deviations are in eval/DEVIATIONS.md but not in EVAL_PLAN section 12:\n  "
        + "\n  ".join(row[:120] for row in only_in_lane_log)
    )
    assert not only_in_plan, (
        "these deviations are in EVAL_PLAN section 12 but not in eval/DEVIATIONS.md:\n  "
        + "\n  ".join(row[:120] for row in only_in_plan)
    )
    assert lane_log == plan, "the two files hold the same rows in a different order"


def test_the_plan_no_longer_claims_it_has_no_deviations():
    """The plan shipped saying an empty section 12 was correct. It is not empty now."""
    text = section_12(PLAN.read_text())
    assert "Empty is the correct state today" not in text
