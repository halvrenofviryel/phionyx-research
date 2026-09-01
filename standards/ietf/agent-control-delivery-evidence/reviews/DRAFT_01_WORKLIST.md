# `-01` worklist

**This is not the `-01` draft.** It is a working checklist. No `-01` text exists
in this work area, no review freeze has been declared, and review is ongoing.
Items move only when the public record supports the move — see
`REVIEW_LEDGER.md` for the evidence behind each line.

Nothing below is normative text, and nothing below is a decision to adopt a
particular vocabulary.

---

## A. Normative / model changes already accepted in public discussion

Each item here has a public author response accepting it. See the ledger entry
for the quotation.

- [ ] **A1 — Instruction × required-target obligation as the reconciliation unit**
      when one instruction has multiple required enforcement targets. *(I-1, I-2)*
- [ ] **A2 — Closed required-target set.** An instruction resolving to multiple
      required enforcement targets binds a closed required-target set, or a
      verifiable reference that resolves to such a set under the declared
      profile. *(I-2)*
- [ ] **A3 — Parent fully confirmed only when all required target obligations
      confirm.** The parent instruction may be reported as fully confirmed only
      if every required instruction-target obligation is `CONFIRMED`. *(I-2, W-3)*
- [ ] **A4 — An open / unresolved / non-closed required-target population cannot
      support a complete-delivery or `PASS` claim.** *(I-2)*
- [ ] **A5 — Exact receiver identity + target boundary binding.** A receiver
      observation satisfies only the target identity and boundary to which it is
      verifiably bound; the right instruction at the wrong enforcement point
      does not confirm delivery. Tighten R-CD-4 and R-CD-5. *(I-3)*
- [ ] **A6 — Obligation-level conservation when target multiplicity exists.**
      Conserve target obligations separately from parent instructions, so
      instruction-level population conservation cannot hide an uncovered path.
      *(I-2)*
- [ ] **A7 — Freeze / in-flight non-retroactivity.** `APPLIED` for a control must
      not retroactively relabel an operation already consumed or in flight
      before the control took effect, and must not establish that an external
      effect already produced by that operation was reversed. *(I-4)*
- [ ] **A8 — Target-set declaration vs independently established path
      completeness.** A required-target population declared closed for
      reconciliation is not itself proof that every possible deployment
      enforcement path has been enumerated. `-00` §9.3 already states the limit;
      the author's public response says `-00` "does not currently represent
      [the distinction] strongly enough". *(I-5)*

## B. Clarifications suggested by review

Candidates. No public acceptance, or acceptance only of the *distinction* and
not of any particular wording.

- [ ] **B1 — Many-to-one diagnostic reduction reviewability.** Where a profile's
      native output is many-to-one against instructions, any
      reduction/precedence rule should be **deterministic and reviewable**, and
      non-selected diagnostics should remain visible. §6.2 already requires this
      for selection among duplicate or superseding *records*; the object here is
      layered diagnostics of a single record, which is different.
      **Do not adopt Cedulon's precedence ordering as a generic rule and do not
      write normative text for it.** *(E-4 — no public author response yet)*
- [ ] **B2 — Composition wording for SCITT.** Possible clarifying wording that
      the evidence-stage semantics stay format-neutral and compose with existing
      SCITT Signed Statements and profile bindings rather than introducing
      another receipt format. *(W-1)*
- [ ] **B3 — Reference check before any reference edit.** Any change to the
      SCITT reference must be verified against RFC metadata, not against
      reviewer prose. `-00` cites **RFC 9943**; a review message referred to
      **RFC 9942** (COSE Receipts), which is a different document. *(W-4)*

## C. Conformance / test-vector changes

- [ ] **C1 — Freeze-race conformance case** binding control epoch, closed target
      population, effect predicate, and observation window; covering that
      `CONFIRMED`/`APPLIED` at one required target does not prove complete
      delivery, global enforcement, or reversal of an operation that crossed
      before the control applied. *(I-4)*
- [ ] **C2 — Per-target obligation cases** for the closed required-target model:
      one obligation `CONFIRMED`, another `UNCONFIRMED`, parent not fully
      confirmed and unable to support `PASS`. *(I-2)*
- [ ] **C3 — Declared-closed vs enumeration-proven case**, keeping
      "closed for this reconciliation" and "enumeration independently proven"
      as separate facts. *(I-5)*
- [ ] **C4 — Provenance-safe handling of the contributed fixture.** If the
      contributed case or its structure is used **unchanged**, keep its fixture
      ID and SHA-256. If **adapted**, assign a new fixture ID, record the source
      fixture ID and digest as provenance, and credit EMILIA Protocol. The
      original contributed fixture stays pinned to AEB `-04`. *(I-6; see
      `../RIGHTS_AND_PROVENANCE.md` §4)*
- [ ] **C5 — Do not flatten the contributed fixture** into a simpler native case
      before testing `-01` against every boundary it contains. *(I-5)*

## D. Related-work / composition changes

- [ ] **D1 — Contestability composition seam.** Compare
      `draft-pinto-agent-authz-contestability-00` §6.3 and its verification
      model in full; make the relationship explicit **only if the comparison
      holds**, and introduce no control-delivery state that restates an
      effect-state distinction that draft already defines. *(T-1)*
- [ ] **D2 — Cedulon composition seam.** Possible §13 sentence referencing the
      opposite-direction adjacent-domain seam, worded so it cannot be read as
      Cedulon implementing this draft. *(E-1)*
- [ ] **D3 — EMILIA composition anchors.** `draft-schrock-ep-revocation-statement`
      and `draft-schrock-ep-outcome-binding` as composition anchors rather than
      dependencies; AEB is now published at `-05` while the contributed fixture
      stays pinned to `-04`. *(I-6, and `-00` §13 which currently cites AEB `-04`)*

## E. External implementation / evaluation evidence

- [ ] **E1 — Cedulon accounting result as external validation of existing `-00`
      rules.** Applying the bounded-population and class-accounting rules to a
      shipped adjacent-domain reconciler exposed a real reporting defect **in
      that reconciler**. Cite as evidence the existing rules catch a real
      adjacent-domain defect — **not** as an implementation of this draft, and
      **not** as a defect in `-00`. Pinned artifact and verified digest recorded
      in `../external-evidence/CEDULON_POPULATION_PROBE.md`. *(E-2, E-5)*
- [ ] **E2 — Section 12 hygiene.** §12 is Implementation Status and is marked for
      removal before RFC publication. The Cedulon probe's five measured rows
      follow the Minimum Conformance Cases appendix, **not** §12, and must not be
      presented as §12 implementation evidence. *(E-7)*
- [ ] **E3 — Acknowledgements.** `-00` §15 says specific names and review
      contributions will be added with permission in a later revision. Reviewers
      on the public record: Iman Schrock, Tiago Pinto, Walter Hawkins, Emek Can
      Dogru. Permission is required before naming anyone.

## F. Still-open design questions

- [ ] **F1 — Structural result vs claim/evidence qualification.** Whether, and
      how, to keep the structural reconciliation result separate from an
      orthogonal claim/evidence qualification. The author has publicly said the
      distinction is important **and that he does not want to freeze the
      vocabulary yet**. **No enum is adopted here.** In particular, do **not**
      invent `FULLY_SUPPORTED` / `CONDITIONALLY_SUPPORTED` / `NOT_SUPPORTED`
      unless a later design decision explicitly adopts them. *(E-3)*
- [ ] **F2 — Aborted / refused-operation classification.** How an issuer-side
      positive non-occurrence relates to `EXPLICIT_FAILURE`, whose §6.1 scope is
      a positive, attributable failure observation for an identified attempt and
      boundary. The reviewer explicitly declined to claim it is
      `EXPLICIT_FAILURE`; this work area does not decide it on his behalf.
      Unresolved. *(E-6)*
- [ ] **F3 — Expressing a "verifiable reference that resolves to a closed target
      set"** format-neutrally, without importing a resolution mechanism. *(I-2)*
- [ ] **F4 — What counts as *verifiably bound*** target identity when the target
      is carried through a broker, gateway, sidecar, or OS channel. *(I-3)*
- [ ] **F5 — Boundary with adjacent action-evidence work** for the consequential
      effect of an operation that crossed before a freeze applied. The author
      wants the execution and consequential-effect semantics left to that work.
      *(I-4)*
- [ ] **F6 — Interaction between §6.3 conservation and obligation-level
      conservation** once obligations and instructions are counted separately.
      *(A6)*

---

## Explicit non-goals for `-01`

- Do **not** define a receipt format, wire protocol, signature scheme,
  transparency service, policy language, or audit regime. `-00`'s abstract and
  §1.1 already exclude these.
- Do **not** adopt Cedulon's finding-code precedence ordering as a generic
  standard rule, and do **not** write normative text for it.
- Do **not** invent `FULLY_SUPPORTED` / `CONDITIONALLY_SUPPORTED` /
  `NOT_SUPPORTED` (or any equivalent enum) unless a later, explicit design
  decision adopts them.
- Do **not** classify the Cedulon aborted/refused receipt as `EXPLICIT_FAILURE`.
- Do **not** restate contestability effect states already defined by
  `draft-pinto-agent-authz-contestability`.
- Do **not** describe any third-party project as an implementation of this
  draft.
- Do **not** claim IETF WG adoption or IETF consensus. The document is an
  individual submission.
