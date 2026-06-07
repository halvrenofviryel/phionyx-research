# Phionyx Compliance Mappings

This directory contains evidence mappings that connect Phionyx Core's runtime
artifacts to industry threat models, risk frameworks, and regulatory
requirements. Each mapping is an **evidence document, not a certification**
— it tells an external reviewer which Phionyx component addresses each row in
the target framework, with which coverage level (Full / Partial / Gap), and
how to verify the claim from the public repository.

## Available mappings

| Document | Target framework | Mapped Phionyx version | Status |
|----------|------------------|------------------------|--------|
| [`owasp-agentic-ai-2025.md`](owasp-agentic-ai-2025.md) | OWASP Agentic AI — Threats and Mitigations v1.0 (Feb 2025) — 15 threats | v0.3.0 | **Public** |
| [`eu-ai-act.md`](eu-ai-act.md) | EU AI Act, Articles 9–15 (high-risk obligations) — with explicit deployer-responsibility per article | v0.3.0 | **Public** |
| [`nist-ai-rmf.md`](nist-ai-rmf.md) | NIST AI Risk Management Framework 1.0 — Govern / Map / Measure / Manage (4 functions) — with explicit deployer-responsibility per function | v0.3.0 | **Public** |
| [`iso-42001.md`](iso-42001.md) | ISO/IEC 42001:2023 AI Management System — 15 control-type rows (1 Full / 8 Partial / 6 Gap) — **draft**, Annex A identifier accuracy requires paid-text verification | v0.3.0 | **Public (draft)** |

Each `Public` row is linked from the [Evidence Matrix at /evidence](https://phionyx.ai/evidence) and is part of the load-bearing public claim set.

## Reading conventions

Every entry in every mapping uses the same structure:
- **Framework description** — paraphrased from the framework, not invented.
- **Phionyx mechanism** — specific block / contract / governance feature.
- **Coverage** — `Full` / `Partial` / `Gap`.
- **Evidence** — file paths, test names, and reproducibility commands a reviewer can run.
- **What's still missing** — explicit residual risk, even on `Full` rows.

## What these mappings are not

- **Not** a certification, accreditation, or compliance attestation.
- **Not** a substitute for a third-party security audit.
- **Not** legal advice.

Phionyx is not an accredited authority. Adopting Phionyx does not by itself satisfy any regulatory or contractual obligation; it produces artifacts an auditor or compliance officer can use as inputs to such an assessment.

See the homepage [Scope of Claims and Known Limitations](https://phionyx.ai) for the broader framing.

## Cadence

Mappings are re-verified:
- After every Phionyx minor release (the `Mapping last verified` date is bumped).
- When the target framework publishes a new version.
- When an independent reviewer re-classifies a row (their note will be appended).

## Machine-readable schema

The structural complement to the human-readable Markdown mappings lives at
[`schema/`](schema/) — JSON Schema (Draft 2020-12) for one mapping row plus a
canonical example and validator. The schema enforces that every row MUST cite
a Phionyx mechanism, MUST have at least one piece of reviewer-reproducible
evidence, and MUST state the deployer's residual responsibility — even when
coverage is `Full`. This is the stable row format other projects can adopt to
produce their own evidence pages from the same data; it sits alongside the
[AI Runtime Evidence Protocol (AIREP)](https://github.com/halvrenofviryel/ai-runtime-evidence-protocol),
the experimental open format for per-decision evidence receipts that Phionyx emits.
