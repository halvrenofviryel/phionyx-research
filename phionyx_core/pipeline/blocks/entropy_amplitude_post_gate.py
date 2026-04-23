"""
Entropy Amplitude Post Gate Block
===================================

Block: entropy_amplitude_post_gate
Gate that checks entropy/amplitude after narrative generation.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

logger = logging.getLogger(__name__)


class EntropyAmplitudeGateProtocol(Protocol):
    """Protocol for entropy/amplitude gating."""
    def apply_gate(
        self,
        physics_state: Dict[str, Any]
    ) -> Dict[str, Any]:  # Returns gated physics_state
        """Apply entropy/amplitude gate."""
        ...


class EntropyAmplitudePostGateBlock(PipelineBlock):
    """
    Entropy Amplitude Post Gate Block.

    Applies entropy/amplitude gate after narrative generation.
    """

    def __init__(self, gate: Optional[EntropyAmplitudeGateProtocol] = None):
        """
        Initialize block.

        Args:
            gate: Entropy/amplitude gate service
        """
        super().__init__("entropy_amplitude_post_gate")
        self.gate = gate

    def should_skip(self, context: BlockContext) -> Optional[str]:
        """Never skip — inline fallback handles missing gate service."""
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute entropy/amplitude post gate.

        When the injected gate service is available it is used.  Otherwise an
        inline fallback checks entropy + coherence: if entropy > 0.8 AND
        coherence < 0.7, the response is flagged for downstream awareness.
        """
        try:
            metadata = context.metadata or {}
            physics_state = metadata.get("physics_state", {})

            if not physics_state:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"physics_state": {}, "gate_action": "pass"},
                )

            if self.gate:
                gated_physics_state = self.gate.apply_gate(physics_state=physics_state)
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"physics_state": gated_physics_state, "gate_action": "delegated"},
                )

            # Inline fallback: post-narrative entropy + coherence check
            entropy = physics_state.get("entropy", 0.5)
            coherence_result = metadata.get("coherence_qa_result", {})
            coherence = (
                coherence_result.get("coherence_score", 1.0)
                if isinstance(coherence_result, dict) else 1.0
            )

            if entropy > 0.8 and coherence < 0.7:
                metadata["entropy_gate_warning"] = True
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "physics_state": physics_state,
                        "gate_action": "flagged",
                        "entropy": entropy,
                        "coherence": coherence,
                    },
                )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "physics_state": physics_state,
                    "gate_action": "pass",
                },
            )
        except Exception as e:
            logger.error(f"Entropy amplitude post gate failed: {e}", exc_info=True)
            metadata = context.metadata or {}
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "physics_state": metadata.get("physics_state", {}),
                    "error": str(e),
                },
            )

