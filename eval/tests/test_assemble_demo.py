"""A refreshed demo must not inherit the old footage identity or overwrite it.

Fixtures contain inert bytes. Media metadata is stubbed, and render is trapped;
these tests neither create nor display video. Hash and destination mutations
were exercised separately to show these guards fail when removed.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from eval import assemble_demo as demo

REAL_ASSEMBLE = demo.assemble


@pytest.fixture
def capture(tmp_path, monkeypatch):
    package = tmp_path / 'current.vpkg'
    package.write_bytes(b'benign package fixture')
    video = tmp_path / 'capture.mp4'
    video.write_bytes(b'benign inert capture fixture')
    data = {
        'schema_version': 1,
        'capture_source_commit': 'a' * 40,
        'capture_package': {'path': str(package), 'sha256': demo.sha256(package)},
        'shots': [{
            'name': 'observed-playback', 'kind': 'native_video',
            'source': str(video), 'sha256': demo.sha256(video),
            'start_seconds': 2, 'duration_seconds': 10,
            'narration': 'The scheduled demo hold uses non-flashing media.',
        }],
    }
    monkeypatch.setattr(demo, 'media_info', lambda path: {
        'format': {'duration': '15'},
        'streams': [{'codec_type': 'video'}, {'codec_type': 'audio'}],
    })
    rendered = []
    monkeypatch.setattr(demo, 'assemble', lambda plan: rendered.append(plan) or {})
    return data, tmp_path / 'plan.json', tmp_path / 'new-output', tmp_path / 'new-result.json', rendered


def invoke(capture, *, dry_run=False):
    data, manifest, output, result, _ = capture
    manifest.write_text(json.dumps(data))
    args = ['--manifest', str(manifest), '--output-dir', str(output), '--result', str(result)]
    return demo.main(args + (['--dry-run'] if dry_run else []))


def test_dry_run_validates_without_creating_outputs_or_rendering(capture, capsys):
    assert invoke(capture, dry_run=True) == 0
    data, _, output, result, rendered = capture
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['capture_source_commit'] == data['capture_source_commit']
    assert receipt['capture_package_sha256'] == data['capture_package']['sha256']
    assert receipt['preflight_passed'] is True
    assert 'do not independently prove' in receipt['provenance_note']
    assert not output.exists() and not result.exists() and not rendered


def test_explicit_current_provenance_reaches_renderer(capture):
    assert invoke(capture) == 0
    data, _, _, _, rendered = capture
    assert len(rendered) == 1
    plan = rendered[0]
    assert plan.source_commit == 'a' * 40
    assert plan.package_sha256 == data['capture_package']['sha256']
    assert plan.shots[0].source.name == 'capture.mp4'
    assert plan.shots[0].kind == 'native_video'


@pytest.mark.parametrize('case', [
    'missing-package', 'missing-shot', 'package-hash', 'shot-hash', 'short-commit',
    'unfilled-commit', 'unfilled-source', 'unknown-kind', 'missing-kind',
    'negative-start', 'zero-duration', 'nan-duration', 'overlong-demo',
    'video-too-short', 'hazard-name', 'no-audio',
])
def test_invalid_input_stops_before_render(capture, monkeypatch, case):
    data, _, output, result, rendered = capture
    shot = data['shots'][0]
    if case == 'missing-package':
        Path(data['capture_package']['path']).unlink()
    elif case == 'missing-shot':
        Path(shot['source']).unlink()
    elif case == 'package-hash':
        Path(data['capture_package']['path']).write_bytes(b'changed package')
    elif case == 'shot-hash':
        Path(shot['source']).write_bytes(b'changed capture')
    elif case == 'short-commit':
        data['capture_source_commit'] = 'cba1a29'
    elif case == 'unfilled-commit':
        data['capture_source_commit'] = ''
    elif case == 'unfilled-source':
        shot['source'] = ''
    elif case == 'unknown-kind':
        shot['kind'] = 'browser_preview'
    elif case == 'missing-kind':
        del shot['kind']
    elif case == 'negative-start':
        shot['start_seconds'] = -1
    elif case == 'zero-duration':
        shot['duration_seconds'] = 0
    elif case == 'nan-duration':
        shot['duration_seconds'] = float('nan')
    elif case == 'overlong-demo':
        shot['duration_seconds'] = 179
    elif case == 'video-too-short':
        shot['duration_seconds'] = 14
    elif case == 'hazard-name':
        source = Path(shot['source'])
        renamed = source.with_name('HAZARD_capture.mp4')
        source.rename(renamed)
        shot['source'] = str(renamed)
    elif case == 'no-audio':
        monkeypatch.setattr(demo, 'media_info', lambda path: {
            'format': {'duration': '15'}, 'streams': [{'codec_type': 'video'}],
        })
    assert invoke(capture) == 1
    assert not rendered
    assert not output.exists() and not result.exists()


@pytest.mark.parametrize('existing', ['output-directory', 'output-file', 'result'])
def test_existing_destinations_are_unchanged_and_no_render_starts(capture, existing):
    _, _, output, result, rendered = capture
    if existing == 'output-directory':
        output.mkdir()
        (output / 'prior-demo.mp4').write_bytes(b'previous reviewed demo')
    elif existing == 'output-file':
        output.write_bytes(b'existing output path')
    else:
        result.write_bytes(b'previous provenance')
    preserved = {path: path.read_bytes() for path in output.parent.rglob('*') if path.is_file()}
    assert invoke(capture) == 1
    assert not rendered
    assert all(path.read_bytes() == content for path, content in preserved.items())


def test_kind_is_explicit_and_does_not_come_from_logs_path(capture, monkeypatch):
    data, manifest, output, result, _ = capture
    editorial = copy.deepcopy(data['shots'][0])
    editorial.update(name='editorial', kind='editorial', start_seconds=0)
    source = manifest.parent / '.logs' / 'editorial-card.png'
    source.parent.mkdir()
    source.write_bytes(b'inert editorial fixture')
    editorial.update(source=str(source), sha256=demo.sha256(source))
    data['shots'].append(editorial)
    monkeypatch.setattr(demo, 'validate_media', lambda shot: None)
    manifest.write_text(json.dumps(data))
    plan = demo.preflight(manifest, output, result)
    assert plan.shots[1].kind == 'editorial'
    assert plan.shots[0].kind == 'native_video'


def test_native_still_requires_zero_offset(capture):
    data, _, _, _, rendered = capture
    still = copy.deepcopy(data['shots'][0])
    still.update(name='still', kind='native_still')
    data['shots'].append(still)
    assert invoke(capture) == 1
    assert not rendered


def test_template_is_unfilled_preserves_limits_and_cannot_overwrite(tmp_path):
    path = tmp_path / 'plan.json'
    assert demo.main(['--write-template', str(path)]) == 0
    before = path.read_bytes()
    data = json.loads(before)
    assert data['capture_source_commit'] == ''
    assert data['capture_package'] == {'path': '', 'sha256': ''}
    assert all(shot['source'] == '' and shot['sha256'] == '' for shot in data['shots'])
    assert {shot['kind'] for shot in data['shots']} == demo.KINDS
    narration = ' '.join(shot['narration'] for shot in data['shots'])
    assert 'not a medical device' in narration
    assert 'not detected flashing' in narration
    assert 'reduces exposure to flashing above published limits in the videos it plays; not a medical device' in narration
    assert demo.main(['--write-template', str(path)]) == 1
    assert path.read_bytes() == before


def test_real_assembly_refuses_linux_before_outputs_or_commands(capture, monkeypatch):
    # Undo the fixture's render trap to exercise the platform boundary.
    monkeypatch.setattr(demo, 'assemble', REAL_ASSEMBLE)
    data, manifest, output, result, _ = capture
    manifest.write_text(json.dumps(data))
    monkeypatch.setattr(demo, 'validate_media', lambda shot: None)
    monkeypatch.setattr(demo.platform, 'system', lambda: 'Linux')
    commands = []
    monkeypatch.setattr(demo, 'run', lambda args: commands.append(args))
    plan = demo.preflight(manifest, output, result)
    with pytest.raises(ValueError, match='requires macOS'):
        demo.assemble(plan)
    assert not commands and not output.exists() and not result.exists()


def test_caption_cues_fit_measured_font_and_preserve_all_words():
    text = ' '.join(['Wide words WWWWWW remain readable without covering the app.'] * 5)
    cues = demo.caption_cues(text, 20, 24)
    font = demo.ImageFont.truetype(str(demo.FONT), demo.CAPTION_SIZE)
    assert len(cues) > 1
    assert ' '.join(line for cue in cues for line in cue['lines']).split() == text.split()
    assert all(1 <= len(cue['lines']) <= 2 for cue in cues)
    assert all(font.getlength(line) <= demo.CAPTION_WIDTH for cue in cues for line in cue['lines'])
    assert cues[0]['start_seconds'] == 0
    assert all(a['end_seconds'] == b['start_seconds'] for a, b in zip(cues, cues[1:]))
    assert 20 <= cues[-1]['end_seconds'] < 24


@pytest.mark.parametrize('speech', [0, -1, float('nan'), float('inf'), 10])
def test_caption_timing_refuses_missing_or_overlong_narration(speech):
    with pytest.raises(ValueError, match='Narration must fit'):
        demo.caption_cues('Keep the full app visible.', speech, 10)


def test_caption_cues_refuse_a_word_that_cannot_fit():
    with pytest.raises(ValueError, match='too wide'):
        demo.caption_cues('W' * 300, 3, 5)


@pytest.mark.parametrize('kind', ['native_still', 'native_video'])
def test_real_encoder_keeps_bottom_of_source_visible_and_limits_audio(tmp_path, kind):
    """Only solid colour fixtures and a synthetic tone; never app/native evidence."""
    import array
    import io
    import math
    import subprocess
    import wave

    from PIL import Image, ImageChops, ImageDraw

    source = tmp_path / 'synthetic-source.png'
    picture = Image.new('RGB', (320, 180), '#102F3A')
    ImageDraw.Draw(picture).rectangle((0, 160, 319, 179), fill='#E6A957')
    picture.save(source)
    voice = tmp_path / 'synthetic-tone.wav'
    samples = array.array('h', (round(0.8 * 32767 * math.sin(2 * math.pi * 330 * i / 48000))
                                for i in range(48000)))
    with wave.open(str(voice), 'wb') as audio:
        audio.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        audio.writeframes(samples.tobytes())
    if kind == 'native_video':
        clip = tmp_path / 'synthetic-source.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-n', '-loop', '1', '-i', str(source),
                        '-stream_loop', '-1', '-i', str(voice), '-t', '2', '-r', '30',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(clip)],
                       check=True)
        source = clip
    shot = demo.Shot('encoder-fixture', source, demo.sha256(source), kind, 0, 2,
                     'The full picture remains visible while short subtitle cues explain '
                     'the scene. Each cue has room to breathe, and the complete source stays above it.')
    output, cues = demo.render_shot(shot, voice, tmp_path, 0)
    frame = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', '0.2', '-i', str(output),
                                     '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'])
    with Image.open(io.BytesIO(frame)) as image:
        # The amber stripe is at the very bottom of the original picture.
        # A footer over an uncropped full-screen source would hide that stripe.
        assert all(abs(a - b) < 8 for a, b in zip(image.getpixel((960, 860)), (230, 169, 87)))
        assert image.size == (1920, 1080)
        caption_region = image.crop((96, 940, 1824, 1026)).convert('RGB')
        delta = ImageChops.difference(caption_region, Image.new('RGB', caption_region.size, '#102F3A'))
        assert max(high for _, high in delta.getextrema()) > 40
    last_frame = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', '1.8', '-i', str(output),
                                          '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'])
    with Image.open(io.BytesIO(last_frame)) as image:
        caption_region = image.crop((96, 940, 1824, 1026)).convert('RGB')
        delta = ImageChops.difference(caption_region, Image.new('RGB', caption_region.size, '#102F3A'))
        assert max(high for _, high in delta.getextrema()) < 8
    decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output),
                                       '-map', '0:a:0', '-f', 'f32le', '-'])
    samples_out = array.array('f')
    samples_out.frombytes(decoded)
    # Measure encoded channels directly; downmixing stereo can add 3 dB.
    peak = max(abs(value) for value in samples_out)
    assert 0.1 < peak < 1.0
    assert len(cues) > 1 and cues[-1]['end_seconds'] <= 2
