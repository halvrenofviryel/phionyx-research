# Phionyx against AARM R1–R9 — a source-level evidence map

> **What this is.** A requirement-by-requirement reading of what the Phionyx source actually
> contains, against the nine AARM conformance requirements, with file paths and honest gaps.
> Written to be checked, not believed.
>
> **What this is not.** A conformance claim. Phionyx does not meet AARM's organizational
> eligibility conditions and is not eligible for Core or Extended — see §4. Nothing here should be
> read as "AARM-conformant".
>
> Requirements quoted from `aarm.dev/conformance`, read 2026-07-30.
> Source read at commit `a8b660d3` of the private development monorepo.

**What a reader can check here, and what they cannot.** This repository is a public mirror and does
not carry everything the reading was made against. Verified 2026-07-30: all eleven cited
`phionyx_core` paths are present here, and `tools/claude_code_mcp/` is present with **4 of the 12
gate scripts and 6 of the 17 tests** that exist in the monorepo. `.claude/settings.json`, which is
where the hooks are wired, is **not mirrored**. Claims below that depend on the unmirrored material
are marked; they are stated because they are true of the system, not because they can be checked
from this repository alone.

## 1. Why the reading is split across multiple artifacts

Phionyx is not one program. **Different parts of it address different AARM requirements**, and
conflating them produces a wrong answer in both directions.

| | Raw lines | What it is |
|---|---:|---|
| `phionyx_core` | 67,267 | The runtime — state, memory, governance, record contracts, telemetry |
| `phionyx_bridge` | 16,365 | Delivery adapters |
| `tools/claude_code_mcp` | 12,871 | The control plane — 12 hooks, 8 of them PreToolUse |
| `phionyx_agents` | 5,021 | Agent-side integration |
| `phionyx_governance` | 3,843 | Cross-turn compliance, offline |

**How these were counted, because the method changes the number.** Raw physical lines of every
`*.py` file under each path — `find <dir> -name '*.py' -exec cat {} + | wc -l`. Comments, blank
lines and test files are **included**; `cloc` was not used and is not installed on the machine that
produced these figures. Excluding blanks and comment-only lines gives 52,317 for `phionyx_core` and
10,087 for `tools/claude_code_mcp`. Line counts are a scale signal and nothing more; no requirement
below is argued from them.

**R1 is addressed by the control plane, not by the runtime.** Addressed, not met — the verdict
below is `partial`. The published architecture paper
(arXiv:2607.18246) describes the runtime; it makes no claim about intercepting external tool
actions. An earlier internal note concluded from this that Phionyx does not address R1. That was
wrong: it read a document about the paper and drew a conclusion about the system. The interception
lives in `tools/claude_code_mcp/`, and it is the part that is exercised on every turn.

This split is ordinary. The registry lists Microsoft's Agent Governance Toolkit under both
`SDK Instrumentation` and `Protocol Gateway` for the same reason.

## 2. The nine requirements

Verdict vocabulary is CDE-12's, applied to ourselves: **`supported`** (present and evidenced at
source level), **`partial`** (present with a named gap), **`not demonstrated`** (looked, did not
find it).

### R1 · Pre-execution interception — `partial`
> *"MUST intercept every agent-initiated action before it is executed. No action may bypass the
> control plane."*

Eight `PreToolUse` hooks are wired in `.claude/settings.json` — **not checkable from this
repository**, which does not mirror that file. What is present here and can be read:
`check_bash_external_effect.py`, `check_self_modification.py`, `check_signed_control_state.py`,
`check_memory_schema.py`, plus `control_override.py`, `control_state.py` and `sandbox_probe.py`.

`check_bash_external_effect.py` runs on **every** Bash invocation — the prefilter was deliberately removed so that no command
shape can dodge it — and classifies against a normalised, quote-stripped form of the command.
A T4 default-deny broker refuses irreversible external effects unless a signed Ed25519 override is
present.

**Named gap.** `control_eval` records honest failures: obfuscated in-process decode and
variable-indirection still evade classification, and a natural-language false claim is not
tool-gated at all because it is not a tool call. "No action may bypass" is therefore not a
statement we can make.

What we can say is narrower, and bounded by a system edge we did not test: **every tool action
routed through the configured Claude Code tool interface is presented to a `PreToolUse` gate.**
Whether every tool type is covered by that configuration, whether a hook-disabled path exists, and
whether an indirect or subprocess invocation constitutes a separate tool boundary are all
unexamined. Each would have to hold for a stronger claim, and none has been checked.

### R2 · Context accumulation — `supported`
`phionyx_core/memory/` (12 modules), `phionyx_core/state/`, `phionyx_core/world/`.
Session state, episodic and semantic memory, and a world model are distinct subsystems.

### R3 · Policy evaluation with intent alignment — `supported`

Two distinct enforcement surfaces sit under this requirement and they are not the same mechanism.
Separated here because a reader is entitled to ask which one AARM's *action-intent alignment* is
actually being answered by.

**R3-A · action policy and authorization.** `phionyx_core/governance/deliberative_ethics.py`,
`rbac.py`, and the pipeline gate blocks. This is the surface R3 describes.

**R3-B · claim/evidence entailment before response release.** The response gate checks whether the
declared evidence entails the claim — `unit_test` does not entail `bug_fixed`. This governs what
the system may **assert**, not what it may **do**.

R3-B is adjacent to R3, not a substitute for it, and is not offered as one.

### R4 · Five authorization decisions — `partial`
> *"MUST be capable of producing one of five decisions: ALLOW, DENY, MODIFY, STEP_UP, or DEFER."*

The capability is there; the **naming is not**. Measured across `phionyx_core/` and
`phionyx_governance/`: `DENY` 22 occurrences, `ALLOW` 13, `DEFER` 5, and **`MODIFY` and `STEP_UP`
zero**. Phionyx's own directive vocabulary is `pass`, `block`, `hedge`, `regenerate`, `rewrite`,
`damp`, `reject`, `require_tool`.

The semantic mapping is defensible but has never been written down or tested:

| AARM | Phionyx | Where |
|---|---|---|
| ALLOW | `pass` | response gate directive |
| DENY | `block`, `reject` | gate directive, hook exit |
| MODIFY | `hedge`, `damp`, `rewrite` | three distinct modification modes |
| STEP_UP | `require_tool` | forces externally-bound evidence before the claim passes |
| DEFER | HITL queue, `AbstentionDecision` | `governance/human_in_the_loop.py`, `contracts/v4/abstention_record.py` |

`regenerate` is deliberately absent from that table because it maps conditionally, and collapsing
it to a single value would be the kind of rounding-up this document exists to avoid:

| `regenerate` when… | maps to |
|---|---|
| the regenerated output replaces the original within the same governed turn | MODIFY |
| additional model or tool verification is required first | STEP_UP |
| completion waits on an external or human action | DEFER |

**Named gap.** An untested mapping is a claim. Until there is a conformance test that drives each
of the five AARM outcomes and asserts the corresponding Phionyx directive, R4 is `partial`.

### R5 · Tamper-evident receipts — `supported`
`phionyx_core/contracts/v4/audit_record.py` carries `record_id`, `sequence_number`,
`previous_hash`, `record_hash` (SHA-256 over content), `signature` (Ed25519 over the hash) and
`signer_public_key`. `decision_receipt.py` carries the directive, decision reason, policy basis,
evidence link kinds, `signature_alg` and `chain_verified`. `abstention_record.py` records
refusals as first-class objects rather than as absent decisions.

AIREP mandates record-level chaining; AARM R5 requires tamper-evidence and offline verification
without mandating a mechanism. **The source implements a construction stricter than the minimum
mechanism R5 describes.** Whether it holds under execution — a tampered record failing
verification — is not established here; see §5.

### R6 · Identity binding — `partial`
> *"Every action receipt MUST be cryptographically bound to an agent identity."*

`audit_record.py` has an `actor` field, and because the signature covers `record_hash` which
covers record content, **the declared `actor` value is integrity-bound to the signed record.**
Integrity of a field is not assurance of an identity, and the next paragraph is the one that
matters.

**Named gap, and it is the honest one.** `actor` is a free-text string the producer sets about
itself. There is no agent key, no credential, no attestation reference — nothing that establishes
the identity as opposed to declaring it. `DecisionReceipt` carries no actor field at all.
`meta/identity_persistence.py` maintains `IdentityTracker` and `IdentitySnapshot`, but that
machinery is not joined to the receipt.

This is exactly the distinction CDE-12's own C11 draws — *a boolean the producer sets about itself
is a claim* — and applying it to ourselves gives `partial`, not `supported`.

### R7 · Semantic distance tracking — `supported`
`phionyx_core/meta/self_model_drift.py` and `meta/knowledge_boundary.py`. The boundary detector
scores an assertion for out-of-distribution risk, graph coverage and novelty before it is allowed
into output, which is drift detection applied at the claim rather than at the task horizon.

### R8 · Telemetry export — `supported`
`phionyx_core/telemetry/otel_export.py` (366 lines) and `otel_metrics.py` (192). Not a stub:
`span_name`, `map_attributes`, `map_events` and `export_envelope` map an AIREP envelope onto
OpenTelemetry spans, attributes and events, with a resolvable semantic-convention module version.

### R9 · Least privilege enforcement — `partial`
`phionyx_core/governance/rbac.py` defines a `Permission` enum, a `Role` enum and
`RBACManager.check_permission`. The control plane adds a bwrap sandbox with the private key
directory masked and the evidence path mounted read-only, plus the T4 default-deny broker.

**Named gap.** AARM's test is *execution-time scoped credentials* — a read-only action holding a
credential that cannot write. Role-based permission checks and a sandbox are a different mechanism
that achieves an overlapping goal. We do not scope credentials at execution time.

## 3. Summary

| | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 |
|---|---|---|---|---|---|---|---|---|---|
| | partial | supported | supported | partial | supported | partial | supported | supported | partial |

**At source-reading level: five `supported`, four `partial`, none `not demonstrated`.** Every
`partial` carries a named gap and none is hidden behind a favourable reading.

## 4. Not a conformance claim

Phionyx is not eligible for AARM Core or Extended and this document does not claim, imply or argue
for either. It is a source reading of what the code contains, published so the reading can be
checked. The registry position it supports is **Aligned** — building in the same space.

## 5. What exists today toward an execution matrix

This document is a source reading. The stronger artifact is a reviewer-runnable evidence package,
and part of it already exists — `tools/claude_code_mcp/tests/` holds 17 test files in the monorepo,
6 of them mirrored here. Naming only
the ones that exist, and marking the rest absent rather than inventing a command:

| Req. | Existing test | Absent |
|---|---|---|
| R1 | `test_external_effect_broker_phase3.py` — the T4 default-deny broker | a test asserting non-invocation from the tool side |
| R5 | `test_control_delivery_c1.py` | a tampered-record verification failure |
| R6 | — | identity mutation invalidating a signature |
| R4 | — | a test driving all five AARM outcomes |
| R9 | — | an execution-time scoped credential refusing a write |

Four of the nine have no test that speaks to the AARM formulation. That is the honest state, and
closing it is a larger piece of work than writing this document was.

## 6. Limits of this reading

- Source read, not executed against a conformance test suite. Every verdict above is a
  **source-level** reading; none is an execution result.
- Single rater, no second reading.
- R4's mapping table is proposed, not tested.
- The reading was made at one commit. A later commit can invalidate any row.

Corrections are wanted, and a correction that moves a row from `supported` to `partial` is more
useful than one that moves it the other way.
