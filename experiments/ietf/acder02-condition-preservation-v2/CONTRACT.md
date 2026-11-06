# K1 condition preservation v2

This is a known-data repair, not a preregistered unseen holdout evaluation.
The sibling frozen benchmark and its DOI archive remain unchanged. Its evaluator
is imported only after an exact source SHA-256 check. No oracle is read by the evaluator.

Native claim state, qualification, obligation disposition and accounting retain
the v1 rules. Conditions in unsuccessful aggregate delivery claims now name the
missing receiver observation and simultaneously present invalid/substituted
evidence. An otherwise attributable observation for another target is retained
as `other_target_observation`; it never satisfies the queried obligation.
`UNCONFIRMED` remains an obligation disposition, not a causal explanation.
Absence is scoped to the supplied inventory/cutoff, not proof of nondelivery.

Enforcement diagnostics collect transformation loss even when a native REFUSED,
NO_EFFECT or contradictory APPLIED/REFUSED result already fixes the verdict.
`cause_details` preserves source and transformation references. A directly
evidenced native APPLIED fact is not refuted by a separate lossy transformation;
its mapping caveat remains in `cause_details`, while native support is unchanged.
This does not endorse that transformation's output or prove real enforcement.

Holdout-05 also contains an actual observation for the wrong target, so v2 retains
`other_target_observation` in addition to the old oracle's missing receiver cause.
The old holdout-12 oracle lists only `semantic_mapping_not_lossless`. V2 retains
both that cause and `source_state_does_not_establish_applied`, because the native
REFUSED observation remains relevant. Therefore 54/54 exact old-oracle condition
agreement is deliberately not claimed. Oracle labels are never rewritten.
All original tests, scenarios, hashes and published measurements remain v1.

Run `python3 -B -m unittest -v test_conditions.py` from this directory, then
`python3 -B report.py --out <new-directory>`. Reports compare every known claim,
include old oracle labels for inspection and record the source/input hashes.
No new external implementer, cryptographic trust or unseen accuracy is measured.
