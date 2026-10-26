"""No footage displayed: small synthetic test media exercises the preparation boundary."""
import json

import pytest

from pipeline import PipelineError, ffmpegtool
from pipeline.ambient import media_identity, prepare_ambient_candidate
from pipeline.flashmap_adapter import FlashMapDoc, MapSegment
from pipeline.hashing import sha256_file

from .clips import make_calm_clip
from .conftest import needs_ffmpeg


class Analyzer:
    def __init__(self, reject=False):
        self.reject = reject
        self.calls = []

    def analyze(self, media, **kwargs):
        self.calls.append((media, kwargs))
        path = kwargs['out_path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'source': sha256_file(media), 'profile': kwargs['profile']}))
        return FlashMapDoc(1, sha256_file(media), kwargs['profile'],
                           [MapSegment(0, 100, 'general')] if self.reject else [])


def inputs(tmp_path):
    source = make_calm_clip(tmp_path/'source.mp4', seconds=3, fps=24, width=96, height=64)
    ambient = tmp_path/'ambient.mp4'
    ffmpegtool.run_ffmpeg(['-f', 'lavfi', '-i', 'color=c=0x102040:s=96x64:r=24:d=3',
                          '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(ambient)])
    maps = {}
    for p in ('wcag', 'broadcast'):
        path = tmp_path/f'{p}.json'
        path.write_text(json.dumps({'version': 1, 'source': {'sha256': sha256_file(source)},
                                   'profile': {'name': p}, 'segments': [{'start_ms': 1000, 'end_ms': 1500, 'reason': 'general'}]}))
        maps[p] = path
    return source, ambient, maps


@needs_ffmpeg
def test_unsigned_candidate_retains_timeline_audio_and_exact_plan(tmp_path):
    source, ambient, maps = inputs(tmp_path)
    analyzer = Analyzer()
    root = tmp_path/'draft'
    result = prepare_ambient_candidate(source, ambient, maps=maps, preset='wcag', out_dir=root,
                                       attribution='Synthetic test fixture only', client=analyzer)
    assert result['status'] == 'prepared-unapproved'
    assert not result['approved'] and not result['signed']
    assert result['intervals'] == [{'startMs': 500, 'endMs': 2000}]
    assert media_identity(source)['audio_packets'] == media_identity(root/'candidate.mp4')['audio_packets']
    assert media_identity(source)['frame_times'] == media_identity(root/'candidate.mp4')['frame_times']
    def frame_hashes(path):
        result = ffmpegtool.run_ffmpeg(['-i', str(path), '-map', '0:v:0', '-vf', 'scale=1:1',
                                       '-f', 'framemd5', '-'])
        return [line.split(',')[-1].strip() for line in result.stdout.splitlines() if not line.startswith('#') and line.strip()]
    hashes = frame_hashes(root/'candidate.mp4')
    replacement = frame_hashes(ambient)[0]
    # Every covered frame is the replacement, including first/last boundary frames.
    assert all(hashes[n] == replacement for n in range(12, 48))
    assert hashes[11] != replacement and hashes[48] != replacement
    assert len(analyzer.calls) == 4
    assert all(call[1]['diag_in'] == 85 and call[1]['distance_ft'] == 4 for call in analyzer.calls)
    assert not list(root.glob('*.pem')) and not list(root.glob('*catalog*'))
    with pytest.raises(PipelineError, match='never overwritten'):
        prepare_ambient_candidate(source, ambient, maps=maps, preset='wcag', out_dir=root,
                                  attribution='Test', client=analyzer)


@needs_ffmpeg
def test_flagged_ambient_stops_before_render_or_metadata(tmp_path):
    source, ambient, maps = inputs(tmp_path)
    root = tmp_path/'rejected'
    with pytest.raises(PipelineError, match='analysis rejected'):
        prepare_ambient_candidate(source, ambient, maps=maps, preset='wcag', out_dir=root,
                                  attribution='Test', client=Analyzer(reject=True))
    assert not (root/'candidate.mp4').exists()
    assert not (root/'metadata.draft.json').exists()
    assert json.loads((root/'receipt.json').read_text())['status'] == 'rejected'


@needs_ffmpeg
def test_audio_bearing_ambient_and_wrong_source_map_are_refused(tmp_path):
    source, ambient, maps = inputs(tmp_path)
    with pytest.raises(PipelineError, match='audio-free'):
        prepare_ambient_candidate(source, source, maps=maps, preset='wcag', out_dir=tmp_path/'bad', attribution='Test')
    maps['wcag'].write_text(maps['wcag'].read_text().replace(sha256_file(source), 'a'*64))
    with pytest.raises(PipelineError, match='source-bound'):
        prepare_ambient_candidate(source, ambient, maps=maps, preset='wcag', out_dir=tmp_path/'bad2', attribution='Test')


@needs_ffmpeg
def test_flagged_complete_output_never_gets_activation_metadata(tmp_path):
    source, ambient, maps = inputs(tmp_path)

    class RejectOutput(Analyzer):
        def analyze(self, media, **kwargs):
            self.reject = media.name == 'candidate.mp4'
            return super().analyze(media, **kwargs)

    root = tmp_path/'bad-output'
    with pytest.raises(PipelineError, match='analysis rejected'):
        prepare_ambient_candidate(source, ambient, maps=maps, preset='wcag', out_dir=root,
                                  attribution='Test', client=RejectOutput())
    assert (root/'candidate.mp4').exists()  # Diagnostic artifact only.
    assert not (root/'metadata.draft.json').exists()


@needs_ffmpeg
def test_input_mutation_during_checks_is_rejected(tmp_path):
    source, ambient, maps = inputs(tmp_path)

    class Mutator(Analyzer):
        def analyze(self, media, **kwargs):
            result = super().analyze(media, **kwargs)
            if media.name == 'candidate.mp4':
                maps['wcag'].write_text(maps['wcag'].read_text() + ' ')
            return result

    root = tmp_path/'mutated'
    with pytest.raises(PipelineError, match='bytes changed'):
        prepare_ambient_candidate(source, ambient, maps=maps, preset='wcag', out_dir=root,
                                  attribution='Test', client=Mutator())
    assert not (root/'metadata.draft.json').exists()


@needs_ffmpeg
def test_short_ambient_cannot_end_before_a_cover(tmp_path):
    source, _, maps = inputs(tmp_path)
    short = make_calm_clip(tmp_path/'short.mp4', seconds=1, fps=24, width=96, height=64, audio=False)
    with pytest.raises(PipelineError, match='outlast every covered interval'):
        prepare_ambient_candidate(source, short, maps=maps, preset='wcag', out_dir=tmp_path/'short-draft', attribution='Test')
