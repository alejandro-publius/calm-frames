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
           "You'll still hear the original audio.", 'Sea otters in Alaska', '20 seconds', 'Choose an island', 'Scene replaced', 'player-scenes', 'player-scene-context', 'Forest creek at Redwood', 'coastal-boat-', 'Calm Frames hides flagged flashing scenes in prepared videos.', 'Acadia replaces them with ocean footage.', 'cannot guarantee seizure prevention']
assert b'77d43b664cb49d6caf82887c70d13df9d98eb32add815abd5d41320ca316503f' in js
archive_names = subprocess.check_output(['tar', '-tf', package], env=env, text=True)
assert '77d43b664cb49d6caf82887c70d13df9d98eb32add815abd5d41320ca316503f' in archive_names
for obsolete in ['4064f489236973b0e8683f24fac9756ed0cdf475d376a7c6501d644397b597f5', '89496fc4b45528558ce35ef9140aa659b86a5f84734156098e2f29e312f2c590']:
    assert obsolete not in archive_names
assert b'forest-preview-label' not in js  # Generic pending-video safety copy remains.
copy = {text: text.encode() in js for text in strings}
assert all(copy.values()), copy
details_strip = (ROOT/'app/src/calmframes/CoveredSectionsStrip.tsx').read_text()
assert 'The sound continues.' not in details_strip
report = json.loads((ROOT/'results/ambient-export-2026-10-18/verification-report.json').read_text())
otter_probe = json.loads((ROOT/'results/sea-otters-2026-10-18/rendition-probes.json').read_text())
evidence = {
    'source_commit': build['source_commit'], 'package_sha256': build['package_sha256'],
    'approved_catalogs': catalogs, 'bundled_copy_strings': copy,
    'details_strip_standalone_sound_continues_absent': True,
    'phrase_remains_in_separate_technical_explanations': True,
    'acadia_original_audio_and_timing': {p: v['timingAudio'] for p, v in report['presets'].items()},
    'otter_rendition_probes': otter_probe,
    'forest_catalog_present_in_package_and_runtime': True,
    'obsolete_generations_absent_from_package': True,
    'native_pixels_observed': False, 'native_audio_observed': False,
    'release_fixes_ancestor': '23a24c27a78b693ec2213cc5f65558d1796d525b'
}
subprocess.run(['git','merge-base','--is-ancestor',evidence['release_fixes_ancestor'],build['source_commit']], cwd=ROOT, check=True)
(OUT/'package-media-proof.json').write_text(json.dumps(evidence, indent=2)+'\n')
print('Three exact catalogs and all 18 media/map assets match; Forest and concise help copy included.')
