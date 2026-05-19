"""Integration test for OTel envelope export.

Verifies that ``export_envelope`` actually emits a span via a real OTel
tracer when the SDK is installed. Uses ``InMemorySpanExporter`` so the
test runs in-process with no external collector.

Skipped if the OpenTelemetry SDK isn't installed in the environment;
this matches the package contract (OTel is an *optional* dependency of
phionyx-core, never a hard one).
"""
from __future__ import annotations

from typing import Any

import pytest

# Skip the entire module when OTel SDK is unavailable.
otel_sdk = pytest.importorskip(
    "opentelemetry.sdk.trace",
    reason="OpenTelemetry SDK not installed — integration test skipped (optional dep).",
)
pytest.importorskip("opentelemetry.sdk.trace.export.in_memory_span_exporter")

from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from phionyx_core.telemetry import otel_semantic_v1_36_0 as sem
from phionyx_core.telemetry.otel_export import export_envelope


@pytest.fixture
def in_memory_tracer():
    """Yield a real OTel tracer wired to an InMemorySpanExporter."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("phionyx.tests.envelope_export")
    yield tracer, exporter
    provider.shutdown()


@pytest.fixture
def sample_envelope() -> dict[str, Any]:
    return {
        "schema": "phionyx.governed_response_envelope.v0_2",
        "subject": {
            "runtime": "phionyx-core",
            "version": "0.3.0",
            "producer": "claude-opus-4-7",
            "turn_index": 3,
            "timestamp_utc": "2026-05-19T22:00:00+00:00",
            "trace_id": "trace-integration-001",
        },
        "input": {"user_text": "integration test"},
        "path": [
            {"block": "input_safety_gate", "disposition": "admit", "reason": None},
            {"block": "audit_layer", "disposition": "record"},
        ],
        "output": {"redacted": False, "text": "ok"},
        "metrics": {"phi_total": 0.5, "input_tokens": 11, "output_tokens": 4},
        "reasoning": {
            "runtime_decision": "release",
            "decision_reason": "no policy violation",
            "runtime_policy_basis": ["input_safety_gate"],
        },
        "integrity": {
            "previous": "sha256:" + "0" * 64,
            "current": "sha256:" + "a" * 64,
            "signature": "demo-hmac:f00ba1",
            "canonical_json": True,
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
        },
    }


def test_export_emits_one_span_with_expected_attributes(
    monkeypatch, in_memory_tracer, sample_envelope
):
    """End-to-end: envelope in, one span out with the mapped attributes."""
    monkeypatch.setenv("PHIONYX_OTEL_EXPORT_ENVELOPES", "true")
    tracer, exporter = in_memory_tracer

    emitted = export_envelope(sample_envelope, tracer=tracer)
    assert emitted is True

    spans = exporter.get_finished_spans()
    assert len(spans) == 1

    span = spans[0]
    assert span.name == "phionyx.governed_response.v0_2"

    attrs = dict(span.attributes or {})
    # Standard
    assert attrs[sem.GEN_AI_SYSTEM] == "phionyx-core"
    assert attrs[sem.GEN_AI_REQUEST_MODEL] == "claude-opus-4-7"
    assert attrs[sem.GEN_AI_RESPONSE_ID] == "sha256:" + "a" * 64
    assert attrs[sem.GEN_AI_USAGE_INPUT_TOKENS] == 11
    assert attrs[sem.GEN_AI_USAGE_OUTPUT_TOKENS] == 4
    # Phionyx
    assert attrs[sem.PHIONYX_TRACE_ID] == "trace-integration-001"
    assert attrs[sem.PHIONYX_TURN_INDEX] == 3
    assert attrs[sem.PHIONYX_DECISION] == "release"
    assert attrs[sem.PHIONYX_PATH_BLOCKS] == "input_safety_gate,audit_layer"
    # MCP
    assert attrs[sem.PHIONYX_MCP_TOOL_DESCRIPTOR_HASH] == "sha256:" + "b" * 64
    assert attrs[sem.PHIONYX_MCP_DESCRIPTOR_CHANGE_DETECTED] is False


def test_export_emits_events_for_each_path_step(
    monkeypatch, in_memory_tracer, sample_envelope
):
    monkeypatch.setenv("PHIONYX_OTEL_EXPORT_ENVELOPES", "true")
    tracer, exporter = in_memory_tracer

    export_envelope(sample_envelope, tracer=tracer)

    span = exporter.get_finished_spans()[0]
    block_step_events = [
        e for e in span.events if e.name == sem.EVENT_PIPELINE_BLOCK_STEP
    ]
    assert len(block_step_events) == 2
    assert dict(block_step_events[0].attributes)["block"] == "input_safety_gate"
    assert dict(block_step_events[1].attributes)["block"] == "audit_layer"

    mcp_events = [e for e in span.events if e.name == sem.EVENT_MCP_TOOL_CALL]
    assert len(mcp_events) == 1


def test_export_skipped_when_opt_in_off(
    monkeypatch, in_memory_tracer, sample_envelope
):
    monkeypatch.delenv("PHIONYX_OTEL_EXPORT_ENVELOPES", raising=False)
    tracer, exporter = in_memory_tracer

    emitted = export_envelope(sample_envelope, tracer=tracer)
    assert emitted is False
    assert exporter.get_finished_spans() == ()


def test_export_force_bypasses_opt_in(
    monkeypatch, in_memory_tracer, sample_envelope
):
    """force=True should emit even when the env var is off (for tests)."""
    monkeypatch.delenv("PHIONYX_OTEL_EXPORT_ENVELOPES", raising=False)
    tracer, exporter = in_memory_tracer

    emitted = export_envelope(sample_envelope, tracer=tracer, force=True)
    assert emitted is True
    assert len(exporter.get_finished_spans()) == 1
