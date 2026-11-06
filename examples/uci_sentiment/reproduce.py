"""Offline, checksum-verified real-data case study. No third-party dependencies.

From the repository root:
  python examples/uci_sentiment/reproduce.py --out my-uci-case

Source partitions are not official train/test splits. Generated protocols are
explicitly ours, and cannot be compared as an author's published benchmark.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import sys
import time

# Also support a source checkout without installation.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from evalcheck import AuditConfig, audit, propose_split, write_report
from evalcheck.io import write_json, write_jsonl

BASE = Path(__file__).resolve().parent
CONFIG = AuditConfig(id_column="source_id", threshold=.8, max_candidates=2_000_000)


def parse_source(raw: bytes, filename: str):
    """Preserve physical LF-delimited records and source line provenance.

    str.splitlines() also breaks on embedded Unicode controls, which occur in
    this corpus. CSV parsers may also interpret quotes that this TSV never
    declared as delimiters. Decode UTF-8 and split LF only, then the last tab.
    """
    rows = []
    for line_number, line in enumerate(raw.decode("utf-8").split("\n"), 1):
        line = line.removesuffix("\r")
        if not line:
            continue
        if "\t" not in line:
            raise ValueError(f"{filename}:{line_number}: missing tab separator")
        text, label = line.rsplit("\t", 1)
        if label not in {"0", "1"} or not text.strip():
            raise ValueError(f"{filename}:{line_number}: invalid label or empty text")
        rows.append({"text": text, "label": label, "source_id": f"{filename}:{line_number}",
                     "domain": filename.removesuffix("_labelled.txt")})
    return rows


def load_sources(base=BASE):
    manifest = json.loads((base / "source-manifest.json").read_text(encoding="utf-8"))
    parts = {}
    for filename, expected in manifest["files"].items():
        raw = (base / "data" / filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected["sha256"] or len(raw) != expected["bytes"]:
            raise ValueError(f"source bytes do not match pinned manifest: {filename}")
        rows = parse_source(raw, filename)
        if len(rows) != expected["records"]:
            raise ValueError(f"unexpected record count: {filename}")
        parts[filename.removesuffix("_labelled.txt")] = rows
    return parts, manifest


def random_split(rows, seed=42):
    ids = list(range(len(rows)))
    random.Random(seed).shuffle(ids)
    test_ids = set(ids[:round(len(rows) * .2)])
    return {"train": [dict(row) for i, row in enumerate(rows) if i not in test_ids],
            "test": [dict(row) for i, row in enumerate(rows) if i in test_ids]}


def context(manifest, title, protocol):
    return {"title": title, "protocol": protocol, "source_name": manifest["dataset"],
            "source_url": manifest["landing_page"], "license": manifest["license"],
            "notes": "Real public data, not planted findings. Derived protocols are authored by this example; these are not official benchmark train/test splits. Dataset text is CC BY 4.0. Similarity does not establish semantic equivalence or score inflation."}


def run(out):
    parts, manifest = load_sources()
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory must be empty")
    out.mkdir(parents=True, exist_ok=True)
    rows = [row for subset in parts.values() for row in subset]
    for name, subset in parts.items():
        write_jsonl(out / f"{name}.jsonl", subset)
    write_json(out / "source-manifest.json", manifest)
    results = {}
    protocols = [
        ("source-partitions", parts, "Cross-source overlap audit",
         "Original Amazon, IMDb and Yelp source files are inspected as three named partitions (1,000 records each). These are source domains, not train/test sets."),
        ("row-random", random_split(rows), "Row-random split · seed 42",
         "Example-authored split: shuffle positional indices with Python Random(42), place the first 600 in test, preserve source order within each output. 2,400 train / 600 test records."),
    ]
    start = time.perf_counter()
    proposal = propose_split(rows, CONFIG, seed=42, test_fraction=.2)
    protocols.append(("component-proposal", proposal["splits"], "Connected-component split proposal · seed 42",
        "A fresh split proposal holds exact-normalized and above-threshold lexical connected components together. No source rows or labels are changed. This changes the held-out examples; it is not a causal comparison of model performance."))
    for name, sets, title, protocol in protocols:
        folder = out / name
        folder.mkdir()
        for split, subset in sets.items():
            write_jsonl(folder / f"{split}.jsonl", subset)
        start = time.perf_counter()
        result = audit(sets, CONFIG)
        elapsed = time.perf_counter() - start
        if not result["coverage"]["near_search_complete"]:
            raise ValueError(f"incomplete audit for {name}; do not publish a full-coverage claim")
        write_json(folder / "audit.json", result)
        write_report(result, folder / "report.html", context=context(manifest, title, protocol))
        results[name] = {"status": result["status"], "summary": result["summary"],
                         "coverage": result["coverage"], "fingerprint": result["fingerprint"]}
        print(f"{name}: {result['summary']['findings']} findings; {result['summary']['overlap_rows']} unique overlap rows; {elapsed:.2f}s (single local run)")
    write_json(out / "component-proposal" / "manifest.json", {k: v for k, v in proposal.items() if k != "splits"})
    summary = {"kind": "real_public_dataset_case_study", "dataset": manifest["dataset"],
               "rows": len(rows), "labels": dict(Counter(row["label"] for row in rows)),
               "source": manifest, "seed": 42, "config": asdict(CONFIG),
               "protocols": results, "proposal_policy": proposal["policy"],
               "interpretation": "Observed overlap evidence, not evidence of model-score inflation. No classifier was trained in this case study. No official benchmark split was modified."}
    write_json(out / "case-summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("my-uci-case"))
    args = parser.parse_args()
    try:
        run(args.out)
    except (OSError, ValueError) as error:
        parser.exit(2, f"case study: {error}\n")


if __name__ == "__main__":
    main()
