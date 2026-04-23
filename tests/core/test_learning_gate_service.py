"""
Learning Gate Service Tests — Sprint 1
=========================================

Tests for:
- 1.2: Boundary zone registry (15 tests)
- 1.3: Evidence criteria schema (5 tests)
- 1.4: Rollback integration (5 tests)

Total: 25 tests
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from phionyx_core.contracts.v4.learning_update import LearningUpdate, LearningGateDecision
from phionyx_core.services.learning_gate_service import (
    LearningGateService,
    TIER_TO_ZONE,
    _load_surface_registry,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_update(
    param: str = "DEFAULT_GAMMA",
    current: float = 0.15,
    proposed: float = 0.18,
    zone: str = "adaptive",
    evidence: list = None,
    min_experiments: int = 3,
) -> LearningUpdate:
    """Create a LearningUpdate for testing."""
    delta = proposed - current
    ev = evidence if evidence is not None else [
        {"experiment_id": f"exp_{i}", "cqs_delta": 0.01, "guardrail_passed": True}
        for i in range(3)
    ]
    return LearningUpdate(
        target_parameter=f"physics.{param}" if "." not in param else param,
        current_value=current,
        proposed_value=proposed,
        delta=delta,
        boundary_zone=zone,
        evidence=ev,
        min_experiments=min_experiments,
    )


def _make_service() -> LearningGateService:
    """Create a service using real surfaces.yaml."""
    return LearningGateService()


# ═══════════════════════════════════════════════════════════════════
# 1.2: Boundary Zone Registry — 15 Tests
# ═══════════════════════════════════════════════════════════════════

class TestBoundaryZoneRegistry:
    """Test zone resolution from surfaces.yaml tier mapping."""

    # ── Tier A → adaptive (5 params) ──

    def test_tier_a_physics_param_resolves_adaptive(self):
        """Tier A physics param DEFAULT_GAMMA → adaptive zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("DEFAULT_GAMMA") == "adaptive"

    def test_tier_a_memory_param_resolves_adaptive(self):
        """Tier A memory param → adaptive zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("min_cluster_size") == "adaptive"

    def test_tier_a_causality_param_resolves_adaptive(self):
        """Tier A causality param → adaptive zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("cf_attenuation_rate") == "adaptive"

    def test_tier_a_meta_param_resolves_adaptive(self):
        """Tier A meta param → adaptive zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("drift_threshold_low") == "adaptive"

    def test_tier_a_social_param_resolves_adaptive(self):
        """Tier A social param → adaptive zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("decay_factor") == "adaptive"

    # ── Tier C → gated (5 params) ──

    def test_tier_c_kill_switch_param_resolves_gated(self):
        """Tier C governance param ethics_max_risk_threshold → gated zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("ethics_max_risk_threshold") == "gated"

    def test_tier_c_ethics_weight_resolves_gated(self):
        """Tier C ethics param deontological_weight → gated zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("deontological_weight") == "gated"

    def test_tier_c_drift_max_resolves_gated(self):
        """Tier C param consecutive_drift_max → gated zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("consecutive_drift_max") == "gated"

    def test_tier_c_meta_threshold_resolves_gated(self):
        """Tier C param t_meta_min_threshold → gated zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("t_meta_min_threshold") == "gated"

    def test_tier_c_virtue_weight_resolves_gated(self):
        """Tier C ethics param virtue_weight → gated zone."""
        svc = _make_service()
        assert svc.get_boundary_zone("virtue_weight") == "gated"

    # ── Unknown params → gated (safe fallback) ──

    def test_unknown_param_defaults_to_gated(self):
        """Unknown parameter defaults to gated (safe fallback)."""
        svc = _make_service()
        assert svc.get_boundary_zone("nonexistent_param") == "gated"

    # ── Registry loading ──

    def test_registry_loads_from_surfaces_yaml(self):
        """Registry contains entries from surfaces.yaml."""
        svc = _make_service()
        assert len(svc._zone_registry) >= 66  # At least Tier A params

    def test_registry_empty_when_file_missing(self):
        """Registry is empty when surfaces.yaml doesn't exist."""
        svc = LearningGateService(surfaces_path=Path("/nonexistent/path.yaml"))
        assert len(svc._zone_registry) == 0

    def test_zone_distribution_counts(self):
        """Zone distribution returns correct counts per zone."""
        svc = _make_service()
        dist = svc.get_zone_distribution()
        assert dist["adaptive"] >= 60  # Tier A params
        assert dist["gated"] >= 9      # Tier C params
        assert "immutable" in dist

    def test_tier_to_zone_mapping_complete(self):
        """TIER_TO_ZONE covers all 4 tiers."""
        assert TIER_TO_ZONE["A"] == "adaptive"
        assert TIER_TO_ZONE["B"] == "gated"
        assert TIER_TO_ZONE["C"] == "gated"
        assert TIER_TO_ZONE["D"] == "immutable"


# ═══════════════════════════════════════════════════════════════════
# 1.3: Evidence Criteria Schema — 5 Tests
# ═══════════════════════════════════════════════════════════════════

class TestEvidenceCriteriaSchema:
    """Test LearningUpdate schema extensions for evidence criteria."""

    def test_min_experiments_default(self):
        """Default min_experiments is 3."""
        update = LearningUpdate(
            target_parameter="physics.gamma",
            current_value=0.15,
            proposed_value=0.18,
        )
        assert update.min_experiments == 3

    def test_cqs_delta_threshold_default(self):
        """Default cqs_delta_threshold is 0.005."""
        update = LearningUpdate(
            target_parameter="physics.gamma",
            current_value=0.15,
            proposed_value=0.18,
        )
        assert update.cqs_delta_threshold == 0.005

    def test_rollback_procedure_default(self):
        """Default rollback_procedure is 'auto'."""
        update = LearningUpdate(
            target_parameter="physics.gamma",
            current_value=0.15,
            proposed_value=0.18,
        )
        assert update.rollback_procedure == "auto"

    def test_custom_evidence_criteria(self):
        """Custom evidence criteria accepted."""
        update = LearningUpdate(
            target_parameter="physics.gamma",
            current_value=0.15,
            proposed_value=0.18,
            min_experiments=5,
            cqs_delta_threshold=0.01,
            rollback_procedure="manual",
        )
        assert update.min_experiments == 5
        assert update.cqs_delta_threshold == 0.01
        assert update.rollback_procedure == "manual"

    def test_rolled_back_at_initially_none(self):
        """rolled_back_at is None by default."""
        update = LearningUpdate(
            target_parameter="physics.gamma",
            current_value=0.15,
            proposed_value=0.18,
        )
        assert update.rolled_back_at is None


# ═══════════════════════════════════════════════════════════════════
# 1.4: Rollback Integration — 5 Tests
# ═══════════════════════════════════════════════════════════════════

class TestRollbackIntegration:
    """Test rollback mechanism for applied updates."""

    @pytest.mark.asyncio
    async def test_rollback_successful(self):
        """Rollback succeeds for a previously applied update."""
        svc = _make_service()
        update = _make_update()
        update.gate_decision = LearningGateDecision.APPROVED
        await svc.apply_approved([update])

        result = svc.rollback_update(update.update_id)
        assert result is True
        assert update.gate_decision == LearningGateDecision.REJECTED
        assert update.rolled_back_at is not None
        assert update.metadata.get("rollback") is True

    @pytest.mark.asyncio
    async def test_rollback_not_found(self):
        """Rollback fails when update_id is unknown."""
        svc = _make_service()
        result = svc.rollback_update("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_rollback_removes_from_applied(self):
        """Rollback removes update from applied tracking."""
        svc = _make_service()
        update = _make_update()
        update.gate_decision = LearningGateDecision.APPROVED
        await svc.apply_approved([update])
        assert update.update_id in svc.get_applied_updates()

        svc.rollback_update(update.update_id)
        assert update.update_id not in svc.get_applied_updates()

    @pytest.mark.asyncio
    async def test_rollback_audit_trail(self):
        """Rollback records audit metadata."""
        svc = _make_service()
        update = _make_update()
        update.gate_decision = LearningGateDecision.APPROVED
        await svc.apply_approved([update])

        svc.rollback_update(update.update_id)
        assert "rollback" in update.metadata
        assert "rollback_reason" in update.metadata
        assert "original value" in update.gate_reason

    @pytest.mark.asyncio
    async def test_rollback_not_applied_fails(self):
        """Rollback fails for update that was tracked but never applied."""
        svc = _make_service()
        update = _make_update()
        # Manually insert without applying
        update.applied_at = None
        svc._applied_updates[update.update_id] = update

        result = svc.rollback_update(update.update_id)
        assert result is False


# ═══════════════════════════════════════════════════════════════════
# Evidence Validation Logic — Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEvidenceValidation:
    """Test evidence criteria enforcement during evaluation."""

    @pytest.mark.asyncio
    async def test_adaptive_approved_with_sufficient_evidence(self):
        """Adaptive zone update approved with 3+ consistent experiments."""
        svc = _make_service()
        update = _make_update(zone="adaptive")
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.APPROVED

    @pytest.mark.asyncio
    async def test_adaptive_rejected_insufficient_experiments(self):
        """Adaptive zone rejected when fewer than min_experiments."""
        svc = _make_service()
        update = _make_update(
            zone="adaptive",
            evidence=[{"experiment_id": "exp_0", "cqs_delta": 0.01, "guardrail_passed": True}],
        )
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.REJECTED
        assert "Insufficient evidence" in result[0].gate_reason

    @pytest.mark.asyncio
    async def test_adaptive_rejected_cqs_below_threshold(self):
        """Adaptive zone rejected when CQS delta below threshold."""
        svc = _make_service()
        update = _make_update(
            zone="adaptive",
            evidence=[
                {"experiment_id": f"exp_{i}", "cqs_delta": 0.001, "guardrail_passed": True}
                for i in range(3)
            ],
        )
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.REJECTED
        assert "CQS delta below threshold" in result[0].gate_reason

    @pytest.mark.asyncio
    async def test_adaptive_rejected_inconsistent_direction(self):
        """Adaptive zone rejected when experiments disagree on direction."""
        svc = _make_service()
        # Use large deltas so average doesn't fall below CQS threshold first
        update = _make_update(
            zone="adaptive",
            evidence=[
                {"experiment_id": "exp_0", "cqs_delta": 0.05, "guardrail_passed": True},
                {"experiment_id": "exp_1", "cqs_delta": -0.03, "guardrail_passed": True},
                {"experiment_id": "exp_2", "cqs_delta": 0.04, "guardrail_passed": True},
            ],
        )
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.REJECTED
        assert "Inconsistent evidence" in result[0].gate_reason

    @pytest.mark.asyncio
    async def test_adaptive_rejected_guardrail_violation(self):
        """Adaptive zone rejected when any experiment has guardrail violation."""
        svc = _make_service()
        update = _make_update(
            zone="adaptive",
            evidence=[
                {"experiment_id": "exp_0", "cqs_delta": 0.01, "guardrail_passed": True},
                {"experiment_id": "exp_1", "cqs_delta": 0.01, "guardrail_passed": False},
                {"experiment_id": "exp_2", "cqs_delta": 0.01, "guardrail_passed": True},
            ],
        )
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.REJECTED
        assert "Guardrail violation" in result[0].gate_reason

    @pytest.mark.asyncio
    async def test_immutable_always_rejected_regardless_of_evidence(self):
        """Immutable zone always rejected, even with perfect evidence."""
        svc = _make_service()
        update = _make_update(zone="immutable")
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.REJECTED

    @pytest.mark.asyncio
    async def test_gated_always_pending_regardless_of_evidence(self):
        """Gated zone always pending, queued for human approval."""
        svc = _make_service()
        update = _make_update(zone="gated")
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.PENDING
        assert len(svc.get_pending_approvals()) == 1

    @pytest.mark.asyncio
    async def test_adaptive_rejected_delta_too_large(self):
        """Adaptive zone rejected when delta exceeds max fraction."""
        svc = _make_service()
        update = _make_update(
            current=0.15,
            proposed=0.50,  # 233% change
            zone="adaptive",
        )
        result = await svc.evaluate_updates([update])
        assert result[0].gate_decision == LearningGateDecision.REJECTED
        assert "Change too large" in result[0].gate_reason

    @pytest.mark.asyncio
    async def test_zone_auto_resolution_from_registry(self):
        """Zone auto-resolved from registry for param with default 'adaptive' zone."""
        svc = _make_service()
        # ethics param should resolve to gated from surfaces.yaml
        update = _make_update(param="ethics_max_risk_threshold", zone="adaptive")
        result = await svc.evaluate_updates([update])
        # Should be pending (gated), not approved
        assert result[0].gate_decision == LearningGateDecision.PENDING
        assert result[0].boundary_zone == "gated"
