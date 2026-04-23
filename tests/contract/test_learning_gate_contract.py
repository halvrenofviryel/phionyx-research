"""
Learning Gate Contract Tests — Sprint 1.3
============================================

Contract conformity tests for Learning Gate Contract v1.0.
Verifies schema, zone definitions, and evidence criteria.
"""

import pytest
from pydantic import ValidationError

from phionyx_core.contracts.v4.learning_update import LearningUpdate, LearningGateDecision
from phionyx_core.services.learning_gate_service import (
    LearningGateService,
    TIER_TO_ZONE,
)


class TestLearningGateContractConformity:
    """Verify LearningUpdate schema conforms to Learning Gate Contract v1.0."""

    def test_schema_has_evidence_criteria_fields(self):
        """Contract §4: Schema must have min_experiments, cqs_delta_threshold, rollback_procedure."""
        update = LearningUpdate(
            target_parameter="test.param",
            current_value=1.0,
            proposed_value=1.1,
        )
        assert hasattr(update, "min_experiments")
        assert hasattr(update, "cqs_delta_threshold")
        assert hasattr(update, "rollback_procedure")

    def test_schema_has_rollback_timestamp(self):
        """Contract §6: Schema must have rolled_back_at field."""
        update = LearningUpdate(
            target_parameter="test.param",
            current_value=1.0,
            proposed_value=1.1,
        )
        assert hasattr(update, "rolled_back_at")
        assert update.rolled_back_at is None

    def test_three_boundary_zones_exist(self):
        """Contract §2: Three zones (immutable, gated, adaptive) must be recognized."""
        _svc = LearningGateService()
        for zone in ["immutable", "gated", "adaptive"]:
            update = LearningUpdate(
                target_parameter="test.param",
                current_value=1.0,
                proposed_value=1.1,
                boundary_zone=zone,
            )
            assert update.boundary_zone == zone

    def test_four_gate_decisions_exist(self):
        """Contract §7: Four decisions (APPROVED, REJECTED, PENDING, DEFERRED)."""
        assert LearningGateDecision.APPROVED == "approved"
        assert LearningGateDecision.REJECTED == "rejected"
        assert LearningGateDecision.PENDING == "pending"
        assert LearningGateDecision.DEFERRED == "deferred"

    def test_tier_to_zone_mapping_matches_contract(self):
        """Contract §3: Tier A→adaptive, B→gated, C→gated, D→immutable."""
        assert TIER_TO_ZONE == {
            "A": "adaptive",
            "B": "gated",
            "C": "gated",
            "D": "immutable",
        }
