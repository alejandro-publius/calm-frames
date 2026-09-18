"""The map sidecar and its signature.

The contract is docs/SIDECAR_SPEC.md. These tests are what stops it drifting.
"""

from __future__ import annotations

import base64
import json

import pytest

import clipgen
from flashmap import (
    SIDECAR_VERSION,
    WCAG,
    RoomSetting,
    analyze_file,
    build_map,
    load_map,
    sign_map,
    verify_map,
    write_map,
)
from flashmap.sidecar import VerificationError, canonical_bytes
from flashmap.signing import generate_keypair, load_private_key

W, H = 64, 48


@pytest.fixture
def strobe(hazard_clip):
    frames = clipgen.alternating(
        30, clipgen.solid(W, H, (0, 0, 0)), clipgen.solid(W, H, (255, 255, 255))
    )
    return hazard_clip("map.mkv", frames, fps=20)


@pytest.fixture
def keypair(tmp_path):
    private_path, public_path = generate_keypair(tmp_path / "team_key")
    return private_path, public_path


def test_the_map_carries_every_section_the_spec_promises(strobe):
    document = build_map(analyze_file(strobe, WCAG))
    assert document["version"] == SIDECAR_VERSION
    for section in ("schema", "generator", "created_utc", "source", "picture", "color",
                    "profile", "segments", "summary"):
        assert section in document, section


def test_source_fields(strobe):
    document = build_map(analyze_file(strobe, WCAG))
    source = document["source"]
    assert len(source["sha256"]) == 64
    assert source["path"] == strobe.name
    assert "/" not in source["path"], "a map must not leak a build machine's paths"
    assert source["timestamp_source"] == "container-pts"
    assert source["frame_count"] > 0


def test_segment_fields(strobe):
    document = build_map(analyze_file(strobe, WCAG))
    assert document["segments"], "this clip is meant to fail"
    for segment in document["segments"]:
        assert set(segment) == {
            "start_ms", "end_ms", "flash_first_ms", "flash_last_ms", "reason",
            "area_fraction", "area_window", "triggered_by", "breaks_baseline",
            "max_flashes_in_window",
        }
        assert segment["reason"] in {"general", "red"}
        assert isinstance(segment["start_ms"], int)
        assert isinstance(segment["end_ms"], int)
        assert segment["end_ms"] > segment["start_ms"]
        assert 0.0 <= segment["area_fraction"] <= 1.0
        # The hidden interval always contains the flashing and starts at or before it.
        assert segment["start_ms"] <= segment["flash_first_ms"]
        assert segment["end_ms"] >= segment["flash_last_ms"]


def test_the_map_says_the_area_was_measured_on_the_picture(strobe):
    document = build_map(analyze_file(strobe, WCAG))
    assert document["picture"]["measured_on"] == "picture"
    assert document["summary"]["area_measured_on"] == "picture"


def test_the_map_records_the_profile_numbers_that_were_applied(strobe):
    profile = build_map(analyze_file(strobe, WCAG))["profile"]
    assert profile["flash_limit_per_second"] == 3
    assert profile["window_ms"] == 1000
    assert profile["area_fraction_limit"] == 0.25
    assert profile["general_flash"]["min_delta"] == 0.10
    assert profile["general_flash"]["dark_image_below"] == 0.80
    assert profile["red_flash"]["saturated_red_ratio"] == 0.8
    assert profile["red_flash"]["min_ucs_distance"] == 0.2


def test_canonical_bytes_leave_out_the_signature_and_are_stable(strobe):
    document = build_map(analyze_file(strobe, WCAG), created_utc="2026-01-01T00:00:00Z")
    before = canonical_bytes(document)
    document["signature"] = {"algorithm": "ed25519", "value": "anything"}
    assert canonical_bytes(document) == before
    assert b'"signature"' not in before


def test_canonical_bytes_do_not_depend_on_key_order(strobe):
    document = build_map(analyze_file(strobe, WCAG), created_utc="2026-01-01T00:00:00Z")
    shuffled = dict(reversed(list(document.items())))
    assert canonical_bytes(shuffled) == canonical_bytes(document)


def test_a_signed_map_verifies(strobe, keypair, tmp_path):
    private_path, public_path = keypair
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    path = write_map(document, tmp_path / "map.json")
    report = verify_map(load_map(path), video_path=strobe, public_key_path=public_path)
    assert report.ok, report.problems
    assert report.checked_signature
    assert report.source_hash_matches


def test_an_unsigned_map_is_refused_unless_you_ask_for_it(strobe):
    document = build_map(analyze_file(strobe, WCAG))
    assert not verify_map(document, video_path=strobe).ok
    assert verify_map(document, video_path=strobe, require_signature=False).ok


def test_verifying_with_no_public_key_is_not_a_pass(strobe, keypair):
    private_path, _ = keypair
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    report = verify_map(document, video_path=strobe)
    assert not report.ok
    assert any("no public key" in problem for problem in report.problems)


def test_changing_one_segment_breaks_the_signature(strobe, keypair):
    private_path, public_path = keypair
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    document["segments"][0]["end_ms"] -= 1
    report = verify_map(document, video_path=strobe, public_key_path=public_path)
    assert not report.ok
    assert any("signature" in problem for problem in report.problems)


def test_removing_every_segment_breaks_the_signature(strobe, keypair):
    """The attack that matters: quietly turning a failing map into a passing one."""
    private_path, public_path = keypair
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    document["segments"] = []
    document["summary"]["pass"] = True
    assert not verify_map(document, video_path=strobe, public_key_path=public_path).ok


def test_a_map_from_another_key_does_not_verify(strobe, keypair, tmp_path):
    private_path, _ = keypair
    _, other_public = generate_keypair(tmp_path / "other")
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    report = verify_map(document, video_path=strobe, public_key_path=other_public)
    assert not report.ok


def test_a_map_for_a_different_file_does_not_verify(strobe, keypair, calm_clip):
    private_path, public_path = keypair
    other = calm_clip("other.mkv", [clipgen.solid(W, H, (30, 30, 30))] * 6, fps=20)
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    report = verify_map(document, video_path=other, public_key_path=public_path)
    assert not report.ok
    assert report.source_hash_matches is False
    assert any("not made for this file" in problem for problem in report.problems)


def test_a_map_with_the_wrong_version_is_refused(strobe, keypair):
    private_path, public_path = keypair
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    document["version"] = 2
    report = verify_map(document, video_path=strobe, public_key_path=public_path)
    assert not report.ok
    assert any("version" in problem for problem in report.problems)


def test_unparseable_json_is_a_verification_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(VerificationError):
        load_map(bad)


def test_a_json_array_is_not_a_map(tmp_path):
    bad = tmp_path / "list.json"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(VerificationError):
        load_map(bad)


def test_the_signature_block_matches_the_documented_shape(strobe, keypair):
    private_path, _ = keypair
    document = sign_map(build_map(analyze_file(strobe, WCAG)), load_private_key(private_path))
    signature = document["signature"]
    assert set(signature) == {"algorithm", "key_id", "public_key", "payload_sha256", "value"}
    assert signature["algorithm"] == "ed25519"
    assert signature["key_id"].startswith("sha256:")
    assert len(base64.b64decode(signature["public_key"])) == 32
    assert len(base64.b64decode(signature["value"])) == 64


def test_a_room_map_records_the_room_and_a_plain_map_does_not(strobe):
    plain = build_map(analyze_file(strobe, WCAG))
    assert plain["profile"]["room"] is None
    with_room = build_map(analyze_file(strobe, WCAG, room=RoomSetting(55, 96)))
    assert with_room["profile"]["room"]["tv_diagonal_in"] == 55


def test_the_written_file_is_readable_json(strobe, tmp_path):
    document = build_map(analyze_file(strobe, WCAG))
    path = write_map(document, tmp_path / "m.json")
    assert json.loads(path.read_text(encoding="utf-8")) == document


# The segment list, which nothing used to check.
#
# Found by eval/fuzz_maps_test.py. A correctly signed map whose segments said a flash ended
# before it started, or were written as strings, or were not a list at all, passed `flashmap
# verify` cleanly. No player would have taken it: both the app's reader and the pipeline's
# loader refuse those maps. The tool a studio runs on its own work was the only one calling
# them fine, which is the wrong way round.


def _signed(segments, keypair):
    private_path, _ = keypair
    document = {
        "version": SIDECAR_VERSION,
        "created_utc": "2026-09-01T00:00:00Z",
        "source": {"path": "x.mp4", "sha256": "a" * 64, "duration_ms": 1000},
        "profile": {"name": "wcag"},
        "picture": {"width": 1920, "height": 1080},
        "summary": {"hidden_ms": 0},
        "segments": segments,
    }
    return sign_map(document, load_private_key(private_path))


def _problems(segments, keypair):
    _, public_path = keypair
    return verify_map(_signed(segments, keypair), public_key_path=public_path).problems


def test_a_sensible_segment_list_still_verifies(keypair):
    """The negative control. Without this, refusing everything would pass the tests below."""
    assert _problems([{"start_ms": 0.0, "end_ms": 500.0, "reason": "general"}], keypair) == []


@pytest.mark.parametrize(
    ("segments", "expected"),
    [
        ([{"start_ms": 900.0, "end_ms": 100.0}], "ends at 100"),
        ([{"start_ms": 900.0, "end_ms": 900.0}], "ends at 900"),
        ([{"start_ms": -5.0, "end_ms": 100.0}], "before the film does"),
        ([{"start_ms": "0", "end_ms": "500"}], "not both numbers"),
        ([{"start_ms": None, "end_ms": None}], "not both numbers"),
        ([{"start_ms": True, "end_ms": 500.0}], "not both numbers"),
        ([{"end_ms": 500.0}], "not both numbers"),
        ([12345], "not an object"),
        ("every frame", "not a list"),
        ({"start_ms": 0.0, "end_ms": 1.0}, "not a list"),
    ],
)
def test_a_segment_that_makes_no_sense_fails_the_map(segments, expected, keypair):
    problems = _problems(segments, keypair)
    assert problems, f"{segments!r} verified cleanly"
    assert any(expected in problem for problem in problems), problems


def test_a_map_full_of_bad_segments_reports_a_readable_number_of_them(keypair):
    problems = _problems([{"start_ms": 9.0, "end_ms": 1.0}] * 40, keypair)
    assert len(problems) == 9
    assert problems[-1] == "and 32 more segment problem(s)"
