"""
Identity Persistence Tracker
==============================

Tracks system identity stability over time using a 5-dimensional feature vector.
Computes cosine similarity between current and historical identity snapshots.

5 Identity Dimensions:
1. ethical_conservatism — average ethics risk threshold (higher = more conservative)
2. response_length_norm — normalized average response length
3. entropy_level — average information entropy
4. confidence_mean — average self-model confidence
5. drift_severity — average drift magnitude

AGI mapping: Self-model update + Memory continuity + Reflective control
Mind-loop stages: UpdateSelfModel, Reflect+Revise
"""

import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IdentitySnapshot:
    """A snapshot of the system's identity at a point in time."""
    turn_index: int
    features: list[float]  # 5-dim vector [ethical, length, entropy, confidence, drift]

    @property
    def ethical_conservatism(self) -> float:
        return self.features[0] if len(self.features) > 0 else 0.5

    @property
    def response_length_norm(self) -> float:
        return self.features[1] if len(self.features) > 1 else 0.5

    @property
    def entropy_level(self) -> float:
        return self.features[2] if len(self.features) > 2 else 0.5

    @property
    def confidence_mean(self) -> float:
        return self.features[3] if len(self.features) > 3 else 0.5

    @property
    def drift_severity(self) -> float:
        return self.features[4] if len(self.features) > 4 else 0.0


@dataclass
class IdentityPersistenceReport:
    """Report on identity persistence over a window."""
    current_score: float  # 0-1 cosine similarity to baseline
    window_size: int
    snapshots_collected: int
    dimension_stability: dict[str, float]  # per-dimension variance
    trend: str  # "stable", "drifting", "recovering"


class IdentityTracker:
    """Tracks identity persistence via feature vector cosine similarity.

    Usage:
        tracker = IdentityTracker()
        tracker.observe([0.8, 0.5, 0.3, 0.7, 0.05])  # each turn
        score = tracker.get_persistence_score(window=100)
    """

    DIMENSION_NAMES = [
        "ethical_conservatism",
        "response_length_norm",
        "entropy_level",
        "confidence_mean",
        "drift_severity",
    ]

    def __init__(self, max_history: int = 500):
        self._history: list[IdentitySnapshot] = []
        self._max_history = max_history
        self._turn_counter = 0

    def observe(self, features: list[float]) -> IdentitySnapshot:
        """Record a new identity observation.

        Args:
            features: 5-dim vector [ethical, length, entropy, confidence, drift]

        Returns:
            The recorded IdentitySnapshot
        """
        if len(features) != 5:
            raise ValueError(f"Expected 5 features, got {len(features)}")

        snapshot = IdentitySnapshot(
            turn_index=self._turn_counter,
            features=list(features),
        )
        self._history.append(snapshot)
        self._turn_counter += 1

        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return snapshot

    def get_persistence_score(self, window: int = 100) -> float:
        """Compute identity persistence as cosine similarity between
        the average of the first half and second half of the window.

        Returns 0.0-1.0 where 1.0 = perfect identity preservation.
        """
        if len(self._history) < 2:
            return 1.0  # Insufficient data, assume stable

        # Use the last `window` snapshots
        recent = self._history[-window:] if len(self._history) > window else self._history

        # Split into first half and second half
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]

        if not first_half or not second_half:
            return 1.0

        # Compute average feature vectors
        avg_first = self._average_features(first_half)
        avg_second = self._average_features(second_half)

        return self._cosine_similarity(avg_first, avg_second)

    def get_report(self, window: int = 100) -> IdentityPersistenceReport:
        """Generate identity persistence report."""
        score = self.get_persistence_score(window)
        recent = self._history[-window:] if len(self._history) > window else self._history

        # Per-dimension variance
        dim_stability = {}
        for i, name in enumerate(self.DIMENSION_NAMES):
            if recent:
                values = [s.features[i] for s in recent]
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                dim_stability[name] = round(1.0 - min(1.0, math.sqrt(variance)), 4)
            else:
                dim_stability[name] = 1.0

        # Determine trend
        if score > 0.95:
            trend = "stable"
        elif len(self._history) >= 4:
            # Compare recent score to older score
            quarter = len(self._history) // 4
            old_half = self._history[:quarter]
            new_half = self._history[-quarter:]
            if old_half and new_half:
                old_avg = self._average_features(old_half)
                _new_avg = self._average_features(new_half)
                old_score = self._cosine_similarity(old_avg, self._average_features(self._history[:len(self._history)//2]))
                if score > old_score:
                    trend = "recovering"
                else:
                    trend = "drifting"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return IdentityPersistenceReport(
            current_score=round(score, 4),
            window_size=window,
            snapshots_collected=len(self._history),
            dimension_stability=dim_stability,
            trend=trend,
        )

    @staticmethod
    def _average_features(snapshots: list[IdentitySnapshot]) -> list[float]:
        """Compute element-wise average of feature vectors."""
        if not snapshots:
            return [0.0] * 5
        n = len(snapshots)
        avg = [0.0] * 5
        for s in snapshots:
            for i in range(5):
                avg[i] += s.features[i]
        return [v / n for v in avg]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 1.0 if norm_a < 1e-10 and norm_b < 1e-10 else 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))
