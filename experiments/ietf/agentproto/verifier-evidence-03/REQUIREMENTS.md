# Draft-derived requirements, before implementation

Source: [draft-he-agentproto-verifier-evidence-03.txt](https://www.ietf.org/archive/id/draft-he-agentproto-verifier-evidence-03.txt). SHA-256: `c64cb2fd988476a56f82bdc4386a652c5841f7b3723941bffea44e73208ef600`. References below use **LF lines** (`nl -ba`), not Python `splitlines()` (which also splits form feeds).

Only CMP-1/CMP-2 and necessary definitions/outcomes inform the implementation. Neither Phionyx/AIREP nor Measurement Axioms is an authority for this experiment. The published draft, including its implementation-status prose, was read; linked code, fixtures, repositories and audits were not.

| ID | Section; raw lines | Requirement (paraphrase) | Interpretation / ambiguity |
|---|---|---|---|
| DEF-DOMAIN | 3; 215–216 | Coverage is the record set asserted by the claim. | A finite, named domain and half-open UTC window are required by this local experiment; the draft does not prescribe a closure algorithm. |
| DEF-MATERIAL | 3; 218–233 | Materiality is relative to the conduct or assertion at issue. | Party identities and their materiality are stipulated fixture facts, not discovered or externally certified. |
| CMP-1 | 8; 567–585 | Name the claimed domain and omission-revealing mechanism; valid disclosed artifacts do not establish wider completeness. | Missing domain or detector leaves the completeness appraisal INDETERMINATE; a separate reporting-conformance check is not implemented. Omission causes are not inferred. |
| CMP-2-CONTROL | 9; 589–627 | Same-party operation or input selection needs an independently appraised basis. Its absence alone is not UNSATISFIED. | A separately controlled exhaustive counterparty index is the only basis implemented. Material-party input selection is disqualifying even with a different operator. |
| CMP-2-APPRAISAL | 9; 629–637 | Retain completed authority, result/domain binding, extent and temporal appraisals before SATISFIED. | A local fixture policy defines exact scope, version+digest binding, trusted counterparty authority, and full-window coverage. Neither digest nor matching identifiers proves truth or independence. |
| CMP-2-EXERCISE | 9; 639–645 | Demonstrate both unestablished and independently appraised established outcomes under one revision and prior expectations. | Pairs and prior local digests will be retained. No externally timed commitment or independently controlled exercise evidence exists; full exercise conformance is NOT claimed. |
| OUTCOME-4 | 6; 399–440 | Keep satisfied, unsatisfied, indeterminate and not-evaluated distinct. | Uppercase underscore spellings are local JSON tokens. A proven missing member of the independently enumerated domain is UNSATISFIED under the local equality predicate; unavailable evidence is INDETERMINATE. |
| OUTCOME-TIME | 6; 442–470 | Record check time, carried evidence times, and distinguish capability from an unattempted check. | A fixed replay instant gives deterministic output; the actual wall-clock execution interval is recorded separately. Capability is supplied explicitly in the evaluation plan, never inferred from resolver failure. |
| PREDICATE-SEPARATION | 9; 597–607 | A refuted predicate and unestablished completeness are separate verdicts. | An optional at-most-once check counts only fixture-authenticated disclosed occurrences; it never reads scenario truth. |
| NON-CLAIMS | 10 / A.4; 663–687, 1371–1384 | Missing independent coverage is not proof of omission; the requirements do not establish protocol truth or deployment security. | Scenario-only withheld records are kept outside the evaluator input. The test author is not an independent evidence root. |

## Local decision policy declared before the first run

The JSON is a synthetic test-input representation, not a protocol or receipt format. All role, authority and authentication facts are stipulated. SATISFIED means the bounded fixture condition held, not that real events were independently witnessed.

1. No completeness claim, or an explicitly skipped evaluation: NOT_EVALUATED; no check-performance timestamp.
2. Attempted but insufficient domain, mechanism, resolver, independent basis, authority, state binding, scope, or time: INDETERMINATE. An omitted reporting field is not silently treated as a factual failure.
3. For an appraised independent exhaustive index, compute expected IDs minus disclosed IDs. A nonempty difference proves a bounded omission: UNSATISFIED. With no omission, SATISFIED. Extra/out-of-domain disclosed IDs make the claimed binding uncertain (INDETERMINATE); duplicates are not extra evidence.
4. A qualified sample can be SATISFIED only for its explicitly named finite sample domain, never for the wider population.
5. The separately reported at-most-once predicate can be UNSATISFIED on two disclosed authenticated occurrences while completeness remains INDETERMINATE. One occurrence does not establish at-most-once unless coverage is established.

The draft does not prescribe precedence between incomplete appraisal and an independently proven counterexample, exact trust bootstrap, finite-domain closure, digest/version encoding, window-boundary arithmetic, or a complete JSON input contract. This experiment chooses an appraisal-first order. Its successful index path is deliberately narrower than the mechanisms permitted by the draft.
