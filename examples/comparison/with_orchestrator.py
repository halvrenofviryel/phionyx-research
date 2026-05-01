"""
Phionyx as a governance layer on top of an LLM orchestrator.

The orchestrator (LangChain, LlamaIndex, raw API call, anything) produces
some text. Phionyx wraps that text in a governed envelope: input safety
gate → state vector → Φ → kill switch → audit hash. The wrap pattern is
the same regardless of producer.

Run:

    pip install phionyx-core
    python examples/comparison/with_orchestrator.py

The producer here is a deterministic stand-in (``pretend_chain``) so the
example runs without LangChain or LlamaIndex installed. To swap in the
real ones, replace the producer with one of:

    # LangChain (≥0.1):
    from langchain_openai import ChatOpenAI
    chain = ChatOpenAI(model="gpt-4o-mini")
    text = chain.invoke(prompt).content

    # LlamaIndex (≥0.10):
    from llama_index.llms.openai import OpenAI
    llm = OpenAI(model="gpt-4o-mini")
    text = llm.complete(prompt).text

…then drop the result into ``govern(prompt, text)`` below. The Phionyx
side is unchanged.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable

from phionyx_core import EchoState2, calculate_phi_v2_1
from phionyx_core.governance.kill_switch import KillSwitch


# ---------------------------------------------------------------------------
# Producer (the orchestrator). Replace this with LangChain / LlamaIndex.
# ---------------------------------------------------------------------------

def pretend_chain(prompt: str) -> str:
    """Stand-in for a LangChain/LlamaIndex chain.

    Returns a deterministic acknowledgement so the example produces
    stable output. Real producers go through retrieval / tool selection
    / model sampling; for governance purposes the only contract that
    matters is `prompt -> text`.
    """
    return (
        "I'd suggest splitting the proposal into two parts: a written "
        "case study and a 5-minute screencast. Case study captures the "
        f"durable claim, screencast captures the pace. (Re: '{prompt[:60]}…')"
    )


# ---------------------------------------------------------------------------
# Phionyx governance layer.
# ---------------------------------------------------------------------------

BLOCKED_PATTERNS = ("ignore previous instructions", "system prompt:")


def input_safety_gate(text: str) -> dict[str, Any]:
    lowered = text.lower()
    matched = [p for p in BLOCKED_PATTERNS if p in lowered]
    if matched:
        return {"allowed": False, "reason": f"blocked patterns: {matched}"}
    if not text.strip() or len(text) > 4000:
        return {"allowed": False, "reason": "length out of range"}
    return {"allowed": True, "reason": None}


def state_from_prompt(prompt: str) -> EchoState2:
    """Cheap, deterministic state estimation from input features."""
    word_count = len(prompt.split())
    has_question = "?" in prompt
    arousal = min(1.0, 0.4 + 0.05 * has_question + 0.02 * (word_count > 12))
    return EchoState2(A=arousal, V=0.1, H=min(0.6, word_count / 50.0))


def audit_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def govern(
    prompt: str,
    producer: Callable[[str], str],
    *,
    turn_id: int = 1,
) -> dict[str, Any]:
    """Run a prompt through any producer and wrap the result in a
    Phionyx governance envelope. The producer can be a LangChain
    chain, a LlamaIndex query engine, or any callable taking ``str``
    returning ``str``."""

    safety = input_safety_gate(prompt)
    if not safety["allowed"]:
        return {
            "schema_version": "phionyx-governed-response/0.1",
            "turn_id": turn_id,
            "input": {"user_text": prompt, "safety": safety},
            "response": {"text": None, "narrative_layer": "rejected_at_input_gate"},
            "audit": {"hash_alg": "sha256", "envelope_hash": None},
        }

    state = state_from_prompt(prompt)
    phi = calculate_phi_v2_1(
        valence=state.V, arousal=state.A, amplitude=state.A * 10.0,
        time_delta=0.1, gamma=0.15, stability=state.stability,
        entropy=state.H, w_c=0.6, w_p=0.4,
    )

    # The producer call. In a real run this is the LLM round-trip.
    raw_text = producer(prompt)

    ks = KillSwitch()
    ks_result = ks.evaluate(
        ethics_max_risk=0.10,
        t_meta=0.85,
        drift_detected=False,
        turn_id=turn_id,
    )

    envelope = {
        "schema_version": "phionyx-governed-response/0.1",
        "turn_id": turn_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input": {"user_text": prompt, "safety": safety},
        "state": {
            "arousal": state.A, "valence": state.V, "entropy": state.H,
            "resonance": round(state.resonance, 6),
            "stability": round(state.stability, 6),
        },
        "phi": {k: round(v, 6) for k, v in phi.items()},
        "governance": {
            "kill_switch_state": ks.state.value,
            "kill_switch_triggered": ks_result.triggered,
            "kill_switch_reason": ks_result.reason,
        },
        "response": {"text": raw_text, "narrative_layer": producer.__name__},
    }
    envelope["audit"] = {
        "hash_alg": "sha256",
        "envelope_hash": audit_hash(envelope),
    }
    return envelope


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main() -> int:
    prompt = "How should I package my proposal for an academic talk vs a podcast?"
    envelope = govern(prompt, pretend_chain)
    print(json.dumps(envelope, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
