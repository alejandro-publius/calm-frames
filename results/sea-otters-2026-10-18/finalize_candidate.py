"""Collect exact candidate identities and check a disposable combined namespace."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from pipeline.packaged_library import check_packaged_library
root=Path.cwd();base=root/'build/sea-otters-2026-10-18';out=root/'results/sea-otters-2026-10-18';candidate=base/'prepared-library'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=check_packaged_library(candidate,require_reports=True)
catalog=json.loads((candidate/'catalog.json').read_text());title=catalog['titles'][0]
report=candidate/'reports'/(title['verification']['reportSha256']+'.json')
r=json.loads(report.read_text())
shutil.copy2(candidate/'catalog.json',out/'candidate-catalog.json');shutil.copy2(report,out/'verification-report.json')
combined=base/'replacement-library';assert not combined.exists()
old='4bab8d81f779d7cf0eac3f5e2fe5372e88e95088fb068680818b28865dc6ad13'
shutil.copytree(root/'app/assets/raw/prepared-library',combined,ignore=lambda directory,names: [old] if Path(directory)==root/'app/assets/raw/prepared-library' else [])
# Remove only unreferenced report copies from this fresh staging directory.
refs={t['verification']['reportSha256']+'.json' for f in combined.glob('*/manifest.json') for t in json.loads(f.read_text())['titles']}
for f in (combined/'reports').iterdir():
 if f.name not in refs:f.unlink()
shutil.copytree(candidate/catalog['bundleId'],combined/catalog['bundleId'])
shutil.copy2(report,combined/'reports'/report.name)
node='/Users/alexvintera/.local/share/fnm/node-versions/v22.23.2/installation/bin/node'
code='import {checkPreparedDirectory} from "./app/tools/check_prepared_library.mjs"; console.log(JSON.stringify(checkPreparedDirectory(process.argv[1],{requireReports:true}),null,2));'
p=subprocess.run([node,'--input-type=module','-e',code,str(combined)],capture_output=True,text=True);(out/'combined-delivery-check.json').write_text(p.stdout);assert p.returncode==0,p.stderr
plans={}
for f in (base/'raft-work/titles'/title['sourceSha256']/'plans').glob('*.json'):
 d=json.loads(f.read_text());plans[f.stem]={'totalCoveredMs':d['total_covered_ms'],'intervals':[(i['start_ms'],i['end_ms']) for i in d['intervals']]}
proposal={'approved':False,'title':'Sea otters in Alaska','species':'Enhydra lutris','location':'Unalaska/Dutch Harbor, Alaska (ocean harbor)','durationMs':title['durationMs'],'sourceSha256':title['sourceSha256'],'bundleId':catalog['bundleId'],'catalogSha256':h(candidate/'catalog.json'),'publicKeyFingerprint':'00c1bd272c4f3068626ddf6a828ae3f52ca32eae76dab35308d5d6687270b881','reportSha256':h(report),'verificationOutcome':r['outcome'],'verificationChecks':len(r['checks']),'allChecksPassed':r['passed'],'coverPlans':plans,'candidateBytes':sum(p.stat().st_size for p in candidate.rglob('*') if p.is_file()),'excludedFromFreshNamespace':[old],'originalNamespacePreserved':True,'allGenerationsAdditionBytes':83714050,'replacementNamespace':str(combined),'combinedBytes':sum(p.stat().st_size for p in combined.rglob('*') if p.is_file()),'unchangedLimitBytes':67108864,'output':str(candidate),'requiredScope':'Approve only this exact sea-otter catalog/bundle under the existing project signer, replace the wrong river-otter shelf selection, use a fresh namespace omitting only obsolete pre-ocean Acadia bundle4bab8d81f779d7cf0eac3f5e2fe5372e88e95088fb068680818b28865dc6ad13 while preserving the original directory for concurrent builds and preserving current ocean Acadia byte-for-byte, update honest runtime/NOAA credit. No broad signer trust or ambient registration. Following approval, run gates and one authorized native build/install and bounded non-capture checks. No activation or native testing has occurred.'}
(out/'approval-proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
(out/'python-catalog-check.json').write_text(json.dumps(check,indent=2)+'\n')
print(json.dumps(proposal,indent=2))
