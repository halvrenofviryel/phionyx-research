# The Measurement Axioms

*Measurement discipline for AI governance evidence — a research doctrine from Phionyx Research (Ali Toygar Abak).*

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21763430.svg)](https://doi.org/10.5281/zenodo.21763430)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**A governance system that returned `safe` may have checked nothing.**

A governance verdict is a measurement of a claim about a system. A measurement
that was not taken must not be reported as one that passed — and the failure is
not exotic. A verifier that returns `valid` for an empty chain, a coverage
metric computed against a repository it could not read, a gate whose silence is
indistinguishable from approval: each serialises a non-measurement as assurance.

This repository holds the doctrine, the specification extracted from it, and an
audit of its authors' own runtime against it.

---

## What is here

| | |
|---|---|
| [`THE_MEASUREMENT_AXIOMS.md`](./THE_MEASUREMENT_AXIOMS.md) | The doctrine. Seven axioms, five properties of a governance measurement path, the verdict algebra, boundaries. **Start here.** |
| [`THE_EVIDENCE_STACK.md`](./THE_EVIDENCE_STACK.md) | Where the doctrine sits relative to a runtime, an evidence protocol and a record format — so the relationship does not have to be inferred |
| [`spec/v1.0/`](./spec/v1.0/) | The normative extract: 45 numbered requirements, a record schema, conformance requirements, a reference implementation, and a checksum manifest |
| [`audit/`](./audit/) | The doctrine applied to its authors' own system. Twelve findings |
| [`tests/`](./tests/) | 314 tests over the specification and the reference implementation |

## The verdict algebra

Six values, and two prohibitions that are the point of the whole document:

```
PASS · FAIL · NOT_MEASURED · INCONCLUSIVE · ERROR · NOT_APPLICABLE
```

**An absence is not a result.** A check that could not run reports
`NOT_MEASURED`, never `PASS`.

**A proxy is not the thing.** The presence of a digest is not fetchability; a
verdict emitted is not a verdict enforced.

These are separate axes and must stay separate in the record:

```yaml
decision_outcome:     ALLOW | DENY | MODIFY | DEFER | STEP_UP
measurement_status:   PASS | FAIL | NOT_MEASURED | INCONCLUSIVE | ERROR | NOT_APPLICABLE
enforcement_status:   NOT_REQUIRED | REQUESTED | ACKNOWLEDGED | APPLIED | FAILED
evidence_status:      E0 | E1 | E2 | E3 | E4
```

## Verify this release

```bash
cd spec/v1.0 && sha256sum -c CHECKSUMS.sha256   # five frozen artefacts
python -m pytest tests/ -q                      # 314 tests
```

A frozen version that cannot be checked is a claim about itself.

## What this document does not claim

- **No conformance claim about any implementation, including its authors'.**
  The licence grants no right to describe a system as conformant; conformance is
  assessable against [`conformance-requirements.yaml`](./spec/v1.0/conformance-requirements.yaml)
  and this repository assesses nothing.
- **No prevalence claim.** The audit reports findings in one runtime.
  Establishing that this failure class is common would require systems other
  than ours, and that study does not exist yet.
- **No independent verification.** See [`audit/STATUS.md`](./audit/STATUS.md):
  `independent_reproducibility: NOT_MEASURED`, `independent_review: NOT_REQUESTED`.

The audit's own most useful finding was found by an independent reader, not by
us — in the conformance probe published alongside the doctrine, which returned a
positive result having measured nothing. That is the doctrine's central failure,
produced by the artefact written to detect it. It is documented rather than
quietly fixed, because a doctrine that hides its own instance of the thing it
names has not earned the reader's attention.

## From verdict validity to claim preservation

The Measurement Axioms constrain what a governance component may report about
its own measurement. A related technical note asks the downstream question:
whether those limits survive normalization, aggregation, replay and
publication. It is a position paper, not part of this specification, and it
changes no v1.0 requirement or conformance condition.

[Access Is Not Yet Verifiability →](https://huggingface.co/blog/phionyx/access-is-not-yet-verifiability)

## Citing

```
Abak, A. T. (2026). The Measurement Axioms: A Doctrine and Specification for
Governance Verdict Validity (1.0.0). Zenodo. https://doi.org/10.5281/zenodo.21763430
```

Machine-readable metadata: [`CITATION.cff`](./CITATION.cff).

Two DOIs, and the difference matters when citing:

| | |
|---|---|
| **10.5281/zenodo.21763430** | Concept DOI — resolves to the most recent version. Cite this unless you need a specific edition |
| **10.5281/zenodo.21763431** | Version DOI — the 1.0.0 baseline edition, fixed |

Licence: CC BY 4.0. It grants no right to describe an implementation as
conformant.
