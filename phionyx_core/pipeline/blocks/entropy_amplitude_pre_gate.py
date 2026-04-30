"""
Entropy Amplitude Pre Gate Block
==================================

Block: entropy_amplitude_pre_gate
Gate that checks entropy/amplitude before CEP evaluation.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class EntropyAmplitudeGateProtocol(Protocol):
    """Protocol for entropy/amplitude gating."""
    def apply_gate(
        self,
        cognitive_state: Any,
        unified_state: Any | None,
        enhanced_context_string: str
    ) -> tuple[str, Any | None]:  # Returns (enhanced_context_string, gated_state)
        """Apply entropy/amplitude gate."""
        ...


class EntropyAmplitudePreGateBlock(PipelineBlock):
    """
    Entropy Amplitude Pre Gate Block.

    Applies entropy/amplitude gate before CEP evaluation.
    """

    def __init__(self, gate: EntropyAmplitudeGateProtocol | None = None):
        """
        Initialize block.

        Args:
            gate: Entropy/amplitude gate service
        """
        super().__init__("entropy_amplitude_pre_gate")
        self.gate = gate

    def should_skip(self, context: BlockContext) -> str | None:
        """Never skip — inline fallback handles missing gate service."""
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute entropy/amplitude pre gate.

        When the injected gate service is available it is used.  Otherwise an
        inline fallback injects a high-uncertainty warning into the context
        string when entropy exceeds the 0.8 threshold.
        """
        try:
            metadata = context.metadata or {}
            enhanced_context_string = metadata.get("enhanced_context_string", "")
            entropy = context.current_entropy

            if self.gate:
                cognitive_state = metadata.get("cognitive_state")
                unified_state = metadata.get("unified_state")
                enhanced_context_string, gated_state = self.gate.apply_gate(
                    cognitive_state=cognitive_state,
                    unified_state=unified_state,
                    enhanced_context_string=enhanced_context_string,
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "enhanced_context_string": enhanced_context_string,
                        "gated_state": gated_state,
                        "gate_action": "delegated",
                    },
                )

            # Inline fallback gating
            if entropy is not None and entropy > 0.8:
                warning = (
                    "[HIGH UNCERTAINTY] Current cognitive entropy is elevated. "
                    "Prioritize factual, verifiable information."
                )
                enhanced_context_string = enhanced_context_string + "\n\n" + warning
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "enhanced_context_string": enhanced_context_string,
                        "gate_action": "warning_injected",
                        "entropy": entropy,
                    },
                )

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "enhanced_context_string": enhanced_context_string,
                    "gate_action": "pass",
                    "entropy": entropy,
                },
            )
        except Exception as e:
            logger.error(f"Entropy amplitude pre gate failed: {e}", exc_info=True)
            metadata = context.metadata or {}
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "enhanced_context_string": metadata.get("enhanced_context_string", ""),
                    "error": str(e),
                },
            )

