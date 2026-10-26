"""Production edit assets retain the approved story and cannot pass as footage."""
import importlib.util
import json
from pathlib import Path

import pytest

from eval import prepare_demo_edit as edit


def test_edit_preserves_story_and_native_slots_and_fails_production_preflight(tmp_path):
    before = {p.name: edit.sha(p) for p in edit.DEMO.iterdir() if p.is_file()}
    receipt = edit.prepare(tmp_path / 'edit', 'a' * 40)
    plan = json.loads((tmp_path / 'edit/assembly.draft.json').read_text())
    assert plan['source_commit'] is None and plan['package_sha256'] is None
    assert plan['narration_cues'] == json.loads((edit.DEMO / 'narration-cues.json').read_text())
    vtt = (tmp_path / 'edit/narration.draft.vtt').read_text()
    assert all(cue['text'] in vtt for cue in plan['narration_cues'])
    assert all(asset['path'] is None for asset in plan['assets'].values())
    assert len(plan['assets']) == 18
    assert sum(s['duration'] for s in plan['segments']) == 170
    assert next(s for s in plan['segments'] if s['asset'] == 'native_ambient')['duration'] == 70
    assert 'MISSING_native_home' in (tmp_path / 'edit/picture-slots.edl').read_text()
    assert '<svg' in (tmp_path / 'edit/opening-title.svg').read_text()
    assert not receipt['produced_native_footage'] and not receipt['produced_narration']
    assert before == {p.name: edit.sha(p) for p in edit.DEMO.iterdir() if p.is_file()}
    spec = importlib.util.spec_from_file_location('production_renderer', edit.DEMO / 'render_demo.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    errors, _ = renderer.validate(plan)
    assert any('package' in error for error in errors)
    assert any('actual absolute local file is missing' in error for error in errors)


@pytest.mark.parametrize('change', ['script', 'order', 'existing-media'])
def test_unreconciled_changes_refused_before_writing(tmp_path, change):
    plan = json.loads((edit.DEMO / 'timeline.json').read_text())
    if change == 'script':
        plan['narration_cues'][0]['text'] = 'Unapproved replacement'
    elif change == 'order':
        plan['segments'].reverse()
    else:
        plan['assets']['manga_01']['path'] = str(Path('/existing/owned-art.png'))
    source = tmp_path / 'unreviewed.json'
    source.write_text(json.dumps(plan))
    with pytest.raises(ValueError):
        edit.prepare(tmp_path / 'output', 'a' * 40, source)
    assert not (tmp_path / 'output').exists()


def test_prior_edit_is_not_overwritten(tmp_path):
    output = tmp_path / 'edit'
    edit.prepare(output, 'a' * 40)
    marker = output / 'operator-notes.txt'
    marker.write_text('Keep this existing work')
    with pytest.raises(FileExistsError):
        edit.prepare(output, 'b' * 40)
    assert marker.read_text() == 'Keep this existing work'


def test_non_drop_timecode_boundaries():
    assert edit.timecode(70) == '00:01:10:00'
    assert edit.timecode(170) == '00:02:50:00'
    assert edit.timecode(1 / 30) == '00:00:00:01'
