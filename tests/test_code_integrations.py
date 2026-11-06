import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from evalcheck.cli import main
from evalcheck.precommit import main as hook
from evalcheck.code_report import write_code_report
from evalcheck.code_scan import scan_source

ROOT=Path(__file__).resolve().parents[1]
BAD='from sklearn.preprocessing import StandardScaler\nfrom sklearn.model_selection import train_test_split\nZ=StandardScaler().fit_transform(X)\na,b,c,d=train_test_split(Z,y)\n'

class CodeIntegrationTests(unittest.TestCase):
    def test_cli_gate_writes_three_evidence_formats(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);f=p/'bad.py';f.write_text(BAD)
            self.assertEqual(main(['scan',str(f),'--out',str(p/'report')]),1)
            self.assertTrue(all((p/'report'/name).is_file() for name in ['scan.json','scan.sarif','report.html']))
            sarif=json.loads((p/'report/scan.sarif').read_text())
            self.assertEqual(sarif['runs'][0]['results'][0]['ruleId'],'EC001')
            self.assertEqual(main(['scan',str(f),'--out',str(p/'inspect'),'--fail-on','none']),0)

    def test_cli_strict_abstention_and_precommit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);f=p/'function.py';f.write_text('def work():\n return 1\n')
            self.assertEqual(main(['scan',str(f),'--out',str(p/'strict'),'--strict']),3)
            self.assertEqual(hook([str(f)]),0)
            f.write_text(BAD)
            self.assertEqual(hook([str(f)]),1)

    def test_scan_never_executes_inspected_module(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);sentinel=p/'should-not-exist'
            f=p/'danger.py';f.write_text(f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n"+BAD)
            main(['scan',str(f),'--out',str(p/'report'),'--fail-on','none'])
            self.assertFalse(sentinel.exists())

    def test_html_escapes_source_and_paths(self):
        with tempfile.TemporaryDirectory() as d:
            r=scan_source(BAD,path='</script><img onerror=alert(1)>.py')
            p=Path(d)/'report.html';write_code_report([r],p)
            text=p.read_text()
            self.assertNotIn('<img onerror',text)
            self.assertIn('&lt;img onerror',text)

    def test_browser_build_contains_current_engine_hashes(self):
        import hashlib
        manifest=json.loads((ROOT/'web/build-manifest.json').read_text())
        for name,digest in manifest['engine_files'].items():
            self.assertEqual(hashlib.sha256((ROOT/'src/evalcheck'/name).read_bytes()).hexdigest(),digest,name)

if __name__=='__main__':unittest.main()
