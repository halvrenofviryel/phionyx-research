"""
Phi Computation Block
=====================

Block: phi_computation
Computes phi (integrated information) value from physics state.
"""

import logging
from typing import Dict, Any, Optional, Protocol

from ..base import PipelineBlock, BlockContext, BlockResult

from ..outcome import (
    BlockOutcome,
    BlockRunStatus,
    errored,
    not_measured,
)

logger = logging.getLogger(__name__)


class PhiComputationProtocol(Protocol):
    """Protocol for phi computation."""
    def compute_phi(
        self,
        physics_state: Dict[str, Any],
        previous_phi: Optional[float] = None
    ) -> Dict[str, Any]:
        """Compute phi value from physics state."""
        ...


class PhiComputationBlock(PipelineBlock):
    """
    Phi Computation Block.

    Computes phi (integrated information) from physics state.
    This is an always-on block.
    """

    def __init__(self, phi_computer: Optional[PhiComputationProtocol] = None):
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

            # entropy and stability are REQUIRED parameters of
            # calculate_phi_cognitive — checked, they carry no defaults —
            # so there is nothing to fall back to. `context.current_entropy
            # or 0.5` reinstated the midpoint that entropy_computation was
            # changed to stop publishing, one block later, and the 0.8 sat
            # under a comment reading "Default from formulas" that is not
            # true of the formula.
            #
            # valence keeps its 0.0: that IS the formula's own default.
            # arousal keeps 0.5 and is not a formula input at all.
            if physics_state.get("entropy") is None:
                carried = context.current_entropy
                if carried is not None:
                    physics_state["entropy"] = carried
            physics_state["valence"] = valence
            physics_state["arousal"] = arousal

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
                # Two substitutions used to live here and both published a
                # phi that read as measured:
                #
                #   entropy 0.5 and stability 0.8 when absent, fed to the real
                #   formula and labelled `calculate_phi_cognitive_inline` —
                #   the same two constants removed from entropy_computation
                #   and the CEP evaluation;
                #
                #   a `(1 - entropy) * 0.8` heuristic when the formula raised,
                #   computed from that same substituted entropy.
                #
                # Together they meant the `computed_phi is None` branch below
                # could never be taken: every path guaranteed a phi. A
                # NOT_MEASURED record that no producer can reach is the shape
                # OD-19 names. Now the inputs are required and a failure
                # publishes nothing.
                entropy = physics_state.get("entropy")
                stability = physics_state.get("stability")
                absent = [name for name, value in
                          (("entropy", entropy), ("stability", stability))
                          if value is None]
                if absent or entropy is None or stability is None:
                    phi_result = {
                        "components": {"source": "inputs_absent"},
                        "unmeasured_inputs": absent,
                    }
                else:
                    measured_entropy = float(entropy)
                    measured_stability = float(stability)
                    try:
                        from phionyx_core.physics.formulas import calculate_phi_cognitive
                        phi_val = calculate_phi_cognitive(
                            entropy=measured_entropy,
                            stability=measured_stability,
                            valence=float(valence),
                        )
                        phi_result = {
                            "phi": phi_val,
                            "components": {
                                "entropy": measured_entropy,
                                "stability": measured_stability,
                                "valence": valence,
                                "source": "calculate_phi_cognitive_inline",
                            }
                        }
                    except Exception as fallback_err:
                        logger.warning(
                            "calculate_phi_cognitive failed: %s", fallback_err)
                        phi_result = {
                            "components": {"source": "formula_raised",
                                           "error": type(fallback_err).__name__},
                        }

            # `phi_result` without a phi used to read as 0.5 — the midpoint,
            # and the value confidence_fusion also defaults to. An engine that
            # returned no phi measured no phi, so nothing is published and
            # `previous_phi` is left alone rather than seeded with a midpoint
            # that the next turn would treat as last turn's measurement.
            computed_phi = phi_result.get("phi")
            if computed_phi is None:
                # Name what was missing. "returned a result carrying no phi"
                # was true of every case and told a reader nothing about
                # which: an absent input, a formula that raised, or an engine
                # that simply omitted the key.
                unmeasured = phi_result.get("unmeasured_inputs")
                source = (phi_result.get("components") or {}).get("source")
                if unmeasured:
                    reason = (f"phi needs {', '.join(unmeasured)} and the turn "
                              "carried neither a measured value nor a computer")
                elif source == "formula_raised":
                    reason = ("calculate_phi_cognitive raised; the heuristic "
                              "that used to stand in here was computed from a "
                              "substituted entropy")
                else:
                    reason = "the phi engine returned a result carrying no phi"
                _outcome = BlockOutcome(
                    block_id=self.block_id,
                    legacy_control_status="ok",
                    block_run_status=BlockRunStatus.COMPLETED,
                    measurement=not_measured(reason, cause="input_absent"),
                    operating_mode="degraded",
                )
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={
                        "phi_components": phi_result.get("components", {}),
                        "phi_result": phi_result,
                        "block_outcome": _outcome.to_record_fields(),
                    }
                )

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
                    "phi computation raised",
                    inputs_present=True,
                    exception=type(e).__name__,
                ),
                operating_mode="degraded",
            )
            return BlockResult(
                block_id=self.block_id,
                status="ok",  # Don't fail pipeline on phi computation error
                # No `phi`. It used to be 0.5 — the midpoint of the range,
                # published from a crash, and the same value confidence_fusion
                # defaults to. audit_layer already treats a missing phi as its
                # own case (audit_layer.py:127), so absence is a signal this
                # pipeline supports and a fabricated midpoint destroyed it.
                data={**({
                    "phi_components": {},
                    "error": str(e)
                }), "block_outcome": _outcome.to_record_fields()}
            )

