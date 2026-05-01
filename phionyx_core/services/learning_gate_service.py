"""
Learning Gate Service — v4.1
==============================

Evaluates learning updates against boundary zone rules.
Implements Learning Gate Contract v1.0: zone registry, evidence validation, rollback.
Port-adapter pattern (AD-2).
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..contracts.v4.learning_update import LearningGateDecision, LearningUpdate

logger = logging.getLogger(__name__)

# Maximum parameter change per update (safety bound)
MAX_DELTA_FRACTION = 0.2  # 20% change per update

# Tier-to-zone mapping (Learning Gate Contract v1.0 §3)
TIER_TO_ZONE: dict[str, str] = {
    "A": "adaptive",
    "B": "gated",
    "C": "gated",
    "D": "immutable",
}

# Default surfaces.yaml path (relative to phionyx_core root)
_SURFACES_YAML = Path(__file__).parent.parent / "research_engine" / "mutation" / "surfaces.yaml"


def _load_surface_registry(surfaces_path: Path | None = None) -> dict[str, str]:
    """Load parameter → boundary zone mapping from surfaces.yaml.

    Returns dict mapping 'param_name' -> 'immutable'|'gated'|'adaptive'.
    """
    path = surfaces_path or _SURFACES_YAML
    registry: dict[str, str] = {}

    if not path.exists():
        logger.warning("surfaces.yaml not found at %s — using empty registry", path)
        return registry

    with open(path) as f:
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
        surfaces_path: Path | None = None,
    ):
        self.max_delta_fraction = max_delta_fraction
        self._approval_queue: list[LearningUpdate] = []
        self._applied_updates: dict[str, LearningUpdate] = {}  # update_id -> update
        self._zone_registry: dict[str, str] = _load_surface_registry(surfaces_path)

    def get_boundary_zone(self, param_name: str) -> str:
        """Resolve boundary zone for a parameter from surfaces.yaml tier mapping.

        Returns 'immutable', 'gated', or 'adaptive'.
        Unknown parameters default to 'gated' (safe fallback).
        """
        return self._zone_registry.get(param_name, "gated")

    async def evaluate_updates(self, updates: list[LearningUpdate]) -> list[LearningUpdate]:
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
        return updates

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

    async def apply_approved(self, updates: list[LearningUpdate]) -> int:
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

        # Record rollback
        update.gate_decision = LearningGateDecision.REJECTED
        update.gate_reason = f"Rolled back: original value {update.current_value} restored"
        update.rolled_back_at = datetime.now(timezone.utc)
        update.metadata["rollback"] = True
        update.metadata["rollback_reason"] = "manual_or_auto_rollback"

        # Remove from applied tracking
        del self._applied_updates[update_id]

        logger.info(
            "Rollback applied: %s -> %s (original: %s)",
            update.target_parameter,
            update.current_value,
            update.proposed_value,
        )
        return True

    def get_pending_approvals(self) -> list[LearningUpdate]:
        """Get updates awaiting human approval."""
        return [u for u in self._approval_queue if u.gate_decision == LearningGateDecision.PENDING]

    def get_applied_updates(self) -> dict[str, LearningUpdate]:
        """Get all currently applied updates (available for rollback)."""
        return dict(self._applied_updates)

    def get_zone_distribution(self) -> dict[str, int]:
        """Get count of parameters per boundary zone from registry."""
        dist: dict[str, int] = {"immutable": 0, "gated": 0, "adaptive": 0}
        for zone in self._zone_registry.values():
            dist[zone] = dist.get(zone, 0) + 1
        return dist
