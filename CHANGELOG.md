# Changelog

## 0.5.0 — 2026-11-06

- Add English/Korean playground presentation, browser preference detection and saved language selection, preserving current inputs and results.
- Add localized standalone HTML exports and CLI `--lang en|ko`; keep canonical evidence, JSON/SARIF and detection logic unchanged.
- Add translation, raw-evidence preservation, CLI and no-rescan report tests.

## 0.4.0 — 2026-11-06

- Add scoped AST/data-flow analysis of Python and Jupyter source, four review rules, cell/line origin evidence and coverage abstentions. Target code is never executed.
- Add browser-local WebAssembly app using the identical Python engine, real/synthetic presets, editable Python input, file inputs, filtering, exports and cancellation.
- Add scan CLI, pre-commit entry point, a local composite GitHub Action and SARIF 2.1.0 output.
- Publish all authored challenge outcomes including four known misses; add a fixed ten-seed synthetic negative control and WebAssembly/CPython parity checks.

## 0.3.0 — 2026-11-06

- Add a fixed-plan classifier comparison on identical component-isolated test records, with train-only feature fitting and development-only candidate selection.
- Preserve plan hash, selection lock, all development scores, held-out predictions and paired component-bootstrap intervals.
- Report the observed small gain and its zero-crossing interval without claiming proven improvement or a causal accuracy benefit from the auditor.
- Add optional experiment tests and a pinned reference environment; the core retains zero runtime dependencies.

## 0.2.0 — 2026-11-06

- Add a checksum-pinned, offline-reproducible case study on all 3,000 UCI Sentiment Labelled Sentences records, with data attribution and explicit split protocols.
- Preserve configured source identifiers in finding evidence through `AuditConfig(id_column=...)` and CLI `--id-column`.
- Add optional report context for dataset source, license and evaluation protocol; validate source URLs and render all annotations as text.
- Bump audit output schema to 1.1: additive `config.id_column` and optional record `source_id`.
- Fix mobile horizontal overflow caused by hidden form labels receiving full-width toolbar styles.
- Add public-data/parser/provenance tests and real Chromium report checks, including JSON download, pagination and script-injection isolation.

## 0.1.0 — 2026-11-06

- Initial text audit engine, CLI, HTML evidence explorer, connected-component split proposals, synthetic demo and group-memorization experiment.
