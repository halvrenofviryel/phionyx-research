# External evidence

Independently authored implementations measured against frozen AIREP releases, and what each
result does and does not establish.

Every entry records the exact frozen AIREP version under test, the exact external artifact
identity, and the boundary of the claim. An entry is added only after the result has been
reproduced by the maintainer side from the external artifact itself.

> **Version boundaries are load-bearing.** The entries below target **different frozen AIREP
> versions**. They are separate evidence classes and are not additive.

---

## Emek Can Doğru — AIREP v0.1.2 — producer side

| | |
|---|---|
| Evidence class | independently authored **producer** |
| Frozen AIREP version under test | **v0.1.2** — tag `v0.1.2`, commit `44387bd43cc06ba656eaa7ff670be5c8e3220aca` |
| External repository | <https://github.com/dogrucanemek-alt/airep-independent-producer> |
| Pinned external commit | `31e12be987105d2ba93ab2abe6135d9e6d5374d2` |
| External bundle licence | Apache-2.0 |
| Verifiers used | frozen v0.1.2 `conformance/verify.py` (`sha256:dc26e22420f174e3bce90e18455ec66786a2a727f4d125ee5865b12659ced7dd`) and `conformance/verify.mjs` (`sha256:9123cccc93ff62541aea08f7f6f6f9e62923822e3561e8d44990073efacae089`) |
| Maintainer-side reproduction | **reproduced** |

### What was reproduced

Running the producer and then running both pinned v0.1.2 verifiers over its output reproduced the
reported result exactly:

- both `integrity.current` values reproduce byte-for-byte —
  `sha256:f6689ea3d183f7ef83e6061ab8e5f26273c924edfec177a9d35d1effb9af3e93` and
  `sha256:dafabb318c840165c6d64077c042cf16477f2cacc2f2b490c1470b34983c4529`, with record 1's
  `previous` equal to record 0's `current`;
- **the first invocation was an acceptance.** Both verifiers reported `PASS sig=skip` without a
  key, `PASS sig=ok` with the producer's public key, and `class=Core` / `CLASS: Core` under
  `--class`. All six commands exited 0.
- the hashes are key-independent: two producer runs with different keys produced identical
  `integrity.current` values and different signature values.

No first-party producer was substituted, and no compatibility workaround was introduced.

**What the reproduction does not cover.** It measures the producer's *behaviour*, not how it was
authored. That the producer was written from `SPEC.md` and `core.schema.json` rather than from a
reference producer is recorded in the bundle's `METHOD.md` as methodology plus the author's
attestation, and `METHOD.md` states the limit itself:

> The claim that the reference producers were never read cannot be proven from the artifacts. What
> can be stated is this: the reference producers, the example-regeneration script, and the git
> directory were removed from the working copy before the producer was written, so they were not
> present to be read, and the author attests to the order of work.

`METHOD.md` lists those removed paths with the SHA-256 of each, taken before removal. Nothing in the
maintainer-side reproduction confirms or could confirm the ordering — an artifact cannot testify to
what its author did not read. The independence claim therefore sits at methodology and attestation
level, and is recorded here at exactly that strength.

### The normative ambiguity this exposed

Acceptance rested on two choices the frozen v0.1 text does not make. Verified against the frozen
v0.1.2 `SPEC.md` rather than taken on report: `signature.value`, `base64`, `UTF-8`, `signed bytes`
and `preimage` each occur **zero** times in it. Section 6 requires a producer to sign
`integrity.current` — a string, `sha256:` followed by 64 lowercase hexadecimal characters — but
does not state whether the signed bytes are that string or the 32 bytes it denotes, and does not
state how `value` is encoded.

The bundle re-signed the same records under the other two readings, same key, nothing else changed.
Both pinned verifiers rejected both variants with a signature-only failure, reproduced here:

| Variant | Reading | `verify.py` | `verify.mjs` |
|---|---|---|---|
| baseline | UTF-8 bytes of the string, hex value | `sig=ok`, exit 0 | `sig=ok`, exit 0 |
| A | the 32 digest bytes the string denotes, hex value | `FAIL(signature)`, exit 1 | `FAIL(signature)`, exit 1 |
| B | UTF-8 bytes of the string, base64 value | `FAIL(signature)`, exit 1 | `FAIL(signature)`, exit 1 |

`integrity.current` is computed with `integrity.signature` removed, so the hashes and chain links
are untouched by construction and only the signature moved. This is tracked as a historical v0.1
interoperability limitation; released v0.1.2 is preserved unchanged.

Two further observations are **interface conventions, not normative-core defects**, and are
recorded as such: `SPEC.md` does not state how a chain is serialised as a file (the string `jsonl`
occurs zero times in it; one-record-per-line comes from the usage line in
`conformance/README.md`), and the CLI public-key encoding is convention rather than specification.

### What this establishes

An independently authored producer, written from the published v0.1 specification, emitted records
that both pinned v0.1.2 reference verifiers accepted on first invocation.

### What this does not establish

**One compatibility result, not a general interchange property.** It does not establish deployment
interoperability, that arbitrary independent producers will interoperate, or anything about
AIREP v0.2. Emek Can Doğru did **not** implement a v0.2 producer.

---

## Joel Hillier / Certisyn, Inc. — AIREP v0.2 — consumer/verifier side

| | |
|---|---|
| Evidence class | independently implemented **consumer/verifier** |
| Frozen package | AIREP v0.2 Independent-Verifier Corpus v0.1, `sha256:b47f01c81577c9dc95b7d1f1fd1119c839866e182d24c251c386ad2a08b17923` |
| Implementation digest | `sha256:2aef1212adeaab5a1dc7f07c3f240183db97478b247c008c5fcc0e177fbfeca8` |
| Implementation source licence | BSD-3-Clause as published by OSI, copyright 2026 Certisyn, Inc. — on `AIREP-verifier-source.txt` only; no licence asserted for the other three artefacts |
| Maintainer-side reproduction | **reproduced** |
| Public deposit of the frozen artefacts | [`external-evidence/certisyn-2026-09/`](./external-evidence/certisyn-2026-09/) — byte-exact, with `SHA256SUMS` and a separate `LICENSE.AIREP-verifier-source.txt` |

Joel Hillier (Certisyn, Inc.) independently implemented an AIREP v0.2 consumer from the frozen normative contract. The run record states that first-party AIREP verifier code was not fetched or read; expected outcomes were present in the package, so no expected-blind claim is made. Against the release-pinned corpus, the implementation reproduced all six fixed vectors byte-exact and matched every frozen field across all 18 cases. The sole disagreement was the package-derived `cryptographic_result` projection for `CLS-XT1`, which the external report classifies as an expected-result defect.

### Maintainer-side reproduction

The four external artefacts were hash-verified before execution, the implementation was
reconstituted from the supplied concatenation without altering a byte (re-concatenation hashes to
the declared implementation digest), and it was executed unmodified in an offline container against
the exact frozen package:

- package integrity, using the package's own `tools/verify_package.py`: `OK: 337 files present,
  digests match, no unexpected files, no prohibited key material, source basis correct`;
- raw verdicts reproduce **byte-exact** —
  `sha256:f4a2b23ab1b996ac3daa4b5985fd90f96467bbe84b6ad878832cf09f73d36f92`;
- all six fixed vectors reproduce byte-exact: V1–V4 canonical bytes, tags, preimages,
  `integrity.current` and producer signature; W1–W2 canonical claim bytes, witness tag, witness
  preimage and witness signature, including W2's non-ASCII `chain_id`;
- all 18 report rows validate against the package report schema and carry the single implementation
  digest above;
- the frozen run remains **17 AGREE / 1 DISAGREE**.

`CLS-LEX1` was confirmed in both directions: the source lexeme `1e0` is rejected under E-1 rather
than normalised to the decoded value `1`; spelling the same member `1` turns the case into
`AIREP-Witnessed` with all five channels empty; injecting `1e0` into the otherwise clean `CLS-P2`
reproduces the same `witness-claim-invalid` failure.

`CLS-XT1` reproduced identically on every frozen field — class `AIREP-Core`, all five reason
channels, observer assessment, process exit, run validity and signing-input reconstruction. The
disagreement is confined to the package-derived `cryptographic_result` projection: expected `PASS`,
observed `NOT_EVALUATED`. Contract section 4 and ruling **R-6** make stage 4's prerequisite
"binding accepted **and** not definitively revoked", so on a definitively revoked producer binding
the signature stage does not execute and no signature is verified under any key. The disagreement
is therefore a defect in the package-derived expected projection, **not** a failure of the frozen
class-verifier contract.

### What this establishes

One external, independently implemented consumer/verifier, run against a release-pinned handoff
corpus, matched every frozen field across all 18 cases; the sole disagreement was the
package-derived projection described above. Subject to the exposure qualifications recorded above.

### Deposit

The four frozen artefacts are deposited byte-exact at
[`external-evidence/certisyn-2026-09/`](./external-evidence/certisyn-2026-09/), verifiable with
`sha256sum -c SHA256SUMS`.

**Licence scope: `AIREP-verifier-source.txt` only.** BSD-3-Clause as published by OSI, copyright
2026 Certisyn, Inc., is an **implementation/source licence** on that one file. It is not a licence
for the external evidence set. No licence is inferred or asserted for `AIREP-RUN-RECORD.txt`,
`AIREP-report-18-rows.txt`, or `AIREP-observed-verdicts.txt`, and no terms are invented for them.

| Artefact | Licence status |
|---|---|
| `AIREP-verifier-source.txt` | **BSD-3-Clause**, copyright 2026 Certisyn, Inc. |
| `AIREP-RUN-RECORD.txt` | No licence asserted |
| `AIREP-report-18-rows.txt` | No licence asserted |
| `AIREP-observed-verdicts.txt` | No licence asserted |

The licence is carried in [`LICENSE.AIREP-verifier-source.txt`](./external-evidence/certisyn-2026-09/LICENSE.AIREP-verifier-source.txt)
and [`LICENSE-SCOPE.txt`](./external-evidence/certisyn-2026-09/LICENSE-SCOPE.txt), never as a header
inside the frozen source: that file's digest
(`sha256:2aef1212adeaab5a1dc7f07c3f240183db97478b247c008c5fcc0e177fbfeca8`) is the implementation
identity recorded on all 18 report rows, so a header would break that tie.

On the licensed source: **no patent rights, expressly or by implication**; it **neither anticipates
nor alters the BCP 79 disclosures Certisyn has filed against its own Internet-Drafts**, where the
licensing declaration is still to come; redistribution, modification and archiving are permitted on
BSD-3-Clause's own terms; the copyright notice and disclaimer must be retained; and the Certisyn
name may not be used to endorse a derived work.

**No DOI is claimed for this deposit.**

### What this does not establish

This run does **not** establish:

- a third-party AIREP v0.2 **producer**;
- deployment interoperability;
- semantic correctness of the protocol as a whole;
- AIREP v0.2 stability;
- IETF endorsement;
- SCITT endorsement.

It is also **not expected-blind validation**: the expected outcomes shipped inside the same archive.
The runner's work-order sequence is his own recorded account and is not an independently checkable
property.

---

## Cross-version non-claim

**These two results MUST NOT be combined into a producer↔consumer interoperability claim because
they target different frozen AIREP versions.** The producer-side result is against v0.1.2; the
consumer-side result is against the v0.2 release-pinned corpus. No AIREP version has both an
independent producer and an independent consumer measured against it.
