"""The signed index of published maps.

Every test here that guards something has been broken on purpose and seen red.
The failure each one printed is quoted in its own docstring, because a new test
that has only ever been green proves nothing about the branch it claims to
cover.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from pipeline import registry
from pipeline.registry import RegistryError

PUBLIC_KEY_NAME = "test_key.pub.pem"


def map_body(
    sha256: str,
    *,
    profile: str = "wcag",
    created_utc: str = "2026-09-17T22:00:00Z",
    segments: list[tuple[int, int, str]] | None = None,
) -> dict:
    """A map in the shape docs/SIDECAR_SPEC.md describes, with the keys a reader needs."""
    spans = segments if segments is not None else []
    hidden = sum(end - start for start, end, _ in spans)
    return {
        "schema": "https://calm-frames.github.io/schemas/flashmap-map-v1.json",
        "version": 1,
        "generator": {"name": "flashmap", "version": "1.0.0"},
        "created_utc": created_utc,
        "source": {
            "path": f"{sha256[:8]}.mkv",
            "sha256": sha256,
            "size_bytes": 5797,
            "coded_width": 64,
            "coded_height": 48,
            "frame_count": 30,
            "timestamp_source": "container-pts",
        },
        "picture": {"measured_on": "picture", "left": 0, "top": 0, "width": 64, "height": 48},
        "color": {"matrix": "bt709", "range": "limited"},
        "profile": {"name": profile, "title": "for the tests", "area_windows": []},
        "segments": [
            {
                "start_ms": start,
                "end_ms": end,
                "flash_first_ms": start,
                "flash_last_ms": end,
                "reason": reason,
                "area_fraction": 1.0,
                "area_window": "wcag-10deg",
                "triggered_by": ["wcag-10deg"],
                "breaks_baseline": True,
                "max_flashes_in_window": 11,
            }
            for start, end, reason in spans
        ],
        "summary": {
            "pass": not spans,
            "segment_count": len(spans),
            "hidden_ms": hidden,
            "general_segment_count": sum(1 for _, _, r in spans if r == "general"),
            "red_segment_count": sum(1 for _, _, r in spans if r == "red"),
            "area_measured_on": "picture",
        },
    }


def write_signed_map(path: Path, body: dict, private_key_path: Path) -> Path:
    private = registry.load_private_key(private_key_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(registry.sign_document(body, private), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


SHA_A = "a" * 64
SHA_B = "b" * 64


@pytest.fixture
def maps_dir(tmp_path: Path, keypair: tuple[Path, Path]) -> Path:
    """Two checked maps for two files, published the way the pipeline lays them out."""
    private_path, _ = keypair
    root = tmp_path / "published"
    write_signed_map(
        root / "titles" / SHA_A / "maps" / "wcag.json",
        map_body(SHA_A, segments=[(1000, 2000, "general"), (1500, 2500, "red")]),
        private_path,
    )
    write_signed_map(
        root / "titles" / SHA_B / "maps" / "wcag.json",
        map_body(SHA_B, created_utc="2026-09-18T09:30:00Z"),
        private_path,
    )
    return root


def build_and_sign(maps_dir: Path, keypair: tuple[Path, Path], **kwargs) -> dict:
    private_path, public_path = keypair
    document = registry.build_registry(maps_dir, public_key_path=public_path, **kwargs)
    return registry.sign_registry(document, registry.load_private_key(private_path))


def test_the_index_it_builds_verifies_against_the_key_that_signed_it(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    signed = build_and_sign(maps_dir, keypair)
    assert registry.verify_registry(signed, public_key_path=keypair[1]) == []
    assert set(signed["files"]) == {SHA_A, SHA_B}
    assert signed["files"][SHA_A]["maps"]["wcag"]["path"] == (
        f"titles/{SHA_A}/maps/wcag.json"
    )


def test_the_entry_carries_the_signature_of_the_map_it_points_at(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """The binding an index-and-maps attacker has to break.

    Seen to fail: with the entry's ``signature`` set to the key id instead of
    the map's signature value, this said::

        AssertionError: assert 'sha256:249150c6d69878a9a385f0036cb3bc26538f4da3
        a1ff485121fcbc6f267c47f7' == 'XDF+O2iTv/v0zwC8mbB11T8lpTzvek3oVeylYKp+V
        BSFWEL+9pS0agqwqYFMQb4VOsfMbgu0BhkUgi0dTgT5Bw=='
    """
    signed = build_and_sign(maps_dir, keypair)
    entry = signed["files"][SHA_A]["maps"]["wcag"]
    on_disk = json.loads((maps_dir / entry["path"]).read_text())
    assert entry["signature"] == on_disk["signature"]["value"]
    assert entry["key_id"] == on_disk["signature"]["key_id"]


def test_the_counts_in_an_entry_come_from_the_map_it_verified(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """Overlapping segments are counted once, the way the map's own summary does.

    Seen to fail: with the overlap branch of ``merged_hidden_ms`` taken out, the
    two spans were added up whole and this said::

        assert 2000 == 1500
    """
    signed = build_and_sign(maps_dir, keypair)
    entry = signed["files"][SHA_A]["maps"]["wcag"]
    assert entry["segment_count"] == 2
    # 1000 to 2000 and 1500 to 2500 is one span of 1500 ms, not two of 1000.
    assert entry["hidden_ms"] == 1500


def test_the_same_maps_build_the_same_bytes(
    maps_dir: Path, tmp_path: Path, keypair: tuple[Path, Path]
) -> None:
    """Reproducible: another directory, another set of mtimes, the same file.

    Seen to fail: with ``_relative`` handing back the absolute path instead of
    the one relative to the maps directory, this said::

        assert b'{\\n  "creat...sion": 1\\n}\\n' == b'{\\n  "creat...sion": 1\\n}\\n'
        At index 479 diff: b'p' != b's'
    """
    first = registry.registry_bytes(build_and_sign(maps_dir, keypair))

    elsewhere = tmp_path / "somewhere-else" / "published"
    shutil.copytree(maps_dir, elsewhere)
    for path in elsewhere.rglob("*.json"):
        os.utime(path, (1_000_000, 1_000_000))
    second = registry.registry_bytes(build_and_sign(elsewhere, keypair))

    assert first == second


def test_the_index_date_is_the_newest_map_not_the_clock(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """Taken from the maps, so two builds of one directory agree.

    Seen to fail: with the newest comparison turned around to the oldest, this
    said::

        AssertionError: assert '2026-09-17T22:00:00Z' == '2026-09-18T09:30:00Z'
    """
    signed = build_and_sign(maps_dir, keypair)
    assert signed["created_utc"] == "2026-09-18T09:30:00Z"


def test_a_given_date_is_used_and_an_empty_directory_needs_one(
    tmp_path: Path, keypair: tuple[Path, Path]
) -> None:
    empty = tmp_path / "nothing"
    empty.mkdir()
    with pytest.raises(RegistryError, match="no maps"):
        registry.build_registry(empty, public_key_path=keypair[1])
    document = registry.build_registry(
        empty, public_key_path=keypair[1], created_utc="2026-01-02T03:04:05Z"
    )
    assert document == {
        "schema": registry.REGISTRY_SCHEMA,
        "version": 1,
        "generator": dict(registry.GENERATOR),
        "created_utc": "2026-01-02T03:04:05Z",
        "files": {},
    }


def test_a_map_changed_after_signing_is_never_indexed(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """A map whose body no longer matches its signature stops the build.

    Seen to fail: with the ``public.verify`` call in ``_check_map_signature``
    removed, this said::

        Failed: DID NOT RAISE RegistryError
    """
    path = maps_dir / "titles" / SHA_A / "maps" / "wcag.json"
    document = json.loads(path.read_text())
    document["segments"] = []
    document["summary"]["pass"] = True
    document["summary"]["segment_count"] = 0
    # An attacker who edits a map recomputes the digest beside it. Leaving the
    # old one would let the cheap check catch this and the signature check
    # never run, which is not what this test is for.
    document["signature"]["payload_sha256"] = hashlib.sha256(
        registry.canonical_bytes(document)
    ).hexdigest()
    path.write_text(json.dumps(document, indent=2, sort_keys=True))

    with pytest.raises(RegistryError, match="does not match the map body"):
        registry.build_registry(maps_dir, public_key_path=keypair[1])


def test_a_map_signed_by_another_key_is_never_indexed(
    maps_dir: Path, tmp_path: Path, keypair: tuple[Path, Path]
) -> None:
    """Trust comes from the key we hold, not from the key inside the map.

    Seen to fail: with the ``carried != held`` refusal removed, the stranger's
    map reached the signature check and was refused for the wrong reason::

        AssertionError: Regex pattern did not match.
         Expected regex: 'does not hold'
         Actual message: '.../maps/wcag.json signature does not match the map
         body, so it cannot be indexed'
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    other = tmp_path / "other_key.pem"
    other.write_bytes(
        ed25519.Ed25519PrivateKey.generate().private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    write_signed_map(
        maps_dir / "titles" / SHA_B / "maps" / "wcag.json", map_body(SHA_B), other
    )

    with pytest.raises(RegistryError, match="does not hold"):
        registry.build_registry(maps_dir, public_key_path=keypair[1])


def test_an_unsigned_map_is_never_indexed(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """An index entry is a claim that a checked map exists.

    Seen to fail: with the ``isinstance(signature, dict)`` refusal replaced by
    an empty signature block, the map was refused for the wrong reason::

        AssertionError: Regex pattern did not match.
         Expected regex: 'carries no signature'
         Actual message: '.../maps/wcag.json is signed with None, not ed25519'
    """
    path = maps_dir / "titles" / SHA_B / "maps" / "wcag.json"
    document = json.loads(path.read_text())
    document.pop("signature")
    path.write_text(json.dumps(document, indent=2, sort_keys=True))

    with pytest.raises(RegistryError, match="carries no signature"):
        registry.build_registry(maps_dir, public_key_path=keypair[1])


def test_two_maps_for_one_file_and_profile_stop_the_build(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """An index cannot choose between them, so it refuses to.

    Seen to fail: with the duplicate check removed, the second map quietly won
    and this said::

        Failed: DID NOT RAISE RegistryError
    """
    write_signed_map(
        maps_dir / "titles" / SHA_A / "maps" / "wcag-copy.json",
        map_body(SHA_A, segments=[(10, 20, "general")]),
        keypair[0],
    )
    with pytest.raises(RegistryError, match="two maps claim file"):
        registry.build_registry(maps_dir, public_key_path=keypair[1])


def test_one_file_can_have_a_map_per_profile(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    write_signed_map(
        maps_dir / "titles" / SHA_A / "maps" / "broadcast.json",
        map_body(SHA_A, profile="broadcast", segments=[(10, 20, "red")]),
        keypair[0],
    )
    signed = build_and_sign(maps_dir, keypair)
    assert sorted(signed["files"][SHA_A]["maps"]) == ["broadcast", "wcag"]


def test_the_index_does_not_index_itself(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """Rebuilding in place is an ordinary thing to do, twice.

    Seen to fail: with the ``path.name != REGISTRY_NAME`` filter removed, the
    second build tried to read the index as a map and this said::

        pipeline.registry.RegistryError: .../published/registry.json could not
        be read as a map: map has no segment list (looked for segments,
        flashes, intervals, hits): .../published/registry.json
    """
    registry.write_registry(build_and_sign(maps_dir, keypair), maps_dir / "registry.json")
    again = build_and_sign(maps_dir, keypair)
    assert set(again["files"]) == {SHA_A, SHA_B}


def test_an_index_changed_after_signing_is_refused(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """The producer side of the reader's fail closed rule.

    Seen to fail: with the ``public.verify`` call in ``verify_registry``
    removed, this said::

        AssertionError: assert 'signature does not match the index body' in []
    """
    signed = build_and_sign(maps_dir, keypair)
    signed["files"][SHA_A]["maps"]["wcag"]["path"] = "titles/somewhere-else/wcag.json"
    signed["signature"]["payload_sha256"] = hashlib.sha256(
        registry.canonical_bytes(signed)
    ).hexdigest()
    problems = registry.verify_registry(signed, public_key_path=keypair[1])
    assert "signature does not match the index body" in problems


def test_an_index_signed_by_another_key_is_refused(
    maps_dir: Path, tmp_path: Path, keypair: tuple[Path, Path]
) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    stranger = ed25519.Ed25519PrivateKey.generate()
    document = registry.build_registry(maps_dir, public_key_path=keypair[1])
    signed = registry.sign_document(document, stranger)
    problems = registry.verify_registry(signed, public_key_path=keypair[1])
    assert "index was signed by a key this build does not hold" in problems

    stranger_pub = tmp_path / "stranger.pub.pem"
    stranger_pub.write_bytes(
        stranger.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    # It is a perfectly good index. It is the wrong signer, and that is the
    # whole difference between a revoked key and a broken signature.
    assert registry.verify_registry(signed, public_key_path=stranger_pub) == []


def test_an_entry_path_that_leaves_the_index_is_refused(
    maps_dir: Path, keypair: tuple[Path, Path]
) -> None:
    """A path is resolved against the index's URL, so it has to stay under it.

    Seen to fail: with ``is_inside_path`` returning True for everything, this
    said::

        AssertionError: https://elsewhere.example/map.json
        assert not True
         +  where True = is_inside_path('https://elsewhere.example/map.json')
    """
    for bad in (
        "https://elsewhere.example/map.json",
        "/etc/passwd",
        "../../outside/map.json",
        "maps\\wcag.json",
        "",
    ):
        assert not registry.is_inside_path(bad), bad
    for good in ("maps/wcag.json", f"titles/{SHA_A}/maps/wcag.json", "wcag.json"):
        assert registry.is_inside_path(good), good

    signed = build_and_sign(maps_dir, keypair)
    signed["files"][SHA_A]["maps"]["wcag"]["path"] = "https://elsewhere.example/map.json"
    problems = registry.verify_registry(signed, public_key_path=keypair[1])
    assert any("leaves the index" in problem for problem in problems)


def test_a_fractional_timestamp_is_written_back_at_seconds_precision(
    tmp_path: Path, keypair: tuple[Path, Path]
) -> None:
    """A map may carry a fraction. Every date the index writes is seconds.

    The spec says seconds precision, and the app parses exactly that shape, so a
    fraction that reached an entry would be a map the player could not date.

    Seen to fail: with ``format_created_utc`` returning ``stamp.isoformat()``,
    this said::

        pipeline.registry.RegistryError: .../published/a.json created_utc is
        not an RFC 3339 UTC timestamp like 2026-09-17T22:00:00Z:
        '2026-09-18T09:30:01.500000+00:00'
    """
    root = tmp_path / "published"
    write_signed_map(
        root / "a.json",
        map_body(SHA_A, created_utc="2026-09-18T09:30:01.500000Z"),
        keypair[0],
    )
    write_signed_map(
        root / "b.json", map_body(SHA_B, created_utc="2026-09-18T09:30:00Z"), keypair[0]
    )
    document = registry.build_registry(root, public_key_path=keypair[1])
    assert document["created_utc"] == "2026-09-18T09:30:01Z"
    assert document["files"][SHA_A]["maps"]["wcag"]["created_utc"] == (
        "2026-09-18T09:30:01Z"
    )


def test_a_map_with_no_usable_hash_or_profile_stops_the_build(
    tmp_path: Path, keypair: tuple[Path, Path]
) -> None:
    """There is nothing to key an entry on, so there is no entry to write.

    Seen to fail: with the ``SHA256_HEX`` check removed, a map with a short hash
    was filed under it and this said::

        Failed: DID NOT RAISE RegistryError
    """
    root = tmp_path / "published"
    body = map_body(SHA_A)
    body["source"]["sha256"] = "abc123"
    write_signed_map(root / "short.json", body, keypair[0])
    with pytest.raises(RegistryError, match="no usable source.sha256"):
        registry.build_registry(root, public_key_path=keypair[1])

    missing_profile = map_body(SHA_B)
    missing_profile["profile"] = {"title": "no name here"}
    root_two = tmp_path / "published-two"
    write_signed_map(root_two / "noprofile.json", missing_profile, keypair[0])
    with pytest.raises(RegistryError, match="no usable profile name"):
        registry.build_registry(root_two, public_key_path=keypair[1])


def test_the_command_line_builds_and_then_checks(
    maps_dir: Path, tmp_path: Path, keypair: tuple[Path, Path], capsys
) -> None:
    """An index that does not check out has to leave with a failing exit code.

    Seen to fail: with the ``--check`` branch returning 0 instead of 1 for an
    index it refused, this said::

        AssertionError: assert 0 == 1
    """
    private_path, public_path = keypair
    out = tmp_path / "out" / "registry.json"
    code = registry.main(
        [
            str(maps_dir),
            "--out",
            str(out),
            "--key",
            str(private_path),
            "--pub",
            str(public_path),
        ]
    )
    assert code == 0
    assert "2 map(s) for 2 file(s)" in capsys.readouterr().out
    assert registry.main(["--check", str(out), "--pub", str(public_path)]) == 0

    out.write_text(out.read_text().replace('"hidden_ms": 1500', '"hidden_ms": 0'))
    assert registry.main(["--check", str(out), "--pub", str(public_path)]) == 1
    assert "signature does not match" in capsys.readouterr().out


def test_the_fixture_the_app_test_reads_is_the_one_this_builder_makes() -> None:
    """The committed fixture is checked, not taken on trust.

    app/test/calmframes/fixtures/registry is built by
    pipeline/tests/make_registry_fixture.py and read by
    app/test/calmframes/mapRegistry.test.ts. If it ever stopped verifying, the
    app test would be proving something about a file nothing else agrees with.

    Seen to fail: with one character of the fixture's ``payload_sha256``
    changed, this said::

        AssertionError: assert ['signature payload_sha256 does not match the
        index body'] == []
    """
    root = Path(__file__).resolve().parent.parent.parent
    fixture = root / "app" / "test" / "calmframes" / "fixtures" / "registry"
    document = registry.load_registry(fixture / registry.REGISTRY_NAME)
    assert registry.verify_registry(document, public_key_path=fixture / "key.pub.pem") == []
    rebuilt = registry.build_registry(fixture, public_key_path=fixture / "key.pub.pem")
    assert rebuilt["files"] == document["files"]
