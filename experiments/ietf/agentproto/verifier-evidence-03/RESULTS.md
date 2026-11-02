# Results

## Requirements implemented

The bounded fixture policy implements CMP-1 domain/detector identification, CMP-2 material-party operation **and input-selection** checks, and required appraisal of an independent basis's authority, result/domain binding, extent and time. Section 6 supplies the four separate outcome tokens, evidence times and capability/attempt context. Exact references and interpretations are in REQUIREMENTS.md.

The independent basis is a **stipulated exhaustive counterparty index**, bound by version and SHA-256 to the supplied run. Its authority and control facts are synthetic inputs, not authenticated external evidence. The evaluator retains each completed appraisal step and the evidence references/digests supporting it. Matching record IDs establishes only coverage of this local finite domain; signature validity and event truth are separate properties.

## Observed agreement with the draft

The first independent implementation run produced the following fixed results; all 59 tests passed on the first execution. “Agreement” means agreement with our prior text-derived expectations, not an author oracle, external review or conformance finding.

| Vector | Completeness | Separate predicate |
|---|---|---|
| closed_independent | SATISFIED | NOT_EVALUATED |
| same_party_only | INDETERMINATE | NOT_EVALUATED |
| withheld_unobservable | INDETERMINATE | INDETERMINATE |
| resolver_unavailable | INDETERMINATE | NOT_EVALUATED |
| known_omission | UNSATISFIED | NOT_EVALUATED |
| open_domain | INDETERMINATE | NOT_EVALUATED |
| qualified_sample | SATISFIED | NOT_EVALUATED |
| unbound_detector_state | INDETERMINATE | NOT_EVALUATED |
| anchor_outside_window | INDETERMINATE | NOT_EVALUATED |
| no_completeness_claim | NOT_EVALUATED | NOT_EVALUATED |
| material_input_selection | INDETERMINATE | NOT_EVALUATED |
| two_disclosed_predicate | INDETERMINATE | UNSATISFIED |

Outcome counts: **2 SATISFIED, 1 UNSATISFIED, 8 INDETERMINATE, 1 NOT_EVALUATED**. These counts describe the deliberately selected 12 fixtures, not a population success rate or coverage score.

- Same-party lists and material-party-selected inputs leave completeness INDETERMINATE even when all disclosed records carry a stipulated valid-authentication label.
- Withheld information in `scenario_only` is unavailable to the evaluator. `withheld_unobservable` therefore stays INDETERMINATE, consistent with Appendix A.4. In `known_omission`, the independently appraised index actually supplies the second record identity, so a completed local membership predicate establishes an omission and returns UNSATISFIED.
- Resolver unavailability stays INDETERMINATE and does not imply either a negative lookup or missing resolver capability.
- Two disclosed authenticated occurrences refute the separate at-most-once predicate while the same-party completeness appraisal remains INDETERMINATE.
- The sample case is SATISFIED only for the explicitly declared sample domain. No verdict is issued for the wider population. An absent completeness claim is NOT_EVALUATED.
- A named anchor cannot satisfy the appraisal with unbound state/version or a coverage window elsewhere.

Four actual implementation mutants were killed: ignoring an exposed missing record, converting unavailable resolution into SATISFIED, converting it into UNSATISFIED, and ignoring material-party control. Additional input mutations test restoration, scope, authority, time, unavailable resolver configuration, duplicates, and all subsets of a two-member population. The pure appraiser reached 100% measured statement/branch coverage; overall src coverage was 93.02%. These tests are not an exhaustive proof.

## Ambiguities / underspecification

1. The draft requires authority and independence appraisal but does not prescribe trust bootstrap, authority discovery, proof formats, or how joint control/input selection is established. We stipulate these facts; this is the main limit on any real-world positive conclusion.
2. It does not define a generic closure algorithm, membership key, version binding format, or window-boundary arithmetic. The local policy uses unique record IDs, an exhaustive finite index, canonical-JSON digest plus state version, and half-open UTC windows. These are experimental choices, not new draft requirements.
3. Missing reporting fields and failed scope/time binding bar SATISFIED, but the text does not define every check's failure precedence or whether a separate reporting-conformance predicate should fail. We appraise completeness only, returning INDETERMINATE for incomplete appraisal. Explicit skipped/no-claim cases are NOT_EVALUATED.
4. The text distinguishes a separately refuted predicate from unknown completeness. Our UNSATISFIED completeness case uses a fully appraised exhaustive index and an actual missing member. The draft does not prescribe a generic reconciliation algorithm or verdict precedence for mixed invalid/missing evidence; this experiment uses appraisal first.
5. Section 9's final paragraph requires prior expectations and both unestablished/established results under one revision. Local requirements and input digests preceded execution, and both outcomes occur. Local timestamps/digests are not externally established chronology, so **full CMP-2 exercise-condition or EXR-1 conformance is not claimed**.

## Not implemented / not testable here

Live resolvers; signature, inclusion-proof or timestamp verification; real identity/materiality discovery; validation of an authority outside the supplied fixtures; append-only log consistency; non-suppressible substrates; multi-basis composition; omission-cause attribution; arbitrary hostile JSON validation; all EXR requirements; all possible domains, evidence conflicts, or draft implementations. Global repository tests were not run: no runtime code outside the new experiment changed. No author/reference implementation was fetched or inspected, either before or after the frozen run; no post-hoc comparison is asserted.

The domain population description is declarative. The positive result depends on the supplied exhaustive-index and party facts being true. The evaluator cannot transform those declarations into independent real-world evidence. No external source other than the pinned draft and its current-revision metadata is relied on. Unread reference links are catalogued as unverified and have no invented access times or hashes.

## Exact non-claims

This is not an AIREP implementation, a new protocol or receipt format, IETF endorsement, a second external evidence root, independent third-party validation, deployment/security certification, proof of event truth, proof that all relevant real events were supplied, a population rate estimate, author-code interoperability, or full draft conformance. A valid signature is not completeness; all supplied records verifying is not all relevant records being supplied. No unknown evidence is promoted to SATISFIED or UNSATISFIED.

Measurement Axioms: **no change needed**. This bounded experiment provides no evidence for a new general measurement principle. Measurement Axioms was neither used as an authority nor modified; no exhaustive comparison to a separately acquired version is claimed. AIREP v0.1 frozen content and normative schemas are untouched.

## Scope and provenance

Work stayed within the designated clone and requested experiment path. The clean starting tree, fetch failure/retry, exact base and post-fetch references are recorded in `provenance/git_initial.json`. The fixed base was not changed. Datatracker's acquired metadata says revision 03; `sources/revision_check.json` records no newer revision delta. The draft byte digest is `c64cb2fd988476a56f82bdc4386a652c5841f7b3723941bffea44e73208ef600`; URLs, exact UTC access times and raw-byte hashes for both acquired sources are in `sources/manifest.json`.

The draft itself, including implementation-status prose, was read. Referenced implementations, fixtures and audits were not read. The local preparation and first-execution records make that methodology inspectable but are not independent testimony. The frozen run record and its detached SHA-256 are immutable experiment outputs; replay validates them without rewriting them.
