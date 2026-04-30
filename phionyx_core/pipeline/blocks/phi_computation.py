"""
Phi Computation Block
=====================

Block: phi_computation
Computes phi (integrated information) value from physics state.
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class PhiComputationProtocol(Protocol):
    """Protocol for phi computation."""
    def compute_phi(
        self,
        physics_state: dict[str, Any],
        previous_phi: float | None = None
    ) -> dict[str, Any]:
        """Compute phi value from physics state."""
        ...


class PhiComputationBlock(PipelineBlock):
    """
    Phi Computation Block.

    Computes phi (integrated information) from physics state.
    This is an always-on block.
    """

    def __init__(self, phi_computer: PhiComputationProtocol | None = None):
        """
        Initialize block.

        Args:
            phi_computer: Service that computes phi
        """
        super().__init__("phi_computation")
        self.phi_computer = phi_computer

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute phi computation.

        Args:
            context: Block context with physics_state

        Returns:
            BlockResult with phi value and components
        """
        try:
            # Get physics_state from context metadata
            metadata = context.metadata or {}
            physics_state = metadata.get("physics_state", {})

            # CRITICAL: Ensure physics_state is a dictionary, not a Mock object
            if not isinstance(physics_state, dict):
                logger.warning(f"physics_state is not a dictionary (type: {type(physics_state)}), creating new dictionary")
                physics_state = {}

            # CRITICAL: Get valence/arousal from EchoState2 (unified_state) if available
            # This ensures we use profile/state-based values, not hardcoded defaults
            unified_state = metadata.get("unified_state")
            valence = None
            arousal = None

            if unified_state:
                # Try to get V (Valence) and A (Arousal) from EchoState2
                try:
                    if hasattr(unified_state, 'V'):
                        valence = float(unified_state.V)
                    elif hasattr(unified_state, 'valence'):
                        valence = float(unified_state.valence)

                    if hasattr(unified_state, 'A'):
                        arousal = float(unified_state.A)
                    elif hasattr(unified_state, 'arousal'):
                        arousal = float(unified_state.arousal)
                except (AttributeError, ValueError, TypeError) as e:
                    logger.debug(f"Could not extract V/A from unified_state: {e}")

            # Get valence/arousal from physics_state (set by emotion_estimation block)
            if "valence" in physics_state:
                valence = physics_state["valence"]
            if "arousal" in physics_state:
                arousal = physics_state["arousal"]

            # Get from profile/config if available (metadata)
            if valence is None:
                valence = metadata.get("valence")
            if arousal is None:
                arousal = metadata.get("arousal")

            # CRITICAL: Use profile defaults (EchoState2 defaults: V=0.0, A=0.5)
            # NOT hardcoded values - these come from EchoState2 model defaults
            # EchoState2.defaults: V=0.0, A=0.5 (from schema)
            if valence is None:
                valence = 0.0  # EchoState2 default V
                logger.debug("Using EchoState2 default valence: 0.0 (from schema)")
            if arousal is None:
                arousal = 0.5  # EchoState2 default A
                logger.debug("Using EchoState2 default arousal: 0.5 (from schema)")

            # Build/update physics_state with all values
            if not physics_state:
                physics_state = {}

            physics_state["entropy"] = physics_state.get("entropy", context.current_entropy or 0.5)
            physics_state["valence"] = valence
            physics_state["arousal"] = arousal
            physics_state["stability"] = physics_state.get("stability", 0.8)  # Default from formulas

            # Get previous_phi from context
            previous_phi = context.previous_phi

            # Compute phi
            if self.phi_computer:
                phi_result = self.phi_computer.compute_phi(
                    physics_state=physics_state,
                    previous_phi=previous_phi
                )
                # Handle both dict and scalar return values
                if not isinstance(phi_result, dict):
                    phi_result = {"phi": phi_result, "components": {}}
            else:
                # Fallback: use real calculate_phi_cognitive formula
                # (block_factory normally injects a phi_computer, but this
                # provides defense-in-depth for direct instantiation)
                try:
                    from phionyx_core.physics.formulas import calculate_phi_cognitive
                    entropy = float(physics_state.get("entropy", 0.5))
                    stability = float(physics_state.get("stability", 0.8))
                    phi_val = calculate_phi_cognitive(
                        entropy=entropy,
                        stability=stability,
                        valence=float(valence),
                    )
                    phi_result = {
                        "phi": phi_val,
                        "components": {
                            "entropy": entropy,
                            "stability": stability,
                            "valence": valence,
                            "source": "calculate_phi_cognitive_inline",
                        }
                    }
                except Exception as fallback_err:
                    logger.warning(f"calculate_phi_cognitive failed: {fallback_err}")
                    entropy = float(physics_state.get("entropy", 0.5))
                    phi_result = {
                        "phi": max(0.05, min(1.0, (1.0 - entropy) * 0.8)),
                        "components": {"entropy": entropy, "source": "heuristic_fallback"}
                    }

            # Update context with computed phi
            computed_phi = phi_result.get("phi", 0.5)
            context.previous_phi = computed_phi
            if context.metadata is None:
                context.metadata = {}
            context.metadata["previous_phi"] = computed_phi

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "phi": computed_phi,
                    "phi_components": phi_result.get("components", {}),
                    "phi_result": phi_result
                }
            )
        except Exception as e:
            logger.error(f"Phi computation failed: {e}", exc_info=True)
            # Fail-open: return default phi
            return BlockResult(
                block_id=self.block_id,
                status="ok",  # Don't fail pipeline on phi computation error
                data={
                    "phi": 0.5,
                    "phi_components": {},
                    "error": str(e)
                }
            )

