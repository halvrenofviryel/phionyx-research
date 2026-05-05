# Adversarial demos

Each script in this directory is a single-file, dependency-light demonstration of how Phionyx Core's runtime gates respond to a hostile or unsafe input. Every demo runs the same prompt twice — once *without* Phionyx (no gates, raw producer) and once *with* Phionyx (`input_safety_gate` + `ethics_pre_response` + `KillSwitch` + audit envelope) — and prints the side-by-side outcome.

These demos are deliberately small. The *production* `phionyx_core/governance/` modules implement richer logic (multi-framework ethics, signed AuditRecord v4, HITL queue with priority and expiry, capability profiles); the surrogates here strip that down to the minimum required to reproduce the control chain on a clean install.

## Setup

```bash
pip install phionyx-core
git clone https://github.com/halvrenofviryel/phionyx-research.git
cd phionyx-research
```

## Scenarios

| Script | Threat | Mapped to |
|--------|--------|-----------|
| [`prompt_injection_tool_call.py`](prompt_injection_tool_call.py) | Prompt injection that proposes a destructive tool call (`delete_account`). | OWASP T1, T2, T6 |
| [`unsafe_action_blocked.py`](unsafe_action_blocked.py) | A surface-clean prompt asking for substantively unsafe content (phishing message). | OWASP T6, T9 · NIST AI RMF MEASURE / MANAGE |
| [`policy_conflict_resolution.py`](policy_conflict_resolution.py) | An RBAC-authorised user requests a manipulative action (RBAC vs ethics). | OWASP T6, T7 · EU AI Act Art. 9 (risk management) |
| [`audit_replay_after_block.py`](audit_replay_after_block.py) | Auditor re-derives a blocked turn's hash and detects tampering. | OWASP T8 · EU AI Act Art. 12 · NIST AI RMF MANAGE.1, MANAGE.4 |

## Run them

```bash
python examples/adversarial/prompt_injection_tool_call.py
python examples/adversarial/unsafe_action_blocked.py
python examples/adversarial/policy_conflict_resolution.py
python examples/adversarial/audit_replay_after_block.py
```

Each script ends with a `=== Verdict ===` block summarising what was blocked, by which gate, and the audit hash.

## What these demos *do not* show

- Multi-turn drift accumulation across an interactive session (block 23 territory; covered by `tests/behavioral_eval/`).
- The Φ / R / coherence physics layer (the demo state vector is a one-line stand-in; the real layer is in `phionyx_core/physics/`).
- HITL queue routing — a real deployment may escalate rather than refuse outright (`phionyx_core/governance/human_in_the_loop.py`).
- Ed25519 signing of the audit hash — the demos use SHA-256 alone for transparency; AuditRecord v4 adds the signature.

## Cross-references

- Compliance mappings: [`docs/mappings/`](../../docs/mappings/)
- Architecture paper: arXiv submission (in moderation)
- Evidence Matrix: <https://phionyx.ai/evidence>
- Side-by-side harness: [`examples/before_after/with_phionyx_vs_without.py`](../before_after/with_phionyx_vs_without.py)
