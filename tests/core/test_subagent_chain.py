"""
Unit tests for SubagentChainV0 — Phionyx Feature F5 (v0.6.0 W1.2)
==================================================================

Mind-loop stages: Act + Reflect.
AGI label: infrastructure — capability expansion for governance / audit.

Coverage:
    - Role invariants (root / child / leaf) — positive + negative
    - chain_depth bounds
    - String-length bounds on agent_id and parent_agent_id
    - compute_handoff_signing_body canonicalisation: byte-identical
      output, deterministic key order, ASCII-safe, no whitespace
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from phionyx_core.contracts.envelopes import (
    SubagentChainV0,
    compute_handoff_signing_body,
)


# ---------------------------------------------------------------------------
# Root role
# ---------------------------------------------------------------------------


class TestRoot:
    """role='root' invariants."""

    def test_minimal_root_valid(self):
        block = SubagentChainV0(
            agent_id="researcher",
            role="root",
            chain_depth=0,
            protocol="phionyx_native",
            parent_envelope_hash=None,
            handoff_signature=None,
            handoff_timestamp_utc=None,
        )
        assert block.role == "root"
        assert block.chain_depth == 0
        assert block.parent_envelope_hash is None
        assert block.handoff_signature is None
        assert block.handoff_timestamp_utc is None
        assert block.child_agent_ids == []
        assert block.protocol_data == {}

    def test_root_with_child_agent_ids_valid(self):
        block = SubagentChainV0(
            agent_id="researcher",
            role="root",
            chain_depth=0,
            protocol="langgraph_subgraph",
            parent_envelope_hash=None,
            handoff_signature=None,
            handoff_timestamp_utc=None,
            child_agent_ids=["writer", "fact_checker"],
        )
        assert block.child_agent_ids == ["writer", "fact_checker"]

    @pytest.mark.parametrize("bad_depth", [1, 2, 42])
    def test_root_with_non_zero_depth_rejected(self, bad_depth):
        with pytest.raises(ValidationError, match="chain_depth=0"):
            SubagentChainV0(
                agent_id="researcher",
                role="root",
                chain_depth=bad_depth,
                protocol="phionyx_native",
                parent_envelope_hash=None,
                handoff_signature=None,
                handoff_timestamp_utc=None,
            )

    @pytest.mark.parametrize(
        "field,value",
        [
            ("parent_envelope_hash", "sha256:deadbeef"),
            ("parent_agent_id", "previous_agent"),
            ("handoff_signature", "demo-hmac:00"),
            ("handoff_timestamp_utc", "2026-05-25T10:00:00Z"),
        ],
    )
    def test_root_with_any_parent_field_rejected(self, field, value):
        kwargs = dict(
            agent_id="researcher",
            role="root",
            chain_depth=0,
            protocol="phionyx_native",
            parent_envelope_hash=None,
            handoff_signature=None,
            handoff_timestamp_utc=None,
        )
        kwargs[field] = value
        with pytest.raises(ValidationError, match="role='root' requires"):
            SubagentChainV0(**kwargs)


# ---------------------------------------------------------------------------
# Child role
# ---------------------------------------------------------------------------


class TestChild:
    """role='child' invariants."""

    def test_minimal_child_valid(self):
        block = SubagentChainV0(
            agent_id="writer",
            role="child",
            chain_depth=1,
            protocol="langgraph_subgraph",
            parent_envelope_hash="sha256:a1b2c3d4",
            parent_agent_id="researcher",
            child_agent_ids=["editor"],
            handoff_signature="demo-hmac:c0ffee",
            handoff_timestamp_utc="2026-05-25T10:00:00Z",
        )
        assert block.role == "child"
        assert block.chain_depth == 1
        assert block.parent_envelope_hash == "sha256:a1b2c3d4"
        assert block.child_agent_ids == ["editor"]

    def test_child_with_zero_depth_rejected(self):
        with pytest.raises(ValidationError, match="chain_depth>=1"):
            SubagentChainV0(
                agent_id="writer",
                role="child",
                chain_depth=0,
                protocol="langgraph_subgraph",
                parent_envelope_hash="sha256:a1b2c3d4",
                handoff_signature="demo-hmac:c0ffee",
                handoff_timestamp_utc="2026-05-25T10:00:00Z",
            )

    @pytest.mark.parametrize(
        "field",
        ["parent_envelope_hash", "handoff_signature", "handoff_timestamp_utc"],
    )
    def test_child_missing_required_parent_field_rejected(self, field):
        kwargs = dict(
            agent_id="writer",
            role="child",
            chain_depth=1,
            protocol="langgraph_subgraph",
            parent_envelope_hash="sha256:a1b2c3d4",
            handoff_signature="demo-hmac:c0ffee",
            handoff_timestamp_utc="2026-05-25T10:00:00Z",
        )
        kwargs[field] = None
        with pytest.raises(ValidationError, match=f"requires {field}"):
            SubagentChainV0(**kwargs)

    def test_child_with_empty_string_parent_hash_rejected(self):
        with pytest.raises(ValidationError, match="parent_envelope_hash"):
            SubagentChainV0(
                agent_id="writer",
                role="child",
                chain_depth=1,
                protocol="langgraph_subgraph",
                parent_envelope_hash="",
                handoff_signature="demo-hmac:c0ffee",
                handoff_timestamp_utc="2026-05-25T10:00:00Z",
            )

    def test_child_can_fan_out_to_multiple_children(self):
        block = SubagentChainV0(
            agent_id="dispatcher",
            role="child",
            chain_depth=1,
            protocol="langgraph_subgraph",
            parent_envelope_hash="sha256:a1b2c3d4",
            handoff_signature="demo-hmac:00",
            handoff_timestamp_utc="2026-05-25T10:00:00Z",
            child_agent_ids=["worker_a", "worker_b", "worker_c"],
        )
        assert len(block.child_agent_ids) == 3


# ---------------------------------------------------------------------------
# Leaf role
# ---------------------------------------------------------------------------


class TestLeaf:
    """role='leaf' invariants."""

    def test_minimal_leaf_valid(self):
        block = SubagentChainV0(
            agent_id="editor",
            role="leaf",
            chain_depth=2,
            protocol="langgraph_subgraph",
            parent_envelope_hash="sha256:7c8e9d0a",
            handoff_signature="demo-hmac:01",
            handoff_timestamp_utc="2026-05-25T10:00:30Z",
        )
        assert block.role == "leaf"
        assert block.child_agent_ids == []

    def test_leaf_with_child_agent_ids_rejected(self):
        with pytest.raises(ValidationError, match="role='leaf' requires child_agent_ids is empty"):
            SubagentChainV0(
                agent_id="editor",
                role="leaf",
                chain_depth=2,
                protocol="langgraph_subgraph",
                parent_envelope_hash="sha256:7c8e9d0a",
                handoff_signature="demo-hmac:01",
                handoff_timestamp_utc="2026-05-25T10:00:30Z",
                child_agent_ids=["unexpected_child"],
            )


# ---------------------------------------------------------------------------
# Field constraints
# ---------------------------------------------------------------------------


class TestFieldConstraints:
    def test_agent_id_min_length(self):
        with pytest.raises(ValidationError, match="agent_id"):
            SubagentChainV0(
                agent_id="",
                role="root",
                chain_depth=0,
                protocol="phionyx_native",
                parent_envelope_hash=None,
                handoff_signature=None,
                handoff_timestamp_utc=None,
            )

    def test_agent_id_max_length(self):
        with pytest.raises(ValidationError, match="agent_id"):
            SubagentChainV0(
                agent_id="x" * 257,
                role="root",
                chain_depth=0,
                protocol="phionyx_native",
                parent_envelope_hash=None,
                handoff_signature=None,
                handoff_timestamp_utc=None,
            )

    def test_invalid_protocol_rejected(self):
        with pytest.raises(ValidationError, match="protocol"):
            SubagentChainV0(
                agent_id="x",
                role="root",
                chain_depth=0,
                protocol="invented_protocol",  # type: ignore[arg-type]
                parent_envelope_hash=None,
                handoff_signature=None,
                handoff_timestamp_utc=None,
            )

    def test_negative_chain_depth_rejected(self):
        with pytest.raises(ValidationError):
            SubagentChainV0(
                agent_id="x",
                role="root",
                chain_depth=-1,
                protocol="phionyx_native",
                parent_envelope_hash=None,
                handoff_signature=None,
                handoff_timestamp_utc=None,
            )

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError, match="Extra inputs"):
            SubagentChainV0(
                agent_id="x",
                role="root",
                chain_depth=0,
                protocol="phionyx_native",
                parent_envelope_hash=None,
                handoff_signature=None,
                handoff_timestamp_utc=None,
                unknown_field="rejected",  # type: ignore[call-arg]
            )

    def test_protocol_data_accepts_open_object(self):
        block = SubagentChainV0(
            agent_id="x",
            role="root",
            chain_depth=0,
            protocol="a2a",
            parent_envelope_hash=None,
            handoff_signature=None,
            handoff_timestamp_utc=None,
            protocol_data={"a2a_task_id": "task_123", "custom_a2a_metric": 0.42},
        )
        assert block.protocol_data["a2a_task_id"] == "task_123"
        assert block.protocol_data["custom_a2a_metric"] == 0.42


# ---------------------------------------------------------------------------
# compute_handoff_signing_body
# ---------------------------------------------------------------------------


class TestHandoffSigningBody:
    """RFC §2.4: canonical-JSON encoding for handoff signature."""

    BASE_KWARGS = dict(
        parent_envelope_hash="sha256:a1b2c3d4",
        parent_agent_id="researcher",
        child_agent_id="writer",
        child_protocol="langgraph_subgraph",
        handoff_timestamp_utc="2026-05-25T10:00:00Z",
    )

    def test_deterministic_byte_output(self):
        """Same inputs → byte-identical output (signing precondition)."""
        a = compute_handoff_signing_body(**self.BASE_KWARGS)
        b = compute_handoff_signing_body(**self.BASE_KWARGS)
        assert a == b
        assert isinstance(a, bytes)

    def test_keys_alphabetical_order(self):
        """sort_keys=True must emit alphabetical key order."""
        body = compute_handoff_signing_body(**self.BASE_KWARGS)
        decoded = json.loads(body)
        assert list(decoded.keys()) == [
            "child_agent_id",
            "child_protocol",
            "handoff_timestamp_utc",
            "parent_agent_id",
            "parent_envelope_hash",
        ]

    def test_no_whitespace(self):
        """separators=(',',':') means no spaces in the body."""
        body = compute_handoff_signing_body(**self.BASE_KWARGS).decode("utf-8")
        assert ", " not in body
        assert ": " not in body
        assert " {" not in body

    def test_ascii_safe(self):
        """ensure_ascii=True means non-ASCII becomes \\uXXXX escapes."""
        body = compute_handoff_signing_body(
            **{**self.BASE_KWARGS, "parent_agent_id": "agent_ş"}
        ).decode("utf-8")
        # Body MUST be pure ASCII after encoding.
        assert all(ord(c) < 128 for c in body)
        # Escape for ş (U+015F) must appear.
        assert "\\u015f" in body

    def test_different_inputs_different_output(self):
        """Different parent_envelope_hash → different bytes."""
        a = compute_handoff_signing_body(**self.BASE_KWARGS)
        kwargs2 = dict(self.BASE_KWARGS)
        kwargs2["parent_envelope_hash"] = "sha256:0000beef"
        b = compute_handoff_signing_body(**kwargs2)
        assert a != b

    def test_body_contains_all_five_fields(self):
        """The signed body must commit to all five fields the RFC names."""
        body = compute_handoff_signing_body(**self.BASE_KWARGS).decode("utf-8")
        decoded = json.loads(body)
        assert decoded == {
            "child_agent_id": "writer",
            "child_protocol": "langgraph_subgraph",
            "handoff_timestamp_utc": "2026-05-25T10:00:00Z",
            "parent_agent_id": "researcher",
            "parent_envelope_hash": "sha256:a1b2c3d4",
        }
