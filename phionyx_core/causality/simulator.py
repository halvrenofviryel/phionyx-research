"""
Causal Simulator — v4 §3 (AGI Layer 3)
========================================

Forward simulation: given current state + proposed action,
predict the next state by propagating through the causal graph.

"If I do X, what will happen to the system?"

Integrates with:
- causality/causal_graph.py (CausalGraph)
- causality/intervention.py (InterventionModel)
- contracts/v4/action_intent.py (ActionIntent for action modeling)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .causal_graph import CausalGraph
from .intervention import InterventionModel

logger = logging.getLogger(__name__)


@dataclass
class SimulationStep:
    """One step in forward simulation."""
    step_index: int
    interventions: Dict[str, float]  # variable → forced value
    state_before: Dict[str, Optional[float]]
    state_after: Dict[str, float]
    effects: List[Dict[str, Any]]  # Simplified InterventionEffect dicts
    delta_summary: Dict[str, float]  # variable → total delta


@dataclass
class SimulationResult:
    """Full simulation result over one or more steps."""
    steps: List[SimulationStep]
    initial_state: Dict[str, Optional[float]]
    final_state: Dict[str, float]
    total_variables_affected: int
    risk_assessment: Dict[str, Any]

    def get_final_value(self, variable: str) -> Optional[float]:
        return self.final_state.get(variable)

    def get_total_delta(self, variable: str) -> float:
        """Total change across all steps for a variable."""
        initial = self.initial_state.get(variable)
        final = self.final_state.get(variable)
        if initial is None or final is None:
            return 0.0
        return final - initial

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [
                {
                    "step": s.step_index,
                    "interventions": s.interventions,
                    "delta_summary": {
                        k: round(v, 4) for k, v in s.delta_summary.items()
                    },
                }
                for s in self.steps
            ],
            "initial_state": {
                k: v for k, v in self.initial_state.items() if v is not None
            },
            "final_state": {
                k: round(v, 4) for k, v in self.final_state.items()
            },
            "total_affected": self.total_variables_affected,
            "risk": self.risk_assessment,
        }


class CausalSimulator:
    """
    Forward simulation through causal graph.

    Usage:
        sim = CausalSimulator(causal_graph)

        # Single step: "What if entropy becomes 0.9?"
        result = sim.simulate_step({"entropy": 0.9})

        # Multi-step: sequence of actions
        result = sim.simulate_sequence([
            {"arousal": 0.8},       # Step 1: user becomes excited
            {"entropy": 0.7},       # Step 2: entropy rises
        ])

        # Risk preview: "Is this action safe?"
        risk = sim.preview_risk({"entropy": 0.95})
    """

    def __init__(
        self,
        graph: CausalGraph,
        attenuation_rate: float = 0.8,
        risk_thresholds: Optional[Dict[str, Tuple[float, float]]] = None,
    ):
        """
        Args:
            graph: Causal graph for simulation
            attenuation_rate: Effect decay per hop
            risk_thresholds: {variable: (low, high)} — values outside trigger risk
        """
        self.graph = graph
        self.attenuation_rate = attenuation_rate
        self.risk_thresholds = risk_thresholds or {
            "entropy": (0.0, 0.8),
            "drift": (0.0, 0.3),
            "coherence": (0.3, 1.0),
        }
        self._intervention_model = InterventionModel(
            graph,
            attenuation_rate=attenuation_rate,
        )

    def simulate_step(
        self,
        interventions: Dict[str, float],
    ) -> SimulationResult:
        """
        Simulate one step: apply interventions and predict effects.

        Args:
            interventions: {variable: new_value} dict

        Returns:
            SimulationResult with predicted state
        """
        return self.simulate_sequence([interventions])

    def simulate_sequence(
        self,
        steps: List[Dict[str, float]],
    ) -> SimulationResult:
        """
        Simulate a sequence of intervention steps.

        Each step builds on the state produced by the previous step.

        Args:
            steps: List of {variable: value} intervention dicts

        Returns:
            SimulationResult with all steps and final state
        """
        # Capture initial state
        initial_state: Dict[str, Optional[float]] = {
            nid: node.current_value
            for nid, node in self.graph.nodes.items()
        }
        current_state = dict(initial_state)

        sim_steps: List[SimulationStep] = []
        all_affected: set = set()

        for i, interventions in enumerate(steps):
            state_before = dict(current_state)

            # Apply all interventions in this step
            delta_summary: Dict[str, float] = {}
            all_effects: List[Dict[str, Any]] = []

            for var, val in interventions.items():
                result = self._intervention_model.do(var, val)
                # Update current state with intervention
                current_state[var] = val
                delta_summary[var] = val - (state_before.get(var) or 0.0)

                for effect in result.effects:
                    current_state[effect.node_id] = effect.new_value
                    delta_summary[effect.node_id] = (
                        delta_summary.get(effect.node_id, 0.0) + effect.delta
                    )
                    all_affected.add(effect.node_id)
                    all_effects.append({
                        "node": effect.node_id,
                        "delta": effect.delta,
                        "path": effect.causal_path,
                    })

            sim_steps.append(SimulationStep(
                step_index=i,
                interventions=interventions,
                state_before=state_before,
                state_after=dict(current_state),
                effects=all_effects,
                delta_summary=delta_summary,
            ))

            # Update graph node values for next step
            for nid, val in current_state.items():
                if nid in self.graph.nodes and val is not None:
                    self.graph.nodes[nid].current_value = val

        # Assess risk on final state
        risk = self._assess_risk(current_state)

        return SimulationResult(
            steps=sim_steps,
            initial_state=initial_state,
            final_state={k: v for k, v in current_state.items() if v is not None},
            total_variables_affected=len(all_affected),
            risk_assessment=risk,
        )

    def preview_risk(
        self,
        interventions: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Preview risk without applying changes.

        Returns risk assessment dict.
        """
        result = self.simulate_step(interventions)
        return result.risk_assessment

    def compare_actions(
        self,
        action_a: Dict[str, float],
        action_b: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Compare two possible actions.

        Returns:
            Dict with per-variable comparison and risk comparison
        """
        result_a = self.simulate_step(action_a)
        result_b = self.simulate_step(action_b)

        comparison = {
            "action_a": {
                "interventions": action_a,
                "affected": result_a.total_variables_affected,
                "risk": result_a.risk_assessment,
            },
            "action_b": {
                "interventions": action_b,
                "affected": result_b.total_variables_affected,
                "risk": result_b.risk_assessment,
            },
            "differences": {},
        }

        # Compare final states
        all_vars = set(result_a.final_state.keys()) | set(result_b.final_state.keys())
        for var in all_vars:
            val_a = result_a.final_state.get(var, 0.0)
            val_b = result_b.final_state.get(var, 0.0)
            if abs(val_a - val_b) > 0.001:
                comparison["differences"][var] = {
                    "action_a": round(val_a, 4),
                    "action_b": round(val_b, 4),
                    "delta": round(val_a - val_b, 4),
                }

        # Recommend the safer action
        risk_a = result_a.risk_assessment.get("risk_score", 0)
        risk_b = result_b.risk_assessment.get("risk_score", 0)
        comparison["recommendation"] = "action_a" if risk_a <= risk_b else "action_b"

        return comparison

    def _assess_risk(
        self,
        state: Dict[str, Optional[float]],
    ) -> Dict[str, Any]:
        """Assess risk of a state against thresholds."""
        violations: List[Dict[str, Any]] = []
        for var, (low, high) in self.risk_thresholds.items():
            val = state.get(var)
            if val is None:
                continue
            if val < low:
                violations.append({
                    "variable": var,
                    "value": round(val, 4),
                    "threshold": f"min={low}",
                    "severity": "high" if val < low - 0.2 else "medium",
                })
            elif val > high:
                violations.append({
                    "variable": var,
                    "value": round(val, 4),
                    "threshold": f"max={high}",
                    "severity": "high" if val > high + 0.2 else "medium",
                })

        risk_score = len(violations) / max(len(self.risk_thresholds), 1)
        return {
            "risk_score": round(min(1.0, risk_score), 4),
            "violations": violations,
            "safe": len(violations) == 0,
        }
