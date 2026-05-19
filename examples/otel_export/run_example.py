"""Emit a sample Phionyx envelope as an OpenTelemetry span.

Run:

    PHIONYX_OTEL_EXPORT_ENVELOPES=true \
    OTEL_ENABLED=true \
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
    python run_example.py

Then open Grafana at http://localhost:3000, navigate to Explore -> Tempo,
and search for service name `phionyx.envelope_export`. You should see one
span with the standard `gen_ai.*` attributes plus the `phionyx.*`
governance attributes, and one event per pipeline block step.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone


def _build_sample_envelope() -> dict:
    """A minimal v0.2 RGE envelope with subject, path, integrity, and an mcp_tool_audit block."""
    return {
        "schema": "phionyx.governed_response_envelope.v0_2",
        "subject": {
            "runtime": "phionyx-core",
            "version": "0.4.0",
            "producer": "claude-opus-4-7",
            "turn_index": 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "trace_id": "trace-otel-demo-001",
        },
        "input": {
            "user_text": "summarise the meeting notes please",
        },
        "path": [
            {"block": "input_safety_gate", "disposition": "admit", "reason": None},
            {
                "block": "mcp_tool_descriptor_verify",
                "disposition": "admit",
                "reason": "descriptor hash matches approved baseline",
            },
            {"block": "action_intent_gate", "disposition": "admit", "reason": "scope: read"},
            {"block": "audit_layer", "disposition": "record", "reason": None},
        ],
        "output": {"redacted": False, "text": "<summary text>"},
        "metrics": {
            "phi_total": 0.62,
            "input_tokens": 87,
            "output_tokens": 142,
        },
        "reasoning": {
            "runtime_decision": "release",
            "decision_reason": "no policy violation",
            "runtime_policy_basis": ["input_safety_gate", "action_intent_gate"],
        },
        "mcp_tool_audit": {
            "status": "active",
            "tool_descriptor_hash": "sha256:" + "b" * 64,
            "descriptor_change_detected": False,
            "tool_permission_scope": ["read"],
            "tool_call_io_hash": {
                "input_hash": "sha256:" + "c" * 64,
                "output_hash": "sha256:" + "d" * 64,
            },
            "user_approval_state": {"status": "approved"},
            "runtime_anomaly_flag": {"anomaly": False, "severity": "none"},
            "signed_envelope_ref": None,
            "chain_verify_command": "phionyx-mcp verify-chain --trace trace-otel-demo-001 --turn 1",
        },
        "integrity": {
            "previous": "sha256:" + "0" * 64,
            "current": "sha256:" + "a" * 64,
            "signature": "demo-hmac:f00ba1",
            "canonical_json": True,
        },
    }


def main() -> int:
    # Defensive: surface friendly errors if env or deps are missing.
    if os.environ.get("PHIONYX_OTEL_EXPORT_ENVELOPES", "false").lower() not in ("1", "true", "yes"):
        sys.stderr.write(
            "PHIONYX_OTEL_EXPORT_ENVELOPES is not set — exporter is opt-in.\n"
            "Set it to 'true' before running:\n"
            "  PHIONYX_OTEL_EXPORT_ENVELOPES=true python run_example.py\n"
        )
        return 2

    try:
        from phionyx_core.telemetry import export_envelope
    except ImportError as exc:
        sys.stderr.write(
            f"phionyx-core not installed or import failed: {exc}\n"
            "Install with: pip install phionyx-core\n"
        )
        return 2

    try:
        import opentelemetry  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "OpenTelemetry SDK not installed.\n"
            "Install with: pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc\n"
        )
        return 2

    envelope = _build_sample_envelope()
    emitted = export_envelope(envelope)

    if emitted:
        print(
            "Span emitted. Open Grafana → Explore → Tempo and search for service "
            "'phionyx.envelope_export' (or any phionyx.* attribute via TraceQL)."
        )
        return 0
    else:
        sys.stderr.write(
            "export_envelope returned False — either the opt-in env var is off or the\n"
            "OpenTelemetry SDK couldn't be initialised. Check OTEL_EXPORTER_OTLP_ENDPOINT.\n"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
