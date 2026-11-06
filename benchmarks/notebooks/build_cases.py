"""Authored challenge suite. Not external notebooks or an independent benchmark.

Cases and labels are frozen before the benchmark runner is first invoked.
Development unit tests are separate. Do not relabel failed cases to improve scores.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P='from sklearn.model_selection import train_test_split, cross_val_score\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression\n'
cases=[]
def add(name,source,risks=(),*,scope='supported',origin='authored-challenge',reference=None):
    cases.append({'id':name,'origin':origin,'source':source,'risk_present':bool(risks),'expected_rules':list(risks),'scope':scope,'reference':reference})

SK='https://scikit-learn.org/stable/common_pitfalls.html#data-leakage'
IM='https://imbalanced-learn.org/stable/common_pitfalls.html#data-leakage'
add('ref-feature-select-all',P+'from sklearn.feature_selection import SelectKBest\nZ=SelectKBest(k=10).fit_transform(X,y)\na,b,c,d=train_test_split(Z,y)',('EC001',),origin='documentation-concept-adaptation',reference=SK)
add('ref-train-preprocess',P+'a,b,c,d=train_test_split(X,y)\ns=StandardScaler()\ns.fit(a)\na=s.transform(a)\nb=s.transform(b)',origin='documentation-concept-adaptation',reference=SK)
add('ref-cv-global-features',P+'Z=StandardScaler().fit_transform(X)\nscore=cross_val_score(LogisticRegression(),Z,y)',('EC003',),origin='documentation-concept-adaptation',reference=SK)
add('ref-cv-pipeline',P+'from sklearn.pipeline import make_pipeline\nscore=cross_val_score(make_pipeline(StandardScaler(),LogisticRegression()),X,y)',origin='documentation-concept-adaptation',reference=SK)
add('ref-resample-all',P+'from imblearn.over_sampling import RandomOverSampler\nZ,t=RandomOverSampler().fit_resample(X,y)\na,b,c,d=train_test_split(Z,t)',('EC004',),origin='documentation-concept-adaptation',reference=IM)
add('ref-resample-train',P+'from imblearn.over_sampling import RandomOverSampler\na,b,c,d=train_test_split(X,y)\na,c=RandomOverSampler().fit_resample(a,c)',origin='documentation-concept-adaptation',reference=IM)
add('ref-fit-heldout',P+'a,b,c,d=train_test_split(X,y)\ns=StandardScaler()\ns.fit(b)',('EC002',),origin='documentation-concept-adaptation',reference=SK)
add('ref-pipeline-heldout-predict',P+'from sklearn.pipeline import make_pipeline\na,b,c,d=train_test_split(X,y)\nm=make_pipeline(StandardScaler(),LogisticRegression())\nm.fit(a,c)\nm.predict(b)',origin='documentation-concept-adaptation',reference=SK)

add('pca-before-split',P+'from sklearn.decomposition import PCA\nZ=PCA(n_components=2).fit_transform(X)\na,b,c,d=train_test_split(Z,y)',('EC001',))
add('impute-before-split',P+'from sklearn.impute import SimpleImputer as Fill\nZ=Fill().fit_transform(X)\na,b,c,d=train_test_split(Z,y)',('EC001',))
add('functional-scale',P+'from sklearn.preprocessing import scale\nZ=scale(X)\na,b,c,d=train_test_split(Z,y)',('EC001',))
add('copy-carries-leak',P+'s=StandardScaler()\ns.fit(X)\nZ=s.transform(X).copy()\na,b,c,d=train_test_split(Z,y)',('EC001',))
add('heldout-keyword-fit',P+'a,b,c,d=train_test_split(X,y)\nm=LogisticRegression()\nm.fit(X=b,y=d)',('EC002',))
add('heldout-partial-fit',P+'a,b,c,d=train_test_split(X,y)\ns=StandardScaler()\ns.partial_fit(b)',('EC002',))
add('merged-cohort-fit',P+'import numpy as np\na,b,c,d=train_test_split(X,y)\nm=LogisticRegression()\nm.fit(np.vstack((a,b)),y)',('EC002',))
add('heldout-pipeline-fit',P+'from sklearn.pipeline import make_pipeline\na,b,c,d=train_test_split(X,y)\nm=make_pipeline(StandardScaler(),LogisticRegression())\nm.fit(b,d)',('EC002',))
add('cv-keyword-vectorizer',P+'from sklearn.feature_extraction.text import TfidfVectorizer\nZ=TfidfVectorizer().fit_transform(texts)\nscore=cross_val_score(LogisticRegression(),X=Z,y=y)',('EC003',))
add('cross-validate-selector',P+'from sklearn.feature_selection import SelectPercentile\nfrom sklearn.model_selection import cross_validate\nZ=SelectPercentile().fit_transform(X,y)\nscore=cross_validate(LogisticRegression(),Z,y)',('EC003',))
add('random-search-prefit',P+'from sklearn.model_selection import RandomizedSearchCV\ns=StandardScaler().fit(X)\nZ=s.transform(X)\nsearch=RandomizedSearchCV(LogisticRegression(),{})\nsearch.fit(Z,y)',('EC003',))
add('cv-resampled-features',P+'from imblearn.over_sampling import SMOTE\nZ,t=SMOTE().fit_resample(X,y)\nscore=cross_val_score(LogisticRegression(),Z,t)',('EC003',))
add('resampler-alias',P+'from imblearn.over_sampling import SMOTE as Resampler\nZ,t=Resampler().fit_resample(X,y)\na,b,c,d=train_test_split(Z,t,test_size=.2)',('EC004',))
add('resampler-module',P+'import imblearn.under_sampling as under\nZ,t=under.RandomUnderSampler().fit_resample(X,y)\na,b,c,d=train_test_split(Z,t)',('EC004',))
add('resampler-reassigned',P+'from imblearn.over_sampling import ADASYN\nX,y=ADASYN().fit_resample(X,y)\na,b,c,d=train_test_split(X,y)',('EC004',))
add('resampler-instance-copy',P+'from imblearn.over_sampling import RandomOverSampler\nr=RandomOverSampler()\nZ,t=r.fit_resample(X,y)\nQ=Z.copy()\na,b,c,d=train_test_split(Q,t)',('EC004',))

add('safe-pca-train',P+'from sklearn.decomposition import PCA\na,b,c,d=train_test_split(X,y)\np=PCA().fit(a)\nza=p.transform(a)\nzb=p.transform(b)\nm=LogisticRegression()\nm.fit(za,c)\nm.predict(zb)')
add('safe-normalizer-all',P+'from sklearn.preprocessing import Normalizer\nZ=Normalizer().fit_transform(X)\na,b,c,d=train_test_split(Z,y)')
add('safe-normalizer-heldout',P+'from sklearn.preprocessing import Normalizer\na,b,c,d=train_test_split(X,y)\nb=Normalizer().fit_transform(b)')
add('safe-external-fitted-transform',P+'s=StandardScaler().fit(external_reference)\nZ=s.transform(X)\na,b,c,d=train_test_split(Z,y)')
add('safe-reset-data',P+'Z=StandardScaler().fit_transform(X)\nZ=load_independent_features()\na,b,c,d=train_test_split(Z,y)')
add('safe-string-comment',P+'# Z=StandardScaler().fit_transform(X)\ndescription="model.fit(X_test,y_test)"\na,b,c,d=train_test_split(X,y)')
add('safe-cv-clones-estimator',P+'m=LogisticRegression()\nm.fit(X,y)\nscore=cross_val_score(m,X,y)')
add('safe-shadowed-api',P+'def train_test_split(*args):\n return args\nZ=StandardScaler().fit_transform(X)\na,b=train_test_split(Z,y)')
add('safe-raw-array',P+'import numpy as np\nX=np.arange(100).reshape(50,2)\na,b,c,d=train_test_split(X,y)\nm=LogisticRegression()\nm.fit(a,c)')
add('safe-no-evaluation',P+'Z=StandardScaler().fit_transform(X)\nm=LogisticRegression()\nm.fit(Z,y)')
add('safe-heldout-predict',P+'a,b,c,d=train_test_split(X,y)\nm=LogisticRegression()\nm.fit(a,c)\nm.predict(b)')
add('safe-unrelated-transform',P+'Z=StandardScaler().fit_transform(other_dataset)\na,b,c,d=train_test_split(X,y)')

add('limit-function-body',P+'def build_model():\n Z=StandardScaler().fit_transform(X)\n return train_test_split(Z,y)',('EC001',),scope='unsupported-risk')
add('limit-branch',P+'if enabled:\n Z=StandardScaler().fit_transform(X)\n a,b,c,d=train_test_split(Z,y)',('EC001',),scope='unsupported-risk')
add('limit-opaque-helper',P+'from project.preprocessing import prepare_all\nZ=prepare_all(X)\na,b,c,d=train_test_split(Z,y)',('EC001',),scope='unsupported-risk')
add('limit-opaque-feature-wrapper',P+'Z=custom_wrapper(StandardScaler().fit_transform(X))\na,b,c,d=train_test_split(Z,y)',('EC001',),scope='unsupported-risk')

out=Path(__file__).with_name('cases.json')
if out.exists():raise SystemExit('Cases already frozen; do not overwrite labels after evaluation.')
out.write_text(json.dumps(cases,indent=2)+'\n')
manifest={'suite':'Authored Notebook Leakage Challenge v1','cases':len(cases),
 'cases_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'engine_sha256_before_first_run':hashlib.sha256((ROOT/'src/evalcheck/code_scan.py').read_bytes()).hexdigest(),
 'label_policy':'Risk-present labels include unsupported examples in overall recall. Expected rules name the authored risk, not a promise that the scanner covers it.',
 'external_validation':False,'provenance':'40 authored examples: 8 concept adaptations from primary documentation, 32 challenge examples including 4 explicit limitations. Not harvested external notebooks. Not an independent or population-representative study.'}
Path(__file__).with_name('manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Frozen',len(cases),'labelled cases before first benchmark run.')
