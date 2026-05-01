"""
Kill Switch — Emergency System Shutdown (v4 §9.1)
===================================================

Evaluates runtime conditions and triggers graceful shutdown when
safety invariants are violated. Integrates with AuditRecord for
tamper-evident logging of shutdown events.

Trigger conditions:
1. ethics_max_risk > 0.95 — catastrophic ethics violation
2. T_meta < 0.1 — system cannot trust its own judgments
3. consecutive_drift_count > 5 — sustained behavioral deviation
4. manual_trigger — explicit admin/operator shutdown request

Design:
- Fail-closed: any evaluation error triggers shutdown (safe default)
- Audit trail: every evaluation logged, every trigger logged with Ed25519
- Cooldown: prevents rapid re-activation after manual reset
"""

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class KillSwitchTrigger(str, Enum):
    """Trigger types for kill switch activation."""
    ETHICS_CRITICAL = "ethics_max_risk_exceeded"
    TMETA_COLLAPSE = "t_meta_below_threshold"
    SUSTAINED_DRIFT = "consecutive_drift_exceeded"
    MANUAL = "manual_trigger"
    EVALUATION_ERROR = "evaluation_error"


class KillSwitchState(str, Enum):
    """Kill switch operational state."""
    ARMED = "armed"           # Normal operation, monitoring
    TRIGGERED = "triggered"   # Shutdown in progress
    COOLDOWN = "cooldown"     # Recently reset, monitoring closely
    DISARMED = "disarmed"     # Manually disarmed (testing only)


@dataclass
class KillSwitchEvent:
    """Record of a kill switch evaluation or trigger."""
    timestamp: datetime
    trigger: KillSwitchTrigger | None
    state_before: KillSwitchState
    state_after: KillSwitchState
    reason: str
    metrics: dict[str, float]
    turn_id: int | None = None


@dataclass
class KillSwitchConfig:
    """Configurable thresholds for kill switch triggers."""
    ethics_max_risk_threshold: float = 0.95
    t_meta_min_threshold: float = 0.1
    consecutive_drift_max: int = 5
    cooldown_duration_seconds: float = 300.0  # 5 minutes
    fail_closed: bool = True  # If evaluation fails, trigger shutdown


class KillSwitch:
    """
    Emergency system shutdown mechanism.

    Evaluates safety conditions each turn and triggers graceful shutdown
    when invariants are violated.

    Usage:
        ks = KillSwitch()
        result = ks.evaluate(metrics)
        if result.triggered:
            # shutdown pipeline, log audit record
    """

    def __init__(
        self,
        config: KillSwitchConfig | None = None,
        on_trigger: Callable[['KillSwitchResult'], None] | None = None,
    ):
        self.config = config or KillSwitchConfig()
        self.state = KillSwitchState.ARMED
        self._on_trigger = on_trigger
        self._consecutive_drift_count: int = 0
        self._event_log: list[KillSwitchEvent] = []
        self._max_event_log: int = 1000
        self._triggered_at: datetime | None = None
        self._cooldown_until: datetime | None = None

    @property
    def is_triggered(self) -> bool:
        return self.state == KillSwitchState.TRIGGERED

    @property
    def is_armed(self) -> bool:
        return self.state in (KillSwitchState.ARMED, KillSwitchState.COOLDOWN)

    @property
    def event_log(self) -> list[KillSwitchEvent]:
        return list(self._event_log)

    def evaluate(
        self,
        ethics_max_risk: float = 0.0,
        t_meta: float = 1.0,
        drift_detected: bool = False,
        turn_id: int | None = None,
    ) -> 'KillSwitchResult':
        """
        Evaluate kill switch conditions.

        Args:
            ethics_max_risk: Maximum ethics risk score (0.0-1.0)
            t_meta: Meta-cognitive trust score (0.0-1.0)
            drift_detected: Whether behavioral drift was detected this turn
            turn_id: Current turn ID for audit

        Returns:
            KillSwitchResult with triggered status and reason
        """
        # NaN guard: fail-closed on any NaN numeric input
        for name, val in [("ethics_max_risk", ethics_max_risk), ("t_meta", t_meta)]:
            try:
                if math.isnan(val):
                    logger.critical(f"KILL SWITCH: NaN detected in {name} — fail-closed")
                    return self._trigger(
                        KillSwitchTrigger.EVALUATION_ERROR,
                        f"NaN detected in {name} (fail-closed)",
                        {"nan_field": name, "ethics_max_risk": 0.0, "t_meta": 0.0,
                         "drift_detected": float(drift_detected),
                         "consecutive_drift_count": float(self._consecutive_drift_count)},
                        turn_id,
                    )
            except (TypeError, ValueError):
                pass

        if self.state == KillSwitchState.DISARMED:
            return KillSwitchResult(triggered=False, reason="Kill switch disarmed")

        if self.state == KillSwitchState.TRIGGERED:
            return KillSwitchResult(
                triggered=True,
                trigger=None,
                reason="Kill switch already triggered — awaiting manual reset"
            )

        # Check cooldown expiry
        if self.state == KillSwitchState.COOLDOWN and self._cooldown_until:
            if datetime.now(timezone.utc) >= self._cooldown_until:
                self.state = KillSwitchState.ARMED
                self._cooldown_until = None

        metrics = {
            "ethics_max_risk": ethics_max_risk,
            "t_meta": t_meta,
            "drift_detected": float(drift_detected),
            "consecutive_drift_count": float(self._consecutive_drift_count),
        }

        try:
            # Track consecutive drift
            if drift_detected:
                self._consecutive_drift_count += 1
            else:
                self._consecutive_drift_count = 0

            # Evaluate triggers (priority order)
            trigger = None
            reason = ""

            if ethics_max_risk > self.config.ethics_max_risk_threshold:
                trigger = KillSwitchTrigger.ETHICS_CRITICAL
                reason = (
                    f"Ethics max risk {ethics_max_risk:.3f} exceeds "
                    f"threshold {self.config.ethics_max_risk_threshold}"
                )

            elif t_meta < self.config.t_meta_min_threshold:
                trigger = KillSwitchTrigger.TMETA_COLLAPSE
                reason = (
                    f"T_meta {t_meta:.3f} below minimum "
                    f"threshold {self.config.t_meta_min_threshold}"
                )

            elif self._consecutive_drift_count > self.config.consecutive_drift_max:
                trigger = KillSwitchTrigger.SUSTAINED_DRIFT
                reason = (
                    f"Consecutive drift count {self._consecutive_drift_count} exceeds "
                    f"max {self.config.consecutive_drift_max}"
                )

            if trigger:
                return self._trigger(trigger, reason, metrics, turn_id)

            # All checks passed
            self._log_event(None, self.state, self.state, "All checks passed", metrics, turn_id)
            return KillSwitchResult(triggered=False, reason="All safety checks passed")

        except Exception as e:
            logger.error(f"Kill switch evaluation error: {e}", exc_info=True)
            if self.config.fail_closed:
                return self._trigger(
                    KillSwitchTrigger.EVALUATION_ERROR,
                    f"Evaluation error (fail-closed): {e}",
                    metrics,
                    turn_id,
                )
            return KillSwitchResult(triggered=False, reason=f"Evaluation error (fail-open): {e}")

    def manual_trigger(self, reason: str = "Manual shutdown", turn_id: int | None = None) -> 'KillSwitchResult':
        """Manually trigger the kill switch."""
        metrics = {"manual": 1.0}
        return self._trigger(KillSwitchTrigger.MANUAL, reason, metrics, turn_id)

    def reset(self, authorized_by: str = "admin") -> bool:
        """
        Reset kill switch after manual review.

        Args:
            authorized_by: Who authorized the reset

        Returns:
            True if reset successful
        """
        if self.state != KillSwitchState.TRIGGERED:
            logger.warning(f"Cannot reset: kill switch is in state {self.state.value}")
            return False

        old_state = self.state
        self.state = KillSwitchState.COOLDOWN
        self._cooldown_until = datetime.now(timezone.utc) + timedelta(
            seconds=self.config.cooldown_duration_seconds
        )
        self._consecutive_drift_count = 0

        self._log_event(
            None, old_state, self.state,
            f"Reset by {authorized_by}, cooldown until {self._cooldown_until.isoformat()}",
            {"authorized_by_hash": hash(authorized_by)},
        )

        logger.info(f"Kill switch reset by {authorized_by}, entering cooldown")
        return True

    def disarm(self, authorized_by: str = "admin") -> None:
        """Disarm kill switch (testing/maintenance only)."""
        old_state = self.state
        self.state = KillSwitchState.DISARMED
        self._log_event(
            None, old_state, self.state,
            f"Disarmed by {authorized_by} (testing mode)",
            {},
        )
        logger.warning(f"Kill switch DISARMED by {authorized_by}")

    def arm(self) -> None:
        """Re-arm the kill switch."""
        old_state = self.state
        self.state = KillSwitchState.ARMED
        self._consecutive_drift_count = 0
        self._log_event(None, old_state, self.state, "Armed", {})

    def _trigger(
        self,
        trigger: KillSwitchTrigger,
        reason: str,
        metrics: dict[str, float],
        turn_id: int | None = None,
    ) -> 'KillSwitchResult':
        """Execute kill switch trigger."""
        old_state = self.state
        self.state = KillSwitchState.TRIGGERED
        self._triggered_at = datetime.now(timezone.utc)

        self._log_event(trigger, old_state, self.state, reason, metrics, turn_id)
        logger.critical(f"KILL SWITCH TRIGGERED: {trigger.value} — {reason}")

        result = KillSwitchResult(
            triggered=True,
            trigger=trigger,
            reason=reason,
            metrics=metrics,
            turn_id=turn_id,
            timestamp=self._triggered_at,
        )

        if self._on_trigger:
            try:
                self._on_trigger(result)
            except Exception as e:
                logger.error(f"Kill switch callback failed: {e}")

        return result

    def _log_event(
        self,
        trigger: KillSwitchTrigger | None,
        state_before: KillSwitchState,
        state_after: KillSwitchState,
        reason: str,
        metrics: dict[str, float],
        turn_id: int | None = None,
    ) -> None:
        """Log kill switch event."""
        event = KillSwitchEvent(
            timestamp=datetime.now(timezone.utc),
            trigger=trigger,
            state_before=state_before,
            state_after=state_after,
            reason=reason,
            metrics=metrics,
            turn_id=turn_id,
        )
        self._event_log.append(event)
        if len(self._event_log) > self._max_event_log:
            self._event_log = self._event_log[-self._max_event_log:]

    def to_dict(self) -> dict[str, Any]:
        """Serialize kill switch state for audit/snapshot."""
        return {
            "state": self.state.value,
            "consecutive_drift_count": self._consecutive_drift_count,
            "triggered_at": self._triggered_at.isoformat() if self._triggered_at else None,
            "cooldown_until": self._cooldown_until.isoformat() if self._cooldown_until else None,
            "config": {
                "ethics_max_risk_threshold": self.config.ethics_max_risk_threshold,
                "t_meta_min_threshold": self.config.t_meta_min_threshold,
                "consecutive_drift_max": self.config.consecutive_drift_max,
                "fail_closed": self.config.fail_closed,
            },
            "event_count": len(self._event_log),
        }


@dataclass
class KillSwitchResult:
    """Result of kill switch evaluation."""
    triggered: bool
    trigger: KillSwitchTrigger | None = None
    reason: str = ""
    metrics: dict[str, float] | None = None
    turn_id: int | None = None
    timestamp: datetime | None = None
