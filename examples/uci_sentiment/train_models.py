"""Fixed-plan model comparison on the same component-isolated test records.

Requires the optional experiment dependencies. From repository root:
  python examples/uci_sentiment/train_models.py --out my-model-experiment

No downloading, embeddings or API calls. Results must be reported even if the
selected candidate fails to improve. EvalCheck supplies evaluation controls;
feature changes, not the auditor, distinguish the compared classifiers.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import platform
from pathlib import Path
import sys
import warnings

import numpy as np
import scipy
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import FeatureUnion, make_pipeline

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from reproduce import CONFIG, load_sources
from model_report import write_model_report
from evalcheck import audit, propose_split, write_report
from evalcheck.io import write_json, write_jsonl

PLAN_PATH = BASE / 'model_experiment' / 'plan.json'


def build_model(name, plan):
    spec = plan['models'][name]
    if name == 'word_char_union':
        features = FeatureUnion([
            ('word', TfidfVectorizer(ngram_range=tuple(spec['word_ngram_range']), sublinear_tf=spec['sublinear_tf'])),
            ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=tuple(spec['char_ngram_range']), sublinear_tf=spec['sublinear_tf'])),
        ])
    else:
        features = TfidfVectorizer(analyzer='char_wb' if name == 'char_ngrams' else 'word',
                                  ngram_range=tuple(spec['ngram_range']), sublinear_tf=spec['sublinear_tf'])
    classifier = plan['classifier']
    return make_pipeline(features, LogisticRegression(C=spec['C'], solver=classifier['solver'],
        max_iter=classifier['max_iter'], random_state=classifier['random_state']))


def metrics(y, prediction):
    return {'macro_f1': float(f1_score(y, prediction, labels=[0,1], average='macro', zero_division=0)),
            'accuracy': float(accuracy_score(y, prediction)),
            'confusion_matrix_labels_0_1': confusion_matrix(y, prediction, labels=[0,1]).tolist()}


def _scores_from_counts(counts):
    tn, fp, fn, tp = np.moveaxis(np.asarray(counts, dtype=float), -1, 0)
    pos_den = 2*tp+fp+fn
    neg_den = 2*tn+fp+fn
    pos = np.divide(2*tp, pos_den, out=np.zeros_like(tp), where=pos_den!=0)
    neg = np.divide(2*tn, neg_den, out=np.zeros_like(tn), where=neg_den!=0)
    return (pos+neg)/2, (tp+tn)/(tn+fp+fn+tp)


def paired_component_bootstrap(y, a, b, components, *, replicates, seed):
    if not (len(y)==len(a)==len(b)==len(components)) or not len(y):
        raise ValueError('nonempty aligned truth, prediction and component arrays are required')
    if replicates < 1:
        raise ValueError('replicates must be positive')
    group_ids = sorted(set(components))
    group_index = {name:i for i,name in enumerate(group_ids)}
    ca = np.zeros((len(group_ids),4),dtype=int)
    cb = np.zeros_like(ca)
    for truth, pa, pb, group in zip(y,a,b,components):
        if truth not in (0,1) or pa not in (0,1) or pb not in (0,1):
            raise ValueError('this experiment supports binary labels 0 and 1')
        ca[group_index[group],int(truth)*2+int(pa)] += 1
        cb[group_index[group],int(truth)*2+int(pb)] += 1
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(group_ids),np.full(len(group_ids),1/len(group_ids)),size=replicates)
    f1a,acca=_scores_from_counts(weights@ca)
    f1b,accb=_scores_from_counts(weights@cb)
    return {'resampling_unit':'outer-test lexical connected component','components':len(group_ids),
            'replicates':replicates,'seed':seed,
            'macro_f1_delta_95_percentile_interval':np.quantile(f1b-f1a,[.025,.975]).tolist(),
            'accuracy_delta_95_percentile_interval':np.quantile(accb-acca,[.025,.975]).tolist(),
            'scope':'Conditional on these fitted models, this split and the development-selected candidate. Does not include training/split variability or independent dataset replication.'}


def make_splits(rows, plan):
    outer = propose_split(rows, CONFIG, seed=plan['outer_split']['seed'],test_fraction=plan['outer_split']['test_fraction'])
    inner = propose_split(outer['splits']['train'], CONFIG, seed=plan['inner_split']['seed'],
                          test_fraction=plan['inner_split']['development_fraction_of_pool'])
    splits={'train':inner['splits']['train'],'development':inner['splits']['test'],'test':outer['splits']['test']}
    component_by_id={rows[a['input_row']-1]['source_id']:a['component'] for a in outer['assignments']}
    assignments=[{'source_id':r['source_id'],'split':split,'component':component_by_id[r['source_id']]} for split,items in splits.items() for r in items]
    return splits, assignments, outer['policy'], inner['policy']


def run(out):
    if out.exists() and any(out.iterdir()):
        raise ValueError('output directory must be empty; preserve previous experiment results')
    plan_bytes=PLAN_PATH.read_bytes()
    plan=json.loads(plan_bytes)
    parts,source=load_sources()
    rows=[r for items in parts.values() for r in items]
    splits,assignments,outer_policy,inner_policy=make_splits(rows,plan)
    audit_result=audit(splits,CONFIG)
    if not audit_result['coverage']['near_search_complete'] or audit_result['summary']['overlap_rows']:
        raise ValueError('split isolation audit did not pass; no model was fit')
    out.mkdir(parents=True,exist_ok=True)
    (out/'plan.json').write_bytes(plan_bytes)
    write_json(out/'assignments.json',assignments)
    write_json(out/'isolation-audit.json',audit_result)
    write_report(audit_result,out/'isolation-report.html',context={
        'title':'Model experiment · train / development / test isolation',
        'protocol':'Fixed component-isolated train/development/test split. Models fit training only; development selects the candidate; test is reserved for the locked comparison.',
        'source_name':source['dataset'],'source_url':source['landing_page'],'license':source['license'],
        'notes':'Lexical/group isolation controls the measured checks, not all possible leakage. This is not an independently blinded external test.'})
    for name,items in splits.items():write_jsonl(out/f'{name}.jsonl',items)
    x={name:[r['text'] for r in items] for name,items in splits.items()}
    y={name:np.array([int(r['label']) for r in items]) for name,items in splits.items()}
    models={};development={}
    # Treat non-convergence as a failed run, not an unreported warning.
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        for name in sorted(plan['models']):
            model=build_model(name,plan)
            model.fit(x['train'],y['train'])
            development[name]=metrics(y['development'],model.predict(x['development']))
            models[name]=model
            print(f"development {name}: macro-F1={development[name]['macro_f1']:.6f}",flush=True)
    selected=sorted(development,key=lambda n:(-development[n]['macro_f1'],n))[0]
    # The candidate name is persisted before any final test prediction is made.
    selection={'selected_model':selected,'development_scores':development,'plan_sha256':hashlib.sha256(plan_bytes).hexdigest()}
    write_json(out/'selection-lock.json',selection)
    baseline=plan['baseline']
    pa=models[baseline].predict(x['test'])
    pb=models[selected].predict(x['test']) if selected!=baseline else pa.copy()
    test={baseline:metrics(y['test'],pa),selected:metrics(y['test'],pb)}
    component_by_id={a['source_id']:a['component'] for a in assignments}
    components=[component_by_id[r['source_id']] for r in splits['test']]
    ci=paired_component_bootstrap(y['test'],pa,pb,components,
        replicates=plan['uncertainty']['replicates'],seed=plan['uncertainty']['seed'])
    predictions=[{'source_id':r['source_id'],'component':component,'truth':int(truth),
        'baseline_prediction':int(a),'selected_prediction':int(b)}
        for r,component,truth,a,b in zip(splits['test'],components,y['test'],pa,pb)]
    write_jsonl(out/'test-predictions.jsonl',predictions)
    delta={key:test[selected][key]-test[baseline][key] for key in ['macro_f1','accuracy']}
    low,high=ci['macro_f1_delta_95_percentile_interval']
    conclusion=('positive conditional evidence on this test split' if low>0 else
                'negative conditional evidence on this test split' if high<0 else
                'interval includes zero; no clear positive difference established')
    result={'kind':'development_selected_model_comparison','plan_sha256':selection['plan_sha256'],
        'source':source,'versions':{'python':platform.python_version(),'scikit_learn':sklearn.__version__,
        'numpy':np.__version__,'scipy':scipy.__version__},'baseline':baseline,'selected_model':selected,
        'split_sizes':{name:len(items) for name,items in splits.items()},
        'label_counts':{name:dict(Counter(map(str,labels))) for name,labels in y.items()},
        'outer_policy':outer_policy,'inner_policy':inner_policy,'audit_fingerprint':audit_result['fingerprint'],
        'isolation_overlap_rows':audit_result['summary']['overlap_rows'],'audit_tool_version':audit_result['tool_version'],'development':development,
        'test':test,'delta_selected_minus_baseline':delta,'uncertainty':ci,'conclusion':conclusion,
        'limitations':['One public dataset and one split; no independent replication.',
          'Improvement, if observed, compares feature representations and does not estimate the causal effect of EvalCheck.',
          'The corpus was previously inspected for audit examples; test labels were not used to choose candidates, hyperparameters or a split seed in this experiment.',
          'Grouping uses all input text for a predeclared unlabeled isolation rule; TF-IDF vocabularies and IDF are fit on training text only.',
          'Bootstrap conditions on fitted models and selected candidate; it is not a full uncertainty estimate for retraining or deploying on a new population.']}
    write_json(out/'results.json',result)
    write_model_report(result,out/'report.html')
    lines=['# Model comparison: measured results','',
        f"Baseline: `{baseline}`. Development-selected candidate: `{selected}`.",'',
        '| Metric | Baseline test | Selected test | Difference (percentage points) |',
        '|---|---:|---:|---:|']
    for key,label in [('macro_f1','Macro-F1'),('accuracy','Accuracy')]:
        lines.append(f"| {label} | {test[baseline][key]*100:.2f}% | {test[selected][key]*100:.2f}% | {delta[key]*100:+.2f} |")
    lines.extend(['',f"Paired component-bootstrap 95% percentile interval for the macro-F1 difference: [{low*100:+.2f}, {high*100:+.2f}] percentage points.",
        '',f"Conclusion: **{conclusion}**.",'',
        'This compares two models on identical held-out rows. It is not evidence that the auditing software itself raised accuracy. See results.json for split sizes, source attribution, complete development results, plan hash, versions, predictions and limitations.'])
    (out/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'selected':selected,'split_sizes':result['split_sizes'],'test':test,'delta':delta,'uncertainty':ci,'conclusion':conclusion},indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('my-model-experiment'))
    args=parser.parse_args()
    try:run(args.out)
    except (OSError,ValueError) as error:parser.exit(2,f'model experiment: {error}\n')


if __name__=='__main__':main()
