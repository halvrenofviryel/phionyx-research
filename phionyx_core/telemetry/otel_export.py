"""OTel exporter: RGE envelope → OpenTelemetry GenAI span.

Maps a Reasoned Governance Envelope (RGE v0.1 / v0.2) to a single
OpenTelemetry span with attributes following the GenAI semantic
conventions (vendor-portable) plus a ``phionyx.*`` namespace for
governance-specific evidence that has no standard counterpart.

Status
------

The OTel GenAI conventions are at **Development** status. This exporter
pins the attribute names to a specific spec version (default
``v1.36.0``) so emitted spans don't silently break when the spec evolves.

Opt-in
------

Envelope export is **opt-in** via the env var
``PHIONYX_OTEL_EXPORT_ENVELOPES=true``. The defensive default is OFF —
users explicitly acknowledge they want experimental GenAI attributes.

Usage
-----

::

    from phionyx_core.telemetry import export_envelope

    envelope = ...  # a v0.1 / v0.2 RGE envelope dict
    export_envelope(envelope)         # emits one span, no-op if disabled

Or use the mapper directly to inspect what would be emitted::

    from phionyx_core.telemetry import EnvelopeToSpanMapper

    mapper = EnvelopeToSpanMapper()
    attrs = mapper.map_attributes(envelope)
    events = mapper.map_events(envelope)

Both APIs are read-only over the envelope.

Version pinning
---------------

::

    PHIONYX_OTEL_SEMANTIC_VERSION=v1.36.0   # default
    PHIONYX_OTEL_SEMANTIC_VERSION=v1.37.0   # requires future Phionyx release

If an unsupported version is requested, the exporter raises a clear
error at first call rather than emitting spans against the wrong spec.

See ``docs/conventions/otel_semantic_bump_policy.md`` for the bump policy.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from types import ModuleType
from typing import Any

logger = logging.getLogger(__name__)

# ─── Env var contract ────────────────────────────────────────────────

ENV_EXPORT_ENVELOPES = "PHIONYX_OTEL_EXPORT_ENVELOPES"
ENV_SEMANTIC_VERSION = "PHIONYX_OTEL_SEMANTIC_VERSION"

DEFAULT_SEMANTIC_VERSION = "v1.36.0"


def envelope_export_enabled() -> bool:
    """Return True if envelope→span emission is opted in via env var."""
    return os.environ.get(ENV_EXPORT_ENVELOPES, "false").lower() in ("1", "true", "yes")


# ─── Semantic module resolver ────────────────────────────────────────


def _resolve_semantic_module(version: str | None = None) -> ModuleType:
    """Return the semantic-conventions module for ``version``.

    Currently only v1.36.0 is supported. Adding a new version means
    creating ``otel_semantic_v1_<minor>_0.py`` next to this file and
    extending the dispatch table.
    """
    requested = version or os.environ.get(ENV_SEMANTIC_VERSION, DEFAULT_SEMANTIC_VERSION)
    if requested == "v1.36.0":
        from . import otel_semantic_v1_36_0 as mod

        return mod
    raise ValueError(
        f"Phionyx OTel exporter does not yet support semantic version {requested!r}. "
        f"Supported: v1.36.0. To add a new pinned version, drop "
        f"otel_semantic_v1_<minor>_0.py next to otel_export.py and extend "
        f"_resolve_semantic_module. See docs/conventions/otel_semantic_bump_policy.md."
    )


# ─── Mapping logic ───────────────────────────────────────────────────


@dataclass
class EnvelopeToSpanMapper:
    """Pure mapping from RGE envelope to OTel span attributes + events.

    Stateless. Construct once and call as many times as needed. The
    mapper is read-only over the envelope; it never mutates the input.

    Attributes
    ----------
    semantic_version:
        Optional override for the pinned spec version. Defaults to
        ``PHIONYX_OTEL_SEMANTIC_VERSION`` env var or ``v1.36.0``.
    """

    semantic_version: str | None = None

    def _sem(self) -> ModuleType:
        return _resolve_semantic_module(self.semantic_version)

    # ─── Span name ──

    def span_name(self, envelope: dict[str, Any]) -> str:
        sem = self._sem()
        schema = envelope.get("schema", "phionyx.governed_response_envelope.v0_2")
        # Last segment after the final dot: "v0_2", "v0_1", etc.
        schema_short = schema.rsplit(".", 1)[-1] if "." in schema else schema
        return sem.SPAN_NAME_TEMPLATE.format(schema_short=schema_short)

    # ─── Attributes ──

    def map_attributes(self, envelope: dict[str, Any]) -> dict[str, Any]:
        """Map envelope → flat attribute dict suitable for span.set_attributes."""
        sem = self._sem()
        attrs: dict[str, Any] = {}

        subject = envelope.get("subject", {}) or {}
        reasoning = envelope.get("reasoning", {}) or {}
        path = envelope.get("path", []) or []
        integrity = envelope.get("integrity", {}) or {}
        metrics = envelope.get("metrics", {}) or {}
        mcp_tool_audit = envelope.get("mcp_tool_audit")  # optional

        # ── Standard OTel GenAI attributes (vendor-portable) ──
        if "runtime" in subject:
            attrs[sem.GEN_AI_SYSTEM] = subject["runtime"]
        if "producer" in subject:
            attrs[sem.GEN_AI_REQUEST_MODEL] = subject["producer"]
            # Default response.model to request.model unless the producer
            # surfaces a different value in metrics.
            attrs[sem.GEN_AI_RESPONSE_MODEL] = subject["producer"]
        if "current" in integrity:
            attrs[sem.GEN_AI_RESPONSE_ID] = integrity["current"]

        # Operation name — Phionyx envelopes describe a single
        # governance-bracketed completion. "chat" is the closest fit
        # for the GenAI taxonomy; document this if a richer mapping
        # becomes available in a future semantic version.
        attrs[sem.GEN_AI_OPERATION_NAME] = "chat"

        # Optional token counts surface from envelope.metrics if present.
        # RGE doesn't mandate these fields, so emit only when populated.
        if isinstance(metrics, dict):
            if "input_tokens" in metrics:
                attrs[sem.GEN_AI_USAGE_INPUT_TOKENS] = metrics["input_tokens"]
            if "output_tokens" in metrics:
                attrs[sem.GEN_AI_USAGE_OUTPUT_TOKENS] = metrics["output_tokens"]

        # ── Phionyx-specific attrs ──
        if "trace_id" in subject:
            attrs[sem.PHIONYX_TRACE_ID] = subject["trace_id"]
        if "turn_index" in subject:
            attrs[sem.PHIONYX_TURN_INDEX] = subject["turn_index"]
        if "version" in subject:
            attrs[sem.PHIONYX_RUNTIME_VERSION] = subject["version"]
        if "schema" in envelope:
            attrs[sem.PHIONYX_ENVELOPE_SCHEMA] = envelope["schema"]

        if "runtime_decision" in reasoning:
            attrs[sem.PHIONYX_DECISION] = reasoning["runtime_decision"]
        if "decision_reason" in reasoning:
            attrs[sem.PHIONYX_DECISION_REASON] = reasoning["decision_reason"]
        if "runtime_policy_basis" in reasoning:
            attrs[sem.PHIONYX_POLICY_BASIS] = ",".join(
                str(b) for b in (reasoning["runtime_policy_basis"] or [])
            )

        if path:
            attrs[sem.PHIONYX_PATH_BLOCKS] = ",".join(
                str(step.get("block", "")) for step in path
            )
            attrs[sem.PHIONYX_PATH_DISPOSITIONS] = ",".join(
                str(step.get("disposition", "")) for step in path
            )

        if "previous" in integrity:
            attrs[sem.PHIONYX_INTEGRITY_PREVIOUS] = integrity["previous"]
        if "current" in integrity:
            attrs[sem.PHIONYX_INTEGRITY_CURRENT] = integrity["current"]
        if "signature" in integrity:
            attrs[sem.PHIONYX_INTEGRITY_SIGNATURE] = integrity["signature"]

        # ── mcp_tool_audit (optional) ──
        if isinstance(mcp_tool_audit, dict):
            if "tool_descriptor_hash" in mcp_tool_audit:
                attrs[sem.PHIONYX_MCP_TOOL_DESCRIPTOR_HASH] = mcp_tool_audit[
                    "tool_descriptor_hash"
                ]
            if "descriptor_change_detected" in mcp_tool_audit:
                attrs[sem.PHIONYX_MCP_DESCRIPTOR_CHANGE_DETECTED] = mcp_tool_audit[
                    "descriptor_change_detected"
                ]
            scope = mcp_tool_audit.get("tool_permission_scope")
            if isinstance(scope, list):
                attrs[sem.PHIONYX_MCP_TOOL_PERMISSION_SCOPE] = ",".join(
                    str(s) for s in scope
                )
            io = mcp_tool_audit.get("tool_call_io_hash")
            if isinstance(io, dict):
                if "input_hash" in io:
                    attrs[sem.PHIONYX_MCP_TOOL_INPUT_HASH] = io["input_hash"]
                if "output_hash" in io:
                    attrs[sem.PHIONYX_MCP_TOOL_OUTPUT_HASH] = io["output_hash"]
            approval = mcp_tool_audit.get("user_approval_state")
            if isinstance(approval, dict) and "status" in approval:
                attrs[sem.PHIONYX_MCP_USER_APPROVAL_STATE] = approval["status"]
            anomaly = mcp_tool_audit.get("runtime_anomaly_flag")
            if isinstance(anomaly, dict):
                if "anomaly" in anomaly:
                    attrs[sem.PHIONYX_MCP_ANOMALY_FLAG] = anomaly["anomaly"]
                if "severity" in anomaly:
                    attrs[sem.PHIONYX_MCP_ANOMALY_SEVERITY] = anomaly["severity"]

        # Drop any None values — OTel rejects them per the SDK contract.
        return {k: v for k, v in attrs.items() if v is not None}

    # ─── Events ──

    def map_events(self, envelope: dict[str, Any]) -> list[dict[str, Any]]:
        """Map envelope → list of span events (name + attributes).

        Each pipeline ``path`` step becomes one event; when ``mcp_tool_audit``
        is populated, an additional event surfaces the tool-call summary.
        """
        sem = self._sem()
        events: list[dict[str, Any]] = []

        for step in envelope.get("path", []) or []:
            attrs = {
                "block": step.get("block"),
                "disposition": step.get("disposition"),
            }
            if step.get("reason") is not None:
                attrs["reason"] = step["reason"]
            events.append(
                {
                    "name": sem.EVENT_PIPELINE_BLOCK_STEP,
                    "attributes": {k: v for k, v in attrs.items() if v is not None},
                }
            )

        mcp = envelope.get("mcp_tool_audit")
        if isinstance(mcp, dict):
            attrs = {
                "status": mcp.get("status"),
                "tool_descriptor_hash": mcp.get("tool_descriptor_hash"),
                "descriptor_change_detected": mcp.get("descriptor_change_detected"),
            }
            events.append(
                {
                    "name": sem.EVENT_MCP_TOOL_CALL,
                    "attributes": {k: v for k, v in attrs.items() if v is not None},
                }
            )

        return events


# ─── Public emission API ─────────────────────────────────────────────


def export_envelope(
    envelope: dict[str, Any],
    *,
    tracer: Any = None,
    force: bool = False,
) -> bool:
    """Emit one OTel span for ``envelope``.

    Args:
        envelope: A v0.1 or v0.2 RGE envelope dict.
        tracer: Optional pre-built OTel tracer. If omitted, the function
            obtains one via ``phionyx_core.telemetry.get_tracer``.
        force: If True, bypass the ``PHIONYX_OTEL_EXPORT_ENVELOPES``
            opt-in check. Useful for tests; not recommended in
            production code paths.

    Returns:
        True if a span was emitted, False if export was skipped (either
        because the opt-in env var is off or the OTel SDK is unavailable).

    Notes:
        - Function is a **no-op** when ``PHIONYX_OTEL_EXPORT_ENVELOPES``
          is not ``true`` (defensive default).
        - Function is a **no-op** when the OpenTelemetry SDK isn't
          importable. This keeps phionyx-core dependency-flexible.
        - Errors during span emission are logged at WARNING level but
          never raised — observability MUST NOT crash the governance path.
    """
    if not force and not envelope_export_enabled():
        return False

    # Lazy import so phionyx-core doesn't hard-require the OTel SDK.
    try:
        from opentelemetry import trace as otel_trace
    except ImportError:
        logger.debug(
            "OpenTelemetry SDK not installed — envelope export is a no-op."
        )
        return False

    if tracer is None:
        try:
            from .opentelemetry_config import get_or_create_tracer

            tracer = get_or_create_tracer("phionyx.envelope_export")
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("Failed to acquire OTel tracer: %s", exc)
            return False

    if tracer is None:
        return False

    mapper = EnvelopeToSpanMapper()
    try:
        span_name = mapper.span_name(envelope)
        attrs = mapper.map_attributes(envelope)
        events = mapper.map_events(envelope)
    except Exception as exc:
        logger.warning("OTel envelope mapping failed: %s", exc)
        return False

    try:
        with tracer.start_as_current_span(span_name, attributes=attrs) as span:
            for event in events:
                span.add_event(event["name"], attributes=event.get("attributes") or {})
            # Mark the span SpanKind.INTERNAL by default (the spec
            # default). Backends that infer kind from gen_ai.* attrs
            # will still attribute it correctly.
            _ = otel_trace  # silence unused import; the SDK is used implicitly via tracer
        return True
    except Exception as exc:
        logger.warning("OTel span emission failed: %s", exc)
        return False


__all__ = [
    "ENV_EXPORT_ENVELOPES",
    "ENV_SEMANTIC_VERSION",
    "DEFAULT_SEMANTIC_VERSION",
    "EnvelopeToSpanMapper",
    "envelope_export_enabled",
    "export_envelope",
]
