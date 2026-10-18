import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { approvedCatalogModule } from './approved_prepared_libraries.mjs';
import { bakedAmbientModule } from './approved_baked_ambient.mjs';
const evidence=new URL('../../results/ambient-export-2026-10-18/',import.meta.url);
function fixture(t) {
  const app=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'ambient-approval-test-')));
  t.after(()=>fs.rmSync(app,{recursive:true,force:true}));
  const info=JSON.parse(fs.readFileSync(new URL('approval-proposal.json',evidence),'utf8'));
  const write=(name,text)=>{const file=path.join(app,name);fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,text);};
  // Test-only approval data in an isolated temporary directory; never the application's registry.
  const registry={version:1,catalogs:[{bundleId:info.bundleId,catalogSha256:info.catalogSha256,publicKeyFingerprint:info.publicKeyFingerprint,consumer:true,label:'Test only',approvalReference:'Synthetic approval rehearsal; not owner authorization'}]};
  write('config/approved-prepared-libraries.json',JSON.stringify(registry));
  write(`assets/raw/prepared-library/${info.bundleId}/manifest.json`,fs.readFileSync(new URL('catalog.json',evidence)));
  write(`assets/raw/prepared-library/reports/${info.reportSha256}.json`,fs.readFileSync(new URL('verification-report.json',evidence)));
  write('src/calmframes/approvedPreparedCatalogs.ts',approvedCatalogModule(app).module);
  return {app,info,write,registry};
}
test('an exact simulated approval produces three per-preset bindings without writing the app',t=>{
  const {app,info}=fixture(t), text=bakedAmbientModule(app);
  for(const checksum of Object.values(info.metadataSha512)) assert.ok(text.includes(checksum));
  assert.equal((text.match(/"sha512":/g)??[]).length,3);
});
test('removing simulated catalog approval also removes all ambient registrations',t=>{
  const {app,write}=fixture(t);write('config/approved-prepared-libraries.json',JSON.stringify({version:1,catalogs:[]}));
  write('src/calmframes/approvedPreparedCatalogs.ts',approvedCatalogModule(app).module);
  assert.ok(bakedAmbientModule(app).includes('[];'));
  assert.equal((bakedAmbientModule(app).match(/"sha512":/g)??[]).length,0);
});
for(const change of ['report','catalog','key','missing-report']) test(`refuses ${change} before generation`,t=>{
  const {app,info,write,registry}=fixture(t);
  const report=`assets/raw/prepared-library/reports/${info.reportSha256}.json`;
  if(change==='report')write(report,'{}');
  if(change==='missing-report')fs.unlinkSync(path.join(app,report));
  if(change==='catalog')write(`assets/raw/prepared-library/${info.bundleId}/manifest.json`,'{}');
  if(change==='key'){registry.catalogs[0].publicKeyFingerprint='f'.repeat(64);write('config/approved-prepared-libraries.json',JSON.stringify(registry));}
  assert.throws(()=>bakedAmbientModule(app));
});
