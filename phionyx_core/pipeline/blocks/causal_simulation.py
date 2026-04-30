"""
Causal Simulation Block
=========================

Block: causal_simulation
Forward simulation — predicts state changes before applying actions.

Position in pipeline: After root_cause_analysis, before response_build.
"""

import logging

from ..base import BlockContext, BlockResult, PipelineBlock

logger = logging.getLogger(__name__)


class CausalSimulationBlock(PipelineBlock):
    """
    Causal Simulation Block (S4 Causality Advanced Sprint).

    Previews the risk of proposed state changes and simulates
    forward effects before they're applied to the real state.
    """

    def __init__(self, causal_simulator=None):
        """
        Args:
            causal_simulator: CausalSimulator instance (injected via DI)
        """
        super().__init__("causal_simulation")
        self._simulator = causal_simulator

    async def execute(self, context: BlockContext) -> BlockResult:
        if self._simulator is None:
            return BlockResult(
                block_id=self.block_id,
                status="skipped",
                data={"reason": "No CausalSimulator instance configured"}
            )

        try:
            metadata = context.metadata or {}

            # Get proposed state changes from intervention or strategy
            intervention_data = metadata.get("causal_intervention", {})
            if isinstance(intervention_data, dict) and intervention_data.get("intervention_applied"):
                interventions = {}
                for var, info in intervention_data.get("interventions", {}).items():
                    interventions[var] = info.get("new_value", 0.5)
            else:
                # No intervention — simulate current trajectory
                physics_state = metadata.get("physics_state", {})
                interventions = {}
                for key in ("entropy", "phi", "valence", "arousal"):
                    val = physics_state.get(key)
                    if val is not None:
                        interventions[key] = val

            if not interventions:
                return BlockResult(
                    block_id=self.block_id,
                    status="ok",
                    data={"simulation_run": False, "reason": "No variables to simulate"}
                )

            # Preview risk
            risk = self._simulator.preview_risk(interventions)

            # Simulate one step forward
            sim_result = self._simulator.simulate_step(interventions)

            return BlockResult(
                block_id=self.block_id,
                status="ok",
                data={
                    "simulation_run": True,
                    "risk_assessment": risk,
                    "variables_affected": sim_result.total_variables_affected,
                    "final_state": sim_result.final_state,
                    "risk_level": risk.get("overall_risk", "low"),
                }
            )

        except Exception as e:
            logger.error(f"Causal simulation error: {e}", exc_info=True)
            return BlockResult(
                block_id=self.block_id,
                status="error",
                data={"error": str(e)}
            )

    def get_dependencies(self) -> list:
        return ["causal_graph_update"]
