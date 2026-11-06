"""Create the standalone browser app with the identical Python engine embedded."""
from pathlib import Path
import json
import hashlib
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'src'))
from evalcheck.locales import locale_script

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent
safe=lambda value:json.dumps(value,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
bundle={p.name:p.read_text(encoding='utf-8') for p in (ROOT/'src/evalcheck').glob('*') if p.suffix in {'.py','.html','.js'}}
worker=(BASE/'worker-template.js').read_text().replace('__PYTHON_BUNDLE__',safe(bundle)).replace('__BRIDGE_SOURCE__',safe((BASE/'bridge.py').read_text()))
presets={
 'leaky_notebook':{'mode':'code','files':[{'name':'leaky.ipynb','text':(ROOT/'examples/notebooks/leaky.ipynb').read_text()}]},
 'fixed_notebook':{'mode':'code','files':[{'name':'fixed.ipynb','text':(ROOT/'examples/notebooks/fixed.ipynb').read_text()}]},
 'public_data':{'mode':'data','files':[{'name':f'{name}.jsonl','text':(ROOT/f'examples/uci_sentiment/results/row-random/{name}.jsonl').read_text()} for name in ['train','test']]},
 'synthetic_data':{'mode':'data','files':[{'name':f'{name}.jsonl','text':(ROOT/f'examples/demo/{name}.jsonl').read_text()} for name in ['train','test']]},
}
text=(BASE/'template.html').read_text().replace('__WORKER_SOURCE__',safe(worker)).replace('__PRESETS__',safe(presets)).replace('__LOCALE_SCRIPT__',locale_script(interactive=True))
(BASE/'index.html').write_text(text,encoding='utf-8')
(BASE/'dist').mkdir(exist_ok=True)
(BASE/'dist/index.html').write_text(text,encoding='utf-8')
(BASE/'build-manifest.json').write_text(json.dumps({'engine_files':{name:hashlib.sha256(value.encode()).hexdigest() for name,value in bundle.items()},'pyodide':'0.29.3','worker_sha256':hashlib.sha256(worker.encode()).hexdigest()},indent=2)+'\n')
print('Built browser app:',len(text.encode()),'bytes; Python engine embedded, runtime fetched on first scan.')
