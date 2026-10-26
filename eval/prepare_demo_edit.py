"""Produce editable credits/title overlays and an unfilled approved-story assembly.

No footage, story art, speech, service call or production acceptance is generated.
The existing production renderer continues to refuse this incomplete assembly.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'docs/cloud-integration-2026-10-23/demo'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timecode(seconds: float) -> str:
    frames = round(seconds * 30)
    return f'{frames // 108000:02}:{frames // 1800 % 60:02}:{frames // 30 % 60:02}:{frames % 30:02}'


def reviewed_plan(template: Path) -> dict:
    plan = json.loads(template.read_text())
    script = json.loads((DEMO / 'narration-cues.json').read_text())
    if (plan.get('narration_cues') != script
            or plan.get('narration_script_sha256') != sha(DEMO / 'narration-cues.json')
            or plan.get('approvals', {}).get('script_sha256') != sha(DEMO / 'narration-cues.json')):
        raise ValueError('The exact approved narration must remain unchanged.')
    if any(asset.get('path') for asset in plan['assets'].values()):
        raise ValueError('Existing production assets must be reconciled before making an unfilled assembly.')
    if plan['segments'] != json.loads((DEMO / 'timeline.json').read_text())['segments']:
        raise ValueError('Keep the established story order and natural-speed timing.')
    return plan


def overlay(lines: list[tuple[str, int, int, str]]) -> str:
    fonts = ROOT / 'app/assets/fonts'
    regular = base64.b64encode((fonts / 'InterRegular.ttf').read_bytes()).decode()
    display = base64.b64encode((fonts / 'CalmDisplaySemibold.ttf').read_bytes()).decode()
    text = ''.join(f'<text x="96" y="{y}" font-size="{size}" font-family="{font}">{html.escape(line)}</text>'
                   for line, y, size, font in lines)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
<title>Calm Frames production text overlay; picture area is transparent</title>
<style>@font-face{{font-family:Inter;src:url(data:font/ttf;base64,{regular})}}
@font-face{{font-family:CalmDisplay;src:url(data:font/ttf;base64,{display})}}</style>
<rect x="0" y="816" width="1920" height="264" fill="#143c3f"/>
<g fill="#fff8e8">{text}</g></svg>'''


def prepare(output: Path, candidate: str, template: Path = DEMO / 'timeline.json') -> dict:
    if re.fullmatch('[0-9a-f]{40}', candidate) is None:
        raise ValueError('Record the full candidate SHA without treating it as accepted.')
    original = reviewed_plan(template)
    plan = copy.deepcopy(original)
    plan.update(artifact_role='assembly_draft_missing_production_inputs', source_commit=None,
                package_sha256=None, candidate_source_commit=candidate,
                production_stage='Unfilled assembly. Product/native acceptance and real production inputs remain pending.')
    for asset in plan['assets'].values():
        if asset['kind'] == 'native_video':
            asset.update(source_commit=None, package_sha256=None, production_capture=False,
                         capture_receipt_path=None, capture_receipt_sha256=None)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'assembly.draft.json').write_text(json.dumps(plan, indent=2) + '\n')
    shutil.copy2(DEMO / 'captions.draft.srt', output / 'narration.draft.srt')
    vtt = re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2', (DEMO / 'captions.draft.srt').read_text())
    (output / 'narration.draft.vtt').write_text('WEBVTT\n\n' + vtt)
    overlays = {
        'opening-title.svg': [('Calm Frames', 890, 58, 'CalmDisplay'), ('A place to return to', 954, 44, 'Inter'),
                              ('Illustrated story; fictional character.', 1025, 32, 'Inter')],
        'closing-credits.svg': [('Not a medical device.', 900, 44, 'Inter'),
                                ('McWay: MoneySavingVideos, CC BY 3.0.', 965, 38, 'Inter'),
                                ('Full credits and adaptation details in the description.', 1025, 30, 'Inter')],
    }
    for name, lines in overlays.items():
        (output / name).write_text(overlay(lines))
    for name in ('LICENSE-Inter', 'LICENSE-Fraunces'):
        shutil.copy2(ROOT / 'app/assets/fonts' / name, output / name)
    edl = ['TITLE: CALM FRAMES UNFILLED APPROVED STORY', 'FCM: NON-DROP FRAME', '']
    slots = []
    for index, segment in enumerate(plan['segments'], 1):
        name = segment['asset']
        duration = segment['duration']
        start = segment['start']
        reel = name.upper().replace('_', '')[:8]
        edl.extend([f'{index:03}  {reel:<8} V     C        {timecode(0)} {timecode(duration)} {timecode(start)} {timecode(start + duration)}',
                    f'* FROM CLIP NAME: MISSING_{name}', '* UNFILLED SLOT; NOT CAPTURE EVIDENCE', ''])
        slots.append({'id': name, 'kind': plan['assets'][name]['kind'], 'start': start,
                      'duration': duration, 'path': None, 'status': 'missing'})
    for cue in plan['narration_cues']:
        slots.append({'id': cue['id'], 'kind': 'narration', 'start': cue['start'],
                      'duration': cue['end'] - cue['start'], 'path': None, 'status': 'missing'})
    (output / 'picture-slots.edl').write_text('\n'.join(edl))
    (output / 'required-inputs.json').write_text(json.dumps(slots, indent=2) + '\n')
    (output / 'README.txt').write_text('''Calm Frames production edit assets

The two self-contained SVG files are real title/credit overlays, 1920 by 1080,
using existing Inter and Fraunces fonts with their licenses. The upper picture
area is transparent. Their text retains the approved story labels and existing
McWay attribution. They are editorial graphics, not story art or native footage.
Their placement over actual art still needs composition and readability review.

picture-slots.edl is a CMX-style 30 fps non-drop picture assembly with explicit
MISSING clip names. Its durations are editorial targets, not recorded footage.
Native audio and narration are not fabricated or represented by silent tracks.
The EDL syntax and timeline totals are checked locally; no editor import is claimed.
assembly.draft.json is the existing renderer's plan with unaccepted build identity
cleared. The candidate SHA is context only. Production preflight must refuse it.
All five illustrations, five native takes and eight narration cues remain absent.
The browser walkthrough is supporting evidence and cannot fill a native slot.

SRT/VTT retain the eight approved narration cues and target times exactly. They
are not aligned to recorded speech. Reconcile the accepted build and measured
narration before production; do not accelerate footage or voice to fit a slot.
The 70-second ambient slot stays one continuous native take at natural speed.
Full-video human review, native acceptance and publication are separate.
No paid generation, private upload, new voice selection or live change occurred.
''')
    result = {
        'candidate_source': candidate, 'accepted_source': None,
        'story_sha256': sha(DEMO / 'STORYBOARD.md'),
        'narration_sha256': sha(DEMO / 'narration-cues.json'),
        'timeline_sha256': sha(DEMO / 'timeline.json'),
        'tool_sha256': sha(Path(__file__)),
        'editorial_overlays_produced': list(overlays),
        'produced_native_footage': False, 'produced_story_art': False, 'produced_narration': False,
        'source_files': {name: sha(output / name) for name in sorted(p.name for p in output.iterdir())},
    }
    (output / 'ASSET_RECEIPT.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    prepare(args.output.resolve(), candidate)
