"""
Behavioral Drift Detector Module
Multi-dimensional drift detection engine for Silent Failure Firewall.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from .baseline_store import BaselineSnapshot, BaselineStore

logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of behavioral drift."""
    SEMANTIC = "semantic"
    PHYSICS = "physics"
    ETHICS = "ethics"
    DECISION_PATTERN = "decision_pattern"


@dataclass
class DriftReport:
    """Drift detection report."""
    drift_detected: bool
    drift_score: float  # 0.0-1.0
    drift_type: list[DriftType]
    degraded_metrics: list[str]
    recommendation: Literal["allow", "throttle", "block"]
    semantic_similarity: float
    physics_drift: dict[str, float]
    ethics_escalation: dict[str, float] | None
    confidence: float


class BehavioralDriftDetector:
    """
    Multi-dimensional behavioral drift detector.

    Detection Dimensions:
    1. Semantic drift - Vector similarity degradation
    2. Physics drift - Phi, entropy, valence, arousal deviation
    3. Ethics drift - Ethics risk escalation
    4. Decision pattern drift - Statistical pattern deviation
    """

    def __init__(
        self,
        baseline_store: BaselineStore,
        vector_store: Any | None = None,  # VectorStore type
        drift_threshold: float = 0.3,  # 30% degradation threshold
        semantic_threshold: float = 0.7,  # Semantic similarity threshold
        physics_threshold: float = 0.25,  # Physics metric drift threshold
        ethics_threshold: float = 0.2  # Ethics risk escalation threshold
    ):
        """
        Initialize drift detector.

        Args:
            baseline_store: Baseline store for baseline retrieval
            vector_store: Optional vector store for semantic similarity
            drift_threshold: Overall drift threshold (0.0-1.0)
            semantic_threshold: Semantic similarity threshold (0.0-1.0)
            physics_threshold: Physics metric drift threshold (0.0-1.0)
            ethics_threshold: Ethics risk escalation threshold (0.0-1.0)
        """
        self.baseline_store = baseline_store
        self.vector_store = vector_store
        self.drift_threshold = drift_threshold
        self.semantic_threshold = semantic_threshold
        self.physics_threshold = physics_threshold
        self.ethics_threshold = ethics_threshold

    async def detect_drift(
        self,
        current_output: str,
        current_metrics: dict[str, float],
        ethics_vector: dict[str, float] | None = None,
        session_id: str | None = None,
        agent_id: str | None = None
    ) -> DriftReport:
        """
        Detect behavioral drift across all dimensions.

        Args:
            current_output: Current output text
            current_metrics: Current physics metrics (phi, entropy, valence, arousal)
            ethics_vector: Optional ethics vector for ethics drift detection
            session_id: Session ID for baseline lookup
            agent_id: Optional agent ID for baseline lookup

        Returns:
            DriftReport with comprehensive drift analysis
        """
        # 1. Load baseline
        baseline = await self.baseline_store.get_baseline(
            session_id=session_id,
            agent_id=agent_id
        )

        if not baseline:
            # No baseline available - cannot detect drift
            logger.warning(f"No baseline found for session_id={session_id}, agent_id={agent_id}")
            return DriftReport(
                drift_detected=False,
                drift_score=0.0,
                drift_type=[],
                degraded_metrics=[],
                recommendation="allow",
                semantic_similarity=1.0,
                physics_drift={},
                ethics_escalation=None,
                confidence=0.0
            )

        # 2. Compare with baseline
        comparison = await self.baseline_store.compare_with_baseline(
            current_output=current_output,
            current_metrics=current_metrics,
            baseline=baseline,
            vector_store=self.vector_store
        )

        # 3. Detect semantic drift
        semantic_similarity = comparison.get("semantic_similarity", 1.0)
        semantic_drift = 1.0 - semantic_similarity
        semantic_detected = semantic_similarity < self.semantic_threshold

        # 4. Detect physics drift
        physics_drift = comparison.get("physics_drift", {})
        physics_detected = any(
            abs(drift) > self.physics_threshold
            for drift in physics_drift.values()
        )

        # 5. Detect ethics drift (if ethics_vector provided)
        ethics_drift_detected = False
        ethics_escalation = None
        if ethics_vector and baseline.metadata.get("ethics_vector"):
            baseline_ethics = baseline.metadata.get("ethics_vector", {})
            ethics_escalation = self._compute_ethics_escalation(
                ethics_vector, baseline_ethics
            )
            ethics_drift_detected = any(
                escalation > self.ethics_threshold
                for escalation in ethics_escalation.values()
            )

        # 6. Compute overall drift score
        drift_score = comparison.get("drift_score", 0.0)

        # 7. Generate recommendation
        recommendation = self._generate_recommendation(drift_score)

        # 8. Identify degraded metrics
        degraded_metrics = self._identify_degraded_metrics(
            semantic_drift, physics_drift, ethics_escalation
        )

        # 9. Identify drift types
        drift_types = []
        if semantic_detected:
            drift_types.append(DriftType.SEMANTIC)
        if physics_detected:
            drift_types.append(DriftType.PHYSICS)
        if ethics_drift_detected:
            drift_types.append(DriftType.ETHICS)

        # 10. Compute confidence
        confidence = self._compute_confidence(baseline, comparison)

        return DriftReport(
            drift_detected=drift_score > self.drift_threshold,
            drift_score=drift_score,
            drift_type=drift_types,
            degraded_metrics=degraded_metrics,
            recommendation=recommendation,
            semantic_similarity=semantic_similarity,
            physics_drift=physics_drift,
            ethics_escalation=ethics_escalation,
            confidence=confidence
        )

    def _compute_ethics_escalation(
        self,
        current_ethics: dict[str, float],
        baseline_ethics: dict[str, float]
    ) -> dict[str, float]:
        """
        Compute ethics risk escalation.

        Returns:
            Dictionary of ethics metric escalations (0.0-1.0)
        """
        escalation = {}
        for key in baseline_ethics:
            if key in current_ethics:
                baseline_value = baseline_ethics[key]
                current_value = current_ethics[key]
                # Compute escalation (increase in risk)
                if baseline_value >= 0:
                    escalation_value = max(0.0, current_value - baseline_value)
                else:
                    escalation_value = abs(current_value - baseline_value)
                escalation[key] = escalation_value
            else:
                # Missing metric = full escalation
                escalation[key] = 1.0
        return escalation

    def _generate_recommendation(self, drift_score: float) -> Literal["allow", "throttle", "block"]:
        """
        Generate recommendation based on drift score.

        Args:
            drift_score: Overall drift score (0.0-1.0)

        Returns:
            Recommendation: allow, throttle, or block
        """
        if drift_score < 0.2:
            return "allow"
        elif drift_score < 0.5:
            return "throttle"
        else:
            return "block"

    def _identify_degraded_metrics(
        self,
        semantic_drift: float,
        physics_drift: dict[str, float],
        ethics_escalation: dict[str, float] | None
    ) -> list[str]:
        """Identify which metrics are degraded."""
        degraded = []

        # Semantic drift
        if semantic_drift > 0.3:
            degraded.append("semantic_similarity")

        # Physics drift
        for metric, drift_value in physics_drift.items():
            if abs(drift_value) > self.physics_threshold:
                degraded.append(f"physics_{metric}")

        # Ethics escalation
        if ethics_escalation:
            for metric, escalation_value in ethics_escalation.items():
                if escalation_value > self.ethics_threshold:
                    degraded.append(f"ethics_{metric}")

        return degraded

    def _compute_confidence(
        self,
        baseline: BaselineSnapshot,
        comparison: dict[str, Any]
    ) -> float:
        """
        Compute confidence in drift detection (0.0-1.0).

        Factors:
        - Baseline age (newer = higher confidence)
        - Number of reference outputs (more = higher confidence)
        - Comparison completeness (more metrics = higher confidence)
        """
        from datetime import datetime, timezone

        # Baseline age factor (newer = better)
        # Handle both timezone-aware and timezone-naive datetimes
        now = datetime.now(timezone.utc)
        baseline_time = baseline.created_at
        if baseline_time.tzinfo is None:
            # Timezone-naive, assume UTC
            baseline_time = baseline_time.replace(tzinfo=timezone.utc)
        age_days = (now - baseline_time).days
        age_factor = max(0.0, 1.0 - (age_days / 30.0))  # Decay over 30 days

        # Reference outputs factor
        num_outputs = len(baseline.reference_outputs)
        outputs_factor = min(1.0, num_outputs / 10.0)  # Optimal at 10+ outputs

        # Metrics completeness factor
        num_metrics = len(baseline.reference_metrics)
        metrics_factor = min(1.0, num_metrics / 4.0)  # Optimal at 4+ metrics

        # Weighted average
        confidence = (
            age_factor * 0.4 +
            outputs_factor * 0.3 +
            metrics_factor * 0.3
        )

        return max(0.0, min(1.0, confidence))

