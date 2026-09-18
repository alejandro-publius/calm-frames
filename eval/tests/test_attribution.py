"""Attribution: every clip credited, every condition carried, both files in step.

The ledger rows read here are the real ones in media/LICENSES.csv, because the point is that
the real credits are right. Nothing in this file writes to NOTICE, to credits.ts or to the
ledger. Where a rule needs a case the pool does not have, the row is FABRICATED FOR TEST ONLY
and says so in its own fields.

What this holds attribution to:

- NOTICE and app/src/calmframes/credits.ts are both current with the ledger, which is what
  stops the credits on the television and the credits in the repository saying different
  things;
- every clip we hold has a name, a licence and a credit line;
- the conditions that are not the licence itself are attached by rule, not by memory: share
  alike, the Blender logo exclusion, the Tears of Steel credit scroll, the DVIDS
  non-endorsement notice, the NASA credit line, and the one author who asks to be told.

To see them fail on purpose: see the note on each test. All were verified on Sep 17, 2026.
"""

from __future__ import annotations

import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

import attribution  # noqa: E402

FABRICATED_FOR_TEST_ONLY = True


def test_the_notice_and_the_credits_screen_are_current():
    """Break it: edit a credit line in the ledger and do not re-run the generator."""
    notice = attribution.build_notice(attribution.NOTICE.read_text())
    assert attribution.NOTICE.read_text() == notice, (
        "NOTICE has drifted from media/LICENSES.csv. Run `python eval/attribution.py`."
    )
    assert attribution.CREDITS_TS.read_text() == attribution.build_credits_ts(), (
        "app/src/calmframes/credits.ts has drifted from media/LICENSES.csv. "
        "Run `python eval/attribution.py`."
    )


def test_every_clip_we_hold_has_a_name_a_licence_and_a_credit():
    """Break it: blank a credit_line in the ledger and this names the row."""
    for entry in attribution.entries():
        assert entry["title"].strip(), entry
        assert entry["license"].strip(), entry
        assert entry["credit"].strip(), entry
        assert entry["source"].startswith("http"), entry


def test_the_tears_of_steel_credit_scroll_condition_is_carried():
    """Break it: remove the tears_of_steel branch from obligations() and this goes red."""
    tears = [e for e in attribution.entries() if e["title"] == "Tears of Steel"]
    assert tears, "Tears of Steel is not in the ledger"
    assert any("credit scroll" in condition for condition in tears[0]["obligations"])


def test_the_blender_logo_exclusion_is_carried_on_every_blender_title():
    """Break it: remove the Blender branch and this goes red on all three."""
    blender = [e for e in attribution.entries() if e["collection"].startswith("Blender")]
    assert len(blender) >= 3, blender
    for entry in blender:
        assert any("logos and trademarks" in c for c in entry["obligations"]), entry["title"]


def test_the_dvids_non_endorsement_notice_is_in_the_credit_and_the_conditions():
    """Break it: remove the DVIDS branch and the condition half goes red."""
    dvids = [e for e in attribution.entries() if e["collection"] == "DVIDS"]
    assert dvids, "no DVIDS clip in the ledger"
    for entry in dvids:
        assert "does not imply or constitute" in entry["credit"], entry["title"]
        assert any("non-endorsement" in c for c in entry["obligations"]), entry["title"]


def test_nasa_is_named_without_its_insignia():
    """Break it: remove the NASA branch and this goes red."""
    nasa = [e for e in attribution.entries() if "NASA" in e["credit"]]
    assert nasa, "no NASA clip in the ledger"
    for entry in nasa:
        assert any("insignia" in c for c in entry["obligations"]), entry["title"]


def test_share_alike_is_carried_on_every_share_alike_licence():
    """Break it: remove the by-sa branch and this goes red on every CC BY-SA clip."""
    share_alike = [e for e in attribution.entries() if "BY-SA" in e["license"].upper()]
    assert share_alike, "no share alike clip in the ledger"
    for entry in share_alike:
        assert any(c.startswith("Share alike") for c in entry["obligations"]), entry["title"]


def test_a_clip_with_no_name_is_refused_rather_than_named_after_its_file():
    """FABRICATED FOR TEST ONLY. Break it: fall back to the file stem and this goes red."""
    row = {
        "file": "HAZARD_invented_clip_with_no_page.mp4",
        "source_page_url": "https://example.invalid/fabricated-for-test-only",
        "license": "CC BY 4.0",
        "credit_line": "Invented, for test only",
        "notes": "source: Invented source. FABRICATED FOR TEST ONLY.",
    }
    assert attribution.title_of(row) is None


def test_a_commons_row_is_named_by_its_own_file_page():
    """FABRICATED FOR TEST ONLY, in the same shape as the real Commons rows."""
    row = {
        "file": "HAZARD_invented.webm",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:Invented_test_clip.webm",
        "license": "CC BY-SA 4.0",
        "credit_line": "Invented author, CC BY-SA 4.0, via Wikimedia Commons",
        "notes": "source: Wikimedia Commons. FABRICATED FOR TEST ONLY.",
    }
    assert attribution.title_of(row) == "Invented test clip"
    assert attribution.obligations(row) == [attribution.SHARE_ALIKE]


def test_the_title_we_keep_out_of_what_we_publish_is_not_credited_as_used():
    """Hell's Angels (1930) is in the considered and not used list, never in the credits."""
    for entry in attribution.entries():
        assert "hell's angels" not in entry["title"].lower()
        assert "hell's angels" not in entry["credit"].lower()
    skipped = attribution.skipped_rows(attribution.rows())
    assert any("hell" in (row.get("notes") or "").lower() for row in skipped), (
        "the reason that title is kept out is no longer written down anywhere"
    )


def test_no_downloaded_row_says_verify_in_its_notes():
    """A trap in the pool builder, kept loud.

    eval/labeling/make_pool.py drops any title whose notes contain "verify", on the repo rule
    that anything marked for checking is checked or dropped. The match is on the bare word in
    free text, so a note that happens to use it for some other reason takes that title out of
    the labelling pool and says only "license line not confirmed". This nearly happened while
    rewriting the notes: the new text described the pipeline's verify step.

    Break it: put the word back into a downloaded row's notes, and this goes red naming it.
    """
    offenders = [
        row["file"]
        for row in attribution.used_rows(attribution.rows())
        if "verify" in (row.get("notes") or "").lower()
    ]
    assert not offenders, (
        "these rows would be dropped from the labelling pool by the word 'verify' in their "
        f"notes: {offenders}. Say it another way."
    )
