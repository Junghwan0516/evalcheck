"""Reproduce a controlled group-memorization trap, not a real benchmark.

Run from repository root: python examples/compare_splits.py
Requires the optional experiment extra. Model and hyperparameters are fixed.
"""
from pathlib import Path
import json
import platform
import random
import statistics
import sys
import time

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline


def generate(seed):
    rng = random.Random(seed)
    rows = []
    # Each group has an independent random target and an otherwise uninformative
    # token. Seeing the same group at train and test time makes memorization easy.
    labels = [0, 1] * 50
    rng.shuffle(labels)
    for group, label in enumerate(labels):
        for variant in range(6):
            rows.append({'text': f'case{group:04d} case{group:04d} response variant{variant}',
                         'label': label, 'group': f'case{group:04d}'})
    return rows


def score(rows, train, test):
    model=make_pipeline(TfidfVectorizer(),LogisticRegression(C=10,max_iter=1000,random_state=0))
    model.fit([rows[i]['text'] for i in train],[rows[i]['label'] for i in train])
    return accuracy_score([rows[i]['label'] for i in test],model.predict([rows[i]['text'] for i in test]))


def main():
    runs=[]
    for seed in [7,19,42,73,101]:
        rows=generate(seed)
        ids=list(range(len(rows)))
        a,b=train_test_split(ids,test_size=.2,random_state=seed)
        c,d=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=seed).split(ids,groups=[r['group'] for r in rows]))
        runs.append({'seed':seed,'row_random_accuracy':score(rows,a,b),'group_heldout_accuracy':score(rows,c,d),
                     'train_rows':len(a),'test_rows':len(b),'heldout_train_rows':len(c),'heldout_test_rows':len(d),
                     'random_shared_groups':len({rows[i]['group'] for i in a}&{rows[i]['group'] for i in b}),
                     'heldout_shared_groups':len({rows[i]['group'] for i in c}&{rows[i]['group'] for i in d})})
    result={'kind':'controlled_synthetic_experiment','description':'Random per-group labels; token identity enables memorization when groups overlap.',
        'warning':'Not a real-world performance estimate or evidence that every row-random split is invalid.',
        'model':'TF-IDF + LogisticRegression(C=10, max_iter=1000, random_state=0)',
        'rows':600,'groups':100,'runs':runs,
        'mean_row_random_accuracy':statistics.mean(r['row_random_accuracy'] for r in runs),
        'mean_group_heldout_accuracy':statistics.mean(r['group_heldout_accuracy'] for r in runs),
        'python':platform.python_version(),'scikit_learn':sklearn.__version__}
    output=Path(__file__).parent/'experiment-results.json'
    output.write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
