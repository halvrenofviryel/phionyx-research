# Resonatus Ontology v1.1.0

> The `v1.0.0` core ontology and default SHACL profile remain frozen. Release `v1.1.0` adds
> owner-approved, opt-in Strict Linear and Strict Assessment profiles under [`profiles/v1.1/`](profiles/v1.1/)
> without importing them into or changing the semantics of the core.

An OWL 2 DL ontology for **persistent causal trace processes**, with a SHACL validation profile,
competency questions, worked examples, adversarial fixtures, and reproducible formal-verification
artefacts. Companion research artefact for *Resonatus: An Ontology of Persistent Causal Trace
Processes* (Ali Toygar Abak, Phionyx Research).

| | |
|---|---|
| Ontology IRI | `https://w3id.org/resonatus` |
| Vocabulary namespace | `https://w3id.org/resonatus#` (prefix `res:`) |
| Frozen core version IRI | `https://w3id.org/resonatus/1.0.0` |
| Optional strict namespace | `https://w3id.org/resonatus/strict#` (prefix `strict:`) |
| Strict-profile version IRI | `https://w3id.org/resonatus/strict/1.1.0` |
| Release version | `1.1.0` |
| Zenodo concept DOI (all versions) | [`10.5281/zenodo.21939902`](https://doi.org/10.5281/zenodo.21939902) |
| Repository | <https://github.com/halvrenofviryel/resonatus-ontology> |

## What Resonatus is

Resonatus is a **proposed** ontological class: a causal trace that survives its initiating interaction,
persists, propagates, is taken up according to a receiving context, and is transformed or participates in
feedback. The definition is a modelling proposal, not an empirical causal-discovery result or a claimed
natural law.

## Layers

1. **OWL 2 DL semantic layer** — `ontology/resonatus.ttl` defines the class structure under open‑world
   semantics.
2. **Graph Shape Validation Profile** — `shapes/resonatus.shacl.ttl` validates assessment‑record
   structure and path‑coherence; it is not part of OWL class semantics and does not prove causality.
3. **Reference assessment policy** — `scripts/validate.py` maps explicit criterion verdicts to
   `MEMBERSHIP_SUPPORTED` / `NON_MEMBERSHIP_SUPPORTED` / `UNDETERMINED`.
4. **Optional BFO 2020 bridge** — `alignments/` (with a vendored, pinned BFO 2020 for offline reasoning).
5. **Evaluation materials** — competency questions/queries, worked examples, and adversarial fixtures.
6. **Optional v1.1 strict profiles** — an additive vocabulary, independently selectable SHACL
   dimensions, a multidimensional result schema, fixtures, and reproducible runners under
   `profiles/v1.1/`. Strict-profile conformance is not scientific validation.

## Constitutive definition (reified path)

The five constitutive conditions are witnessed on a single reified continuation path, not on the
candidate as separable existentials. The notation below keeps object properties separate from class
inclusion:

```
Object-property pattern:
ResonatusCandidate --hasTracePath--> ContinuationPath

Class inclusions:
ResonatusPath ⊆ CausalTraceProcess ⊆ ContinuationPath

Class definition:
Resonatus ≡ ResonatusCandidate ⊓ (∃ hasTracePath.ResonatusPath)
```

- `ContinuationPath` is the Trace‑**neutral** genus (causal status is not presupposed here).
- `CausalTraceProcess` = a `ContinuationPath` that carries a Trace continuation.
- `ResonatusPath` = the qualifying path: Trace, post‑interaction Delay, Propagation, Selectivity,
  Transformation‑or‑Feedback, and exactly one declared originating interaction, all on one path.
- `Resonatus` is a candidate with **some qualifying path**. It is **not** a subclass of
  `CausalTraceProcess`; that specialization applies to the path.

**Witness mixing** means satisfying different parts of one classification from different path
individuals, such as taking Trace from path A, Delay from path B, and Selectivity from path C. The
reified-path definition blocks that aggregation because one `ResonatusPath` must carry all five
witness types.

`res:causallyAttributedTo` has one core meaning across domains: the `TraceContinuation` is asserted to
be causally attributable to the linked `Interaction`, not merely later than or broadly influenced by
it. Domains may use different evidence methods to warrant that assertion; they may not redefine the
property's meaning. See [`DESIGN_RATIONALE.md`](DESIGN_RATIONALE.md) for the formal boundary.

**Division of responsibility:**

- **OWL 2 DL** enforces the *path‑level* semantics — all five witness types on one path node.
- **SHACL** enforces *origin/receiver co‑reference coherence* (declared origin = Trace origin = Delay
  reference; Propagation receiver = Selectivity receiver) plus completeness, using canonical RDF‑node
  identity (not `owl:sameAs`). This co‑reference is not captured by the ontology's OWL 2 DL role pattern
  (the natural chain‑plus‑functionality encoding leaves OWL 2 DL); it is scoped to that role pattern, not
  a general expressivity theorem. See `DESIGN_RATIONALE.md`.
- The **epistemic classifier** is a separate layer and never asserts ontic truth.

The historical three‑of‑five rule is not an ontological membership rule.

## Reproducible offline validation

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt          # rdflib, pyshacl, owlready2 (bundles HermiT; needs a JRE)

python scripts/run_reasoner_gates.py     # OWL 2 DL gates R2–R17 (HermiT); R2 uses the vendored BFO 2020
python scripts/run_shacl_gates.py        # SHACL assessment + path‑coherence gates R18–R26 (pyShACL)
python scripts/run_example_crosslayer.py # 13 aligned examples + 2 independence cases + outcome guards
python scripts/run_competency_queries.py # 7 executable structural queries from 22 documented questions
python scripts/validate.py .             # verdict‑based reference classifier
python scripts/audit_structure.py        # structural audit
python scripts/check_wording.py          # documentation wording lint
```

All reasoning runs **offline** — BFO 2020 is vendored at `alignments/vendor/bfo-2020-core.owl`. The full
gate specification is in `tests/reasoner-release-gates.md`. `FORMAL_VERIFICATION_REPORT.md` and
`SHA256SUMS.txt` record the frozen v1.0.0 verification and integrity state; current `main` adds the
post-release hardening described above.

## Repository layout

```
ontology/          OWL 2 DL ontology
shapes/            SHACL Graph Shape Validation Profile
alignments/        BFO 2020 bridge + vendored pinned BFO
tests/             OWL, SHACL, and cross-layer adversarial fixtures + gate specification
competency-queries/ 7 executable SPARQL queries
competency-questions.md   all 22 natural-language competency questions
examples/          worked example graphs
scripts/           HermiT/pySHACL runners, reference classifier, wording lint
docs/              review record and architecture figure
profiles/v1.1/     optional Strict Linear and Strict Assessment v1.1.0 package
FORMAL_VERIFICATION_REPORT.md   separate‑toolchain formal verification report
DESIGN_RATIONALE.md             design rationale
```

## Citing

Please cite the archived artefact (see `CITATION.cff`):

> Abak, A. T. (2026). *Resonatus Ontology: OWL 2 DL Model, SHACL Validation Profile, Optional Strict
> Profiles, and Verification Artefacts* (Version 1.1.0) [Software]. Zenodo.
> https://doi.org/10.5281/zenodo.21939902

## Methodological limits & Future Work

- OWL class entailment is not empirical causal discovery; SHACL conformance is not ontological truth;
  missing measurement is not failure.
- The BFO bridge is optional; the core does not require an upper ontology.
- Executable competency-query coverage is currently **7/22**. `7/7` means only that every query that
  currently exists passed; it is not a claim of full competency-question coverage. See
  [`competency-questions.md`](competency-questions.md).
- **Future Work:** a paired‑state real‑system intervention and independent external reuse are not
  established here; broader executable coverage, branch/merge identity, and independent evaluation
  of the five constitutive criteria remain open.

## Licence

Split licence — **CC BY 4.0** for ontology/documentation/examples/shapes and **Apache‑2.0** for the
validation code. Full texts and the per‑path mapping are in `LICENSE.md`, `LICENSE-CC-BY-4.0.txt`, and
`LICENSE-APACHE-2.0.txt`. These apply only to this repository.
