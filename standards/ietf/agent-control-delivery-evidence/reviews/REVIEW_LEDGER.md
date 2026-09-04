# Review ledger — draft-abak-agent-control-delivery-evidence-00

One entry per substantive public review item raised on the IETF SCITT mailing
list. Whole messages are **not** reproduced here; the archive is the record and
every entry links to it. Short quotations are attributed.

**Review is ongoing.** Nothing in this ledger has been incorporated into a
published revision. `-01` has not been submitted.

Entries `I-1` … `E-7` record public review of the **published `-00`**. Entries
`E-8` … `E-15` and `I-7` … `I-12` record the **focused pre-submission review
round on the `-01` candidate**, described in its own section below. Nothing in
either group is IETF or working-group consensus.

## Disposition vocabulary

| Disposition | Meaning |
|---|---|
| `ACCEPTED FOR -01` | The author's own public response accepts the finding and states an intent to change `-01`. |
| `CLARIFICATION CANDIDATE` | A candidate clarification. Not yet accepted on the public record. |
| `EXTERNAL VALIDATION OF EXISTING -00 RULE` | An existing `-00` rule was applied to something outside this work and held; the finding is about the external system, not about `-00`. |
| `COMPOSITION NOTE` | Concerns how `-00` composes with adjacent work. No requirement change implied. |
| `OPEN / NEEDS DESIGN` | Real problem, no settled answer. Vocabulary/mechanism deliberately not frozen. |
| `NO CHANGE REQUIRED` | No change to the draft text follows from this item. |
| `FOCUSED REVIEW COMPLETED` | A review round this work area requested was carried out and its outcome is recorded. Not a consensus outcome. |
| `SUPPORTING REVIEW` | A second reviewer independently agrees with a finding recorded under another entry. Recorded so the finding is not double-counted as two separate defects. |
| `AUTHOR-SIDE REPRODUCTION` | This work area independently reran a third party's measurement and preserved the raw output. It is **not** a reviewer finding, **not** an implementation, and evidence about the measured system only. |

`Status` is one of `OPEN`, `TRACKED FOR -01`, or `RECORDED`.

> An entry is marked `ACCEPTED FOR -01` **only** where the author's public reply
> actually says so. Where a reviewer's message postdates the author's last
> public reply, that is stated explicitly and the item is not marked accepted.

---

## I-1 — Target multiplicity: existential evidence must not satisfy a universal delivery claim

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/nmX5kiPFudYFDhKIHuno-0hLD8U/> |
| **Affected `-00` sections** | 5.4 (R-CD-4), 5.5 (R-CD-5), 6.1, 6.3, 9.3 |
| **Finding** | R-CD-4 requires a target or resolution input and R-CD-5 a receiver identity, but no normative step binds the resolved target to that receiver, and no accounting unit prevents **one** receiver observation from satisfying a control that resolves to **several** required enforcement paths. |
| **Evidence / example** | `ctrl-1` resolves to `EP-A` and `EP-B`. `EP-A` reads and applies it. `EP-B` produces no receiver observation and remains able to dispatch. Under §6.1 `ctrl-1` can be `CONFIRMED`; the §6.3 issuer population still conserves; §9.3 says the control may nevertheless be ineffective. Reviewer's phrase: "existential evidence for a universal delivery claim". |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/kW9z4Btvou0I568hk4-5NlH17G8/> — "I agree that the target-multiplicity case exposes a real gap in -00" and "your description — existential evidence accidentally satisfying a universal delivery claim — captures the problem precisely". |
| **Disposition** | `ACCEPTED FOR -01` |
| **Open questions** | Exact normative wording; whether the obligation appears in §5, §6, or both. |
| **Expected `-01` impact** | Sections 5 and 6 must prevent an instruction-level `CONFIRMED` when a required path remains unevidenced. |
| **Status** | `TRACKED FOR -01` |

---

## I-2 — Closed required-target set / instruction-target obligation model

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol); supported by Walter Hawkins (see W-3) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/nmX5kiPFudYFDhKIHuno-0hLD8U/> |
| **Affected `-00` sections** | 6.1, 6.2, 6.3, 6.4, 9.3 |
| **Finding** | The model needs one of two contracts: either every intended path gets its own instruction identifier and disposition, or the instruction binds a **closed target set** and reconciliation produces one sub-disposition per target before the parent can be `CONFIRMED`. An open or unresolved target population should preclude `PASS`. |
| **Evidence / example** | Same `ctrl-1` / `EP-A` / `EP-B` case as I-1. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/kW9z4Btvou0I568hk4-5NlH17G8/> — states a preference for the **second** contract, and enumerates: a closed required-target set (or a verifiable reference resolving to one under the declared profile); a disposition per instruction-target obligation; a receiver observation satisfying only the target identity and boundary it is verifiably bound to; parent reported fully confirmed only if **every** required obligation is `CONFIRMED`; and an open/unresolved/non-closed required-target population unable to support a complete-delivery or `PASS` claim. Also: conserve target obligations separately from parent instructions when target multiplicity exists. Reaffirmed at <https://mailarchive.ietf.org/arch/msg/scitt/RvBLhnvOY2_RtdtISeEMwG4Ujbw/>. |
| **Disposition** | `ACCEPTED FOR -01` |
| **Open questions** | How a "verifiable reference that resolves to a closed set" is expressed format-neutrally; interaction with §6.3 conservation when obligations and instructions are counted separately. |
| **Expected `-01` impact** | New reconciliation unit (instruction × required target); parent/child disposition rule; conservation extended to obligations; `PASS` precondition tightened. |
| **Status** | `TRACKED FOR -01` |

---

## I-3 — Exact receiver target / boundary binding

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/nmX5kiPFudYFDhKIHuno-0hLD8U/> |
| **Affected `-00` sections** | 5.4 (R-CD-4), 5.5 (R-CD-5), 6.1 |
| **Finding** | R-CD-4 and R-CD-5 should require **exact agreement** between the resolved target and the receiver identity and boundary, "so the right instruction at the wrong enforcement point cannot confirm delivery". |
| **Evidence / example** | Implicit in the multi-target case: today a matching instruction identifier plus content binding is enough for `CONFIRMED`, regardless of which enforcement point observed it. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/kW9z4Btvou0I568hk4-5NlH17G8/> — "a receiver observation can satisfy only the target identity and boundary to which it is verifiably bound". |
| **Disposition** | `ACCEPTED FOR -01` |
| **Open questions** | What counts as *verifiably* bound when target identity is carried by a third-party transport or broker. |
| **Expected `-01` impact** | Tighten R-CD-4/R-CD-5 to require target↔receiver identity and boundary agreement as a precondition of `CONFIRMED`. |
| **Status** | `TRACKED FOR -01` |

---

## I-4 — Freeze race: `APPLIED` is not retroactive

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/nmX5kiPFudYFDhKIHuno-0hLD8U/>; fixture at <https://mailarchive.ietf.org/arch/msg/scitt/YcoTPgdpSl2RNWvcsB1p3c4VpAM/> |
| **Affected `-00` sections** | 4.4, 5.9 (R-CD-9), 6.1, 9.1, Minimum Conformance Cases appendix |
| **Finding** | `O1` crosses provider entry, then a freeze commits and `O2` is blocked. `O1` remains consumed or in flight and requires outcome reconciliation. Delivery or `APPLIED` status for the freeze **cannot** relabel `O1` and does not prove that an external effect already produced was reversed. |
| **Evidence / example** | Contributed fixture `freeze-after-provider-entry-with-multiple-required-targets` — see `../fixtures/README.md`. Its enforcement record's `local_semantics` states the freeze must "not relabel, release, or reverse operations that crossed provider entry before application". |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/kW9z4Btvou0I568hk4-5NlH17G8/> — "I also agree with the freeze race … I would like to add a conformance case covering that composition boundary while leaving the exact execution and consequential-effect semantics to the adjacent action-evidence work." |
| **Disposition** | `ACCEPTED FOR -01` |
| **Open questions** | Where the boundary sits between this document's control-effect observation and the adjacent action-evidence work's consequential-effect semantics. |
| **Expected `-01` impact** | A non-retroactivity statement and a conformance case binding control epoch, closed target population, effect predicate, and observation window. |
| **Status** | `TRACKED FOR -01` |

---

## I-5 — A declared closed target set does not prove path enumeration is complete

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | Fixture message <https://mailarchive.ietf.org/arch/msg/scitt/YcoTPgdpSl2RNWvcsB1p3c4VpAM/>; provenance message <https://mailarchive.ietf.org/arch/msg/scitt/5J5i8Y6w3WkzewIzH23oMPpb9cI/> |
| **Affected `-00` sections** | 6.3, 6.4, 9.3, 10.3 |
| **Finding** | A required-target population can be structurally **declared closed for reconciliation** without that declaration proving every possible enforcement path in the deployment has been enumerated. Blocking `O2` at `EP-A` does not prove every dispatch path was closed. |
| **Evidence / example** | The fixture carries `closed_for_this_fixture: true` **and** `enumeration_completeness_independently_proven: false` in the same object. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/Ei71eBl2k0_hW32hqvqvyGzEuAM/> — "That makes explicit a distinction that -00 does not currently represent strongly enough"; the author lists "the declared target set is not promoted into an independently proven complete-mediation claim" among the boundaries `-01` must be tested against. |
| **Disposition** | `ACCEPTED FOR -01` |
| **Open questions** | Whether this is a distinct declared property, or a strengthening of §9.3 (which already states "This document does not prove that the enumeration is complete") plus a `PASS` precondition. |
| **Expected `-01` impact** | Represent the declared-closed vs independently-proven-complete distinction explicitly rather than only in §9.3 prose. |
| **Status** | `TRACKED FOR -01` |

---

## I-6 — Fixture provenance rule

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/5J5i8Y6w3WkzewIzH23oMPpb9cI/> |
| **Affected `-00` sections** | None (process/provenance, not draft text). Touches §15 Acknowledgements if the case is incorporated. |
| **Finding** | Unchanged use of the contributed fixture keeps its fixture ID and SHA-256. An adapted use needs a **new ID**, must record the original fixture ID and digest as provenance, and must credit EMILIA Protocol. The **original fixture stays pinned to AEB `-04`**; a derived case or `-01` related-work text may point to the current AEB revision (now `-05`). |
| **Evidence / example** | Fixture `related_work` names `draft-schrock-action-evidence-boundary-04`; Datatracker shows AEB currently at `-05` (submitted 2026-08-31). |
| **Author response on public record** | Partial and **predates** this message. At <https://mailarchive.ietf.org/arch/msg/scitt/Ei71eBl2k0_hW32hqvqvyGzEuAM/> the author confirms he verified the attachment against the stated SHA-256 and will "preserve the fixture ID and credit EMILIA Protocol as the contributor". The **derivative-ID rule and the AEB `-04` pinning** were sent afterwards and have no public author response yet. |
| **Disposition** | `NO CHANGE REQUIRED` (to draft text). Adopted operationally in this work area. |
| **Open questions** | The reviewer asked whether the provenance split fits the conformance-set structure. Not yet answered publicly. |
| **Expected `-01` impact** | None to the requirements. If the case or its structure is incorporated, attribution and pinning must follow this rule. |
| **Status** | `RECORDED` — implemented in `../RIGHTS_AND_PROVENANCE.md` §4, `../fixtures/README.md`, and `../fixtures/contributed/PROVENANCE.md`. |

---

## T-1 — Contestability effect-state composition seam

| Field | Value |
|---|---|
| **Reviewer** | Tiago Pinto (independent) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/7kC3d2XZuGpvnBMkKwwkBm2Yy7w/> |
| **Affected `-00` sections** | 4, 13 |
| **Finding** | Partial overlap with `draft-pinto-agent-authz-contestability-00` in the narrower case where a contestation filing is declared to affect execution state. That draft's §6.3 keeps the executor's acceptance of the declared effect policy, the authenticated trigger, ordering against execution, and the executor's claimed application as separate evidence states; a valid trigger does not imply the effect was applied, and absence of an application record is reported as `not_observed`. The shared discipline is a **composition point**, not a reason to duplicate. |
| **Evidence / example** | The reviewer scopes his comment explicitly: he had not read the full draft and was answering only the author's fourth question. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/xyd1v3mIPRO7GvIUBunwePrjvG8/> — agrees the shared discipline creates a composition seam rather than duplication; will read §6.3 and the surrounding verification model before `-01` and "make the relationship explicit if the comparison holds"; wants to avoid introducing control-delivery states that restate an effect-state distinction the other draft already defines. |
| **Disposition** | `COMPOSITION NOTE` |
| **Open questions** | Whether the comparison holds on a full read. **No restatement** of the contestability effect states is to be introduced. |
| **Expected `-01` impact** | Possible §13 related-work text only, conditional on the comparison holding. No requirement change. |
| **Status** | `OPEN` |

---

## W-1 — Evidence-stage separation and SCITT composition without a new receipt format

| Field | Value |
|---|---|
| **Reviewer** | Walter Hawkins (Corrente Labs, Inc.) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/fOhLQ8vUVoS_Rznapl6OlIaHQ_E/>; also <https://mailarchive.ietf.org/arch/msg/scitt/y14Ek_T_6e1IpoZYQxzKIv5ZKRc/> |
| **Affected `-00` sections** | 4, 8.2, 13 |
| **Finding** | Support: the separation of the four evidence boundaries addresses a useful distinction for autonomous systems, and existing SCITT Signed Statements and profile payload bindings "provide a natural container for referencing these observation facts without requiring new receipt formats". Separately, aligning this draft and the contestability draft around explicit evidence-stage separation "avoids duplicating boundaries while strengthening SCITT composition". |
| **Evidence / example** | Reviewer prose; no test case supplied. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/RvBLhnvOY2_RtdtISeEMwG4Ujbw/> — "I intend to keep these evidence-stage semantics format-neutral and compose them with existing SCITT Signed Statements and profile bindings rather than introduce another receipt format", and will "make both points more explicit" while incorporating the target-multiplicity review into `-01`. |
| **Disposition** | `COMPOSITION NOTE` |
| **Open questions** | See **W-4**: the RFC number in this message does not match the citation in `-00` and must not be imported. |
| **Expected `-01` impact** | Possible clarifying wording in §8.2 / §13 that composition uses existing SCITT mechanisms and introduces no receipt format. No requirement change. |
| **Status** | `OPEN` |

> **Not an adoption signal.** This message opens "Welcome
> draft-abak-agent-control-delivery-evidence-00 to the SCITT WG." That is a
> reviewer's greeting on the list. The document is an individual submission
> (Datatracker group "Individual Submissions"); it has **not** been adopted by
> the SCITT working group and no consensus is implied.

---

## W-2 — Reserved

Merged into **W-1** (the contestability-alignment message
<https://mailarchive.ietf.org/arch/msg/scitt/y14Ek_T_6e1IpoZYQxzKIv5ZKRc/> is a
one-paragraph endorsement of the seam already tracked as T-1 and W-1).

---

## W-3 — Support for the closed required-target / per-target disposition model

| Field | Value |
|---|---|
| **Reviewer** | Walter Hawkins (Corrente Labs, Inc.) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/B-SiXm6sqDnDb2da8b7zRkhhZuw/> |
| **Affected `-00` sections** | 6.1, 6.3, 6.4 |
| **Finding** | Support: "Adopting the closed required-target set contract for -01 is the right move. Requiring per-target sub-dispositions before confirming parent control delivery ensures evidence integrity across multi-target enforcement paths." |
| **Evidence / example** | Reviewer prose; no test case supplied. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/RvBLhnvOY2_RtdtISeEMwG4Ujbw/> — "I agree that the per-target obligation is the important unit here: the parent control should only support a fully confirmed delivery claim when every required target obligation is itself confirmed under the declared rules." |
| **Disposition** | `NO CHANGE REQUIRED` — supporting review. The change it supports is tracked as **I-2**. |
| **Open questions** | None specific to this message. |
| **Expected `-01` impact** | None beyond I-2. |
| **Status** | `RECORDED` |

---

## W-4 — RFC number in reviewer prose does not match the `-00` citation

| Field | Value |
|---|---|
| **Reviewer** | Walter Hawkins (Corrente Labs, Inc.) — raised by this work area, not by the reviewer |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/fOhLQ8vUVoS_Rznapl6OlIaHQ_E/> |
| **Affected `-00` sections** | 8.2, 17 |
| **Finding** | The message refers to "Existing SCITT Signed Statements (RFC 9942)". `-00` §8.2 and §17 cite **RFC 9943**, "An Architecture for Trustworthy and Transparent Digital Supply Chains" (June 2026), with the sentence "[RFC9943] defines signed statements and receipts for registration in a transparency service." Checked against `rfc-editor.org`: **RFC 9942** is "CBOR Object Signing and Encryption (COSE) Receipts" (June 2026) — a different document. |
| **Evidence / example** | `-00` XML `<reference anchor="RFC9943">`; RFC metadata retrieved 2026-09-01 (see `../SOURCES.md` §6). |
| **Author response on public record** | None. Not raised on the list. |
| **Disposition** | `NO CHANGE REQUIRED` — no normative or related-work edit is made on the strength of a reviewer's RFC number. The `-00` XML is authoritative for what `-00` cites. |
| **Open questions** | Whether `-01` should cite RFC 9942 **in addition to** RFC 9943 where receipts specifically are meant. That is a `-01` drafting decision to be made against the RFCs themselves, not against reviewer prose. |
| **Expected `-01` impact** | Possibly none. Any reference change must be verified against RFC metadata first. |
| **Status** | `OPEN` |

---

## E-1 — Cedulon as an opposite-direction adjacent-domain composition

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru (Cedulon / Conarium) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/0DEnFwL01UQXxsO954NhgevgNGk/> |
| **Affected `-00` sections** | 13 |
| **Finding** | Cedulon (`draft-dogru-cedulon`, `-06` posted) reconciles a spend that already happened against an authenticated extract of what the rail reported. Its object moves the **opposite way**: this draft follows a governance control toward the constraining component; Cedulon follows money that already left, back to whether a signed receipt exists for it. A denied spend leaves no portable artifact in the Cedulon profile at all, because its Decision Token encodes an allow — so what its audit says about a refusal it says through the settlement that never appeared on the extract. That is an effect observation over a declared population, never an acknowledgement from an enforcement point. The documents should compose. |
| **Evidence / example** | The reviewer added the neighbourhood sentence on the Cedulon side rather than repeating the four boundaries. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/_R-gOpqjmM0fdOWKUvCR3RVJFqw/> — "I agree that the objects move in opposite directions and that the shared part is the accounting discipline rather than the lifecycle itself. I would prefer to reference that seam rather than duplicate Cedulon's settlement or effect semantics." |
| **Disposition** | `COMPOSITION NOTE` |
| **Open questions** | Whether `-01` §13 gains a sentence, and how to word it without implying Cedulon implements this draft. |
| **Expected `-01` impact** | Possible §13 related-work sentence. No requirement change. |
| **Status** | `OPEN` |

---

## E-2 — Bounded-population rule found a real Cedulon scope/reporting defect

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru (Cedulon / Conarium) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/0DEnFwL01UQXxsO954NhgevgNGk/> |
| **Affected `-00` sections** | 5.11 (R-CD-11), 6.3, 9.3, 10.3 — **applied**, not amended |
| **Finding** | Applying the `-00` bounded-population rule to a **shipped** reconciler in an adjacent domain caught a real defect **in that reconciler**. Cedulon had guarded one axis of the population (a verifier stating no period gets a conditional guarantee) since `-05`, but never carried the rule to the other two axes: a verifier stating neither the account nor the rail still received an unconditional "balanced". An account able to settle on a second rail therefore has a settlement path no presented extract covers — "existential evidence reported as though it were universal, in the money domain rather than the control-delivery one". |
| **Evidence / example** | Reviewer's own account/rail example; a working Cedulon `-07` would close it with two requirements. `-06` remains what is posted and does not contain them. The reviewer notes that enumerating the rails an account can settle on stays the deployment's statement, and that he does not claim the enumeration can be proven complete — the same limit `-00` §9.3 states. |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/_R-gOpqjmM0fdOWKUvCR3RVJFqw/> — "applying the bounded-population rule to a shipped reconciler in another domain exposed a real scope defect"; "a very useful concrete demonstration of why a bounded population has to be defined independently of the favorable evidence later presented to the reconciler." |
| **Disposition** | `EXTERNAL VALIDATION OF EXISTING -00 RULE` |
| **Open questions** | None. This is not a defect in `-00`. |
| **Expected `-01` impact** | None normative. Citable as external evidence that the existing rule catches a real adjacent-domain defect; would need care not to overstate it as an implementation of this draft. |
| **Status** | `RECORDED` — see `../external-evidence/CEDULON_POPULATION_PROBE.md` finding 1. |

---

## E-3 — Structural reconciliation result vs evidentiary/trust qualification

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru (Cedulon / Conarium) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/0DEnFwL01UQXxsO954NhgevgNGk/>; restated with a count in <https://mailarchive.ietf.org/arch/msg/scitt/rZvUFar7Zmy2u6OD5MFwA0kFMgg/> |
| **Affected `-00` sections** | 6.4, 8.1, 5.13 (R-CD-13) |
| **Finding** | Offered explicitly "as a question rather than as a proposed requirement". Where nothing failed but the inputs that would attribute the evidence were never supplied (no externally configured observer binding, no declared window): `FAIL` is wrong because §6.4 requires a positive failing condition; `PASS` says more than the evidence does; `INCONCLUSIVE` is available but loses that the run **was** fully reconciled. Those are two different facts about the same run and one label makes them one. Cedulon carries it as a second axis — balanced or not, and separately unconditional or conditional — which must appear wherever the verdict appears, including the passing path. In the follow-up message, 26 of 49 exported finding codes carry no disposition on their own and instead report whether the declared population or the evidence stands at all. |
| **Evidence / example** | Measured by the pinned probe: `26 not-a-disposition` codes across four sub-kinds (`evidence-authenticity` 14, `population-not-established` 6, `terms-layer` 2, `transparency-layer` 4). |
| **Author response on public record** | <https://mailarchive.ietf.org/arch/msg/scitt/_R-gOpqjmM0fdOWKUvCR3RVJFqw/> — agrees a single aggregate axis can collapse two facts; "For -01 I therefore want to explore keeping the structural reconciliation result separate from an orthogonal claim/evidence qualification. **I do not want to freeze the vocabulary yet** — I want to compare your -06/-07 treatment and the other review comments first — but I think the distinction itself is important." |
| **Disposition** | `OPEN / NEEDS DESIGN` at the time this entry was written; the focused review round closes it — see **E-8**. |
| **Open questions** | Whether it becomes a second axis, a qualifier on the aggregate, or additional required reporting. Vocabulary deliberately **not** frozen. No enum is adopted. |
| **Expected `-01` impact** | Possibly a separation of structural result from claim qualification in §6.4. Nothing decided. |
| **Status** | `SUPERSEDED BY E-8` — the `-01` candidate separates the two dimensions and the reviewer's focused review of that separation is recorded at **E-8**. |

---

## E-4 — Many-to-one native diagnostics need explicit, reviewable reduction

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru (Cedulon / Conarium) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/rZvUFar7Zmy2u6OD5MFwA0kFMgg/> |
| **Affected `-00` sections** | 6.1, 6.2 |
| **Finding** | Cedulon's native output is many-to-one against instructions — one malformed receipt emits seven codes, one of them twice, across the record, matching, chain, checkpoint and scope layers — while a disposition is one verdict. So no mapping can exist without a precedence rule; the probe states one and prints what it did not select. The reviewer is explicit that **this precedence is Cedulon's, not §6.2's**: §6.2 permits selection among duplicate or superseding *records* and requires the discarded alternatives and the rule to stay reviewable, and its object is records, not layered diagnostics of a single record. What may be worth a sentence in `-01` is that a profile whose native output is many-to-one needs the same reviewability for a different reason. |
| **Evidence / example** | Reproduced in the verification run of the pinned probe: the malformed-issuer-record row emits `malformed-policy-hash, settlement-without-receipt, receipt-chain-break, checkpoint-total-mismatch, checkpoint-total-mismatch, checkpoint-head-mismatch, counterparty-unbound` and selects `INVALID`. |
| **Author response on public record** | **None.** This message (2026-09-01 12:58 UTC) postdates the author's most recent public reply in the thread (2026-09-01 03:37 UTC). |
| **Disposition** | `CLARIFICATION CANDIDATE` at the time this entry was written; carried forward and strengthened — see **E-11** and **E-12**. |
| **Open questions** | Whether `-01` says anything at all; if it does, only that a reduction rule be **deterministic and reviewable** and that non-selected diagnostics remain visible. **Cedulon's precedence ordering is not to be adopted as a generic rule**, and no normative text for it is to be written. |
| **Expected `-01` impact** | At most one clarifying sentence extending §6.2's reviewability discipline to many-to-one diagnostics. |
| **Status** | `SUPERSEDED BY E-11 / E-12` — the constraint against importing Cedulon's precedence ordering is still honoured. |

---

## E-5 — Shipped Cedulon report does not expose enough class accounting to reconstruct the population

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru (Cedulon / Conarium) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/rZvUFar7Zmy2u6OD5MFwA0kFMgg/> |
| **Affected `-00` sections** | 6.3, 6.4 — **applied**, not amended |
| **Finding** | Two rows can leave a window's accounting in Cedulon. A settlement unmatched inside the **opening** clock-skew boundary is reported as `boundary-deferred` with the row and the rule named, so `\|R\|` stays reconstructible. A receipt unmatched inside the **closing** boundary, whose reference appears in the next window's extract, is dropped **in silence** and the summary reads "balanced", so a reader cannot tell whether `\|I\|` was one or zero. The behaviour is **correct in both cases** — the row belongs to the neighbouring window and charging it here would be a false positive — and the probe runs a control for each proving neither is a row that was never counted. The defect is that the same reconciler publishes its exclusion rule on the record side and hides it on the instruction side, and the silent side is the side the completeness claim is about. Root cause, in his words: the report publishes findings and an aggregate rather than the class counts required by the last bullet of §6.4. Recorded on the Cedulon side as an open defect, not a difference of view. |
| **Evidence / example** | Reproduced in the verification run — probe `PART 4`: case (a) prints `boundary-deferred` with its rule; case (b) prints `audit: balanced`, no findings, "anything said about the excluded row: no"; each with a control that hardens into a finding. |
| **Author response on public record** | **None to this message** (it postdates the author's last reply). The earlier, related account/rail result is accepted at <https://mailarchive.ietf.org/arch/msg/scitt/_R-gOpqjmM0fdOWKUvCR3RVJFqw/>. |
| **Disposition** | `EXTERNAL VALIDATION OF EXISTING -00 RULE` |
| **Open questions** | None for `-00`. Closing it is Cedulon-side work. |
| **Expected `-01` impact** | None normative. Citable as evidence that §6.4's class-count requirement is load-bearing in practice. |
| **Status** | `RECORDED` — see `../external-evidence/CEDULON_POPULATION_PROBE.md` finding 1. |

---

## E-6 — Aborted / refused-spend mapping deliberately unresolved

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru (Cedulon / Conarium) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/rZvUFar7Zmy2u6OD5MFwA0kFMgg/> |
| **Affected `-00` sections** | 6.1 (`EXPLICIT_FAILURE`), 6.3 |
| **Finding** | A Cedulon receipt that positively did not settle stays in the issuer population and receives no class, so nothing separates a window holding one refused spend from a window holding none. The reviewer **explicitly declines** to claim this belongs in `EXPLICIT_FAILURE`, reasoning that §6.1 wants a positive, attributable failure observation scoped to an identified attempt and boundary while his own artifact is an issuer-side statement rather than a receiver-side delivery observation. "What is certain is only that the count is missing, whichever class it belongs in." |
| **Evidence / example** | Reproduced in the verification run — probe `PART 4` case (c): `audit: balanced`, no findings, "the receipt is in the issuer population and appears in no class count." |
| **Author response on public record** | **None.** Message postdates the author's last reply. |
| **Disposition** | `OPEN / NEEDS DESIGN` |
| **Open questions** | Whether an issuer-side aborted receipt satisfies the `EXPLICIT_FAILURE` requirements is unresolved. §6.1 requires a positive, attributable failure observation scoped to an identified attempt and boundary; it does not itself restrict `EXPLICIT_FAILURE` to receiver-side observations. The reviewer's narrower reading is his own scoping of his own artifact, not a statement about what `-00` requires. **This work area does not label the aborted receipt `EXPLICIT_FAILURE` on the reviewer's behalf, and equally does not read a receiver-side-only restriction into §6.1.** |
| **Expected `-01` impact** | Undetermined. |
| **Status** | `OPEN` |

---

## E-7 — The five measured rows follow the Minimum Conformance Cases list

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru (Cedulon / Conarium) |
| **Source** | <https://mailarchive.ietf.org/arch/msg/scitt/rZvUFar7Zmy2u6OD5MFwA0kFMgg/> |
| **Affected `-00` sections** | Minimum Conformance Cases appendix — **not** §12 Implementation Status |
| **Finding** | Reading note, stated by the reviewer: the probe's five measured rows follow the Minimum Conformance Cases list, not §12, which is Implementation Status. Its self-check compares the finding codes the package exports against the set the mapping covers and exits non-zero when they differ — catching a code added or removed, not a code whose name stayed while its meaning moved. |
| **Evidence / example** | Verification run: `PART 3 One row per Minimum Conformance Case, measured`, five rows matching appendix cases 1–4 and 6; self-check reported 49 exported codes, 49 covered, no unmapped codes, exit `0`. |
| **Author response on public record** | **None.** Message postdates the author's last reply. |
| **Disposition** | `NO CHANGE REQUIRED` |
| **Open questions** | None. |
| **Expected `-01` impact** | None. Recorded so the probe is never described as evidence bearing on §12 Implementation Status. |
| **Status** | `RECORDED` |

---

---

# Focused pre-submission review round on the `-01` candidate

**Reviewed artifact.** Both reviewers assessed the `-01` author candidate at

```
standards/ietf/agent-control-delivery-evidence/draft/candidate/01/draft-abak-agent-control-delivery-evidence-01.xml
SHA-256 da64a03846e03f3868aa2fa54682c87d338a4dedcbc1dc4b5642cdfea79a81c6
```

Those are the exact bytes reviewed. The dispositions below were applied to the
candidate afterwards, producing a **new candidate digest**. Neither reviewer has
reviewed the updated bytes, and this ledger does not claim that they have.

**What these entries are.** They are **public reviewer findings** plus this work
area's own disposition of them. They are not IETF consensus, not a working-group
position, and not an adoption signal. In this round the reviewers' messages and
the author's dispositions are close together in time, so `ACCEPTED FOR -01` here
records **the author's disposition made in this work area on 2026-09-04** rather
than a quotation from a separate public author reply. That is a deliberate
departure from the `-00` convention above and is stated so a reader does not
mistake it for one.

**Archive links.** No IETF mail-archive URL for these two focused reviews is
recorded in this work area at the time of writing. Where one becomes available it
is to be added to the `Source` field of the affected entries. The absence of a
link here is a gap in this record, not evidence that the review was private.

---

## E-8 — Structural Result × Claim Support: focused review completed

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Source** | Focused review of the `-01` candidate at `da64a038…81c6`; archive URL not recorded here |
| **Affected candidate sections** | `global-results`, `claim-qualification`, R-CD-3, R-CD-13, R-CD-15 |
| **Finding** | The separation of the structural reconciliation result from Claim Support holds under focused review. In the reviewer's words: *"The distinction survives, and the case I could not place in -00 now has a place."* |
| **Disposition** | `FOCUSED REVIEW COMPLETED` |
| **Effect on the candidate** | None required. `FULLY_SUPPORTED`, `CONDITIONALLY_SUPPORTED`, and `NOT_SUPPORTED` are retained as **conceptual interoperability meanings, not wire enums**; a profile may use other vocabulary through the lossless mapping `claim-qualification` requires. |
| **Effect on the worklist** | **F1 is no longer pending.** The pre-submission review it required has been carried out and its outcome is recorded here. |
| **Status** | `RECORDED` |

---

## E-9 — A bare structural result can still escape through another representation

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Source** | Same focused review |
| **Affected candidate sections** | `claim-qualification`, R-CD-13 |
| **Finding** | The candidate requires Claim Support to be **preserved** separately from the structural result, but does not require the qualification to **accompany every representation** in which the structural result is exposed. A profile could therefore export a bare `PASS`, `FAIL`, or `INCONCLUSIVE` that a relying party consumes as the complete result. |
| **Disposition** | `ACCEPTED FOR -01` (author disposition, 2026-09-04) |
| **Effect on the candidate** | `claim-qualification` now requires the claim scope and claim-support qualification to be exposed **in the same result context** wherever a structural aggregate result is rendered, returned, exported, or otherwise exposed, and forbids exposing a bare structural result consumable as the complete result. The rule applies to `PASS`, `FAIL`, and `INCONCLUSIVE` alike. R-CD-13 points at it and keeps its existing prohibition on an unqualified end-to-end `PASS`. No wire field layout is mandated. Conformance case 28 exercises it for a passing and a failing result. |
| **Status** | `APPLIED IN CANDIDATE` |

---

## E-10 — Empty Required Target Set: a real population-accounting hole

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru; **independently supported by Iman Schrock** (see `I-11`) |
| **Source** | Same focused review |
| **Affected candidate sections** | R-CD-11, `population-conservation` |
| **Finding** | If `T_i` is empty, instruction `i` contributes no Delivery Obligation to `O` and can disappear from the obligation conservation equation entirely. Obligation-level accounting alone cannot show that the instruction was ever considered. |
| **Disposition** | `ACCEPTED FOR -01` (author disposition, 2026-09-04) |
| **Effect on the candidate** | R-CD-11 now requires every instruction in the bounded issuer population to remain accounted for during target-set construction; a zero-target instruction stays in the report, is reported as contributing zero Delivery Obligations, and carries the rule or condition that produced the empty set. `population-conservation` adds `\|I\| = Ninstructions_with_obligations + Nzero_obligation_instructions` alongside the retained `\|O\|` equation, and requires `\|I\|` to be published. A profile MUST declare whether an empty set is a valid terminal resolution; where it is not, the empty set prevents structural `PASS` for the affected scope. **No synthetic target and no synthetic disposition is introduced**, and an empty set is not automatically `EXPLICIT_FAILURE`. Conformance case 27 exercises it. |
| **Status** | `APPLIED IN CANDIDATE` |

---

## E-11 — R-CD-10 reduction rule was too weak at `SHOULD`

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Source** | Same focused review |
| **Affected candidate sections** | R-CD-10 |
| **Finding** | `SHOULD be deterministic and reviewable` is too weak, because the minimum reconciliation procedure already requires the structural verdict to be reproducible by a third party. A non-deterministic reduction rule defeats that existing requirement. |
| **Disposition** | `ACCEPTED FOR -01` (author disposition, 2026-09-04) |
| **Effect on the candidate** | R-CD-10 now says the reduction rule **MUST** be deterministic and reviewable. |
| **Status** | `APPLIED IN CANDIDATE` |

---

## E-12 — Non-selected diagnostics are not R-CD-11 population members

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Source** | Same focused review |
| **Affected candidate sections** | R-CD-10 |
| **Finding** | The candidate made inputs not selected as the primary diagnostic "subject to the population and input-record accounting rules in R-CD-11". That is the wrong object: R-CD-11 accounts for Delivery Obligations and receiver-side **input records**, not for layered diagnostics of a single record. The reviewability requirement is real; the R-CD-11 hook was a category error. |
| **Disposition** | `ACCEPTED FOR -01` (author disposition, 2026-09-04) |
| **Effect on the candidate** | The R-CD-11 cross-reference is removed from that paragraph. R-CD-10 now requires **all applicable diagnostics, including those not selected as the primary disposition-driving diagnostic, to remain visible in the report or in an explicitly linked diagnostic collection**. **Cedulon's precedence ordering is still not adopted** and the document still declines to prescribe a universal precedence order. Conformance case 29 exercises it. |
| **Status** | `APPLIED IN CANDIDATE` |

---

## E-13 — FAIL-from-absence: reviewer measurement supports the existing rule

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Source** | Same focused review |
| **Affected candidate sections** | `global-results` — **applied, not amended** |
| **Finding** | A no-extract measurement, in which a nominal implementation reports `FAIL` because a receipt or issuer-side object is unmatched while the authenticated comparison population was never presented, lands exactly on the existing rule that `FAIL` **MUST identify at least one positive failing condition and MUST NOT be inferred solely from missing evidence**. |
| **Disposition** | `EXTERNAL VALIDATION OF EXISTING RULE` |
| **Effect on the candidate** | The rule is **retained unchanged and not weakened**. The only change is conformance coverage: case 30 exercises it and states explicitly that it tests the existing FAIL-from-absence rule rather than adding a new disposition. |
| **Status** | `APPLIED IN CANDIDATE` (conformance coverage only) |

---

## E-14 — Cedulon finding-code mapping is stale relative to 0.12.0

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Source** | Same focused review |
| **Affected candidate sections** | Implementation Status — reporting hygiene only |
| **Finding** | Cedulon 0.12.0 exports an additional finding code, `settlement-comparison-skipped`, which the pinned population probe's mapping does not cover. The old mapping is therefore **known stale relative to 0.12.0**. |
| **Disposition** | `RECORDED` — **no silent repin** |
| **What was NOT done** | The pinned probe evidence was **not** edited, repinned, or rewritten. It remains commit `0a3fa04`, SHA-256 `031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb`, recorded against the package versions it was executed against. That record is **historical pinned evidence and is not corrupted**; a later upstream release exporting a new code does not retroactively invalidate a measurement of an earlier release. This work area does **not** claim the old probe covers current Cedulon 0.12.0. |
| **Effect on the candidate** | One hygiene sentence in Implementation Status: the probe stays pinned to the versions it was executed against, and later reviewer-reported measurements against a newer Cedulon release are reviewer-reported public evidence that **the author has not independently reproduced**. No reproduction was performed in this pass. |
| **Status** | `RECORDED` |

---

## E-15 — Acknowledgement permission (Emek Can Dogru)

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Source** | Same focused review |
| **Finding** | Permission granted explicitly: *"On acknowledgements: you may name me."* |
| **Disposition** | `RECORDED` |
| **Effect on the candidate** | Acknowledgements now name **Emek Can Dogru** for bounded-population review, structural-result / Claim Support separation, diagnostic-reduction review, and the empty-target accounting observation. Permission was given for the name; no organizational affiliation was requested and none is asserted. The non-endorsement statement is retained and strengthened. |
| **Status** | `RECORDED` |

---

## I-7 — Multi-target model and parent aggregation: focused review completed

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | Focused review of the `-01` candidate at `da64a038…81c6`; archive URL not recorded here |
| **Affected candidate sections** | `target-set-model`, R-CD-4, R-CD-5, `reconciliation-states`, `parent-aggregation` |
| **Finding** | **No additional blocker.** The existing per-target Delivery Obligation model and the parent-aggregation rule survive focused review. |
| **Disposition** | `FOCUSED REVIEW COMPLETED` / `NO CHANGE REQUIRED` |
| **Status** | `RECORDED` |

---

## I-8 — Structural closure vs verified enumeration: focused review completed

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | Same focused review |
| **Affected candidate sections** | R-CD-11, R-CD-15 |
| **Finding** | **No additional blocker.** The distinction between a target set closed for a reconciliation run and an independently verified enumeration is kept as it stands. |
| **Disposition** | `FOCUSED REVIEW COMPLETED` / `NO CHANGE REQUIRED` |
| **Status** | `RECORDED` |

---

## I-9 — Local admission and provider entry are not interchangeable

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | Same focused review |
| **Affected candidate sections** | `control-activation` (§9.4) |
| **Finding** | No blocker, but one clarification is required. The candidate's §9.4 treated "admission or provider-entry boundary" as effectively interchangeable. They are not. An operation admitted **before** freeze activation can still be refused at a **later** provider-entry or other enforcement boundary. Non-retroactivity means *do not rewrite a boundary fact that already happened*; it does **not** mean an admitted or in-flight operation is exempt from later applicable enforcement. |
| **Disposition** | `ACCEPTED FOR -01` (author disposition, 2026-09-04) |
| **Effect on the candidate** | §9.4 rewritten: every boundary crossing is a historical fact; only a crossing that **actually occurred** before activation is protected from retroactive relabelling; local admission and provider entry are named as distinct, non-interchangeable boundaries; a subsequently applied control **MAY** still prevent a later transition; the report **MUST** preserve the earlier admission fact and separately preserve the later refusal or blocked transition; and an admitted or in-flight operation is not automatically exempt from later applicable enforcement. The existing rule that reversal, compensation, or remedy needs its own evidence is **retained**. A follow-on consistency fix in the same pass repaired the Problem Statement, which still described the protected object as the earlier **operation** rather than the earlier **boundary transition**; the introduction and §9.4 now agree, and no new requirement was added. |
| **Status** | `APPLIED IN CANDIDATE` |

---

## I-10 — Fixture and provenance treatment verified by the contributor

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | Same focused review |
| **Affected candidate sections** | `appendix-freeze-fixture`, Implementation Status; `../fixtures/`, `../RIGHTS_AND_PROVENANCE.md` §4 |
| **Finding** | Confirmed by the contributor: the PR treatment preserves the fixture; the per-target binding and parent rule fit the EP-A / EP-B case; structural closure remains separate from verified enumeration; `O1` stays unresolved; `O2` establishes only a scoped EP-A refusal; the fixture attachment remains byte-for-byte archived; and the original AEB `-04` pin and the derivative-provenance rule are intact. |
| **Disposition** | `NO CHANGE REQUIRED` — verified by the reviewer |
| **Effect on the candidate** | None. The fixture SHA-256 `2d8faa1b64b8a73fd0bf81b21889bbf726cbfb324af099b700499627af84203a` is unchanged, the stored attachment is untouched, and no derivative exists. |
| **Status** | `RECORDED` |

---

## I-11 — Empty target accounting: independent supporting review

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | Same focused review |
| **Affected candidate sections** | R-CD-11, `population-conservation` |
| **Finding** | Explicit agreement with the empty-target accounting point raised in `E-10`. |
| **Disposition** | `SUPPORTING REVIEW` — of `E-10`, not a second finding |
| **Effect on the candidate** | None beyond `E-10`. Recorded so the same defect is counted once and so the record shows two reviewers reached it independently. |
| **Status** | `RECORDED` |

---

## I-12 — Acknowledgement permission (Iman Schrock)

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Source** | Same focused review |
| **Finding** | Permission confirmed for the personal acknowledgement in the form **"Iman Schrock, EMILIA Protocol"**. |
| **Disposition** | `RECORDED` |
| **Effect on the candidate** | The open question in worklist item `E3` — whether the fixture-attribution request extends to a personal acknowledgement — is **closed by the contributor's own confirmation**. The fallback of removing the personal name before submission is no longer needed. The acknowledgement scope now also covers target multiplicity, the required-target and freeze-race fixture, in-flight operation semantics, and provenance review. |
| **Status** | `RECORDED` |

---

---

# Closure of the focused review round, and the author-side reproduction

Three objects are kept separate below and are never merged:

1. **the reviewer measurement** — what a reviewer reported;
2. **the author-side reproduction** — what this work area independently reran; and
3. **the draft requirement** — what the document says.

A reproduction of (1) is not evidence for (3), and neither is an implementation
of the draft.

---

## E-16 — Emek Can Dogru: dispositions checked against the current candidate

| Field | Value |
|---|---|
| **Reviewer** | Emek Can Dogru |
| **Artifact checked** | Candidate XML SHA-256 `11884630dcb89082d88f838051e19b4736b4908c67cca2f65725ac3ed46501a7` |
| **Finding** | The reviewer checked the **changed passages** on that digest and stated that the dispositions reflect what he meant. |
| **Scope limit** | **This is not a full-document review**, and is not recorded as one. The reviewer checked the passages that changed in response to his findings; he made no statement about the rest of the document. |
| **Disposition** | `FOCUSED REVIEW COMPLETED` — closure of `E-8` … `E-15` on the changed passages |
| **Status** | `RECORDED` |

---

## I-13 — Iman Schrock: dispositions checked against the current candidate

| Field | Value |
|---|---|
| **Reviewer** | Iman Schrock (EMILIA Protocol) |
| **Artifact checked** | Candidate XML SHA-256 `11884630dcb89082d88f838051e19b4736b4908c67cca2f65725ac3ed46501a7` |
| **Finding** | The reviewer checked the **changed passages** on that digest and closed his focused review. |
| **Scope limit** | **This is not a full-document review**, and is not recorded as one. |
| **Disposition** | `FOCUSED REVIEW COMPLETED` — closure of `I-7` … `I-12` on the changed passages |
| **Status** | `RECORDED` |

---

## A-1 — Author-side reproduction of the Cedulon focused-review measurements

**This is not a reviewer finding.** It is an evidence event produced by this work
area, recorded in the ledger so it stays visibly distinct from the reviewer
measurement it reproduces.

| Field | Value |
|---|---|
| **Performed by** | the author, 4 September 2026 |
| **Object** | The measurements Emek Can Dogru reported during focused review (`E-13`, `E-14`, and the measured basis of `E-8`) |
| **Method** | The reviewer's own pinned case driver — `dogrucanemek-alt/cedulon`, commit `52cf577`, `interop/abak-00/cases-0.12.0.mjs`, observed SHA-256 `f7f1218abd1535f104b0010b9127c565b3afab0e72242583ebc459000937bc8e`, 135 lines, 6 153 bytes, LF only — run **byte-for-byte unmodified** against the published npm package sets `0.12.0` and `0.8.0`, from two separate clean directories created outside every git clone. Both graphs resolved homogeneously (seven `@cedulon` packages each, no third-party dependencies). No lifecycle install scripts exist in either graph, so `--ignore-scripts` was **not** used and the reviewer's invocation contract was preserved. |
| **Result** | `node` exit `0` and empty `stderr` for both runs. **All seven reviewer-reported behaviors reproduced; no claim failed and no mismatch was observed.** Reproduced: structural-success-plus-`conditional` with `unstated-audit-window` / `unstated-audit-scope`; `unauthenticated-extract` on omitted rail trust; structural `FAIL` returned while the qualification axis reports the comparison population was never established; `aborted=1` / `settled=0` class counts published at `0.12.0` and absent at `0.8.0`; the carried closing-boundary row exposed in `0.12.0` counts; multiple layered diagnostics on one malformed record; and `settlement-comparison-skipped` present at `0.12.0` only. |
| **Evidence** | `../external-evidence/cedulon-review-reproduction-2026-09-04/` — raw stdout/stderr, dependency graphs, registry metadata for all fourteen package-versions, environment, `SHA256SUMS.txt`, and a case-by-case matrix in `RESULTS.md`. |
| **Effect on E-14** | The staleness recorded at `E-14` is now **directly confirmed here**: `settlement-comparison-skipped` is emitted at `0.12.0` and by no `0.8.0` case. `E-14`'s disposition is unchanged. |
| **What was NOT done** | The historical 1 September probe — commit `0a3fa04`, SHA-256 `031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb` — was **not** repinned, edited, replaced, or corrected. The reproduction is a separate, later evidence event with its own driver, packages, and date. No Cedulon source was vendored into this repository. |
| **Explicit non-claims** | This is an **author-side reproduction**, not an *independent implementation* of Cedulon, not an implementation of this document, not a conformance result, and not an interoperability result. Cedulon remains adjacent-domain evaluation evidence. The reproduction changed **no normative requirement**; in particular the rule that structural `FAIL` must not be inferred solely from missing evidence was neither modified nor weakened by it. |
| **Disposition** | `AUTHOR-SIDE REPRODUCTION` |
| **Status** | `RECORDED` |

---

## Index

| ID | Reviewer | Disposition | Status |
|---|---|---|---|
| I-1 | Iman Schrock | `ACCEPTED FOR -01` | TRACKED FOR -01 |
| I-2 | Iman Schrock | `ACCEPTED FOR -01` | TRACKED FOR -01 |
| I-3 | Iman Schrock | `ACCEPTED FOR -01` | TRACKED FOR -01 |
| I-4 | Iman Schrock | `ACCEPTED FOR -01` | TRACKED FOR -01 |
| I-5 | Iman Schrock | `ACCEPTED FOR -01` | TRACKED FOR -01 |
| I-6 | Iman Schrock | `NO CHANGE REQUIRED` | RECORDED |
| T-1 | Tiago Pinto | `COMPOSITION NOTE` | OPEN |
| W-1 | Walter Hawkins | `COMPOSITION NOTE` | OPEN |
| W-3 | Walter Hawkins | `NO CHANGE REQUIRED` | RECORDED |
| W-4 | (raised here) | `NO CHANGE REQUIRED` | OPEN |
| E-1 | Emek Can Dogru | `COMPOSITION NOTE` | OPEN |
| E-2 | Emek Can Dogru | `EXTERNAL VALIDATION OF EXISTING -00 RULE` | RECORDED |
| E-3 | Emek Can Dogru | `OPEN / NEEDS DESIGN` | OPEN |
| E-4 | Emek Can Dogru | `CLARIFICATION CANDIDATE` | OPEN |
| E-5 | Emek Can Dogru | `EXTERNAL VALIDATION OF EXISTING -00 RULE` | RECORDED |
| E-6 | Emek Can Dogru | `OPEN / NEEDS DESIGN` | OPEN |
| E-7 | Emek Can Dogru | `NO CHANGE REQUIRED` | RECORDED |

### Focused pre-submission review round on the `-01` candidate

Reviewed artifact: candidate XML SHA-256
`da64a03846e03f3868aa2fa54682c87d338a4dedcbc1dc4b5642cdfea79a81c6`.
The reviewers have **not** reviewed the updated candidate produced by these
dispositions.

| ID | Reviewer | Disposition | Status |
|---|---|---|---|
| E-8 | Emek Can Dogru | `FOCUSED REVIEW COMPLETED` | RECORDED |
| E-9 | Emek Can Dogru | `ACCEPTED FOR -01` | APPLIED IN CANDIDATE |
| E-10 | Emek Can Dogru (supported by Iman Schrock) | `ACCEPTED FOR -01` | APPLIED IN CANDIDATE |
| E-11 | Emek Can Dogru | `ACCEPTED FOR -01` | APPLIED IN CANDIDATE |
| E-12 | Emek Can Dogru | `ACCEPTED FOR -01` | APPLIED IN CANDIDATE |
| E-13 | Emek Can Dogru | `EXTERNAL VALIDATION OF EXISTING RULE` | APPLIED IN CANDIDATE (conformance coverage only) |
| E-14 | Emek Can Dogru | `RECORDED` — no silent repin | RECORDED |
| E-15 | Emek Can Dogru | `RECORDED` — acknowledgement permission | RECORDED |
| I-7 | Iman Schrock | `FOCUSED REVIEW COMPLETED` / `NO CHANGE REQUIRED` | RECORDED |
| I-8 | Iman Schrock | `FOCUSED REVIEW COMPLETED` / `NO CHANGE REQUIRED` | RECORDED |
| I-9 | Iman Schrock | `ACCEPTED FOR -01` | APPLIED IN CANDIDATE |
| I-10 | Iman Schrock | `NO CHANGE REQUIRED` — verified by reviewer | RECORDED |
| I-11 | Iman Schrock | `SUPPORTING REVIEW` of E-10 | RECORDED |
| I-12 | Iman Schrock | `RECORDED` — acknowledgement permission | RECORDED |

### Closure and author-side reproduction

| ID | Actor | Disposition | Status |
|---|---|---|---|
| E-16 | Emek Can Dogru | `FOCUSED REVIEW COMPLETED` — changed passages on `11884630…01a7`; **not a full-document review** | RECORDED |
| I-13 | Iman Schrock | `FOCUSED REVIEW COMPLETED` — changed passages on `11884630…01a7`; **not a full-document review** | RECORDED |
| A-1 | **the author** (not a reviewer) | `AUTHOR-SIDE REPRODUCTION` of the Cedulon measurements | RECORDED |
