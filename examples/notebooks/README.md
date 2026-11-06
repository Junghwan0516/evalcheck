# From code evidence to a measured evaluation failure

Try both notebooks:

```bash
evalcheck scan examples/notebooks/leaky.ipynb --out my-leaky-audit --fail-on none
evalcheck scan examples/notebooks/fixed.ipynb --out my-fixed-audit --fail-on none
```

The leaky notebook produces EC001 at cell 3 line 1, traced to the fitted scaler at cell 2 line 2, and EC002 at cell 3 line 3. The corrected version splits first, fits a Pipeline on training only and predicts held-out records; no supported pattern is found. These notebooks illustrate source analysis and use placeholder input arrays. The scanner never executes them.

## Fixed synthetic negative control

To measure a consequence of the feature-selection pattern:

```bash
python -m pip install '.[experiment]'
python examples/notebooks/impact_experiment.py
```

The analysis plan in `impact_plan.json` was written locally before running the experiment. It specifies all ten seeds, independent random labels, Gaussian noise features, selected-feature count, split fraction, model and reporting rule. No setting was changed after observing results.

| Same raw test rows within each replicate | Mean accuracy across 10 noise datasets |
|---|---:|
| Feature selection fitted on all records before splitting | 79.5% |
| Feature selection inside a training-only Pipeline | 51.6% |
| Mean apparent score excess | 27.9 percentage points |

There is no predictive relationship to learn by construction. The first protocol lets feature selection see held-out labels; the second does not. This is **inflated evaluation exposed**, not a claim that the tool improves a real classifier's accuracy. It does not estimate prevalence or effect size on real projects. The test sets are identical within each paired replicate.

All ten results are reported, including the plan hash, software versions and scanner output for minimal bad/fixed source illustrations in `impact_results.json`. The scanner finds EC001 in the bad illustration and no supported pattern in the fixed one. The source illustrations correspond to the operations in the explicit experiment; they are not arbitrary uploaded code being executed.

The earlier [public sentiment model comparison](../uci_sentiment/model_experiment/README.md), with its inconclusive small gain, is retained. The negative control answers a different question and does not supersede that real-data result.
