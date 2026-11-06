"""Conservative AST/data-flow checks. Target code is never imported or executed.

Scope: straight-line module/notebook source order, known sklearn/imblearn APIs.
Explicit abstentions are part of the output. No general program-proof claim.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from ._version import VERSION

RULES = {
    'EC001': {'name': 'Preprocessing fitted before a holdout split',
              'help': 'Split raw data first; fit preprocessing on training only and transform the held-out set.',
              'reference': 'https://scikit-learn.org/stable/common_pitfalls.html#data-leakage'},
    'EC002': {'name': 'Estimator fitted on held-out records',
              'help': 'Keep validation/test records out of fit, fit_transform and fit_resample during evaluation.',
              'reference': 'https://scikit-learn.org/stable/common_pitfalls.html#data-leakage'},
    'EC003': {'name': 'Prefitted features passed to cross-validation',
              'help': 'Place fitted preprocessing inside a Pipeline so each fold learns it from that fold’s training records.',
              'reference': 'https://scikit-learn.org/stable/common_pitfalls.html#data-leakage'},
    'EC004': {'name': 'Resampling applied before a holdout split',
              'help': 'Split first and resample training only, or use an imbalanced-learn Pipeline within cross-validation.',
              'reference': 'https://imbalanced-learn.org/stable/common_pitfalls.html#data-leakage'},
}
TRANSFORMERS = {
    'sklearn.preprocessing.StandardScaler', 'sklearn.preprocessing.MinMaxScaler',
    'sklearn.preprocessing.MaxAbsScaler', 'sklearn.preprocessing.RobustScaler',
    'sklearn.preprocessing.PowerTransformer', 'sklearn.preprocessing.QuantileTransformer',
    'sklearn.impute.SimpleImputer', 'sklearn.impute.KNNImputer',
    'sklearn.decomposition.PCA', 'sklearn.decomposition.KernelPCA', 'sklearn.decomposition.TruncatedSVD',
    'sklearn.feature_selection.SelectKBest', 'sklearn.feature_selection.SelectPercentile',
    'sklearn.feature_selection.SelectFpr', 'sklearn.feature_selection.SelectFdr', 'sklearn.feature_selection.SelectFwe',
    'sklearn.feature_extraction.text.TfidfVectorizer', 'sklearn.feature_extraction.text.CountVectorizer',
}
STATELESS = {'sklearn.preprocessing.Normalizer', 'sklearn.preprocessing.FunctionTransformer',
             'sklearn.feature_extraction.FeatureHasher'}
SPLIT = 'sklearn.model_selection.train_test_split'
CV = {'sklearn.model_selection.cross_val_score', 'sklearn.model_selection.cross_validate',
      'sklearn.model_selection.cross_val_predict'}
SEARCH = {'sklearn.model_selection.GridSearchCV', 'sklearn.model_selection.RandomizedSearchCV'}
SCALE_FUNCTIONS = {'sklearn.preprocessing.scale', 'sklearn.preprocessing.minmax_scale',
                   'sklearn.preprocessing.robust_scale', 'sklearn.preprocessing.power_transform',
                   'sklearn.preprocessing.quantile_transform'}
MAX_BYTES = 2_000_000


@dataclass(frozen=True)
class Domain:
    root: str
    branches: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Event:
    kind: str
    location: tuple[int | None, int]
    api: str
    domains: tuple[Domain, ...]


@dataclass(frozen=True)
class Value:
    domains: tuple[Domain, ...] = ()
    events: tuple[Event, ...] = ()


@dataclass
class Instance:
    api: str
    fitted: Value | None = None
    fit_event: Event | None = None


def merge(*values):
    return Value(tuple(dict.fromkeys(d for v in values for d in v.domains)),
                 tuple(dict.fromkeys(e for v in values for e in v.events)))


def overlaps(a, b):
    for left in a:
        for right in b:
            if left.root != right.root:
                continue
            x, y = dict(left.branches), dict(right.branches)
            if not any(x[key] != y[key] for key in x.keys() & y.keys()):
                return True
    return False


def heldout(value):
    return any(branch == 'heldout' for domain in value.domains for _, branch in domain.branches)


class Scanner:
    def __init__(self, path):
        self.path = path
        self.aliases = {}
        self.values = {}
        self.objects = {}
        self.findings = []
        self.notes = []
        self.sources = {}
        self.cell = None
        self.serial = 0
        self.split_serial = 0
        self.analyzed_statements = 0
        self.seen = set()
        self.call_objects = {}

    def location(self, node):
        return self.cell, node.lineno

    def api(self, node):
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id, '')
        if isinstance(node, ast.Attribute):
            base = self.api(node.value)
            return f'{base}.{node.attr}' if base else ''
        return ''

    def note(self, code, message, node=None):
        self.notes.append({'kind': code, 'message': message, 'cell': self.cell,
                           'line': getattr(node, 'lineno', None)})

    def source_line(self, location):
        cell, line = location
        lines = self.sources.get(cell, '').split('\n')
        return lines[line-1] if 0 < line <= len(lines) else ''

    def add(self, rule, node, event=None):
        location = self.location(node)
        origin = event.location if event else location
        key = (rule, location, origin)
        if key in self.seen:
            return
        self.seen.add(key)
        self.findings.append({'id': f'C{len(self.findings)+1:04d}', 'rule': rule,
            'severity': 'warning', 'confidence': 'direct_supported_flow',
            'title': RULES[rule]['name'], 'path': self.path,
            'cell': location[0], 'line': location[1], 'code': self.source_line(location),
            'origin': {'cell': origin[0], 'line': origin[1], 'code': self.source_line(origin),
                       'api': event.api if event else None},
            'explanation': 'A supported static data-flow pattern was observed. Review the intended evaluation protocol; this is not a proof of invalid model performance.',
            'suggestion': RULES[rule]['help'], 'reference': RULES[rule]['reference']})

    def instance(self, node):
        if isinstance(node, ast.Name):
            return self.objects.get(node.id)
        if isinstance(node, ast.Call):
            api = self.api(node.func)
            if api.startswith(('sklearn.', 'imblearn.')):
                if node not in self.call_objects:
                    self.call_objects[node] = Instance(api)
                return self.call_objects[node]
        return None

    def data_arg(self, node, pos=0, names=('X', 'x')):
        if len(node.args) > pos:
            return self.value(node.args[pos])
        for kw in node.keywords:
            if kw.arg in names:
                return self.value(kw.value)
        return Value()

    def value(self, node):
        if isinstance(node, ast.Name):
            return self.values.get(node.id, Value((Domain(node.id),)))
        if isinstance(node, (ast.Constant, ast.Lambda)):
            return Value()
        if isinstance(node, ast.Call):
            api = self.api(node.func)
            if api in SCALE_FUNCTIONS:
                data = self.data_arg(node)
                event = Event('preprocessing', self.location(node), api, data.domains)
                return Value(data.domains, data.events+(event,))
            if api in CV:
                data = self.data_arg(node, 1)
                for event in data.events:
                    if overlaps(event.domains, data.domains):
                        self.add('EC003', node, event)
                return Value()
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
                obj = self.instance(node.func.value)
                if obj:
                    data = self.data_arg(node)
                    if method in {'fit', 'fit_transform', 'fit_resample', 'partial_fit'}:
                        if heldout(data) and obj.api not in STATELESS:
                            self.add('EC002', node)
                        if obj.api in SEARCH:
                            for event in data.events:
                                if overlaps(event.domains, data.domains):
                                    self.add('EC003', node, event)
                        kind = 'resampling' if method == 'fit_resample' and obj.api.startswith('imblearn.') else 'preprocessing'
                        event = Event(kind, self.location(node), obj.api, data.domains)
                        obj.fitted, obj.fit_event = data, event
                        stateful = (obj.api in TRANSFORMERS or obj.api.startswith('imblearn.')
                                    or obj.api in {'sklearn.pipeline.Pipeline', 'sklearn.pipeline.make_pipeline'}) and obj.api not in STATELESS
                        if method in {'fit_transform', 'fit_resample'}:
                            return Value(data.domains, data.events+((event,) if stateful else ()))
                        return Value()
                    if method == 'transform':
                        events = data.events + ((obj.fit_event,) if obj.fit_event and obj.api not in STATELESS else ())
                        return Value(data.domains, events)
                    if method in {'predict', 'predict_proba', 'score'}:
                        return Value()
                elif method in {'fit', 'fit_transform', 'fit_resample', 'partial_fit'}:
                    self.note('unresolved_fit', 'Fit receiver is not a supported imported sklearn/imblearn object; no inference made.', node)
            # Preserve visible lineage through simple calls such as np.concatenate,
            # np.asarray, DataFrame operations and .copy(). Unknown helper functions
            # are not analyzed and cannot be assumed to preserve or remove leakage.
            visible = [self.value(arg) for arg in node.args]
            if isinstance(node.func, ast.Attribute) and self.api(node.func.value) == '':
                visible.append(self.value(node.func.value))
            if api.startswith(('numpy.', 'pandas.')) or (isinstance(node.func, ast.Attribute) and node.func.attr in {'copy', 'astype', 'reshape', 'to_numpy'}):
                return merge(*visible)
            if any(value.events or heldout(value) or (api and not api.startswith(("sklearn.","imblearn.")) and value.domains) for value in visible):
                self.note('opaque_call', 'Tracked data passes through an unmodeled call; its output lineage is not inferred.', node)
            return Value()
        if isinstance(node, ast.Attribute):
            return self.value(node.value)
        if isinstance(node, ast.Subscript):
            # Column/index projections preserve the known parent cohort; row
            # filtering semantics are not inferred, so record the limitation.
            self.note('projection', 'Index/column projection is tracked conservatively; row-filter semantics are not resolved.', node)
            return self.value(node.value)
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return merge(*(self.value(e) for e in node.elts))
        if isinstance(node, ast.BinOp):
            return merge(self.value(node.left), self.value(node.right))
        return Value()

    def bind(self, target, value, source_node=None):
        if isinstance(target, ast.Name):
            self.serial += 1
            self.values[target.id] = value if value.domains else Value((Domain(f'{target.id}@{self.serial}'),), value.events)
            self.objects.pop(target.id, None)
            self.aliases.pop(target.id, None)
            if isinstance(source_node, ast.Name):
                obj = self.objects.get(source_node.id)
                if obj:
                    self.objects[target.id] = obj
            elif source_node is not None:
                obj = self.instance(source_node)
                if obj:
                    self.objects[target.id] = obj
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self.bind(item, value)
        else:
            self.note('mutation', 'Attribute/subscript assignment is not analyzed; state tracking reset.', target)
            self.values.clear();self.objects.clear()

    def statement(self, node):
        self.analyzed_statements += 1
        if isinstance(node, ast.Import):
            for item in node.names:
                name=item.asname or item.name.split('.')[0]
                self.aliases[name]=item.name if item.asname else item.name.split('.')[0]
                self.values.pop(name,None);self.objects.pop(name,None)
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                if item.name=='*':
                    self.note('star_import', 'Star imports are not resolved.', node)
                else:
                    name=item.asname or item.name
                    self.aliases[name]=f'{node.module}.{item.name}'
                    self.values.pop(name,None);self.objects.pop(name,None)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            source=node.value
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            if source is None:
                return
            if isinstance(source,ast.Call) and self.api(source.func)==SPLIT:
                self.split_serial += 1
                split_id=f'split{self.split_serial}'
                data=[self.value(arg) for arg in source.args]
                for value in data:
                    for event in value.events:
                        if overlaps(event.domains,value.domains):
                            self.add('EC004' if event.kind=='resampling' else 'EC001',source,event)
                if len(targets)==1 and isinstance(targets[0],(ast.Tuple,ast.List)) and len(targets[0].elts)==2*len(data):
                    for i,target in enumerate(targets[0].elts):
                        value=data[i//2]
                        branch='train' if i%2==0 else 'heldout'
                        domains=tuple(Domain(d.root,d.branches+((split_id,branch),)) for d in value.domains)
                        self.bind(target,Value(domains,value.events))
                else:
                    self.note('split_unpack', 'train_test_split output is not directly unpacked into two variables per positional array.',source)
                    for target in targets:self.bind(target,Value())
            else:
                value=self.value(source)
                # A fit() chained assignment returns the same instance; evaluate
                # it once before binding rather than executing target code.
                obj = self.instance(source.func.value) if isinstance(source,ast.Call) and isinstance(source.func,ast.Attribute) and source.func.attr=='fit' else None
                for target in targets:
                    self.bind(target,value,source)
                    if obj and isinstance(target,ast.Name):self.objects[target.id]=obj
        elif isinstance(node,ast.Expr):
            self.value(node.value)
        elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            self.note('scope_skipped','Function/class bodies are not analyzed; source-order analysis does not follow calls.',node)
            self.aliases.pop(node.name,None);self.values.pop(node.name,None);self.objects.pop(node.name,None)
        elif isinstance(node,(ast.If,ast.For,ast.AsyncFor,ast.While,ast.Try,ast.With,ast.AsyncWith,ast.Match)):
            self.note('control_flow_skipped','Control-flow block is not analyzed; tracked data/object state is reset.',node)
            self.values.clear();self.objects.clear()
        elif isinstance(node,(ast.AugAssign,ast.Delete)):
            self.note('mutation','Mutation is not analyzed; tracked state is reset.',node)
            self.values.clear();self.objects.clear()
        elif not isinstance(node,(ast.Pass,ast.Assert)):
            self.note('unsupported_statement',f'{type(node).__name__} is outside the supported straight-line analysis.',node)

    def cell_source(self, source, cell=None):
        self.cell=cell;self.sources[cell]=source
        lines=source.split('\n')
        if any(line.lstrip().startswith('%%') for line in lines):
            self.note('cell_magic','Cell-magic body skipped; tracked state reset.')
            self.values.clear();self.objects.clear();return
        sanitized=[]
        for i,line in enumerate(lines,1):
            if line.lstrip().startswith(('%','!','?')):
                self.notes.append({'kind':'line_magic','message':'Notebook magic/shell line skipped.','cell':cell,'line':i})
                sanitized.append(' '*(len(line)-len(line.lstrip()))+'pass')
            else:sanitized.append(line)
        try:
            tree=ast.parse('\n'.join(sanitized))
        except (SyntaxError,RecursionError,ValueError) as error:
            self.note('parse_error',f'Cell/source not parsed: {error}')
            self.values.clear();self.objects.clear();return
        for node in tree.body:self.statement(node)

    def result(self, fingerprint):
        return {'schema_version':'1.0','tool_version':VERSION,'kind':'code_scan','path':self.path,
                'fingerprint':fingerprint,'status':'partial' if self.notes else 'findings' if self.findings else 'no_findings_in_scope',
                'findings':self.findings,'coverage':{'analyzed_statements':self.analyzed_statements,'notes':self.notes,
                    'scope':'Straight-line module/notebook source order; known sklearn/imblearn APIs. No code execution.'},
                'limitations':['Static patterns require protocol review; no findings is not a leakage-free certification.',
                    'Function bodies, control flow, custom transformers/helpers and cross-file execution are not followed.',
                    'Notebook source order can differ from execution order; cells are never executed.',
                    'No temporal, target-derived-feature, semantic or foundation-model contamination checks.']}


def scan_source(source: str, *, path='snippet.py'):
    if len(source.encode('utf-8'))>MAX_BYTES:raise ValueError('source exceeds 2 MB scan limit')
    scanner=Scanner(path);scanner.cell_source(source)
    return scanner.result(hashlib.sha256(source.encode()).hexdigest())


def scan_notebook(notebook: dict, *, path='notebook.ipynb'):
    if not isinstance(notebook,dict) or not isinstance(notebook.get('cells'),list):
        raise ValueError('notebook must be an object with a cells array')
    encoded=json.dumps(notebook,ensure_ascii=False).encode()
    if len(encoded)>MAX_BYTES:raise ValueError('notebook exceeds 2 MB scan limit')
    scanner=Scanner(path);counts=[]
    for index,cell in enumerate(notebook['cells'],1):
        if not isinstance(cell,dict):raise ValueError('each notebook cell must be an object')
        if cell.get('cell_type')!='code':continue
        source=cell.get('source','')
        if isinstance(source,list) and all(isinstance(x,str) for x in source):source=''.join(source)
        if not isinstance(source,str):raise ValueError('code cell source must be a string or list of strings')
        count=cell.get('execution_count')
        if isinstance(count,int):counts.append(count)
        scanner.cell_source(source,index)
    if counts!=sorted(set(counts)):
        scanner.notes.append({'kind':'execution_order','message':'Execution counts are repeated/out of source order; source-order results may not match the executed notebook.','cell':None,'line':None})
    return scanner.result(hashlib.sha256(encoded).hexdigest())


def scan_path(path):
    path=Path(path)
    if path.stat().st_size>MAX_BYTES:raise ValueError(f'{path.name}: file exceeds 2 MB scan limit')
    source=path.read_text(encoding='utf-8-sig')
    if path.suffix=='.py':return scan_source(source,path=path.name)
    if path.suffix=='.ipynb':return scan_notebook(json.loads(source),path=path.name)
    raise ValueError('code scan supports .py and .ipynb files')


def to_sarif(results):
    rules=[{'id':key,'name':value['name'].replace(' ','').replace('-',''),
            'shortDescription':{'text':value['name']},'helpUri':value['reference'],
            'help':{'text':value['help']},'defaultConfiguration':{'level':'warning'}} for key,value in RULES.items()]
    findings=[]
    for result in results:
        for f in result['findings']:
            physical={'artifactLocation':{'uri':quote(f['path'].replace('\\','/'),safe='/')}}
            message=f"{f['title']}. {f['suggestion']}"
            if f['cell'] is None:
                physical['region']={'startLine':f['line'],'startColumn':1}
            else:
                message+=f" Notebook cell {f['cell']}, source line {f['line']}; origin cell {f['origin']['cell']}, line {f['origin']['line']}."
            findings.append({'ruleId':f['rule'],'level':'warning','message':{'text':message},
                'locations':[{'physicalLocation':physical}],
                'properties':{'cell':f['cell'],'cellLine':f['line'],'origin':f['origin'],
                    'confidence':f['confidence']},
                'partialFingerprints':{'evalcheckFlow/v1':hashlib.sha256(json.dumps([f['path'],f['rule'],f['cell'],f['line'],f['origin']],sort_keys=True).encode()).hexdigest()}})
    return {'$schema':'https://json.schemastore.org/sarif-2.1.0.json','version':'2.1.0',
        'runs':[{'tool':{'driver':{'name':'EvalCheck','semanticVersion':VERSION,'rules':rules}},
                 'results':findings}]}
