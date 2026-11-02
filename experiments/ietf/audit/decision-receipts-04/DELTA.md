# Semantic delta: frozen -03 to exact -04

The two raw texts were independently acquired for this run. Their URLs, UTC
access times and SHA-256 values are in [sources/manifest.json](sources/manifest.json).
The fetched -03 bytes equal the previous experiment's frozen source exactly.
The target for this run is -04 even if a later revision becomes available.

| Area | -03 | -04 | Consequence and measurement boundary |
| --- | --- | --- | --- |
| §3.2 step 1 | Describes a JSON envelope with named members | Explicit UTF-8, one object and no duplicate names in any object | Feed raw duplicate root/nested member bytes directly to the real CLI; do not pre-parse them into a Python dict |
| §3.2 step 7 / §3.4 step 3 | Refer to the upstream predicate field constraints | Refer to new §3.8; list digest/timestamp paths; specify typedDigest shape | Field rules are stated within this draft; no complete new validator is implemented here |
| §3.8 | Absent | Tables enumerate member types, presence, nullability and allowed fields; distinguish JSON boolean from string | Signed `rawInputsIncluded="false"` and numeric `0` are negative controls; literal boolean false remains in the positive base |
| §3.8 provenance | No table-source pin | Cites `e1fec86351b216af369a2e6ac106dcc41aaf4b4c` for the table's schema/doc provenance | This is a reference reported by the acquired draft. That commit is not installed or tested; measured implementation stays the released 6.4.0 wheel |
| §3.3 Case 1 | Exactly one entry named approval record | Clarifies that other inputSnapshot entries are allowed | No change to base fixture bytes; no claim that a generic CLI verifies approval-record contents |
| §3.6 | Describes digest bindings collectively | Names the supplied action and required approval byte bindings precisely | Separate missing verifier inputs from successfully verified receipt fields |
| §3.7 / new A.4 | Informative registration description | Adds full-envelope and content-root Signed Statement examples with SCITT Receipts | SOURCE_DELTA_ONLY; no COSE, SCITT, transparency service or live registration measurement |
| A.3 | Seven original DSSE vectors and CLI results | Same bytes/signatures; identifies the particular procedure and inputs judging each vector | Verify all seven base payload pins; do not rerun the old nine-scenario study |
| New A.5 | Absent | F1–F10; ap2 reissue and c1 consumption fixture; explicit draft/CLI scope distinction | Generate exact new bytes, verify hashes/signatures, run ten commands and capture actual outputs |
| A.5 F10 | Absent | Receipt procedure passes; relying party must refuse under §4 with c1 | CLI result is measured, consumption enforcement is NOT_EVALUATED; c1 is inert fixture bytes |
| §§5 and A provenance | Describes original vectors | Distinguishes seven proofbundle-generated DSSE vectors from new illustrative examples | No preview/runtime conformance is inferred |
| §8 privacy | Mentions rawInputsIncluded=false | Explains that field rules do not establish absence of raw inputs | Boolean validation is not a privacy assurance |
| References | PB-DECISION/PB-OUTCOME normative; fewer registration references | Moves predicate references to informative; adds SCITT/COSE-related informative references | No additional protocol or implementation brought into this experiment |

The acquired texts have equal normalized content for §§3.1, 3.5, 4 and A.1–A.2
after removing page furniture and normalizing whitespace. This is a text
comparison, not a proof of global semantic equivalence. See
[section-comparison.json](evidence/section-comparison.json) and the complete
[normalized diff](sources/draft-03-to-04.normalized.diff). Raw sources are untouched.

The version/role distinction remains: draft §5 names released proofbundle 6.4.0
at `699545521ec5ef479bb84e61fe7461fc79ed558c`, and separately describes Agent Guard
preview `8bb289c8b41d32c54734155fc00756231093bc2a`. This run rehashes the released
wheel against fresh versioned PyPI metadata and compares all 80 installed Python
modules to the wheel. The older study's tag/preview evidence remains frozen;
neither preview runtime nor the new table-source commit is tested here.
