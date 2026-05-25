"""
Multi-Agent Subagent Chain Block (RGE v0.2 §2.2.3, active v0.1) — Phionyx Feature F5
=====================================================================================

Active specification of the ``subagent_chain`` block reserved in
Reasoned Governance Envelope v0.2 §2.2.3 as ``reserved-for-v0.6.0-f5``.

This module implements the JSON-Schema-defined shape published at
``examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.schema.json``.
The schema is the canonical wire shape; this Pydantic model is the
runtime helper used by Phionyx-instrumented producers (LangGraph
supervisor, future A2A adapter, future AGNTCY/ACP adapter, etc.).

Mind-loop stages affected: Act (delegation handoff) + Reflect
(cross-agent evidence reconstruction). AGI label: infrastructure —
governance / audit capability expansion, NOT cognitive progress.

References:
    - examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.md   (RFC)
    - examples/envelopes/rge_v0_2/rge_v0_2.md §2.2.3                  (predecessor block)
    - tools/phionyx_langchain_langgraph/.../langgraph_handler.py     (v0.5.0 supervisor adapter, W1.3 will populate this block)
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


SubagentChainProtocol = Literal[
    "a2a",
    "agntcy",
    "phionyx_native",
    "langgraph_subgraph",
    "crewai",
    "autogen",
]

SubagentChainRole = Literal["root", "child", "leaf"]


class SubagentChainV0(BaseModel):
    """Per-turn multi-agent handoff evidence carried inside an RGE envelope.

    See ``examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.md``
    for the full specification. This Pydantic model enforces the same
    if/then invariants the JSON Schema enforces; producers may use either
    surface (model OR schema) — both are bit-compatible.

    Invariants enforced by ``_validate_role_invariants``:
        1. ``role == "root"`` ⇒ ``chain_depth == 0`` AND all parent
           fields (``parent_envelope_hash``, ``parent_agent_id``,
           ``handoff_signature``, ``handoff_timestamp_utc``) are ``None``.
        2. ``role in {"child", "leaf"}`` ⇒ ``chain_depth >= 1`` AND
           the three required-for-non-root parent fields are non-None
           strings.
        3. ``role == "leaf"`` ⇒ ``child_agent_ids`` is empty.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    status: Literal["active"] = Field(
        default="active",
        description="v0.1 envelopes MUST set 'active'. RGE v0.2 reserved value 'reserved-for-v0.6.0-f5' is migrated to 'active' upon F5 adoption.",
    )
    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Stable identifier of THIS agent (LangGraph node / A2A agent-card URI fragment / AGNTCY DID).",
    )
    role: SubagentChainRole = Field(
        ...,
        description="Position in the chain for this turn.",
    )
    chain_depth: int = Field(
        ...,
        ge=0,
        description="root MUST have depth=0; every child increments. Bounded recommended 16.",
    )
    protocol: SubagentChainProtocol = Field(
        ...,
        description="Inter-agent protocol identifier.",
    )
    parent_envelope_hash: str | None = Field(
        ...,
        description="Parent's integrity.current, copied verbatim. NULL when role=root.",
    )
    handoff_signature: str | None = Field(
        ...,
        description="Signed handoff payload from the parent. NULL when role=root. Format ed25519:<hex> (Core) or demo-hmac:<hex> (launch wrapper).",
    )
    handoff_timestamp_utc: str | None = Field(
        ...,
        description="ISO-8601 UTC timestamp of parent's emission. NULL when role=root.",
    )
    parent_agent_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="Optional. The parent's agent_id. NULL when role=root.",
    )
    child_agent_ids: list[str] = Field(
        default_factory=list,
        description="For non-leaf nodes, the agent_id of each child this agent handed off to during this turn. Empty when role=leaf. Fan-out allowed.",
    )
    protocol_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Protocol-specific extension. Reserved keys: depth_exceeded, replay_window_seconds_used, a2a_task_id, agntcy_acp_envelope_id, langgraph_thread_id, crewai_crew_id, autogen_groupchat_id.",
    )

    @model_validator(mode="after")
    def _validate_role_invariants(self) -> "SubagentChainV0":
        if self.role == "root":
            if self.chain_depth != 0:
                raise ValueError(
                    f"role='root' requires chain_depth=0, got {self.chain_depth}"
                )
            null_required = {
                "parent_envelope_hash": self.parent_envelope_hash,
                "parent_agent_id": self.parent_agent_id,
                "handoff_signature": self.handoff_signature,
                "handoff_timestamp_utc": self.handoff_timestamp_utc,
            }
            for field_name, value in null_required.items():
                if value is not None:
                    raise ValueError(
                        f"role='root' requires {field_name} is None, got {value!r}"
                    )
        else:
            if self.chain_depth < 1:
                raise ValueError(
                    f"role='{self.role}' requires chain_depth>=1, got {self.chain_depth}"
                )
            non_null_required = {
                "parent_envelope_hash": self.parent_envelope_hash,
                "handoff_signature": self.handoff_signature,
                "handoff_timestamp_utc": self.handoff_timestamp_utc,
            }
            for field_name, value in non_null_required.items():
                if not isinstance(value, str) or not value:
                    raise ValueError(
                        f"role='{self.role}' requires {field_name} is a non-empty string, got {value!r}"
                    )

        if self.role == "leaf" and self.child_agent_ids:
            raise ValueError(
                f"role='leaf' requires child_agent_ids is empty, got {self.child_agent_ids!r}"
            )

        return self


def compute_handoff_signing_body(
    *,
    parent_envelope_hash: str,
    parent_agent_id: str,
    child_agent_id: str,
    child_protocol: str,
    handoff_timestamp_utc: str,
) -> bytes:
    """Return the canonical-JSON byte sequence to sign for ``handoff_signature``.

    Per the v0.1 RFC §2.4 the signed body is the canonical-JSON encoding
    (``sort_keys=True``, no whitespace, ASCII-safe) of a five-field
    object. Two compliant runtimes that produce the same five inputs
    MUST produce byte-identical signing bodies.

    Args:
        parent_envelope_hash: Parent envelope's ``integrity.current``.
        parent_agent_id:      Parent's ``agent_id``.
        child_agent_id:       This agent's ``agent_id`` (the child).
        child_protocol:       This agent's ``protocol`` value (the child).
        handoff_timestamp_utc: ISO-8601 timestamp from the parent's emission.

    Returns:
        UTF-8 encoded canonical-JSON bytes ready for signing.
    """
    body = {
        "child_agent_id": child_agent_id,
        "child_protocol": child_protocol,
        "handoff_timestamp_utc": handoff_timestamp_utc,
        "parent_agent_id": parent_agent_id,
        "parent_envelope_hash": parent_envelope_hash,
    }
    return json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


__all__ = [
    "SubagentChainV0",
    "SubagentChainProtocol",
    "SubagentChainRole",
    "compute_handoff_signing_body",
]
