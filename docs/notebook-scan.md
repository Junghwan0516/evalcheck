# Notebook/code risk scanning

`evalcheck scan` traces a scoped set of sklearn/imbalanced-learn data-flow patterns in `.py` and `.ipynb` files. It parses AST and source order; inspected code is never imported, evaluated or executed.

```bash
python -m pip install .
evalcheck scan examples/notebooks/leaky.ipynb --out my-code-audit
```

The command writes `scan.json`, `scan.sarif` and `report.html`, then returns `1` if findings violate the default warning gate. Use `--fail-on none` for inspection without a finding-driven failure. Output directories must be empty.

| Rule | Observable static flow | Typical correction |
|---|---|---|
| EC001 | A known fitted preprocessing result flows into `train_test_split` | Split raw records, fit preprocessing on training only |
| EC002 | A known sklearn/imblearn estimator fits an array tracked as held out | Keep held-out records out of fitting during evaluation |
| EC003 | Prefitted features flow into supported cross-validation/search APIs | Put fitted operations inside the estimator Pipeline |
| EC004 | Resampled records flow into `train_test_split` | Split first; resample training only or use an imblearn Pipeline |

Each finding preserves both the origin and observed-use source locations. Notebook cell numbers count all cells, including Markdown; source-line numbers are relative to the code cell. For SARIF, notebook cell lines are kept in the message/properties, not falsely represented as physical lines in the notebook's JSON file. Python source uses a physical start line.

## Scope is part of the result

Supported analysis follows straight-line module-level statements across notebook cells, known import aliases, direct unpacking of `train_test_split`, simple assignments, selected array wrappers and known fitted objects. It tracks distinct train/held-out branches and avoids treating stateless `Normalizer` as fitted preprocessing. It does not infer that a previously fit estimator leaks into `cross_val_score`, which clones it.

Function/class bodies, branch/loop blocks, custom helper internals, imported project code, general mutation and dynamic execution are outside this version's analysis. Coverage notes disclose skipped scopes, unknown fits, opaque calls, projections and notebook magics. Notebook execution counts that conflict with source order are also disclosed. A file with notes has `partial` status. A file with no detected pattern has `no_findings_in_scope`, never a leakage-free certification.

`--strict` returns `3` when any coverage notes remain, before the normal finding policy. Without `--strict`, notes are reported but do not themselves fail the command. Input limits are 1–500 source/notebook files and 2 MB per file. Standard Git/build/virtual-environment directories are excluded in directory scans.

These rules are policy checks for possible evaluation risks, not an inference that an author's reported performance is invalid. Fitting on a previously held-out cohort can be intentional for a final deployment model after evaluation. Review context and expected workflow before treating a warning as a defect.

## Evidence supporting this release

- 22 targeted source-flow tests, plus integration tests for CLI gates, pre-commit and HTML/SARIF output.
- The [frozen authored challenge](../benchmarks/notebooks/README.md): 40 examples, including explicit limitations in overall recall. This is not external population validation.
- The [synthetic negative control](../examples/notebooks/README.md): a supported feature-selection flow produces inflated scores on unlearnable noise; a training-only Pipeline returns toward chance.
- Browser WebAssembly runs the same engine rather than a JavaScript imitation; the 40 case decisions and the full 3,000-row public-data summary are compared with CPython.

Primary methodological references: [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) and [imbalanced-learn pitfalls](https://imbalanced-learn.org/stable/common_pitfalls.html#data-leakage).
