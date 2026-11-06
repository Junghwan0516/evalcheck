# Model comparison: measured results

Baseline: `word_unigram`. Development-selected candidate: `word_char_union`.

| Metric | Baseline test | Selected test | Difference (percentage points) |
|---|---:|---:|---:|
| Macro-F1 | 79.49% | 80.33% | +0.84 |
| Accuracy | 79.50% | 80.33% | +0.83 |

Paired component-bootstrap 95% percentile interval for the macro-F1 difference: [-1.64, +3.20] percentage points.

Conclusion: **interval includes zero; no clear positive difference established**.

This compares two models on identical held-out rows. It is not evidence that the auditing software itself raised accuracy. See results.json for split sizes, source attribution, complete development results, plan hash, versions, predictions and limitations.
