import unittest
from evalcheck.code_scan import scan_source, scan_notebook, to_sarif

PREFIX='from sklearn.model_selection import train_test_split, cross_val_score\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.linear_model import LogisticRegression\n'
def rules(source):return {f['rule'] for f in scan_source(PREFIX+source)['findings']}

class CodeScanTests(unittest.TestCase):
    def test_inline_fit_before_split(self):
        self.assertEqual(rules('Z=StandardScaler().fit_transform(X)\na,b,c,d=train_test_split(Z,y)'),{'EC001'})
    def test_fit_transform_steps(self):
        self.assertEqual(rules('s=StandardScaler()\ns.fit(X)\nZ=s.transform(X)\na,b,c,d=train_test_split(Z,y)'),{'EC001'})
    def test_chained_fit(self):
        self.assertEqual(rules('s=StandardScaler().fit(X)\nZ=s.transform(X)\na,b,c,d=train_test_split(Z,y)'),{'EC001'})
    def test_safe_fit_on_train(self):
        self.assertFalse(rules('a,b,c,d=train_test_split(X,y)\ns=StandardScaler()\ns.fit(a)\nza=s.transform(a)\nzb=s.transform(b)\nm=LogisticRegression()\nm.fit(za,c)\nm.predict(zb)'))
    def test_heldout_fit(self):
        self.assertEqual(rules('a,b,c,d=train_test_split(X,y)\nm=LogisticRegression()\nm.fit(b,d)'),{'EC002'})
    def test_concatenated_fit(self):
        self.assertEqual(rules('import numpy as np\na,b,c,d=train_test_split(X,y)\nm=LogisticRegression()\nm.fit(np.concatenate([a,b]),y)'),{'EC002'})
    def test_preprocessing_cv(self):
        self.assertEqual(rules('Z=StandardScaler().fit_transform(X)\nscores=cross_val_score(LogisticRegression(),Z,y)'),{'EC003'})
    def test_pipeline_cv(self):
        self.assertFalse(rules('from sklearn.pipeline import make_pipeline\np=make_pipeline(StandardScaler(),LogisticRegression())\nscores=cross_val_score(p,X,y)'))
    def test_inner_cv_on_prefitted_train(self):
        self.assertEqual(rules('a,b,c,d=train_test_split(X,y)\nZ=StandardScaler().fit_transform(a)\nscores=cross_val_score(LogisticRegression(),Z,c)'),{'EC003'})
    def test_grid_search(self):
        self.assertEqual(rules('from sklearn.model_selection import GridSearchCV\nZ=StandardScaler().fit_transform(X)\ns=GridSearchCV(LogisticRegression(),{})\ns.fit(Z,y)'),{'EC003'})
    def test_resample(self):
        self.assertEqual(rules('from imblearn.over_sampling import SMOTE\nZ,t=SMOTE().fit_resample(X,y)\na,b,c,d=train_test_split(Z,t)'),{'EC004'})
    def test_train_resample(self):
        self.assertFalse(rules('from imblearn.over_sampling import SMOTE\na,b,c,d=train_test_split(X,y)\nZ,t=SMOTE().fit_resample(a,c)\nm=LogisticRegression()\nm.fit(Z,t)'))
    def test_alias_multiline(self):
        r=scan_source('import sklearn.model_selection as ms\nfrom sklearn.preprocessing import StandardScaler as S\nZ=S().fit_transform(X)\na,b,c,d=ms.train_test_split(\nZ,y\n)')
        self.assertEqual((r['findings'][0]['line'],r['findings'][0]['origin']['line']),(4,3))
    def test_stateless(self):
        self.assertFalse(rules('from sklearn.preprocessing import Normalizer\nZ=Normalizer().fit_transform(X)\na,b,c,d=train_test_split(Z,y)'))
    def test_reassign(self):
        self.assertFalse(rules('Z=StandardScaler().fit_transform(X)\nZ=load_new_data()\na,b,c,d=train_test_split(Z,y)'))
    def test_unrelated(self):
        self.assertFalse(rules('Z=StandardScaler().fit_transform(other)\na,b,c,d=train_test_split(X,y)'))
    def test_never_execute_strings(self):
        r=scan_source('# StandardScaler().fit_transform(X)\ntext="m.fit(X_test, y_test)"\nraise RuntimeError("must never run")')
        self.assertFalse(r['findings']);self.assertEqual(r['status'],'partial')
    def test_abstentions(self):
        r=scan_source(PREFIX+'def build():\n Z=StandardScaler().fit_transform(X)\n return train_test_split(Z,y)\nif flag:\n m.fit(X_test,y_test)')
        self.assertFalse(r['findings']);self.assertEqual({n['kind'] for n in r['coverage']['notes']},{'scope_skipped','control_flow_skipped'})
    def test_notebook_cells(self):
        nb={'cells':[{'cell_type':'markdown','source':'example'},{'cell_type':'code','source':PREFIX+'Z=StandardScaler().fit_transform(X)','execution_count':1},{'cell_type':'code','source':['a,b,c,d=train_test_split(Z,y)'],'execution_count':2}]}
        f=scan_notebook(nb)['findings'][0];self.assertEqual((f['cell'],f['line'],f['origin']['cell']),(3,1,2))
    def test_magics_order(self):
        nb={'cells':[{'cell_type':'code','source':'%matplotlib inline\nx=1','execution_count':5},{'cell_type':'code','source':'x=2','execution_count':2}]}
        r=scan_notebook(nb);self.assertEqual({n['kind'] for n in r['coverage']['notes']},{'line_magic','execution_order'})
    def test_sarif_notebook_line(self):
        nb={'cells':[{'cell_type':'code','source':PREFIX+'Z=StandardScaler().fit_transform(X)\na,b,c,d=train_test_split(Z,y)'}]}
        r=to_sarif([scan_notebook(nb,path='notebook.ipynb')]);self.assertNotIn('region',r['runs'][0]['results'][0]['locations'][0]['physicalLocation'])
    def test_bad_inputs(self):
        self.assertEqual(scan_source('def bad(')['status'],'partial')
        self.assertEqual(scan_source('custom.fit(X)')['coverage']['notes'][0]['kind'],'unresolved_fit')
        with self.assertRaises(ValueError):scan_notebook({'no':'cells'})
        with self.assertRaises(ValueError):scan_source('x'*(2_000_001))

if __name__=='__main__':unittest.main()
