# K1 condition repair review evidence — 6 November 2026

Measured source commit: `a327dbd6fe1a2d7bda6f1ffb46e45fd61af391cd`.
This is post-holdout repair on known regression cases. It does not update the
frozen v1.0.0 result or its DOI and does not measure unseen-data accuracy.

`comparison.json` contains all 107 bounded claims from 24 known cases, the
before/after states and conditions, original oracle labels, input hashes and
source hashes. `predictions.json` preserves the resulting evaluator output.
State/qualification changes: zero. Condition rows with additional detail: nine.
The original frozen condition-set result remains 52/54; no 54/54 exact agreement
with the old oracle is claimed.

`frozen-tests.txt` records 44 passing original tests; `v2-tests.txt` records ten
new tests. These logs belong to the measured source commit. New PR CI results
are separate and must be tied to the exact PR head.

Reproduce from the repository root:

```sh
python -B experiments/ietf/acder02-control-benchmark/reproduce.py --check-only
(cd experiments/ietf/acder02-condition-preservation-v2 && python -B -m unittest -v test_conditions.py)
python -B experiments/ietf/acder02-condition-preservation-v2/report.py --out /tmp/k1-public-replay-new
```

The output directory must not exist. See the experiment's `README.md` and
`CONTRACT.md` for scope and test rationale. The original benchmark and oracle
remain unchanged. These files retain the Research repository's AGPL-3.0 context;
no AIREP component is relicensed. `MANIFEST.json` records the exact file hashes.
