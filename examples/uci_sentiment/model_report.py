"""Standard-library, standalone presentation of the recorded model comparison."""
import html
import json
from pathlib import Path
import sys


def write_model_report(result, path):
    baseline=result['baseline'];selected=result['selected_model']
    a=result['test'][baseline];b=result['test'][selected]
    low,high=result['uncertainty']['macro_f1_delta_95_percentile_interval']
    e=html.escape
    if low > 0:
        verdict='Positive conditional evidence on this split'
        evidence='The interval lies above zero for these fitted models and this test split. Independent replication is still needed.'
    elif high < 0:
        verdict='Negative conditional evidence on this split'
        evidence='The interval lies below zero: the selected model performed worse under this comparison.'
    else:
        verdict='Inconclusive improvement evidence'
        evidence='The interval includes zero; a clear positive difference has not been established.'
    direction='higher' if b['macro_f1']>a['macro_f1'] else 'lower' if b['macro_f1']<a['macro_f1'] else 'identical'

    table_rows=''
    for key,label,fmt in [('macro_f1','Macro-F1','.4f'),('accuracy','Accuracy','.2%')]:
        difference=f"{(b[key]-a[key])*100:+.2f} pp" if key=='accuracy' else f"{b[key]-a[key]:+.4f}"
        table_rows+=f'<tr><th>{label}</th><td>{format(a[key],fmt)}</td><td>{format(b[key],fmt)}</td><td>{difference}</td></tr>' 
    dev_rows=''.join(f'<tr><th>{e(name)}</th><td>{score["macro_f1"]:.4f}</td><td>{"Selected" if name==selected else "Baseline" if name==baseline else "Development only"}</td></tr>'
        for name,score in sorted(result['development'].items()))
    limits=''.join(f'<li>{e(line)}</li>' for line in result['limitations'])
    text='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvalCheck · Model comparison</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b0e14;color:#edf0f7;font:16px/1.6 system-ui,sans-serif}.wrap{max-width:1050px;margin:auto;padding:36px 24px 60px}.brand{color:#c4f56b;font-weight:750;font-size:20px}h1{font-size:clamp(30px,5vw,48px);line-height:1.15;letter-spacing:-1.5px;margin:36px 0 15px}h2{font-size:20px}p,li{color:#a6b0c2}.status{padding:18px 22px;background:#30281b;border:1px solid #73613d;border-radius:10px;color:#f5ce77;margin:24px 0}.status strong{display:block}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:24px 0}.card,.panel{background:#121722;border:1px solid #273041;border-radius:12px;padding:22px}.card span{display:block;color:#a6b0c2;font-size:13px}.card strong{display:block;font-size:33px;margin:8px 0}.card small{color:#a6b0c2}.panel{margin:20px 0}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:13px 10px;text-align:left;border-bottom:1px solid #273041}th{font-weight:600}td{font-variant-numeric:tabular-nums}a{color:#c4f56b}.muted{font-size:13px;color:#a6b0c2}code{font-size:12px;overflow-wrap:anywhere}footer{margin-top:32px;font-size:12px;overflow-wrap:anywhere;color:#a6b0c2}.table-wrap{overflow-x:auto}li{margin:10px 0}@media(max-width:650px){.wrap{padding:24px 18px}.cards{grid-template-columns:1fr}.card{padding:17px}.card strong{font-size:28px}.panel{padding:16px}table{font-size:12px}th,td{padding:10px 6px}h1{letter-spacing:-1px}}
</style></head><body><main class="wrap"><div class="brand">evalcheck / model evidence</div><h1>Measured model comparison.</h1><p>Same held-out records. Development-only candidate selection. Uncertainty reported alongside the score.</p>
__STATUS__
<div class="cards">__CARDS__</div><section class="panel"><h2>Identical 600-record test set</h2><div class="table-wrap"><table><thead><tr><th>Metric</th><th>Word baseline</th><th>Selected model</th><th>Difference</th></tr></thead><tbody>__TABLE__</tbody></table></div><p class="muted">Macro-F1 is on a 0–1 scale. The accuracy difference is an absolute percentage-point change.</p><p>Paired component-bootstrap 95% percentile interval for the Macro-F1 difference: <strong>__INTERVAL__</strong>. __INTERVAL_NOTE__</p></section>
<section class="panel"><h2>Candidate selection used development data</h2><div class="table-wrap"><table><thead><tr><th>Candidate</th><th>Development Macro-F1</th><th>Role</th></tr></thead><tbody>__DEV__</tbody></table></div><p class="muted">Only the baseline and the locked development-selected candidate were scored on test. The character-only candidate's test score was not computed. Candidates were not revised after final test results.</p></section>
<section class="panel"><h2>Evaluation protocol</h2><p>1,800 training / 600 development / 600 test records. Lexical connected components are kept within one partition, with threshold 0.8 and a complete three-way audit returning zero overlap rows. Vocabulary and IDF are fit on training text only.</p><p>A local analysis plan was written before fitting, then a model-selection lock was saved before final test predictions. This was not an externally preregistered or independently blinded study.</p><p>Resampling unit: __COMPONENTS__ test components; 5,000 paired replicates. The interval conditions on the fitted models and this split.</p></section>
<section class="panel"><h2>What the result supports</h2><p>__INTERPRETATION__ This does not demonstrate an accuracy benefit caused by the auditing tool.</p><ul>__LIMITS__</ul></section>
<footer>Data: <a href="https://doi.org/10.24432/C57604">Sentiment Labelled Sentences · Kotzias (2015)</a> · UCI · CC BY 4.0. Software: MIT.<br>Plan SHA-256: <code>__HASH__</code><br>Recorded environment: __VERSIONS__</footer></main></body></html>'''
    cards=''.join(f'<div class="card"><span>{e(label)}</span><strong>{e(value)}</strong><small>{e(note)}</small></div>' for label,value,note in [
        ('Baseline test Macro-F1',f'{a["macro_f1"]:.4f}','Word TF-IDF unigrams'),
        ('Selected test Macro-F1',f'{b["macro_f1"]:.4f}',selected),
        ('Observed difference',f'{b["macro_f1"]-a["macro_f1"]:+.4f}','Paired component-bootstrap interval below')])
    status=f'<div class="status"><strong>{e(verdict)}</strong>{e(evidence)}</div>'
    replacements={'__STATUS__':status,'__CARDS__':cards,'__TABLE__':table_rows,'__DEV__':dev_rows,
        '__INTERVAL__':f'[{low:+.4f}, {high:+.4f}]','__COMPONENTS__':str(result['uncertainty']['components']),
        '__INTERVAL_NOTE__':e(evidence),'__INTERPRETATION__':e(f'The selected representation has a {direction} observed Macro-F1 score. {evidence}'),'__LIMITS__':limits,'__HASH__':e(result['plan_sha256']),
        '__VERSIONS__':e(' · '.join(f'{k} {v}' for k,v in result['versions'].items()))}
    for marker,value in replacements.items():text=text.replace(marker,value)
    Path(path).write_text(text,encoding='utf-8')


if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: python model_report.py RESULTS_JSON REPORT_HTML')
    write_model_report(json.loads(Path(sys.argv[1]).read_text()),sys.argv[2])
