"""
GER v1 — Group Execution Record tests (P2)
==========================================

Acceptance criteria (analysis doc §3 P2):
1. an N-agent workflow produces ONE GER
2. each agent action carries its authority tier
3. parent->child spawn lineage is preserved
4. tamper detection passes
5. replay reconstructs the group decision chain
"""

import pytest

from phionyx_core.contracts.v4.group_execution_record import (
    GroupExecutionRecord,
    GroupActionNode,
    AuthorityTier,
)


def _three_agent_run() -> GroupExecutionRecord:
    ger = GroupExecutionRecord(trace_id="trace-ger-test")
    ger.add_action(agent_id="supervisor", role="root", chain_depth=0,
                   authority_tier=AuthorityTier.EXECUTE, directive="release")
    ger.add_action(agent_id="researcher", role="child", chain_depth=1,
                   parent_agent_id="supervisor", authority_tier=AuthorityTier.READ,
                   directive="defer")
    ger.add_action(agent_id="writer", role="leaf", chain_depth=1,
                   parent_agent_id="supervisor", authority_tier=AuthorityTier.PROPOSE,
                   directive="release")
    return ger


# (1) one GER for an N-agent run + (2) authority tiers carried
def test_single_record_with_authority_tiers():
    ger = _three_agent_run()
    assert isinstance(ger, GroupExecutionRecord)
    assert len(ger.nodes) == 3
    tiers = [n.authority_tier for n in ger.nodes]
    assert tiers == [AuthorityTier.EXECUTE, AuthorityTier.READ, AuthorityTier.PROPOSE]


# (3) spawn lineage preserved
def test_spawn_lineage_preserved():
    ger = _three_agent_run()
    root = ger.nodes[0]
    for child in ger.nodes[1:]:
        assert child.parent_agent_id == "supervisor"
        assert child.parent_node_hash == root.node_hash


def test_unknown_parent_rejected():
    ger = GroupExecutionRecord()
    ger.add_action(agent_id="root", role="root", chain_depth=0,
                   authority_tier=AuthorityTier.EXECUTE)
    with pytest.raises(ValueError):
        ger.add_action(agent_id="orphan", role="child", chain_depth=1,
                       parent_agent_id="ghost", authority_tier=AuthorityTier.READ)


# (4) tamper detection
def test_verify_true_then_tamper_breaks():
    ger = _three_agent_run()
    assert ger.verify() is True
    ger.nodes[1].directive = "release"   # flip a recorded decision
    assert ger.verify() is False


def test_verify_rejects_missing_root():
    ger = GroupExecutionRecord()
    # Manually craft a chain with no root (bypass add_action linkage).
    n = GroupActionNode(agent_id="a", role="child", chain_depth=1,
                        parent_agent_id="x", authority_tier=AuthorityTier.READ)
    n.node_hash = n.compute_hash()
    ger.nodes.append(n)
    assert ger.verify() is False


# (5) replay
def test_replay_reconstructs_path():
    ger = _three_agent_run()
    path = ger.replay()
    assert [p["agent_id"] for p in path] == ["supervisor", "researcher", "writer"]
    assert [p["directive"] for p in path] == ["release", "defer", "release"]
    assert path[1]["parent_agent_id"] == "supervisor"


def test_role_invariants_enforced():
    # root with non-zero depth rejected
    with pytest.raises(ValueError):
        GroupActionNode(agent_id="r", role="root", chain_depth=1,
                        authority_tier=AuthorityTier.READ)
    # child without parent rejected
    with pytest.raises(ValueError):
        GroupActionNode(agent_id="c", role="child", chain_depth=1,
                        authority_tier=AuthorityTier.READ)


def test_authority_lifecycle_status():
    """② GER expresses bounded-authority lifecycle: EXECUTE requested vs completed."""
    ger = GroupExecutionRecord()
    ger.add_action(agent_id="root", role="root", chain_depth=0,
                   authority_tier=AuthorityTier.EXECUTE, action_status="requested")
    ger.add_action(agent_id="child", role="leaf", chain_depth=1, parent_agent_id="root",
                   authority_tier=AuthorityTier.EXECUTE, action_status="approved")
    statuses = [n.action_status for n in ger.nodes]
    assert statuses == ["requested", "approved"]
    # status is part of the signed body → tampering the lifecycle breaks verify
    assert ger.verify() is True
    ger.nodes[0].action_status = "completed"
    assert ger.verify() is False


def test_decision_keyed_hash_excludes_clock():
    a = GroupActionNode(agent_id="x", role="root", chain_depth=0,
                        authority_tier=AuthorityTier.READ, timestamp_utc="2026-06-13T00:00:00Z")
    b = GroupActionNode(agent_id="x", role="root", chain_depth=0,
                        authority_tier=AuthorityTier.READ, timestamp_utc="2026-06-13T11:11:11Z")
    assert a.compute_hash() == b.compute_hash()
