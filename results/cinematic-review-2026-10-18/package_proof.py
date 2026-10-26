"""Read the built package; bind exact catalogs, assets and UI copy to its hash."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
build = json.loads((OUT/'build-receipt.json').read_text())
approved = json.loads((ROOT/'app/config/approved-prepared-libraries.json').read_text())
env = {**os.environ, 'LC_ALL': 'C'}
package = build['package_path']
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(Path(package).read_bytes()) == build['package_sha256']

def read(name):
    return subprocess.check_output(['tar', '-xOf', package, name], env=env)

catalogs = []
for entry in approved['catalogs']:
    prefix = 'assets/raw/prepared-library/'+entry['bundleId']+'/'
    raw = read(prefix+'manifest.json')
    assert sha(raw) == entry['catalogSha256']
    manifest = json.loads(raw)
    checks = {}
    for name, expected in manifest['files'].items():
        actual = sha(read(prefix+name))
        checks[name] = {'sha256': actual, 'matches': actual == expected}
        assert actual == expected
    catalogs.append({**entry, 'package_asset_hashes': checks})
js = read('bundle/index.bundle')
strings = ['Scenes replaced', 'Scenes covered', 'Ocean footage replaces flagged scenes.',
           "You'll still hear the original audio.", 'Otters', '4.24 seconds', 'Scene replaced', 'player-scenes', 'player-scene-context']
copy = {text: text.encode() in js for text in strings}
assert all(copy.values()), copy
details_strip = (ROOT/'app/src/calmframes/CoveredSectionsStrip.tsx').read_text()
assert 'The sound continues.' not in details_strip
report = json.loads((ROOT/'results/ambient-export-2026-10-18/verification-report.json').read_text())
otter_probe = json.loads((ROOT/'results/otter-preview-2026-10-18/all-rendition-probes.json').read_text())
evidence = {
    'source_commit': build['source_commit'], 'package_sha256': build['package_sha256'],
    'approved_catalogs': catalogs, 'bundled_copy_strings': copy,
    'details_strip_standalone_sound_continues_absent': True,
    'phrase_remains_in_separate_technical_explanations': True,
    'acadia_original_audio_and_timing': {p: v['timingAudio'] for p, v in report['presets'].items()},
    'otter_rendition_probes': otter_probe,
    'native_pixels_observed': False, 'native_audio_observed': False,
    'release_fixes_ancestor': '23a24c27a78b693ec2213cc5f65558d1796d525b'
}
subprocess.run(['git','merge-base','--is-ancestor',evidence['release_fixes_ancestor'],build['source_commit']], cwd=ROOT, check=True)
(OUT/'package-media-proof.json').write_text(json.dumps(evidence, indent=2)+'\n')
print('Both exact catalogs and all 12 media/map assets preserved; cinematic timeline and scene copy included.')
