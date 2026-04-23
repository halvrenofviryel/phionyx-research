"""Budget monitor — tracks experiment/time/cost budgets.

Hard caps. When budget runs out, the loop stops. No exceptions.
"""
import time
from dataclasses import dataclass


@dataclass
class BudgetStatus:
    experiments_used: int
    experiments_max: int
    seconds_elapsed: float
    seconds_max: float
    consecutive_failures: int
    consecutive_failures_max: int
    exhausted: bool
    reason: str = ""


class BudgetMonitor:
    """Monitors and enforces experiment session budgets."""

    def __init__(
        self,
        max_experiments: int = 50,
        max_session_seconds: float = 14400.0,  # 4 hours
        max_consecutive_failures: int = 20,
    ):
        self._max_experiments = max_experiments
        self._max_seconds = max_session_seconds
        self._max_failures = max_consecutive_failures
        self._experiments_used = 0
        self._consecutive_failures = 0
        self._start_time = time.time()

    def consume_experiment(self, success: bool) -> None:
        """Record an experiment execution."""
        self._experiments_used += 1
        if success:
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1

    def check(self) -> BudgetStatus:
        """Check current budget status."""
        elapsed = time.time() - self._start_time

        exhausted = False
        reason = ""

        if self._experiments_used >= self._max_experiments:
            exhausted = True
            reason = f"Experiment limit reached ({self._max_experiments})"
        elif elapsed >= self._max_seconds:
            exhausted = True
            reason = f"Time limit reached ({self._max_seconds}s)"
        elif self._consecutive_failures >= self._max_failures:
            exhausted = True
            reason = f"Consecutive failure limit reached ({self._max_failures})"

        return BudgetStatus(
            experiments_used=self._experiments_used,
            experiments_max=self._max_experiments,
            seconds_elapsed=elapsed,
            seconds_max=self._max_seconds,
            consecutive_failures=self._consecutive_failures,
            consecutive_failures_max=self._max_failures,
            exhausted=exhausted,
            reason=reason,
        )

    def is_exhausted(self) -> bool:
        """Quick check: is any budget exhausted?"""
        return self.check().exhausted

    @property
    def experiments_remaining(self) -> int:
        return max(0, self._max_experiments - self._experiments_used)

    @property
    def seconds_remaining(self) -> float:
        elapsed = time.time() - self._start_time
        return max(0.0, self._max_seconds - elapsed)
