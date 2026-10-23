import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { checkAmbientReport, strictJson } from './ambient_report.mjs';
const fixture = () => JSON.parse(fs.readFileSync(new URL('../../pipeline/tests/fixtures/ambient-report.json', import.meta.url), 'utf8'));
const hash = (s, a='sha256') => createHash(a).update(s).digest('hex');
function refresh(data) {
  const {report,title}=data, binding=JSON.parse(report.inputBindingRaw);
  for (const [p,proof] of Object.entries(report.presets)) {
    const meta=JSON.parse(proof.metadataRaw);
    for (const group of ['ambientAnalysis','outputAnalysis']) for (const [q,entry] of Object.entries(proof[group])) {
      entry.sha256=hash(entry.raw); if (group==='outputAnalysis') meta.analysis[q]=entry.sha256;
    }
    proof.metadataRaw=JSON.stringify(meta);binding.metadataSha512[p]=hash(proof.metadataRaw,'sha512');
  }
  report.inputBindingRaw=JSON.stringify(binding);title.verification.checkedInputsSha256=hash(report.inputBindingRaw);
}
test('accepts distinct synthetic ambient report and rejects duplicate JSON',()=>{
  const {report,title}=fixture();checkAmbientReport(JSON.stringify(report),[title]);
  assert.throws(()=>strictJson('{"recipe":1,"recipe":2}'));
  assert.throws(()=>checkAmbientReport(JSON.stringify(report),[]));
});
for (const [field,value] of [['renditionSha256','f'.repeat(64)],['durationMs',10001],['renditionStartOffsetMs',1],['preset','broadcast'],['audioPreserved',false],['frameTimingPreserved',false],['ambientSha256','f'.repeat(64)],['intervals',[{startMs:501,endMs:2500}]],['version',true]]) {
  test(`rejects rebound metadata ${field}`,()=>{
    const data=fixture(),proof=data.report.presets.wcag,meta=JSON.parse(proof.metadataRaw);
    meta[field]=value;proof.metadataRaw=JSON.stringify(meta);refresh(data);
    assert.throws(()=>checkAmbientReport(JSON.stringify(data.report),[data.title]));
  });
}
for (const change of ['source','flags','thresholds','profile','failed']) test(`rejects rebound analysis ${change}`,()=>{
  const data=fixture(),entry=data.report.presets.wcag.outputAnalysis.wcag,raw=JSON.parse(entry.raw);
  if(change==='source')raw.source.sha256='e'.repeat(64);
  if(change==='flags')raw.segments=[{start_ms:0,end_ms:1}];
  if(change==='thresholds')raw.profile.room.seat_distance_in=96;
  if(change==='profile')raw.profile.name='broadcast';
  if(change==='failed')raw.summary.pass=false;
  entry.raw=JSON.stringify(raw);refresh(data);
  assert.throws(()=>checkAmbientReport(JSON.stringify(data.report),[data.title]));
});
for (const [field,value] of [['sourceEqualsOutput',false],['frameCount',0],['audioPacketCount',-1],['videoDurationRational','9'],['frameTimesSha256','wrong']]) test(`rejects missing timing/audio proof ${field}`,()=>{
  const data=fixture();data.report.presets.wcag.timingAudio[field]=value;
  assert.throws(()=>checkAmbientReport(JSON.stringify(data.report),[data.title]));
});
