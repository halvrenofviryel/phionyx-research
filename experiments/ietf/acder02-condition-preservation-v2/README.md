# K1 condition preservation repair

The original experiment's native verdicts were correct for the two reported
condition mismatches. This extension retains missing causal detail without
rewriting the frozen experiment or its oracle. See [CONTRACT.md](CONTRACT.md).

Source base: Research main `7b8f1b8f14eecf93176843dc928ec913e7e3e285`.
The frozen evaluator is imported with a checked SHA-256.

```sh
cd experiments/ietf/acder02-condition-preservation-v2
python3 -B -m unittest -v test_conditions.py
python3 -B report.py --out /tmp/k1-condition-v2-new
```

Results on 6 November 2026:

- Original evaluator/scorer tests: 44 passed, frozen subtree unchanged.
- New tests: 10 passed, including eight outcome/mapping combinations and mixed
  positive/negative native records, wrong-target and simultaneous invalid/content
  substitution cases, cutoff, unrelated transformation and record-order controls.
- All 24 known cases, 107 bounded claims: zero native state or qualification
  changes; obligation accounting and structural results unchanged.
- Nine claim rows gain more precise conditions. The two known mismatches retain
  the missing receiver cause and mapping-loss cause, respectively.

V2 intentionally retains additional source-supported causes absent from the old
oracle (wrong target in holdout-05; native refusal in holdout-12). This is not a
claim of 54/54 exact old-oracle agreement or new unseen accuracy. Positive native
APPLIED evidence remains support for that bounded fact; any loss in a separate
transformation remains visible as a source diagnostic.

The report contains every before/after claim, original oracle labels, exact input
hashes and source hashes. This is a regression repair under stipulated fixture
trust, not independent replication or a cryptographic verifier change.
