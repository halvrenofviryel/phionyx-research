"""
Learning Gate Block — v3.0.0
================================

Block: learning_gate
Position: After audit_layer
v4 Schema: LearningUpdate

Gates learning updates through boundary zone checks.
"""

import logging
from typing import Optional, Protocol, List, Any

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class LearningGateServiceProtocol(Protocol):
    """Protocol for learning gate service."""
    async def evaluate_updates(self, updates: List[Any]) -> List[Any]: ...
    async def apply_approved(self, updates: List[Any]) -> int: ...


class LearningGateBlock(PipelineBlock):
    """
    Gates learning parameter updates through boundary zone checks.

    Immutable zone: always rejected.
    Gated zone: requires approval.
    Adaptive zone: auto-approved within bounds.
    """

    def __init__(self, gate_service: Optional[LearningGateServiceProtocol] = None):
        super().__init__("learning_gate")
        if gate_service is None:
            # Contract v1.0 §7 / §9.3: a decision must NEVER be made without an audit
            # trail. Default to the real service (which records every decision) rather
            # than a silent ad-hoc fallback that decided without emitting a record.
            from ...services.learning_gate_service import LearningGateService
            gate_service = LearningGateService()
        self.gate_service = gate_service

    def should_skip(self, context: BlockContext) -> Optional[str]:
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

            # Single path: the service evaluates AND records every decision (§7).
            evaluated = await self.gate_service.evaluate_updates(pending_updates)
            approved = [u for u in evaluated if getattr(u, "gate_decision", "") == "approved"]
            approved_count = await self.gate_service.apply_approved(approved)
            rejected_count = len(evaluated) - len(approved)

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
            # Fail-CLOSED: a governance gate must never report success on failure.
            # Nothing is approved/applied (updates_approved=0) and the block signals
            # an error rather than masking it as "ok" (the prior behaviour).
            logger.error(f"Learning gate failed (fail-closed): {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                error=e,  # surface the exception so the orchestrator telemetry records it
                data={
                    "updates_processed": 0,
                    "updates_approved": 0,
                    "error": str(e),
                    "fail_closed": True,
                },
            )

    def get_dependencies(self) -> list[str]:
        return ["outcome_feedback"]
