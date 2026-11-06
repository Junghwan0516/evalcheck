# Security

The CLI is a pre-release local utility with no hosted service, telemetry, network calls or automatic model downloads. The optional browser app downloads pinned Pyodide assets on first use, then analyzes input in a Web Worker; it has no application upload endpoint. The generated report embeds matched source text and labels; review it before sharing. JSON exports contain the same row evidence.

Dataset text is serialized into an inert JSON script with `<`, `>` and `&` escaped. The interactive report inserts text via `textContent`, never `innerHTML`. Tests cover closing-script payloads. This does not replace an independent security review.

Large or highly repetitive inputs can consume substantial memory/time despite the similarity-comparison budget. Run untrusted large inputs with appropriate resource limits. EvalCheck does not execute source records, deserialize pickle files or import dataset-provided code.

Once a public repository exists, enable GitHub private vulnerability reporting. Until then, do not publish exploit payloads containing sensitive data; use a minimal synthetic reproducer. No reporting address is claimed by this source bundle.

Source scanning uses AST and JSON parsing; it never executes inspected notebook/Python code. Resource limits do not provide a formal denial-of-service guarantee. Browser-runtime/third-party supply-chain trust and static-analysis blind spots remain; no independent security audit has been completed.
