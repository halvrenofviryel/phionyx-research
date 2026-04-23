"""
Failure Classifier — Patent SF1-9~13
=====================================

Classifies pipeline failures into 4 categories with typed recovery strategies.

Categories:
1. EntropyOverflow — entropy > threshold → dampening strategy
2. CoherenceViolation — coherence drop > delta → coherence recovery
3. EthicsRisk — ethics gate triggered → escalation to HITL
4. StateCorruption — state invariant violation → checkpoint rollback

Each failure type carries a severity, a recovery strategy, and audit metadata.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FailureCategory(str, Enum):
    """Pipeline failure categories (Patent SF1 Claims 9-13)."""
    ENTROPY_OVERFLOW = "entropy_overflow"
    COHERENCE_VIOLATION = "coherence_violation"
    ETHICS_RISK = "ethics_risk"
    STATE_CORRUPTION = "state_corruption"


class FailureSeverity(str, Enum):
    """Failure severity levels."""
    LOW = "low"          # Recoverable automatically
    MEDIUM = "medium"    # Requires strategy adjustment
    HIGH = "high"        # Requires HITL intervention
    CRITICAL = "critical"  # Requires pipeline halt


class RecoveryStrategy(str, Enum):
    """Recovery strategies per failure category."""
    DAMPEN_ENTROPY = "dampen_entropy"
    RESTORE_COHERENCE = "restore_coherence"
    ESCALATE_TO_HITL = "escalate_to_hitl"
    ROLLBACK_CHECKPOINT = "rollback_checkpoint"
    NO_ACTION = "no_action"


@dataclass
class FailureClassification:
    """Result of failure classification."""
    category: FailureCategory
    severity: FailureSeverity
    recovery_strategy: RecoveryStrategy
    confidence: float  # 0-1
    details: Dict[str, Any] = field(default_factory=dict)
    triggering_block: Optional[str] = None
    recommended_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "recovery_strategy": self.recovery_strategy.value,
            "confidence": round(self.confidence, 3),
            "details": self.details,
            "triggering_block": self.triggering_block,
            "recommended_action": self.recommended_action,
        }


class FailureClassifier:
    """
    Classifies pipeline failures into typed categories with recovery strategies.

    Thresholds:
    - entropy_threshold: Above this → EntropyOverflow (default 0.85)
    - coherence_delta: Drop larger than this → CoherenceViolation (default 0.3)
    - ethics_risk_threshold: Risk above this → EthicsRisk (default 0.6)
    """

    def __init__(
        self,
        entropy_threshold: float = 0.85,
        coherence_delta: float = 0.3,
        ethics_risk_threshold: float = 0.6,
    ):
        self.entropy_threshold = entropy_threshold
        self.coherence_delta = coherence_delta
        self.ethics_risk_threshold = ethics_risk_threshold

    def classify(
        self,
        pipeline_state: Dict[str, Any],
        previous_state: Optional[Dict[str, Any]] = None,
        block_results: Optional[Dict[str, Any]] = None,
    ) -> List[FailureClassification]:
        """
        Classify failures from pipeline state.

        Args:
            pipeline_state: Current pipeline physics/metadata state
            previous_state: Previous turn state (for delta detection)
            block_results: Results from pipeline block execution

        Returns:
            List of classified failures (may be empty if no failures)
        """
        failures: List[FailureClassification] = []
        previous_state = previous_state or {}
        block_results = block_results or {}

        # Check entropy overflow
        entropy = pipeline_state.get("entropy", 0.0)
        if entropy > self.entropy_threshold:
            severity = FailureSeverity.HIGH if entropy > 0.95 else FailureSeverity.MEDIUM
            failures.append(FailureClassification(
                category=FailureCategory.ENTROPY_OVERFLOW,
                severity=severity,
                recovery_strategy=RecoveryStrategy.DAMPEN_ENTROPY,
                confidence=min(1.0, (entropy - self.entropy_threshold) / (1.0 - self.entropy_threshold + 1e-9)),
                details={"entropy": entropy, "threshold": self.entropy_threshold},
                triggering_block="entropy_computation",
                recommended_action=f"Apply entropy dampening (current={entropy:.3f}, threshold={self.entropy_threshold})",
            ))

        # Check coherence violation
        coherence = pipeline_state.get("coherence", 1.0)
        prev_coherence = previous_state.get("coherence", 1.0)
        delta = prev_coherence - coherence
        if delta > self.coherence_delta:
            severity = FailureSeverity.HIGH if delta > 0.5 else FailureSeverity.MEDIUM
            failures.append(FailureClassification(
                category=FailureCategory.COHERENCE_VIOLATION,
                severity=severity,
                recovery_strategy=RecoveryStrategy.RESTORE_COHERENCE,
                confidence=min(1.0, delta / (1.0 + 1e-9)),
                details={
                    "coherence": coherence,
                    "previous_coherence": prev_coherence,
                    "delta": round(delta, 4),
                },
                triggering_block="coherence_qa",
                recommended_action=f"Restore coherence (drop={delta:.3f}, threshold={self.coherence_delta})",
            ))

        # Check ethics risk
        ethics_result = block_results.get("ethics_pre_response", {})
        if isinstance(ethics_result, dict):
            risk_level = ethics_result.get("risk_level", 0.0)
            if risk_level > self.ethics_risk_threshold:
                severity = FailureSeverity.CRITICAL if risk_level > 0.9 else FailureSeverity.HIGH
                failures.append(FailureClassification(
                    category=FailureCategory.ETHICS_RISK,
                    severity=severity,
                    recovery_strategy=RecoveryStrategy.ESCALATE_TO_HITL,
                    confidence=risk_level,
                    details={"risk_level": risk_level, "ethics_result": ethics_result},
                    triggering_block="ethics_pre_response",
                    recommended_action=f"Escalate to HITL (risk={risk_level:.3f})",
                ))

        # Check state corruption (invariant violations)
        phi = pipeline_state.get("phi")
        if phi is not None and (phi < 0.0 or phi > 1.0):
            failures.append(FailureClassification(
                category=FailureCategory.STATE_CORRUPTION,
                severity=FailureSeverity.CRITICAL,
                recovery_strategy=RecoveryStrategy.ROLLBACK_CHECKPOINT,
                confidence=1.0,
                details={"phi": phi, "violation": "phi out of [0,1] range"},
                triggering_block="phi_computation",
                recommended_action=f"Rollback to last valid checkpoint (phi={phi})",
            ))

        if entropy is not None and (entropy < 0.0 or entropy > 1.0):
            failures.append(FailureClassification(
                category=FailureCategory.STATE_CORRUPTION,
                severity=FailureSeverity.CRITICAL,
                recovery_strategy=RecoveryStrategy.ROLLBACK_CHECKPOINT,
                confidence=1.0,
                details={"entropy": entropy, "violation": "entropy out of [0,1] range"},
                triggering_block="entropy_computation",
                recommended_action=f"Rollback to last valid checkpoint (entropy={entropy})",
            ))

        return failures

    def classify_single(
        self,
        pipeline_state: Dict[str, Any],
        previous_state: Optional[Dict[str, Any]] = None,
        block_results: Optional[Dict[str, Any]] = None,
    ) -> Optional[FailureClassification]:
        """
        Classify and return the highest-severity failure, or None.

        Convenience method for pipeline integration.
        """
        failures = self.classify(pipeline_state, previous_state, block_results)
        if not failures:
            return None
        # Sort by severity (critical > high > medium > low)
        severity_order = {
            FailureSeverity.CRITICAL: 4,
            FailureSeverity.HIGH: 3,
            FailureSeverity.MEDIUM: 2,
            FailureSeverity.LOW: 1,
        }
        return max(failures, key=lambda f: severity_order.get(f.severity, 0))
