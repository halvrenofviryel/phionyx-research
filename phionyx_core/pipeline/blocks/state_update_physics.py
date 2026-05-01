"""
State Update Physics Block
===========================

Block: state_update_physics
Final physics state update (always-on block).
"""

import logging
from typing import Any, Protocol

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class PhysicsStateUpdaterProtocol(Protocol):
    """Protocol for physics state update."""
    def update_physics_state(
        self,
        physics_state: dict[str, Any],
        unified_state: Any | None
    ) -> dict[str, Any]:  # Returns updated physics_state
        """Update physics state from unified state."""
        ...


class StateUpdatePhysicsBlock(PipelineBlock):
    """
    State Update Physics Block.

    Final physics state update (always-on block).
    This block MUST ALWAYS run, even on early exit.
    """

    def __init__(self, updater: PhysicsStateUpdaterProtocol | None = None):
        """
        Initialize block.

        Args:
            updater: Physics state updater service
        """
        super().__init__("state_update_physics")
        self.updater = updater

    def should_skip(self, context: BlockContext) -> str | None:
        """Skip only if there is no physics_state at all — nothing to update."""
        metadata = context.metadata or {}
        # Run if physics_state exists (even without unified_state):
        # - UKF merge uses predicted_state + physics_state
        # - Pre-update snapshot is always useful
        # - unified_state copy is optional (lines 94-107)
        if not metadata.get("physics_state") and not metadata.get("unified_state"):
            return "no_physics_state_or_unified_state"
        return None

    async def execute(self, context: BlockContext) -> BlockResult:
        """
        Execute physics state update.

        Args:
            context: Block context with physics_state and unified_state

        Returns:
            BlockResult with updated physics_state
        """
        try:
            # Get physics_state and unified_state from metadata
            metadata = context.metadata or {}
            physics_state = metadata.get("physics_state", {})
            unified_state = metadata.get("unified_state")

            # Check for early exit
            early_exit = metadata.get("early_exit_triggered", False)
            if early_exit:
                # Minimal state update for early exit
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "physics_state": physics_state,
                        "early_exit": True
                    }
                )

            # Pre-update snapshot for rollback capability (SF1 Claim 15/17)
            pre_update_snapshot = dict(physics_state) if physics_state else {}
            metadata["_state_snapshot_pre_physics"] = pre_update_snapshot

            # Update physics state
            if self.updater and unified_state:
                updated_physics_state = self.updater.update_physics_state(
                    physics_state=physics_state,
                    unified_state=unified_state
                )
            else:
                # Fallback: update directly if unified_state available
                if unified_state:
                    if hasattr(unified_state, 'phi'):
                        physics_state['phi'] = unified_state.phi
                    if hasattr(unified_state, 'entropy'):
                        physics_state['entropy'] = unified_state.entropy
                    if hasattr(unified_state, 'valence'):
                        physics_state['valence'] = unified_state.valence
                    if hasattr(unified_state, 'arousal'):
                        physics_state['arousal'] = unified_state.arousal
                    if hasattr(unified_state, 'narrative_drive'):
                        physics_state['narrative_drive'] = unified_state.narrative_drive
                    if hasattr(unified_state, 'coherence'):
                        physics_state['coherence'] = unified_state.coherence
                updated_physics_state = physics_state

            # UKF predicted_state merge: adaptive Kalman-style alpha blending
            predicted_state = metadata.get("predicted_state")
            if predicted_state and isinstance(predicted_state, dict):
                _KEY_MAP = {
                    "phi": "phi_predicted",
                    "entropy": "entropy_predicted",
                    "valence": "V_predicted",
                    "arousal": "A_predicted",
                }
                for meas_key, pred_key in _KEY_MAP.items():
                    pred_val = predicted_state.get(pred_key, predicted_state.get(meas_key))
                    meas_val = updated_physics_state.get(meas_key)
                    if pred_val is not None and meas_val is not None:
                        try:
                            p = float(pred_val)
                            m = float(meas_val)
                            # Adaptive alpha: innovation = |prediction - measurement|
                            # Large innovation → distrust prediction (lower alpha)
                            # Small innovation → trust prediction (higher alpha)
                            innovation = abs(p - m)
                            # alpha ∈ [0.1, 0.5]: maps innovation [0,1] → alpha [0.5, 0.1]
                            alpha = max(0.1, 0.5 - innovation * 0.4)
                            updated_physics_state[meas_key] = alpha * p + (1 - alpha) * m
                        except (TypeError, ValueError):
                            pass  # Keep measured value on conversion error

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "physics_state": updated_physics_state
                }
            )
        except Exception as e:
            logger.error(f"Physics state update failed: {e}", exc_info=True)
            # Fail-open: return original physics_state
            metadata = context.metadata or {}
            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "physics_state": metadata.get("physics_state", {}),
                    "error": str(e)
                }
            )

