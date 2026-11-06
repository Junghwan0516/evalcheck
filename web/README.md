# Browser-local demo

Open the generated `index.html` in a modern browser, or serve this directory as static files. No application backend, API key or account is required. On the first scan the worker downloads pinned **Pyodide 0.29.3** assets from jsDelivr; internet access and a browser that permits this runtime bootstrap are required. This is not a fully offline-first browser application.

Input contents are sent to a Web Worker in the same browser, not to an application server. The worker receives JSON in a Python global; it never interpolates file contents into executable Python. Notebook/Python source is parsed with AST and is never executed. The runtime executes only the project's own embedded engine and bridge. A third-party runtime download still has the ordinary trust/supply-chain implications of using that runtime; no claim of absolute privacy or an independent security audit is made.

Supported interactions:

- Leaky/fixed notebook presets and local `.py` / `.ipynb` input.
- An editable Python source mode.
- Real 3,000-record UCI and clearly labelled synthetic data presets.
- Two local CSV/JSONL inputs with explicit text/label/group/source-ID mapping.
- Search/filter evidence, inspect scope notes, export JSON, SARIF (code) and standalone HTML reports.
- Cancellation by terminating the worker. A cancelled run is not a completed audit.

The same Python modules are embedded by `python web/build.py`. The build manifest hashes each module; no separate JavaScript detector is used. Run `node tools/check_wasm.cjs` with the optional `pyodide@0.29.3` Node package to compare WebAssembly decisions on all 40 authored cases and the public-data summary with CPython.

Browser limits: code files up to 2 MB, combined input up to 4 MB, at most 10 code files; data mode needs exactly 2 inputs with up to 5,000 records each. Its lexical comparison budget is 200,000. Large inputs may still consume noticeable browser memory/time. The CLI has a configurable larger budget. Coverage limitations and incomplete scans are shown, not presented as a clean bill of health.

The HTML embeds the demonstration inputs. UCI text/labels retain CC BY 4.0 attribution in the project notices. Pyodide is fetched unmodified from its pinned distribution and is not vendored or relicensed by this project. No runtime binaries are bundled in the deliverable.

## English / 한국어

The playground has an English/Korean language selector. It follows the browser language on the first visit and remembers the selection when storage is available. Switching language preserves inputs, filters and the current audit. HTML export uses the selected language without rescanning.

CLI: `evalcheck scan notebooks --out audit-ko --lang ko`. All four commands accept `--lang en|ko` (default `en`). Python report writers accept `lang="ko"`. UI text is localized; source code, record text, identifiers, canonical JSON/SARIF, fingerprints and detection decisions remain unchanged. This does not add multilingual semantic detection.
