"""Strict CSV / JSONL loading and output."""
import csv
import json
from pathlib import Path


def load_records(path):
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        if path.suffix.lower() == ".csv":
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            if not fields or any(not f for f in fields) or len(set(fields)) != len(fields):
                raise ValueError(f"{path.name}: CSV requires unique, nonempty column names")
            rows = []
            for i, row in enumerate(reader, 1):
                if None in row or any(v is None for v in row.values()):
                    raise ValueError(f"{path.name}: data row {i} has an inconsistent column count")
                rows.append(row)
            return rows
        if path.suffix.lower() == ".jsonl":
            rows = []
            for i, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(f"nonfinite JSON number: {s}")))
                except (ValueError, json.JSONDecodeError) as e:
                    raise ValueError(f"{path.name}: invalid JSON on line {i}: {e}") from e
                if not isinstance(row, dict):
                    raise ValueError(f"{path.name}: line {i} must be a JSON object")
                rows.append(row)
            return rows
    raise ValueError("supported file formats are .csv and .jsonl")


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+"\n")
