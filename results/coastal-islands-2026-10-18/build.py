"""One authorized build; retain exact source/input/package identity, no installation."""
import datetime
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not (OUT/'build-receipt.json').exists(), 'This build slot was already used.'
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
files = subprocess.check_output(['git', 'ls-files', 'app'], cwd=ROOT, text=True).splitlines()
files += subprocess.check_output(['git', 'ls-files', '--others', '--ignored', '--exclude-standard', 'app/src'], cwd=ROOT, text=True).splitlines()
inputs = {f: sha(ROOT/f) for f in files if (ROOT/f).is_file()}
(OUT/'app-inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
receipt = {'source_commit': source, 'build_count': 1, 'build_start_utc': now(), 'app_inputs': len(inputs),
           'command': 'npm run build:debug', 'visual_audio_acceptance': False}
(OUT/'build-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
with (OUT/'build.log').open('w') as log:
    result = subprocess.run(['npm', 'run', 'build:debug'], cwd=ROOT/'app', stdout=log, stderr=subprocess.STDOUT)
receipt.update(build_exit=result.returncode, build_end_utc=now(),
               changed_inputs=[f for f,h in inputs.items() if not (ROOT/f).is_file() or sha(ROOT/f)!=h])
if result.returncode == 0:
    package = ROOT/'build/release/coastal-islands-2026-10-18/calm-frames-coastal-islands-aarch64-debug.vpkg'
    package.parent.mkdir(parents=True, exist_ok=True)
    assert not package.exists()
    shutil.copy2(ROOT/'app/build/aarch64-debug/calm-frames-app_aarch64.vpkg', package)
    receipt.update(package_path=str(package), package_sha256=sha(package))
(OUT/'build-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2), flush=True)
raise SystemExit(result.returncode)
