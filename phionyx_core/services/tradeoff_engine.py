"""
Trade-off Elicitation Engine
=============================

Faz 3.1: Kalan Özellikler

Alternatif mimari/fonksiyon seçeneklerini listeler ve maliyet/risk analizi yapar.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AlternativeType(Enum):
    """Type of alternative."""
    ARCHITECTURAL = "architectural"
    FUNCTIONAL = "functional"
    IMPLEMENTATION = "implementation"


@dataclass
class Constraint:
    """Constraint definition."""
    name: str
    type: str  # "performance", "security", "cost", "maintainability"
    value: Any
    priority: str = "medium"  # "low", "medium", "high", "critical"


@dataclass
class Alternative:
    """Alternative solution."""
    id: str
    name: str
    description: str
    type: AlternativeType
    cost_score: float = 0.0  # 0.0-1.0, lower is better
    risk_score: float = 0.0  # 0.0-1.0, lower is better
    complexity_score: float = 0.0  # 0.0-1.0, lower is better
    maintainability_score: float = 0.0  # 0.0-1.0, higher is better
    pros: List[str] = None
    cons: List[str] = None

    def __post_init__(self):
        if self.pros is None:
            self.pros = []
        if self.cons is None:
            self.cons = []


@dataclass
class TradeOffTable:
    """Trade-off comparison table."""
    alternatives: List[Alternative]
    metrics: List[str]  # ["cost", "risk", "complexity", "maintainability"]
    recommendation: Optional[Alternative] = None


class TradeOffElicitationEngine:
    """
    Full-featured Trade-off Elicitation Engine.

    Provides:
    - Alternative generation (architectural, functional, implementation)
    - Cost/risk/complexity analysis
    - Trade-off table generation
    - Recommendation engine
    """

    def __init__(self):
        """Initialize trade-off engine."""
        self.alternative_cache: Dict[str, List[Alternative]] = {}

    def generate_alternatives(
        self,
        requirement: str,
        constraints: Optional[List[Constraint]] = None
    ) -> List[Alternative]:
        """
        Generate alternative solutions for a requirement.

        Args:
            requirement: Requirement description
            constraints: List of constraints (optional)

        Returns:
            List of Alternative solutions
        """
        alternatives = []

        # 1. Architectural alternatives
        alternatives.extend(self._generate_architectural_alternatives(requirement, constraints))

        # 2. Functional alternatives
        alternatives.extend(self._generate_functional_alternatives(requirement, constraints))

        # 3. Implementation alternatives
        alternatives.extend(self._generate_implementation_alternatives(requirement, constraints))

        # 4. Calculate scores for each alternative
        for alt in alternatives:
            alt.cost_score = self._calculate_cost(alt, constraints)
            alt.risk_score = self._calculate_risk(alt, constraints)
            alt.complexity_score = self._calculate_complexity(alt, constraints)
            alt.maintainability_score = self._calculate_maintainability(alt, constraints)

        return alternatives

    def _generate_architectural_alternatives(
        self,
        requirement: str,
        constraints: Optional[List[Constraint]] = None
    ) -> List[Alternative]:
        """Generate architectural alternatives."""
        alternatives = []

        # Example: Generate different architectural patterns
        patterns = [
            ("monolithic", "Single monolithic application"),
            ("microservices", "Microservices architecture"),
            ("layered", "Layered architecture"),
            ("event-driven", "Event-driven architecture"),
        ]

        for pattern_id, pattern_desc in patterns:
            alt = Alternative(
                id=f"arch_{pattern_id}",
                name=f"{pattern_id.capitalize()} Architecture",
                description=f"{pattern_desc} for {requirement}",
                type=AlternativeType.ARCHITECTURAL,
                pros=self._get_architectural_pros(pattern_id),
                cons=self._get_architectural_cons(pattern_id)
            )
            alternatives.append(alt)

        return alternatives

    def _generate_functional_alternatives(
        self,
        requirement: str,
        constraints: Optional[List[Constraint]] = None
    ) -> List[Alternative]:
        """Generate functional alternatives."""
        alternatives = []

        # Example: Generate different functional approaches
        approaches = [
            ("simple", "Simple, straightforward implementation"),
            ("optimized", "Optimized for performance"),
            ("extensible", "Extensible design for future changes"),
            ("minimal", "Minimal implementation with core features"),
        ]

        for approach_id, approach_desc in approaches:
            alt = Alternative(
                id=f"func_{approach_id}",
                name=f"{approach_id.capitalize()} Approach",
                description=f"{approach_desc} for {requirement}",
                type=AlternativeType.FUNCTIONAL,
                pros=self._get_functional_pros(approach_id),
                cons=self._get_functional_cons(approach_id)
            )
            alternatives.append(alt)

        return alternatives

    def _generate_implementation_alternatives(
        self,
        requirement: str,
        constraints: Optional[List[Constraint]] = None
    ) -> List[Alternative]:
        """Generate implementation alternatives."""
        alternatives = []

        # Example: Generate different implementation strategies
        strategies = [
            ("iterative", "Iterative development with incremental delivery"),
            ("agile", "Agile development with sprints"),
            ("waterfall", "Waterfall approach with phases"),
            ("prototype", "Prototype-first approach"),
        ]

        for strategy_id, strategy_desc in strategies:
            alt = Alternative(
                id=f"impl_{strategy_id}",
                name=f"{strategy_id.capitalize()} Strategy",
                description=f"{strategy_desc} for {requirement}",
                type=AlternativeType.IMPLEMENTATION,
                pros=self._get_implementation_pros(strategy_id),
                cons=self._get_implementation_cons(strategy_id)
            )
            alternatives.append(alt)

        return alternatives

    def _calculate_cost(
        self,
        alternative: Alternative,
        constraints: Optional[List[Constraint]] = None
    ) -> float:
        """Calculate cost score (0.0-1.0, lower is better)."""
        # Base cost based on type
        base_cost = {
            AlternativeType.ARCHITECTURAL: 0.5,
            AlternativeType.FUNCTIONAL: 0.3,
            AlternativeType.IMPLEMENTATION: 0.4,
        }.get(alternative.type, 0.5)

        # Adjust based on complexity
        cost = base_cost + (alternative.complexity_score * 0.3)

        # Adjust based on constraints
        if constraints:
            for constraint in constraints:
                if constraint.type == "cost" and constraint.priority == "high":
                    cost += 0.2

        return min(1.0, cost)

    def _calculate_risk(
        self,
        alternative: Alternative,
        constraints: Optional[List[Constraint]] = None
    ) -> float:
        """Calculate risk score (0.0-1.0, lower is better)."""
        # Base risk based on type
        base_risk = {
            AlternativeType.ARCHITECTURAL: 0.4,
            AlternativeType.FUNCTIONAL: 0.3,
            AlternativeType.IMPLEMENTATION: 0.5,
        }.get(alternative.type, 0.4)

        # Adjust based on complexity
        risk = base_risk + (alternative.complexity_score * 0.2)

        # Adjust based on constraints
        if constraints:
            for constraint in constraints:
                if constraint.type == "security" and constraint.priority == "high":
                    risk += 0.2

        return min(1.0, risk)

    def _calculate_complexity(
        self,
        alternative: Alternative,
        constraints: Optional[List[Constraint]] = None
    ) -> float:
        """Calculate complexity score (0.0-1.0, lower is better)."""
        # Base complexity based on type
        base_complexity = {
            AlternativeType.ARCHITECTURAL: 0.6,
            AlternativeType.FUNCTIONAL: 0.4,
            AlternativeType.IMPLEMENTATION: 0.5,
        }.get(alternative.type, 0.5)

        # Adjust based on description length (proxy for complexity)
        description_length = len(alternative.description)
        if description_length > 200:
            base_complexity += 0.2
        elif description_length > 100:
            base_complexity += 0.1

        return min(1.0, base_complexity)

    def _calculate_maintainability(
        self,
        alternative: Alternative,
        constraints: Optional[List[Constraint]] = None
    ) -> float:
        """Calculate maintainability score (0.0-1.0, higher is better)."""
        # Base maintainability (inverse of complexity)
        maintainability = 1.0 - alternative.complexity_score

        # Adjust based on pros/cons
        if len(alternative.pros) > len(alternative.cons):
            maintainability += 0.1
        elif len(alternative.cons) > len(alternative.pros):
            maintainability -= 0.1

        return max(0.0, min(1.0, maintainability))

    def generate_tradeoff_table(
        self,
        alternatives: List[Alternative],
        metrics: Optional[List[str]] = None
    ) -> TradeOffTable:
        """
        Generate trade-off comparison table.

        Args:
            alternatives: List of alternatives
            metrics: List of metrics to compare (optional)

        Returns:
            TradeOffTable with recommendation
        """
        if metrics is None:
            metrics = ["cost", "risk", "complexity", "maintainability"]

        # Find best alternative (weighted score)
        best_alternative = None
        best_score = float('inf')

        for alt in alternatives:
            # Weighted score (lower is better)
            score = (
                alt.cost_score * 0.3 +
                alt.risk_score * 0.3 +
                alt.complexity_score * 0.2 -
                alt.maintainability_score * 0.2  # Negative because higher is better
            )

            if score < best_score:
                best_score = score
                best_alternative = alt

        return TradeOffTable(
            alternatives=alternatives,
            metrics=metrics,
            recommendation=best_alternative
        )

    def _get_architectural_pros(self, pattern_id: str) -> List[str]:
        """Get pros for architectural pattern."""
        pros_map = {
            "monolithic": ["Simple to develop", "Easy to deploy", "Low overhead"],
            "microservices": ["Scalable", "Independent deployment", "Technology diversity"],
            "layered": ["Clear separation", "Easy to understand", "Maintainable"],
            "event-driven": ["Loose coupling", "Scalable", "Responsive"],
        }
        return pros_map.get(pattern_id, [])

    def _get_architectural_cons(self, pattern_id: str) -> List[str]:
        """Get cons for architectural pattern."""
        cons_map = {
            "monolithic": ["Hard to scale", "Tight coupling", "Single point of failure"],
            "microservices": ["Complex deployment", "Network latency", "Data consistency"],
            "layered": ["Performance overhead", "Rigid structure", "Dependency issues"],
            "event-driven": ["Complex debugging", "Event ordering", "Message loss risk"],
        }
        return cons_map.get(pattern_id, [])

    def _get_functional_pros(self, approach_id: str) -> List[str]:
        """Get pros for functional approach."""
        pros_map = {
            "simple": ["Easy to understand", "Quick to implement", "Low maintenance"],
            "optimized": ["High performance", "Efficient resource use", "Fast execution"],
            "extensible": ["Future-proof", "Easy to extend", "Flexible"],
            "minimal": ["Lightweight", "Fast to implement", "Low complexity"],
        }
        return pros_map.get(approach_id, [])

    def _get_functional_cons(self, approach_id: str) -> List[str]:
        """Get cons for functional approach."""
        cons_map = {
            "simple": ["Limited features", "May need refactoring", "Not optimized"],
            "optimized": ["Complex implementation", "Harder to maintain", "Premature optimization risk"],
            "extensible": ["Over-engineering risk", "Higher complexity", "Slower initial development"],
            "minimal": ["Limited functionality", "May need expansion", "Feature gaps"],
        }
        return cons_map.get(approach_id, [])

    def _get_implementation_pros(self, strategy_id: str) -> List[str]:
        """Get pros for implementation strategy."""
        pros_map = {
            "iterative": ["Incremental delivery", "Early feedback", "Flexible"],
            "agile": ["Adaptive", "Customer collaboration", "Rapid delivery"],
            "waterfall": ["Clear phases", "Well-documented", "Predictable"],
            "prototype": ["Early validation", "User feedback", "Risk reduction"],
        }
        return pros_map.get(strategy_id, [])

    def _get_implementation_cons(self, strategy_id: str) -> List[str]:
        """Get cons for implementation strategy."""
        cons_map = {
            "iterative": ["Requires discipline", "Integration challenges", "Scope creep risk"],
            "agile": ["Requires experience", "Less documentation", "Uncertainty"],
            "waterfall": ["Inflexible", "Late feedback", "High risk"],
            "prototype": ["May be discarded", "Time investment", "Scope confusion"],
        }
        return cons_map.get(strategy_id, [])


__all__ = [
    'TradeOffElicitationEngine',
    'Alternative',
    'TradeOffTable',
    'Constraint',
    'AlternativeType',
]

