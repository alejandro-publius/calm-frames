"""Assemble a reviewed demo from explicitly identified Vega captures on macOS.

Write and fill a capture-plan template, then run --dry-run before assembly.
Hashes establish file identity, not independent evidence of a Vega observation
or that a package was built from the operator-supplied source commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
KINDS = {'native_still', 'native_video', 'editorial'}
PROVENANCE_NOTE = (
    'Capture observations and the package/source association are operator-supplied. '
    'Validated hashes establish file identity; they do not independently prove '
    'that these frames were observed in Vega or built from the stated commit.'
)
# Timing and narration from the reviewed demo, without its old capture identity.
TEMPLATE_SHOTS = [
    ('brand-opening', 'editorial', 0, 6,
     'Calm Frames. A calmer way to watch, for families where a child has photosensitive epilepsy.'),
    ('library', 'native_still', 0, 10,
     'Calm Frames is running on the Vega Virtual Device. This redesigned library contains the checked videos packaged with the app.'),
    ('details', 'native_still', 0, 12,
     'Harbor is original, non-flashing media. The scene hold demo adds two scheduled holds. These are examples, not detected flashing.'),
    ('harbor-holds', 'native_video', 2, 26,
     'Watch the scheduled holds. The recorded tone and English captions continue while the picture holds a calm scene.'),
    ('transport', 'native_video', 2, 22,
     'The remote seeks, pauses, and resumes. Interrupted playback uses an opaque cover. This demonstrates behavior, not physical screen timing.'),
    ('pin', 'native_still', 0, 9,
     'A PIN protects parental controls. Incorrect entries stay locked, and Delete corrects a partial entry.'),
    ('parent', 'native_still', 0, 12,
     'Parents choose Standard, Broadcast, or Extra cautious. Each choice was tested in Vega. A child cannot relax the settings chosen for everyone.'),
    ('history', 'native_still', 0, 12,
     'Settings survive restart. Scheduled demo holds are excluded from exposure history. Actual cover history is not saved across app restarts.'),
    ('prepared-harbor', 'native_video', 2, 21,
     'This separate Harbor title uses real local preparation without the demonstration holds. The app plays its checked, packaged rendition. The source had no detected flashing.'),
    ('prototype-status', 'editorial', 0, 20,
     'The saved AWS run published a signed title. The app uses its local library. Detection can miss flashing. Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device.'),
    ('brand-closing', 'editorial', 0, 6,
     'Calm Frames. A calmer way to watch.'),
]


@dataclass(frozen=True)
class Shot:
    name: str
    source: Path
    sha256: str
    kind: str
    start: float
    duration: float
    narration: str


@dataclass(frozen=True)
class Plan:
    manifest: Path
    manifest_sha256: str
    source_commit: str
    package: Path
    package_sha256: str
    shots: tuple[Shot, ...]
    output: Path
    result: Path


def sha256(path: Path) -> str:
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def required_text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be filled in')
    return value


def input_file(value, label: str) -> Path:
    path = Path(required_text(value, label)).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if any(part.upper().startswith('HAZARD_') for part in path.parts):
        raise ValueError(f'{label}: hazardous media is not a demo input')
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'{label} must name an existing nonempty file: {path}')
    return path


def verify_hash(path: Path, expected, label: str) -> str:
    if not isinstance(expected, str) or re.fullmatch(r'[0-9a-f]{64}', expected) is None:
        raise ValueError(f'{label} requires a lowercase SHA-256')
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f'{label} SHA-256 mismatch: {path}')
    return actual


def number(value, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} must be a finite number')
    value = float(value)
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f'{label} must be {"positive" if positive else "nonnegative"} and finite')
    return value


def new_destination(path: Path, label: str) -> Path:
    path = path.expanduser().resolve()
    if path.exists() or path.is_symlink():
        raise ValueError(f'{label} already exists; choose a new path: {path}')
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir():
        raise ValueError(f'{label} has a parent that is not a directory: {parent}')
    return path


def media_info(path: Path) -> dict:
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type', '-of', 'json', str(path),
    ], text=True))


def validate_media(shot: Shot) -> None:
    if shot.kind != 'native_video':
        if shot.start != 0:
            raise ValueError(f'{shot.name}: still images require start_seconds=0')
        with Image.open(shot.source) as image:
            image.verify()
        return
    info = media_info(shot.source)
    streams = {stream.get('codec_type') for stream in info.get('streams', [])}
    if not {'video', 'audio'} <= streams:
        raise ValueError(f'{shot.name}: native video requires video and audio streams')
    try:
        available = float(info['format']['duration'])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f'{shot.name}: video duration is unavailable') from error
    if not math.isfinite(available) or shot.start + shot.duration > available:
        raise ValueError(f'{shot.name}: requested interval exceeds the captured video')


def preflight(manifest: Path, output: Path, result: Path) -> Plan:
    """Validate every input and destination before rendering or creating outputs."""
    output = new_destination(output, 'Output directory')
    result = new_destination(result, 'Result JSON')
    if output == result or output.is_relative_to(result):
        raise ValueError('Result JSON cannot be the output directory or its parent')
    if result.suffix != '.json':
        raise ValueError('Result path must end in .json')
    manifest = input_file(str(manifest), 'Manifest')
    data = json.loads(manifest.read_text())
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Manifest schema_version must be 1')
    commit = data.get('capture_source_commit')
    if not isinstance(commit, str) or re.fullmatch(r'[0-9a-f]{40}', commit) is None or set(commit) == {'0'}:
        raise ValueError('capture_source_commit requires the full 40-character commit')
    package_info = data.get('capture_package')
    if not isinstance(package_info, dict):
        raise ValueError('capture_package must contain path and sha256')
    package = input_file(package_info.get('path'), 'Capture package')
    if package.suffix != '.vpkg':
        raise ValueError('Capture package must be a .vpkg file')
    package_hash = verify_hash(package, package_info.get('sha256'), 'Capture package')
    entries = data.get('shots')
    if not isinstance(entries, list) or not entries:
        raise ValueError('shots must be a nonempty list')
    shots = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f'Shot {index + 1} must be an object')
        name = required_text(entry.get('name'), f'Shot {index + 1} name')
        kind = entry.get('kind')
        if not isinstance(kind, str) or kind not in KINDS:
            raise ValueError(f'{name}: kind must be native_still, native_video or editorial')
        source = input_file(entry.get('source'), f'{name} source')
        digest = verify_hash(source, entry.get('sha256'), name)
        shots.append(Shot(
            name, source, digest, kind,
            number(entry.get('start_seconds'), f'{name} start_seconds'),
            number(entry.get('duration_seconds'), f'{name} duration_seconds', positive=True),
            required_text(entry.get('narration'), f'{name} narration'),
        ))
    if len({shot.name for shot in shots}) != len(shots):
        raise ValueError('Shot names must be unique')
    if not any(shot.kind == 'native_video' for shot in shots):
        raise ValueError('The demo must include an explicitly identified native_video shot')
    if sum(shot.duration for shot in shots) >= 179:
        raise ValueError('Planned demo must be shorter than 179 seconds')
    for shot in shots:
        validate_media(shot)
    return Plan(manifest, sha256(manifest), commit, package, package_hash, tuple(shots), output, result)


def write_template(path: Path) -> None:
    """Leave provenance blank so an old build cannot silently become the default."""
    data = {
        'schema_version': 1,
        'instructions': 'Fill every blank from the new capture session. Relative input paths are relative to the repository root. Review every narration claim against observed behavior. Editorial entries require existing still images, including the prototype status card.',
        'provenance_note': PROVENANCE_NOTE,
        'capture_source_commit': '',
        'capture_package': {'path': '', 'sha256': ''},
        'shots': [dict(name=name, kind=kind, source='', sha256='', start_seconds=start,
                       duration_seconds=duration, narration=narration)
                  for name, kind, start, duration, narration in TEMPLATE_SHOTS],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as target:
        target.write(json.dumps(data, indent=2) + '\n')


def run(args):
    subprocess.run(args, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def assemble(plan: Plan) -> dict:
    """Render on macOS only, after all source hashes and media passed preflight."""
    if platform.system() != 'Darwin':
        raise ValueError('Assembly requires macOS Samantha TTS; use --dry-run on Linux')
    # Recheck file identity immediately before creating a new assembly.
    verify_hash(plan.manifest, plan.manifest_sha256, 'Manifest')
    verify_hash(plan.package, plan.package_sha256, 'Capture package')
    for shot in plan.shots:
        verify_hash(shot.source, shot.sha256, shot.name)
    new_destination(plan.result, 'Result JSON')
    plan.output.mkdir(parents=True, exist_ok=False)
    manifest = []
    captions = []
    cursor = 0
    for i, shot in enumerate(plan.shots):
        voice = plan.output / f'voice-{i:02}.aiff'
        textfile = plan.output / f'voice-{i:02}.txt'
        textfile.write_text(shot.narration + '\n')
        run(['say', '-v', 'Samantha', '-r', '165', '-o', str(voice), '-f', str(textfile)])
        voice_seconds = float(media_info(voice)['format']['duration'])
        if voice_seconds > shot.duration - 0.3:
            raise ValueError(f'{shot.name}: narration is too long; revise the plan and choose new output paths')
        overlay = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle((0, 944, 1920, 1080), fill=(12, 32, 39, 255))
        label = {
            'native_still': 'Vega Virtual Device | Actual still capture',
            'native_video': 'Vega Virtual Device | Actual video capture',
            'editorial': 'Calm Frames | Editorial card',
        }[shot.kind]
        draw.text((55, 952), label, font=ImageFont.truetype(FONT, 23), fill='#e6ab55')
        lines = textwrap.wrap(shot.narration, width=110)
        font = ImageFont.truetype(FONT, 30 if len(lines) > 2 else 34)
        for j, line in enumerate(lines):
            draw.text((55, 987 + j * 29), line, font=font, fill='#f4ead3')
        overlay_path = plan.output / f'footer-{i:02}.png'
        overlay.save(overlay_path)
        args = ['ffmpeg', '-v', 'error', '-n']
        still = shot.kind != 'native_video'
        if still:
            args += ['-loop', '1', '-framerate', '30', '-i', str(shot.source)]
        else:
            args += ['-ss', str(shot.start), '-i', str(shot.source)]
        args += ['-loop', '1', '-i', str(overlay_path), '-i', str(voice)]
        graph = '[0:v]scale=1920:1080,setsar=1,fps=30[v];[v][1:v]overlay=0:0:shortest=1[outv];'
        if still:
            graph += '[2:a]aresample=48000,apad[outa]'
        else:
            graph += '[0:a]aresample=48000,volume=6.3,apad[native];[2:a]aresample=48000,apad[voice];[native][voice]amix=inputs=2:normalize=0[outa]'
        dest = plan.output / f'part-{i:02}.mp4'
        args += ['-filter_complex', graph, '-map', '[outv]', '-map', '[outa]', '-t', str(shot.duration),
                 '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
                 '-c:a', 'aac', '-b:a', '192k', str(dest)]
        run(args)
        manifest.append({
            'name': shot.name, 'kind': shot.kind, 'source': display_path(shot.source),
            'source_sha256': shot.sha256, 'source_start_seconds': shot.start,
            'output_start_seconds': cursor, 'duration_seconds': shot.duration,
            'still': still, 'narration': shot.narration, 'narration_voice': 'macOS Samantha TTS',
            'native_audio_gain_db': 0 if still else 15.99,
        })
        captions.append(f'{i+1}\n{stamp(cursor)} --> {stamp(cursor+shot.duration)}\n{shot.narration}\n')
        cursor += shot.duration
        print(f'Encoded shot {i+1}: {shot.duration}s', flush=True)
    concat = plan.output / 'parts.txt'
    concat.write_text(''.join(f"file 'part-{i:02}.mp4'\n" for i in range(len(plan.shots))))
    final = plan.output / 'Calm-Frames-demo-English.mp4'
    run(['ffmpeg', '-v', 'error', '-n', '-f', 'concat', '-safe', '0', '-i', str(concat),
         '-c', 'copy', '-movflags', '+faststart', str(final)])
    (plan.output / 'Calm-Frames-demo-English.srt').write_text('\n'.join(captions))
    result = {
        'capture_source_commit': plan.source_commit,
        'capture_package': display_path(plan.package), 'capture_package_sha256': plan.package_sha256,
        'capture_manifest': display_path(plan.manifest), 'capture_manifest_sha256': plan.manifest_sha256,
        'provenance_note': PROVENANCE_NOTE,
        'video': display_path(final), 'sha256': sha256(final),
        'duration_seconds': float(media_info(final)['format']['duration']),
        'language': 'English', 'narration': 'macOS Samantha synthetic narration',
        'footage': 'Operator-identified Vega Virtual Device recordings and still captures; disclosed editorial cards',
        'edits': 'Cuts, scaling, constant-frame-rate encoding, footer subtitles, narration and native audio gain. No generated app footage.',
        'shots': manifest,
    }
    if result['duration_seconds'] >= 180:
        raise ValueError('Encoded demo is not shorter than three minutes; no success receipt written')
    plan.result.parent.mkdir(parents=True, exist_ok=True)
    with plan.result.open('x') as target:
        target.write(json.dumps(result, indent=2) + '\n')
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--write-template', type=Path)
    source.add_argument('--manifest', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.write_template:
            if args.output_dir or args.result or args.dry_run:
                parser.error('--write-template cannot be combined with assembly options')
            write_template(args.write_template)
            print(f'Unfilled capture plan: {args.write_template}')
            return 0
        if not args.output_dir or not args.result:
            parser.error('--manifest requires --output-dir and --result')
        plan = preflight(args.manifest, args.output_dir, args.result)
        if args.dry_run:
            print(json.dumps({
                'preflight_passed': True, 'capture_source_commit': plan.source_commit,
                'capture_package_sha256': plan.package_sha256, 'shots': len(plan.shots),
                'planned_duration_seconds': sum(shot.duration for shot in plan.shots),
                'provenance_note': PROVENANCE_NOTE,
                'next': 'Review capture observations and narration, then assemble on macOS without --dry-run.',
            }, indent=2))
        else:
            result = assemble(plan)
            print(json.dumps({key: value for key, value in result.items() if key != 'shots'}))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Demo preparation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
