/* Pure Node/WebAssembly engine parity check. No browser automation.
   npm install --no-save pyodide@0.29.3
   node tools/check_wasm.cjs */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {loadPyodide}=require(process.env.EVALCHECK_PYODIDE_MODULE||'pyodide');
const root=path.resolve(__dirname,'..');
(async()=>{
 const py=await loadPyodide();py.FS.mkdirTree('/home/pyodide/evalcheck');
 for(const name of fs.readdirSync(path.join(root,'src/evalcheck'))){if(/\.(py|html|js)$/.test(name))py.FS.writeFile('/home/pyodide/evalcheck/'+name,fs.readFileSync(path.join(root,'src/evalcheck',name),'utf8'));}
 py.runPython(fs.readFileSync(path.join(root,'web/bridge.py'),'utf8'));
 function call(request){py.globals.set('_request',JSON.stringify(request));return JSON.parse(py.runPython('json.dumps(handle_request(json.loads(_request)), ensure_ascii=False, allow_nan=False)'));}
 const cases=JSON.parse(fs.readFileSync(path.join(root,'benchmarks/notebooks/cases.json'),'utf8'));
 const native=JSON.parse(fs.readFileSync(path.join(root,'benchmarks/notebooks/results.json'),'utf8'));
 for(const c of cases){const got=call({mode:'code',files:[{name:c.id+'.py',text:c.source}]});const rules=[...new Set(got.findings.map(f=>f.rule))].sort();assert.deepEqual(rules,native.cases_detail.find(n=>n.id===c.id).detected_rules,c.id);}
 const files=['train','test'].map(name=>({name:name+'.jsonl',text:fs.readFileSync(path.join(root,'examples/uci_sentiment/results/row-random',name+'.jsonl'),'utf8')}));
 const inspect=call({mode:'inspect',files});assert.deepEqual(inspect.sizes,{train:2400,test:600});
 const data=call({mode:'data',files,config:{text:'text',label:'label',id_column:'source_id',threshold:.8}});
 const expected=JSON.parse(fs.readFileSync(path.join(root,'examples/uci_sentiment/results/row-random/audit.json'),'utf8'));
 assert.deepEqual(data.audit.summary,expected.summary);assert.equal(data.audit.coverage.near_search_complete,true);
 for(const name of ['leaky','fixed']){const result=call({mode:'code',files:[{name:name+'.ipynb',text:fs.readFileSync(path.join(root,'examples/notebooks',name+'.ipynb'),'utf8')}]});assert.equal(result.findings.length,name==='leaky'?2:0);}
 const korean=call({mode:'render',lang:'ko',result:data});assert.ok(korean.report_html.includes('<html lang="ko">'));
 console.log(JSON.stringify({pyodide:'0.29.3',python:py.runPython('import sys;sys.version'),'authored_cases_parity':cases.length,'public_data_rows':data.audit.summary.rows,'public_data_findings':data.audit.summary.findings,'notebook_presets_passed':2},null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
