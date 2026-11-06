"""Deterministic evidence, not a claim that an evaluation is leakage-free."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
import re
import unicodedata
from typing import Any, Mapping, Sequence

from ._version import VERSION


@dataclass(frozen=True)
class AuditConfig:
    text: str = "text"
    label: str | None = "label"
    group: str | None = None
    threshold: float = 0.8
    max_candidates: int = 200_000
    id_column: str | None = None

    def __post_init__(self):
        if isinstance(self.threshold, bool) or not math.isfinite(self.threshold) or not 0 < self.threshold <= 1:
            raise ValueError("threshold must be finite and in (0, 1]")
        if isinstance(self.max_candidates, bool) or not isinstance(self.max_candidates, int) or self.max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        if not isinstance(self.text, str) or not self.text:
            raise ValueError("text must name a nonempty column")
        fields = [f for f in (self.text, self.label, self.group, self.id_column) if f is not None]
        if any(not isinstance(f, str) or not f for f in fields) or len(set(fields)) != len(fields):
            raise ValueError("text, label, group and id_column must name distinct, nonempty columns")


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def tokens(text: str) -> frozenset[str]:
    return frozenset(re.findall(r"\w+", normalize(text), flags=re.UNICODE))


def _prepare(parts: Mapping[str, Sequence[Mapping[str, Any]]], config: AuditConfig):
    records = []
    for split, rows in parts.items():
        if not isinstance(split, str) or not split:
            raise ValueError("split names must be nonempty strings")
        for pos, row in enumerate(rows, 1):
            if not isinstance(row, Mapping):
                raise ValueError(f"{split}:{pos}: record must be an object")
            for field in (config.text, config.label, config.group, config.id_column):
                if field is not None and field not in row:
                    raise ValueError(f"{split}:{pos}: missing column {field!r}")
            text = row[config.text]
            if not isinstance(text, str) or not normalize(text):
                raise ValueError(f"{split}:{pos}: text must be a nonempty string")
            for field in (config.label, config.group, config.id_column):
                if field is not None:
                    value = row[field]
                    if value is None or isinstance(value, (list, dict, bool)) or (isinstance(value, str) and not value.strip()):
                        raise ValueError(f"{split}:{pos}: {field!r} must be a nonempty string or finite number")
                    if not isinstance(value, (str, int, float)) or (isinstance(value, float) and not math.isfinite(value)):
                        raise ValueError(f"{split}:{pos}: {field!r} must be a nonempty string or finite number")
            records.append({"id": f"{split}:{pos}", "split": split, "row": pos,
                            "text": text, "label": row.get(config.label),
                            "group": row.get(config.group), "source_id": row.get(config.id_column), "data": dict(row)})
    return records


def _key(value):
    # Preserve types: integer 1 and string '1' are distinct labels/groups.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _near_pairs(records, config, cross_only=True):
    """Exact token-set Jaccard over all eligible token-overlapping candidates.

    An inverted index plus a length bound prunes impossible matches. No random
    sampling or hidden approximate search. A budget stop is explicitly incomplete.
    """
    index = defaultdict(list)
    normalized = [normalize(r["text"]) for r in records]
    sets = [tokens(text) for text in normalized]
    checked = 0
    pairs = []
    complete = True
    for j, right in enumerate(records):
        current = sets[j]
        candidates = set()
        for token in current:
            candidates.update(index[token])
        for i in sorted(candidates):
            left = records[i]
            if cross_only and left["split"] == right["split"]:
                continue
            if normalized[i] == normalized[j]:
                continue  # separately represented as exact-match clusters
            other = sets[i]
            if min(len(current), len(other)) / max(len(current), len(other)) < config.threshold:
                continue
            if checked >= config.max_candidates:
                complete = False
                return pairs, checked, complete
            checked += 1
            score = len(current & other) / len(current | other)
            if score >= config.threshold:
                pairs.append((i, j, score))
        for token in current:
            index[token].append(j)
    return pairs, checked, complete


def _ref(record):
    ref = {k: record[k] for k in ("id", "split", "row", "text", "label", "group")}
    if record["source_id"] is not None:
        ref["source_id"] = record["source_id"]
    return ref


def audit(parts: Mapping[str, Sequence[Mapping[str, Any]]], config: AuditConfig | None = None) -> dict:
    """Audit named splits. Labels are optional via AuditConfig(label=None).

    Input rows are never modified. Row positions are 1-based data-row positions,
    excluding CSV headers. No model is trained and no labels are auto-corrected.
    """
    config = config or AuditConfig()
    if len(parts) < 2 or any(not rows for rows in parts.values()):
        raise ValueError("provide at least two nonempty splits")
    records = _prepare(parts, config)
    exact = defaultdict(list)
    groups = defaultdict(list)
    for r in records:
        exact[normalize(r["text"])].append(r)
        if config.group is not None:
            groups[_key(r["group"])].append(r)
    findings = []
    def add(kind, severity, members, explanation, **extra):
        findings.append({"id": f"F{len(findings)+1:04d}", "kind": kind,
                         "severity": severity, "records": [_ref(r) for r in members],
                         "explanation": explanation, **extra})
    for members in exact.values():
        if len({r["split"] for r in members}) > 1:
            add("exact_overlap", "error", members,
                "The same normalized text occurs in more than one split.")
        if config.label is not None and len({_key(r["label"]) for r in members}) > 1:
            add("label_conflict", "warning", members,
                "Identical normalized text has different labels. Review task context before changing any label.")
    for members in groups.values():
        if len({r["split"] for r in members}) > 1:
            add("group_overlap", "error", members,
                "A configured isolation group occurs in multiple splits. Confirm that this group should be held out.")
    pairs, checked, complete = _near_pairs(records, config)
    for i, j, score in pairs:
        add("near_overlap", "warning", [records[i], records[j]],
            "Token-set Jaccard meets the configured threshold; similarity alone does not establish leakage.",
            similarity=round(score, 6))
    counts = Counter(f["kind"] for f in findings)
    affected = {r["id"] for f in findings if f["kind"] in ("exact_overlap", "near_overlap", "group_overlap") for r in f["records"]}
    by_split = {}
    for split, rows in parts.items():
        n = sum(r["id"] in affected for r in records if r["split"] == split)
        by_split[split] = {"rows": len(rows), "overlap_rows": n,
                           "overlap_fraction": n / len(rows),
                           "labels": dict(Counter(_key(r["label"]) for r in records if r["split"] == split)) if config.label else {}}
    fingerprint = hashlib.sha256(json.dumps({"parts": parts, "config": asdict(config)},
        ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return {"schema_version": "1.1", "tool_version": VERSION, "fingerprint": fingerprint,
            "status": "incomplete" if not complete else ("review" if findings else "no_findings"),
            "config": asdict(config), "summary": {"rows": len(records), "findings": len(findings),
                "counts": dict(counts), "overlap_rows": len(affected), "splits": by_split},
            "coverage": {"near_search_complete": complete, "candidates_compared": checked,
                         "candidate_budget": config.max_candidates,
                         "method": "NFKC + casefold + whitespace; Unicode word token-set Jaccard"},
            "limitations": ["No findings does not establish a leakage-free evaluation.",
                "No semantic, temporal, feature/target, pretraining or model-selection leakage detection.",
                "Label conflicts may be valid when identical answers have different question context.",
                "Group overlap is meaningful only if the configured group is an isolation boundary.",
                "Token-set similarity ignores word order, token counts and multilingual semantics."],
            "findings": findings}


class _Union:
    def __init__(self, n):
        self.parent = list(range(n))
    def root(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i
    def join(self, i, j):
        self.parent[self.root(j)] = self.root(i)


def propose_split(rows: Sequence[Mapping[str, Any]], config: AuditConfig | None = None,
                  test_fraction: float = 0.2, seed: int = 42, include_near: bool = True):
    """Propose a fresh split. Connected groups/texts stay together; no deletion.

    This changes the evaluation question. Never substitute it for a published
    benchmark split or tune it using held-out performance.
    """
    config = config or AuditConfig()
    if not math.isfinite(test_fraction) or not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be finite and in (0, 1)")
    if len(rows) < 2:
        raise ValueError("at least two rows are required")
    records = _prepare({"input": rows}, config)
    union = _Union(len(records))
    seen_text, seen_group = {}, {}
    for i, r in enumerate(records):
        text = normalize(r["text"])
        if text in seen_text:
            union.join(i, seen_text[text])
        seen_text[text] = i
        if config.group is not None:
            key = _key(r["group"])
            if key in seen_group:
                union.join(i, seen_group[key])
            seen_group[key] = i
    compared = 0
    if include_near:
        pairs, compared, complete = _near_pairs(records, config, cross_only=False)
        if not complete:
            raise ValueError("near search exceeded candidate budget; increase --max-candidates or explicitly use --exact-only")
        for i, j, _ in pairs:
            union.join(i, j)
    components = defaultdict(list)
    for i in range(len(records)):
        components[union.root(i)].append(i)
    chunks = list(components.values())
    if len(chunks) < 2:
        raise ValueError("all rows form one connected component; an isolated train/test split is impossible")
    random.Random(seed).shuffle(chunks)
    # Choose the seeded prefix with a closest attainable row fraction. Always
    # keep both sets nonempty; do not pretend that group sizes permit exact ratios.
    target = len(rows) * test_fraction
    size = 0
    candidates = []
    for k, chunk in enumerate(chunks[:-1], 1):
        size += len(chunk)
        candidates.append((abs(size-target), k))
    _, cut = min(candidates)
    test_ids = {i for chunk in chunks[:cut] for i in chunk}
    output = {"train": [], "test": []}
    assignments = []
    component_ids = {i: f"C{k:05d}" for k, chunk in enumerate(sorted(chunks, key=min), 1) for i in chunk}
    for i, row in enumerate(rows):
        split = "test" if i in test_ids else "train"
        output[split].append(dict(row))
        assignments.append({"input_row": i+1, "component": component_ids[i], "split": split})
    return {"splits": output, "assignments": assignments, "policy": {
        "seed": seed, "requested_test_fraction": test_fraction,
        "actual_test_fraction": len(test_ids)/len(rows), "components": len(chunks),
        "largest_component": max(map(len, chunks)), "include_near": include_near,
        "candidates_compared": compared, "config": asdict(config),
        "stratified": False, "rows_deleted": 0,
        "notice": "A proposal for a new evaluation, not a repair of a fixed benchmark. Inspect class balance and the evaluation question."}}
