"""A stand-in for the flashmap CLI, for tests only.

It speaks the same two commands the pipeline uses:

    analyze VIDEO --profile P --out MAP.json [--diag D --distance-ft F --key K]
    verify MAP.json VIDEO --pub PUB

What it fakes: which spans are flagged. That comes from a plan file named by
``FAKE_FLASHMAP_PLAN``.

What it does for real: hashing the video, writing a map in the shape the
sidecar spec describes, signing it with Ed25519 and checking that signature
again on verify. So a tampered map, a swapped video or a wrong key fails here
the same way the real analyzer would fail.

Plan file::

    {
      "log": "/path/to/invocations.jsonl",
      "rules": [
        {"match": "clip.mp4", "segments": {"wcag": [[1000, 1500, "general"]]}}
      ],
      "fail": {"match": "broken.mp4", "message": "boom"}
    }

The first rule whose ``match`` appears in the video path wins. A rule may use
``segments_all`` instead of ``segments`` to answer the same way for every
profile. Anything with no rule comes back clean.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
from pathlib import Path

MAP_VERSION = 1
PLAN_ENV = "FAKE_FLASHMAP_PLAN"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _plan() -> dict:
    path = os.environ.get(PLAN_ENV)
    if not path or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text())


def _log(event: dict) -> None:
    plan = _plan()
    log_path = plan.get("log")
    if not log_path:
        return
    with open(log_path, "a") as handle:
        handle.write(json.dumps({**event, "at": time.time()}) + "\n")


def _segments_for(video: str, profile: str) -> list[dict]:
    plan = _plan()
    raw: list = []
    for rule in plan.get("rules", []):
        if rule.get("match") and rule["match"] in video:
            if "segments_all" in rule:
                raw = rule["segments_all"]
            else:
                raw = (rule.get("segments") or {}).get(profile, [])
            break
    return [
        {
            "start_ms": item[0],
            "end_ms": item[1],
            "flash_first_ms": item[0],
            "flash_last_ms": item[1],
            "reason": item[2] if len(item) > 2 else "general",
            "area_fraction": 1.0,
            "area_window": "wcag-10deg",
            "triggered_by": ["wcag-10deg"],
            "breaks_baseline": True,
            "max_flashes_in_window": 6,
        }
        for item in raw
    ]


def _canonical(payload: dict) -> bytes:
    """The exact bytes docs/SIDECAR_SPEC.md says are signed."""
    body = {key: value for key, value in payload.items() if key != "signature"}
    return json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sign(payload: dict, key_path: str) -> dict:
    from cryptography.hazmat.primitives import serialization

    private = serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
    signature = private.sign(_canonical(payload))
    return {"alg": "ed25519", "value": base64.b64encode(signature).decode("ascii")}


def _check_signature(payload: dict, pub_path: str) -> tuple[bool, str]:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization

    signature = payload.get("signature")
    if not signature:
        return False, "the map carries no signature"
    public = serialization.load_pem_public_key(Path(pub_path).read_bytes())
    try:
        public.verify(base64.b64decode(signature["value"]), _canonical(payload))
    except InvalidSignature:
        return False, "the map signature does not match its contents"
    return True, "signature ok"


def cmd_analyze(args: argparse.Namespace) -> int:
    plan = _plan()
    failure = plan.get("fail")
    if failure and failure.get("match", "") in args.video:
        print(failure.get("message", "analysis failed"), file=sys.stderr)
        _log({"cmd": "analyze", "video": args.video, "profile": args.profile, "failed": True})
        return 2

    video = Path(args.video)
    if not video.exists():
        print(f"no such file: {video}", file=sys.stderr)
        return 2

    segments = _segments_for(str(video), args.profile)
    payload = {
        "schema": "https://calm-frames.github.io/schemas/flashmap-map-v1.json",
        "version": MAP_VERSION,
        "generator": {"name": "fake-flashmap", "version": "0.0.0"},
        "created_utc": "2026-09-17T00:00:00Z",
        "source": {
            "path": video.name,
            "sha256": _sha256(video),
            "size_bytes": video.stat().st_size,
        },
        "picture": {"measured_on": "picture"},
        "color": {"matrix": "bt709", "range": "limited"},
        "profile": {
            "name": _plan().get("force_profile") or args.profile,
            "room": (
                {"tv_diagonal_in": args.diag, "seat_distance_in": args.distance_ft}
                if args.diag or args.distance_ft
                else None
            ),
        },
        "segments": segments,
        "summary": {
            "pass": not segments,
            "segment_count": len(segments),
            "general_segment_count": sum(
                1 for s in segments if s["reason"] == "general"
            ),
            "red_segment_count": sum(1 for s in segments if s["reason"] == "red"),
            "area_measured_on": "picture",
        },
    }
    if args.key:
        payload["signature"] = _sign(payload, args.key)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    _log(
        {
            "cmd": "analyze",
            "video": str(video),
            "profile": args.profile,
            "out": str(out),
            "segments": len(payload["segments"]),
        }
    )
    # The same exit code convention as the real CLI: 0 below the thresholds,
    # 1 over them, 2 an error. A test can force a wrong one to check that the
    # adapter notices the map and the exit code disagreeing.
    forced = plan.get("force_exit")
    if forced is not None:
        return int(forced)
    return 1 if segments else 0


def cmd_verify(args: argparse.Namespace) -> int:
    _log({"cmd": "verify", "map": args.map, "video": args.video})
    map_path = Path(args.map)
    if not map_path.exists():
        print(f"no such map: {map_path}", file=sys.stderr)
        return 4
    try:
        payload = json.loads(map_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"map is not valid JSON: {exc}", file=sys.stderr)
        return 5

    ok, detail = _check_signature(payload, args.pub)
    if not ok:
        print(detail, file=sys.stderr)
        return 6

    video = Path(args.video)
    if not video.exists():
        print(f"no such file: {video}", file=sys.stderr)
        return 4
    actual = _sha256(video)
    bound = (payload.get("source") or {}).get("sha256") or payload.get("source_sha256")
    if bound != actual:
        print(
            f"the map is bound to {bound} but this file hashes to {actual}",
            file=sys.stderr,
        )
        return 7
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fake-flashmap")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze")
    analyze.add_argument("video")
    analyze.add_argument("--profile", required=True)
    analyze.add_argument("--out", required=True)
    analyze.add_argument("--diag", type=float)
    analyze.add_argument("--distance-ft", dest="distance_ft", type=float)
    analyze.add_argument("--key")
    analyze.set_defaults(func=cmd_analyze)

    verify = sub.add_parser("verify")
    verify.add_argument("map")
    verify.add_argument("video")
    verify.add_argument("--pub", required=True)
    verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
