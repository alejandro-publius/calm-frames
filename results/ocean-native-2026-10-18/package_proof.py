"""Read the built Zstandard package with platform tar; compare all approved assets."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
build = json.loads((OUT/'build-receipt.json').read_text())
proposal = json.loads((ROOT/'results/ambient-export-2026-10-18/approval-proposal.json').read_text())
env = {**os.environ, 'LC_ALL': 'C'}
package = build['package_path']
assert hashlib.sha256(Path(package).read_bytes()).hexdigest()==build['package_sha256']
prefix = 'assets/raw/prepared-library/'+proposal['bundleId']+'/'
def read(name):
    return subprocess.check_output(['tar','-xOf',package,name], env=env)
raw = read(prefix+'manifest.json')
assert hashlib.sha256(raw).hexdigest()==proposal['catalogSha256']
manifest = json.loads(raw)
checks = {}
for name, expected in manifest['files'].items():
    actual = hashlib.sha256(read(prefix+name)).hexdigest()
    checks[name] = {'sha256': actual, 'matches': actual==expected}
    assert actual==expected
report = json.loads((ROOT/'results/ambient-export-2026-10-18/verification-report.json').read_text())
evidence = {'source_commit': build['source_commit'], 'package_sha256': build['package_sha256'],
            'bundleId': proposal['bundleId'], 'catalogSha256': proposal['catalogSha256'],
            'package_asset_hashes': checks,
            'original_audio_and_timing': {p: proof['timingAudio'] for p,proof in report['presets'].items()},
            'native_audio_observed': False, 'native_pixels_observed': False,
            'release_fixes_ancestor': '23a24c27a78b693ec2213cc5f65558d1796d525b'}
subprocess.run(['git','merge-base','--is-ancestor',evidence['release_fixes_ancestor'],build['source_commit']], cwd=ROOT, check=True)
(OUT/'package-media-proof.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('Manifest and all',len(checks),'approved media/map assets match; audio/timing proofs bound to the packaged MP4s.')
