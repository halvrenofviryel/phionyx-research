# Explain supplied lifecycle evidence

This is a NON-NORMATIVE, first-party explanatory view of the existing
`0.2-beta.1` reconciliation result. Package version remains `0.2.0-beta.1`;
wire version remains `0.2`. It is a derived view, not a new AIREP conformance
layer, artifact family, assurance class or change to reconciliation semantics.

Run from the repository root after the existing dependency setup. Use a fresh
output directory for the lifecycle generator:

```bash
python3 examples/v02/run_lifecycle.py --out /tmp/airep-explain-example
python3 -m tools.airep_v02 explain \
  --input /tmp/airep-explain-example/lifecycle.json \
  --bindings /tmp/airep-explain-example/bindings.json \
  --revocation /tmp/airep-explain-example/revocation.json \
  --independence-policy /tmp/airep-explain-example/independence.json
python3 -m tools.airep_v02 explain \
  --input /tmp/airep-explain-example/variants/no-receipt.json \
  --bindings /tmp/airep-explain-example/bindings.json \
  --revocation /tmp/airep-explain-example/revocation.json --json
```

For a dependency-ready checkout, the committed fixture also works immediately:

```bash
python3 -m tools.airep_v02 explain --input examples/v02/fixtures/complete.json
python3 -m tools.airep_v02 explain --input examples/v02/fixtures/complete.json --json
```

Without trusted operator inputs, authentication is visibly `NOT_EVALUATED`;
schema/hash admission can still be `SATISFIED`. `--out path` preserves the
existing refusal to overwrite an output file. Exit zero means evaluation
completed, including `FAILURE`, `MISSING`, `NOT_EVALUATED` or `INDETERMINATE`.
Unreadable/invalid run input exits one; CLI usage errors exit two. Input is an
artifact array, as for `reconcile`; saved reports are not accepted or trusted.

## Reading the matrix

| Field | Meaning in this derived view |
|---|---|
| `claim` | NON-NORMATIVE rendering label for the named claim family; never an assurance assertion |
| `source`, `source_check` | JSON pointer into the equivalent native `reconcile` result and its unchanged check name |
| `source_status` | Exact native state or summary status; null when there is no native predicate |
| `explanatory_status` | Normally null; `NOT_EVALUATED` only for a predicate unavailable from the reconciler, explicitly a NON-NORMATIVE rendering label |
| `basis` | Unchanged check detail, or an explicit explanation of an unavailable predicate |
| `source_artifact_references` | Native supporting references, preserving empty and ambiguous evidence sets |
| `context` | Original subject (including Decision/instruction identity), supplied population, occurrence indexes and target window if evaluated; null means no evaluated window available |
| `limitations` | Per-row qualifications in addition to the view-level limitations |

`artifact_context` preserves each admitted occurrence's declared scope and
reported timestamp. A timestamp is not a verified event time or a coverage
window. Ambiguous identities are not resolved by picking one occurrence.
`record_assurance` preserves every admission and complete class result, including
failure, withheld, caveat, observer, operator-input digest and profile channels.
The text renderer prints every field from the same object as JSON mode and
escapes embedded newlines/control characters in reported text.

The complete fixture reports dispatch, receipt, execution and bound observation,
yet intended-target coverage remains `NOT_EVALUATED` and the aggregate remains
`INCOMPLETE`. The native summary vocabulary is `SATISFIED`, `FAILURE` and
`INCOMPLETE`, not a global PASS/FAIL verdict. Profile PASS/FAIL remains separate
inside each record's class result. Structural success cannot establish a
relying-party claim.

The missing-receipt variant keeps dispatch `SATISFIED`, receipt and execution
evidence `MISSING`, and TOCTOU `NOT_EVALUATED`. This is no proof of non-delivery
or non-execution. Omitting the independence policy keeps effective observer
independence unknown and its check `INDETERMINATE`; same-executor observation
remains evidence without independent corroboration.

## Enforcement, effect and consumer claims

The worker-pause example describes an application enforcement action. In the
`no-effect.json` variant, execution of that action is reported and its digest
comparison is `SATISFIED`, while bound Effect evidence is `MISSING`. That report
does not establish the resulting worker state. The current reconciler has no
separate enforcement predicate: `explain` therefore marks `enforcement_observed`
with null native status and explanatory `NOT_EVALUATED`. Failed and suppressed
execution outcomes retain their native `FAILURE` and explicit event names; they
are not reinterpreted as successful enforcement.

Similarly, an Effect report supplies observed state without proving causation,
desired effect or independent corroboration. The view retains effect binding
and observer checks to qualify it. No consumer claim or acceptance policy is
evaluated, so `relying_party_claim_support` has explanatory `NOT_EVALUATED` even
when particular structural checks are satisfied. Neither row declares the
event or claim false. Separate enforcement or claim-support adjudication cannot
be represented as a native reconciler result without extending its contract;
this feature makes no such extension.

These deterministic fixtures and tests are internal regression evidence, not
third-party independent evidence, deployment interoperability, truth assurance
or complete population coverage. The source audit is recorded in
[source-basis.json](../../reports/explain/source-basis.json).
