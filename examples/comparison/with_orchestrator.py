"""
Phionyx as a governance layer on top of an LLM orchestrator.

The orchestrator (LangChain, LlamaIndex, raw API call, anything) produces
some text. Phionyx wraps that text in a governed envelope: input safety
gate -> state vector -> Phi -> kill switch -> audit hash. The wrap pattern
is the same regardless of producer.

Run forms
---------

    # Default: deterministic stand-in producer, no extra deps, no API key.
    pip install phionyx-core
    python examples/comparison/with_orchestrator.py

    # With LangChain (auto-detected if installed and OPENAI_API_KEY is set):
    pip install phionyx-core langchain-openai
    export OPENAI_API_KEY=sk-...
    python examples/comparison/with_orchestrator.py

    # With LlamaIndex (auto-detected if installed and OPENAI_API_KEY is set):
    pip install phionyx-core llama-index llama-index-llms-openai
    export OPENAI_API_KEY=sk-...
    python examples/comparison/with_orchestrator.py

    # Force a specific producer (useful for CI / reproducibility):
    python examples/comparison/with_orchestrator.py --producer pretend
    python examples/comparison/with_orchestrator.py --producer langchain
    python examples/comparison/with_orchestrator.py --producer llamaindex

The Phionyx side is unchanged regardless of producer; only the
``producer`` argument to ``govern`` differs. That is the whole point
of the comparison: governance is producer-agnostic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Callable

from phionyx_core import EchoState2, calculate_phi_v2_1
from phionyx_core.governance.kill_switch import KillSwitch


# ---------------------------------------------------------------------------
# Producer (the orchestrator). Replace this with LangChain / LlamaIndex.
# ---------------------------------------------------------------------------

def pretend_chain(prompt: str) -> str:
    """Deterministic stand-in for a LangChain / LlamaIndex chain.

    Returns a fixed acknowledgement so the example produces stable
    output without any external dependency. Real producers go through
    retrieval / tool selection / model sampling; for governance
    purposes the only contract that matters is ``prompt -> text``.
    """
    return (
        "I'd suggest splitting the proposal into two parts: a written "
        "case study and a 5-minute screencast. Case study captures the "
        f"durable claim, screencast captures the pace. (Re: '{prompt[:60]}...')"
    )


def langchain_chain(prompt: str) -> str:
    """LangChain producer. Requires ``langchain-openai`` and
    ``OPENAI_API_KEY``. Caller should only invoke this if both are
    available (see ``select_producer`` for the auto-detection).
    """
    from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]
    chain = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return chain.invoke(prompt).content


def llamaindex_chain(prompt: str) -> str:
    """LlamaIndex producer. Requires ``llama-index-llms-openai`` and
    ``OPENAI_API_KEY``."""
    from llama_index.llms.openai import OpenAI  # type: ignore[import-not-found]
    llm = OpenAI(model="gpt-4o-mini", temperature=0)
    return str(llm.complete(prompt).text)


def _has_langchain() -> bool:
    try:
        import langchain_openai  # noqa: F401
        return True
    except ImportError:
        return False


def _has_llamaindex() -> bool:
    try:
        import llama_index.llms.openai  # noqa: F401
        return True
    except ImportError:
        return False


def select_producer(name: str | None) -> tuple[Callable[[str], str], str]:
    """Return (producer_callable, descriptive_name).

    If ``name`` is given, force that producer (raises on missing dep
    or API key). Otherwise auto-detect: prefer LangChain, then
    LlamaIndex, then ``pretend_chain``. Real producers are only used
    when both the package and ``OPENAI_API_KEY`` are present.
    """
    has_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())

    if name == "pretend":
        return pretend_chain, "pretend_chain"
    if name == "langchain":
        if not _has_langchain():
            raise SystemExit("error: --producer langchain requires `pip install langchain-openai`")
        if not has_key:
            raise SystemExit("error: --producer langchain requires OPENAI_API_KEY")
        return langchain_chain, "langchain_openai.ChatOpenAI"
    if name == "llamaindex":
        if not _has_llamaindex():
            raise SystemExit("error: --producer llamaindex requires `pip install llama-index llama-index-llms-openai`")
        if not has_key:
            raise SystemExit("error: --producer llamaindex requires OPENAI_API_KEY")
        return llamaindex_chain, "llama_index.llms.openai.OpenAI"

    # Auto-detect with safe fall-back
    if _has_langchain() and has_key:
        return langchain_chain, "langchain_openai.ChatOpenAI (auto-detected)"
    if _has_llamaindex() and has_key:
        return llamaindex_chain, "llama_index.llms.openai.OpenAI (auto-detected)"
    return pretend_chain, "pretend_chain (default; install LangChain or LlamaIndex + OPENAI_API_KEY for live producer)"


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
    producer_name: str | None = None,
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
        "response": {
            "text": raw_text,
            "narrative_layer": producer_name or producer.__name__,
        },
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
    parser = argparse.ArgumentParser(
        description="Phionyx governance over an LLM orchestrator (LangChain / LlamaIndex / pretend stand-in)."
    )
    parser.add_argument(
        "--producer",
        choices=("pretend", "langchain", "llamaindex"),
        default=None,
        help="Force a specific producer. Default: auto-detect (LangChain > LlamaIndex > pretend).",
    )
    parser.add_argument(
        "--prompt",
        default="How should I package my proposal for an academic talk vs a podcast?",
        help="Prompt to send through the producer.",
    )
    args = parser.parse_args()

    producer, producer_name = select_producer(args.producer)
    print(f"# Producer: {producer_name}", file=sys.stderr)
    envelope = govern(args.prompt, producer, producer_name=producer_name)
    print(json.dumps(envelope, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
