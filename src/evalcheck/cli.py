"""CLI exit codes: 0 complete; 1 policy failure; 2 usage; 3 incomplete."""
import argparse
import csv
import json
from pathlib import Path
import sys

from ._version import VERSION
from .code_scan import scan_path, to_sarif
from .code_report import write_code_report
from .core import AuditConfig, audit, propose_split
from .demo import make_demo
from .io import load_records, write_json, write_jsonl
from .report import write_report
from .locales import tr, localize_error


def _config(args):
    return AuditConfig(text=args.text, label=None if args.no_label else args.label,
                       group=args.group, threshold=args.threshold,
                       max_candidates=args.max_candidates, id_column=args.id_column)


def _fields(p):
    p.add_argument("--text", default="text", help="Text column (default: text)")
    p.add_argument("--label", default="label", help="Label column (default: label)")
    p.add_argument("--no-label", action="store_true", help="Skip label validation and conflict checks")
    p.add_argument("--id-column", help="Column preserving a stable source record identifier in evidence")
    p.add_argument("--group", help="Column defining an evaluation isolation boundary")
    p.add_argument("--threshold", type=float, default=.8, help="Token-set Jaccard threshold (default: .8)")
    p.add_argument("--max-candidates", type=int, default=200_000, help="Maximum similarity comparisons")


def _out(path):
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"output directory must be empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="evalcheck", description="Before you trust the score, inspect the split.")
    parser.add_argument("--version", action="version", version=f"evalcheck {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("audit", help="Inspect named CSV / JSONL splits")
    p.add_argument("--split", action="append", required=True, metavar="NAME=PATH")
    p.add_argument("--out", type=Path, default=Path("evalcheck-report"))
    p.add_argument("--fail-on", choices=["none", "error", "warning"], default="error", help="CI policy; warnings includes errors")
    _fields(p)
    p = sub.add_parser("split", help="Propose fresh splits without discarding rows")
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, default=Path("evalcheck-split"))
    p.add_argument("--test-fraction", type=float, default=.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--exact-only", action="store_true", help="Explicitly skip near-duplicate isolation")
    _fields(p)
    p = sub.add_parser("scan", help="Find supported evaluation-risk patterns in .py / .ipynb source; never executes it")
    p.add_argument("path", type=Path)
    p.add_argument("--out", type=Path, default=Path("evalcheck-code-report"))
    p.add_argument("--fail-on", choices=["none", "warning"], default="warning")
    p.add_argument("--strict", action="store_true", help="Exit 3 when any scope/coverage notes remain")
    p = sub.add_parser("demo", help="Generate a labeled synthetic demonstration")
    p.add_argument("--out", type=Path, default=Path("evalcheck-demo"))
    for command in sub.choices.values():
        command.add_argument("--lang", choices=["en","ko"], default="en", help="Report and console language (default: en)")
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            root=args.path
            if root.is_file():
                paths=[root]
            elif root.is_dir():
                ignored={'.git','.venv','venv','node_modules','__pycache__','build','dist'}
                paths=sorted(p for p in root.rglob('*') if p.suffix in {'.py','.ipynb'} and p.is_file() and not any(part in ignored for part in p.relative_to(root).parts))
            else:raise ValueError(f"scan path does not exist: {root}")
            if not paths or len(paths)>500:raise ValueError('scan requires 1–500 Python/notebook files')
            results=[]
            for path in paths:
                result=scan_path(path)
                relative=path.relative_to(root).as_posix() if root.is_dir() else path.name
                result['path']=relative
                for finding in result['findings']:finding['path']=relative
                results.append(result)
            _out(args.out)
            write_json(args.out/'scan.json',{'kind':'code_scan_collection','files':results})
            write_json(args.out/'scan.sarif',to_sarif(results))
            write_code_report(results,args.out/'report.html',lang=args.lang)
            count=sum(len(r['findings']) for r in results)
            partial=sum(bool(r['coverage']['notes']) for r in results)
            print(tr("CODE SCAN: {files} files; {count} findings; {partial} files with scope notes",args.lang,files=len(results),count=count,partial=partial))
            print(tr("Report: {path}",args.lang,path=(args.out/"report.html").resolve()))
            if args.strict and partial:return 3
            return 1 if count and args.fail_on=='warning' else 0
        elif args.command == "demo":
            _out(args.out)
            result = make_demo(args.out,lang=args.lang)
            print(tr("Synthetic demonstration — findings intentionally planted.",args.lang))
        elif args.command == "split":
            result = propose_split(load_records(args.input), _config(args), args.test_fraction, args.seed, not args.exact_only)
            _out(args.out)
            for name, rows in result["splits"].items():
                write_jsonl(args.out / f"{name}.jsonl", rows)
            write_json(args.out / "manifest.json", {k: v for k, v in result.items() if k != "splits"})
            post = audit(result["splits"], _config(args))
            write_json(args.out / "audit.json", post)
            write_report(post, args.out / "report.html",lang=args.lang)
            print(tr("Proposed {train} train / {test} test rows; deleted 0.",args.lang,train=len(result["splits"]["train"]),test=len(result["splits"]["test"])))
            print(tr(result["policy"]["notice"],args.lang))
            print(tr("Post-split audit: {status}; {count} findings",args.lang,status=tr(post["status"],args.lang),count=post["summary"]["findings"]))
            print(tr("Report: {path}",args.lang,path=(args.out/"report.html").resolve()))
            return 3 if post["status"] == "incomplete" else 0
        else:
            parts = {}
            for spec in args.split:
                name, sep, path = spec.partition("=")
                if not sep or not name or not path or name in parts:
                    raise ValueError("each --split must be a unique NAME=PATH")
                parts[name] = load_records(path)
            result = audit(parts, _config(args))
            _out(args.out)
            write_json(args.out / "audit.json", result)
            write_report(result, args.out / "report.html",lang=args.lang)
        print(tr("{status}: {count} findings / {rows} rows",args.lang,status=tr(result["status"],args.lang).upper(),count=result["summary"]["findings"],rows=result["summary"]["rows"]))
        print(tr("Report: {path}",args.lang,path=(args.out/"report.html").resolve()))
        if result["status"] == "incomplete":
            return 3
        if args.command == "audit":
            levels = {"none": set(), "error": {"error"}, "warning": {"error", "warning"}}
            if any(f["severity"] in levels[args.fail_on] for f in result["findings"]):
                return 1
        return 0
    except (ValueError, OSError, csv.Error) as e:
        print(f"evalcheck: {localize_error(str(e),args.lang)}", file=sys.stderr)
        return 2

