"""
Counterfactual Reasoning — v4 §3 (AGI Layer 3)
================================================

Answers: "What would have happened if X had been different?"

Three-step counterfactual process (Pearl's framework):
1. **Abduction**: Infer hidden state from factual observations
2. **Action**: Apply intervention do(X=x') in the counterfactual world
3. **Prediction**: Propagate effects to predict counterfactual outcomes

Integrates with:
- causality/causal_graph.py (CausalGraph)
- causality/intervention.py (InterventionModel)
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from .causal_graph import CausalGraph
from .intervention import InterventionModel, InterventionResult

logger = logging.getLogger(__name__)

# Module-level tunable defaults (Tier A — PRE surfaces)
cf_attenuation_rate = 0.8
cf_min_effect = 0.01


@dataclass
class CounterfactualQuery:
    """A 'what if' question."""
    variable: str           # Which variable to change
    counterfactual_value: float  # What value it would have been
    target_variables: list[str] = field(default_factory=list)  # What to predict (empty = all)
    context: str = ""       # Human-readable description


@dataclass
class CounterfactualOutcome:
    """Predicted outcome for one target variable."""
    variable: str
    factual_value: float | None
    counterfactual_value: float
    delta: float
    causal_path: list[str]
    necessity_score: float  # How necessary was the cause? (0-1)


@dataclass
class CounterfactualResult:
    """Full result of counterfactual analysis."""
    query: CounterfactualQuery
    factual_state: dict[str, float | None]
    counterfactual_state: dict[str, float]
    outcomes: list[CounterfactualOutcome]
    intervention_result: InterventionResult
    reasoning: str

    def get_outcome(self, variable: str) -> CounterfactualOutcome | None:
        for o in self.outcomes:
            if o.variable == variable:
                return o
        return None

    @property
    def max_impact_variable(self) -> str | None:
        """Variable with largest counterfactual impact."""
        if not self.outcomes:
            return None
        return max(self.outcomes, key=lambda o: abs(o.delta)).variable

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": {
                "variable": self.query.variable,
                "counterfactual_value": self.query.counterfactual_value,
                "targets": self.query.target_variables,
            },
            "outcomes": [
                {
                    "variable": o.variable,
                    "factual": o.factual_value,
                    "counterfactual": round(o.counterfactual_value, 4),
                    "delta": round(o.delta, 4),
                    "necessity": round(o.necessity_score, 4),
                    "path": o.causal_path,
                }
                for o in self.outcomes
            ],
            "reasoning": self.reasoning,
        }


class CounterfactualEngine:
    """
    Counterfactual reasoning engine.

    Usage:
        engine = CounterfactualEngine(causal_graph)
        result = engine.what_if("entropy", 0.9)
        for outcome in result.outcomes:
            print(f"If entropy were 0.9, {outcome.variable} would be {outcome.counterfactual_value}")

    Necessity test:
        score = engine.necessity("entropy_high", "coherence_low")
        # 0.0 = entropy had nothing to do with coherence
        # 1.0 = entropy was the sole cause of coherence
    """

    def __init__(
        self,
        graph: CausalGraph,
        attenuation_rate: float = cf_attenuation_rate,
        min_effect: float = cf_min_effect,
    ):
        self.graph = graph
        self.intervention_model = InterventionModel(
            graph,
            attenuation_rate=attenuation_rate,
            min_effect_threshold=min_effect,
        )

    def what_if(
        self,
        variable: str,
        counterfactual_value: float,
        targets: list[str] | None = None,
        context: str = "",
    ) -> CounterfactualResult:
        """
        Ask: "What would have happened if {variable} had been {value}?"

        Args:
            variable: Variable to change
            counterfactual_value: Hypothetical value
            targets: Which variables to predict (None = all affected)
            context: Description for audit

        Returns:
            CounterfactualResult with predicted outcomes
        """
        query = CounterfactualQuery(
            variable=variable,
            counterfactual_value=counterfactual_value,
            target_variables=targets or [],
            context=context,
        )

        if variable not in self.graph.nodes:
            return CounterfactualResult(
                query=query,
                factual_state={},
                counterfactual_state={},
                outcomes=[],
                intervention_result=self.intervention_model.do(variable, counterfactual_value),
                reasoning=f"Variable '{variable}' not found in causal graph",
            )

        # Step 1: Capture factual state
        factual_state = {
            nid: node.current_value
            for nid, node in self.graph.nodes.items()
        }

        # Step 2: Apply counterfactual intervention
        intervention = self.intervention_model.do(variable, counterfactual_value)

        # Step 3: Build counterfactual state
        cf_state = dict(intervention.graph_snapshot)

        # Step 4: Build outcomes
        outcomes = []
        target_set = set(targets) if targets else intervention.affected_node_ids
        for effect in intervention.effects:
            if targets and effect.node_id not in target_set:
                continue
            factual_val = factual_state.get(effect.node_id)
            necessity = self._compute_necessity(
                variable, effect.node_id, counterfactual_value
            )
            outcomes.append(CounterfactualOutcome(
                variable=effect.node_id,
                factual_value=factual_val,
                counterfactual_value=effect.new_value,
                delta=effect.delta,
                causal_path=effect.causal_path,
                necessity_score=necessity,
            ))

        reasoning = self._build_reasoning(query, outcomes)

        return CounterfactualResult(
            query=query,
            factual_state=factual_state,
            counterfactual_state=cf_state,
            outcomes=outcomes,
            intervention_result=intervention,
            reasoning=reasoning,
        )

    def necessity(
        self,
        cause: str,
        effect: str,
    ) -> float:
        """
        Test necessity: Was {cause} necessary for {effect}?

        Necessity = P(~effect | do(~cause)) — "if cause hadn't happened,
        would effect still have happened?"

        Approximation: How much does removing cause's value change effect?

        Returns:
            0.0 = cause was not necessary
            1.0 = cause was fully necessary
        """
        return self._compute_necessity(cause, effect)

    def sufficiency(
        self,
        cause: str,
        effect: str,
    ) -> float:
        """
        Test sufficiency: Was {cause} sufficient for {effect}?

        Approximation: total causal effect from cause to effect.

        Returns:
            0.0 = cause is not sufficient
            1.0 = cause is fully sufficient
        """
        return self.intervention_model.estimate_total_effect(cause, effect)

    def _compute_necessity(
        self,
        cause: str,
        effect: str,
        cf_value: float | None = None,
    ) -> float:
        """Compute necessity score for cause→effect."""
        cause_node = self.graph.nodes.get(cause)
        effect_node = self.graph.nodes.get(effect)
        if not cause_node or not effect_node:
            return 0.0

        # Total causal effect represents how much cause contributes
        total_effect = self.intervention_model.estimate_total_effect(cause, effect)

        # If there are other paths to effect (from other parents), necessity decreases
        parents = self.graph.get_parents(effect)
        if not parents:
            return 0.0
        if cause not in self.graph.get_ancestors(effect) and cause not in parents:
            return 0.0

        # Necessity: proportion of effect explained by this cause
        # Simple: total_effect / (number_of_parents' combined effect)
        other_effects = 0.0
        for parent in parents:
            if parent != cause:
                edge = self.graph.get_edge(parent, effect)
                if edge:
                    other_effects += edge.effective_strength

        if total_effect + other_effects == 0:
            return 0.0

        return min(1.0, total_effect / (total_effect + other_effects))

    def _build_reasoning(
        self,
        query: CounterfactualQuery,
        outcomes: list[CounterfactualOutcome],
    ) -> str:
        if not outcomes:
            return f"No downstream effects detected for do({query.variable}={query.counterfactual_value})"

        parts = []
        for o in outcomes[:3]:  # Top 3 effects
            direction = "increase" if o.delta > 0 else "decrease"
            parts.append(
                f"{o.variable} would {direction} by {abs(o.delta):.3f} "
                f"(necessity={o.necessity_score:.2f})"
            )
        return f"If {query.variable} were {query.counterfactual_value}: " + "; ".join(parts)
