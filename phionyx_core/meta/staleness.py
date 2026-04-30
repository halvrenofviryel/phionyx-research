"""
Stale Model Invalidation — v4 §7
==================================

Invalidates model/module outputs when they exceed staleness threshold.
Default: τ > 3600s (1 hour) → stale.
"""

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Default staleness threshold (seconds)
DEFAULT_STALENESS_THRESHOLD = 3600.0  # 1 hour


@dataclass
class StalenessEntry:
    """Tracks staleness for a single module/model."""
    module_id: str
    last_update: float  # monotonic timestamp
    threshold: float = DEFAULT_STALENESS_THRESHOLD
    is_stale: bool = False
    age_seconds: float = 0.0


@dataclass
class StalenessRegistry:
    """
    Registry tracking staleness of module outputs.

    Modules register their last update timestamp.
    Query to check if any module is stale.
    """
    entries: dict[str, StalenessEntry] = field(default_factory=dict)
    default_threshold: float = DEFAULT_STALENESS_THRESHOLD

    def register_update(
        self,
        module_id: str,
        timestamp: float | None = None,
        threshold: float | None = None,
    ) -> None:
        """Register a module update."""
        ts = timestamp if timestamp is not None else time.monotonic()
        th = threshold if threshold is not None else self.default_threshold
        self.entries[module_id] = StalenessEntry(
            module_id=module_id,
            last_update=ts,
            threshold=th,
        )

    def check_staleness(
        self,
        module_id: str,
        current_time: float | None = None,
    ) -> StalenessEntry:
        """Check if a module's output is stale."""
        now = current_time if current_time is not None else time.monotonic()

        if module_id not in self.entries:
            # Unknown module → treat as stale
            return StalenessEntry(
                module_id=module_id,
                last_update=0.0,
                is_stale=True,
                age_seconds=float("inf"),
            )

        entry = self.entries[module_id]
        age = now - entry.last_update
        is_stale = age > entry.threshold

        entry.age_seconds = age
        entry.is_stale = is_stale

        if is_stale:
            logger.warning(
                f"Stale model detected: {module_id} "
                f"(age={age:.1f}s > threshold={entry.threshold:.1f}s)"
            )

        return entry

    def get_stale_modules(
        self,
        current_time: float | None = None,
    ) -> list:
        """Get all stale modules."""
        return [
            self.check_staleness(mid, current_time)
            for mid in self.entries
            if self.check_staleness(mid, current_time).is_stale
        ]

    def invalidate(self, module_id: str) -> None:
        """Force-invalidate a module (mark as stale)."""
        if module_id in self.entries:
            self.entries[module_id].last_update = 0.0
            self.entries[module_id].is_stale = True
