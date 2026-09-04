# `-01` worklist

## Status of this worklist

**This file is not the `-01` draft text.** It is a traceability and review
record.

- **A repository candidate `-01` now exists.** It is stored at
  `../draft/candidate/01/` and dated 4 September 2026 as of the pre-submission
  update. This worklist is reconciled against that candidate's actual text.
- **The candidate has been revised once since the focused review round**
  (2026-09-04). Candidate provenance:

  | Candidate state | XML SHA-256 | Reviewed by |
  |---|---|---|
  | Initial focused-review candidate | `da64a03846e03f3868aa2fa54682c87d338a4dedcbc1dc4b5642cdfea79a81c6` | Emek Can Dogru; Iman Schrock |
  | Focused-review disposition candidate | `11884630dcb89082d88f838051e19b4736b4908c67cca2f65725ac3ed46501a7` | Emek and Iman each checked the **changed passages** on this digest (ledger `E-16`, `I-13`) — **not a full-document review** |
  | Post-reproduction candidate | `98c6ad0d1560028e56e0ddd619c2f1e8ebbc3becb58cd48d569368f880e383f9` | **not reviewed by either reviewer** |
  | Current candidate, pre-submission | `b7d515006a650644e94ddefb24df74b74b9946b39c57b4a077946e8880295ada` | **not reviewed by either reviewer** |

  Both reviewers gave a focused review of the initial digest within the
  requested scope, and **both subsequently checked the changed passages on the
  disposition candidate and closed their focused reviews** (ledger `E-16`,
  `I-13`). **Neither claimed a full-document review.** Neither has reviewed the
  post-reproduction or pre-submission bytes, and nothing in this file may be read
  as saying they have — those steps changed evidence bookkeeping, provenance
  wording, and the document date only, with **no normative change**. The document
  remains `draft-abak-agent-control-delivery-evidence-01`; these are candidate
  revisions, not new Internet-Draft revision numbers.
- **`-01` was submitted and posted on 4 September 2026.** The published baseline
  of this document is now `-01`, stored under `../draft/published/01/`. This
  worklist continues to describe the **pre-submission candidate** and is retained
  as provenance; where it and the published files could be read differently, the
  published files control.
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
      → **Implemented, and strengthened on 2026-09-04 after focused review.**
      R-CD-10's final paragraph now says the reduction rule **MUST** be
      deterministic and reviewable (E-11), and requires **all applicable
      diagnostics, including those not selected as the primary
      disposition-driving diagnostic, to remain visible in the report or in an
      explicitly linked diagnostic collection** (E-12). The earlier
      cross-reference making non-selected diagnostics subject to R-CD-11 was
      removed: R-CD-11 accounts for Delivery Obligations and receiver-side input
      records, not for layered diagnostics of one record, and the reviewer
      identified that hook as a category error. The document still states that it
      "does not prescribe a universal precedence ordering among profile-specific
      diagnostics", and **Cedulon's ordering is still not adopted**. Conformance
      case 29 exercises the rule.
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

The candidate's "Minimum Conformance Cases" appendix lists **30** cases, up from
sixteen in `-00` and from 26 in the initial `-01` candidate. Case numbers below
refer to that appendix. Note that these are
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
      document". The paragraph cites Cedulon revision **-08**, and the
      reference list pins `draft-dogru-cedulon-08`.
      **Revision verified 2026-09-03** against the Datatracker
      (<https://datatracker.ietf.org/doc/draft-dogru-cedulon/>): the current
      revision is `draft-dogru-cedulon-08`, last updated 2 September 2026,
      Active Internet-Draft, individual submission, no working group. The
      candidate's citation is therefore correct and this item is closed.
      `../SOURCES.md` §5 records `-06` because it is a dated snapshot taken on
      2026-09-01; it is not wrong, it is earlier, and Cedulon advanced after it
      was written. Like every draft in that table, Cedulon remains an individual
      submission — the Datatracker page states the document is "not endorsed by
      the IETF" and carries "no formal standing".
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
      **Author decision, 2026-09-03: not a submission blocker.** The section is
      scoped to "implementation *and evaluation* experience" in its own first
      sentence. If a reviewer raises the placement, the entries move to a
      separate *Evaluation Experience* subheading; no pre-review churn.
- [x] **E3 — Acknowledgements.** `-00` §15 says specific names and review
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
      **Resolved 2026-09-04 — both permissions are now recorded.**
      Iman Schrock confirmed the personal acknowledgement in the form
      "Iman Schrock, EMILIA Protocol" (ledger **I-12**), so the earlier fallback
      of removing the personal name before submission is no longer needed.
      Emek Can Dogru granted permission explicitly — "you may name me"
      (ledger **E-15**) — and is now named for bounded-population review, the
      structural-result / Claim Support separation, diagnostic-reduction review,
      and the empty-target accounting observation. Permission was given for the
      name only; **no organizational affiliation was requested for him and none
      is asserted**. Tiago Pinto and Walter Hawkins are still **not** named: no
      acknowledgement permission is recorded for either, and they remain within
      the collective thanks. The candidate retains "Specific additional names can
      be added with permission in a later revision" and an explicit
      non-endorsement statement, now stating that being named records a review
      contribution only and implies no endorsement by any named individual,
      organization, or working group.

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
      **The candidate is that later design decision.**
      **What the candidate does and does not freeze.** It does *not* impose the
      three names as a wire enum. `claim-qualification` requires a profile to
      define "a lossless mapping to at least the following conceptual meanings",
      and R-CD-15 uses the same construction for its coverage conditions — "a
      profile MAY use different vocabulary, but it MUST preserve the distinction
      among at least the following conceptual conditions". The three names are a
      **conceptual interoperability floor**, not a mandated vocabulary. An
      earlier draft of this note described the candidate as freezing the
      vocabulary; that was too strong and is corrected here.
      This is still an author-candidate disposition rather than an agreed
      outcome: E-3 remains `OPEN / NEEDS DESIGN` in `REVIEW_LEDGER.md` and the
      reviewer has not responded to it. **The author's decision is to keep the
      model**, because it resolves the problem E-3 actually raised — that a
      single aggregate axis collapses structural reconciliation and evidentiary
      strength into one label. **Action: sync the public record**, by asking the
      reviewer to review this axis on the candidate and stating explicitly that
      the labels are used as a conceptual interoperability floor with lossless
      mapping permitted, rather than as frozen wire vocabulary. That closes the
      distance between the author's earlier "I do not want to freeze the
      vocabulary yet" and the candidate's design, on the record and in public.
      **Classification (superseded): PRE-SUBMISSION REVIEW REQUIRED.**
      **Closed 2026-09-04. The review round was carried out and its outcome is
      recorded at ledger E-8.** The reviewer's focused review of the separation
      reports that "the distinction survives, and the case I could not place in
      -00 now has a place". The three names are retained as a **conceptual
      interoperability floor** with lossless mapping permitted, not as a wire
      enum, which is exactly the framing the review was asked to assess.
      **F1 is no longer pending**, and the "action: sync the public record" above
      is discharged by that review round. What the review does **not** establish
      is consensus, adoption, or agreement by anyone other than the reviewer.
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

## G. Focused pre-submission review round (2026-09-04)

Both reviewers assessed the candidate at XML SHA-256
`da64a03846e03f3868aa2fa54682c87d338a4dedcbc1dc4b5642cdfea79a81c6`. These are
**public reviewer findings plus this work area's dispositions of them**. They are
not IETF consensus, not a working-group position, and not an adoption signal. The
dispositions below produced a **new candidate digest**, which **neither reviewer
has reviewed**.

### Emek Can Dogru

- [x] **G1 — Structural Result × Claim Support: focused review completed.** *(E-8)*
      → No change required. `FULLY_SUPPORTED` / `CONDITIONALLY_SUPPORTED` /
      `NOT_SUPPORTED` are retained as conceptual interoperability meanings with
      lossless mapping permitted for profile vocabulary. **F1 is closed.**
- [x] **G2 — Structural result and Claim Support must be co-exposed.** *(E-9)*
      → Implemented in `claim-qualification`: wherever a structural aggregate
      result is rendered, returned, exported, or otherwise exposed, the claim
      scope and claim-support qualification MUST be exposed **in the same result
      context**, for `PASS`, `FAIL`, and `INCONCLUSIVE` alike; a profile MUST NOT
      expose a bare structural result consumable as the complete result. R-CD-13
      points at the rule and keeps its existing unqualified-`PASS` prohibition.
      **No wire field layout is mandated** — "same result context", not literal
      sibling fields. Conformance case 28.
- [x] **G3 — Empty Required Target Set accounting.** *(E-10; supported by I-11)*
      → Implemented in R-CD-11 and `population-conservation`. Every instruction
      in `I` stays accounted for through target-set construction; a zero-target
      instruction stays in the report with its zero-obligation count and the rule
      that produced the empty set; `|I|` is published alongside `|O|`; the
      instruction-level equation
      `|I| = Ninstructions_with_obligations + Nzero_obligation_instructions` is
      added and the seven-class `|O|` equation is retained unchanged. A profile
      MUST declare whether an empty set is a valid terminal resolution; where it
      is not, the empty set prevents structural `PASS` for the affected scope.
      **No synthetic target and no synthetic disposition** was introduced, and an
      empty set is **not** automatically `EXPLICIT_FAILURE`. Conformance case 27.
- [x] **G4 — R-CD-10 reduction rule: `SHOULD` → `MUST`.** *(E-11)*
      → Implemented. See **B1**.
- [x] **G5 — Non-selected diagnostics are not R-CD-11 population members.** *(E-12)*
      → Implemented. The R-CD-11 cross-reference is removed and replaced with a
      direct visibility requirement. See **B1**. Conformance case 29.
- [x] **G6 — FAIL-from-absence.** *(E-13)*
      → **No normative change.** The rule that `FAIL` "MUST identify at least one
      positive failing condition and MUST NOT be inferred solely from missing
      evidence" is **retained verbatim and not weakened**. The reviewer's
      no-extract measurement is recorded as evaluation evidence that the existing
      rule is load-bearing. The only change is conformance coverage: case 30,
      which states in the case text that it exercises the existing rule rather
      than adding a disposition.
- [x] **G7 — Cedulon mapping drift.** *(E-14)*
      → **Recorded, no repin.** Cedulon 0.12.0 exports an additional finding
      code, `settlement-comparison-skipped`, which the pinned probe's mapping
      does not cover, so **that mapping is known stale relative to 0.12.0**. The
      pinned probe — commit `0a3fa04`, SHA-256
      `031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb` — was
      **not** edited, repinned, or rewritten, and this work area does **not**
      claim it covers current Cedulon 0.12.0. Staleness relative to a later
      upstream release is **not** corruption of the historical measurement.
      **Superseded on 2026-09-04 by G15.** At the time this item was written no
      reproduction had been performed, so the measurements were recorded as
      reviewer-reported evidence only. They have since been independently rerun
      by the author; see **G15**. The "no repin" constraint is unchanged and still
      holds.
- [x] **G8 — Acknowledgement permission recorded.** *(E-15)* → See **E3**.

### Iman Schrock

- [x] **G9 — Multi-target model and parent aggregation: focused review
      completed, no additional blocker.** *(I-7)* → No change.
- [x] **G10 — Closure vs enumeration: focused review completed, no additional
      blocker.** *(I-8)* → No change; the distinction is kept as it stands.
- [x] **G11 — §9.4 admission vs provider entry.** *(I-9)*
      → Implemented in `control-activation`. Every boundary crossing is a
      historical fact and only a crossing that **actually occurred** before
      activation is protected from retroactive relabelling. Local admission and
      provider entry are named as distinct, non-interchangeable boundaries: an
      operation admitted before activation but not yet past a later
      provider-entry or other enforcement boundary **MAY** still be refused
      there, the report **MUST** preserve the earlier admission fact and
      separately preserve the later refusal or blocked transition, and an
      admitted or in-flight operation is **not** automatically exempt from later
      applicable enforcement. The existing requirement that reversal,
      compensation, or remedy needs its own evidence is retained.
      **Follow-on consistency fix (2026-09-04):** the Problem Statement still
      said a later `APPLIED` result "does not relabel that earlier **operation**
      as blocked". That object is too broad once admission and provider entry are
      distinguished, so it now reads as the earlier **boundary transition**, with
      an explicit statement that an operation which crossed one earlier boundary
      can still be subject to a later applicable enforcement boundary. No new
      requirement; the introduction and §9.4 now say the same thing.
- [x] **G12 — Fixture and provenance verified by the contributor.** *(I-10)*
      → **No model change.** Fixture preserved, per-target binding and parent
      rule fit the EP-A / EP-B case, structural closure stays separate from
      verified enumeration, `O1` stays unresolved, `O2` establishes only a scoped
      EP-A refusal, the attachment remains byte-for-byte archived at SHA-256
      `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a`, and the
      AEB `-04` pin and derivative-provenance rule are intact.
- [x] **G13 — Empty-target: supporting review of E-10.** *(I-11)*
      → Recorded as independent support for **G3**, not as a second finding.
- [x] **G14 — Acknowledgement permission confirmed.** *(I-12)* → See **E3**.

---

### Closure and author-side reproduction (2026-09-04)

- [x] **G15 — Author-side reproduction of the Cedulon focused-review
      measurements.** *(ledger A-1; supersedes the "not reproduced" note in G7)*
      → **Performed and PASSED.** The reviewer's pinned case driver
      (`dogrucanemek-alt/cedulon`, commit `52cf577`,
      `interop/abak-00/cases-0.12.0.mjs`, observed SHA-256
      `f7f1218abd1535f104b0010b9127c565b3afab0e72242583ebc459000937bc8e`,
      135 lines, 6 153 bytes, LF only) was rerun **byte-for-byte unmodified**
      against the published `0.12.0` and `0.8.0` npm package sets, from two
      separate clean directories outside every git clone. Both graphs resolved
      homogeneously at the requested version with no third-party dependencies;
      `node` exited `0` with empty `stderr` in both runs.
      **All seven reviewer-reported behaviors reproduced; nothing failed.**
      Raw output, dependency graphs, registry metadata for all fourteen
      package-versions, environment, and the case matrix are in
      `../external-evidence/cedulon-review-reproduction-2026-09-04/`.
      **Three objects stay separate:** the reviewer measurement, the author-side
      reproduction, and the draft requirement. This is an **author-side
      reproduction**, not an independent implementation of Cedulon, not an
      implementation of this document, and not a conformance or interoperability
      result. **The historical 1 September probe was not repinned or edited**, and
      no Cedulon source was vendored. **No normative requirement changed because
      of it** — in particular the FAIL-from-absence rule was neither modified nor
      weakened; cases `h` and `i` are recorded as adjacent-domain evaluation
      evidence bearing on that rule.
- [x] **G16 — Emek checked the dispositions on the current candidate.**
      *(ledger E-16)* → He checked the **changed passages** on
      `11884630dcb89082d88f838051e19b4736b4908c67cca2f65725ac3ed46501a7` and
      stated that the dispositions reflect what he meant. **Not a full-document
      review**, and not recorded as one.
- [x] **G17 — Iman checked the dispositions and closed his focused review.**
      *(ledger I-13)* → Same digest, **changed passages only**. **Not a
      full-document review.**

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
  — **Held.** As of 2026-09-04 R-CD-10 states a `MUST`-level
  deterministic-and-reviewable requirement and requires non-selected applicable
  diagnostics to stay visible or explicitly linked, while still explicitly
  declining to prescribe a universal precedence ordering. The strengthening is
  about *reviewability*, not about importing an ordering: no Cedulon finding
  code and no Cedulon precedence rule appears in the candidate.
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
  outside `../draft/published/`. It was subsequently submitted and posted on
  4 September 2026; the published artifacts are under `../draft/published/01/`,
  and publication remains distinct from adoption or consensus.

## Open items to settle before `-01` goes to the Datatracker

Reviewed by the author on **2026-09-03**, and again on **2026-09-04** after the
focused review round. As of 2026-09-04 the review round that gated submission has
been carried out, the acknowledgement question is settled by explicit permission
from both named reviewers, and no item below still blocks submission. Submission
has nonetheless **not** been made: this pass dispositions review findings and
does not post anything to the Datatracker.

Two different things are tracked below and they are deliberately not merged:

- what the **candidate text** still needs before it is submitted to the
  Datatracker; and
- the **review workflow this work area has chosen** for PR #100, which is a
  local process decision, not a property of the draft.

### Pre-submission review required — DISCHARGED 2026-09-04

- **F1 — structural result × Claim Support.** ~~Seek focused review before
  Datatracker submission and record the resulting disposition.~~ **Done.** The
  focused review was carried out; the reviewer reports that the distinction
  survives and that the case he could not place in `-00` now has a place
  (ledger **E-8**). The three meanings stay a conceptual interoperability floor
  with lossless mapping permitted, not a wire enum. **F1 no longer pending.**
  The review outcome is a reviewer's assessment, not consensus or adoption.

### Attribution confirmation — SETTLED 2026-09-04

- **E3 — personal acknowledgement wording.** ~~Ask Iman Schrock whether the
  personal acknowledgement wording is acceptable.~~ **Confirmed** for
  "Iman Schrock, EMILIA Protocol" (ledger **I-12**), so the removal fallback is
  not needed. **Emek Can Dogru separately granted permission to be named**
  (ledger **E-15**) and is now acknowledged for bounded-population review, the
  structural-result / Claim Support separation, diagnostic-reduction review, and
  the empty-target accounting observation — name only, no affiliation asserted.
  Tiago Pinto and Walter Hawkins remain unnamed: no permission is recorded.

### Closed

- **D2 — Cedulon revision.** ~~Unverified.~~ **Verified 2026-09-03** against the
  Datatracker: current revision `draft-dogru-cedulon-08`, last updated
  2 September 2026. The candidate's citation and reference pin are correct.

### Downgraded — not submission blockers

- **W-4 — RFC 9942 vs RFC 9943.** Not a blocker. RFC 9943 defines the SCITT
  architecture's Signed Statement, registration, and Receipt relationship, and
  refers to RFC 9942 for the lower-level COSE receipt / verifiable data
  structure proof mechanics. The candidate's `scitt-composition` text is about
  carriage and registration properties, so **RFC 9943 alone is the correct
  citation** and is not an error. RFC 9942 would need to be cited additionally
  only if `-01` gains a detailed statement about receipt encoding or proof
  semantics. W-4's original point stands and was honoured: no reference was
  changed on the strength of reviewer prose.
- **E2 — Cedulon inside Implementation Status.** Not a blocker at this stage.
  The section's own first sentence scopes it to "implementation **and
  evaluation** experience" and labels Cedulon explicitly as "adjacent-domain
  evaluation evidence, not an implementation of this document", so no false
  claim is made. If a reviewer raises the placement, the fix is to move those
  entries under a separate *Evaluation Experience* subheading. Not worth the
  churn before review.

### Standing caveat

- **E-4, E-5, E-6, E-7** — these reviewer messages postdate the author's last
  public reply and have received no public response. Candidate text addressing
  them is the author acting alone. This does not block submission; it bounds
  what may be claimed about them. **E-4 is superseded** by the focused review
  round (ledger **E-11**, **E-12**), which restates the same reduction-and-
  visibility point directly; **E-5**, **E-6**, and **E-7** are unaffected and
  keep their existing dispositions. **E-6 / F2 remains open** — nothing in this
  round decides the aborted/refused-operation classification.
- **The focused review round itself is not consensus.** Reviewer findings and
  this work area's dispositions of them are two different things and are kept
  apart in section **G** and in the ledger. No working group has adopted
  anything, no IETF consensus exists for any item in this file, and neither
  reviewer has seen the candidate bytes produced by these dispositions.

---

## Pre-submission gates

Submission readiness for `-01`. These are gates this work area has chosen; none
of them is an IETF requirement, and none of them is a defect in the candidate.

- [x] Focused Claim Support review requested from Emek Can Dogru (F1).
      **COMPLETE** — carried out; outcome at ledger **E-8**; F1 closed.
- [x] Multi-target / freeze-race / provenance review requested from Iman Schrock.
      **COMPLETE** — carried out; outcomes at ledger **I-7**, **I-8**, **I-9**,
      **I-10**, **I-11**.
- [x] Personal acknowledgement wording confirmed by Iman, or removed before
      submission. **COMPLETE** — confirmed (ledger **I-12**); the removal
      fallback is not needed. Emek's permission is separately recorded
      (ledger **E-15**).
- [x] Targeted review responses dispositioned in this work area.
      **COMPLETE** as of 2026-09-04 — see section **G** and ledger entries
      **E-8** … **E-15**, **I-7** … **I-12**.
- [ ] Candidate revalidated after any resulting edits.
      **INCOMPLETE.** Mechanical checks were re-run over the updated candidate in
      this pass (XML well-formedness; `docName` and `seriesInfo` still `-01`;
      R-CD-1 … R-CD-16 each present exactly once; anchors unique; every `xref`
      resolves; every reference cited; the four population equations present and
      mutually consistent; `xml2rfc` 3.34.0 TXT + HTML render, exit 0, with only
      the two pre-existing over-72-character reference-URL warnings). This gate
      stays open because **`idnits` was not available in this environment and was
      NOT RUN**, and it is not ticked on a partial check.

Gates one, two, and four are **submission readiness**: they exist so `-01` goes
to the Datatracker with the two axes it newly depends on having been put in
front of the people who raised them. Gate three is **housekeeping** with two
acceptable outcomes — confirmation, or removal of the personal name with the
required fixture attribution preserved. Gate five applies only if a review
response produces an edit; the mechanical checks are cheap and are re-run rather
than assumed.

### Merge gate vs submission gate

These are separate, and neither implies the other.

- **PR #100 merge gate.** This work area chose not to merge PR #100 until the
  Iman and Emek review responses were in, so that any resulting correction landed
  in the same integration rather than as a follow-up. **Both responses are now in
  and dispositioned (2026-09-04), and the resulting corrections are in the same
  branch.** PR #100 remains **open and unmerged**; merging is a separate decision
  and is not taken by the review-disposition pass. That is a **local
  review-workflow decision**. It is not a statement that the candidate is
  defective, incomplete, or blocked on a technical finding.
- **Datatracker submission gate.** Submission was gated on **F1** only, in the
  narrow sense described above. **F1 is closed** (ledger **E-8**), so that gate
  is discharged. **No Datatracker submission has been made**, and this pass makes
  none: it is a drafting and review-disposition pass, not a submission, an
  adoption action, or a consensus claim.

A reader should not infer from an unmerged PR that `-01` has an unresolved
technical problem, and should not infer from a merged PR that `-01` is ready for
submission.
