"""
Drive Coherence Update Block
==============================

Block: drive_coherence_update
Updates narrative drive intensity and coherence metrics in the unified state
based on physics parameters (arousal, entropy, phi) and coherence QA results.
Drive = arousal * (1 - entropy) * min(phi, 1.0).
"""

import logging
from typing import Any, Protocol

from ...base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class DriveCoherenceUpdaterProtocol(Protocol):
    """Protocol for drive/coherence update."""
    def update_drive_coherence(
        self,
        unified_state: Any,
        narrative_response: str,
        physics_state: dict[str, Any]
    ) -> Any:
        """Update narrative drive and coherence."""
        ...


class DriveCoherenceUpdateBlock(PipelineBlock):
    """
    Drive Coherence Update Block.

    Updates drive intensity and coherence metrics in the unified state based on
    physics parameters and coherence QA results from the upstream coherence_qa
    block.  When no external updater is injected, the block computes drive and
    coherence inline (fail-open design).
    """

    def __init__(self, updater: DriveCoherenceUpdaterProtocol | None = None):
        super().__init__("drive_coherence_update")
        self.updater = updater

    async def execute(self, context: BlockContext) -> BlockResult:
        try:
            metadata = context.metadata or {}
            unified_state = metadata.get("unified_state")
            physics_state = metadata.get("physics_state", {})

            # Delegate to injected updater if available
            if self.updater and unified_state:
                narrative_response = metadata.get("narrative_text", "")
                updated = self.updater.update_drive_coherence(
                    unified_state=unified_state,
                    narrative_response=narrative_response,
                    physics_state=physics_state,
                )
                drive_result: dict[str, Any] = {"drive": None, "coherence": None, "source": "injected"}
                context.metadata["drive_update_result"] = drive_result
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"unified_state": updated, "drive_update_result": drive_result},
                )

            # --- Inline drive/coherence computation ---
            phi = float(physics_state.get("phi", 0.5))
            entropy = float(physics_state.get("entropy", 0.5))
            arousal = float(physics_state.get("arousal", 0.5))

            # Drive: narrative force intensity
            drive = arousal * (1.0 - entropy) * min(phi, 1.0)
            drive = max(0.0, min(1.0, drive))

            # Coherence: prefer QA result from upstream coherence_qa block
            qa_result = metadata.get("coherence_qa_result", {})
            if qa_result and "coherence_score" in qa_result:
                coherence = float(qa_result["coherence_score"])
                source = "coherence_qa"
            else:
                # Physics-based fallback
                coherence = max(0.0, min(1.0, 1.0 - entropy * 0.3))
                source = "physics_fallback"

            # Update unified_state if available
            if unified_state is not None:
                if isinstance(unified_state, dict):
                    unified_state["drive"] = drive
                    unified_state["coherence"] = coherence
                else:
                    if hasattr(unified_state, "drive"):
                        unified_state.drive = drive
                    if hasattr(unified_state, "coherence"):
                        unified_state.coherence = coherence

            drive_result = {
                "drive": drive,
                "coherence": coherence,
                "source": source,
            }

            # Enrich metadata for downstream blocks
            context.metadata["drive_update_result"] = drive_result

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": unified_state,
                    "drive_update_result": drive_result,
                },
            )
        except Exception as e:
            logger.error(f"Drive/coherence update failed: {e}", exc_info=True)
            # Fail-open: return original unified_state
            metadata = context.metadata or {}
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "unified_state": metadata.get("unified_state"),
                    "error": str(e),
                },
            )

