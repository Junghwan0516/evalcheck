/* Pinned bootstrap; user file content is never used as executable Python. */
const bundle=__PYTHON_BUNDLE__;
const bridge=__BRIDGE_SOURCE__;
let runtime;
async function ready(){
 if(!runtime){
  self.postMessage({type:'progress',message:'Loading the pinned Python WebAssembly runtime. Your files stay in this worker.'});
  importScripts('https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js');
  runtime=await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/'});
  runtime.FS.mkdirTree('/home/pyodide/evalcheck');
  for(const [name,text] of Object.entries(bundle))runtime.FS.writeFile('/home/pyodide/evalcheck/'+name,text);
  await runtime.runPythonAsync(bridge);
 }
 return runtime;
}
self.onmessage=async({data})=>{
 try{
  const py=await ready();
  self.postMessage({type:'progress',message:'Inspecting locally with the same Python engine as the CLI…'});
  py.globals.set('_evalcheck_request_json',JSON.stringify(data.request));
  const value=py.runPython('json.dumps(dispatch_request(json.loads(_evalcheck_request_json)), ensure_ascii=False, allow_nan=False)');
  py.globals.delete('_evalcheck_request_json');
  const parsed=JSON.parse(value);
  if(parsed.kind==='error')self.postMessage({type:'error',id:data.id,message:parsed.canonical||parsed.message});
  else self.postMessage({type:'result',id:data.id,value:parsed});
 }catch(error){self.postMessage({type:'error',id:data.id,message:String(error.message||error)});}
};
