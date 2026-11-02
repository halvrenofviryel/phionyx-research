# Results — NON-NORMATIVE local mapping experiment

This is a same-author implementation experiment against CP-00, SER-04 and mappings-04. It does not establish independent interoperability, full CP/SER conformance, event truth, model safety, complete populations, trusted identity, or endorsement/adoption. EQR-05 is context only.

All 12 requirements have bounded questions below; all 20 Appendix A scenarios run through four routes (80 scenario-route observations). Native-domain boundary probes and missing reliance events are explicitly NOT_APPLICABLE, not successful native mappings.

**48 matrix cells:** NOT_APPLICABLE=4, PRESERVED=17, QUALIFIED_LOSS=10, UNESTABLISHED=17.
**80 scenario-route results:** NOT_APPLICABLE=16, PRESERVED=34, QUALIFIED_LOSS=17, UNESTABLISHED=13.

Labels apply to the stated bounded question, not the whole normative requirement. Matrix judgments combine measured field visibility with the explicit native field limits; they are not a mechanical conformance verdict or an average of scenario labels.

## Concrete losses and ambiguities

1. **Coverage and history do not cross.** SER carries reported n but no population, retries, excluded-count or amendment/mapping-history fields. Three supplied records with two distinct B digests establish neither two nor three actual attempts. Later local MAC authentication leaves the lost partial/excluded qualification absent (CP-T06/07/12/16).
2. **A digest-only route cannot supply payload semantics.** Without the cited receipt bytes, the typed reference is Unresolved/unavailable and matching is INDETERMINATE. Score, threshold and identity commitments are unavailable. Providing a matching receipt restores access to B, not signature/key verification or qualifications lost before B (CP-T03/08/09/11/20).
3. **Comparison and execution are different.** SER cannot encode no-criterion completion or did-not-run/invalid/not-evaluated states. P2 reports score 0.762, threshold 0.800, passed=false; rounding to one decimal gives 0.8 and a true presentation comparison. The source assertion remains false; no execution status is inferred (CP-T01/02/05/08).

## Requirement × representation matrix

SER = direct receipt; DSSE = section 4.1 exact-payload envelope; DIGEST_ONLY = section 5.1 typed reference without candidate; DIGEST_RESOLVED = same reference with matching candidate. No live SCITT registration or COSE statement validation was performed.

| CP requirement | Representation | Result | Bounded question and reason | Probes |
|---|---|---|---|---|
| R-CP-1 | SER | UNESTABLISHED | Native mapping-instance identity and history recoverable? No native converter/profile/source-selection record; local binding probe is separately scoped. | CP-T18 |
| R-CP-2 | SER | PRESERVED | Selected single B and available metric kept unambiguous? One explicit B; ambiguous multi-record selection and duplicates rejected. | CP-T04, CP-T19 |
| R-CP-3 | SER | UNESTABLISHED | Execution / observation / non-assessment states transportable? SER requires a comparison and has no execution-state enum; boundary cases cannot be encoded. | CP-T01, CP-T02, CP-T05 |
| R-CP-4 | SER | PRESERVED | Exact score/comparator/threshold and explicit rounding kept separate? P2 exact false comparison remains separate from true rounded display; units/uncertainty absent, not inferred. | CP-T08 |
| R-CP-5 | SER | UNESTABLISHED | Source/later judgment separation AND pre-run criterion ordering established? Later judgments stay separate when B is available; criteria_digest/timestamp do not establish ordering. | CP-T03, CP-T15 |
| R-CP-6 | SER | QUALIFIED_LOSS | Population and known retry/attempt qualifications recoverable? Only reported n; supplied record/retry/exclusion context has no native field. Full population unknown. | CP-T06, CP-T07 |
| R-CP-7 | SER | PRESERVED | Declared identity strength retained without claiming executed identity? Names and salted identifier commitments retained as declarations; executed model/corpus/config unestablished. | CP-T09 |
| R-CP-8 | SER | UNESTABLISHED | General source evidence availability/qualification recoverable? No general evidence-reference/access field; B availability and digest recomputation are separately scoped. | CP-T10, CP-T11 |
| R-CP-9 | SER | QUALIFIED_LOSS | Known earlier loss and amendment link survive in the carrier? Earlier partial/excluded context and amendment links are absent; later test authentication cannot restore them. | CP-T12, CP-T16 |
| R-CP-10 | SER | PRESERVED | Typed checks and bounded unsupported consumption stay separate? Digest match, local test MAC and semantic support stay distinct; SER signature remains NOT_EVALUATED. | CP-T13, CP-T20 |
| R-CP-11 | SER | NOT_APPLICABLE | Actual downstream decision transported? No reliance event supplied; successful export produces no decision/control assertion. | CP-T14 |
| R-CP-12 | SER | PRESERVED | This local supported basis and negative behavior explicitly versioned? Exact draft/profile/implementation/fixture hashes recorded; unknown basis refuses semantics. Local evidence only. | CP-T17 |
| R-CP-1 | DSSE | UNESTABLISHED | Native mapping-instance identity and history recoverable? No native converter/profile/source-selection record; local binding probe is separately scoped. | CP-T18 |
| R-CP-2 | DSSE | PRESERVED | Selected single B and available metric kept unambiguous? One explicit B; ambiguous multi-record selection and duplicates rejected. | CP-T04, CP-T19 |
| R-CP-3 | DSSE | UNESTABLISHED | Execution / observation / non-assessment states transportable? SER requires a comparison and has no execution-state enum; boundary cases cannot be encoded. | CP-T01, CP-T02, CP-T05 |
| R-CP-4 | DSSE | PRESERVED | Exact score/comparator/threshold and explicit rounding kept separate? P2 exact false comparison remains separate from true rounded display; units/uncertainty absent, not inferred. | CP-T08 |
| R-CP-5 | DSSE | UNESTABLISHED | Source/later judgment separation AND pre-run criterion ordering established? Later judgments stay separate when B is available; criteria_digest/timestamp do not establish ordering. | CP-T03, CP-T15 |
| R-CP-6 | DSSE | QUALIFIED_LOSS | Population and known retry/attempt qualifications recoverable? Only reported n; supplied record/retry/exclusion context has no native field. Full population unknown. | CP-T06, CP-T07 |
| R-CP-7 | DSSE | PRESERVED | Declared identity strength retained without claiming executed identity? Names and salted identifier commitments retained as declarations; executed model/corpus/config unestablished. | CP-T09 |
| R-CP-8 | DSSE | UNESTABLISHED | General source evidence availability/qualification recoverable? No general evidence-reference/access field; B availability and digest recomputation are separately scoped. | CP-T10, CP-T11 |
| R-CP-9 | DSSE | QUALIFIED_LOSS | Known earlier loss and amendment link survive in the carrier? Earlier partial/excluded context and amendment links are absent; later test authentication cannot restore them. | CP-T12, CP-T16 |
| R-CP-10 | DSSE | PRESERVED | Typed checks and bounded unsupported consumption stay separate? Digest match, local test MAC and semantic support stay distinct; SER signature remains NOT_EVALUATED. | CP-T13, CP-T20 |
| R-CP-11 | DSSE | NOT_APPLICABLE | Actual downstream decision transported? No reliance event supplied; successful export produces no decision/control assertion. | CP-T14 |
| R-CP-12 | DSSE | PRESERVED | This local supported basis and negative behavior explicitly versioned? Exact draft/profile/implementation/fixture hashes recorded; unknown basis refuses semantics. Local evidence only. | CP-T17 |
| R-CP-1 | DIGEST_ONLY | UNESTABLISHED | Native mapping-instance identity and history recoverable? No native converter/profile/source-selection record; local binding probe is separately scoped. | CP-T18 |
| R-CP-2 | DIGEST_ONLY | UNESTABLISHED | Selected single B and available metric kept unambiguous? Only digest identity is visible; metric/task/attempt context is unavailable. | CP-T04, CP-T19 |
| R-CP-3 | DIGEST_ONLY | UNESTABLISHED | Execution / observation / non-assessment states transportable? SER requires a comparison and has no execution-state enum; boundary cases cannot be encoded. | CP-T01, CP-T02, CP-T05 |
| R-CP-4 | DIGEST_ONLY | QUALIFIED_LOSS | Exact score/comparator/threshold and explicit rounding kept separate? Digest alone omits numeric values and transformation interpretation. | CP-T08 |
| R-CP-5 | DIGEST_ONLY | UNESTABLISHED | Source/later judgment separation AND pre-run criterion ordering established? Later judgments stay separate when B is available; criteria_digest/timestamp do not establish ordering. | CP-T03, CP-T15 |
| R-CP-6 | DIGEST_ONLY | QUALIFIED_LOSS | Population and known retry/attempt qualifications recoverable? Only reported n; supplied record/retry/exclusion context has no native field. Full population unknown. | CP-T06, CP-T07 |
| R-CP-7 | DIGEST_ONLY | QUALIFIED_LOSS | Declared identity strength retained without claiming executed identity? Digest-only citation carries no suite or model/dataset identity declarations. | CP-T09 |
| R-CP-8 | DIGEST_ONLY | UNESTABLISHED | General source evidence availability/qualification recoverable? No general evidence-reference/access field; B availability and digest recomputation are separately scoped. | CP-T10, CP-T11 |
| R-CP-9 | DIGEST_ONLY | QUALIFIED_LOSS | Known earlier loss and amendment link survive in the carrier? Earlier partial/excluded context and amendment links are absent; later test authentication cannot restore them. | CP-T12, CP-T16 |
| R-CP-10 | DIGEST_ONLY | PRESERVED | Typed checks and bounded unsupported consumption stay separate? Digest match, local test MAC and semantic support stay distinct; SER signature remains NOT_EVALUATED. | CP-T13, CP-T20 |
| R-CP-11 | DIGEST_ONLY | NOT_APPLICABLE | Actual downstream decision transported? No reliance event supplied; successful export produces no decision/control assertion. | CP-T14 |
| R-CP-12 | DIGEST_ONLY | PRESERVED | This local supported basis and negative behavior explicitly versioned? Exact draft/profile/implementation/fixture hashes recorded; unknown basis refuses semantics. Local evidence only. | CP-T17 |
| R-CP-1 | DIGEST_RESOLVED | UNESTABLISHED | Native mapping-instance identity and history recoverable? No native converter/profile/source-selection record; local binding probe is separately scoped. | CP-T18 |
| R-CP-2 | DIGEST_RESOLVED | PRESERVED | Selected single B and available metric kept unambiguous? One explicit B; ambiguous multi-record selection and duplicates rejected. | CP-T04, CP-T19 |
| R-CP-3 | DIGEST_RESOLVED | UNESTABLISHED | Execution / observation / non-assessment states transportable? SER requires a comparison and has no execution-state enum; boundary cases cannot be encoded. | CP-T01, CP-T02, CP-T05 |
| R-CP-4 | DIGEST_RESOLVED | PRESERVED | Exact score/comparator/threshold and explicit rounding kept separate? P2 exact false comparison remains separate from true rounded display; units/uncertainty absent, not inferred. | CP-T08 |
| R-CP-5 | DIGEST_RESOLVED | UNESTABLISHED | Source/later judgment separation AND pre-run criterion ordering established? Later judgments stay separate when B is available; criteria_digest/timestamp do not establish ordering. | CP-T03, CP-T15 |
| R-CP-6 | DIGEST_RESOLVED | QUALIFIED_LOSS | Population and known retry/attempt qualifications recoverable? Only reported n; supplied record/retry/exclusion context has no native field. Full population unknown. | CP-T06, CP-T07 |
| R-CP-7 | DIGEST_RESOLVED | PRESERVED | Declared identity strength retained without claiming executed identity? Names and salted identifier commitments retained as declarations; executed model/corpus/config unestablished. | CP-T09 |
| R-CP-8 | DIGEST_RESOLVED | UNESTABLISHED | General source evidence availability/qualification recoverable? No general evidence-reference/access field; B availability and digest recomputation are separately scoped. | CP-T10, CP-T11 |
| R-CP-9 | DIGEST_RESOLVED | QUALIFIED_LOSS | Known earlier loss and amendment link survive in the carrier? Earlier partial/excluded context and amendment links are absent; later test authentication cannot restore them. | CP-T12, CP-T16 |
| R-CP-10 | DIGEST_RESOLVED | PRESERVED | Typed checks and bounded unsupported consumption stay separate? Digest match, local test MAC and semantic support stay distinct; SER signature remains NOT_EVALUATED. | CP-T13, CP-T20 |
| R-CP-11 | DIGEST_RESOLVED | NOT_APPLICABLE | Actual downstream decision transported? No reliance event supplied; successful export produces no decision/control assertion. | CP-T14 |
| R-CP-12 | DIGEST_RESOLVED | PRESERVED | This local supported basis and negative behavior explicitly versioned? Exact draft/profile/implementation/fixture hashes recorded; unknown basis refuses semantics. Local evidence only. | CP-T17 |

## Scenario results

| CP scenario | Representation | Result | Reason |
|---|---|---|---|
| CP-T01 | SER | NOT_APPLICABLE | Valid SER requires a criterion comparison; a score-only completed run is outside its domain. |
| CP-T02 | SER | NOT_APPLICABLE | Neither explicit no-criterion nor omitted unknown criterion is a valid SER assessment. |
| CP-T03 | SER | PRESERVED | A later threshold assessment has its own actor, rule, inputs and result. |
| CP-T04 | SER | PRESERVED | No first/last/favorable selection without a unique snapshot selector. |
| CP-T05 | SER | NOT_APPLICABLE | SER has no native execution-state field; local boundary states cannot be emitted as passed booleans. |
| CP-T06 | SER | UNESTABLISHED | n is a reported sample count, not complete population or attempt accounting. |
| CP-T07 | SER | QUALIFIED_LOSS | Three supplied records/two B digests do not encode retries or actual attempt count in SER. |
| CP-T08 | SER | PRESERVED | The exact P2 score remains false while its rounded presentation compares true. |
| CP-T09 | SER | PRESERVED | Declared suite/model/dataset commitments do not establish executed artifacts. |
| CP-T10 | SER | UNESTABLISHED | No source evidence bytes/digest supplied; SER has no general evidence availability field. |
| CP-T11 | SER | PRESERVED | criteria_digest is an issuer report, not recomputation of unseen criteria bytes. |
| CP-T12 | SER | QUALIFIED_LOSS | A later test MAC verifies surviving bytes; the earlier partial/excluded qualification is absent. |
| CP-T13 | SER | PRESERVED | Local MAC authentication is separate from unsupported payload interpretation. |
| CP-T14 | SER | NOT_APPLICABLE | No actual reliance/decision record exists in the input. |
| CP-T15 | SER | UNESTABLISHED | P10 commitment and issuer timestamp provide no supported criteria-before-run relation. |
| CP-T16 | SER | QUALIFIED_LOSS | SER has no correction/amendment link; local context is not recovered from either carrier. |
| CP-T17 | SER | PRESERVED | Unknown local profile and native payload basis cannot reuse old semantics. |
| CP-T18 | SER | PRESERVED | LOCAL record substitution detected; native SER/DSSE/reference still has no mapping-instance record. |
| CP-T19 | SER | PRESERVED | Reject duplicate decoded names deterministically. |
| CP-T20 | SER | PRESERVED | Retain common source and both later judgments without rewriting it. |
| CP-T01 | DSSE | NOT_APPLICABLE | Valid SER requires a criterion comparison; a score-only completed run is outside its domain. |
| CP-T02 | DSSE | NOT_APPLICABLE | Neither explicit no-criterion nor omitted unknown criterion is a valid SER assessment. |
| CP-T03 | DSSE | PRESERVED | A later threshold assessment has its own actor, rule, inputs and result. |
| CP-T04 | DSSE | PRESERVED | No first/last/favorable selection without a unique snapshot selector. |
| CP-T05 | DSSE | NOT_APPLICABLE | SER has no native execution-state field; local boundary states cannot be emitted as passed booleans. |
| CP-T06 | DSSE | UNESTABLISHED | n is a reported sample count, not complete population or attempt accounting. |
| CP-T07 | DSSE | QUALIFIED_LOSS | Three supplied records/two B digests do not encode retries or actual attempt count in SER. |
| CP-T08 | DSSE | PRESERVED | The exact P2 score remains false while its rounded presentation compares true. |
| CP-T09 | DSSE | PRESERVED | Declared suite/model/dataset commitments do not establish executed artifacts. |
| CP-T10 | DSSE | UNESTABLISHED | No source evidence bytes/digest supplied; SER has no general evidence availability field. |
| CP-T11 | DSSE | PRESERVED | criteria_digest is an issuer report, not recomputation of unseen criteria bytes. |
| CP-T12 | DSSE | QUALIFIED_LOSS | A later test MAC verifies surviving bytes; the earlier partial/excluded qualification is absent. |
| CP-T13 | DSSE | PRESERVED | Local MAC authentication is separate from unsupported payload interpretation. |
| CP-T14 | DSSE | NOT_APPLICABLE | No actual reliance/decision record exists in the input. |
| CP-T15 | DSSE | UNESTABLISHED | P10 commitment and issuer timestamp provide no supported criteria-before-run relation. |
| CP-T16 | DSSE | QUALIFIED_LOSS | SER has no correction/amendment link; local context is not recovered from either carrier. |
| CP-T17 | DSSE | PRESERVED | Unknown local profile and native payload basis cannot reuse old semantics. |
| CP-T18 | DSSE | PRESERVED | LOCAL record substitution detected; native SER/DSSE/reference still has no mapping-instance record. |
| CP-T19 | DSSE | PRESERVED | Reject duplicate decoded names deterministically. |
| CP-T20 | DSSE | PRESERVED | Retain common source and both later judgments without rewriting it. |
| CP-T01 | DIGEST_ONLY | NOT_APPLICABLE | Valid SER requires a criterion comparison; a score-only completed run is outside its domain. |
| CP-T02 | DIGEST_ONLY | NOT_APPLICABLE | Neither explicit no-criterion nor omitted unknown criterion is a valid SER assessment. |
| CP-T03 | DIGEST_ONLY | QUALIFIED_LOSS | Digest-only input supplies no score for the new assessment. |
| CP-T04 | DIGEST_ONLY | UNESTABLISHED | No payload metric visible; digest identity alone supplies no task/run context. |
| CP-T05 | DIGEST_ONLY | NOT_APPLICABLE | SER has no native execution-state field; local boundary states cannot be emitted as passed booleans. |
| CP-T06 | DIGEST_ONLY | UNESTABLISHED | n is a reported sample count, not complete population or attempt accounting. |
| CP-T07 | DIGEST_ONLY | QUALIFIED_LOSS | Three supplied records/two B digests do not encode retries or actual attempt count in SER. |
| CP-T08 | DIGEST_ONLY | QUALIFIED_LOSS | Digest-only input carries neither the exact score nor the threshold. |
| CP-T09 | DIGEST_ONLY | QUALIFIED_LOSS | Digest citation alone does not carry the declared suite or model/dataset commitments. |
| CP-T10 | DIGEST_ONLY | UNESTABLISHED | No source evidence bytes/digest supplied; SER has no general evidence availability field. |
| CP-T11 | DIGEST_ONLY | QUALIFIED_LOSS | The citation reports a digest of B, but the criteria digest inside B is unavailable. |
| CP-T12 | DIGEST_ONLY | QUALIFIED_LOSS | A later test MAC verifies surviving bytes; the earlier partial/excluded qualification is absent. |
| CP-T13 | DIGEST_ONLY | PRESERVED | Local MAC authentication is separate from unsupported payload interpretation. |
| CP-T14 | DIGEST_ONLY | NOT_APPLICABLE | No actual reliance/decision record exists in the input. |
| CP-T15 | DIGEST_ONLY | UNESTABLISHED | P10 commitment and issuer timestamp provide no supported criteria-before-run relation. |
| CP-T16 | DIGEST_ONLY | QUALIFIED_LOSS | SER has no correction/amendment link; local context is not recovered from either carrier. |
| CP-T17 | DIGEST_ONLY | PRESERVED | Unknown local profile and native payload basis cannot reuse old semantics. |
| CP-T18 | DIGEST_ONLY | PRESERVED | LOCAL record substitution detected; native SER/DSSE/reference still has no mapping-instance record. |
| CP-T19 | DIGEST_ONLY | PRESERVED | Reject duplicate decoded names deterministically. |
| CP-T20 | DIGEST_ONLY | QUALIFIED_LOSS | Neither policy can evaluate the unavailable source score. |
| CP-T01 | DIGEST_RESOLVED | NOT_APPLICABLE | Valid SER requires a criterion comparison; a score-only completed run is outside its domain. |
| CP-T02 | DIGEST_RESOLVED | NOT_APPLICABLE | Neither explicit no-criterion nor omitted unknown criterion is a valid SER assessment. |
| CP-T03 | DIGEST_RESOLVED | PRESERVED | A later threshold assessment has its own actor, rule, inputs and result. |
| CP-T04 | DIGEST_RESOLVED | PRESERVED | No first/last/favorable selection without a unique snapshot selector. |
| CP-T05 | DIGEST_RESOLVED | NOT_APPLICABLE | SER has no native execution-state field; local boundary states cannot be emitted as passed booleans. |
| CP-T06 | DIGEST_RESOLVED | UNESTABLISHED | n is a reported sample count, not complete population or attempt accounting. |
| CP-T07 | DIGEST_RESOLVED | QUALIFIED_LOSS | Three supplied records/two B digests do not encode retries or actual attempt count in SER. |
| CP-T08 | DIGEST_RESOLVED | PRESERVED | The exact P2 score remains false while its rounded presentation compares true. |
| CP-T09 | DIGEST_RESOLVED | PRESERVED | Declared suite/model/dataset commitments do not establish executed artifacts. |
| CP-T10 | DIGEST_RESOLVED | UNESTABLISHED | No source evidence bytes/digest supplied; SER has no general evidence availability field. |
| CP-T11 | DIGEST_RESOLVED | PRESERVED | criteria_digest is an issuer report, not recomputation of unseen criteria bytes. |
| CP-T12 | DIGEST_RESOLVED | QUALIFIED_LOSS | A later test MAC verifies surviving bytes; the earlier partial/excluded qualification is absent. |
| CP-T13 | DIGEST_RESOLVED | PRESERVED | Local MAC authentication is separate from unsupported payload interpretation. |
| CP-T14 | DIGEST_RESOLVED | NOT_APPLICABLE | No actual reliance/decision record exists in the input. |
| CP-T15 | DIGEST_RESOLVED | UNESTABLISHED | P10 commitment and issuer timestamp provide no supported criteria-before-run relation. |
| CP-T16 | DIGEST_RESOLVED | QUALIFIED_LOSS | SER has no correction/amendment link; local context is not recovered from either carrier. |
| CP-T17 | DIGEST_RESOLVED | PRESERVED | Unknown local profile and native payload basis cannot reuse old semantics. |
| CP-T18 | DIGEST_RESOLVED | PRESERVED | LOCAL record substitution detected; native SER/DSSE/reference still has no mapping-instance record. |
| CP-T19 | DIGEST_RESOLVED | PRESERVED | Reject duplicate decoded names deterministically. |
| CP-T20 | DIGEST_RESOLVED | PRESERVED | Retain common source and both later judgments without rewriting it. |

## Verification limits

The complete 66-vector public file and proofbundle fixture are byte-pinned and their receipt reconstruction is checked for equality. This is not a 66-vector cryptographic verification run. Selected external receipts and M1 exercise semantic carriage; mappings C1–C8 and R1–R16 exercise digest extraction/matching/reference states. Ed25519 and COSE/SCITT checks are NOT_EVALUATED. Published PASS/FAIL expectations remain external expectations. The two later-auth probes use an explicitly local, public-key-material-free symmetric HMAC test key, not an Ed25519 signature or independent evidence.

Local context records for unsupported states, exclusions, evidence references and amendment links are marked author-constructed and NOT SER. They are used to expose missing carrier capacity, never read by consume() as hidden evidence. The internal analysis and binding records are not proposed wire formats or new normative requirements.

A preserved declaration does not establish exact evaluator, harness, test/corpus bytes, model/configuration actually used, evaluator independence or an enforcement event. Reported criteria_digest is not recomputed without criteria bytes; timestamps do not establish criteria chronology. Binding hashes demonstrate local tuple consistency, not authentication or completeness of a loss inventory.

Reproduce offline: `python3 experiments/ietf/claim-preservation/ser04/src/run.py --check`. Full machine-readable observations and input hashes are in `results.json`; source access times/hashes and environment are in SOURCE_PINS.json and run_record.json.
