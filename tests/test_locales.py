import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from evalcheck import AuditConfig, audit
from evalcheck.cli import main
from evalcheck.code_scan import scan_source
from evalcheck.code_report import write_code_report
from evalcheck.report import write_report
from evalcheck.locales import tr, language, locale_script

ROOT=Path(__file__).resolve().parents[1]
BAD='from sklearn.preprocessing import StandardScaler\nfrom sklearn.model_selection import train_test_split\nZ=StandardScaler().fit_transform(X)\na,b,c,d=train_test_split(Z,y)\n'
class LocaleTests(unittest.TestCase):
    def test_language_validation_and_literal_values(self):
        with self.assertRaises(ValueError):language('fr')
        self.assertEqual(tr('Findings','ko'),'검사 항목')
        self.assertEqual(tr('Report: {path}','ko',path='${unchanged}<x>'),'보고서: ${unchanged}<x>')
        self.assertNotIn('__LOCALE_CATALOG__',locale_script('ko'))

    def test_data_report_keeps_canonical_evidence_and_fingerprint(self):
        value='Findings 한국어 <script>alert(1)</script>'
        result=audit({'train':[{'text':value,'label':'Warning'}], 'test':[{'text':value,'label':'Warning'}]},AuditConfig())
        before=copy.deepcopy(result)
        with tempfile.TemporaryDirectory() as d:
            for lang in ['en','ko']:
                path=Path(d)/f'{lang}.html';write_report(result,path,lang=lang)
                page=path.read_text(encoding='utf-8');self.assertIn(f'<html lang="{lang}">',page)
                data=json.loads(re.search(r'<script id="audit-data" type="application/json">(.*?)</script>',page,re.S)[1])
                self.assertEqual(data,result)
                self.assertIn("raw('p',r.text)",page)
                self.assertNotIn('<script>alert(1)</script>',page)
        self.assertEqual(result,before)

    def test_code_report_and_cli_korean(self):
        result=scan_source(BAD,path='Findings.py');before=copy.deepcopy(result)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'ko.html';write_code_report([result],path,lang='ko')
            page=path.read_text(encoding='utf-8');self.assertIn('홀드아웃 분할 전에 전처리를 학습함',page)
            self.assertIn('scaler',page.lower());self.assertIn('Findings.py',page)
            code=Path(d)/'bad.py';code.write_text(BAD, encoding='utf-8')
            out=io.StringIO()
            with contextlib.redirect_stdout(out):status=main(['scan',str(code),'--out',str(Path(d)/'out'),'--lang','ko'])
            self.assertEqual(status,1);self.assertIn('코드 검사:',out.getvalue());self.assertIn('보고서:',out.getvalue())
        self.assertEqual(result,before)

    def test_bridge_rerender_does_not_recompute_or_mutate(self):
        spec=importlib.util.spec_from_file_location('locale_bridge',ROOT/'web/bridge.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
        result=bridge.handle_request({'mode':'code','files':[{'name':'bad.py','text':BAD}]})
        before=copy.deepcopy(result)
        bridge.scan_source=lambda *a,**kw: self.fail('render must not scan again')
        rendered=bridge.handle_request({'mode':'render','lang':'ko','result':result})
        self.assertEqual(rendered['kind'],'render');self.assertIn('<html lang="ko">',rendered['report_html']);self.assertEqual(result,before)

    def test_browser_translation_template_precedence(self):
        import shutil, subprocess
        if not shutil.which('node'):self.skipTest('Node required for JS contract')
        setup="const assert=require('node:assert/strict'),window={},NodeFilter={SHOW_TEXT:4},document={documentElement:{},body:{},createTreeWalker:()=>({nextNode:()=>null}),querySelectorAll:()=>[]};"
        checks="assert.equal(window.evalcheckLocale.translate('ERROR · 2 rows'),'오류 · 2행');assert.equal(window.evalcheckLocale.translate('cell 3 · line 7'),'셀 3 · 7행');window.evalcheckLocale.setLanguage('en');assert.equal(window.evalcheckLocale.translate('Findings'),'Findings');"
        subprocess.run(['node','-e',setup+locale_script('ko')+checks],check=True,capture_output=True)
