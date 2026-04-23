"""
v3.8.0 Canonical Order Contract Tests
======================================

Purpose:
    Prove that v3.8.0 closes the in-turn state → response feedback loop by
    placing phi_computation, entropy_computation, confidence_fusion, and
    arbitration_resolve ABOVE response_build, and by inserting the new
    response_revision_gate immediately before response_build.

    These tests are the binding contract assertion for Plan v2.
"""

from __future__ import annotations

import pytest

from phionyx_core.contracts.telemetry import (
    get_canonical_blocks,
    get_contract_version,
    get_required_event_types,
)
from phionyx_core.contracts.telemetry.migration_v3_7_0_to_v3_8_0 import (
    NEW_BLOCKS,
    NEW_EVENT_TYPES,
    REORDERED_BLOCKS,
    migrate_block_id,
)


STATE_COMPUTATION_BLOCKS = (
    "phi_computation",
    "entropy_computation",
    "confidence_fusion",
    "arbitration_resolve",
)


def test_v3_8_0_contract_is_loadable():
    order = get_canonical_blocks(version="3.8.0")
    assert isinstance(order, list)
    assert len(order) == 46


def test_v3_8_0_is_current_version():
    assert get_contract_version() == "3.8.0"


def test_response_revision_gate_present_in_v3_8_0():
    order = get_canonical_blocks(version="3.8.0")
    assert "response_revision_gate" in order


def test_response_revision_gate_absent_in_v3_7_0():
    order = get_canonical_blocks(version="3.7.0")
    assert "response_revision_gate" not in order
    assert len(order) == 45


@pytest.mark.parametrize("block", STATE_COMPUTATION_BLOCKS)
def test_state_computations_run_before_response_build_in_v3_8_0(block):
    order = get_canonical_blocks(version="3.8.0")
    assert order.index(block) < order.index("response_build"), (
        f"{block} must precede response_build in v3.8.0"
    )


@pytest.mark.parametrize("block", STATE_COMPUTATION_BLOCKS)
def test_state_computations_run_AFTER_response_build_in_v3_7_0(block):
    """Regression baseline: in v3.7.0 these blocks ran AFTER response_build
    (the very misalignment v3.8.0 fixes)."""
    order = get_canonical_blocks(version="3.7.0")
    assert order.index(block) > order.index("response_build")


def test_response_revision_gate_sits_immediately_before_response_build():
    order = get_canonical_blocks(version="3.8.0")
    gate_idx = order.index("response_revision_gate")
    build_idx = order.index("response_build")
    assert build_idx == gate_idx + 1, (
        "response_revision_gate must be the direct predecessor of response_build"
    )


def test_response_revision_gate_runs_after_all_state_computations():
    order = get_canonical_blocks(version="3.8.0")
    gate_idx = order.index("response_revision_gate")
    for block in STATE_COMPUTATION_BLOCKS:
        assert order.index(block) < gate_idx, (
            f"{block} must precede response_revision_gate so its signals "
            "are available when the gate decides"
        )


def test_no_block_deleted_between_v3_7_0_and_v3_8_0():
    v37 = set(get_canonical_blocks(version="3.7.0"))
    v38 = set(get_canonical_blocks(version="3.8.0"))
    missing = v37 - v38
    assert missing == set(), f"v3.8.0 deleted blocks: {missing}"


def test_exactly_one_new_block_added():
    v37 = set(get_canonical_blocks(version="3.7.0"))
    v38 = set(get_canonical_blocks(version="3.8.0"))
    added = v38 - v37
    assert added == {"response_revision_gate"}


def test_migration_module_lists_match_contract():
    assert NEW_BLOCKS == ["response_revision_gate"]
    assert set(REORDERED_BLOCKS) == set(STATE_COMPUTATION_BLOCKS)
    assert "response_revision" in NEW_EVENT_TYPES


def test_migration_is_identity_for_block_ids():
    """v3.8.0 does not rename any block."""
    for block_id in get_canonical_blocks(version="3.7.0"):
        assert migrate_block_id(block_id) == block_id


def test_required_event_types_include_response_revision():
    events = get_required_event_types(version="3.8.0")
    assert "response_revision" in events


def test_v3_7_0_still_loadable_after_v3_8_0_added():
    """Backward compatibility: v3.7.0 must remain loadable."""
    order = get_canonical_blocks(version="3.7.0")
    assert "response_revision_gate" not in order
    assert len(order) == 45


def test_pipeline_length_increased_by_exactly_one():
    assert len(get_canonical_blocks(version="3.8.0")) == len(
        get_canonical_blocks(version="3.7.0")
    ) + 1
