import subprocess,json,hashlib,datetime,shutil
from pathlib import Path
r=Path('/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-creator-editions');d=Path('/Users/alexvintera/Documents/Codex/2026-10-15/task/scene-bridge-native')
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
files=subprocess.check_output(['git','ls-files','app'],cwd=r,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--ignored','--exclude-standard','app/src'],cwd=r,text=True).splitlines(); inputs={f:hashlib.sha256((r/f).read_bytes()).hexdigest() for f in files if (r/f).is_file()}
(d/'app-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
receipt={'source_commit':source,'build_count':1,'build_start_utc':now(),'app_inputs_including_existing_generated':len(inputs),'command':'npm run build:debug -- --config '+'/Users/alexvintera/Documents/Codex/2026-10-15/task/creator-editions-evidence/isolated-metro.config.cjs'}
with (d/'build.log').open('w') as out: p=subprocess.run(['npm','run','build:debug','--','--config','/Users/alexvintera/Documents/Codex/2026-10-15/task/creator-editions-evidence/isolated-metro.config.cjs'],cwd=r/'app',stdout=out,stderr=subprocess.STDOUT)
receipt.update(build_exit=p.returncode,build_end_utc=now(),changed_inputs=[f for f,h in inputs.items() if hashlib.sha256((r/f).read_bytes()).hexdigest()!=h])
if p.returncode==0:
 target=r/'build/release/scene-bridge-native-2026-10-18/calm-frames-bridge-fixture-aarch64-debug.vpkg';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/'app/build/aarch64-debug/calm-frames-app_aarch64.vpkg',target)
 receipt.update(package_path=str(target),package_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(d/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
raise SystemExit(p.returncode)
