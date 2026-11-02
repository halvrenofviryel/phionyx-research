# SCITT claim-boundary demonstration

From the repository root, run:

```sh
python3 integrations/scitt-claim-boundaries/demo.py
```

This runs three **local synthetic scenarios**, writes full text and JSON explain
outputs under `.airep-demo/runs/`, and prints a compact navigation table. It uses
the repository's existing Python 3.12 / Node 20 dependency bootstrap (offline on
the reproduced Linux x86-64 axis). Use `--out /tmp/airep-scitt-demo` for a new,
explicit output directory. Existing output directories are refused.

Expected matrix: **S** = native `SATISFIED`, **M** = native `MISSING`,
**NE** = `NOT_EVALUATED`, **—** = no native check emitted, no status inferred.
S means a named predicate over supplied reports holds; it does not mean that an
event occurred or that a relying-party claim was accepted.

| Claim / evidence kind | Assumed registered | Uncheckable measurement | Composed reports |
| --- | --- | --- | --- |
| SCITT statement signature verification | NE; fixture premise only | NE; fixture premise only | NE; fixture premise only |
| SCITT registration / receipt verification | NE; fixture premise only | NE; fixture premise only | NE; fixture premise only |
| Statement existence / integrity | Local payload bytes and checksum; AIREP admission S | Same | Same |
| Identity / binding | AIREP test-policy authentication S; SCITT NE | Same | Same |
| Issuer control dispatch report | S | S | S |
| Receiver delivery report | M | M | S |
| Enforcement observation | NE | NE | Separate sidecar supplied; NE |
| Execution report / outcome | M / — | M / — | S / S |
| Effect report / binding | — / — | — / — | S / S |
| Measurement source state | No capsule projection | `UNCHECKABLE`; observation unavailable | No capsule projection |
| Coverage / completeness | NE | NE | NE, including the AEE projection |
| Relying-party claim support | NE | NE | NE |
| Native structural summary | `INCOMPLETE` | `INCOMPLETE` | `INCOMPLETE` |

`MISSING` means absent from the supplied evidence set, not proof of non-delivery
or non-execution. No Execution report exists in the first two scenarios, so D
emits no Effect check there. The adapter preserves that absence of a check.
The composed scenario also retains `execution_instruction_binding`, `toctou`,
`effect_binding` and `observer_relationship` with their original qualifications.

## What is run

`adapter.py` calls task D's unchanged `tools.airep_v02.explain.explain` and uses
its original text renderer. The boundary matrix only indexes and copies native
rows, including source pointers, evidence references, context and limitations.
External fields remain in a separate fixture ledger; no capsule or AEE record
is converted into a Decision, authorization, enforcement result or AIREP status.
The JSON `airep_explain` object is identical to the existing `explain` CLI result
on the same AIREP inputs. Tests compare both CLI text and JSON for every scenario.

The signed AIREP records are locally constructed with the existing lifecycle
fixture builder at D. The actual AIREP schema/hash/signature and binding checks
run against public, insecure **test-only** keys and explicit local operator
inputs. Separate producer identities and a fixture independence policy are not
independent third-party evidence. The demo does not contact or operate a worker,
endpoint, agent harness or transparency service.

1. **assumed-registered** grants valid SCITT signing/registration as a stated
   fixture premise, then supplies only AIREP Decision and issuer dispatch
   records. There is no COSE Signed Statement, SCITT receipt, inclusion proof,
   TS trust anchor or registration transaction here. Thus actual SCITT
   verification remains NE even though the hypothetical premise is positive.
2. **uncheckable-measurement** adds a local projection of the published Capsule
   fields: declaration, unavailable observation, differential, source digests,
   `UNCHECKABLE` and the no-authority value. Nulls and the source vocabulary
   survive unchanged. This is not a full capsule or a capsule conformance test;
   no identifier, batch root or profile verification is performed.
3. **composed-reports** supplies separate AIREP receiver, execution and effect
   reports, an application enforcement sidecar, and a partial AEE field
   projection. The stronger native predicates now satisfied concern matching
   reports, reported outcome, digest equality and reference binding. D has no
   enforcement or relying-party claim evaluator, so those remain NE. The AEE
   projection is retained, not verified; its presence establishes no complete
   call/task history. Effect binding does not establish causation or desired
   outcome. No new predicate is invented to promote these reports.

## Boundaries

- SCITT registration does not make payload assertions true.
- A SCITT receipt does not by itself prove control delivery, enforcement,
  execution or intended effect.
- A Measurement Capsule does not become authorization.
- Presence of an agent execution evidence record does not automatically prove
  all relevant records are complete.

The only external byte identity calculated here is SHA-256 of an explicitly
local JSON payload. It is not an identifier for a Signed Statement, a capsule ID
or a registration proof. Changing its bytes makes the fixture checksum comparison
false; this is separate from AIREP authentication and from unevaluated SCITT
checks. A completed demo exits zero even for negative/withheld evidence states;
it is not a conformance or assurance verdict.

## Sources and provenance

[SOURCE_PINS.json](SOURCE_PINS.json) records exact revision URLs, raw HTTP body
SHA-256, byte counts and UTC retrieval times, plus separate Datatracker discovery
responses confirming current revisions on 2026-11-02. No large text excerpts or
third-party sample objects are included.

- [RFC 9943](https://www.rfc-editor.org/rfc/rfc9943.txt), sections 4 and 7.1:
  transparency, signatures, receipt validation and relying-party validation
  policies are distinct concerns.
- [Measurement Capsule -01](https://www.ietf.org/archive/id/draft-templeman-scitt-measurement-capsule-01.txt),
  sections 3, 8, 8.1 and Appendix B.3: field names and `UNCHECKABLE` for
  `measurement.contract_parity`, with no authorization inference.
- [Agent Execution Evidence -02](https://www.ietf.org/archive/id/draft-thaha-scitt-agent-execution-evidence-02.txt),
  section 6.7 and section 9.2: receipt field projection and the limit on
  inferring harness completeness. Its section 9 verification is **not run**.

The two drafts are work in progress. This integration is not an AIREP SCITT
profile, endorsement, IETF interoperability result, or claim of conformance to
any of these documents. No RFC, draft, frozen AIREP v0.1 material or normative
schema is modified.

All fixtures are authored locally for this demonstration. The AIREP fixture
arrays are `lifecycle('no-receipt')[0]` and `lifecycle('complete')[0]` from
`examples/v02/run_lifecycle.py`; operator inputs come from `policy()` at base
`0130fcf8e7d70a0f9c4f977957e5de76ca8ef689`. Sidecars are original field
projections, not copied published vectors. Code and fixtures: Apache-2.0;
documentation: CC-BY-4.0, following repository contribution terms.

## Reproduce the checks

After the one-command bootstrap/demo:

```sh
.airep-demo/venv/bin/python -m unittest discover -s integrations/scitt-claim-boundaries/tests -v
.airep-demo/venv/bin/python -m unittest discover -s tests/v02 -v
make demo-test
make demo
python3 scripts/check_beta.py --out /tmp/airep-scitt-beta-check
```

The final output directory must be new. `check_beta.py` performs its 56 checks
in a disposable copy so frozen evidence is not overwritten. Integration tests
are a separate command; this small demo does not change the existing CI workflow.
The test suite includes tampered AIREP signatures, unavailable key bindings,
failed execution, absent effect, misleading SCITT source assertions and missing
stages despite supplied sidecars. It rejects status collapse without treating a
successful fixture test as SCITT crypto/registration verification.

For one machine-readable scenario:

```sh
.airep-demo/venv/bin/python integrations/scitt-claim-boundaries/adapter.py --scenario uncheckable-measurement --json
```

[RESULTS.md](RESULTS.md) and [run_record.json](run_record.json) bind this local run
to inputs, outputs, checks and limitations. The containing Git commit identifies
the complete review package; it is deliberately not embedded in its own contents.
