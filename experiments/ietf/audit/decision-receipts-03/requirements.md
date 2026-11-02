# Scope, revision delta and API coverage

The primary target is the exact [-03 text](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-03.txt).
The [-00 text](https://www.ietf.org/archive/id/draft-gruszka-audit-decision-receipts-00.txt)
is a historical comparison, with no execution observations attributed to it.
The freshly retrieved [Datatracker document record](https://datatracker.ietf.org/api/v1/doc/document/draft-gruszka-audit-decision-receipts/)
at `2026-11-02T16:16:07.890868+00:00` says `rev=03`, document time
`2026-11-02T09:01:08Z`. No newer target revision was seen at that acquisition.
The fixed local git base remains `69bc8cfd282e9a0a45e34b1fcf6106b1ab618f9d`.

## -00 to -03 delta

The table combines an actual comparison of the two pinned texts with -03
Appendix B. Intermediate -01/-02 attribution is Appendix B's account, not an
independent acquisition of those revisions. Pagination and whitespace are
ignored only in the derived comparison; original bytes remain unchanged.

| Area | -00 to -03 difference | Appendix B attribution | Consequence for this probe |
| --- | --- | --- | --- |
| §1 introduction | Explicitly identifies AUDIT-ARCH -01 as the mapping basis | B.3 (-00→-01) | No silent update to another architecture revision |
| §1.1 | Names the verifier, set auditor, relying party and test-key users to whom normative keywords apply | B.2 (-01→-02) | Receipt verification does not discharge relying-party obligations |
| §§2.6, 3.1–3.5, 4, 5 | Equal after pagination/whitespace normalization | B.3 explicitly lists §§3.1–3.5, 4, 5 as unchanged at -01 | Same relevant approval, verification, set and implementation text in the two acquired endpoints |
| §2.7 | New informative mapping observations about approval evidence, previous state, decision binding, refusals and recorder identity | B.1 (-02→-03) | No new wire format or normative verifier behavior |
| §§2.5, 3.6, new 3.7 | Adds informative SCITT registration and its limits; clarifies payload-root vs envelope/signature binding | B.3 | No transparency registration is performed or inferred |
| §6 | Expands comparisons with GILDA and IZMAYLOV | B.1 | No extension of this experiment to those drafts |
| §7 suppression | Completeness needs an expected population; registration does not establish it | B.3 | All set findings are limited to supplied records |
| §7 compromise | Adds key-compromise/replacement and external time-anchor limits | B.2 | Test signatures do not authenticate events or historic key control |
| §7 gaps/clocks | Explains optional outcome sequence gaps, absent decision sequence, boundary records and RFC3161 accuracy | B.1 | Exercise existing sequence helper with bounded interpretation; do not deploy a TSA |
| §8 | Explains privacy of full-envelope versus content-root registration | B.2 | No registration is made |
| Appendix A | Same example inputs, payload roots, signatures and verification results in the compared texts | B.3 lists vectors unchanged at -01 | Reproduce seven -03 vectors; do not label that a -00 run |
| XML metadata | B.2 reports removal of `submissionType` | B.2 | Not checked: this experiment pins plain text, not XML |

Evidence: [normalized diff](sources/draft-00-to-03.normalized.diff) and
[section hashes](evidence/draft-section-comparison.json). Tests assert every
reconstructed Appendix A payload length, root and signature against -03.

## Released package versus preview

| Role | Exact pin | Verification and result class |
| --- | --- | --- |
| Released receipt library and CLI | [proofbundle 6.4.0](https://pypi.org/project/proofbundle/6.4.0/), [tag commit 699545521ec5ef479bb84e61fe7461fc79ed558c](https://github.com/b7n0de/proofbundle/commit/699545521ec5ef479bb84e61fe7461fc79ed558c) | Wheel installed in isolated venv; archive hash agrees with PyPI; 80 wheel Python members match the Git blob hashes of the pinned tree; measured API/CLI results |
| Agent Guard preview | [8bb289c8b41d32c54734155fc00756231093bc2a](https://github.com/b7n0de/proofbundle/commit/8bb289c8b41d32c54734155fc00756231093bc2a) | Commit object and pinned plugin README acquired; `SOURCE_METADATA_ONLY`; runtime `NOT_EVALUATED` |

The annotated tag object `e57b357c2ba2bd859d20e712835af26e42be38b1` resolves
to the release commit. It does not resolve to the preview. Section 5's preview
store/rotation descriptions are not released-library measurements. No preview
hook or signing service is run, patched or substituted for a missing library API.
The acquired decision documentation describes the predicate as shipped since
2.1.0; the outcome documentation marks that predicate experimental. The PyPI
6.4.0 metadata contains the Beta classifier. These are source descriptions,
not assessments of production readiness.

## Requirement-to-measurement mapping

| Requirement | Public API exercised | Explicit boundary |
| --- | --- | --- |
| §3.2 exact payload, signature, canonical JSON, subject, audience/nonce/expiry | `emit_decision_receipt`, `verify_decision_receipt`, CLI `decision verify`; strict mode, fixed time and derived-subject enforcement | `ok=True` is this API's result, not a full draft-conformance result; action/approval bytes are not arguments to this verifier |
| §3.3 approval binding, identity and time bounds | Published fixture hashes and fixed values checked locally | No package approval verifier was found; approval verification `NOT_EVALUATED`; no human signature in the fixture |
| §3.4 signed outcomes, decision root binding, executor/maker ID distinction | `emit_outcome_receipt`, `verify_outcome_receipt`, CLI `outcome verify` | No complete cross-receipt action/time validation or trusted expected-executor binding is claimed; differing test keys/IDs do not prove operational independence |
| §3.5 duplicate approvals / executed outcome against refusal | No released set auditor found | `NOT_EVALUATED`; local inventory describes two roots and an identical fixture, not an upstream verdict |
| §4 durable consumption before ALLOW, reuse, archive/rotation, missing state, original lifetime retention | No corresponding public API found | S02–S04 entirely `NOT_EVALUATED`; no simulated store is introduced |
| One authorization versus one execution; retry after timeout | Receipt verification only | S01/S05/S06 partial; no executor, timeout or retry hook found; runtime `NOT_EVALUATED`, effects `UNOBSERVED` |
| §2.6 evaluation evidence must not authorize | `resolve_evidence_ref`, `verify_decision_receipt` with/without ALLOW-only policy; public PAE and Ed25519 helpers on SER P1 | P1 is the exact published SER -04 positive vector. Full SER-profile verification is `NOT_EVALUATED`; digest/signature/canonical/score preflight is narrower |
| §7 optional outcome sequence gaps | `detect_outcome_sequence_gaps` after individually verifying generated outcomes | Missing number 2 in [1,3] is detectable; a sole 3 yields `complete=True` only inside observed bounds; cause and missing suffix remain unknown |

[API inventory](evidence/api-inventory.json) records public signatures and installed
module SHA-256 values. Inspection of the two pinned predicate docs, all 80 wheel
Python source members, the decision/outcome API signatures and CLI help found no
approval consume/re-present, generation/rotation, execution/retry, or section-3.5
approval-identity set-audit entry point. Absence of a relevant hook is a coverage
limit, not evidence of a replay bug.

## Interpretation rules

- Approval once does not imply execution once.
- A valid ALLOW records a decision; it is not a bearer token or evidence of an effect.
- A timeout with no observed result remains UNKNOWN/UNOBSERVED, never inferred failed.
- Validity of supplied receipts does not establish an entire population's completeness.
- Different keys and IDs do not prove different operators or independent observation.
- Fixture preflight, local inventory and internal testing are not third-party independent evidence.
- Test success means these bounded observations reproduced; it does not turn unmeasured axes into PASS.
