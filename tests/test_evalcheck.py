import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from evalcheck import AuditConfig, audit, load_records, propose_split, write_report, __version__
from evalcheck.core import normalize, tokens, _near_pairs
from evalcheck.cli import main
from evalcheck.io import write_jsonl


def row(text, label='ok', **kw):
    return dict(text=text, label=label, **kw)


class AuditTests(unittest.TestCase):
    def test_unicode_exact_and_affected_union(self):
        r=audit({'train':[row(' Ａ  CAT ')], 'test':[row('a cat')]})
        self.assertEqual(r['summary']['counts'], {'exact_overlap':1})
        self.assertEqual(r['summary']['overlap_rows'],2)

    def test_conflicts_within_and_across_splits(self):
        r=audit({'train':[row('a','yes'),row('a','no')], 'test':[row('b')]})
        self.assertEqual(r['summary']['counts'], {'label_conflict':1})
        self.assertEqual(r['summary']['overlap_rows'],0)

    def test_label_types_not_conflated(self):
        r=audit({'train':[row('a',1)],'test':[row('a','1')]})
        self.assertEqual(r['summary']['counts']['label_conflict'],1)

    def test_group_overlap_is_configured(self):
        parts={'train':[row('alpha',g='patient-1')],'test':[row('beta',g='patient-1')]}
        self.assertEqual(audit(parts)['status'],'no_findings')
        r=audit(parts,AuditConfig(group='g'))
        self.assertEqual(r['summary']['counts'],{'group_overlap':1})

    def test_near_inclusive_threshold(self):
        r=audit({'train':[row('one two three four')],'test':[row('one two three four five')]},AuditConfig(threshold=.8))
        self.assertEqual(r['findings'][0]['similarity'],.8)

    def test_no_semantic_claim(self):
        r=audit({'train':[row('dog')],'test':[row('canine')]})
        self.assertEqual(r['status'],'no_findings')
        self.assertTrue(any('semantic' in x for x in r['limitations']))

    def test_budget_stop_is_incomplete(self):
        r=audit({'train':[row('a b c'),row('a b d')],'test':[row('a b e')]},AuditConfig(threshold=.4,max_candidates=1))
        self.assertEqual(r['status'],'incomplete')
        self.assertEqual(r['coverage']['candidates_compared'],1)

    def test_exact_budget_not_false_incomplete(self):
        r=audit({'train':[row('a b')],'test':[row('a b c')]},AuditConfig(threshold=.4,max_candidates=1))
        self.assertTrue(r['coverage']['near_search_complete'])

    def test_determinism_and_immutability(self):
        parts={'train':[row('a')],'test':[row('b')]}; before=copy.deepcopy(parts)
        self.assertEqual(audit(parts),audit(parts))
        self.assertEqual(parts,before)

    def test_no_label_mode(self):
        r=audit({'train':[{'text':'a'}],'test':[{'text':'b'}]},AuditConfig(label=None))
        self.assertEqual(r['status'],'no_findings')

    def test_invalid_configs(self):
        for threshold in [0,-1,1.1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):AuditConfig(threshold=threshold)
        for budget in [0,-1,1.5,True]:
            with self.assertRaises(ValueError):AuditConfig(max_candidates=budget)
        with self.assertRaises(ValueError):AuditConfig(group='text')

    def test_missing_and_blank_values(self):
        for bad in [{'text':''},{'text':'  ','label':'x'},{'text':'x','label':None},{'text':1,'label':'x'}]:
            with self.assertRaises(ValueError):audit({'train':[bad],'test':[row('b')]})

    def test_empty_or_single_split(self):
        for parts in [{'train':[row('a')]},{'train':[],'test':[row('b')]}]:
            with self.assertRaises(ValueError):audit(parts)

    def test_index_matches_brute_force_randomized(self):
        rng=random.Random(123)
        for threshold in [.2,.5,.8,1]:
            records=[{'text':' '.join(rng.sample(list('abcdefgh'),rng.randint(1,6))), 'split':'train' if i<15 else 'test'} for i in range(30)]
            got,n,complete=_near_pairs(records,AuditConfig(threshold=threshold))
            expected=[]
            for j in range(len(records)):
                for i in range(j):
                    a,b=records[i],records[j]
                    if a['split']==b['split'] or normalize(a['text'])==normalize(b['text']):continue
                    x,y=tokens(a['text']),tokens(b['text'])
                    score=len(x&y)/len(x|y)
                    if score>=threshold:expected.append((i,j,score))
            self.assertEqual(got,expected)
            self.assertTrue(complete)

    def test_three_splits_and_no_double_count(self):
        r=audit({'train':[row('a',g='x')],'dev':[row('a',g='x')],'test':[row('a',g='x')]},AuditConfig(group='g'))
        self.assertEqual(r['summary']['overlap_rows'],3)
        self.assertEqual(r['summary']['findings'],2)


class SplitTests(unittest.TestCase):
    def test_connected_groups_and_duplicates_preserved(self):
        rows=[row('a',g='x'),row('b',g='x'),row('b',g='y'),row('c',g='y'),row('d',g='z'),row('e',g='w')]
        before=copy.deepcopy(rows)
        result=propose_split(rows,AuditConfig(group='g'),seed=12)
        assigned={a['input_row']:a['split'] for a in result['assignments']}
        self.assertEqual(len({assigned[i] for i in range(1,5)}),1)
        self.assertEqual(sum(map(len,result['splits'].values())),len(rows))
        self.assertEqual(rows,before)
        self.assertEqual(audit(result['splits'],AuditConfig(group='g'))['status'],'no_findings')

    def test_near_transitive_components(self):
        rows=[row('a b c'),row('a b d'),row('a d e'),row('z')]
        result=propose_split(rows,AuditConfig(threshold=.5))
        self.assertEqual(result['policy']['largest_component'],3)
        self.assertEqual(audit(result['splits'],AuditConfig(threshold=.5))['status'],'no_findings')

    def test_single_component_refused(self):
        with self.assertRaises(ValueError):propose_split([row('a'),row('a')])

    def test_incomplete_split_refused(self):
        with self.assertRaisesRegex(ValueError,'budget'):
            propose_split([row('a b'),row('a c'),row('a d')],AuditConfig(threshold=.3,max_candidates=1))

    def test_seed_and_nonempty(self):
        rows=[row(str(i)) for i in range(10)]
        a=propose_split(rows,seed=1)
        self.assertEqual(a,propose_split(rows,seed=1))
        self.assertNotEqual(a['assignments'],propose_split(rows,seed=2)['assignments'])
        self.assertTrue(all(propose_split(rows,test_fraction=.001)['splits'].values()))

    def test_invalid_fraction(self):
        for value in [0,1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):propose_split([row('a'),row('b')],test_fraction=value)


class FileAndCliTests(unittest.TestCase):
    def test_csv_unicode_multiline(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.csv';p.write_text('\ufefftext,label\n"안녕\n세계",정답\n',encoding='utf-8')
            self.assertEqual(load_records(p),[row('안녕\n세계','정답')])

    def test_bad_csv_headers_and_width(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.csv'
            for content in ['text,text\na,b\n','text,label\na,b,c\n','text,label\na\n']:
                p.write_text(content)
                with self.assertRaises(ValueError):load_records(p)

    def test_jsonl_invalid_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.jsonl'
            for content in ['[]','{"text": NaN}','bad']:
                p.write_text(content)
                with self.assertRaises(ValueError):load_records(p)

    def test_html_script_termination_and_no_remote_assets(self):
        with tempfile.TemporaryDirectory() as d:
            text='</script><script>alert("x")</script><img src=x onerror=alert(1)>'
            result=audit({'train':[row(text)],'test':[row(text)]})
            p=Path(d)/'report.html';write_report(result,p);html=p.read_text()
            self.assertNotIn(text,html)
            payload=html.split('<script id="audit-data" type="application/json">')[1].split('</script>')[0]
            self.assertEqual(json.loads(payload),result)
            self.assertNotIn('innerHTML',html)
            self.assertNotIn('https://',html)

    def test_cli_policy_and_incomplete_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);write_jsonl(p/'a.jsonl',[row('a b'),row('a c')]);write_jsonl(p/'b.jsonl',[row('a d')])
            base=['audit','--split',f'train={p}/a.jsonl','--split',f'test={p}/b.jsonl','--threshold','.3']
            self.assertEqual(main(base+['--out',str(p/'one'),'--fail-on','warning']),1)
            self.assertEqual(main(base+['--out',str(p/'two'),'--fail-on','none']),0)
            self.assertEqual(main(base+['--out',str(p/'three'),'--max-candidates','1']),3)
            self.assertEqual(main(base+['--out',str(p/'one')]),2)

    def test_installed_module_entry_point(self):
        p=subprocess.run([sys.executable,'-m','evalcheck','--version'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0)
        self.assertIn(__version__,p.stdout)


if __name__=='__main__':unittest.main()
