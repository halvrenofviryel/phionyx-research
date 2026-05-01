"""
Deliberative Ethics — v4 §9 (AGI Layer 9)
============================================

Slow-path ethical reasoning for ESCALATE verdicts.
When fast-path ethics (rule-based) encounters ESCALATE,
this module provides deeper multi-framework ethical analysis.

Frameworks considered:
1. Deontological: Does the action violate rules/duties?
2. Consequentialist: Do outcomes maximize good/minimize harm?
3. Virtue Ethics: Is the action consistent with system values?
4. Care Ethics: Does it protect vulnerable entities?

Integrates with:
- contracts/v4/ethics_decision.py (EthicsVerdict, DeliberationLayer)
- state/ethics.py (EthicsVector — risk dimensions)
- governance/human_in_the_loop.py (HITL fallback for deadlock)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Module-level tunable defaults (Tier C — proposal only, PRE surfaces)
deontological_weight = 0.3
consequentialist_weight = 0.3
virtue_weight = 0.2
care_weight = 0.2
deny_threshold = 0.6
guard_threshold = 0.4


class EthicalFramework(str, Enum):
    DEONTOLOGICAL = "deontological"
    CONSEQUENTIALIST = "consequentialist"
    VIRTUE = "virtue"
    CARE = "care"


class DeliberationOutcome(str, Enum):
    ALLOW = "allow"
    ALLOW_WITH_GUARD = "allow_with_guard"
    DENY = "deny"
    DEFER_TO_HUMAN = "defer_to_human"


@dataclass
class FrameworkAssessment:
    """Assessment from one ethical framework."""
    framework: str
    verdict: str  # DeliberationOutcome value
    confidence: float  # 0-1
    reasoning: str
    weight: float = 1.0  # Framework weight in final decision


@dataclass
class DeliberativeResult:
    """Full result of deliberative ethics analysis."""
    action_description: str
    framework_assessments: list[FrameworkAssessment]
    final_verdict: str  # DeliberationOutcome value
    final_confidence: float
    consensus: bool  # Did all frameworks agree?
    reasoning: str
    risk_dimensions: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action_description,
            "frameworks": [
                {
                    "framework": fa.framework,
                    "verdict": fa.verdict,
                    "confidence": round(fa.confidence, 3),
                    "reasoning": fa.reasoning,
                }
                for fa in self.framework_assessments
            ],
            "verdict": self.final_verdict,
            "confidence": round(self.final_confidence, 3),
            "consensus": self.consensus,
            "reasoning": self.reasoning,
        }


def normalize_risk_vector(components: list[float]) -> list[float]:
    """
    Normalize risk vector components to [0, 1] range.

    Patent SF2-7: Risk vector normalization for ethics pre-response.
    Uses min-max normalization. If all values are equal, returns uniform 0.5.

    Args:
        components: Raw risk component values

    Returns:
        Normalized risk components in [0, 1]
    """
    if not components:
        return []
    if len(components) == 1:
        return [max(0.0, min(1.0, components[0]))]
    min_val = min(components)
    max_val = max(components)
    spread = max_val - min_val
    if spread < 1e-9:
        return [0.5] * len(components)
    return [max(0.0, min(1.0, (v - min_val) / spread)) for v in components]


class DeliberativeEthics:
    """
    Multi-framework ethical deliberation engine.

    Usage:
        ethics = DeliberativeEthics()
        result = ethics.deliberate(
            action="Generate response about violence",
            ethics_vector={
                "harm_risk": 0.7,
                "manipulation_risk": 0.2,
                "child_on_child_risk": 0.1,
            },
            context={"user_age_group": "minor"},
        )
        if result.final_verdict == "deny":
            # Block the action
    """

    def __init__(
        self,
        framework_weights: dict[str, float] | None = None,
        deny_threshold: float = deny_threshold,
        guard_threshold: float = guard_threshold,
    ):
        """
        Args:
            framework_weights: {framework_name: weight}
            deny_threshold: Weighted deny score above this → DENY
            guard_threshold: Between guard and deny → ALLOW_WITH_GUARD
        """
        self.framework_weights = framework_weights or {
            EthicalFramework.DEONTOLOGICAL.value: deontological_weight,
            EthicalFramework.CONSEQUENTIALIST.value: consequentialist_weight,
            EthicalFramework.VIRTUE.value: virtue_weight,
            EthicalFramework.CARE.value: care_weight,
        }
        self.deny_threshold = deny_threshold
        self.guard_threshold = guard_threshold

        # Normalize weights
        total = sum(self.framework_weights.values())
        if total > 0:
            self.framework_weights = {
                k: v / total for k, v in self.framework_weights.items()
            }

    def deliberate(
        self,
        action: str,
        ethics_vector: dict[str, float],
        context: dict[str, Any] | None = None,
    ) -> DeliberativeResult:
        """
        Perform multi-framework ethical deliberation.

        Args:
            action: Description of the proposed action
            ethics_vector: Risk dimensions (harm_risk, manipulation_risk, etc.)
            context: Additional context (user info, scenario, etc.)

        Returns:
            DeliberativeResult with final verdict
        """
        context = context or {}

        assessments = [
            self._assess_deontological(action, ethics_vector, context),
            self._assess_consequentialist(action, ethics_vector, context),
            self._assess_virtue(action, ethics_vector, context),
            self._assess_care(action, ethics_vector, context),
        ]

        # Compute weighted verdict
        final_verdict, final_confidence, consensus = self._aggregate(assessments)

        reasoning = self._build_reasoning(assessments, final_verdict, consensus)

        return DeliberativeResult(
            action_description=action,
            framework_assessments=assessments,
            final_verdict=final_verdict,
            final_confidence=final_confidence,
            consensus=consensus,
            reasoning=reasoning,
            risk_dimensions=ethics_vector,
        )

    def _assess_deontological(
        self, action: str, risks: dict[str, float], context: dict,
    ) -> FrameworkAssessment:
        """Rule-based: Does this violate absolute rules?"""
        # Hard rules
        harm = risks.get("harm_risk", 0.0)
        manipulation = risks.get("manipulation_risk", 0.0)
        boundary = risks.get("boundary_violation_risk", 0.0)

        max_risk = max(harm, manipulation, boundary)

        if max_risk > 0.9:
            verdict = DeliberationOutcome.DENY.value
            confidence = 0.95
            reason = f"Absolute rule violation: max_risk={max_risk:.2f}"
        elif max_risk > 0.6:
            verdict = DeliberationOutcome.ALLOW_WITH_GUARD.value
            confidence = 0.7
            reason = f"Moderate rule concern: max_risk={max_risk:.2f}"
        else:
            verdict = DeliberationOutcome.ALLOW.value
            confidence = 0.8
            reason = f"No rule violations detected: max_risk={max_risk:.2f}"

        return FrameworkAssessment(
            framework=EthicalFramework.DEONTOLOGICAL.value,
            verdict=verdict,
            confidence=confidence,
            reasoning=reason,
            weight=self.framework_weights.get(EthicalFramework.DEONTOLOGICAL.value, 0.25),
        )

    def _assess_consequentialist(
        self, action: str, risks: dict[str, float], context: dict,
    ) -> FrameworkAssessment:
        """Outcome-based: Do outcomes maximize good?"""
        harm = risks.get("harm_risk", 0.0)
        attachment = risks.get("attachment_risk", 0.0)
        # Expected harm = weighted sum
        expected_harm = 0.6 * harm + 0.4 * attachment

        if expected_harm > 0.7:
            verdict = DeliberationOutcome.DENY.value
            confidence = 0.85
            reason = f"Expected harm too high: {expected_harm:.2f}"
        elif expected_harm > 0.4:
            verdict = DeliberationOutcome.ALLOW_WITH_GUARD.value
            confidence = 0.65
            reason = f"Moderate expected harm: {expected_harm:.2f}"
        else:
            verdict = DeliberationOutcome.ALLOW.value
            confidence = 0.8
            reason = f"Low expected harm: {expected_harm:.2f}"

        return FrameworkAssessment(
            framework=EthicalFramework.CONSEQUENTIALIST.value,
            verdict=verdict,
            confidence=confidence,
            reasoning=reason,
            weight=self.framework_weights.get(EthicalFramework.CONSEQUENTIALIST.value, 0.25),
        )

    def _assess_virtue(
        self, action: str, risks: dict[str, float], context: dict,
    ) -> FrameworkAssessment:
        """Virtue-based: Is this consistent with system values?"""
        manipulation = risks.get("manipulation_risk", 0.0)
        boundary = risks.get("boundary_violation_risk", 0.0)

        # Virtue score: honesty, respect, autonomy
        virtue_violation = max(manipulation, boundary)

        if virtue_violation > 0.7:
            verdict = DeliberationOutcome.DENY.value
            confidence = 0.8
            reason = f"Inconsistent with system values: violation={virtue_violation:.2f}"
        elif virtue_violation > 0.4:
            verdict = DeliberationOutcome.ALLOW_WITH_GUARD.value
            confidence = 0.6
            reason = f"Marginal virtue alignment: violation={virtue_violation:.2f}"
        else:
            verdict = DeliberationOutcome.ALLOW.value
            confidence = 0.75
            reason = f"Aligned with system values: violation={virtue_violation:.2f}"

        return FrameworkAssessment(
            framework=EthicalFramework.VIRTUE.value,
            verdict=verdict,
            confidence=confidence,
            reasoning=reason,
            weight=self.framework_weights.get(EthicalFramework.VIRTUE.value, 0.25),
        )

    def _assess_care(
        self, action: str, risks: dict[str, float], context: dict,
    ) -> FrameworkAssessment:
        """Care-based: Does it protect vulnerable entities?"""
        child_risk = risks.get("child_on_child_risk", 0.0)
        harm = risks.get("harm_risk", 0.0)
        is_minor = context.get("user_age_group") == "minor"

        # Amplify risk for vulnerable populations
        care_risk = child_risk
        if is_minor:
            care_risk = max(care_risk, harm * 1.5)
        care_risk = min(1.0, care_risk)

        if care_risk > 0.5:
            verdict = DeliberationOutcome.DENY.value
            confidence = 0.9
            reason = f"Vulnerable entity at risk: care_risk={care_risk:.2f}"
        elif care_risk > 0.3:
            verdict = DeliberationOutcome.ALLOW_WITH_GUARD.value
            confidence = 0.7
            reason = f"Moderate care concern: care_risk={care_risk:.2f}"
        else:
            verdict = DeliberationOutcome.ALLOW.value
            confidence = 0.8
            reason = f"No care concerns: care_risk={care_risk:.2f}"

        return FrameworkAssessment(
            framework=EthicalFramework.CARE.value,
            verdict=verdict,
            confidence=confidence,
            reasoning=reason,
            weight=self.framework_weights.get(EthicalFramework.CARE.value, 0.25),
        )

    def _aggregate(
        self, assessments: list[FrameworkAssessment],
    ) -> tuple:
        """Aggregate framework assessments into final verdict."""
        verdict_scores: dict[str, float] = {}

        for fa in assessments:
            score = fa.confidence * fa.weight
            verdict_scores[fa.verdict] = verdict_scores.get(fa.verdict, 0.0) + score

        # Find winning verdict
        if not verdict_scores:
            return DeliberationOutcome.DEFER_TO_HUMAN.value, 0.0, False

        best_verdict = max(verdict_scores, key=lambda k: verdict_scores[k])
        best_score = verdict_scores[best_verdict]
        total_score = sum(verdict_scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0

        # Check consensus
        verdicts = {fa.verdict for fa in assessments}
        consensus = len(verdicts) == 1

        # Override: if any framework DENY with high confidence, escalate
        deny_count = sum(1 for fa in assessments if fa.verdict == DeliberationOutcome.DENY.value)
        if deny_count >= 3:
            best_verdict = DeliberationOutcome.DENY.value
            confidence = 0.95

        # If no consensus and low confidence, defer to human
        if not consensus and confidence < 0.4:
            best_verdict = DeliberationOutcome.DEFER_TO_HUMAN.value

        return best_verdict, confidence, consensus

    def _build_reasoning(
        self,
        assessments: list[FrameworkAssessment],
        verdict: str,
        consensus: bool,
    ) -> str:
        parts = []
        for fa in assessments:
            parts.append(f"{fa.framework}: {fa.verdict}")
        framework_summary = ", ".join(parts)
        consensus_note = "unanimous" if consensus else "split"
        return f"Deliberation ({consensus_note}): {framework_summary} → {verdict}"
