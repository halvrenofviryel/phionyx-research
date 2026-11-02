# Independent draft-text completeness appraisal (-03)

A small offline Python experiment derived from [draft-he-agentproto-verifier-evidence-03](https://www.ietf.org/archive/id/draft-he-agentproto-verifier-evidence-03.txt), especially CMP-1 and CMP-2. Here “independent” describes writing the implementation from the published text without reading linked implementations. It does **not** describe third-party validation or an independent evidence root.

The 12 synthetic vectors produce **2 SATISFIED, 1 UNSATISFIED, 8 INDETERMINATE, 1 NOT_EVALUATED**. The first run passed **59 tests**, including four deliberately defective implementation mutants. These are local fixture outcomes, not a protocol conformance certificate.

```sh
python3 experiments/ietf/agentproto/verifier-evidence-03/reproduce.py
```

Run from this clone's repository root; Python 3.10+ and pytest are needed. Evaluation itself uses only the standard library. See [REPRODUCE.md](REPRODUCE.md) for the absolute command and optional coverage check.

- [REQUIREMENTS.md](REQUIREMENTS.md) and [requirements.json](requirements.json): requirement table, exact raw-source line references and local policy, written before logic.
- [RESULTS.md](RESULTS.md) and [results.json](results.json): findings and per-vector evidence/diagnostics.
- [run_record.json](run_record.json), [run_record.sha256](run_record.sha256), and `provenance/`: acquisition, preparation, first execution and freeze records.
- `sources/`: exact fetched draft bytes, Datatracker metadata, URL/time/digest manifest, revision check, and unread implementation links.
- `src/`, `vectors/`, and `tests/`: bounded evaluator, fixed inputs/expectations and deterministic adversarial tests.

The sole positive mechanism is a finite exhaustive counterparty index with explicitly stipulated authority, control, scope and time facts. The evaluator checks those facts for consistency and reconciles record IDs. No cryptographic authentication, real-world observation, external authority validation, live resolver, or network access occurs during replay. The JSON is a local fixture representation, not a protocol or receipt format.

No AIREP code, frozen content, normative schema or Measurement Axioms was changed or used as authority. Nothing outside this experiment is staged. There is no push, PR, issue, email, external comment, IETF submission, or follow-on task.
