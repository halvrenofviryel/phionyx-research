"""
Controllable Forgetting - Echoism Core v1.1
============================================

Per Echoism Core v1.1:
- Passive Decay: Event intensity/trace_weight decays with exp(-λ*dt), λ from Inertia (I)
- Active Suppression: User says "forget this" → intensity/trace_weight * 0.1, suppressed=true, reversible
- Full Erasure: User says "delete completely" → permanent deletion (DB + index), tombstone in E_tags
- GDPR/Privacy compliance: Erasure audit log
- Entropy invariant: H >= 0.01 (never zero)
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime
import math


# Module-level tunable defaults (Tier A — PRE surfaces)
suppression_factor = 0.1
min_intensity = 0.001


class ForgettingConfig:
    """Configuration for controllable forgetting."""

    def __init__(
        self,
        suppression_factor: float = suppression_factor,  # 90% reduction
        min_intensity: float = min_intensity,  # Minimum intensity after suppression
        min_entropy: float = 0.01,  # Entropy invariant
        audit_log_enabled: bool = True
    ):
        self.suppression_factor = suppression_factor
        self.min_intensity = min_intensity
        self.min_entropy = min_entropy
        self.audit_log_enabled = audit_log_enabled


class EventForgettingState:
    """State for event forgetting (suppression/erasure)."""

    def __init__(
        self,
        event_id: str,
        suppressed: bool = False,
        suppressed_at: Optional[datetime] = None,
        erased: bool = False,
        erased_at: Optional[datetime] = None,
        original_intensity: Optional[float] = None
    ):
        self.event_id = event_id
        self.suppressed = suppressed
        self.suppressed_at = suppressed_at
        self.erased = erased
        self.erased_at = erased_at
        self.original_intensity = original_intensity


def apply_passive_decay(
    event_intensity: float,
    trace_weight: float,
    dt: float,
    decay_rate_lambda: float,
    min_intensity: float = 0.001
) -> Dict[str, float]:
    """
    Apply passive decay to event intensity and trace weight.

    Per Echoism Core v1.1:
    - Decay: exp(-λ * dt)
    - λ (decay rate) comes from Inertia (I) via apply_inertia_to_decay_rate()

    Args:
        event_intensity: Current event intensity (0.0-1.0)
        trace_weight: Current trace weight (0.0-1.0)
        dt: Time delta since last update (seconds)
        decay_rate_lambda: Decay rate λ (from Inertia)
        min_intensity: Minimum intensity after decay

    Returns:
        Dictionary with decayed intensity and trace_weight
    """
    # Decay factor: exp(-λ * dt)
    decay_factor = math.exp(-decay_rate_lambda * dt)

    # Apply decay
    intensity_decayed = event_intensity * decay_factor
    trace_weight_decayed = trace_weight * decay_factor

    # Clamp to minimum
    intensity_decayed = max(min_intensity, intensity_decayed)
    trace_weight_decayed = max(min_intensity, trace_weight_decayed)

    return {
        "intensity": intensity_decayed,
        "trace_weight": trace_weight_decayed,
        "decay_factor": decay_factor
    }


def apply_active_suppression(
    event_intensity: float,
    trace_weight: float,
    suppression_factor: float = 0.1,
    min_intensity: float = 0.001
) -> Dict[str, Any]:
    """
    Apply active suppression to event (user says "forget this").

    Per Echoism Core v1.1:
    - Event is NOT deleted
    - Intensity and trace_weight reduced by suppression_factor (default: 90% reduction)
    - suppressed=true flag set
    - Reversible (can be restored)

    Args:
        event_intensity: Current event intensity
        trace_weight: Current trace weight
        suppression_factor: Suppression factor (default: 0.1 = 90% reduction)
        min_intensity: Minimum intensity after suppression

    Returns:
        Dictionary with suppressed values and metadata
    """
    # Store original for potential restoration
    original_intensity = event_intensity
    original_trace_weight = trace_weight

    # Apply suppression (90% reduction)
    intensity_suppressed = event_intensity * suppression_factor
    trace_weight_suppressed = trace_weight * suppression_factor

    # Clamp to minimum
    intensity_suppressed = max(min_intensity, intensity_suppressed)
    trace_weight_suppressed = max(min_intensity, trace_weight_suppressed)

    return {
        "intensity": intensity_suppressed,
        "trace_weight": trace_weight_suppressed,
        "suppressed": True,
        "original_intensity": original_intensity,
        "original_trace_weight": original_trace_weight,
        "suppressed_at": datetime.now()
    }


def restore_suppressed_event(
    suppressed_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Restore a suppressed event (reverse active suppression).

    Per Echoism Core v1.1:
    - Suppression is reversible
    - Restore original intensity and trace_weight

    Args:
        suppressed_state: Suppressed event state (from apply_active_suppression)

    Returns:
        Dictionary with restored values
    """
    original_intensity = suppressed_state.get("original_intensity", suppressed_state.get("intensity", 0.0))
    original_trace_weight = suppressed_state.get("original_trace_weight", suppressed_state.get("trace_weight", 0.0))

    return {
        "intensity": original_intensity,
        "trace_weight": original_trace_weight,
        "suppressed": False,
        "restored_at": datetime.now()
    }


def apply_full_erasure(
    event_id: str,
    audit_log: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Apply full erasure to event (user says "delete completely").

    Per Echoism Core v1.1:
    - Event is permanently deleted (DB + index)
    - E_tags reference becomes tombstone (id + "erased" tag)
    - GDPR/Privacy: Erasure audit log entry

    Args:
        event_id: Event ID to erase
        audit_log: Audit log list (for GDPR compliance)

    Returns:
        Dictionary with erasure metadata
    """
    erasure_record = {
        "event_id": event_id,
        "erased_at": datetime.now().isoformat(),
        "reason": "user_request_full_erasure",
        "gdpr_compliant": True
    }

    # Add to audit log if enabled
    if audit_log is not None:
        audit_log.append(erasure_record)

    return {
        "erased": True,
        "event_id": event_id,
        "erased_at": datetime.now(),
        "tombstone_id": f"erased_{event_id}",
        "audit_log_entry": erasure_record
    }


def create_tombstone_reference(
    event_id: str,
    original_tag: str
) -> Dict[str, Any]:
    """
    Create tombstone reference for erased event in E_tags.

    Per Echoism Core v1.1:
    - E_tags references are NOT deleted
    - Instead, replaced with tombstone (id + "erased" tag)

    Args:
        event_id: Original event ID
        original_tag: Original event tag

    Returns:
        Tombstone reference dictionary
    """
    return {
        "id": f"erased_{event_id}",
        "tag": "erased",
        "intensity": 0.0,
        "original_id": event_id,
        "original_tag": original_tag,
        "erased_at": datetime.now().isoformat()
    }


def apply_forgetting_to_entropy(
    current_entropy: float,
    min_entropy: float = 0.01
) -> float:
    """
    Apply forgetting to entropy (ensure H >= 0.01 invariant).

    Per Echoism Core v1.1:
    - Entropy H never goes to 0
    - Clamp minimum to 0.01

    Args:
        current_entropy: Current entropy value
        min_entropy: Minimum entropy (default: 0.01)

    Returns:
        Clamped entropy value
    """
    return max(min_entropy, current_entropy)


def calculate_decay_rate_from_inertia(
    base_decay_rate: float,
    inertia: float
) -> float:
    """
    Calculate decay rate λ from Inertia (I).

    Per Echoism Core v1.1:
    - Uses core-physics.inertia.apply_inertia_to_decay_rate()

    Args:
        base_decay_rate: Base decay rate
        inertia: Inertia value (0.0-1.0)

    Returns:
        Adjusted decay rate λ
    """
    try:
        from phionyx_core.physics.inertia import apply_inertia_to_decay_rate
        return apply_inertia_to_decay_rate(base_decay_rate, inertia)
    except ImportError:
        # Fallback
        return base_decay_rate * (1.0 - inertia)


class ForgettingManager:
    """
    Manager for controllable forgetting operations.

    Per Echoism Core v1.1:
    - Coordinates passive decay, active suppression, full erasure
    - Maintains audit log for GDPR compliance
    - Manages event state (suppressed/erased)
    """

    def __init__(self, config: Optional[ForgettingConfig] = None):
        self.config = config or ForgettingConfig()
        self.suppressed_events: Dict[str, Dict[str, Any]] = {}
        self.erased_events: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def apply_passive_decay_to_event(
        self,
        event_id: str,
        event_intensity: float,
        trace_weight: float,
        dt: float,
        decay_rate_lambda: float
    ) -> Dict[str, float]:
        """Apply passive decay to a single event."""
        return apply_passive_decay(
            event_intensity=event_intensity,
            trace_weight=trace_weight,
            dt=dt,
            decay_rate_lambda=decay_rate_lambda,
            min_intensity=self.config.min_intensity
        )

    def suppress_event(
        self,
        event_id: str,
        event_intensity: float,
        trace_weight: float
    ) -> Dict[str, Any]:
        """Apply active suppression to an event."""
        suppressed = apply_active_suppression(
            event_intensity=event_intensity,
            trace_weight=trace_weight,
            suppression_factor=self.config.suppression_factor,
            min_intensity=self.config.min_intensity
        )
        suppressed["event_id"] = event_id
        self.suppressed_events[event_id] = suppressed

        # Audit log
        if self.config.audit_log_enabled:
            self.audit_log.append({
                "event_id": event_id,
                "action": "suppress",
                "timestamp": datetime.now().isoformat(),
                "original_intensity": suppressed["original_intensity"]
            })

        return suppressed

    def restore_event(
        self,
        event_id: str
    ) -> Optional[Dict[str, Any]]:
        """Restore a suppressed event."""
        if event_id not in self.suppressed_events:
            return None

        suppressed_state = self.suppressed_events[event_id]
        restored = restore_suppressed_event(suppressed_state)
        restored["event_id"] = event_id

        # Remove from suppressed
        del self.suppressed_events[event_id]

        # Audit log
        if self.config.audit_log_enabled:
            self.audit_log.append({
                "event_id": event_id,
                "action": "restore",
                "timestamp": datetime.now().isoformat()
            })

        return restored

    def erase_event(
        self,
        event_id: str
    ) -> Dict[str, Any]:
        """Apply full erasure to an event."""
        erased = apply_full_erasure(
            event_id=event_id,
            audit_log=self.audit_log if self.config.audit_log_enabled else None
        )
        self.erased_events[event_id] = erased

        # Remove from suppressed if present
        if event_id in self.suppressed_events:
            del self.suppressed_events[event_id]

        return erased

    def get_tombstone_reference(
        self,
        event_id: str,
        original_tag: str
    ) -> Dict[str, Any]:
        """Get tombstone reference for erased event."""
        return create_tombstone_reference(event_id, original_tag)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get erasure audit log (GDPR compliance)."""
        return self.audit_log.copy()

