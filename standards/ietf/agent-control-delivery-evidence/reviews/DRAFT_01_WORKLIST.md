# `-01` worklist

## Status of this worklist

**This file is not the `-01` draft text.** It is a traceability and review
record.

- **A repository candidate `-01` now exists.** It is stored at
  `../draft/candidate/01/` and dated 3 September 2026. This worklist is
  reconciled against that candidate's actual text.
- **The candidate is not an IETF-submitted revision.** It has not been posted to
  the Datatracker. The published baseline of this document remains `-00`.
- **The worklist remains a traceability/review record**, not a specification and
  not a changelog. `../draft/candidate/01/CHANGELOG.md` is the author's own
  account of what changed; this file records whether each tracked review item is
  actually reflected in the candidate text.
- **Implemented candidate text is not equivalent to WG consensus.** A ticked box
  below means only that the author's candidate contains text addressing the
  item. It does not mean a reviewer agreed with the resolution, that the item is
  closed on the public record, or that any working group has adopted anything.
- **Review is ongoing** and no review freeze has been declared.

## How to read the boxes

| Mark | Meaning |
|---|---|
| `[x]` | The `-01` candidate contains text implementing the item. **Author design decision.** |
| `[~]` | Partially addressed in the candidate, or deliberately deferred to profiles; the underlying question is not settled. |
| `[ ]` | Not implemented in the candidate, or still open. |

Each ticked item names the candidate section that implements it, so the claim is
checkable against the XML rather than taken on trust.

Three things stay distinct throughout, and a box never merges them:

1. **a public reviewer finding** — what a reviewer said, recorded in
   `REVIEW_LEDGER.md`;
2. **an author design decision in `-01`** — what the candidate text does about
   it, recorded here; and
3. **IETF/WG consensus** — which does not exist for any item in this file.

Where `-01` settles a question that the public record left open, that is
recorded below as an **author-candidate disposition**, explicitly and by name.

---

## A. Normative / model changes already accepted in public discussion

Each item here has a public author response accepting it. See the ledger entry
for the quotation. Every item in this section is implemented in the `-01`
candidate; the public acceptance is of the *finding*, while the *wording chosen*
in the candidate is the author's own.

- [x] **A1 — Instruction × required-target obligation as the reconciliation unit**
      when one instruction has multiple required enforcement targets. *(I-1, I-2)*
      → Implemented: candidate §"Required Target Set and Delivery Obligations"
      (`target-set-model`) makes each member of the Required Target Set create
      one Delivery Obligation; R-CD-10 requires "a deterministic disposition for
      every Delivery Obligation"; the reconciliation states are per-obligation
      (`reconciliation-states`).
- [x] **A2 — Closed required-target set.** An instruction resolving to multiple
      required enforcement targets binds a closed required-target set, or a
      verifiable reference that resolves to such a set under the declared
      profile. *(I-2)*
      → Implemented: `target-set-model` freezes the set, or a verifiable
      reference resolving to it, at the reconciliation cutoff *before* receiver
      evidence is used; R-CD-4 requires a stable binding to the Required Target
      Set "or to a verifiable resolution rule and inputs from which the same set
      can be reconstructed".
- [x] **A3 — Parent fully confirmed only when all required target obligations
      confirm.** The parent instruction may be reported as fully confirmed only
      if every required instruction-target obligation is `CONFIRMED`. *(I-2, W-3)*
      → Implemented: candidate §"Parent Instruction Aggregation"
      (`parent-aggregation`), which also requires the per-target dispositions
      used to derive the parent result to be retained, and scopes the parent
      result to the identified target set.
- [x] **A4 — An open / unresolved / non-closed required-target population cannot
      support a complete-delivery or `PASS` claim.** *(I-2)*
      → Implemented: R-CD-11 ("MUST NOT claim complete delivery for that
      instruction over an unspecified target population"; open-population results
      permitted only with an explicit open-population scope) and
      `global-results`, where PASS requires a closed obligation population and
      successful conservation. Conformance case 20 exercises it.
- [x] **A5 — Exact receiver identity + target boundary binding.** A receiver
      observation satisfies only the target identity and boundary to which it is
      verifiably bound; the right instruction at the wrong enforcement point
      does not confirm delivery. Tighten R-CD-4 and R-CD-5. *(I-3)*
      → Implemented: R-CD-5 — "An observation for target A MUST NOT be used to
      confirm target B merely because the parent instruction identifier and
      content digest match" — plus the required-target identity and receiving
      boundary in the mandatory observation fields. R-CD-4 carries the
      corresponding issuer-side target-set binding. Conformance case 18
      exercises it. See also **F4**, which remains only partly settled.
- [x] **A6 — Obligation-level conservation when target multiplicity exists.**
      Conserve target obligations separately from parent instructions, so
      instruction-level population conservation cannot hide an uncovered path.
      *(I-2)*
      → Implemented: candidate §"Population Conservation" defines
      `O = { (i,t) : i in I and t in T_i }` and requires `|O|` to equal the sum
      of the seven per-obligation disposition counts, with receiver-record
      accounting (`|R|`) kept as a separate equation. This resolves **F6**.
- [x] **A7 — Freeze / in-flight non-retroactivity.** `APPLIED` for a control must
      not retroactively relabel an operation already consumed or in flight
      before the control took effect, and must not establish that an external
      effect already produced by that operation was reversed. *(I-4)*
      → Implemented: candidate §"Control Activation and In-Flight Operations"
      (`control-activation`) — a reconciler "MUST NOT retroactively relabel an
      operation as blocked merely because a later control was APPLIED", and a
      later blocked-operation observation does not prove an earlier operation
      produced no external effect or that a prior effect was reversed.
      Consequential-effect semantics are left to the adjacent action-evidence
      work, consistent with **F5**.
- [x] **A8 — Target-set declaration vs independently established path
      completeness.** A required-target population declared closed for
      reconciliation is not itself proof that every possible deployment
      enforcement path has been enumerated. `-00` §9.3 already states the limit;
      the author's public response says `-00` "does not currently represent
      [the distinction] strongly enough". *(I-5)*
      → Implemented: R-CD-15 ("Target-Set Closure and Coverage Qualification")
      raises the distinction to a requirement with three conceptual conditions —
      `VERIFIED`, `DECLARED_ONLY`, `INDETERMINATE` — supported by R-CD-11
      ("Closing a target population for reconciliation is not equivalent to
      proving complete mediation") and `target-set-model`. Conformance cases 19
      and 24 exercise it. **Author-candidate disposition:** the three-way
      vocabulary is the author's choice; the public record accepted the
      distinction, not this enumeration.

## B. Clarifications suggested by review

Candidates. No public acceptance, or acceptance only of the *distinction* and
not of any particular wording.

- [x] **B1 — Many-to-one diagnostic reduction reviewability.** Where a profile's
      native output is many-to-one against instructions, any
      reduction/precedence rule should be **deterministic and reviewable**, and
      non-selected diagnostics should remain visible. §6.2 already requires this
      for selection among duplicate or superseding *records*; the object here is
      layered diagnostics of a single record, which is different.
      **Do not adopt Cedulon's precedence ordering as a generic rule and do not
      write normative text for it.** *(E-4 — no public author response yet)*
      → Implemented as a non-normative SHOULD: R-CD-10 final paragraph says a
      reduction rule "SHOULD be deterministic and reviewable", keeps non-selected
      inputs subject to the R-CD-11 accounting rules, and states that "this
      document does not prescribe a universal precedence ordering among
      profile-specific diagnostics". The constraint is honoured — Cedulon's
      ordering is **not** adopted. **Author-candidate disposition:** E-4 still has
      no public author response, so this is the author acting on a reviewer
      suggestion, not an agreed outcome.
- [x] **B2 — Composition wording for SCITT.** Possible clarifying wording that
      the evidence-stage semantics stay format-neutral and compose with existing
      SCITT Signed Statements and profile bindings rather than introducing
      another receipt format. *(W-1)*
      → Implemented: candidate §"SCITT Composition" (`scitt-composition`) states
      that the document "does not require a new SCITT receipt format", that
      existing Signed Statements and profile-specific payload bindings can carry
      or reference the facts, and that SCITT registration does not by itself
      prove delivery, enforcement, correct observation, or truth. **This records
      a composition property of the candidate text; it is not a SCITT WG
      position and implies no SCITT endorsement.**
- [x] **B3 — Reference check before any reference edit.** Any change to the
      SCITT reference must be verified against RFC metadata, not against
      reviewer prose. `-00` cites **RFC 9943**; a review message referred to
      **RFC 9942** (COSE Receipts), which is a different document. *(W-4)*
      → Constraint honoured: the candidate's normative references are RFC 2119,
      RFC 8174, and **RFC 9943** only. RFC 9942 was **not** imported on the
      strength of reviewer prose. W-4's open question — whether `-01` should
      *additionally* cite RFC 9942 where receipts specifically are meant — is
      left unanswered by the candidate and remains open in the ledger.

## C. Conformance / test-vector changes

The candidate's "Minimum Conformance Cases" appendix lists **26** cases, up from
sixteen in `-00`. Case numbers below refer to that appendix. Note that these are
cases a conforming profile *SHOULD publish test vectors for* — the candidate
does **not** ship a vector set, and this work area has published none.

- [x] **C1 — Freeze-race conformance case** binding control epoch, closed target
      population, effect predicate, and observation window; covering that
      `CONFIRMED`/`APPLIED` at one required target does not prove complete
      delivery, global enforcement, or reversal of an operation that crossed
      before the control applied. *(I-4)*
      → Implemented: conformance case 23 (freeze applied after O1 crossed
      provider entry and before O2 attempts entry), with the appendix
      "Contributed Freeze-Race Fixture Summary" carrying the same boundaries and
      their explicit non-claims.
- [x] **C2 — Per-target obligation cases** for the closed required-target model:
      one obligation `CONFIRMED`, another `UNCONFIRMED`, parent not fully
      confirmed and unable to support `PASS`. *(I-2)*
      → Implemented: conformance case 17 (EP-A `CONFIRMED`, EP-B `UNCONFIRMED`,
      parent not fully confirmed, no complete-delivery `PASS`) and case 18 (an
      EP-A-bound observation presented as evidence for EP-B does not confirm
      EP-B).
- [x] **C3 — Declared-closed vs enumeration-proven case**, keeping
      "closed for this reconciliation" and "enumeration independently proven"
      as separate facts. *(I-5)*
      → Implemented: conformance case 19 (both targets `CONFIRMED` while coverage
      is `DECLARED_ONLY`) and case 24 (set closed for the fixture without
      independently verified enumeration completeness).
- [x] **C4 — Provenance-safe handling of the contributed fixture.** If the
      contributed case or its structure is used **unchanged**, keep its fixture
      ID and SHA-256. If **adapted**, assign a new fixture ID, record the source
      fixture ID and digest as provenance, and credit EMILIA Protocol. The
      original contributed fixture stays pinned to AEB `-04`. *(I-6; see
      `../RIGHTS_AND_PROVENANCE.md` §4)*
      → Implemented: the candidate summarizes rather than copies the fixture, and
      preserves the `fixture_id`
      `freeze-after-provider-entry-with-multiple-required-targets` and the
      SHA-256 `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a`
      verbatim, credits Iman Schrock / EMILIA Protocol, restates the
      new-ID-plus-source-provenance rule for derivatives, and states that the
      fixture "remains pinned to the related-work revisions it named when
      contributed" while the document's own related-work citations advance (the
      candidate cites AEB **-05**). The stored fixture is untouched by this
      integration and no derivative exists.
- [x] **C5 — Do not flatten the contributed fixture** into a simpler native case
      before testing `-01` against every boundary it contains. *(I-5)*
      → Constraint honoured: the fixture appendix retains target multiplicity,
      the closed-set/enumeration-completeness split, the per-target expected
      results, the in-flight O1 case, the post-freeze O2 case, and all four
      stated non-claims. It is a summary with attribution, not a simplification.
      The contributed JSON itself remains stored unmodified under
      `../fixtures/contributed/`.

## D. Related-work / composition changes

- [x] **D1 — Contestability composition seam.** Compare
      `draft-pinto-agent-authz-contestability-00` §6.3 and its verification
      model in full; make the relationship explicit **only if the comparison
      holds**, and introduce no control-delivery state that restates an
      effect-state distinction that draft already defines. *(T-1)*
      → Implemented: the candidate's "Relationship to Adjacent Work" states that
      the shared discipline is avoiding the collapse of separately evidenced
      stages, and "therefore treats that effect-state model as a composition
      boundary rather than restating its states". The constraint against
      restatement is honoured. **The author's full re-read of §6.3 is not
      independently evidenced here** — T-1 remains `OPEN` in the ledger, and the
      reviewer's comment was itself scoped to a partial read.
- [x] **D2 — Cedulon composition seam.** Possible §13 sentence referencing the
      opposite-direction adjacent-domain seam, worded so it cannot be read as
      Cedulon implementing this draft. *(E-1)*
      → Implemented: the adjacent-work section describes the opposite direction
      of travel and the shared bounded-population / total-accounting /
      qualified-claim disciplines, and closes with the explicit non-claim that
      the document "does not describe Cedulon as an implementation of this
      document". **To verify before submission:** that paragraph cites Cedulon
      revision **-08**, while this work area's `../SOURCES.md` recorded `-06` as
      the published revision on 2026-09-01. The candidate's reference list also
      pins `draft-dogru-cedulon-08`. That revision number is the author's and
      has not been checked against the Datatracker by this integration.
- [x] **D3 — EMILIA composition anchors.** `draft-schrock-ep-revocation-statement`
      and `draft-schrock-ep-outcome-binding` as composition anchors rather than
      dependencies; AEB is now published at `-05` while the contributed fixture
      stays pinned to `-04`. *(I-6, and `-00` §13 which currently cites AEB `-04`)*
      → Implemented: the candidate cites
      `draft-schrock-action-evidence-boundary-05`,
      `draft-schrock-ep-revocation-statement-01`, and
      `draft-schrock-ep-outcome-binding-00`, and treats each as a composition
      boundary — explicitly not redefining the revocation statement format,
      atomic execution semantics, consequential-action outcome states, source
      quorum, or physical-effect reconciliation. The fixture's own pin is
      preserved separately, satisfying the split required by I-6.

## E. External implementation / evaluation evidence

- [x] **E1 — Cedulon accounting result as external validation of existing `-00`
      rules.** Applying the bounded-population and class-accounting rules to a
      shipped adjacent-domain reconciler exposed a real reporting defect **in
      that reconciler**. Cite as evidence the existing rules catch a real
      adjacent-domain defect — **not** as an implementation of this draft, and
      **not** as a defect in `-00`. Pinned artifact and verified digest recorded
      in `../external-evidence/CEDULON_POPULATION_PROBE.md`. *(E-2, E-5)*
      → Implemented: the candidate's Implementation Status section says the probe
      "exposed a reporting-scope defect in the adjacent implementation rather
      than a defect in this document" and that "Cedulon remains adjacent-domain
      evaluation evidence, not an implementation of this document". The evidence
      classes stay separate.
- [~] **E2 — Section 12 hygiene.** §12 is Implementation Status and is marked for
      removal before RFC publication. The Cedulon probe's five measured rows
      follow the Minimum Conformance Cases appendix, **not** §12, and must not be
      presented as §12 implementation evidence. *(E-7)*
      → Addressed by explicit disclaimer rather than by exclusion. The candidate
      keeps `removeInRFC="true"` on Implementation Status, opens that section
      with "Adjacent interoperability results that do not implement this document
      are not promoted into implementation claims", and labels the Cedulon probe
      as adjacent-domain evaluation evidence. It also separates the AIREP
      v0.1.2 external-producer result from the v0.2 external consumer/verifier
      result as "explicitly non-additive", so no single-version
      producer↔consumer interoperability claim is made.
      **Author-candidate disposition:** the probe is nonetheless *described
      within* the Implementation Status section rather than kept out of it. The
      stricter reading of E-7 — keep it out of §12 entirely — was not taken. The
      disclaimers are explicit, so the risk is presentational, not a false
      claim.
- [~] **E3 — Acknowledgements.** `-00` §15 says specific names and review
      contributions will be added with permission in a later revision. Reviewers
      on the public record: Iman Schrock, Tiago Pinto, Walter Hawkins, Emek Can
      Dogru. Permission is required before naming anyone.
      → Partially exercised. The candidate names **Iman Schrock of EMILIA
      Protocol** only, for the contributed fixture — which rests on the
      contributor's own public request that "the fixture ID and EMILIA Protocol
      attribution be preserved" (ledger I-6). The other three reviewers are
      **not** named; they are thanked collectively as "SCITT participants who
      provided public review", and the candidate retains "Specific additional
      names can be added with permission in a later revision" plus the explicit
      non-claim that "these acknowledgements do not imply endorsement of this
      document".
      **To confirm before submission:** whether the contributor's attribution
      request is intended to extend to being named personally in the
      Acknowledgements section, as distinct from fixture attribution. No public
      message in `../SOURCES.md` records permission in those terms.

## F. Still-open design questions

Some of these are no longer open *in the candidate text*, because the author
made a design choice. That is recorded here as an **author-candidate
disposition**. It does not mean the underlying question was settled on the
public record, and in the case of **F1** the candidate goes further than the
author's own public statement did.

- [x] **F1 — Structural result vs claim/evidence qualification.** Whether, and
      how, to keep the structural reconciliation result separate from an
      orthogonal claim/evidence qualification. *(E-3)*
      → **Resolved in the candidate as an author design decision, and this is the
      one item where the candidate moves ahead of the public record.**
      The candidate separates the two dimensions structurally: §"Structural
      Aggregate Results" (`global-results`) covers `PASS` / `FAIL` /
      `INCONCLUSIVE`, and a separate §"Claim-Support Qualification"
      (`claim-qualification`) defines the conceptual meanings
      **`FULLY_SUPPORTED`**, **`CONDITIONALLY_SUPPORTED`**, and
      **`NOT_SUPPORTED`**, with a required lossless mapping for profiles using
      other vocabulary. R-CD-3, R-CD-13, and R-CD-15 refer to it, and conformance
      cases 21 and 22 exercise it.
      **What the public record actually supports:** in E-3 the author agreed the
      *distinction* is important and said, in terms, "**I do not want to freeze
      the vocabulary yet** — I want to compare your -06/-07 treatment and the
      other review comments first". This worklist previously recorded, on the
      strength of that statement, an instruction not to invent these three names
      "unless a later design decision explicitly adopts them".
      **The candidate is that later design decision, and it adopts exactly those
      three names.** It is therefore an author-candidate disposition that is
      *ahead of* the author's last public position, not an implementation of an
      agreed outcome. E-3 remains `OPEN / NEEDS DESIGN` in `REVIEW_LEDGER.md`;
      the reviewer has not responded to this resolution, and nothing here is
      reviewer agreement or consensus. **Flagged for the author to confirm
      deliberately before `-01` is submitted to the Datatracker.**
- [ ] **F2 — Aborted / refused-operation classification.** *(still open — the
      candidate does not decide it.)* Whether an
      issuer-side aborted receipt satisfies the `EXPLICIT_FAILURE` requirements
      is unresolved. §6.1 requires a positive, attributable failure observation
      scoped to an identified attempt and boundary; it does not itself restrict
      `EXPLICIT_FAILURE` to receiver-side observations. The reviewer explicitly
      declined to claim his artifact is `EXPLICIT_FAILURE`, scoping it as an
      issuer-side statement; that is his reading of his own case, not a
      constraint `-00` states. This work area decides neither question on his
      behalf. *(E-6)*
      → Not resolved in the candidate. Its `EXPLICIT_FAILURE` definition requires
      "a positive, attributable failure observation ... to the identified
      delivery attempt, target, and boundary" and does **not** restrict the state
      to receiver-side observations — so the candidate leaves the question
      exactly where `-00` left it, and takes no position on the reviewer's
      artifact. E-6 stays `OPEN / NEEDS DESIGN`.
- [x] **F3 — Expressing a "verifiable reference that resolves to a closed target
      set"** format-neutrally, without importing a resolution mechanism. *(I-2)*
      → **Author-candidate disposition.** The candidate expresses it as "a
      verifiable resolution rule and inputs from which the same set can be
      reconstructed at the reconciliation cutoff" (R-CD-4) and as a "set
      identifier or reproducible resolution rule" whose closure basis must be
      stated (R-CD-15). No resolution mechanism, wire format, or registry is
      imported. Whether this phrasing is sufficient in practice has had no public
      review.
- [~] **F4 — What counts as *verifiably bound*** target identity when the target
      is carried through a broker, gateway, sidecar, or OS channel. *(I-3)*
      → **Partially addressed, deliberately deferred to profiles.** R-CD-16
      requires that evidence reaching the relying party preserve enough source
      and transformation information to determine whether the distinction
      survived the path, and requires a profile to define a lossless mapping for
      every governance-relevant state or expose that the mapping is incomplete,
      ambiguous, or unavailable. Conformance cases 25 and 26 exercise the
      intermediary failure modes. The candidate does **not** define a general
      test for what makes a target identity verifiably bound through a specific
      intermediary; it makes the profile state and expose it. The underlying
      question stays open.
- [x] **F5 — Boundary with adjacent action-evidence work** for the consequential
      effect of an operation that crossed before a freeze applied. The author
      wants the execution and consequential-effect semantics left to that work.
      *(I-4)*
      → **Author-candidate disposition.** The candidate draws the boundary
      explicitly: the Action Evidence Boundary addresses "a different direction
      and object", and "the 'control effect' here is the governed runtime state,
      not the consequential business or physical effect of the protected
      action". `control-activation` leaves the in-flight operation's outcome to
      "the applicable outcome profile". Stated by the author; not agreed with the
      AEB author on the record.
- [x] **F6 — Interaction between §6.3 conservation and obligation-level
      conservation** once obligations and instructions are counted separately.
      *(A6)*
      → **Author-candidate disposition.** Resolved by replacement rather than
      coexistence: the candidate's conservation equation is stated over Delivery
      Obligations (`|O|`), with receiver-record accounting (`|R|`) as a separate
      equation, and profiles may subdivide a class provided the subdivisions sum
      to the parent count. There is no longer a competing per-instruction
      equation for the two to interact.

---

## Explicit non-goals for `-01`

These constraints were set before the candidate existed. Each is followed by
whether the candidate holds to it.

- Do **not** define a receipt format, wire protocol, signature scheme,
  transparency service, policy language, or audit regime. `-00`'s abstract and
  §1.1 already exclude these.
  — **Held.** The candidate's abstract repeats the exclusion verbatim and
  `scitt-composition` states that no new SCITT receipt format is required.
- Do **not** adopt Cedulon's finding-code precedence ordering as a generic
  standard rule, and do **not** write normative text for it.
  — **Held.** R-CD-10 states a `SHOULD`-level deterministic-and-reviewable
  expectation and explicitly declines to prescribe a universal precedence
  ordering.
- Do **not** invent `FULLY_SUPPORTED` / `CONDITIONALLY_SUPPORTED` /
  `NOT_SUPPORTED` (or any equivalent enum) unless a later, explicit design
  decision adopts them.
  — **Superseded by an explicit author design decision.** The candidate adopts
  all three as conceptual meanings in `claim-qualification`. This constraint was
  conditional from the start, and the condition — "a later, explicit design
  decision" — is now met by the candidate itself. It is **not** met by reviewer
  agreement or consensus, and it sits ahead of the author's own public statement
  that he did not want to freeze the vocabulary yet. See **F1**.
- Do **not** classify the Cedulon aborted/refused receipt as `EXPLICIT_FAILURE`.
  — **Held.** The candidate takes no position on the reviewer's artifact. See
  **F2**.
- Do **not** restate contestability effect states already defined by
  `draft-pinto-agent-authz-contestability`.
  — **Held.** The candidate treats that model as a composition boundary and does
  not restate its states. See **D1**.
- Do **not** describe any third-party project as an implementation of this
  draft.
  — **Held.** Cedulon, the contributed EMILIA fixture, and the AIREP artifacts
  are each labelled with their own evidence class — adjacent-domain evaluation
  evidence, test input, and author-side experimental implementation input
  respectively — and the candidate states that none is an independent
  implementation of the document and that "additional independent
  implementations are sought".
- Do **not** claim IETF WG adoption or IETF consensus. The document is an
  individual submission.
  — **Held.** No adoption, consensus, or endorsement claim appears in the
  candidate; this was checked mechanically over the XML as part of integrating
  it. The candidate is stored under `../draft/candidate/01/`, deliberately
  outside `../draft/published/`, and has not been submitted to the Datatracker.

## Open items to settle before `-01` goes to the Datatracker

- **F1** — confirm the deliberate adoption of the three claim-support names,
  which is ahead of the author's last public statement on freezing vocabulary.
- **D2** — the Cedulon revision cited by the candidate (`-08`) is ahead of the
  revision this work area verified (`-06`, checked 2026-09-01). Verify against
  the Datatracker before submission.
- **E3** — confirm that naming Iman Schrock personally in Acknowledgements is
  covered by the contributor's public attribution request.
- **W-4** — still unanswered: whether `-01` should additionally cite RFC 9942
  where receipts specifically are meant. The candidate cites RFC 9943 only.
- **E-4, E-5, E-6, E-7** — these reviewer messages postdate the author's last
  public reply and have received no public response. Candidate text addressing
  them is the author acting alone.
