"""
Mind-Loop Validator Unit Tests — Sprint 2.2
=============================================

Tests for the runtime stage data flow validator.
Total: 10 tests
"""

import pytest
from phionyx_core.meta.mind_loop_validator import (
    MindLoopValidator,
    STAGE_EXPECTED_KEYS,
    STAGE_ORDER,
    STAGE_DEPENDENCIES,
)


def _make_block_result(status="ok"):
    return {"status": status, "data": {}}


def _all_blocks_ok():
    """All current canonical blocks executed (v3.8.0, 46 blocks).

    The validator's expected stage-block sets (in
    phionyx_core/meta/mind_loop_validator.py) track the current
    contract, so the test helper must load the current canonical list,
    not an older one. Loading directly from the package keeps the test
    self-contained — the older `tests.behavioral_eval` fixture is
    monorepo-only and not shipped here.
    """
    from phionyx_core.contracts.telemetry import get_canonical_blocks
    blocks = get_canonical_blocks()  # defaults to current (v3.8.0)
    return {b: _make_block_result("ok") for b in blocks}


def _full_metadata():
    return {
        "intent_type": "question",
        "safety_assessment": {"risk": 0.1},
        "knowledge_boundary_recommendation": "proceed",
        "memory_updated": True,
        "self_model_available": True,
        "world_state_hash": "abc",
        "decomposition_plan": {},
        "ethics_verdict": "ok",
        "response_committed": True,
        "audit_record": {},
    }


class TestMindLoopValidator:
    """Unit tests for MindLoopValidator."""

    def test_validate_returns_report(self):
        """validate() returns MindLoopValidationReport."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        assert hasattr(report, "stages")
        assert hasattr(report, "all_valid")

    def test_all_valid_full_pipeline(self):
        """Full pipeline + full metadata → all_valid True."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        assert report.all_valid

    def test_empty_results_invalid(self):
        """Empty block results → all stages invalid."""
        v = MindLoopValidator()
        report = v.validate({}, _full_metadata())
        assert not report.all_valid
        assert report.total_stages_complete == 0

    def test_empty_metadata_partial_valid(self):
        """Full blocks but empty metadata → stages with required metadata invalid."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), {})
        # Perceive requires intent_type + safety_assessment → invalid
        assert not report.stages["perceive"].valid

    def test_skipped_blocks_count_as_executed(self):
        """Blocks with status 'skipped' count as executed for stage validation."""
        v = MindLoopValidator()
        results = _all_blocks_ok()
        results["learning_gate"] = {"status": "skipped"}
        report = v.validate(results, _full_metadata())
        assert "learning_gate" in report.stages["reflect_revise"].executed_blocks

    def test_error_blocks_not_counted(self):
        """Blocks with status 'error' don't count as executed."""
        v = MindLoopValidator()
        results = {"kill_switch_gate": {"status": "error"}}
        report = v.validate(results, _full_metadata())
        assert "kill_switch_gate" not in report.stages["perceive"].executed_blocks

    def test_dependency_chain_propagation(self):
        """Dependency failures cascade: if Perceive fails, downstream unmet."""
        v = MindLoopValidator()
        # Only Act stage blocks present (no Perceive, etc.)
        results = {
            "narrative_layer": _make_block_result(),
            "ethics_pre_response": _make_block_result(),
        }
        metadata = _full_metadata()
        report = v.validate(results, metadata)
        # Act should show unmet dependencies
        assert not report.stages["act"].dependencies_met

    def test_completion_ratio_calculation(self):
        """completion_ratio = stages_complete / total_stages."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        assert report.completion_ratio == 1.0

    def test_get_stage_for_block_returns_none_for_unknown(self):
        """Unknown block returns None."""
        assert MindLoopValidator.get_stage_for_block("unknown_block") is None

    def test_seven_stages_defined(self):
        """Exactly 7 stages are defined in STAGE_ORDER."""
        assert len(STAGE_ORDER) == 7
        assert len(STAGE_EXPECTED_KEYS) == 7


class TestStageQualityScoring:
    """Tests for stage quality scalars (Sprint B)."""

    def test_full_pipeline_quality_is_high(self):
        """Full pipeline + full metadata → overall quality >= 0.8."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        assert report.overall_quality >= 0.8
        assert report.quality_label == "high quality"

    def test_quality_distribution_has_7_stages(self):
        """Quality distribution maps all 7 stages."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        assert len(report.quality_distribution) == 7
        for stage in STAGE_ORDER:
            assert stage in report.quality_distribution

    def test_block_coverage_full_pipeline(self):
        """All blocks executed → block_coverage = 1.0 for each stage."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        for stage_name, result in report.stages.items():
            assert result.block_coverage == 1.0, f"{stage_name} block_coverage != 1.0"

    def test_metadata_completeness_full(self):
        """Full metadata → metadata_completeness = 1.0 for stages with required keys."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        for stage_name, result in report.stages.items():
            assert result.metadata_completeness == 1.0, f"{stage_name} metadata_completeness != 1.0"

    def test_signal_strength_with_all_signals(self):
        """Full metadata → signal_strength = 1.0 for each stage."""
        v = MindLoopValidator()
        report = v.validate(_all_blocks_ok(), _full_metadata())
        for stage_name, result in report.stages.items():
            assert result.signal_strength == 1.0, f"{stage_name} signal_strength != 1.0"

    def test_empty_blocks_quality_zero(self):
        """No blocks executed + no metadata → overall quality = 0.0."""
        v = MindLoopValidator()
        report = v.validate({}, {})
        assert report.overall_quality == 0.0

    def test_min_stage_quality_tracks_weakest(self):
        """min_stage_quality reflects the weakest stage."""
        v = MindLoopValidator()
        # Remove all perceive blocks to make perceive the weakest
        results = _all_blocks_ok()
        for block_id in ["kill_switch_gate", "input_safety_gate",
                         "intent_classification", "context_retrieval_rag",
                         "perceptual_frame_emit", "knowledge_boundary_check"]:
            del results[block_id]
        report = v.validate(results, _full_metadata())
        assert report.min_stage_quality == report.stages["perceive"].quality_score
        assert report.min_stage_quality < report.stages["reflect_revise"].quality_score

    def test_partial_metadata_reduces_completeness(self):
        """Missing required metadata reduces metadata_completeness."""
        v = MindLoopValidator()
        meta = _full_metadata()
        del meta["intent_type"]  # perceive requires intent_type
        report = v.validate(_all_blocks_ok(), meta)
        # perceive has 2 required: intent_type, safety_assessment → completeness = 0.5
        assert report.stages["perceive"].metadata_completeness == 0.5
