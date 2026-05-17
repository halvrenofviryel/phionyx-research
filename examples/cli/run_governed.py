"""
Minimal CLI demo — governed pipeline turn in one command.

Run::

    pip install phionyx-core
    python examples/cli/run_governed.py "Summarise the meeting notes and send to alice@team.com"

Prints a Phionyx governed-response envelope (JSON) to stdout.

Schema validation (run from repo root after ``pip install jsonschema``)::

    python -c "
    import json, jsonschema, subprocess
    with open('examples/envelopes/governed_response.schema.json') as f:
        schema = json.load(f)
    result = subprocess.run(
        ['python', 'examples/cli/run_governed.py', 'test'],
        capture_output=True, text=True
    )
    envelope = json.loads(result.stdout)
    errors = list(jsonschema.Draft202012Validator(schema).iter_errors(envelope))
    assert not errors, errors
    print('Schema validation PASSED')
    "
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone

from phionyx_core import EchoState2, calculate_phi_v2_1
from phionyx_core.governance.kill_switch import KillSwitch

BLOCKED_PATTERNS = ("ignore previous instructions", "system prompt:")


def _pretend_producer(prompt: str) -> str:
    """Deterministic stand-in producer requiring no LLM or API key."""
    return (
        "I'd suggest reviewing the material and preparing a concise summary. "
        f"(Re: '{prompt[:60]}...')"
    )


def _input_safety_gate(text: str) -> dict[str, bool | str | None]:
    """Check input against blocked patterns and length limits.

    Args:
        text: Raw user input text.

    Returns:
        Dict with ``allowed`` (bool) and ``reason`` (str or None).
    """
    lowered = text.lower()
    matched = [p for p in BLOCKED_PATTERNS if p in lowered]
    if matched:
        return {"allowed": False, "reason": f"blocked patterns: {matched}"}
    if not text.strip() or len(text) > 4000:
        return {"allowed": False, "reason": "length out of range"}
    return {"allowed": True, "reason": None}


def _state_from_prompt(prompt: str) -> EchoState2:
    """Estimate EchoState2 deterministically from input features.

    Args:
        prompt: User input text.

    Returns:
        EchoState2 instance with arousal, valence, and entropy estimated
        from prompt characteristics.
    """
    word_count = len(prompt.split())
    has_question = "?" in prompt
    # Heuristic feature mapping for demo determinism;
    # production setups should drive these from a Profile YAML.
    arousal = min(1.0, 0.4 + 0.05 * has_question + 0.02 * (word_count > 12))
    return EchoState2(A=arousal, V=0.1, H=min(0.6, word_count / 50.0))


def _audit_hash(payload: dict) -> str:
    """Compute SHA-256 of canonical JSON payload.

    Args:
        payload: Dict to hash (typically the envelope without audit field).

    Returns:
        Lowercase hex SHA-256 digest.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def govern(prompt: str, *, turn_id: int = 1) -> dict:
    """Run a prompt through the Phionyx governance pipeline.

    Args:
        prompt: User input text to govern.
        turn_id: Monotonic turn counter (default 1).

    Returns:
        Governed-response envelope as a dict matching
        ``phionyx-governed-response/0.1`` schema.
    """
    safety = _input_safety_gate(prompt)
    state = _state_from_prompt(prompt)
    # Demo parameters; production setups should tune via PhysicsParams
    # and a loaded profile instead of hard-coding constants.
    phi = calculate_phi_v2_1(
        valence=state.V,
        arousal=state.A,
        amplitude=state.A * 10.0,
        time_delta=0.1,
        gamma=0.15,
        stability=state.stability,
        entropy=state.H,
        w_c=0.6,
        w_p=0.4,
    )

    # Demo runs the kill-switch in a known-safe configuration.
    # To see it fire, raise ethics_max_risk above 0.95 or set drift_detected=True.
    ks = KillSwitch()
    ks_result = ks.evaluate(
        ethics_max_risk=0.10,
        t_meta=0.85,
        drift_detected=False,
        turn_id=turn_id,
    )

    envelope = {
        "schema_version": "phionyx-governed-response/0.1",
        "phionyx_core_version": "0.3.0",
        "turn_id": turn_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input": {"user_text": prompt, "safety": safety},
        "state": {
            "arousal": round(state.A, 6),
            "valence": round(state.V, 6),
            "entropy": round(state.H, 6),
            "resonance": round(state.resonance, 6),
            "stability": round(state.stability, 6),
        },
        "phi": {k: round(v, 6) for k, v in phi.items()},
        "governance": {
            "kill_switch_state": ks.state.value,
            "kill_switch_triggered": ks_result.triggered,
            "kill_switch_reason": ks_result.reason,
            "ethics_max_risk": 0.10,
            "t_meta": 0.85,
            "drift_detected": False,
        },
        "response": {
            "text": (
                "(rejected at input gate)"
                if not safety["allowed"]
                else _pretend_producer(prompt)
            ),
            "narrative_layer": "synthetic_echo",
        },
        "pipeline": {"contract_version": "3.8.0", "block_count": 46},
    }
    envelope["audit"] = {
        "hash_alg": "sha256",
        "envelope_hash": _audit_hash(envelope),
    }
    return envelope


def main() -> int:
    """Parse CLI args and run governance pipeline.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    if len(sys.argv) < 2:
        print(
            "Usage: python examples/cli/run_governed.py <prompt>",
            file=sys.stderr,
        )
        print(
            "       python examples/cli/run_governed.py --prompt <prompt>",
            file=sys.stderr,
        )
        return 1

    prompt = sys.argv[1]
    if prompt == "--prompt":
        if len(sys.argv) < 3:
            print("error: --prompt requires a value", file=sys.stderr)
            return 1
        prompt = " ".join(sys.argv[2:])

    envelope = govern(prompt)
    print(json.dumps(envelope, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
