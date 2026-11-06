# Methodology and boundaries

## Define the evaluation first

Choose the unit you want to generalize to: a new answer to a known question, a new question, a new patient, a future date, or a new source document. The same overlap can be intended under one protocol and invalid under another. EvalCheck does not infer this choice. `--group` declares one isolation boundary; composite boundaries can be prepared as an extra column before loading.

## Normalization and exact overlap

1. Unicode NFKC normalization.
2. Unicode `casefold()`.
3. Whitespace collapse and trimming.

Punctuation is retained. Blank normalized text is rejected. Text normalization may merge distinctions that matter to a task, so every finding retains original text and source row references.

Identical normalized text is clustered. A cluster spanning multiple supplied splits produces one exact-overlap finding, regardless of cluster size. Label conflicts are checked across all rows, including rows within one split. JSON scalar label/group types are preserved. CSV values are strings.

## Lexical similarity

Tokenize normalized text with Python's Unicode `\w+` regular expression and discard token frequency. Similarity is set Jaccard:

`J(A, B) = |A ∩ B| / |A ∪ B|`

Candidates share at least one token. A size-ratio upper bound removes pairs that cannot reach the threshold. Remaining candidates are compared exactly and deterministically, using ascending source position. Exact normalized matches are excluded from near-pair reporting and handled by exact clusters.

If two nonempty token sets reach a positive threshold, they must share a token. The index therefore does not omit eligible lexical matches when the search completes. The tests compare index results against brute-force computation on randomized fixtures. This is a correctness check, not a real-world accuracy benchmark.

Punctuation-only text can have an empty token set: exact matching still applies, but near matching will not identify it. Token sets ignore order and frequency. Whitespace-poor languages, paraphrases, negation and technical symbols need careful interpretation. A high score does not prove semantic equivalence.

## Budget and scaling

The default budget is 200,000 candidate Jaccard computations. The first additional eligible candidate causes an explicit incomplete result. Exact, group and conflict checks have already run and remain available, but near findings may be missing. Incomplete audits exit `3`, even when `--fail-on none` is set.

The budget does not bound tokenization, inverted-index storage, candidate enumeration or exact-cluster output size. Worst-case repeated-token corpora can still create quadratic enumeration work. There is no validated throughput claim or corpus-size guarantee for this release.

## Split proposals

Build connected components using exact normalized text, a configured group, and optionally all above-threshold near pairs, including within the original data. Transitivity matters: if A shares a group with B and B duplicates C, all three stay together.

Shuffle components using a local `random.Random(seed)` instance. Of the nonempty proper prefixes of that component ordering, select the prefix whose row count is closest to the requested test size. This is deterministic for the same ordered input, configuration and seed. It is not a globally optimal packing algorithm and is not stratified.

All rows and columns are preserved, in original relative order within each output split. A manifest maps each 1-based input data-row position to a component and split. No labels are changed. A fresh audit of the proposed split is written. Near-aware proposals are refused when the similarity search is incomplete; `--exact-only` is an explicit alternative, and its post-audit may report near matches.

One connected component means no nonempty isolated split is possible. Large components can make the requested fraction unattainable. Inspect the actual fraction and label distributions. Do not choose a split seed based on evaluation scores. Do not rewrite official splits and compare the resulting scores as though they used the original benchmark protocol.

## Fingerprint and reproducibility

Optional `id_column` values are preserved as `source_id` in evidence; the configured field must exist on every record. These source identifiers are distinct from generated split/row references and need not be globally unique unless your source contract requires it.

The audit SHA-256 hashes JSON-serialized input content and configuration, with sorted object keys and preserved list order. It is a content fingerprint, not a signature, tamper-proof log or proof of who created the data. Exact file bytes, CSV formatting and filenames are not hashed. Python and scikit-learn versions are recorded separately for the optional experiment.

## Not covered

Semantic paraphrases, timestamps and temporal protocols, target-derived features, feature preprocessing, hyperparameter/model-selection reuse, contamination of foundation-model pretraining data, and data-use permissions are outside this release's checks. A `no_findings` status means no configured lexical/group/label finding was observed, not that an evaluation is safe in all respects.
