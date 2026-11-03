# K1 control-failure benchmark results

**On the frozen holdout's same 18 unsupported queries applicable to both claim-producing comparators, the explicitly naive ACK rule asserted full support 16 times; the ACDER-derived bounded evaluator did so 0 times.** The latter recovered all 31 evidenced bounded claims in its broader contract, so its result is not blanket abstention. The integrity-only baseline correctly limits itself to byte integrity and receives no penalty for effect claims it does not make.

This is one fixed same-owner synthetic comparison, not a measured product ranking, external implementation result or operational safety gain. Development agreement informed the implementation; the following holdout numbers are from the first post-freeze run. There were 12 development and 12 holdout cases, exactly one of each in each of the twelve preregistered categories, with 53 + 54 distinct claim queries and 321 comparator rows. No case or claim was removed; all frozen ambiguity flags are false.

## First holdout results

Different applicability denominators reflect the declared contracts; compare the shared subset above when comparing stronger-claim acceptance directly.

| Comparator | Applicable queries /54 | Unsupported stronger support | Evidenced-claim recall | Semantically wrong definite claim | False rejection | Exact state | Exact qualification | Exact condition set |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| integrity_only | 12/54 | N/A (0/0) | 12/12 | 0/12 | 0/12 | 12/12 | 12/12 | 12/12 |
| naive_ack | 29/54 | 16/18 | 11/11 | 12/27 | 0/11 | 13/29 | 13/29 | 11/29 |
| acder_bounded | 54/54 | 0/23 | 31/31 | 0/36 | 0/31 | 54/54 | 54/54 | 52/54 |

ACDER appropriately withheld 18/18 oracle-indeterminate claims; naive ACK withheld 2/16 within its contract. Their holdout output states are respectively 31 SUPPORTED, 5 REFUTED, 18 INDETERMINATE and 27 SUPPORTED, 0 REFUTED, 2 INDETERMINATE plus 25 NOT_APPLICABLE. Integrity-only has 12 SUPPORTED and 42 NOT_APPLICABLE. None produces NOT_EVALUATED on this selected corpus. Four naive ACK overclaims are latently true but insufficiently evidenced; these are epistemic overclaims, not semantic falsehoods.

All 12 holdout reconciliation records match the author's frozen oracle: per-target dispositions, instruction/obligation/receiver counts, structural result and aggregate qualification/conditions. A structural PASS describes that bounded reconciliation only; it cannot establish enforcement, effect, deployment completeness or semantic preservation. FULLY_SUPPORTED attached to an INCONCLUSIVE structural finding supports that finding, not successful delivery.

## Two condition differences retained, without tuning

| First holdout row | Frozen oracle condition | Frozen C condition | What remains established |
|---|---|---|---|
| holdout-05 / q-all | missing_receiver_observation | unconfirmed_required_target | Both INDETERMINATE / NOT_SUPPORTED. One names missing exact target/content evidence; the other names the resulting unconfirmed obligation. Exact condition retention fails despite the same bounded conclusion. |
| holdout-12 / q-enforcement | semantic_mapping_not_lossless | source_state_does_not_establish_applied | Both REFUTED / NOT_SUPPORTED because native REFUSED contradicts APPLIED. The claim's condition list omits the gateway semantic-loss condition. The separate semantic-preservation query still reports that loss; this is not a claim that the whole report hid it. |

The frozen flags remain unambiguous and both rows remain in primary metrics. Neither oracle nor comparator was corrected after first holdout. No spelling equivalence, newly invented ambiguity exclusion or label-only summary was used to turn 52/54 into perfect condition agreement. Future implementation corrections would require a new version, preserve this result and use new withheld data if claiming unseen evaluation.

## Side-by-side bounded example

In holdout-07, a genuine author-verified synthetic Ed25519 receipt and matching delivery evidence coexist with no enforcement/effect observation. The digest-only baselines do not claim signature or authority verification.

| Query | Integrity only | Naive ACK | ACDER bounded | Evidence oracle |
|---|---|---|---|---|
| envelope_integrity | SUPPORTED | NOT_APPLICABLE | SUPPORTED | SUPPORTED |
| receiver_receipt | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED |
| all_required_delivery | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED |
| enforcement_applied | NOT_APPLICABLE | SUPPORTED | INDETERMINATE | INDETERMINATE |
| effect_observed | NOT_APPLICABLE | SUPPORTED | INDETERMINATE | INDETERMINATE |

## Complete results and evidence

The complete 24-case C results are 0/46 unsupported stronger support, 61/61 evidenced support recall, 0/69 semantically incorrect definite predictions, 107/107 state/qualification and 105/107 condition agreement. Naive ACK has 32/36 unsupported stronger support and 25/53 semantically incorrect definite predictions. These totals include development and must not replace the first-holdout result as evidence of generalization. Integrity-only is correct on all 24 applicable integrity queries; its stronger-support denominator is zero.

[METRICS.md](METRICS.md) gives every comparator/split/claim-kind numerator and denominator. [results/score.json](results/score.json) contains all 321 raw scoped rows, oracle rationale/evidence/latent truth, fixed applicability, confusion matrices and reconciliation differences. The separately implemented arithmetic audit recounts 576 metric fractions, 720 scalar counts and 72 per-split confusion matrices without calling the scorer or comparator. All matched the saved reports. This is same-team verification, not an external result.

The pre-implementation protocol is benchmark commit `9a1d931156b0e8f92bde0fe9fc65a32b3958f02c`, author protocol `c8c5889c5a96df92febf8ba44888479dd320e646`. Author data/oracles were frozen at `c6123b4309801c0bf007c0a3d95f6c2bc0820ac5` and pinned in benchmark commit `b17eced04bb30f7687a654cbc7426a94c04d142d` before comparator execution. Evaluator, scorer, tests and profile were frozen at **`9c4989243d3c319d236ebb81b584711d0f7f5153`** before holdout access. LOGIC_FREEZE.json and HOLDOUT_RELEASE.json record the exact order and hashes. The author-data Git bundle carries the original protocol/data commits. It also deliberately carries the freshly generated, explicitly public synthetic Ed25519 test private/public key pair. This fixture has no real issuer/account authority; PUBLICATION_SCOPE.json identifies it separately from account credentials. It contains a named branch; check out `codex/acder02-benchmark-author` explicitly when cloning it.

All 79 relocated authored data files and all 99 author-bundle manifest blobs hash-match the freeze. A disposable offline author validation verified both real Ed25519 signatures and rejected both altered payloads. Its system jsonschema4.10.3 differs from the original4.25.1; the frozen author report remains intact. An initial root bundle clone did not check out the named branch, so validation could not find its script; that infrastructure log is retained and did not execute a comparator. The corrected checkout validation passed.

The one-command replay reproduced all 24 cases and all 321 rows, preserving the two discrepancies, and passed all **44 tests**. The exact semantic report hash is `f73be47c6b2e61411b4c18466e0bb7ed85fce06aa415dc7ef23b3b86a397aacb`; only machine-specific input file locations are removed for that deterministic comparison. Evaluator execution had no oracle, latent truth, credentials, home or external network mount. Its only data inputs were profile and evidence. No paid LLM call occurred. See [REPRODUCE.md](REPRODUCE.md), [run_record.json](run_record.json) and the retained original/replay records.

**Decision: GO for review and reproduction of this bounded differentiating result; HOLD for a claim of exact condition equivalence or broader conformance. Publication/outreach remains HOLD pending explicit user approval.** There is no basis here to change H1 into a normative-revision GO, claim external adoption, or upgrade K3's runtime claims. Strongest nonclaims: full ACDER conformance, third-party independence, real event truth, general complete mediation, operational safety improvement, production cancellation guarantees, interoperability or adoption. See [LIMITATIONS.md](LIMITATIONS.md).
