# Decision receipts -03: released API probe

This local experiment studies `draft-gruszka-audit-decision-receipts-03` against
the unmodified PyPI wheel `proofbundle==6.4.0`. Start with [RESULTS.md](RESULTS.md).

Nine requested scenarios are recorded: six have measured receipt-API subsets,
three are entirely `NOT_EVALUATED`. There is no executable relying party,
approval store, rotation model, or execution simulator here. No live action is
authorized or performed by a fixture. The commands inside Appendix A payloads
are inert bytes.

```sh
bash experiments/ietf/audit/decision-receipts-03/reproduce.sh
```

Run from this isolated repository; the script also resolves its own location.
See [REPRODUCE.md](REPRODUCE.md) for installation and platform details.

| File | Purpose |
| --- | --- |
| [requirements.md](requirements.md) | -00/-03 delta, normative requirements, actual API coverage |
| [run_record.json](run_record.json) | Initial clean tree, fetch result, fixed base, environment, pins |
| [sources/manifest.json](sources/manifest.json) | Exact retrieval URL, UTC access time, byte length and SHA-256 per external resource |
| [cases/scenario_results.json](cases/scenario_results.json) | All nine scenarios and all eight requested observation axes |
| [cases/api_results.json](cases/api_results.json) | Public API results with explicit process-token masking; all verdicts, nulls and warnings preserved |
| [evidence/api_results.original.json](evidence/api_results.original.json) | Unmodified original API capture, including process-local tokens; archival evidence only |
| [cases/cli_results.json](cases/cli_results.json) | Seven Appendix A CLI calls, stdout, stderr and exit codes |
| [fixtures.py](fixtures.py), [probe.py](probe.py) | Deterministic fixtures and thin public API calls |
| [tests/test_probe.py](tests/test_probe.py) | Positive/negative controls, source pins and deterministic reproduction |

No adapter is needed. Local fixture preflight and inventory are explicitly
labelled; they are not upstream approval verification or a set-level auditor.
The preview has a separate `SOURCE_METADATA_ONLY` class, with runtime
`NOT_EVALUATED`. The historical -00 bytes are used only for text comparison.

The experiment adds files only in this directory. It does not change AIREP v0.1,
repository normative schemas, or proofbundle. No outreach, push or publication
is part of this work.
