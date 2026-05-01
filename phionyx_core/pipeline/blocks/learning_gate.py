"""
Learning Gate Block — v3.0.0
================================

Block: learning_gate
Position: After audit_layer
v4 Schema: LearningUpdate

Gates learning updates through boundary zone checks.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class LearningGateServiceProtocol(Protocol):
    """Protocol for learning gate service."""
    async def evaluate_updates(self, updates: list[Any]) -> list[Any]: ...
    async def apply_approved(self, updates: list[Any]) -> int: ...


class LearningGateBlock(PipelineBlock):
    """
    Gates learning parameter updates through boundary zone checks.

    Immutable zone: always rejected.
    Gated zone: requires approval.
    Adaptive zone: auto-approved within bounds.
    """

    def __init__(self, gate_service: LearningGateServiceProtocol | None = None):
        super().__init__("learning_gate")
        self.gate_service = gate_service

    def should_skip(self, context: BlockContext) -> str | None:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            metadata = context.metadata or {}
            pending_updates = metadata.get("learning_updates", [])

            if not pending_updates:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"updates_processed": 0, "updates_approved": 0},
                )

            approved_count = 0
            rejected_count = 0

            if self.gate_service:
                evaluated = await self.gate_service.evaluate_updates(pending_updates)
                approved = [u for u in evaluated if getattr(u, "gate_decision", "") == "approved"]
                approved_count = await self.gate_service.apply_approved(approved)
                rejected_count = len(evaluated) - len(approved)
            else:
                # Default: approve adaptive, reject immutable, defer gated
                from ...contracts.v4.learning_update import LearningGateDecision, LearningUpdate

                for update in pending_updates:
                    if isinstance(update, LearningUpdate):
                        if update.boundary_zone == "immutable":
                            update.gate_decision = LearningGateDecision.REJECTED
                            update.gate_reason = "Immutable boundary zone"
                            rejected_count += 1
                        elif update.boundary_zone == "gated":
                            update.gate_decision = LearningGateDecision.PENDING
                            update.gate_reason = "Requires human approval"
                        else:
                            update.gate_decision = LearningGateDecision.APPROVED
                            update.gate_reason = "Adaptive zone — auto-approved"
                            approved_count += 1

            context.v4_learning_updates = pending_updates

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "updates_processed": len(pending_updates),
                    "updates_approved": approved_count,
                    "updates_rejected": rejected_count,
                },
            )
        except Exception as e:
            logger.error(f"Learning gate failed: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"updates_processed": 0, "error": str(e)},
            )

    def get_dependencies(self) -> list[str]:
        return ["outcome_feedback"]
