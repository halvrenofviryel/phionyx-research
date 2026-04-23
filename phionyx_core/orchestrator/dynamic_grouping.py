"""
Dynamic Grouping
================

Intent-based dynamic parallel group formation.

Features:
- Intent-based group adaptation
- Dynamic parallel execution groups
- Performance optimization based on intent
"""

import logging
from typing import Dict, Optional, List, Set
from dataclasses import dataclass

from .parallel_executor import ParallelGroup

logger = logging.getLogger(__name__)


@dataclass
class IntentBasedGroupConfig:
    """Configuration for intent-based parallel groups."""
    intent: str
    parallel_groups: List[List[str]]  # List of block groups that can run in parallel
    skip_blocks: Set[str] = None  # Blocks to skip for this intent
    preserve_blocks: Set[str] = None  # Blocks that must always run

    def __post_init__(self):
        """Initialize default sets."""
        if self.skip_blocks is None:
            self.skip_blocks = set()
        if self.preserve_blocks is None:
            self.preserve_blocks = {"response_build", "phi_computation", "entropy_computation"}


class DynamicGrouping:
    """
    Dynamic grouping based on intent for optimal parallel execution.

    Features:
    - Intent-based group formation
    - Adaptive parallel execution
    - Performance optimization
    """

    def __init__(self):
        """Initialize dynamic grouping."""
        self.configs: Dict[str, IntentBasedGroupConfig] = {}
        self._initialize_configs()

    def _initialize_configs(self) -> None:
        """Initialize intent-based group configurations."""
        # Greeting intent: Skip heavy processing, use templates
        self.configs["greeting"] = IntentBasedGroupConfig(
            intent="greeting",
            parallel_groups=[
                # Group 1: Perception (can run in parallel)
                ["intent_classification", "input_safety_gate"],
                # Group 2: Observation (can run in parallel)
                ["phi_computation", "entropy_computation"]
            ],
            skip_blocks={
                "context_retrieval_rag",  # Skip RAG for greetings
                "cognitive_layer",  # Skip cognitive processing
                "ukf_predict",  # Skip prediction
                "entropy_amplitude_pre_gate",
                "ethics_pre_response",
                "neurotransmitter_memory_growth",
                "emotion_estimation",
                "unified_state_update_esc"
            }
        )

        # Question intent: Full processing, optimize RAG
        self.configs["question"] = IntentBasedGroupConfig(
            intent="question",
            parallel_groups=[
                # Group 1: Perception (parallel)
                ["intent_classification", "input_safety_gate"],
                # Group 2: Context retrieval (after intent)
                ["context_retrieval_rag"],
                # Group 3: Prediction (parallel)
                ["ukf_predict", "entropy_amplitude_pre_gate"],
                # Group 4: State update (parallel)
                ["neurotransmitter_memory_growth", "emotion_estimation"],
                # Group 5: Observation (parallel)
                ["phi_computation", "entropy_computation"]
            ],
            skip_blocks=set()
        )

        # High-risk intent: Sequential processing for safety
        self.configs["high_risk"] = IntentBasedGroupConfig(
            intent="high_risk",
            parallel_groups=[
                # Group 1: Safety checks (sequential for high-risk)
                ["input_safety_gate"],
                # Group 2: Observation (can still be parallel)
                ["phi_computation", "entropy_computation"]
            ],
            skip_blocks={
                "context_retrieval_rag",  # Skip RAG for safety
                "cognitive_layer",  # Skip cognitive processing
                "narrative_layer"  # Skip narrative generation
            }
        )

        # Conversation intent: Balanced processing
        self.configs["conversation"] = IntentBasedGroupConfig(
            intent="conversation",
            parallel_groups=[
                # Group 1: Perception (parallel)
                ["intent_classification", "input_safety_gate"],
                # Group 2: Context & Prediction (parallel)
                ["context_retrieval_rag", "ukf_predict"],
                # Group 3: State update (parallel)
                ["neurotransmitter_memory_growth", "emotion_estimation"],
                # Group 4: Observation (parallel)
                ["phi_computation", "entropy_computation"]
            ],
            skip_blocks=set()
        )

        # Command intent: Fast processing
        self.configs["command"] = IntentBasedGroupConfig(
            intent="command",
            parallel_groups=[
                # Group 1: Perception (parallel)
                ["intent_classification", "input_safety_gate"],
                # Group 2: Observation (parallel)
                ["phi_computation", "entropy_computation"]
            ],
            skip_blocks={
                "context_retrieval_rag",  # Skip RAG for commands
                "cognitive_layer",  # Skip cognitive processing
                "ukf_predict"  # Skip prediction
            }
        )

    def get_groups_for_intent(
        self,
        intent: Optional[str],
        block_order: List[str],
        executed_blocks: Set[str]
    ) -> List[ParallelGroup]:
        """
        Get parallel groups for specific intent.

        Args:
            intent: Intent type (greeting, question, command, etc.)
            block_order: Canonical block order
            executed_blocks: Already executed blocks

        Returns:
            List of ParallelGroup objects
        """
        if not intent:
            # Default: no dynamic grouping
            return []

        config = self.configs.get(intent.lower())
        if not config:
            # Unknown intent: use default (no dynamic grouping)
            logger.debug(f"Unknown intent for dynamic grouping: {intent}")
            return []

        # Build parallel groups from config
        groups = []

        for group_block_ids in config.parallel_groups:
            # Filter out already executed blocks
            available_blocks = [
                block_id for block_id in group_block_ids
                if block_id not in executed_blocks and block_id in block_order
            ]

            if len(available_blocks) > 1:
                # Create parallel group
                group = ParallelGroup(
                    block_ids=available_blocks,
                    dependencies=set(),  # Dependencies handled by orchestrator
                    read_only=False
                )
                groups.append(group)
            elif len(available_blocks) == 1:
                # Single block, no parallel execution needed
                pass

        logger.debug(f"Dynamic groups for intent '{intent}': {len(groups)} groups")

        return groups

    def get_blocks_to_skip_for_intent(self, intent: Optional[str]) -> Set[str]:
        """
        Get blocks to skip for specific intent.

        Args:
            intent: Intent type

        Returns:
            Set of block IDs to skip
        """
        if not intent:
            return set()

        config = self.configs.get(intent.lower())
        if not config:
            return set()

        return config.skip_blocks.copy()

    def should_preserve_block(
        self,
        block_id: str,
        intent: Optional[str]
    ) -> bool:
        """
        Check if block should be preserved (always run) for intent.

        Args:
            block_id: Block ID
            intent: Intent type

        Returns:
            True if block should be preserved, False otherwise
        """
        if not intent:
            return False

        config = self.configs.get(intent.lower())
        if not config:
            return False

        return block_id in config.preserve_blocks

