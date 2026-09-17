"""Tests for the ingest and verify pipeline.

Nothing in here needs a working flashmap. Every test drives the pipeline
through the fake analyzer in ``fake_flashmap.py``, which talks the same
command line and signs its maps for real, so the adapter, the signature check
and the hash binding are all exercised.

Safety: the clips these tests generate are calm by construction. A slow moving
box on a slowly drifting background has no flash in it. No test generates
flashing content, and no test opens a file in a player.
"""
