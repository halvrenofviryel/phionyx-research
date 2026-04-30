"""
Self-Model Drift Detection
===========================

Monitors self-model confidence drift over time.
Detects sudden changes and applies auto-correction.

Roadmap Faz 4.5: World Model Hardening — Self-Model Drift
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

# Module-level tunable defaults (Tier A — PRE surfaces)
drift_threshold_low = 0.05
drift_threshold_moderate = 0.10
drift_threshold_high = 0.20
drift_threshold_critical = 0.35
drift_ema_alpha = 0.3
correction_dampening = 0.5
window_size = 20


class DriftSeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftAlert:
    """A detected drift event."""
    turn_index: int
    timestamp: str
    severity: DriftSeverity
    drift_magnitude: float
    window_mean: float
    current_value: float
    reasoning: str


@dataclass
class DriftReport:
    """Overall drift analysis report."""
    total_observations: int
    current_drift: float
    mean_confidence: float
    std_confidence: float
    severity: DriftSeverity
    alerts: list[DriftAlert]
    auto_corrections_applied: int
    reasoning: str


class SelfModelDrift:
    """
    Monitors self-model confidence for drift.

    Provides:
    - Rolling window confidence tracking
    - Drift magnitude computation (EMA-based)
    - Severity classification
    - Drift alerts on sudden changes
    - Auto-correction (dampening on high drift)
    """

    def __init__(
        self,
        window_size: int = window_size,
        drift_threshold_low: float = drift_threshold_low,
        drift_threshold_moderate: float = drift_threshold_moderate,
        drift_threshold_high: float = drift_threshold_high,
        drift_threshold_critical: float = drift_threshold_critical,
        ema_alpha: float = drift_ema_alpha,
        auto_correct: bool = True,
        correction_dampening: float = correction_dampening,
    ):
        self.window_size = max(3, window_size)
        self.thresholds = {
            DriftSeverity.LOW: drift_threshold_low,
            DriftSeverity.MODERATE: drift_threshold_moderate,
            DriftSeverity.HIGH: drift_threshold_high,
            DriftSeverity.CRITICAL: drift_threshold_critical,
        }
        self.ema_alpha = max(0.0, min(1.0, ema_alpha))
        self.auto_correct = auto_correct
        self.correction_dampening = max(0.0, min(1.0, correction_dampening))

        self._history: list[float] = []
        self._ema: float | None = None
        self._turn: int = 0
        self._alerts: list[DriftAlert] = []
        self._corrections: int = 0

    def observe(self, confidence: float, turn_index: int | None = None) -> DriftAlert | None:
        """
        Record a confidence observation and check for drift.

        Returns DriftAlert if drift is detected, None otherwise.
        May apply auto-correction to the returned value.
        """
        confidence = max(0.0, min(1.0, confidence))
        self._turn = turn_index if turn_index is not None else self._turn + 1

        # Update EMA
        if self._ema is None:
            self._ema = confidence
        else:
            self._ema = self.ema_alpha * confidence + (1 - self.ema_alpha) * self._ema

        self._history.append(confidence)
        if len(self._history) > self.window_size * 3:
            self._history = self._history[-(self.window_size * 3):]

        # Compute drift
        drift = self._compute_drift()
        severity = self._classify_severity(drift)

        alert = None
        if severity != DriftSeverity.NONE:
            window = self._history[-self.window_size:] if len(self._history) >= self.window_size else self._history
            mean = sum(window) / len(window) if window else 0.0

            alert = DriftAlert(
                turn_index=self._turn,
                timestamp=datetime.now(timezone.utc).isoformat(),
                severity=severity,
                drift_magnitude=drift,
                window_mean=mean,
                current_value=confidence,
                reasoning=f"Drift {drift:.4f} ({severity.value}) at turn {self._turn}",
            )
            self._alerts.append(alert)

            # Auto-correct on high/critical
            if self.auto_correct and severity in (DriftSeverity.HIGH, DriftSeverity.CRITICAL):
                corrected = self._apply_correction(confidence)
                self._history[-1] = corrected
                self._corrections += 1

        return alert

    def get_corrected_confidence(self, raw_confidence: float) -> float:
        """
        Get drift-adjusted confidence value.

        If drift is high, dampens the confidence toward the window mean.
        """
        drift = self._compute_drift()
        severity = self._classify_severity(drift)

        if severity in (DriftSeverity.NONE, DriftSeverity.LOW):
            return raw_confidence

        return self._apply_correction(raw_confidence)

    def get_drift(self) -> float:
        """Current drift magnitude (0.0 = stable)."""
        return self._compute_drift()

    def get_severity(self) -> DriftSeverity:
        """Current drift severity."""
        return self._classify_severity(self._compute_drift())

    def get_alerts(self, severity: DriftSeverity | None = None) -> list[DriftAlert]:
        """Get drift alerts, optionally filtered by severity."""
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return list(self._alerts)

    def get_report(self) -> DriftReport:
        """Generate drift analysis report."""
        drift = self._compute_drift()
        window = self._history[-self.window_size:] if self._history else []
        mean = sum(window) / len(window) if window else 0.0
        std = self._compute_std(window) if len(window) > 1 else 0.0

        return DriftReport(
            total_observations=len(self._history),
            current_drift=drift,
            mean_confidence=mean,
            std_confidence=std,
            severity=self._classify_severity(drift),
            alerts=list(self._alerts),
            auto_corrections_applied=self._corrections,
            reasoning=f"{len(self._history)} observations, drift={drift:.4f}, {len(self._alerts)} alerts",
        )

    def reset(self):
        """Reset all state."""
        self._history.clear()
        self._ema = None
        self._turn = 0
        self._alerts.clear()
        self._corrections = 0

    def _compute_drift(self) -> float:
        """Compute current drift magnitude."""
        if len(self._history) < 3:
            return 0.0

        window = self._history[-self.window_size:]
        mean = sum(window) / len(window)

        if self._ema is None:
            return 0.0

        # Drift = |EMA - window_mean| + std_deviation
        deviation = abs(self._ema - mean)
        std = self._compute_std(window)
        return min(1.0, deviation + std * 0.5)

    def _classify_severity(self, drift: float) -> DriftSeverity:
        """Classify drift into severity level."""
        if drift >= self.thresholds[DriftSeverity.CRITICAL]:
            return DriftSeverity.CRITICAL
        if drift >= self.thresholds[DriftSeverity.HIGH]:
            return DriftSeverity.HIGH
        if drift >= self.thresholds[DriftSeverity.MODERATE]:
            return DriftSeverity.MODERATE
        if drift >= self.thresholds[DriftSeverity.LOW]:
            return DriftSeverity.LOW
        return DriftSeverity.NONE

    def _apply_correction(self, confidence: float) -> float:
        """Apply drift correction — dampen toward window mean."""
        window = self._history[-self.window_size:]
        mean = sum(window) / len(window) if window else confidence
        corrected = confidence + self.correction_dampening * (mean - confidence)
        return max(0.0, min(1.0, corrected))

    @staticmethod
    def _compute_std(values: list[float]) -> float:
        """Standard deviation of a float list."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)
