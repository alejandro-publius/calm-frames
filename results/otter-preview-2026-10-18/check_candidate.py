"""Verify an isolated candidate copy and reject byte tampering; never activate it."""
import json
import shutil
import subprocess
from pathlib import Path
from pipeline.packaged_library import check_packaged_library

ROOT = Path.cwd()
OUT = ROOT/'results/otter-preview-2026-10-18'
source = ROOT/'build/otter-preview-2026-10-18/prepared-library'
target = ROOT/'build/otter-preview-2026-10-18/tamper-check'
assert not target.exists()
shutil.copytree(source,target)
manifest = json.loads((target/'catalog.json').read_text())
title = manifest['titles'][0]
node = '/Users/alexvintera/.local/share/fnm/node-versions/v22.23.2/installation/bin/node'
code = 'import {checkPreparedDirectory} from "./app/tools/check_prepared_library.mjs";checkPreparedDirectory(process.argv[1],{requireReports:true});'
def accepted():
    try:
        check_packaged_library(target,require_reports=True)
        py = True
    except (ValueError, OSError, RuntimeError):
        py = False
    js = subprocess.run([node,'--input-type=module','-e',code,str(target)],cwd=ROOT,capture_output=True).returncode==0
    return {'python':py,'node':js}
results = [{'case':'original','accepted':accepted()}]
assert all(results[0]['accepted'].values())
files = {'media':target/manifest['bundleId']/title['renditions']['wcag']['path'],
         'map':target/manifest['bundleId']/title['maps']['wcag']['path'],
         'report':target/'reports'/(title['verification']['reportSha256']+'.json')}
for name,p in files.items():
    original=p.read_bytes()
    try:
        p.write_bytes(original+b' ')
        result=accepted();assert not any(result.values())
        results.append({'case':name+' bytes changed','accepted':result})
    finally:
        p.write_bytes(original)
results.append({'case':'restored','accepted':accepted()})
assert all(results[-1]['accepted'].values())
(OUT/'tamper-results.json').write_text(json.dumps(results,indent=2)+'\n')
print('Both validators accept original/restored and reject changed media, map and report.')
