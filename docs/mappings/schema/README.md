# Compliance-mapping JSON Schema (v0.1)

This directory holds the machine-readable schema for one row of a Phionyx compliance mapping. It is the structural complement to the human-readable mappings in `docs/mappings/owasp-agentic-ai-2025.md`, `docs/mappings/eu-ai-act.md`, and `docs/mappings/nist-ai-rmf.md`.

The schema is intentionally tight: every row MUST cite a Phionyx mechanism (file / block / contract / test), MUST have at least one piece of reviewer-reproducible evidence, and MUST state the deployer's residual responsibility — even when coverage is `Full`. Honest framing is encoded in the type system, not just in the prose.

## Files

| File | Purpose |
|------|---------|
| [`compliance_mapping_row.schema.json`](compliance_mapping_row.schema.json) | JSON Schema (Draft 2020-12) for one mapping row. |
| [`example_row.json`](example_row.json) | Canonical example: EU AI Act Article 12 (Record-keeping) → AuditRecord v4. |
| [`validate.py`](validate.py) | Tiny validator (uses `jsonschema`) confirming `example_row.json` conforms. |

## Run

```bash
pip install jsonschema
python docs/mappings/schema/validate.py
```

Expected output:

```
OK: example_row.json validates against compliance_mapping_row.schema.json
     framework            = EU AI Act Regulation (EU) 2024/1689
     identifier           = Article 12
     coverage             = Full (within the runtime perimeter ...)
     mechanisms           = 3
     evidence_items       = 3
```

## Why this exists

Phionyx's evidence-protocol thesis is that runtime-governance evaluations should produce *reproducible software evidence*, not just policy documentation. To make that concrete, the protocol needs a stable row format that other projects can adopt. This schema is that stable row format. A LangGraph- or AutoGen-based governance layer can write a JSON file conforming to this schema and produce its own `/evidence`-style page from the same data.

## Required fields, at a glance

| Field | Why required |
|-------|--------------|
| `framework` + `framework_version` + `framework_identifier` | Stable lookup key — without it, "Phionyx maps to Article 12" is unverifiable. |
| `framework_text` | Forces the row author to paraphrase the obligation, not just hand-wave it. |
| `phionyx_mechanism[]` | Every row MUST point at concrete artifacts. Empty mechanisms are not a row, they are a wish list. |
| `coverage` (Full / Partial / Gap) | The honest answer. `Full` is rare; `Gap` is fine — both are more useful than a vague "it depends". |
| `evidence[]` | At least one reproducible piece of evidence per row. A claim without evidence is not a claim. |
| `deployer_responsibility` | REQUIRED on every row, including `Full` rows. Encodes the constitutional fact that no runtime ever satisfies a regulatory obligation by itself. |

## Status

`v0.1` — initial release alongside the OWASP / EU AI Act / NIST mappings. Schema fields may be tightened (e.g., enum validation for canonical block names) once the JSON form of all three mappings is generated.

## Cross-references

- Companion human-readable mappings: [`../owasp-agentic-ai-2025.md`](../owasp-agentic-ai-2025.md), [`../eu-ai-act.md`](../eu-ai-act.md), [`../nist-ai-rmf.md`](../nist-ai-rmf.md)
- Governed-response envelope schema: [`../../../examples/envelopes/governed_response.schema.json`](../../../examples/envelopes/governed_response.schema.json)
- Evidence Matrix (web): <https://phionyx.ai/evidence>
