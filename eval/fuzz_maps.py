"""Fuzz the flash map parser and the sidecar loader, and keep what it finds.

Three readers open a flash map, and all three have to fail closed: the app's
`verifyFlashMap` in TypeScript, flashmap's `verify_map` in Python and the pipeline's
`load_map`. Fail closed here has a precise meaning, and it is not "returns an error":

    either the map is refused and the picture stays hidden,
    or the map is accepted and every span it flags is hidden.

An exception counts as neither. Nor does a map that is accepted and then produces a schedule
that leaves one of its own segments showing.

    python3 eval/fuzz_maps.py --write-corpus     regenerate eval/fuzz_corpus
    python3 eval/fuzz_maps.py --write-fixtures   regenerate the two app test fixtures
    python3 eval/fuzz_maps.py                    run the corpus and write results/fuzz.json

The corpus is committed so a finding cannot quietly stop being tested, and
eval/fuzz_maps_test.py replays every case on every CI run.

About the key. Signing is unavoidable: the signature is checked before the segments are, so
an unsigned fuzz case only ever proves that the signature check works. The key is derived
from a fixed phrase at run time rather than stored, so there is no private key anywhere in
the repository and the corpus stays readable JSON. It is a test key with no other use.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "eval" / "fuzz_corpus"
APP_FIXTURES = REPO / "app" / "test" / "calmframes" / "fixtures"
RESULT = REPO / "results" / "fuzz.json"

SOURCE_SHA256 = "a" * 64
CREATED_UTC = "2026-09-01T00:00:00Z"
NOW_MS = 1_756_684_800_000  # 2025-09-01T00:00:00Z, well inside the default 90 day window


def fuzz_key() -> Ed25519PrivateKey:
    """A signing key derived from a phrase, so nothing secret is ever written down."""
    seed = hashlib.sha256(b"calm frames fuzz corpus, not a secret").digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


def canonical_bytes(document: dict[str, Any]) -> bytes:
    """The bytes a signature covers. Must match flashmap.sidecar.canonical_bytes exactly."""
    payload = {key: value for key, value in document.items() if key != "signature"}
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sign(document: dict[str, Any]) -> dict[str, Any]:
    private = fuzz_key()
    public = private.public_key()
    from cryptography.hazmat.primitives import serialization

    raw = public.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    payload = canonical_bytes(document)
    signed = dict(document)
    signed["signature"] = {
        "algorithm": "ed25519",
        "key_id": hashlib.sha256(raw).hexdigest()[:16],
        "public_key": base64.b64encode(raw).decode("ascii"),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "value": base64.b64encode(private.sign(payload)).decode("ascii"),
    }
    return signed


def public_key_base64() -> str:
    from cryptography.hazmat.primitives import serialization

    return base64.b64encode(
        fuzz_key()
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
    ).decode("ascii")


def base_map(segments: list[dict] | Any = None) -> dict[str, Any]:
    """A map that verifies, to be spoiled one field at a time."""
    if segments is None:
        segments = [{"start_ms": 10_000, "end_ms": 12_000, "reason": "general"}]
    return {
        "version": 1,
        "created_utc": CREATED_UTC,
        "source": {
            "path": "media/example.mp4",
            "sha256": SOURCE_SHA256,
            "duration_ms": 600_000,
            "coded_width": 1920,
            "coded_height": 1080,
        },
        "profile": {
            "name": "wcag",
            "area_windows": [{"name": "wcag-10deg", "width_px": 640}],
        },
        "picture": {"width": 1920, "height": 1080, "source": "detected"},
        "summary": {"hidden_ms": 2_000, "violation_count": 1},
        "segments": segments,
    }


# (name, what it is, how the document is spoiled). A case that returns a string is raw text
# and is never signed, because text that is not JSON cannot carry a signature.
CASES: list[tuple[str, str, Any]] = [
    # -------------------------------------------------------------- malformed JSON
    ("not_json_at_all", "plain text where a map should be", lambda: "this is not a map"),
    ("empty_file", "an empty file", lambda: ""),
    ("whitespace_only", "nothing but spaces and newlines", lambda: "   \n\t  \n"),
    ("truncated_object", "JSON cut off in the middle", lambda: '{"version": 1, "seg'),
    ("json_array", "a JSON array rather than an object", lambda: "[1, 2, 3]"),
    ("json_number", "a bare number", lambda: "42"),
    ("json_null", "a bare null", lambda: "null"),
    ("json_true", "a bare true", lambda: "true"),
    ("duplicate_keys", "the same key twice, which the canonical reader refuses",
     lambda: '{"version": 1, "version": 2}'),
    ("nan_literal", "NaN, which JSON does not have", lambda: '{"version": NaN}'),
    ("infinity_literal", "Infinity, which JSON does not have",
     lambda: '{"version": Infinity}'),
    ("trailing_comma", "a trailing comma", lambda: '{"version": 1,}'),
    ("single_quotes", "single quoted strings", lambda: "{'version': 1}"),
    ("bom_prefixed", "a byte order mark in front of the object",
     lambda: "﻿" + json.dumps(sign(base_map()))),
    ("deeply_nested", "two hundred levels of nesting",
     lambda: "[" * 200 + "1" + "]" * 200),
    ("huge_string_key", "a key a hundred thousand characters long",
     lambda: json.dumps({"x" * 100_000: 1, "version": 1})),
    ("control_characters", "a raw control character inside a string",
     lambda: '{"version": 1, "created_utc": "2026-01-01T00:00:00\x01Z"}'),
    ("lone_surrogate", "an unpaired surrogate escape",
     lambda: '{"version": 1, "created_utc": "\\ud800"}'),

    # ---------------------------------------------------------------- wrong versions
    ("version_zero", "version 0", lambda: sign(base_map() | {"version": 0})),
    ("version_two", "a version newer than this build reads",
     lambda: sign(base_map() | {"version": 2})),
    ("version_string", "the version as a string", lambda: sign(base_map() | {"version": "1"})),
    ("version_missing", "no version at all",
     lambda: sign({k: v for k, v in base_map().items() if k != "version"})),
    ("version_float", "version 1.5", lambda: sign(base_map() | {"version": 1.5})),
    ("version_huge", "a version larger than a double can hold exactly",
     lambda: sign(base_map() | {"version": 10**30})),

    # ------------------------------------------------------------------ bad segments
    ("segment_negative_start", "a segment that starts before the film does",
     lambda: sign(base_map([{"start_ms": -5_000, "end_ms": 1_000, "reason": "general"}]))),
    ("segment_reversed", "a segment that ends before it starts",
     lambda: sign(base_map([{"start_ms": 9_000, "end_ms": 1_000, "reason": "general"}]))),
    ("segment_zero_length", "a segment of no length at all",
     lambda: sign(base_map([{"start_ms": 9_000, "end_ms": 9_000, "reason": "general"}]))),
    ("segment_huge_interval", "a segment a thousand years long",
     lambda: sign(base_map([{"start_ms": 0, "end_ms": 31_536_000_000_000, "reason": "red"}]))),
    ("segment_start_beyond_duration", "a segment that starts after the film ends",
     lambda: sign(base_map([{"start_ms": 10**12, "end_ms": 10**12 + 1_000, "reason": "red"}]))),
    ("segment_times_as_strings", "times written as strings",
     lambda: sign(base_map([{"start_ms": "10000", "end_ms": "12000", "reason": "general"}]))),
    ("segment_times_null", "times that are null",
     lambda: sign(base_map([{"start_ms": None, "end_ms": None, "reason": "general"}]))),
    ("segment_not_an_object", "a segment that is a number",
     lambda: sign(base_map([12_345]))),
    ("segments_not_a_list", "segments given as an object",
     lambda: sign(base_map({"start_ms": 1, "end_ms": 2}))),
    ("segments_missing", "no segment list at all",
     lambda: sign({k: v for k, v in base_map().items() if k != "segments"})),
    ("segments_empty", "an empty segment list, which is a clean title",
     lambda: sign(base_map([]))),
    ("segments_overlapping", "two segments that overlap",
     lambda: sign(base_map([
         {"start_ms": 10_000, "end_ms": 20_000, "reason": "general"},
         {"start_ms": 15_000, "end_ms": 25_000, "reason": "red"},
     ]))),
    ("segments_identical", "the same segment twice",
     lambda: sign(base_map([
         {"start_ms": 10_000, "end_ms": 12_000, "reason": "general"},
         {"start_ms": 10_000, "end_ms": 12_000, "reason": "general"},
     ]))),
    ("segments_out_of_order", "segments listed back to front",
     lambda: sign(base_map([
         {"start_ms": 50_000, "end_ms": 52_000, "reason": "red"},
         {"start_ms": 10_000, "end_ms": 12_000, "reason": "general"},
     ]))),
    ("segments_contained", "one segment entirely inside another",
     lambda: sign(base_map([
         {"start_ms": 10_000, "end_ms": 40_000, "reason": "general"},
         {"start_ms": 20_000, "end_ms": 21_000, "reason": "red"},
     ]))),
    ("segment_unknown_reason", "a reason this build has never seen",
     lambda: sign(base_map([{"start_ms": 10_000, "end_ms": 12_000, "reason": "chromatic-x"}]))),
    ("segment_reason_missing", "no reason at all",
     lambda: sign(base_map([{"start_ms": 10_000, "end_ms": 12_000}]))),
    ("segment_reason_number", "a reason that is a number",
     lambda: sign(base_map([{"start_ms": 10_000, "end_ms": 12_000, "reason": 7}]))),
    ("segments_two_thousand", "two thousand segments, far more than any real title",
     lambda: sign(base_map([
         {"start_ms": i * 1_000, "end_ms": i * 1_000 + 100, "reason": "general"}
         for i in range(2_000)
     ]))),
    ("segment_times_not_finite", "times written as 1e400, which reads back as infinity",
     lambda: '{"version": 1, "segments": [{"start_ms": 1e400, "end_ms": 2e400}]}'),

    # ----------------------------------------------------------------- source block
    ("source_missing", "no source block",
     lambda: sign({k: v for k, v in base_map().items() if k != "source"})),
    ("source_not_an_object", "a source block that is a string",
     lambda: sign(base_map() | {"source": "media/example.mp4"})),
    ("source_sha_missing", "a source block with no hash",
     lambda: sign(base_map() | {"source": {"path": "media/example.mp4"}})),
    ("source_sha_wrong", "a hash for a different file",
     lambda: sign(base_map() | {"source": {"path": "p", "sha256": "b" * 64}})),
    ("source_sha_uppercase", "the right hash in capitals",
     lambda: sign(base_map() | {
         "source": {"path": "p", "sha256": SOURCE_SHA256.upper(), "duration_ms": 1},
     })),
    ("source_sha_short", "a hash of the wrong length",
     lambda: sign(base_map() | {"source": {"path": "p", "sha256": "abc"}})),

    # ------------------------------------------------------------------ timestamps
    ("created_missing", "no created_utc",
     lambda: sign({k: v for k, v in base_map().items() if k != "created_utc"})),
    ("created_local_time", "a local time rather than UTC",
     lambda: sign(base_map() | {"created_utc": "2026-09-01T00:00:00+02:00"})),
    ("created_date_only", "a date with no time",
     lambda: sign(base_map() | {"created_utc": "2026-09-01"})),
    ("created_far_future", "a map made in the year 9999",
     lambda: sign(base_map() | {"created_utc": "9999-01-01T00:00:00Z"})),
    ("created_far_past", "a map made in 1970",
     lambda: sign(base_map() | {"created_utc": "1970-01-01T00:00:00Z"})),
    ("created_nonsense_month", "month 13",
     lambda: sign(base_map() | {"created_utc": "2026-13-01T00:00:00Z"})),

    # ------------------------------------------------------------------- signatures
    ("unsigned", "no signature block at all", lambda: base_map()),
    ("signature_empty_object", "an empty signature block",
     lambda: base_map() | {"signature": {}}),
    ("signature_wrong_algorithm", "a signature that claims another algorithm",
     lambda: sign(base_map()) | {"signature": dict(sign(base_map())["signature"],
                                                  algorithm="rsa")}),
    ("signature_not_base64", "a signature value that is not base64",
     lambda: sign(base_map()) | {"signature": dict(sign(base_map())["signature"],
                                                  value="!!!not base64!!!")}),
    ("signature_truncated", "a signature with its last character removed",
     lambda: sign(base_map()) | {"signature": dict(
         sign(base_map())["signature"],
         value=sign(base_map())["signature"]["value"][:-4] + "AAA=")}),
    ("signature_over_a_different_body", "a real signature over a different map",
     lambda: dict(sign(base_map([{"start_ms": 1, "end_ms": 2, "reason": "general"}])),
                  segments=[{"start_ms": 500_000, "end_ms": 500_100, "reason": "general"}])),
    ("signature_is_a_string", "a signature block that is a string",
     lambda: base_map() | {"signature": "trust me"}),
    ("signature_public_key_swapped", "signed by us, but claiming another key",
     lambda: sign(base_map()) | {"signature": dict(sign(base_map())["signature"],
                                                  public_key="A" * 44)}),

    # ---------------------------------------------------------------- profile block
    ("profile_missing", "no profile block",
     lambda: sign({k: v for k, v in base_map().items() if k != "profile"})),
    ("profile_windows_missing", "a profile with no area windows",
     lambda: sign(base_map() | {"profile": {"name": "wcag"}})),
    ("profile_window_width_string", "a window width written as a string",
     lambda: sign(base_map() | {"profile": {
         "name": "wcag", "area_windows": [{"name": "w", "width_px": "640"}]}})),
    ("picture_width_zero", "a picture zero pixels wide",
     lambda: sign(base_map() | {"picture": {"width": 0, "height": 1080}})),
    ("picture_missing", "no picture block",
     lambda: sign({k: v for k, v in base_map().items() if k != "picture"})),
]


def render(value: Any) -> str:
    """Readable JSON, unless readable would mean a megabyte in the repository."""
    if isinstance(value, str):
        return value
    pretty = json.dumps(value, indent=2, sort_keys=True)
    if len(pretty) <= 64_000:
        return pretty
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def write_corpus() -> int:
    CORPUS.mkdir(parents=True, exist_ok=True)
    kept = set()
    index = []
    for name, description, make in CASES:
        text = render(make())
        suffix = ".json" if text.strip().startswith(("{", "[")) else ".txt"
        path = CORPUS / f"{name}{suffix}"
        path.write_text(text, encoding="utf-8")
        kept.add(path.name)
        index.append({"name": name, "file": path.name, "description": description})
    (CORPUS / "index.json").write_text(
        json.dumps(
            {
                "statement": (
                    "Every case a flash map reader has to survive. Written by "
                    "eval/fuzz_maps.py and replayed by eval/fuzz_maps_test.py on every CI "
                    "run. Fail closed means the map is refused, or it is accepted and "
                    "everything it flags is hidden."
                ),
                "public_key_base64": public_key_base64(),
                "source_sha256": SOURCE_SHA256,
                "now_ms": NOW_MS,
                "cases": index,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    kept.add("index.json")
    for stale in CORPUS.iterdir():
        if stale.name not in kept:
            stale.unlink()
    print(f"{len(index)} case(s) written to {CORPUS}")
    return 0


def write_app_fixtures() -> int:
    """Two signed maps the app's jest suite needs and cannot make for itself.

    Both close a hole the mutation gate found: nothing in the suite had a validly signed map
    with a segment that makes no sense, or one with a reason this build has never seen, so
    two guards in flashMap.ts had never been seen to fail.
    """
    APP_FIXTURES.mkdir(parents=True, exist_ok=True)
    written = []
    for name, segments in (
        (
            "signed_reversed_segment.flashmap.json",
            [{"start_ms": 9_000, "end_ms": 1_000, "reason": "general"}],
        ),
        (
            "signed_unknown_reason.flashmap.json",
            [{"start_ms": 10_000, "end_ms": 12_000, "reason": "chromatic-x"}],
        ),
    ):
        path = APP_FIXTURES / name
        path.write_text(
            json.dumps(sign(base_map(segments)), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path.name)
    (APP_FIXTURES / "fuzz_key.json").write_text(
        json.dumps(
            {
                "note": (
                    "The public half of the key eval/fuzz_maps.py derives from a fixed "
                    "phrase. It signs test maps and nothing else. There is no private key "
                    "in this repository."
                ),
                "public_key_base64": public_key_base64(),
                "source_sha256": SOURCE_SHA256,
                "created_utc": CREATED_UTC,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {', '.join(written)} and fuzz_key.json into {APP_FIXTURES}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-corpus", action="store_true")
    parser.add_argument("--write-fixtures", action="store_true")
    args = parser.parse_args(argv)
    if args.write_corpus:
        return write_corpus()
    if args.write_fixtures:
        return write_app_fixtures()
    print("nothing to do. Pass --write-corpus or --write-fixtures, or run pytest on")
    print("eval/fuzz_maps_test.py, which replays the corpus and writes results/fuzz.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
