"""
Counterfactual Self-Coherence Adapter + Self-Directed Assessment
=================================================================

Routes self-model variables (confidence, drift, capability) through the
CounterfactualEngine to answer "what if my confidence were different?"

Includes self-directed assessment: the system scans its own variables,
identifies sensitivity weaknesses, and proposes stabilization interventions.

AGI mapping: Self-model update + Reflective control
Mind-loop stage: UpdateSelfModel, Reflect+Revise
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any

from ..causality.causal_graph import CausalGraph
from ..causality.counterfactual import CounterfactualEngine, CounterfactualResult

logger = logging.getLogger(__name__)

# Self-model variables that can be assessed counterfactually
SELF_MODEL_VARIABLES = {
    "confidence": "Overall confidence score (0-1)",
    "drift_severity": "Self-model drift magnitude (0-1)",
    "capability_score": "Task capability assessment (0-1)",
    "knowledge_coverage": "Knowledge boundary coverage (0-1)",
    "coherence": "Response coherence score (0-1)",
}


@dataclass
class CounterfactualSelfResult:
    """Result of counterfactual self-assessment."""
    variable: str
    original_value: float
    counterfactual_value: float
    cf_result: CounterfactualResult
    stability_score: float  # 0 = highly unstable, 1 = stable under perturbation
    reasoning: str


class CounterfactualSelfAssessment:
    """Adapter routing self-model variables through counterfactual reasoning.

    Given a self-model variable (e.g., 'confidence') and a hypothetical value,
    this adapter:
    1. Maps the self-model variable to a causal graph node
    2. Runs counterfactual analysis via CounterfactualEngine
    3. Computes stability: how much does the system change when self-model changes?

    Usage:
        graph = CausalGraph()
        # ... add nodes for confidence, coherence, etc.
        adapter = CounterfactualSelfAssessment(graph)
        result = adapter.assess("confidence", 0.3)  # what if confidence were 0.3?
    """

    def __init__(self, graph: CausalGraph):
        self._graph = graph
        self._engine = CounterfactualEngine(graph)

    def assess(
        self,
        variable: str,
        cf_value: float,
        targets: Optional[List[str]] = None,
    ) -> CounterfactualSelfResult:
        """Assess counterfactual impact of changing a self-model variable.

        Args:
            variable: Self-model variable name (must be in causal graph)
            cf_value: Hypothetical value to test
            targets: Downstream variables to predict (None = all)

        Returns:
            CounterfactualSelfResult with stability analysis
        """
        # Get original value
        node = self._graph.nodes.get(variable)
        original = node.current_value if node and node.current_value is not None else 0.5

        # Run counterfactual
        cf_result = self._engine.what_if(
            variable=variable,
            counterfactual_value=cf_value,
            targets=targets,
            context=f"Self-model counterfactual: what if {variable} were {cf_value}?",
        )

        # Compute stability: how much do downstream variables change?
        stability = self._compute_stability(cf_result, original, cf_value)

        reasoning = self._build_reasoning(variable, original, cf_value, cf_result, stability)

        return CounterfactualSelfResult(
            variable=variable,
            original_value=original,
            counterfactual_value=cf_value,
            cf_result=cf_result,
            stability_score=stability,
            reasoning=reasoning,
        )

    def assess_confidence_sensitivity(
        self,
        perturbation: float = 0.2,
    ) -> Dict[str, CounterfactualSelfResult]:
        """Assess how sensitive the system is to confidence changes.

        Tests both increase and decrease by perturbation amount.
        """
        node = self._graph.nodes.get("confidence")
        if not node or node.current_value is None:
            return {}

        current = node.current_value
        results = {}

        high = min(1.0, current + perturbation)
        low = max(0.0, current - perturbation)

        results["confidence_increase"] = self.assess("confidence", high)
        results["confidence_decrease"] = self.assess("confidence", low)

        return results

    def _compute_stability(
        self,
        cf_result: CounterfactualResult,
        original: float,
        cf_value: float,
    ) -> float:
        """Compute stability score: 1.0 = stable, 0.0 = highly sensitive.

        Stability = 1 - (avg downstream delta / input delta).
        A system is stable if changing self-model doesn't wildly change outputs.
        """
        if not cf_result.outcomes:
            return 1.0  # No downstream effects = perfectly stable

        input_delta = abs(cf_value - original)
        if input_delta < 1e-10:
            return 1.0  # No change requested

        total_delta = sum(abs(o.delta) for o in cf_result.outcomes)
        avg_delta = total_delta / len(cf_result.outcomes)

        # Sensitivity ratio: how much output changes per unit input change
        sensitivity = avg_delta / input_delta

        # Convert to stability: 1/(1+sensitivity)
        stability = 1.0 / (1.0 + sensitivity)
        return round(min(1.0, max(0.0, stability)), 4)

    def _build_reasoning(
        self,
        variable: str,
        original: float,
        cf_value: float,
        cf_result: CounterfactualResult,
        stability: float,
    ) -> str:
        """Build human-readable reasoning for the assessment."""
        if not cf_result.outcomes:
            return (
                f"Changing {variable} from {original:.2f} to {cf_value:.2f} "
                f"has no downstream effects. System is stable."
            )

        n_affected = len(cf_result.outcomes)
        label = "stable" if stability > 0.7 else "sensitive" if stability > 0.4 else "highly sensitive"
        return (
            f"If {variable} were {cf_value:.2f} (currently {original:.2f}), "
            f"{n_affected} downstream variables affected. "
            f"Stability: {stability:.2f} ({label})."
        )


# ─── Self-Directed Counterfactual Assessment ─────────────────────────────────


@dataclass
class StabilizationProposal:
    """Proposed intervention to improve stability of a self-model variable."""
    variable: str
    current_stability: float
    target_stability: float
    strategy: str  # "dampening" | "diversification"
    reasoning: str
    edge_changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SelfScanReport:
    """Report of full self-model sensitivity scan."""
    variables: Dict[str, float]  # variable → stability score
    weakest_variable: Optional[str]
    weakest_stability: float
    mean_stability: float
    all_stable: bool  # True if all variables have stability >= threshold


class SelfDirectedCounterfactual:
    """Self-directed counterfactual: the system assesses its own stability.

    Extends CounterfactualSelfAssessment with autonomous capabilities:
    1. Scans all self-model variables for sensitivity
    2. Identifies the weakest (most sensitive) variable
    3. Proposes stabilization strategies

    Mind-loop stage: Reflect+Revise
    AGI component: Self-model + Reflective control
    """

    def __init__(self, graph: CausalGraph, stability_threshold: float = 0.70):
        self._graph = graph
        self._assessor = CounterfactualSelfAssessment(graph)
        self._stability_threshold = stability_threshold

    def scan_all(self, perturbation: float = 0.2) -> SelfScanReport:
        """Assess all self-model variables present in the causal graph.

        Returns:
            SelfScanReport with per-variable stability scores.
        """
        scores: Dict[str, float] = {}
        for var_name in SELF_MODEL_VARIABLES:
            node = self._graph.nodes.get(var_name)
            if node is None or node.current_value is None:
                continue
            cf_value = min(1.0, node.current_value + perturbation)
            result = self._assessor.assess(var_name, cf_value)
            scores[var_name] = result.stability_score

        if not scores:
            return SelfScanReport(
                variables={},
                weakest_variable=None,
                weakest_stability=1.0,
                mean_stability=1.0,
                all_stable=True,
            )

        weakest = min(scores, key=scores.get)  # type: ignore[arg-type]
        mean_stab = sum(scores.values()) / len(scores)
        return SelfScanReport(
            variables=scores,
            weakest_variable=weakest,
            weakest_stability=scores[weakest],
            mean_stability=round(mean_stab, 4),
            all_stable=all(s >= self._stability_threshold for s in scores.values()),
        )

    def identify_weakest(self, perturbation: float = 0.2) -> Optional[str]:
        """Find the self-model variable with lowest stability score."""
        report = self.scan_all(perturbation)
        return report.weakest_variable

    def propose_stabilization(
        self,
        variable: str,
        target_stability: float = 0.80,
    ) -> Optional[StabilizationProposal]:
        """Propose a stabilization strategy for a specific variable.

        Analyzes the variable's downstream edges and suggests either:
        - dampening: reduce the strongest edges to lower sensitivity
        - diversification: the variable needs more weak edges (detected but not auto-created)

        Returns None if variable not in graph or already stable enough.
        """
        node = self._graph.nodes.get(variable)
        if node is None or node.current_value is None:
            return None

        # Assess current stability
        cf_value = min(1.0, node.current_value + 0.2)
        result = self._assessor.assess(variable, cf_value)
        current_stability = result.stability_score

        if current_stability >= target_stability:
            return StabilizationProposal(
                variable=variable,
                current_stability=current_stability,
                target_stability=target_stability,
                strategy="none",
                reasoning=f"{variable} already stable ({current_stability:.4f} >= {target_stability})",
                edge_changes=[],
            )

        # Find outgoing edges and their strengths
        children = self._graph.get_children(variable)
        if not children:
            return StabilizationProposal(
                variable=variable,
                current_stability=current_stability,
                target_stability=target_stability,
                strategy="diversification",
                reasoning=(
                    f"{variable} has no downstream edges. "
                    f"Add causal links to reduce isolation."
                ),
                edge_changes=[],
            )

        # Collect edge strengths
        edges = []
        for child in children:
            edge = self._graph.get_edge(variable, child)
            if edge:
                edges.append((child, abs(edge.strength)))

        # Compute what average strength is needed
        # stability = 1/(1 + avg_strength) >= target
        # avg_strength <= 1/target - 1
        max_avg = (1.0 / target_stability) - 1.0
        current_avg = sum(s for _, s in edges) / len(edges) if edges else 0

        if current_avg <= max_avg:
            return StabilizationProposal(
                variable=variable,
                current_stability=current_stability,
                target_stability=target_stability,
                strategy="none",
                reasoning=f"{variable} edge average ({current_avg:.4f}) within target bounds",
                edge_changes=[],
            )

        # Strategy: dampen the strongest edges
        sorted_edges = sorted(edges, key=lambda x: x[1], reverse=True)
        edge_changes = []
        for child, strength in sorted_edges:
            if strength > max_avg:
                dampened = max(max_avg, strength * 0.7)  # 30% dampening
                edge_changes.append({
                    "source": variable,
                    "target": child,
                    "current_strength": round(strength, 4),
                    "proposed_strength": round(dampened, 4),
                    "change": "dampening",
                })

        strategy = "dampening" if edge_changes else "diversification"
        reasoning = (
            f"{variable} stability {current_stability:.4f} < target {target_stability}. "
            f"avg|strength| = {current_avg:.4f}, need <= {max_avg:.4f}. "
            f"Propose {len(edge_changes)} edge dampening(s)."
            if edge_changes else
            f"{variable} stability {current_stability:.4f} < target {target_stability}. "
            f"Add more downstream edges with weaker strengths."
        )

        return StabilizationProposal(
            variable=variable,
            current_stability=current_stability,
            target_stability=target_stability,
            strategy=strategy,
            reasoning=reasoning,
            edge_changes=edge_changes,
        )
