"""Unit tests for phionyx_core.telemetry.otel_export.

Coverage:

    - span_name follows the SPAN_NAME_TEMPLATE
    - map_attributes emits OTel GenAI standard attrs from RGE subject
    - map_attributes emits phionyx.* attrs from envelope reasoning/integrity/path
    - mcp_tool_audit block surfaces under phionyx.mcp.* attrs
    - map_events emits one event per pipeline path step
    - None values are scrubbed (OTel SDK rejects None attribute values)
    - envelope_export_enabled() honors PHIONYX_OTEL_EXPORT_ENVELOPES env var
    - _resolve_semantic_module raises on unsupported version
    - export_envelope is a no-op when opt-in is off
    - export_envelope is a no-op when OTel SDK is unavailable

These are pure-Python tests — they do NOT require the OpenTelemetry SDK.
"""
from __future__ import annotations

import sys
from typing import Any

import pytest

from phionyx_core.telemetry import otel_export
from phionyx_core.telemetry import otel_semantic_v1_36_0 as sem
from phionyx_core.telemetry.otel_export import (
    EnvelopeToSpanMapper,
    envelope_export_enabled,
    export_envelope,
)


# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def minimal_envelope() -> dict[str, Any]:
    """Minimal v0.2 envelope — required keys only."""
    return {
        "schema": "phionyx.governed_response_envelope.v0_2",
        "subject": {
            "runtime": "phionyx-core",
            "version": "0.3.0",
            "producer": "claude-opus-4-7",
            "turn_index": 1,
            "timestamp_utc": "2026-05-19T22:00:00+00:00",
            "trace_id": "trace-test-001",
        },
        "input": {"user_text": "hello"},
        "path": [
            {"block": "input_safety_gate", "disposition": "admit", "reason": None},
            {"block": "audit_layer", "disposition": "record"},
        ],
        "output": {"redacted": False, "text": "hi"},
        "metrics": {"phi_total": 0.5},
        "integrity": {
            "previous": "sha256:" + "0" * 64,
            "current": "sha256:abc123",
            "signature": "demo-hmac:f00ba1",
            "canonical_json": True,
        },
    }


@pytest.fixture
def envelope_with_reasoning(minimal_envelope: dict[str, Any]) -> dict[str, Any]:
    minimal_envelope["reasoning"] = {
        "runtime_decision": "release",
        "decision_reason": "no policy violation",
        "runtime_policy_basis": ["input_safety_gate", "ethics_pre_response"],
    }
    return minimal_envelope


@pytest.fixture
def envelope_with_mcp(envelope_with_reasoning: dict[str, Any]) -> dict[str, Any]:
    envelope_with_reasoning["mcp_tool_audit"] = {
        "status": "active",
        "tool_descriptor_hash": "sha256:tooldescriptorhash",
        "descriptor_change_detected": False,
        "tool_permission_scope": ["read", "list"],
        "tool_call_io_hash": {
            "input_hash": "sha256:inputhash",
            "output_hash": "sha256:outputhash",
        },
        "user_approval_state": {"status": "approved"},
        "runtime_anomaly_flag": {"anomaly": False, "severity": "none"},
    }
    return envelope_with_reasoning


# ─── 1. Span name ────────────────────────────────────────────────────


def test_span_name_uses_schema_short_segment(minimal_envelope):
    mapper = EnvelopeToSpanMapper()
    assert mapper.span_name(minimal_envelope) == "phionyx.governed_response.v0_2"


def test_span_name_handles_v0_1_envelopes():
    mapper = EnvelopeToSpanMapper()
    name = mapper.span_name({"schema": "phionyx.governed_response_envelope.v0_1"})
    assert name == "phionyx.governed_response.v0_1"


def test_span_name_default_when_schema_missing():
    mapper = EnvelopeToSpanMapper()
    # Falls back to the v0_2 default per docstring.
    assert mapper.span_name({}) == "phionyx.governed_response.v0_2"


# ─── 2. Standard GenAI attributes ────────────────────────────────────


def test_standard_gen_ai_attrs_from_subject(minimal_envelope):
    attrs = EnvelopeToSpanMapper().map_attributes(minimal_envelope)
    assert attrs[sem.GEN_AI_SYSTEM] == "phionyx-core"
    assert attrs[sem.GEN_AI_REQUEST_MODEL] == "claude-opus-4-7"
    assert attrs[sem.GEN_AI_RESPONSE_MODEL] == "claude-opus-4-7"
    assert attrs[sem.GEN_AI_RESPONSE_ID] == "sha256:abc123"
    assert attrs[sem.GEN_AI_OPERATION_NAME] == "chat"


def test_token_counts_optional(minimal_envelope):
    attrs = EnvelopeToSpanMapper().map_attributes(minimal_envelope)
    assert sem.GEN_AI_USAGE_INPUT_TOKENS not in attrs
    assert sem.GEN_AI_USAGE_OUTPUT_TOKENS not in attrs


def test_token_counts_surface_when_present(minimal_envelope):
    minimal_envelope["metrics"]["input_tokens"] = 42
    minimal_envelope["metrics"]["output_tokens"] = 7
    attrs = EnvelopeToSpanMapper().map_attributes(minimal_envelope)
    assert attrs[sem.GEN_AI_USAGE_INPUT_TOKENS] == 42
    assert attrs[sem.GEN_AI_USAGE_OUTPUT_TOKENS] == 7


# ─── 3. Phionyx-specific attributes ──────────────────────────────────


def test_phionyx_subject_and_integrity_attrs(minimal_envelope):
    attrs = EnvelopeToSpanMapper().map_attributes(minimal_envelope)
    assert attrs[sem.PHIONYX_TRACE_ID] == "trace-test-001"
    assert attrs[sem.PHIONYX_TURN_INDEX] == 1
    assert attrs[sem.PHIONYX_RUNTIME_VERSION] == "0.3.0"
    assert attrs[sem.PHIONYX_ENVELOPE_SCHEMA] == "phionyx.governed_response_envelope.v0_2"
    assert attrs[sem.PHIONYX_INTEGRITY_PREVIOUS] == "sha256:" + "0" * 64
    assert attrs[sem.PHIONYX_INTEGRITY_CURRENT] == "sha256:abc123"
    assert attrs[sem.PHIONYX_INTEGRITY_SIGNATURE] == "demo-hmac:f00ba1"


def test_phionyx_path_blocks_joined(minimal_envelope):
    attrs = EnvelopeToSpanMapper().map_attributes(minimal_envelope)
    assert attrs[sem.PHIONYX_PATH_BLOCKS] == "input_safety_gate,audit_layer"
    assert attrs[sem.PHIONYX_PATH_DISPOSITIONS] == "admit,record"


def test_phionyx_decision_attrs(envelope_with_reasoning):
    attrs = EnvelopeToSpanMapper().map_attributes(envelope_with_reasoning)
    assert attrs[sem.PHIONYX_DECISION] == "release"
    assert attrs[sem.PHIONYX_DECISION_REASON] == "no policy violation"
    assert attrs[sem.PHIONYX_POLICY_BASIS] == "input_safety_gate,ethics_pre_response"


# ─── 4. mcp_tool_audit branch ────────────────────────────────────────


def test_mcp_tool_audit_attrs_present_when_block_populated(envelope_with_mcp):
    attrs = EnvelopeToSpanMapper().map_attributes(envelope_with_mcp)
    assert attrs[sem.PHIONYX_MCP_TOOL_DESCRIPTOR_HASH] == "sha256:tooldescriptorhash"
    assert attrs[sem.PHIONYX_MCP_DESCRIPTOR_CHANGE_DETECTED] is False
    assert attrs[sem.PHIONYX_MCP_TOOL_PERMISSION_SCOPE] == "read,list"
    assert attrs[sem.PHIONYX_MCP_TOOL_INPUT_HASH] == "sha256:inputhash"
    assert attrs[sem.PHIONYX_MCP_TOOL_OUTPUT_HASH] == "sha256:outputhash"
    assert attrs[sem.PHIONYX_MCP_USER_APPROVAL_STATE] == "approved"
    assert attrs[sem.PHIONYX_MCP_ANOMALY_FLAG] is False
    assert attrs[sem.PHIONYX_MCP_ANOMALY_SEVERITY] == "none"


def test_mcp_tool_audit_absent_when_no_block(minimal_envelope):
    attrs = EnvelopeToSpanMapper().map_attributes(minimal_envelope)
    for key in (
        sem.PHIONYX_MCP_TOOL_DESCRIPTOR_HASH,
        sem.PHIONYX_MCP_DESCRIPTOR_CHANGE_DETECTED,
        sem.PHIONYX_MCP_TOOL_PERMISSION_SCOPE,
    ):
        assert key not in attrs


# ─── 5. None scrubbing ───────────────────────────────────────────────


def test_none_values_scrubbed(minimal_envelope):
    """OTel SDK rejects None attribute values; mapper must drop them."""
    minimal_envelope["subject"].pop("trace_id")
    attrs = EnvelopeToSpanMapper().map_attributes(minimal_envelope)
    assert all(v is not None for v in attrs.values())
    assert sem.PHIONYX_TRACE_ID not in attrs


# ─── 6. Events ───────────────────────────────────────────────────────


def test_one_event_per_path_step(minimal_envelope):
    events = EnvelopeToSpanMapper().map_events(minimal_envelope)
    block_events = [e for e in events if e["name"] == sem.EVENT_PIPELINE_BLOCK_STEP]
    assert len(block_events) == 2
    assert block_events[0]["attributes"]["block"] == "input_safety_gate"
    assert block_events[0]["attributes"]["disposition"] == "admit"
    assert block_events[1]["attributes"]["block"] == "audit_layer"


def test_mcp_event_emitted_when_block_present(envelope_with_mcp):
    events = EnvelopeToSpanMapper().map_events(envelope_with_mcp)
    mcp_events = [e for e in events if e["name"] == sem.EVENT_MCP_TOOL_CALL]
    assert len(mcp_events) == 1
    assert mcp_events[0]["attributes"]["status"] == "active"
    assert mcp_events[0]["attributes"]["descriptor_change_detected"] is False


def test_no_mcp_event_when_no_block(minimal_envelope):
    events = EnvelopeToSpanMapper().map_events(minimal_envelope)
    mcp_events = [e for e in events if e["name"] == sem.EVENT_MCP_TOOL_CALL]
    assert mcp_events == []


# ─── 7. Opt-in env var ───────────────────────────────────────────────


def test_export_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PHIONYX_OTEL_EXPORT_ENVELOPES", raising=False)
    assert envelope_export_enabled() is False


def test_export_enabled_truthy_values(monkeypatch):
    for truthy in ("true", "1", "yes", "TRUE", "YeS"):
        monkeypatch.setenv("PHIONYX_OTEL_EXPORT_ENVELOPES", truthy)
        assert envelope_export_enabled() is True


def test_export_disabled_other_values(monkeypatch):
    for falsy in ("false", "0", "no", "off", ""):
        monkeypatch.setenv("PHIONYX_OTEL_EXPORT_ENVELOPES", falsy)
        assert envelope_export_enabled() is False


# ─── 8. Version pinning ──────────────────────────────────────────────


def test_default_version_is_v1_36_0():
    assert otel_export.DEFAULT_SEMANTIC_VERSION == "v1.36.0"
    assert sem.SEMANTIC_VERSION == "v1.36.0"


def test_unsupported_version_raises(monkeypatch):
    mapper = EnvelopeToSpanMapper(semantic_version="v1.99.0")
    with pytest.raises(ValueError, match="does not yet support semantic version"):
        mapper.span_name({"schema": "phionyx.governed_response_envelope.v0_2"})


# ─── 9. export_envelope no-op behaviour ──────────────────────────────


def test_export_envelope_noop_when_opt_in_off(monkeypatch, minimal_envelope):
    monkeypatch.delenv("PHIONYX_OTEL_EXPORT_ENVELOPES", raising=False)
    assert export_envelope(minimal_envelope) is False


def test_export_envelope_noop_when_otel_sdk_unavailable(
    monkeypatch, minimal_envelope
):
    """Even when opted in, missing OTel SDK results in a clean no-op."""
    monkeypatch.setenv("PHIONYX_OTEL_EXPORT_ENVELOPES", "true")
    # Hide the OTel package so the lazy import fails.
    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    monkeypatch.setitem(sys.modules, "opentelemetry.trace", None)
    assert export_envelope(minimal_envelope) is False
