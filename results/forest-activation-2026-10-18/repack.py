"""Repair only stale staged media after one successful compile; gates remain strict."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess
root=Path(__file__).resolve().parents[2];out=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'build-receipt.json').read_text())
assert receipt['build_exit']==1 and not receipt['changed_inputs']
assert 'vega vtbuild exited with code 0' in (out/'build.log').read_text()
assert (out/'build.log').read_text().rstrip().endswith('Prepared library check failed: Prepared library exceeds its package budget.')
inputs=json.loads((out/'app-inputs.json').read_text());assert all(sha(root/p)==h for p,h in inputs.items())
source=root/'app/assets/raw/prepared-library';expected={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
recovery=root/'build/forest-activation-2026-10-18/package-recovery';assert not recovery.exists();recovery.mkdir(parents=True)
results=[]
for arch in ['armv7','aarch64','x86_64']:
 stage=root/f'app/build/private/vega/{arch}/Debug';media=stage/'assets/raw/prepared-library'
 before={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file() and media not in p.parents}
 media.rename(recovery/f'{arch}-stale-prepared-library');shutil.copytree(source,media)
 assert {str(p.relative_to(media)):sha(p) for p in media.rglob('*') if p.is_file()}==expected
 destination=recovery/arch;destination.mkdir()
 cmd=['/Users/alexvintera/vega/sdk/vega-sdk/main/0.24.9914/bin/tools/vpt','pack',str(stage),'-n',f'calm-frames-app_{arch}','-d',str(destination),'--validate']
 with (out/f'repack-{arch}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 after={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file() and media not in p.parents};assert before==after
 package=destination/f'calm-frames-app_{arch}.vpkg';shutil.copy2(package,root/f'app/build/{arch}-debug'/package.name)
 results.append({'architecture':arch,'package_sha256':sha(package),'nonmedia_staged_files_unchanged':len(before)})
with (out/'post-recovery-package-gates.log').open('w') as log:subprocess.run(['node','app/tools/check_prepared_library.mjs','--packages','Debug','--require-reports'],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
package=root/'build/release/forest-activation-2026-10-18/calm-frames-three-islands-aarch64-debug.vpkg';package.parent.mkdir(parents=True,exist_ok=True);assert not package.exists();shutil.copy2(recovery/'aarch64/calm-frames-app_aarch64.vpkg',package)
receipt.update(package_path=str(package),package_sha256=sha(package),package_recovery_exit=0,package_recovery_count=1,package_recovery='One compile succeeded; postbuild gate rejected stale incremental media. Replaced only staged media namespace, then repackaged with installed vpt and reran all strict package gates.',package_recovery_architectures=results,package_recovery_end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(out/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
