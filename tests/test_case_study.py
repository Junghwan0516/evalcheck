import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from evalcheck import AuditConfig, audit, write_report

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('uci_case', ROOT/'examples/uci_sentiment/reproduce.py')
case = importlib.util.module_from_spec(spec)
spec.loader.exec_module(case)


class ProvenanceTests(unittest.TestCase):
    def test_source_id_preserved(self):
        parts={'train':[{'text':'same','label':'0','original':'a.txt:1'}],
               'test':[{'text':'same','label':'0','original':'b.txt:4'}]}
        result=audit(parts,AuditConfig(id_column='original'))
        self.assertEqual([r['source_id'] for r in result['findings'][0]['records']],['a.txt:1','b.txt:4'])
        self.assertEqual(result['schema_version'],'1.1')

    def test_source_id_missing_or_invalid_refused(self):
        for value in [None, '', [], True, float('nan')]:
            with self.assertRaises(ValueError):
                audit({'train':[{'text':'a','label':'0','sid':value}], 'test':[{'text':'b','label':'0','sid':'2'}]},AuditConfig(id_column='sid'))
        with self.assertRaises(ValueError):
            audit({'train':[{'text':'a','label':'0'}], 'test':[{'text':'b','label':'0'}]},AuditConfig(id_column='missing'))

    def test_context_roundtrip_escaped_without_mutating_audit(self):
        result=audit({'train':[{'text':'a','label':'0'}],'test':[{'text':'b','label':'1'}]})
        before=copy.deepcopy(result)
        context={'title':'</script><img onerror=alert(1)>','source_name':'UCI','source_url':'https://archive.ics.uci.edu/dataset/331','license':'CC BY 4.0'}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.html';write_report(result,p,context=context)
            html=p.read_text();payload=html.split('<script id="audit-data" type="application/json">')[1].split('</script>')[0]
            self.assertEqual(json.loads(payload)['report_context'],context)
            self.assertNotIn(context['title'],html)
        self.assertEqual(result,before)

    def test_context_rejects_executable_or_credential_urls(self):
        with tempfile.TemporaryDirectory() as d:
            for url in ['javascript:alert(1)','data:text/html,x','//example.com','https://user:password@example.com','https:///bad']:
                with self.assertRaises(ValueError):write_report({},Path(d)/'x.html',context={'source_url':url})
            with self.assertRaises(ValueError):write_report({},Path(d)/'x.html',context={'not_a_field':'x'})


class PublicDataCaseTests(unittest.TestCase):
    def test_physical_lines_preserve_embedded_unicode_separators(self):
        raw='First\x85sentence\t1\nSecond\u2028sentence\t0\n'.encode()
        rows=case.parse_source(raw,'sample.txt')
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['text'],'First\x85sentence')
        self.assertEqual(rows[1]['source_id'],'sample.txt:2')

    def test_pinned_full_corpus_and_source_overlap_regression(self):
        parts,manifest=case.load_sources()
        self.assertEqual([len(rows) for rows in parts.values()],[1000,1000,1000])
        self.assertEqual(len({r['source_id'] for rows in parts.values() for r in rows}),3000)
        result=audit(parts,case.CONFIG)
        self.assertEqual(result['summary']['counts'],{'exact_overlap':1,'near_overlap':4})
        self.assertEqual(result['summary']['overlap_rows'],7)
        self.assertTrue(result['coverage']['near_search_complete'])

    def test_source_checksum_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);(base/'data').mkdir()
            (base/'source-manifest.json').write_text(json.dumps({'files':{'sample.txt':{'sha256':'not-the-hash','bytes':4,'records':1}}}))
            (base/'data/sample.txt').write_text('x\t0\n')
            with self.assertRaisesRegex(ValueError,'pinned manifest'):case.load_sources(base)

    def test_fixed_seed_preserves_all_source_ids(self):
        parts,_=case.load_sources();rows=[row for subset in parts.values() for row in subset]
        a=case.random_split(rows)
        self.assertEqual(a,case.random_split(rows))
        self.assertEqual([len(a[x]) for x in ['train','test']],[2400,600])
        self.assertEqual({r['source_id'] for rows in a.values() for r in rows},{r['source_id'] for r in rows})
        self.assertFalse({r['source_id'] for r in a['train']}&{r['source_id'] for r in a['test']})


if __name__=='__main__':unittest.main()
