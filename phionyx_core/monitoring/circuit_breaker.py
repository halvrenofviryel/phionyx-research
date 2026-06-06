"""
Circuit Breaker Module
Deterministic circuit breaker with state machine for automatic execution halting.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time
import logging

from .behavioral_drift import DriftReport

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"    # Normal operation
    OPEN = "open"        # Blocked - requires human approval
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerResult:
    """Circuit breaker check result."""
    allowed: bool
    reason: Optional[str]
    human_approval_required: bool
    safe_mode_required: bool
    drift_report: Optional[DriftReport] = None


class CircuitBreaker:
    """
    Deterministic circuit breaker with state machine.

    States:
    - CLOSED: Normal operation, drift monitoring active
    - OPEN: Drift detected, execution blocked, human approval required
    - HALF_OPEN: Testing recovery, limited execution allowed

    State Transitions:
    - CLOSED -> OPEN: Drift exceeds threshold
    - OPEN -> HALF_OPEN: Recovery timeout expired, testing recovery
    - HALF_OPEN -> CLOSED: Recovery successful, drift below threshold
    - HALF_OPEN -> OPEN: Recovery failed, drift still exceeds threshold
    """

    def __init__(
        self,
        drift_threshold: float = 0.3,
        failure_threshold: int = 3,  # Consecutive failures to open
        recovery_timeout: float = 300.0,  # 5 minutes
        half_open_test_limit: int = 5,  # Max executions in HALF_OPEN
        ethics_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            drift_threshold: Drift threshold to open circuit (0.0-1.0)
            failure_threshold: Number of consecutive failures to open circuit
            recovery_timeout: Time in seconds before attempting recovery (HALF_OPEN)
            half_open_test_limit: Maximum executions allowed in HALF_OPEN state
            ethics_config: Optional ethics enforcement config
        """
        self.drift_threshold = drift_threshold
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_test_limit = half_open_test_limit
        self.ethics_config = ethics_config or {}

        # State machine
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_executions = 0
        self.last_success_time: Optional[float] = None

    async def check_before_execution(
        self,
        context: Dict[str, Any]  # BlockContext-like dict
    ) -> CircuitBreakerResult:
        """
        Check circuit state before execution (pre-gate).

        Args:
            context: Execution context (may contain ethics_vector, etc.)

        Returns:
            CircuitBreakerResult indicating if execution is allowed
        """
        # 1. Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout expired
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) > self.recovery_timeout:
                # Transition to HALF_OPEN for recovery testing
                self.state = CircuitState.HALF_OPEN
                self.half_open_executions = 0
                logger.info("Circuit breaker: OPEN -> HALF_OPEN (recovery testing)")
            else:
                # Still OPEN - require human approval
                return CircuitBreakerResult(
                    allowed=False,
                    reason=f"Circuit breaker is OPEN - previous drift detected (failure_count={self.failure_count})",
                    human_approval_required=True,
                    safe_mode_required=True
                )

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_executions >= self.half_open_test_limit:
                # Too many test executions without recovery - back to OPEN
                self.state = CircuitState.OPEN
                self.last_failure_time = time.time()
                return CircuitBreakerResult(
                    allowed=False,
                    reason="Circuit breaker: HALF_OPEN -> OPEN (recovery failed)",
                    human_approval_required=True,
                    safe_mode_required=True
                )
            # Allow limited execution in HALF_OPEN state
            self.half_open_executions += 1

        # 2. Check ethics (if context has ethics_vector)
        if "ethics_vector" in context:
            # Simple ethics check (can be extended with full ethics enforcement)
            ethics_vector = context.get("ethics_vector", {})
            if isinstance(ethics_vector, dict):
                # Check for high risk values
                high_risk = any(
                    abs(value) > 0.8 for value in ethics_vector.values()
                )
                if high_risk:
                    self.failure_count += 1
                    if self.failure_count >= self.failure_threshold:
                        self.state = CircuitState.OPEN
                        self.last_failure_time = time.time()
                        return CircuitBreakerResult(
                            allowed=False,
                            reason=f"Circuit opened due to repeated ethics violations (count={self.failure_count})",
                            human_approval_required=True,
                            safe_mode_required=True
                        )

        # Execution allowed
        return CircuitBreakerResult(
            allowed=True,
            reason=None,
            human_approval_required=False,
            safe_mode_required=False
        )

    async def check_after_execution(
        self,
        drift_report: DriftReport
    ) -> CircuitBreakerResult:
        """
        Check drift after execution (post-gate).

        If drift detected, open circuit for next requests.

        Args:
            drift_report: Drift detection report

        Returns:
            CircuitBreakerResult with drift information
        """
        if drift_report.drift_detected:
            # Drift detected - increment failure count
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # Recovery failed - back to OPEN
                self.state = CircuitState.OPEN
                self.half_open_executions = 0
                logger.warning("Circuit breaker: HALF_OPEN -> OPEN (drift detected in recovery)")
            elif self.failure_count >= self.failure_threshold:
                # Open circuit
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker: CLOSED -> OPEN (drift_score={drift_report.drift_score:.2f})")

            return CircuitBreakerResult(
                allowed=False,
                reason=f"Drift detected: score={drift_report.drift_score:.2f}, types={[dt.value for dt in drift_report.drift_type]}",
                human_approval_required=True,
                safe_mode_required=True,
                drift_report=drift_report
            )

        # No drift detected
        if self.state == CircuitState.HALF_OPEN:
            # Recovery successful - reset failure count
            self.failure_count = 0
            self.last_success_time = time.time()
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker: HALF_OPEN -> CLOSED (recovery successful)")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.last_success_time and (time.time() - self.last_success_time) > 60.0:
                # 1 minute of successful operation - reset failure count
                self.failure_count = 0
            self.last_success_time = time.time()

        return CircuitBreakerResult(
            allowed=True,
            reason=None,
            human_approval_required=False,
            safe_mode_required=False,
            drift_report=drift_report
        )

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_executions = 0
        self.last_success_time = None
        logger.info("Circuit breaker: RESET -> CLOSED")

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "half_open_executions": self.half_open_executions,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time
        }

