"""Measured consequence of the supported feature-selection leakage pattern.

Optional ML dependencies. No user code is executed by the static scanner.
The two classifiers below are our own explicit, fixed-plan experiment code.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import sklearn
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parents[1]/'src'))
from evalcheck.code_scan import scan_source


def run():
    plan_bytes=(BASE/'impact_plan.json').read_bytes();plan=json.loads(plan_bytes)
    rows=[]
    for seed in plan['data_seeds']:
        rng=np.random.default_rng(seed)
        X=rng.normal(size=(plan['samples'],plan['features']))
        y=rng.integers(0,2,size=plan['samples'])
        train,test=train_test_split(np.arange(len(y)),test_size=plan['test_fraction'],random_state=plan['split_seed'])
        selected=SelectKBest(f_classif,k=plan['features_selected']).fit_transform(X,y)
        bad=LogisticRegression(solver='liblinear',C=1,max_iter=2000,random_state=7).fit(selected[train],y[train])
        fixed=make_pipeline(SelectKBest(f_classif,k=plan['features_selected']),LogisticRegression(solver='liblinear',C=1,max_iter=2000,random_state=7)).fit(X[train],y[train])
        a=accuracy_score(y[test],bad.predict(selected[test]));b=accuracy_score(y[test],fixed.predict(X[test]))
        rows.append({'data_seed':seed,'leaky_accuracy':a,'pipeline_accuracy':b,'apparent_score_excess':a-b,'test_rows':len(test)})
        print(f'seed {seed}: leaky={a:.2%}; pipeline={b:.2%}',flush=True)
    bad_source='from sklearn.model_selection import train_test_split\nfrom sklearn.feature_selection import SelectKBest, f_classif\nZ=SelectKBest(f_classif,k=50).fit_transform(X,y)\na,b,c,d=train_test_split(Z,y,test_size=.25,random_state=7)\n'
    fixed_source='from sklearn.model_selection import train_test_split\nfrom sklearn.feature_selection import SelectKBest, f_classif\nfrom sklearn.pipeline import make_pipeline\nfrom sklearn.linear_model import LogisticRegression\na,b,c,d=train_test_split(X,y,test_size=.25,random_state=7)\nm=make_pipeline(SelectKBest(f_classif,k=50),LogisticRegression())\nm.fit(a,c)\npred=m.predict(b)\n'
    result={'kind':'synthetic_negative_control','plan_sha256':hashlib.sha256(plan_bytes).hexdigest(),
        'versions':{'numpy':np.__version__,'sklearn':sklearn.__version__},'runs':rows,
        'mean_leaky_accuracy':float(np.mean([r['leaky_accuracy'] for r in rows])),
        'mean_pipeline_accuracy':float(np.mean([r['pipeline_accuracy'] for r in rows])),
        'mean_apparent_score_excess':float(np.mean([r['apparent_score_excess'] for r in rows])),
        'bad_source_scan':scan_source(bad_source,path='feature_selection_bad.py'),
        'fixed_source_scan':scan_source(fixed_source,path='feature_selection_fixed.py'),
        'interpretation':plan['claim_boundary']}
    (BASE/'impact_results.json').write_text(json.dumps(result,indent=2)+'\n')
    (BASE/'feature_selection_bad.py').write_text(bad_source)
    (BASE/'feature_selection_fixed.py').write_text(fixed_source)
    print(json.dumps({k:result[k] for k in ['mean_leaky_accuracy','mean_pipeline_accuracy','mean_apparent_score_excess']},indent=2))


if __name__=='__main__':run()
