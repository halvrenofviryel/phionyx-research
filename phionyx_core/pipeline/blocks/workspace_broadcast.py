"""
Workspace Broadcast Block — v3.0.0
=====================================

Block: workspace_broadcast
Position: After behavioral_drift_detection
v4 Schema: WorkspaceEvent

Implements Global Workspace Theory broadcast.
High-salience events are broadcast to all subscribed modules.
"""

import logging
from typing import Optional, Protocol, List, Any

from ..base import PipelineBlock, BlockContext, BlockResult

from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    errored,
)

logger = logging.getLogger(__name__)


class GlobalWorkspaceProtocol(Protocol):
    """Protocol for global workspace service."""
    async def broadcast(self, event: Any) -> None: ...
    async def get_pending_events(self) -> List[Any]: ...


class WorkspaceBroadcastBlock(PipelineBlock):
    """
    Broadcasts significant events via Global Workspace.

    Collects high-salience events from the current turn
    and broadcasts them to subscribed modules.
    """

    def __init__(self, workspace: Optional[GlobalWorkspaceProtocol] = None):
        super().__init__("workspace_broadcast")
        self.workspace = workspace

    def should_skip(self, context: BlockContext) -> Optional[str]:
        if context.pipeline_version < "3.0.0":
            return "v4_block_requires_pipeline_v3"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            from ...contracts.v4.workspace_event import WorkspaceEvent, SalienceLevel

            metadata = context.metadata or {}
            events_broadcast = 0

            # Detect significant events from current turn
            drift_report = metadata.get("drift_report")
            ethics_result = metadata.get("ethics_result", {})

            events = []

            # Drift event
            if drift_report and drift_report.get("drift_detected"):
                events.append(WorkspaceEvent(
                    event_type="behavioral_drift",
                    salience=SalienceLevel.HIGH,
                    salience_score=0.9,
                    source_module="behavioral_drift_detection",
                    payload={"drift_report": drift_report},
                ))

            # Ethics enforcement event
            if ethics_result.get("enforced"):
                events.append(WorkspaceEvent(
                    event_type="ethics_enforcement",
                    salience=SalienceLevel.CRITICAL,
                    salience_score=1.0,
                    source_module="ethics_engine",
                    payload={"triggered_risks": ethics_result.get("triggered_risks", [])},
                ))

            # Broadcast events
            if self.workspace:
                for event in events:
                    await self.workspace.broadcast(event)
                    events_broadcast += 1

            context.v4_workspace_events = events

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={"events_broadcast": events_broadcast},
            )
        except Exception as e:
            logger.error(f"Workspace broadcast failed: {e}", exc_info=True)
            # Control channel unchanged — this block stays fail-open so the
            # pipeline still completes, and the `return BlockResult(...)`
            # shape is kept so the inventory sweep can still see it. What
            # changes is the record: block_run_status FAILED, measurement
            # ERROR, operating_mode degraded — a crash here can no longer
            # read as a clean measurement.
            _outcome = BlockOutcome(
                block_id=self.block_id,
                legacy_control_status="ok",
                block_run_status=BlockRunStatus.FAILED,
                measurement=errored(
                    "workspace broadcast raised",
                    inputs_present=True,
                    exception=type(e).__name__,
                ),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={**({"events_broadcast": 0, "error": str(e)}), "block_outcome": _outcome.to_record_fields()},
            )

    def get_dependencies(self) -> list[str]:
        return ["behavioral_drift_detection"]
