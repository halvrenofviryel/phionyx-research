# Changelog: draft-abak-agent-control-delivery-evidence-00 → -01

**Document:** *Evidence Requirements for Agent Control Delivery and Outcome Reconciliation*  
**Author:** Ali Toygar Abak  
**Change interval:** `draft-abak-agent-control-delivery-evidence-00` → `draft-abak-agent-control-delivery-evidence-01`  
**Prepared:** 3 September 2026

> **Status of this file:** This is an explanatory, non-normative changelog. It describes the substantive differences between the published `-00` and the current `-01` candidate. If this file and the RFCXML differ, the RFCXML controls.

## 1. Baselines compared

| Item | `-00` | `-01` candidate |
|---|---|---|
| Document date | 30 August 2026 | 3 September 2026 |
| Model | Primarily one instruction ↔ one intended enforcement point | One instruction ↔ one or more required enforcement targets |
| Reconciliation unit | Instruction | Instruction-target **Delivery Obligation** |
| Normative requirements | R-CD-1 through R-CD-14 | R-CD-1 through R-CD-16 |
| Minimum conformance cases | 16 | 26 |
| Published/source status | Published individual Internet-Draft | Current candidate; not yet represented by this changelog as an IETF or WG consensus document |
| `-00` XML SHA-256 | `8ed78f9428ee9a9f0d13526fee04055fef8d16809996ac2932c7907cdfc4d3da` | — |
| `-01` candidate XML SHA-256 | — | `da64a03846e03f3868aa2fa54682c87d338a4dedcbc1dc4b5642cdfea79a81c6` |

The central architectural change is that `-00` treated a control instruction as the primary reconciliation object. `-01` makes the **instruction-target obligation** the load-bearing unit whenever a control must reach more than one enforcement target. This prevents evidence from one target from being generalized to another target or to the parent instruction as a whole.

---

## 2. Executive summary of substantive changes

| ID | Change | Why it was needed |
|---|---|---|
| C-01 | Added **Required Target Set** and **Delivery Obligation** concepts | A single receiver observation must not satisfy a multi-target parent instruction |
| C-02 | Added target-set closure vs deployment-coverage qualification | A set can be closed for repeatable accounting without proving that every relevant enforcement path was enumerated |
| C-03 | Added parent-instruction aggregation rules | Parent success must be universal over required targets, not existential on one successful target |
| C-04 | Replaced instruction-level population conservation with obligation-level conservation | Instruction counts can hide an uncovered target |
| C-05 | Split structural reconciliation from **Claim Support** | `PASS` over a declared population is not automatically a fully supported end-to-end claim |
| C-06 | Added freeze/revocation non-retroactivity | A later control must not rewrite the history of an already admitted or in-flight operation |
| C-07 | Added **R-CD-16: Semantic Preservation Across Intermediaries** | Syntax or identifiers can survive an intermediary while source distinctions are silently collapsed |
| C-08 | Added deterministic/reviewable many-to-one diagnostic reduction guidance | A profile may need one primary disposition without erasing non-selected diagnostics |
| C-09 | Expanded protocol attachment-point guidance and AgentProto composition | Protocols can preserve evidence-relevant facts without defining an audit or receipt format |
| C-10 | Clarified SCITT composition | Existing SCITT Signed Statements/profile bindings can carry the facts; no new SCITT receipt format is required |
| C-11 | Reworked implementation/evaluation status and claim boundaries | Author-side probes, contributed fixtures, adjacent-domain probes, and cross-version AIREP evidence must not be merged into a stronger claim |
| C-12 | Expanded adjacent-work composition | Added explicit seams for AgentProto preservation, revocation, outcome binding, contestability, and Cedulon |
| C-13 | Expanded conformance corpus from 16 to 26 minimum cases | New target, coverage, claim-support, race, and intermediary failure modes need direct tests |
| C-14 | Expanded security and privacy discussion for target-set manipulation and intermediary semantic loss | A structurally valid subset or transformed message can still support an over-broad claim |
| C-15 | Updated examples and appendices | Examples now exercise multi-target, partial delivery, claim qualification, and fixture provenance |

---

## 3. Detailed changes

### C-01 — Multi-target control delivery is now first-class

**`-00`:** The model spoke primarily about “the intended enforcement point.” Delivery dispositions were assigned per instruction.

**`-01`:** Introduces:

- **Required Target Set** — the reproducible set of enforcement targets required under the declared reconciliation profile.
- **Delivery Obligation** — the tuple of a control instruction/delivery attempt and one member of its Required Target Set.
- A receiver observation for target A can satisfy only target A's Delivery Obligation.
- A matching parent instruction identifier or digest is not enough to transfer evidence from target A to target B.

**Rationale:** Public SCITT review identified the existential-aggregation failure: if one control must reach multiple enforcement points, one successful observation cannot establish delivery to the parent instruction as a whole.

**Principal affected areas:** Terminology; Problem Statement; Logical Evidence Model; R-CD-4; R-CD-5; R-CD-10; R-CD-11; R-CD-14; Reconciliation Model; Multiple Enforcement Paths; appendices.

---

### C-02 — Structural target-set closure is separated from complete-mediation coverage

**`-00`:** A bounded/closed population was necessary for completeness, but the distinction between “closed for this reconciliation” and “complete enumeration of every relevant enforcement path” was not represented strongly enough.

**`-01`:** Adds **R-CD-15: Target-Set Closure and Coverage Qualification** with three conceptual coverage conditions:

- `VERIFIED`
- `DECLARED_ONLY`
- `INDETERMINATE`

A `DECLARED_ONLY` target set can support deterministic structural reconciliation over its named members, but it cannot by itself support a fully qualified claim that every relevant enforcement path in the deployment was covered.

**Rationale:** A producer can provide a perfectly closed but deceptively small target set. Conservation over that set proves accounting over the set; it does not prove that no omitted path exists.

---

### C-03 — Parent instruction confirmation now requires every required target

**`-00`:** No explicit parent aggregation rule was required because the reconciliation model was per instruction.

**`-01`:** Adds a dedicated **Parent Instruction Aggregation** rule:

- a parent is fully confirmed within its Required Target Set only if **every** Delivery Obligation is `CONFIRMED`;
- any `EXPLICIT_FAILURE`, `UNCONFIRMED`, `SUBSTITUTION`, `CONFLICT`, `INVALID`, or `INDETERMINATE` obligation prevents a fully confirmed parent result;
- the result remains scoped to the identified target set.

**Rationale:** Parent delivery must be derived from the complete required-target population rather than from the existence of any successful receiver record.

---

### C-04 — Population conservation is now obligation-level

**`-00`:**

```text
|I| = Nconfirmed + Nexplicit_failure + Nunconfirmed
    + Nsubstitution + Nconflict + Ninvalid + Nindeterminate
```

where `I` was the bounded set of expected issuer instructions.

**`-01`:** Defines, for each instruction `i`, its Required Target Set `T_i`, and constructs:

```text
O = { (i,t) : i in I and t in T_i }
```

The primary conservation equation becomes:

```text
|O| = Nconfirmed + Nexplicit_failure + Nunconfirmed
    + Nsubstitution + Nconflict + Ninvalid + Nindeterminate
```

Receiver-record conservation remains a separate equation.

`-01` also requires the expected obligation population to be constructed from issuer inclusion and target-resolution rules **before** present receiver evidence is used to decide what counts as expected.

**Rationale:** Otherwise a missing target or suppressed failed path can disappear from the population before reconciliation starts.

---

### C-05 — Structural result and claim strength are now separate dimensions

**`-00`:** Defined aggregate `PASS`, `FAIL`, or `INCONCLUSIVE`, but did not provide a separate vocabulary for the evidentiary strength of the claim being made from that structural result.

**`-01`:**

1. Renames the concept to **Structural Reconciliation Result**.
2. Adds **Claim Support** as a separate dimension.
3. Defines conceptual meanings:
   - `FULLY_SUPPORTED`
   - `CONDITIONALLY_SUPPORTED`
   - `NOT_SUPPORTED`

A structural `PASS` can therefore coexist with `CONDITIONALLY_SUPPORTED` claim support, for example where all declared obligations reconcile but target-set coverage or another required trust predicate remains declared-only.

A structural `FAIL` can also have `FULLY_SUPPORTED` claim support when the scoped failure itself is strongly evidenced.

**Rationale:** Structural balance and evidentiary strength answer different questions. Collapsing them permits a bounded, internally consistent subset to be promoted into an unqualified end-to-end claim.

**Principal affected areas:** Terminology; R-CD-3; R-CD-13; Structural Aggregate Results; new Claim-Support Qualification section; conformance cases.

---

### C-06 — Controls are explicitly non-retroactive with respect to prior operations

**`-00`:** Distinguished control enforcement from control effect, but did not explicitly define how a later freeze/revocation relates to an operation already admitted or in flight.

**`-01`:** Adds **Control Activation and In-Flight Operations** rules:

- `APPLIED` does not retroactively relabel an operation that crossed the relevant admission/provider-entry boundary before control activation;
- the earlier operation's outcome remains a separate lifecycle fact;
- a later observation that a subsequent operation was blocked does not prove that the earlier operation produced no external effect;
- reversal, compensation, or remedy requires its own evidence.

**Rationale:** A control changes behavior from its effective boundary onward; it does not rewrite historical ordering or prove reversal of a prior external effect.

---

### C-07 — New R-CD-16: Semantic Preservation Across Intermediaries

**New in `-01`.**

Where a gateway, broker, adapter, or other intermediary transforms a governance-relevant state, a relying party must be able to determine whether the source distinction survived.

A profile must either:

- define a **lossless mapping** for every governance-relevant state used by the claim; or
- expose that the mapping is incomplete, ambiguous, or unavailable.

The intermediary must not silently collapse distinct applicable states such as `deny`, `defer`, `reject`, `timeout`, `unresolved`, or `indeterminate` into a representation that can be consumed as a stronger or different state.

If lossless preservation cannot be established, the resulting state remains explicitly qualified or `INDETERMINATE`.

**Rationale:** Preserving an identifier or a signed transformed record is not enough if the transformation erased the source semantics. Cryptographic integrity cannot restore a distinction that was already lost before signing or registration.

**Origin of the refinement:** Relevant AgentProto preservation discussion sharpened the boundary between:
- preserving the facts/distinctions a downstream verifier needs; and
- standardizing an audit format or audit conclusion.

`-01` adopts the former without claiming mailing-list discussion as WG consensus.

---

### C-08 — Many-to-one diagnostic reduction must remain deterministic and reviewable

**`-00`:** Required profile-specific conflict selection among duplicate or superseding records to remain reviewable.

**`-01`:** Extends this discipline to layered observations/diagnostics:

- when several applicable observations or diagnostics are reduced to one primary per-obligation disposition, the reduction rule should be deterministic and reviewable;
- non-selected inputs remain visible under total accounting/reviewability rules;
- the document deliberately **does not define a universal precedence ordering** for profile-specific diagnostics.

**Rationale:** A profile may need a primary outcome, but selecting one diagnostic must not erase the evidence that other applicable diagnostics existed.

---

### C-09 — Protocol attachment points now cover target sets, attempts, and path preservation

`-01` expands the protocol-facing preservation guidance to include, where applicable:

- stable delivery-attempt references;
- target identity or a Required Target Set / target-resolution reference;
- target-bound enforcement-point receipt;
- source attribution and preservation through intermediaries;
- explicit handling of stale, missing, ambiguous, or inconsistent external references.

The document continues to permit these facts to be carried as native fields, structured errors, acknowledgements, events, or references.

**Rationale:** The draft specifies what facts must survive a boundary, not how an audit system must package them.

---

### C-10 — SCITT composition is more explicit, without a new receipt format

**`-00`:** Already treated the document as format-neutral and compatible with SCITT.

**`-01`:** Makes the composition rule explicit:

- control observations, target-set bindings, or reconciliation reports can be carried as or referenced by SCITT Signed Statements;
- a SCITT receipt proves the registration properties defined by the applicable transparency service;
- SCITT registration alone does **not** prove delivery, enforcement, observation truth, target-set completeness, or control effect;
- **no new SCITT receipt format is required by this draft**.

**Rationale:** Separate statement semantics from transparency-registration semantics and avoid duplicating SCITT's carrier/receipt mechanisms.

---

### C-11 — Implementation Status is rewritten around evidence classes and non-claims

**`-00`:** The implementation-status section primarily described AIREP v0.1 and v0.2 prerelease artifacts.

**`-01`:** Separates several evidence classes and refuses to merge them into a stronger result:

1. **AIREP author-side control-delivery implementation input**
   - current public snapshot is referenced;
   - its control-delivery model is useful implementation input, not the conformance authority for this draft.

2. **AIREP external evidence**
   - the external producer result targets frozen AIREP v0.1.2;
   - the independent consumer/verifier result targets a frozen AIREP v0.2 corpus;
   - because the versions differ, they are explicitly **non-additive** and are not presented as producer↔consumer interoperability for one AIREP version.

3. **phionyx-research author-side runtime probe**
   - issuer and enforcement observations are placed on opposite filesystem trust sides;
   - identity and instruction hash are correlated;
   - the enforcement-side record explicitly declares that it is writable by the controlled system and is therefore corroboration, not proof;
   - an issued-but-unacknowledged instruction remains **unaccounted for**, not proven undelivered, because delivery failure, evidence-recording failure, and a never-demanded override are not yet distinguishable.

4. **Historical ACDER probe**
   - retained as a pinned author-side research artifact;
   - exercises an earlier instruction-target obligation model;
   - does not implement the complete `-01` claim-support or intermediary-preservation model.

5. **EMILIA Protocol fixture**
   - retained as contributed test input, not an implementation.

6. **Cedulon population probe**
   - retained as adjacent-domain evaluation evidence, not an implementation of this draft.

**Rationale:** Evidence classes have different provenance and scope. Combining them would create a stronger claim than any single artifact establishes.

---

### C-12 — Adjacent work is expanded and more sharply scoped

`-01` adds or expands explicit composition seams for:

- AgentProto preservation discussions;
- Portable Revocation Statements;
- Outcome Binding;
- Contestability Bindings;
- Cedulon;
- current Action Evidence Boundary work.

The broader audit-architecture reference carried by `-00` is no longer used as a central relationship paragraph; `-01` concentrates on narrower protocol/evidence boundaries that directly constrain the draft's semantics.

**Rationale:** The draft should define the control-delivery gap without restating adjacent authorization, consequential-action, contestability, revocation, audit, or payment semantics.

---

### C-13 — Minimum conformance cases expand from 16 to 26

The original `-00` cases remain conceptually represented, but the vocabulary is updated from instructions to obligations where required.

New `-01` cases directly exercise:

1. two required targets with one `CONFIRMED` and one `UNCONFIRMED`;
2. a receiver observation for EP-A presented as evidence for EP-B;
3. both named targets confirmed while target-set coverage remains `DECLARED_ONLY`;
4. an open or unresolved Required Target Set;
5. structural pass with a permitted missing trust predicate → conditional claim support;
6. structural failure with strongly supported evidence → fully supported scoped failure claim;
7. freeze applied after O1 crossed provider entry and before O2;
8. fixture-closed target population without independently verified enumeration completeness;
9. intermediary mapping `DEFER` to generic `FAILURE` without a lossless mapping;
10. stable instruction identifier surviving an intermediary while the governed content changes.

**Rationale:** The new normative distinctions are not useful unless an implementation can be tested against the failure modes they were introduced to prevent.

---

### C-14 — Security and privacy considerations are extended

`-01` adds or strengthens discussion of:

- target omission and deceptively small closed target sets;
- binding valid target-A evidence to target B;
- target-resolution manipulation;
- control activation races;
- intermediary semantic degradation;
- increased topology/linkability exposure from explicit target-set accounting.

**Rationale:** Multi-target accounting creates new integrity and privacy surfaces. A closed set can be internally valid and still be incomplete for the relying party's stronger claim.

---

### C-15 — Examples and appendices now demonstrate the new model

**Illustrative record:**

`-00` used a single-target logical record set.

`-01` uses an **Illustrative Multi-Target Reconciliation Record**, including:

- a named Required Target Set;
- `structural_closure`;
- `coverage_qualification`;
- separate EP-A and EP-B results;
- parent-instruction aggregation;
- structural result;
- separate claim-support result.

**New contributed-fixture appendix:**

`-01` adds the EMILIA Protocol freeze-race fixture summary with:

- `fixture_id`: `freeze-after-provider-entry-with-multiple-required-targets`
- SHA-256: `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a`
- explicit target results;
- in-flight and post-freeze operation semantics;
- non-claims;
- provenance rules for unchanged vs adapted use.

**Rationale:** The appendices now show not only how to produce a positive result, but also how to preserve partial delivery, uncertainty, scope, and provenance.

---

## 4. Requirement-by-requirement delta

| Requirement | `-01` status | Main change from `-00` |
|---|---|---|
| **R-CD-1 Stable Instruction Identity** | Tightened | Adds explicit retry/delivery-attempt binding when retries create distinct attempts |
| **R-CD-2 Content Binding** | Substantively retained | Core digest/projection/canonicalization semantics remain |
| **R-CD-3 Boundary Attribution** | Tightened | Missing external trust/authority binding must be exposed through claim-support qualification; self-declared role/key cannot silently become fully supported attribution |
| **R-CD-4 Issuer-Side Emission** | Expanded | Adds target-set/reference/resolution binding and reconstructability at cutoff |
| **R-CD-5 Receiver-Side Observation** | Expanded | Adds required-target identity, receiving boundary, attempt binding, and target-specific satisfaction rule |
| **R-CD-6 Separate Enforcement Outcome** | Substantively retained | Receipt and enforcement remain distinct; missing enforcement still cannot default to `APPLIED` |
| **R-CD-7 Separate Control-Effect Observation** | Substantively retained/clarified | Effect remains separate and bounded; target scope is more explicit |
| **R-CD-8 Negative Observations** | Substantively retained | Silence remains non-evidence; bounded positive negative-observation semantics remain |
| **R-CD-9 Time and Ordering** | Substantively retained | Correspondence still does not establish precedence without an ordering basis |
| **R-CD-10 Total Reconciliation** | Major expansion | Reconciliation is per Delivery Obligation; expected population is built before receiver evidence; diagnostic reduction must remain deterministic/reviewable |
| **R-CD-11 Bounded-Population Accounting** | Major expansion | Counts obligations rather than only instructions; requires target-set resolution; separates closed population from complete mediation |
| **R-CD-12 Resolution Failure** | Expanded | External references now explicitly include target and target-set bindings |
| **R-CD-13 Scope, Qualification, and Non-Claims** | Major expansion / renamed | Adds explicit claim scope and Claim Support; structural `PASS` cannot be consumed as unqualified end-to-end success |
| **R-CD-14 Consumption and Fail-Safe Handling** | Updated | Applies to unresolved/unacknowledged **Delivery Obligations**, not only parent instructions |
| **R-CD-15 Target-Set Closure and Coverage Qualification** | **New** | Separates structural closure from evidence of enumeration completeness |
| **R-CD-16 Semantic Preservation Across Intermediaries** | **New** | Requires lossless governance-state mapping or explicit uncertainty across intermediaries |

---

## 5. Important invariants that did not change

Despite the expansion, the following design boundaries remain intact from `-00`:

- The document remains **Informational**.
- It remains **format-independent**.
- It does **not** define a new receipt, token, wire protocol, authorization system, policy language, transparency service, or audit regime.
- Decision, dispatch, receipt, enforcement, and observed control effect remain distinct facts.
- Missing evidence is not silently converted into failure or success.
- A bare absence of acknowledgement is not proof of non-delivery.
- Signatures and transparency receipts prove only their native verified properties; they do not establish the truth of the underlying event assertion by themselves.
- The document still does not prove policy correctness, legal correctness, complete mediation, or physical-world effect.
- No IANA action is introduced.
- Nothing in `-01` is represented here as IETF, SCITT, or AgentProto working-group consensus.

---

## 6. Review/evidence provenance behind the main changes

| Source | Contribution to `-01` |
|---|---|
| **Iman Schrock / EMILIA Protocol** | Multi-target obligation model; parent aggregation; freeze/in-flight race; contributed fixture; fixture provenance; closed-for-fixture vs enumeration-complete distinction |
| **Emek Can Doğru / Cedulon** | Bounded-population discipline; favorable-subset hazard; structural result vs claim-strength separation; adjacent-domain population probe; diagnostic-reduction reviewability question |
| **Tiago Pinto** | Contestability composition seam; avoid duplicating effect-state semantics |
| **Walter Hawkins** | SCITT Signed Statements/profile bindings as natural carriers; no need for a new receipt format |
| **AgentProto discussion** | Preservation boundary: protocol transitions should retain identifiers, bindings, source-attributable outcomes, and non-success distinctions without turning the protocol into an audit format |
| **AIREP / phionyx-research** | Author-side evidence for delivery-vs-emission separation, opposite-side observations, trust/write-path qualification, total reconciliation, and the non-inference from “no acknowledgement” to proven non-delivery |
| **AIREP external evidence** | Strengthened claim hygiene: producer-side and consumer/verifier-side results on different frozen versions are separate evidence classes and are not additive |

---

## 7. Reviewer-facing interpretation

The `-01` revision should be read as a change from:

> **“Can we distinguish that a control was issued, received, enforced, and observed?”**

to the stronger but still format-neutral question:

> **“For every enforcement target the declared profile required, can we account for the corresponding delivery obligation, preserve uncertainty and source semantics across the path, and state exactly how strongly the resulting scoped claim is supported?”**

That is the principal semantic difference between `-00` and `-01`.

---

## 8. Source identities used for this changelog

- Published `-00` source:
  - `draft-abak-agent-control-delivery-evidence-00`
  - document date: 30 August 2026
  - XML SHA-256: `8ed78f9428ee9a9f0d13526fee04055fef8d16809996ac2932c7907cdfc4d3da`
  - archived work-area copy:  
    `https://github.com/halvrenofviryel/phionyx-research/tree/main/standards/ietf/agent-control-delivery-evidence/draft/published/00`

- Current `-01` candidate:
  - `draft-abak-agent-control-delivery-evidence-01`
  - document date: 3 September 2026
  - XML SHA-256: `da64a03846e03f3868aa2fa54682c87d338a4dedcbc1dc4b5642cdfea79a81c6`

- Current implementation/evaluation pins referenced by `-01` include:
  - AIREP snapshot: `a3973ce3b6ad984635867a2bb52d83c472e5c0cb`
  - phionyx-research control-delivery source: `706e40748be18e988d4efd1e307787e009161c6a`
  - historical ACDER probe: `449f4fb6a07fd54b45a6e68208dece109446ef93`
  - EMILIA contributed fixture SHA-256: `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a`
  - Cedulon population-probe pin: `0a3fa04`

