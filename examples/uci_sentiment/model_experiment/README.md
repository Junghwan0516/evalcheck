# Model performance study: a small observed gain, not clear improvement evidence

A split auditor should help make model comparisons credible. It does not automatically make a classifier more accurate. This experiment measures an explicit model change under an audited evaluation protocol.

## Measured result

| Same 600 test records | Word unigram baseline | Development-selected word + character model | Difference |
|---|---:|---:|---:|
| Macro-F1 | 0.7949 | 0.8033 | +0.0084 |
| Accuracy | 79.50% | 80.33% | +0.83 percentage points |

The paired component-bootstrap **95% percentile interval for the Macro-F1 difference is [-0.0164, +0.0320]** (equivalently [-1.64, +3.20] percentage points on a 0–100 scale). It includes zero. **The selected model has a higher observed point score, but this experiment does not clearly establish a positive improvement.**

This honest result is retained. The candidates and settings were not changed after final test results became available. It is not appropriate to describe it as a proven gain or to attribute the score difference to EvalCheck itself.

## Fixed before fitting

[plan.json](plan.json) was written locally before fitting models in this experiment; it was not an externally preregistered study. The result records its SHA-256. The full public corpus and source-manifest ordering are the same as the audit case study.

- Hold out 600 component-isolated test records with outer seed 42.
- Split the remaining pool with seed 43 into 1,800 training and 600 development records.
- Require a complete three-way lexical isolation audit with zero overlap rows at threshold 0.8.
- Fit all TF-IDF vocabularies, IDF weights and classifier coefficients on training only.
- Evaluate three predeclared candidates on development only; choose highest Macro-F1, ties alphabetically.
- Save [selection-lock.json](results/selection-lock.json) before predicting the final test set.
- Keep the training-only fits; compare the selected model and the baseline on identical test records. Do not refit on development.
- Report a paired bootstrap over the 591 test connected components (5,000 replicates, fixed bootstrap seed). This preserves dependence within detected lexical groups.

No threshold, candidate hyperparameter or split seed is selected from final test performance. The corpus was previously inspected for audit examples; this is not an independently blinded external evaluation.

## Candidates and development selection

All models use LogisticRegression with the liblinear solver, a fixed random state, and a default prediction rule. No stop-word removal is used.

| Candidate | Features | C | Development Macro-F1 |
|---|---|---:|---:|
| `word_unigram` | Word TF-IDF unigrams | 1.0 | 0.8317 |
| `char_ngrams` | Character-within-word TF-IDF, 3–5 grams | 2.0 | 0.8483 |
| `word_char_union` | Unweighted word 1–2 grams + character-within-word 3–5 grams | 2.0 | **0.8599** |

Only baseline and the development-selected union model are scored on test. The character-only candidate's test performance is not computed. Raw development scores and all configuration details are in [results.json](results/results.json) and the plan.

## Reproduce

From the repository root:

```bash
python -m pip install '.[experiment]'
python examples/uci_sentiment/train_models.py --out my-model-experiment
```

For the recorded environment, use Python 3.12 and `requirements-experiment.txt`. The ML dependencies are optional and are not installed by the core package. No model downloads or API keys are required.

The output contains input splits, source/component assignments, a three-way isolation audit, the copied plan and hash, the selection lock, test predictions, metrics, component-bootstrap intervals and software versions. Model binaries are not distributed; rebuild them from the fixed plan rather than loading untrusted pickle files.

## Interpretation boundary

The score change compares two feature representations and their predeclared regularization values. It does not estimate the causal effect of the auditing tool. The uncertainty interval is conditional on the fitted models, the selected candidate and this split. It does not include retraining variance, split-seed variance, independent dataset replication or deployment distribution shifts.

A larger independent evaluation or a clearly labeled follow-up study is needed before claiming a reliable improvement. Repeatedly modifying models against this now-observed test set would make it unsuitable for an untouched-test claim.

Dataset text/labels retain the UCI CC BY 4.0 attribution in [THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md). Generated splits are ours; no official benchmark split is changed or claimed.
