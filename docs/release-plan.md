# Release plan

## Available in v0.5.0

- Standard-library audit engine, Python API and installed CLI.
- Four lexical/group/label checks, source identifiers, explicit incomplete results.
- Connected-component proposals with row preservation and post-audit.
- Standalone HTML evidence explorer with search, filters, export and dataset/protocol context.
- Synthetic examples clearly separated from the full, checksum-pinned UCI public-data case.
- Offline reproduction of original source partitions, a fixed row-random split and a component proposal.
- Real Chromium interaction and mobile overflow checks, unit tests, packaging and CI definitions.
- English/Korean documentation, data attribution and contributor entry points.

- A real classifier comparison with development-only selection, held-out predictions and a zero-crossing uncertainty interval; it is documented as inconclusive improvement evidence.

## Before public promotion

1. Canonical source: https://github.com/Junghwan0516/evalcheck. The provisional distribution name is `evalcheck-local`; no PyPI publication is claimed.
2. Independently review the implementation and interpretations. Run hosted CI; local checks do not establish that hosted CI passed.
3. Measure time and peak memory across representative dataset sizes, lengths and repetition rates. No web-scale throughput claim is currently supported.
4. Record a short demonstration showing a real finding, its source location and a proposal. The included SVG summarizes measured audit results and is not a browser screenshot.
5. Ask a few real users to run their own audits; fix installation and interpretation friction.

## Next contribution-sized tasks

- Reviewed multilingual fixtures and a tokenizer adapter interface.
- Optional Hugging Face input adapters.
- Independent measurement of near-match precision/recall with a task-specific review protocol.
- Multi-column isolation boundaries and explicit class-balance diagnostics.
- Faster candidate enumeration for repetitive corpora, verified against the exact oracle.

## Launch description draft

“EvalCheck is a local text-split auditor with traceable row-level evidence. Its reproducible 3,000-record public-data example exposes overlap in an explicitly generated split and proposes a new component-isolated split without deleting records. It exports a standalone report, requires no API keys and has no runtime dependencies.”

The public-data case does not establish classifier score inflation or invalidate the original authors' work. Stars and forks are reach signals; useful audits and reproducible contributions are the engineering goal.

## Added before launch

Source tracing, a browser-local shared-engine demo, frozen authored challenge, negative-control impact example, pre-commit hook, local composite Action, SARIF schema validation and a manual GitHub Pages deployment workflow are now included. The canonical repository is now configured; independent user/benchmark validation remains open. See GitHub Actions for hosted CI status. The runtime bootstrap needs internet access; no application upload service is used.
