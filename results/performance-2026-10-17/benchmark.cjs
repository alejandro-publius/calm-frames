const fs=require('fs');const path=require('path');const {performance}=require('perf_hooks');
const root=path.resolve(process.argv[2] || 'app');
const ts=require(root+'/node_modules/typescript');
require.extensions['.ts']=(mod,file)=>mod._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,file);
const {verifyFlashMap}=require(root+'/src/calmframes/flashMap.ts');
const catalog=JSON.parse(require(root+'/src/calmframes/acadiaCatalog.ts').PACKAGED_LIBRARY_JSON);
const title=catalog.titles[0];const maps=Object.values(title.maps).map(x=>x.text);
const options={publicKeyBase64:catalog.publicKeyBase64,expectedSha256:title.sourceSha256,nowMs:Date.parse('2026-10-17T03:00:00Z')};
const times=[];for(let i=0;i<11;i++){const start=performance.now();for(const text of maps){const v=verifyFlashMap(text,options);if(!v.ok)throw Error(JSON.stringify(v));}times.push(performance.now()-start);}
console.log(JSON.stringify({runtime:process.version,platform:process.platform,arch:process.arch,method:'11 successive batches, each verifies the 3 exact compiled Acadia maps; first cold then 10 warm. Host Node, NOT Vega.',mapLengths:maps.map(x=>x.length),batchMs:times,firstMs:times[0],warmMedianMs:(()=>{const sorted=times.slice(1).sort((a,b)=>a-b);return (sorted[4]+sorted[5])/2;})()},null,2));
