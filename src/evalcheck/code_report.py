"""Render static-code findings without executing the inspected source."""
import html
from pathlib import Path
from .code_scan import RULES
from .locales import locale_script, language, tr


def write_code_report(results,path,*,lang="en"):
    language(lang)
    e=html.escape
    def T(message):
        import re
        if lang=='ko':
            m=re.fullmatch(r'cell (\d+) · line (\d+)',message)
            if m:return tr('cell {cell} · line {line}',lang,cell=m[1],line=m[2])
            m=re.fullmatch(r'line (\d+)',message)
            if m:return tr('line {line}',lang,line=m[1])
        return tr(message,lang)
    findings=[f for r in results for f in r['findings']]
    cards=[]
    for f in findings:
        loc=f"cell {f['cell']} · line {f['line']}" if f['cell'] is not None else f"line {f['line']}"
        origin=f['origin'];orig=f"cell {origin['cell']} · line {origin['line']}" if origin['cell'] is not None else f"line {origin['line']}"
        cards.append(f'''<article><div class="tag">{e(f['rule'])} · <span data-raw>{e(f['path'])}</span> · {e(T(loc))}</div><h2>{e(T(f['title']))}</h2><div class="flow"><section><small>Origin · {e(T(orig))}</small><pre>{e(origin['code'])}</pre></section><section><small>Observed use · {e(T(loc))}</small><pre>{e(f['code'])}</pre></section></div><p>{e(T(f['suggestion']))}</p><p class="muted">{e(T(f['explanation']))}</p><a href="{e(f['reference'],quote=True)}" rel="noopener noreferrer">Primary documentation ↗</a></article>''')
    coverage=[]
    for r in results:
        notes=''.join(f"<li>{e(T(n['kind']))}: {e(T(n['message']))} (cell {e(str(n['cell']))}, line {e(str(n['line']))})</li>" for n in r['coverage']['notes'])
        coverage.append(f"<details><summary><span data-raw>{e(r['path'])}</span> · {e(T(r['status']))} · {r['coverage']['analyzed_statements']} statements</summary><ul>{notes or '<li>No additional coverage notes.</li>'}</ul></details>")
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvalCheck · Notebook code evidence</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b0e14;color:#edf0f7;font:15px/1.6 system-ui,sans-serif}.wrap{max-width:1100px;margin:auto;padding:32px 24px 60px}.brand,.tag,a{color:#c4f56b}.brand{font-size:21px;font-weight:750}.tag,small{font:12px/1.6 ui-monospace,monospace}h1{font-size:clamp(30px,5vw,48px);letter-spacing:-1.4px;line-height:1.13}h2{font-size:19px}p,.muted,small{color:#a6b0c2}.stats{display:flex;gap:28px;margin:25px 0}.stats strong{font-size:34px;display:block}.banner{padding:18px;border:1px solid #73613d;border-radius:10px;background:#30281b;color:#f5ce77}article,details{border:1px solid #273041;background:#121722;border-radius:12px;padding:21px;margin:17px 0}.flow{display:grid;grid-template-columns:1fr 1fr;gap:12px}.flow section{min-width:0;background:#0b0e14;border:1px solid #273041;border-radius:8px;padding:15px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.7 ui-monospace,monospace;margin:12px 0 0}summary{cursor:pointer;font-weight:600}.muted{font-size:12px}li{margin:8px 0;overflow-wrap:anywhere}.tag{overflow-wrap:anywhere}@media(max-width:650px){.wrap{padding:24px 18px}.flow{grid-template-columns:1fr}.stats{gap:16px}.stats strong{font-size:28px}}
</style></head><body><main class="wrap"><div class="brand">evalcheck / code evidence</div><h1>Find the line behind<br>the evaluation risk.</h1><p>AST + scoped data-flow analysis for Python and Jupyter notebooks. Target code is never executed.</p><div class="stats"><div><strong>__FILES__</strong>files scanned</div><div><strong>__FINDINGS__</strong>findings to review</div><div><strong>__PARTIAL__</strong>files with scope notes</div></div><div class="banner">Static patterns are review evidence. Function bodies, control flow, custom helpers and notebook execution order can fall outside analysis. No findings does not certify a leakage-free model.</div>__CARDS__<h2>Coverage and abstentions</h2>__COVERAGE__</main></body></html>'''
    substitutions={'__FILES__':str(len(results)),'__FINDINGS__':str(len(findings)),
        '__PARTIAL__':str(sum(bool(r['coverage']['notes']) for r in results)),
        '__CARDS__':''.join(cards) or '<article>No supported risk patterns found. Review the coverage notes below.</article>',
        '__COVERAGE__':''.join(coverage)}
    for key,value in substitutions.items():page=page.replace(key,value)
    page=page.replace('<html lang="en">',f'<html lang="{lang}">').replace('</body>', '<script>'+locale_script(lang)+'</script></body>')
    Path(path).write_text(page,encoding='utf-8')
