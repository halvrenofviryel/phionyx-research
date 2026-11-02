# Results: released proofbundle receipt boundaries

The unmodified `proofbundle==6.4.0` wheel reproduces all seven -03 Appendix A
CLI vectors: four exit 0, the invalid signature exits 1, and the noncanonical
payload and wrong decision binding exit 2. All 16 deterministic tests pass.

Of the nine requested scenarios, six have measured receipt-API subsets and
three (S02–S04) are entirely `NOT_EVALUATED`. **No end-to-end runtime scenario
was executed.** The release exposes no approval-consumption/rotation hook found
by this inspection. It therefore supplies no measured answer here about refusal,
indeterminacy or re-allow when an old generation is missing. No replay bug is
asserted.

```sh
bash experiments/ietf/audit/decision-receipts-03/reproduce.sh
```

## Pins

| Input | Exact version or revision | SHA-256 of acquired bytes |
| --- | --- | --- |
| [Primary draft](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-03.txt) | -03 | `c0aae84b82108a3bd40cbbbee33df13c760b5c2e943a205e9efca4c623438245` |
| [Historical text](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-00.txt) | -00, comparison only | `427a7f6958c9c4f169136e980989bc55de707e24a52e9b55fc60d25430f1eefa` |
| PyPI wheel | `proofbundle-6.4.0-py3-none-any.whl` | `72153d160c2f78647095f029c0946dbfd64a15e006a233a5abc78a3071eebf94` |
| PyPI sdist | `proofbundle-6.4.0.tar.gz` | `9b074c7ed9dec106b45ae541b9194087f7238230953a7c784df7c4a08c386699` |
| [Evaluation vector source](https://www.ietf.org/archive/id/draft-gruszka-signed-evaluation-receipts-04.txt) | SER -04, P1 | `d60c3dd95aefb8019a5f1c0ce041d8c4eb1d4571302766944bfbc92b91c1e358` |

The [source manifest](sources/manifest.json) records exact URLs, UTC access times
and hashes for every acquired external resource. The draft bytes were acquired
at `2026-11-02T16:16:07Z`; Datatracker still reported -03, with document time
`2026-11-02T09:01:08Z`. The release tag resolves to
`699545521ec5ef479bb84e61fe7461fc79ed558c`. Its 80 Python modules match the
wheel's corresponding Git blob hashes. This does not establish a reproducible
whole build, publisher identity or artifact safety.

Agent Guard preview commit `8bb289c8b41d32c54734155fc00756231093bc2a` is separately
pinned as `SOURCE_METADATA_ONLY`; its runtime is `NOT_EVALUATED`. It is not the
installed release. Python was 3.12.3 on Linux x86_64; exact dependencies and
artifact hashes are in [requirements.lock](requirements.lock).

## Observations

| Scenario | Status | Observed result and limit |
| --- | --- | --- |
| S01 baseline approval → ALLOW → executed outcome | PARTIALLY_EVALUATED | Published approval fixture, ALLOW and one synthetic outcome are bound as constructed; both receipt API results are `ok=True`. No approval consumption or actual execution occurred in the harness. |
| S02 consumed approval, state retained | NOT_EVALUATED | No public consume/re-present store hook. |
| S03 rotation preserving required old state | NOT_EVALUATED | No public rotation/preservation hook. |
| S04 required old generation unavailable | NOT_EVALUATED | No missing-generation hook. Fail-closed, indeterminate and silent re-allow behavior all remain unknown. |
| S05 one ALLOW reused for two attempts | PARTIALLY_EVALUATED | Verifying the same ALLOW twice at the same audit time returns the same successful receipt result. These calls are not execution attempts; execution reuse remains unmeasured. |
| S06 timeout/unknown then retry | PARTIALLY_EVALUATED | `decision.actionOutcome.status=unknown` is accepted; `outcome.status=unknown` is rejected by its enum. No timeout/retry was simulated; no failed outcome is substituted for an unknown result. |
| S07 two outcomes reference one ALLOW | PARTIALLY_EVALUATED | Both distinct synthetic outcomes verify against the same root. Local inventory detects two outcome roots/one decision ref. The unnumbered sequence helper returns no groups; it does not detect repeated execution. |
| S08 two distinct ALLOWs cite one approval identity | PARTIALLY_EVALUATED | Both payloads individually verify and reference the exact same approval bytes. A local inventory exposes the two roots and identity in an explicitly supplied fixture scope. The package §3.5 duplicate-approval verdict is `NOT_EVALUATED`. |
| S09 evaluation evidence is not authorization | PARTIALLY_EVALUATED | Exact SER P1 payload resolves as `CONTENT_RESOLVED`; its signature/canonical bytes/score are preflighted. A decision citing it remains DENY: receipt validity is true, ALLOW-only policy acceptance is false, and the positive ALLOW control is accepted. The original SER envelope is rejected by the decision verifier. Full SER-profile and live authorization verification are unmeasured. |

The [machine-readable matrix](cases/scenario_results.json) separately captures
approval verification, approval consumption, decision validity, outcome validity,
set audit, execution observation, effect observation and non-claims for every
scenario. All approval-consumption and §3.5 set-audit axes remain
`NOT_EVALUATED`; execution and effect observations remain `UNOBSERVED` in all nine.

Two bounded findings matter for interpreting the returns:

1. On a synthetic executed outcome with a well-formed digest,
   `execution_proven=True` coexists with effect evidence
   `REFERENCE_WELL_FORMED` and `executor_role_trusted=null`. The library emits a
   deprecation warning explaining the digest-presence meaning. This harness
   observes no execution or effect; it does not promote the legacy field name
   into event truth.
2. On verified outcomes numbered 1 and 3, `detect_outcome_sequence_gaps` reports
   gap 2. With only number 3 supplied, it returns `complete=True`. That boolean
   describes gaps inside the supplied minimum/maximum range, not run or receipt
   population completeness. An absent suffix and the cause of a gap are unknown.

## Non-claims and validation limits

These are local synthetic fixtures and internal tests. The two test signing keys
are controlled by this same harness. No independent operator, observer, real
human approval, actual action or external effect is established. An ALLOW is
not an access token. Authorization once does not imply execution once; unknown
execution does not imply failure. Receipt validity cannot establish records that
were not supplied.

The package's `ok` is not a full implementation of every draft §3.2–3.5 step.
Approval-record input, durable consumption, cross-record action/time and complete
expected-executor trust checks are not supplied by these calls. Historical audit
times are fixed solely for verification of test vectors and cannot revive an
expired live approval. No -00 execution results are claimed. No preview behavior
is inferred from the release or from the draft author's source observations.

The test run validates API/CLI controls, source hashes, exact vector payloads and
signatures, wrong-key/nonce/expiry refusal, unknown-state handling, evidence
binding and two byte-identical report generations in separate processes. The
report explicitly masks only the process-local `verified_origin` HMAC token,
after policy evaluation. An initial reproduction failed on that field; the
unmodified first capture is archived in `evidence/api_results.original.json`.
All receipt bytes, verdicts, nulls, warnings and evidence digests remain unchanged.
The test suite compares that archived capture's projection with fresh results.
It does not run the repository's
unrelated application suite or proofbundle's entire upstream suite.

No outreach or protocol change is proposed. The missing runtime hooks are a
coverage limit; they do not by themselves create a technical ambiguity in §4.
