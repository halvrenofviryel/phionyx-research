"""
Learning Gate Service — v4.1
==============================

Evaluates learning updates against boundary zone rules.
Implements Learning Gate Contract v1.0: zone registry, evidence validation, rollback.
Port-adapter pattern (AD-2).
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

import yaml

from ..contracts.v4.learning_update import LearningUpdate, LearningGateDecision
from ..contracts.v4.learning_decision_record import LearningDecisionRecord
from ..ports.learning_record_port import (
    LearningRecordPort,
    InMemoryLearningRecordPort,
)

logger = logging.getLogger(__name__)

# Maximum parameter change per update (safety bound)
MAX_DELTA_FRACTION = 0.2  # 20% change per update

# Tier-to-zone mapping (Learning Gate Contract v1.0 §3)
TIER_TO_ZONE: Dict[str, str] = {
    "A": "adaptive",
    "B": "gated",
    "C": "gated",
    "D": "immutable",
}

# Default surfaces.yaml path (relative to phionyx_core root)
_SURFACES_YAML = Path(__file__).parent.parent / "research_engine" / "mutation" / "surfaces.yaml"


def _load_surface_registry(surfaces_path: Optional[Path] = None) -> Dict[str, str]:
    """Load parameter → boundary zone mapping from surfaces.yaml.

    Returns dict mapping 'param_name' -> 'immutable'|'gated'|'adaptive'.
    """
    path = surfaces_path or _SURFACES_YAML
    registry: Dict[str, str] = {}

    if not path.exists():
        logger.warning("surfaces.yaml not found at %s — using empty registry", path)
        return registry

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    for surface in data.get("surfaces", []):
        tier = surface.get("tier", "D")
        zone = TIER_TO_ZONE.get(str(tier), "immutable")
        for param in surface.get("parameters", []):
            name = param.get("name", "")
            if name:
                registry[name] = zone

    return registry


class LearningGateService:
    """
    Evaluates and gates learning parameter updates.

    Boundary zone rules (Learning Gate Contract v1.0):
    - IMMUTABLE: Always rejected (safety rules, core identity)
    - GATED: Requires human approval (governance, ethics)
    - ADAPTIVE: Auto-approved if evidence criteria met

    Zone registry derived from surfaces.yaml tier mapping:
    - Tier A → adaptive
    - Tier B → gated
    - Tier C → gated
    - Tier D → immutable
    """

    def __init__(
        self,
        max_delta_fraction: float = MAX_DELTA_FRACTION,
        surfaces_path: Optional[Path] = None,
        record_port: Optional[LearningRecordPort] = None,
    ):
        self.max_delta_fraction = max_delta_fraction
        self._approval_queue: List[LearningUpdate] = []
        self._applied_updates: Dict[str, LearningUpdate] = {}  # update_id -> update
        self._zone_registry: Dict[str, str] = _load_surface_registry(surfaces_path)
        # Contract v1.0 §7: every decision produces an audit record. Default to a
        # deterministic in-core hash chain; the bridge/MCP RGE adapter can inject a
        # signed-envelope sink (Core cannot import the envelope store).
        self.record_port: LearningRecordPort = record_port or InMemoryLearningRecordPort()

    def get_boundary_zone(self, param_name: str) -> str:
        """Resolve boundary zone for a parameter from surfaces.yaml tier mapping.

        Returns 'immutable', 'gated', or 'adaptive'.
        Unknown parameters default to 'gated' (safe fallback).
        """
        return self._zone_registry.get(param_name, "gated")

    async def evaluate_updates(self, updates: List[LearningUpdate]) -> List[LearningUpdate]:
        """Evaluate a batch of learning updates."""
        for update in updates:
            # Auto-resolve zone from registry if not explicitly set or still default
            if update.boundary_zone == "adaptive" and update.target_parameter:
                resolved_zone = self.get_boundary_zone(
                    update.target_parameter.split(".")[-1]
                    if "." in update.target_parameter
                    else update.target_parameter
                )
                update.boundary_zone = resolved_zone

            self._evaluate_single(update)
            # Contract v1.0 §7: record EVERY decision (approved/rejected/pending).
            self._emit_decision_record(update)
        return updates

    @staticmethod
    def _value_hash(value: object) -> str:
        """sha256 over the FULL repr of a value (so truncated previews can't collide)."""
        return "sha256:" + hashlib.sha256(repr(value).encode("utf-8")).hexdigest()

    def _mean_cqs_delta(self, update: LearningUpdate) -> Optional[float]:
        """Mean measured ΔCQS across evidence entries, or None if unavailable."""
        deltas = [
            float(e["cqs_delta"])
            for e in update.evidence
            if e.get("cqs_delta") is not None
        ]
        return sum(deltas) / len(deltas) if deltas else None

    def _emit_decision_record(
        self,
        update: LearningUpdate,
        *,
        rollback: bool = False,
        restored: bool = False,
    ) -> str:
        """Build a data-minimised LearningDecisionRecord and emit it to the sink.

        Returns the new chain head hash (empty string for a null sink).
        """
        decision = update.gate_decision
        record = LearningDecisionRecord(
            update_id=update.update_id,
            target_parameter=update.target_parameter,
            boundary_zone=update.boundary_zone,
            gate_decision=getattr(decision, "value", str(decision)),
            gate_reason=update.gate_reason,
            evidence_count=len(update.evidence),
            cqs_delta=self._mean_cqs_delta(update),
            original_value_repr=repr(update.current_value)[:128],
            proposed_value_repr=repr(update.proposed_value)[:128],
            original_value_hash=self._value_hash(update.current_value),
            proposed_value_hash=self._value_hash(update.proposed_value),
            rollback=rollback,
            restored=restored,
            restored_value_repr=repr(update.current_value)[:128] if restored else None,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        return self.record_port.emit(record)

    def _evaluate_single(self, update: LearningUpdate) -> None:
        """Evaluate a single learning update against zone rules."""
        if update.boundary_zone == "immutable":
            update.gate_decision = LearningGateDecision.REJECTED
            update.gate_reason = "Immutable boundary zone — parameter cannot be modified"
            return

        if update.boundary_zone == "gated":
            update.gate_decision = LearningGateDecision.PENDING
            update.gate_reason = "Gated boundary zone — requires human approval"
            self._approval_queue.append(update)
            return

        # Adaptive zone: validate evidence criteria (Contract v1.0 §4)
        if not self._validate_evidence(update):
            return  # gate_decision set inside _validate_evidence

        # Check delta bounds
        if update.delta is not None and update.current_value is not None:
            try:
                current = float(update.current_value)
                if current != 0:
                    relative_change = abs(update.delta) / abs(current)
                    if relative_change > self.max_delta_fraction:
                        update.gate_decision = LearningGateDecision.REJECTED
                        update.gate_reason = (
                            f"Change too large: {relative_change:.1%} > "
                            f"{self.max_delta_fraction:.1%} max"
                        )
                        return
            except (ValueError, TypeError):
                pass

        update.gate_decision = LearningGateDecision.APPROVED
        update.gate_reason = "Adaptive zone — evidence criteria met, within bounds"

    def _validate_evidence(self, update: LearningUpdate) -> bool:
        """Validate evidence criteria for adaptive zone (Contract v1.0 §4).

        Returns True if evidence is sufficient, False if rejected.
        Sets gate_decision and gate_reason on rejection.
        """
        evidence = update.evidence

        # §4.1: Minimum experiments
        if len(evidence) < update.min_experiments:
            update.gate_decision = LearningGateDecision.REJECTED
            update.gate_reason = (
                f"Insufficient evidence: {len(evidence)} experiments "
                f"< {update.min_experiments} minimum required"
            )
            return False

        # §4.1: CQS delta threshold
        cqs_deltas = []
        for e in evidence:
            delta = e.get("cqs_delta")
            if delta is not None:
                cqs_deltas.append(float(delta))

        if cqs_deltas:
            avg_delta = sum(cqs_deltas) / len(cqs_deltas)
            if abs(avg_delta) < update.cqs_delta_threshold:
                update.gate_decision = LearningGateDecision.REJECTED
                update.gate_reason = (
                    f"CQS delta below threshold: |{avg_delta:.4f}| "
                    f"< {update.cqs_delta_threshold}"
                )
                return False

            # §4.1: Consistency — all experiments must agree on direction
            if len(cqs_deltas) >= 2:
                positive = sum(1 for d in cqs_deltas if d > 0)
                negative = sum(1 for d in cqs_deltas if d < 0)
                if positive > 0 and negative > 0:
                    update.gate_decision = LearningGateDecision.REJECTED
                    update.gate_reason = (
                        f"Inconsistent evidence: {positive} positive, "
                        f"{negative} negative CQS deltas"
                    )
                    return False

        # §4.2: Guardrail pass
        for e in evidence:
            if e.get("guardrail_passed") is False:
                update.gate_decision = LearningGateDecision.REJECTED
                update.gate_reason = (
                    f"Guardrail violation in experiment {e.get('experiment_id', '?')}"
                )
                return False

        return True

    async def apply_approved(self, updates: List[LearningUpdate]) -> int:
        """Apply approved updates and track for potential rollback."""
        applied = 0
        for update in updates:
            if update.gate_decision == LearningGateDecision.APPROVED:
                update.applied_at = datetime.now(timezone.utc)
                self._applied_updates[update.update_id] = update
                applied += 1
        return applied

    def rollback_update(self, update_id: str) -> bool:
        """Rollback a previously applied update (Contract v1.0 §6).

        Returns True if rollback succeeded, False if update not found or not applied.
        """
        update = self._applied_updates.get(update_id)
        if update is None:
            logger.warning("Rollback failed: update %s not found in applied updates", update_id)
            return False

        if update.applied_at is None:
            logger.warning("Rollback failed: update %s was never applied", update_id)
            return False

        # Contract v1.0 §6.5: restore the original value + write an audit record.
        # The gate is the authority for the restore decision; it records the
        # value to re-apply (current_value = the pre-change original). The
        # parameter store consumer (PRE) re-applies metadata["restored_value"],
        # consistent with apply_approved not writing the param store directly.
        update.gate_decision = LearningGateDecision.REJECTED
        update.gate_reason = f"Rolled back: original value {update.current_value!r} restored"
        update.rolled_back_at = datetime.now(timezone.utc)
        update.metadata["rollback"] = True
        update.metadata["rollback_reason"] = "manual_or_auto_rollback"
        update.metadata["restored_value"] = update.current_value

        # Remove from applied tracking
        del self._applied_updates[update_id]

        # §6.5 + §7: emit the rollback audit record into the chain.
        self._emit_decision_record(update, rollback=True, restored=True)

        logger.info(
            "Rollback applied: %s -> %s (original: %s)",
            update.target_parameter,
            update.current_value,
            update.proposed_value,
        )
        return True

    def get_pending_approvals(self) -> List[LearningUpdate]:
        """Get updates awaiting human approval."""
        return [u for u in self._approval_queue if u.gate_decision == LearningGateDecision.PENDING]

    def get_applied_updates(self) -> Dict[str, LearningUpdate]:
        """Get all currently applied updates (available for rollback)."""
        return dict(self._applied_updates)

    def get_zone_distribution(self) -> Dict[str, int]:
        """Get count of parameters per boundary zone from registry."""
        dist: Dict[str, int] = {"immutable": 0, "gated": 0, "adaptive": 0}
        for zone in self._zone_registry.values():
            dist[zone] = dist.get(zone, 0) + 1
        return dist
