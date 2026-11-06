"""Optional experiment tests. The core package still has no ML dependency."""
import importlib.util
import hashlib
import json
from pathlib import Path
import unittest

AVAILABLE = all(importlib.util.find_spec(name) for name in ['numpy','sklearn','scipy'])
ROOT = Path(__file__).resolve().parents[1]
if AVAILABLE:
    spec=importlib.util.spec_from_file_location('model_experiment',ROOT/'examples/uci_sentiment/train_models.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import numpy as np
    from sklearn.metrics import f1_score, accuracy_score


@unittest.skipUnless(AVAILABLE,'install the optional experiment dependencies')
class ModelExperimentTests(unittest.TestCase):
    def test_confusion_count_scoring_matches_independent_metric(self):
        for y,p in [([0,0,1,1],[0,1,0,1]),([0,0],[0,0]),([1,1],[1,1]),([0,1],[1,0])]:
            counts=np.zeros(4,dtype=int)
            for a,b in zip(y,p):counts[a*2+b]+=1
            f1,acc=module._scores_from_counts(counts)
            self.assertAlmostEqual(float(f1),f1_score(y,p,labels=[0,1],average='macro',zero_division=0))
            self.assertAlmostEqual(float(acc),accuracy_score(y,p))

    def test_component_bootstrap_not_row_resampling(self):
        y=[0,1,0,1];a=[0,0,0,1];b=[0,1,1,1];groups=['a','a','b','c']
        first=module.paired_component_bootstrap(y,a,b,groups,replicates=200,seed=12)
        # Duplicating every row inside each cluster must not change the cluster
        # draw distribution or either row-based score in a drawn sample.
        second=module.paired_component_bootstrap(y+y,a+a,b+b,groups+groups,replicates=200,seed=12)
        self.assertEqual(first,second)
        self.assertEqual(first['components'],3)

    def test_identical_models_have_zero_paired_difference(self):
        r=module.paired_component_bootstrap([0,1,1],[0,0,1],[0,0,1],['a','b','b'],replicates=100,seed=1)
        self.assertEqual(r['macro_f1_delta_95_percentile_interval'],[0.,0.])
        self.assertEqual(r['accuracy_delta_95_percentile_interval'],[0.,0.])

    def test_vocabulary_excludes_unseen_data(self):
        plan=json.loads(module.PLAN_PATH.read_text())
        model=module.build_model('word_unigram',plan)
        model.fit(['good useful device','bad broken device'],[1,0])
        model.predict(['unseenvalidationtoken good'])
        self.assertNotIn('unseenvalidationtoken',model.steps[0][1].vocabulary_)

    def test_saved_plan_predictions_and_source_assignments(self):
        folder=ROOT/'examples/uci_sentiment/model_experiment/results'
        result=json.loads((folder/'results.json').read_text())
        lock=json.loads((folder/'selection-lock.json').read_text())
        self.assertEqual(result['plan_sha256'],hashlib.sha256(module.PLAN_PATH.read_bytes()).hexdigest())
        self.assertEqual(lock['plan_sha256'],result['plan_sha256'])
        self.assertEqual(set(result['test']),{result['baseline'],result['selected_model']})
        records=[json.loads(line) for line in (folder/'test-predictions.jsonl').read_text().splitlines()]
        self.assertEqual(len(records),600)
        for key,field in [(result['baseline'],'baseline_prediction'),(result['selected_model'],'selected_prediction')]:
            self.assertAlmostEqual(f1_score([r['truth'] for r in records],[r[field] for r in records],labels=[0,1],average='macro',zero_division=0),result['test'][key]['macro_f1'])
        assignments=json.loads((folder/'assignments.json').read_text())
        components={}
        for item in assignments:
            components.setdefault(item['component'],set()).add(item['split'])
        self.assertTrue(all(len(splits)==1 for splits in components.values()))
        self.assertEqual(len({a['source_id'] for a in assignments}),3000)
        self.assertEqual({r['source_id'] for r in records},{a['source_id'] for a in assignments if a['split']=='test'})


if __name__=='__main__':unittest.main()
