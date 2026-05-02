"""
Mind-Loop Stage Data Flow Validator
=====================================

**Honesty note:** This module validates pipeline stage schema and metadata
key presence, not cognitive function. It ensures each orchestration stage
sets expected keys — a structural completeness check, not a cognitive test.

Runtime validator ensuring each pipeline orchestration stage sets expected
metadata keys. Used in debug mode to verify pipeline data integrity.

Pipeline Stages (per PHIONYX_MIND_LOOP_CONTRACT.md):
1. Perceive: intent + safety + knowledge boundary
2. UpdateMemory: memory retrieval + consolidation
3. UpdateSelfModel: capability + drift
4. UpdateWorldModel: causal graph + state versioning
5. Plan: goals + decomposition
6. Act: ethics + narrative + response
7. Reflect+Revise: drift + physics + confidence + audit + learning
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ─── Stage Metadata Requirements ──────────────────────────────────

STAGE_EXPECTED_KEYS: dict[str, dict[str, Any]] = {
    "perceive": {
        "blocks": [
            "kill_switch_gate", "input_safety_gate", "intent_classification",
            "context_retrieval_rag", "perceptual_frame_emit", "knowledge_boundary_check",
        ],
        "required_metadata": {"intent_type", "safety_assessment"},
        "completion_signal": "knowledge_boundary_recommendation",
    },
    "update_memory": {
        "blocks": [
            "context_retrieval_rag", "neurotransmitter_memory_growth",
            "memory_consolidation",
        ],
        "required_metadata": set(),
        "completion_signal": "memory_updated",
    },
    "update_self_model": {
        "blocks": ["self_model_assessment"],
        "required_metadata": {"self_model_available"},
        "completion_signal": "self_model_available",
    },
    "update_world_model": {
        "blocks": [
            "causal_graph_update", "causal_intervention",
            "counterfactual_analysis", "root_cause_analysis",
            "causal_simulation", "world_state_snapshot",
        ],
        "required_metadata": set(),
        "completion_signal": "world_state_hash",
    },
    "plan": {
        "blocks": ["goal_evaluation", "goal_decomposition"],
        "required_metadata": set(),
        "completion_signal": "decomposition_plan",
    },
    "act": {
        "blocks": [
            "entropy_amplitude_pre_gate", "cognitive_layer",
            "ethics_pre_response", "deliberative_ethics_gate",
            "narrative_layer", "ethics_post_response",
            "action_intent_gate", "response_build",
        ],
        "required_metadata": {"ethics_verdict"},
        "completion_signal": "response_committed",
    },
    "reflect_revise": {
        "blocks": [
            "behavioral_drift_detection", "phi_computation",
            "entropy_computation", "confidence_fusion",
            "arbitration_resolve", "audit_layer", "outcome_feedback",
            "learning_gate",
        ],
        "required_metadata": set(),
        "completion_signal": "audit_record",
    },
}

# Ordered stage names for dependency validation
STAGE_ORDER = [
    "perceive",
    "update_memory",
    "update_self_model",
    "update_world_model",
    "plan",
    "act",
    "reflect_revise",
]

# Hard dependencies: stage -> set of stages that must complete first
STAGE_DEPENDENCIES: dict[str, set[str]] = {
    "perceive": set(),
    "update_memory": {"perceive"},
    "update_self_model": {"perceive"},
    "update_world_model": {"update_memory", "update_self_model"},
    "plan": {"update_world_model"},
    "act": {"plan"},
    "reflect_revise": {"act"},
}


@dataclass
class StageValidationResult:
    """Result of validating a single mind-loop stage."""
    stage: str
    executed_blocks: list[str] = field(default_factory=list)
    missing_blocks: list[str] = field(default_factory=list)
    missing_metadata: set[str] = field(default_factory=set)
    completion_signal_present: bool = False
    dependencies_met: bool = True
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    # Quality scalars [0,1]
    quality_score: float = 0.0
    metadata_completeness: float = 0.0
    block_coverage: float = 0.0
    signal_strength: float = 0.0


@dataclass
class MindLoopValidationReport:
    """Complete mind-loop validation report for one pipeline turn."""
    stages: dict[str, StageValidationResult] = field(default_factory=dict)
    all_valid: bool = True
    total_blocks_executed: int = 0
    total_stages_complete: int = 0
    errors: list[str] = field(default_factory=list)
    # Quality aggregation
    overall_quality: float = 0.0
    min_stage_quality: float = 0.0
    quality_distribution: dict[str, float] = field(default_factory=dict)

    @property
    def completion_ratio(self) -> float:
        if not self.stages:
            return 0.0
        return self.total_stages_complete / len(self.stages)

    @property
    def quality_label(self) -> str:
        """Human-readable quality label."""
        if self.overall_quality >= 0.8:
            return "high quality"
        elif self.overall_quality >= 0.6:
            return "adequate"
        else:
            return "insufficient"


class MindLoopValidator:
    """Validates mind-loop stage data flow through the pipeline.

    Checks:
    1. Each stage has at least one block executed (or policy-skipped)
    2. Required metadata keys are present after stage execution
    3. Completion signals are set
    4. Stage dependencies are respected
    """

    def validate(
        self,
        block_results: dict[str, Any],
        metadata: dict[str, Any],
    ) -> MindLoopValidationReport:
        """Validate mind-loop integrity from pipeline execution results.

        Args:
            block_results: Dict of block_id -> BlockResult (or dict with 'status')
            metadata: Accumulated pipeline metadata (context.metadata or similar)

        Returns:
            MindLoopValidationReport with per-stage and overall results.
        """
        report = MindLoopValidationReport()
        completed_stages: set[str] = set()

        # Extract executed block IDs
        executed_blocks = set()
        for block_id, result in block_results.items():
            status = self._get_status(result)
            if status in ("ok", "skipped"):
                executed_blocks.add(block_id)

        report.total_blocks_executed = len(executed_blocks)

        for stage_name in STAGE_ORDER:
            stage_def = STAGE_EXPECTED_KEYS[stage_name]
            result = StageValidationResult(stage=stage_name)

            # Check block execution
            stage_blocks = stage_def["blocks"]
            for block_id in stage_blocks:
                if block_id in executed_blocks:
                    result.executed_blocks.append(block_id)
                else:
                    result.missing_blocks.append(block_id)

            # At least one block must have executed for stage to count
            stage_active = len(result.executed_blocks) > 0

            # Check required metadata
            required = stage_def["required_metadata"]
            for key in required:
                if key not in metadata:
                    result.missing_metadata.add(key)

            # Check completion signal
            signal = stage_def["completion_signal"]
            result.completion_signal_present = signal in metadata

            # Check dependencies
            deps = STAGE_DEPENDENCIES.get(stage_name, set())
            unmet = deps - completed_stages
            if unmet:
                result.dependencies_met = False
                result.errors.append(
                    f"Unmet dependencies: {', '.join(sorted(unmet))}"
                )

            # Determine validity
            if result.missing_metadata:
                result.valid = False
                result.errors.append(
                    f"Missing metadata: {', '.join(sorted(result.missing_metadata))}"
                )

            if not stage_active:
                result.valid = False
                result.errors.append("No blocks executed for this stage")

            if not result.dependencies_met:
                result.valid = False

            if stage_active and result.valid:
                completed_stages.add(stage_name)
                report.total_stages_complete += 1

            # Compute quality scalars
            total_expected_blocks = len(stage_blocks)
            result.block_coverage = (
                len(result.executed_blocks) / total_expected_blocks
                if total_expected_blocks > 0 else 0.0
            )

            total_required = len(required)
            present_keys = total_required - len(result.missing_metadata)
            result.metadata_completeness = (
                present_keys / total_required
                if total_required > 0 else 1.0  # no required keys = fully complete
            )

            result.signal_strength = 1.0 if result.completion_signal_present else 0.0

            result.quality_score = round(
                0.4 * result.block_coverage
                + 0.4 * result.metadata_completeness
                + 0.2 * result.signal_strength,
                4,
            )

            report.stages[stage_name] = result

        report.all_valid = all(s.valid for s in report.stages.values())
        if not report.all_valid:
            for stage_name, stage_result in report.stages.items():
                for err in stage_result.errors:
                    report.errors.append(f"[{stage_name}] {err}")

        # Aggregate quality
        self._compute_quality_aggregation(report)

        return report

    @staticmethod
    def _compute_quality_aggregation(report: MindLoopValidationReport) -> None:
        """Compute overall quality as geometric mean of stage quality scores."""
        if not report.stages:
            return

        quality_scores = []
        for stage_name, stage_result in report.stages.items():
            report.quality_distribution[stage_name] = stage_result.quality_score
            quality_scores.append(stage_result.quality_score)

        if quality_scores:
            report.min_stage_quality = min(quality_scores)
            # Geometric mean: any zero collapses the score
            product = 1.0
            for q in quality_scores:
                product *= q
            if product <= 0:
                report.overall_quality = 0.0
            else:
                report.overall_quality = round(
                    product ** (1.0 / len(quality_scores)), 4
                )
        else:
            report.min_stage_quality = 0.0
            report.overall_quality = 0.0

    @staticmethod
    def _get_status(result: Any) -> str:
        """Extract status from BlockResult or dict."""
        if hasattr(result, "status"):
            return str(result.status)
        if isinstance(result, dict):
            return str(result.get("status", "unknown"))
        return "unknown"

    @staticmethod
    def get_stage_for_block(block_id: str) -> str | None:
        """Return which mind-loop stage a block belongs to."""
        for stage_name, stage_def in STAGE_EXPECTED_KEYS.items():
            if block_id in stage_def["blocks"]:
                return stage_name
        return None

    @staticmethod
    def get_all_stage_blocks() -> dict[str, list[str]]:
        """Return all blocks grouped by stage."""
        return {
            stage: def_["blocks"]
            for stage, def_ in STAGE_EXPECTED_KEYS.items()
        }
