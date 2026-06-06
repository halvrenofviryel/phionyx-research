"""
Ethics Pre Response Block
==========================

Block: ethics_pre_response
Ethics check before narrative generation.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class EthicsProcessorProtocol(Protocol):
    """Protocol for ethics processing."""
    def check_ethics_pre_response(
        self,
        frame: Any,
        user_input: str,
        cognitive_state: Any
    ) -> Dict[str, Any]:  # Returns ethics_result
        """Check ethics before response."""
        ...


class EthicsPreResponseBlock(PipelineBlock):
    """
    Ethics Pre Response Block.

    Performs ethics check before narrative generation.
    """

    def __init__(self, processor: Optional[EthicsProcessorProtocol] = None):
        """
        Initialize block.

        Args:
            processor: Ethics processor
        """
        super().__init__("ethics_pre_response")
        self.processor = processor

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute ethics pre response check.

        Args:
            context: Block context with frame and inputs

        Returns:
            BlockResult with ethics_result
        """
        try:
            # Get frame from metadata
            metadata = context.metadata or {}
            frame = metadata.get("frame")
            cognitive_state = metadata.get("cognitive_state")

            if not frame:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"ethics_result": None}
                )

            # Check ethics
            if self.processor:
                # Check if processor method is async
                import inspect
                if hasattr(self.processor, 'check_ethics_pre_response'):
                    check_method = self.processor.check_ethics_pre_response
                    if inspect.iscoroutinefunction(check_method):
                        # Async method - await it
                        ethics_result = await check_method(
                            frame=frame,
                            user_input=context.user_input,
                            cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None)
                        )
                    else:
                        # Sync method - call directly
                        ethics_result = check_method(
                            frame=frame,
                            user_input=context.user_input,
                            cognitive_state=cognitive_state or getattr(frame, 'cognitive_state', None)
                        )
                else:
                    # Fallback: use assess_ethics_pre_response if available
                    if hasattr(self.processor, 'assess_ethics_pre_response'):
                        ethics_result = self.processor.assess_ethics_pre_response(
                            user_input=context.user_input,
                            unified_state=None,
                            current_entropy=0.5,
                            valence_from_emotion=0.0,
                            arousal_from_emotion=0.5
                        )
                        # Convert to expected format
                        ethics_result = {
                            "status": ethics_result.get("status", "ok"),
                            "risk_level": ethics_result.get("risk_level", 0.0),
                            "reason": ethics_result.get("reason"),
                            "harm_risk": ethics_result.get("risk_level", 0.0)
                        }
                    else:
                        ethics_result = None
            else:
                ethics_result = None

            # Include harm_risk directly in data for test compatibility
            data = {
                "ethics_result": ethics_result
            }
            # Also include harm_risk directly if available
            if ethics_result:
                if isinstance(ethics_result, dict):
                    data["harm_risk"] = ethics_result.get("harm_risk", ethics_result.get("risk_level", 0.0))
                    data["risk_level"] = ethics_result.get("risk_level", 0.0)
                    data["status"] = ethics_result.get("status", "ok")
                elif hasattr(ethics_result, 'harm_risk'):
                    data["harm_risk"] = ethics_result.harm_risk
                elif hasattr(ethics_result, 'risk_level'):
                    data["harm_risk"] = ethics_result.risk_level
                    data["risk_level"] = ethics_result.risk_level

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data=data
            )
        except Exception as e:
            logger.error(f"Ethics pre response check failed: {e}", exc_info=True)
            # Fail-open: continue without ethics check
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "ethics_result": None,
                    "error": str(e)
                }
            )

