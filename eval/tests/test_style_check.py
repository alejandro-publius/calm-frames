"""The style guard refuses a dash and the three words, and passes the repository.

eval/style_check.py is the first thing that holds documents, Python and
TypeScript outside the app's own copy to CLAUDE.md's style rule. Four jest
tests hold the UI copy; this holds everything else.

Seen to fail on Oct 11, 2026: an em dash and the word "genuinely" appended to
docs/PLAN.md made `python3 eval/style_check.py` exit 1 naming both lines, and
removing them made it exit 0 again. Breaking the guard itself: make
`violations` return [] and the first three tests go red.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "style_check.py"
spec = importlib.util.spec_from_file_location("style_check", SCRIPT)
style_check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(style_check)


def test_an_em_dash_and_an_en_dash_are_both_refused():
    found = style_check.violations("one " + chr(0x2014) + " two\nthree " + chr(0x2013) + " four\nfive\n", "x.md")
    assert found == ["x.md:1: em or en dash", "x.md:2: em or en dash"]


def test_the_three_words_are_refused_whatever_their_case():
    text = "It is Genuinely fine.\nhonestly, no.\nA STRAIGHTFORWARD path.\nstraightforwardly is a different word.\n"
    found = style_check.violations(text, "y.py")
    assert found == [
        "y.py:1: the word 'Genuinely'",
        "y.py:2: the word 'honestly'",
        "y.py:3: the word 'STRAIGHTFORWARD'",
    ]


def test_the_line_that_states_the_rule_is_allowed():
    rule = '- Don\'t use the words "genuinely", "honestly" or "straightforward". Plain, warm writing.\n'
    assert style_check.violations(rule, "CLAUDE.md") == []


def test_the_scope_leaves_other_peoples_files_and_the_fixtures_alone():
    assert style_check.in_scope("docs/STATUS.md")
    assert style_check.in_scope("eval/plots.py")
    assert style_check.in_scope("app/src/calmframes/copy.ts")
    assert style_check.in_scope("NOTICE")
    assert not style_check.in_scope("app/test/calmframes/copy.test.ts")
    assert not style_check.in_scope("app/src/w3cmedia/shakaplayer/ShakaPlayer.ts")
    assert not style_check.in_scope("app/assets/fonts/LICENSE-Inter")
    assert not style_check.in_scope("app/assets/image/tv/harbor.png")
    assert not style_check.in_scope("eval/style_check.py")
    assert not style_check.in_scope("eval/tests/test_style_check.py")


def test_the_repository_passes_its_own_rule():
    """Break it: put an em dash in any tracked document."""
    assert style_check.scan(style_check.tracked_files()) == []
