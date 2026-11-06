# Authored Notebook Leakage Challenge v1

This is a **small, developer-authored challenge suite**, not independent external validation or a population-representative notebook benchmark. Eight examples reillustrate concepts from primary documentation; 32 are authored variations and counterexamples, including four explicit unsupported-risk examples. No external repository is represented as having been audited.

The cases and labels were serialized and hashed before the first benchmark invocation. The engine hash at case freeze is compared with its evaluation hash. Labels were not relabeled and the engine was not tuned after seeing this challenge's results. Development unit tests are separate. This local sequencing is not a publicly preregistered study, and the same developer designed both rules and challenge cases.

```bash
python benchmarks/notebooks/evaluate.py
```

| File-level outcome | Count |
|---|---:|
| Risk present, detected | 20 |
| Risk present, missed | 4 |
| Safe example, unflagged | 16 |
| Safe example, flagged | 0 |

There are 24 risk-present cases, including the four unsupported examples. Overall recall is **20/24 = 83.3%**. Authored-suite precision is **20/20 = 100%**; this must not be advertised as real-world precision. The four known misses remain false negatives in the overall metric. No confidence interval or prevalence claim is supported by this small, purposively chosen set.

The missed examples put the risky operation in a function, a branch, an opaque imported helper or an opaque wrapper. These remain useful regression targets for future releases and are not silently excluded from the headline results. Detection does not prove that a real project violates its intended evaluation protocol.

`cases.json` contains the complete source and risk labels. `manifest.json` records hashes and provenance. `results.json` contains each observed rule set and scope note. `build_cases.py` refuses to overwrite an already-frozen case file.

Concept references: [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage), [imbalanced-learn common pitfalls](https://imbalanced-learn.org/stable/common_pitfalls.html#data-leakage). Code snippets are our minimal reillustrations; they are not copied external notebooks or independent expert annotations.
