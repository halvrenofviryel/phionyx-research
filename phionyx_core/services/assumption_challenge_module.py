"""
Assumption Challenge Module
===========================

Faz 3.1: Kalan Özellikler

AI varsayımlarını kabul etmek yerine challenge eder.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from phionyx_core.services.assumption_types import Assumption


class ChallengeType(Enum):
    """Type of assumption challenge."""
    EVIDENCE_MISSING = "evidence_missing"
    LOW_CONFIDENCE = "low_confidence"
    CONTRADICTORY = "contradictory"
    UNVALIDATED = "unvalidated"


@dataclass
class AssumptionChallenge:
    """Assumption challenge structure."""
    assumption_id: str
    assumption: Assumption
    challenge_type: ChallengeType
    challenge_reason: str
    required_evidence: list[str]
    severity: str = "medium"  # "low", "medium", "high", "critical"


class AssumptionChallengeModule:
    """
    Full-featured Assumption Challenge Module.

    Provides:
    - Assumption validation
    - Evidence requirement checking
    - Challenge generation
    - Assumption rejection/acceptance
    """

    def __init__(self):
        """Initialize assumption challenge module."""
        self.challenge_history: list[AssumptionChallenge] = []

    def challenge_assumptions(
        self,
        assumptions: list[Assumption]
    ) -> list[AssumptionChallenge]:
        """
        Challenge assumptions that lack evidence or have low confidence.

        Args:
            assumptions: List of Assumption objects

        Returns:
            List of AssumptionChallenge
        """
        challenges = []

        for i, assumption in enumerate(assumptions):
            # Check for missing evidence
            if not assumption.evidence or len(assumption.evidence) == 0:
                challenges.append(AssumptionChallenge(
                    assumption_id=f"assumption_{i}",
                    assumption=assumption,
                    challenge_type=ChallengeType.EVIDENCE_MISSING,
                    challenge_reason="Assumption lacks evidence",
                    required_evidence=self._get_required_evidence(assumption),
                    severity="high"
                ))

            # Check for low confidence
            elif assumption.confidence < 0.5:
                challenges.append(AssumptionChallenge(
                    assumption_id=f"assumption_{i}",
                    assumption=assumption,
                    challenge_type=ChallengeType.LOW_CONFIDENCE,
                    challenge_reason=f"Assumption has low confidence ({assumption.confidence})",
                    required_evidence=self._get_required_evidence(assumption),
                    severity="medium"
                ))

            # Check for contradictory assumptions
            contradictory = self._check_contradictory(assumption, assumptions)
            if contradictory:
                challenges.append(AssumptionChallenge(
                    assumption_id=f"assumption_{i}",
                    assumption=assumption,
                    challenge_type=ChallengeType.CONTRADICTORY,
                    challenge_reason="Assumption contradicts other assumptions",
                    required_evidence=self._get_required_evidence(assumption),
                    severity="critical"
                ))

        self.challenge_history.extend(challenges)
        return challenges

    def _get_required_evidence(self, assumption: Assumption) -> list[str]:
        """Get required evidence for assumption type."""
        evidence_map = {
            "input_type": ["Type annotation", "Usage examples", "Documentation"],
            "state": ["State initialization", "State update logic", "State invariants"],
            "dependency": ["Import statement", "Dependency declaration", "Usage in code"],
            "performance": ["Performance benchmarks", "Complexity analysis", "Resource usage"],
        }

        return evidence_map.get(assumption.type, ["Code reference", "Documentation", "Test cases"])

    def _check_contradictory(
        self,
        assumption: Assumption,
        all_assumptions: list[Assumption]
    ) -> bool:
        """Check if assumption contradicts others."""
        # Simple heuristic: check for opposite descriptions
        opposite_keywords = {
            "string": "int",
            "int": "string",
            "list": "dict",
            "dict": "list",
        }

        for other in all_assumptions:
            if other == assumption:
                continue

            # Check for type contradictions
            if assumption.type == "input_type" and other.type == "input_type":
                # Check if they describe opposite types
                for key, opposite in opposite_keywords.items():
                    if key in assumption.description.lower() and opposite in other.description.lower():
                        return True

        return False

    def process_challenge_response(
        self,
        challenge_id: str,
        response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process response to assumption challenge.

        Args:
            challenge_id: Challenge ID
            response: Response data (evidence, acceptance, etc.)

        Returns:
            Processed response
        """
        # Find challenge
        challenge = None
        for ch in self.challenge_history:
            if ch.assumption_id == challenge_id:
                challenge = ch
                break

        if not challenge:
            return {"error": "Challenge not found"}

        # Process response
        accepted = response.get("accepted", False)
        evidence_provided = response.get("evidence", [])

        if accepted and evidence_provided:
            # Assumption accepted with evidence
            return {
                "challenge_id": challenge_id,
                "status": "accepted",
                "evidence_count": len(evidence_provided),
                "assumption_validated": True
            }
        elif not accepted:
            # Assumption rejected
            return {
                "challenge_id": challenge_id,
                "status": "rejected",
                "assumption_validated": False
            }
        else:
            # Still needs evidence
            return {
                "challenge_id": challenge_id,
                "status": "pending_evidence",
                "required_evidence": challenge.required_evidence
            }


__all__ = [
    'AssumptionChallengeModule',
    'AssumptionChallenge',
    'ChallengeType',
]

