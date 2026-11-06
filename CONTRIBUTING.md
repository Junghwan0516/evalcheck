# Contributing

Start by running the demo and the standard-library test suite:

```bash
python -m pip install .
python -m unittest discover -s tests -v
evalcheck demo --out my-demo
```

For a bug report, include Python/OS versions, a minimal synthetic reproducer, the exact command, expected behavior and actual JSON output. Never attach private production records just to demonstrate a bug.

For a new detector, propose its evaluation meaning and counterexamples first. It must name the evidence type, preserve source-row references, state its scope, and expose incomplete computation rather than returning a false all-clear. Keep optional model dependencies out of the core package. Add fixtures covering a true finding and a plausible false positive. The near-pair oracle and split-preservation tests must continue to pass.

For report changes, test a narrow viewport, search, each filter, empty results, pagination, keyboard focus, export and user-controlled HTML/script-like text. Use textContent for dataset content; never interpolate it as HTML. Keep all report assets local.

For public-data examples, include the source, license, extraction recipe, intended evaluation unit, review method and all limitations. Keep demo issues labeled as synthetic.

Open a small issue or pull request with the problem, resulting behavior and meaningful validation. Maintainers can label fixture improvements and documentation fixes as good first issues after review.
