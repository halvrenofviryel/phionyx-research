"""
Global Workspace Service — v4
================================

Implements Global Workspace Theory (GWT) broadcast mechanism.
High-salience events are broadcast to all subscribed modules.
Port-adapter pattern (AD-2).
"""

import logging
from typing import List, Dict, Set, Optional
from collections import defaultdict

from ..contracts.v4.workspace_event import WorkspaceEvent, SalienceLevel

logger = logging.getLogger(__name__)


class GlobalWorkspace:
    """
    In-memory Global Workspace implementation.

    Manages event subscriptions and salience-based broadcasting.
    """

    def __init__(self, salience_threshold: float = 0.3):
        self._subscribers: Dict[str, Set[str]] = defaultdict(set)
        self._event_log: List[WorkspaceEvent] = []
        self._salience_threshold = salience_threshold
        self._max_log_size = 1000

    def subscribe(self, module_id: str, event_types: List[str]) -> None:
        """Subscribe a module to specific event types."""
        for event_type in event_types:
            self._subscribers[event_type].add(module_id)

    def unsubscribe(self, module_id: str, event_types: Optional[List[str]] = None) -> None:
        """Unsubscribe a module from event types."""
        if event_types is None:
            for subs in self._subscribers.values():
                subs.discard(module_id)
        else:
            for event_type in event_types:
                self._subscribers[event_type].discard(module_id)

    async def broadcast(self, event: WorkspaceEvent) -> None:
        """Broadcast an event to subscribed modules."""
        # Skip low-salience events below threshold
        if event.salience_score < self._salience_threshold:
            logger.debug(f"Event {event.event_type} below salience threshold, logged only")
            self._log_event(event)
            return

        # Determine targets
        targets = set()
        if event.salience == SalienceLevel.CRITICAL:
            # Broadcast to ALL subscribers
            for subs in self._subscribers.values():
                targets.update(subs)
        else:
            # Broadcast to event-type subscribers
            targets = self._subscribers.get(event.event_type, set())

        event.broadcast_targets = list(targets)
        self._log_event(event)

        logger.info(
            f"GWT broadcast: {event.event_type} "
            f"(salience={event.salience.value}, targets={len(targets)})"
        )

    async def get_pending_events(self) -> List[WorkspaceEvent]:
        """Get recent events from the workspace."""
        return list(self._event_log[-50:])

    def _log_event(self, event: WorkspaceEvent) -> None:
        """Log event to workspace history."""
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
