# Results — author-side reproduction, 4 September 2026

Raw output is in `run-0.8.0.stdout.txt` and `run-0.12.0.stdout.txt`. Everything
below is transcribed from those files. **No field is inferred that the program
did not print.**

Both runs: `node` exit code **0**, `stderr` empty, identical driver bytes
(`f7f1218a…37bc8e`).

## 1. Case matrix

`counts` means the report object carried a `counts` key. Field names are
Cedulon's own, as printed.

| Case | 0.8.0 observed | 0.12.0 observed | Reviewer claim tested | Match |
|---|---|---|---|---|
| **d** — balanced, full trust, window+scope declared | `ok=true`, `guarantee=unconditional`, `summary="audit: balanced"`, **no `counts` key**, `scope` present, findings `(none)`, warnings `counterparty-unbound` | same `ok`/`guarantee`/`summary`/`scope`/findings/warnings, **plus `counts`** (`receipts.submitted 1, attested 1, inScope 1, aborted 0, settled 1, matched 1, deferred 0, carried 0, unmatched 0, repeated 0, unreconciled 0`; `settlements.rows 1, matched 1`) | baseline / class counts new in 0.12.0 | **MATCH** |
| **e** — balanced, NO rail key, NO window, NO scope | `ok=true`, `guarantee=`**`conditional`**, `summary="audit: balanced"`, findings `(none)`, warnings **`unauthenticated-extract`**, `counterparty-unbound` | identical, plus `counts` | **Claim 2** — omitting the rail trust input yields `unauthenticated-extract` and conditional guarantee | **MATCH** |
| **e2** — balanced, rail key pinned, window+scope NOT declared | `ok=true`, `guarantee=`**`conditional`**, `summary="audit: balanced"`, findings `(none)`, warnings **`unstated-audit-window`**, **`unstated-audit-scope`**, `counterparty-unbound` | identical, plus `counts` | **Claim 1** — structural success shape *plus* `guarantee=conditional` *plus* `unstated-audit-window` / `unstated-audit-scope` | **MATCH** |
| **b** — closing-boundary receipt, next window names it | `ok=true`, `guarantee=unconditional`, `summary="audit: balanced"`, findings `(none)`, warnings `counterparty-unbound`; **no counts, so the row is not exposed anywhere in the report** | same top-level fields, **plus `counts.receipts.carried = 1`** (with `matched 0`, `unmatched 0`, `settlements.rows 0`) | **Claim 5** — 0.12.0 exposes the carried row in its counts instead of letting it disappear from the reported population | **MATCH** |
| **c** — aborted receipt (refused spend) | `ok=true`, `guarantee=unconditional`, `summary="audit: balanced"`, findings `(none)`, warnings `counterparty-unbound`; **no counts** | same top-level fields, **plus `counts.receipts.aborted = 1`** and **`counts.receipts.settled = 0`** | **Claim 4** — 0.12.0 publishes class counts separating `aborted=1` from `settled=0`; 0.8.0 lacks those counts | **MATCH** |
| **f** — malformed issuer record (many-to-one) | `ok=false`, `guarantee=unconditional`, `summary="audit: 1 settlement without receipt → FAIL"`; findings, in order: `malformed-policy-hash(n8…)`, `settlement-without-receipt(r8)`, `receipt-chain-break(n8…)`, `checkpoint-total-mismatch(epoch-1)`, `checkpoint-total-mismatch(epoch-1-count)`, `checkpoint-head-mismatch(epoch-1-head)`; warnings `counterparty-unbound` | **identical findings list, identical order, identical warnings**, plus `counts` | **Claim 6** — one malformed record emits several layered diagnostics and they stay visible | **MATCH** |
| **g** — rail key pinned, extract signed by a DIFFERENT key | `ok=false`, `guarantee=conditional`, `summary="audit: 1 finding(s) → FAIL"`, findings `extract-key-mismatch(extract)`, warnings `counterparty-unbound` | same `ok`/`guarantee`/`summary`/findings, warnings **`settlement-comparison-skipped(extract)`**, `counterparty-unbound`; `counts` shows `receipts.unreconciled 1` and `settlements.unreconciled 1` | **Claim 7** — 0.12.0 exposes `settlement-comparison-skipped`; 0.8.0 does not emit it | **MATCH** |
| **h** — rail key pinned, NO extract supplied at all | `ok=`**`false`**, `guarantee=`**`conditional`**, `summary="audit: 1 finding(s) → FAIL"`, findings `receipt-without-settlement(n1…)`, warnings **`unauthenticated-extract`**, `scope=undefined` | identical, plus `counts` (`receipts.unmatched 1`, `settlements.rows 0`) | **Claim 3** — structural FAIL while the qualification axis reports the evidence population was not established | **MATCH** |
| **i** — no rail key, NO extract supplied at all | identical to **h** | identical to **h**, plus `counts` | **Claim 3**, second form | **MATCH** |
| **j** — extract declares a DIFFERENT account than pinned | `ok=false`, `guarantee=conditional`, `summary="audit: 1 finding(s) → FAIL"`, findings `extract-scope-mismatch(extract)`, warnings `counterparty-unbound`, `scope.accountId="other"` | identical, plus `counts` | not a separately stated review claim; recorded for completeness | **NOT CLAIMED** |

## 2. The only two differences between the versions

Across all ten cases, `ok`, `guarantee`, `summary`, `scope`, `findings`, and
`warnings` are **identical between 0.8.0 and 0.12.0**, with exactly two
exceptions:

1. **`counts` is present in 0.12.0 and absent in 0.8.0**, in every case. This is
   the class-count publication the review described.
2. **`settlement-comparison-skipped` appears in 0.12.0 case `g` only.** 0.8.0
   emits no such code in any case.

No other semantic difference was observed. Formatting is identical because the
same driver printed both.

## 3. Claim-by-claim outcome

| # | Reviewer claim | Outcome |
|---|---|---|
| 1 | Structural result / qualification separation: rail key pinned but window and scope undeclared returns the structural success shape **plus** `guarantee=conditional` **plus** `unstated-audit-window` and `unstated-audit-scope` | **Reproduced** (case `e2`, both versions) |
| 2 | Omitting the rail trust input produces `unauthenticated-extract` with conditional guarantee | **Reproduced** (case `e`, both versions) |
| 3 | Receipts presented with no authenticated extract: structural FAIL is returned while the qualification axis says the comparison population was not established | **Reproduced** (cases `h` and `i`, both versions): `ok=false` with `guarantee=conditional`, finding `receipt-without-settlement`, warning `unauthenticated-extract`, and `scope=undefined` |
| 4 | 0.12.0 publishes class counts distinguishing `aborted=1` from `settled=0`; 0.8.0 lacks them | **Reproduced** (case `c`) |
| 5 | The 0.12.0 report exposes the carried closing-boundary row in its counts rather than letting it disappear | **Reproduced** (case `b`: `counts.receipts.carried=1`; 0.8.0 has no counts and says nothing about the row) |
| 6 | One malformed record emits multiple layered diagnostics that remain visible | **Reproduced** (case `f`: six ordered findings, one code repeated, plus one warning — seven emitted codes with one appearing twice, matching the enumeration recorded from the earlier probe) |
| 7 | 0.12.0 exposes `settlement-comparison-skipped` | **Reproduced** (case `g`, 0.12.0 only) |

**No reviewer claim failed to reproduce.** No mismatch was observed.

## 4. Observations recorded without being promoted into claims

- In case `f` this driver prints `counterparty-unbound` on the **warnings** axis,
  so the ordered *findings* list holds six entries rather than seven. The earlier
  probe record in `../CEDULON_POPULATION_PROBE.md` enumerates seven codes for the
  same row **including** `counterparty-unbound`. The set of emitted codes agrees;
  the two records split them across the findings/warnings axes differently
  because they are **different driver programs**. This is a presentational
  difference between two author-side records, not a semantic disagreement, and it
  is **not** treated as a correction to the historical probe.
- Cases `h` and `i` produce byte-identical reports at both versions, i.e. pinning
  the rail key changes nothing when no extract is supplied at all.
- Case `g` at 0.12.0 reports `unreconciled = 1` on both the receipts and the
  settlements axis, so the rows remain counted when the comparison is skipped.

## 5. What this reproduction does not establish

- It does not establish that Cedulon implements
  `draft-abak-agent-control-delivery-evidence`. It does not.
- It does not establish conformance of anything to that document.
- It does not establish an interoperability result between two implementations.
- It does not establish that the draft's requirements are correct — it
  establishes only what these published packages printed for these inputs.
- It does not restate, correct, or replace the 1 September 2026 probe.
- The draft's rule that structural `FAIL` "MUST identify at least one positive
  failing condition and MUST NOT be inferred solely from missing evidence" was
  **not** modified during or because of this measurement. Cases `h` and `i` are
  recorded as adjacent-domain evaluation evidence bearing on that rule, not as a
  reason to change it.
