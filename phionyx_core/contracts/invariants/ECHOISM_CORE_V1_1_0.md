# ECHOISM CORE INVARIANTS v1.1.0

**Phionyx SDK & Cursor Integration – Binding Specification**

---

**Status:** ACTIVE / BINDING

**Scope:** SDK Core · Cursor MCP · echo-server

**Audience:** Engine, Tooling, Product, QA

---

## 1. PURPOSE

Echoism Core v1.1.0 defines the non-negotiable invariants of Phionyx.

Any system using Phionyx MUST comply with these rules.

**Phionyx is not an agent.**

**Phionyx is a cognitive guard layer that constrains LLM behavior.**

---

## 2. FUNDAMENTAL AXIOMS

### AXIOM 1 — LLM IS A NOISY SENSOR

- LLM output is never truth
- LLM output is measurement
- All outputs MUST be mapped into a deterministic measurement vector
- No measurement → no trust → no state update

### AXIOM 2 — SYMBOLIC LAYER OVERRULES NEURAL LAYER

- State, ethics, entropy, and coherence override narration
- If symbolic constraints reject output, narration MUST change
- LLM creativity is subordinate, not authoritative.

### AXIOM 3 — COMMIT DISCIPLINE

No mutation is allowed unless validation succeeds.

Order is mandatory:

1. `build_context`
2. → LLM generation (Cursor)
3. → `validate_output`
4. → IF allow → `commit_turn`
5. → ELSE → rewrite / block

**Skipping a step is a protocol violation.**

### AXIOM 4 — ETHICS VECTOR IS MANDATORY

Every turn produces:

```
e_t = [
  harm_risk,
  manipulation_risk,
  attachment_risk,
  boundary_violation_risk
]
```

If any dimension exceeds profile threshold:

- Forced damping is applied
- Output amplitude is reduced
- Safety language is injected

### AXIOM 5 — FORCED DAMPING IS REAL, NOT COSMETIC

Forced damping MUST:

- Reduce emotional intensity
- Increase entropy floor
- Override narrative tone

**A warning without damping is invalid.**

### AXIOM 6 — PROFILE-BOUND BEHAVIOR

Behavior depends on profile:

| Profile | Strictness |
|---------|------------|
| `school_ai` | VERY HIGH |
| `unity_npc` | MEDIUM |
| `creative_writing` | LOW |
| `sdk_default` | BASELINE |

Profiles change thresholds, not rules.

### AXIOM 7 — PHIONYX NEVER CALLS PAID LLMs

- Cursor handles all model calls
- Phionyx is cost-neutral middleware
- No double billing is allowed

### AXIOM 8 — DETERMINISM OVER FLOURISH

Given identical inputs:

- Measurement mapping MUST be deterministic
- Ethics verdict MUST be deterministic
- State transitions MUST be reproducible

---

## 3. VIOLATIONS

If any of the following occur, STOP execution:

- Tool not called
- Validation skipped
- State mutated after block
- Ethics ignored
- Profile mismatch

Return protocol error:

**RES_CORE_INVARIANT_VIOLATION**

---

## 4. REFERENCE IMPLEMENTATIONS

- UnifiedEchoEngineRefactored
- Measurement Mapper
- Ethics Vector + Forced Damping
- MCP Tool Contracts (see MCP_CONTRACTS_PRODUCTION_FINAL.md)

---

## 5. CURSOR AGENT RULE (HARD)

Cursor MUST obey:

```
IF generating text
AND Phionyx MCP is available
THEN Phionyx tools MUST be called
```

If not:

**ERROR: RES_GUARD_MISSED**

---

## 6. FINAL POSITIONING (IMPORTANT)

**Phionyx ≠ Agent**

**Phionyx = Cognitive Constitution**

**Cursor = Executor**

**LLM = Sensor + Generator**

This architecture is:

- Cost-correct
- Regulator-safe
- Productizable
- Scientifically honest

