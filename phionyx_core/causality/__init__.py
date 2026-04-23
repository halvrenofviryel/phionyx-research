"""
Causality Module — v4 §3 (AGI Layer 3)
========================================

Causal inference engine for Phionyx cognitive runtime.
Builds directed causal graphs, estimates causal strengths,
simulates interventions, counterfactual reasoning, root cause
analysis, and forward simulation.

Components:
- CausalGraphBuilder: Constructs causal DAGs from observations
- InterventionModel: Simulates do(X=x) interventions
- CounterfactualEngine: "What would have happened if...?"
- RootCauseAnalyzer: Traces anomalies to root causes
- CausalSimulator: Forward simulation of actions
"""

from .causal_graph import CausalGraphBuilder, CausalNode, CausalEdge, CausalGraph
from .intervention import InterventionModel, InterventionResult
from .counterfactual import CounterfactualEngine, CounterfactualResult
from .root_cause import RootCauseAnalyzer, RootCauseAnalysis
from .simulator import CausalSimulator, SimulationResult

__all__ = [
    "CausalGraphBuilder",
    "CausalNode",
    "CausalEdge",
    "CausalGraph",
    "InterventionModel",
    "InterventionResult",
    "CounterfactualEngine",
    "CounterfactualResult",
    "RootCauseAnalyzer",
    "RootCauseAnalysis",
    "CausalSimulator",
    "SimulationResult",
]
