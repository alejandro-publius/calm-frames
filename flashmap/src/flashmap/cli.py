"""The `python -m flashmap` command line.

Four subcommands, as in docs/BUILD_PROMPT.md 0.4:

    python -m flashmap keygen  --out team_key
    python -m flashmap analyze VIDEO --profile wcag --out MAP.json --diag 55 --distance-ft 8 \
        --key team_key.pem
    python -m flashmap verify  MAP.json VIDEO --pub team_key.pub.pem
    python -m flashmap check   VIDEO [VIDEO ...] --profile wcag

Exit codes: 0 means the content is below the thresholds or the map verified. 1 means it is not.
2 means flashmap could not tell, which callers must treat as a failure too.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analyze import AnalysisResult, analyze_file
from .decode import ColorPolicy, UnsupportedInput
from .picture import LetterboxSettings
from .profiles import PROFILES, get_profile
from .room import RoomSetting
from .sidecar import VerificationError, build_map, load_map, sign_map, verify_map, write_map
from .signing import generate_keypair, load_private_key

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_ERROR = 2

_DISCLAIMER = (
    "flashmap reduces exposure to flashing above published limits in the videos it measures. "
    "It is not a medical device."
)


def _room_from_args(args: argparse.Namespace) -> RoomSetting | None:
    distance_in = None
    if getattr(args, "distance_ft", None) is not None:
        distance_in = float(args.distance_ft) * 12.0
    if getattr(args, "distance_in", None) is not None:
        distance_in = float(args.distance_in)
    if args.diag is None and distance_in is None:
        return None
    if args.diag is None or distance_in is None:
        raise SystemExit(
            "the room rule needs both --diag (TV diagonal in inches) and a seat distance "
            "(--distance-ft or --distance-in)"
        )
    aspect_w, _, aspect_h = str(args.display_aspect).partition(":")
    return RoomSetting(
        tv_diagonal_in=float(args.diag),
        seat_distance_in=distance_in,
        display_aspect_w=float(aspect_w),
        display_aspect_h=float(aspect_h or 9),
    )


def _analyze(args: argparse.Namespace, path: Path) -> AnalysisResult:
    profile = get_profile(args.profile, peak_nits=getattr(args, "peak_nits", None))
    return analyze_file(
        path,
        profile=profile,
        room=_room_from_args(args),
        policy=ColorPolicy(hd_min_height=args.hd_min_height),
        analysis_width=args.analysis_width,
        letterbox=LetterboxSettings(),
        chunk_frames=args.chunk_frames,
        chunk_overlap=args.chunk_overlap,
    )


def _describe(result: AnalysisResult) -> str:
    picture = result.picture
    bars = []
    if picture.letterbox:
        bars.append("letterbox")
    if picture.pillarbox:
        bars.append("pillarbox")
    where = (
        f"area measured on the picture, {picture.width}x{picture.height} of "
        f"{picture.frame_width}x{picture.frame_height} analysis pixels"
    )
    if bars:
        where += f" after removing {' and '.join(bars)} bars"
    lines = [where]
    lines.append(
        "colour: "
        f"{result.source.color.matrix} ({result.source.color.matrix_source}), "
        f"{result.source.color.color_range} range ({result.source.color.range_source})"
    )
    lines.append(
        "timing: real container timestamps, "
        + ("variable frame rate" if result.variable_frame_rate else "constant frame rate")
        + f", {result.frame_count} frames"
    )
    for window in result.area_windows:
        lines.append(f"area window {window.name}: {window.width_px}x{window.height_px} px")
    if result.segments:
        lines.append(f"{len(result.segments)} segment(s) over the threshold:")
        for segment in result.segments:
            lines.append(
                f"  {segment.start_ms:.0f} to {segment.end_ms:.0f} ms  {segment.reason}  "
                f"area {segment.area_fraction:.3f} in {segment.area_window}  "
                f"flashes {segment.max_flashes_in_window}  "
                f"triggered by {', '.join(segment.triggered_by)}"
            )
    else:
        lines.append("no segment broke the thresholds")
    return "\n".join(lines)


def cmd_keygen(args: argparse.Namespace) -> int:
    private_path, public_path = generate_keypair(args.out)
    print(f"private key: {private_path}  (never commit this)")
    print(f"public key:  {public_path}")
    return EXIT_OK


def cmd_analyze(args: argparse.Namespace) -> int:
    path = Path(args.video)
    try:
        result = _analyze(args, path)
    except UnsupportedInput as exc:
        print(f"flashmap cannot measure {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR
    document = build_map(result)
    if args.key:
        document = sign_map(document, load_private_key(args.key))
    if args.out:
        write_map(document, args.out)
        print(f"map written to {args.out}")
    else:
        print(json.dumps(document, indent=2, sort_keys=True))
    if not args.quiet:
        print(_describe(result), file=sys.stderr)
        print(_DISCLAIMER, file=sys.stderr)
    return EXIT_OK if result.passes else EXIT_FAIL


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        document = load_map(args.map)
    except VerificationError as exc:
        print(f"FAIL {args.map}: {exc}", file=sys.stderr)
        return EXIT_ERROR
    report = verify_map(
        document,
        video_path=args.video,
        public_key_path=args.pub,
        require_signature=not args.allow_unsigned,
    )
    if report.ok:
        print(f"OK {args.map} verifies against {args.video}")
        return EXIT_OK
    for problem in report.problems:
        print(f"FAIL {args.map}: {problem}", file=sys.stderr)
    return EXIT_FAIL


def cmd_check(args: argparse.Namespace) -> int:
    worst = EXIT_OK
    for name in args.videos:
        path = Path(name)
        try:
            result = _analyze(args, path)
        except UnsupportedInput as exc:
            print(f"ERROR {path}: {exc}", file=sys.stderr)
            worst = max(worst, EXIT_ERROR)
            continue
        if result.passes:
            print(f"PASS {path}: below the {result.profile.name} thresholds")
        else:
            worst = max(worst, EXIT_FAIL)
            print(f"FAIL {path}: {len(result.segments)} segment(s) over the thresholds")
            for segment in result.segments:
                print(
                    f"  {segment.start_ms:.0f} to {segment.end_ms:.0f} ms  {segment.reason} "
                    f"flash, area {segment.area_fraction:.3f} of the {segment.area_window} "
                    "window, measured on the picture"
                )
        if args.json:
            Path(args.json).write_text(
                json.dumps(build_map(result), indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    if worst != EXIT_OK:
        print(
            "\nDo not open a failing file in a player. Analyse it, act on the map, delete it.",
            file=sys.stderr,
        )
    return worst


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile", default="wcag", choices=sorted(PROFILES), help="which rule set to measure against"
    )
    parser.add_argument("--peak-nits", type=float, default=None, help="broadcast profile peak white")
    parser.add_argument("--diag", type=float, default=None, help="TV diagonal in inches")
    parser.add_argument("--distance-ft", type=float, default=None, help="seat distance in feet")
    parser.add_argument("--distance-in", type=float, default=None, help="seat distance in inches")
    parser.add_argument("--display-aspect", default="16:9", help="display aspect, for example 16:9")
    parser.add_argument("--analysis-width", type=int, default=192, help="working width in pixels")
    parser.add_argument(
        "--hd-min-height",
        type=int,
        default=720,
        help="picture height at which an untagged stream is decoded as BT.709 instead of BT.601",
    )
    parser.add_argument("--chunk-frames", type=int, default=None, help="analyse in chunks this big")
    parser.add_argument(
        "--chunk-overlap", type=int, default=0, help="frames re-sent from the previous chunk"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flashmap",
        description=(
            "Measure video against the WCAG 2.2 general and red flash thresholds. "
            + _DISCLAIMER
        ),
    )
    parser.add_argument("--version", action="version", version=f"flashmap {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    keygen = subparsers.add_parser("keygen", help="make an Ed25519 signing keypair")
    keygen.add_argument("--out", required=True, help="path stem, gives <stem>.pem and <stem>.pub.pem")
    keygen.set_defaults(func=cmd_keygen)

    analyze = subparsers.add_parser("analyze", help="write a map sidecar for one file")
    analyze.add_argument("video")
    analyze.add_argument("--out", default=None, help="where to write the map, default stdout")
    analyze.add_argument("--key", default=None, help="Ed25519 private key to sign the map with")
    analyze.add_argument("--quiet", action="store_true", help="do not print the summary")
    _add_common(analyze)
    analyze.set_defaults(func=cmd_analyze)

    verify = subparsers.add_parser("verify", help="check a map against its file and a public key")
    verify.add_argument("map")
    verify.add_argument("video")
    verify.add_argument("--pub", default=None, help="Ed25519 public key you already hold")
    verify.add_argument(
        "--allow-unsigned", action="store_true", help="accept a map with no signature"
    )
    verify.set_defaults(func=cmd_verify)

    check = subparsers.add_parser("check", help="pass or fail one or more files")
    check.add_argument("videos", nargs="+")
    check.add_argument("--json", default=None, help="also write the map of the last file here")
    _add_common(check)
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except SystemExit:
        raise
    except (UnsupportedInput, ValueError) as exc:
        print(f"flashmap: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
