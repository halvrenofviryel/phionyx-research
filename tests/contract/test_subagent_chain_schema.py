"""
SubagentChainV0 ↔ JSON Schema Contract Test
============================================

Purpose:
    The published JSON Schema at
    ``examples/envelopes/subagent_chain_v0_1/subagent_chain_v0_1.schema.json``
    is the canonical wire shape of the v0.1 ``subagent_chain`` block.

    The Pydantic model ``SubagentChainV0`` in
    ``phionyx_core/contracts/envelopes/subagent_chain.py`` is the
    runtime helper Phionyx-instrumented producers use.

    These two surfaces MUST agree:
        - Every instance valid under the model MUST validate against
          the schema.
        - Every instance the model rejects MUST also be rejected by
          the schema (and vice versa) for the role invariants.

    This test exercises both directions on a curated sample set.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from phionyx_core.contracts.envelopes import SubagentChainV0


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT
    / "examples"
    / "envelopes"
    / "subagent_chain_v0_1"
    / "subagent_chain_v0_1.schema.json"
)
MINIMAL_ENVELOPE_PATH = (
    REPO_ROOT
    / "examples"
    / "envelopes"
    / "subagent_chain_v0_1"
    / "subagent_chain_v0_1_minimal_envelope.json"
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def schema_validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


# ---------------------------------------------------------------------------
# Canonical positive fixtures: the published worked example
# ---------------------------------------------------------------------------


def test_published_minimal_envelope_blocks_validate(schema_validator):
    """All three subagent_chain blocks in the published 3-agent example
    must validate against the schema (sanity check that the example
    shipped to readers actually conforms to its own schema)."""
    envelopes = json.loads(MINIMAL_ENVELOPE_PATH.read_text())["envelopes"]
    assert len(envelopes) == 3, "minimal example should have 3 envelopes"

    for i, env in enumerate(envelopes):
        block = env["subagent_chain"]
        errors = list(schema_validator.iter_errors(block))
        assert errors == [], (
            f"envelope[{i}] (agent={block['agent_id']!r} role={block['role']!r}) "
            f"failed schema validation: {[e.message for e in errors]}"
        )


def test_published_minimal_envelope_blocks_load_into_model():
    """The published example blocks must also load cleanly into the
    Pydantic model — the model's invariants must accept what the
    schema accepts."""
    envelopes = json.loads(MINIMAL_ENVELOPE_PATH.read_text())["envelopes"]
    for i, env in enumerate(envelopes):
        block = env["subagent_chain"]
        SubagentChainV0.model_validate(block)  # raises on failure


# ---------------------------------------------------------------------------
# Round-trip: model → dict → schema
# ---------------------------------------------------------------------------


def _root() -> SubagentChainV0:
    return SubagentChainV0(
        agent_id="researcher",
        role="root",
        chain_depth=0,
        protocol="langgraph_subgraph",
        parent_envelope_hash=None,
        handoff_signature=None,
        handoff_timestamp_utc=None,
        child_agent_ids=["writer"],
    )


def _child() -> SubagentChainV0:
    return SubagentChainV0(
        agent_id="writer",
        role="child",
        chain_depth=1,
        protocol="langgraph_subgraph",
        parent_envelope_hash="sha256:a1b2c3d4e5f60718",
        parent_agent_id="researcher",
        child_agent_ids=["editor"],
        handoff_signature="demo-hmac:4f7b2a8c91e36042",
        handoff_timestamp_utc="2026-05-25T10:00:00Z",
    )


def _leaf() -> SubagentChainV0:
    return SubagentChainV0(
        agent_id="editor",
        role="leaf",
        chain_depth=2,
        protocol="langgraph_subgraph",
        parent_envelope_hash="sha256:7c8e9d0a1b2c3d4f",
        parent_agent_id="writer",
        child_agent_ids=[],
        handoff_signature="demo-hmac:1a2b3c4d5e6f7081",
        handoff_timestamp_utc="2026-05-25T10:00:30Z",
    )


@pytest.mark.parametrize("ctor", [_root, _child, _leaf])
def test_model_dump_validates_against_schema(schema_validator, ctor):
    instance = ctor()
    errors = list(schema_validator.iter_errors(instance.model_dump()))
    assert errors == [], (
        f"model {ctor.__name__} dump rejected by schema: "
        f"{[e.message for e in errors]}"
    )


# ---------------------------------------------------------------------------
# Negative parity: invariants both surfaces enforce
# ---------------------------------------------------------------------------


def test_root_with_non_zero_depth_rejected_by_both(schema_validator):
    """role='root' AND chain_depth>0 must be rejected by both surfaces."""
    bad = {
        "status": "active",
        "agent_id": "root_agent",
        "role": "root",
        "chain_depth": 1,  # invalid
        "protocol": "phionyx_native",
        "parent_envelope_hash": None,
        "handoff_signature": None,
        "handoff_timestamp_utc": None,
    }
    assert list(schema_validator.iter_errors(bad)), "schema must reject"
    with pytest.raises(ValidationError):
        SubagentChainV0.model_validate(bad)


def test_root_with_parent_hash_rejected_by_both(schema_validator):
    """role='root' AND parent_envelope_hash!=None must be rejected
    by both surfaces."""
    bad = {
        "status": "active",
        "agent_id": "root_agent",
        "role": "root",
        "chain_depth": 0,
        "protocol": "phionyx_native",
        "parent_envelope_hash": "sha256:deadbeef",  # invalid for root
        "handoff_signature": None,
        "handoff_timestamp_utc": None,
    }
    assert list(schema_validator.iter_errors(bad)), "schema must reject"
    with pytest.raises(ValidationError):
        SubagentChainV0.model_validate(bad)


def test_child_without_parent_hash_rejected_by_both(schema_validator):
    """role='child' AND parent_envelope_hash=None must be rejected by both."""
    bad = {
        "status": "active",
        "agent_id": "child_agent",
        "role": "child",
        "chain_depth": 1,
        "protocol": "phionyx_native",
        "parent_envelope_hash": None,  # invalid for child
        "handoff_signature": "demo-hmac:00",
        "handoff_timestamp_utc": "2026-05-25T10:00:00Z",
    }
    assert list(schema_validator.iter_errors(bad)), "schema must reject"
    with pytest.raises(ValidationError):
        SubagentChainV0.model_validate(bad)


def test_leaf_with_child_agent_ids_rejected_by_both(schema_validator):
    """role='leaf' AND child_agent_ids non-empty must be rejected by both."""
    bad = {
        "status": "active",
        "agent_id": "leaf_agent",
        "role": "leaf",
        "chain_depth": 1,
        "protocol": "phionyx_native",
        "parent_envelope_hash": "sha256:cafef00d",
        "handoff_signature": "demo-hmac:00",
        "handoff_timestamp_utc": "2026-05-25T10:00:00Z",
        "child_agent_ids": ["downstream"],  # invalid for leaf
    }
    assert list(schema_validator.iter_errors(bad)), "schema must reject"
    with pytest.raises(ValidationError):
        SubagentChainV0.model_validate(bad)


# ---------------------------------------------------------------------------
# Schema field-set ↔ model field-set: structural contract
# ---------------------------------------------------------------------------


def test_schema_required_fields_match_model_required(schema: dict):
    """Required-fields contract: schema's required list and model's
    non-default fields must overlap on the eight wire-required fields."""
    schema_required = set(schema["required"])
    expected = {
        "status",
        "agent_id",
        "role",
        "chain_depth",
        "protocol",
        "parent_envelope_hash",
        "handoff_signature",
        "handoff_timestamp_utc",
    }
    assert schema_required == expected, (
        f"schema required mismatch: schema={schema_required} vs expected={expected}"
    )

    model_fields = SubagentChainV0.model_fields
    for f in expected:
        assert f in model_fields, f"Pydantic model missing field {f!r}"


def test_schema_protocol_enum_matches_model_literal(schema: dict):
    """Protocol enum must be identical across schema and model."""
    schema_enum = set(schema["properties"]["protocol"]["enum"])
    expected = {"a2a", "agntcy", "phionyx_native", "langgraph_subgraph", "crewai", "autogen"}
    assert schema_enum == expected


def test_schema_role_enum_matches_model_literal(schema: dict):
    """Role enum must be identical across schema and model."""
    schema_enum = set(schema["properties"]["role"]["enum"])
    assert schema_enum == {"root", "child", "leaf"}
