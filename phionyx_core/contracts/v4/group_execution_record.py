"""
GroupExecutionRecord (GER) — v4 Schema (P2 v1)
==============================================

The signed, replayable **collective** evidence record for a multi-agent run — the
**Group Execution Record (GER)**. Where the VLDR
(`learning_decision_record.py`) attests ONE self-modification decision, the GER attests
ONE N-agent workflow as a single chain: *who acted, under what authority, spawned by whom,
with what decision* — turning a sequence of opaque agent/tool calls into one institutional
record.

Relationship to existing primitives:
- per-turn handoff evidence is `contracts/envelopes/subagent_chain.py` (`SubagentChainV0`);
  the GER is the *aggregate* record that composes those handoffs across a whole run.
- it reuses the same honesty + determinism discipline as the VLDR and DecisionReceipt:
  **attests made + chained, NOT correct**; **data-minimised** (no raw payloads); the hash
  is **decision-keyed, not clock-keyed** (timestamp excluded from the signing body).

Core owns the SHAPE + in-memory verification only. The signed RGE-envelope persistence
adapter lives in the bridge/MCP companion (Core cannot import the envelope store), exactly
like the VLDR's `EnvelopeLearningRecordPort`.

Mind-loop stage: Act + Reflect. AGI label: governance/audit capability — evidence, not
cognition.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class AuthorityTier(str, Enum):
    """Bounded-authority tier of an agent action (HearthOS bounded_authority_envelope vocab)."""

    READ = "read"        # may observe only
    PROPOSE = "propose"  # may suggest; no external effect
    EXECUTE = "execute"  # may take an effecting action


# Authority LIFECYCLE state, distinct from the tier (the real HearthOS envelope models
# execute_requested/approved/rejected/completed). The tier says "how much authority";
# the status says "where in the request->approve->complete lifecycle this action is".
# Without it a GER could not express "EXECUTE requested but not yet approved" (fix ②).
GroupActionStatus = Literal["requested", "approved", "rejected", "completed", "n/a"]

GroupActionRole = ("root", "child", "leaf")


class GroupActionNode(BaseModel):
    """One agent action within a group run: who, under what authority, spawned by whom."""

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = Field(..., min_length=1, description="Stable id of the acting agent")
    role: str = Field(..., description="root | child | leaf")
    chain_depth: int = Field(..., ge=0, description="root=0; each spawn increments")
    authority_tier: AuthorityTier = Field(..., description="read | propose | execute (how much)")
    action_status: GroupActionStatus = Field(
        default="completed",
        description="requested | approved | rejected | completed | n/a (where in the lifecycle)",
    )

    # spawn lineage
    parent_agent_id: Optional[str] = Field(default=None)
    parent_node_hash: Optional[str] = Field(default=None, description="node_hash of the spawner")

    # the decision this action recorded (governance facts only)
    directive: str = Field(default="n/a", description="recorded decision, e.g. release|block|defer")
    decision_reason: str = Field(default="", description="STATED policy reason — not raw content")
    evidence_count: int = Field(default=0, ge=0)

    # integrity / chain
    timestamp_utc: Optional[str] = Field(default=None, description="ISO-8601 UTC (NOT signed)")
    prev_node_hash: Optional[str] = Field(default=None)
    node_hash: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_role(self) -> "GroupActionNode":
        if self.role == "root":
            if self.chain_depth != 0:
                raise ValueError(f"role='root' requires chain_depth=0, got {self.chain_depth}")
            if self.parent_agent_id is not None or self.parent_node_hash is not None:
                raise ValueError("role='root' requires no parent")
        elif self.role in ("child", "leaf"):
            if self.chain_depth < 1:
                raise ValueError(f"role='{self.role}' requires chain_depth>=1")
            if not self.parent_agent_id:
                raise ValueError(f"role='{self.role}' requires parent_agent_id")
        else:
            raise ValueError(f"role must be one of {GroupActionRole}, got {self.role!r}")
        return self

    def canonical_signing_body(self) -> bytes:
        """Decision-keyed canonical-JSON bytes (excludes node_id, hashes set by chain, clock)."""
        body = {
            "action_status": self.action_status,
            "agent_id": self.agent_id,
            "authority_tier": self.authority_tier.value,
            "chain_depth": self.chain_depth,
            "decision_reason": self.decision_reason,
            "directive": self.directive,
            "evidence_count": self.evidence_count,
            "parent_agent_id": self.parent_agent_id,
            "parent_node_hash": self.parent_node_hash,
            "prev_node_hash": self.prev_node_hash,
            "role": self.role,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    def compute_hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical_signing_body()).hexdigest()


class GroupExecutionRecord(BaseModel):
    """One multi-agent run as a single hash-chained, lineage-checked collective record."""

    ger_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: Optional[str] = None
    nodes: List[GroupActionNode] = Field(default_factory=list)
    signature_alg: str = Field(default="sha256-chain")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_action(
        self,
        *,
        agent_id: str,
        role: str,
        authority_tier: AuthorityTier,
        action_status: GroupActionStatus = "completed",
        chain_depth: int = 0,
        parent_agent_id: Optional[str] = None,
        directive: str = "n/a",
        decision_reason: str = "",
        evidence_count: int = 0,
        timestamp_utc: Optional[str] = None,
    ) -> GroupActionNode:
        """Append one agent action: links to the chain head + the named parent, then hashes it."""
        prev_hash = self.nodes[-1].node_hash if self.nodes else None
        parent_node_hash = None
        if parent_agent_id is not None:
            # most recent node for the named parent (spawn lineage)
            for n in reversed(self.nodes):
                if n.agent_id == parent_agent_id:
                    parent_node_hash = n.node_hash
                    break
            if parent_node_hash is None:
                raise ValueError(f"parent_agent_id {parent_agent_id!r} has no prior node in this GER")
        node = GroupActionNode(
            agent_id=agent_id,
            role=role,
            chain_depth=chain_depth,
            authority_tier=authority_tier,
            action_status=action_status,
            parent_agent_id=parent_agent_id,
            parent_node_hash=parent_node_hash,
            directive=directive,
            decision_reason=decision_reason,
            evidence_count=evidence_count,
            timestamp_utc=timestamp_utc,
            prev_node_hash=prev_hash,
        )
        node.node_hash = node.compute_hash()
        self.nodes.append(node)
        return node

    def chain_head(self) -> Optional[str]:
        return self.nodes[-1].node_hash if self.nodes else None

    def verify(self) -> bool:
        """Verify hash chain + spawn lineage. False on tamper or broken lineage."""
        if not self.nodes:
            return True
        roots = [n for n in self.nodes if n.role == "root"]
        if len(roots) != 1 or self.nodes[0].role != "root":
            return False
        seen: Dict[str, str] = {}  # agent_id -> latest node_hash
        prev: Optional[str] = None
        for node in self.nodes:
            if node.prev_node_hash != prev:
                return False
            if node.node_hash != node.compute_hash():
                return False
            if node.role != "root":
                if node.parent_agent_id not in seen:
                    return False
                if node.parent_node_hash != seen[node.parent_agent_id]:
                    return False
            seen[node.agent_id] = node.node_hash
            prev = node.node_hash
        return True

    def replay(self) -> List[Dict[str, Any]]:
        """Reconstruct the group decision path from the chain alone."""
        return [
            {
                "agent_id": n.agent_id,
                "role": n.role,
                "authority_tier": n.authority_tier.value,
                "action_status": n.action_status,
                "directive": n.directive,
                "parent_agent_id": n.parent_agent_id,
            }
            for n in self.nodes
        ]


__all__ = ["GroupExecutionRecord", "GroupActionNode", "AuthorityTier"]
