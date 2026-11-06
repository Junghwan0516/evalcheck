# Output contract — schema 1.1

The CLI emits UTF-8 `audit.json` and a self-contained `report.html`. The public Python API returns the same JSON-compatible dictionary.

| Field | Meaning |
|---|---|
| `schema_version` | Output shape version, currently `1.1` |
| `tool_version` | Implementation version |
| `fingerprint` | SHA-256 of canonicalized input content + audit configuration |
| `status` | `review`, `incomplete`, or `no_findings` |
| `config` | Column choices (including optional `id_column`), threshold, candidate budget |
| `summary.rows` | Number of records in all supplied splits |
| `summary.counts` | Number of findings per check kind; absent kinds have count zero |
| `summary.overlap_rows` | Unique rows involved in exact, near or group overlap |
| `summary.splits` | Row and unique-overlap counts/fraction for each split; label counts use JSON-encoded scalar keys |
| `coverage` | Near-search completion, comparisons, budget and method |
| `findings` | Findings with IDs, kind, severity, original row evidence, explanation and optional similarity |
| `limitations` | Scope limitations to keep with downstream interpretations |

Finding IDs are deterministic for the same input order and configuration; they are not stable identities across edited datasets. A record reference includes split, 1-based data-row index, raw text, label and group. Original JSONL physical line numbers may differ when blank lines occur. CSV multiline fields count as one data record.

`incomplete` takes precedence over `review` and `no_findings`. A label-conflict warning may be produced within one split, and does not on its own contribute to overlap-row counts.

Split output adds `manifest.json`: an assignment per input data row, component ID and output split; plus requested/actual fraction, seed, component counts, enabled isolation checks and the audit configuration. It is not a record of model-selection decisions.

Schema 1.1 adds `config.id_column` and optional evidence-record `source_id`. The latter preserves the configured original identifier; row references still retain split and 1-based data-row position. These are additive fields.

`write_report(result, path, context=...)` accepts optional string presentation fields `title`, `protocol`, `source_name`, `source_url`, `license` and `notes`. Report-only JSON export includes `report_context`. Context is not part of the audit fingerprint; source links are restricted to absolute HTTP(S) URLs without credentials.
