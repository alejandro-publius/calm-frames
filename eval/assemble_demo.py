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
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / 'app/assets/fonts/InterRegular.ttf'
LABEL_FONT = ROOT / 'app/assets/fonts/InterMedium.ttf'
FRAME_HEIGHT = 880
CAPTION_WIDTH = 1728
CAPTION_SIZE = 38
CAPTION_LINE_HEIGHT = 48
KINDS = {'native_still', 'native_video', 'editorial'}
PROVENANCE_NOTE = (
    'Capture observations and the package/source association are operator-supplied. '
    'Validated hashes establish file identity; they do not independently prove '
    'that these frames were observed in Vega or built from the stated commit.'
)
# The next recording plan. Source identity stays blank until a fresh native run.
TEMPLATE_SHOTS = [
    ('brand-opening', 'editorial', 0, 6,
     'Calm Frames helps families affected by photosensitivity share a calmer movie night.'),
    ('library', 'native_video', 0, 10,
     'On the Vega Virtual Device, families browse checked titles with a remote. The quiet library opens directly into a story.'),
    ('details', 'native_video', 0, 12,
     'Harbor is our original, non-flashing demo film. Two scheduled practice holds show the player in action. These are examples, not detected flashing.'),
    ('harbor-holds', 'native_video', 2, 26,
     'When the picture holds a checked still, the recorded tone and English captions continue. Watch both scheduled holds, without showing hazardous footage.'),
    ('transport', 'native_video', 2, 22,
     'Every seek passes through the same guard. Pause, skip or go back with the remote; interrupted playback keeps an opaque cover in place.'),
    ('pin', 'native_video', 0, 9,
     'Parental controls stay behind a PIN. A clear Delete action makes corrections easy.'),
    ('parent', 'native_video', 0, 12,
     'Parents choose the viewing preset and room. Child profiles can only make settings stricter. Gentle artwork motion and selection sounds are optional.'),
    ('history', 'native_still', 0, 12,
     'The household choices stay saved after restarting. Practice holds never enter exposure history, and actual cover history clears when the app restarts.'),
    ('prepared-harbor', 'native_video', 2, 21,
     'This version of Harbor went through the real preparation pipeline. Its signed map is checked before playback; the rendition is packaged with the app.'),
    ('prototype-status', 'editorial', 0, 20,
     'AWS has also published a signed title through a separate cloud pipeline. Detection can miss flashing. Calm Frames reduces exposure to flashing above published limits in the videos it plays; not a medical device.'),
    ('brand-closing', 'editorial', 0, 6,
     'A reusable analyzer and player hook, built for calmer family viewing.'),
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


def caption_cues(text: str, speech_seconds: float, duration: float) -> list[dict]:
    """Fit readable phrases to the bundled font; timing follows spoken word share.

    These are estimated subtitle timings, not speech alignment or observations
    of native playback. Each cue uses at most two measured lines.
    """
    if not math.isfinite(speech_seconds) or not 0 < speech_seconds <= duration - 0.3:
        raise ValueError('Narration must fit inside its shot with time to finish')
    words = text.split()
    if not words:
        raise ValueError('Narration cannot be empty')
    font = ImageFont.truetype(str(FONT), CAPTION_SIZE)
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if font.getlength(word) > CAPTION_WIDTH:
            raise ValueError('A narration word is too wide for the subtitle area')
        candidate = ' '.join([*current, word])
        if current and (font.getlength(candidate) > CAPTION_WIDTH or len(current) >= 9):
            lines.append(' '.join(current))
            current = []
        current.append(word)
    if current:
        lines.append(' '.join(current))
    cues = []
    spoken_words = 0
    for index in range(0, len(lines), 2):
        pair = lines[index:index + 2]
        start = speech_seconds * spoken_words / len(words)
        spoken_words += sum(len(line.split()) for line in pair)
        end = speech_seconds * spoken_words / len(words)
        if spoken_words == len(words):
            end = min(duration, end + 0.5)
        cues.append({'start_seconds': start, 'end_seconds': end, 'lines': pair})
    return cues


def render_shot(shot: Shot, voice: Path, directory: Path, index: int) -> tuple[Path, list[dict]]:
    """Fit the whole source above the subtitles without cropping native captions.

    This encoder can be exercised with benign synthetic fixtures on Linux.
    Producing the actual narrated demo still requires the Mac capture and TTS.
    """
    speech_seconds = float(media_info(voice)['format']['duration'])
    cues = caption_cues(shot.narration, speech_seconds, shot.duration)
    footer = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(footer)
    draw.rectangle((0, FRAME_HEIGHT, 1920, 1080), fill='#102F3A')
    label = {
        'native_still': 'Vega Virtual Device | Actual still capture',
        'native_video': 'Vega Virtual Device | Actual video capture',
        'editorial': 'Calm Frames | Editorial card',
    }[shot.kind]
    draw.text((96, 898), label + ' | Synthetic narration',
              font=ImageFont.truetype(str(LABEL_FONT), 24), fill='#E6A957', anchor='lt')
    footer_path = directory / f'footer-{index:02}.png'
    footer.save(footer_path)
    font = ImageFont.truetype(str(FONT), CAPTION_SIZE)
    overlays = []
    for cue_index, cue in enumerate(cues):
        overlay = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for line_index, line in enumerate(cue['lines']):
            draw.text((96, 940 + line_index * CAPTION_LINE_HEIGHT), line,
                      font=font, fill='#F3E8D3', anchor='lt')
        path = directory / f'caption-{index:02}-{cue_index:02}.png'
        overlay.save(path)
        overlays.append(path)
    args = ['ffmpeg', '-v', 'error', '-n']
    still = shot.kind != 'native_video'
    if still:
        args += ['-loop', '1', '-framerate', '30', '-i', str(shot.source)]
    else:
        args += ['-ss', str(shot.start), '-i', str(shot.source)]
    args += ['-loop', '1', '-i', str(footer_path), '-i', str(voice)]
    for overlay in overlays:
        args += ['-loop', '1', '-i', str(overlay)]
    graph = (
        f'[0:v]scale=1920:{FRAME_HEIGHT}:force_original_aspect_ratio=decrease:'
        'force_divisible_by=2,setsar=1,fps=30,'
        'pad=1920:1080:(ow-iw)/2:0:color=0x102F3A[frame];'
        '[frame][1:v]overlay=0:0:shortest=1[caption0];'
    )
    for cue_index, cue in enumerate(cues):
        graph += (
            f'[caption{cue_index}][{cue_index + 3}:v]overlay=0:0:shortest=1:'
            f"enable='gte(t,{cue['start_seconds']:.6f})*lt(t,{cue['end_seconds']:.6f})'"
            f'[caption{cue_index + 1}];'
        )
    if still:
        graph += '[2:a]aresample=48000,apad,alimiter=limit=0.95:level=0[outa]'
    else:
        graph += (
            '[0:a]aresample=48000,apad[native];[2:a]aresample=48000,apad[voice];'
            '[native][voice]amix=inputs=2:normalize=0,alimiter=limit=0.95:level=0[outa]'
        )
    dest = directory / f'part-{index:02}.mp4'
    args += ['-filter_complex', graph, '-map', f'[caption{len(cues)}]', '-map', '[outa]',
             '-t', str(shot.duration), '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', str(dest)]
    run(args)
    return dest, cues


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
        _, cues = render_shot(shot, voice, plan.output, i)
        manifest.append({
            'name': shot.name, 'kind': shot.kind, 'source': display_path(shot.source),
            'source_sha256': shot.sha256, 'source_start_seconds': shot.start,
            'output_start_seconds': cursor, 'duration_seconds': shot.duration,
            'still': shot.kind != 'native_video', 'narration': shot.narration, 'narration_voice': 'macOS Samantha TTS',
            'native_audio_gain_db': 0, 'subtitle_cues': cues,
        })
        for cue in cues:
            caption_text = '\n'.join(cue['lines'])
            captions.append(f"{len(captions)+1}\n{stamp(cursor+cue['start_seconds'])} --> {stamp(cursor+cue['end_seconds'])}\n{caption_text}\n")
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
        'edits': 'Cuts, aspect-preserving scaling with the full source above a dedicated subtitle area, constant-frame-rate encoding, timed subtitles and narration mixed with native audio at unity gain through a peak limiter. No generated app footage.',
        'subtitle_timing': 'Estimated from each cue word count and the measured narration duration. Review against the spoken audio before publication.',
        'fonts': {display_path(path): sha256(path) for path in [FONT, LABEL_FONT]},
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
