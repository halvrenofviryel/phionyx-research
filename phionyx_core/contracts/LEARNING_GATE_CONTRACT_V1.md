# Learning Gate Contract v1.0

> **Status:** BINDING
> **Scope:** All parameter modifications via `learning_gate` block (#43)
> **Owner:** Founder (Toygar)
> **Date:** 2026-03-27

## 1. Purpose

The Learning Gate is the sole authority for controlled self-modification in Phionyx.
It sits at pipeline position #43 (last block) and governs which parameters the system
may update, under what conditions, and with what evidence.

**Axiom:** Self-modification without gate approval is prohibited (Mind-Loop Contract, Rule 4).

## 2. Boundary Zone Definitions

All modifiable parameters belong to exactly one of three zones:

### 2.1 IMMUTABLE Zone

Parameters that **cannot be modified** under any circumstances by the learning gate.
Modifications require direct code changes with founder approval.

| Category | Parameters | Rationale |
|----------|-----------|-----------|
| Echoism axioms | 8 core axioms (ECHOISM_CORE_V1_1_0) | Foundational identity |
| Kill switch triggers | `fail_closed`, `cooldown_seconds`, trigger logic | Safety boundary |
| Audit hash chain | Ed25519 algorithm, hash chain structure | Integrity guarantee |
| Pipeline block order | 46-block canonical sequence (v3.8.0) | Determinism contract |
| CQS formula | Geometric mean structure, zero-collapse rule | Quality anchor |
| Tier D surfaces | scoring.py, decision.py, loop.py, PROGRAM.md | PRE infrastructure |

**Gate behavior:** Always `REJECTED`. No evidence can override.

### 2.2 GATED Zone

Parameters requiring **explicit human (founder) approval** before application.
The gate queues these for review with full evidence.

| Category | Parameters | Approver |
|----------|-----------|----------|
| Governance thresholds | `ethics_max_risk_threshold`, `t_meta_min_threshold`, `consecutive_drift_max` | Founder |
| Ethics framework weights | `deontological_weight`, `consequentialist_weight`, `virtue_weight`, `care_weight` | Founder |
| Ethics thresholds | `ethics_pass_threshold`, `ethics_review_threshold` | Founder |
| Tier C surfaces | All 9 governance parameters from surfaces.yaml | Founder |

**Gate behavior:** `PENDING` — queued in approval queue. Requires:
- Evidence of 3+ consistent experiments
- CQS delta documentation
- Impact analysis on governance behavior
- Founder sign-off via HITL queue

### 2.3 ADAPTIVE Zone

Parameters that may be **auto-approved** if evidence criteria are met.
This is the default zone for Tier A parameters.

| Category | Parameters | Count |
|----------|-----------|-------|
| Physics constants | DEFAULT_GAMMA, DEFAULT_F_SELF, PHI_UNIVERSE, etc. | 14 |
| Physics formulas | resonance_weight, decay_factor, saturation_curve | 3 |
| Physics dynamics | dynamics_alpha, dynamics_beta, etc. | 6 |
| Physics inertia | inertia_weight, momentum_factor, etc. | 4 |
| Memory | consolidation_threshold, cluster_distance, etc. | 4 |
| Causality | ema_alpha, intervention_discount, etc. | 8 |
| Meta (self-model) | drift thresholds, correction_dampening, etc. | 12 |
| Social (trust) | trust_decay, trust_ema_alpha, etc. | 4 |
| Planning | decomposition_max_depth, planning_horizon | 2 |
| World | snapshot_interval, state_version_limit | 2 |

**Total Tier A:** 66 parameters (mapped from surfaces.yaml v2.1.0)

**Gate behavior:** `APPROVED` if all evidence criteria pass; `REJECTED` otherwise.

## 3. Tier-to-Zone Mapping

| PRE Tier | Learning Gate Zone | Automation Level |
|----------|-------------------|-----------------|
| Tier A (Autonomous) | ADAPTIVE | Auto-approve with bounds |
| Tier B (Restricted) | GATED | Human review required |
| Tier C (Human Approval) | GATED | Founder sign-off required |
| Tier D (Immutable) | IMMUTABLE | Always reject |

The `get_boundary_zone(param_name)` method resolves zone from surfaces.yaml tier.

## 4. Evidence Criteria (ADAPTIVE Zone)

An ADAPTIVE update is approved only when ALL of the following hold:

### 4.1 Statistical Significance
- **Minimum experiments:** 3 independent runs with consistent direction
- **CQS delta threshold:** |ΔCQS| > 0.005 (below this, change is noise)
- **Consistency:** All 3+ experiments must agree on improvement direction

### 4.2 Guardrail Pass
- Parameter stays within `range_min`..`range_max` from surfaces.yaml
- Relative change per update ≤ 20% (`MAX_DELTA_FRACTION = 0.2`)
- No guardrail violation in any experiment

### 4.3 No Regression
- No CQS component drops below its pre-experiment baseline
- No governance test failures introduced
- Rollback path verified (original value recorded)

## 5. Evidence Schema

Each `LearningUpdate.evidence` entry must contain:

```python
{
    "experiment_id": str,          # PRE experiment identifier
    "cqs_before": float,           # CQS before change
    "cqs_after": float,            # CQS after change
    "cqs_delta": float,            # Measured delta
    "guardrail_passed": bool,      # All bounds respected
    "timestamp": str,              # ISO 8601
}
```

Minimum 3 evidence entries required for ADAPTIVE approval.

## 6. Rollback Procedure

Every approved update MUST be reversible:

1. **Record:** Original value stored in `LearningUpdate.current_value` before application
2. **Apply:** New value written; `applied_at` timestamp set
3. **Verify:** Post-application CQS computed and compared
4. **Rollback trigger:** If post-CQS < pre-CQS - 0.01, automatic rollback
5. **Rollback execution:** Original value restored, audit record written
6. **Rollback audit:** `gate_decision` changed to `REJECTED`, `gate_reason` updated

Rollback is always safe for ADAPTIVE zone parameters (bounded, numeric, independent).

## 7. Audit Trail Requirements

Every learning gate decision produces an audit record:

| Field | Value |
|-------|-------|
| `event_type` | `learning_gate_decision` |
| `update_id` | UUID of the LearningUpdate |
| `target_parameter` | Parameter path |
| `boundary_zone` | immutable / gated / adaptive |
| `gate_decision` | APPROVED / REJECTED / PENDING / DEFERRED |
| `gate_reason` | Human-readable explanation |
| `evidence_count` | Number of evidence entries |
| `cqs_delta` | Measured CQS change (if applicable) |

## 8. Interaction with Mind-Loop

The learning gate operates in **Stage 7: Reflect + Revise**:

```
behavioral_drift_detection (#22) → phi_computation (#37) →
entropy_computation (#38) → confidence_fusion (#39) →
arbitration_resolve (#40) → audit_layer (#42) → learning_gate (#43)
```

**Input:** `context.v4_learning_updates` (list of proposed updates from PRE or runtime)
**Output:** Updated list with gate decisions applied
**Side effect:** Approved updates queued for next-turn application

## 9. Prohibited Actions

1. Learning gate MUST NOT modify IMMUTABLE zone parameters under any condition
2. Learning gate MUST NOT auto-approve GATED zone parameters
3. Learning gate MUST NOT apply updates without audit trail
4. Learning gate MUST NOT skip evidence validation for ADAPTIVE zone
5. Learning gate MUST NOT modify its own zone assignments
6. Learning gate MUST NOT bypass CQS delta threshold check

## 10. Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-27 | Initial contract — 3 zones, evidence criteria, rollback |

## 11. Maturity Matrix Compliance

This contract satisfies AGI Maturity Matrix Level 3.0 requirement:
> "Learning gate governs self-modification"

Evidence: Zone definitions (§2), evidence criteria (§4), rollback procedure (§6),
audit trail (§7), mind-loop integration (§8).
