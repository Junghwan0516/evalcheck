# Put the check in a real workflow

## Pre-commit

After installing the project, a repository-local configuration can use the installed entry point:

```yaml
repos:
  - repo: local
    hooks:
      - id: evalcheck-code
        name: EvalCheck evaluation-risk scan
        entry: evalcheck-precommit
        language: system
        files: '\.(py|ipynb)$'
```

The hook accepts pre-commit's filename arguments, never executes the inspected source, prints matching locations and exits `1` on findings. Coverage notes are printed, but do not fail this lightweight hook; use the CLI's `--strict` gate when abstentions must also block CI. Use `repo: https://github.com/Junghwan0516/evalcheck` and `rev: v0.5.0` for the remote hook.

## Local composite GitHub Action

The source project includes `.github/actions/evalcheck/action.yml`. For a repository containing this project at its root:

```yaml
name: Notebook evaluation gate
on: [push, pull_request]
permissions:
  contents: read
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: ./.github/actions/evalcheck
        id: audit
        with:
          path: notebooks
          fail-on: warning
          strict: 'false'
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: notebook-code-evidence
          path: ${{ steps.audit.outputs.report-directory }}
```

Replace `notebooks` with a real path in the adopting repository. The action writes HTML, JSON and SARIF to the runner's temporary directory. Use `Junghwan0516/evalcheck/.github/actions/evalcheck@v0.5.0` from another repository. Hosted workflow status is visible in the repository Actions tab; export support does not imply SARIF ingestion was exercised.

SARIF output uses schema version 2.1.0. A repository with code-scanning support can upload it using its chosen GitHub SARIF integration and appropriate permissions. Export support and schema validation do not establish that a hosted upload succeeded; see [GitHub SARIF documentation](https://docs.github.com/en/code-security/concepts/code-scanning/sarif-files).
