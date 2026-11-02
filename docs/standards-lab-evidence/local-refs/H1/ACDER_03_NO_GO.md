# ACDER -03: NO-GO on the available evidence

**Decision: do not prepare an ACDER -03 patch from this evidence set.** Proposed
changes: **0**. Normative changes: **0**. Source patch: **none**. This is a scoped
local review, not a finding that ACDER -02 is defect-free or that later evidence
cannot justify a revision. Public publication requires the user's separate approval.

The playbook makes revision preparation conditional on measured evidence. B2 has
not run because an agent-level boundary excluding private answers and builder
context has not been established. B3 therefore has no frozen result to compare.
This report decides against a patch on the currently available A/C/F evidence;
it does not claim completion of the B3-dependent interoperability review.

## Frozen basis

- Published ACDER -02, SHA-256
  `fe3baeb08c8e0979ca64efece098c972827fab483debe0b2bcbfd697bb714782`.
- AgentProto verifier-evidence -03 and the exact task A commit/results.
- AUDIT -03 and the exact C03 receipt-API experiment; the new -04 source and C04
  addendum are separately identified. No -03 measurement is relabelled as -04.
- SCITT Measurement Capsule -01, Agent Execution Evidence -02, and task F's
  local composition demo on task D's explain feature.
- Current-at-retrieval ACDER Referenced-by HTML: eight draft relationships,
  including the author's Claim Preservation draft. References show citation,
  not endorsement, adoption, implementation or semantic agreement.

[SOURCE_PINS.json](SOURCE_PINS.json) records exact URLs, retrieval times, sizes,
revisions and hashes. [EVIDENCE_LEDGER.json](EVIDENCE_LEDGER.json) identifies exact
local commits and copied public result reports/run records. These are first-party
inspectable records; no external implementer participated in this review.

## Evidence-to-decision matrix

| Candidate reason to revise | Available evidence | Existing ACDER coverage and decision |
|---|---|---|
| Completeness and authority | A has 12 deliberately constructed fixtures; positive completeness depends on a stipulated exhaustive index and material-party control facts. A implements another draft's bounded appraisal, not ACDER interoperability. | §§5.3, 5.11, 5.15 and 6.6 already separate attribution, bounded accounting, declared closure and stronger claim support. No reproducible ACDER ambiguity was demonstrated. |
| Unknown or unavailable evidence | A preserves unavailable resolver/independent-basis results; F preserves unavailable measurement state. | §§5.8 and 5.12 distinguish missing observations, bounded negative evidence and unresolved references. No new universal status or mapping is justified. |
| Approval verification versus execution | C03 has six partially measured receipt-API scenarios and three unevaluated runtime scenarios. All actual execution/effect axes are unobserved. C04 separately tests the new draft's published receipt vectors. | §§5.6, 5.7 and 5.13 already separate delivery, enforcement and observed effect; §13 distinguishes upstream authorization from downstream control-delivery evidence. Receipt acceptance alone establishes no new control-delivery fact. |
| Population and sequence completeness | C03's sequence helper checks gaps only inside the supplied minimum/maximum range; its result establishes no unseen population or suffix. | §§5.10, 5.11 and 5.15 already require frozen population construction and qualification of coverage. This observation is not a new ACDER requirement. |
| SCITT composition | F has three local scenarios and 15 integration tests. SCITT signature, registration and identity verification remain NOT_EVALUATED; enforcement and stronger coverage remain separate. | §§5.13, 6.5, 6.6 and 13 already limit signature/registration claims and distinguish a structural result from support for a relying-party claim. F is not live SCITT or ACDER conformance evidence. |
| Implementation Status | D/F are first-party AIREP explanation/demo work. B1 is only a sealed challenge; B2/B3 are absent. | Do not report these as a distinct ACDER -02 interoperability implementation or an external implementation result. |
| Related-work citations | Current neighboring revisions and eight citation relationships are recorded. | New neighboring text or visibility alone does not require an ACDER revision. No concrete conflicting composition statement was established. |

## AUDIT -04 revision discovered during review

The metadata snapshot at 2026-11-02T17:36Z reported -04 rather than the expected
-03. Both texts remain pinned. The acquired -04 raw-byte SHA-256 is
`f5065d91493fb15a4995f85ffd1a71911d01bc9c8b063b1938521e1bfc05c826`.
[AUDIT_03_TO_04.diff](AUDIT_03_TO_04.diff) preserves the complete source delta.

The new text adds explicit field validation rules, clarifies digest/time input
handling, supplies local illustrative COSE/SCITT objects, and gives F1–F10 failure
vectors. Its receipt procedures and the released CLI have different supplied-input
boundaries; the draft explicitly distinguishes those results. C04 measures the
unmodified released package separately. Its report is copied at
[evidence/C04/RESULTS.md](evidence/C04/RESULTS.md), exact commit `ecaff138be0fd833848b6f27267e555e6b31e7f6`.

The addendum does not observe real approval consumption, action execution or an
external effect. A CLI acceptance cannot substitute for a relying party's
missing identity, action, effect or consumption-state checks. These remain the
existing ACDER separation-of-evidence issue, not a newly demonstrated defect in
ACDER -02. This review is frozen to AUDIT -04; it does not claim later revisions
were examined.

## When to reopen the gate

Reopen this decision if a frozen B2/B3 comparison yields a reproducible textual
ambiguity or interoperability difference; if an actual independent implementation
provides an appropriately scoped Implementation Status result; or if a concrete
adjacent specification conflicts with ACDER's stated composition boundaries.
Map each proposed edit to that evidence before changing source text. A real
editorial misreading can also justify a narrowly scoped clarification, but this
review found no new such example requiring an edit.

No ACDER source, schema, state model or BCP 14 language was changed. No new
Measurement Axioms principle is established; that separate theory was neither
modified nor exhaustively audited. The private B1 answers were not read. No
commit was pushed, no PR/message created and no Internet-Draft submitted.
