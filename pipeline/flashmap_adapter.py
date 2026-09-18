"""The one place that knows the flashmap CLI and the map file format.

Lane 1 owns ``flashmap/``. This pipeline never imports it. It talks to it
through two commands and one JSON file:

    python -m flashmap analyze VIDEO --profile wcag --out MAP.json \\
        [--diag 55 --distance-ft 8 --key team_key.pem]
    python -m flashmap verify MAP.json VIDEO --pub team_key.pub.pem

Set ``CALM_FRAMES_FLASHMAP_CMD`` to point at something else. Tests point it at
a fake analyzer, so the whole pipeline suite runs with no working flashmap.

Map format: docs/SIDECAR_SPEC.md, version 1. This reader follows it, including
the rules it sets for readers:

- fail closed. A map that is missing, unparseable, the wrong version or bound
  to a different file is not a map;
- hide ``[start_ms, end_ms]``, never ``[flash_first_ms, flash_last_ms]``;
- ignore unknown keys, because version 1 may grow new optional ones;
- a reader may hide more, never less.

It also accepts a few older spellings of the same fields, so a map written
before the spec landed still reads, and it fails loudly on anything else.

Three deliberate choices, all about failing safe:

- an unknown reason string is read as "red", which is the strictest handling
  (always an opaque cover, never dimmed);
- a map with no recognisable segment list is an error, not an empty list. A
  map we cannot read must never look like a clean bill of health;
- a map whose ``summary.pass`` disagrees with its own segment list is an
  error, not a coin toss.

Presets: the pipeline ships three, the analyzer has two profiles. The third,
extra-cautious, is the WCAG profile measured with a room window for a large
television at close seating. The spec says the room rule can only add hides,
never remove them, so extra-cautious is a superset of wcag by construction.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from . import PipelineError

COMMAND_ENV = "CALM_FRAMES_FLASHMAP_CMD"

PRESETS: tuple[str, ...] = ("wcag", "broadcast", "extra-cautious")

# Version 1 is the only map this reader understands. Anything else is refused
# rather than guessed at, which is what docs/SIDECAR_SPEC.md asks for.
SUPPORTED_MAP_VERSIONS = (1, "1")

# flashmap's exit codes, from flashmap/README.md and flashmap/src/flashmap/cli.py:
# 0 below the thresholds or verified, 1 over the thresholds or failed to
# verify, 2 an error. So a finished analysis of flashing content exits 1, and
# treating that as a crash would throw away every map that found something.
EXIT_NOTHING_FLAGGED = 0
EXIT_SOMETHING_FLAGGED = 1
EXIT_ERROR = 2
ANALYZE_OK_EXIT_CODES = (EXIT_NOTHING_FLAGGED, EXIT_SOMETHING_FLAGGED)


@dataclass(frozen=True)
class Preset:
    """How one pipeline preset is asked for on the analyzer's command line.

    The analyzer has two rule sets, wcag and broadcast. The third preset is
    the WCAG rules measured in a room window: a 75 inch television at 5 feet.
    That window is smaller than WCAG's fixed one, so a flashing area fills
    more of it and more spans are flagged. The room rule can only add hides,
    so extra-cautious always contains everything wcag would hide.
    """

    name: str
    profile: str
    diag_in: float | None = None
    distance_ft: float | None = None

    @property
    def is_room_preset(self) -> bool:
        return self.diag_in is not None or self.distance_ft is not None


PRESET_SPECS: dict[str, Preset] = {
    "wcag": Preset("wcag", "wcag"),
    "broadcast": Preset("broadcast", "broadcast"),
    "extra-cautious": Preset("extra-cautious", "wcag", diag_in=75.0, distance_ft=5.0),
}

RED = "red"
GENERAL = "general"

_RED_WORDS = {"red", "red_flash", "red-flash", "saturated_red", "saturatedred", "redflash"}
_GENERAL_WORDS = {
    "general",
    "general_flash",
    "general-flash",
    "luminance",
    "luminance_flash",
    "generalflash",
}

_SEGMENT_KEYS = ("segments", "flashes", "intervals", "hits")
# "source" is the version 1 spelling: an object with a sha256 inside it.
_SHA_KEYS = ("source_sha256", "sha256", "source_hash", "file_sha256", "source")
_START_KEYS = ("start_ms", "startMs", "start")
_END_KEYS = ("end_ms", "endMs", "end")
_REASON_KEYS = ("reason", "kind", "type", "rule")
_SIGNATURE_KEYS = ("signature", "sig", "ed25519", "seal")


class FlashmapUnavailable(PipelineError):
    """The analyzer could not be started at all."""


class FlashmapFailed(PipelineError):
    """The analyzer ran and reported a failure."""


class MapFormatError(PipelineError):
    """A map file could not be read the way the spec describes."""


def normalise_reason(value: Any) -> str:
    """Map a reason string onto "general" or "red", defaulting to red.

    Red is the safe default: a red segment is always covered opaque, so
    guessing red can only ever hide more, never less.
    """
    if value is None:
        return RED
    text = str(value).strip().lower().replace(" ", "_")
    if text in _GENERAL_WORDS:
        return GENERAL
    if text in _RED_WORDS:
        return RED
    return RED


def _first_key(data: dict, keys: Sequence[str]) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


@dataclass(frozen=True)
class MapSegment:
    start_ms: float
    end_ms: float
    reason: str = GENERAL

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms

    def to_dict(self) -> dict:
        return {"start_ms": self.start_ms, "end_ms": self.end_ms, "reason": self.reason}


@dataclass
class FlashMapDoc:
    version: Any
    source_sha256: str | None
    profile: str | None
    segments: list[MapSegment]
    path: Path | None = None
    raw: dict = field(default_factory=dict)
    # The pipeline preset this map was asked for. It can differ from
    # ``profile``: extra-cautious is the wcag profile with a room window.
    preset: str | None = None

    @property
    def violation_count(self) -> int:
        return len(self.segments)

    @property
    def is_clean(self) -> bool:
        return not self.segments

    @property
    def signature(self) -> Any:
        return _first_key(self.raw, _SIGNATURE_KEYS)

    @property
    def is_signed(self) -> bool:
        return bool(self.signature)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "source_sha256": self.source_sha256,
            "profile": self.profile,
            "segments": [s.to_dict() for s in self.segments],
            "path": str(self.path) if self.path else None,
            "signed": self.is_signed,
        }


def parse_map(data: dict, *, path: Path | None = None) -> FlashMapDoc:
    if not isinstance(data, dict):
        raise MapFormatError(f"map is not a JSON object: {path}")

    version = data.get("version")
    if version is not None and version not in SUPPORTED_MAP_VERSIONS:
        raise MapFormatError(
            f"map version {version!r} is not one this reader understands "
            f"({SUPPORTED_MAP_VERSIONS}): {path}"
        )

    raw_segments = None
    for key in _SEGMENT_KEYS:
        if isinstance(data.get(key), list):
            raw_segments = data[key]
            break
    if raw_segments is None:
        raise MapFormatError(
            f"map has no segment list (looked for {', '.join(_SEGMENT_KEYS)}): {path}"
        )

    segments: list[MapSegment] = []
    for index, item in enumerate(raw_segments):
        if not isinstance(item, dict):
            raise MapFormatError(f"segment {index} is not an object: {path}")
        start = _first_key(item, _START_KEYS)
        end = _first_key(item, _END_KEYS)
        if start is None or end is None:
            raise MapFormatError(f"segment {index} has no start or end: {path}")
        try:
            start_ms = float(start)
            end_ms = float(end)
        except (TypeError, ValueError) as exc:
            raise MapFormatError(f"segment {index} has a non numeric time: {path}") from exc
        if end_ms < start_ms:
            raise MapFormatError(f"segment {index} ends before it starts: {path}")
        segments.append(
            MapSegment(
                start_ms=start_ms,
                end_ms=end_ms,
                reason=normalise_reason(_first_key(item, _REASON_KEYS)),
            )
        )

    segments.sort(key=lambda s: (s.start_ms, s.end_ms))

    # A map that contradicts itself is unreadable, not clean.
    summary = data.get("summary")
    if isinstance(summary, dict) and "pass" in summary:
        if bool(summary["pass"]) != (not segments):
            raise MapFormatError(
                f"map summary says pass={summary['pass']!r} but carries "
                f"{len(segments)} segment(s): {path}"
            )

    sha = _first_key(data, _SHA_KEYS)
    if isinstance(sha, dict):
        sha = sha.get("sha256")

    profile = data.get("profile") or data.get("preset")
    if isinstance(profile, dict):
        profile = profile.get("name")

    return FlashMapDoc(
        version=version,
        source_sha256=str(sha).lower() if sha else None,
        profile=profile,
        segments=segments,
        path=path,
        raw=data,
    )


def load_map(path: str | Path) -> FlashMapDoc:
    path = Path(path)
    if not path.exists():
        raise MapFormatError(f"map file is missing: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise MapFormatError(f"map file is not valid JSON: {path}: {exc}") from exc
    return parse_map(data, path=path)


@dataclass
class CommandResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    cmd: list[str]


class FlashmapAdapter:
    """Runs the flashmap CLI. Nothing else in the pipeline shells out to it."""

    def __init__(
        self,
        command: Sequence[str] | None = None,
        *,
        env: dict[str, str] | None = None,
        timeout_s: float | None = 60 * 60 * 4,
    ) -> None:
        self.command = list(command) if command else self._default_command()
        self.env = env
        self.timeout_s = timeout_s

    @staticmethod
    def _default_command() -> list[str]:
        override = os.environ.get(COMMAND_ENV)
        if override:
            return shlex.split(override)
        return [sys.executable, "-m", "flashmap"]

    def describe(self) -> str:
        return " ".join(self.command)

    def available(self) -> bool:
        """True when the analyzer answers at all.

        Used to say plainly which titles could not be ingested, rather than
        producing an empty map and calling the title safe.
        """
        try:
            result = self._run(["--help"], timeout_s=120)
        except PipelineError:
            return False
        return result.returncode == 0

    def _run(self, args: Sequence[str], *, timeout_s: float | None = None) -> CommandResult:
        cmd = [*self.command, *[str(a) for a in args]]
        env = None
        if self.env is not None:
            env = {**os.environ, **self.env}
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout_s if timeout_s is not None else self.timeout_s,
            )
        except FileNotFoundError as exc:
            raise FlashmapUnavailable(f"cannot start the analyzer: {' '.join(cmd)}") from exc
        except subprocess.TimeoutExpired as exc:
            raise FlashmapUnavailable(
                f"the analyzer timed out after {exc.timeout} s: {' '.join(cmd)}"
            ) from exc
        return CommandResult(
            ok=completed.returncode == 0,
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            cmd=cmd,
        )

    def analyze(
        self,
        video: str | Path,
        *,
        profile: str,
        out_path: str | Path,
        diag_in: float | None = None,
        distance_ft: float | None = None,
        key: str | Path | None = None,
        picture_from: str | Path | None = None,
        timeout_s: float | None = None,
    ) -> FlashMapDoc:
        """Analyze ``video`` for one pipeline preset.

        ``profile`` is the preset name. The analyzer profile and any room
        window that preset implies come from ``PRESET_SPECS``. A caller that
        passes its own ``diag_in`` or ``distance_ft`` overrides the preset,
        which is how a household's own television and seat distance reach the
        analyzer.

        ``picture_from`` is the map to take the picture rectangle from instead
        of detecting one. It is for a re-encode of the file that map describes:
        re-encoding nudges the outermost rows and columns, and the detector can
        come back with a bar one row taller or shorter than the one it found in
        the original. Area fractions are measured on the picture, so one row is
        enough to lift a span over the limit and flag content the source never
        had. Titles are always analyzed from the source; this keeps a check on
        a rendition measured on the same ground the source was.
        """
        preset = PRESET_SPECS.get(profile, Preset(profile, profile))
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        args: list[str] = [
            "analyze",
            str(video),
            "--profile",
            preset.profile,
            "--out",
            str(out_path),
        ]
        room_diag = diag_in if diag_in is not None else preset.diag_in
        room_distance = distance_ft if distance_ft is not None else preset.distance_ft
        if room_diag is not None:
            args += ["--diag", str(room_diag)]
        if room_distance is not None:
            args += ["--distance-ft", str(room_distance)]
        if key is not None:
            args += ["--key", str(key)]
        if picture_from is not None:
            args += ["--picture-from", str(picture_from)]

        result = self._run(args, timeout_s=timeout_s)
        if result.returncode not in ANALYZE_OK_EXIT_CODES:
            raise FlashmapFailed(
                f"flashmap analyze failed for {video} at preset {profile} "
                f"(exit {result.returncode})\n"
                f"{(result.stderr or result.stdout).strip()[-2000:]}"
            )
        if not out_path.exists():
            raise FlashmapFailed(
                f"flashmap analyze finished but wrote no map at {out_path}"
            )
        doc = load_map(out_path)
        # The exit code and the map have to tell the same story. If they do
        # not, something is wrong with the run and the map cannot be trusted
        # either way.
        if (result.returncode == EXIT_NOTHING_FLAGGED) != doc.is_clean:
            raise FlashmapFailed(
                f"flashmap analyze exited {result.returncode} but wrote "
                f"{doc.violation_count} segment(s) at {out_path}. Exit "
                f"{EXIT_NOTHING_FLAGGED} means nothing was over the thresholds "
                f"and exit {EXIT_SOMETHING_FLAGGED} means something was."
            )
        if doc.profile and doc.profile != preset.profile:
            raise FlashmapFailed(
                f"map at {out_path} says profile {doc.profile!r}, preset "
                f"{profile!r} asked for {preset.profile!r}"
            )
        doc.preset = profile
        return doc

    def verify(
        self,
        map_path: str | Path,
        video: str | Path,
        *,
        pub_key: str | Path,
        timeout_s: float | None = None,
    ) -> CommandResult:
        """Check the map's signature and its binding to the file.

        The analyzer owns the signing scheme, so it owns the check. The
        pipeline still compares the source hash itself, in verify.py, so a
        missing analyzer cannot quietly turn that check off.
        """
        args = ["verify", str(map_path), str(video), "--pub", str(pub_key)]
        return self._run(args, timeout_s=timeout_s)


def tail_to_hold_ms(map_path: str | Path) -> float:
    """How long the last picture has to be held for a rendition to end where the title does.

    A container can outlive its last coded frame. Ogg Theora writes a frame identical to the
    one before it as an empty packet, so a file that ends on repeats has a last coded frame
    well before its duration. flashmap keeps those repeats in the timeline, because that is
    what a player shows. ffmpeg drops them when it re-encodes, so without this the rendition
    comes out short: three NASA clips in this project's pool lose between 1.4 and 1.8 seconds
    off the end, which is both a missing tail and a rendition that no longer has the source's
    frame timing.

    Returns 0 whenever the file ends on its last picture, which is almost every file, and
    whenever the map does not say. Nothing is padded on a guess.
    """
    try:
        doc = load_map(map_path)
    except MapFormatError:
        return 0.0
    source = doc.raw.get("source") if isinstance(doc.raw, dict) else None
    if not isinstance(source, dict):
        return 0.0
    last = source.get("last_pts_ms")
    last_coded = source.get("last_coded_pts_ms")
    if not isinstance(last, (int, float)) or not isinstance(last_coded, (int, float)):
        return 0.0
    return max(0.0, float(last) - float(last_coded))


def iter_presets(value: Iterable[str] | None) -> list[str]:
    if not value:
        return list(PRESETS)
    presets = [str(v).strip() for v in value if str(v).strip()]
    unknown = [p for p in presets if p not in PRESETS]
    if unknown:
        raise PipelineError(
            f"unknown preset(s): {', '.join(unknown)}. Known: {', '.join(PRESETS)}"
        )
    return presets
