"""Browser bridge. Only our engine is executed; target notebooks are parsed as AST.

Called with JSON via a Python global, never interpolated into executable code.
No HTTP calls are made by this bridge. Files live only in WebAssembly memory.
"""
import json
import tempfile
from pathlib import Path
from evalcheck import AuditConfig, audit
from evalcheck.io import load_records
from evalcheck.code_scan import scan_source, scan_notebook, to_sarif
from evalcheck.code_report import write_code_report
from evalcheck.report import write_report
from evalcheck.locales import language, localize_error

TEMP_ROOT=Path(tempfile.gettempdir())


def inputs(request):
    items=request.get('files',[])
    if not isinstance(items,list) or not 1<=len(items)<=10:raise ValueError('select 1–10 files')
    if any(not isinstance(f.get('name'),str) or not isinstance(f.get('text'),str) for f in items):raise ValueError('files require string name and text')
    if sum(len(f['text'].encode('utf-8')) for f in items)>4_000_000:raise ValueError('combined input exceeds 4 MB browser limit')
    return items


def handle_request(request):
    mode=request.get('mode')
    lang=language(request.get('lang','en'))
    if mode=='render':
        result=request['result']
        path=TEMP_ROOT/'browser-render.html'
        if result['kind']=='code':write_code_report(result['files'],path,lang=lang)
        elif result['kind']=='data':write_report(result['audit'],path,lang=lang)
        else:raise ValueError('unknown browser mode')
        return {'kind':'render','report_html':Path(path).read_text(encoding='utf-8')}
    files=inputs(request)
    if mode=='code':
        results=[]
        for item in files:
            name=Path(item['name']).name
            if name.endswith('.ipynb'):result=scan_notebook(json.loads(item['text']),path=name)
            elif name.endswith('.py'):result=scan_source(item['text'],path=name)
            else:raise ValueError('code mode accepts .py or .ipynb')
            results.append(result)
        write_code_report(results,TEMP_ROOT/'browser-code-report.html',lang=lang)
        return {'kind':'code','files':results,'findings':[f for result in results for f in result['findings']],
            'sarif':to_sarif(results),'report_html':Path(TEMP_ROOT/'browser-code-report.html').read_text(encoding='utf-8')}
    if mode in {'inspect','data'}:
        if len(files)!=2:raise ValueError('dataset mode needs exactly two files: train, then test')
        parts={}
        for i,item in enumerate(files):
            suffix=Path(item['name']).suffix.lower()
            if suffix not in {'.csv','.jsonl'}:raise ValueError('dataset mode accepts CSV and JSONL')
            path=TEMP_ROOT/f'browser-input-{i}{suffix}'
            path.write_text(item['text'],encoding='utf-8')
            rows=load_records(path)
            if not rows or len(rows)>5000:raise ValueError('each browser input must contain 1–5,000 records')
            parts['train' if i==0 else 'test']=rows
            path.unlink()
        common=sorted(set.intersection(*(set.intersection(*(set(row) for row in rows)) for rows in parts.values())))
        if mode=='inspect':return {'kind':'inspect','columns':common,'sizes':{k:len(v) for k,v in parts.items()}}
        config=request.get('config',{})
        result=audit(parts,AuditConfig(text=config.get('text','text'),label=config.get('label') or None,
            group=config.get('group') or None,id_column=config.get('id_column') or None,
            threshold=float(config.get('threshold',.8)),max_candidates=200000))
        write_report(result,TEMP_ROOT/'browser-data-report.html',lang=lang)
        return {'kind':'data','audit':result,'findings':result['findings'],
            'report_html':Path(TEMP_ROOT/'browser-data-report.html').read_text(encoding='utf-8')}
    raise ValueError('unknown browser mode')


def dispatch_request(request):
    try:return handle_request(request)
    except (ValueError, OSError, KeyError, TypeError) as error:
        return {'kind':'error','canonical':str(error),'message':localize_error(str(error),request.get('lang','en'))}
