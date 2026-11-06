/* Dependency-free DOM-contract checks, NOT a browser/layout/accessibility test.
   Run: node tests/report_harness.cjs examples/demo/report.html */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2]||'examples/demo/report.html','utf8');
const payload=JSON.parse(html.match(/<script id="audit-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const script=[...html.matchAll(/<script>\s*([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(s=>s.includes('const data=JSON.parse')); 
class Element{
  constructor(tag='div'){this.tag=tag;this.children=[];this.events={};this.style={};this.value='';this.textContent='';this.classList={add:()=>{}};}
  append(...nodes){this.children.push(...nodes)}
  replaceChildren(...nodes){this.children=[...nodes]}
  setAttribute(name,value){this[name]=value}
  addEventListener(name,fn){this.events[name]=fn}
  click(){this.clicked=true}
}
function run(data){
  const ids={};for(const match of html.matchAll(/\bid="([\w-]+)"/g))ids[match[1]]=new Element();
  ids['audit-data'].textContent=JSON.stringify(data);ids.kind.value=ids.severity.value='all';
  let exported=false;
  const ctx={window:{},document:{getElementById:id=>ids[id],createElement:tag=>new Element(tag)},Blob,URL:{createObjectURL:()=>{exported=true;return 'blob:local'},revokeObjectURL:()=>{}},setTimeout:fn=>fn()};
  vm.runInNewContext(script,ctx);return {ids,exported:()=>exported};
}
const {ids,exported}=run(payload);
assert.equal(ids.findings.children.length,7);
ids.kind.value='label_conflict';ids.kind.events.input();assert.equal(ids.findings.children.length,1);
assert.match(ids.count.textContent,/1 of 7/);
ids.search.value='nothing-matches-this';ids.search.events.input();assert.equal(ids.findings.children[0].textContent,'No findings match these filters.');
ids.search.value='';ids.kind.value='all';ids.severity.value='error';ids.severity.events.input();assert.match(ids.count.textContent,/5 of 7/);
ids.download.onclick();assert.equal(exported(),true);
const many=structuredClone(payload);many.findings=Array.from({length:61},(_,i)=>({...payload.findings[0],id:`F${i}`}));
const paged=run(many).ids;assert.equal(paged.findings.children.length,25);assert.equal(paged.prev.disabled,true);paged.next.onclick();assert.equal(paged.page.textContent,'Page 2 / 3');paged.next.onclick();assert.equal(paged.findings.children.length,11);assert.equal(paged.next.disabled,true);paged.prev.onclick();assert.equal(paged.findings.children.length,25);
const empty=structuredClone(payload);empty.findings=[];empty.status='no_findings';assert.match(run(empty).ids.status.textContent,/No findings/);
const incomplete=structuredClone(payload);incomplete.status='incomplete';incomplete.coverage.near_search_complete=false;assert.match(run(incomplete).ids.coverage.textContent,/INCOMPLETE/);
console.log('Passed 8 report DOM-contract scenarios: render, filter, empty search, severity, export, pagination, empty audit, incomplete audit. Browser layout is not covered.');
