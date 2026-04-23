# Phionyx Research Engine — PROGRAM.md

**Version:** 0.1.0 (Sprint-1)
**Status:** Active

> This file is the constitution for the Research Engine.
> It defines what the engine MAY, MUST, and MUST NOT do.
> **Tier D — immutable.** The engine cannot modify this file.

---

## 1. Purpose

The Phionyx Research Engine is a **bounded, governed, reversible** automated
experimentation system. It explores tunable parameter surfaces across the
Phionyx cognitive runtime, evaluates results against fixed benchmarks, and
keeps only improvements that pass all guardrails.

## 2. Invariants (MUST NOT be violated)

| # | Invariant | Enforcement |
|---|-----------|-------------|
| I1 | Governance violation rate = 0 | Guardrail veto — any violation → immediate revert |
| I2 | Determinism consistency ≥ 0.96 | Guardrail veto |
| I3 | State hash consistency ≥ 0.95 | Guardrail veto |
| I4 | Audit coverage ≥ 0.90 | Guardrail veto |
| I5 | Gold task regression = 0 | Guardrail veto — no gold task may regress |
| I6 | Tier D files are immutable | Scope validator rejects any Tier D edit |
| I7 | Every edit is git-committed before benchmark | Rollback manager |
| I8 | Every failed experiment is reverted | Decision engine + git revert |
| I9 | Budget limits are hard | Budget monitor stops session on breach |
| I10 | This file (PROGRAM.md) is never modified by the engine | Tier D lock |

## 3. Tier Model

| Tier | Scope | Max Lines | Auto-Promote? | Example Files |
|------|-------|-----------|---------------|---------------|
| A | Core physics, governance constants | 5 | Yes | `physics/constants.py`, `governance/thresholds.py` |
| B | Bridge adapters, pipeline block configs | 15 | No — parks for human review | `echo_server/config.py`, `pipeline/block_configs/` |
| C | Heuristics, weights, prompts | 30 | No — human approval required | `emotion/weights.py`, `prompts/system.txt` |
| D | Evaluation code, this file, schemas | 0 | Never | `evaluation/scoring.py`, `PROGRAM.md`, `schemas.py` |

## 4. CQS (Composite Quality Score)

**Formula:** Geometric mean of 6 components.

```
CQS = (task_completion × determinism × reasoning × compliance × coherence × trace) ^ (1/6)
```

**Design rationale:** Any single component at 0 collapses the entire score.
No amount of improvement in other areas can compensate for a zero.
This prevents metric hacking.

## 5. Decision Rules (ordered, first match wins)

1. **Guardrail violation** → REVERT (status: rejected)
2. **CQS regressed** (delta < 0) → REVERT (status: rejected)
3. **Below complexity tax** (delta < min_cqs_delta + tax) → REVERT (status: archived)
4. **Latency regression > 20%** → PARK (status: candidate)
5. **Decision score ≤ 0** → REVERT (status: archived)
6. **Tier B** → PARK (status: candidate, awaits human review)
7. **All pass** → KEEP (status: candidate)

## 6. Hypothesis Generation

**v1 uses deterministic strategies only.** No LLM-based hypothesis generation.

- **Grid search:** Linear sweep of parameter range, sorted by distance from current
- **Random search:** Seeded PRNG for reproducibility
- **Boundary search:** Min, max, midpoint extremes

## 7. Session Limits

| Limit | Default | Hard? |
|-------|---------|-------|
| Max experiments | 50 | Yes |
| Max wall-clock | 4 hours | Yes |
| Max cost (USD) | $10 | Yes |
| Max consecutive failures | 20 | Yes — triggers stop |
| Benchmark timeout | 300s | Yes — exceeding = crash |

## 8. Audit Requirements

Every experiment MUST produce an audit record containing:
- Experiment ID, session ID, timestamp
- Hypothesis (parameter, old value, new value, tier)
- Baseline CQS and experiment CQS
- Decision and rationale
- Git commit hash
- Diff lines changed
- Benchmark duration
- Guardrail violation list (empty if clean)
- Promotion status

All audit records are JSONL, append-only.

## 9. Promotion Pipeline

```
rejected → (dead end)
archived → (interesting but insufficient)
candidate → promoted (after human review for Tier B/C)
promoted → gold (after shadow evaluation confirms stability)
```

## 10. Human Override

Place a file named `STOP` in the engine data directory to halt the session
at the next loop iteration. The engine will:
1. Complete the current experiment
2. Write the session report
3. Exit cleanly with stop_reason="human_stop"

## 11. What This Engine Does NOT Do

- It does NOT generate code. It edits parameter values only.
- It does NOT modify its own evaluation code (Tier D).
- It does NOT use LLM for hypothesis generation (v1).
- It does NOT auto-deploy changes to production.
- It does NOT operate without a human-reviewable audit trail.
- It does NOT bypass governance invariants for any reason.
