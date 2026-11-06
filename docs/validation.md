# Validation record — v0.3.0

Date: 2026-11-06. Local environment: Python 3.12.14, Linux; Chromium 153.0.8010.0; the optional synthetic classifier experiment used scikit-learn 1.8.0.

## Completed

- Built a wheel and source distribution without build warnings, verified packaged report assets and data notices, and installed the wheel in a separate virtual environment. All 35 Python tests also passed against the installed package.
- 35 Python tests: the original 27 plus public-data byte hashes, physical-line parsing, full-corpus overlap regression, provenance identifiers, report context and URL validation.
- 8 dependency-free report DOM-contract scenarios (not browser/layout tests).
- 14 real Chromium checks: report rendering, source context/link, source identifiers, type filter, severity/empty state, source-ID search, evidence expansion, keyboard focus, JSON download, 390px mobile overflow, 61-finding pagination, script/HTML injection isolation, no external requests and no page errors.
- Desktop (1440px) and mobile (390px) QA screenshots were visually inspected as internal checks. A mobile overflow defect in hidden toolbar labels was found and fixed. Screenshots are not distributed with this source bundle.
- The complete public-data case ran offline using checksum-pinned original files: 3 x 1,000 records and balanced source labels. Source-domain audit: 5 findings / 7 overlap rows. Seed-42 row-random audit: 14 findings / 25 overlap rows. Component proposal: 0 findings under configured checks, all 3,000 rows retained.
- Every public-data protocol completed its lexical search. Original files and labels are preserved; source file/line evidence, split assignments, comparison counts and fingerprints are distributed.
- The synthetic five-seed classifier example remains separate: mean row-random accuracy 1.00 versus group-held-out 0.43. It is not a real-world model-performance result.

Package build and installed-wheel checks are recorded as part of delivery verification. The CI workflow includes a Python/OS matrix, packaging, report DOM checks and Chromium checks, but has not run on a hosted repository.

## Remaining limits

Only the stated local Python/OS/browser have been exercised. There is no independent security review, formal accessibility audit, task-specific near-match accuracy benchmark or representative scale/memory benchmark. The public-data case is a reproducibility and evidence demonstration, not a study of classifier performance or author methodology.

GitHub repository creation, public launch and PyPI publication have not been performed. A successful lexical audit does not establish absence of other forms of leakage.

## Added real classifier experiment

The first fixed-plan training run used the v0.2 audit engine (the audit algorithm is unchanged in v0.3). Training/development/test sizes are 1,800/600/600. Development selected word + character features. On identical test rows the baseline Macro-F1 was 0.794931 and the selected model's 0.803314; the 95% paired component-bootstrap difference interval [-0.016419, +0.032041] includes zero. This is not clear positive improvement evidence. The local analysis plan predates fitting but is not externally preregistered. No candidate was changed after observing final test scores.

Five optional ML experiment tests validate scoring against independent metrics, component-resampling invariance, identical-model zero differences, train-only vocabulary fitting and source-aligned saved predictions/plan hashes. A full local run with optional ML dependencies has 40 tests; core-only environments skip these five. The model study does not establish an accuracy benefit caused by the auditing software.

The v0.3 wheel was installed in a separate environment without ML dependencies: 35 core tests passed and 5 optional ML tests were skipped. In the ML-enabled reference environment all 40 tests passed. The standalone model report was checked at desktop and 390px mobile widths.

## v0.4: source tracing, browser runtime and adoption

The v0.4 engine adds 22 source-flow tests and 5 code-integration tests to the earlier 40, for 67 tests in the ML-enabled reference environment. Tests cover fitted preprocessing, held-out fitting, CV/search flows, resampling, aliases, stateless counterexamples, assignments, notebook locations, abstentions, no target execution, CLI gates, pre-commit and source escaping. The generated browser build is checked against current engine hashes.

The frozen authored 40-case challenge returned TP 20 / FP 0 / TN 16 / FN 4, with all four unsupported-risk cases retained in overall recall. Both label-file hash and pre-first-run engine hash are recorded. This is authored validation, not independent population performance.

A Node/Pyodide 0.29.3 parity check passed all 40 code decisions, both bad/fixed notebook presets and the full 3,000-record public-data summary against CPython. Pyodide used Python 3.13.2. The actual browser preview loaded its pinned runtime, found 2 risks in the leaky notebook, found none in the fixed example, completed the 3,000-record audit with 14 findings / 25 overlap rows, and correctly filtered/search-matched a source pair. The browser download-event observation timed out; end-to-end download capture is not claimed. CLI files and in-memory export generation are separately verified. New browser-app mobile layout and custom local-file chooser interactions were not independently exercised in this environment.

SARIF output for all challenge cases and the two-notebook example passed the SARIF 2.1.0 JSON schema using jsonschema 4.25.1; the source schema URL/hash is in sarif-validation.json. This does not establish hosted GitHub ingestion. The composite Action, pre-commit hook and manual Pages workflow are supplied; hosted execution/publication is not performed.

The fixed ten-seed synthetic negative control measured mean apparent test accuracy 79.5% with all-record feature selection and 51.6% with a training-only Pipeline on identical test rows within each replicate. All seeds are reported. This demonstrates a supported evaluation failure on noise, not real-world model-quality improvement or a population effect size.

The final v0.4 wheel installed successfully in a separate core-only environment: 62 tests passed and 5 optional ML tests were skipped. In the ML-enabled reference environment all 67 passed. Installed `evalcheck` and `evalcheck-precommit` entry points returned the expected results on leaky/fixed notebooks.

## v0.5: English/Korean presentation

All 72 tests passed in the ML-enabled reference environment. The installed core-only wheel ran the same suite with 67 passes and 5 optional ML skips. Both distribution formats include localization assets. Browser QA verified language switching after a notebook scan without losing findings, language preference after reload, public-data counts of 14 findings / 25 overlap rows, Korean search and Korean standalone report rendering with original English evidence. Node/Pyodide parity still matches all 40 authored source cases, both notebook presets and the complete public-data summary.

These are local observations. Hosted CI and Pages publish results are recorded by GitHub Actions, not inferred from this document. Historical version sections describe verification at the time of those deliveries.
