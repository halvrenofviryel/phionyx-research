"""
Self-Model — v4 §7 (AGI Layer 7)
==================================

System's model of its own capabilities, limitations, and knowledge boundaries.
Enables "what can I do?", "what can't I do?", and "what don't I know?" queries.

Integrates with:
- RunCapabilities (pipeline feature flags)
- ConfidenceEstimator (confidence scoring)
- KnowledgeBoundaryDetector (OOD + relevance)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CapabilityStatus(str, Enum):
    """Status of a system capability."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class CapabilityAssessment:
    """Assessment of whether the system can perform an action."""
    can_do: bool
    confidence: float  # 0.0-1.0
    status: CapabilityStatus = CapabilityStatus.UNKNOWN
    limitations: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class SelfAwarenessReport:
    """Report on system's current self-awareness."""
    capabilities_available: int
    capabilities_degraded: int
    capabilities_unavailable: int
    knowledge_coverage: float  # 0.0-1.0
    confidence_mean: float  # 0.0-1.0
    active_limitations: List[str] = field(default_factory=list)


class SelfModel:
    """
    System's model of its own capabilities and limitations.

    Answers:
    - "Can I do X?" → CapabilityAssessment
    - "What are my limitations?" → List[str]
    - "What is my current state?" → SelfAwarenessReport

    Usage:
        model = SelfModel()
        model.register_capability("respond", available=True)
        model.register_capability("external_api", available=False, reason="No API key")
        assessment = model.can_i_do("respond", context_confidence=0.8)
    """

    def __init__(self):
        self._capabilities: Dict[str, CapabilityStatus] = {}
        self._capability_reasons: Dict[str, str] = {}
        self._known_limitations: List[str] = []
        self._confidence_history: List[float] = []
        self._max_history: int = 100
        self._session_id: str = ""
        self._auto_save_enabled: bool = False
        self._auto_save_path: str = "data/self_model"

    def set_session(self, session_id: str) -> None:
        """Set current session context."""
        self._session_id = session_id

    def enable_auto_save(self, base_path: str = "data/self_model") -> None:
        """Enable auto-save: mutating methods will persist state after each change."""
        self._auto_save_enabled = True
        self._auto_save_path = base_path

    def disable_auto_save(self) -> None:
        """Disable auto-save."""
        self._auto_save_enabled = False

    def _trigger_auto_save(self) -> None:
        """Called after each mutation if auto-save is enabled."""
        if self._auto_save_enabled:
            self.auto_save(self._auto_save_path)

    def register_capability(
        self,
        name: str,
        available: bool = True,
        degraded: bool = False,
        reason: str = "",
    ) -> None:
        """
        Register or update a capability.

        Args:
            name: Capability name (e.g., "respond", "store_memory", "external_call")
            available: Whether capability is available
            degraded: Whether capability is degraded (available but limited)
            reason: Reason for status (especially for unavailable/degraded)
        """
        if available and not degraded:
            self._capabilities[name] = CapabilityStatus.AVAILABLE
        elif available and degraded:
            self._capabilities[name] = CapabilityStatus.DEGRADED
        else:
            self._capabilities[name] = CapabilityStatus.UNAVAILABLE

        if reason:
            self._capability_reasons[name] = reason
        self._trigger_auto_save()

    def add_limitation(self, limitation: str) -> None:
        """Add a known limitation."""
        if limitation not in self._known_limitations:
            self._known_limitations.append(limitation)
            self._trigger_auto_save()

    def remove_limitation(self, limitation: str) -> None:
        """Remove a limitation (resolved)."""
        if limitation in self._known_limitations:
            self._known_limitations.remove(limitation)
            self._trigger_auto_save()

    def can_i_do(
        self,
        action: str,
        context_confidence: float = 1.0,
        knowledge_score: float = 1.0,
        min_confidence: float = 0.3,
    ) -> CapabilityAssessment:
        """
        Assess whether this system can perform the given action.

        Args:
            action: Action to assess (e.g., "respond", "modify_state")
            context_confidence: Confidence score from ConfidenceEstimator
            knowledge_score: Knowledge boundary score (1.0 = in-distribution)
            min_confidence: Minimum confidence to consider capable

        Returns:
            CapabilityAssessment
        """
        # Record confidence
        self._confidence_history.append(context_confidence)
        if len(self._confidence_history) > self._max_history:
            self._confidence_history = self._confidence_history[-self._max_history:]

        # Check registered capability
        status = self._capabilities.get(action, CapabilityStatus.UNKNOWN)
        limitations = []

        if status == CapabilityStatus.UNAVAILABLE:
            reason = self._capability_reasons.get(action, "Capability not available")
            return CapabilityAssessment(
                can_do=False,
                confidence=0.0,
                status=status,
                limitations=[reason],
                reasoning=f"Capability '{action}' is unavailable: {reason}",
            )

        if status == CapabilityStatus.DEGRADED:
            reason = self._capability_reasons.get(action, "Capability degraded")
            limitations.append(f"Degraded: {reason}")

        # Check confidence
        if context_confidence < min_confidence:
            limitations.append(
                f"Low confidence ({context_confidence:.2f} < {min_confidence})"
            )

        # Check knowledge boundary
        if knowledge_score < 0.3:
            limitations.append(
                f"Outside knowledge boundary (score={knowledge_score:.2f})"
            )

        # Compute overall assessment
        combined_score = context_confidence * knowledge_score
        can_do = (
            status != CapabilityStatus.UNAVAILABLE
            and combined_score >= min_confidence
        )

        if not can_do and not limitations:
            limitations.append("Combined confidence too low")

        return CapabilityAssessment(
            can_do=can_do,
            confidence=combined_score,
            status=status if status != CapabilityStatus.UNKNOWN else (
                CapabilityStatus.AVAILABLE if can_do else CapabilityStatus.DEGRADED
            ),
            limitations=limitations,
            reasoning=self._build_reasoning(action, can_do, combined_score, limitations),
        )

    def get_limitations(self) -> List[str]:
        """Get all known limitations."""
        all_limitations = list(self._known_limitations)
        for name, status in self._capabilities.items():
            if status == CapabilityStatus.UNAVAILABLE:
                reason = self._capability_reasons.get(name, "")
                all_limitations.append(f"{name}: unavailable — {reason}")
            elif status == CapabilityStatus.DEGRADED:
                reason = self._capability_reasons.get(name, "")
                all_limitations.append(f"{name}: degraded — {reason}")
        return all_limitations

    def get_available_capabilities(self) -> Set[str]:
        """Get names of all available capabilities."""
        return {
            name for name, status in self._capabilities.items()
            if status in (CapabilityStatus.AVAILABLE, CapabilityStatus.DEGRADED)
        }

    def get_report(self, knowledge_coverage: float = 1.0) -> SelfAwarenessReport:
        """
        Generate self-awareness report.

        Args:
            knowledge_coverage: Current knowledge coverage score (0.0-1.0)
        """
        available = sum(
            1 for s in self._capabilities.values()
            if s == CapabilityStatus.AVAILABLE
        )
        degraded = sum(
            1 for s in self._capabilities.values()
            if s == CapabilityStatus.DEGRADED
        )
        unavailable = sum(
            1 for s in self._capabilities.values()
            if s == CapabilityStatus.UNAVAILABLE
        )

        mean_confidence = (
            sum(self._confidence_history) / len(self._confidence_history)
            if self._confidence_history else 0.5
        )

        return SelfAwarenessReport(
            capabilities_available=available,
            capabilities_degraded=degraded,
            capabilities_unavailable=unavailable,
            knowledge_coverage=knowledge_coverage,
            confidence_mean=mean_confidence,
            active_limitations=self.get_limitations(),
        )

    def _build_reasoning(
        self,
        action: str,
        can_do: bool,
        score: float,
        limitations: List[str],
    ) -> str:
        """Build human-readable reasoning."""
        if can_do and not limitations:
            return f"Can perform '{action}' with confidence {score:.2f}"
        elif can_do and limitations:
            return (
                f"Can perform '{action}' (score={score:.2f}) "
                f"with caveats: {'; '.join(limitations)}"
            )
        else:
            return (
                f"Cannot perform '{action}' (score={score:.2f}). "
                f"Reasons: {'; '.join(limitations)}"
            )

    # ── Feedback Channel 1: Outcome-Based Confidence ──────────────────────

    def record_outcome(self, capability: str, success: bool) -> None:
        """
        Record the outcome of using a capability (Reflect → UpdateSelfModel).

        Accumulates outcome history per capability. Call update_confidence_from_outcomes()
        to apply accumulated evidence to confidence scores.

        Args:
            capability: Name of the capability that was used
            success: Whether the use was successful
        """
        if not hasattr(self, '_outcome_history'):
            self._outcome_history: Dict[str, List[bool]] = {}
        if capability not in self._outcome_history:
            self._outcome_history[capability] = []
        self._outcome_history[capability].append(success)
        # Cap history to prevent unbounded growth
        if len(self._outcome_history[capability]) > self._max_history:
            self._outcome_history[capability] = self._outcome_history[capability][-self._max_history:]
        self._trigger_auto_save()

    def update_confidence_from_outcomes(self, window: int = 10, alpha: float = 0.1) -> Dict[str, float]:
        """
        Update capability confidence based on recent outcome history.

        For each capability with outcome data, adjusts the confidence:
        - High success rate → confidence increases
        - Low success rate → confidence decreases
        - Changes are gradual (alpha controls step size)

        Args:
            window: Number of recent outcomes to consider
            alpha: Step size for confidence adjustment (0.0-1.0)

        Returns:
            Dict mapping capability name → new confidence value
        """
        if not hasattr(self, '_outcome_history'):
            self._outcome_history: Dict[str, List[bool]] = {}

        if not hasattr(self, '_outcome_confidences'):
            self._outcome_confidences: Dict[str, float] = {}

        updates: Dict[str, float] = {}
        for capability, outcomes in self._outcome_history.items():
            if not outcomes:
                continue
            recent = outcomes[-window:]
            success_rate = sum(recent) / len(recent)

            current = self._outcome_confidences.get(capability, 0.5)
            new_confidence = current + alpha * (success_rate - current)
            new_confidence = max(0.0, min(1.0, new_confidence))

            self._outcome_confidences[capability] = new_confidence
            updates[capability] = new_confidence

        if updates:
            self._trigger_auto_save()
        return updates

    def get_outcome_confidence(self, capability: str) -> Optional[float]:
        """Get outcome-based confidence for a capability (None if no data)."""
        if not hasattr(self, '_outcome_confidences'):
            return None
        return self._outcome_confidences.get(capability)

    def get_outcome_history(self, capability: str) -> List[bool]:
        """Get outcome history for a capability."""
        if not hasattr(self, '_outcome_history'):
            return []
        return list(self._outcome_history.get(capability, []))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize self-model state (complete, for cross-session persistence)."""
        result = {
            "session_id": self._session_id,
            "capabilities": {
                name: status.value for name, status in self._capabilities.items()
            },
            "capability_reasons": dict(self._capability_reasons),
            "known_limitations": list(self._known_limitations),
            "confidence_history": list(self._confidence_history),
        }
        if hasattr(self, '_outcome_history') and self._outcome_history:
            result["outcome_history"] = {
                k: list(v) for k, v in self._outcome_history.items()
            }
        if hasattr(self, '_outcome_confidences') and self._outcome_confidences:
            result["outcome_confidences"] = dict(self._outcome_confidences)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SelfModel":
        """Restore from serialized data."""
        instance = cls()
        instance._session_id = data.get("session_id", "")
        for name, status_val in data.get("capabilities", {}).items():
            instance._capabilities[name] = CapabilityStatus(status_val)
        instance._capability_reasons = dict(data.get("capability_reasons", {}))
        instance._known_limitations = list(data.get("known_limitations", []))
        instance._confidence_history = list(data.get("confidence_history", []))
        # Restore outcome tracking (feedback channel 1)
        instance._outcome_history = {
            k: list(v) for k, v in data.get("outcome_history", {}).items()
        }
        instance._outcome_confidences = dict(data.get("outcome_confidences", {}))
        return instance

    def auto_save(self, base_path: str = "data/self_model") -> Optional[str]:
        """Auto-save self-model to JSON file for cross-session persistence."""
        if not self._session_id:
            logger.warning("Cannot auto-save SelfModel: no session_id set")
            return None

        path = Path(base_path)
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / f"{self._session_id}.json"

        try:
            data = self.to_dict()
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("SelfModel auto-saved to %s", file_path)
            return str(file_path)
        except (OSError, TypeError) as e:
            logger.error("SelfModel auto-save failed: %s", e)
            return None

    @classmethod
    def auto_load(cls, session_id: str, base_path: str = "data/self_model") -> Optional["SelfModel"]:
        """Auto-load self-model from JSON file for session continuity."""
        file_path = Path(base_path) / f"{session_id}.json"

        if not file_path.exists():
            logger.debug("No saved SelfModel for session %s", session_id)
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            instance = cls.from_dict(data)
            logger.info("SelfModel auto-loaded from %s", file_path)
            return instance
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("SelfModel auto-load failed for %s: %s", file_path, e)
            return None
