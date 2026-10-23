import subprocess,json,hashlib,datetime
from pathlib import Path
r=Path('/Users/alexvintera/Documents/Codex/2026-10-15/task/calm-frames-creator-editions');d=Path('/Users/alexvintera/Documents/Codex/2026-10-15/task/scene-bridge-native');b=json.loads((d/'build-receipt.json').read_text());inputs=json.loads((d/'app-inputs.json').read_text())
assert b['build_exit']==0 and not b['changed_inputs']
assert all(hashlib.sha256((r/f).read_bytes()).hexdigest()==h for f,h in inputs.items())
p=Path(b['package_path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==b['package_sha256']
out={'source_commit':b['source_commit'],'package_path':str(p),'package_sha256':b['package_sha256'],'install_count':1,'inputs_matched':len(inputs),'commands':[]}
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(args):
 start=now();x=subprocess.run(['vega',*args],capture_output=True,text=True,timeout=45);row={'args':args,'start_utc':start,'end_utc':now(),'exit':x.returncode,'output':x.stdout+x.stderr};out['commands'].append(row);(d/'install-receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(row['output'],flush=True);assert x.returncode==0 and 'FAILED' not in row['output'];return row['output']
run(['device','run-cmd','--device','VirtualDevice','--command','vlcm terminate-app --force --pkg-id io.github.alejandropublius.calmframes'])
run(['device','install-app','--device','VirtualDevice','--packagePath',str(p),'--buildType','Debug'])
h=run(['device','run-cmd','--device','VirtualDevice','--command','sha256sum /tmp/'+p.name]);assert b['package_sha256'] in h;out['device_copy_sha256_matches']=True
run(['device','run-cmd','--device','VirtualDevice','--command','vmsgr send pkg://io.github.alejandropublius.calmframes.main'])
a=run(['device','running-apps','--device','VirtualDevice']);out['running_confirmed']='io.github.alejandropublius.calmframes.main' in a;assert out['running_confirmed'];(d/'install-receipt.json').write_text(json.dumps(out,indent=2)+'\n')
