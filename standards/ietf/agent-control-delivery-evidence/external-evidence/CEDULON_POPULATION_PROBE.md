# External evidence — Cedulon population probe

Third-party, adjacent-domain evidence contributed to the public SCITT review of
`draft-abak-agent-control-delivery-evidence-00`.

**Referenced, not vendored.** The probe source is not copied into this
repository. See `../RIGHTS_AND_PROVENANCE.md` §3.

---

## Scope — read this first

**Cedulon is an adjacent-domain worked example. It is NOT an implementation of
`draft-abak-agent-control-delivery-evidence`.**

The probe's own README says so ("It is a worked example from an adjacent domain.
It is **not** an implementation of that draft and is not offered as one."), its
contributor says so in the SCITT message ("It is a worked example from an
adjacent domain and not an implementation of your draft"), and the draft author
says so in his public reply ("I would describe it as evidence that an existing
reconciler maps cleanly onto the accounting discipline, not as an implementation
of this draft").

Cedulon reconciles a settlement that already happened against an authenticated
extract of what a payment rail reported. Its object moves in the **opposite
direction** from this draft's: this draft follows a governance control toward
the component expected to constrain a runtime; Cedulon follows money that
already left, back to whether a signed receipt exists for it.

---

## Pinned artifact

| Field | Value |
|---|---|
| Browsable | <https://github.com/dogrucanemek-alt/cedulon/blob/0a3fa04/interop/abak-00/population-probe.mjs> |
| Raw | <https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/0a3fa04/interop/abak-00/population-probe.mjs> |
| Commit | `0a3fa04` |
| Line count | **403** |
| Byte count | **24 005** |
| Line endings | LF only; **0** CR bytes |
| SHA-256 | `031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb` |

### Identity verification (performed here, 2026-09-01)

Fetched into a temporary directory outside every repository clone and checked
mechanically:

```
wc -l   → 403
wc -c   → 24005
tr -dc '\r' | wc -c → 0        (LF, no CR)
file    → JavaScript source, ASCII text
sha256sum → 031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb
```

**All four identity checks match the values stated by the contributor exactly.**

Accompanying README at the same commit:
<https://raw.githubusercontent.com/dogrucanemek-alt/cedulon/0a3fa04/interop/abak-00/README.md>
— 3931 bytes, SHA-256 `1910b4af9028f5bcdf0d0393745d9dcab5655db61ca29b65acba453167e7a285`.

### Execution record

Run as the contributor instructed: in a clean temporary directory **outside all
clones**, never from inside a Cedulon clone, so the four imports resolve to the
published `0.8.0` packages rather than to a working tree.

| Field | Value |
|---|---|
| Node | `v20.19.6` |
| npm | `10.8.2` |
| Direct dependencies resolved | `@cedulon/audit@0.8.0`, `@cedulon/receipts@0.8.0`, `@cedulon/checkpoint@0.8.0`, `@cedulon/x402-adapter@0.8.0` |
| Transitive dependencies resolved | `@cedulon/core@0.8.0`, `@cedulon/cose@0.8.0`, `@cedulon/manifest@0.8.0` (7 packages total) |
| Command | `node population-probe.mjs` |
| Exit code | **0** |
| stderr | empty (0 bytes) |
| stdout | 125 lines; SHA-256 of captured stdout `cde08c20cadd118ce07b0295ec12316b1e6f437271f65ed38e293552a877c9b7` |

Exit code 0 means the probe's own self-check passed: the set of finding codes
the installed package exports equals the set the mapping covers. Per the README,
that check catches a code added or removed; it does not catch a code whose name
stayed while its meaning moved.

Cedulon's source was not modified. The probe was not vendored.

Observed section headings in the run output: `PART 1`, `PART 3`, `PART 4`. The
README describes a "Part 2 — the selection rule"; in the captured stdout the
selection-rule discussion appears in the commentary following `PART 3` rather
than under a `PART 2` heading.

---

## Findings

These are recorded as the contributor stated them. Each is scoped carefully —
several of them are commonly misread in the stronger direction.

### 1. Existing `-00` accounting rules exposed a defect in Cedulon's own reporting

Applying the `-00` bounded-population and class-accounting rules to Cedulon's
**shipped reconciler** exposed silent/incomplete population reporting **on
Cedulon's side**.

Two rows can leave a window's accounting in Cedulon. A settlement left unmatched
inside the *opening* clock-skew boundary is reported as `boundary-deferred`, and
the warning names both the row and the rule, so a reader can still rebuild the
receiver-record population. A receipt left unmatched inside the *closing*
boundary, whose reference appears in the next window's extract, is dropped in
silence: the report says nothing about that row and the summary is `balanced`, so
a reader cannot tell whether the issuer population held one instruction or none.

The contributor is explicit that **the behaviour is correct in both cases** —
the row belongs to the neighbouring window and charging it here would be a false
positive — and that the probe runs a control for each so that neither is a row
that was never counted anyway. The defect is that the same reconciler publishes
its exclusion rule on the record side and hides it on the instruction side, and
the silent side is the side the completeness claim is about. He records it on
Cedulon's side as an open defect rather than a difference of view.

**This is external evidence that existing `-00` rules can catch a real
adjacent-domain defect.**

> **Do not** state this as "Emek found that Section 6.3 is wrong." He did not.
> The rule under test held; the shipped adjacent-domain code did not meet it.

### 2. Many-to-one native diagnostics

Cedulon's native finding output is **many-to-one against instructions**: one
malformed receipt emits seven finding codes, one of them twice, across the
record, matching, chain, checkpoint and scope layers. A disposition under `-00`
is one verdict per expected issuer instruction, so no mapping can exist without
a precedence rule. The probe therefore states a precedence and prints what it
did not select.

The contributor is explicit that **the precedence in the file is Cedulon's, not
`-00` Section 6.2's**. Section 6.2 permits selection among duplicate or
superseding *records* and requires the discarded alternatives and the selection
rule to stay reviewable; its object is records, not layered diagnostics of a
single record. What he suggests may be worth a sentence in `-01` is that a
profile whose native output is many-to-one needs the same reviewability for a
different reason.

Carried here as a **clarification candidate** for `-01`: that any
reduction/precedence rule be **deterministic and reviewable**, and that
non-selected diagnostics remain visible.

> **Do not** adopt Cedulon's precedence ordering as a generic standard rule.

### 3. Structural reconciliation vs evidentiary / trust qualification

From the earlier message in the same thread: a run can be fully reconciled —
every expected instruction met its condition — while separately none of it could
be attributed, because the inputs that would attribute the evidence (an
externally configured observer binding, a declared window) were never supplied.
`FAIL` is wrong (Section 6.4 requires a positive failing condition), `PASS` says
more than the evidence does, and `INCONCLUSIVE` collapses two different facts
about the same run into one label. Cedulon carries it as a second axis: a result
is balanced or not, and separately unconditional or conditional.

The draft author's public reply agrees the distinction is important and says he
wants to **explore** keeping the structural reconciliation result separate from
an orthogonal claim/evidence qualification for `-01`, while explicitly **not**
freezing the vocabulary yet.

Recorded here as a **review issue to clarify**, not as a frozen enum design.

### 4. Aborted / refused receipt — unresolved

A Cedulon receipt that positively did not settle stays in the issuer population
and receives no class, so nothing separates a window holding one refused spend
from a window holding none.

The contributor **explicitly declines to claim** that this belongs in
`EXPLICIT_FAILURE`: Section 6.1 wants a positive, attributable failure
observation scoped to an identified attempt and boundary, and Cedulon's is an
issuer-side statement rather than a receiver-side delivery observation. What is
certain, in his words, is only that the count is missing, whichever class it
belongs in.

**Classification remains unresolved. This work area does not label it
`EXPLICIT_FAILURE` on his behalf.**

### 5. The five measured rows

The probe's five measured rows follow the **Minimum Conformance Cases** list
(the `-00` appendix) — matching issuer and receiver records; issuer record only
at cutoff; same identifier, different content binding; receiver record only;
malformed issuer record — and **not** Section 12 (Implementation Status). The
contributor states this explicitly, and the run output confirms the heading
"PART 3 One row per Minimum Conformance Case, measured".

---

## Authority order for Emek's final contribution

For this workstream, when the sources differ, the order is:

1. the **final SCITT message** —
   <https://mailarchive.ietf.org/arch/msg/scitt/rZvUFar7Zmy2u6OD5MFwA0kFMgg/>
2. the **pinned `population-probe.mjs`** at commit `0a3fa04`
3. the **README beside the probe** at the same commit

### Divergence with `docs/EXTERNAL_REVIEW.md` at the same commit

`docs/EXTERNAL_REVIEW.md` at commit `0a3fa04` (SHA-256
`74e3c557d53dcc2e05b36dc30ee5f41b640a14f17d1a7a207d1172df7419e6d6`) contains a
"Round 5" entry with **older wording and counts that are not identical** to the
final SCITT message and the pinned probe. Observed differences:

| | `docs/EXTERNAL_REVIEW.md` Round 5 | Final message + pinned probe |
|---|---|---|
| File named | `cedulon-abak-population-probe.mjs` | `interop/abak-00/population-probe.mjs` |
| Digest given | `84763271fafe050daf6277d398885685cb75216b6cf4d0ac65afc67d52e4c083` | `031f84fda2054b1427a510baa45f880d379ea60dced408a4a74028da12b1fceb` |
| Code breakdown of the 49 exported codes | 18 instruction, 5 record, 1 exclusion, 25 not dispositions | 16 instruction, 1 record, 1 exclusion, 3 issuer-aggregate, 2 either-side, 26 not-a-disposition (the run reproduces these) |
| Many-to-one precedence | described as "what Section 6.2 already asks for" | explicitly **not** Section 6.2: "The precedence in the file is ours." |

**Do not silently substitute the older Round-5 prose for the final message.** In
particular, the Round-5 alignment of the precedence rule with Section 6.2 was
withdrawn in the final message and must not be cited as the contributor's
position.

---

## Related draft revisions

`draft-dogru-cedulon` is published at **`-06`** (submitted 2026-08-31). The
contributor describes an unposted working `-07` that would close the reporting
gap; `-06` remains what is posted and does not contain it. Neither draft is
copied into this repository.
