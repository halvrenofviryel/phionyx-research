"""
Early Exit Optimizer
====================

Optimizes early exit conditions for short-circuiting pipeline execution.

Features:
- Intent-based short-circuiting
- Template response early exit
- Safety gate early exit
- Metrics collection
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EarlyExitCondition:
    """Early exit condition definition."""
    condition_type: str  # "intent", "safety", "template"
    block_id: str
    skip_blocks: set[str]  # Blocks to skip when condition is met
    preserve_blocks: set[str]  # Blocks that must always run (always-on)


class EarlyExitOptimizer:
    """
    Optimizes early exit conditions for short-circuiting.

    Features:
    - Intent-based short-circuiting
    - Template response early exit
    - Safety gate early exit
    """

    def __init__(self):
        """Initialize early exit optimizer."""
        self.conditions: dict[str, EarlyExitCondition] = {}
        self.metrics = {
            "early_exits": 0,
            "intent_based_exits": 0,
            "safety_exits": 0,
            "template_exits": 0,
            "blocks_skipped": 0
        }
        self._initialize_conditions()

    def _initialize_conditions(self) -> None:
        """Initialize early exit conditions."""
        # Intent-based early exit conditions
        # If intent is "greeting" and template response is available, skip cognitive processing
        self.conditions["intent_greeting_template"] = EarlyExitCondition(
            condition_type="intent",
            block_id="intent_classification",
            skip_blocks={
                "cognitive_layer",
                "context_retrieval_rag",  # Skip RAG for simple greetings
                "ukf_predict",  # Skip prediction for simple greetings
                "entropy_amplitude_pre_gate",
                "ethics_pre_response",
                "neurotransmitter_memory_growth",
                "emotion_estimation",
                "unified_state_update_esc"
            },
            preserve_blocks={
                "response_build",
                "phi_computation",
                "entropy_computation",
                "audit_layer",
                "telemetry_publish"
            }
        )

        # Safety gate early exit
        self.conditions["safety_gate_blocked"] = EarlyExitCondition(
            condition_type="safety",
            block_id="input_safety_gate",
            skip_blocks={
                "intent_classification",
                "context_retrieval_rag",
                "create_scenario_frame",
                "initialize_unified_state",
                "ukf_predict",
                "cognitive_layer",
                "narrative_layer"
            },
            preserve_blocks={
                "response_build",
                "phi_computation",
                "entropy_computation",
                "audit_layer"
            }
        )

        # Template response early exit
        self.conditions["template_response"] = EarlyExitCondition(
            condition_type="template",
            block_id="narrative_layer",
            skip_blocks={
                "cognitive_layer",  # Already have template response
                "context_retrieval_rag"  # Not needed for template
            },
            preserve_blocks={
                "response_build",
                "phi_computation",
                "entropy_computation"
            }
        )

    def should_short_circuit(
        self,
        block_id: str,
        context: Any,
        result: Any | None = None
    ) -> EarlyExitCondition | None:
        """
        Check if pipeline should short-circuit based on current block result.

        Args:
            block_id: Current block ID
            context: Block context
            result: Optional block result

        Returns:
            EarlyExitCondition if short-circuit should occur, None otherwise
        """
        # Check intent-based short-circuit
        if block_id == "intent_classification" and result:
            intent_data = result.data.get("intent") if result.data else None
            if isinstance(intent_data, dict):
                intent_type = intent_data.get("intent")
                if intent_type == "greeting":
                    # Check if template response is available
                    metadata = context.metadata or {}
                    if metadata.get("template_response_available"):
                        condition = self.conditions.get("intent_greeting_template")
                        if condition:
                            self.metrics["intent_based_exits"] += 1
                            self.metrics["early_exits"] += 1
                            logger.debug("Early exit: Intent-based short-circuit (greeting + template)")
                            return condition

        # Check safety gate early exit
        if block_id == "input_safety_gate" and result:
            if result.data and result.data.get("is_blocked"):
                condition = self.conditions.get("safety_gate_blocked")
                if condition:
                    self.metrics["safety_exits"] += 1
                    self.metrics["early_exits"] += 1
                    logger.debug("Early exit: Safety gate blocked")
                    return condition

        # Check template response early exit
        if block_id == "narrative_layer" and result:
            if result.data and result.data.get("narrative_result", {}).get("source") == "template":
                condition = self.conditions.get("template_response")
                if condition:
                    self.metrics["template_exits"] += 1
                    self.metrics["early_exits"] += 1
                    logger.debug("Early exit: Template response used")
                    return condition

        return None

    def get_blocks_to_skip(
        self,
        condition: EarlyExitCondition,
        current_block_id: str
    ) -> set[str]:
        """
        Get list of blocks to skip based on early exit condition.

        Args:
            condition: EarlyExitCondition
            current_block_id: Current block ID

        Returns:
            Set of block IDs to skip
        """
        # Skip blocks defined in condition, but preserve always-on blocks
        blocks_to_skip = condition.skip_blocks.copy()

        # Remove preserve blocks from skip list
        blocks_to_skip -= condition.preserve_blocks

        # Don't skip current block
        blocks_to_skip.discard(current_block_id)

        return blocks_to_skip

    def get_metrics(self) -> dict[str, int]:
        """
        Get early exit metrics.

        Returns:
            Dictionary with metrics
        """
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset metrics."""
        self.metrics = {
            "early_exits": 0,
            "intent_based_exits": 0,
            "safety_exits": 0,
            "template_exits": 0,
            "blocks_skipped": 0
        }

