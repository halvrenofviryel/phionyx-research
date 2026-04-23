"""
ResonanceScore (R) Update - Echoism Core v1.1
==============================================

Per Echoism Core v1.1:
- R: Relationship depth, bounded/saturating (0.0-1.0, mandatory)
- R = 1 - exp(-k * interactions_effective)
- interactions_effective includes trace_weight and positive bond events
- Active Suppression or ethics breach → R growth damping
"""

from __future__ import annotations

import math


def calculate_resonance_score(
    interactions_effective: float,
    k: float = 0.1,
    trace_weight_sum: float = 0.0,
    positive_bond_events: int = 0,
    suppression_active: bool = False,
    ethics_breach: bool = False
) -> float:
    """
    Calculate ResonanceScore (R) with saturating function.

    Per Echoism Core v1.1:
    - R = 1 - exp(-k * interactions_effective)
    - interactions_effective includes trace_weight and positive bond events
    - R is bounded to [0.0, 1.0]
    - Active Suppression or ethics breach → R growth damping

    Args:
        interactions_effective: Effective interaction count (not just message count)
        k: Saturation rate (default: 0.1)
        trace_weight_sum: Sum of trace weights from positive events
        positive_bond_events: Count of positive bond-forming events
        suppression_active: Whether active suppression is active (damps R growth)
        ethics_breach: Whether ethics breach detected (damps R growth)

    Returns:
        ResonanceScore (0.0-1.0)
    """
    # Calculate effective interactions (weighted by trace and positive events)
    effective = interactions_effective + trace_weight_sum * 0.5 + positive_bond_events * 0.3

    # Apply damping if suppression or ethics breach
    damping_factor = 1.0
    if suppression_active:
        damping_factor *= 0.5  # 50% damping
    if ethics_breach:
        damping_factor *= 0.3  # 70% damping (stronger)

    effective = effective * damping_factor

    # Saturating function: R = 1 - exp(-k * effective)
    R = 1.0 - math.exp(-k * effective)

    # Clamp to [0.0, 1.0]
    R = max(0.0, min(1.0, R))

    return R


def update_resonance_from_events(
    current_R: float,
    new_interactions: int = 0,
    trace_weight_sum: float = 0.0,
    positive_bond_events: int = 0,
    suppression_active: bool = False,
    ethics_breach: bool = False,
    k: float = 0.1
) -> float:
    """
    Update ResonanceScore (R) incrementally from new events.

    Per Echoism Core v1.1:
    - R update happens in 'post-event' phase
    - Each turn, R is updated based on new interactions
    - R growth is damped if suppression or ethics breach

    Args:
        current_R: Current ResonanceScore
        new_interactions: New interaction count this turn
        trace_weight_sum: Sum of trace weights from positive events this turn
        positive_bond_events: Count of positive bond-forming events this turn
        suppression_active: Whether active suppression is active
        ethics_breach: Whether ethics breach detected
        k: Saturation rate

    Returns:
        Updated ResonanceScore (0.0-1.0)
    """
    # Calculate effective new interactions
    effective_new = new_interactions + trace_weight_sum * 0.5 + positive_bond_events * 0.3

    # Apply damping
    damping_factor = 1.0
    if suppression_active:
        damping_factor *= 0.5
    if ethics_breach:
        damping_factor *= 0.3

    effective_new = effective_new * damping_factor

    # Calculate R increment
    # R_new = 1 - exp(-k * (effective_total))
    # We need to reverse-engineer effective_total from current_R
    # current_R = 1 - exp(-k * effective_old)
    # effective_old = -ln(1 - current_R) / k

    if current_R >= 1.0:
        return 1.0  # Already saturated

    effective_old = -math.log(1.0 - current_R) / k if k > 0 else 0.0
    effective_total = effective_old + effective_new

    # Calculate new R
    R_new = 1.0 - math.exp(-k * effective_total)
    R_new = max(0.0, min(1.0, R_new))

    return R_new


def get_resonance_growth_rate(
    current_R: float,
    k: float = 0.1
) -> float:
    """
    Get current resonance growth rate (for diagnostics).

    Args:
        current_R: Current ResonanceScore
        k: Saturation rate

    Returns:
        Growth rate (effective interactions per unit R)
    """
    if current_R >= 1.0:
        return 0.0  # Saturated

    if k <= 0:
        return 0.0

    # Reverse-engineer effective interactions from R
    _effective = -math.log(1.0 - current_R) / k

    # Growth rate = dR/d(effective) = k * (1 - R)
    growth_rate = k * (1.0 - current_R)

    return growth_rate

