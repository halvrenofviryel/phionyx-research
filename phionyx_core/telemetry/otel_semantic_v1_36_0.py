"""OpenTelemetry GenAI semantic conventions — frozen at v1.36.0.

This module captures the attribute names from the OpenTelemetry **GenAI
semantic conventions** as of v1.36.0 (status: Development per
https://opentelemetry.io/docs/specs/semconv/gen-ai, 2026-05-19).

Why a frozen module
-------------------

The GenAI semantic conventions are still in **Development** status. Spec
revisions can rename, deprecate, or restructure attributes. Phionyx pins
the exporter to a specific spec version so users emitting spans today
won't silently break when the spec evolves.

To support a newer spec version, add a sibling module
(`otel_semantic_v1_37_0.py`, etc.) and update the resolver in
``otel_export._resolve_semantic_module``. The default pinned version
bumps in Phionyx minor releases per
``docs/conventions/otel_semantic_bump_policy.md``.

References
----------
- OTel GenAI semantic conventions:
  https://opentelemetry.io/docs/specs/semconv/gen-ai/
- This module pinned: v1.36.0 (verified 2026-05-19)
"""
from __future__ import annotations

# ─── Identification ──────────────────────────────────────────────────

SEMANTIC_VERSION = "v1.36.0"
SPEC_STATUS = "Development"
SPEC_URL = "https://opentelemetry.io/docs/specs/semconv/gen-ai/"

# ─── Standard OTel GenAI attributes (vendor-portable) ────────────────
# Source: spec section "GenAI Attributes" at v1.36.0.

# Identification
GEN_AI_SYSTEM = "gen_ai.system"
"""The Generative AI product / system. RGE: envelope.subject.runtime."""

GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
"""The name of the GenAI model the request is targeting. RGE: envelope.subject.producer."""

GEN_AI_RESPONSE_ID = "gen_ai.response.id"
"""Unique identifier for the completion. RGE: envelope.integrity.current."""

GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
"""Name of the model that produced the response. Optional fallback to request.model."""

# Operation / usage
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
"""Type of GenAI operation: chat, text_completion, embeddings, etc."""

GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
"""Number of input tokens used by the request."""

GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
"""Number of output tokens used by the response."""

# Response metadata
GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
"""Array of reasons the model stopped generating tokens."""

# ─── Phionyx-specific attributes (phionyx.* namespace) ──────────────
# These extend OTel GenAI with Phionyx governance evidence that has no
# direct standard counterpart. They are kept in a private namespace so
# vendors can filter or surface them explicitly.

# Trace + turn
PHIONYX_TRACE_ID = "phionyx.trace_id"
"""Phionyx session trace id (ADR-0006 shared trace contract)."""

PHIONYX_TURN_INDEX = "phionyx.turn_index"
"""Turn index within the trace. RGE: envelope.subject.turn_index."""

PHIONYX_RUNTIME_VERSION = "phionyx.runtime.version"
"""Producing runtime version. RGE: envelope.subject.version."""

# Decision + reasoning
PHIONYX_DECISION = "phionyx.decision"
"""Runtime decision verdict: release | block | defer | redact. RGE: envelope.reasoning.runtime_decision."""

PHIONYX_DECISION_REASON = "phionyx.decision_reason"
"""Human-readable rationale for the decision. RGE: envelope.reasoning.decision_reason."""

PHIONYX_POLICY_BASIS = "phionyx.policy_basis"
"""Comma-separated list of policy components consulted. RGE: envelope.reasoning.runtime_policy_basis."""

# Pipeline path
PHIONYX_PATH_BLOCKS = "phionyx.path.blocks"
"""Comma-separated list of pipeline blocks fired this turn. RGE: envelope.path[].block."""

PHIONYX_PATH_DISPOSITIONS = "phionyx.path.dispositions"
"""Comma-separated list of dispositions (admit/block/...) per block."""

# Integrity / audit chain
PHIONYX_INTEGRITY_PREVIOUS = "phionyx.integrity.previous"
"""Previous envelope's integrity.current. Chain link."""

PHIONYX_INTEGRITY_CURRENT = "phionyx.integrity.current"
"""This envelope's content hash."""

PHIONYX_INTEGRITY_SIGNATURE = "phionyx.integrity.signature"
"""Signature over integrity.current (Ed25519 in production)."""

# Schema + envelope identification
PHIONYX_ENVELOPE_SCHEMA = "phionyx.envelope.schema"
"""Envelope schema identifier. RGE: envelope.schema."""

# MCP tool audit (optional block — populated when envelope carries mcp_tool_audit)
PHIONYX_MCP_TOOL_DESCRIPTOR_HASH = "phionyx.mcp.tool_descriptor_hash"
PHIONYX_MCP_DESCRIPTOR_CHANGE_DETECTED = "phionyx.mcp.descriptor_change_detected"
PHIONYX_MCP_TOOL_PERMISSION_SCOPE = "phionyx.mcp.tool_permission_scope"
PHIONYX_MCP_TOOL_INPUT_HASH = "phionyx.mcp.tool_call_io_hash.input"
PHIONYX_MCP_TOOL_OUTPUT_HASH = "phionyx.mcp.tool_call_io_hash.output"
PHIONYX_MCP_USER_APPROVAL_STATE = "phionyx.mcp.user_approval_state.status"
PHIONYX_MCP_ANOMALY_FLAG = "phionyx.mcp.runtime_anomaly_flag.anomaly"
PHIONYX_MCP_ANOMALY_SEVERITY = "phionyx.mcp.runtime_anomaly_flag.severity"

# ─── Span event names ────────────────────────────────────────────────

EVENT_PIPELINE_BLOCK_STEP = "phionyx.pipeline.block_step"
"""Event emitted per pipeline block step. Attributes: block, disposition, reason."""

EVENT_MCP_TOOL_CALL = "phionyx.mcp.tool_call"
"""Event emitted when an mcp_tool_audit block is present."""

# ─── Span name template ──────────────────────────────────────────────

SPAN_NAME_TEMPLATE = "phionyx.governed_response.{schema_short}"
"""Span name format. schema_short = the last segment of envelope.schema, e.g. 'v0_2'."""

__all__ = [
    "SEMANTIC_VERSION",
    "SPEC_STATUS",
    "SPEC_URL",
    # OTel GenAI standard attrs
    "GEN_AI_SYSTEM",
    "GEN_AI_REQUEST_MODEL",
    "GEN_AI_RESPONSE_ID",
    "GEN_AI_RESPONSE_MODEL",
    "GEN_AI_OPERATION_NAME",
    "GEN_AI_USAGE_INPUT_TOKENS",
    "GEN_AI_USAGE_OUTPUT_TOKENS",
    "GEN_AI_RESPONSE_FINISH_REASONS",
    # Phionyx-specific
    "PHIONYX_TRACE_ID",
    "PHIONYX_TURN_INDEX",
    "PHIONYX_RUNTIME_VERSION",
    "PHIONYX_DECISION",
    "PHIONYX_DECISION_REASON",
    "PHIONYX_POLICY_BASIS",
    "PHIONYX_PATH_BLOCKS",
    "PHIONYX_PATH_DISPOSITIONS",
    "PHIONYX_INTEGRITY_PREVIOUS",
    "PHIONYX_INTEGRITY_CURRENT",
    "PHIONYX_INTEGRITY_SIGNATURE",
    "PHIONYX_ENVELOPE_SCHEMA",
    "PHIONYX_MCP_TOOL_DESCRIPTOR_HASH",
    "PHIONYX_MCP_DESCRIPTOR_CHANGE_DETECTED",
    "PHIONYX_MCP_TOOL_PERMISSION_SCOPE",
    "PHIONYX_MCP_TOOL_INPUT_HASH",
    "PHIONYX_MCP_TOOL_OUTPUT_HASH",
    "PHIONYX_MCP_USER_APPROVAL_STATE",
    "PHIONYX_MCP_ANOMALY_FLAG",
    "PHIONYX_MCP_ANOMALY_SEVERITY",
    # Event names
    "EVENT_PIPELINE_BLOCK_STEP",
    "EVENT_MCP_TOOL_CALL",
    # Span name
    "SPAN_NAME_TEMPLATE",
]
