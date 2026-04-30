"""
Memory Consolidation Block
============================

Block: memory_consolidation
Consolidates episodic memories into semantic knowledge via clustering and promotion.

Position in pipeline: After audit_layer (post-response), end of pipeline.
"""

import logging

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class MemoryConsolidationBlock(PipelineBlock):
    """
    Memory Consolidation Block (S2 Self-Awareness Sprint).

    Periodically consolidates episodic memories into semantic knowledge.
    Clusters similar memories, promotes frequently accessed ones,
    and decays weak memories.
    """

    def __init__(self, memory_consolidator=None, consolidation_interval: int = 5):
        """
        Args:
            memory_consolidator: MemoryConsolidator instance (injected via DI)
            consolidation_interval: Run consolidation every N turns
        """
        super().__init__("memory_consolidation")
        self._consolidator = memory_consolidator
        self._interval = consolidation_interval
        self._turn_count = 0

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._consolidator is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No MemoryConsolidator instance configured"}
            )

        try:
            self._turn_count += 1
            metadata = context.metadata or {}

            # Only consolidate every N turns
            if self._turn_count % self._interval != 0:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "consolidation_run": False,
                        "turns_until_next": self._interval - (self._turn_count % self._interval),
                    }
                )

            # Channel 4: Consume priority boosts from outcome_feedback (set in previous turn)
            boost_ids = metadata.get("_feedback_memory_boost_ids", [])
            if boost_ids:
                try:
                    self._consolidator.set_priority_boost(boost_ids, boost=1.5)
                    logger.info(f"[MEMORY_BOOST] Applied boost to {len(boost_ids)} memories")
                except Exception as boost_err:
                    logger.warning(f"[MEMORY_BOOST] skipped: {boost_err}")

            # Get memories from context
            memories = metadata.get("memories", [])
            if not memories:
                # Clear boosts even if no memories to consolidate
                if boost_ids:
                    self._consolidator.clear_priority_boosts()
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"consolidation_run": False, "reason": "No memories to consolidate",
                           "boost_applied": len(boost_ids)}
                )

            # Run consolidation
            result = self._consolidator.consolidate(memories)

            # Clear priority boosts after consolidation has used them
            if boost_ids:
                self._consolidator.clear_priority_boosts()

            result_data = {
                "consolidation_run": True,
                "consolidated_count": result.consolidated_count,
                "promoted_count": result.promoted_count,
                "decayed_count": result.decayed_count,
                "candidates_found": len(result.candidates),
                "timestamp": result.timestamp,
                "boost_applied": len(boost_ids),
            }

            logger.info(
                f"[MEMORY_CONSOLIDATION] Consolidated: {result.consolidated_count}, "
                f"Promoted: {result.promoted_count}, Decayed: {result.decayed_count}"
            )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=result_data,
            )

        except Exception as e:
            logger.error(f"Memory consolidation error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["audit_layer"]
