# Reproduce offline

From the designated clone root:

```sh
python3 experiments/ietf/agentproto/verifier-evidence-03/reproduce.py
```

Equivalent from any working directory:

```sh
python3 /home/toygar/Documents/ChatGPT/AACDE/standards-reentry/2026-11-02/a-agentproto-completeness/phionyx-research/experiments/ietf/agentproto/verifier-evidence-03/reproduce.py
```

Python 3.10+ and pytest are required; the recorded environment used Python 3.12.3 and pytest 9.0.2. pytest was already declared by the repository and installed. No dependency was installed for this task. The evaluator and reproduction driver are stdlib-only; pytest is a test dependency. Coverage and Ruff were used for local validation but are optional for ordinary reproduction.

The script verifies the frozen run-record digest, every frozen file and the prior input commitment; evaluates only each vector's `input` (never its `scenario_only` or `expected`); compares replay output byte-for-byte against `results.json`; and runs the isolated pytest suite including four in-memory implementation mutations. It disables unrelated pytest plugins and does not load the SDK or the repository's top-level test fixtures. Temporary pytest cache stays outside the repository. A changed frozen file fails integrity before evaluation.

Expected: 59 passing tests, integrity MATCH, replay BYTE_IDENTICAL, 12 vectors and counts SATISFIED=2, UNSATISFIED=1, INDETERMINATE=8, NOT_EVALUATED=1. The fixed replay time is a synthetic evaluation context; actual first-execution UTC start/finish are in `provenance/first_execution.json` and `run_record.json`.

Direct output inspection (no frozen-record verification):

```sh
python3 experiments/ietf/agentproto/verifier-evidence-03/src/run.py
```

Optional coverage from the experiment directory, with existing pytest-cov:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 COVERAGE_FILE=/tmp/agentproto-coverage-replay python3 -m pytest -c pytest.ini --confcutdir=. tests -q -p pytest_cov --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
```

The first run measured appraise.py at 100% statement/branch coverage and src overall at 93.02%; the runner was executed separately, not measured by the pytest coverage session. Coverage is not proof of semantic completeness or full draft conformance.

Initial acquisition used `git fetch --all --prune` and the exact HTTPS URLs in `sources/manifest.json`. A sandbox DNS failure was retained, followed by successful authorized read-only network acquisition. Reproduction intentionally does not re-fetch mutable metadata. The draft's raw bytes and LF line numbers are frozen. Both expected and observed current revision were -03; newer-revision delta was NONE. The base remained 69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d.

Local digests and local timestamps make this package internally inspectable; they are not an externally witnessed precommitment. The final Git commit is identified by the task's final response and can be checked with `git log -1`; it is not embedded in its own hashed content.
