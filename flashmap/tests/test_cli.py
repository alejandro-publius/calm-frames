"""The four subcommands, their exit codes and their output.

Exit codes are part of the contract: 0 below the thresholds or verified, 1 over the thresholds
or failed to verify, 2 could not tell. A caller that treats 2 as a pass has a hole in it.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

import clipgen
from flashmap.cli import EXIT_ERROR, EXIT_FAIL, EXIT_OK, main

W, H = 64, 48
CALM_FIXTURE = Path(__file__).parent / "fixtures" / "calm_sweep.mp4"


@pytest.fixture
def strobe(hazard_clip):
    frames = clipgen.alternating(
        30, clipgen.solid(W, H, (0, 0, 0)), clipgen.solid(W, H, (255, 255, 255))
    )
    return hazard_clip("cli.mkv", frames, fps=20)


# ---- keygen --------------------------------------------------------------------------------


def test_keygen_writes_both_keys_and_locks_the_private_one(tmp_path, capsys):
    stem = tmp_path / "team_key"
    assert main(["keygen", "--out", str(stem)]) == EXIT_OK
    private = tmp_path / "team_key.pem"
    public = tmp_path / "team_key.pub.pem"
    assert private.is_file() and public.is_file()
    assert stat.S_IMODE(os.stat(private).st_mode) == 0o600
    assert b"PRIVATE KEY" in private.read_bytes()
    assert b"PUBLIC KEY" in public.read_bytes()
    assert "never commit this" in capsys.readouterr().out


# ---- analyze -------------------------------------------------------------------------------


def test_analyze_writes_a_map_and_returns_one_for_a_failing_clip(strobe, tmp_path):
    out = tmp_path / "map.json"
    assert main(["analyze", str(strobe), "--out", str(out)]) == EXIT_FAIL
    document = json.loads(out.read_text(encoding="utf-8"))
    assert document["version"] == 1
    assert document["segments"]


def test_analyze_returns_zero_for_a_calm_clip(tmp_path):
    out = tmp_path / "calm.json"
    assert main(["analyze", str(CALM_FIXTURE), "--out", str(out)]) == EXIT_OK
    assert json.loads(out.read_text(encoding="utf-8"))["summary"]["pass"] is True


def test_analyze_says_where_it_measured_and_what_it_is_not(strobe, tmp_path, capsys):
    main(["analyze", str(strobe), "--out", str(tmp_path / "m.json")])
    stderr = capsys.readouterr().err
    assert "area measured on the picture" in stderr
    assert "real container timestamps" in stderr
    assert "not a medical device" in stderr


def test_analyze_can_sign_the_map(strobe, tmp_path):
    main(["keygen", "--out", str(tmp_path / "k")])
    out = tmp_path / "signed.json"
    main(["analyze", str(strobe), "--out", str(out), "--key", str(tmp_path / "k.pem")])
    assert "signature" in json.loads(out.read_text(encoding="utf-8"))


def test_analyze_refuses_half_a_room_setting(strobe, tmp_path):
    with pytest.raises(SystemExit, match="needs both"):
        main(["analyze", str(strobe), "--out", str(tmp_path / "m.json"), "--diag", "55"])


def test_analyze_accepts_a_room_in_feet(strobe, tmp_path):
    out = tmp_path / "room.json"
    main([
        "analyze", str(strobe), "--out", str(out),
        "--diag", "55", "--distance-ft", "8",
    ])
    room = json.loads(out.read_text(encoding="utf-8"))["profile"]["room"]
    assert room["seat_distance_in"] == 96.0


def test_analyze_reports_an_unreadable_file_as_could_not_tell(tmp_path, capsys):
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"nope")
    assert main(["analyze", str(broken), "--out", str(tmp_path / "m.json")]) == EXIT_ERROR
    assert "cannot measure" in capsys.readouterr().err


# ---- verify --------------------------------------------------------------------------------


def _signed_map(strobe, tmp_path):
    main(["keygen", "--out", str(tmp_path / "k")])
    out = tmp_path / "map.json"
    main(["analyze", str(strobe), "--out", str(out), "--key", str(tmp_path / "k.pem")])
    return out, tmp_path / "k.pub.pem"


def test_verify_accepts_a_good_map(strobe, tmp_path, capsys):
    map_path, public = _signed_map(strobe, tmp_path)
    assert main(["verify", str(map_path), str(strobe), "--pub", str(public)]) == EXIT_OK
    assert "OK" in capsys.readouterr().out


def test_verify_rejects_a_tampered_map(strobe, tmp_path):
    map_path, public = _signed_map(strobe, tmp_path)
    document = json.loads(map_path.read_text(encoding="utf-8"))
    document["segments"] = []
    map_path.write_text(json.dumps(document), encoding="utf-8")
    assert main(["verify", str(map_path), str(strobe), "--pub", str(public)]) == EXIT_FAIL


def test_verify_rejects_a_map_made_for_another_file(strobe, tmp_path, calm_clip):
    map_path, public = _signed_map(strobe, tmp_path)
    other = calm_clip("other.mkv", [clipgen.solid(W, H, (10, 10, 10))] * 5, fps=20)
    assert main(["verify", str(map_path), str(other), "--pub", str(public)]) == EXIT_FAIL


def test_verify_rejects_an_unsigned_map_unless_told_not_to(strobe, tmp_path):
    out = tmp_path / "unsigned.json"
    main(["analyze", str(strobe), "--out", str(out)])
    assert main(["verify", str(out), str(strobe)]) == EXIT_FAIL
    assert main(["verify", str(out), str(strobe), "--allow-unsigned"]) == EXIT_OK


def test_verify_reports_unreadable_json_as_could_not_tell(strobe, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert main(["verify", str(bad), str(strobe)]) == EXIT_ERROR


# ---- check ---------------------------------------------------------------------------------


def test_check_passes_a_calm_file(capsys):
    assert main(["check", str(CALM_FIXTURE)]) == EXIT_OK
    assert "PASS" in capsys.readouterr().out


def test_check_fails_a_strobe_and_says_where_the_area_was_measured(strobe, capsys):
    assert main(["check", str(strobe)]) == EXIT_FAIL
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "measured on the picture" in captured.out
    assert "Do not open a failing file in a player" in captured.err


def test_check_takes_several_files_and_fails_if_any_do(strobe):
    assert main(["check", str(CALM_FIXTURE), str(strobe)]) == EXIT_FAIL


def test_check_with_a_room_can_only_add_failures(strobe):
    plain = main(["check", str(strobe)])
    roomed = main(["check", str(strobe), "--diag", "55", "--distance-ft", "3"])
    assert roomed >= plain


def test_an_unknown_profile_is_rejected(strobe):
    with pytest.raises(SystemExit):
        main(["check", str(strobe), "--profile", "made-up"])


def test_chunked_and_whole_give_the_same_verdict_through_the_cli(strobe):
    assert main(["check", str(strobe)]) == main(
        ["check", str(strobe), "--chunk-frames", "7", "--chunk-overlap", "3"]
    )
