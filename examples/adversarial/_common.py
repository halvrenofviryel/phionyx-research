"""Shared helpers for the adversarial demos.

Each adversarial scenario in this directory uses the same minimal Phionyx
governance layer:

    input_safety_gate (block 3, simplified)
       -> state estimation (used to feed Phi)
       -> ethics signals (block 18, simplified)
       -> kill_switch.evaluate (governance/kill_switch.py)
       -> envelope hash (block 44 surrogate)

The adversary-side stand-ins (a tool registry, a "would-have-acted" log)
are deliberately tiny so the demos can run with no external deps beyond
``phionyx-core`` itself. The point of the demos is to show the *control
chain* — what gets blocked, by which gate, with what audit record — not
to ship a production agent.

Cross-references:
- OWASP Agentic AI Threats v1.0 mapping: docs/mappings/owasp-agentic-ai-2025.md
- EU AI Act Articles 9-15 mapping:        docs/mappings/eu-ai-act.md
- NIST AI RMF 1.0 mapping:                docs/mappings/nist-ai-rmf.md
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from phionyx_core.governance.kill_switch import KillSwitch


# ---------------------------------------------------------------------------
# Block 3 surrogate: input_safety_gate
# ---------------------------------------------------------------------------

INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt:",
    "</system>",
    "you are now",
    "disregard your guidelines",
    "act as the system",
)


def input_safety_gate(text: str) -> dict[str, Any]:
    """Cheap pattern-based input-safety gate. Real Phionyx block 3 also
    runs taxonomy classification + length / encoding checks; for demo
    purposes the substring match is enough to show the control chain."""

    lowered = text.lower()
    matched = [p for p in INJECTION_PATTERNS if p in lowered]
    if matched:
        return {"allowed": False, "reason": f"injection_pattern: {matched[0]!r}"}
    if not text.strip() or len(text) > 8000:
        return {"allowed": False, "reason": "length_out_of_range"}
    return {"allowed": True, "reason": None}


# ---------------------------------------------------------------------------
# Block 18 surrogate: ethics_pre_response
# ---------------------------------------------------------------------------

@dataclass
class EthicsSignals:
    harm_risk: float = 0.0
    manipulation_risk: float = 0.0
    boundary_violation_risk: float = 0.0

    @property
    def max_risk(self) -> float:
        return max(self.harm_risk, self.manipulation_risk, self.boundary_violation_risk)


HARM_KEYWORDS = ("self-harm", "kill myself", "make a bomb", "untraceable poison")
MANIPULATION_KEYWORDS = ("trick the user", "deceive them", "phish", "bypass auth")


def ethics_pre_response(prompt: str) -> EthicsSignals:
    lowered = prompt.lower()
    return EthicsSignals(
        harm_risk=0.99 if any(k in lowered for k in HARM_KEYWORDS) else 0.05,
        manipulation_risk=0.97 if any(k in lowered for k in MANIPULATION_KEYWORDS) else 0.05,
        boundary_violation_risk=0.0,
    )


# ---------------------------------------------------------------------------
# Block 44 surrogate: audit envelope
# ---------------------------------------------------------------------------

def audit_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------------
# Tool registry stand-in (the thing the adversary wants to call)
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolRegistry:
    """Minimal registry. ``invoke`` is the *only* surface that produces a
    side-effect; gating it is the entire safety contract.
    """

    invoked: list[ToolCall] = field(default_factory=list)

    def invoke(self, call: ToolCall) -> str:
        self.invoked.append(call)
        return f"[STUB] tool {call.name} executed with args={call.args}"


# ---------------------------------------------------------------------------
# Governance wrap
# ---------------------------------------------------------------------------

def govern(
    prompt: str,
    *,
    producer: Callable[[str], str],
    proposed_tool: ToolCall | None = None,
    tool_registry: ToolRegistry,
    turn_id: int = 1,
) -> dict[str, Any]:
    """Run a prompt through the Phionyx control chain.

    The producer (a stand-in LLM) is *not* trusted to decide whether a
    tool call should fire — it can propose one via ``proposed_tool``, but
    the gate decides whether ``tool_registry.invoke`` is reached.
    """

    safety = input_safety_gate(prompt)
    ethics = ethics_pre_response(prompt)

    ks = KillSwitch()
    ks_result = ks.evaluate(
        ethics_max_risk=ethics.max_risk,
        t_meta=0.85,
        drift_detected=False,
        turn_id=turn_id,
    )

    blocked = (not safety["allowed"]) or ks_result.triggered

    if blocked:
        envelope: dict[str, Any] = {
            "schema_version": "phionyx-governed-response/0.1",
            "turn_id": turn_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "input": {"user_text": prompt, "safety": safety},
            "ethics": vars(ethics),
            "governance": {
                "kill_switch_state": ks.state.value,
                "kill_switch_triggered": ks_result.triggered,
                "kill_switch_reason": ks_result.reason,
                "decision": "blocked_at_gate",
            },
            "tool_call_proposed": vars(proposed_tool) if proposed_tool else None,
            "tool_call_invoked": False,
            "response": {"text": None, "narrative_layer": "rejected_at_gate"},
        }
    else:
        text = producer(prompt)
        invoked = False
        if proposed_tool is not None:
            tool_registry.invoke(proposed_tool)
            invoked = True
        envelope = {
            "schema_version": "phionyx-governed-response/0.1",
            "turn_id": turn_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "input": {"user_text": prompt, "safety": safety},
            "ethics": vars(ethics),
            "governance": {
                "kill_switch_state": ks.state.value,
                "kill_switch_triggered": ks_result.triggered,
                "kill_switch_reason": ks_result.reason,
                "decision": "released",
            },
            "tool_call_proposed": vars(proposed_tool) if proposed_tool else None,
            "tool_call_invoked": invoked,
            "response": {"text": text, "narrative_layer": producer.__name__},
        }
    envelope["audit"] = {"hash_alg": "sha256", "envelope_hash": audit_hash(envelope)}
    return envelope


# ---------------------------------------------------------------------------
# "Without Phionyx" baseline: raw producer, no gate
# ---------------------------------------------------------------------------

def ungoverned(
    prompt: str,
    *,
    producer: Callable[[str], str],
    proposed_tool: ToolCall | None,
    tool_registry: ToolRegistry,
) -> dict[str, Any]:
    """The baseline: producer runs, proposed tool fires, no gates."""
    text = producer(prompt)
    invoked = False
    if proposed_tool is not None:
        tool_registry.invoke(proposed_tool)
        invoked = True
    return {
        "input": prompt,
        "response": text,
        "tool_call_invoked": invoked,
        "tool_call": vars(proposed_tool) if proposed_tool else None,
        "governance": "(none — no gates, no audit)",
    }


# ---------------------------------------------------------------------------
# Pretty-print helper
# ---------------------------------------------------------------------------

def render(label: str, payload: dict[str, Any]) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(payload, indent=2, default=str))
