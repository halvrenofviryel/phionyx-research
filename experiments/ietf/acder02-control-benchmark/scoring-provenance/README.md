# K1 scorer implementation before benchmark execution

`score.py` implements the shared frozen metrics with Python's standard library.
See [CONTRACT.md](CONTRACT.md) for the normalized API, raw-author loader and exact
denominators. The implementation and tests are separate from comparator code.

Only these author files were read for implementation: PROFILE.json,
BENCHMARK_PROTOCOL.md, CONTRACT.md, EVIDENCE_SCHEMA.json, CLAIM_OUTPUT_SCHEMA.json
and SCENARIO_SELECTION.json. Raw oracle/latent **key shapes** were supplied by
the author agent. No development or holdout case, latent value, oracle content,
author generator or recipe was opened. The later author data-freeze notification
did not trigger data reads or benchmark execution.

Run the small scorer-contract suite from the workspace root:

```sh
python3 -B -m unittest discover \
  -s evidence/standards_third_wave_2026-11-02/k1-scoring \
  -p 'test_*.py' -v
```

Tests invent their own tiny records. Real CLI subprocess checks write fixtures
only in disposable temporary directories; the `dev-01` label in those fixtures
tests selection metadata mapping and contains no author case contents. No
comparator or benchmark measurement is executed by this suite. Tests cover
denominator escape, claim-only ambiguity, latent/epistemic separation, independent
qualification/condition scores, structural/type mismatches, split/kind partitions,
malformed/missing rows, directory isolation and first-output preservation.

The root task will include this directory in its evaluator logic-freeze commit.
No separate commit was made here while the root was editing other files in the
shared workspace. No public action or external message was performed.
