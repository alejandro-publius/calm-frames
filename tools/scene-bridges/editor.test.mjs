import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import test from 'node:test';
const html=readFileSync(new URL('./editor.html',import.meta.url),'utf8');
const source=html.match(/<script>([\s\S]*?)<\/script>/)[1];
function editor(){
 const fields=new Map();const get=id=>{if(!fields.has(id))fields.set(id,{value:'',checked:false,hidden:false,addEventListener(type,fn){this[type]=fn;}});return fields.get(id);};
 let exports=0;
 const context={document:{getElementById:get,createElement:()=>({click(){exports++;}})},URL:{createObjectURL:()=> 'blob:local',revokeObjectURL(){}},Blob};
 vm.runInNewContext(source,context);
 for(const [id,value] of Object.entries({'title-id':'fixture','source':'a'.repeat(64),rendition:'b'.repeat(64),duration:'20000.75',offset:'0.25',start:'2000.25',end:'10000.75',text:'Test fixture: a card shows one.'}))get(id).value=value;
 get('fixture').checked=true;get('confirmed').checked=true;
 return {get,submit(){get('editor').submit({preventDefault(){}});},exports:()=>exports};
}
test('exports exact fractional identity and explicitly labeled authored fixture',()=>{const e=editor();e.submit();const d=JSON.parse(e.get('output').textContent);assert.equal(d.durationMs,20000.75);assert.equal(d.entries[0].startMs,2000.25);assert.equal(d.testFixture,true);assert.equal(d.authorConfirmed,true);assert.equal(e.exports(),1);});
for(const [name,id,value] of [['short cover','end','7000'],['out of bounds','end','21000'],['invalid hash','source','bad'],['markup','text','<b>text</b>'],['too long','text','a'.repeat(121)],['reading budget','text',Array(20).fill('word').join(' ')]])test(name,()=>{const e=editor();e.get(id).value=value;e.submit();assert.equal(e.exports(),0);assert.equal(e.get('output').hidden,true);});
test('authorship must be confirmed; no stale draft on failure',()=>{const e=editor();e.submit();e.get('confirmed').checked=false;e.submit();assert.equal(e.exports(),1);assert.equal(e.get('output').hidden,true);});
