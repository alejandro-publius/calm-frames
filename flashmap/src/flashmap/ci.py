"""The check a pull request runs.

`python -m flashmap.ci` takes a list of files, keeps the ones that are images or video,
measures each against a profile, and exits non zero if any of them breaks the thresholds. The
GitHub Action in action.yml is a thin wrapper around this.

Nothing here opens a file in a player, and nothing writes a copy of a failing file anywhere.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .analyze import analyze_file
from .decode import ColorPolicy, UnsupportedInput
from .profiles import PROFILES, get_profile

__all__ = ["MEDIA_SUFFIXES", "select_media", "main"]

# Formats that can hold more than one frame, so formats where a flash is possible. A still
# image cannot flash, but .png also carries APNG and .webp also carries animated WebP, so both
# are measured rather than assumed safe.
MEDIA_SUFFIXES = frozenset(
    {
        ".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".mpg", ".mpeg",
        ".ts", ".m2ts", ".ogv", ".flv", ".wmv",
        ".gif", ".png", ".apng", ".webp", ".avif",
    }
)


def select_media(paths: list[str] | list[Path]) -> list[Path]:
    """Keep the entries that exist and look like media, in a stable order."""
    kept: list[Path] = []
    for entry in paths:
        path = Path(str(entry).strip())
        if not str(path):
            continue
        if path.suffix.lower() not in MEDIA_SUFFIXES:
            continue
        if not path.is_file():
            continue
        kept.append(path)
    return sorted(set(kept))


def _read_list(source: str | None) -> list[str]:
    if source in (None, "-"):
        return sys.stdin.read().splitlines()
    return Path(str(source)).read_text(encoding="utf-8").splitlines()


def _summary(lines: list[str]) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="flashmap.ci",
        description="Fail a pull request that adds an image or video breaking WCAG 2.3.1.",
    )
    parser.add_argument("paths", nargs="*", help="files to check")
    parser.add_argument(
        "--changed-from",
        default=None,
        help="read the file list from this file, or from standard input with -",
    )
    parser.add_argument("--profile", default="wcag", choices=sorted(PROFILES))
    parser.add_argument("--peak-nits", type=float, default=None)
    parser.add_argument("--analysis-width", type=int, default=192)
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="treat a file flashmap cannot measure as a failure",
    )
    args = parser.parse_args(argv)

    candidates = list(args.paths)
    if args.changed_from is not None:
        candidates += _read_list(args.changed_from)
    files = select_media(candidates)

    if not files:
        print("flashmap: no image or video files to check")
        _summary(["### flashmap", "", "No image or video files in this change."])
        return 0

    profile = get_profile(args.profile, peak_nits=args.peak_nits)
    failed: list[tuple[Path, list[str]]] = []
    unmeasurable: list[tuple[Path, str]] = []
    passed: list[Path] = []

    for path in files:
        try:
            result = analyze_file(
                path,
                profile=profile,
                policy=ColorPolicy(),
                analysis_width=args.analysis_width,
            )
        except UnsupportedInput as exc:
            unmeasurable.append((path, str(exc)))
            print(f"SKIP {path}: {exc}")
            continue
        if result.passes:
            passed.append(path)
            print(f"PASS {path}")
        else:
            detail = [
                f"{segment.start_ms:.0f} to {segment.end_ms:.0f} ms, {segment.reason} flash, "
                f"area {segment.area_fraction:.2f} of the {segment.area_window} window "
                "measured on the picture"
                for segment in result.segments
            ]
            failed.append((path, detail))
            print(f"FAIL {path}")
            for line in detail:
                print(f"  {line}")

    lines = ["### flashmap: WCAG 2.2 Success Criterion 2.3.1", ""]
    if failed:
        lines.append(f"{len(failed)} file(s) break the {profile.name} thresholds.")
        lines.append("")
        for path, detail in failed:
            lines.append(f"**{path}**")
            for entry in detail:
                lines.append(f"- {entry}")
            lines.append("")
    else:
        lines.append(f"All {len(passed)} file(s) are below the {profile.name} thresholds.")
    if unmeasurable:
        lines.append("")
        lines.append("Could not be measured:")
        for path, reason in unmeasurable:
            lines.append(f"- {path}: {reason}")
    lines.append("")
    lines.append(
        "Do not open a failing file in a player. flashmap reduces exposure to flashing above "
        "published limits in the videos it measures. It is not a medical device."
    )
    _summary(lines)

    if failed:
        print(
            f"\nflashmap: {len(failed)} file(s) break WCAG 2.2 Success Criterion 2.3.1.",
            file=sys.stderr,
        )
        return 1
    if unmeasurable and args.fail_on_error:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
