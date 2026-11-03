# Scorer input and frozen metric contract

This is a stdlib scorer for the preregistered K1 protocol. It executes no
comparator and derives no oracle. The author protocol/profile define the metrics;
the scorer implements them. The evaluator receives evidence and PROFILE only.
Oracle and latent truth are inputs only to scoring.

## Python API

`score(cases, predictions)` returns a JSON-serializable report without mutating
its arguments. `cases` is a nonempty list of normalized objects:

```python
{
    "case_id": "opaque-id",
    "split": "development",  # or "holdout"
    "category_id": "opaque-category",
    "queries": [{
        "claim_id": "opaque-row-id",
        "kind": "receiver_receipt",  # one fixed PROFILE kind
        "subject": {...},
        "scope": {...},
        "oracle": {
            "justified_state": "INDETERMINATE",
            "qualification": "NOT_SUPPORTED",
            "conditions": ["missing_receiver_observation"],
            "ambiguous": False,
            # Optional rationale, evidence_basis, missing_evidence,
            # known_nonclaims, draft_clauses and other inspectable metadata.
        },
        "latent_truth": None  # explicit bool or null; integer 0/1 forbidden
    }],
    "reconciliation": {
        "obligations": [...],
        "instruction_accounting": {...},
        "obligation_counts": {...},
        "receiver_record_counts": {...},
        "structural_result": "INCONCLUSIVE",
        "aggregate_claim": {"qualification": "NOT_SUPPORTED", "conditions": [...]}
    }
}
```

Reconciliation is required when scoring `acder_bounded`. Other case metadata is
retained in all-row output. `predictions` maps each supplied comparator name to a
list of `{case_id, claims, ...}` outputs. Claim objects use the shared output
schema: claim_id, state, qualification, conditions, reason_codes, evidence_refs.
Extra kind/subject/scope metadata remains visible. ACDER output supplies the six
reconciliation fields above. Its aggregate may also contain fact/scope, which
remain inspectable and are not exact-prose scores.

Only the three fixed comparator names are accepted. Small API checks may supply
a subset; the report explicitly lists missing comparators and marks that run
incomplete. Every supplied comparator must emit every supplied case and query
exactly once. Missing/duplicate/unknown case or claim IDs, invalid states,
conditions, qualification, ambiguity/latent types and malformed claim arrays
raise `InputError`. No missing prediction is silently replaced with NOT_EVALUATED.
NOT_APPLICABLE is a retained prediction state, never a request to remove a row.

## CLI and raw author files

```sh
python3 -B score.py \
  --evidence-dir /path/to/selected/evidence-subtree \
  --oracle-dir /path/to/matching/oracle-subtree \
  --predictions /path/to/comparator-output.json \
  --out /path/to/new-scoring-output.json
```

For each `<relative-case-dir>/evidence.json` under the explicit evidence subtree,
the loader reads `<relative-case-dir>/oracle.json` and `latent_truth.json` under
the explicit oracle subtree. Both roots can be the same author case directory;
use a development-only subtree before the holdout gate. The loader does not
discover sibling splits. It validates case/claim identity, oracle kind and the
exact latent reference `latent_truth.json#/claim_truth/<claim_id>`.

Raw oracle shape is `{schema,case_id,derivation,claims,reconciliation}` with each
claim's `justified_state`, qualification, conditions, ambiguity and documentation.
Raw latent shape is `{schema,case_id,status,claim_truth,latent_facts}`. The frozen
selection maps opaque case IDs to split/category metadata. All three input-file
SHA-256 values and paths are retained. Scoring is not author-file schema
validation or a substitute for the author's independent oracle validation.

PROFILE and SCENARIO_SELECTION bytes must match the pinned shared hashes. The
CLI refuses an existing output path, exits 2 for an input error, and emits no new
successful report on failure. First measurement output must be preserved; choose
a distinct path for an explicitly versioned follow-up.

## Metrics

Every comparator × development/holdout/total × fixed claim kind/ALL_KINDS bucket
contains numerator, denominator and rate; a zero denominator has rate null.
Eligibility is **fixed-contract applicable AND oracle ambiguous=false**.
Ambiguity excludes only that claim, never all claims or structural outputs of
the case. All rows remain visible, including nonapplicable and ambiguous rows.

| Metric | Numerator | Denominator |
|---|---|---|
| unsupported_stronger_support | Predicted SUPPORTED | Eligible non-integrity oracle-not-SUPPORTED rows |
| semantic_incorrectness | Definite prediction contradicts bool latent truth | Eligible definite SUPPORTED/REFUTED predictions with bool truth |
| false_rejection | Predicted REFUTED | Eligible oracle-SUPPORTED rows |
| useful_support_recall | Predicted SUPPORTED | Eligible oracle-SUPPORTED rows |
| appropriate_withholding | Predicted INDETERMINATE or NOT_EVALUATED | Eligible oracle-INDETERMINATE-or-NOT_EVALUATED rows |
| state_agreement | Exact state match | All eligible rows |
| qualification_agreement | Exact qualification match | All eligible rows |
| exact_condition_retention | Same sorted unique condition set | All eligible rows |

The first metric's numerator is restricted to its stated denominator, as are all
other numerators. Integrity has a separate kind and is excluded only from the
stronger-support metric. Unsupported-but-latently-true assertions are a separate
count, not semantic errors. Null latent truth supplies no semantic denominator;
INDETERMINATE and NOT_EVALUATED are not definite false predictions.

Each bucket retains the fixed 5×5 state confusion matrix, all-row and eligible
state counts, applicability/ambiguity counts, unexpected NOT_APPLICABLE and
outside-contract outputs, and supported claims withheld as INDETERMINATE versus
NOT_EVALUATED. All rows preserve original prediction, evidence-oracle
qualification/conditions, rationale/evidence/nonclaim metadata, query scope,
latent truth/error and missing/extra conditions. Raw row error flags can also be
present on excluded rows; `primary_eligible` determines metric inclusion.

## Separate reconciliation checks

Only ACDER's contract includes reconciliation outputs. Structural result,
per-target disposition/identity, instruction accounting, obligation counts and
receiver counts are compared independently of claim metrics and ambiguity.
Differences retain paths and raw values, distinguish missing from null and bool
from integer, and do not repair predictions. Aggregate qualification and condition
agreement are separately reported per case and split. Aggregate fact/scope and
prose rationale remain inspectable rather than becoming count mismatches. Text
reasons and evidence-reference wording are never exact-string scoring targets.

This scorer produces no winner, significance, confidence interval, population
prevalence or real-world safety claim. Interpretation and HOLD/no-difference
decisions belong to the frozen benchmark's final report.
