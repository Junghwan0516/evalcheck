"""Evaluate frozen authored cases, including unsupported risks in overall recall."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from evalcheck.code_scan import scan_source

base=Path(__file__).resolve().parent
raw=(base/'cases.json').read_bytes();manifest=json.loads((base/'manifest.json').read_text())
if hashlib.sha256(raw).hexdigest()!=manifest['cases_sha256']:raise SystemExit('case labels changed from frozen manifest')
cases=json.loads(raw)
rows=[];tp=fp=tn=fn=0
for case in cases:
    result=scan_source(case['source'],path=case['id']+'.py')
    actual=sorted({f['rule'] for f in result['findings']})
    positive=case['risk_present'];detected=bool(actual)
    tp+=positive and detected;fn+=positive and not detected
    fp+=not positive and detected;tn+=not positive and not detected
    rows.append({'id':case['id'],'risk_present':positive,'scope':case['scope'],'expected_rules':case['expected_rules'],
        'detected_rules':actual,'exact_rule_match':sorted(case['expected_rules'])==actual,
        'coverage_notes':result['coverage']['notes']})
result={'suite':manifest['suite'],'external_validation':False,'cases':len(rows),
 'cases_sha256':manifest['cases_sha256'],
 'engine_sha256_at_evaluation':hashlib.sha256((ROOT/'src/evalcheck/code_scan.py').read_bytes()).hexdigest(),
 'engine_unchanged_since_case_freeze':hashlib.sha256((ROOT/'src/evalcheck/code_scan.py').read_bytes()).hexdigest()==manifest['engine_sha256_before_first_run'],
 'file_level':{'tp':tp,'fp':fp,'tn':tn,'fn':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall_including_unsupported':tp/(tp+fn) if tp+fn else None},
 'interpretation':'Authored challenge-suite result, not real-world precision/recall or independent validation. Unsupported risk cases remain false negatives in overall recall.',
 'cases_detail':rows}
(base/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='cases_detail'},indent=2))
