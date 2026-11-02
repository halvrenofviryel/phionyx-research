# Claim preservation across SER-04 and mappings-04

**NON-NORMATIVE, local, same-author experiment.** This directory asks which bounded
claim distinctions survive consumption of a Signed Evaluation Receipt (SER) and
selected representations. It defines no protocol or wire format and changes no
published draft, frozen AIREP content or normative schema.

## Reproduce offline

From the isolated repository root:

```sh
python3 experiments/ietf/claim-preservation/ser04/src/run.py --check
```

Python 3.10+ and its standard library are sufficient (recorded run: Python 3.12).
No package installation, network, signing keys or external service is required.
The command runs 30 unittest tests, verifies pinned source and fixture bytes,
executes 80 scenario-route observations, and checks that both `results.json` and
`RESULTS.md` reproduce byte-for-byte. Failure exits nonzero. The optional `--write`
mode regenerates those two outputs only after the tests succeed.

Optional development checks, if the tools are installed:

```sh
ruff check experiments/ietf/claim-preservation/ser04/src experiments/ietf/claim-preservation/ser04/tests
ruff format --check --line-length 100 experiments/ietf/claim-preservation/ser04/src experiments/ietf/claim-preservation/ser04/tests
COVERAGE_FILE=/tmp/ser04.coverage coverage run --source=experiments/ietf/claim-preservation/ser04/src --omit='*/acquire_sources.py,*/run.py' experiments/ietf/claim-preservation/ser04/src/run.py --check
COVERAGE_FILE=/tmp/ser04.coverage coverage report --fail-under=80
```

## Sources and authority

`SOURCE_PINS.json` records exact URLs, raw-response SHA-256, byte counts and UTC
retrieval times. All four requested revisions were freshly fetched on 2026-11-02.
The separately pinned Datatracker snapshots reported the same latest revisions:
CP **00**, SER **04**, mappings **04**, EQR conformance **05**. Observed revision
difference: **NONE**. The experimental bases were not replaced after discovery.
The initial sandbox DNS failure and successful read-only network retry are
recorded in `run_record.json`.

- [CP-00](https://www.ietf.org/archive/id/draft-abak-ai-evaluation-claim-preservation-00.txt),
  sections 4–5 and Appendix A, is the authority for R-CP-1..12 and CP-T01..20.
- [SER-04](https://www.ietf.org/archive/id/draft-gruszka-signed-evaluation-receipts-04.txt),
  sections 3, 5–6 and Appendix A, defines receipt fields and their limits.
- [Mappings-04](https://www.ietf.org/archive/id/draft-gruszka-evaluation-receipt-mappings-04.txt),
  sections 3.1–3.3, 4.1 and 5.1, supplies the implemented transformations and
  matching rules. Section 8 expressly disclaims full coverage and mapping-instance
  records; this experiment does not treat that document as a CP conformance claim.
- [EQR conformance-05](https://www.ietf.org/archive/id/draft-watts-eqr-conformance-05.txt)
  is comparison context only. Its distinction among structural acceptance,
  semantic conformance and stronger evidence claims informs reporting discipline;
  no EQR algorithm, normative requirement or vector corpus is implemented here.

The [public SER v1 vector file](https://signed-evidence.org/eval-receipt/v1/test-vectors.json)
is fixed by SER-04 Appendix A.3 to 232309 bytes and SHA-256
`710cb8abab7ca51cf61b85c5610018f9a153add4c3db4f71b2d597e57b1671d1`.
It contains 66 vectors. The
[proofbundle fixture at a339424e07fd58fa261d8ca3f41af5de4dcbf751](https://github.com/b7n0de/proofbundle/blob/a339424e07fd58fa261d8ca3f41af5de4dcbf751/tests/fixtures/signed_eval_receipt/draft1_vectors.json)
is separately pinned with its README, license and exact-commit discovery tree.
Its README describes the older -00 provenance. Reconstruction demonstrates all
66 receipt byte strings equal the public SER-04 vector file; this does **not**
upgrade that implementation to a newly tested -04 verifier. No proofbundle code
was imported or executed. A mutable vector URL is acceptable here only because
its exact bytes match the digest in the pinned draft.

## Profile and measured routes

`CP_REQUIREMENTS.md` paraphrases the published obligations with section references.
`mapping_profile.json` declares the local interpretation, unknown-value policy,
resource bounds, numerical rules and four experiment labels.

| Route | Consumer receives | Source of mapping rule |
|---|---|---|
| SER | Exact supplied receipt | SER-04 sections 3 and 5 |
| DSSE | B and selected signature in an envelope | Mappings-04 section 4.1; exact external M1 reproduced |
| DIGEST_ONLY | Typed JSON digest reference, no receipt candidate | Mappings-04 section 5.1 |
| DIGEST_RESOLVED | Same typed reference plus a matching receipt candidate | Mappings-04 sections 3.3 and 5.1 |

The typed reference is a citation form described for use in SCITT/COSE contexts;
this experiment does not construct or verify a COSE Signed Statement, implement
`cpb-refs`, register with a Transparency Service or verify a SCITT receipt. The
local consumer explicitly selects section 5.1's interpretation for the experiment;
this is not a new normative accepting profile. DSSE is the richer payload-carrying
route. in-toto test-result, SLSA VSA, certificate profiles and PRML are not exercised.

The normalized dictionaries in `src/profile.py` are **internal analysis records**.
They separate source assertions, local derivations, later consumer judgments,
actor-scoped availability, typed verification and limitations. The consumer reads
only supplied wire bytes and, on the resolved route, an explicitly supplied
candidate. It never consults the harness's earlier context to fill a missing field.

No executed model, evaluator identity, corpus/configuration bytes, complete
population, pre-run chronology, evidence custody, decision authority or enforcement
is inferred. `n` is the issuer's reported count. Model/dataset commitments bind
identifiers under the SER construction; they are not model/dataset artifact digests.
`criteria_digest` is reported unless its actual bytes were provided and recomputed;
this experiment never supplies those criteria bytes.

## Fixtures and test scope

`fixtures/MANIFEST.json` identifies exact extractions of P1, P2, P4, P6, P10, N7,
N13, N14 and DSSE M1. `fixtures/scenarios.json` records all 20 CP scenarios and their
observable obligations. The runner also reconstructs all 66 proofbundle receipts,
checks all public vector byte-block hashes, and executes mappings C1–C8 and R1–R16.
It does not run the 66 SER verification verdicts.

All context added by this experiment is **author-constructed local fixture data**:
completion/no-criterion states, error/non-execution states, two-metric run context,
attempt lists, partial coverage/exclusions, missing evidence references and
amendment relationships. These are justified pressure cases from CP-00 Appendix A,
not extensions asserted to be valid SER fields. Generated altered payloads have an
empty signature and are explicitly unsigned semantic/negative specimens, not valid
signed SER receipts. CP-T01/02/05 are native-domain boundary probes: unsupported
states remain distinct locally and are refused as SER encodings.

`structure_and_arithmetic: SUPPORTED` means only that this implementation accepted
the supported payload subset and its exact decimal comparison. It is not a full
SER validation result. The canonical serializer is restricted to the SER payload's
fixed ASCII keys, strings, boolean and bounded integer `n`; it is not general JCS.
Ed25519 signature and selected-key verification are always **NOT_EVALUATED**.
Published signature expectations remain attributed external expectations.
CP-T12/13 use an explicit local HMAC-SHA256 test carrier to demonstrate that later
authentication cannot supply earlier missing semantics. The key is public test
material; this is not an Ed25519 signature, signer-identity proof or SCITT test.

The 48-cell requirement matrix answers explicitly bounded questions. Some rows
report preservation of a limited declaration/negative behavior, while other rows
ask whether stronger context is available. **PRESERVED does not mean all clauses of
that R-CP requirement are implemented.** NOT_APPLICABLE boundary probes are not
native positive cases. The report makes no independent-interoperability claim.

## Artifacts and provenance

- `RESULTS.md`: requirement × route matrix, scenario results and concrete losses.
- `results.json`: complete deterministic observations, checks and exact input hashes.
- `run_record.json`: initial clean state, base/branch, fetch output and validation record.
- `PROPOSED_CP_01_CHANGES.md`: conditional editorial preparation only; no submitted text.
- `sources/`: unchanged external response bytes, including metadata snapshots.

The published IETF material retains its stated IETF Trust/BCP 78/79 terms. It is not
relicensed by placement in this repository. proofbundle's pinned MIT license is
retained in `sources/proofbundle-LICENSE`; extracted fixtures retain their original
provenance. The raw discovery tree and metadata are snapshots, not instructions.

Only this experiment directory is changed. No frozen AIREP or normative schema
was edited. No other task was started; no push, PR, issue, external comment, contact,
publication or IETF submission was made.
